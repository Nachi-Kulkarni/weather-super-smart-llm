-- Optional acceleration for pgvector cosine search on `source_chunk.embedding`.
-- Run after you have enough rows (IVFFLAT benefits from populated data).
-- Requires: CREATE EXTENSION vector;

CREATE INDEX IF NOT EXISTS source_chunk_embedding_ivfflat_idx
  ON source_chunk
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100)
  WHERE embedding IS NOT NULL;
