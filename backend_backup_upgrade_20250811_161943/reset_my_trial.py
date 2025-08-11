#!/usr/bin/env python3
"""
Reset trial state for current user
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import Database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_trial_state():
    """Reset trial state for the most recent user (likely you)"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get the most recent user (likely you)
        cursor.execute("SELECT id, email FROM users ORDER BY created_at DESC LIMIT 1")
        user_data = cursor.fetchone()
        
        if not user_data:
            print("No users found in database")
            return
        
        user_id, email = user_data
        print(f"Resetting trial state for user ID {user_id} ({email})")
        
        # Reset trial state
        if db.use_postgres:
            cursor.execute("""
                UPDATE users 
                SET trial_active = FALSE, 
                    trial_started_at = NULL,
                    trial_used_permanently = FALSE,
                    trial_warning_sent = FALSE,
                    user_plan = 'free'
                WHERE id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                UPDATE users 
                SET trial_active = 0, 
                    trial_started_at = NULL,
                    trial_used_permanently = 0,
                    trial_warning_sent = 0,
                    user_plan = 'free'
                WHERE id = ?
            """, (user_id,))
        
        conn.commit()
        conn.close()
        
        print("✅ Trial state reset successfully!")
        print("You can now start a new 5-hour trial")
        
    except Exception as e:
        logger.error(f"Error resetting trial state: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    reset_trial_state()