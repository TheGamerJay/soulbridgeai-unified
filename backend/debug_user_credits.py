#!/usr/bin/env python3
"""
Debug user credits by directly calling the get_artistic_time function
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app and functions
from app import get_artistic_time, ensure_user_data_initialized, get_database
import sqlite3

def debug_user_credits():
    """Debug what get_artistic_time returns for different users"""
    
    print("🔍 DEBUGGING USER CREDITS...")
    
    # Check database first
    db_path = "soulbridge.db"
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("""
            SELECT id, email, user_plan, artistic_time, trial_active, trial_credits 
            FROM users 
            ORDER BY id
        """)
        users = cursor.fetchall()
        
        print("\\n=== DATABASE VALUES ===")
        for user in users:
            user_id, email, plan, artistic, trial_active, trial_credits = user
            print(f"User {user_id}: {email}")
            print(f"  Plan: {plan}")
            print(f"  DB Artistic Time: {artistic}")
            print(f"  Trial Active: {trial_active}")
            print(f"  Trial Credits: {trial_credits}")
        
        conn.close()
        
        print("\\n=== TESTING get_artistic_time() FUNCTION ===")
        
        # Test the get_artistic_time function for each user
        for user in users:
            user_id = user[0]
            email = user[1]
            
            try:
                # Test the actual function
                credits = get_artistic_time(user_id)
                print(f"User {user_id} ({email}): get_artistic_time() returns {credits}")
            except Exception as e:
                print(f"User {user_id} ({email}): ERROR - {e}")
        
        print("\\n=== DIAGNOSIS ===")
        print("If get_artistic_time() returns 0 but DB shows proper values:")
        print("- Check if database connection is working properly")
        print("- Check if get_artistic_time() is using correct database")
        print("- Users may need to log out and log back in to refresh session")
        
    else:
        print("❌ Local database not found")

if __name__ == "__main__":
    debug_user_credits()