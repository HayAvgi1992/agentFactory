"""Tests for §10–§19 features."""

from app.agents.planner_agent import run_planner_agent
from app.agents.research_agent import run_research_agent
from app.rag.chunker import chunk_markdown
from app.rag.store import index_knowledge_base, rag_search
from app.state import initial_state
from app.tools.registry import execute_tool, list_tools


def test_planner_returns_required_sources():
    state = initial_state(
        {
            "company_name": "Acme",
            "industry": "SaaS",
            "message": "We need pricing for CRM",
        }
    )
    result = run_planner_agent(state)
    assert result["required_sources"]
    assert "crm_accounts" in result["required_sources"]
    assert result["context_inputs"]
    assert result["prompt_version"]


def test_research_uses_tools_and_rag():
    state = initial_state(
        {
            "company_name": "Acme",
            "industry": "SaaS",
            "message": "project management solution",
        }
    )
    state["planner"] = run_planner_agent(state)
    result = run_research_agent(state)
    assert result["retrieved_documents"]
    assert result["tools_used"]
    assert "search_crm_account" in result["tools_used"]
    assert result["retrieved_context"]


def test_tool_registry_lists_vision_tools():
    tools = list_tools()
    names = {t["name"] for t in tools}
    assert "search_crm_account" in names
    assert "search_product_catalog" in names
    assert "search_case_studies" in names
    assert "search_knowledge_base" in names


def test_execute_tool_crm():
    hits = execute_tool("search_crm_account", "Acme")
    assert hits
    assert hits[0]["source"] == "crm_accounts"


def test_rag_index_and_search():
    count = index_knowledge_base(force=True)
    assert count > 0
    hits = rag_search("project management SaaS", sources=["product_catalog"], limit=3)
    assert hits
    assert hits[0].get("retrieval_method") == "rag"


def test_rag_status_reports_chromadb():
    from app.rag.store import get_rag_status

    index_knowledge_base(force=True)
    status = get_rag_status()
    assert status["vector_store"] == "chromadb"
    assert status["embedding_model"]
    assert status["indexed_chunks"] > 0


def test_chunk_markdown_splits_sections():
    text = "# Title\n\nIntro\n\n## Section\n\nBody"
    chunks = chunk_markdown(text, "doc1", "product_catalog")
    assert len(chunks) >= 2
