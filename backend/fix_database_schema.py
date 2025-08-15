#!/usr/bin/env python3
"""
Database Schema Fix for SoulBridge AI
Adds missing columns and tables for unified tier system
"""
import os
import sys
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_schema():
    """Add missing columns and tables to the database"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL environment variable not found")
            return False
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        logger.info("🔧 Starting database schema migration...")
        
        # Add missing columns to users table
        missing_columns = [
            ('timezone', 'VARCHAR(50) DEFAULT \'America/New_York\''),
            ('credits', 'INTEGER DEFAULT 0'),
            ('last_credit_reset', 'TIMESTAMP'),
            ('purchased_credits', 'INTEGER DEFAULT 0')
        ]
        
        for column_name, column_def in missing_columns:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
                logger.info(f"✅ Added column: users.{column_name}")
                conn.commit()
            except psycopg2.Error as e:
                if 'already exists' in str(e).lower():
                    logger.info(f"ℹ️  Column users.{column_name} already exists")
                    conn.rollback()
                else:
                    logger.error(f"❌ Error adding column users.{column_name}: {e}")
                    conn.rollback()
        
        # Create feature_usage table
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feature_usage (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    feature VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ Created feature_usage table")
            conn.commit()
        except psycopg2.Error as e:
            logger.error(f"❌ Error creating feature_usage table: {e}")
            conn.rollback()
        
        # Create index for performance
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_feature_usage_user_feature_date ON feature_usage(user_id, feature, DATE(created_at))")
            logger.info("✅ Created feature_usage index")
            conn.commit()
        except psycopg2.Error as e:
            logger.error(f"❌ Error creating index: {e}")
            conn.rollback()
        
        # Check current schema
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('timezone', 'credits', 'last_credit_reset', 'purchased_credits')
            ORDER BY column_name
        """)
        user_columns = cur.fetchall()
        logger.info(f"📊 Users table columns: {user_columns}")
        
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'feature_usage')")
        feature_usage_exists = cur.fetchone()[0]
        logger.info(f"📊 Feature_usage table exists: {feature_usage_exists}")
        
        conn.close()
        logger.info("🎉 Database schema migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"💥 Database schema migration failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_database_schema()
    sys.exit(0 if success else 1)