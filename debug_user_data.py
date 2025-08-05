#!/usr/bin/env python3
"""
Debug script to examine user data and understand why free users show Growth limits
"""
import os
import sys

# Add backend to path so we can import from app.py
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app import get_feature_limit, is_trial_active
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv('backend/.env')
    
    def debug_user_data():
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("ERROR: No DATABASE_URL found")
            return
            
        print("DEBUG: Debugging User Data")
        print("=" * 50)
        
        try:
            conn = psycopg2.connect(database_url)
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
                LIMIT 10
            """)
            
            users = cursor.fetchall()
            
            print(f"FOUND: {len(users)} recent users:")
            print()
            
            for user in users:
                print(f"User: {user['username']} (ID: {user['id']})")
                print(f"   Created: {user['created_at']}")
                print(f"   Subscription: {user['subscription_tier']}")
                print(f"   Trial expires: {user['trial_expires_at']}")
                print(f"   Trial active (DB): {user['trial_active_db']}")
                
                # Test what the app functions would return
                trial_active = is_trial_active(user['id'])
                decoder_limit = get_feature_limit(user['subscription_tier'] or 'free', 'decoder', trial_active)
                fortune_limit = get_feature_limit(user['subscription_tier'] or 'free', 'fortune', trial_active)
                horoscope_limit = get_feature_limit(user['subscription_tier'] or 'free', 'horoscope', trial_active)
                
                print(f"   App trial check: {trial_active}")
                print(f"   Limits: {decoder_limit}/{fortune_limit}/{horoscope_limit}")
                print()
                
                # If this user has wrong limits, show the issue
                if user['subscription_tier'] == 'free' and decoder_limit != 3:
                    print(f"   ISSUE: Free user showing decoder limit {decoder_limit} instead of 3")
                if user['subscription_tier'] is None and decoder_limit != 3:
                    print(f"   ISSUE: NULL tier user showing decoder limit {decoder_limit} instead of 3")
                    
            cursor.close()
            conn.close()
                
        except Exception as e:
            print(f"ERROR: Database error: {e}")
            import traceback
            traceback.print_exc()
    
    if __name__ == "__main__":
        debug_user_data()
        
except ImportError as e:
    print(f"ERROR: Import error: {e}")
    print("TIP: Make sure you're running from the project root directory")