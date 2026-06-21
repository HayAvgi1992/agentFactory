"""Recommendation Agent — decides next action: book_meeting, send_email, nurture, reject."""

from __future__ import annotations

from typing import Any, Dict

from app.agents.base import call_json_agent, get_client
from app.state import GTMState

MEETING_THRESHOLD = 75
VALID_ACTIONS = {"book_meeting", "send_email", "nurture", "reject", "human_review"}


def _mock_recommendation(state: GTMState) -> Dict[str, Any]:
    qualification = state.get("qualification") or {}
    product_fit = state.get("product_fit") or {}
    score = qualification.get("score", 0)
    fit_confidence = product_fit.get("confidence", 1.0)

    if fit_confidence < 0.65 and qualification.get("qualified"):
        return {"next_action": "human_review"}

    if score >= MEETING_THRESHOLD:
        next_action = "book_meeting"
    elif qualification.get("qualified"):
        next_action = "send_email"
    elif score >= 30:
        next_action = "nurture"
    else:
        next_action = "reject"

    return {"next_action": next_action}


def run_recommendation_agent(state: GTMState) -> Dict[str, Any]:
    client = get_client()
    if not client:
        return _mock_recommendation(state)

    lead_data = state["lead"]
    qualification = state.get("qualification") or {}
    product_fit = state.get("product_fit") or {}

    prompt = f"""Decide the next sales action for this lead.

Company: {lead_data.get('company_name')}
Qualification: score={qualification.get('score')}, qualified={qualification.get('qualified')}
Reasoning: {qualification.get('reasoning', qualification.get('reason'))}
Product fit: {product_fit.get('recommended_product')} (confidence {product_fit.get('confidence')})

Choose ONE next_action:
- book_meeting: Strong lead, schedule a meeting (score >= {MEETING_THRESHOLD})
- send_email: Qualified but needs warming up
- nurture: Low intent, add to nurture campaign
- reject: Poor fit, do not pursue
- human_review: Uncertain — escalate for manual review

Return JSON with exactly one key: next_action (string).
"""

    result = call_json_agent(
        "You are a B2B sales strategist deciding the next action. Return structured JSON only.",
        prompt,
        temperature=0.2,
    )
    action = result.get("next_action", result.get("action", "send_email"))
    if action not in VALID_ACTIONS:
        action = "send_email"
    return {"next_action": action}
