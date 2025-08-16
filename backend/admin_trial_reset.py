#!/usr/bin/env python3
"""
Admin Trial Reset Tool
Properly resets trial state in both database and session
"""

import os
import psycopg2
import logging

logger = logging.getLogger(__name__)

def reset_user_trial(user_id: int):
    """
    Reset trial state for a specific user in database
    NOTE: Session cache will still need to be cleared by user logging out/in
    """
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("X No DATABASE_URL found")
            return False
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Check current state
        cur.execute("""
            SELECT trial_active, trial_used_permanently, trial_started_at, trial_expires_at
            FROM users WHERE id = %s
        """, (user_id,))
        
        result = cur.fetchone()
        if not result:
            print(f"X User {user_id} not found")
            conn.close()
            return False
        
        trial_active, trial_used, trial_started, trial_expires = result
        print(f"INFO: CURRENT STATE for user {user_id}:")
        print(f"   trial_active: {trial_active}")
        print(f"   trial_used_permanently: {trial_used}")
        print(f"   trial_started_at: {trial_started}")
        print(f"   trial_expires_at: {trial_expires}")
        
        # Reset all trial fields
        cur.execute("""
            UPDATE users
            SET
                trial_active           = 0,
                trial_started_at       = NULL,
                trial_used_permanently = FALSE,
                trial_companion        = NULL,
                trial_expires_at       = NULL,
                trial_warning_sent     = 0
            WHERE id = %s
        """, (user_id,))
        
        # Verify the reset
        cur.execute("""
            SELECT trial_active, trial_used_permanently, trial_started_at, trial_expires_at
            FROM users WHERE id = %s
        """, (user_id,))
        
        new_result = cur.fetchone()
        trial_active, trial_used, trial_started, trial_expires = new_result
        
        conn.commit()
        conn.close()
        
        print(f"OK RESET COMPLETE for user {user_id}:")
        print(f"   trial_active: {trial_active}")
        print(f"   trial_used_permanently: {trial_used}")
        print(f"   trial_started_at: {trial_started}")
        print(f"   trial_expires_at: {trial_expires}")
        
        print("\nWARNING:  IMPORTANT: User needs to log out and log back in to clear session cache!")
        return True
        
    except Exception as e:
        print(f"X Error resetting trial: {e}")
        return False

def reset_all_trials():
    """
    Reset ALL trial states (for testing)
    """
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("X No DATABASE_URL found")
            return False
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Count current active trials
        cur.execute("SELECT COUNT(*) FROM users WHERE trial_active = 1")
        active_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM users WHERE trial_used_permanently = TRUE")
        used_count = cur.fetchone()[0]
        
        print(f"INFO: BEFORE RESET:")
        print(f"   Active trials: {active_count}")
        print(f"   Used trials: {used_count}")
        
        # Reset all trials
        cur.execute("""
            UPDATE users
            SET
                trial_active           = 0,
                trial_started_at       = NULL,
                trial_used_permanently = FALSE,
                trial_companion        = NULL,
                trial_expires_at       = NULL,
                trial_warning_sent     = 0
        """)
        
        affected_rows = cur.rowcount
        conn.commit()
        conn.close()
        
        print(f"OK RESET {affected_rows} users")
        print("WARNING:  IMPORTANT: All users need to log out and log back in to clear session cache!")
        return True
        
    except Exception as e:
        print(f"X Error resetting all trials: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python admin_trial_reset.py 104        # Reset trial for user 104")
        print("  python admin_trial_reset.py all        # Reset ALL trials")
        sys.exit(1)
    
    if sys.argv[1] == "all":
        confirm = input("WARNING:  Reset ALL user trials? Type 'YES' to confirm: ")
        if confirm == "YES":
            reset_all_trials()
        else:
            print("X Cancelled")
    else:
        try:
            user_id = int(sys.argv[1])
            reset_user_trial(user_id)
        except ValueError:
            print("X Invalid user ID. Must be a number or 'all'")