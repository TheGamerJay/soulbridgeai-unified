-- =====================================================================================
-- SoulBridge AI: Hybrid Referrals Table Migration
-- =====================================================================================
-- This script implements a hybrid approach for the referrals table:
-- ✅ Keeps referrer_id / referred_id (FKs to users.id) for proper relational integrity  
-- ✅ Adds referrer_email / referred_email for app compatibility & legacy queries
-- ✅ Syncs both via trigger for data consistency
-- ✅ Indexes both IDs and emails for performance
-- =====================================================================================

BEGIN;

-- Step 1: Add email columns if missing
-- -------------------------------------
DO $$
BEGIN
    -- Add referrer_email column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='referrals' AND column_name='referrer_email') THEN
        ALTER TABLE referrals ADD COLUMN referrer_email VARCHAR(255);
        RAISE NOTICE '✅ Added referrer_email column to referrals table';
    ELSE
        RAISE NOTICE '📋 referrer_email column already exists in referrals table';
    END IF;
    
    -- Add referred_email column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='referrals' AND column_name='referred_email') THEN
        ALTER TABLE referrals ADD COLUMN referred_email VARCHAR(255);
        RAISE NOTICE '✅ Added referred_email column to referrals table';
    ELSE
        RAISE NOTICE '📋 referred_email column already exists in referrals table';
    END IF;
END $$;

-- Step 2: Backfill emails from users based on existing IDs
-- ---------------------------------------------------------
DO $$
DECLARE
    referrer_updates INTEGER;
    referred_updates INTEGER;
BEGIN
    -- Backfill referrer emails
    UPDATE referrals r
    SET referrer_email = u.email
    FROM users u
    WHERE r.referrer_id = u.id AND r.referrer_email IS NULL;
    
    GET DIAGNOSTICS referrer_updates = ROW_COUNT;
    RAISE NOTICE '✅ Backfilled % referrer_email values from users table', referrer_updates;
    
    -- Backfill referred emails
    UPDATE referrals r
    SET referred_email = u.email
    FROM users u
    WHERE r.referred_id = u.id AND r.referred_email IS NULL;
    
    GET DIAGNOSTICS referred_updates = ROW_COUNT;
    RAISE NOTICE '✅ Backfilled % referred_email values from users table', referred_updates;
END $$;

-- Step 3: Backfill IDs from emails (if any emails exist without matching IDs)
-- ---------------------------------------------------------------------------
DO $$
DECLARE
    referrer_id_updates INTEGER;
    referred_id_updates INTEGER;
BEGIN
    -- Backfill referrer IDs from emails
    UPDATE referrals r
    SET referrer_id = u.id
    FROM users u
    WHERE r.referrer_id IS NULL 
      AND r.referrer_email IS NOT NULL
      AND lower(r.referrer_email) = lower(u.email);
    
    GET DIAGNOSTICS referrer_id_updates = ROW_COUNT;
    RAISE NOTICE '✅ Backfilled % referrer_id values from emails', referrer_id_updates;
    
    -- Backfill referred IDs from emails
    UPDATE referrals r
    SET referred_id = u.id
    FROM users u
    WHERE r.referred_id IS NULL 
      AND r.referred_email IS NOT NULL
      AND lower(r.referred_email) = lower(u.email);
    
    GET DIAGNOSTICS referred_id_updates = ROW_COUNT;
    RAISE NOTICE '✅ Backfilled % referred_id values from emails', referred_id_updates;
END $$;

-- Step 4: Create performance indexes (using IF NOT EXISTS for safety)
-- -------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id     ON referrals (referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred_id     ON referrals (referred_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_email  ON referrals (lower(referrer_email));
CREATE INDEX IF NOT EXISTS idx_referrals_referred_email  ON referrals (lower(referred_email));
CREATE INDEX IF NOT EXISTS idx_referrals_status          ON referrals (status);
CREATE INDEX IF NOT EXISTS idx_referrals_code            ON referrals (referral_code);

-- Step 5: Create trigger function to keep emails and IDs in sync
-- --------------------------------------------------------------
CREATE OR REPLACE FUNCTION sync_referral_emails() RETURNS trigger AS $$
BEGIN
    -- If referrer_id is set/changed, update the corresponding email
    IF NEW.referrer_id IS NOT NULL AND (OLD.referrer_id IS DISTINCT FROM NEW.referrer_id) THEN
        SELECT email INTO NEW.referrer_email FROM users WHERE id = NEW.referrer_id;
        
        -- If user not found, keep existing email (defensive programming)
        IF NEW.referrer_email IS NULL AND OLD.referrer_email IS NOT NULL THEN
            NEW.referrer_email := OLD.referrer_email;
        END IF;
    END IF;
    
    -- If referred_id is set/changed, update the corresponding email
    IF NEW.referred_id IS NOT NULL AND (OLD.referred_id IS DISTINCT FROM NEW.referred_id) THEN
        SELECT email INTO NEW.referred_email FROM users WHERE id = NEW.referred_id;
        
        -- If user not found, keep existing email (defensive programming)  
        IF NEW.referred_email IS NULL AND OLD.referred_email IS NOT NULL THEN
            NEW.referred_email := OLD.referred_email;
        END IF;
    END IF;
    
    RETURN NEW;
END $$ LANGUAGE plpgsql;

-- Step 6: Create the trigger (drop first to avoid conflicts)
-- ----------------------------------------------------------
DROP TRIGGER IF EXISTS trg_sync_referral_emails ON referrals;
CREATE TRIGGER trg_sync_referral_emails
    BEFORE INSERT OR UPDATE ON referrals
    FOR EACH ROW
    EXECUTE PROCEDURE sync_referral_emails();

-- Step 7: Validation queries to verify migration success
-- ------------------------------------------------------
DO $$
DECLARE
    total_rows INTEGER;
    rows_with_both_ids INTEGER;
    rows_with_both_emails INTEGER;
    rows_with_orphaned_emails INTEGER;
    rows_with_orphaned_ids INTEGER;
BEGIN
    -- Count total referrals
    SELECT COUNT(*) INTO total_rows FROM referrals;
    
    -- Count rows with both ID fields populated
    SELECT COUNT(*) INTO rows_with_both_ids 
    FROM referrals 
    WHERE referrer_id IS NOT NULL AND referred_id IS NOT NULL;
    
    -- Count rows with both email fields populated
    SELECT COUNT(*) INTO rows_with_both_emails 
    FROM referrals 
    WHERE referrer_email IS NOT NULL AND referred_email IS NOT NULL;
    
    -- Count orphaned emails (emails without corresponding IDs)
    SELECT COUNT(*) INTO rows_with_orphaned_emails 
    FROM referrals r 
    WHERE (r.referrer_email IS NOT NULL AND r.referrer_id IS NULL) 
       OR (r.referred_email IS NOT NULL AND r.referred_id IS NULL);
    
    -- Count orphaned IDs (IDs without corresponding emails)
    SELECT COUNT(*) INTO rows_with_orphaned_ids 
    FROM referrals r 
    WHERE (r.referrer_id IS NOT NULL AND r.referrer_email IS NULL) 
       OR (r.referred_id IS NOT NULL AND r.referred_email IS NULL);
    
    -- Report results
    RAISE NOTICE '';
    RAISE NOTICE '🔍 MIGRATION VALIDATION RESULTS:';
    RAISE NOTICE '================================';
    RAISE NOTICE '📊 Total referral records: %', total_rows;
    RAISE NOTICE '✅ Records with both ID fields: % (%% of total)', rows_with_both_ids, 
                 CASE WHEN total_rows > 0 THEN ROUND((rows_with_both_ids * 100.0 / total_rows), 1) ELSE 0 END;
    RAISE NOTICE '✅ Records with both email fields: % (%% of total)', rows_with_both_emails,
                 CASE WHEN total_rows > 0 THEN ROUND((rows_with_both_emails * 100.0 / total_rows), 1) ELSE 0 END;
    RAISE NOTICE '⚠️  Orphaned emails (no matching IDs): %', rows_with_orphaned_emails;
    RAISE NOTICE '⚠️  Orphaned IDs (no matching emails): %', rows_with_orphaned_ids;
    
    IF rows_with_orphaned_emails > 0 OR rows_with_orphaned_ids > 0 THEN
        RAISE NOTICE '🚨 WARNING: Some data inconsistencies found. Manual review recommended.';
    ELSE
        RAISE NOTICE '🎉 SUCCESS: All referral data is consistent between IDs and emails!';
    END IF;
    
    RAISE NOTICE '';
END $$;

COMMIT;

-- =====================================================================================
-- USAGE EXAMPLES AFTER MIGRATION
-- =====================================================================================

-- Legacy email-based queries (app.py current code works as-is):
/*
SELECT referred_email, created_at, status
FROM referrals
WHERE referrer_email = 'user@example.com';
*/

-- Future-proof ID-based queries (better performance & referential integrity):
/*
SELECT u2.email AS referred_email, r.created_at, r.status
FROM referrals r
JOIN users u1 ON u1.id = r.referrer_id
JOIN users u2 ON u2.id = r.referred_id
WHERE u1.email = 'user@example.com';
*/

-- Mixed approach (use IDs when available, fallback to emails):
/*
SELECT COALESCE(u2.email, r.referred_email) AS referred_email, 
       r.created_at, r.status
FROM referrals r
LEFT JOIN users u2 ON u2.id = r.referred_id
WHERE r.referrer_id = 123 OR r.referrer_email = 'user@example.com';
*/