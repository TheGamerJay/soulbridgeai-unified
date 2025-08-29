#!/usr/bin/env python3
"""
Force cleanup of trial session data for aceelnene@gmail.com
"""
import sqlite3
import os

def force_cleanup_trial_data():
    """Force cleanup of trial data for aceelnene user"""
    try:
        # Connect to SQLite database
        db_path = "soulbridge.db"
        if not os.path.exists(db_path):
            print(f"ERROR: Database file {db_path} not found")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get aceelnene user info
        cursor.execute('SELECT id, email, user_plan, trial_active, trial_expires_at FROM users WHERE email = "aceelnene@gmail.com"')
        result = cursor.fetchone()
        
        if not result:
            print("ERROR: aceelnene@gmail.com user not found")
            conn.close()
            return False
            
        user_id, email, user_plan, trial_active, trial_expires = result
        print(f"CURRENT STATUS:")
        print(f"  User ID: {user_id}")
        print(f"  Email: {email}")
        print(f"  Plan: {user_plan}")
        print(f"  Trial Active: {trial_active}")
        print(f"  Trial Expires: {trial_expires}")
        
        # Force set trial_active = False for Bronze users
        if user_plan == 'bronze':
            print(f"FORCING: Setting trial_active=False for Bronze user {user_id}")
            
            cursor.execute("""
                UPDATE users 
                SET trial_active = 0, 
                    trial_used_permanently = 1,
                    trial_expires_at = NULL
                WHERE id = ?
            """, (user_id,))
            
            conn.commit()
            print(f"SUCCESS: Force updated database - trial_active=False")
            
            # Verify the change
            cursor.execute('SELECT user_plan, trial_active, trial_expires_at FROM users WHERE id = ?', (user_id,))
            new_result = cursor.fetchone()
            if new_result:
                new_plan, new_trial, new_expires = new_result
                print(f"VERIFIED: Plan={new_plan}, Trial={new_trial}, Expires={new_expires}")
            
        else:
            print(f"INFO: User has {user_plan} plan - not modifying trial settings")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== FORCE SESSION CLEANUP ===")
    success = force_cleanup_trial_data()
    if success:
        print("\nSUCCESS: Database updated! Please log out and log back in to clear session cache.")
        print("Then you should only see Bronze companions in the community section.")
    else:
        print("\nERROR: Failed to cleanup session data")