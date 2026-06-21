"""File-based knowledge search — simulates CRM, catalog, playbooks (pre-RAG)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from app.config import settings

SOURCE_DIRS = {
    "crm_accounts": "crm_accounts",
    "product_catalog": "product_catalog",
    "pricing": "pricing",
    "sales_playbooks": "sales_playbooks",
    "case_studies": "case_studies",
}


def _knowledge_root() -> Path:
    return Path(settings.knowledge_dir)


def _score_document(text: str, query: str) -> int:
    text_lower = text.lower()
    score = 0
    for token in query.lower().split():
        if len(token) < 3:
            continue
        if token in text_lower:
            score += 2
    return score


def search_knowledge_source(source: str, query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Search markdown files under a knowledge category."""
    subdir = SOURCE_DIRS.get(source)
    if not subdir:
        return []

    folder = _knowledge_root() / subdir
    if not folder.is_dir():
        return []

    hits: List[Dict[str, Any]] = []
    for path in sorted(folder.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        score = _score_document(text, query)
        if score == 0 and query:
            continue
        snippet = text.strip().replace("\n", " ")[:400]
        hits.append(
            {
                "source": source,
                "document_id": path.stem,
                "title": path.stem.replace("_", " ").title(),
                "snippet": snippet,
                "score": score,
            }
        )

    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits[:limit]


def search_crm_account(company_name: str) -> List[Dict[str, Any]]:
    return search_knowledge_source("crm_accounts", company_name)


def search_product_catalog(query: str) -> List[Dict[str, Any]]:
    return search_knowledge_source("product_catalog", query)


def search_case_studies(query: str) -> List[Dict[str, Any]]:
    return search_knowledge_source("case_studies", query)


def search_pricing(query: str) -> List[Dict[str, Any]]:
    return search_knowledge_source("pricing", query)


def search_sales_playbooks(query: str) -> List[Dict[str, Any]]:
    return search_knowledge_source("sales_playbooks", query)


def search_knowledge_base(query: str, sources: List[str] | None = None) -> List[Dict[str, Any]]:
    targets = sources or list(SOURCE_DIRS.keys())
    results: List[Dict[str, Any]] = []
    for source in targets:
        results.extend(search_knowledge_source(source, query, limit=1))
    results.sort(key=lambda h: h["score"], reverse=True)
    return results
