# agronomy-core

Domain logic (normalization, STCR calculator, scoring, rule selection) ships inside the API package:

- `apps/api/soil_crop_advisor/domain/`

This directory is reserved if you later split a shared Python wheel for ingestion workers and the API.
