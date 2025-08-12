#!/usr/bin/env python3
"""
Database Schema Fix - Add Missing Tables and Columns for Unified Tier System
"""

import os
import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_schema():
    """Add missing tables and columns for the unified tier system"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL not found in environment")
            return False
            
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # 1. Create feature_usage table if it doesn't exist
        logger.info("🔧 Creating feature_usage table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feature_usage (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                feature VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Add missing columns to users table
        missing_columns = [
            ('credits', 'INTEGER DEFAULT 0'),
            ('last_credit_reset', 'TIMESTAMP'),
            ('purchased_credits', 'INTEGER DEFAULT 0')
        ]
        
        for column_name, column_type in missing_columns:
            try:
                logger.info(f"🔧 Adding column '{column_name}' to users table...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                logger.info(f"✅ Successfully added column '{column_name}'")
            except psycopg2.errors.DuplicateColumn:
                logger.info(f"⚠️ Column '{column_name}' already exists, skipping...")
                conn.rollback()  # Rollback the failed transaction
            except Exception as e:
                logger.error(f"❌ Error adding column '{column_name}': {e}")
                conn.rollback()
        
        # 3. Create indexes for performance
        logger.info("🔧 Creating indexes for performance...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feature_usage_user_feature_date ON feature_usage(user_id, feature, DATE(created_at))")
            logger.info("✅ Created feature_usage index")
        except Exception as e:
            logger.info(f"⚠️ Index creation warning: {e}")
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        logger.info("🎉 Database schema fix completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database schema fix failed: {e}")
        return False

if __name__ == "__main__":
    print("SoulBridge AI Database Schema Fix")
    print("=================================")
    
    success = fix_database_schema()
    
    if success:
        print("Schema fix completed! The unified tier system should now work properly.")
    else:
        print("Schema fix failed! Check the logs for errors.")