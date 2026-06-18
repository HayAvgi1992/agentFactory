"""Recommendation Agent — decides next action: book_meeting, send_email, nurture, reject."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from openai import OpenAI

from app.config import settings

MEETING_THRESHOLD = 75


def _get_client() -> Optional[OpenAI]:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def _mock_recommendation(qualification: Dict[str, Any]) -> Dict[str, Any]:
    score = qualification.get("score", 0)

    if score >= MEETING_THRESHOLD:
        next_action = "book_meeting"
    elif qualification.get("qualified"):
        next_action = "send_email"
    elif score >= 30:
        next_action = "nurture"
    else:
        next_action = "reject"

    return {"next_action": next_action}


def run_recommendation_agent(
    lead_data: Dict[str, Any],
    qualification: Dict[str, Any],
    outreach: Dict[str, Any],
) -> Dict[str, Any]:
    client = _get_client()
    if not client:
        return _mock_recommendation(qualification)

    prompt = f"""Decide the next sales action for this lead.

Company: {lead_data.get('company_name')}
Qualification: score={qualification.get('score')}, qualified={qualification.get('qualified')}
Reason: {qualification.get('reason')}

Choose ONE next_action:
- book_meeting: Strong lead, schedule a meeting (score >= {MEETING_THRESHOLD})
- send_email: Qualified but needs warming up
- nurture: Low intent, add to nurture campaign
- reject: Poor fit, do not pursue

Return JSON with exactly one key: next_action (string).
"""

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "You are a B2B sales strategist deciding the next action. Return structured JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    result = json.loads(response.choices[0].message.content)
    action = result.get("next_action", result.get("action", "send_email"))
    valid = {"book_meeting", "send_email", "nurture", "reject"}
    if action not in valid:
        action = "send_email"
    return {"next_action": action}
