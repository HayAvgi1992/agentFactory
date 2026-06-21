"""Product Fit Agent — vision §8: recommend the most appropriate product."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import call_json_agent, get_client, reasoning_system_prompt
from app.agents.guardrails import apply_product_fit_guardrails
from app.agents.product_fit_context import (
    available_product_fit_inputs,
    build_product_fit_reasoning,
    format_product_fit_prompt_context,
    partition_product_fit_context,
    recommend_product_from_signals,
)
from app.state import GTMState, get_lead, get_qualification, get_retrieved_context


def _mock_product_fit(
    lead_data: Dict[str, Any],
    qualification: Dict[str, Any],
    retrieved_context: List[Dict[str, Any]],
) -> Dict[str, Any]:
    partitions = partition_product_fit_context(retrieved_context)
    input_labels = available_product_fit_inputs(
        partitions,
        has_qualification=bool(qualification),
    )
    product, alt, requirements, patterns, tradeoffs, confidence = recommend_product_from_signals(
        lead_data,
        qualification,
        partitions,
    )
    reasoning = build_product_fit_reasoning(lead_data, product, requirements, input_labels)

    raw = {
        "recommended_product": product,
        "alternative_products": alt,
        "confidence": confidence,
        "matching_requirements": requirements,
        "patterns": patterns,
        "tradeoffs": tradeoffs,
        "reasoning": reasoning,
        "context_inputs": input_labels,
    }
    return apply_product_fit_guardrails(raw)


def run_product_fit_agent(state: GTMState) -> Dict[str, Any]:
    lead_data = get_lead(state)
    qualification = get_qualification(state)
    retrieved_context = get_retrieved_context(state)
    partitions = partition_product_fit_context(retrieved_context)
    input_labels = available_product_fit_inputs(
        partitions,
        has_qualification=bool(qualification),
    )

    client = get_client()
    if not client:
        return _mock_product_fit(lead_data, qualification, retrieved_context)

    context_block = format_product_fit_prompt_context(lead_data, qualification, partitions)
    prompt = f"""Recommend the most appropriate product for this B2B lead (vision §8).

{context_block}

Use all inputs above. Match lead requirements to product capabilities and case study evidence.
Explain WHY the recommended product fits — a human reviewer must understand your decision.

Return JSON with:
- recommended_product (string — "Monday CRM" or "Work Management")
- alternative_products (array of strings)
- confidence (float 0-1)
- matching_requirements (array — e.g. "Pipeline visibility", "Lead tracking")
- patterns (array — requirement patterns identified)
- tradeoffs (array — why not the alternative)
- reasoning (string — explain WHY, per vision §8)
"""

    result = call_json_agent(
        reasoning_system_prompt("product specialist matching leads to offerings"),
        prompt,
        temperature=0.3,
    )
    reasoning = str(result.get("reasoning") or "")
    raw = {
        "recommended_product": result.get("recommended_product", "Work Management"),
        "alternative_products": list(result.get("alternative_products") or []),
        "confidence": float(result.get("confidence", 0.7)),
        "matching_requirements": list(result.get("matching_requirements") or []),
        "patterns": list(result.get("patterns") or []),
        "tradeoffs": list(result.get("tradeoffs") or []),
        "reasoning": reasoning,
        "context_inputs": input_labels,
    }
    return apply_product_fit_guardrails(raw)
