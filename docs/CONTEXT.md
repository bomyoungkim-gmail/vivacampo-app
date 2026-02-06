# Durable Project Context (Human-readable)

Last Updated: 2026-02-06

## What this is
This file is the compact, durable memory of the project.
Keep it short (1–2 pages). Update it weekly or after major changes.

## Product Summary
**Problem:** Traditional agricultural monitoring relies on manual field visits or expensive consultancy, making precision agriculture inaccessible to small/medium farmers.

**Solution:** VivaCampo is a multi-tenant Earth Observation platform that transforms free satellite imagery (Sentinel-1 Radar + Sentinel-2 Optical) into actionable agronomic insights. Core value proposition: **"GIS for everyone"** - democratizing advanced geospatial intelligence without requiring GIS expertise.

**Audience:**
- Primary: Brazilian farmers and farm managers
- Secondary: Agronomists and agricultural consultants
- Tertiary: Agribusiness companies managing multiple properties

**Value Proposition:**
- Automated crop health monitoring (14 satellite indices: NDVI, NDRE, EVI, etc)
- AI-powered anomaly detection (vigor drop, water stress, disease risk)
- Historical trend analysis (52-week charts, year-over-year comparison)
- Zero-cost satellite data (Copernicus/Sentinel program)
- No GIS software required (web-based map interface)

## Current State
**Stage:** MVP (Development) - hexagonal migration complete; validation pending

**What exists today:**
- ✅ Multi-tenant backend (FastAPI + PostGIS)
- ✅ Hexagonal architecture across API/Worker (ports/adapters, use cases, DI)
- ✅ Background job processor (Python Worker + SQS)
- ✅ Map tile server (TiTiler for COG → XYZ tiles)
- ✅ User frontend (Next.js + Leaflet + Geoman)
  - Dark mode support (app-ui native, admin-ui implemented)
  - WCAG AA accessibility (4.5:1 contrast, 44px touch targets)
  - Mobile-first responsive design
  - shadcn/ui design system
- ✅ Admin panel (tenant management, system monitoring)
- ✅ Admin UI for missing weeks ("buracos") with reprocess action
- ✅ 14 satellite indices (NDVI, NDRE, NDWI, NDMI, EVI, SAVI, etc)
- ✅ Radar monitoring (Sentinel-1 RVI, all-weather)
- ✅ Weather integration (Open-Meteo, localized per AOI)
- ✅ Nitrogen status API + SRRE zone map
- ✅ Correlation API (vigor x climate) + insights
- ✅ Analysis tab with correlation chart
- ✅ Year-over-year comparison + productivity score card
- ✅ Radar fallback tooltip + radar mode badge
- ✅ AI Copilot (anomaly detection, recommended actions)
- ✅ Authentication (OIDC + Mock for dev)
- ✅ Security suite for tenant isolation (`tests/security/`)
- ✅ RLS context wiring + migration available (set_config + SQL)

**What is missing:**
- ✅ TiTiler security (presigned URLs; raw S3 URIs not exposed)
- ✅ Integration tests for Worker jobs and external integrations (stubbed)
- ✅ Dynamic Tiling with MosaicJSON (ADR-0007) - multi-band vegetation indices working
- ⚠️ Cloudflare CDN setup for tile caching (workers ready; pending credentials)
- ⚠️ E2E validation (Playwright) with WebKit/Mobile Safari remaining
- ⚠️ Validation after volume run (Admin UI Jobs, missing-weeks reprocess, error visibility)
- ⚠️ Staging/prod validation of new flows (tiles/process_week/admin jobs/missing weeks)
- ⚠️ RLS rollout validation in staging/prod
- ⚠️ Request ID propagation across services
- ⚠️ Production deployment (staging + CI/CD workflows ready; pending credentials)
- ⚠️ Alert delivery (email/SMS/push notifications)

## Core Domain
**Entities:**
- **Identity:** User authentication (OIDC provider + subject)
- **Tenant:** Multi-tenant isolation (COMPANY/PERSONAL), quotas, plan (BASIC/PRO)
- **Farm:** Physical property with timezone
- **AOI (Area of Interest):** Polygon geometry (MULTIPOLYGON, SRID 4326), use_type, area_ha
- **Job:** Async processing tasks (BACKFILL, PROCESS_WEEK, FORECAST_WEEK)
- **OpportunitySignal:** AI-detected anomalies (signal_type, severity, confidence)
- **DerivedAssets:** Processed Sentinel-2 indices (NDVI, NDRE, EVI, etc + stats)
- **DerivedRadarAssets:** Processed Sentinel-1 data (RVI, Ratio, S3 URIs)
- **DerivedWeatherDaily:** Localized weather per AOI (temp, precip, ET0)

**Critical Flows:**
1. **AOI Creation:** User draws polygon → API validates + saves to PostGIS → Auto-triggers 8-week backfill (PROCESS_WEEK, PROCESS_RADAR_WEEK, PROCESS_WEATHER, PROCESS_TOPOGRAPHY)
2. **Weekly Processing:** Worker fetches Sentinel data → Calculates 14 indices → Stores GeoTIFFs in S3 + stats in DB
3. **Map Rendering:** Frontend requests `/v1/tiles/aois/{id}/{z}/{x}/{y}.png?index=ndvi` → API redirects to TiTiler → TiTiler reads MosaicJSON → Fetches bands from Planetary Computer → Computes vegetation index → Returns PNG tile → Leaflet displays (CDN caches for 7 days)
4. **Anomaly Detection:** Worker runs change detection → Creates OpportunitySignal → AI Copilot suggests actions

**Non-goals:**
- Real-time monitoring (<1 day latency) - Sentinel revisit is 5 days
- Sub-meter resolution - Sentinel-2 is 10m
- Drone imagery processing (future scope)
- Prescription map generation (agronomist responsibility)
- Direct machinery integration (John Deere, etc)

## Contracts
**API Contract:**
- Location: FastAPI auto-generated OpenAPI (`/docs`)
- Error shape: `{ error: { code, message, details?, traceId? } }`
- Pagination: `page`, `page_size`, `total`
- Geospatial: WKT input, WKT/GeoJSON output, SRID 4326

**Data Contract:**
- Location: `infra/migrations/sql/*.sql`
- All geometries: `GEOMETRY(MULTIPOLYGON, 4326)` with GIST index
- Migrations: Expand/contract pattern for breaking changes
- Idempotency: Jobs safe to retry, S3 keys deterministic
- Job errors: `jobs.error_message` persists failure reasons

**Domain Contract:**
- Location: `services/api/app/domain` + `services/worker/worker/domain`
- Multi-tenant isolation: All queries filter by `tenant_id`
- No business logic in routers (thin controllers)

## Tech Stack
**Backend:**
- FastAPI 0.109+ (async, Pydantic validation)
- Python 3.11+
- SQLAlchemy 2.0 + GeoAlchemy2 (ORM)
- Structlog (JSON logging)

**Frontend:**
- Next.js 14.2 (React 18, TypeScript)
- Leaflet + React-Leaflet (maps)
- Leaflet-Geoman (geometry editing)
- Turf.js (client-side spatial analysis)
- Recharts (time series viz)
- Radix UI + Tailwind CSS

**Database:**
- PostgreSQL 16 + PostGIS 3.4
- Redis 7 (caching, rate limiting)

**Infra:**
- Docker Compose (local dev)
- LocalStack (S3, SQS simulation)
- AWS S3 (raster storage - COG format)
- AWS SQS (job queue)

**GIS Processing:**
- GDAL (raster manipulation)
- Rasterio (Python raster I/O)
- GeoPandas + Shapely (vector ops)
- TiTiler + titiler-mosaic (COG/MosaicJSON → XYZ tiles server)
- cogeo-mosaic (MosaicJSON backend)
- Planetary Computer (Sentinel-2/Sentinel-1 STAC catalog)

## Operational Notes
**Environments:**
- **Development:** Docker Compose + LocalStack (S3, SQS)
- **Staging:** (Planned) AWS ECS + RDS + S3 + SQS
- **Production:** (Future) AWS ECS + RDS + S3 + SQS + CloudFront

**Deploy Strategy:**
- CI/CD: GitHub Actions (planned)
- Migrations: Manual via `psql` (local), automated via CI (staging/prod)
- Rollback: Redeploy previous Docker image + restore DB snapshot if needed

**Backups:**
- Database: Daily snapshots, 30-day retention (planned)
- S3: Versioning enabled (planned)

**Monitoring:**
- Logs: Structlog (JSON format)
- Metrics: Prometheus (planned)
- Alerts: Error rate >5% for 5 minutes (planned)
- STAC reliability: retry/backoff and timeouts configured in worker client

**Accessibility:**
- WCAG AA compliance: 4.5:1 minimum contrast ratio
- Touch targets: 44x44px minimum (WCAG 2.1 Level AAA)
- Dark mode: System preference detection + manual toggle
- Reduced motion: Respects prefers-reduced-motion

**Security:**
- Auth: OIDC (production), Mock (dev)
- Multi-tenant: RLS via `tenant_id` + `set_config` context
- Rate limiting: 100 req/min per IP (SlowAPI)
- Secrets: Env vars (local), AWS Secrets Manager (prod, planned)

## Last Updated
2026-02-06
