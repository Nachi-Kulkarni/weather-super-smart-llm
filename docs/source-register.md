# Source Register

| Source | Role | Status | Notes |
| --- | --- | --- | --- |
| ICAR AICRP-STCR corpus | Agronomy equation backbone | Required | Normalize into structured `stcr_equation` rows. |
| Soil Health Card schema/data | Soil sample vocabulary | Required | Preserve raw payloads for auditability. |
| Agro-ecological region layer | Geography and climate gating | Required | Use for feasibility filtering before scoring. |
| IMD APIs and agromet advisories | Authoritative India weather/advisory layer | Required | Some endpoints may require public-IP allowlisting. |
| Open-Meteo | Prototype weather fallback | Optional | Treat seasonal outputs as priors, not deterministic farm truth. |
| DES crop area/production/yield | Local adoption prior | Recommended | Useful for district crop priors. |
| data.gov.in mandi prices | Market signal | Recommended | Use as a lightweight market-aware ranker. |

## Ingestion rules

- Never store an equation as verified if coefficients are missing or inferred from prose.
- Store raw documents and chunked extracts separately.
- Preserve publisher, URL, publication date, checksum, and geography tags.
- Mark each source-derived rule with an explicit confidence band.

## Starter scaffold note

This repo scaffold includes the schema and code pathways for all of the above, but no bundled production agronomy data.
