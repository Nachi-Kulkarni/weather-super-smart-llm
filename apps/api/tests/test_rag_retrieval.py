"""Regression + integration checks for RAG retrieval (Postgres optional)."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from soil_crop_advisor.env import load_repo_env

load_repo_env()


@unittest.skipUnless(os.getenv("DATABASE_URL"), "DATABASE_URL not set — skip Postgres RAG tests")
class RagRetrievalIntegrationTests(unittest.TestCase):
    """Run against local seed data (see `db/seed.sql`) when DATABASE_URL is configured."""

    @classmethod
    def setUpClass(cls) -> None:
        load_repo_env()

    def test_keyword_retrieval_does_not_confuse_state_with_text_array(self) -> None:
        """Crop tag + state filters used to mis-bind params (malformed array literal)."""
        from soil_crop_advisor.db.pool import close_pool, get_pool
        from soil_crop_advisor.rag.retrieval import retrieve_chunks

        pool = get_pool()
        self.assertIsNotNone(pool)
        chunks = retrieve_chunks(
            pool,
            query="rice kharif fertilizer",
            state_name="Karnataka",
            crop_codes=["rice"],
            limit=4,
            mode="keyword",
        )
        self.assertGreaterEqual(len(chunks), 1)
        self.assertEqual(chunks[0].match_type, "keyword")
        close_pool()


if __name__ == "__main__":
    unittest.main()
