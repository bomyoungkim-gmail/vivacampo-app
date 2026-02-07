-- Add STAC scene cache table
-- Purpose: cache provider scene metadata for fallback/retry

CREATE TABLE IF NOT EXISTS stac_scene_cache (
    cache_key TEXT PRIMARY KEY,
    provider_name TEXT NOT NULL,
    collections TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    max_cloud_cover FLOAT NOT NULL,
    bbox JSONB,
    geometry JSONB,
    scenes JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stac_scene_cache_provider
    ON stac_scene_cache(provider_name);

CREATE INDEX IF NOT EXISTS idx_stac_scene_cache_created_at
    ON stac_scene_cache(created_at);
