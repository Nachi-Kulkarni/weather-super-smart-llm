#!/usr/bin/env python3
"""
Backfill `source_chunk.embedding` for rows where it is NULL (pgvector).

Usage (from repo root, with DATABASE_URL + OPENAI_API_KEY):

  cd apps/api && .venv/bin/python scripts/backfill_chunk_embeddings.py

Requires: openai package, Postgres with pgvector extension.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from soil_crop_advisor.env import load_repo_env
from soil_crop_advisor.rag.embeddings import embed_texts_batch


def main() -> None:
    load_repo_env()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    from psycopg_pool import ConnectionPool

    pool = ConnectionPool(conninfo=database_url, min_size=1, max_size=2, open=True)
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, chunk_text
                    FROM source_chunk
                    WHERE embedding IS NULL
                    """
                )
                rows = cur.fetchall()
        if not rows:
            print("No rows need embeddings.")
            return

        texts = [str(r[1]) for r in rows]
        vectors = embed_texts_batch(texts)
        with pool.connection() as conn:
            with conn.cursor() as cur:
                for (row_id, _text), vec in zip(rows, vectors, strict=False):
                    if vec is None:
                        continue
                    lit = "[" + ",".join(f"{x:.8f}" for x in vec) + "]"
                    cur.execute(
                        "UPDATE source_chunk SET embedding = %s::vector WHERE id = %s",
                        (lit, row_id),
                    )
            conn.commit()
        print(f"Updated {len(rows)} chunk(s).")
    finally:
        pool.close()


if __name__ == "__main__":
    main()
