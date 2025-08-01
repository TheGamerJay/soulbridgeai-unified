#!/usr/bin/env python3
"""
Simple script to update companion_data field in users table
EDIT THE CONNECTION DETAILS BELOW BEFORE RUNNING
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor

# ===========================================
# CONNECTION DETAILS FROM YOUR RAILWAY SETUP:
# ===========================================
DB_HOST = "trolley.proxy.rlwy.net"     # Your Railway PostgreSQL host
DB_PORT = "51310"                       # Your Railway PostgreSQL port  
DB_USER = "postgres"                    # Your Railway PostgreSQL user
DB_PASSWORD = "YOUR_PASSWORD_HERE"      # Your Railway PostgreSQL password
DB_NAME = "railway"                     # Your Railway PostgreSQL database name

# The JSON data to insert
COMPANION_DATA = {
    "trial_active": True,
    "trial_expires": "2025-08-02T22:06:53.766074",
    "trial_companion": "blayzica_growth",
    "selected_companion": "blayzica_growth",
    "trial_used_permanently": True
}

def main():
    print("SoulBridge AI - Companion Data Updater (Simple)")
    print("=" * 50)
    
    # Check if password was updated
    if DB_PASSWORD == "YOUR_PASSWORD_HERE":
        print("ERROR: Please edit the script and set your actual database password")
        print("Look for DB_PASSWORD = 'YOUR_PASSWORD_HERE' in the script")
        return
    
    # Build connection URL
    database_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all users
        cursor.execute("SELECT id, email, companion_data FROM users ORDER BY id;")
        users = cursor.fetchall()
        
        if not users:
            print("No users found in the database")
            return
        
        print(f"Found {len(users)} users:")
        for i, user in enumerate(users):
            print(f"{i+1}. ID: {user['id']}, Email: {user['email']}")
            if user['companion_data']:
                print(f"   Current data: {user['companion_data']}")
            else:
                print("   Current data: None")
        
        print(f"\nUpdating ALL users with new companion_data...")
        
        # Update all users
        updated_count = 0
        for user in users:
            cursor.execute(
                "UPDATE users SET companion_data = %s WHERE id = %s",
                (json.dumps(COMPANION_DATA), user['id'])
            )
            updated_count += 1
            print(f"Updated user {user['id']} ({user['email']})")
        
        # Commit changes
        conn.commit()
        print(f"\nSuccessfully updated companion_data for {updated_count} users!")
        
        # Verify the update
        print("\nVerifying updates...")
        cursor.execute("SELECT id, email, companion_data FROM users ORDER BY id;")
        updated_users = cursor.fetchall()
        
        for user in updated_users:
            data = user['companion_data']
            if data and isinstance(data, dict):
                print(f"User {user['id']}: trial_active = {data.get('trial_active')}, selected_companion = {data.get('selected_companion')}")
        
        print("\nUpdate completed successfully!")
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()