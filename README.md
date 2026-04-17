# Soil Crop Advisor

Soil Crop Advisor is a starter monorepo for a farmer-facing recommendation system that combines:

- verified agronomy retrieval from ICAR/STCR and related sources,
- deterministic fertilizer computation,
- weather-aware crop ranking,
- an assistant-ui frontend on top of a deepagents-backed chat API.

The scaffold intentionally separates retrieval from math:

- retrieval finds the right rule, citation, and confidence context,
- code computes fertilizer doses, scores, and audit traces.

## Repo layout

```text
project_review_2/
  AGENTS.md
  CLAUDE.md
  langgraph.json
  apps/
    api/
    web/
  db/
    schema.sql
  docs/
    PRD.md
    scoring-spec.md
    source-register.md
  packages/
    agronomy-core/
    ingestion/
    scoring/
    shared-types/
    weather-clients/
  prompts/
    supervisor.md
```

## What is implemented

- a Postgres schema for sources, equations, soil samples, weather, market data, and recommendation audit logs,
- project-level Codex and Claude instructions,
- Claude-style specialist subagent definitions,
- a FastAPI starter API with `/health` and `/recommend`,
- a FastAPI `/chat` endpoint that invokes a deep agent with agronomy-safe tools,
- a deterministic Python recommendation engine with:
  - nutrient basis normalization,
  - rule selection by geography priority,
  - STCR-style fertilizer calculation from structured coefficients,
  - confidence-aware ranking and trace payload generation,
- shared TypeScript recommendation contracts,
- a Next.js web shell with:
  - assistant-ui custom backend wiring for deepagents,
  - a recommendation probe panel that calls the REST API.

## What is intentionally not bundled

- production STCR coefficients,
- production crop calendars,
- live IMD credentials or whitelisted API access,
- market and DES ingestion jobs.

Until verified source data is loaded, the API remains structurally useful but should not be treated as field-ready agronomy guidance.

## Quick start

### 1. Python API

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn soil_crop_advisor.main:app --reload --port 8000
```

### 2. Deep agent chat

OpenRouter is the default workflow in this scaffold:

```bash
export OPENROUTER_API_KEY=your-openrouter-key
export OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
export SOIL_CROP_ADVISOR_MODEL=minimax/minimax-m2.7
```

The backend will automatically map those values onto the OpenAI-compatible env vars that the deepagents stack expects and normalize the model id into the deepagents-compatible form.

If you want to use another provider, you can still set `SOIL_CROP_ADVISOR_MODEL` directly with the provider-specific deepagents model string and the matching provider credentials.

The web app uses assistant-ui's custom backend runtime and sends chat requests to the FastAPI `/chat` endpoint.

### 3. Optional LangGraph-compatible deployment

If you later want to deploy the deep agent through a LangGraph-compatible runtime, `langgraph.json` now points at the deep agent factory.

### 4. Web app

```bash
npm install
npm --workspace apps/web run dev
```

Create a `.env.local` from `.env.example` or set the equivalent environment variables.

## Validation

The backend tests are stdlib `unittest` so they can run without external test tooling once Python dependencies are available:

```bash
python3 -m unittest discover -s apps/api/tests
```

## Next implementation step

The highest-value follow-up is to load a small verified crop/rule set from the ICAR STCR corpus and wire it into both the deterministic repository layer and the deep agent tools.
