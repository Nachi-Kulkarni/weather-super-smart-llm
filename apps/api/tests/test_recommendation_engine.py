from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from soil_crop_advisor.domain.models import CropMetadata, EquationRule, Location, SoilSample
from soil_crop_advisor.domain.recommendation_engine import RecommendationEngine
from soil_crop_advisor.domain.repository import InMemoryCatalogRepository


class RecommendationEngineTests(unittest.TestCase):
    def test_generates_ranked_option_with_trace(self) -> None:
        repository = InMemoryCatalogRepository(
            crops=[
                CropMetadata(
                    crop_code="wheat",
                    crop_name="Wheat",
                    default_target_yield_value=50.0,
                    default_target_yield_unit="q/ha",
                )
            ],
            rules=[
                EquationRule(
                    crop_code="wheat",
                    equation_family="TEST_SYNTHETIC",
                    geography_scope="state",
                    state_name="Punjab",
                    nutrient_basis="N-P2O5-K2O",
                    target_yield_unit="q/ha",
                    confidence_band="C",
                    nr_n=2.0,
                    nr_p=1.0,
                    nr_k=1.0,
                    cs_n=50.0,
                    cs_p=25.0,
                    cs_k=20.0,
                    cf_n=50.0,
                    cf_p=50.0,
                    cf_k=50.0,
                    source_doc_id="fixture-doc",
                    source_title="Synthetic test fixture",
                    citation_text="Synthetic coefficients for deterministic engine tests only.",
                )
            ],
        )
        engine = RecommendationEngine(repository=repository, scoring_version="test-version")

        response = engine.recommend(
            location=Location(state="Punjab", district="Ludhiana"),
            soil_sample=SoilSample(
                n_value=80.0,
                p_value=40.0,
                k_value=50.0,
                nutrient_basis="N-P2O5-K2O",
            ),
            season_name="rabi",
        )

        self.assertEqual(len(response.options), 1)
        option = response.options[0]
        self.assertEqual(option.crop_id, "wheat")
        self.assertEqual(option.rank, 1)
        self.assertEqual(option.confidence_band, "C")
        self.assertEqual(option.recommended_n, 120.0)
        self.assertEqual(option.recommended_p, 80.0)
        self.assertEqual(option.recommended_k, 80.0)
        self.assertIn("selectedRule", option.trace_payload)
        self.assertEqual(option.citations[0].source_doc_id, "fixture-doc")


if __name__ == "__main__":
    unittest.main()
