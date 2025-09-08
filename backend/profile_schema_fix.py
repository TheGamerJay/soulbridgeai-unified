#!/usr/bin/env python3
"""
Profile Schema Fix - Add missing profile columns and ensure display name works
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_profile_columns():
    """Ensure all profile-related columns exist in users table"""
    try:
        conn = sqlite3.connect('soulbridge.db')
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = {col[1] for col in cursor.fetchall()}
        logger.info(f"Existing columns: {sorted(existing_columns)}")
        
        # Add missing profile columns
        columns_to_add = {
            'profile_image': 'TEXT',
            'profile_image_data': 'TEXT'
        }
        
        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                    logger.info(f"✅ Added column: {column_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to add {column_name}: {e}")
        
        # Verify display_name column is properly configured
        if 'display_name' in existing_columns:
            logger.info("✅ display_name column exists")
            
            # Test display name functionality
            cursor.execute("SELECT id, display_name FROM users LIMIT 5")
            sample_users = cursor.fetchall()
            logger.info(f"Sample display names: {sample_users}")
        else:
            logger.error("❌ display_name column missing!")
        
        conn.commit()
        conn.close()
        logger.info("🎯 Profile schema verification complete")
        
    except Exception as e:
        logger.error(f"Schema fix failed: {e}")

if __name__ == "__main__":
    ensure_profile_columns()