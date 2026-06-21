"""Product Fit Agent — recommends the best product for a qualified lead."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import call_json_agent, format_retrieved_context, get_client, reasoning_system_prompt
from app.agents.guardrails import apply_product_fit_guardrails
from app.state import GTMState, get_lead, get_qualification, get_retrieved_context

CRM_KEYWORDS = ("crm", "pipeline", "lead", "sales", "deal", "revenue")
PM_KEYWORDS = ("project", "management", "collaboration", "task", "sprint", "team")


def _mock_product_fit(lead_data: Dict[str, Any], qualification: Dict[str, Any]) -> Dict[str, Any]:
    message = (lead_data.get("message") or "").lower()
    industry = (lead_data.get("industry") or "").lower()
    score = qualification.get("score", 0)

    crm_score = sum(1 for kw in CRM_KEYWORDS if kw in message)
    pm_score = sum(1 for kw in PM_KEYWORDS if kw in message)
    patterns: List[str] = []
    tradeoffs: List[str] = []

    if crm_score:
        patterns.append(f"CRM-related language ({crm_score} signals)")
    if pm_score:
        patterns.append(f"Project-management language ({pm_score} signals)")

    if crm_score > pm_score:
        product = "Monday CRM"
        alt = ["Work Management"]
        requirements = ["Pipeline visibility", "Lead tracking"]
        reasoning = "Lead language emphasizes sales pipeline over project delivery."
        tradeoffs.append("Work Management viable if collaboration becomes primary need")
    else:
        product = "Work Management"
        alt = ["Monday CRM"]
        requirements = ["Project coordination", "Team collaboration"]
        reasoning = "Lead language emphasizes team coordination over sales tooling."
        tradeoffs.append("Monday CRM viable if pipeline tracking becomes priority")

    if industry == "fintech" and crm_score >= pm_score:
        requirements.append("Deal velocity tracking")
        patterns.append("Fintech industry — deal velocity matters")

    confidence = min(0.95, 0.65 + score / 300 + max(crm_score, pm_score) * 0.05)

    raw = {
        "recommended_product": product,
        "alternative_products": alt,
        "confidence": round(confidence, 2),
        "matching_requirements": requirements,
        "patterns": patterns,
        "tradeoffs": tradeoffs,
        "reasoning": reasoning,
    }
    return apply_product_fit_guardrails(raw)


def run_product_fit_agent(state: GTMState) -> Dict[str, Any]:
    lead_data = get_lead(state)
    qualification = get_qualification(state)
    retrieved_context = get_retrieved_context(state)

    client = get_client()
    if not client:
        return _mock_product_fit(lead_data, qualification)

    context_block = format_retrieved_context(retrieved_context)
    prompt = f"""Recommend the best product for this B2B lead.

Company: {lead_data.get('company_name')}
Industry: {lead_data.get('industry', 'unknown')}
Message: {lead_data.get('message')}
Qualification score: {qualification.get('score')}/100

Retrieved context:
{context_block}

Products: Monday CRM (sales pipeline, lead tracking), Work Management (projects, collaboration).

Identify patterns, weigh tradeoffs between products, then recommend.

Return JSON with:
- recommended_product (string)
- alternative_products (array of strings)
- confidence (float 0-1)
- matching_requirements (array of strings)
- patterns (array — requirement patterns you identified)
- tradeoffs (array — why not the alternative)
- reasoning (string — explain WHY)
"""

    result = call_json_agent(
        reasoning_system_prompt("product specialist matching leads to offerings"),
        prompt,
        temperature=0.3,
    )
    raw = {
        "recommended_product": result.get("recommended_product", "Work Management"),
        "alternative_products": list(result.get("alternative_products") or []),
        "confidence": float(result.get("confidence", 0.7)),
        "matching_requirements": list(result.get("matching_requirements") or []),
        "patterns": list(result.get("patterns") or []),
        "tradeoffs": list(result.get("tradeoffs") or []),
        "reasoning": str(result.get("reasoning") or ""),
    }
    return apply_product_fit_guardrails(raw)
