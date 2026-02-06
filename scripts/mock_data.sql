-- 1. Insert Sentinel-2 Data (Optical)
INSERT INTO derived_assets (tenant_id, aoi_id, year, week, pipeline_version, ndvi_mean, ndvi_s3_uri)
VALUES 
('d290f1ee-6c54-4b01-90e6-d701748f0851', '98fd8eb9-3d20-4180-ab4b-0e5272e20076', 2025, 40, '1.0.0', 0.75, 's3://mock-bucket/ndvi-2025-40.tif'),
('d290f1ee-6c54-4b01-90e6-d701748f0851', '98fd8eb9-3d20-4180-ab4b-0e5272e20076', 2025, 41, '1.0.0', 0.60, 's3://mock-bucket/ndvi-2025-41.tif'),
('d290f1ee-6c54-4b01-90e6-d701748f0851', '98fd8eb9-3d20-4180-ab4b-0e5272e20076', 2025, 42, '1.0.0', 0.82, 's3://mock-bucket/ndvi-2025-42.tif')
ON CONFLICT DO NOTHING;

-- 2. Create & Insert Sentinel-1 Data (Radar)
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

INSERT INTO derived_radar_assets (tenant_id, aoi_id, year, week, pipeline_version, rvi_mean, rvi_s3_uri)
VALUES
('d290f1ee-6c54-4b01-90e6-d701748f0851', '98fd8eb9-3d20-4180-ab4b-0e5272e20076', 2025, 40, '1.0.0', 0.45, 's3://mock-bucket/rvi-2025-40.tif'),
('d290f1ee-6c54-4b01-90e6-d701748f0851', '98fd8eb9-3d20-4180-ab4b-0e5272e20076', 2025, 41, '1.0.0', 0.55, 's3://mock-bucket/rvi-2025-41.tif')
ON CONFLICT DO NOTHING;

-- 3. Create & Insert Topography Data
CREATE TABLE IF NOT EXISTS derived_topography (
    tenant_id UUID NOT NULL,
    aoi_id UUID NOT NULL,
    pipeline_version VARCHAR(50) NOT NULL,
    dem_s3_uri TEXT,
    slope_s3_uri TEXT,
    aspect_s3_uri TEXT,
    elevation_min FLOAT,
    elevation_max FLOAT,
    elevation_mean FLOAT,
    slope_mean FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, aoi_id, pipeline_version)
);

INSERT INTO derived_topography (tenant_id, aoi_id, pipeline_version, elevation_mean, slope_mean, dem_s3_uri)
VALUES
('d290f1ee-6c54-4b01-90e6-d701748f0851', '98fd8eb9-3d20-4180-ab4b-0e5272e20076', '1.0.0', 450.5, 12.3, 's3://mock-bucket/dem.tif')
ON CONFLICT DO NOTHING;
