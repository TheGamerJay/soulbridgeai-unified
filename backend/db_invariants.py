# backend/db_invariants.py
import logging

def enforce_trial_schema(conn):
    """Harden trial columns: real booleans + correct defaults; timestamps = timestamptz."""
    with conn.cursor() as cur:
        cur.execute("""
        -- Add if missing
        ALTER TABLE users
          ADD COLUMN IF NOT EXISTS trial_active            boolean,
          ADD COLUMN IF NOT EXISTS trial_used_permanently  boolean,
          ADD COLUMN IF NOT EXISTS trial_warning_sent      boolean,
          ADD COLUMN IF NOT EXISTS trial_started_at        timestamptz,
          ADD COLUMN IF NOT EXISTS trial_expires_at        timestamptz;
        """)
        # Drop legacy defaults first to avoid cast errors
        cur.execute("""
        ALTER TABLE users
          ALTER COLUMN trial_active DROP DEFAULT,
          ALTER COLUMN trial_used_permanently DROP DEFAULT,
          ALTER COLUMN trial_warning_sent DROP DEFAULT;
        """)
        # Force correct types
        cur.execute("""
        ALTER TABLE users
          ALTER COLUMN trial_active TYPE boolean
            USING ( (trial_active)::text IN ('1','t','true','y','yes','on') ),
          ALTER COLUMN trial_used_permanently TYPE boolean
            USING ( (trial_used_permanently)::text IN ('1','t','true','y','yes','on') ),
          ALTER COLUMN trial_warning_sent TYPE boolean
            USING ( (trial_warning_sent)::text IN ('1','t','true','y','yes','on') );
        """)
        # Defaults + NOT NULL
        cur.execute("""
        ALTER TABLE users
          ALTER COLUMN trial_active           SET DEFAULT FALSE,
          ALTER COLUMN trial_used_permanently SET DEFAULT FALSE,
          ALTER COLUMN trial_warning_sent     SET DEFAULT FALSE,
          ALTER COLUMN trial_active           SET NOT NULL,
          ALTER COLUMN trial_used_permanently SET NOT NULL,
          ALTER COLUMN trial_warning_sent     SET NOT NULL;
        """)
        # Timestamps normalization (no-op if already tz)
        cur.execute("""
        ALTER TABLE users
          ALTER COLUMN trial_started_at TYPE timestamptz
            USING (CASE WHEN trial_started_at IS NULL THEN NULL ELSE trial_started_at::timestamptz END),
          ALTER COLUMN trial_expires_at TYPE timestamptz
            USING (CASE WHEN trial_expires_at IS NULL THEN NULL ELSE trial_expires_at::timestamptz END);
        """)
    conn.commit()
    logging.info("✅ Trial schema invariants enforced")