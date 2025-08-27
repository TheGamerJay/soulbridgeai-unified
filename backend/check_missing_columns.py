#!/usr/bin/env python3
"""
Check for missing columns in the users table based on the CLAUDE.md schema
"""

import os
import logging
import sqlite3

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_missing_columns():
    """Check for missing columns in users table"""
    db_path = "soulbridge.db"
    
    if not os.path.exists(db_path):
        logger.error(f"❌ Database file {db_path} not found")
        return False
    
    # Expected columns based on CLAUDE.md tier system
    expected_columns = [
        'id', 'email', 'password_hash', 'created_at', 'user_plan',
        'trial_active', 'trial_expires_at', 'trial_credits',
        'credits', 'purchased_credits', 'artistic_time', 'last_credit_reset'
    ]
    
    try:
        logger.info("🔍 Checking users table columns...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current columns
        cursor.execute("PRAGMA table_info(users)")
        current_columns = [row[1] for row in cursor.fetchall()]
        
        logger.info(f"📋 Current columns: {', '.join(current_columns)}")
        
        # Find missing columns
        missing_columns = []
        for col in expected_columns:
            if col not in current_columns:
                missing_columns.append(col)
        
        if missing_columns:
            logger.warning(f"⚠️ Missing columns: {', '.join(missing_columns)}")
            
            # Add missing columns
            column_definitions = {
                'trial_active': 'BOOLEAN DEFAULT FALSE',
                'trial_expires_at': 'TIMESTAMP NULL',
                'trial_credits': 'INTEGER DEFAULT 60',
                'credits': 'INTEGER DEFAULT 0', 
                'purchased_credits': 'INTEGER DEFAULT 0',
                'artistic_time': 'INTEGER DEFAULT 0',
                'last_credit_reset': 'DATE NULL'
            }
            
            for col in missing_columns:
                if col in column_definitions:
                    sql = f"ALTER TABLE users ADD COLUMN {col} {column_definitions[col]}"
                    logger.info(f"🔧 Adding column: {sql}")
                    try:
                        cursor.execute(sql)
                        logger.info(f"  ✅ Added {col}")
                    except Exception as e:
                        logger.error(f"  ❌ Failed to add {col}: {e}")
            
            conn.commit()
            
        else:
            logger.info("✅ All expected columns are present")
        
        # Check sample user data
        cursor.execute("SELECT id, email, user_plan, trial_active, credits, artistic_time FROM users LIMIT 3")
        results = cursor.fetchall()
        logger.info("📊 Sample user data:")
        for row in results:
            logger.info(f"  User {row[0]}: {row[1]} - Plan: {row[2]} - Trial: {row[3]} - Credits: {row[4]} - Artistic: {row[5]}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking columns: {e}")
        return False

if __name__ == "__main__":
    check_missing_columns()