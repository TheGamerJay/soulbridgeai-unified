#!/usr/bin/env python3

import sqlite3
import os

def simple_debug():
    print("DEBUGGING USER CREDITS...")
    
    db_path = "soulbridge.db"
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, email, user_plan, artistic_time, trial_active FROM users")
        users = cursor.fetchall()
        
        print("\nDATABASE VALUES:")
        for user in users:
            user_id, email, plan, artistic, trial = user
            print(f"User {user_id}: {email} - Plan: {plan} - Artistic Time: {artistic} - Trial: {trial}")
        
        conn.close()
        
        print("\nSUMMARY:")
        print("If users still see 0 artistic time in the UI, they need to:")
        print("1. Log out completely") 
        print("2. Log back in")
        print("3. This will refresh their session with new database values")
        
    else:
        print("Database not found")

if __name__ == "__main__":
    simple_debug()