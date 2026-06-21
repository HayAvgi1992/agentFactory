"""Evaluation Agent — assesses decision quality and flags human review."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import call_json_agent, get_client
from app.state import GTMState

HUMAN_REVIEW_THRESHOLD = 0.6


def _mock_evaluation(state: GTMState) -> Dict[str, Any]:
    qualification = state.get("qualification") or {}
    product_fit = state.get("product_fit") or {}
    recommendation = state.get("recommendation") or {}
    lead_data = state["lead"]

    score = qualification.get("score", 0)
    fit_confidence = product_fit.get("confidence", 0.7)
    has_context = bool(state.get("retrieved_context"))
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
        confidence < HUMAN_REVIEW_THRESHOLD
        or len(missing) >= 2
        or recommendation.get("next_action") == "reject"
    )

    return {
        "confidence": round(confidence, 2),
        "needs_human_review": needs_review,
        "missing_information": missing,
    }


def run_evaluation_agent(state: GTMState) -> Dict[str, Any]:
    client = get_client()
    if not client:
        return _mock_evaluation(state)

    lead_data = state["lead"]
    qualification = state.get("qualification") or {}
    product_fit = state.get("product_fit") or {}
    recommendation = state.get("recommendation") or {}

    prompt = f"""Evaluate the quality and completeness of this GTM agent pipeline output.

Lead: {lead_data.get('company_name')} — {lead_data.get('message')}
Qualification: score={qualification.get('score')}, qualified={qualification.get('qualified')}
Product fit: {product_fit.get('recommended_product')} (confidence {product_fit.get('confidence')})
Recommendation: {recommendation.get('next_action')}
Context documents retrieved: {len(state.get('retrieved_context') or [])}

Return JSON with:
- confidence (float 0-1, overall pipeline confidence)
- needs_human_review (boolean)
- missing_information (array of strings — gaps like budget, timeline, decision maker)
"""

    result = call_json_agent(
        "You are a GTM quality evaluator assessing AI decision reliability. Return structured JSON only.",
        prompt,
        temperature=0.1,
    )
    return {
        "confidence": float(result.get("confidence", 0.7)),
        "needs_human_review": bool(result.get("needs_human_review", False)),
        "missing_information": list(result.get("missing_information", [])),
    }
