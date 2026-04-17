from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

_logger = logging.getLogger(__name__)

OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class OpenMeteoSeries:
    """Normalized daily series used to derive short-range vs longer-horizon priors."""

    latitude: float
    longitude: float
    days: int
    daily_precip_mm: list[float]
    daily_tmax_c: list[float]
    daily_tmin_c: list[float]
    raw: dict[str, Any]


def fetch_forecast_series(
    latitude: float,
    longitude: float,
    *,
    forecast_days: int = 46,
    timeout_s: float = 12.0,
) -> OpenMeteoSeries:
    """
    Pull Open-Meteo daily forecast (free tier; check licensing for commercial use).

    We request a 46-day window so the caller can treat days 0–13 as short-range signal
    and days 14–45 as a coarse seasonal prior (not farm-level certainty).
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "forecast_days": forecast_days,
        "timezone": "auto",
    }
    with httpx.Client(timeout=timeout_s) as client:
        response = client.get(OPEN_METEO_FORECAST, params=params)
        response.raise_for_status()
        payload = response.json()

    daily = payload.get("daily") or {}
    precip_raw = daily.get("precipitation_sum") or []
    tmax_raw = daily.get("temperature_2m_max") or []
    tmin_raw = daily.get("temperature_2m_min") or []
    m = min(len(precip_raw), len(tmax_raw), len(tmin_raw))
    precip: list[float] = []
    tmax: list[float] = []
    tmin: list[float] = []
    for i in range(m):
        if tmax_raw[i] is None or tmin_raw[i] is None:
            continue
        precip.append(float(precip_raw[i] or 0.0))
        tmax.append(float(tmax_raw[i]))
        tmin.append(float(tmin_raw[i]))

    _logger.info(
        "open_meteo forecast pulled",
        extra={"latitude": latitude, "longitude": longitude, "points": len(precip)},
    )

    return OpenMeteoSeries(
        latitude=latitude,
        longitude=longitude,
        days=len(precip),
        daily_precip_mm=precip,
        daily_tmax_c=tmax,
        daily_tmin_c=tmin,
        raw=payload,
    )
