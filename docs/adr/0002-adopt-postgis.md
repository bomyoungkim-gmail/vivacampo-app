# ADR-0002 — Adopt PostGIS for Spatial Data Storage

Date: 2025-12-15
Status: Accepted
Owners: Backend Team

## Context
VivaCampo requires storing and querying agricultural field boundaries (polygons) with high performance. We need to:
- Store MULTIPOLYGON geometries (farms can have non-contiguous areas)
- Calculate areas in hectares (using geographic projection)
- Perform spatial queries (point-in-polygon, intersections, buffering)
- Support spatial indexing for fast queries on 10,000+ AOIs

**Options considered:**
1. MongoDB with GeoJSON
2. PostgreSQL + PostGIS
3. Dedicated GIS database (e.g., SpatiaLite)

## Decision
**Adopt PostgreSQL 16 + PostGIS 3.4** as the primary database.

## Options considered

### 1) MongoDB with GeoJSON
**Pros:**
- Native GeoJSON support
- Flexible schema (good for evolving domain)
- Horizontal scaling (sharding)

**Cons:**
- Limited spatial functions (no ST_Area with geography, no buffering)
- No ACID transactions across collections
- Weaker spatial indexing (2dsphere less mature than GIST)
- Team lacks MongoDB expertise

### 2) PostgreSQL + PostGIS ✅
**Pros:**
- Industry-standard for GIS (used by QGIS, ArcGIS, etc)
- Rich spatial functions (ST_Area, ST_Buffer, ST_Intersection, ST_GeomFromText, etc)
- GIST spatial indexing (very fast for polygon queries)
- ACID transactions (critical for multi-tenant isolation)
- Team has PostgreSQL expertise
- Free and open-source

**Cons:**
- Vertical scaling only (but sufficient for MVP scale)
- Requires learning PostGIS SQL functions

### 3) SpatiaLite
**Pros:**
- Lightweight (SQLite-based)
- Good for embedded/mobile apps

**Cons:**
- Not designed for multi-user concurrent access
- Limited scalability
- No replication/backup features

## Consequences
**What changes:**
- All geometry data stored as `GEOMETRY(MULTIPOLYGON, 4326)` in PostgreSQL
- Spatial queries use PostGIS functions (`ST_*`)
- ORM (SQLAlchemy) uses GeoAlchemy2 extension
- Migrations include PostGIS extension setup (`CREATE EXTENSION postgis;`)

**Trade-offs accepted:**
- Vertical scaling limit (acceptable for MVP, can migrate to Citus/TimescaleDB later if needed)
- Learning curve for PostGIS SQL (mitigated by team's SQL expertise)

**Benefits:**
- Fast spatial queries (GIST index on `geom` column)
- Accurate area calculations (using geography type)
- Compatibility with external GIS tools (QGIS, ArcGIS can connect directly)
- Strong data integrity (ACID transactions, foreign keys)

## Follow-ups
- [x] Add PostGIS extension to Docker image (`postgis/postgis:16-3.4`)
- [x] Create migration with `CREATE EXTENSION postgis;`
- [x] Add GIST index on `aois.geom` column
- [x] Document spatial query patterns in `ai/contracts.md`
- [ ] Add performance benchmarks for 10,000+ AOIs (TASK-0200)
