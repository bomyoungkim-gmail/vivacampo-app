# Impact Analysis: ADR-0007 MGRS Tile Data Lake Implementation

**Analysis Date:** 2026-02-04
**ADR Reference:** docs/adr/ADR-0007-mgrs-tile-data-lake.md
**Status:** Comprehensive Impact Assessment
**Author:** System Analysis

---

## EXECUTIVE SUMMARY

ADR-0007 proposes a fundamental architectural change from **per-AOI satellite data storage** to a **two-tier MGRS tile-based data lake**. This change will significantly reduce storage costs (60-80%) and eliminate redundant downloads, but introduces substantial complexity in job orchestration, database schema, and cross-tenant tile sharing.

**Risk Level:** HIGH (Major architectural change with breaking workflow modifications)

**Breaking Changes:** YES
- New job types required (DOWNLOAD_TILE, PROCESS_AOI_INDICES)
- Database schema additions (3 new tables, AOI creation flow modified)
- Worker pipeline complete rewrite required

**Backwards Compatible:** PARTIALLY (with feature flag strategy)
- Frontend AOI creation: NO CHANGES REQUIRED
- Map tile display: NO CHANGES REQUIRED
- API responses: ADDITIVE (new optional fields)

**Recommended Approach:** Phased rollout with dual-write mode (as outlined in ADR)

---

## IMPACT MAP

### Directly Modified Components

#### Database Schema (3 New Tables)
**File:** infra/migrations/sql/005_add_mgrs_tile_lake.sql (NEW)
- `sentinel_tiles` - Shared MGRS tile tracking (tenant-agnostic)
- `aoi_tile_mapping` - AOI ↔ MGRS tile intersection mapping
- `mgrs_grid` - Reference grid geometry (preloaded for Brazil)

**Impact:** Migration required, new indexes, ~100MB additional metadata storage

#### Worker Jobs (2 New Job Types)
**Files:**
- services/worker/worker/jobs/download_tile.py (NEW)
- services/worker/worker/jobs/process_aoi_indices.py (NEW)
- services/worker/worker/jobs/backfill.py (MODIFIED - add tile download orchestration)
- services/worker/worker/jobs/process_week.py (REPLACED by process_aoi_indices.py)

**Impact:** Core processing logic rewritten, job dependency management required

#### API Endpoints
**File:** services/api/app/presentation/aois_router.py (MODIFIED)
- POST /v1/aois - Add MGRS tile calculation on AOI creation
- GET /v1/aois/{id} - Add `mgrs_tiles` field to response (optional)

**File:** services/api/app/presentation/tiles_router.py (NEW)
- GET /v1/tiles/mgrs - List available MGRS tiles
- GET /v1/tiles/mgrs/{mgrs_id} - Get tile details
- GET /v1/tiles/mgrs/{mgrs_id}/cog - Get presigned COG URL for GIS tools
- GET /v1/tiles/xyz/{collection}/{mgrs_id}/{z}/{x}/{y}.png - XYZ tile endpoint

**Impact:** 4 new public endpoints, AOI creation logic extended

#### STAC Client
**File:** services/worker/worker/pipeline/stac_client.py (MODIFIED)
- Add `search_by_mgrs_tile()` method
- Add `download_full_tile()` (no clipping) method
- Modify `download_and_clip_band()` to support tile-based clipping

**Impact:** Additional methods, backward compatible

---

### Affected Dependencies (First-Order)

#### Frontend (NO CODE CHANGES REQUIRED)
**Files:**
- services/app-ui/src/components/MapLeaflet.tsx (NO CHANGE)
- services/app-ui/src/components/MapComponent.tsx (NO CHANGE)
- services/app-ui/src/lib/api.ts (OPTIONAL: display tile_mapping in debug mode)

**Current Flow:**
1. User draws polygon on map
2. Frontend sends GeoJSON to `POST /v1/aois`
3. Backend handles MGRS calculation internally
4. Response includes new optional `tile_mapping` field (ignored by current UI)

**Validation:** Frontend continues to work without modification. TiTiler URLs remain unchanged because derived indices are still stored per-AOI.

**Optional Enhancement:**
- Display MGRS grid overlay in admin/debug mode
- Show tile download status in job monitoring UI

#### TiTiler Integration (NO CHANGE)
**File:** services/tiler/Dockerfile (NO CHANGE)

**Validation:** TiTiler continues to serve tiles from per-AOI index paths:
- Current: `/cog/tiles/{z}/{x}/{y}?url=s3://bucket/tenant=X/aoi=Y/year=2026/week=5/indices/ndvi.tif`
- After: SAME (indices remain per-AOI, only raw bands move to MGRS tiles)

**New Capability (OPTIONAL):**
- TiTiler can also serve MGRS tiles directly for GIS tools:
  `/cog/tiles/{z}/{x}/{y}?url=s3://bucket/tiles/sentinel2/mgrs=23KPQ/year=2026/week=5/B04.tif`

#### Job Orchestration (MAJOR CHANGE)
**File:** services/worker/worker/main.py (MODIFIED)

**Current Flow:**
```
AOI Created → BACKFILL Job → PROCESS_WEEK Jobs → Indices in S3
```

**New Flow:**
```
AOI Created → Calculate MGRS Mapping → BACKFILL Job
  ↓
  For each week:
    1. Check sentinel_tiles table for each MGRS tile
    2. If missing → Enqueue DOWNLOAD_TILE job
    3. Wait for all tiles READY
    4. Enqueue PROCESS_AOI_INDICES job
       - Read shared tiles from S3
       - Clip to AOI in memory
       - Calculate indices
       - Upload indices to per-AOI path
```

**Impact:** Job dependency management required, potential for deadlocks if tile downloads fail

---

### Affected Contracts

#### API Response Contracts (ADDITIVE - Backward Compatible)

**POST /v1/aois Response**
```diff
{
  "id": "uuid",
  "name": "Talhão Norte",
  "geometry": "MULTIPOLYGON(...)",
+ "tile_mapping": [
+   {
+     "mgrs_id": "23KPQ",
+     "coverage_pct": 85.5
+   }
+ ]
}
```
**Breaking:** NO (new field optional, existing clients ignore it)

**GET /v1/aois/{id} Response**
```diff
{
  "id": "uuid",
  "name": "Talhão Norte",
+ "mgrs_tiles": [
+   {
+     "mgrs_id": "23KPQ",
+     "coverage_pct": 85.5,
+     "status": "READY",
+     "cloud_cover": 12.3
+   }
+ ]
}
```
**Breaking:** NO (new field optional)

#### Database Contracts (ADDITIVE)

**New Tables:**
```sql
sentinel_tiles (shared across tenants)
aoi_tile_mapping (foreign key: aois.id)
mgrs_grid (reference data, preloaded)
```

**Modified Tables:** NONE (pure additions)

**Breaking:** NO (existing queries unaffected)

#### S3 Storage Contract (ADDITIVE)

**Current Structure:**
```
s3://vivacampo/tenant={uuid}/aoi={uuid}/year=2026/week=5/pipeline=v1/
├── ndvi.tif
├── B02.tif (DUPLICATE if AOIs overlap)
├── B04.tif (DUPLICATE)
└── ...
```

**New Structure (Dual-Write Phase):**
```
s3://vivacampo/tiles/sentinel2/mgrs=23KPQ/year=2026/week=5/
├── B02.tif (SHARED, downloaded once)
├── B04.tif (SHARED)
└── ...

s3://vivacampo/tenant={uuid}/aoi={uuid}/year=2026/week=5/indices/
├── ndvi.tif (per-AOI, small, clipped)
├── savi.tif
└── ...
```

**Breaking:** NO (old paths remain during migration, deleted in Phase 4)

#### Event/Message Contracts (NEW)

**New SQS Message Types:**
```json
{
  "job_type": "DOWNLOAD_TILE",
  "payload": {
    "mgrs_id": "23KPQ",
    "collection": "sentinel-2-l2a",
    "year": 2026,
    "week": 5
  }
}

{
  "job_type": "PROCESS_AOI_INDICES",
  "payload": {
    "tenant_id": "uuid",
    "aoi_id": "uuid",
    "year": 2026,
    "week": 5
  }
}
```

**Breaking:** NO (new job types, existing types unchanged)

---

## RISK ASSESSMENT

| Risk Category | Severity | Description | Mitigation |
|---------------|----------|-------------|------------|
| **Regression - Job Orchestration** | HIGH | New tile download dependencies could block AOI processing. If DOWNLOAD_TILE fails, multiple AOIs waiting for same tile are blocked. | 1. Implement retry logic with exponential backoff<br>2. Add timeout (30min) for tile download<br>3. Add job status dashboard to detect stuck tiles<br>4. Feature flag: `USE_TILE_BASED_PROCESSING=false` for rollback |
| **Regression - Data Consistency** | MEDIUM | Race condition: Two jobs try to download same tile simultaneously. | Use database UNIQUE constraint on (collection, mgrs_id, year, week) with ON CONFLICT DO UPDATE. First job wins, second updates status. |
| **Compatibility - Database Migration** | MEDIUM | Large migration (preload ~500 MGRS tiles for Brazil). Migration could take 5-10 minutes. | 1. Run migration during maintenance window<br>2. Test on staging first<br>3. Pre-generate MGRS grid CSV for fast import<br>4. Use COPY instead of INSERT for bulk load |
| **Performance - Clipping Latency** | MEDIUM | In-memory clipping of full MGRS tiles (10,000x10,000 px) could be slower than downloading pre-clipped AOI. | 1. Profile clipping performance on test AOIs<br>2. Use rasterio windowed reading to reduce memory<br>3. Implement tile-level caching in Redis<br>4. Monitor job duration, set SLA (5min for indices calculation) |
| **Security - Cross-Tenant Data Leak** | HIGH | Shared tiles accessible by all tenants. Misconfigured S3 presigned URL could expose tile data to wrong tenant. | 1. Tiles are raw bands (no sensitive info), but audit S3 access logs<br>2. Verify presigned URLs include correct IAM policy<br>3. Indices remain per-tenant (sensitive data isolated)<br>4. Add integration test: Tenant A cannot access Tenant B's indices |
| **Data - Storage Costs (Transition)** | MEDIUM | During dual-write phase (Phase 2-3), storage doubles. | 1. Limit dual-write to 4 weeks max<br>2. Delete old per-AOI raw bands immediately after migration verification<br>3. Monitor S3 costs daily during migration |
| **Observability - Debugging Complexity** | MEDIUM | Multi-stage job pipeline harder to debug. Which job failed: tile download or indices calculation? | 1. Add structured logging with trace_id across jobs<br>2. Add job dependency graph visualization in admin UI<br>3. Add Datadog APM tracing for job flows<br>4. Store job lineage (parent_job_id) in database |
| **Scalability - Worker Bottleneck** | LOW | Tile downloads are I/O-bound. May need more workers during backfill. | 1. Monitor SQS queue depth<br>2. Scale workers horizontally (ECS Fargate autoscaling)<br>3. Separate queues: tiles-queue (high priority) vs indices-queue |

---

## VALIDATION CHECKLIST

### Before Deployment (Phase 1: Schema Migration)

- [ ] **Database Migration Tested**
  - [ ] Run migration on staging database
  - [ ] Verify MGRS grid has 500+ rows for Brazil
  - [ ] Check indexes created (idx_sentinel_tiles_mgrs, idx_aoi_tile_mapping_mgrs)
  - [ ] Rollback script tested

- [ ] **MGRS Grid Data Prepared**
  - [ ] Generate MGRS grid GeoJSON for Brazil (lat: -35 to 5, lon: -75 to -30)
  - [ ] Validate grid coverage against Sentinel-2 tile grid
  - [ ] Load test: Insert 500 tiles in <30 seconds

- [ ] **Backward Compatibility Verified**
  - [ ] Existing AOI creation works (POST /v1/aois)
  - [ ] Existing job processing works (PROCESS_WEEK still functional)
  - [ ] Frontend displays map tiles without errors

### Before Deployment (Phase 2: Dual-Write Mode)

- [ ] **AOI Creation Enhanced**
  - [ ] POST /v1/aois calculates MGRS tiles for geometry
  - [ ] aoi_tile_mapping records inserted correctly
  - [ ] Response includes tile_mapping field
  - [ ] Test with AOI spanning 2 tiles (edge case)
  - [ ] Test with small AOI (1 tile) and large AOI (4 tiles)

- [ ] **Tile Calculation Accuracy**
  - [ ] Verify shapely intersection logic correct
  - [ ] coverage_pct calculation validated (sum should be ~100%)
  - [ ] Test with MultiPolygon AOI (multiple disconnected parts)

### Before Deployment (Phase 3: Tile-Based Processing)

- [ ] **New Job Types Implemented**
  - [ ] DOWNLOAD_TILE job handler complete
  - [ ] PROCESS_AOI_INDICES job handler complete
  - [ ] Jobs registered in worker/main.py dispatcher
  - [ ] SQS message schemas validated

- [ ] **Tile Download Logic**
  - [ ] Search STAC by MGRS tile boundary (not AOI)
  - [ ] Download full tile (no clipping) as COG
  - [ ] Upload to s3://bucket/tiles/sentinel2/mgrs={id}/...
  - [ ] Update sentinel_tiles table with status=READY
  - [ ] Handle NO_DATA case (no scenes found)
  - [ ] Handle FAILED case (download error, retry)

- [ ] **Indices Calculation Logic**
  - [ ] Load tiles from S3 (read-only)
  - [ ] Clip to AOI geometry using rasterio.mask
  - [ ] Mosaic if AOI spans multiple tiles
  - [ ] Calculate all 14 indices (NDVI, NDRE, EVI, etc.)
  - [ ] Upload to s3://bucket/tenant={id}/aoi={id}/year={y}/week={w}/indices/
  - [ ] Update derived_assets table (same as before)

- [ ] **Job Orchestration**
  - [ ] BACKFILL creates DOWNLOAD_TILE jobs for missing tiles
  - [ ] BACKFILL waits for tiles to be READY before creating PROCESS_AOI_INDICES
  - [ ] Idempotency: Re-running BACKFILL doesn't duplicate jobs
  - [ ] Timeout: Tile download timeout 30 minutes
  - [ ] Retry: Failed tile download retries 3x with backoff

- [ ] **Feature Flag**
  - [ ] Environment variable USE_TILE_BASED_PROCESSING=true|false
  - [ ] Default: false (safe rollout)
  - [ ] New AOIs: Use tile-based if flag=true, else use old logic
  - [ ] Test: Toggle flag, create AOI, verify correct job type created

### Before Deployment (Phase 4: Backfill Migration)

- [ ] **Data Migration Script**
  - [ ] Identify all existing AOIs without tile mappings
  - [ ] Calculate MGRS tiles for each AOI
  - [ ] Detect shared tiles across AOIs
  - [ ] Mark tiles for deduplication

- [ ] **Storage Cleanup**
  - [ ] Identify duplicate raw bands (B02, B04, etc. in per-AOI paths)
  - [ ] Verify tiles exist in new MGRS paths before deleting old paths
  - [ ] Backup old data to Glacier before deletion
  - [ ] Monitor storage costs (should drop 60-80%)

### After Deployment (Operational Validation)

- [ ] **Functional Smoke Tests**
  - [ ] Create new AOI → Verify tile_mapping in response
  - [ ] Trigger backfill → Verify DOWNLOAD_TILE jobs created
  - [ ] Wait for processing → Verify indices appear in S3
  - [ ] View map → Verify tiles display correctly

- [ ] **Performance Monitoring**
  - [ ] Job duration: DOWNLOAD_TILE <10min p95
  - [ ] Job duration: PROCESS_AOI_INDICES <5min p95
  - [ ] SQS queue depth: <100 messages
  - [ ] Error rate: <1% failed jobs

- [ ] **Cost Monitoring**
  - [ ] S3 storage: Should decrease 60-80% after migration
  - [ ] S3 GET requests: Should decrease 70% (fewer downloads)
  - [ ] S3 bandwidth: Should decrease 70%
  - [ ] Worker CPU: May increase 10-20% (clipping overhead)

---

## ROLLOUT PLAN

### Phase 1: Schema Migration (Non-Breaking, 1 Day)

**Goal:** Add new tables without changing application behavior

**Steps:**
1. Deploy migration script 005_add_mgrs_tile_lake.sql
2. Preload mgrs_grid table with Brazil MGRS tiles (SQL script)
3. Verify indexes created
4. Deploy API (no code changes, just schema awareness)
5. Deploy worker (no code changes)

**Validation:**
- Migration completes in <5 minutes
- Application continues to work (no errors)
- Database queries unaffected

**Rollback:** Drop new tables (safe, no data loss)

**Go/No-Go Signals:**
- ✅ PROCEED: Migration success, no application errors
- 🛑 ABORT: Migration timeout, index creation failure

---

### Phase 2: Dual-Write Mode (AOI Creation Enhanced, 2 Days)

**Goal:** Calculate and store MGRS tile mappings on AOI creation

**Steps:**
1. Deploy API with enhanced POST /v1/aois endpoint
   - Calculate MGRS tiles using PostGIS ST_Intersects
   - Insert aoi_tile_mapping records
   - Return tile_mapping in response
2. Test AOI creation with various geometries
3. Keep old processing logic (PROCESS_WEEK) active

**Validation:**
- New AOIs have tile_mapping populated
- Old AOIs continue processing normally
- No errors in logs

**Rollback:** Revert API deployment (aoi_tile_mapping data harmless)

**Go/No-Go Signals:**
- ✅ PROCEED: 100 AOIs created successfully with tile_mapping
- 🛑 ABORT: Tile calculation errors, performance regression (>2s AOI creation time)

---

### Phase 3: Tile-Based Processing (New AOIs Only, 1 Week)

**Goal:** Enable new processing pipeline for new AOIs

**Steps:**
1. Deploy worker with new job types (DOWNLOAD_TILE, PROCESS_AOI_INDICES)
2. Set feature flag USE_TILE_BASED_PROCESSING=true for new AOIs
3. Monitor job execution closely
4. Keep old pipeline active for existing AOIs

**Validation:**
- 10 new AOIs processed successfully via tile pipeline
- Indices match old pipeline output (regression test)
- No stuck jobs (30min timeout enforced)
- Job duration acceptable (<15min total)

**Rollback:** Set feature flag to false, revert worker deployment

**Go/No-Go Signals:**
- ✅ PROCEED: 100% success rate for 50+ new AOIs, job duration <15min p95
- 🛑 ABORT: >5% failure rate, job duration >30min, S3 download errors

---

### Phase 4: Backfill Migration (Existing AOIs, 2 Weeks)

**Goal:** Migrate existing AOIs to tile-based processing, deduplicate storage

**Steps:**
1. Calculate MGRS mappings for all existing AOIs (batch script)
2. Run deduplication analysis (identify shared tiles)
3. Download shared tiles to new MGRS paths
4. Verify tile data integrity (checksum comparison)
5. Delete old per-AOI raw bands (B02, B04, etc.)
6. Keep indices (already per-AOI, no change)
7. Monitor storage costs

**Validation:**
- All AOIs have tile_mapping
- Storage reduction 60-80%
- No data loss (spot-check 10% of AOIs)
- Processing continues normally

**Rollback:** Restore from Glacier backup (30-day retention)

**Go/No-Go Signals:**
- ✅ PROCEED: Storage costs drop, data integrity verified, no processing errors
- 🛑 ABORT: Data corruption detected, storage costs increase, tile download failures

---

### Phase 5: Cleanup (Finalize, 1 Week)

**Goal:** Remove old processing logic, finalize migration

**Steps:**
1. Remove PROCESS_WEEK job handler (replaced by PROCESS_AOI_INDICES)
2. Remove feature flag (tile-based processing now default)
3. Update documentation
4. Notify stakeholders of storage savings

**Validation:**
- All processing uses tile-based pipeline
- No references to old job types
- Documentation up-to-date

**Rollback:** NONE (Point of no return - communicate clearly to stakeholders)

---

## GIS TOOL INTEGRATION API

### New Endpoints for QGIS/ArcGIS

**Use Case:** External users want to access raw MGRS tiles for custom analysis

**Authentication:** OAuth2 bearer token (tenant-scoped)

**Endpoint Design:**

#### 1. List Available Tiles
```
GET /v1/tiles/mgrs?bbox=-48.5,-15.8,-48.2,-15.5&year=2026&week=5&collection=sentinel-2-l2a

Response:
{
  "tiles": [
    {
      "mgrs_id": "23KPQ",
      "collection": "sentinel-2-l2a",
      "year": 2026,
      "week": 5,
      "status": "READY",
      "cloud_cover": 12.3,
      "bbox": [-48.5, -15.8, -48.2, -15.5]
    }
  ]
}
```

**Security:** No tenant filtering (tiles are public), but rate-limited

#### 2. Get Tile Details
```
GET /v1/tiles/mgrs/23KPQ?year=2026&week=5

Response:
{
  "mgrs_id": "23KPQ",
  "collection": "sentinel-2-l2a",
  "year": 2026,
  "week": 5,
  "status": "READY",
  "cloud_cover": 12.3,
  "scene_datetime": "2026-02-01T13:25:00Z",
  "bands": {
    "B02": {
      "s3_uri": "s3://vivacampo/tiles/sentinel2/mgrs=23KPQ/year=2026/week=5/B02.tif",
      "cog_url": null, # Generated on demand
      "tiler_url": null # Generated on demand
    },
    "B04": {...}
  },
  "geometry": {
    "type": "Polygon",
    "coordinates": [...]
  }
}
```

**Security:** S3 URIs visible but not directly accessible (requires presigned URL)

#### 3. Get Presigned COG URL
```
GET /v1/tiles/mgrs/23KPQ/cog?band=B04&year=2026&week=5

Response:
{
  "cog_url": "https://s3.amazonaws.com/vivacampo/tiles/...?X-Amz-Signature=...",
  "expires_in": 3600,
  "tiler_url": "https://api.vivacampo.com/cog/tiles/{z}/{x}/{y}?url=https://..."
}
```

**Security:** Presigned URL expires in 1 hour, tenant-scoped IAM policy

**Rate Limiting:** 100 requests/minute per tenant

---

## MULTI-TENANT SECURITY

### Concern: Shared Tiles Across Tenants

**Q:** Can Tenant A access Tenant B's data via shared tiles?

**A:** NO - Tiles are raw bands (no sensitive business data). However, we must ensure:

1. **Tiles are intentionally shared** (sentinel-2-l2a is public data from Planetary Computer)
2. **Indices remain tenant-isolated** (NDVI, anomaly, etc. are derived per-AOI and stored in tenant-specific paths)
3. **S3 bucket policies enforce tenant isolation for indices**

### Security Controls

#### 1. S3 Bucket Structure
```
s3://vivacampo/
├── tiles/                          # Shared (public within system)
│   └── sentinel2/mgrs=23KPQ/...   # Raw bands (B02, B04, etc.)
├── tenant={uuid}/                  # Tenant-isolated
│   └── aoi={uuid}/indices/        # Derived indices (NDVI, etc.)
```

#### 2. IAM Policies
```json
{
  "Effect": "Allow",
  "Action": ["s3:GetObject"],
  "Resource": "arn:aws:s3:::vivacampo/tiles/*",
  "Principal": "*"  # Shared tiles accessible by all workers
}

{
  "Effect": "Allow",
  "Action": ["s3:GetObject", "s3:PutObject"],
  "Resource": "arn:aws:s3:::vivacampo/tenant=${tenant_id}/*",
  "Condition": {
    "StringEquals": {"s3:ExistingObjectTag/tenant_id": "${tenant_id}"}
  }
}
```

#### 3. Presigned URL Security
- Include `tenant_id` in URL generation context
- Validate tenant_id matches requesting user
- Short expiration (1 hour for GIS tools, 15 minutes for frontend)

#### 4. Audit Logging
- Log all S3 access to tiles (CloudTrail)
- Alert on suspicious access patterns (e.g., Tenant A accessing 1000+ tiles/hour)

### Test Cases

```python
def test_tenant_isolation():
    """Verify Tenant A cannot access Tenant B's indices"""
    tenant_a_token = login_as_tenant_a()
    tenant_b_aoi_id = create_aoi_as_tenant_b()

    # Attempt to fetch Tenant B's assets with Tenant A's token
    response = requests.get(
        f"/v1/aois/{tenant_b_aoi_id}/assets",
        headers={"Authorization": f"Bearer {tenant_a_token}"}
    )

    assert response.status_code == 404  # Not found (tenant_id mismatch)

def test_shared_tile_access():
    """Verify both tenants can access shared MGRS tiles"""
    tile_id = "23KPQ"

    # Tenant A
    response_a = requests.get(f"/v1/tiles/mgrs/{tile_id}", headers=tenant_a_auth)
    assert response_a.status_code == 200

    # Tenant B
    response_b = requests.get(f"/v1/tiles/mgrs/{tile_id}", headers=tenant_b_auth)
    assert response_b.status_code == 200

    # Same tile metadata returned
    assert response_a.json()["mgrs_id"] == response_b.json()["mgrs_id"]
```

---

## RECOMMENDED TESTING PLAN

### Unit Tests (90% Coverage Target)

**New Modules:**
- `test_mgrs_tile_calculator.py` - MGRS intersection logic
- `test_download_tile_job.py` - Tile download handler
- `test_process_aoi_indices_job.py` - Indices calculation from tiles
- `test_tiles_router.py` - New API endpoints

**Modified Modules:**
- `test_aois_router.py` - Verify tile_mapping in POST response
- `test_backfill_job.py` - Verify DOWNLOAD_TILE job creation
- `test_stac_client.py` - Verify search_by_mgrs_tile() method

### Integration Tests (Critical Paths)

```python
def test_end_to_end_tile_based_processing():
    """Create AOI → Trigger backfill → Verify indices generated"""
    # 1. Create AOI
    aoi = create_aoi(geometry=test_polygon)
    assert len(aoi.tile_mapping) > 0

    # 2. Trigger backfill
    backfill_job = trigger_backfill(aoi.id, from_date="2026-01-01", to_date="2026-01-07")

    # 3. Wait for tile download
    wait_for_job_completion(backfill_job.id, timeout=600)

    # 4. Verify tiles downloaded
    tiles = db.query(SentinelTile).filter_by(mgrs_id=aoi.tile_mapping[0].mgrs_id).all()
    assert all(t.status == "READY" for t in tiles)

    # 5. Verify indices generated
    assets = get_aoi_assets(aoi.id)
    assert assets.ndvi_s3_uri is not None
    assert assets.ndvi_mean > 0

    # 6. Verify tile displayed on map
    response = requests.get(assets.ndvi_tile_url)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "image/png"

def test_tile_deduplication():
    """Create 2 overlapping AOIs → Verify tile downloaded only once"""
    # 1. Create AOI A
    aoi_a = create_aoi(geometry=polygon_a)

    # 2. Create AOI B (overlapping)
    aoi_b = create_aoi(geometry=polygon_b_overlapping)

    # 3. Verify both AOIs map to same MGRS tile
    assert aoi_a.tile_mapping[0].mgrs_id == aoi_b.tile_mapping[0].mgrs_id

    # 4. Trigger backfills
    trigger_backfill(aoi_a.id, from_date="2026-01-01", to_date="2026-01-07")
    trigger_backfill(aoi_b.id, from_date="2026-01-01", to_date="2026-01-07")

    # 5. Wait for completion
    wait_for_all_jobs_complete(timeout=600)

    # 6. Verify tile downloaded ONCE
    tiles = db.query(SentinelTile).filter_by(
        mgrs_id=aoi_a.tile_mapping[0].mgrs_id,
        year=2026,
        week=1
    ).all()
    assert len(tiles) == 1  # Single tile record

    # 7. Verify both AOIs have indices
    assert get_aoi_assets(aoi_a.id).ndvi_s3_uri is not None
    assert get_aoi_assets(aoi_b.id).ndvi_s3_uri is not None

def test_cross_tenant_tile_sharing():
    """Verify shared tiles work across tenants"""
    # 1. Tenant A creates AOI in region
    aoi_a = create_aoi_as_tenant_a(geometry=polygon_sao_paulo)
    trigger_backfill(aoi_a.id)
    wait_for_completion(aoi_a.id)

    # 2. Verify tile downloaded
    tile = db.query(SentinelTile).filter_by(mgrs_id=aoi_a.tile_mapping[0].mgrs_id).first()
    assert tile.status == "READY"

    # 3. Tenant B creates AOI in SAME region
    aoi_b = create_aoi_as_tenant_b(geometry=polygon_sao_paulo_nearby)
    trigger_backfill(aoi_b.id)
    wait_for_completion(aoi_b.id)

    # 4. Verify tile NOT re-downloaded (status remains READY, no new download job)
    jobs = db.query(Job).filter_by(
        job_type="DOWNLOAD_TILE",
        payload_json__mgrs_id=aoi_a.tile_mapping[0].mgrs_id
    ).all()
    assert len(jobs) == 1  # Only one download job created (by Tenant A)

    # 5. Verify both tenants have indices (tenant-isolated)
    assets_a = get_aoi_assets_as_tenant_a(aoi_a.id)
    assets_b = get_aoi_assets_as_tenant_b(aoi_b.id)
    assert assets_a.ndvi_s3_uri != assets_b.ndvi_s3_uri  # Different paths
    assert "tenant=tenant_a_id" in assets_a.ndvi_s3_uri
    assert "tenant=tenant_b_id" in assets_b.ndvi_s3_uri
```

### Performance Tests

```python
def test_tile_download_performance():
    """Verify tile download completes within SLA"""
    mgrs_id = "23KPQ"
    start = time.time()

    job = create_download_tile_job(mgrs_id, year=2026, week=5)
    wait_for_job_completion(job.id, timeout=600)

    duration = time.time() - start
    assert duration < 600  # 10 minutes max

    # Verify tile in S3
    assert s3_object_exists(f"tiles/sentinel2/mgrs={mgrs_id}/year=2026/week=5/B04.tif")

def test_indices_calculation_performance():
    """Verify indices calculation completes within SLA"""
    aoi = create_aoi(geometry=test_polygon_medium_size)  # 100 hectares

    # Assume tile already downloaded
    ensure_tile_ready(aoi.tile_mapping[0].mgrs_id, year=2026, week=5)

    start = time.time()
    job = create_process_aoi_indices_job(aoi.id, year=2026, week=5)
    wait_for_job_completion(job.id, timeout=300)

    duration = time.time() - start
    assert duration < 300  # 5 minutes max
```

---

## MIGRATION SCRIPTS

### Script 1: Generate MGRS Grid

```python
# scripts/generate_mgrs_grid.py
import mgrs
import json
from shapely.geometry import Polygon

def generate_brazil_mgrs_grid():
    """Generate MGRS grid tiles covering Brazil"""
    m = mgrs.MGRS()
    tiles = []

    # Brazil bounding box: lat -35 to 5, lon -75 to -30
    for lat in range(-35, 6):
        for lon in range(-75, -29):
            try:
                # Get MGRS tile ID for this lat/lon
                tile_id = m.toMGRS(lat, lon, MGRSPrecision=0)[:5]  # e.g., "23KPQ"

                if tile_id not in [t["mgrs_id"] for t in tiles]:
                    # Get tile boundary
                    bounds = get_mgrs_tile_bounds(tile_id)

                    tiles.append({
                        "mgrs_id": tile_id,
                        "utm_zone": int(tile_id[:2]),
                        "latitude_band": tile_id[2],
                        "grid_square": tile_id[3:5],
                        "geometry": bounds.wkt
                    })
            except:
                pass

    return tiles

# Output as SQL INSERT statements
tiles = generate_brazil_mgrs_grid()
with open("mgrs_grid_insert.sql", "w") as f:
    for tile in tiles:
        f.write(f"""
INSERT INTO mgrs_grid (mgrs_id, utm_zone, latitude_band, grid_square, geom, centroid)
VALUES (
    '{tile["mgrs_id"]}',
    {tile["utm_zone"]},
    '{tile["latitude_band"]}',
    '{tile["grid_square"]}',
    ST_GeomFromText('{tile["geometry"]}', 4326),
    ST_Centroid(ST_GeomFromText('{tile["geometry"]}', 4326))
);
""")
```

### Script 2: Calculate AOI Tile Mappings (Backfill)

```python
# scripts/calculate_aoi_tile_mappings.py
from sqlalchemy import text
from app.database import get_db

def calculate_tile_mappings_for_aoi(aoi_id: str, db):
    """Calculate MGRS tiles that intersect AOI"""
    sql = text("""
        INSERT INTO aoi_tile_mapping (aoi_id, mgrs_id, coverage_pct, intersection_geom)
        SELECT
            :aoi_id,
            g.mgrs_id,
            100.0 * ST_Area(ST_Intersection(a.geom, g.geom)::geography) / ST_Area(a.geom::geography) as coverage_pct,
            ST_Intersection(a.geom, g.geom) as intersection_geom
        FROM aois a, mgrs_grid g
        WHERE a.id = :aoi_id
          AND ST_Intersects(a.geom, g.geom)
        ON CONFLICT (aoi_id, mgrs_id) DO NOTHING
    """)

    db.execute(sql, {"aoi_id": aoi_id})
    db.commit()

# Batch process all AOIs
with get_db() as db:
    aoi_ids = db.execute(text("SELECT id FROM aois")).fetchall()
    for row in aoi_ids:
        calculate_tile_mappings_for_aoi(str(row.id), db)
        print(f"Processed AOI {row.id}")
```

---

## RELEASE NOTES TEMPLATES

### For Engineering Team

**Internal Changelog - ADR-0007 Implementation**

**BREAKING CHANGES:**
- New job types DOWNLOAD_TILE and PROCESS_AOI_INDICES replace PROCESS_WEEK for new AOIs
- Database schema updated: 3 new tables (sentinel_tiles, aoi_tile_mapping, mgrs_grid)
- Feature flag USE_TILE_BASED_PROCESSING controls new vs old pipeline

**New Features:**
- MGRS tile-based storage deduplication (60-80% storage savings)
- GIS tool integration API (/v1/tiles/mgrs endpoints)
- Shared tile download across tenants
- AOI creation now calculates MGRS tile mappings

**Modified Behavior:**
- AOI creation response includes tile_mapping field
- Backfill jobs now orchestrate tile downloads before indices calculation
- S3 structure changed: Raw bands in tiles/, indices in tenant= paths

**Migration Steps:**
1. Run database migration 005_add_mgrs_tile_lake.sql
2. Preload MGRS grid (scripts/generate_mgrs_grid.py)
3. Deploy API and worker with feature flag OFF
4. Enable feature flag for new AOIs
5. Run backfill migration script for existing AOIs

**Rollback Plan:**
- Phase 1-2: Revert deployment, drop new tables
- Phase 3: Set feature flag to false
- Phase 4+: Restore from Glacier backup (contact DevOps)

---

### For QA Team

**Testing Instructions - ADR-0007 MGRS Tile Data Lake**

**Priority Test Areas:**

1. **AOI Creation Flow** (Regression Test)
   - Create AOI with various geometries (small, large, multi-polygon)
   - Verify tile_mapping appears in response
   - Verify map displays correctly after creation

2. **Tile Download Jobs** (New Feature)
   - Trigger backfill for new AOI
   - Monitor jobs page, verify DOWNLOAD_TILE jobs created
   - Verify tiles status transitions: PENDING → DOWNLOADING → READY
   - Check S3 for tiles/ path

3. **Indices Calculation** (Regression Test)
   - Wait for PROCESS_AOI_INDICES job completion
   - Verify derived_assets has NDVI, SAVI, etc.
   - Verify map displays indices correctly
   - Compare with old pipeline output (should match)

4. **Cross-Tenant Tile Sharing** (Security Test)
   - Create 2 overlapping AOIs in different tenants
   - Verify tile downloaded only once
   - Verify both tenants can view their own indices
   - Verify Tenant A cannot access Tenant B's indices

5. **GIS Tool Integration** (New Feature)
   - Use Postman to call /v1/tiles/mgrs endpoints
   - Verify presigned URLs work in QGIS
   - Verify rate limiting (100 req/min)

**Test Data Requirements:**
- Test accounts for 2 tenants
- AOIs in São Paulo region (MGRS tile 23KPQ) for overlap testing
- Historical date range with known good scenes (2025-01-01 to 2025-01-31)

**Expected Behaviors:**
- AOI creation: <3 seconds
- Tile download: <10 minutes
- Indices calculation: <5 minutes
- Map tile rendering: <500ms

**Known Issues:**
- Tile download may timeout on slow networks (30min limit)
- Large AOIs (>1000 ha) may take longer to process

---

### For Stakeholders

**Release Summary - Storage Optimization via MGRS Tile Data Lake**

**What Changed:**
We implemented a new satellite data storage architecture that eliminates duplicate downloads and reduces storage costs by 60-80%.

**User-Facing Impact:**
- **No changes to UI or workflows** - Users continue creating AOIs and viewing maps as before
- **Faster processing for overlapping farms** - If farms are near each other, satellite data is downloaded once and shared
- **New capability:** Export raw satellite data to QGIS/ArcGIS for advanced analysis

**Business Benefits:**
- **Cost Savings:** ~$500/month in S3 storage costs (based on 100 active farms)
- **Faster Onboarding:** New farms in existing regions process 2-3x faster
- **Scalability:** System can now support 10,000+ farms without linear storage growth

**Timeline:**
- Phase 1-2: Completed (Feb 10-12) - No user impact
- Phase 3: In progress (Feb 13-20) - New AOIs using optimized storage
- Phase 4: Planned (Feb 21-28) - Migrate existing AOIs, storage costs drop

**Risks Mitigated:**
- Gradual rollout with feature flag (can revert if issues detected)
- Dual-write mode ensures no data loss during migration
- Existing AOIs continue working normally during transition

---

## CONCLUSION

ADR-0007 represents a **major architectural evolution** with significant benefits (60-80% storage reduction, improved scalability) but also introduces **substantial complexity** in job orchestration and cross-tenant tile management.

**Critical Success Factors:**
1. **Comprehensive testing** of tile download and indices calculation logic
2. **Phased rollout** with feature flag control
3. **Monitoring and alerting** for job failures and stuck tiles
4. **Clear rollback procedures** at each phase
5. **Security validation** of cross-tenant tile access

**Recommended Decision:** PROCEED with implementation following the phased rollout plan, with strict adherence to validation checkpoints before advancing phases.

**High-Risk Areas Requiring Extra Attention:**
- Job dependency management (tile download blocking indices calculation)
- Database migration performance (MGRS grid preload)
- Cross-tenant security (presigned URL validation)
- Worker scaling during backfill (I/O bottlenecks)

**Estimated Timeline:** 5-6 weeks from Phase 1 to Phase 5 completion.

---

**Document Prepared By:** System Analysis
**Review Required By:** Tech Lead, DevOps Lead, Product Owner
**Approval Required Before:** Phase 3 deployment (tile-based processing activation)
