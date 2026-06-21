"""Qualification Agent — scores leads 0-100 and decides qualified/not qualified."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import call_json_agent, get_client
from app.config import settings
from app.state import GTMState

QUALIFICATION_THRESHOLD = 60


def _mock_qualification(lead_data: Dict[str, Any], retrieved_context: List[Dict[str, Any]]) -> Dict[str, Any]:
    message = lead_data.get("message", "").lower()
    score = 50
    signals: List[str] = []
    risks: List[str] = []

    if "demo" in message or "pricing" in message or "solution" in message:
        score += 20
        signals.append("Pricing or solution engagement")
    if "urgent" in message or "asap" in message:
        score += 15
        signals.append("Urgency expressed")
    if lead_data.get("company_size") and "500" in str(lead_data["company_size"]):
        score += 10
        signals.append("Mid-market company size")
    if lead_data.get("industry"):
        score += 5
        signals.append(f"Industry fit: {lead_data['industry']}")

    if retrieved_context:
        signals.append("CRM/playbook context available")
    else:
        risks.append("Limited business context retrieved")

    if "budget" not in message:
        risks.append("Budget unknown")

    score = min(100, max(0, score))
    qualified = score >= QUALIFICATION_THRESHOLD

    reasoning = (
        f"Strong fit — score {score}/100 based on intent, company size, and industry."
        if qualified
        else f"Below threshold ({QUALIFICATION_THRESHOLD}) — score {score}/100."
    )

    return {
        "qualified": qualified,
        "score": score,
        "signals": signals,
        "risks": risks,
        "reasoning": reasoning,
        "reason": reasoning,
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


def run_qualification_agent(state: GTMState) -> Dict[str, Any]:
    lead_data = state["lead"]
    retrieved_context = state.get("retrieved_context") or []

    client = get_client()
    if not client:
        return _mock_qualification(lead_data, retrieved_context)

    context_block = _format_context(retrieved_context)
    prompt = f"""Qualify this B2B inbound lead on a scale of 0-100.

Company: {lead_data.get('company_name')}
Industry: {lead_data.get('industry', 'unknown')}
Company Size: {lead_data.get('company_size', 'unknown')}
Message: {lead_data.get('message')}

Retrieved business context:
{context_block}

Score based on: company size, industry fit, urgency, product fit, intent in message, CRM context.
Qualification threshold: {QUALIFICATION_THRESHOLD} (score >= threshold = qualified).

Return JSON with:
- qualified (boolean)
- score (integer 0-100)
- signals (array of strings — positive indicators)
- risks (array of strings — concerns or unknowns)
- reasoning (string, one sentence explaining the decision)
"""

    result = call_json_agent(
        "You are a B2B sales qualification expert. Return structured JSON only.",
        prompt,
        temperature=0.2,
    )
    reasoning = result.get("reasoning", result.get("reason", ""))
    return {
        "qualified": bool(result.get("qualified", result.get("is_qualified", False))),
        "score": int(result.get("score", 0)),
        "signals": list(result.get("signals", [])),
        "risks": list(result.get("risks", [])),
        "reasoning": reasoning,
        "reason": reasoning,
    }
