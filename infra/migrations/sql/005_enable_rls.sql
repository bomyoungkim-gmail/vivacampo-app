BEGIN;

-- Enable RLS for tenant-scoped tables only.
-- NOTE: identities/tenants/memberships/system_admins are intentionally excluded
-- because auth flows need to enumerate memberships without a tenant context.

DO $$
DECLARE
  t text;
  tenant_tables text[] := ARRAY[
    'farms',
    'aois',
    'aoi_versions',
    'jobs',
    'job_runs',
    'observations_weekly',
    'derived_assets',
    'alerts',
    'seasons',
    'yield_forecasts',
    'tenant_webhooks',
    'tenant_event_outbox',
    'opportunity_signals',
    'signal_feedback',
    'copilot_threads',
    'copilot_checkpoints',
    'copilot_approvals',
    'derived_radar_assets',
    'derived_weather_daily',
    'derived_topography'
  ];
BEGIN
  FOREACH t IN ARRAY tenant_tables LOOP
    IF to_regclass(t) IS NOT NULL THEN
      EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
      EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);

      BEGIN
        EXECUTE format(
          'CREATE POLICY tenant_isolation ON %I USING (tenant_id = NULLIF(current_setting(''app.tenant_id'', true), '''')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting(''app.tenant_id'', true), '''')::uuid)',
          t
        );
      EXCEPTION
        WHEN duplicate_object THEN
          NULL;
      END;

      BEGIN
        EXECUTE format(
          'CREATE POLICY system_admin_bypass ON %I USING (current_setting(''app.is_system_admin'', true) = ''true'') WITH CHECK (current_setting(''app.is_system_admin'', true) = ''true'')',
          t
        );
      EXCEPTION
        WHEN duplicate_object THEN
          NULL;
      END;
    END IF;
  END LOOP;
END $$;

COMMIT;
