from __future__ import annotations

from dataclasses import dataclass

from .models import EquationRule, WeatherProfile


@dataclass(frozen=True)
class ScoreBreakdown:
    nutrient_fit_score: float
    weather_feasibility_score: float
    agro_region_fit_score: float
    local_adoption_score: float
    market_signal_score: float
    input_burden_score: float
    season_suitability_score: float
    final_score: float
    trace: dict[str, float]


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def compute_weather_score(weather: WeatherProfile | None) -> float:
    if weather is None:
        return 0.5

    scores = [score for score in (weather.short_range_score, weather.seasonal_prior_score) if score is not None]
    if not scores:
        return 0.5

    if len(scores) == 1:
        return clamp01(scores[0])

    return clamp01((scores[0] * 0.6) + (scores[1] * 0.4))


def compute_agro_region_score(rule: EquationRule) -> float:
    if rule.geography_scope == "district":
        return 1.0
    if rule.geography_scope == "state":
        return 0.85
    if rule.geography_scope == "agro_region":
        return 0.75
    return 0.6


def compute_confidence_band(rule: EquationRule) -> str:
    if rule.equation_family in {"STCR", "STCR_IPNS"} and rule.geography_scope == "district":
        return "A"
    if rule.equation_family in {"STCR", "STCR_IPNS"}:
        return "B"
    return rule.confidence_band


def compute_scores(
    recommended_n: float | None,
    recommended_p: float | None,
    recommended_k: float | None,
    rule: EquationRule,
    weather: WeatherProfile | None,
    local_adoption_score: float,
    market_signal_score: float,
    season_suitability_score: float = 0.8,
) -> ScoreBreakdown:
    total_input = sum(value or 0.0 for value in (recommended_n, recommended_p, recommended_k))
    input_burden_score = clamp01(1.0 - (total_input / 400.0))
    nutrient_fit_score = clamp01(1.0 - (total_input / 500.0))
    weather_feasibility_score = compute_weather_score(weather)
    agro_region_fit_score = compute_agro_region_score(rule)
    local_adoption_score = clamp01(local_adoption_score)
    market_signal_score = clamp01(market_signal_score)
    season_suitability_score = clamp01(season_suitability_score)

    # Rebalanced weights: less nutrient dominance, season suitability added
    final_score = clamp01(
        (0.30 * nutrient_fit_score)
        + (0.20 * weather_feasibility_score)
        + (0.15 * season_suitability_score)
        + (0.12 * agro_region_fit_score)
        + (0.10 * local_adoption_score)
        + (0.08 * market_signal_score)
        + (0.05 * input_burden_score)
    )

    return ScoreBreakdown(
        nutrient_fit_score=nutrient_fit_score,
        weather_feasibility_score=weather_feasibility_score,
        agro_region_fit_score=agro_region_fit_score,
        local_adoption_score=local_adoption_score,
        market_signal_score=market_signal_score,
        input_burden_score=input_burden_score,
        season_suitability_score=season_suitability_score,
        final_score=final_score,
        trace={
            "nutrientFitScore": nutrient_fit_score,
            "weatherFeasibilityScore": weather_feasibility_score,
            "agroRegionFitScore": agro_region_fit_score,
            "localAdoptionScore": local_adoption_score,
            "marketSignalScore": market_signal_score,
            "inputBurdenScore": input_burden_score,
            "seasonSuitabilityScore": season_suitability_score,
            "finalScore": final_score,
        },
    )
