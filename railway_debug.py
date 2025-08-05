#!/usr/bin/env python3
"""
Railway debug script to check user data and fix free user limits
Run this on Railway to access the production database
"""
import os
import sys

# Check if we're in Railway environment
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    print("ERROR: This script must run in Railway environment")
    print("Deploy this to Railway and run it there")
    sys.exit(1)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: psycopg2 not available")
    sys.exit(1)

def debug_and_fix_users():
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("ERROR: No DATABASE_URL found")
        return False
        
    print("DEBUG: Checking user data and limits")
    print("=" * 50)
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all users with their subscription and trial data
        cursor.execute("""
            SELECT 
                u.id, u.username, u.subscription_tier,
                u.trial_expires_at, u.created_at,
                CASE 
                    WHEN u.trial_expires_at > NOW() THEN true 
                    ELSE false 
                END as trial_active_db
            FROM users u 
            ORDER BY u.created_at DESC 
            LIMIT 20
        """)
        
        users = cursor.fetchall()
        
        print(f"FOUND: {len(users)} recent users")
        print()
        
        free_users_fixed = 0
        
        for user in users:
            print(f"User: {user['username']} (ID: {user['id']})")
            print(f"   Created: {user['created_at']}")
            print(f"   Subscription: {user['subscription_tier']}")
            print(f"   Trial expires: {user['trial_expires_at']}")
            print(f"   Trial active (DB): {user['trial_active_db']}")
            
            # Check if this user should be free but isn't
            tier = user['subscription_tier']
            trial_active = user['trial_active_db']
            
            # Fix users that should be free
            if tier is None or tier == '' or (tier in ['foundation', 'free'] and not trial_active):
                print(f"   ACTION: Setting user to truly free tier")
                
                # Clear trial data and set to free
                cursor.execute("""
                    UPDATE users 
                    SET subscription_tier = 'free', 
                        trial_expires_at = NULL
                    WHERE id = %s
                """, (user['id'],))
                
                free_users_fixed += 1
                print(f"   FIXED: User now set to free tier")
            
            print()
                
        cursor.close()
        conn.close()
        
        print(f"SUMMARY: Fixed {free_users_fixed} users to be truly free")
        return True
            
    except Exception as e:
        print(f"ERROR: Database error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Railway User Data Debug & Fix Tool")
    print("=" * 40)
    
    success = debug_and_fix_users()
    
    if success:
        print("DEBUG completed successfully!")
        print("Now test your free users to see if they show correct limits (3/2/3)")
    else:
        print("DEBUG failed - check errors above")