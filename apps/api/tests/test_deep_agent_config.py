from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from soil_crop_advisor.deep_agent import (
    DEFAULT_OPENROUTER_BASE_URL,
    configure_provider_environment,
    resolve_model_name,
)


class DeepAgentConfigTests(unittest.TestCase):
    def test_defaults_to_openrouter_workflow_when_key_is_present(self) -> None:
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=True):
            self.assertEqual(resolve_model_name(), "openai:minimax/minimax-m2.7")

    def test_normalizes_openrouter_model_without_provider_prefix(self) -> None:
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "test-key",
                "SOIL_CROP_ADVISOR_MODEL": "minimax/minimax-m2.7",
            },
            clear=True,
        ):
            self.assertEqual(resolve_model_name(), "openai:minimax/minimax-m2.7")

    def test_preserves_explicit_provider_prefixed_model(self) -> None:
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "test-key",
                "SOIL_CROP_ADVISOR_MODEL": "openai:gpt-4.1-mini",
            },
            clear=True,
        ):
            self.assertEqual(resolve_model_name(), "openai:gpt-4.1-mini")

    def test_maps_openrouter_env_to_openai_compatible_env_vars(self) -> None:
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "test-key",
            },
            clear=True,
        ):
            configure_provider_environment()
            self.assertEqual(os.environ["OPENAI_API_KEY"], "test-key")
            self.assertEqual(os.environ["OPENAI_API_BASE"], DEFAULT_OPENROUTER_BASE_URL)
            self.assertEqual(os.environ["OPENAI_BASE_URL"], DEFAULT_OPENROUTER_BASE_URL)


if __name__ == "__main__":
    unittest.main()
