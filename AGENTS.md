# Soil Crop Advisor - Project Instructions

## Mission
Build a farmer-facing recommendation system that:
1. accepts soil test values and location,
2. retrieves scientifically grounded agronomy rules,
3. computes fertilizer recommendations deterministically,
4. ranks feasible crops with confidence and citations.

## Hard rules
- Never invent STCR equations.
- RAG retrieves rules and evidence only; math happens in code.
- Every recommendation must emit:
  - selected rule source
  - confidence band
  - scoring trace
- Prefer verified district/state/agro-region rules over generic fallbacks.
- If exact crop-region equations are missing, downgrade confidence and label the result clearly.

## Data contracts
- Normalize nutrients into a declared basis:
  - input basis may be N-P-K
  - compute basis must be explicit: N-P-K or N-P2O5-K2O
- Weather scoring must separate:
  - short-range forecast
  - seasonal prior
- Keep raw source payloads in storage for auditability.

## Engineering rules
- Backend: Python
- Web: Next.js + TypeScript
- DB: PostgreSQL
- Vector store: pgvector
- No business logic in React components.
- No agronomy equations embedded in prompt text.
- All equation logic must live in versioned code.

## Quality gates
- Add tests for:
  - unit normalization
  - equation selection
  - fertilizer calculation
  - ranking stability
  - confidence labeling
- Reject merges if citations/traces are missing from recommendation payloads.

## Output contract
For each crop option return:
- crop_id
- crop_name
- target_yield
- recommended_n
- recommended_p
- recommended_k
- nutrient_basis
- final_score
- confidence_band
- reasons[]
- citations[]
- trace_payload
