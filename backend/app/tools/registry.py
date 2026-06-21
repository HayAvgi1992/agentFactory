"""Tool registry — vision §14: agents call tools to retrieve knowledge."""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from app.tools import knowledge as kb

ToolFn = Callable[..., List[Dict[str, Any]]]

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "search_crm_account": {
        "description": "Search CRM account records by company name",
        "source": "crm_accounts",
        "fn": lambda query, **_: kb.search_crm_account(query),
    },
    "search_product_catalog": {
        "description": "Search product documentation",
        "source": "product_catalog",
        "fn": lambda query, **_: kb.search_product_catalog(query),
    },
    "search_case_studies": {
        "description": "Search customer success case studies",
        "source": "case_studies",
        "fn": lambda query, **_: kb.search_case_studies(query),
    },
    "search_pricing": {
        "description": "Search internal pricing sheets",
        "source": "pricing",
        "fn": lambda query, **_: kb.search_pricing(query),
    },
    "search_sales_playbooks": {
        "description": "Search sales playbooks",
        "source": "sales_playbooks",
        "fn": lambda query, **_: kb.search_sales_playbooks(query),
    },
    "search_knowledge_base": {
        "description": "Broad search across all knowledge sources",
        "source": "all",
        "fn": lambda query, **_: kb.search_knowledge_base(query),
    },
}

SOURCE_TO_TOOL = {
    "crm_accounts": "search_crm_account",
    "product_catalog": "search_product_catalog",
    "case_studies": "search_case_studies",
    "pricing": "search_pricing",
    "sales_playbooks": "search_sales_playbooks",
}


def list_tools() -> List[Dict[str, str]]:
    return [
        {"name": name, "description": meta["description"], "source": meta["source"]}
        for name, meta in TOOL_REGISTRY.items()
    ]


def execute_tool(tool_name: str, query: str, *, lead_data: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """Execute a registered knowledge tool (§14)."""
    meta = TOOL_REGISTRY.get(tool_name)
    if not meta:
        return []
    return meta["fn"](query, lead_data=lead_data or {})


def execute_source_search(source: str, lead_data: Dict[str, Any]) -> tuple[str, List[Dict[str, Any]]]:
    """Map planner source id → tool call."""
    company = str(lead_data.get("company_name") or "")
    industry = str(lead_data.get("industry") or "")
    message = str(lead_data.get("message") or "")
    query = f"{company} {industry} {message}".strip()

    if source == "crm_accounts":
        return "search_crm_account", execute_tool("search_crm_account", company, lead_data=lead_data)
    if source == "sales_playbooks":
        return "search_sales_playbooks", execute_tool("search_sales_playbooks", "qualification", lead_data=lead_data)

    tool_name = SOURCE_TO_TOOL.get(source, "search_knowledge_base")
    return tool_name, execute_tool(tool_name, query, lead_data=lead_data)
