#!/usr/bin/env python3
"""
Simple script to check and fix user plan data in SQLite database
"""
import sqlite3
import os

def main():
    # Connect to SQLite database
    db_path = 'soulbridge.db'
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("✅ Connected to SQLite database")
        
        # Check current user plans
        cursor.execute("SELECT id, email, plan_type, user_plan, trial_active FROM users")
        users = cursor.fetchall()
        
        print(f"\n📊 Found {len(users)} users:")
        for user in users:
            user_id, email, plan_type, user_plan, trial_active = user
            print(f"  ID: {user_id}, Email: {email}, plan_type: {plan_type}, user_plan: {user_plan}, trial_active: {trial_active}")
        
        # Fix any users with NULL or invalid user_plan
        cursor.execute("UPDATE users SET user_plan = 'free' WHERE user_plan IS NULL OR user_plan = ''")
        updated_count = cursor.rowcount
        if updated_count > 0:
            print(f"\n✅ Fixed {updated_count} users with NULL/empty user_plan")
        
        # Ensure trial_active is properly set (0 for False)
        cursor.execute("UPDATE users SET trial_active = 0 WHERE trial_active IS NULL")
        trial_fixed = cursor.rowcount
        if trial_fixed > 0:
            print(f"✅ Fixed {trial_fixed} users with NULL trial_active")
        
        conn.commit()
        
        # Show updated data
        cursor.execute("SELECT id, email, plan_type, user_plan, trial_active FROM users")
        updated_users = cursor.fetchall()
        
        print(f"\n📊 Updated user data:")
        for user in updated_users:
            user_id, email, plan_type, user_plan, trial_active = user
            print(f"  ID: {user_id}, Email: {email}, plan_type: {plan_type}, user_plan: {user_plan}, trial_active: {trial_active}")
        
        conn.close()
        print("\n✅ User data verification completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
