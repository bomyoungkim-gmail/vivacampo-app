# Runbook — Migrations

Last Updated: 2026-02-03

## Principles
- **Prefer expand/contract** for breaking schema changes (avoid downtime)
- **Avoid long locks** on large tables (use `CONCURRENTLY` for indices)
- **Test on staging** before production (always)
- **Idempotent migrations** (safe to run multiple times)
- **Backward compatible** (old code works with new schema during transition)

---

## Expand/Contract Pattern

**Goal:** Zero-downtime schema changes.

### Example: Rename Column

**Problem:** Rename `copilot_threads` table to `ai_assistant_threads`.

**❌ Breaking approach (causes downtime):**
```sql
ALTER TABLE copilot_threads RENAME TO ai_assistant_threads;
```
**Issue:** Old code breaks immediately (references `copilot_threads`).

**✅ Expand/Contract approach (zero downtime):**

**Step 1: Expand (add new table)**
```sql
-- Migration 002_add_ai_assistant_threads.sql
CREATE TABLE ai_assistant_threads (
  -- same schema as copilot_threads
);

-- Copy existing data
INSERT INTO ai_assistant_threads SELECT * FROM copilot_threads;
```

**Step 2: Deploy code supporting both tables**
```python
# Code reads from ai_assistant_threads, writes to both
def create_thread(data):
    thread = AIAssistantThread(**data)
    db.add(thread)
    
    # Also write to old table (for backward compat)
    old_thread = CopilotThread(**data)
    db.add(old_thread)
    db.commit()
```

**Step 3: Backfill (ensure data sync)**
```sql
-- Sync any missing data
INSERT INTO ai_assistant_threads 
SELECT * FROM copilot_threads 
WHERE id NOT IN (SELECT id FROM ai_assistant_threads);
```

**Step 4: Switch reads to new table**
```python
# Code now only reads/writes ai_assistant_threads
def create_thread(data):
    thread = AIAssistantThread(**data)
    db.add(thread)
    db.commit()
```

**Step 5: Contract (remove old table)**
```sql
-- Migration 003_drop_copilot_threads.sql
DROP TABLE copilot_threads;
```

**Timeline:** ~1 week (allows safe rollback at each step).

---

## Migration Checklist

**Before writing migration:**
- [ ] Understand current schema (`\d table_name` in psql)
- [ ] Identify affected queries (grep codebase)
- [ ] Estimate table size (`SELECT COUNT(*) FROM table;`)
- [ ] Choose strategy (expand/contract vs direct change)

**Writing migration:**
- [ ] Use `IF NOT EXISTS` / `IF EXISTS` (idempotent)
- [ ] Add comments explaining why
- [ ] Include rollback plan (down migration or notes)
- [ ] Test on local database

**Before deploying:**
- [ ] Test on staging database
- [ ] Measure migration runtime (use `EXPLAIN ANALYZE`)
- [ ] Check for lock conflicts (`SELECT * FROM pg_locks;`)
- [ ] Prepare rollback plan

**After deploying:**
- [ ] Verify migration applied (`SELECT * FROM schema_migrations;`)
- [ ] Verify data integrity (spot check)
- [ ] Monitor for errors (logs, metrics)

---

## Planned Migration — Add jobs.error_message

**Goal:** Persist job failure reasons for admin visibility and troubleshooting.

**Steps:**
1. Add nullable column `jobs.error_message` (text).
2. Deploy code that writes `error_message` on job failure.
3. (Optional) Surface error_message in Admin UI for failed jobs.

**Rollback:**
- Drop column `jobs.error_message` if needed:
```sql
ALTER TABLE jobs DROP COLUMN IF EXISTS error_message;
```

---

## Planned Migration — Enable RLS (Row-Level Security)

**Goal:** Enforce tenant isolation at DB level for tenant-scoped tables.

**Migration:** `infra/migrations/sql/005_enable_rls.sql`

**Pre-req (code):**
- API must set `app.tenant_id` per request (DB session).
- System admin flow must set `app.is_system_admin=true` (bypass policy).
- Worker must set `app.tenant_id` per job.

**Notes:**
- Tables without `tenant_id` (e.g., `tenants`, `memberships`, `identities`) are excluded.
- Policies are additive: `tenant_isolation` OR `system_admin_bypass`.

**Rollback (manual):**
```sql
ALTER TABLE farms DISABLE ROW LEVEL SECURITY;
-- Repeat for each table in the migration.
```

**Rollout Checklist:**
- [ ] Apply migration on staging
- [ ] Verify `rowsecurity = t` for tenant tables
- [ ] Verify system-admin endpoints still work (global queries)
- [ ] Run `pytest tests/security -v`
- [ ] Apply migration on production during low traffic window
- [ ] Monitor DB errors and 403/401 spikes after rollout

---

## Common Migration Patterns

### 1. Add Column (Safe)
```sql
-- Add column with default value (safe, no lock)
ALTER TABLE aois ADD COLUMN status TEXT DEFAULT 'ACTIVE';

-- Add NOT NULL constraint later (after backfill)
UPDATE aois SET status = 'ACTIVE' WHERE status IS NULL;
ALTER TABLE aois ALTER COLUMN status SET NOT NULL;
```

### 2. Add Index (Use CONCURRENTLY)
```sql
-- ❌ Locks table during index creation
CREATE INDEX aois_tenant_idx ON aois(tenant_id);

-- ✅ No lock (safe for production)
CREATE INDEX CONCURRENTLY aois_tenant_idx ON aois(tenant_id);
```

### 3. Add Foreign Key (Two Steps)
```sql
-- Step 1: Add column (nullable)
ALTER TABLE jobs ADD COLUMN tenant_id UUID;

-- Step 2: Backfill data
UPDATE jobs SET tenant_id = (SELECT tenant_id FROM aois WHERE aois.id = jobs.aoi_id);

-- Step 3: Add NOT NULL constraint
ALTER TABLE jobs ALTER COLUMN tenant_id SET NOT NULL;

-- Step 4: Add foreign key
ALTER TABLE jobs ADD CONSTRAINT jobs_tenant_fk 
  FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
```

### 4. Change Column Type (Expand/Contract)
```sql
-- Example: Change area_ha from FLOAT to NUMERIC(10,2)

-- Step 1: Add new column
ALTER TABLE aois ADD COLUMN area_ha_new NUMERIC(10,2);

-- Step 2: Backfill
UPDATE aois SET area_ha_new = area_ha::NUMERIC(10,2);

-- Step 3: Deploy code using area_ha_new

-- Step 4: Drop old column
ALTER TABLE aois DROP COLUMN area_ha;
ALTER TABLE aois RENAME COLUMN area_ha_new TO area_ha;
```

---

## Migration Commands

### Local (Development)
```bash
# Apply migration
docker compose exec -T db psql -U vivacampo -d vivacampo < infra/migrations/sql/002_new_migration.sql

# Verify
docker compose exec db psql -U vivacampo -d vivacampo -c "\d aois"
```

### Staging
```bash
# Connect to RDS
psql -h vivacampo-staging.xxxx.us-east-1.rds.amazonaws.com -U vivacampo -d vivacampo

# Apply migration
\i infra/migrations/sql/002_new_migration.sql

# Verify
\d aois
```

### Production
```bash
# ⚠️ CRITICAL: Always test on staging first!

# Connect to RDS (read-only first, to verify)
psql -h vivacampo-prod.xxxx.us-east-1.rds.amazonaws.com -U vivacampo_readonly -d vivacampo

# Dry run (EXPLAIN)
EXPLAIN UPDATE aois SET status = 'ACTIVE' WHERE status IS NULL;

# Apply migration (with write access)
psql -h vivacampo-prod.xxxx.us-east-1.rds.amazonaws.com -U vivacampo -d vivacampo
\i infra/migrations/sql/002_new_migration.sql
```

---

## Rollback Strategies

### 1. Down Migration (Preferred)
Create `infra/migrations/sql/down/002_revert.sql`:
```sql
-- Revert changes from 002_new_migration.sql
DROP TABLE IF EXISTS ai_assistant_threads;
-- etc
```

### 2. Snapshot Restore (Last Resort)
```bash
# Restore from snapshot (loses data since snapshot)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier vivacampo-prod-restored \
  --db-snapshot-identifier vivacampo-prod-2026-02-03-06-00
```

### 3. Forward Fix (If Possible)
```sql
-- Fix data corruption
UPDATE aois SET area_ha = ST_Area(geom::geography) / 10000 WHERE area_ha IS NULL;
```

---

## Performance Considerations

### Large Table Migrations
**Problem:** `ALTER TABLE` locks table, blocking reads/writes.

**Solution:** Use `CONCURRENTLY` or batch updates.

**Example: Add index to 1M row table**
```sql
-- ❌ Locks table for ~30 seconds
CREATE INDEX aois_tenant_idx ON aois(tenant_id);

-- ✅ No lock, takes ~60 seconds but no downtime
CREATE INDEX CONCURRENTLY aois_tenant_idx ON aois(tenant_id);
```

**Example: Update 1M rows**
```sql
-- ❌ Locks table for minutes
UPDATE aois SET status = 'ACTIVE' WHERE status IS NULL;

-- ✅ Batch updates (10k rows at a time)
DO $$
DECLARE
  batch_size INT := 10000;
  updated INT;
BEGIN
  LOOP
    UPDATE aois SET status = 'ACTIVE' 
    WHERE id IN (
      SELECT id FROM aois WHERE status IS NULL LIMIT batch_size
    );
    GET DIAGNOSTICS updated = ROW_COUNT;
    EXIT WHEN updated = 0;
    COMMIT;
    PERFORM pg_sleep(0.1);  -- Pause between batches
  END LOOP;
END $$;
```

---

## Pending Migration Plans

### Add AOI parent + Field Calibrations
**Reason:** Suportar divisão de macro-área em talhões e registrar calibrações de campo.  
**Migration:** `infra/migrations/sql/008_add_aoi_parent_and_field_calibrations.sql`  
**Rollback:**
```sql
ALTER TABLE aois DROP CONSTRAINT IF EXISTS aois_parent_aoi_fk;
ALTER TABLE aois DROP COLUMN IF EXISTS parent_aoi_id;
DROP TABLE IF EXISTS field_calibrations;
DROP INDEX IF EXISTS aois_parent_idx;
DROP INDEX IF EXISTS field_calibrations_aoi_time_idx;
DROP INDEX IF EXISTS field_calibrations_active_idx;
DROP INDEX IF EXISTS field_calibrations_version_idx;
```

### Add split_batches for idempotent splits
**Reason:** Evitar duplicação de AOIs em confirmações repetidas.  
**Migration:** `infra/migrations/sql/009_add_split_batches.sql`  
**Rollback:**
```sql
DROP TABLE IF EXISTS split_batches;
DROP INDEX IF EXISTS split_batches_parent_idx;
```

### Add field_feedback for paddock feedback
**Reason:** Registrar feedback de campo (issue/false positive) por talhão.  
**Migration:** `infra/migrations/sql/010_add_field_feedback.sql`  
**Rollback:**
```sql
DROP TABLE IF EXISTS field_feedback;
DROP INDEX IF EXISTS field_feedback_aoi_time_idx;
```

### Add local auth credentials to identities
**Reason:** Suportar login local (email/senha) e reset de senha.  
**Migration:** `infra/migrations/sql/011_add_identity_local_credentials.sql`  
**Rollback:**
```sql
ALTER TABLE identities
  DROP COLUMN IF EXISTS password_hash,
  DROP COLUMN IF EXISTS password_reset_token,
  DROP COLUMN IF EXISTS password_reset_expires_at;
DROP INDEX IF EXISTS identities_provider_email_idx;
```

### Add farm ownership (created_by_user_id)
**Reason:** Registrar ownership de fazendas para regras de EDITOR vs TENANT_ADMIN.  
**Migration:** `infra/migrations/sql/012_add_farm_created_by_user.sql`  
**Rollback:**
```sql
ALTER TABLE farms
  DROP COLUMN IF EXISTS created_by_user_id;
DROP INDEX IF EXISTS farms_created_by_user_idx;
```

### Add Composite Indexes for Tenant Queries
**Reason:** Improve p95 for tenant-scoped queries on jobs, AOIs, and signals.  
**Plan:** Create concurrent composite indexes.  
**Migration:** `infra/migrations/sql/006_add_tenant_query_indexes.sql`  
**Rollback:**
```sql
DROP INDEX CONCURRENTLY IF EXISTS idx_jobs_tenant_status_created;
DROP INDEX CONCURRENTLY IF EXISTS idx_aois_tenant_status;
DROP INDEX CONCURRENTLY IF EXISTS idx_opportunity_signals_tenant_week;
```

### Add STAC Scene Cache Table
**Reason:** Cache STAC scene metadata for provider fallback and resilience.  
**Migration:** `infra/migrations/sql/007_add_stac_scene_cache.sql`  
**Rollback:**
```sql
DROP TABLE IF EXISTS stac_scene_cache;
```

### Add Timestamps to `derived_weather_daily`
**Reason:** Worker upsert expects `updated_at`, but older tables may not have the column.  
**Plan:** Add columns if missing, with defaults.  
**SQL (to be applied via migration):**
```sql
ALTER TABLE derived_weather_daily
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now(),
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
```

---

## Last Updated
2026-02-06
