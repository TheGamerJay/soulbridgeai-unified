#!/usr/bin/env python3
"""
Clear trial session data for Bronze users without active trial
"""
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_utils import get_database
from datetime import datetime, timezone

def clear_trial_session_data(user_id=104):
    """Clear any stale trial session data in the database"""
    try:
        # Try SQLite database first
        import sqlite3
        db_path = "soulbridge.db"
        if not os.path.exists(db_path):
            print(f"ERROR: Database file {db_path} not found")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current user status
        cursor.execute("SELECT user_plan, trial_active, trial_expires_at FROM users WHERE id = ?", (user_id,))
        
        result = cursor.fetchone()
        if not result:
            print(f"ERROR: User {user_id} not found")
            conn.close()
            return False
            
        user_plan, trial_active, trial_expires = result
        print(f"CURRENT STATUS:")
        print(f"   User ID: {user_id}")
        print(f"   Plan: {user_plan}")
        print(f"   Trial Active: {trial_active}")
        print(f"   Trial Expires: {trial_expires}")
        
        # Check if trial should be expired
        should_expire_trial = False
        if trial_active and trial_expires:
            now = datetime.now(timezone.utc)
            if isinstance(trial_expires, str):
                expires_dt = datetime.fromisoformat(trial_expires.replace('Z', '+00:00'))
            else:
                expires_dt = trial_expires.replace(tzinfo=timezone.utc) if trial_expires.tzinfo is None else trial_expires
            
            if now > expires_dt:
                should_expire_trial = True
                print(f"WARNING: Trial has expired! Current time: {now}, Trial expired: {expires_dt}")
        
        # For Bronze users, ensure trial is properly disabled
        if user_plan == 'bronze' and (trial_active or should_expire_trial):
            print(f"FIXING: Setting trial_active=False for Bronze user {user_id}")
            
            cursor.execute("""
                UPDATE users 
                SET trial_active = ?, trial_used_permanently = ?
                WHERE id = ?
            """, (False, True, user_id))
            
            conn.commit()
            print(f"SUCCESS: Updated database: trial_active=False, trial_used_permanently=True")
            
        elif user_plan == 'bronze' and not trial_active:
            print(f"SUCCESS: Bronze user {user_id} already has trial_active=False - no changes needed")
            
        else:
            print(f"INFO: User {user_id} has {user_plan} plan - leaving trial settings as-is")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== CLEAR TRIAL SESSION DATA ===")
    success = clear_trial_session_data(104)  # Your user ID
    if success:
        print("\nSUCCESS: Session data cleared! Please restart the app and log in again to see changes.")
    else:
        print("\nERROR: Failed to clear session data")