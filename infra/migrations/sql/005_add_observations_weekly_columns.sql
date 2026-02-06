-- Add missing columns to observations_weekly for dynamic tiling stats

BEGIN;

ALTER TABLE observations_weekly
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS is_fallback boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS ndwi_mean double precision NULL,
  ADD COLUMN IF NOT EXISTS ndwi_std double precision NULL,
  ADD COLUMN IF NOT EXISTS ndmi_mean double precision NULL,
  ADD COLUMN IF NOT EXISTS ndmi_std double precision NULL,
  ADD COLUMN IF NOT EXISTS savi_mean double precision NULL,
  ADD COLUMN IF NOT EXISTS savi_std double precision NULL,
  ADD COLUMN IF NOT EXISTS evi_mean double precision NULL,
  ADD COLUMN IF NOT EXISTS evi_std double precision NULL,
  ADD COLUMN IF NOT EXISTS ndre_mean double precision NULL,
  ADD COLUMN IF NOT EXISTS ndre_std double precision NULL,
  ADD COLUMN IF NOT EXISTS gndvi_mean double precision NULL,
  ADD COLUMN IF NOT EXISTS gndvi_std double precision NULL;

ALTER TABLE observations_weekly
  ALTER COLUMN valid_pixel_ratio SET DEFAULT 0;

COMMIT;
