-- Delete specific test user to allow re-registration
-- Run this in Railway PostgreSQL console if you want to test with the same email

DELETE FROM users WHERE email = 'thegamerjay11309@gmail.com';

-- Verify deletion
SELECT COUNT(*) as remaining_users FROM users WHERE email = 'thegamerjay11309@gmail.com';