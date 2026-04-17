from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
import urllib.error
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import lru_cache
from logging import getLogger
from typing import Any, Iterator

import httpx
from deepagents import create_deep_agent

from .api_schemas import RecommendRequest
from .service import SCORING_VERSION, build_response, get_repository

DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "minimax/minimax-m2.7:online"

_logger = getLogger(__name__)

_tool_trace_ctx: ContextVar[list[dict[str, Any]] | None] = ContextVar("_tool_trace_ctx", default=None)


def _emit_tool_event(tool: str, phase: str, detail: str | None = None) -> None:
    bucket = _tool_trace_ctx.get()
    if bucket is None:
        return
    bucket.append(
        {
            "tool": tool,
            "phase": phase,
            "detail": detail,
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    )


@contextmanager
def tool_trace_session() -> Iterator[list[dict[str, Any]]]:
    """Attach per-request tool start/end/error events for the chat API (ContextVar-scoped)."""
    bucket: list[dict[str, Any]] = []
    token = _tool_trace_ctx.set(bucket)
    try:
        yield bucket
    finally:
        _tool_trace_ctx.reset(token)


def run_recommendation_core(request_json: str) -> str:
    """
    Run the deterministic recommendation engine.

    `request_json` must be a single JSON string. Required keys:
    - "location": object with "state" (and optionally "district", "lat", "lon")
    - "soilSample": object with "nValue", "pValue", "kValue" (optionally "nutrientBasis")
    - "season": string like "kharif" or "rabi"

    Example:
    {"location":{"state":"Karnataka","district":"Tumkur"},"soilSample":{"nValue":180,"pValue":24,"kValue":210,"nutrientBasis":"N-P-K"},"season":"kharif"}

    Do NOT use keys "locationContext" or "seasonWindow" — they will be rejected.
    """
    _logger.info("run_recommendation called: %s", request_json[:200])
    payload = RecommendRequest.model_validate_json(request_json)
    response = build_response(payload)
    _logger.info("run_recommendation done: %d options returned", len(response.options))
    return response.model_dump_json(indent=2)


def run_recommendation(request_json: str) -> str:
    """Same as run_recommendation_core; emits start/end/error tool trace events for /chat."""
    # Signature must stay `request_json: str` — LangChain builds the tool schema from parameter
    # names; a generic *args/**kwargs wrapper makes the model pass `args=...` and breaks invocation.
    _emit_tool_event("run_recommendation", "start")
    try:
        result = run_recommendation_core(request_json)
    except Exception as exc:  # noqa: BLE001
        _emit_tool_event("run_recommendation", "error", str(exc))
        raise
    _emit_tool_event("run_recommendation", "end")
    return result


def get_scoring_policy_core() -> str:
    """Return the current deterministic scoring policy and confidence rules."""
    return (
        f"Scoring version: {SCORING_VERSION}\n"
        "Selection order: district STCR -> state STCR -> agro-region STCR -> package-of-practice fallback.\n"
        "Confidence bands: A = verified STCR with direct geography match, "
        "B = verified regional agronomy source without exact match, "
        "C = fallback approximation with explicit warning.\n"
        "Weather policy: 0-14 days deterministic forecast, 15-90 days seasonal prior."
    )


def get_scoring_policy() -> str:
    """Return the current deterministic scoring policy and confidence rules (tool entrypoint with traces)."""
    _emit_tool_event("get_scoring_policy", "start")
    try:
        result = get_scoring_policy_core()
    except Exception as exc:  # noqa: BLE001
        _emit_tool_event("get_scoring_policy", "error", str(exc))
        raise
    _emit_tool_event("get_scoring_policy", "end")
    return result


def get_source_policy_core() -> str:
    """Return the agronomy safety rules for source usage."""
    return (
        "Never fabricate STCR equations. Use retrieved rules and citations only. "
        "Deterministic code computes fertilizer prescriptions. "
        "If a verified rule is missing, downgrade confidence and say so explicitly."
    )


def get_source_policy() -> str:
    """Return the agronomy safety rules for source usage (tool entrypoint with traces)."""
    _emit_tool_event("get_source_policy", "start")
    try:
        result = get_source_policy_core()
    except Exception as exc:  # noqa: BLE001
        _emit_tool_event("get_source_policy", "error", str(exc))
        raise
    _emit_tool_event("get_source_policy", "end")
    return result


# ---------------------------------------------------------------------------
# Weather lookup — works without NPK data
# ---------------------------------------------------------------------------

# Approximate lat/lon for Indian districts (expanded list)
_DISTRICT_COORDS: dict[str, tuple[float, float]] = {
    # Karnataka
    "tumkur": (13.34, 77.10), "bangalore": (12.97, 77.59), "bengaluru": (12.97, 77.59),
    "mysore": (12.30, 76.65), "raichur": (16.21, 77.35), "dharwad": (15.46, 75.02),
    "belgaum": (15.85, 74.50), "gulbarga": (17.33, 76.83), "mandya": (12.52, 76.90),
    "shivamogga": (13.93, 75.57), "davangere": (14.46, 75.92), "bellary": (15.14, 76.91),
    "hassan": (13.01, 76.10), "chitradurga": (14.23, 76.40),
    # Bihar
    "patna": (25.61, 85.14), "gaya": (24.80, 84.99), "bhagalpur": (25.24, 86.97),
    "muzaffarpur": (26.12, 85.39), "ara": (25.56, 84.67), "bhojpur": (25.56, 84.67),
    "darbhanga": (26.15, 85.90), "purnia": (25.78, 87.48), "saran": (25.88, 84.62),
    "siwan": (26.22, 84.36), "madhubani": (26.35, 86.08), "nalanda": (25.14, 85.42),
    # Madhya Pradesh
    "bhopal": (23.26, 77.41), "indore": (22.72, 75.86), "jabalpur": (23.18, 79.99),
    "gwalior": (26.22, 78.18), "sagar": (23.84, 78.74),
    # Maharashtra
    "pune": (18.52, 73.86), "nagpur": (21.15, 79.09), "nashik": (19.99, 73.79),
    "kolhapur": (16.71, 74.24), "aurangabad": (19.88, 75.34),
    # Tamil Nadu
    "chennai": (13.08, 80.27), "coimbatore": (11.02, 76.96), "madurai": (9.93, 78.12),
    "salem": (11.66, 78.14), "trichy": (10.79, 78.69), "tiruchirappalli": (10.79, 78.69),
    # Uttar Pradesh
    "lucknow": (26.85, 80.95), "kanpur": (26.45, 80.33), "varanasi": (25.32, 83.01),
    "allahabad": (25.43, 81.85), "agra": (27.18, 78.01),
    # Rajasthan
    "jaipur": (26.91, 75.79), "jodhpur": (26.24, 73.02), "udaipur": (24.59, 73.71),
    # Punjab / Haryana
    "ludhiana": (30.90, 75.86), "amritsar": (31.63, 74.87), "chandigarh": (30.73, 76.78),
    "hisar": (29.15, 75.72), "karnal": (29.69, 76.99),
    # West Bengal
    "kolkata": (22.57, 88.36), "bardhaman": (23.23, 87.86), "murshidabad": (24.18, 88.27),
    # Telangana / AP
    "hyderabad": (17.39, 78.49), "warangal": (17.98, 79.60), "visakhapatnam": (17.69, 83.22),
    "vijayawada": (16.51, 80.65), "guntur": (16.31, 80.44),
    # Gujarat
    "ahmedabad": (23.02, 72.57), "rajkot": (22.30, 70.80), "surat": (21.17, 72.83),
    # Odisha
    "bhubaneswar": (20.30, 85.82), "cuttack": (20.46, 85.88), "sambalpur": (21.47, 83.98),
    # Kerala
    "thiruvananthapuram": (8.52, 76.94), "kochi": (9.93, 76.27), "kozhikode": (11.26, 75.78),
}

# State-level fallback coordinates
_STATE_COORDS: dict[str, tuple[float, float]] = {
    "karnataka": (15.32, 75.71), "bihar": (25.61, 85.14), "madhya pradesh": (23.47, 77.95),
    "maharashtra": (19.75, 75.71), "tamil nadu": (11.13, 78.28), "uttar pradesh": (26.85, 80.95),
    "rajasthan": (27.02, 74.22), "punjab": (31.15, 75.34), "haryana": (29.06, 76.09),
    "west bengal": (22.99, 87.53), "telangana": (18.11, 79.02), "andhra pradesh": (15.91, 79.74),
    "gujarat": (22.26, 71.19), "odisha": (20.95, 85.10), "kerala": (10.85, 76.27),
    "chhattisgarh": (21.28, 81.63), "jharkhand": (23.61, 85.33), "assam": (26.24, 92.54),
}


def _resolve_coords(state: str, district: str | None) -> tuple[float, float] | None:
    if district:
        key = district.strip().lower().replace(" ", "")
        if key in _DISTRICT_COORDS:
            return _DISTRICT_COORDS[key]
    state_key = state.strip().lower()
    return _STATE_COORDS.get(state_key)


def lookup_weather_core(location_json: str) -> str:
    """Fetch real weather forecast for a location. Does NOT require NPK data.

    location_json format: {"state": "Bihar", "district": "Ara"}
    Returns temperature, precipitation, and weather assessment for short-range + seasonal outlook.
    """
    _logger.info("lookup_weather called: %s", location_json[:200])
    loc = json.loads(location_json)
    state = loc.get("state", "")
    district = loc.get("district")
    coords = _resolve_coords(state, district)
    if coords is None:
        return json.dumps({"error": f"Could not resolve coordinates for {state}/{district}. Provide lat/lon manually."})

    lat, lon = coords

    # Fetch 16-day deterministic forecast
    try:
        with httpx.Client(timeout=12.0) as client:
            resp = client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat, "longitude": lon,
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                    "forecast_days": 16,
                    "timezone": "auto",
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"Weather fetch failed: {exc}"})

    # Fetch 92-day seasonal forecast (covers 3+ months for crop planning)
    seasonal_data = None
    try:
        with httpx.Client(timeout=12.0) as client:
            resp2 = client.get(
                "https://seasonal-api.open-meteo.com/v1/seasonal",
                params={
                    "latitude": lat, "longitude": lon,
                    "daily": "temperature_2m_mean,precipitation_sum",
                    "forecast_days": 92,
                    "timezone": "auto",
                },
            )
            if resp2.status_code == 200:
                seasonal_data = resp2.json()
    except Exception:  # noqa: BLE001
        pass

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])

    # Short-range summary (16 days)
    summary_lines = []
    total_precip = 0.0
    valid_days = 0
    for i in range(min(len(dates), 16)):
        if tmax[i] is None:
            continue
        valid_days += 1
        p = float(precip[i] or 0)
        total_precip += p
        summary_lines.append(f"  {dates[i]}: {float(tmin[i]):.0f}-{float(tmax[i]):.0f}°C, rain {p:.1f}mm")

    avg_tmax = sum(float(t) for t in tmax if t is not None) / max(valid_days, 1)
    avg_tmin = sum(float(t) for t in tmin if t is not None) / max(valid_days, 1)

    if total_precip < 10:
        rain_status = "Very dry — irrigation likely needed"
    elif total_precip < 40:
        rain_status = "Low rainfall — monitor closely"
    elif total_precip < 120:
        rain_status = "Moderate rainfall — generally favorable"
    elif total_precip < 200:
        rain_status = "Good rainfall — favorable for most crops"
    else:
        rain_status = "Heavy rainfall — watch for waterlogging"

    result = (
        f"Weather forecast for {district or state} ({lat:.2f}°N, {lon:.2f}°E):\n"
        f"Source: Open-Meteo (open-meteo.com)\n\n"
        f"SHORT-RANGE (next {valid_days} days):\n"
        f"  Average high: {avg_tmax:.1f}°C, Average low: {avg_tmin:.1f}°C\n"
        f"  Total expected rainfall: {total_precip:.1f}mm\n"
        f"  Assessment: {rain_status}\n"
    )

    # Seasonal outlook (3-4 months) — aggregate weekly from daily seasonal data
    if seasonal_data:
        s_daily = seasonal_data.get("daily", {})
        s_time = s_daily.get("time", [])
        s_temp = s_daily.get("temperature_2m_mean", [])
        s_precip = s_daily.get("precipitation_sum", [])
        if s_time:
            result += "\nSEASONAL OUTLOOK (next 3 months, source: Open-Meteo seasonal ensemble):\n"
            # Aggregate by week
            for wk in range(0, min(len(s_time), 92), 7):
                wk_end = min(wk + 7, len(s_time))
                wk_temps = [s_temp[i] for i in range(wk, wk_end) if i < len(s_temp) and s_temp[i] is not None]
                wk_rain = [s_precip[i] for i in range(wk, wk_end) if i < len(s_precip) and s_precip[i] is not None]
                if wk_temps or wk_rain:
                    avg_t = sum(wk_temps) / max(len(wk_temps), 1) if wk_temps else None
                    total_r = sum(wk_rain) if wk_rain else 0
                    start_d = s_time[wk] if wk < len(s_time) else "?"
                    end_d = s_time[wk_end - 1] if wk_end - 1 < len(s_time) else "?"
                    t_str = f"{avg_t:.1f}°C avg" if avg_t is not None else "N/A"
                    result += f"  {start_d} to {end_d}: {t_str}, ~{total_r:.0f}mm rain\n"
            result += "Note: Seasonal outlook is a model ensemble projection. Use for crop planning, not day-to-day decisions.\n"

    result += f"\nDaily breakdown:\n" + "\n".join(summary_lines)
    return result


def lookup_weather(location_json: str) -> str:
    """Fetch real weather forecast for a location. Does NOT require NPK data.

    location_json format: {"state": "Bihar", "district": "Ara"}
    Returns temperature, precipitation, and weather feasibility for the next 16 days.
    """
    _emit_tool_event("lookup_weather", "start")
    try:
        result = lookup_weather_core(location_json)
    except Exception as exc:  # noqa: BLE001
        _emit_tool_event("lookup_weather", "error", str(exc))
        raise
    _emit_tool_event("lookup_weather", "end")
    return result


# ---------------------------------------------------------------------------
# Crop catalog — list available crops and their seasons
# ---------------------------------------------------------------------------

def lookup_crops_core(season: str | None = None) -> str:
    """List crops available in the catalog with their suitable seasons.

    Returns crop names, groups, default yields, and which seasons they're grown in.
    Optionally filter by season to see only crops suitable for that season.
    """
    repo = get_repository()
    crops = repo.list_crops()

    lines = [f"Available crops ({len(crops)} total):"]
    for c in crops:
        seasons = ", ".join(c.season_names) if c.season_names else "unknown"
        yield_info = f", default yield: {c.default_target_yield_value} {c.default_target_yield_unit}" if c.default_target_yield_value else ""
        lines.append(f"  - {c.crop_name} ({c.crop_group}): seasons [{seasons}]{yield_info}")

    if season:
        matching = [c for c in crops if not c.season_names or season.lower() in [s.lower() for s in c.season_names]]
        rejected = [c for c in crops if c.season_names and season.lower() not in [s.lower() for s in c.season_names]]
        if matching:
            lines.append(f"\nCrops suitable for {season}: {', '.join(c.crop_name for c in matching)}")
        if rejected:
            lines.append(f"Crops NOT suitable for {season}: {', '.join(c.crop_name for c in rejected)}")

    return "\n".join(lines)


def lookup_crops(state_json: str) -> str:
    """List available crops and which seasons they grow in.

    state_json format: {"season": "kharif"} or {"season": "rabi"} or {} for all crops.
    """
    _emit_tool_event("lookup_crops", "start")
    try:
        params = json.loads(state_json) if state_json.strip() else {}
        result = lookup_crops_core(season=params.get("season"))
    except Exception as exc:  # noqa: BLE001
        _emit_tool_event("lookup_crops", "error", str(exc))
        raise
    _emit_tool_event("lookup_crops", "end")
    return result


# ---------------------------------------------------------------------------
# Source / RAG search — agronomy sources and STCR citations
# ---------------------------------------------------------------------------

def search_sources_core(query_json: str) -> str:
    """Search verified agronomy sources and STCR citations in the database.

    Returns matching source documents, STCR equations, and citations.
    """
    params = json.loads(query_json)
    query = params.get("query", "")
    crop_code = params.get("crop_code")
    state = params.get("state")

    repo = get_repository()
    results = []

    # Search STCR rules
    rules = repo.list_rules(crop_code=crop_code)
    if state:
        rules = [r for r in rules if r.state_name and state.lower() in r.state_name.lower()]

    if rules:
        results.append(f"STCR Equations found ({len(rules)}):")
        for r in rules[:8]:
            results.append(
                f"  - {r.crop_code} | {r.state_name} | {r.season_name} | "
                f"NR: N={r.nr_n} P={r.nr_p} K={r.nr_k} | "
                f"Confidence: {r.confidence_band} | "
                f"Source: {r.source_title or 'N/A'} | "
                f"Citation: {r.citation_text or 'N/A'}"
            )
    else:
        results.append("No STCR equations found for this query.")

    # Try RAG retrieval from Postgres if available
    try:
        from .db import get_pool
        from .rag.retrieval import retrieve_chunks
        pool = get_pool()
        if pool is not None:
            crop_codes = [crop_code] if crop_code else []
            chunks = retrieve_chunks(
                pool, query=query, state_name=state, crop_codes=crop_codes, limit=5, mode="keyword",
            )
            if chunks:
                results.append(f"\nSource chunks ({len(chunks)}):")
                for ch in chunks:
                    results.append(
                        f"  - [{ch.chunk_type}] {ch.chunk_text[:200]} | "
                        f"Source: {ch.title} | Crops: {', '.join(ch.crop_tags)}"
                    )
    except Exception:  # noqa: BLE001
        pass

    return "\n".join(results)


def search_sources(query_json: str) -> str:
    """Search verified agronomy sources, STCR equations, and RAG citations.

    query_json format: {"query": "maize fertilizer kharif", "crop_code": "maize", "state": "Bihar"}
    Returns STCR equation coefficients, source documents, and confidence bands.
    """
    _emit_tool_event("search_sources", "start")
    try:
        result = search_sources_core(query_json)
    except Exception as exc:  # noqa: BLE001
        _emit_tool_event("search_sources", "error", str(exc))
        raise
    _emit_tool_event("search_sources", "end")
    return result


# ---------------------------------------------------------------------------
# Web search — for market prices, crop research, and live data
# ---------------------------------------------------------------------------

def web_search_core(query: str) -> str:
    """Search the web for agricultural information (market prices, crop research).

    Search is handled via OpenRouter web plugin configured in model settings.
    This tool is a fallback - OpenRouter does automatic searching with :online models.
    """
    return "Search is configured via OpenRouter web plugin. Use model with :online suffix for automatic search."


def web_search(query: str) -> str:
    """Search the web for agricultural information (market prices, crop research).

    Note: For search, use Exa MCP configured in your Claude Code settings.
    This Python tool is a fallback. Set EXA_API_KEY if you want direct search.
    """
    _emit_tool_event("web_search", "start")
    result = web_search_core(query)
    _emit_tool_event("web_search", "end")
    return result


SYSTEM_PROMPT = """\
You are Soil Crop Advisor. You help farmers maximize PROFIT.

## YOUR JOB — NPK DIFFERENTIAL MATRIX
This system has something ChatGPT doesn't: actual NPK calculations.

For each crop, show the DIFFERENCE between:
- What your SOIL has (from soil test)
- What the CROP needs (from STCR equation)

CREATE A MATRIX TABLE:

Crop | Your Soil | Crop Needs | GAP (What to Add)
-----|-----------|----------|---------------
Maize | N=150 | N=180 | +30 kg N
     | P=20 | P=45 | +25 kg P2O5
     | K=180 | K=120 | OK
Groundnut | N=150 | N=100 | OK
     | P=20 | P=35 | +15 kg P2O5
     | K=180 | K=90 | OK

This is YOUR DIFFERENTIATOR — show the math, not just advice.

## SOIL — EXPLAIN SIMPLY
- "Your soil is good on N/P/K" or "Your P is low - needs DAP"
- No technical jargon

## SOIL TYPE GUESSING
If farmer doesn't know soil type, make educated guesses based on location:
- Red soils → likely Alfisols (common in Karnataka, AP)
- Black cotton soils → likely Vertisols (Madhya Pradesh, Maharashtra)
- Sandy soils → likely Inceptisols/Entisols

SAY your assumption: "Based on Bidar being in North Karnataka with red soils, I'm assuming Alfisols."

If uncertain, use web_search to find the actual soil type for that district.

## STCR KARNATAKA REFERENCE (2022-2026) — UAS BANGALORE
This system has STCR reference data from UAS Bangalore for a LIMITED set of Karnataka districts:
- Districts with verified equations: Tumkur, Shimoga, Hassan, Chikmagalur only
- Crops: maize, aerobic_rice, green_gram, ragi, little_millet, coriander, groundnut, sunflower
- Soil types: Alfisols, Vertisols

This is a REFERENCE dataset (confidence A), NOT comprehensive for all Karnataka.
- For these specific districts: use STCR reference
- For other Karnataka districts: uses universal scaffold (confidence B)
- For other states: uses universal scaffold

Use STCR reference when available. Always cite confidence band.

You are Soil Crop Advisor. You help farmers and advisors with crop and fertilizer decisions.

## HOW THE SYSTEM WORKS — THE DETERMINISTIC ENGINE
This system does NOT use LLM-generated fertilizer math. All fertilizer prescriptions are computed by a deterministic STCR (Soil Test Crop Response) engine using verified equations.

**STCR Formula**: `dose_kg_per_ha = (NR / CF) × target_yield − (CS / CF) × soil_test_value − organic_credit`

Where:
- NR = Nutrient Requirement (kg nutrient per quintal of yield) — from verified STCR equations
- CS = Contribution from Soil (how much nutrient 1 unit of soil test value supplies)
- CF = Contribution from Fertilizer (nutrient content fraction)
- organic_credit = adjustment for organic manure/compost applications

**Rule selection priority**: district-level STCR → state-level STCR → agro-region STCR → package-of-practice fallback

**Confidence bands**:
- A = verified ICAR STCR with direct geography match (highest trust)
- B = verified regional agronomy source, not exact district match
- C = fallback approximation (always flagged with warning)

**What this means**: The fertilizer doses you see from `run_recommendation` are mathematically computed, not guessed. Always cite the STCR source and confidence band when explaining results.

**Data sources**: The system uses ICAR/STCR equation databases. If a state/crop combination has no STCR data, the tool returns no results — never fabricate equations. Use `search_sources` to check what's available, and `web_search` to find ICAR research for missing regions.

## RULE #1: ASK BEFORE YOU ACT — ALWAYS
BEFORE pulling any data or giving any recommendation, you MUST ask the user clarifying questions to understand their full situation. Never jump straight to tools.

Minimum info to gather BEFORE using any tools:
1. **Location** — state and district
2. **Planting/harvest timing** — what month they plan to sow, when they want to harvest
3. **Irrigation** — do they have irrigation (borewell, canal, pump)? Or fully rainfed?
4. **Land size** — how many acres/bigha?
5. **Soil test** — do they have NPK values? Even partial data helps.
6. **Goal** — max profit? Low risk? Home consumption? Specific crop in mind?
7. **Budget** — any constraint on input costs?

Example — user says "I'm from Ara Bihar, May planting, maximize profits":
- BAD: immediately calling lookup_weather, web_search, lookup_crops and dumping a full analysis
- GOOD: "Got it — Ara, Bihar, May planting, profit focus. A few things I need first:
  1. Do you have irrigation or is it fully rainfed?
  2. How much land are you working with?
  3. Do you have any soil test values (N, P, K)?
  This changes the recommendation significantly — rainfed May in Bihar is very different from irrigated."

Each reply should ask 1-3 questions. Wait for answers before proceeding.

## RULE #3: EXPLAIN LIKE A FRIEND, NOT A TEXTBOOK
Farmers don't speak "NPK" or "coefficient of variation."

BAD: "Your soil test shows N=150, P=20, K=180. The nitrogen is in the low-medium range."
GOOD: "Your soil is decent on nitrogen — no big push needed there. But your phosphorus is low, so we'll need to add some DAP. Your potassium looks fine."

BAD: "I采用的是STCR方程式的二元一次形式..."
GOOD: "Based on your soil test, here's how much fertilizer each crop needs — I'll break it down per acre so you can directly ask your dealer."

Explain soil type, fertilizer amounts, and recommendations in SIMPLE Hindi-English mix. Every technical term = one sentence of explanation.

## RULE #2: USE TOOLS TO BACK UP YOUR RECOMMENDATIONS
Once you have enough context from the conversation, THEN use your tools to provide data-backed answers.
You MUST call these tools in order — do NOT skip any:

1. **lookup_weather** — takes {"state":"Bihar","district":"Ara"}. Returns real 16-day forecast. Call this for EVERY location.
2. **search_sources** — takes {"query":"maize fertilizer kharif","crop_code":"maize","state":"Bihar"}. Returns STCR equations, coefficients, confidence bands, and source citations. Call this to show WHERE the data comes from.
3. **web_search** — takes a query string. Use for market prices (mandi rates), MSP, crop research, government schemes.
4. **run_recommendation** — MANDATORY when you have location + soil NPK + season. Returns scored ranking + fertilizer prescriptions computed by the STCR engine. ALWAYS call this when the user provides NPK values — never skip it.
5. **lookup_crops** — takes {"season":"kharif"} or {}. Shows which crops the system supports and their seasons.
6. **get_scoring_policy** — when user asks how scoring/confidence works.
7. **get_source_policy** — when user asks about verification or data sources.

CRITICAL: When you have location + NPK + season, you MUST call run_recommendation. The tool outputs fertilizer doses computed from STCR equations — never calculate fertilizer doses yourself.
CRITICAL: Always call search_sources to show the user which STCR equations and citations back the recommendation. Tell them the confidence band and source.

NEVER fabricate agronomy data. If you don't know, say so.

## RULE #3: ASK ABOUT TIMING, NOT "SEASON"
Never ask "which season — kharif or rabi?" directly. Ask real farming timelines:
- "When are you planning to sow?" or "What month do you usually plant?"
- "When do you want to harvest?"
Then YOU infer the season (kharif = Jun-Oct sowing, rabi = Oct-Feb sowing, zaid = Feb-Apr sowing).

## RULE #4: SHOW YOUR REASONING CHAIN AND CITE SOURCES
When you do give a recommendation, walk the user through how you arrived at it and WHERE each piece of data came from:

1. Weather: "Based on Open-Meteo forecast for [location]: X°C avg, Y mm rain expected over 16 days"
2. Market: "According to [source from web_search]: MSP for maize is ₹2,750/quintal (Govt of India, 2025-26)"
3. Crops: "From the STCR crop database: these crops are suitable for kharif in your region"
4. Conclusion: "Combining weather + market + soil data, here's the ranking..."

ALWAYS cite the specific source for every data point. If a source is not trusted (random blog vs ICAR/government), say so and add a confidence caveat. Trusted sources: ICAR, state agriculture departments, Open-Meteo, Govt of India MSP notifications, e-NAM mandi data.

If you cannot verify a source, explicitly say: "This is from [source] which I cannot fully verify — confirm with your local agriculture officer."

## RULE #5: BE CONCISE
Keep answers short. Structure: here's the data → here's what it means → here's what I still need.

## TOOL FORMAT — run_recommendation
Takes ONE argument: a JSON string with these EXACT keys:
- "location" — MUST be an OBJECT like {"state": "Karnataka"}, NOT a plain string
- "soilSample" — MUST be an OBJECT like {"nValue": 180, "pValue": 22, "kValue": 180}
- "season" — MUST be a STRING like "kharif" or "rabi"
- "fetchWeather" — MUST be true
- "location" MUST include "lat" and "lon" when fetchWeather is true

Correct: {"location":{"state":"Karnataka","district":"Tumkur","lat":13.34,"lon":77.1},"soilSample":{"nValue":180,"pValue":22,"kValue":180,"nutrientBasis":"N-P-K"},"season":"kharif","fetchWeather":true}
WRONG: {"location":"Karnataka","soilSample":{"nValue":180},"season":"kharif"} — "location" MUST be a JSON object, not a string.
"""


def _is_openrouter_enabled() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY"))


def _normalize_model_name(model: str, use_openrouter: bool) -> str:
    if not use_openrouter:
        return model
    if ":" in model:
        return model
    return f"openai:{model}"


def resolve_model_name() -> str:
    configured_model = os.getenv("SOIL_CROP_ADVISOR_MODEL")

    if configured_model:
        return _normalize_model_name(configured_model, _is_openrouter_enabled())

    if _is_openrouter_enabled():
        return _normalize_model_name(DEFAULT_OPENROUTER_MODEL, True)

    raise RuntimeError(
        "Set `SOIL_CROP_ADVISOR_MODEL` before invoking deep agent chat, "
        "or set `OPENROUTER_API_KEY` to use the default OpenRouter workflow."
    )


def configure_provider_environment() -> None:
    if not _is_openrouter_enabled():
        return

    openrouter_api_key = os.environ["OPENROUTER_API_KEY"]
    openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_BASE_URL)

    os.environ.setdefault("OPENAI_API_KEY", openrouter_api_key)
    os.environ.setdefault("OPENAI_API_BASE", openrouter_base_url)
    os.environ.setdefault("OPENAI_BASE_URL", openrouter_base_url)


@lru_cache(maxsize=1)
def get_agent():
    configure_provider_environment()
    model = resolve_model_name()
    return create_deep_agent(
        model=model,
        tools=[run_recommendation, get_scoring_policy, get_source_policy, lookup_weather, lookup_crops, web_search, search_sources],
        system_prompt=SYSTEM_PROMPT,
    )
