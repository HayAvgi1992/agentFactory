"""Planner Agent — decides which knowledge sources to retrieve before decisions."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import call_json_agent, get_client
from app.state import GTMState

ALL_SOURCES = [
    "crm_accounts",
    "product_catalog",
    "case_studies",
    "pricing",
    "sales_playbooks",
]


def _mock_planner(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    sources: List[str] = ["sales_playbooks", "product_catalog"]
    company = (lead_data.get("company_name") or "").lower()
    industry = (lead_data.get("industry") or "").lower()
    message = (lead_data.get("message") or "").lower()

    if company:
        sources.insert(0, "crm_accounts")
    if "pricing" in message or "cost" in message:
        sources.append("pricing")
    if industry in ("fintech", "finance", "saas"):
        sources.append("case_studies")

    seen: List[str] = []
    for source in sources:
        if source not in seen:
            seen.append(source)
    return {"required_sources": seen}


def run_planner_agent(state: GTMState) -> Dict[str, Any]:
    lead_data = state["lead"]
    client = get_client()
    if not client:
        return _mock_planner(lead_data)

    prompt = f"""Plan what business knowledge sources are needed to qualify and recommend products for this lead.

Company: {lead_data.get('company_name')}
Industry: {lead_data.get('industry', 'unknown')}
Company Size: {lead_data.get('company_size', 'unknown')}
Message: {lead_data.get('message')}

Available sources: {', '.join(ALL_SOURCES)}

Return JSON with exactly one key:
- required_sources (array of strings, subset of available sources)
"""

    result = call_json_agent(
        "You are a GTM planning agent deciding what context to gather. Return structured JSON only.",
        prompt,
        temperature=0.1,
    )
    sources = result.get("required_sources", ALL_SOURCES[:3])
    valid = [s for s in sources if s in ALL_SOURCES]
    return {"required_sources": valid or ALL_SOURCES[:3]}
