#!/usr/bin/env python3
"""
Emergency Database Fix - Resolve feature_usage schema errors immediately
"""

import os
import sys
import logging
import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def emergency_fix():
    """Fix the feature_usage table schema immediately"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.info("No DATABASE_URL found - not in Railway environment")
            return True
            
        logger.info("🚨 EMERGENCY DATABASE FIX - Fixing feature_usage table...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Drop the problematic index if it exists
        try:
            cursor.execute("DROP INDEX IF EXISTS idx_feature_usage_user_feature_date")
            logger.info("✅ Dropped problematic index")
        except Exception as e:
            logger.warning(f"Index drop warning: {e}")
        
        # Check if feature_usage table exists
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'feature_usage'
        """)
        
        if not cursor.fetchone():
            # Create table if it doesn't exist
            logger.info("Creating feature_usage table...")
            cursor.execute("""
                CREATE TABLE feature_usage (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    feature_name VARCHAR(50) NOT NULL,
                    usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    usage_count INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            # Add missing columns to existing table
            logger.info("Updating existing feature_usage table...")
            
            # Add feature_name column if missing
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'feature_usage' AND column_name = 'feature_name'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE feature_usage 
                    ADD COLUMN feature_name VARCHAR(50) NOT NULL DEFAULT 'unknown'
                """)
                logger.info("Added feature_name column")
            
            # Add usage_date column if missing
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'feature_usage' AND column_name = 'usage_date'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE feature_usage 
                    ADD COLUMN usage_date DATE NOT NULL DEFAULT CURRENT_DATE
                """)
                logger.info("Added usage_date column")
            
            # Add usage_count column if missing
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'feature_usage' AND column_name = 'usage_count'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE feature_usage 
                    ADD COLUMN usage_count INTEGER NOT NULL DEFAULT 1
                """)
                logger.info("Added usage_count column")
        
        # Create the correct index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feature_usage_user_feature_date_fixed 
            ON feature_usage(user_id, feature_name, usage_date)
        """)
        logger.info("✅ Created correct index")
        
        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("🎉 EMERGENCY FIX COMPLETED SUCCESSFULLY!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Emergency fix failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = emergency_fix()
    if not success:
        sys.exit(1)
    logger.info("🚀 Database is now fixed!")