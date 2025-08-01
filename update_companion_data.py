#!/usr/bin/env python3
"""
Script to update companion_data field in users table
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Environment variables loaded from .env file")
except ImportError:
    print("python-dotenv not installed, relying on system environment variables")

def update_companion_data():
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not found in environment. Please provide connection details:")
        host = input("PostgreSQL host (e.g., shinkansen.proxy.rlwy.net): ").strip()
        port = input("PostgreSQL port (e.g., 15522): ").strip()
        user = input("PostgreSQL user (e.g., postgres): ").strip()
        password = input("PostgreSQL password: ").strip()
        database = input("PostgreSQL database (e.g., railway): ").strip()
        
        if not all([host, port, user, password, database]):
            print("ERROR: All connection details are required")
            return False
            
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    # The JSON data to insert
    companion_data = {
        "trial_active": True,
        "trial_expires": "2025-08-02T22:06:53.766074",
        "trial_companion": "blayzica_growth",
        "selected_companion": "blayzica_growth",
        "trial_used_permanently": True
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # First, let's see what users exist
        cursor.execute("SELECT id, email, companion_data FROM users ORDER BY id;")
        users = cursor.fetchall()
        
        print(f"Found {len(users)} users:")
        for i, user in enumerate(users):
            print(f"{i+1}. ID: {user['id']}, Email: {user['email']}, Current companion_data: {user['companion_data']}")
        
        if not users:
            print("No users found in the database")
            return False
        
        # Ask which user to update
        try:
            choice = input(f"\nWhich user would you like to update? (1-{len(users)} or 'all' for all users): ").strip().lower()
            
            if choice == 'all':
                # Update all users
                for user in users:
                    cursor.execute(
                        "UPDATE users SET companion_data = %s WHERE id = %s",
                        (json.dumps(companion_data), user['id'])
                    )
                    print(f"Updated user {user['id']} ({user['email']})")
                
                conn.commit()
                print(f"\nSuccessfully updated companion_data for all {len(users)} users")
                
            else:
                # Update specific user
                user_index = int(choice) - 1
                if 0 <= user_index < len(users):
                    selected_user = users[user_index]
                    
                    cursor.execute(
                        "UPDATE users SET companion_data = %s WHERE id = %s",
                        (json.dumps(companion_data), selected_user['id'])
                    )
                    
                    conn.commit()
                    print(f"\nSuccessfully updated companion_data for user {selected_user['id']} ({selected_user['email']})")
                else:
                    print("Invalid choice")
                    return False
                    
        except (ValueError, KeyboardInterrupt):
            print("Operation cancelled")
            return False
            
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
    
    return True

if __name__ == "__main__":
    print("SoulBridge AI - Companion Data Updater")
    print("=" * 50)
    
    success = update_companion_data()
    if success:
        print("\nUpdate completed successfully!")
    else:
        print("\nUpdate failed!")