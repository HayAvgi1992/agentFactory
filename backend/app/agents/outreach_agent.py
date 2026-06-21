"""Outreach Agent — generates email, LinkedIn message, and discovery questions."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import call_json_agent, get_client, reasoning_system_prompt
from app.state import GTMState, get_lead, get_product_fit, get_qualification


def _mock_outreach(state: GTMState) -> Dict[str, Any]:
    lead_data = get_lead(state)
    product_fit = get_product_fit(state)
    qualification = get_qualification(state)
    company = lead_data.get("company_name", "your company")
    industry = lead_data.get("industry", "your industry")
    product = product_fit.get("recommended_product", "our platform")

    patterns = [
        f"Personalized for {industry} industry" if industry else "Generic industry outreach",
        f"Anchored on {product} recommendation",
    ]
    reasoning = (
        f"Outreach tailored to qualification score {qualification.get('score', 'N/A')} "
        f"and product fit ({product})."
    )

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
        "patterns": patterns,
        "reasoning": reasoning,
    }


def run_outreach_agent(state: GTMState) -> Dict[str, Any]:
    client = get_client()
    if not client:
        return _mock_outreach(state)

    lead_data = get_lead(state)
    qualification = get_qualification(state)
    product_fit = get_product_fit(state)

    prompt = f"""Generate personalized outreach for this B2B lead.

Company: {lead_data.get('company_name')}
Industry: {lead_data.get('industry', 'unknown')}
Message: {lead_data.get('message')}
Qualification score: {qualification.get('score')}/100
Recommended product: {product_fit.get('recommended_product', 'unknown')}
Product fit reasoning: {product_fit.get('reasoning', '')}

Identify personalization patterns, then generate outreach.

Return JSON with:
- email (string — full first-touch email with subject line)
- linkedin (string — concise LinkedIn DM under 300 chars)
- questions (array of 4 discovery questions)
- patterns (array — personalization patterns applied)
- reasoning (string — why this outreach approach)
"""

    result = call_json_agent(
        reasoning_system_prompt("B2B SDR writing personalized outreach"),
        prompt,
        temperature=0.7,
    )
    return {
        "email": result.get("email", result.get("email_draft", "")),
        "linkedin": result.get("linkedin", result.get("linkedin_message", "")),
        "questions": result.get("questions", result.get("discovery_questions", [])),
        "patterns": list(result.get("patterns") or []),
        "reasoning": str(result.get("reasoning") or ""),
    }
