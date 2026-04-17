from __future__ import annotations

from uuid import uuid4

from .calculator import calculate_fertilizer_recommendation
from .models import (
    CitationRef,
    CropMetadata,
    HeatmapCell,
    Location,
    RecommendationOption,
    RecommendationResponse,
    RejectedCrop,
    SoilSample,
    WeatherProfile,
)
from .repository import CatalogRepository
from .rule_selector import select_best_rule
from .scoring import compute_confidence_band, compute_scores


class RecommendationEngine:
    def __init__(self, repository: CatalogRepository, scoring_version: str) -> None:
        self.repository = repository
        self.scoring_version = scoring_version

    def recommend(
        self,
        location: Location,
        soil_sample: SoilSample,
        season_name: str,
        target_yield_value: float | None = None,
        target_yield_unit: str | None = None,
        candidate_crop_codes: list[str] | None = None,
        weather: WeatherProfile | None = None,
        local_adoption_overrides: dict[str, float] | None = None,
        market_signal_overrides: dict[str, float] | None = None,
        organic_contributions: dict[str, float] | None = None,
        soil_order: str | None = None,
    ) -> RecommendationResponse:
        local_adoption_overrides = local_adoption_overrides or {}
        market_signal_overrides = market_signal_overrides or {}
        organic_contributions = organic_contributions or {}

        all_crops = self.repository.list_crops()
        if candidate_crop_codes:
            candidate_set = set(candidate_crop_codes)
            candidate_crops = [crop for crop in all_crops if crop.crop_code in candidate_set]
        else:
            candidate_crops = all_crops

        options: list[RecommendationOption] = []
        rejected_crops: list[RejectedCrop] = []

        if not candidate_crops:
            rejected_crops.append(
                RejectedCrop(
                    crop_name="Catalog",
                    reason="No crops are loaded yet. Ingest verified STCR sources before running recommendations.",
                )
            )

        for crop in candidate_crops:
            # Reject crops that are not suitable for the requested season
            if crop.season_names and season_name.lower() not in [s.lower() for s in crop.season_names]:
                rejected_crops.append(
                    RejectedCrop(
                        crop_name=crop.crop_name,
                        reason=f"{crop.crop_name} is not a {season_name} crop in this region (suitable seasons: {', '.join(crop.season_names)}).",
                    )
                )
                continue

            option_or_rejection = self._recommend_for_crop(
                crop=crop,
                location=location,
                soil_sample=soil_sample,
                season_name=season_name,
                target_yield_value=target_yield_value,
                target_yield_unit=target_yield_unit,
                weather=weather,
                local_adoption_score=local_adoption_overrides.get(crop.crop_code, 0.5),
                market_signal_score=market_signal_overrides.get(crop.crop_code, 0.5),
                organic_contributions=organic_contributions,
                soil_order=soil_order,
            )
            if isinstance(option_or_rejection, RecommendationOption):
                options.append(option_or_rejection)
            else:
                rejected_crops.append(option_or_rejection)

        ranked_options = sorted(options, key=lambda option: (-option.final_score, option.crop_name))
        reranked_options: list[RecommendationOption] = []
        heatmap: list[HeatmapCell] = []
        for index, option in enumerate(ranked_options, start=1):
            reranked_option = RecommendationOption(
                crop_id=option.crop_id,
                crop_name=option.crop_name,
                rank=index,
                target_yield_value=option.target_yield_value,
                target_yield_unit=option.target_yield_unit,
                recommended_n=option.recommended_n,
                recommended_p=option.recommended_p,
                recommended_k=option.recommended_k,
                nutrient_basis=option.nutrient_basis,
                nutrient_fit_score=option.nutrient_fit_score,
                weather_feasibility_score=option.weather_feasibility_score,
                agro_region_fit_score=option.agro_region_fit_score,
                local_adoption_score=option.local_adoption_score,
                market_signal_score=option.market_signal_score,
                input_burden_score=option.input_burden_score,
                season_suitability_score=option.season_suitability_score,
                final_score=option.final_score,
                confidence_band=option.confidence_band,
                reasons=list(option.reasons),
                cautions=list(option.cautions),
                citations=list(option.citations),
                trace_payload=dict(option.trace_payload),
            )
            reranked_options.append(reranked_option)
            heatmap.append(
                HeatmapCell(
                    crop_id=reranked_option.crop_id,
                    crop_name=reranked_option.crop_name,
                    delta_n=reranked_option.recommended_n,
                    delta_p=reranked_option.recommended_p,
                    delta_k=reranked_option.recommended_k,
                    score=reranked_option.final_score,
                    confidence_band=reranked_option.confidence_band,
                )
            )

        return RecommendationResponse(
            run_id=str(uuid4()),
            scoring_version=self.scoring_version,
            location=location,
            soil_sample_payload={
                "nValue": soil_sample.n_value,
                "pValue": soil_sample.p_value,
                "kValue": soil_sample.k_value,
                "phValue": soil_sample.ph_value,
                "ecValue": soil_sample.ec_value,
                "ocValue": soil_sample.oc_value,
                "nutrientBasis": soil_sample.nutrient_basis,
                **soil_sample.extras,
            },
            options=reranked_options,
            heatmap=heatmap,
            rejected_crops=rejected_crops,
        )

    def _recommend_for_crop(
        self,
        crop: CropMetadata,
        location: Location,
        soil_sample: SoilSample,
        season_name: str,
        target_yield_value: float | None,
        target_yield_unit: str | None,
        weather: WeatherProfile | None,
        local_adoption_score: float,
        market_signal_score: float,
        organic_contributions: dict[str, float],
        soil_order: str | None = None,
    ) -> RecommendationOption | RejectedCrop:
        selection = select_best_rule(
            crop_code=crop.crop_code,
            location=location,
            season_name=season_name,
            rules=self.repository.list_rules(crop.crop_code),
            soil_order=soil_order,
        )
        rule = selection.selected_rule
        if rule is None:
            return RejectedCrop(
                crop_name=crop.crop_name,
                reason="No verified rule matched the requested crop, season, and geography.",
            )

        resolved_target_yield_value = target_yield_value or crop.default_target_yield_value
        resolved_target_yield_unit = target_yield_unit or crop.default_target_yield_unit or rule.target_yield_unit
        if resolved_target_yield_value is None:
            return RejectedCrop(
                crop_name=crop.crop_name,
                reason="Missing target yield. Provide one in the request or seed a crop default.",
            )

        fertilizer = calculate_fertilizer_recommendation(
            rule=rule,
            soil_sample=soil_sample,
            target_yield=resolved_target_yield_value,
            organic_contributions=organic_contributions,
        )

        # Season suitability: crop is in-season (already filtered above, so this is always >= 0.8)
        season_suitability = _compute_season_suitability(crop, season_name)

        scores = compute_scores(
            recommended_n=fertilizer.recommended_n,
            recommended_p=fertilizer.recommended_p,
            recommended_k=fertilizer.recommended_k,
            rule=rule,
            weather=weather,
            local_adoption_score=local_adoption_score,
            market_signal_score=market_signal_score,
            season_suitability_score=season_suitability,
        )

        confidence_band = compute_confidence_band(rule)
        citations = []
        if rule.source_doc_id and rule.source_title:
            citations.append(
                CitationRef(
                    source_doc_id=rule.source_doc_id,
                    title=rule.source_title,
                    snippet=rule.citation_text,
                )
            )

        reasons = [
            f"Used {rule.equation_family} rule at {rule.geography_scope} scope.",
            f"Computed fertilizer need in {fertilizer.nutrient_basis} basis.",
            f"Applied scoring version {self.scoring_version}.",
            f"Season suitability for {season_name}: {season_suitability:.2f}.",
        ]
        cautions = list(selection.warnings)
        if weather is None:
            cautions.append("Weather score is neutral because no forecast payload was supplied.")
        if confidence_band != "A":
            cautions.append("Result is not an exact district-level verified STCR match.")
        cautions.append("Fertilizer values are indicative — district, pH, and target yield are needed for precise STCR calculations.")

        return RecommendationOption(
            crop_id=crop.crop_code,
            crop_name=crop.crop_name,
            rank=0,
            target_yield_value=resolved_target_yield_value,
            target_yield_unit=resolved_target_yield_unit,
            recommended_n=fertilizer.recommended_n,
            recommended_p=fertilizer.recommended_p,
            recommended_k=fertilizer.recommended_k,
            nutrient_basis=fertilizer.nutrient_basis,
            nutrient_fit_score=scores.nutrient_fit_score,
            weather_feasibility_score=scores.weather_feasibility_score,
            agro_region_fit_score=scores.agro_region_fit_score,
            local_adoption_score=scores.local_adoption_score,
            market_signal_score=scores.market_signal_score,
            input_burden_score=scores.input_burden_score,
            season_suitability_score=scores.season_suitability_score,
            final_score=scores.final_score,
            confidence_band=confidence_band,
            reasons=reasons,
            cautions=cautions,
            citations=citations,
            trace_payload={
                "selectedRule": {
                    "equationFamily": rule.equation_family,
                    "geographyScope": rule.geography_scope,
                    "sourceDocId": rule.source_doc_id,
                    "targetYieldUnit": rule.target_yield_unit,
                    "nutrientBasis": rule.nutrient_basis,
                },
                "fertilizerTrace": fertilizer.trace,
                "scoreTrace": scores.trace,
            },
        )


def _compute_season_suitability(crop: CropMetadata, season_name: str) -> float:
    """Score how well a crop fits the requested season.

    Crops that match the primary season for the region get a high score.
    Multi-season crops get a moderate score (they're flexible but not optimal).
    """
    if not crop.season_names:
        return 0.6  # no calendar data — neutral-low

    season_lower = season_name.lower()
    crop_seasons_lower = [s.lower() for s in crop.season_names]

    if season_lower not in crop_seasons_lower:
        return 0.1  # shouldn't happen (filtered earlier), but defensive

    # Single-season match (strong signal) vs multi-season (more flexible)
    if len(crop_seasons_lower) == 1:
        return 1.0  # this crop is exclusively grown in this season
    return 0.85  # multi-season crop — decent fit but less specialized
