"""
Database migration to add ad_free functionality
Adds ad_free boolean column and Stripe integration fields
"""
import sqlite3
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)

def migrate_sqlite(db_path):
    """Add ad_free column to SQLite database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add ad_free column
        cursor.execute('''
            ALTER TABLE users 
            ADD COLUMN ad_free BOOLEAN NOT NULL DEFAULT FALSE
        ''')
        
        # Update existing free users to show ads (ad_free = False)
        cursor.execute('''
            UPDATE users 
            SET ad_free = FALSE 
            WHERE plan_type = 'free' OR user_plan = 'free'
        ''')
        
        # Update existing ad_free plan users 
        cursor.execute('''
            UPDATE users 
            SET ad_free = TRUE 
            WHERE plan_type = 'ad_free' OR user_plan = 'ad_free'
        ''')
        
        # Create index for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_ad_free ON users(ad_free)')
        
        conn.commit()
        conn.close()
        
        logger.info("✅ SQLite migration completed: ad_free column added")
        return True
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            logger.info("⚠️ ad_free column already exists in SQLite")
            return True
        else:
            logger.error(f"❌ SQLite migration failed: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ SQLite migration error: {e}")
        return False

def migrate_postgresql(database_url):
    """Add ad_free column to PostgreSQL database"""
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Add ad_free column
        cursor.execute('''
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS ad_free BOOLEAN NOT NULL DEFAULT FALSE
        ''')
        
        # Update existing free users to show ads (ad_free = False)
        cursor.execute('''
            UPDATE users 
            SET ad_free = FALSE 
            WHERE (plan_type = 'free' OR user_plan = 'free') AND ad_free IS NULL
        ''')
        
        # Update existing ad_free plan users 
        cursor.execute('''
            UPDATE users 
            SET ad_free = TRUE 
            WHERE (plan_type = 'ad_free' OR user_plan = 'ad_free') AND ad_free IS NULL
        ''')
        
        # Create index for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_ad_free ON users(ad_free)')
        
        conn.commit()
        conn.close()
        
        logger.info("✅ PostgreSQL migration completed: ad_free column added")
        return True
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL migration error: {e}")
        return False

def run_migration():
    """Run the appropriate migration based on environment"""
    # Check for PostgreSQL (Railway production)
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgresql'):
        logger.info("🔄 Running PostgreSQL migration...")
        return migrate_postgresql(database_url)
    
    # Fallback to SQLite (local development)
    sqlite_path = os.path.join(os.path.dirname(__file__), '..', 'soulbridge.db')
    if os.path.exists(sqlite_path):
        logger.info("🔄 Running SQLite migration...")
        return migrate_sqlite(sqlite_path)
    
    logger.error("❌ No database found to migrate")
    return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_migration()
    if success:
        print("✅ Migration completed successfully")
    else:
        print("❌ Migration failed")
        exit(1)