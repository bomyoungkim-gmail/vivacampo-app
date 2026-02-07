-- Add composite indexes for common tenant-scoped queries
-- Uses CONCURRENTLY to avoid long locks in production

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_tenant_status_created
    ON jobs (tenant_id, status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_aois_tenant_status
    ON aois (tenant_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_opportunity_signals_tenant_week
    ON opportunity_signals (tenant_id, year, week);
