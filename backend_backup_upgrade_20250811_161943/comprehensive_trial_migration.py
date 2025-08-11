#!/usr/bin/env python3
"""
Comprehensive Trial System Migration
Adds all required columns from the user's comprehensive trial system
"""

import os
import sys
import logging
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from auth import Database

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def migrate_database():
    """Add comprehensive trial system columns to users table"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        logger.info("Starting comprehensive trial system migration...")
        
        # List of columns to add with their definitions
        columns_to_add = [
            ("user_plan", "TEXT DEFAULT 'free'"),
            ("trial_active", "BOOLEAN DEFAULT FALSE" if db.use_postgres else "INTEGER DEFAULT 0"),
            ("trial_started_at", "TIMESTAMP"),
            ("trial_used_permanently", "BOOLEAN DEFAULT FALSE" if db.use_postgres else "INTEGER DEFAULT 0"),
            ("is_admin", "BOOLEAN DEFAULT FALSE" if db.use_postgres else "INTEGER DEFAULT 0"),
            ("decoder_used", "INTEGER DEFAULT 0"),
            ("fortune_used", "INTEGER DEFAULT 0"),
            ("horoscope_used", "INTEGER DEFAULT 0"),
            ("feature_preview_seen", "BOOLEAN DEFAULT FALSE" if db.use_postgres else "INTEGER DEFAULT 0"),
            ("trial_warning_sent", "BOOLEAN DEFAULT FALSE" if db.use_postgres else "INTEGER DEFAULT 0")
        ]
        
        # Add each column if it doesn't exist
        for column_name, column_def in columns_to_add:
            try:
                if db.use_postgres:
                    # PostgreSQL - use IF NOT EXISTS
                    cursor.execute(f"""
                        ALTER TABLE users 
                        ADD COLUMN IF NOT EXISTS {column_name} {column_def}
                    """)
                else:
                    # SQLite - check if column exists first
                    cursor.execute("PRAGMA table_info(users)")
                    existing_columns = [row[1] for row in cursor.fetchall()]
                    
                    if column_name not in existing_columns:
                        cursor.execute(f"""
                            ALTER TABLE users 
                            ADD COLUMN {column_name} {column_def}
                        """)
                        logger.info(f"Added column: {column_name}")
                    else:
                        logger.info(f"Column already exists: {column_name}")
                        
            except Exception as e:
                logger.warning(f"Could not add column {column_name}: {e}")
                continue
        
        # Migrate existing trial_start data to trial_started_at
        if db.use_postgres:
            cursor.execute("""
                UPDATE users 
                SET trial_started_at = trial_start,
                    trial_active = CASE WHEN trial_start IS NOT NULL THEN TRUE ELSE FALSE END
                WHERE trial_started_at IS NULL AND trial_start IS NOT NULL
            """)
        else:
            cursor.execute("""
                UPDATE users 
                SET trial_started_at = trial_start,
                    trial_active = CASE WHEN trial_start IS NOT NULL THEN 1 ELSE 0 END
                WHERE trial_started_at IS NULL AND trial_start IS NOT NULL
            """)
        
        # Set default user_plan for existing users
        cursor.execute("""
            UPDATE users 
            SET user_plan = 'free'
            WHERE user_plan IS NULL OR user_plan = ''
        """)
        
        conn.commit()
        logger.info("Comprehensive trial system migration completed successfully!")
        
        # Verify the migration
        if db.use_postgres:
            cursor.execute("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
        else:
            cursor.execute("PRAGMA table_info(users)")
            
        columns = cursor.fetchall()
        logger.info("Updated users table schema:")
        for col in columns:
            logger.info(f"   - {col}")
            
        # Check migration results
        cursor.execute("SELECT COUNT(*) FROM users WHERE user_plan IS NOT NULL")
        user_count = cursor.fetchone()[0]
        logger.info(f"Migration verified: {user_count} users have user_plan set")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Comprehensive Trial System Migration")
    print("=" * 50)
    
    success = migrate_database()
    
    if success:
        print("=" * 50)
        print("Migration completed successfully!")
        print("The comprehensive trial system is now ready to use.")
    else:
        print("=" * 50)
        print("Migration failed. Please check the logs above.")
        sys.exit(1)