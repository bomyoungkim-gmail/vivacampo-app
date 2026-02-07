BEGIN;

ALTER TABLE farms
  ADD COLUMN IF NOT EXISTS created_by_user_id uuid NULL REFERENCES identities(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS farms_created_by_user_idx
  ON farms (tenant_id, created_by_user_id);

-- Backfill existing farms to tenant admin
UPDATE farms
SET created_by_user_id = (
    SELECT i.id
    FROM memberships m
    JOIN identities i ON i.id = m.identity_id
    WHERE m.tenant_id = farms.tenant_id
      AND m.role = 'TENANT_ADMIN'
      AND m.status = 'ACTIVE'
    ORDER BY m.created_at ASC
    LIMIT 1
)
WHERE created_by_user_id IS NULL;

COMMIT;
