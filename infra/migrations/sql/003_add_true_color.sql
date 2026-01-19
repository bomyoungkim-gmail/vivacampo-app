-- Add true_color_s3_uri to derived_assets

ALTER TABLE derived_assets
ADD COLUMN IF NOT EXISTS true_color_s3_uri TEXT;
