"""Evaluation Agent — vision §12: measure decision quality."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import call_json_agent, get_client, reasoning_system_prompt
from app.agents.guardrails import HUMAN_REVIEW_CONFIDENCE_THRESHOLD, apply_evaluation_guardrails
from app.prompts.registry import get_prompt_instruction, get_prompt_version
from app.state import (
    GTMState,
    get_lead,
    get_product_fit,
    get_qualification,
    get_recommendation,
    get_retrieved_context,
)


def _evaluation_inputs(state: GTMState) -> List[str]:
    labels = ["Lead Input", "Qualification Output", "Product Fit Output", "Recommendation Output"]
    if get_retrieved_context(state):
        labels.append("Retrieved Context")
    return labels


def _mock_evaluation(state: GTMState) -> Dict[str, Any]:
    qualification = get_qualification(state)
    product_fit = get_product_fit(state)
    recommendation = get_recommendation(state)
    lead_data = get_lead(state)

    score = qualification.get("score", 0)
    fit_confidence = product_fit.get("confidence", 0.7)
    has_context = bool(get_retrieved_context(state))
    message = (lead_data.get("message") or "").lower()

    confidence = min(0.95, (score / 100) * 0.5 + fit_confidence * 0.4 + (0.1 if has_context else 0))
    missing: List[str] = []
    if "budget" not in message and "pricing" not in message:
        missing.append("budget")
    if not lead_data.get("company_size"):
        missing.append("company_size")
    if not has_context:
        missing.append("crm_context")

    needs_review = (
        confidence < HUMAN_REVIEW_CONFIDENCE_THRESHOLD
        or len(missing) >= 2
        or recommendation.get("next_action") in ("reject", "human_review")
    )

    reasoning = (
        f"Pipeline confidence {confidence:.0%} based on qualification ({score}/100), "
        f"product-fit ({fit_confidence:.0%}), and {len(missing)} information gaps."
    )

    raw = {
        "confidence": round(confidence, 2),
        "needs_human_review": needs_review,
        "missing_information": missing,
        "reasoning": reasoning,
        "context_inputs": _evaluation_inputs(state),
        "prompt_version": get_prompt_version("evaluation"),
    }
    return apply_evaluation_guardrails(raw)


def run_evaluation_agent(state: GTMState) -> Dict[str, Any]:
    client = get_client()
    if not client:
        return _mock_evaluation(state)

    lead_data = get_lead(state)
    qualification = get_qualification(state)
    product_fit = get_product_fit(state)
    recommendation = get_recommendation(state)
    context_count = len(get_retrieved_context(state))

    prompt = f"""{get_prompt_instruction("evaluation")}

Lead: {lead_data.get('company_name')} — {lead_data.get('message')}
Qualification: score={qualification.get('score')}, qualified={qualification.get('qualified')}
Product fit: {product_fit.get('recommended_product')} (confidence {product_fit.get('confidence')})
Recommendation: {recommendation.get('next_action')}
Context documents retrieved: {context_count}

Return JSON with:
- confidence (float 0-1)
- needs_human_review (boolean)
- missing_information (array of strings)
- reasoning (string — quality assessment per §12)
"""

    result = call_json_agent(
        reasoning_system_prompt("GTM quality evaluator measuring AI decision reliability"),
        prompt,
        temperature=0.2,
    )
    raw = {
        "confidence": float(result.get("confidence", 0.7)),
        "needs_human_review": bool(result.get("needs_human_review", False)),
        "missing_information": list(result.get("missing_information") or []),
        "reasoning": str(result.get("reasoning") or ""),
        "context_inputs": _evaluation_inputs(state),
        "prompt_version": get_prompt_version("evaluation"),
    }
    return apply_evaluation_guardrails(raw)
