-- Migrate legacy plan values to new system
-- Run this in Railway PostgreSQL console

UPDATE users 
SET user_plan = 'free' 
WHERE user_plan = 'foundation';

UPDATE users 
SET plan_type = 'free' 
WHERE plan_type = 'foundation';

UPDATE users 
SET user_plan = 'growth' 
WHERE user_plan = 'premium';

UPDATE users 
SET plan_type = 'growth' 
WHERE plan_type = 'premium';

UPDATE users 
SET user_plan = 'max' 
WHERE user_plan = 'enterprise';

UPDATE users 
SET plan_type = 'max' 
WHERE plan_type = 'enterprise';

-- Verify the changes
SELECT user_plan, plan_type, COUNT(*) as count
FROM users 
GROUP BY user_plan, plan_type;