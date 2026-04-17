"""
LangGraph CLI / Platform entrypoint.

Run from repo with `apps/api` on PYTHONPATH, e.g.:

  cd apps/api && PYTHONPATH=. langgraph dev --config ../../langgraph.json

Or import `build_graph` in LangGraph Cloud / Studio configs.
"""

from __future__ import annotations

from typing import Any


def build_graph() -> Any:
    """Return the compiled deep agent graph (`messages` state key preserved)."""
    from soil_crop_advisor.deep_agent import get_agent

    return get_agent()
