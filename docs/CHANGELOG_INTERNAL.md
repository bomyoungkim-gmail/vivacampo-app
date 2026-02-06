# Internal Changelog

> For humans. Keep it factual. Link PRs if available.

## Unreleased
- Added SRRE (Simple Ratio Red Edge) vegetation index to TiTiler expressions.
- Added DETECT_HARVEST worker job to create HARVEST_DETECTED signals from RVI drops.
- Added nitrogen status API use case and router (SRRE zone map support).
- Added correlation API use case and router for vigor/climate insights.
- Added radar fallback tooltip and dot styling for NDVI chart when NDVI is missing but RVI is present.
- Added NitrogenAlert component and wired it into AOI Overview.
- Added Analysis tab with correlation chart and insights panel.
- Added GitHub Actions workflows for staging/prod deploys and a test placeholder.
- Added Terraform scaffold for staging/production (ECS, RDS, S3, SQS modules).
- Added Cloudflare intelligence cache worker for nitrogen/correlation endpoints.
- Added year-over-year correlation endpoint and UI chart for season comparison.
- Added productivity score card based on NDVI average and radar mode badge on map.
- Removed non-existent `rio-tiler-stac` dependency from TiTiler requirements to fix Docker build.
- Added missing shadcn `Alert` component to resolve NitrogenAlert import.
- Auto-backfill now triggers on AOI creation (last 8 weeks).
- Backfill now enqueues PROCESS_RADAR_WEEK, PROCESS_WEATHER, and PROCESS_TOPOGRAPHY.
- Worker job handlers mark status as RUNNING at start.
- Added STAC/Open-Meteo request/response logging for data acquisition visibility.
- Added admin endpoint to enqueue backfills for AOIs without derived assets.
- Added Admin UI action to trigger reprocess of AOIs without data.
- Fixed SQS client usage in admin reprocess and AOI backfill dispatch.
- Fixed admin_ui dev host binding and port mapping to make /admin reachable on localhost:3001.
- Fixed admin UI routes to avoid double basePath (/admin/admin/*).
- Admin jobs list now shows `aoi_id` and `job_key`.
- Admin jobs list now shows farm and AOI names; filters use DONE status.
- Added `aiohttp` to worker dependencies.
- Fixed admin jobs filtering to use jobs table alias with joins.
- Fixed process_weather status update to avoid non-existent error_message column.
- Jobs filter label normalized to DONE; weather end_date is clamped to today for Open-Meteo.
- Added jobs.error_message migration and surfaced errors in Admin Jobs UI.
- Fixed PROCESS_WEATHER to handle AOI geometry as GeoJSON (prevents TypeError).
- Added admin endpoints to list missing weeks and reprocess missing weeks.
- Added Admin UI page for missing weeks with reprocess action.
- Increased worker throughput with configurable concurrency and batch receive.
- **Dynamic Tiling + MosaicJSON (ADR-0007)**:
  - TiTiler updated with titiler-mosaic, MosaicTilerFactory, and STAC-mosaic endpoints
  - Added `/stac-mosaic/tiles` endpoint for multi-band vegetation indices (NDVI, NDRE, NDWI, etc.)
  - MosaicJSON stores unsigned STAC item URLs; signing at request time via pystac.sign_inplace()
  - Added CREATE_MOSAIC job for weekly MosaicJSON generation (Brazil-wide Sentinel-2)
  - Added CALCULATE_STATS and WARM_CACHE worker jobs
  - Added tiles_router.py with authenticated tile endpoints and TileJSON for GIS integration
  - Migration 004_add_mosaic_registry.sql for mosaic tracking
  - Full pipeline tested: Auth → API → TiTiler → MosaicJSON → STAC → Planetary Computer → PNG
  - Expected storage savings: ~99.9% (~2.5MB vs ~2.6TB/year)
- **UI/UX Improvements (2026-02-04)**:
  - Admin-UI: Implemented dark mode with ThemeToggle component (localStorage + system preference detection)
  - Admin-UI: Refactored globals.css with WCAG AA accessible colors (HSL system, 4.5:1 contrast)
  - Admin-UI: Updated tailwind.config.js with chart colors, aspect-ratio utilities, touch targets (44px)
  - Admin-UI: Implemented mobile-first design in all 4 pages (dashboard, audit, jobs, tenants)
  - Admin-UI: Added interactive states (.interactive-card, .table-row-interactive)
  - App-UI: Added aspect-ratio wrappers to Charts.tsx to eliminate horizontal scroll
  - App-UI: Improved dark mode contrast (muted-foreground: 65.1% → 70%)
  - App-UI: Added dark mode support to chart components

## 2026-02-04
- Added LocalStack custom build + init script for SQS queue bootstrap
- Added/updated P0 RBAC regression tests and Windows-friendly DB host override
- Fixed vision-service router exception handler registration
- Presigned S3 asset URLs in AOI/radar responses to avoid exposing raw S3 URIs

## 2026-02-03
- Initialized template pack (AI Scaffolding)
