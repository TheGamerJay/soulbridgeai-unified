-- ============================================================================
-- PRODUCTION TRIAL SCHEMA MIGRATION (Idempotent - Safe to Re-run)
-- ============================================================================
-- This permanently fixes trial column schema drift with belt-and-suspenders approach
-- Run ONCE in PostgreSQL production (Beekeeper Studio, psql, etc.)

BEGIN;

-- Ensure columns exist (no-op if present)
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS trial_active            boolean,
  ADD COLUMN IF NOT EXISTS trial_used_permanently  boolean,
  ADD COLUMN IF NOT EXISTS trial_warning_sent      boolean,
  ADD COLUMN IF NOT EXISTS trial_started_at        timestamptz,
  ADD COLUMN IF NOT EXISTS trial_expires_at        timestamptz;

-- Convert flags to proper boolean (drop legacy int defaults first)
ALTER TABLE users
  ALTER COLUMN trial_active DROP DEFAULT,
  ALTER COLUMN trial_used_permanently DROP DEFAULT,
  ALTER COLUMN trial_warning_sent DROP DEFAULT;

ALTER TABLE users
  ALTER COLUMN trial_active TYPE boolean
    USING ( (trial_active)::text IN ('1','t','true','y','yes','on') ),
  ALTER COLUMN trial_used_permanently TYPE boolean
    USING ( (trial_used_permanently)::text IN ('1','t','true','y','yes','on') ),
  ALTER COLUMN trial_warning_sent TYPE boolean
    USING ( (trial_warning_sent)::text IN ('1','t','true','y','yes','on') );

-- Set correct defaults + NOT NULL
ALTER TABLE users
  ALTER COLUMN trial_active           SET DEFAULT FALSE,
  ALTER COLUMN trial_used_permanently SET DEFAULT FALSE,
  ALTER COLUMN trial_warning_sent     SET DEFAULT FALSE,
  ALTER COLUMN trial_active           SET NOT NULL,
  ALTER COLUMN trial_used_permanently SET NOT NULL,
  ALTER COLUMN trial_warning_sent     SET NOT NULL;

-- Normalize timestamps (keeps NULLs)
ALTER TABLE users
  ALTER COLUMN trial_started_at TYPE timestamptz
    USING (CASE WHEN trial_started_at IS NULL THEN NULL ELSE trial_started_at::timestamptz END),
  ALTER COLUMN trial_expires_at TYPE timestamptz
    USING (CASE WHEN trial_expires_at IS NULL THEN NULL ELSE trial_expires_at::timestamptz END);

COMMIT;

-- Sanity check - verify the migration worked
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name='users'
  AND column_name IN ('trial_active','trial_used_permanently','trial_warning_sent',
                      'trial_started_at','trial_expires_at')
ORDER BY column_name;

-- Optional: Reset user 104's trial state (clean slate for testing)
-- UPDATE users
-- SET
--   trial_active = FALSE,
--   trial_started_at = NULL,
--   trial_expires_at = NULL,
--   trial_warning_sent = FALSE,
--   trial_used_permanently = FALSE
-- WHERE id = 104;