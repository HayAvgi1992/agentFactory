"""ChromaDB vector store — vision §13 (embeddings + vector search)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb

from app.config import settings
from app.rag.chunker import chunk_knowledge_file
from app.rag.embeddings import COLLECTION_NAME, get_embedding_function
from app.tools.knowledge import SOURCE_DIRS, _knowledge_root

_META_FILENAME = "index_meta.json"
_client: chromadb.PersistentClient | None = None
_collection: Any = None
_cached_model: str | None = None


def _chroma_root() -> Path:
    root = Path(settings.chroma_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _meta_path() -> Path:
    return _chroma_root() / _META_FILENAME


def _knowledge_fingerprint() -> str:
    root = _knowledge_root()
    parts: List[str] = []
    for _source, subdir in SOURCE_DIRS.items():
        folder = root / subdir
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.md")):
            stat = path.stat()
            parts.append(f"{path.relative_to(root)}:{stat.st_mtime_ns}:{stat.st_size}")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _load_chunks() -> List[Dict[str, Any]]:
    root = _knowledge_root()
    chunks: List[Dict[str, Any]] = []
    for source, subdir in SOURCE_DIRS.items():
        folder = root / subdir
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.md")):
            chunks.extend(chunk_knowledge_file(path, source))
    return chunks


def _read_meta() -> Dict[str, Any]:
    path = _meta_path()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_meta(*, fingerprint: str, embedding_model: str, chunk_count: int) -> None:
    payload = {
        "fingerprint": fingerprint,
        "embedding_model": embedding_model,
        "chunk_count": chunk_count,
        "vector_store": "chromadb",
    }
    _meta_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _reset_collection() -> Any:
    global _client, _collection, _cached_model
    embedding_fn, model_name = get_embedding_function()
    _cached_model = model_name

    root = _chroma_root()
    _client = chromadb.PersistentClient(path=str(root))
    try:
        _client.delete_collection(COLLECTION_NAME)
    except (ValueError, chromadb.errors.NotFoundError):
        pass

    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def _get_collection() -> Any:
    global _client, _collection, _cached_model
    if _collection is not None:
        return _collection

    embedding_fn, model_name = get_embedding_function()
    _cached_model = model_name
    root = _chroma_root()
    _client = chromadb.PersistentClient(path=str(root))
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def _distance_to_score(distance: float) -> float:
    return round(max(0.0, 1.0 - float(distance)), 4)


def get_rag_status() -> Dict[str, Any]:
    """Expose vector index metadata for API / health."""
    meta = _read_meta()
    collection = _get_collection() if settings.rag_enabled else None
    return {
        "enabled": settings.rag_enabled,
        "vector_store": "chromadb",
        "embedding_model": meta.get("embedding_model") or _cached_model,
        "indexed_chunks": collection.count() if collection else 0,
        "chroma_dir": str(_chroma_root()),
        "fingerprint": meta.get("fingerprint"),
    }


def index_knowledge_base(force: bool = False) -> int:
    """Chunk markdown, embed, and upsert into ChromaDB."""
    if not settings.rag_enabled:
        return 0

    chunks = _load_chunks()
    if not chunks:
        return 0

    fingerprint = _knowledge_fingerprint()
    _embedding_fn, model_name = get_embedding_function()
    meta = _read_meta()
    collection = _get_collection()

    up_to_date = (
        not force
        and meta.get("fingerprint") == fingerprint
        and meta.get("embedding_model") == model_name
        and collection.count() == len(chunks)
    )
    if up_to_date:
        return len(chunks)

    collection = _reset_collection()
    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
    )
    _write_meta(
        fingerprint=fingerprint,
        embedding_model=model_name,
        chunk_count=len(chunks),
    )
    return len(chunks)


def rag_search(
    query: str,
    *,
    sources: Optional[List[str]] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Vector search over ChromaDB-indexed knowledge chunks (§13)."""
    if not settings.rag_enabled or not query.strip():
        return []

    index_knowledge_base()
    collection = _get_collection()
    if collection.count() == 0:
        return []

    where: Optional[Dict[str, Any]] = None
    if sources:
        where = {"source": {"$in": sources}}

    results = collection.query(
        query_texts=[query],
        n_results=min(limit, collection.count()),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents") or [[]]
    metadatas = results.get("metadatas") or [[]]
    distances = results.get("distances") or [[]]

    hits: List[Dict[str, Any]] = []
    for document, metadata, distance in zip(documents[0], metadatas[0], distances[0]):
        meta = metadata or {}
        snippet = (document or "").replace("\n", " ")[:400]
        hits.append(
            {
                "source": str(meta.get("source") or ""),
                "document_id": str(meta.get("document_id") or ""),
                "title": str(meta.get("title") or meta.get("document_id") or ""),
                "snippet": snippet,
                "score": _distance_to_score(distance),
                "retrieval_method": "rag",
            }
        )

    hits.sort(key=lambda hit: hit["score"], reverse=True)
    return hits[:limit]
