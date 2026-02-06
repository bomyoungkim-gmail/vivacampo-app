# FEAT-0005 — Radar Processing (Sentinel-1)

Date: 2026-01-05
Owner: Backend Team, GIS Team
Status: Done

## Goal
Process Sentinel-1 Radar (SAR) data to provide all-weather vegetation monitoring, complementing optical Sentinel-2 data.

**User value:** Users can monitor fields even during cloudy periods when optical satellites cannot capture clear imagery.

## Scope
**In scope:**
- Sentinel-1 data acquisition (VV, VH polarizations)
- RVI (Radar Vegetation Index) calculation
- VH/VV ratio analysis
- Cloud-penetrating monitoring
- Weekly radar processing alongside optical

**Out of scope:**
- Soil moisture estimation (future: FEAT-0025)
- Flood detection (future: FEAT-0026)
- Change detection specific to radar

## User Stories
- **As a farmer**, I want vegetation data even during rainy season, so that monitoring doesn't stop due to clouds.
- **As an agronomist**, I want to compare optical and radar indices, so that I can better understand crop structure.
- **As a farm manager**, I want continuous monitoring regardless of weather, so that I don't miss critical changes.

## UX Notes
**Radar Tab:**
- RVI map layer (toggle with optical indices)
- RVI time series chart
- VH/VV ratio chart
- Cloud coverage indicator (shows why radar is valuable)

**Legend:**
- RVI: 0 (bare soil) to 1 (dense vegetation)
- Color ramp: Brown -> Yellow -> Green

## Contract Changes
**API:**
- Endpoint: `GET /v1/aois/{aoi_id}/radar?week={week_date}`
- Response:
  ```json
  {
    "week": "2026-01-13",
    "rvi_mean": 0.62,
    "rvi_std": 0.08,
    "vh_vv_ratio_mean": 0.45,
    "tile_url": "https://tiler.vivacampo.com/cog/tiles/{z}/{x}/{y}?url=...",
    "s3_uri": "s3://vivacampo-rasters/radar/aoi_123/2026-01-13/rvi.tif"
  }
  ```

**Domain:**
- Entity: `DerivedRadarAssets`
- Service: `process_radar_week(aoi_id, week_date)`
- Calculation: `RVI = 4 * VH / (VV + VH)` (normalized)

**Data:**
- Table: `derived_radar_assets`
- Columns: `id`, `aoi_id`, `week_date`, `rvi_mean`, `rvi_std`, `vh_vv_ratio_mean`, `s3_uri_rvi`, `s3_uri_vh`, `s3_uri_vv`

## Acceptance Criteria
- [x] System fetches Sentinel-1 GRD data from Copernicus
- [x] System calculates RVI and VH/VV ratio
- [x] System stores radar GeoTIFFs in S3 (COG format)
- [x] User can view RVI layer on map
- [x] User sees RVI time series chart
- [x] Radar processing runs alongside optical in weekly job
- [x] System handles missing radar data gracefully (12-day revisit)

## Observability
**Logs:**
- `radar.processed` (aoi_id, week_date, rvi_mean)
- `radar.data_unavailable` (aoi_id, week_date, reason)
- `sentinel1.download_completed` (scene_id, size_mb)

**Metrics:**
- `radar_processing_duration_seconds` (histogram)
- `radar_data_availability_ratio` (gauge)

## Testing
**Unit tests:**
- RVI calculation formula
- VH/VV ratio calculation

**Integration tests:**
- Sentinel-1 data retrieval (stubbed)
- Radar processing pipeline
- S3 storage verification

## Status
Done - Deployed 2026-01-10
