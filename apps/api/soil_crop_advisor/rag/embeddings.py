from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Sequence

_logger = logging.getLogger(__name__)

# Matches `db/schema.sql` VECTOR(1536) for text-embedding-3-small / compatible models.
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIM = 1536


@lru_cache(maxsize=1)
def _openai_client():
    """Lazy OpenAI client for query embeddings (optional — keyword RAG works without it)."""
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError("Install the `openai` package to enable vector RAG.") from exc

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE") or os.getenv("OPENROUTER_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def embedding_model_name() -> str:
    return os.getenv("RAG_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def embed_query_text(text: str) -> list[float] | None:
    """
    Embed a single user/query string for pgvector similarity.

    Returns None when no API key or embedding fails — callers should fall back to keyword search.
    """
    client = _openai_client()
    if client is None:
        _logger.debug("embed_query_text: no OpenAI-compatible client (set OPENAI_API_KEY)")
        return None

    model = embedding_model_name()
    try:
        response = client.embeddings.create(model=model, input=text[:8000])
        vector = response.data[0].embedding
    except Exception as exc:  # noqa: BLE001
        _logger.warning("embedding request failed: %s", exc)
        return None

    if len(vector) != DEFAULT_EMBEDDING_DIM:
        _logger.warning(
            "embedding dim %s != %s — update schema VECTOR(...) or change model",
            len(vector),
            DEFAULT_EMBEDDING_DIM,
        )
        return None

    return list(vector)


def embed_texts_batch(texts: Sequence[str]) -> list[list[float] | None]:
    """Batch embed for offline ingestion scripts (optional)."""
    client = _openai_client()
    if client is None:
        return [None for _ in texts]

    model = embedding_model_name()
    cleaned = [t[:8000] for t in texts]
    try:
        response = client.embeddings.create(model=model, input=list(cleaned))
    except Exception as exc:  # noqa: BLE001
        _logger.warning("batch embedding failed: %s", exc)
        return [None for _ in texts]

    out: list[list[float] | None] = []
    for item in response.data:
        vec = item.embedding
        out.append(list(vec) if len(vec) == DEFAULT_EMBEDDING_DIM else None)
    return out
