"""Planner Agent — vision §10: orchestrate information gathering."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import call_json_agent, get_client, reasoning_system_prompt
from app.prompts.registry import get_prompt_instruction, get_prompt_version
from app.state import GTMState, get_lead
from app.tools.knowledge import KNOWLEDGE_REGISTRY, list_knowledge_sources
from app.tools.registry import list_tools

ALL_SOURCES = list_knowledge_sources()


def _available_source_labels() -> List[str]:
    return [KNOWLEDGE_REGISTRY[s]["label"] for s in ALL_SOURCES if s in KNOWLEDGE_REGISTRY]


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
        if source not in seen and source in ALL_SOURCES:
            seen.append(source)

    reasoning = (
        f"Before making qualification and product-fit decisions, retrieval from {len(seen)} "
        f"sources will provide CRM context, product documentation, and proof points."
    )
    return {
        "required_sources": seen,
        "patterns": patterns,
        "reasoning": reasoning,
        "context_inputs": ["Lead Information", "Available Knowledge Sources"],
        "prompt_version": get_prompt_version("planner"),
    }


def run_planner_agent(state: GTMState) -> Dict[str, Any]:
    lead_data = get_lead(state)
    client = get_client()
    if not client:
        return _mock_planner(lead_data)

    tools_desc = ", ".join(f"{t['name']}({t['source']})" for t in list_tools())
    prompt = f"""{get_prompt_instruction("planner")}

Company: {lead_data.get('company_name')}
Industry: {lead_data.get('industry', 'unknown')}
Company Size: {lead_data.get('company_size', 'unknown')}
Message: {lead_data.get('message')}

Available knowledge sources: {', '.join(ALL_SOURCES)}
Registered tools: {tools_desc}

Return JSON with:
- required_sources (array — subset of available sources)
- patterns (array — patterns in the lead profile)
- reasoning (string — why these sources are required before decisions)
"""

    result = call_json_agent(
        reasoning_system_prompt("GTM planner orchestrating information gathering"),
        prompt,
        temperature=0.2,
    )
    sources = result.get("required_sources", ALL_SOURCES[:3])
    valid = [s for s in sources if s in ALL_SOURCES]
    return {
        "required_sources": valid or ALL_SOURCES[:3],
        "patterns": list(result.get("patterns") or []),
        "reasoning": str(result.get("reasoning") or ""),
        "context_inputs": ["Lead Information", "Available Knowledge Sources"],
        "prompt_version": get_prompt_version("planner"),
    }
