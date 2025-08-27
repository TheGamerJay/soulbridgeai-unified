#!/usr/bin/env python3
"""
Complete schema fix for SoulBridge AI users table
Adds all missing columns needed for the Bronze/Silver/Gold tier system
"""

import os
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_postgresql_schema():
    """Fix PostgreSQL production database schema"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.info("🔄 No DATABASE_URL found - skipping PostgreSQL schema fix")
        return True
    
    try:
        import psycopg2
        
        # Fix postgres:// URL format
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        logger.info("🐘 Fixing PostgreSQL schema...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Get current columns
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        current_columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"📋 Current PostgreSQL columns: {len(current_columns)} found")
        
        # Define missing columns to add
        missing_columns = [
            ("credits", "INTEGER DEFAULT 0"),
            ("purchased_credits", "INTEGER DEFAULT 0"), 
            ("artistic_time", "INTEGER DEFAULT 0"),
            ("trial_credits", "INTEGER DEFAULT 60"),
            ("trial_active", "BOOLEAN DEFAULT FALSE"),
            ("trial_expires_at", "TIMESTAMP NULL"),
            ("last_credit_reset", "DATE NULL")
        ]
        
        # Add missing columns
        added_count = 0
        for col_name, col_def in missing_columns:
            if col_name not in current_columns:
                try:
                    sql = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
                    cursor.execute(sql)
                    logger.info(f"  ✅ Added {col_name}")
                    added_count += 1
                except Exception as e:
                    logger.warning(f"  ⚠️ Column {col_name} may already exist: {e}")
        
        # Initialize artistic_time based on user_plan
        if added_count > 0:
            cursor.execute("""
                UPDATE users 
                SET artistic_time = CASE 
                    WHEN user_plan = 'silver' THEN 200
                    WHEN user_plan = 'gold' THEN 500
                    WHEN user_plan = 'max' THEN 500  -- Old naming
                    WHEN user_plan = 'growth' THEN 200  -- Old naming
                    ELSE 0
                END
                WHERE artistic_time = 0 OR artistic_time IS NULL
            """)
            logger.info("🎨 Initialized artistic_time based on user plans")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ PostgreSQL schema updated - {added_count} columns added")
        return True
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL schema fix failed: {e}")
        return False

def fix_sqlite_schema():
    """Fix local SQLite database schema"""
    db_path = "soulbridge.db"
    
    if not os.path.exists(db_path):
        logger.info(f"🔄 Local database {db_path} not found - skipping SQLite schema fix")
        return True
    
    try:
        import sqlite3
        
        logger.info("🗄️ Fixing SQLite schema...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current columns
        cursor.execute("PRAGMA table_info(users)")
        current_columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"📋 Current SQLite columns: {len(current_columns)} found")
        
        # Define missing columns to add
        missing_columns = [
            ("credits", "INTEGER DEFAULT 0"),
            ("purchased_credits", "INTEGER DEFAULT 0"), 
            ("artistic_time", "INTEGER DEFAULT 0"),
            ("trial_credits", "INTEGER DEFAULT 60"),
            ("trial_active", "BOOLEAN DEFAULT FALSE"),
            ("trial_expires_at", "TIMESTAMP NULL"),
            ("last_credit_reset", "DATE NULL")
        ]
        
        # Add missing columns
        added_count = 0
        for col_name, col_def in missing_columns:
            if col_name not in current_columns:
                try:
                    sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"
                    cursor.execute(sql)
                    logger.info(f"  ✅ Added {col_name}")
                    added_count += 1
                except Exception as e:
                    logger.warning(f"  ⚠️ Column {col_name} may already exist: {e}")
        
        # Initialize artistic_time based on user_plan
        if added_count > 0:
            cursor.execute("""
                UPDATE users 
                SET artistic_time = CASE 
                    WHEN user_plan = 'silver' THEN 200
                    WHEN user_plan = 'gold' THEN 500
                    WHEN user_plan = 'max' THEN 500  -- Old naming
                    WHEN user_plan = 'growth' THEN 200  -- Old naming
                    ELSE 0
                END
                WHERE artistic_time = 0 OR artistic_time IS NULL
            """)
            logger.info("🎨 Initialized artistic_time based on user plans")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ SQLite schema updated - {added_count} columns added")
        return True
        
    except Exception as e:
        logger.error(f"❌ SQLite schema fix failed: {e}")
        return False

def main():
    """Main function to fix both database schemas"""
    logger.info("🚀 Starting complete schema fix for SoulBridge AI...")
    
    # Fix both database types
    sqlite_success = fix_sqlite_schema()
    postgres_success = fix_postgresql_schema()
    
    if sqlite_success and postgres_success:
        logger.info("🎉 Schema fix completed successfully!")
        return True
    else:
        logger.error("❌ Some schema fixes failed - check logs above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)