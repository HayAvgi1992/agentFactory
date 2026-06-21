"""Recommendation Agent — decides next action: book_meeting, send_email, nurture, reject."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import call_json_agent, get_client, reasoning_system_prompt
from app.agents.guardrails import MEETING_THRESHOLD, apply_recommendation_guardrails
from app.state import GTMState, get_lead, get_product_fit, get_qualification


def _mock_recommendation(state: GTMState) -> Dict[str, Any]:
    qualification = get_qualification(state)
    product_fit = get_product_fit(state)
    score = qualification.get("score", 0)
    patterns: List[str] = []
    tradeoffs: List[str] = []

    if score >= MEETING_THRESHOLD:
        action = "book_meeting"
        patterns.append("High qualification score supports direct meeting")
    elif qualification.get("qualified"):
        action = "send_email"
        patterns.append("Qualified but needs warming")
        tradeoffs.append("Meeting deferred — score below meeting threshold")
    elif score >= 30:
        action = "nurture"
        patterns.append("Low intent — nurture track")
    else:
        action = "reject"
        patterns.append("Poor fit signals")

    reasoning = (
        f"Recommended '{action}' based on score {score} and "
        f"product-fit confidence {product_fit.get('confidence', 0):.0%}."
    )
    raw = {
        "next_action": action,
        "patterns": patterns,
        "tradeoffs": tradeoffs,
        "reasoning": reasoning,
    }
    return apply_recommendation_guardrails(raw, qualification, product_fit)


def run_recommendation_agent(state: GTMState) -> Dict[str, Any]:
    client = get_client()
    if not client:
        return _mock_recommendation(state)

    lead_data = get_lead(state)
    qualification = get_qualification(state)
    product_fit = get_product_fit(state)

    prompt = f"""Decide the next sales action for this lead.

Company: {lead_data.get('company_name')}
Qualification: score={qualification.get('score')}, qualified={qualification.get('qualified')}
Reasoning: {qualification.get('reasoning', qualification.get('reason'))}
Product fit: {product_fit.get('recommended_product')} (confidence {product_fit.get('confidence')})

Identify patterns, weigh tradeoffs, then choose ONE next_action:
- book_meeting, send_email, nurture, reject, human_review

Guidance (guardrails may adjust): book_meeting typically requires score >= {MEETING_THRESHOLD}.

Return JSON with:
- next_action (string)
- patterns (array — decision patterns you identified)
- tradeoffs (array — alternatives you considered)
- reasoning (string — explain WHY)
"""

    result = call_json_agent(
        reasoning_system_prompt("B2B sales strategist deciding the next action"),
        prompt,
        temperature=0.3,
    )
    raw = {
        "next_action": result.get("next_action", result.get("action", "send_email")),
        "patterns": list(result.get("patterns") or []),
        "tradeoffs": list(result.get("tradeoffs") or []),
        "reasoning": str(result.get("reasoning") or ""),
    }
    return apply_recommendation_guardrails(raw, qualification, product_fit)
