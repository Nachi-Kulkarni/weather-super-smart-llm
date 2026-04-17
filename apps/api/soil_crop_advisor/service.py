from __future__ import annotations

import logging
from typing import Any

from .api_schemas import (
    ChatRequest,
    ChatResponse,
    RecommendationResponseModel,
    RecommendRequest,
    ToolEventModel,
    SoilSampleInput,
    SoilNpkOffset,
    WhatIfScenarioModel,
)
from .db import get_pool
from .db.pg_repository import PgCatalogRepository
from .domain.models import Location, SoilSample, WeatherProfile
from .domain.recommendation_engine import RecommendationEngine
from .domain.repository import CatalogRepository, InMemoryCatalogRepository
from .integrations.imd_live import fetch_imd_best_effort
from .integrations.open_meteo import fetch_forecast_series
from .integrations.weather_scores import build_weather_profile_from_open_meteo
from .rag.retrieval import retrieve_chunks

_logger = logging.getLogger(__name__)

SCORING_VERSION = "2026-04-10-starter"

_repository: CatalogRepository | None = None
_engine: RecommendationEngine | None = None
_stcr_ref_repo: CatalogRepository | None = None


def get_repository() -> CatalogRepository:
    """Prefer Postgres when `DATABASE_URL` is set; returns empty catalog if no DB and no STCR match."""
    global _repository
    if _repository is None:
        pool = get_pool()
        if pool is not None:
            _repository = PgCatalogRepository(pool)
            _logger.info("catalog repository: postgres")
        else:
            _repository = InMemoryCatalogRepository.empty()
            _logger.info("catalog repository: empty (set DATABASE_URL for Postgres, or ingest STCR data)")
    return _repository


def get_stcr_reference_repository() -> CatalogRepository:
    """Get STCR reference data for Karnataka (UAS Bangalore 2022-2026).

    Use this only when:
    - Location is Karnataka AND district is one of Tumkur, Shimoga, Hassan, Chikmagalur
    - Need to demonstrate STCR structure/coefficients
    - NOT for production use
    """
    global _stcr_ref_repo
    if _stcr_ref_repo is None:
        _stcr_ref_repo = InMemoryCatalogRepository.stcr_reference()
        _logger.info("catalog repository: STCR Karnataka reference only")
    return _stcr_ref_repo


def get_engine() -> RecommendationEngine:
    global _engine
    if _engine is None:
        _engine = RecommendationEngine(repository=get_repository(), scoring_version=SCORING_VERSION)
    return _engine


def _weather_to_api(profile: WeatherProfile | None) -> dict[str, Any] | None:
    if profile is None:
        return None
    return {
        "shortRangeScore": profile.short_range_score,
        "seasonalPriorScore": profile.seasonal_prior_score,
        "sourceName": profile.source_name,
        "notes": list(profile.notes),
    }


def _open_meteo_profile(lat: float, lon: float) -> WeatherProfile:
    try:
        series = fetch_forecast_series(lat, lon)
        return build_weather_profile_from_open_meteo(series)
    except Exception as exc:  # noqa: BLE001
        _logger.warning("open-meteo fetch failed: %s", exc)
        return WeatherProfile(
            short_range_score=None,
            seasonal_prior_score=None,
            source_name="OpenMeteo",
            notes=(f"Open-Meteo fetch failed: {exc}",),
        )


def _imd_profile(lat: float, lon: float) -> tuple[WeatherProfile, bool]:
    """Return (profile, ok) where ok means JSON was retrieved (hints may still be heuristic)."""
    result = fetch_imd_best_effort(lat, lon)
    if result.ok:
        return (
            WeatherProfile(
                short_range_score=result.short_range_hint,
                seasonal_prior_score=result.seasonal_hint,
                source_name="IMD",
                notes=result.notes
                + (
                    "IMD live JSON received — confirm field mapping against mausam.imd.gov.in schema for production.",
                ),
            ),
            True,
        )
    return (
        WeatherProfile(
            short_range_score=None,
            seasonal_prior_score=None,
            source_name="IMD",
            notes=result.notes,
        ),
        False,
    )


def _merge_imd_open_meteo(imd: WeatherProfile, om: WeatherProfile) -> WeatherProfile:
    return WeatherProfile(
        short_range_score=imd.short_range_score or om.short_range_score,
        seasonal_prior_score=om.seasonal_prior_score or imd.seasonal_prior_score,
        source_name="IMD+OpenMeteo",
        notes=tuple(
            dict.fromkeys(
                (
                    "Merged: IMD (authoritative India source when reachable) + Open-Meteo seasonal prior.",
                    *imd.notes,
                    *om.notes,
                )
            )
        ),
    )


def resolve_weather(request: RecommendRequest) -> WeatherProfile | None:
    """Combine optional IMD / Open-Meteo fetches with explicit API weather overrides."""
    auto: WeatherProfile | None = None
    if request.fetchWeather and request.location.lat is not None and request.location.lon is not None:
        lat_f = float(request.location.lat)
        lon_f = float(request.location.lon)
        provider = request.weatherProvider
        om = _open_meteo_profile(lat_f, lon_f)

        if provider == "open_meteo":
            auto = om
        elif provider == "imd":
            imd_prof, ok = _imd_profile(lat_f, lon_f)
            if ok:
                auto = imd_prof
            else:
                auto = WeatherProfile(
                    short_range_score=om.short_range_score,
                    seasonal_prior_score=om.seasonal_prior_score,
                    source_name="OpenMeteo",
                    notes=om.notes
                    + ("IMD endpoints did not return usable JSON — Open-Meteo scores used instead.",)
                    + imd_prof.notes,
                )
        else:  # both
            imd_prof, ok = _imd_profile(lat_f, lon_f)
            if ok:
                auto = _merge_imd_open_meteo(imd_prof, om)
            else:
                auto = _merge_imd_open_meteo(
                    WeatherProfile(
                        short_range_score=None,
                        seasonal_prior_score=None,
                        source_name="IMD",
                        notes=imd_prof.notes,
                    ),
                    om,
                )

    if request.weather is None:
        return auto

    manual = request.weather
    base = auto
    return WeatherProfile(
        short_range_score=manual.shortRangeScore
        if manual.shortRangeScore is not None
        else (base.short_range_score if base else None),
        seasonal_prior_score=manual.seasonalPriorScore
        if manual.seasonalPriorScore is not None
        else (base.seasonal_prior_score if base else None),
        source_name=manual.sourceName or (base.source_name if base else None),
        notes=tuple(dict.fromkeys((*tuple(manual.notes), *((base.notes if base else ()))))),
    )


def _soil_domain_from_input(sample: SoilSampleInput) -> SoilSample:
    return SoilSample(
        n_value=sample.nValue,
        p_value=sample.pValue,
        k_value=sample.kValue,
        ph_value=sample.phValue,
        ec_value=sample.ecValue,
        oc_value=sample.ocValue,
        nutrient_basis=sample.nutrientBasis,
        extras=dict(sample.extras),
    )


def _apply_soil_offset(sample: SoilSampleInput, offset: SoilNpkOffset) -> SoilSample:
    base = _soil_domain_from_input(sample)
    return SoilSample(
        n_value=(base.n_value + offset.n) if base.n_value is not None else None,
        p_value=(base.p_value + offset.p) if base.p_value is not None else None,
        k_value=(base.k_value + offset.k) if base.k_value is not None else None,
        ph_value=base.ph_value,
        ec_value=base.ec_value,
        oc_value=base.oc_value,
        nutrient_basis=base.nutrient_basis,
        extras=dict(base.extras),
    )


def _domain_to_response(domain: RecommendationResponse) -> dict[str, Any]:
    return {
        "runId": domain.run_id,
        "scoringVersion": domain.scoring_version,
        "location": {
            "state": domain.location.state,
            "district": domain.location.district,
            "lat": domain.location.lat,
            "lon": domain.location.lon,
        },
        "soilSample": domain.soil_sample_payload,
        "options": [
            {
                "cropId": option.crop_id,
                "cropName": option.crop_name,
                "rank": option.rank,
                "targetYieldValue": option.target_yield_value,
                "targetYieldUnit": option.target_yield_unit,
                "recommendedN": option.recommended_n,
                "recommendedP": option.recommended_p,
                "recommendedK": option.recommended_k,
                "nutrientBasis": option.nutrient_basis,
                "nutrientFitScore": option.nutrient_fit_score,
                "weatherFeasibilityScore": option.weather_feasibility_score,
                "agroRegionFitScore": option.agro_region_fit_score,
                "localAdoptionScore": option.local_adoption_score,
                "marketSignalScore": option.market_signal_score,
                "inputBurdenScore": option.input_burden_score,
                "seasonSuitabilityScore": option.season_suitability_score,
                "finalScore": option.final_score,
                "confidenceBand": option.confidence_band,
                "reasons": option.reasons,
                "cautions": option.cautions,
                "citations": [
                    {
                        "sourceDocId": citation.source_doc_id,
                        "title": citation.title,
                        "snippet": citation.snippet,
                    }
                    for citation in option.citations
                ],
                "tracePayload": option.trace_payload,
            }
            for option in domain.options
        ],
        "heatmap": [
            {
                "cropId": cell.crop_id,
                "cropName": cell.crop_name,
                "deltaN": cell.delta_n,
                "deltaP": cell.delta_p,
                "deltaK": cell.delta_k,
                "score": cell.score,
                "confidenceBand": cell.confidence_band,
            }
            for cell in domain.heatmap
        ],
        "rejectedCrops": [
            {
                "cropName": rejected.crop_name,
                "reason": rejected.reason,
            }
            for rejected in domain.rejected_crops
        ],
    }


def build_response(request: RecommendRequest) -> RecommendationResponseModel:
    weather = resolve_weather(request)

    is_karnataka_stcr_district = (
        request.location.state and request.location.state.lower() == "karnataka"
        and request.location.district
        and request.location.district.lower() in ("tumkur", "shimoga", "hassan", "chikmagalur")
    )

    if is_karnataka_stcr_district:
        engine = RecommendationEngine(
            repository=get_stcr_reference_repository(),
            scoring_version=SCORING_VERSION,
        )
    else:
        engine = get_engine()
        if request.location.state and request.location.state.lower() == "karnataka":
            _logger.info(
                "Karnataka location '%s' not in STCR reference district; using universal fallback",
                request.location.district,
            )

    domain = engine.recommend(
        location=Location(
            state=request.location.state,
            district=request.location.district,
            agro_region_code=request.location.agroRegionCode,
            lat=request.location.lat,
            lon=request.location.lon,
        ),
        soil_sample=_soil_domain_from_input(request.soilSample),
        season_name=request.season,
        target_yield_value=request.targetYieldValue,
        target_yield_unit=request.targetYieldUnit,
        candidate_crop_codes=list(request.candidateCropCodes),
        weather=weather,
        local_adoption_overrides=dict(request.localAdoptionOverrides),
        market_signal_overrides=dict(request.marketSignalOverrides),
        organic_contributions=dict(request.organicContributions),
    )

    retrieval_models: list[RetrievalChunkModel] | None = None
    if request.includeRetrieval:
        pool = get_pool()
        query = request.retrievalQuery or f"{request.season} {request.location.state or ''} fertilizer recommendation"
        crops = list(request.candidateCropCodes) or [opt.crop_id for opt in domain.options]
        chunks = retrieve_chunks(
            pool,
            query=query,
            state_name=request.location.state,
            crop_codes=crops,
            limit=8,
            mode=request.ragMode,
        )
        retrieval_models = [
            RetrievalChunkModel(
                chunkId=chunk.chunk_id,
                sourceDocId=chunk.source_doc_id,
                title=chunk.title,
                chunkType=chunk.chunk_type,
                chunkText=chunk.chunk_text,
                cropTags=list(chunk.crop_tags),
                matchType=chunk.match_type
                if chunk.match_type in ("keyword", "vector", "hybrid")
                else None,
                score=chunk.score,
            )
            for chunk in chunks
        ]

    what_if_models: list[WhatIfScenarioModel] | None = None
    if request.soilNpkOffsets:
        what_if_models = []
        for offset in request.soilNpkOffsets[:24]:
            shifted = get_engine().recommend(
                location=Location(
                    state=request.location.state,
                    district=request.location.district,
                    agro_region_code=request.location.agroRegionCode,
                    lat=request.location.lat,
                    lon=request.location.lon,
                ),
                soil_sample=_apply_soil_offset(request.soilSample, offset),
                season_name=request.season,
                target_yield_value=request.targetYieldValue,
                target_yield_unit=request.targetYieldUnit,
                candidate_crop_codes=list(request.candidateCropCodes),
                weather=weather,
                local_adoption_overrides=dict(request.localAdoptionOverrides),
                market_signal_overrides=dict(request.marketSignalOverrides),
                organic_contributions=dict(request.organicContributions),
            )
            payload = _domain_to_response(shifted)
            what_if_models.append(
                WhatIfScenarioModel(
                    label=offset.label,
                    soilSample=payload["soilSample"],
                    options=payload["options"],
                    heatmap=payload["heatmap"],
                    rejectedCrops=payload["rejectedCrops"],
                )
            )

    base_payload = _domain_to_response(domain)
    return RecommendationResponseModel(
        runId=base_payload["runId"],
        scoringVersion=base_payload["scoringVersion"],
        location=base_payload["location"],
        soilSample=base_payload["soilSample"],
        options=base_payload["options"],
        heatmap=base_payload["heatmap"],
        rejectedCrops=base_payload["rejectedCrops"],
        weatherProfile=_weather_to_api(weather),
        retrievalChunks=retrieval_models,
        whatIfRuns=what_if_models,
    )
