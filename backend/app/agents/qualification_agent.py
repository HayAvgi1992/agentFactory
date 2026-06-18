"""Qualification Agent — scores leads 0-100 and decides qualified/not qualified."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from openai import OpenAI

from app.config import settings

QUALIFICATION_THRESHOLD = 60


def _get_client() -> Optional[OpenAI]:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def _mock_qualification(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    message = lead_data.get("message", "").lower()
    score = 50

    if "demo" in message or "pricing" in message or "solution" in message:
        score += 20
    if "urgent" in message or "asap" in message:
        score += 15
    if lead_data.get("company_size") and "500" in str(lead_data["company_size"]):
        score += 10
    if lead_data.get("industry"):
        score += 5

    score = min(100, max(0, score))
    qualified = score >= QUALIFICATION_THRESHOLD

    reason = (
        f"Strong fit — score {score}/100 based on intent, company size, and industry."
        if qualified
        else f"Below threshold ({QUALIFICATION_THRESHOLD}) — score {score}/100."
    )

    return {"qualified": qualified, "score": score, "reason": reason}


def run_qualification_agent(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    client = _get_client()
    if not client:
        return _mock_qualification(lead_data)

    prompt = f"""Qualify this B2B inbound lead on a scale of 0-100.

Company: {lead_data.get('company_name')}
Industry: {lead_data.get('industry', 'unknown')}
Company Size: {lead_data.get('company_size', 'unknown')}
Message: {lead_data.get('message')}

Score based on: company size, industry fit, urgency, product fit, intent in message.
Qualification threshold: {QUALIFICATION_THRESHOLD} (score >= threshold = qualified).

Return JSON with exactly these keys:
- qualified (boolean)
- score (integer 0-100)
- reason (string, one sentence explaining the decision)
"""

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "You are a B2B sales qualification expert. Return structured JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    result = json.loads(response.choices[0].message.content)
    return {
        "qualified": bool(result.get("qualified", result.get("is_qualified", False))),
        "score": int(result.get("score", 0)),
        "reason": result.get("reason", result.get("reasoning", "")),
    }
