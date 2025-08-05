-- Debug script to check if user actually exists
-- Run this in Railway PostgreSQL console

-- Check if the user exists
SELECT * FROM users WHERE email = 'thegamerjay11309@gmail.com';

-- Check if there are any similar emails (case sensitivity issues)
SELECT * FROM users WHERE LOWER(email) LIKE '%thegamerjay11309%';

-- Check total user count
SELECT COUNT(*) as total_users FROM users;

-- Check recent users
SELECT id, email, created_at FROM users ORDER BY created_at DESC LIMIT 5;