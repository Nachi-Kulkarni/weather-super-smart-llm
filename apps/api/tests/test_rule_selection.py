from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from soil_crop_advisor.domain.models import EquationRule, Location
from soil_crop_advisor.domain.rule_selector import select_best_rule


class RuleSelectionTests(unittest.TestCase):
    def test_prefers_district_scope_over_state_scope(self) -> None:
        location = Location(state="Karnataka", district="Tumkur", agro_region_code="AER-12")
        rules = [
            EquationRule(
                crop_code="maize",
                equation_family="STCR",
                geography_scope="state",
                state_name="Karnataka",
                nutrient_basis="N-P2O5-K2O",
                target_yield_unit="q/ha",
            ),
            EquationRule(
                crop_code="maize",
                equation_family="STCR",
                geography_scope="district",
                state_name="Karnataka",
                district_name="Tumkur",
                nutrient_basis="N-P2O5-K2O",
                target_yield_unit="q/ha",
            ),
        ]

        selection = select_best_rule("maize", location, "kharif", rules)

        self.assertIsNotNone(selection.selected_rule)
        self.assertEqual(selection.selected_rule.geography_scope, "district")


if __name__ == "__main__":
    unittest.main()
