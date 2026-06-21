"""ChromaDB RAG store — vision §13."""

from app.rag.store import get_rag_status, index_knowledge_base, rag_search


def test_chromadb_index_and_search():
    count = index_knowledge_base(force=True)
    assert count > 0

    status = get_rag_status()
    assert status["vector_store"] == "chromadb"
    assert status["indexed_chunks"] == count
    assert status["embedding_model"]

    hits = rag_search("project management SaaS", sources=["product_catalog"], limit=3)
    assert hits
    assert hits[0].get("retrieval_method") == "rag"
    assert hits[0]["score"] > 0
