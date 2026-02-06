BEGIN;

-- Add error message to jobs for troubleshooting failed runs
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS error_message TEXT;

COMMIT;
