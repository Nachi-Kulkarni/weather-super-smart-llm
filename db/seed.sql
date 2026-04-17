-- Dev/demo seed: scaffold coefficients — replace with verified ICAR STCR ingestion before production.
-- Safe to re-run: removes prior demo rows for the same IDs/codes, then inserts fresh rows.
-- Apply after `db/schema.sql`.

BEGIN;

DELETE FROM stcr_equation
WHERE source_doc_id = '11111111-1111-1111-1111-111111111101'::uuid;

DELETE FROM source_chunk
WHERE source_doc_id = '11111111-1111-1111-1111-111111111101'::uuid;

DELETE FROM crop
WHERE crop_code IN ('maize', 'wheat', 'rice', 'ragi', 'groundnut');

DELETE FROM source_document
WHERE id = '11111111-1111-1111-1111-111111111101'::uuid;

INSERT INTO source_document (
  id,
  doc_type,
  title,
  publisher,
  source_url,
  crop_tags,
  metadata
) VALUES (
  '11111111-1111-1111-1111-111111111101'::uuid,
  'manual',
  'SCAFFOLD: Karnataka demo coefficients (NOT verified ICAR STCR)',
  'Soil Crop Advisor — local dev seed',
  NULL,
  ARRAY['maize', 'wheat', 'rice', 'ragi', 'groundnut'],
  '{"warning": "Scaffold only. Ingest verified STCR rows and citations before farmer-facing use."}'::jsonb
);

INSERT INTO crop (
  id,
  crop_code,
  crop_name,
  crop_group,
  default_target_yield_value,
  default_target_yield_unit,
  notes
) VALUES
  ('22222222-2222-2222-2222-222222222201'::uuid, 'maize', 'Maize', 'cereal', 50.0, 'q/ha', 'Demo default yield — adjust per district STCR.'),
  ('22222222-2222-2222-2222-222222222202'::uuid, 'wheat', 'Wheat', 'cereal', 48.0, 'q/ha', 'Demo default yield — adjust per district STCR.'),
  ('22222222-2222-2222-2222-222222222203'::uuid, 'rice', 'Rice', 'cereal', 55.0, 'q/ha', 'Demo default yield — adjust per district STCR.'),
  ('22222222-2222-2222-2222-222222222204'::uuid, 'ragi', 'Ragi', 'millet', 25.0, 'q/ha', 'Demo default yield — adjust per district STCR.'),
  ('22222222-2222-2222-2222-222222222205'::uuid, 'groundnut', 'Groundnut', 'oilseed', 18.0, 'q/ha', 'Demo default yield — adjust per district STCR.');

INSERT INTO stcr_equation (
  crop_id,
  equation_family,
  geography_scope,
  state_name,
  district_name,
  agro_region_code,
  season_name,
  target_yield_unit,
  nutrient_basis,
  nr_n, nr_p, nr_k,
  cs_n, cs_p, cs_k,
  cf_n, cf_p, cf_k,
  c_org_n, c_org_p, c_org_k,
  raw_coefficients,
  validity_notes,
  confidence_band,
  source_doc_id,
  citation_text
) VALUES
(
  '22222222-2222-2222-2222-222222222201'::uuid,
  'STCR',
  'state',
  'Karnataka',
  NULL,
  NULL,
  'kharif',
  'q/ha',
  'N-P2O5-K2O',
  2.0, 1.0, 1.2,
  50.0, 25.0, 20.0,
  50.0, 50.0, 50.0,
  0.0, 0.0, 0.0,
  '{}'::jsonb,
  'Synthetic demo row for API tests — not an official STCR extract.',
  'B',
  '11111111-1111-1111-1111-111111111101'::uuid,
  'Dev seed: replace with district STCR citation text from ICAR source registry.'
),
(
  '22222222-2222-2222-2222-222222222202'::uuid,
  'STCR',
  'state',
  'Karnataka',
  NULL,
  NULL,
  'kharif',
  'q/ha',
  'N-P2O5-K2O',
  2.1, 1.05, 1.1,
  48.0, 24.0, 19.0,
  50.0, 50.0, 50.0,
  0.0, 0.0, 0.0,
  '{}'::jsonb,
  'Synthetic demo row for API tests — not an official STCR extract.',
  'B',
  '11111111-1111-1111-1111-111111111101'::uuid,
  'Dev seed: replace with district STCR citation text from ICAR source registry.'
),
(
  '22222222-2222-2222-2222-222222222203'::uuid,
  'STCR',
  'state',
  'Karnataka',
  NULL,
  NULL,
  'kharif',
  'q/ha',
  'N-P2O5-K2O',
  2.2, 1.0, 1.15,
  52.0, 26.0, 21.0,
  50.0, 50.0, 50.0,
  0.0, 0.0, 0.0,
  '{}'::jsonb,
  'Synthetic demo row for API tests — not an official STCR extract.',
  'B',
  '11111111-1111-1111-1111-111111111101'::uuid,
  'Dev seed: replace with district STCR citation text from ICAR source registry.'
),
(
  '22222222-2222-2222-2222-222222222204'::uuid,
  'STCR',
  'state',
  'Karnataka',
  NULL,
  NULL,
  'kharif',
  'q/ha',
  'N-P2O5-K2O',
  1.6, 0.8, 0.9,
  45.0, 22.0, 18.0,
  50.0, 50.0, 50.0,
  0.0, 0.0, 0.0,
  '{}'::jsonb,
  'Synthetic demo row for API tests — not an official STCR extract.',
  'B',
  '11111111-1111-1111-1111-111111111101'::uuid,
  'Dev seed: replace with district STCR citation text from ICAR source registry.'
),
(
  '22222222-2222-2222-2222-222222222205'::uuid,
  'STCR',
  'state',
  'Karnataka',
  NULL,
  NULL,
  'kharif',
  'q/ha',
  'N-P2O5-K2O',
  1.4, 0.9, 1.0,
  46.0, 23.0, 18.5,
  50.0, 50.0, 50.0,
  0.0, 0.0, 0.0,
  '{}'::jsonb,
  'Synthetic demo row for API tests — not an official STCR extract.',
  'B',
  '11111111-1111-1111-1111-111111111101'::uuid,
  'Dev seed: replace with district STCR citation text from ICAR source registry.'
);

INSERT INTO source_chunk (
  source_doc_id,
  chunk_type,
  chunk_text,
  state_name,
  crop_tags
) VALUES
(
  '11111111-1111-1111-1111-111111111101'::uuid,
  'note',
  'Maize (kharif) in Karnataka: maintain balanced NPK where soil tests show medium availability; verify against district STCR bulletins.',
  'Karnataka',
  ARRAY['maize']
),
(
  '11111111-1111-1111-1111-111111111101'::uuid,
  'note',
  'Wheat: typically rabi-dominant — this scaffold row is for API wiring only.',
  'Karnataka',
  ARRAY['wheat']
),
(
  '11111111-1111-1111-1111-111111111101'::uuid,
  'advisory',
  'Rice transplanted kharif: monitor water stress during tillering; fertilizer need scales with target yield and soil credits.',
  'Karnataka',
  ARRAY['rice']
);

COMMIT;
