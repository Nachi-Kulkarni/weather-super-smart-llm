from __future__ import annotations

import os
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Iterator

from deepagents import create_deep_agent

from .api_schemas import RecommendRequest
from .service import SCORING_VERSION, build_response

DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "minimax/minimax-m2.7"

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

    `request_json` must be a single JSON object matching RecommendRequest (camelCase keys):
    location (state, district, optional lat/lon), soilSample (nValue, pValue, kValue, nutrientBasis),
    season, optional candidateCropCodes, includeRetrieval, ragMode (keyword|vector|hybrid).

    Example:
    {"location":{"state":"Karnataka","district":"Tumkur"},"soilSample":{"nValue":180,"pValue":24,"kValue":210,"nutrientBasis":"N-P-K"},"season":"kharif","includeRetrieval":true,"ragMode":"hybrid"}
    """
    payload = RecommendRequest.model_validate_json(request_json)
    response = build_response(payload)
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


SYSTEM_PROMPT = """\
You are Soil Crop Advisor, a deep agent for agronomy-safe recommendation workflows.

Rules:
- Never invent STCR equations or fertilizer coefficients.
- Use the run_recommendation tool whenever the user provides soil values, location, season, or asks for ranked crop options.
  Pass one JSON string argument using camelCase keys (soilSample.nValue, not soil.N); see the tool description for a minimal example.
- Use get_scoring_policy when the user asks how scoring or confidence works.
- Use get_source_policy when the user asks about verification, evidence, or safety.
- Present fertilizer recommendation as the main agronomic output, followed by confidence, reasons, and cautions.
- Be concise, practical, and explicit about missing verified data.
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
        tools=[run_recommendation, get_scoring_policy, get_source_policy],
        system_prompt=SYSTEM_PROMPT,
    )
