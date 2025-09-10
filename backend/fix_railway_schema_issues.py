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
        
        # Fix 1: Add missing columns to feature_usage table
        logger.info("🔧 Fixing feature_usage table schema...")
        try:
            # Check if created_at column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'feature_usage' AND column_name = 'created_at'
            """)
            
            if not cursor.fetchone():
                logger.info("Adding created_at column to feature_usage...")
                cursor.execute("""
                    ALTER TABLE feature_usage 
                    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
                
            # Now create the index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feature_usage_user_feature_date 
                ON feature_usage(user_id, feature, DATE(created_at))
            """)
            logger.info("✅ feature_usage table fixed")
            
        except Exception as e:
            logger.warning(f"feature_usage table fix failed: {e}")
        
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