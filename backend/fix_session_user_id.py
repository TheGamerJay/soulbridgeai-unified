#!/usr/bin/env python3
"""
Quick utility to check and fix session user_id mismatch
Run this to check what user_id should be used based on email
"""

import os
from database import Database

def check_user_email(email):
    """Check what user_id corresponds to an email"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, email, display_name, created_at FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()
        
        if result:
            print(f"✅ Found user: ID={result[0]}, Email={result[1]}, Name={result[2]}, Created={result[3]}")
            return result[0]
        else:
            print(f"❌ No user found with email: {email}")
            return None
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def check_user_id(user_id):
    """Check if a user_id exists"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, email, display_name FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        
        if result:
            print(f"✅ User ID {user_id} exists: {result[1]} ({result[2]})")
            return True
        else:
            print(f"❌ User ID {user_id} does not exist")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking user session mismatch...")
    
    # Check if user_id 17 exists
    print("\n1. Checking user_id 17 (from session):")
    check_user_id(17)
    
    # Check if user_id 91 exists  
    print("\n2. Checking user_id 91 (reported current):")
    check_user_id(91)
    
    # Check by email
    print("\n3. Checking by email:")
    email = input("Enter your email: ").strip()
    if email:
        correct_user_id = check_user_email(email)
        if correct_user_id:
            print(f"\n✅ Your correct user_id should be: {correct_user_id}")