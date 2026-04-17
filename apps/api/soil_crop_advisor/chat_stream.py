"""
NDJSON streaming for `/chat/stream` using LangGraph `astream_events` (v2).

Emits:
- `text` deltas for assistant tokens (from chat model stream)
- `reasoning` snippets when the model exposes reasoning blocks (e.g. OpenRouter / o1-style)
- `tool` rows aligned with ToolEventModel (start/end/error)
- `error` on failure
- `done` with fullText + toolEvents for clients that want a final snapshot
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

_logger = logging.getLogger(__name__)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _blocks_from_chunk(chunk: Any) -> list[dict[str, Any]]:
    """Normalize AIMessageChunk.content into a list of content blocks."""
    raw = getattr(chunk, "content", None)
    if raw is None:
        return []
    if isinstance(raw, str):
        if not raw.strip():
            return []
        return [{"type": "text", "text": raw}]
    if isinstance(raw, list):
        out: list[dict[str, Any]] = []
        for item in raw:
            if isinstance(item, dict):
                out.append(item)
        return out
    return []


def _reasoning_preview(block: dict[str, Any]) -> str | None:
    """Best-effort human snippet from a provider reasoning block."""
    if block.get("text"):
        return str(block["text"])
    summary = block.get("summary")
    if isinstance(summary, list) and summary:
        return json.dumps(summary, ensure_ascii=False)[:2000]
    status = block.get("status")
    if status:
        return f"[reasoning {status}]"
    return None


async def stream_chat_ndjson(
    messages: list[dict[str, str]],
) -> AsyncIterator[str]:
    """
    Yield newline-delimited JSON objects (UTF-8). Each line is one JSON value.
    """
    from .deep_agent import get_agent

    agent = get_agent()
    full_text_parts: list[str] = []
    tool_events: list[dict[str, Any]] = []

    def emit(obj: dict[str, Any]) -> str:
        return json.dumps(obj, ensure_ascii=False) + "\n"

    try:
        async for ev in agent.astream_events({"messages": messages}, version="v2"):
            et = ev.get("event")
            if et == "on_chat_model_stream":
                chunk = ev.get("data", {}).get("chunk")
                if chunk is None:
                    continue
                for block in _blocks_from_chunk(chunk):
                    btype = block.get("type")
                    if btype == "text":
                        t = block.get("text") or ""
                        if t:
                            full_text_parts.append(t)
                            yield emit({"type": "text", "delta": t})
                    elif btype == "reasoning":
                        preview = _reasoning_preview(block)
                        payload = {
                            "type": "reasoning",
                            "delta": preview or json.dumps(block, ensure_ascii=False)[:2000],
                            "status": block.get("status"),
                        }
                        yield emit(payload)
            elif et == "on_tool_start":
                name = str(ev.get("name") or "tool")
                inp = ev.get("data", {}).get("input")
                detail: str | None
                if inp is None or inp == {}:
                    detail = None
                else:
                    try:
                        detail = json.dumps(inp, ensure_ascii=False)
                    except TypeError:
                        detail = str(inp)
                    if len(detail) > 6000:
                        detail = detail[:6000] + "…"
                rec = {
                    "tool": name,
                    "phase": "start",
                    "detail": detail,
                    "at": _iso_now(),
                }
                tool_events.append(rec)
                yield emit({"type": "tool", **rec})
            elif et == "on_tool_end":
                name = str(ev.get("name") or "tool")
                rec = {
                    "tool": name,
                    "phase": "end",
                    "detail": None,
                    "at": _iso_now(),
                }
                tool_events.append(rec)
                yield emit({"type": "tool", **rec})
            elif et == "on_tool_error":
                name = str(ev.get("name") or "tool")
                err = ev.get("data", {}).get("error")
                detail = str(err) if err is not None else "tool error"
                rec = {
                    "tool": name,
                    "phase": "error",
                    "detail": detail[:8000],
                    "at": _iso_now(),
                }
                tool_events.append(rec)
                yield emit({"type": "tool", **rec})
    except Exception as exc:  # noqa: BLE001
        _logger.exception("chat stream failed")
        yield emit({"type": "error", "message": str(exc)})
        yield emit(
            {
                "type": "done",
                "fullText": "".join(full_text_parts),
                "toolEvents": tool_events,
            }
        )
        return

    yield emit(
        {
            "type": "done",
            "fullText": "".join(full_text_parts),
            "toolEvents": tool_events,
        }
    )
