from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from soil_crop_advisor.api_schemas import RecommendRequest
from soil_crop_advisor.domain.models import Location, SoilSample
from soil_crop_advisor.domain.recommendation_engine import RecommendationEngine
from soil_crop_advisor.domain.repository import InMemoryCatalogRepository
from soil_crop_advisor.service import SCORING_VERSION, build_response


class DemoKarnatakaCatalogTests(unittest.TestCase):
    def test_demo_catalog_ranks_multiple_crops(self) -> None:
        engine = RecommendationEngine(
            repository=InMemoryCatalogRepository.demo_karnataka(),
            scoring_version=SCORING_VERSION,
        )
        response = engine.recommend(
            location=Location(state="Karnataka", district="Tumkur"),
            soil_sample=SoilSample(
                n_value=180.0,
                p_value=24.0,
                k_value=210.0,
                nutrient_basis="N-P-K",
            ),
            season_name="kharif",
        )

        self.assertGreaterEqual(len(response.options), 3)
        self.assertEqual(len(response.heatmap), len(response.options))

    def test_build_response_supports_what_if_offsets(self) -> None:
        payload = RecommendRequest.model_validate(
            {
                "location": {"state": "Karnataka", "district": "Tumkur"},
                "soilSample": {"nValue": 180, "pValue": 24, "kValue": 210, "nutrientBasis": "N-P-K"},
                "season": "kharif",
                "soilNpkOffsets": [
                    {"label": "N-5", "n": -5, "p": 0, "k": 0},
                    {"label": "N+5", "n": 5, "p": 0, "k": 0},
                ],
            }
        )
        api_response = build_response(payload)
        self.assertIsNotNone(api_response.whatIfRuns)
        assert api_response.whatIfRuns is not None
        self.assertEqual(len(api_response.whatIfRuns), 2)


if __name__ == "__main__":
    unittest.main()
