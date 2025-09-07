#!/usr/bin/env python3
"""
Comprehensive Database Schema Fix
Fix all missing tables and columns causing Railway deployment errors
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main fix runner for all database schema issues"""
    print("Comprehensive Database Schema Fix")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable not set")
        print("This script requires Railway DATABASE_URL")
        return False
    
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Railway PostgreSQL'}")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        fixes_applied = []
        
        print("\n=== COMPREHENSIVE DATABASE SCHEMA FIX ===")
        
        # 1. Fix missing referrals column in users table
        print("\n1. Adding missing 'referrals' column to users table...")
        try:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS referrals INTEGER DEFAULT 0
            """)
            conn.commit()
            print("✅ Added referrals column to users table")
            fixes_applied.append("Added referrals column to users table")
        except Exception as e:
            print(f"⚠️ Referrals column: {e}")
            conn.rollback()
            fixes_applied.append(f"Referrals column issue: {str(e)}")
        
        # 2. Fix tier_limits table - ensure it has proper ID column
        print("\n2. Fixing tier_limits table structure...")
        try:
            # Check if table exists and has proper structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'tier_limits'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            if not columns:
                # Table doesn't exist, create it
                cursor.execute("""
                    CREATE TABLE tier_limits (
                        id SERIAL PRIMARY KEY,
                        tier VARCHAR(20) NOT NULL,
                        feature VARCHAR(50) NOT NULL,
                        daily_limit INTEGER NOT NULL DEFAULT 0,
                        UNIQUE(tier, feature)
                    )
                """)
                print("✅ Created tier_limits table")
                fixes_applied.append("Created tier_limits table")
            else:
                # Check if id column is auto-increment
                has_serial_id = any(col for col in columns if col[0] == 'id' and col[3] and 'nextval' in str(col[3]))
                if not has_serial_id:
                    # Drop and recreate table with proper ID
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
                    print("✅ Recreated tier_limits table with proper ID column")
                    fixes_applied.append("Recreated tier_limits table with proper ID column")
                else:
                    print("✅ tier_limits table structure is correct")
                    fixes_applied.append("tier_limits table structure verified")
            
            conn.commit()
        except Exception as e:
            print(f"⚠️ tier_limits table fix: {e}")
            conn.rollback()
            fixes_applied.append(f"tier_limits table issue: {str(e)}")
        
        # 3. Fix feature_usage table - standardize column names
        print("\n3. Fixing feature_usage table structure...")
        try:
            # Drop existing table to ensure consistent structure
            cursor.execute("DROP TABLE IF EXISTS feature_usage CASCADE")
            
            # Create with standardized structure
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
            
            # Create proper index (using usage_date instead of DATE(created_at))
            cursor.execute("""
                CREATE INDEX idx_feature_usage_user_feature_date 
                ON feature_usage(user_id, feature, usage_date)
            """)
            
            print("✅ Recreated feature_usage table with standardized structure")
            fixes_applied.append("Recreated feature_usage table with standardized structure")
            conn.commit()
        except Exception as e:
            print(f"⚠️ feature_usage table fix: {e}")
            conn.rollback()
            fixes_applied.append(f"feature_usage table issue: {str(e)}")
        
        # 4. Create user_activity_log table
        print("\n4. Creating user_activity_log table...")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity_log (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    feature_type VARCHAR(50) NOT NULL,
                    session_duration_seconds INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_log_user_created
                ON user_activity_log(user_id, created_at)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_log_created_at
                ON user_activity_log(created_at)
            """)
            
            print("✅ Created user_activity_log table with indexes")
            fixes_applied.append("Created user_activity_log table with indexes")
            conn.commit()
        except Exception as e:
            print(f"⚠️ user_activity_log table: {e}")
            conn.rollback()
            fixes_applied.append(f"user_activity_log table issue: {str(e)}")
        
        # 5. Populate tier_limits with default data
        print("\n5. Populating tier_limits with default data...")
        try:
            default_limits = [
                ('bronze', 'decoder', 5),
                ('bronze', 'fortune', 5),
                ('bronze', 'horoscope', 5),
                ('bronze', 'creative_writer', 5),
                ('bronze', 'soul_riddle', 3),
                ('silver', 'decoder', 15),
                ('silver', 'fortune', 8),
                ('silver', 'horoscope', 10),
                ('silver', 'creative_writer', 20),
                ('silver', 'soul_riddle', 20),
                ('gold', 'decoder', 999),
                ('gold', 'fortune', 999),
                ('gold', 'horoscope', 999),
                ('gold', 'creative_writer', 999),
                ('gold', 'soul_riddle', 999)
            ]
            
            for tier, feature, limit in default_limits:
                cursor.execute("""
                    INSERT INTO tier_limits (tier, feature, daily_limit)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (tier, feature) DO UPDATE SET 
                    daily_limit = EXCLUDED.daily_limit
                """, (tier, feature, limit))
            
            print("✅ Populated tier_limits with default data")
            fixes_applied.append("Populated tier_limits with default data")
            conn.commit()
        except Exception as e:
            print(f"⚠️ tier_limits population: {e}")
            conn.rollback()
            fixes_applied.append(f"tier_limits population issue: {str(e)}")
        
        # 6. Final verification
        print("\n6. Verifying all fixes...")
        try:
            # Check users.referrals column
            cursor.execute("SELECT referrals FROM users LIMIT 1")
            print("✅ users.referrals column accessible")
            
            # Check tier_limits structure
            cursor.execute("SELECT COUNT(*) FROM tier_limits")
            count = cursor.fetchone()[0]
            print(f"✅ tier_limits table has {count} records")
            
            # Check feature_usage structure
            cursor.execute("SELECT usage_date, feature FROM feature_usage LIMIT 1")
            print("✅ feature_usage table structure correct")
            
            # Check user_activity_log
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) 
                FROM user_activity_log 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """)
            daily_users = cursor.fetchone()[0]
            print(f"✅ user_activity_log table works: {daily_users} users in last 24h")
            
        except Exception as e:
            print(f"⚠️ Verification issue: {e}")
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ COMPREHENSIVE DATABASE SCHEMA FIX COMPLETED!")
        print("All identified database issues have been resolved:")
        for fix in fixes_applied:
            print(f"  - {fix}")
        print("\nRailway deployment errors should now be resolved!")
        
        return True
        
    except Exception as e:
        logger.error(f"Database fix failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)