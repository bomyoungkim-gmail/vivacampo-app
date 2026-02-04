# FEAT-0001 — AOI Creation and Backfill

Date: 2025-12-01
Owner: Backend Team, Frontend Team
Status: Done

## Goal
Enable users to define Areas of Interest (AOIs) by drawing polygons on a map, automatically triggering satellite data processing for the past 8 weeks.

**User value:** Users can start monitoring their fields immediately without waiting for new satellite passes.

## Scope
**In scope:**
- Draw polygon on map (Leaflet + Geoman)
- Validate geometry (no self-intersections, area >0.1 ha, <10,000 ha)
- Save to PostGIS with SRID 4326
- Auto-trigger 8-week backfill job
- Display processing status in UI

**Out of scope:**
- Import from Shapefile/KML (future: FEAT-0010)
- Automatic field boundary detection (future: FEAT-0015)
- Real-time processing (<1 day latency)

## User Stories
- **As a farmer**, I want to draw my field boundaries on a map, so that I can start monitoring crop health.
- **As a farmer**, I want the system to automatically process historical data, so that I can see trends immediately.
- **As an agronomist**, I want to see processing status, so that I know when data is ready for analysis.

## UX Notes
**States:**
- **Empty state:** Map with "Draw AOI" button
- **Drawing state:** Geoman toolbar active, polygon being drawn
- **Validation state:** Show area in hectares, validate constraints
- **Processing state:** Show progress bar (0/8 weeks processed)
- **Complete state:** Show AOI on map with color-coded NDVI overlay

**Errors:**
- "Area too small (min 0.1 ha)"
- "Area too large (max 10,000 ha)"
- "Polygon has self-intersections"
- "Processing failed (retry available)"

## Contract Changes
**API:**
- Endpoint: `POST /v1/aois`
- Request:
  ```json
  {
    "farm_id": "uuid",
    "name": "Talhão 01",
    "use_type": "CROP",
    "geom": "MULTIPOLYGON(...)"  // WKT format
  }
  ```
- Response:
  ```json
  {
    "id": "uuid",
    "name": "Talhão 01",
    "area_ha": 45.3,
    "status": "ACTIVE",
    "created_at": "2026-01-15T10:30:00Z"
  }
  ```
- Errors: `400` (invalid geometry), `403` (quota exceeded), `500` (server error)

**Domain:**
- New validation: `validate_geometry(wkt: str) -> bool`
- New service method: `create_aoi_with_backfill(tenant_id, farm_id, name, use_type, geom)`

**Data:**
- Table: `aois` (already exists)
- Trigger: Auto-create job with `job_type=BACKFILL`, `params={weeks: 8}`

## Acceptance Criteria
- [x] User can draw polygon on map using Geoman
- [x] System validates area (0.1 ha - 10,000 ha)
- [x] System saves geometry to PostGIS as MULTIPOLYGON
- [x] System auto-triggers backfill job (8 weeks)
- [x] User sees processing status in UI
- [x] System displays processed NDVI on map after completion
- [x] System enforces tenant quota (max AOIs per plan)

## Observability
**Logs:**
- `aoi.created` (tenant_id, aoi_id, area_ha)
- `job.triggered` (job_id, job_type=BACKFILL, aoi_id)
- `geometry.validation_failed` (reason, geom_wkt)

**Metrics:**
- `aois_created_total` (counter)
- `backfill_jobs_triggered_total` (counter)
- `geometry_validation_errors_total` (counter by reason)

## Rollout Plan
- [x] Feature flag: Not needed (core feature)
- [x] Backward compatible: Yes (new feature)
- [x] Migration: None required (table already exists)

## Testing
**Unit tests:**
- Geometry validation (valid, invalid, edge cases)
- Area calculation (hectares)

**Integration tests:**
- End-to-end: Draw AOI → Save → Job triggered → Processing → Map display

**Manual tests:**
- Draw various polygon shapes (simple, complex, with holes)
- Test quota enforcement (exceed max AOIs)
- Test error states (invalid geometry, server error)

## Status
✅ **Done** - Deployed to production 2025-12-15
