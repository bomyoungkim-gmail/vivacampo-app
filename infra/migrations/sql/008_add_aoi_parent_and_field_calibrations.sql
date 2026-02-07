-- Add parent_aoi_id to aois + field_calibrations table for paddock calibration data

ALTER TABLE aois
  ADD COLUMN IF NOT EXISTS parent_aoi_id uuid NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'aois_parent_aoi_fk'
  ) THEN
    ALTER TABLE aois
      ADD CONSTRAINT aois_parent_aoi_fk
      FOREIGN KEY (parent_aoi_id) REFERENCES aois(id) ON DELETE SET NULL;
  END IF;
END $$;

CREATE INDEX CONCURRENTLY IF NOT EXISTS aois_parent_idx
  ON aois (tenant_id, parent_aoi_id);

CREATE TABLE IF NOT EXISTS field_calibrations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
  observed_date date NOT NULL,
  metric_type text NOT NULL,
  value double precision NOT NULL,
  unit text NOT NULL DEFAULT 'kg_ha',
  source text NOT NULL DEFAULT 'MANUAL',
  is_active boolean NOT NULL DEFAULT true,
  version int NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX CONCURRENTLY IF NOT EXISTS field_calibrations_aoi_time_idx
  ON field_calibrations (tenant_id, aoi_id, observed_date DESC);

CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS field_calibrations_active_idx
  ON field_calibrations (tenant_id, aoi_id, observed_date, metric_type)
  WHERE is_active;

CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS field_calibrations_version_idx
  ON field_calibrations (tenant_id, aoi_id, observed_date, metric_type, version);
