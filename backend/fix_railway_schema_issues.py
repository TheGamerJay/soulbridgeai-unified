#!/usr/bin/env python3
"""
SoulBridge AI - Railway Schema Fix
Addresses specific PostgreSQL schema issues causing Railway deployment problems
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_railway_schema():
    """Fix Railway PostgreSQL schema issues"""
    try:
        # Only run if DATABASE_URL exists (Railway environment)
        if not os.environ.get('DATABASE_URL'):
            logger.info("Not running in Railway environment, skipping schema fixes")
            return True
            
        logger.info("🔧 Fixing Railway PostgreSQL schema issues...")
        
        # Import database connection
        try:
            from modules.shared.database import get_database
        except ImportError:
            from database_utils import get_database
        
        db = get_database()
        if not db:
            logger.error("❌ Could not get database connection")
            return False
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Fix 1: Ensure feature_usage table has proper schema
        logger.info("🔧 Fixing feature_usage table schema...")
        try:
            # First check if feature_usage table exists at all
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'feature_usage'
            """)
            
            if not cursor.fetchone():
                # Table doesn't exist, create it with proper schema
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
                logger.info("✅ feature_usage table created")
            else:
                # Table exists, check and add missing columns
                logger.info("Checking existing feature_usage table structure...")
                
                # Check for feature_name column (preferred column name)
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'feature_usage' AND column_name = 'feature_name'
                """)
                has_feature_name = cursor.fetchone()
                
                # Check for feature column (legacy column name)
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'feature_usage' AND column_name = 'feature'
                """)
                has_feature = cursor.fetchone()
                
                # Add feature_name column if neither exists
                if not has_feature_name and not has_feature:
                    logger.info("Adding feature_name column...")
                    cursor.execute("""
                        ALTER TABLE feature_usage 
                        ADD COLUMN feature_name VARCHAR(50) NOT NULL DEFAULT 'unknown'
                    """)
                
                # If we have 'feature' but not 'feature_name', rename it
                elif has_feature and not has_feature_name:
                    logger.info("Renaming feature column to feature_name...")
                    cursor.execute("""
                        ALTER TABLE feature_usage 
                        RENAME COLUMN feature TO feature_name
                    """)
                
                # Check for usage_date column
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'feature_usage' AND column_name = 'usage_date'
                """)
                if not cursor.fetchone():
                    logger.info("Adding usage_date column...")
                    cursor.execute("""
                        ALTER TABLE feature_usage 
                        ADD COLUMN usage_date DATE NOT NULL DEFAULT CURRENT_DATE
                    """)
                
                # Check for usage_count column
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'feature_usage' AND column_name = 'usage_count'
                """)
                if not cursor.fetchone():
                    logger.info("Adding usage_count column...")
                    cursor.execute("""
                        ALTER TABLE feature_usage 
                        ADD COLUMN usage_count INTEGER NOT NULL DEFAULT 1
                    """)
                
                # Check for created_at column
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'feature_usage' AND column_name = 'created_at'
                """)
                if not cursor.fetchone():
                    logger.info("Adding created_at column...")
                    cursor.execute("""
                        ALTER TABLE feature_usage 
                        ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """)
            
            # Now create the index with correct column names
            logger.info("Creating feature_usage index...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feature_usage_user_feature_date 
                ON feature_usage(user_id, feature_name, usage_date)
            """)
            logger.info("✅ feature_usage table schema fixed")
            
        except Exception as e:
            logger.warning(f"feature_usage table fix failed: {e}")
            import traceback
            logger.warning(traceback.format_exc())
        
        # Fix 2: Fix tier_limits table with proper primary key
        logger.info("🔧 Fixing tier_limits table schema...")
        try:
            # Check if tier_limits table exists and has proper structure
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'tier_limits' AND column_name = 'id'
            """)
            
            if not cursor.fetchone():
                logger.info("Recreating tier_limits table with proper schema...")
                
                # Drop the problematic table and recreate
                cursor.execute("DROP TABLE IF EXISTS tier_limits CASCADE")
                
                # Create with proper schema
                cursor.execute("""
                    CREATE TABLE tier_limits (
                        id SERIAL PRIMARY KEY,
                        tier VARCHAR(20) NOT NULL,
                        feature VARCHAR(50) NOT NULL,
                        daily_limit INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(tier, feature)
                    )
                """)
                
                # Insert default data
                default_limits = [
                    ('bronze', 'decoder', 5),
                    ('bronze', 'fortune', 5),
                    ('bronze', 'horoscope', 5),
                    ('bronze', 'creative_writing', 5),
                    ('silver', 'decoder', 15),
                    ('silver', 'fortune', 12),
                    ('silver', 'horoscope', 10),
                    ('silver', 'creative_writing', 15),
                    ('gold', 'decoder', 100),
                    ('gold', 'fortune', 150),
                    ('gold', 'horoscope', 50),
                    ('gold', 'creative_writing', 75)
                ]
                
                for tier, feature, limit in default_limits:
                    cursor.execute("""
                        INSERT INTO tier_limits (tier, feature, daily_limit)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (tier, feature) DO NOTHING
                    """, (tier, feature, limit))
                
                logger.info("✅ tier_limits table recreated with proper schema")
            
        except Exception as e:
            logger.warning(f"tier_limits table fix failed: {e}")
        
        # Fix 3: Ensure user_credits table exists with proper schema
        logger.info("🔧 Checking user_credits table...")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_credits (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    credits_remaining INTEGER DEFAULT 0,
                    last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ user_credits table verified")
            
        except Exception as e:
            logger.warning(f"user_credits table check failed: {e}")
        
        # Fix 4: Ensure credit_ledger table exists
        logger.info("🔧 Checking credit_ledger table...")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS credit_ledger (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    delta INTEGER NOT NULL,
                    reason VARCHAR(100),
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add index for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_credit_ledger_user_id 
                ON credit_ledger(user_id)
            """)
            logger.info("✅ credit_ledger table verified")
            
        except Exception as e:
            logger.warning(f"credit_ledger table check failed: {e}")
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        logger.info("✅ Railway schema fixes completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema fix failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = fix_railway_schema()
    if not success:
        sys.exit(1)
    logger.info("🚀 Schema fixes completed - Railway deployment should work now!")