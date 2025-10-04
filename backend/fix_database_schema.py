#!/usr/bin/env python3
"""
Fix database schema issues causing 500 errors
- Add missing 'referrals' and 'credits' columns to users table
- Fix tier_limits table primary key constraint
- Fix feature_usage table structure
"""

import os
import logging
from database_utils import get_database
from database_utils import format_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_schema():
    """Fix all database schema issues"""
    try:
        db = get_database()
        if not db:
            logger.error("Could not connect to database")
            return False
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        logger.info("Starting database schema fixes...")
        
        # Fix 1: Add missing columns to users table
        logger.info("Adding missing columns to users table...")
        
        if db.use_postgres:
            # Add referrals column if missing
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS referrals INTEGER DEFAULT 0
            """)
            
            # Add credits column if missing (artistic_credits might already exist)
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS credits INTEGER DEFAULT 0
            """)
            
            # Update credits from artistic_credits if exists
            cursor.execute("""
                UPDATE users 
                SET credits = COALESCE(artistic_credits, 0) 
                WHERE credits IS NULL OR credits = 0
            """)
            
        else:
            # SQLite - need to check if columns exist first
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'referrals' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN referrals INTEGER DEFAULT 0")
            
            if 'credits' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 0")
                
            # Update credits from artistic_credits if exists
            if 'artistic_credits' in columns:
                cursor.execute("""
                    UPDATE users 
                    SET credits = COALESCE(artistic_credits, 0) 
                    WHERE credits IS NULL OR credits = 0
                """)
        
        # Fix 2: Fix tier_limits table structure
        logger.info("Fixing tier_limits table...")
        
        if db.use_postgres:
            # Drop and recreate tier_limits table with proper structure
            cursor.execute("DROP TABLE IF EXISTS tier_limits CASCADE")
            cursor.execute("""
                CREATE TABLE tier_limits (
                    id SERIAL PRIMARY KEY,
                    tier VARCHAR(20) NOT NULL,
                    feature VARCHAR(50) NOT NULL,
                    daily_limit INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(tier, feature)
                )
            """)
        else:
            # SQLite
            cursor.execute("DROP TABLE IF EXISTS tier_limits")
            cursor.execute("""
                CREATE TABLE tier_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tier TEXT NOT NULL,
                    feature TEXT NOT NULL,
                    daily_limit INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(tier, feature)
                )
            """)
        
        # Insert default tier limits
        tier_limits_data = [
            ('bronze', 'decoder', 5),
            ('bronze', 'fortune', 5),
            ('bronze', 'horoscope', 5),
            ('bronze', 'creative_writer', 5),
            ('silver', 'decoder', 15),
            ('silver', 'fortune', 8),
            ('silver', 'horoscope', 10),
            ('silver', 'creative_writer', 20),
            ('gold', 'decoder', -1),  # -1 means unlimited
            ('gold', 'fortune', -1),
            ('gold', 'horoscope', -1),
            ('gold', 'creative_writer', -1),
        ]
        
        if db.use_postgres:
            for tier, feature, limit in tier_limits_data:
                cursor.execute("""
                    INSERT INTO tier_limits (tier, feature, daily_limit)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (tier, feature) DO NOTHING
                """, (tier, feature, limit))
        else:
            for tier, feature, limit in tier_limits_data:
                cursor.execute(format_query("""
                    INSERT OR IGNORE INTO tier_limits (tier, feature, daily_limit)
                    VALUES (?, ?, ?)
                """), (tier, feature, limit))
        
        # Fix 3: Fix feature_usage table structure
        logger.info("Fixing feature_usage table...")
        
        if db.use_postgres:
            # Drop and recreate with proper structure
            cursor.execute("DROP TABLE IF EXISTS feature_usage CASCADE")
            cursor.execute("""
                CREATE TABLE feature_usage (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    feature VARCHAR(50) NOT NULL,
                    usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    usage_count INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, feature, usage_date)
                )
            """)
            
            # Create index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feature_usage_user_feature_date 
                ON feature_usage(user_id, feature, usage_date)
            """)
            
        else:
            # SQLite
            cursor.execute("DROP TABLE IF EXISTS feature_usage")
            cursor.execute("""
                CREATE TABLE feature_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    feature TEXT NOT NULL,
                    usage_date DATE NOT NULL DEFAULT (DATE('now')),
                    usage_count INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, feature, usage_date)
                )
            """)
            
            # Create index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feature_usage_user_feature_date 
                ON feature_usage(user_id, feature, usage_date)
            """)
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        logger.info("Database schema fixes completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database schema fix failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = fix_database_schema()
    if success:
        print("✅ Database schema fixed successfully!")
    else:
        print("❌ Database schema fix failed!")
        exit(1)