from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx

_logger = logging.getLogger(__name__)

# Documented on IMD Mausam pages — lat/lon city-style forecast (may require IP allowlisting).
IMD_CITY_WEATHER_LOC = "https://city.imd.gov.in/api/cityweather_loc.php"
# Current weather / nowcast-style endpoint used on mausam.imd.gov.in API listings.
IMD_CURRENT_WX = "https://mausam.imd.gov.in/api/current_wx_api.php"


@dataclass(frozen=True)
class ImdLiveResult:
    ok: bool
    source: str
    notes: tuple[str, ...]
    raw: dict[str, Any]
    # Normalized hints for scoring (0–1) when parsable; else None.
    short_range_hint: float | None = None
    seasonal_hint: float | None = None


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _hint_from_payload(payload: Any) -> tuple[float | None, float | None]:
    """
    Best-effort extraction: IMD JSON shapes vary by endpoint/version.

    We look for common keys and nested forecast arrays without asserting a single schema.
    """
    if not isinstance(payload, dict):
        return None, None

    def dig_numbers(obj: Any, depth: int = 0) -> list[float]:
        if depth > 6:
            return []
        out: list[float] = []
        if isinstance(obj, (int, float)):
            out.append(float(obj))
        elif isinstance(obj, dict):
            for key in (
                "temp",
                "temperature",
                "temp_max",
                "temp_min",
                "rainfall",
                "rain",
                "precip",
                "rh",
                "humidity",
            ):
                if key in obj and isinstance(obj[key], (int, float)):
                    out.append(float(obj[key]))
            for v in obj.values():
                out.extend(dig_numbers(v, depth + 1))
        elif isinstance(obj, list):
            for item in obj[:40]:
                out.extend(dig_numbers(item, depth + 1))
        return out

    nums = dig_numbers(payload)
    if not nums:
        return None, None

    # Very rough: use spread of numeric fields as a weak stress proxy (scaffold).
    avg = sum(nums) / len(nums)
    spread = max(nums) - min(nums) if len(nums) > 1 else 0.0
    short = _clamp01(0.75 - min(0.4, abs(avg - 30.0) / 80.0) - min(0.35, spread / 120.0))
    seasonal = _clamp01(0.65 - min(0.35, spread / 150.0))
    return short, seasonal


def fetch_imd_cityweather_latlon(lat: float, lon: float, *, timeout_s: float = 20.0) -> ImdLiveResult:
    """
    Live call to IMD city weather by coordinates.

    IMD may block non-Indian networks or require IP allowlisting — failures are surfaced in `notes`.
    """
    params = {"lat": lat, "lon": lon}
    try:
        with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
            response = client.get(IMD_CITY_WEATHER_LOC, params=params)
            response.raise_for_status()
            text = response.text
    except Exception as exc:  # noqa: BLE001
        _logger.warning("imd cityweather_loc failed: %s", exc)
        return ImdLiveResult(
            ok=False,
            source="IMD",
            notes=(f"cityweather_loc request failed: {exc}",),
            raw={},
        )

    payload: dict[str, Any]
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        # Some deployments return HTML or non-JSON error pages.
        snippet = text.strip()[:400]
        return ImdLiveResult(
            ok=False,
            source="IMD",
            notes=("IMD response was not JSON — check allowlisting or endpoint changes.", f"Body snippet: {snippet}"),
            raw={"_raw_text": text[:2000]},
        )

    short, seasonal = _hint_from_payload(payload)
    _logger.info("imd cityweather_loc ok keys=%s", list(payload.keys())[:12])
    return ImdLiveResult(
        ok=True,
        source="IMD",
        notes=("IMD cityweather_loc JSON retrieved — hints are heuristic until field mapping is locked to IMD schema.",),
        raw=payload,
        short_range_hint=short,
        seasonal_hint=seasonal,
    )


def fetch_imd_current_wx(lat: float, lon: float, *, timeout_s: float = 20.0) -> ImdLiveResult:
    """Secondary endpoint attempt (parameters may vary — kept as a best-effort fallback)."""
    try:
        with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
            response = client.get(IMD_CURRENT_WX, params={"lat": lat, "lon": lon})
            response.raise_for_status()
            text = response.text
    except Exception as exc:  # noqa: BLE001
        return ImdLiveResult(
            ok=False,
            source="IMD",
            notes=(f"current_wx_api request failed: {exc}",),
            raw={},
        )

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return ImdLiveResult(
            ok=False,
            source="IMD",
            notes=("IMD current_wx response was not JSON.",),
            raw={"_raw_text": text[:2000]},
        )

    short, seasonal = _hint_from_payload(payload)
    return ImdLiveResult(
        ok=True,
        source="IMD",
        notes=("IMD current_wx JSON retrieved (fallback path).",),
        raw=payload,
        short_range_hint=short,
        seasonal_hint=seasonal,
    )


def fetch_imd_best_effort(lat: float, lon: float) -> ImdLiveResult:
    """Try primary lat/lon API, then secondary."""
    primary = fetch_imd_cityweather_latlon(lat, lon)
    if primary.ok:
        return primary
    secondary = fetch_imd_current_wx(lat, lon)
    if secondary.ok:
        merged_notes = primary.notes + secondary.notes
        return ImdLiveResult(
            ok=True,
            source="IMD",
            notes=merged_notes + ("Used current_wx fallback after cityweather_loc non-JSON or failed.",),
            raw=secondary.raw,
            short_range_hint=secondary.short_range_hint,
            seasonal_hint=secondary.seasonal_hint,
        )
    return ImdLiveResult(
        ok=False,
        source="IMD",
        notes=primary.notes + secondary.notes,
        raw={},
    )
