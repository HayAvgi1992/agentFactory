"""Internal knowledge base — vision §9 (pre-RAG file search)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

SOURCE_DIRS = {
    "crm_accounts": "crm_accounts",
    "product_catalog": "product_catalog",
    "pricing": "pricing",
    "sales_playbooks": "sales_playbooks",
    "case_studies": "case_studies",
}

# Vision §9 — what each folder simulates in a real GTM stack
KNOWLEDGE_REGISTRY: Dict[str, Dict[str, str]] = {
    "crm_accounts": {
        "label": "CRM Accounts",
        "simulates": "Salesforce / HubSpot account records",
        "description": "Named account context, deal stage, and fit signals",
    },
    "product_catalog": {
        "label": "Product Catalog",
        "simulates": "Product documentation",
        "description": "Monday CRM and Work Management capabilities and ICP",
    },
    "pricing": {
        "label": "Pricing",
        "simulates": "Internal pricing sheets",
        "description": "Plan tiers and packaging for sales conversations",
    },
    "sales_playbooks": {
        "label": "Sales Playbooks",
        "simulates": "Internal sales playbooks",
        "description": "Qualification criteria, scoring, and disqualifiers",
    },
    "case_studies": {
        "label": "Case Studies",
        "simulates": "Customer success stories",
        "description": "Industry proof points and product outcomes",
    },
}


def _knowledge_root() -> Path:
    return Path(settings.knowledge_dir)


def list_knowledge_sources() -> List[str]:
    return list(SOURCE_DIRS.keys())


def get_source_info(source: str) -> Optional[Dict[str, str]]:
    meta = KNOWLEDGE_REGISTRY.get(source)
    if not meta:
        return None
    return {"source": source, **meta}


def inventory_knowledge_base() -> List[Dict[str, Any]]:
    """Return catalog of sources with on-disk document inventory (§9)."""
    items: List[Dict[str, Any]] = []
    root = _knowledge_root()
    for source, subdir in SOURCE_DIRS.items():
        meta = KNOWLEDGE_REGISTRY[source]
        folder = root / subdir
        documents: List[str] = []
        if folder.is_dir():
            documents = sorted(path.stem for path in folder.glob("*.md"))
        items.append(
            {
                "source": source,
                "label": meta["label"],
                "simulates": meta["simulates"],
                "description": meta["description"],
                "path": f"knowledge/{subdir}",
                "document_count": len(documents),
                "documents": documents,
            }
        )
    return items


def validate_knowledge_base() -> Dict[str, Any]:
    """Check required folders exist and contain markdown documents."""
    root = _knowledge_root()
    missing_dirs: List[str] = []
    empty_dirs: List[str] = []
    for source, subdir in SOURCE_DIRS.items():
        folder = root / subdir
        if not folder.is_dir():
            missing_dirs.append(source)
        elif not list(folder.glob("*.md")):
            empty_dirs.append(source)
    inventory = inventory_knowledge_base()
    return {
        "root": str(root),
        "valid": not missing_dirs and not empty_dirs,
        "missing_dirs": missing_dirs,
        "empty_dirs": empty_dirs,
        "total_documents": sum(item["document_count"] for item in inventory),
        "sources": inventory,
    }


def load_document(source: str, document_id: str, max_chars: int = 2000) -> Optional[str]:
    subdir = SOURCE_DIRS.get(source)
    if not subdir:
        return None
    path = _knowledge_root() / subdir / f"{document_id}.md"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")[:max_chars]


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
