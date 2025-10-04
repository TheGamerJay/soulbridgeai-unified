#!/usr/bin/env python3
"""
Reset trial for testing - allows user to test new credit system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_utils import get_database
import logging
from database_utils import format_query

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_trial_for_testing(user_id=104):
    """Reset trial for testing purposes"""
    try:
        db = get_database()
        if not db:
            print("❌ Database connection failed")
            return False
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Use correct placeholder for database type
        placeholder = "%s" if hasattr(db, 'postgres_url') and db.postgres_url else "?"
        
        print(f"🔄 Resetting trial for user {user_id}...")
        
        # Clear max_trials table (allows new trial activation)
        cursor.execute(f"DELETE FROM max_trials WHERE user_id = {placeholder}", (user_id,))
        deleted_trials = cursor.rowcount
        
        # Clear any trial_used_permanently flag in users table (if it exists)
        try:
            cursor.execute(f"UPDATE users SET trial_used_permanently = FALSE WHERE id = {placeholder}", (user_id,))
            updated_users = cursor.rowcount
        except Exception as e:
            print(f"⚠️ Note: trial_used_permanently column might not exist: {e}")
            updated_users = 0
        
        conn.commit()
        conn.close()
        
        print(f"✅ Trial reset complete:")
        print(f"   - Deleted {deleted_trials} trial records")
        print(f"   - Updated {updated_users} user records")
        print(f"   - User {user_id} can now activate a fresh 5-hour trial")
        print(f"   - New credit system: credits only decrease from usage!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting trial: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== TRIAL RESET FOR TESTING ===")
    success = reset_trial_for_testing(104)
    if success:
        print("\n🎉 Ready to test! Now activate trial with new fair credit system.")
    else:
        print("\n💥 Reset failed - check logs above")