"""Outreach Agent — generates email, LinkedIn message, and discovery questions."""

from __future__ import annotations

from typing import Any, Dict

from app.agents.base import call_json_agent, get_client
from app.state import GTMState


def _mock_outreach(state: GTMState) -> Dict[str, Any]:
    lead_data = state["lead"]
    product_fit = state.get("product_fit") or {}
    company = lead_data.get("company_name", "your company")
    industry = lead_data.get("industry", "your industry")
    product = product_fit.get("recommended_product", "our platform")

    return {
        "email": (
            f"Subject: Following up on your inquiry\n\n"
            f"Hi,\n\n"
            f"Thanks for reaching out. Based on {company}'s focus in {industry}, "
            f"I'd love to share how similar teams are succeeding with {product}.\n\n"
            f"Would you be open to a 20-minute call this week?\n\n"
            f"Best,\nSDR Team"
        ),
        "linkedin": (
            f"Saw your inquiry from {company} — would love to connect and share "
            f"relevant case studies for {product}. Open to a quick chat?"
        ),
        "questions": [
            "What prompted you to explore a solution like ours now?",
            "Who else is involved in the evaluation process?",
            "What does success look like in the next 90 days?",
            "What's your current approach to this challenge?",
        ],
    }


def run_outreach_agent(state: GTMState) -> Dict[str, Any]:
    client = get_client()
    if not client:
        return _mock_outreach(state)

    lead_data = state["lead"]
    qualification = state.get("qualification") or {}
    product_fit = state.get("product_fit") or {}

    prompt = f"""Generate personalized outreach for this B2B lead.

Company: {lead_data.get('company_name')}
Industry: {lead_data.get('industry', 'unknown')}
Message: {lead_data.get('message')}
Qualification score: {qualification.get('score')}/100
Recommended product: {product_fit.get('recommended_product', 'unknown')}
Product fit reasoning: {product_fit.get('reasoning', '')}

Generate:
1. email — full first-touch email with subject line
2. linkedin — concise LinkedIn DM (under 300 chars)
3. questions — array of 4 discovery questions

Return JSON with exactly these keys: email, linkedin, questions.
"""

    result = call_json_agent(
        "You are a B2B SDR writing personalized outreach. Return structured JSON only.",
        prompt,
        temperature=0.7,
    )
    return {
        "email": result.get("email", result.get("email_draft", "")),
        "linkedin": result.get("linkedin", result.get("linkedin_message", "")),
        "questions": result.get("questions", result.get("discovery_questions", [])),
    }
