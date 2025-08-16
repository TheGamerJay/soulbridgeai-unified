-- Reset trial for user 104
-- IMPORTANT: User needs to log out and log back in after this!

BEGIN;

-- Check current state first
SELECT 
    id, 
    trial_active, 
    trial_used_permanently, 
    trial_started_at, 
    trial_expires_at
FROM users 
WHERE id = 104;

-- Reset all trial fields (including trial_active which was missing from your query)
UPDATE users
SET
    trial_active           = 0,           -- This was the missing field!
    trial_started_at       = NULL,
    trial_used_permanently = FALSE,
    trial_companion        = NULL,
    trial_expires_at       = NULL,
    trial_warning_sent     = 0
WHERE id = 104;

-- Verify the reset
SELECT 
    id, 
    trial_active, 
    trial_used_permanently, 
    trial_started_at, 
    trial_expires_at
FROM users 
WHERE id = 104;

COMMIT;

-- IMPORTANT NOTES:
-- 1. The user needs to LOG OUT and LOG BACK IN to clear session cache
-- 2. trial_active = 0 was the critical missing field in your original query
-- 3. Session cache overrides database state until user re-authenticates