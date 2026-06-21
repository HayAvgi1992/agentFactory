"""Research Agent — vision §11: collect context via tools and RAG."""

from __future__ import annotations

from typing import Any, Dict, List, Set

from app.config import settings
from app.prompts.registry import get_prompt_version
from app.rag import rag_search
from app.state import GTMState, get_lead, get_planner
from app.tools.registry import execute_source_search, execute_tool


def _merge_hits(existing: List[Dict[str, Any]], new_hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Set[str] = {f"{h.get('source')}:{h.get('document_id')}" for h in existing}
    merged = list(existing)
    for hit in new_hits:
        key = f"{hit.get('source')}:{hit.get('document_id')}"
        if key not in seen:
            seen.add(key)
            merged.append(hit)
    return merged


def run_research_agent(state: GTMState) -> Dict[str, Any]:
    lead_data = get_lead(state)
    planner = get_planner(state)
    required_sources = planner.get("required_sources") or [
        "crm_accounts",
        "product_catalog",
        "sales_playbooks",
    ]

    company = str(lead_data.get("company_name") or "")
    industry = str(lead_data.get("industry") or "")
    message = str(lead_data.get("message") or "")
    query = f"{company} {industry} {message}".strip()

    retrieved_context: List[Dict[str, Any]] = []
    document_ids: List[str] = []
    patterns_identified: List[str] = []
    tools_used: List[str] = []
    retrieval_methods: List[str] = []

    for source in required_sources:
        tool_name, hits = execute_source_search(source, lead_data)
        tools_used.append(tool_name)
        if hits:
            patterns_identified.append(f"Tool {tool_name}: {len(hits)} doc(s) from {source}")
            for hit in hits:
                hit.setdefault("retrieval_method", "keyword")
            retrieved_context = _merge_hits(retrieved_context, hits)

    if settings.rag_enabled:
        rag_hits = rag_search(query, sources=required_sources, limit=6)
        if rag_hits:
            retrieval_methods.append("rag")
            patterns_identified.append(f"RAG vector search: {len(rag_hits)} chunk(s)")
            retrieved_context = _merge_hits(retrieved_context, rag_hits)
    retrieval_methods.append("keyword")

    for hit in retrieved_context:
        doc_id = hit.get("document_id")
        if doc_id and doc_id not in document_ids:
            document_ids.append(str(doc_id))

    if not retrieved_context:
        tools_used.append("search_knowledge_base")
        fallback = execute_tool("search_knowledge_base", query, lead_data=lead_data)
        for hit in fallback[:3]:
            hit.setdefault("retrieval_method", "keyword")
            retrieved_context.append(hit)
            doc_id = hit.get("document_id")
            if doc_id and doc_id not in document_ids:
                document_ids.append(str(doc_id))
        if fallback:
            patterns_identified.append("Fallback broad knowledge search used")

    reasoning = (
        f"Collected {len(document_ids)} documents using tools {', '.join(sorted(set(tools_used)))}. "
        f"Populated shared state retrieved_context for downstream agents."
    )

    return {
        "retrieved_context": retrieved_context,
        "retrieved_documents": document_ids,
        "patterns_identified": patterns_identified,
        "reasoning": reasoning,
        "tools_used": sorted(set(tools_used)),
        "retrieval_methods": sorted(set(retrieval_methods)),
        "prompt_version": get_prompt_version("research"),
    }
