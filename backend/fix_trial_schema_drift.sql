-- ============================================================================
-- PostgreSQL Schema Migration: Fix Trial Column Types
-- ============================================================================
-- This migration fixes schema drift where trial columns are INTEGER instead of BOOLEAN
-- Run this ONCE in production PostgreSQL (Beekeeper Studio, psql, etc.)

-- 1) Check current column types
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name='users'
  AND column_name IN ('trial_active','trial_used_permanently','trial_warning_sent','trial_started_at','trial_expires_at');

-- 2) Normalize to proper types (boolean + timestamptz)
DO $migration$
BEGIN
  RAISE NOTICE 'Starting trial schema migration...';

  -- Convert trial_active from INTEGER to BOOLEAN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='users' AND column_name='trial_active' AND data_type <> 'boolean'
  ) THEN
    RAISE NOTICE 'Converting trial_active from % to boolean...', (
      SELECT data_type FROM information_schema.columns 
      WHERE table_name='users' AND column_name='trial_active'
    );
    ALTER TABLE users
      ALTER COLUMN trial_active TYPE boolean
      USING (CASE WHEN trial_active::text IN ('1','t','true','y','yes','on') THEN TRUE ELSE FALSE END),
      ALTER COLUMN trial_active SET DEFAULT FALSE,
      ALTER COLUMN trial_active SET NOT NULL;
    RAISE NOTICE 'trial_active converted to boolean';
  ELSE
    RAISE NOTICE 'trial_active already boolean - skipping';
  END IF;

  -- Convert trial_used_permanently from INTEGER to BOOLEAN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='users' AND column_name='trial_used_permanently' AND data_type <> 'boolean'
  ) THEN
    RAISE NOTICE 'Converting trial_used_permanently from % to boolean...', (
      SELECT data_type FROM information_schema.columns 
      WHERE table_name='users' AND column_name='trial_used_permanently'
    );
    ALTER TABLE users
      ALTER COLUMN trial_used_permanently TYPE boolean
      USING (CASE WHEN trial_used_permanently::text IN ('1','t','true','y','yes','on') THEN TRUE ELSE FALSE END),
      ALTER COLUMN trial_used_permanently SET DEFAULT FALSE,
      ALTER COLUMN trial_used_permanently SET NOT NULL;
    RAISE NOTICE 'trial_used_permanently converted to boolean';
  ELSE
    RAISE NOTICE 'trial_used_permanently already boolean - skipping';
  END IF;

  -- Convert trial_warning_sent from INTEGER to BOOLEAN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='users' AND column_name='trial_warning_sent' AND data_type <> 'boolean'
  ) THEN
    RAISE NOTICE 'Converting trial_warning_sent from % to boolean...', (
      SELECT data_type FROM information_schema.columns 
      WHERE table_name='users' AND column_name='trial_warning_sent'
    );
    ALTER TABLE users
      ALTER COLUMN trial_warning_sent TYPE boolean
      USING (CASE WHEN trial_warning_sent::text IN ('1','t','true','y','yes','on') THEN TRUE ELSE FALSE END),
      ALTER COLUMN trial_warning_sent SET DEFAULT FALSE,
      ALTER COLUMN trial_warning_sent SET NOT NULL;
    RAISE NOTICE 'trial_warning_sent converted to boolean';
  ELSE
    RAISE NOTICE 'trial_warning_sent already boolean - skipping';
  END IF;

  -- Convert trial_started_at to TIMESTAMPTZ (optional but good hygiene)
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='users' AND column_name='trial_started_at' 
    AND data_type NOT IN ('timestamp with time zone')
  ) THEN
    RAISE NOTICE 'Converting trial_started_at from % to timestamptz...', (
      SELECT data_type FROM information_schema.columns 
      WHERE table_name='users' AND column_name='trial_started_at'
    );
    ALTER TABLE users
      ALTER COLUMN trial_started_at TYPE timestamptz
      USING (CASE WHEN trial_started_at IS NULL THEN NULL ELSE (trial_started_at::timestamptz) END);
    RAISE NOTICE 'trial_started_at converted to timestamptz';
  ELSE
    RAISE NOTICE 'trial_started_at already timestamptz - skipping';
  END IF;

  -- Convert trial_expires_at to TIMESTAMPTZ
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='users' AND column_name='trial_expires_at' 
    AND data_type NOT IN ('timestamp with time zone')
  ) THEN
    RAISE NOTICE 'Converting trial_expires_at from % to timestamptz...', (
      SELECT data_type FROM information_schema.columns 
      WHERE table_name='users' AND column_name='trial_expires_at'
    );
    ALTER TABLE users
      ALTER COLUMN trial_expires_at TYPE timestamptz
      USING (CASE WHEN trial_expires_at IS NULL THEN NULL ELSE (trial_expires_at::timestamptz) END);
    RAISE NOTICE 'trial_expires_at converted to timestamptz';
  ELSE
    RAISE NOTICE 'trial_expires_at already timestamptz - skipping';
  END IF;

  RAISE NOTICE 'Trial schema migration completed successfully!';
END $migration$;

-- 3) Verify the migration worked
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name='users'
  AND column_name IN ('trial_active','trial_used_permanently','trial_warning_sent','trial_started_at','trial_expires_at')
ORDER BY column_name;

-- 4) Optional: Reset user 104's trial state (clean slate for testing)
-- UPDATE users
-- SET
--   trial_active           = FALSE,
--   trial_started_at       = NULL,
--   trial_expires_at       = NULL,
--   trial_warning_sent     = FALSE,
--   trial_used_permanently = FALSE
-- WHERE id = 104;

-- COMMIT; -- Uncomment if running in a transaction