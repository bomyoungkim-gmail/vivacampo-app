BEGIN;

-- Add local auth credentials to identities
ALTER TABLE identities
  ADD COLUMN IF NOT EXISTS password_hash text NULL,
  ADD COLUMN IF NOT EXISTS password_reset_token text NULL,
  ADD COLUMN IF NOT EXISTS password_reset_expires_at timestamptz NULL;

-- Optional index to speed up login lookups (provider + email)
CREATE INDEX IF NOT EXISTS identities_provider_email_idx ON identities (provider, email);

COMMIT;
