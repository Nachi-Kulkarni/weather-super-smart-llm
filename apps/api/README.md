# API

The API app exposes:

- `GET /health` for liveness,
- `POST /recommend` for deterministic recommendation runs,
- `POST /chat` for deepagents-backed conversational orchestration,
- `apps/api/soil_crop_advisor/deep_agent.py` as the deep agent entrypoint referenced by `langgraph.json`.

The starter engine is intentionally data-safe:

- it supports structured STCR-style coefficients,
- it does not bundle production agronomy equations,
- it refuses to manufacture recommendations when verified rules are unavailable.
