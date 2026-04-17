from __future__ import annotations

from dataclasses import dataclass

from .models import EquationRule, SoilSample
from .normalization import normalize_soil_sample


@dataclass(frozen=True)
class FertilizerRecommendation:
    recommended_n: float | None
    recommended_p: float | None
    recommended_k: float | None
    nutrient_basis: str
    trace: dict[str, float | str | None]


def _calculate_nutrient_dose(
    target_yield: float,
    soil_test_value: float | None,
    nutrient_requirement: float | None,
    contribution_from_soil: float | None,
    contribution_from_fertilizer: float | None,
    organic_contribution: float = 0.0,
    contribution_from_organic: float | None = None,
) -> float | None:
    if soil_test_value is None:
        return None
    if nutrient_requirement is None or contribution_from_soil is None or contribution_from_fertilizer in (None, 0):
        return None

    fertilizer_term = (nutrient_requirement * 100.0 / contribution_from_fertilizer) * target_yield
    soil_credit = (contribution_from_soil / contribution_from_fertilizer) * soil_test_value
    organic_credit = 0.0
    if contribution_from_organic and organic_contribution:
        organic_credit = (contribution_from_organic / contribution_from_fertilizer) * organic_contribution

    return round(max(0.0, fertilizer_term - soil_credit - organic_credit), 4)


def calculate_fertilizer_recommendation(
    rule: EquationRule,
    soil_sample: SoilSample,
    target_yield: float,
    organic_contributions: dict[str, float] | None = None,
) -> FertilizerRecommendation:
    organic_contributions = organic_contributions or {}
    normalized_sample = normalize_soil_sample(soil_sample, rule.nutrient_basis)

    recommended_n = _calculate_nutrient_dose(
        target_yield=target_yield,
        soil_test_value=normalized_sample.n_value,
        nutrient_requirement=rule.nr_n,
        contribution_from_soil=rule.cs_n,
        contribution_from_fertilizer=rule.cf_n,
        organic_contribution=organic_contributions.get("N", 0.0),
        contribution_from_organic=rule.c_org_n,
    )
    recommended_p = _calculate_nutrient_dose(
        target_yield=target_yield,
        soil_test_value=normalized_sample.p_value,
        nutrient_requirement=rule.nr_p,
        contribution_from_soil=rule.cs_p,
        contribution_from_fertilizer=rule.cf_p,
        organic_contribution=organic_contributions.get("P", 0.0),
        contribution_from_organic=rule.c_org_p,
    )
    recommended_k = _calculate_nutrient_dose(
        target_yield=target_yield,
        soil_test_value=normalized_sample.k_value,
        nutrient_requirement=rule.nr_k,
        contribution_from_soil=rule.cs_k,
        contribution_from_fertilizer=rule.cf_k,
        organic_contribution=organic_contributions.get("K", 0.0),
        contribution_from_organic=rule.c_org_k,
    )

    trace = {
        "targetYield": target_yield,
        "nutrientBasis": rule.nutrient_basis,
        "soilN": normalized_sample.n_value,
        "soilP": normalized_sample.p_value,
        "soilK": normalized_sample.k_value,
        "recommendedN": recommended_n,
        "recommendedP": recommended_p,
        "recommendedK": recommended_k,
    }
    return FertilizerRecommendation(
        recommended_n=recommended_n,
        recommended_p=recommended_p,
        recommended_k=recommended_k,
        nutrient_basis=rule.nutrient_basis,
        trace=trace,
    )
