-- Migration: Add mosaic_registry table for tracking MosaicJSON files
-- Part of ADR-0007: Dynamic Tiling with MosaicJSON

-- Up Migration
CREATE TABLE IF NOT EXISTS mosaic_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection VARCHAR(50) NOT NULL,           -- e.g., 'sentinel-2-l2a', 'sentinel-1-rtc'
    year INT NOT NULL,
    week INT NOT NULL,
    s3_url TEXT NOT NULL,                      -- e.g., 's3://bucket/mosaics/sentinel-2-l2a/2026/w05.json'
    scene_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'READY',        -- READY, NO_DATA, FAILED
    metadata JSONB,                            -- Additional metadata (bounds, center, etc.)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (collection, year, week)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_mosaic_registry_collection_year
    ON mosaic_registry(collection, year);
CREATE INDEX IF NOT EXISTS idx_mosaic_registry_status
    ON mosaic_registry(status);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_mosaic_registry_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_mosaic_registry_updated_at ON mosaic_registry;
CREATE TRIGGER trg_mosaic_registry_updated_at
    BEFORE UPDATE ON mosaic_registry
    FOR EACH ROW
    EXECUTE FUNCTION update_mosaic_registry_updated_at();

-- Add comment
COMMENT ON TABLE mosaic_registry IS 'Registry of MosaicJSON files for dynamic tiling (ADR-0007)';

-- Down Migration (run manually if needed)
-- DROP TABLE IF EXISTS mosaic_registry;
