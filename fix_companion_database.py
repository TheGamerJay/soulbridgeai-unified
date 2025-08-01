#!/usr/bin/env python3
"""
Fix companion_data in database with proper JSONB format
"""

import psycopg2
import json

import os

def main():
    print("Fixing companion_data in database...")
    
    # Use environment variable for database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not found")
        print("Set it with your Railway database connection string")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # First, check current data
        print("Current data in database:")
        cursor.execute("SELECT id, email, companion_data FROM users WHERE id = 17;")
        result = cursor.fetchone()
        if result:
            print(f"User ID: {result[0]}")
            print(f"Email: {result[1]}")
            print(f"Current companion_data: {result[2]}")
        
        # Update with proper JSONB format
        print("\nUpdating companion_data...")
        cursor.execute("""
            UPDATE users
            SET companion_data = jsonb_build_object(
                'trial_active', true,
                'trial_companion', 'blayzica_growth',
                'trial_expires', '2025-08-02T22:06:53.766074',
                'selected_companion', 'blayzica_growth',
                'trial_used_permanently', true
            )
            WHERE id = 17;
        """)
        
        # Verify the update
        print("Verifying update...")
        cursor.execute("SELECT companion_data FROM users WHERE id = 17;")
        result = cursor.fetchone()
        if result:
            print(f"Updated companion_data: {result[0]}")
        
        conn.commit()
        print("\nDatabase updated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()