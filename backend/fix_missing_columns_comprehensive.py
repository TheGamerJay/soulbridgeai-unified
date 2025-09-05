#!/usr/bin/env python3
"""
Fix all missing database columns found in the audit
Critical missing columns that are causing website issues
"""

import logging
from database_utils import get_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_all_missing_columns():
    """Fix all missing columns found in the audit"""
    try:
        db = get_database()
        if not db:
            logger.error("Could not connect to database")
            return False
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        logger.info("Starting comprehensive column fix...")
        
        # Fix users table missing columns
        logger.info("Fixing users table missing columns...")
        
        missing_users_columns = [
            ('user_plan', 'TEXT DEFAULT "bronze"'),
            ('trial_active', 'INTEGER DEFAULT 0'),
            ('password', 'TEXT'),
            ('profile_image_url', 'TEXT'),
            ('trial_used_permanently', 'INTEGER DEFAULT 0'),
            ('artistic_credits', 'INTEGER DEFAULT 0'),
            ('trial_expires_at', 'TEXT'),
        ]
        
        for column_name, column_def in missing_users_columns:
            try:
                if db.use_postgres:
                    # PostgreSQL syntax
                    postgres_def = column_def.replace('INTEGER', 'INTEGER').replace('TEXT', 'VARCHAR(255)')
                    cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {postgres_def}")
                else:
                    # SQLite syntax
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
                logger.info(f"  Added users.{column_name}")
            except Exception as e:
                if "duplicate column name" in str(e) or "already exists" in str(e):
                    logger.info(f"  Column users.{column_name} already exists")
                else:
                    logger.warning(f"  Failed to add users.{column_name}: {e}")
        
        # Update existing credits data
        try:
            cursor.execute("UPDATE users SET artistic_credits = COALESCE(credits, 0) WHERE artistic_credits IS NULL OR artistic_credits = 0")
            logger.info("  Updated artistic_credits from credits column")
        except Exception as e:
            logger.warning(f"  Could not update artistic_credits: {e}")
        
        # Fix community_posts table missing columns
        logger.info("Fixing community_posts table missing columns...")
        
        missing_community_columns = [
            ('user_id', 'INTEGER'),
            ('content', 'TEXT'),
            ('is_anonymous', 'INTEGER DEFAULT 1'),
        ]
        
        for column_name, column_def in missing_community_columns:
            try:
                if db.use_postgres:
                    postgres_def = column_def.replace('INTEGER', 'INTEGER').replace('TEXT', 'TEXT')
                    cursor.execute(f"ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS {column_name} {postgres_def}")
                else:
                    cursor.execute(f"ALTER TABLE community_posts ADD COLUMN {column_name} {column_def}")
                logger.info(f"  Added community_posts.{column_name}")
            except Exception as e:
                if "duplicate column name" in str(e) or "already exists" in str(e):
                    logger.info(f"  Column community_posts.{column_name} already exists")
                else:
                    logger.warning(f"  Failed to add community_posts.{column_name}: {e}")
        
        # Migrate existing community_posts data if needed
        try:
            # Map text -> content if content is empty
            cursor.execute("UPDATE community_posts SET content = text WHERE content IS NULL OR content = ''")
            # Map author_uid -> user_id if user_id is empty (this might need more complex logic)
            cursor.execute("UPDATE community_posts SET user_id = COALESCE(author_uid, 0) WHERE user_id IS NULL OR user_id = 0")
            logger.info("  Migrated existing community_posts data")
        except Exception as e:
            logger.warning(f"  Could not migrate community_posts data: {e}")
        
        # Add any other commonly needed columns that might be missing
        logger.info("Adding other commonly needed columns...")
        
        # Check if user_activity table exists, create if not
        try:
            cursor.execute("SELECT COUNT(*) FROM user_activity LIMIT 1")
        except:
            logger.info("Creating user_activity table...")
            if db.use_postgres:
                cursor.execute("""
                    CREATE TABLE user_activity (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        activity_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        activity_type VARCHAR(100)
                    )
                """)
            else:
                cursor.execute("""
                    CREATE TABLE user_activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        activity_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        activity_type TEXT
                    )
                """)
            logger.info("  Created user_activity table")
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        logger.info("All missing columns have been fixed!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to fix missing columns: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = fix_all_missing_columns()
    if success:
        print("Database column fixes completed successfully!")
    else:
        print("Database column fixes failed!")
        exit(1)