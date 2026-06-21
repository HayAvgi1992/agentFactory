"""Embedding providers for ChromaDB — vision §13."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from chromadb.api.types import EmbeddingFunction

from app.config import settings

COLLECTION_NAME = "gtm_knowledge"


def get_embedding_function() -> Tuple[EmbeddingFunction, str]:
    """OpenAI embeddings when keyed; otherwise local ONNX all-MiniLM-L6-v2."""
    if settings.openai_api_key:
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

        model = settings.embedding_model
        return (
            OpenAIEmbeddingFunction(
                api_key=settings.openai_api_key,
                model_name=model,
            ),
            model,
        )

    from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2

    cache_root = Path(settings.chroma_dir) / "onnx_models"
    cache_root.mkdir(parents=True, exist_ok=True)
    ONNXMiniLM_L6_V2.DOWNLOAD_PATH = cache_root / ONNXMiniLM_L6_V2.MODEL_NAME
    return ONNXMiniLM_L6_V2(), ONNXMiniLM_L6_V2.MODEL_NAME
