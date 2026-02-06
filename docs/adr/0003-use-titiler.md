# ADR-0003 — Use TiTiler for Map Tile Serving

Date: 2025-12-18
Status: Accepted
Owners: Backend Team, Frontend Team

## Context
VivaCampo processes satellite imagery into GeoTIFF files (14 indices: NDVI, NDRE, EVI, etc). We need to display these rasters on a web map (Leaflet). 

**Problem:** GeoTIFF files are too large to send directly to browser (10-50MB per AOI per week). We need a tile server that:
- Converts GeoTIFF to XYZ map tiles (256x256 PNG)
- Supports Cloud-Optimized GeoTIFF (COG) for efficient S3 access
- Applies colormaps (e.g., red-yellow-green for NDVI)
- Supports rescaling (e.g., -1 to 1 for NDVI)
- Minimal infrastructure overhead

## Decision
**Adopt TiTiler** as the map tile server, deployed as a separate microservice.

## Options considered

### 1) MapServer
**Pros:**
- Mature, widely used
- Supports many formats

**Cons:**
- Complex configuration (MapFile syntax)
- Requires file system access (not cloud-native)
- Heavy infrastructure

### 2) GeoServer
**Pros:**
- Feature-rich (WMS, WFS, WCS)
- GUI for configuration

**Cons:**
- Java-based (heavy memory footprint)
- Overkill for our use case (we only need XYZ tiles)
- Complex setup

### 3) TiTiler ✅
**Pros:**
- Python-based (matches our stack)
- Cloud-native (reads directly from S3 via HTTP range requests)
- Minimal configuration (FastAPI-based, auto-generated OpenAPI)
- Supports COG (Cloud-Optimized GeoTIFF) natively
- Lightweight (single Docker container)
- Active development (by Development Seed)

**Cons:**
- Less mature than MapServer/GeoServer
- Limited to raster data (no vector tiles, but we don't need them)

### 4) Custom tile server (rio-tiler)
**Pros:**
- Full control

**Cons:**
- Reinventing the wheel
- Maintenance burden

## Consequences
**What changes:**
- Deploy TiTiler as `services/tiler` microservice
- Frontend requests tiles via `/cog/tiles/{z}/{x}/{y}?url=s3://...&colormap_name=rdylgn&rescale=-1,1`
- All GeoTIFFs stored as COG format (using `gdal_translate -of COG`)
- S3 URIs stored in database (not file contents)

**Trade-offs accepted:**
- Dependency on external library (TiTiler) - mitigated by active development and community
- S3 URIs exposed to frontend (security risk) - **TODO: TASK-0001 to fix**

**Benefits:**
- Fast tile serving (<300ms p95 with COG)
- No file system management (reads directly from S3)
- Easy to scale (stateless, can run multiple instances)
- Automatic caching (browser caches tiles by z/x/y)

## Follow-ups
- [x] Deploy TiTiler as Docker service
- [x] Configure S3 access (LocalStack for dev, AWS for prod)
- [x] Update frontend to use TiTiler endpoints
- [ ] Implement signed URLs or API proxy for security (TASK-0001)
- [ ] Add Redis caching layer for frequently accessed tiles (TASK-0201)
