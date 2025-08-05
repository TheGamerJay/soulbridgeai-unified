-- Add missing columns to PostgreSQL users table
-- Run this in Railway console or PostgreSQL admin tool

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

-- Verify the changes
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;