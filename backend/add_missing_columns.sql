-- Add missing columns to PostgreSQL users table
-- Run this in Railway console or PostgreSQL admin tool

-- Core required columns for registration and admin display
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_type TEXT DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_plan TEXT DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_active INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_started_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_used_permanently BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_warning_sent INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS decoder_used INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS fortune_used INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS horoscope_used INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS feature_preview_seen INTEGER DEFAULT 0;

-- Additional columns that might be missing
ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified INTEGER DEFAULT 1;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Run the legacy plan migration
UPDATE users SET user_plan = 'free' WHERE user_plan = 'foundation';
UPDATE users SET plan_type = 'free' WHERE plan_type = 'foundation';
UPDATE users SET user_plan = 'growth' WHERE user_plan = 'premium';
UPDATE users SET plan_type = 'growth' WHERE plan_type = 'premium';
UPDATE users SET user_plan = 'max' WHERE user_plan = 'enterprise';
UPDATE users SET plan_type = 'max' WHERE plan_type = 'enterprise';

-- Verify the changes
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;

-- Check user data
SELECT id, email, display_name, user_plan, plan_type, trial_active, created_at
FROM users 
ORDER BY created_at DESC;