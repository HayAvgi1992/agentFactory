"""Planner Agent — decides which knowledge sources to retrieve before decisions."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import call_json_agent, get_client, reasoning_system_prompt
from app.state import GTMState, get_lead
from app.tools.knowledge import SOURCE_DIRS

ALL_SOURCES = list(SOURCE_DIRS.keys())


def _mock_planner(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    company = (lead_data.get("company_name") or "").lower()
    industry = (lead_data.get("industry") or "").lower()
    message = (lead_data.get("message") or "").lower()

    patterns: List[str] = []
    sources: List[str] = ["sales_playbooks", "product_catalog"]

    if company:
        sources.insert(0, "crm_accounts")
        patterns.append("Named account — CRM lookup valuable")
    if "pricing" in message or "cost" in message:
        sources.append("pricing")
        patterns.append("Pricing intent detected in message")
    if industry in ("fintech", "finance", "saas"):
        sources.append("case_studies")
        patterns.append(f"Industry '{industry}' has relevant case studies")

    seen: List[str] = []
    for source in sources:
        if source not in seen:
            seen.append(source)

    reasoning = (
        f"Planned retrieval from {len(seen)} sources based on "
        f"{len(patterns)} observed patterns in the lead profile."
    )
    return {
        "required_sources": seen,
        "patterns": patterns,
        "reasoning": reasoning,
    }


def run_planner_agent(state: GTMState) -> Dict[str, Any]:
    lead_data = get_lead(state)
    client = get_client()
    if not client:
        return _mock_planner(lead_data)

    prompt = f"""Plan what business knowledge sources are needed to qualify and recommend products for this lead.

Company: {lead_data.get('company_name')}
Industry: {lead_data.get('industry', 'unknown')}
Company Size: {lead_data.get('company_size', 'unknown')}
Message: {lead_data.get('message')}

Available sources: {', '.join(ALL_SOURCES)}

Analyze the lead, identify patterns, then decide which sources to retrieve.

Return JSON with:
- required_sources (array of strings, subset of available sources)
- patterns (array of strings — patterns you identified in the lead)
- reasoning (string — why these sources are needed)
"""

    result = call_json_agent(
        reasoning_system_prompt("GTM planning agent deciding what context to gather"),
        prompt,
        temperature=0.2,
    )
    sources = result.get("required_sources", ALL_SOURCES[:3])
    valid = [s for s in sources if s in ALL_SOURCES]
    return {
        "required_sources": valid or ALL_SOURCES[:3],
        "patterns": list(result.get("patterns") or []),
        "reasoning": str(result.get("reasoning") or ""),
    }
