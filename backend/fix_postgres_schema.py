#!/usr/bin/env python3
"""
Fix PostgreSQL database schema by adding missing columns
"""
import os
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_postgres_connection():
    """Get PostgreSQL connection from environment variables"""
    postgres_url = None
    
    # Try to construct private URL from individual components first
    if all([os.environ.get('PGHOST'), os.environ.get('PGUSER'), 
            os.environ.get('PGPASSWORD'), os.environ.get('PGDATABASE')]):
        host = os.environ.get('PGHOST')
        user = os.environ.get('PGUSER') 
        password = os.environ.get('PGPASSWORD')
        database = os.environ.get('PGDATABASE')
        port = os.environ.get('PGPORT', '5432')
        
        postgres_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    # Fallback to provided URLs
    if not postgres_url:
        postgres_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
    
    if not postgres_url:
        raise Exception("No PostgreSQL connection URL found")
    
    conn = psycopg2.connect(postgres_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn

def fix_users_table():
    """Add missing columns to users table"""
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        # Check current table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        existing_columns = {row[0]: row for row in cursor.fetchall()}
        logger.info(f"Found {len(existing_columns)} existing columns in users table")
        
        # Define all required columns with their specifications
        required_columns = {
            'plan_type': "TEXT DEFAULT 'bronze'",
            'user_plan': "TEXT DEFAULT 'bronze'",
            'trial_active': "INTEGER DEFAULT 0",
            'trial_started_at': "TIMESTAMP",
            'trial_used_permanently': "BOOLEAN DEFAULT FALSE",
            'trial_warning_sent': "INTEGER DEFAULT 0",
            'is_admin': "INTEGER DEFAULT 0",
            'decoder_used': "INTEGER DEFAULT 0",
            'fortune_used': "INTEGER DEFAULT 0",
            'horoscope_used': "INTEGER DEFAULT 0",
            'feature_preview_seen': "INTEGER DEFAULT 0"
        }
        
        # Add missing columns
        for column_name, column_spec in required_columns.items():
            if column_name not in existing_columns:
                logger.info(f"Adding missing column: {column_name}")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_spec}")
                logger.info(f"✅ Added column: {column_name}")
            else:
                logger.info(f"Column already exists: {column_name}")
        
        # Verify the changes
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        final_columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"Final users table has {len(final_columns)} columns: {final_columns}")
        
        conn.close()
        logger.info("✅ Database schema migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔧 Starting PostgreSQL schema migration...")
    success = fix_users_table()
    
    if success:
        logger.info("🎉 Migration completed successfully!")
    else:
        logger.error("💥 Migration failed!")