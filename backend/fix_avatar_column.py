#!/usr/bin/env python3
"""
Fix Avatar Column - Add companion_data column to users table if missing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_utils import get_database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_create_companion_column():
    """Check if companion_data column exists, create it if missing"""
    try:
        db = get_database()
        if not db:
            logger.error("❌ Database not available")
            return False
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if column exists
        logger.info("🔍 Checking if companion_data column exists...")
        
        if db.use_postgres:
            # PostgreSQL: Check information_schema
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'companion_data'
            """)
            result = cursor.fetchone()
            
            if not result:
                logger.info("❌ companion_data column missing in PostgreSQL, creating it...")
                cursor.execute("""
                    ALTER TABLE users ADD COLUMN companion_data TEXT
                """)
                conn.commit()
                logger.info("✅ companion_data column created in PostgreSQL!")
            else:
                logger.info("✅ companion_data column already exists in PostgreSQL")
                
        else:
            # SQLite: Use PRAGMA table_info
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]  # col[1] is column name
            
            if 'companion_data' not in column_names:
                logger.info("❌ companion_data column missing in SQLite, creating it...")
                cursor.execute("""
                    ALTER TABLE users ADD COLUMN companion_data TEXT
                """)
                conn.commit()
                logger.info("✅ companion_data column created in SQLite!")
            else:
                logger.info("✅ companion_data column already exists in SQLite")
        
        # Test the column works
        logger.info("🧪 Testing column with a sample query...")
        cursor.execute("SELECT id, companion_data FROM users LIMIT 1")
        test_result = cursor.fetchone()
        
        if test_result:
            logger.info(f"✅ Column test successful: User {test_result[0]} has companion_data: {test_result[1]}")
        else:
            logger.info("⚠️ No users found to test, but column should be working")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to check/create companion_data column: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔧 Starting companion_data column check/creation...")
    success = check_and_create_companion_column()
    
    if success:
        logger.info("✅ Avatar column fix completed successfully!")
        print("\n🎭 Avatar persistence should now work!")
        print("Try setting an avatar and refreshing the page.")
    else:
        logger.error("❌ Failed to fix avatar column")
        print("\n❌ Column fix failed - check the logs above")