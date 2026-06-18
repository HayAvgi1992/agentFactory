"""Outreach Agent — generates email, LinkedIn message, and discovery questions."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from openai import OpenAI

from app.config import settings


def _get_client() -> Optional[OpenAI]:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def _mock_outreach(lead_data: Dict[str, Any], qualification: Dict[str, Any]) -> Dict[str, Any]:
    company = lead_data.get("company_name", "your company")
    industry = lead_data.get("industry", "your industry")

    return {
        "email": (
            f"Subject: Following up on your inquiry\n\n"
            f"Hi,\n\n"
            f"Thanks for reaching out about a project management solution. "
            f"Given {company}'s focus in {industry}, I'd love to share how similar teams "
            f"are improving productivity.\n\n"
            f"Would you be open to a 20-minute call this week?\n\n"
            f"Best,\nSDR Team"
        ),
        "linkedin": (
            f"Saw your inquiry from {company} — would love to connect and share "
            f"relevant case studies from {industry}. Open to a quick chat?"
        ),
        "questions": [
            "What prompted you to explore a solution like ours now?",
            "Who else is involved in the evaluation process?",
            "What does success look like in the next 90 days?",
            "What's your current approach to this challenge?",
        ],
    }


def run_outreach_agent(
    lead_data: Dict[str, Any],
    qualification: Dict[str, Any],
) -> Dict[str, Any]:
    client = _get_client()
    if not client:
        return _mock_outreach(lead_data, qualification)

    prompt = f"""Generate personalized outreach for this B2B lead.

Company: {lead_data.get('company_name')}
Industry: {lead_data.get('industry', 'unknown')}
Message: {lead_data.get('message')}
Qualification score: {qualification.get('score')}/100

Generate:
1. email — full first-touch email with subject line
2. linkedin — concise LinkedIn DM (under 300 chars)
3. questions — array of 4 discovery questions

Return JSON with exactly these keys: email, linkedin, questions.
"""

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "You are a B2B SDR writing personalized outreach. Return structured JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    result = json.loads(response.choices[0].message.content)
    return {
        "email": result.get("email", result.get("email_draft", "")),
        "linkedin": result.get("linkedin", result.get("linkedin_message", "")),
        "questions": result.get("questions", result.get("discovery_questions", [])),
    }
