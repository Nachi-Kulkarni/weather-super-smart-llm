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
    def test_stcr_reference_ranks_multiple_crops(self) -> None:
        engine = RecommendationEngine(
            repository=InMemoryCatalogRepository.stcr_reference(),
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


if __name__ == "__main__":
    unittest.main()
