#!/usr/bin/env python3
"""
Fix missing artistic_time column in users table
"""

import os
import logging
import sqlite3

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_artistic_time_column():
    """Add the artistic_time column to users table if it doesn't exist"""
    db_path = "soulbridge.db"
    
    if not os.path.exists(db_path):
        logger.error(f"❌ Database file {db_path} not found")
        return False
    
    try:
        logger.info("🔧 Adding artistic_time column to users table...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'artistic_time' in columns:
            logger.info("✅ artistic_time column already exists")
            conn.close()
            return True
        
        # Add the column
        cursor.execute("ALTER TABLE users ADD COLUMN artistic_time INTEGER DEFAULT 0")
        
        # Commit changes
        conn.commit()
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'artistic_time' in columns:
            logger.info("✅ artistic_time column added successfully")
            
            # Set default value for existing users (Silver = 200, Gold = 500, Bronze = 0)
            cursor.execute("""
                UPDATE users 
                SET artistic_time = CASE 
                    WHEN user_plan = 'silver' THEN 200
                    WHEN user_plan = 'gold' THEN 500
                    ELSE 0
                END
                WHERE artistic_time IS NULL
            """)
            conn.commit()
            
            # Show current user data
            cursor.execute("SELECT id, email, user_plan, artistic_time FROM users LIMIT 5")
            results = cursor.fetchall()
            logger.info("📊 Sample user data:")
            for row in results:
                logger.info(f"  User {row[0]}: {row[1]} - Plan: {row[2]} - Artistic Time: {row[3]}")
            
            conn.close()
            return True
        else:
            logger.error("❌ Failed to add artistic_time column")
            conn.close()
            return False
            
    except Exception as e:
        logger.error(f"❌ Error adding artistic_time column: {e}")
        return False

if __name__ == "__main__":
    add_artistic_time_column()