from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


NutrientBasis = Literal["N-P-K", "N-P2O5-K2O"]
ConfidenceBand = Literal["A", "B", "C"]
GeographyScope = Literal["district", "state", "agro_region", "national"]


@dataclass(frozen=True)
class Location:
    state: str | None = None
    district: str | None = None
    agro_region_code: str | None = None
    lat: float | None = None
    lon: float | None = None


@dataclass(frozen=True)
class SoilSample:
    n_value: float | None = None
    p_value: float | None = None
    k_value: float | None = None
    ph_value: float | None = None
    ec_value: float | None = None
    oc_value: float | None = None
    nutrient_basis: NutrientBasis = "N-P-K"
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WeatherProfile:
    short_range_score: float | None = None
    seasonal_prior_score: float | None = None
    source_name: str | None = None
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CropMetadata:
    crop_code: str
    crop_name: str
    crop_group: str | None = None
    default_target_yield_value: float | None = None
    default_target_yield_unit: str | None = "q/ha"
    season_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class EquationRule:
    crop_code: str
    equation_family: str
    geography_scope: GeographyScope
    nutrient_basis: NutrientBasis
    target_yield_unit: str
    state_name: str | None = None
    district_name: str | None = None
    agro_region_code: str | None = None
    soil_order: str | None = None
    season_name: str | None = None
    confidence_band: ConfidenceBand = "A"
    nr_n: float | None = None
    nr_p: float | None = None
    nr_k: float | None = None
    cs_n: float | None = None
    cs_p: float | None = None
    cs_k: float | None = None
    cf_n: float | None = None
    cf_p: float | None = None
    cf_k: float | None = None
    c_org_n: float | None = None
    c_org_p: float | None = None
    c_org_k: float | None = None
    source_doc_id: str | None = None
    source_title: str | None = None
    citation_text: str | None = None


@dataclass(frozen=True)
class CitationRef:
    source_doc_id: str
    title: str
    snippet: str | None = None


@dataclass(frozen=True)
class RecommendationOption:
    crop_id: str
    crop_name: str
    rank: int
    target_yield_value: float | None
    target_yield_unit: str | None
    recommended_n: float | None
    recommended_p: float | None
    recommended_k: float | None
    nutrient_basis: NutrientBasis
    nutrient_fit_score: float
    weather_feasibility_score: float
    agro_region_fit_score: float
    local_adoption_score: float
    market_signal_score: float
    input_burden_score: float
    season_suitability_score: float
    final_score: float
    confidence_band: ConfidenceBand
    reasons: list[str]
    cautions: list[str]
    citations: list[CitationRef]
    trace_payload: dict[str, Any]


@dataclass(frozen=True)
class HeatmapCell:
    crop_id: str
    crop_name: str
    delta_n: float | None
    delta_p: float | None
    delta_k: float | None
    score: float
    confidence_band: ConfidenceBand


@dataclass(frozen=True)
class RejectedCrop:
    crop_name: str
    reason: str


@dataclass(frozen=True)
class RecommendationResponse:
    run_id: str
    scoring_version: str
    location: Location
    soil_sample_payload: dict[str, Any]
    options: list[RecommendationOption]
    heatmap: list[HeatmapCell]
    rejected_crops: list[RejectedCrop]
