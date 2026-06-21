"""Research Agent — retrieves business context via knowledge tools."""

from __future__ import annotations

from typing import Any, Dict, List

from app.state import GTMState, get_lead, get_planner
from app.tools import knowledge as kb


def _search_source(source: str, lead_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    company = lead_data.get("company_name", "")
    industry = lead_data.get("industry", "")
    message = lead_data.get("message", "")
    query = f"{company} {industry} {message}".strip()

    if source == "crm_accounts":
        return kb.search_crm_account(company)
    if source == "product_catalog":
        return kb.search_product_catalog(query)
    if source == "case_studies":
        return kb.search_case_studies(query)
    if source == "pricing":
        return kb.search_pricing(query)
    if source == "sales_playbooks":
        return kb.search_sales_playbooks("qualification")
    return kb.search_knowledge_source(source, query)


def run_research_agent(state: GTMState) -> Dict[str, Any]:
    lead_data = get_lead(state)
    planner = get_planner(state)
    required_sources = planner.get("required_sources") or [
        "crm_accounts",
        "product_catalog",
        "sales_playbooks",
    ]

    retrieved_context: List[Dict[str, Any]] = []
    document_ids: List[str] = []
    patterns_identified: List[str] = []

    for source in required_sources:
        hits = _search_source(source, lead_data)
        if hits:
            patterns_identified.append(f"Found {len(hits)} doc(s) in {source}")
        for hit in hits:
            retrieved_context.append(hit)
            doc_id = hit.get("document_id")
            if doc_id and doc_id not in document_ids:
                document_ids.append(doc_id)

    if not retrieved_context:
        fallback = kb.search_knowledge_base(
            f"{lead_data.get('company_name', '')} {lead_data.get('industry', '')}"
        )
        for hit in fallback[:3]:
            retrieved_context.append(hit)
            doc_id = hit.get("document_id")
            if doc_id and doc_id not in document_ids:
                document_ids.append(doc_id)
        if fallback:
            patterns_identified.append("Fallback broad knowledge search used")

    reasoning = (
        f"Retrieved {len(document_ids)} documents across {len(required_sources)} planned sources "
        f"to enrich shared state for downstream agents."
    )

    return {
        "retrieved_context": retrieved_context,
        "retrieved_documents": document_ids,
        "patterns_identified": patterns_identified,
        "reasoning": reasoning,
    }
