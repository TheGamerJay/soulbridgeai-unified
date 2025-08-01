#!/usr/bin/env python3
"""
Database Migration: Add Trial System Columns
Adds trial-related columns to the users table for premium companion trials
"""
import os
import sys
import psycopg2
from datetime import datetime

def migrate_trial_columns():
    """Add trial columns to users table"""
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: No DATABASE_URL found")
        return False
        
    print("Connecting to database for trial migration...")
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL database")
        
        # Check if trial columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('trial_started_at', 'trial_companion', 'trial_used_permanently')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        if len(existing_columns) == 3:
            print("✅ Trial columns already exist in users table")
            cursor.close()
            conn.close()
            return True
        
        # Add trial columns to users table
        print("📋 Adding trial columns to users table...")
        
        migrations = []
        
        if 'trial_started_at' not in existing_columns:
            migrations.append("ADD COLUMN trial_started_at TIMESTAMP")
            
        if 'trial_companion' not in existing_columns:
            migrations.append("ADD COLUMN trial_companion TEXT")
            
        if 'trial_used_permanently' not in existing_columns:
            migrations.append("ADD COLUMN trial_used_permanently BOOLEAN DEFAULT FALSE")
        
        if migrations:
            migration_sql = f"ALTER TABLE users {', '.join(migrations)}"
            print(f"🔧 Executing: {migration_sql}")
            cursor.execute(migration_sql)
            print("✅ Trial columns added successfully!")
        else:
            print("✅ All trial columns already exist")
        
        # Create index for better performance on trial queries
        print("🔧 Creating trial indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_trial_started_at 
            ON users(trial_started_at) 
            WHERE trial_started_at IS NOT NULL
        """)
        
        cursor.close()
        conn.close()
        
        print("✅ Trial system database migration completed successfully!")
        print("📊 Added columns:")
        print("   - trial_started_at (TIMESTAMP)")
        print("   - trial_companion (TEXT)")
        print("   - trial_used_permanently (BOOLEAN)")
        
        return True
        
    except Exception as e:
        print(f"❌ Trial migration failed: {e}")
        return False

if __name__ == "__main__":
    print("SoulBridge AI Trial System Migration")
    print("=" * 50)
    
    if migrate_trial_columns():
        print("\nTrial system database is ready!")
    else:
        print("\nTrial migration failed!")
        sys.exit(1)