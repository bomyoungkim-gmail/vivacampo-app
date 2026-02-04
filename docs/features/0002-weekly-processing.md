# FEAT-0002 — Weekly Satellite Processing

Date: 2025-12-05
Owner: Backend Team (Worker)
Status: Done

## Goal
Automatically process new Sentinel-1 and Sentinel-2 satellite imagery every week for all active AOIs, calculating 14 vegetation/water/soil indices and storing results in S3 + database.

**User value:** Users receive automatic weekly updates on crop health without manual intervention.

## Scope
**In scope:**
- Fetch Sentinel-2 imagery (10m resolution, 13 bands)
- Fetch Sentinel-1 radar (VV, VH polarization)
- Calculate 14 indices (NDVI, NDRE, NDWI, NDMI, EVI, SAVI, GNDVI, RECI, ARI, CRI, MSI, NBR, BSI, RVI)
- Store GeoTIFFs in S3 as COG (Cloud-Optimized GeoTIFF)
- Calculate statistics (mean, min, max, std) per AOI
- Store stats in database for charting

**Out of scope:**
- Real-time processing (Sentinel revisit is 5 days)
- Cloud removal (use cloud masks, skip cloudy scenes)
- Atmospheric correction (use L2A products)

## User Stories
- **As a farmer**, I want automatic weekly updates, so that I don't have to manually request processing.
- **As an agronomist**, I want to see trends over time, so that I can identify issues early.
- **As a system admin**, I want processing to complete within 24h, so that users get timely data.

## UX Notes
**States:**
- **Processing:** Show spinner + "Processing week 2026-W05..."
- **Complete:** Show NDVI map overlay + chart with new data point
- **Failed:** Show error message + "Retry" button

**Errors:**
- "No cloud-free imagery available for this week"
- "Processing failed (will retry automatically)"

## Contract Changes
**API:**
- Endpoint: `GET /v1/aois/{id}/history?year=2026&limit=52`
- Response:
  ```json
  {
    "aoi_id": "uuid",
    "data": [
      {
        "year": 2026,
        "week": 5,
        "ndvi_mean": 0.65,
        "ndvi_std": 0.12,
        "ndvi_s3_uri": "s3://bucket/tenant/aoi/2026/05/ndvi.tif",
        // ... other indices
      }
    ]
  }
  ```

**Domain:**
- Worker job: `process_week(aoi_id, year, week)`
- Indices calculation: `calculate_indices(bands: dict) -> dict`
- COG creation: `create_cog(array, transform, crs) -> bytes`

**Data:**
- Table: `derived_assets` (Sentinel-2 indices)
- Table: `derived_radar_assets` (Sentinel-1 indices)
- S3 bucket: `vivacampo-rasters/{tenant_id}/{aoi_id}/{year}/{week}/{index}.tif`

## Acceptance Criteria
- [x] Worker processes all active AOIs weekly
- [x] Worker calculates 14 indices correctly
- [x] Worker stores GeoTIFFs as COG in S3
- [x] Worker stores statistics in database
- [x] Processing completes within 24h for all AOIs
- [x] Worker retries failed jobs (max 3 attempts)
- [x] Worker skips cloudy scenes (>50% cloud cover)

## Observability
**Logs:**
- `processing.started` (aoi_id, year, week)
- `processing.completed` (aoi_id, year, week, duration_sec)
- `processing.failed` (aoi_id, year, week, error)
- `processing.skipped_cloudy` (aoi_id, year, week, cloud_cover_pct)

**Metrics:**
- `processing_duration_seconds` (histogram by index)
- `processing_success_total` (counter)
- `processing_failure_total` (counter by error_type)
- `s3_upload_bytes_total` (counter)

## Rollout Plan
- [x] Feature flag: Not needed (core feature)
- [x] Backward compatible: Yes
- [x] Migration: None required

## Testing
**Unit tests:**
- Index calculation (NDVI, NDRE, etc)
- COG creation
- Statistics calculation

**Integration tests:**
- End-to-end: Trigger job → Fetch imagery → Calculate indices → Store S3 → Store DB

**Manual tests:**
- Verify GeoTIFFs are valid COG (gdalinfo)
- Verify tiles display correctly in Leaflet
- Verify statistics match visual inspection

## Status
✅ **Done** - Deployed to production 2025-12-20
