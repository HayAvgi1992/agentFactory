"""Markdown chunking for local RAG — vision §13."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List


def chunk_markdown(text: str, document_id: str, source: str) -> List[dict]:
    """Split markdown into section chunks with metadata."""
    sections = re.split(r"\n(?=#+\s)", text.strip())
    chunks: List[dict] = []
    for index, section in enumerate(sections):
        body = section.strip()
        if not body:
            continue
        title_match = re.match(r"^#+\s*(.+)", body)
        title = title_match.group(1).strip() if title_match else document_id
        chunks.append(
            {
                "id": f"{source}:{document_id}:{index}",
                "text": body,
                "metadata": {
                    "source": source,
                    "document_id": document_id,
                    "title": title,
                    "chunk_index": index,
                },
            }
        )
    if not chunks and text.strip():
        chunks.append(
            {
                "id": f"{source}:{document_id}:0",
                "text": text.strip(),
                "metadata": {
                    "source": source,
                    "document_id": document_id,
                    "title": document_id,
                    "chunk_index": 0,
                },
            }
        )
    return chunks


def chunk_knowledge_file(path: Path, source: str) -> List[dict]:
    text = path.read_text(encoding="utf-8")
    return chunk_markdown(text, path.stem, source)
