#!/usr/bin/env python3
"""
Simple Display Name Management - Direct ID to display_name column
"""
import sqlite3
import logging
from database_utils import format_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDisplayNameManager:
    """Simple, direct display name management tied to user ID"""
    
    def __init__(self, db_path='soulbridge.db'):
        self.db_path = db_path
    
    def set_display_name(self, user_id: int, display_name: str) -> bool:
        """Set display name for user ID - direct to column"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Direct update: user_id -> display_name column
            cursor.execute(
                format_query(UPDATE users SET display_name = ? WHERE id = ?"),
                (display_name.strip(), user_id)
            )
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"✅ User ID {user_id} display name set to: '{display_name.strip()}'")
            else:
                logger.error(f"❌ User ID {user_id} not found")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to set display name for user {user_id}: {e}")
            return False
    
    def get_display_name(self, user_id: int) -> str:
        """Get display name for user ID - direct from column"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Direct query: user_id -> display_name column
            cursor.execute(
                format_query(SELECT display_name, email FROM users WHERE id = ?"),
                (user_id,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                display_name = result[0]
                email = result[1]
                
                if display_name and display_name.strip():
                    logger.info(f"✅ User ID {user_id} display name: '{display_name.strip()}'")
                    return display_name.strip()
                else:
                    # Fallback to email prefix if no display name
                    fallback = email.split('@')[0] if email else "User"
                    logger.info(f"📧 User ID {user_id} using email fallback: '{fallback}'")
                    return fallback
            else:
                logger.error(f"❌ User ID {user_id} not found")
                return "User"
                
        except Exception as e:
            logger.error(f"Failed to get display name for user {user_id}: {e}")
            return "User"
    
    def test_display_name_system(self, user_id: int = 104):
        """Test the display name system with a user ID"""
        logger.info(f"🧪 Testing display name system for user ID {user_id}")
        
        # Get current name
        current_name = self.get_display_name(user_id)
        logger.info(f"Current name: {current_name}")
        
        # Set a test name
        test_name = "TestDisplayName123"
        success = self.set_display_name(user_id, test_name)
        
        if success:
            # Verify it was saved
            saved_name = self.get_display_name(user_id)
            if saved_name == test_name:
                logger.info(f"✅ SUCCESS: Display name system working! {user_id} -> '{saved_name}'")
            else:
                logger.error(f"❌ FAILED: Expected '{test_name}', got '{saved_name}'")
        else:
            logger.error("❌ FAILED: Could not set display name")

if __name__ == "__main__":
    manager = SimpleDisplayNameManager()
    manager.test_display_name_system()