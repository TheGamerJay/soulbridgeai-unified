#!/usr/bin/env python3
"""
Setup development user account
Creates your user account in the local SQLite database for development
"""

from auth import Database
import hashlib
from database_utils import format_query

def setup_dev_user():
    """Create development user account"""
    print("Setting up development user account...")
    
    # Initialize database
    db = Database()
    db.init_database()
    
    # User details
    import os
    email = os.environ.get('DEV_ADMIN_EMAIL', 'dev-admin@localhost')
    password = os.environ.get('DEV_ADMIN_PASSWORD', 'dev-password-change-me')
    display_name = os.environ.get('DEV_ADMIN_NAME', 'DevAdmin')
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute(format_query(SELECT id FROM users WHERE email = ?"), (email,))
        if cursor.fetchone():
            print(f"User {email} already exists in development database")
            conn.close()
            return
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create user
        cursor.execute(format_query("""
            INSERT INTO users (email, password_hash, display_name, user_plan, terms_accepted, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """), (email, password_hash, display_name, 'free', True))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✓ Development user created successfully!")
        print(f"  Email: {email}")
        print(f"  User ID: {user_id}")
        print(f"  Plan: free")
        print(f"  Terms accepted: True")
        
    except Exception as e:
        print(f"Error creating user: {e}")

if __name__ == "__main__":
    setup_dev_user()