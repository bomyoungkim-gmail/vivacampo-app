-- Add field feedback for paddocks (manual issue/false positive)

CREATE TABLE IF NOT EXISTS field_feedback (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
  feedback_type text NOT NULL,
  message text NOT NULL,
  created_by_membership_id uuid NULL REFERENCES memberships(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX CONCURRENTLY IF NOT EXISTS field_feedback_aoi_time_idx
  ON field_feedback (tenant_id, aoi_id, created_at DESC);
