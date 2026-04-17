CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- ----------------------------
-- Reference dimensions
-- ----------------------------

CREATE TABLE admin_location (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  country_code TEXT NOT NULL DEFAULT 'IN',
  state_name TEXT NOT NULL,
  district_name TEXT,
  subdistrict_name TEXT,
  village_name TEXT,
  latitude NUMERIC(9,6),
  longitude NUMERIC(9,6),
  UNIQUE (state_name, district_name, subdistrict_name, village_name)
);

CREATE TABLE agro_ecological_region (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  region_code TEXT UNIQUE NOT NULL,
  region_name TEXT NOT NULL,
  subregion_code TEXT,
  subregion_name TEXT,
  source_name TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE crop (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_code TEXT UNIQUE NOT NULL,
  crop_name TEXT NOT NULL,
  scientific_name TEXT,
  crop_group TEXT,
  is_horticulture BOOLEAN NOT NULL DEFAULT FALSE,
  is_perennial BOOLEAN NOT NULL DEFAULT FALSE,
  default_duration_days INT,
  default_target_yield_value NUMERIC(12,4),
  default_target_yield_unit TEXT,
  notes TEXT
);

CREATE TABLE crop_alias (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_id UUID NOT NULL REFERENCES crop(id) ON DELETE CASCADE,
  alias TEXT NOT NULL,
  UNIQUE (crop_id, alias)
);

CREATE TABLE crop_calendar (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_id UUID NOT NULL REFERENCES crop(id) ON DELETE CASCADE,
  state_name TEXT,
  district_name TEXT,
  agro_region_code TEXT,
  season_name TEXT NOT NULL,
  sowing_start_month INT,
  sowing_end_month INT,
  harvest_start_month INT,
  harvest_end_month INT,
  source_doc_id UUID,
  confidence_band TEXT NOT NULL DEFAULT 'B'
);

CREATE TABLE crop_region_suitability (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_id UUID NOT NULL REFERENCES crop(id) ON DELETE CASCADE,
  state_name TEXT,
  district_name TEXT,
  agro_region_code TEXT,
  preferred_ph_min NUMERIC(5,2),
  preferred_ph_max NUMERIC(5,2),
  rainfall_min_mm NUMERIC(10,2),
  rainfall_max_mm NUMERIC(10,2),
  temp_min_c NUMERIC(5,2),
  temp_max_c NUMERIC(5,2),
  soil_types TEXT[],
  irrigation_required BOOLEAN,
  source_doc_id UUID,
  confidence_band TEXT NOT NULL DEFAULT 'B'
);

-- ----------------------------
-- Source registry + RAG store
-- ----------------------------

CREATE TABLE source_document (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  doc_type TEXT NOT NULL,
  title TEXT NOT NULL,
  publisher TEXT,
  source_url TEXT,
  published_on DATE,
  state_name TEXT,
  district_name TEXT,
  crop_tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  checksum_sha256 TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE source_chunk (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_doc_id UUID NOT NULL REFERENCES source_document(id) ON DELETE CASCADE,
  chunk_type TEXT NOT NULL,
  chunk_text TEXT NOT NULL,
  embedding VECTOR(1536),
  state_name TEXT,
  district_name TEXT,
  agro_region_code TEXT,
  crop_tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  numeric_entities JSONB NOT NULL DEFAULT '{}'::jsonb,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX source_chunk_source_doc_idx ON source_chunk(source_doc_id);
CREATE INDEX source_chunk_chunk_type_idx ON source_chunk(chunk_type);
CREATE INDEX source_chunk_crop_tags_gin ON source_chunk USING GIN (crop_tags);
CREATE INDEX source_chunk_metadata_gin ON source_chunk USING GIN (metadata);

-- ----------------------------
-- STCR / equation layer
-- ----------------------------

CREATE TABLE stcr_equation (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_id UUID NOT NULL REFERENCES crop(id) ON DELETE CASCADE,
  equation_family TEXT NOT NULL,
  geography_scope TEXT NOT NULL,
  state_name TEXT,
  district_name TEXT,
  agro_region_code TEXT,
  soil_order TEXT,
  soil_type TEXT,
  season_name TEXT,
  target_yield_unit TEXT NOT NULL,
  nutrient_basis TEXT NOT NULL,
  target_yield_min NUMERIC(12,4),
  target_yield_max NUMERIC(12,4),
  n_formula_text TEXT,
  p_formula_text TEXT,
  k_formula_text TEXT,
  nr_n NUMERIC(12,6),
  nr_p NUMERIC(12,6),
  nr_k NUMERIC(12,6),
  cs_n NUMERIC(12,6),
  cs_p NUMERIC(12,6),
  cs_k NUMERIC(12,6),
  cf_n NUMERIC(12,6),
  cf_p NUMERIC(12,6),
  cf_k NUMERIC(12,6),
  c_org_n NUMERIC(12,6),
  c_org_p NUMERIC(12,6),
  c_org_k NUMERIC(12,6),
  raw_coefficients JSONB NOT NULL DEFAULT '{}'::jsonb,
  validity_notes TEXT,
  confidence_band TEXT NOT NULL DEFAULT 'A',
  source_doc_id UUID REFERENCES source_document(id),
  citation_text TEXT
);

CREATE INDEX stcr_equation_lookup_idx
  ON stcr_equation(crop_id, equation_family, geography_scope, state_name, district_name, agro_region_code, season_name);

-- ----------------------------
-- Soil samples
-- ----------------------------

CREATE TABLE soil_sample (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_ref TEXT,
  farmer_ref TEXT,
  location_id UUID REFERENCES admin_location(id),
  sample_date DATE NOT NULL,
  n_value NUMERIC(12,4),
  p_value NUMERIC(12,4),
  k_value NUMERIC(12,4),
  s_value NUMERIC(12,4),
  zn_value NUMERIC(12,4),
  fe_value NUMERIC(12,4),
  cu_value NUMERIC(12,4),
  mn_value NUMERIC(12,4),
  b_value NUMERIC(12,4),
  ph_value NUMERIC(5,2),
  ec_value NUMERIC(12,4),
  oc_value NUMERIC(12,4),
  value_unit_system TEXT NOT NULL DEFAULT 'lab_raw',
  source_name TEXT NOT NULL,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  normalized_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX soil_sample_farmer_idx ON soil_sample(farmer_ref);
CREATE INDEX soil_sample_location_idx ON soil_sample(location_id);
CREATE INDEX soil_sample_date_idx ON soil_sample(sample_date);

-- ----------------------------
-- Weather
-- ----------------------------

CREATE TABLE weather_run (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  location_id UUID REFERENCES admin_location(id),
  latitude NUMERIC(9,6) NOT NULL,
  longitude NUMERIC(9,6) NOT NULL,
  source_name TEXT NOT NULL,
  horizon_days INT NOT NULL,
  requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE weather_day (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  weather_run_id UUID NOT NULL REFERENCES weather_run(id) ON DELETE CASCADE,
  forecast_date DATE NOT NULL,
  tmin_c NUMERIC(6,2),
  tmax_c NUMERIC(6,2),
  precipitation_mm NUMERIC(10,2),
  rain_probability NUMERIC(6,2),
  relative_humidity_pct NUMERIC(6,2),
  wind_speed_kmph NUMERIC(6,2),
  solar_radiation_mj NUMERIC(10,2),
  weather_code TEXT,
  UNIQUE (weather_run_id, forecast_date)
);

CREATE TABLE seasonal_outlook (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  weather_run_id UUID NOT NULL REFERENCES weather_run(id) ON DELETE CASCADE,
  month_label TEXT NOT NULL,
  rainfall_anomaly_class TEXT,
  temperature_anomaly_class TEXT,
  source_name TEXT NOT NULL,
  confidence_notes TEXT
);

-- ----------------------------
-- Market + crop history
-- ----------------------------

CREATE TABLE mandi_price (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_id UUID REFERENCES crop(id),
  state_name TEXT NOT NULL,
  district_name TEXT,
  market_name TEXT NOT NULL,
  variety TEXT,
  grade TEXT,
  arrival_date DATE NOT NULL,
  min_price NUMERIC(12,2),
  max_price NUMERIC(12,2),
  modal_price NUMERIC(12,2),
  source_name TEXT NOT NULL DEFAULT 'data.gov.in'
);

CREATE INDEX mandi_price_crop_date_idx ON mandi_price(crop_id, arrival_date DESC);

CREATE TABLE crop_production_stat (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_id UUID REFERENCES crop(id),
  state_name TEXT NOT NULL,
  district_name TEXT,
  season_name TEXT,
  agri_year TEXT NOT NULL,
  area_ha NUMERIC(14,2),
  production_tonnes NUMERIC(14,2),
  yield_value NUMERIC(14,4),
  yield_unit TEXT,
  source_name TEXT NOT NULL
);

CREATE INDEX crop_production_lookup_idx
  ON crop_production_stat(crop_id, state_name, district_name, season_name, agri_year);

-- ----------------------------
-- Fertilizer materials
-- ----------------------------

CREATE TABLE fertilizer_material (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  material_code TEXT UNIQUE NOT NULL,
  material_name TEXT NOT NULL,
  material_type TEXT NOT NULL,
  notes TEXT
);

CREATE TABLE fertilizer_material_nutrient (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  material_id UUID NOT NULL REFERENCES fertilizer_material(id) ON DELETE CASCADE,
  nutrient_code TEXT NOT NULL,
  percentage_value NUMERIC(8,4) NOT NULL,
  UNIQUE (material_id, nutrient_code)
);

-- ----------------------------
-- Recommendation audit
-- ----------------------------

CREATE TABLE recommendation_run (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  soil_sample_id UUID NOT NULL REFERENCES soil_sample(id),
  weather_run_id UUID REFERENCES weather_run(id),
  user_query JSONB NOT NULL DEFAULT '{}'::jsonb,
  scoring_version TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE recommendation_option (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recommendation_run_id UUID NOT NULL REFERENCES recommendation_run(id) ON DELETE CASCADE,
  crop_id UUID NOT NULL REFERENCES crop(id),
  rank_position INT NOT NULL,
  target_yield_value NUMERIC(12,4),
  target_yield_unit TEXT,
  recommended_n NUMERIC(12,4),
  recommended_p NUMERIC(12,4),
  recommended_k NUMERIC(12,4),
  nutrient_basis TEXT NOT NULL,
  nutrient_fit_score NUMERIC(6,4) NOT NULL,
  weather_feasibility_score NUMERIC(6,4) NOT NULL,
  agro_region_fit_score NUMERIC(6,4) NOT NULL,
  local_adoption_score NUMERIC(6,4) NOT NULL,
  market_signal_score NUMERIC(6,4) NOT NULL,
  input_burden_score NUMERIC(6,4) NOT NULL,
  final_score NUMERIC(6,4) NOT NULL,
  confidence_band TEXT NOT NULL,
  reason_summary TEXT NOT NULL,
  trace_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX recommendation_option_run_rank_idx
  ON recommendation_option(recommendation_run_id, rank_position);

-- ----------------------------
-- Suggested seed data contracts
-- ----------------------------

CREATE TABLE ingestion_job (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_name TEXT NOT NULL,
  source_name TEXT NOT NULL,
  job_status TEXT NOT NULL,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
  error_text TEXT
);
