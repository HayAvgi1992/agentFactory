"""Knowledge base tests — vision §9."""

from app.tools.knowledge import (
    KNOWLEDGE_REGISTRY,
    inventory_knowledge_base,
    list_knowledge_sources,
    search_product_catalog,
    validate_knowledge_base,
)


def test_knowledge_registry_covers_all_sources():
    sources = list_knowledge_sources()
    assert set(sources) == set(KNOWLEDGE_REGISTRY.keys())
    assert "crm_accounts" in sources
    assert "product_catalog" in sources
    assert "case_studies" in sources


def test_validate_knowledge_base_is_valid():
    report = validate_knowledge_base()
    assert report["valid"] is True
    assert report["total_documents"] >= 7
    assert not report["missing_dirs"]
    assert not report["empty_dirs"]


def test_inventory_lists_documents():
    inventory = inventory_knowledge_base()
    by_source = {item["source"]: item for item in inventory}
    assert by_source["product_catalog"]["document_count"] >= 2
    assert "monday_crm" in by_source["product_catalog"]["documents"]
    assert by_source["crm_accounts"]["simulates"] == "Salesforce / HubSpot account records"


def test_search_product_catalog_finds_work_management():
    hits = search_product_catalog("project management collaboration")
    assert hits
    assert any(h["document_id"] == "work_management" for h in hits)
