-- Add trial system columns to users table
-- Run this in your PostgreSQL database

ALTER TABLE users
ADD COLUMN IF NOT EXISTS trial_started_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS trial_companion TEXT,
ADD COLUMN IF NOT EXISTS trial_used_permanently BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMP;

-- Create index for better performance on trial queries
CREATE INDEX IF NOT EXISTS idx_users_trial_started_at 
ON users(trial_started_at) 
WHERE trial_started_at IS NOT NULL;

-- Verify columns were added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name LIKE 'trial_%'
ORDER BY column_name;