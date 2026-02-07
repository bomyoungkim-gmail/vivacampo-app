-- Store idempotency for AOI split batches

CREATE TABLE IF NOT EXISTS split_batches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  parent_aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
  idempotency_key text NOT NULL,
  created_ids jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX CONCURRENTLY IF NOT EXISTS split_batches_parent_idx
  ON split_batches (tenant_id, parent_aoi_id, created_at DESC);
