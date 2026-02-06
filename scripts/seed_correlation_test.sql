BEGIN;

-- Fixed IDs for local testing
-- Tenant: 11111111-1111-1111-1111-111111111111
-- Identity: 22222222-2222-2222-2222-222222222222
-- Membership: 33333333-3333-3333-3333-333333333333
-- Farm: 44444444-4444-4444-4444-444444444444
-- AOI: 55555555-5555-5555-5555-555555555555

INSERT INTO identities (id, provider, subject, email, name, status)
VALUES ('22222222-2222-2222-2222-222222222222', 'local', 'local-user', 'local.user@vivacampo.com', 'Local User', 'ACTIVE')
ON CONFLICT DO NOTHING;

INSERT INTO tenants (id, type, name, status, plan)
VALUES ('11111111-1111-1111-1111-111111111111', 'COMPANY', 'VivaCampo Local Tenant', 'ACTIVE', 'BASIC')
ON CONFLICT DO NOTHING;

INSERT INTO memberships (id, tenant_id, identity_id, role, status)
VALUES ('33333333-3333-3333-3333-333333333333', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', 'TENANT_ADMIN', 'ACTIVE')
ON CONFLICT DO NOTHING;

INSERT INTO farms (id, tenant_id, name, timezone)
VALUES ('44444444-4444-4444-4444-444444444444', '11111111-1111-1111-1111-111111111111', 'Fazenda Local', 'America/Sao_Paulo')
ON CONFLICT DO NOTHING;

INSERT INTO aois (id, tenant_id, farm_id, name, use_type, status, geom, area_ha)
VALUES (
  '55555555-5555-5555-5555-555555555555',
  '11111111-1111-1111-1111-111111111111',
  '44444444-4444-4444-4444-444444444444',
  'AOI Local Teste',
  'CROP',
  'ACTIVE',
  ST_GeomFromText('MULTIPOLYGON(((-47.1000 -23.5000, -47.1000 -23.4900, -47.0900 -23.4900, -47.0900 -23.5000, -47.1000 -23.5000)))', 4326),
  50.0
)
ON CONFLICT DO NOTHING;

-- Radar table (if not already created by migrations)
CREATE TABLE IF NOT EXISTS derived_radar_assets (
    tenant_id UUID NOT NULL,
    aoi_id UUID NOT NULL,
    year INTEGER NOT NULL,
    week INTEGER NOT NULL,
    pipeline_version VARCHAR(50) NOT NULL,
    rvi_s3_uri TEXT,
    ratio_s3_uri TEXT,
    vh_s3_uri TEXT,
    vv_s3_uri TEXT,
    rvi_mean FLOAT,
    rvi_std FLOAT,
    ratio_mean FLOAT,
    ratio_std FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, aoi_id, year, week, pipeline_version)
);

-- Weather table (if not already created by migrations)
CREATE TABLE IF NOT EXISTS derived_weather_daily (
    tenant_id UUID NOT NULL,
    aoi_id UUID NOT NULL,
    date DATE NOT NULL,
    temp_max FLOAT,
    temp_min FLOAT,
    precip_sum FLOAT,
    et0_fao FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, aoi_id, date)
);

-- 14 weeks of synthetic data (current week and 13 prior)
WITH weeks AS (
  SELECT
    generate_series(0, 13) AS i,
    (current_date - (generate_series(0, 13) * 7 || ' days')::interval)::date AS d
)
INSERT INTO derived_assets (
  tenant_id, aoi_id, year, week, pipeline_version,
  ndvi_mean, ndvi_s3_uri, created_at
)
SELECT
  '11111111-1111-1111-1111-111111111111',
  '55555555-5555-5555-5555-555555555555',
  EXTRACT(ISOYEAR FROM d)::int,
  EXTRACT(WEEK FROM d)::int,
  'v1',
  CASE
    WHEN i = 3 THEN 0.40
    WHEN i = 4 THEN 0.58
    WHEN i = 7 THEN NULL
    WHEN i = 8 THEN 0.30
    ELSE 0.55 + (i * 0.01)
  END,
  's3://mock-bucket/ndvi-' || EXTRACT(ISOYEAR FROM d)::int || '-' || EXTRACT(WEEK FROM d)::int || '.tif',
  d::timestamptz
FROM weeks
ON CONFLICT DO NOTHING;

WITH weeks AS (
  SELECT
    generate_series(0, 13) AS i,
    (current_date - (generate_series(0, 13) * 7 || ' days')::interval)::date AS d
)
INSERT INTO derived_radar_assets (
  tenant_id, aoi_id, year, week, pipeline_version,
  rvi_mean, rvi_s3_uri, created_at
)
SELECT
  '11111111-1111-1111-1111-111111111111',
  '55555555-5555-5555-5555-555555555555',
  EXTRACT(ISOYEAR FROM d)::int,
  EXTRACT(WEEK FROM d)::int,
  'v1',
  0.45 + (i * 0.01),
  's3://mock-bucket/rvi-' || EXTRACT(ISOYEAR FROM d)::int || '-' || EXTRACT(WEEK FROM d)::int || '.tif',
  d::timestamptz
FROM weeks
ON CONFLICT DO NOTHING;

WITH weeks AS (
  SELECT
    generate_series(0, 13) AS i,
    (current_date - (generate_series(0, 13) * 7 || ' days')::interval)::date AS d
)
INSERT INTO derived_weather_daily (
  tenant_id, aoi_id, date, temp_max, temp_min, precip_sum, et0_fao
)
SELECT
  '11111111-1111-1111-1111-111111111111',
  '55555555-5555-5555-5555-555555555555',
  d,
  28 + (i % 3),
  18 + (i % 3),
  CASE WHEN i = 5 THEN 15 ELSE 2 END,
  3.5
FROM weeks
ON CONFLICT DO NOTHING;

COMMIT;
