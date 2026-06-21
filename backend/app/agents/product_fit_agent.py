"""Product Fit Agent — recommends the best product for a qualified lead."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import call_json_agent, get_client
from app.state import GTMState

CRM_KEYWORDS = ("crm", "pipeline", "lead", "sales", "deal", "revenue")
PM_KEYWORDS = ("project", "management", "collaboration", "task", "sprint", "team")


def _mock_product_fit(lead_data: Dict[str, Any], qualification: Dict[str, Any]) -> Dict[str, Any]:
    message = (lead_data.get("message") or "").lower()
    industry = (lead_data.get("industry") or "").lower()
    score = qualification.get("score", 0)

    crm_score = sum(1 for kw in CRM_KEYWORDS if kw in message)
    pm_score = sum(1 for kw in PM_KEYWORDS if kw in message)

    if crm_score > pm_score:
        product = "Monday CRM"
        alt = ["Work Management"]
        requirements = ["Pipeline visibility", "Lead tracking"]
        reasoning = "Lead signals align with CRM and sales pipeline needs."
    else:
        product = "Work Management"
        alt = ["Monday CRM"]
        requirements = ["Project coordination", "Team collaboration"]
        reasoning = "Lead signals align with project management and team coordination."

    if industry == "fintech" and crm_score >= pm_score:
        requirements.append("Deal velocity tracking")

    confidence = min(0.95, 0.65 + score / 300 + max(crm_score, pm_score) * 0.05)

    return {
        "recommended_product": product,
        "alternative_products": alt,
        "confidence": round(confidence, 2),
        "matching_requirements": requirements,
        "reasoning": reasoning,
    }


def _format_context(retrieved_context: List[Dict[str, Any]]) -> str:
    if not retrieved_context:
        return "No retrieved context."
    lines = []
    for item in retrieved_context[:5]:
        lines.append(
            f"- [{item.get('source')}] {item.get('title', item.get('document_id'))}: "
            f"{item.get('snippet', '')[:200]}"
        )
    return "\n".join(lines)


def run_product_fit_agent(state: GTMState) -> Dict[str, Any]:
    lead_data = state["lead"]
    qualification = state.get("qualification") or {}
    retrieved_context = state.get("retrieved_context") or []

    client = get_client()
    if not client:
        return _mock_product_fit(lead_data, qualification)

    context_block = _format_context(retrieved_context)
    prompt = f"""Recommend the best product for this B2B lead.

Company: {lead_data.get('company_name')}
Industry: {lead_data.get('industry', 'unknown')}
Message: {lead_data.get('message')}
Qualification score: {qualification.get('score')}/100

Retrieved context:
{context_block}

Products: Monday CRM (sales pipeline, lead tracking), Work Management (projects, collaboration).

Return JSON with:
- recommended_product (string)
- alternative_products (array of strings)
- confidence (float 0-1)
- matching_requirements (array of strings)
- reasoning (string, one sentence)
"""

    result = call_json_agent(
        "You are a product specialist matching leads to the right offering. Return structured JSON only.",
        prompt,
        temperature=0.2,
    )
    return {
        "recommended_product": result.get("recommended_product", "Work Management"),
        "alternative_products": list(result.get("alternative_products", [])),
        "confidence": float(result.get("confidence", 0.7)),
        "matching_requirements": list(result.get("matching_requirements", [])),
        "reasoning": result.get("reasoning", ""),
    }
