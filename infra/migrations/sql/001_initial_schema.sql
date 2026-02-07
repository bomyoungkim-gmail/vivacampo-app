BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ===========
-- Identity / Tenancy
-- ===========
CREATE TABLE IF NOT EXISTS identities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,                -- cognito|google|microsoft|local
  subject text NOT NULL,                 -- sub do IdP
  email text NOT NULL,
  name text NOT NULL,
  status text NOT NULL DEFAULT 'ACTIVE',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (provider, subject),
  UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  type text NOT NULL DEFAULT 'COMPANY',  -- COMPANY|PERSONAL
  name text NOT NULL,
  status text NOT NULL DEFAULT 'ACTIVE', -- ACTIVE|SUSPENDED
  plan text NOT NULL DEFAULT 'BASIC',
  quotas jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS tenants_type_status_idx ON tenants (type, status);

CREATE TABLE IF NOT EXISTS memberships (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  identity_id uuid NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
  role text NOT NULL DEFAULT 'VIEWER',     -- TENANT_ADMIN|EDITOR|VIEWER
  status text NOT NULL DEFAULT 'ACTIVE',   -- ACTIVE|INVITED|SUSPENDED
  invited_by_membership_id uuid NULL REFERENCES memberships(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, identity_id)
);
CREATE INDEX IF NOT EXISTS memberships_tenant_role_idx ON memberships (tenant_id, role);
CREATE INDEX IF NOT EXISTS memberships_identity_idx ON memberships (identity_id);
CREATE INDEX IF NOT EXISTS idx_active_memberships ON memberships (tenant_id, identity_id, role) WHERE status = 'ACTIVE';

CREATE TABLE IF NOT EXISTS system_admins (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  identity_id uuid NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
  role text NOT NULL DEFAULT 'SYSTEM_ADMIN', -- SYSTEM_ADMIN|OPS|SUPPORT
  status text NOT NULL DEFAULT 'ACTIVE',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (identity_id)
);

-- Audit log (append-only)
CREATE TABLE IF NOT EXISTS audit_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NULL REFERENCES tenants(id) ON DELETE SET NULL,
  actor_type text NOT NULL, -- IDENTITY|MEMBERSHIP|SYSTEM_ADMIN|WORKER
  actor_id uuid NULL,
  action text NOT NULL,
  resource_type text NOT NULL,
  resource_id uuid NULL,
  diff_json jsonb NULL,
  metadata_json jsonb NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS audit_time_idx ON audit_log (created_at DESC);
CREATE INDEX IF NOT EXISTS audit_tenant_time_idx ON audit_log (tenant_id, created_at DESC);

-- Feature flags
CREATE TABLE IF NOT EXISTS feature_flags (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  key text NOT NULL UNIQUE,
  description text NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_feature_flags (
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  feature_flag_id uuid NOT NULL REFERENCES feature_flags(id) ON DELETE CASCADE,
  enabled boolean NOT NULL DEFAULT false,
  config_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_at timestamptz NOT NULL DEFAULT now(),
  updated_by_system_admin_id uuid NULL REFERENCES system_admins(id) ON DELETE SET NULL,
  PRIMARY KEY (tenant_id, feature_flag_id)
);

-- Tenant settings
CREATE TABLE IF NOT EXISTS tenant_settings (
  tenant_id uuid PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  max_cloud_cover int NOT NULL DEFAULT 60,
  min_valid_pixel_ratio double precision NOT NULL DEFAULT 0.15,
  alert_thresholds jsonb NOT NULL DEFAULT '{}'::jsonb,
  notifications jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_at timestamptz NOT NULL DEFAULT now(),
  updated_by_membership_id uuid NULL REFERENCES memberships(id) ON DELETE SET NULL
);

-- ===========
-- Domain
-- ===========
CREATE TABLE IF NOT EXISTS farms (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name text NOT NULL,
  timezone text NOT NULL DEFAULT 'America/Sao_Paulo',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS farms_tenant_idx ON farms (tenant_id);

CREATE TABLE IF NOT EXISTS aois (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  farm_id uuid NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  name text NOT NULL,
  use_type text NOT NULL, -- PASTURE|CROP
  status text NOT NULL DEFAULT 'ACTIVE',
  geom geometry(MultiPolygon, 4326) NOT NULL,
  area_ha double precision NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS aois_geom_gist ON aois USING GIST (geom);
CREATE INDEX IF NOT EXISTS aois_tenant_farm_idx ON aois (tenant_id, farm_id, status);

CREATE TABLE IF NOT EXISTS aoi_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
  geom geometry(MultiPolygon, 4326) NOT NULL,
  area_ha double precision NOT NULL,
  effective_date date NOT NULL DEFAULT CURRENT_DATE,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS aoi_versions_aoi_time_idx ON aoi_versions (tenant_id, aoi_id, created_at DESC);

-- ===========
-- Jobs
-- ===========
CREATE TABLE IF NOT EXISTS jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  aoi_id uuid NULL REFERENCES aois(id) ON DELETE SET NULL,
  job_type text NOT NULL, -- PROCESS_WEEK|ALERTS_WEEK|SIGNALS_WEEK|FORECAST_WEEK|BACKFILL
  job_key text NOT NULL,
  status text NOT NULL DEFAULT 'PENDING',
  payload_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, job_key)
);
CREATE INDEX IF NOT EXISTS jobs_filter_idx ON jobs (tenant_id, status, job_type, created_at DESC);
CREATE INDEX IF NOT EXISTS jobs_aoi_time_idx ON jobs (tenant_id, aoi_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status_type_created ON jobs (status, job_type, created_at) WHERE status IN ('PENDING', 'RUNNING');

CREATE TABLE IF NOT EXISTS job_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  job_id uuid NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  attempt int NOT NULL,
  status text NOT NULL,
  metrics_json jsonb NULL,
  error_json jsonb NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz NULL
);
CREATE INDEX IF NOT EXISTS job_runs_job_idx ON job_runs (tenant_id, job_id, attempt DESC);

-- ===========
-- Observations / Assets
-- ===========
CREATE TABLE IF NOT EXISTS observations_weekly (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
  year int NOT NULL,
  week int NOT NULL,
  pipeline_version text NOT NULL,
  status text NOT NULL, -- OK|NO_DATA
  valid_pixel_ratio double precision NOT NULL,
  ndvi_mean double precision NULL,
  ndvi_p10 double precision NULL,
  ndvi_p50 double precision NULL,
  ndvi_p90 double precision NULL,
  ndvi_std double precision NULL,
  baseline double precision NULL,
  anomaly double precision NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, aoi_id, year, week, pipeline_version)
);
CREATE INDEX IF NOT EXISTS obs_aoi_time_idx ON observations_weekly (tenant_id, aoi_id, year, week);
CREATE INDEX IF NOT EXISTS idx_obs_tenant_aoi_year_week ON observations_weekly (tenant_id, aoi_id, year DESC, week DESC);

CREATE TABLE IF NOT EXISTS derived_assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
  year int NOT NULL,
  week int NOT NULL,
  pipeline_version text NOT NULL,
  ndvi_s3_uri text NULL,
  anomaly_s3_uri text NULL,
  quicklook_s3_uri text NULL,
  ndwi_s3_uri text NULL,
  ndmi_s3_uri text NULL,
  savi_s3_uri text NULL,
  false_color_s3_uri text NULL,
  stac_item_id text NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, aoi_id, year, week, pipeline_version)
);
CREATE INDEX IF NOT EXISTS assets_aoi_time_idx ON derived_assets (tenant_id, aoi_id, year, week);

-- ===========
-- Alerts
-- ===========
CREATE TABLE IF NOT EXISTS alerts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
  alert_type text NOT NULL,
  status text NOT NULL DEFAULT 'OPEN',
  severity text NOT NULL,
  confidence text NOT NULL,
  evidence_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS alerts_filter_idx ON alerts (tenant_id, status, alert_type, created_at DESC);

-- ===========
-- Yield
-- ===========
CREATE TABLE IF NOT EXISTS seasons (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
  season_year int NOT NULL,
  start_date date NOT NULL,
  end_date date NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, aoi_id, season_year)
);

CREATE TABLE IF NOT EXISTS yield_forecasts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
  season_year int NOT NULL,
  model_version text NOT NULL,
  pipeline_version text NOT NULL,
  index_p10 double precision NOT NULL,
  index_p50 double precision NOT NULL,
  index_p90 double precision NOT NULL,
  confidence text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS yield_aoi_time_idx ON yield_forecasts (tenant_id, aoi_id, season_year, created_at DESC);

-- ===========
-- Outbox / webhooks
-- ===========
CREATE TABLE IF NOT EXISTS tenant_webhooks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  url text NOT NULL,
  secret text NULL,
  events jsonb NOT NULL DEFAULT '[]'::jsonb,
  enabled boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_event_outbox (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  event_type text NOT NULL,
  payload jsonb NOT NULL,
  status text NOT NULL DEFAULT 'PENDING',
  attempts int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  next_retry_at timestamptz NULL
);
CREATE INDEX IF NOT EXISTS outbox_pending_idx ON tenant_event_outbox (tenant_id, status, created_at DESC);

-- ===========
-- Opportunity Signals + Feedback
-- ===========
CREATE TABLE IF NOT EXISTS opportunity_signals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
  year int NOT NULL,
  week int NOT NULL,
  pipeline_version text NOT NULL,
  signal_type text NOT NULL,
  status text NOT NULL DEFAULT 'OPEN', -- OPEN|ACK|RESOLVED|DISMISSED
  severity text NOT NULL,
  confidence text NOT NULL,
  score double precision NOT NULL,
  model_version text NOT NULL,
  change_method text NOT NULL,
  evidence_json jsonb NOT NULL,
  features_json jsonb NOT NULL,
  recommended_actions jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, aoi_id, year, week, pipeline_version, signal_type)
);
CREATE INDEX IF NOT EXISTS signals_filter_idx ON opportunity_signals (tenant_id, status, signal_type, created_at DESC);
CREATE INDEX IF NOT EXISTS signals_aoi_time_idx ON opportunity_signals (tenant_id, aoi_id, year, week);
CREATE INDEX IF NOT EXISTS idx_signals_tenant_status_type_created ON opportunity_signals (tenant_id, status, signal_type, created_at DESC);

CREATE TABLE IF NOT EXISTS signal_feedback (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  signal_id uuid NOT NULL REFERENCES opportunity_signals(id) ON DELETE CASCADE,
  membership_id uuid NULL REFERENCES memberships(id) ON DELETE SET NULL,
  label text NOT NULL,
  root_cause text NULL,
  note text NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS signal_feedback_idx ON signal_feedback (tenant_id, signal_id, created_at DESC);

-- ===========
-- Copilot (LangGraph/HIL) state + approvals
-- ===========
CREATE TABLE IF NOT EXISTS copilot_threads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  aoi_id uuid NULL REFERENCES aois(id) ON DELETE SET NULL,
  signal_id uuid NULL REFERENCES opportunity_signals(id) ON DELETE SET NULL,
  created_by_membership_id uuid NULL REFERENCES memberships(id) ON DELETE SET NULL,
  status text NOT NULL DEFAULT 'OPEN', -- OPEN|WAITING_HUMAN|CLOSED
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS copilot_threads_idx ON copilot_threads (tenant_id, created_at DESC);

-- Checkpoints/persisted state (simplificado para MVP)
CREATE TABLE IF NOT EXISTS copilot_checkpoints (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  thread_id uuid NOT NULL REFERENCES copilot_threads(id) ON DELETE CASCADE,
  step int NOT NULL,
  state_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, thread_id, step)
);
CREATE INDEX IF NOT EXISTS copilot_ckpt_thread_idx ON copilot_checkpoints (tenant_id, thread_id, step DESC);

-- Aprovações (HIL)
CREATE TABLE IF NOT EXISTS copilot_approvals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  thread_id uuid NOT NULL REFERENCES copilot_threads(id) ON DELETE CASCADE,
  requested_by_system boolean NOT NULL DEFAULT true,
  tool_name text NOT NULL,             -- ex: create_notification, trigger_webhook
  tool_payload jsonb NOT NULL,
  decision text NOT NULL DEFAULT 'PENDING', -- PENDING|APPROVED|REJECTED
  decided_by_membership_id uuid NULL REFERENCES memberships(id) ON DELETE SET NULL,
  decision_note text NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  decided_at timestamptz NULL
);
CREATE INDEX IF NOT EXISTS copilot_approvals_idx ON copilot_approvals (tenant_id, decision, created_at DESC);

COMMIT;
