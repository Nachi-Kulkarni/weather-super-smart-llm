# Soil-to-Crop Intelligence Advisor

## Problem
Farmers know their soil test values, but they still lack an actionable answer to:

- what crops are feasible on this soil, here, now,
- what fertilizer additions are needed for each crop,
- which crops are worth considering over the next season,
- how weather and local climate change the recommendation.

## Product thesis
Do not treat this as a pure chatbot.

- RAG retrieves the right agronomy rule, STCR equation, crop note, and citation.
- Deterministic code computes fertilizer recommendations, suitability scores, and heat maps.

## Primary users

- farmer,
- agri-advisor,
- FPO field officer,
- soil lab operator.

## Inputs

- location: village, district, or lat/lon,
- soil test values: at minimum N, P, K,
- preferred extended values: pH, EC, OC, S, Zn, Fe, Cu, Mn, B,
- season intent: now, kharif, rabi, or next 90 days,
- optional target yield,
- optional constraints such as water, duration, crop type, or price sensitivity.

## Outputs

For each feasible crop:

- feasibility score,
- nutrient-fit score,
- weather-risk score,
- local suitability score,
- fertilizer recommendation,
- expected input burden,
- confidence level,
- explanation with source references.

## Recommendation flow

1. Geo-filter by district, state, and agro-region.
2. Season-filter by sowing window and weather outlook.
3. Retrieve the best-fit rule in this order:
   - exact district STCR,
   - state STCR,
   - agro-region STCR,
   - package-of-practice fallback.
4. Compute fertilizer recommendation.
5. Compute weather risk.
6. Compute local adoption prior.
7. Compute market attractiveness.
8. Rank and explain the result.

## Confidence policy

- `A`: verified STCR equation with strong geography match,
- `B`: verified regional agronomy source without exact match,
- `C`: explicit fallback or approximation.

## MVP

- 5 to 10 crops,
- 1 to 2 states,
- manual soil value entry,
- district-level location mapping,
- IMD + Open-Meteo weather adapter,
- equation-backed crop ranking,
- heat map and what-if simulator.
