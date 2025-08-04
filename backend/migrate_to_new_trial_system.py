#!/usr/bin/env python3
"""
Database migration script for the new trial system
Adds required columns and updates existing data
"""

import os
import psycopg2
from datetime import datetime, timedelta
import sys

def migrate_database():
    """Migrate database to new trial system"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("Starting database migration for new trial system...")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name IN ('trial_expires_at', 'trial_used_permanently')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add new columns if they don't exist
        if 'trial_expires_at' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN trial_expires_at TIMESTAMP")
            print("Added trial_expires_at column")
        else:
            print("trial_expires_at column already exists")
            
        if 'trial_used_permanently' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN trial_used_permanently BOOLEAN DEFAULT FALSE")
            print("Added trial_used_permanently column")
        else:
            print("trial_used_permanently column already exists")
        
        # Migrate existing trial data
        cursor.execute("""
            SELECT id, trial_started_at FROM users 
            WHERE trial_started_at IS NOT NULL AND trial_expires_at IS NULL
        """)
        users_to_migrate = cursor.fetchall()
        
        for user_id, trial_started_at in users_to_migrate:
            if trial_started_at:
                # Calculate expiration (5 hours from start)
                trial_expires_at = trial_started_at + timedelta(hours=5)
                cursor.execute("""
                    UPDATE users 
                    SET trial_expires_at = %s, trial_used_permanently = TRUE 
                    WHERE id = %s
                """, (trial_expires_at, user_id))
                print(f"Migrated user {user_id} trial data")
        
        # Update plan names to consistent naming
        cursor.execute("UPDATE users SET plan = 'free' WHERE plan = 'foundation'")
        cursor.execute("UPDATE users SET plan = 'growth' WHERE plan = 'premium'") 
        cursor.execute("UPDATE users SET plan = 'max' WHERE plan = 'enterprise'")
        
        print("Updated plan names to consistent naming (free/growth/max)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)