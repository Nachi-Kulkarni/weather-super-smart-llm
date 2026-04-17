-- Dev/demo seed: scaffold coefficients — replace with verified ICAR STCR ingestion before production.
-- Safe to re-run: removes prior demo rows for the same IDs/codes, then inserts fresh rows.
-- Apply after `db/schema.sql`.

BEGIN;

DELETE FROM stcr_equation
WHERE source_doc_id IN ('11111111-1111-1111-1111-111111111101'::uuid, '11111111-1111-1111-1111-111111111102'::uuid);

DELETE FROM source_chunk
WHERE source_doc_id IN ('11111111-1111-1111-1111-111111111101'::uuid, '11111111-1111-1111-1111-111111111102'::uuid);

DELETE FROM crop
WHERE crop_code IN ('maize', 'wheat', 'rice', 'ragi', 'groundnut');

DELETE FROM source_document
WHERE id IN ('11111111-1111-1111-1111-111111111101'::uuid, '11111111-1111-1111-1111-111111111102'::uuid);

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
  'rabi',
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

-- Crop calendars: which season each crop is actually grown in Karnataka
INSERT INTO crop_calendar (crop_id, state_name, season_name, confidence_band)
VALUES
  ('22222222-2222-2222-2222-222222222201'::uuid, 'Karnataka', 'kharif', 'B'),
  ('22222222-2222-2222-2222-222222222201'::uuid, 'Karnataka', 'rabi',   'B'),
  ('22222222-2222-2222-2222-222222222202'::uuid, 'Karnataka', 'rabi',   'B'),
  ('22222222-2222-2222-2222-222222222203'::uuid, 'Karnataka', 'kharif', 'B'),
  ('22222222-2222-2222-2222-222222222204'::uuid, 'Karnataka', 'kharif', 'B'),
  ('22222222-2222-2222-2222-222222222204'::uuid, 'Karnataka', 'rabi',   'B'),
  ('22222222-2222-2222-2222-222222222205'::uuid, 'Karnataka', 'kharif', 'B'),
  ('22222222-2222-2222-2222-222222222205'::uuid, 'Karnataka', 'rabi',   'B')
ON CONFLICT DO NOTHING;

-- =====================================================================
-- Bihar scaffold data
-- =====================================================================

INSERT INTO source_document (
  id, doc_type, title, publisher, source_url, crop_tags, metadata
) VALUES (
  '11111111-1111-1111-1111-111111111102'::uuid,
  'manual',
  'SCAFFOLD: Bihar demo coefficients (NOT verified ICAR STCR)',
  'Soil Crop Advisor — local dev seed',
  NULL,
  ARRAY['maize', 'wheat', 'rice', 'ragi', 'groundnut'],
  '{"warning": "Bihar scaffold only — based on ICAR-IISR alluvial soil zone estimates. Replace with verified Bhojpur/Ara district STCR."}'::jsonb
);

-- Bihar STCR equations (kharif)
INSERT INTO stcr_equation (
  crop_id, equation_family, geography_scope, state_name, district_name,
  agro_region_code, season_name, target_yield_unit, nutrient_basis,
  nr_n, nr_p, nr_k, cs_n, cs_p, cs_k, cf_n, cf_p, cf_k,
  c_org_n, c_org_p, c_org_k, raw_coefficients, validity_notes,
  confidence_band, source_doc_id, citation_text
) VALUES
-- Maize kharif Bihar
('22222222-2222-2222-2222-222222222201'::uuid, 'STCR', 'state', 'Bihar', NULL, NULL,
 'kharif', 'q/ha', 'N-P2O5-K2O',
 2.3, 0.95, 1.1,  48.0, 22.0, 19.0,  50.0, 50.0, 50.0,  0.0, 0.0, 0.0,
 '{}'::jsonb, 'Bihar scaffold: ICAR-IISR alluvial soil zone estimates — not verified district STCR.',
 'B', '11111111-1111-1111-1111-111111111102'::uuid,
 'Bihar scaffold based on ICAR-IISR alluvial soil zone. Replace with Bhojpur/Ara district STCR bulletin.'),
-- Rice kharif Bihar
('22222222-2222-2222-2222-222222222203'::uuid, 'STCR', 'state', 'Bihar', NULL, NULL,
 'kharif', 'q/ha', 'N-P2O5-K2O',
 2.4, 1.1, 1.2,  55.0, 28.0, 22.0,  50.0, 50.0, 50.0,  0.0, 0.0, 0.0,
 '{}'::jsonb, 'Bihar scaffold: ICAR-IISR alluvial soil zone estimates — not verified district STCR.',
 'B', '11111111-1111-1111-1111-111111111102'::uuid,
 'Bihar scaffold based on ICAR-IISR alluvial soil zone. Replace with Bhojpur/Ara district STCR bulletin.'),
-- Ragi kharif Bihar
('22222222-2222-2222-2222-222222222204'::uuid, 'STCR', 'state', 'Bihar', NULL, NULL,
 'kharif', 'q/ha', 'N-P2O5-K2O',
 1.7, 0.75, 0.85,  42.0, 20.0, 17.0,  50.0, 50.0, 50.0,  0.0, 0.0, 0.0,
 '{}'::jsonb, 'Bihar scaffold: ICAR-IISR alluvial soil zone estimates — not verified district STCR.',
 'B', '11111111-1111-1111-1111-111111111102'::uuid,
 'Bihar scaffold based on ICAR-IISR alluvial soil zone. Replace with Bhojpur/Ara district STCR bulletin.'),
-- Groundnut kharif Bihar
('22222222-2222-2222-2222-222222222205'::uuid, 'STCR', 'state', 'Bihar', NULL, NULL,
 'kharif', 'q/ha', 'N-P2O5-K2O',
 1.5, 1.0, 1.1,  44.0, 24.0, 19.0,  50.0, 50.0, 50.0,  0.0, 0.0, 0.0,
 '{}'::jsonb, 'Bihar scaffold: ICAR-IISR alluvial soil zone estimates — not verified district STCR.',
 'B', '11111111-1111-1111-1111-111111111102'::uuid,
 'Bihar scaffold based on ICAR-IISR alluvial soil zone. Replace with Bhojpur/Ara district STCR bulletin.'),
-- Wheat rabi Bihar
('22222222-2222-2222-2222-222222222202'::uuid, 'STCR', 'state', 'Bihar', NULL, NULL,
 'rabi', 'q/ha', 'N-P2O5-K2O',
 2.5, 1.2, 1.15,  50.0, 26.0, 20.0,  50.0, 50.0, 50.0,  0.0, 0.0, 0.0,
 '{}'::jsonb, 'Bihar scaffold: ICAR-IISR alluvial soil zone estimates — not verified district STCR.',
 'B', '11111111-1111-1111-1111-111111111102'::uuid,
 'Bihar scaffold based on ICAR-IISR alluvial soil zone. Replace with Bhojpur/Ara district STCR bulletin.'),
-- Maize rabi Bihar
('22222222-2222-2222-2222-222222222201'::uuid, 'STCR', 'state', 'Bihar', NULL, NULL,
 'rabi', 'q/ha', 'N-P2O5-K2O',
 2.2, 1.0, 1.05,  47.0, 23.0, 18.5,  50.0, 50.0, 50.0,  0.0, 0.0, 0.0,
 '{}'::jsonb, 'Bihar scaffold: ICAR-IISR alluvial soil zone estimates — not verified district STCR.',
 'B', '11111111-1111-1111-1111-111111111102'::uuid,
 'Bihar scaffold based on ICAR-IISR alluvial soil zone. Replace with Bhojpur/Ara district STCR bulletin.');

-- Bihar source chunks (RAG)
INSERT INTO source_chunk (source_doc_id, chunk_type, chunk_text, state_name, crop_tags) VALUES
('11111111-1111-1111-1111-111111111102'::uuid, 'advisory',
 'Maize (kharif) in Bihar: Indo-Gangetic alluvial soils are typically low in N and P. Apply basal DAP at sowing followed by split urea doses at knee-high and tasseling stage. Target 50-60 q/ha with hybrid varieties.',
 'Bihar', ARRAY['maize']),
('11111111-1111-1111-1111-111111111102'::uuid, 'advisory',
 'Rice (kharif) in Bihar: Transplant by mid-July after monsoon onset. Low N soils need 80-120 kg N/ha. P deficiency common — apply DAP basal. Zinc sulphate recommended for Bhojpur district alluvial soils.',
 'Bihar', ARRAY['rice']),
('11111111-1111-1111-1111-111111111102'::uuid, 'note',
 'Wheat (rabi) is the dominant Bihar crop. Sow November, harvest March-April. High N requirement (120-150 kg/ha). Bihar plains benefit from late irrigation at grain-filling stage.',
 'Bihar', ARRAY['wheat']),
('11111111-1111-1111-1111-111111111102'::uuid, 'note',
 'Groundnut in Bihar kharif: well-drained sandy loam preferred. Low P soils need heavy basal P correction. Row spacing 30cm, seed rate 80-100 kg/ha.',
 'Bihar', ARRAY['groundnut']);

-- Bihar crop calendars
INSERT INTO crop_calendar (crop_id, state_name, season_name, confidence_band)
VALUES
  ('22222222-2222-2222-2222-222222222201'::uuid, 'Bihar', 'kharif', 'B'),
  ('22222222-2222-2222-2222-222222222201'::uuid, 'Bihar', 'rabi',   'B'),
  ('22222222-2222-2222-2222-222222222202'::uuid, 'Bihar', 'rabi',   'B'),
  ('22222222-2222-2222-2222-222222222203'::uuid, 'Bihar', 'kharif', 'B'),
  ('22222222-2222-2222-2222-222222222204'::uuid, 'Bihar', 'kharif', 'B'),
  ('22222222-2222-2222-2222-222222222205'::uuid, 'Bihar', 'kharif', 'B')
ON CONFLICT DO NOTHING;

COMMIT;
