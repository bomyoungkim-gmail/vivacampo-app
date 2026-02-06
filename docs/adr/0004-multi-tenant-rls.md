# ADR-0004 — Multi-Tenant Architecture with Row-Level Security

Date: 2025-12-10
Status: Accepted
Owners: Backend Team

## Context
VivaCampo is a SaaS platform serving multiple customers (tenants). Each tenant should:
- Have isolated data (cannot access other tenants' farms/AOIs)
- Have separate quotas (max AOIs, max backfill weeks)
- Have different plans (BASIC, PRO, ENTERPRISE)
- Share the same infrastructure (cost efficiency)

**Multi-tenancy approaches:**
1. Database per tenant (separate PostgreSQL database for each)
2. Schema per tenant (separate schema within same database)
3. Row-level security (shared tables, filtered by `tenant_id`)

## Decision
**Adopt row-level security (RLS) with `tenant_id` column** in all domain tables.

## Options considered

### 1) Database per tenant
**Pros:**
- Strongest isolation (physical separation)
- Easy to backup/restore individual tenants
- Can scale individual tenants independently

**Cons:**
- High infrastructure overhead (N databases for N tenants)
- Complex connection pooling
- Difficult to run cross-tenant analytics
- Migration complexity (must run on all databases)

### 2) Schema per tenant
**Pros:**
- Good isolation (logical separation)
- Single database connection pool

**Cons:**
- PostgreSQL has limits on number of schemas
- Complex query routing (must set `search_path` per request)
- Migration complexity (must run on all schemas)

### 3) Row-level security (RLS) ✅
**Pros:**
- Simple architecture (single database, single schema)
- Easy to implement (just add `tenant_id` column + WHERE clause)
- Efficient connection pooling
- Easy cross-tenant analytics (for admin)
- Simple migrations (single schema)

**Cons:**
- Risk of data leakage if query forgets `tenant_id` filter
- All tenants share same database resources (noisy neighbor problem)

## Consequences
**What changes:**
- All domain tables have `tenant_id UUID NOT NULL` column
- All queries MUST filter by `tenant_id` (enforced via middleware)
- Foreign keys include `tenant_id` for referential integrity
- Composite indices on `(tenant_id, ...)` for performance

**Implementation:**
```sql
-- Example: AOIs table
CREATE TABLE aois (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  farm_id UUID NOT NULL,
  name TEXT NOT NULL,
  geom GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
  -- ...
  FOREIGN KEY (tenant_id, farm_id) REFERENCES farms(tenant_id, id) ON DELETE CASCADE
);

CREATE INDEX aois_tenant_farm_idx ON aois(tenant_id, farm_id);
```

**Enforcement:**
- Middleware extracts `tenant_id` from JWT token
- All ORM queries automatically filter by `tenant_id`
- Raw SQL queries use parameterized `tenant_id`

**Trade-offs accepted:**
- Potential data leakage risk - **mitigated by:**
  - Code review checklist (all queries must filter by `tenant_id`)
  - Integration tests verify isolation
  - Linter rule to detect missing `tenant_id` filters (future)
- Noisy neighbor problem - **mitigated by:**
  - Quotas per tenant (max AOIs, max jobs)
  - Rate limiting per tenant
  - Can migrate to database-per-tenant later if needed

**Benefits:**
- Simple to implement and maintain
- Cost-efficient (shared infrastructure)
- Fast queries (composite indices on `tenant_id`)
- Easy to add new tenants (just insert row in `tenants` table)

## Follow-ups
- [x] Add `tenant_id` to all domain tables
- [x] Add composite indices on `(tenant_id, ...)`
- [x] Implement middleware to extract `tenant_id` from JWT
- [x] Add integration tests for tenant isolation
- [ ] Add linter rule to detect missing `tenant_id` filters (TASK-0250)
- [ ] Document multi-tenant patterns in `ai/contracts.md` ✅
