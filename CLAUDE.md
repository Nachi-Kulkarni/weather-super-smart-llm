# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Soil Crop Advisor — a monorepo for a farmer-facing recommendation system that combines verified agronomy retrieval (ICAR/STCR sources) with deterministic fertilizer computation. The system separates **retrieval** (finding the right rule/citation) from **math** (computing fertilizer doses in code). Do not embed agronomy equations in prompts; all equation logic lives in versioned Python code.

## Commands

### Python API backend
```bash
cd apps/api
source .venv/bin/activate        # Python 3.11 venv
pip install -e .[dev]            # install with dev deps
uvicorn soil_crop_advisor.main:app --reload --port 8000
```

### Run tests
```bash
# All backend tests (stdlib unittest — no external test runner needed)
cd apps/api && python -m unittest discover -s tests

# Single test file
cd apps/api && python -m unittest tests.test_normalization

# Single test case
cd apps/api && python -m unittest tests.test_normalization.TestNormalization.test_something
```

### Web frontend (Next.js)
```bash
npm install                       # from repo root
npm run dev:web                   # starts Next.js dev server
npm run build:web                 # production build
npm run typecheck:web             # TypeScript check
```

### Database
```bash
docker compose up -d              # PostgreSQL 16 + pgvector on :5432
# Schema: db/schema.sql | Seed: db/seed.sql
```

## Architecture

### Two-app monorepo
- **`apps/api/`** — Python (FastAPI) backend. Package name: `soil_crop_advisor`. Installed editable via `pyproject.toml`.
- **`apps/web/`** — Next.js 15 + React 19 + TypeScript frontend using `@assistant-ui/react` for chat.
- **`packages/shared-types/`** — Shared TypeScript recommendation contracts (`CropOption`, `HeatmapCell`, `RecommendationResponse`, etc.).
- **`db/`** — PostgreSQL schema (`schema.sql`) and seed data (`seed.sql`). Uses pgvector for RAG embeddings.

### Backend data flow (the critical path)

```
FastAPI endpoint (main.py)
  → service.py::build_response()
    → resolve_weather() — IMD + Open-Meteo integration
    → RecommendationEngine.recommend()
      → CatalogRepository.list_crops() / list_rules()
      → rule_selector.py::select_best_rule() — geography-priority matching
      → normalization.py — convert between N-P-K and N-P2O5-K2O bases
      → calculator.py::calculate_fertilizer_recommendation() — STCR formula
      → scoring.py::compute_scores() — weighted multi-factor scoring
    → rag/retrieval.py — optional vector/keyword/hybrid RAG
```

### Domain models (`domain/models.py`)
All domain types are frozen dataclasses: `Location`, `SoilSample`, `EquationRule`, `CropMetadata`, `RecommendationOption`, `HeatmapCell`, `CitationRef`, `RecommendationResponse`. API schemas (`api_schemas.py`) are Pydantic models using camelCase JSON keys; domain models use snake_case.

### Catalog repository pattern
`CatalogRepository` (abstract) → `InMemoryCatalogRepository` (demo data, no DB needed) or `PgCatalogRepository` (Postgres-backed). When `DATABASE_URL` is unset, the system falls back to `InMemoryCatalogRepository.demo_karnataka()` with scaffold coefficients. These demo coefficients are NOT verified ICAR STCR data.

### Deep agent chat
`deep_agent.py` uses the `deepagents` library (`create_deep_agent`) with three tools: `run_recommendation`, `get_scoring_policy`, `get_source_policy`. Provider config: set `OPENROUTER_API_KEY` for OpenRouter, or `SOIL_CROP_ADVISOR_MODEL` + provider-specific credentials for other providers. Streaming via `/chat/stream` uses LangGraph `astream_events` v2, emitting NDJSON lines (`text`, `reasoning`, `tool`, `error`, `done`).

### Frontend chat wiring
`apps/web/lib/chat-api.ts` → `/api/chat` route → FastAPI backend. The frontend uses `assistant-ui` with a custom backend runtime. Components: `assistant-panel.tsx`, `recommendation-probe.tsx`, `nutrient-heatmap.tsx`, `tool-trace-strip.tsx`.

### Subagent definitions (`.claude/agents/`)
Four specialist agents for Claude Code: `agronomy-retriever`, `weather-risk-analyst`, `recommendation-scorer`, `ui-contract-guardian`. Use these when a task needs domain-specific retrieval or validation.

## Key Domain Rules

- **Rule selection order**: district STCR → state STCR → agro-region STCR → package-of-practice fallback.
- **Confidence bands**: `A` = verified STCR + direct geography match; `B` = verified regional source without exact match; `C` = fallback approximation.
- **Scoring weights**: nutrient_fit (0.45), weather_feasibility (0.20), agro_region_fit (0.15), local_adoption (0.10), market_signal (0.05), input_burden (0.05).
- **Nutrient basis**: input may be N-P-K; compute basis is explicit (N-P-K or N-P2O5-K2O). `normalization.py` handles conversion.
- **STCR formula**: `dose = (NR/CF)*target_yield - (CS/CF)*soil_test_value - organic_credit`. NR = nutrient requirement, CS = contribution from soil, CF = contribution from fertilizer.

## Environment Variables

See `.env.example`. Key vars:
- `DATABASE_URL` — Postgres connection (unset → in-memory demo catalog)
- `OPENROUTER_API_KEY` + `OPENROUTER_BASE_URL` — for deep agent chat via OpenRouter
- `SOIL_CROP_ADVISOR_MODEL` — model string (default: `minimax/minimax-m2.7`)
- `OPENAI_API_KEY` — for RAG embeddings (falls back to OpenRouter key)
- `IMD_API_KEY` / `IMD_API_BASE_URL` — live IMD weather integration

## Important Caveats

- Demo coefficients are scaffold-only, not verified ICAR STCR. Do not treat recommendation outputs as field-ready agronomy guidance until verified source data is loaded.
- `langgraph.json` points at `langgraph_export.py:build_graph` for LangGraph-compatible deployment — this is an alternative deployment path, not the primary one. The primary app hookup is the FastAPI server.
- The frontend TypeScript types in `packages/shared-types/recommendation.ts` must stay in sync with the Python `api_schemas.py` Pydantic models. Both use camelCase JSON keys.
