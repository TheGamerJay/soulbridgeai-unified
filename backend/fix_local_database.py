#!/usr/bin/env python3
"""
FIX LOCAL DATABASE: Add missing artistic_time columns
"""

import os
import sqlite3
import sys
sys.path.append(os.path.dirname(__file__))

from database_utils import get_database
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_local_database():
    """Add missing columns to local SQLite database"""
    print("\n🔧 FIXING LOCAL DATABASE")
    print("=" * 50)
    
    try:
        # Connect to SQLite database
        db = get_database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("✅ Connected to local SQLite database")
        
        # Check what columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        
        print(f"\n📋 Existing columns in users table:")
        for col in existing_columns:
            print(f"   - {col}")
        
        # Add missing columns
        missing_columns = []
        
        # Check and add artistic_time
        if 'artistic_time' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN artistic_time INTEGER DEFAULT 0")
            missing_columns.append('artistic_time')
            print("✅ Added artistic_time column")
        
        # Check and add trial_credits  
        if 'trial_credits' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN trial_credits INTEGER DEFAULT 60")
            missing_columns.append('trial_credits')
            print("✅ Added trial_credits column")
        
        # Check and add last_credit_reset
        if 'last_credit_reset' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_credit_reset DATE")
            missing_columns.append('last_credit_reset')
            print("✅ Added last_credit_reset column")
        
        # Check and add trial_active
        if 'trial_active' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN trial_active BOOLEAN DEFAULT FALSE")
            missing_columns.append('trial_active')
            print("✅ Added trial_active column")
        
        # Check and add trial_expires_at
        if 'trial_expires_at' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN trial_expires_at TIMESTAMP")
            missing_columns.append('trial_expires_at')
            print("✅ Added trial_expires_at column")
        
        # Check and add trial_used_permanently
        if 'trial_used_permanently' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN trial_used_permanently BOOLEAN DEFAULT FALSE")
            missing_columns.append('trial_used_permanently')
            print("✅ Added trial_used_permanently column")
        
        if missing_columns:
            print(f"\n📦 Added {len(missing_columns)} missing columns: {', '.join(missing_columns)}")
        else:
            print("\n✅ All required columns already exist")
        
        # Now initialize your user data
        print(f"\n🔧 INITIALIZING USER 104 DATA")
        print("-" * 40)
        
        # Get your current data
        cursor.execute("SELECT id, email, user_plan, trial_active FROM users WHERE id = ?", (104,))
        result = cursor.fetchone()
        
        if result:
            user_id, email, plan, trial_active = result
            print(f"✅ Found user: {email} (Plan: {plan}, Trial: {trial_active})")
            
            # Set up proper artistic time based on plan
            if plan == 'bronze':
                if trial_active:
                    # Bronze trial user gets 60 trial credits
                    cursor.execute("""
                        UPDATE users 
                        SET artistic_time = 0, trial_credits = 60
                        WHERE id = ?
                    """, (104,))
                    print("✅ Set Bronze trial user: 0 monthly + 60 trial credits")
                else:
                    # Bronze user gets no credits
                    cursor.execute("""
                        UPDATE users 
                        SET artistic_time = 0, trial_credits = 0  
                        WHERE id = ?
                    """, (104,))
                    print("✅ Set Bronze user: 0 credits (needs trial)")
            elif plan == 'silver':
                # Silver gets 200 monthly
                cursor.execute("""
                    UPDATE users 
                    SET artistic_time = 200, trial_credits = 0
                    WHERE id = ?
                """, (104,))
                print("✅ Set Silver user: 200 monthly credits")
            elif plan == 'gold':
                # Gold gets 500 monthly
                cursor.execute("""
                    UPDATE users 
                    SET artistic_time = 500, trial_credits = 0
                    WHERE id = ?
                """, (104,))
                print("✅ Set Gold user: 500 monthly credits")
        else:
            print("❌ User 104 not found")
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        print(f"\n🎯 DATABASE FIX COMPLETE!")
        print("=" * 50)
        print("Now run: python debug_artistic_time.py")
        print("Your artistic time should work correctly!")
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_local_database()