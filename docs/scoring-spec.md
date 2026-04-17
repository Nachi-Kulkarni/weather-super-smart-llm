# Scoring Spec

## Equation selection order
1. district STCR
2. state STCR
3. agro-region STCR
4. government package-of-practice fallback
5. heuristic fallback disabled by default in production

## Weather interpretation
- 0 to 14 days: deterministic forecast contribution
- 15 to 90 days: seasonal or anomaly prior contribution
- seasonal outlook must never be shown as daily certainty

## Confidence bands
- A: verified STCR equation + direct geography match
- B: verified regional agronomy source but not exact equation match
- C: fallback approximation with explicit warning

## Heat-map semantics
- delta values are fertilizer recommendation outputs, not pure soil chemistry deltas
- colors map to input burden thresholds
