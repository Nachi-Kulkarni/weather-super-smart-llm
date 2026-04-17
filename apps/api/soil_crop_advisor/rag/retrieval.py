from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from psycopg_pool import ConnectionPool

from .embeddings import embed_query_text

_logger = logging.getLogger(__name__)

_psql_available = True
try:
    from psycopg_pool import ConnectionPool
except ImportError:
    ConnectionPool = None
    _psql_available = False

RRF_K = 60

MatchMode = Literal["keyword", "vector", "hybrid"]


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    source_doc_id: str
    title: str
    chunk_type: str
    chunk_text: str
    crop_tags: tuple[str, ...]
    match_type: MatchMode | str = "keyword"
    score: float | None = None


def _tokenize(query: str) -> list[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", " ", query.lower()).strip()
    return [token for token in cleaned.split() if len(token) > 2]


def _row_to_tuple(row: Any) -> tuple[Any, ...]:
    return tuple(row)


def _fetch_keyword_rows(
    conn: Any,
    *,
    query: str,
    state_name: str | None,
    crop_codes: list[str],
    limit: int,
) -> list[tuple[Any, ...]]:
    tokens = _tokenize(query) or ["crop"]
    like_clauses: list[str] = []
    params: list[Any] = []
    for token in tokens[:6]:
        like_clauses.append("sc.chunk_text ILIKE %s")
        params.append(f"%{token}%")

    crop_filters = ""
    if crop_codes:
        crop_filters = "AND sc.crop_tags && %s::text[]"
        params.append(crop_codes)

    state_filter = ""
    if state_name:
        state_filter = "AND (sc.state_name IS NULL OR sc.state_name ILIKE %s)"
        params.append(state_name)

    where_sql = " AND ".join(like_clauses) if like_clauses else "TRUE"

    # Param order must match SQL placeholders: ILIKE params, then crop `&&`, then state ILIKE, then LIMIT.
    # (Previously state was listed before crop while params appended crop first — Postgres then bound
    # a string to `text[]`, causing "malformed array literal".)
    sql = f"""
        SELECT sc.id,
               sc.source_doc_id,
               sd.title,
               sc.chunk_type,
               sc.chunk_text,
               sc.crop_tags
        FROM source_chunk sc
        JOIN source_document sd ON sd.id = sc.source_doc_id
        WHERE ({where_sql})
        {crop_filters}
        {state_filter}
        ORDER BY sd.title ASC, sc.chunk_type ASC
        LIMIT %s
    """
    params.append(limit)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def _fetch_vector_rows(
    conn: Any,
    *,
    embedding: list[float],
    state_name: str | None,
    crop_codes: list[str],
    limit: int,
) -> list[tuple[Any, ...]]:
    """Cosine distance via pgvector — lower `<=>` is better; we attach `1 - dist` as similarity."""
    state_filter = ""
    crop_filters = ""
    extra: list[Any] = []
    if state_name:
        state_filter = "AND (sc.state_name IS NULL OR sc.state_name ILIKE %s)"
        extra.append(state_name)
    if crop_codes:
        crop_filters = "AND sc.crop_tags && %s::text[]"
        extra.append(crop_codes)

    vec_literal = "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"
    sql = f"""
        SELECT sc.id,
               sc.source_doc_id,
               sd.title,
               sc.chunk_type,
               sc.chunk_text,
               sc.crop_tags,
               (1 - (sc.embedding <=> %s::vector)) AS sim
        FROM source_chunk sc
        JOIN source_document sd ON sd.id = sc.source_doc_id
        WHERE sc.embedding IS NOT NULL
        {state_filter}
        {crop_filters}
        ORDER BY sc.embedding <=> %s::vector
        LIMIT %s
    """
    params = [vec_literal, *extra, vec_literal, limit]
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def _rrf_hybrid(
    keyword_rows: list[tuple[Any, ...]],
    vector_rows: list[tuple[Any, ...]],
    *,
    limit: int,
) -> list[tuple[tuple[Any, ...], float]]:
    """Fuse two ranked lists with reciprocal rank fusion scores (higher is better)."""
    scores: dict[str, float] = {}
    row_map: dict[str, tuple[Any, ...]] = {}

    for rank, row in enumerate(keyword_rows):
        cid = str(row[0])
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
        row_map[cid] = row[:6]

    for rank, row in enumerate(vector_rows):
        cid = str(row[0])
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
        row_map.setdefault(cid, row[:6])

    ordered_ids = sorted(scores.keys(), key=lambda i: scores[i], reverse=True)[:limit]
    return [(row_map[cid], scores[cid]) for cid in ordered_ids]


def retrieve_chunks(
    pool: ConnectionPool | None,
    *,
    query: str,
    state_name: str | None,
    crop_codes: list[str],
    limit: int = 8,
    mode: MatchMode = "hybrid",
) -> list[RetrievedChunk]:
    """
    RAG retrieval:
    - keyword: ILIKE token search (no embeddings required)
    - vector: pgvector cosine on `source_chunk.embedding` (requires populated embeddings + OPENAI_API_KEY)
    - hybrid: RRF fusion of keyword + vector rankings (falls back if vector path unavailable)
    """
    if pool is None:
        return []

    query_vec = embed_query_text(query) if mode in {"vector", "hybrid"} else None
    if mode == "vector" and query_vec is None:
        _logger.info("vector mode requested but embedding unavailable — falling back to keyword")
        mode = "keyword"

    with pool.connection() as conn:
        keyword_rows = _fetch_keyword_rows(
            conn,
            query=query,
            state_name=state_name,
            crop_codes=crop_codes,
            limit=max(limit * 3, 24),
        )

        vector_rows: list[tuple[Any, ...]] = []
        if mode in {"vector", "hybrid"} and query_vec is not None:
            try:
                vector_rows = _fetch_vector_rows(
                    conn,
                    embedding=query_vec,
                    state_name=state_name,
                    crop_codes=crop_codes,
                    limit=max(limit * 3, 24),
                )
            except Exception as exc:  # noqa: BLE001
                _logger.warning("vector retrieval failed, using keyword only: %s", exc)
                vector_rows = []

        merged_pack: list[tuple[tuple[Any, ...], str, float | None]] = []

        if mode == "keyword" or (mode in {"vector", "hybrid"} and query_vec is None):
            for row in keyword_rows[:limit]:
                merged_pack.append((row[:6], "keyword", None))
        elif mode == "vector" and vector_rows:
            for row in vector_rows[:limit]:
                sim = float(row[6]) if len(row) > 6 else None
                merged_pack.append((row[:6], "vector", sim))
        elif mode == "hybrid" and vector_rows:
            for row_tuple, rrf_score in _rrf_hybrid(keyword_rows, vector_rows, limit=limit):
                merged_pack.append((row_tuple, "hybrid", rrf_score))
        else:
            for row in keyword_rows[:limit]:
                merged_pack.append((row[:6], "keyword", None))

    results: list[RetrievedChunk] = []
    for row, mtype, sim in merged_pack[:limit]:
        chunk_id, source_doc_id, title, chunk_type, chunk_text, crop_tags = row
        tags = tuple(str(tag) for tag in (crop_tags or []))
        results.append(
            RetrievedChunk(
                chunk_id=str(chunk_id),
                source_doc_id=str(source_doc_id),
                title=str(title),
                chunk_type=str(chunk_type),
                chunk_text=str(chunk_text),
                crop_tags=tags,
                match_type=mtype,
                score=sim,
            )
        )

    _logger.info("rag retrieval: mode=%s chunks=%s", mode, len(results))
    return results
