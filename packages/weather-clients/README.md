# weather-clients

Python implementation lives in the API package:

- `apps/api/soil_crop_advisor/integrations/open_meteo.py` — coordinate forecast + scoring split (0–14d vs 15–45d prior).
- `apps/api/soil_crop_advisor/integrations/imd_client.py` — IMD seam (requires allowlisting + credentials in production).

This folder remains a pointer so the monorepo layout matches the architecture diagram.
