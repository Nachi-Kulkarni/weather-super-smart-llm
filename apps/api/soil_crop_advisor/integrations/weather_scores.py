from __future__ import annotations

import math
from dataclasses import dataclass

from soil_crop_advisor.domain.models import WeatherProfile

from .open_meteo import OpenMeteoSeries


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _stress_from_temperature(tmax: list[float], tmin: list[float]) -> float:
    """Heuristic 0–1 stress signal: hotter + wider swings increase stress."""
    if not tmax or not tmin:
        return 0.5
    avg_high = _mean(tmax)
    avg_low = _mean(tmin)
    swing = abs(avg_high - avg_low)
    heat_penalty = max(0.0, (avg_high - 32.0) / 12.0)
    swing_penalty = min(1.0, swing / 18.0)
    return _clamp01(0.65 - 0.35 * heat_penalty - 0.25 * swing_penalty)


def _rain_score(precip: list[float]) -> float:
    """Favor moderate rainfall for broad cropping; penalize drought/heavy extremes."""
    if not precip:
        return 0.5
    total = sum(precip)
    # 14-day totals between ~20mm and ~180mm treated as favorable band for this scaffold
    if total < 5.0:
        return 0.35
    if total > 260.0:
        return 0.45
    return _clamp01(0.55 + min(0.35, (total - 20.0) / 400.0))


@dataclass(frozen=True)
class WeatherScoreBreakdown:
    short_range_score: float
    seasonal_prior_score: float
    notes: tuple[str, ...]


def scores_from_open_meteo(series: OpenMeteoSeries) -> WeatherScoreBreakdown:
    """
    Split Open-Meteo daily data:
    - Short range: first 14 days (deterministic forecast contribution).
    - Seasonal prior: days 15–45 (coarse outlook — not daily certainty).
    """
    precip = series.daily_precip_mm
    tmax = series.daily_tmax_c
    tmin = series.daily_tmin_c

    short_precip = precip[:14]
    long_precip = precip[14:46]
    short_tmax = tmax[:14]
    short_tmin = tmin[:14]
    long_tmax = tmax[14:46]
    long_tmin = tmin[14:46]

    short_rain = _rain_score(short_precip)
    long_rain = _rain_score(long_precip)
    short_temp = _stress_from_temperature(short_tmax, short_tmin)
    long_temp = _stress_from_temperature(long_tmax, long_tmin)

    short_range = _clamp01(0.55 * short_rain + 0.45 * short_temp)
    seasonal_prior = _clamp01(0.5 * long_rain + 0.5 * long_temp)

    notes = (
        "Short-range score blends 0–14d rainfall adequacy with temperature stress.",
        "Seasonal prior uses days 15–45 as a coarse outlook (not field-scale truth).",
    )
    return WeatherScoreBreakdown(
        short_range_score=short_range,
        seasonal_prior_score=seasonal_prior,
        notes=notes,
    )


def build_weather_profile_from_open_meteo(series: OpenMeteoSeries) -> WeatherProfile:
    breakdown = scores_from_open_meteo(series)
    return WeatherProfile(
        short_range_score=breakdown.short_range_score,
        seasonal_prior_score=breakdown.seasonal_prior_score,
        source_name="OpenMeteo",
        notes=(
            "Open-Meteo free access may be non-commercial — verify licensing before production.",
            *breakdown.notes,
        ),
    )


def safe_float(value: float | None, default: float = 0.5) -> float:
    if value is None:
        return default
    if math.isnan(value) or math.isinf(value):
        return default
    return float(value)
