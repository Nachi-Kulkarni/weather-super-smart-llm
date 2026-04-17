from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from .api_schemas import (
    ChatRequest,
    ChatResponse,
    RecommendationResponseModel,
    RecommendRequest,
    ToolEventModel,
)
from .chat_stream import stream_chat_ndjson
from .db.pool import close_pool
from .deep_agent import get_agent, tool_trace_session
from .env import load_repo_env
from .logging_config import setup_logging
from .service import SCORING_VERSION, build_response

load_repo_env()

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    yield
    close_pool()


app = FastAPI(
    title="Soil Crop Advisor API",
    version=SCORING_VERSION,
    description="Deterministic recommendation API scaffold for soil-to-crop intelligence.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/recommend", response_model=RecommendationResponseModel)
def recommend(payload: RecommendRequest) -> RecommendationResponseModel:
    return build_response(payload)


def _parts_to_text(content: list[dict[str, object]] | str) -> str:
    if isinstance(content, str):
        return content

    chunks: list[str] = []
    for part in content:
        if part.get("type") == "text" and isinstance(part.get("text"), str):
            chunks.append(str(part["text"]))
    return "\n".join(chunk for chunk in chunks if chunk)


def _normalize_messages(payload: ChatRequest) -> list[dict[str, str]]:
    normalized_messages: list[dict[str, str]] = []
    for message in payload.messages:
        text = _parts_to_text(message.content)
        if text.strip():
            normalized_messages.append({"role": message.role, "content": text})
    return normalized_messages


def _message_content_to_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text = part.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return str(content)


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    messages = _normalize_messages(payload)
    if not messages:
        return ChatResponse(
            text="Share a soil sample, location, or recommendation question to get started.",
            toolEvents=[],
        )

    _logger.info("chat request: %d messages, last user msg: %s",
                 len(messages), messages[-1]["content"][:120] if messages[-1]["role"] == "user" else "(assistant)")

    t0 = time.time()
    with tool_trace_session() as tool_events:
        try:
            result = get_agent().invoke({"messages": messages})
            last_message = result["messages"][-1]
            content = getattr(last_message, "content", "")
            text = _message_content_to_text(content)
        except Exception as exc:
            _logger.exception("deep agent chat failed")
            text = (
                "Deep agent chat is configured, but it could not run yet. "
                "Set `SOIL_CROP_ADVISOR_MODEL` plus the matching provider API key, "
                "or set `OPENROUTER_API_KEY` to use the default OpenRouter workflow, then retry. "
                f"Underlying error: {exc}"
            )

    events = [ToolEventModel.model_validate(event) for event in tool_events]
    elapsed = time.time() - t0
    _logger.info("chat response: %.1fs, %d tool events, %d chars text",
                 elapsed, len(events), len(text))
    return ChatResponse(text=text, toolEvents=events)


@app.post("/chat/stream")
async def chat_stream(payload: ChatRequest) -> StreamingResponse:
    """NDJSON stream: `text`/`reasoning`/`tool` lines, then final `done` (see `chat_stream.py`)."""
    messages = _normalize_messages(payload)

    async def body():
        if not messages:
            line = json.dumps(
                {
                    "type": "done",
                    "fullText": "Share a soil sample, location, or recommendation question to get started.",
                    "toolEvents": [],
                },
                ensure_ascii=False,
            )
            yield (line + "\n").encode("utf-8")
            return
        async for line in stream_chat_ndjson(messages):
            yield line.encode("utf-8")

    return StreamingResponse(
        body(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
