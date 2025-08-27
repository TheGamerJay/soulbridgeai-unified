#!/usr/bin/env python3
"""
Fix missing columns in production PostgreSQL database
This script adds all the missing artistic time system columns
"""

import os
import psycopg2
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_production_columns():
    """Add missing columns to production database"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        logger.error("❌ DATABASE_URL not found - cannot connect to production")
        return False
    
    try:
        # Fix postgres:// URL format
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        logger.info("🔧 Connecting to production PostgreSQL database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check what columns currently exist
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        current_columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"📋 Current columns: {len(current_columns)} found")
        
        # Define all required columns with their definitions
        required_columns = {
            'artistic_time': 'INTEGER DEFAULT 0',
            'trial_credits': 'INTEGER DEFAULT 60', 
            'credits': 'INTEGER DEFAULT 0',
            'purchased_credits': 'INTEGER DEFAULT 0',
            'last_credit_reset': 'DATE NULL'
        }
        
        # Add missing columns
        added_count = 0
        for col_name, col_def in required_columns.items():
            if col_name not in current_columns:
                try:
                    sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"
                    cursor.execute(sql)
                    logger.info(f"✅ Added column: {col_name}")
                    added_count += 1
                except Exception as e:
                    logger.error(f"❌ Failed to add {col_name}: {e}")
            else:
                logger.info(f"✓ Column {col_name} already exists")
        
        # Initialize artistic_time based on user_plan for existing users
        if added_count > 0:
            logger.info("🎨 Initializing artistic_time for existing users...")
            cursor.execute("""
                UPDATE users 
                SET artistic_time = CASE 
                    WHEN user_plan = 'silver' OR user_plan = 'growth' THEN 200
                    WHEN user_plan = 'gold' OR user_plan = 'max' THEN 500
                    ELSE 0
                END
                WHERE artistic_time = 0 OR artistic_time IS NULL
            """)
            
            cursor.execute("SELECT ROW_COUNT()")
            updated_count = cursor.fetchone()[0] if cursor.rowcount > 0 else 0
            logger.info(f"🎯 Updated {updated_count} users with proper artistic time allocation")
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        logger.info(f"🎉 Production database updated successfully!")
        logger.info(f"📊 Added {added_count} new columns")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating production database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_production_columns()
    if success:
        print("✅ Production database is now ready!")
        print("🔄 Users should now see their correct artistic time balance")
    else:
        print("❌ Production database update failed")