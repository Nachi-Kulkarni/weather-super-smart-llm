from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from soil_crop_advisor.domain.models import SoilSample
from soil_crop_advisor.domain.normalization import normalize_soil_sample


class NormalizationTests(unittest.TestCase):
    def test_converts_elemental_basis_to_oxide_basis(self) -> None:
        sample = SoilSample(n_value=120.0, p_value=20.0, k_value=30.0, nutrient_basis="N-P-K")
        normalized = normalize_soil_sample(sample, "N-P2O5-K2O")

        self.assertEqual(normalized.n_value, 120.0)
        self.assertAlmostEqual(normalized.p_value or 0.0, 45.82, places=2)
        self.assertAlmostEqual(normalized.k_value or 0.0, 36.14, places=2)

    def test_converts_oxide_basis_to_elemental_basis(self) -> None:
        sample = SoilSample(n_value=120.0, p_value=45.82, k_value=36.14, nutrient_basis="N-P2O5-K2O")
        normalized = normalize_soil_sample(sample, "N-P-K")

        self.assertEqual(normalized.n_value, 120.0)
        self.assertAlmostEqual(normalized.p_value or 0.0, 20.0, places=1)
        self.assertAlmostEqual(normalized.k_value or 0.0, 30.0, places=1)


if __name__ == "__main__":
    unittest.main()
