# Database utilities module
# Standalone database access to avoid circular imports

import os
import logging

logger = logging.getLogger(__name__)
_db_instance = None

def get_database():
    """Get database instance without importing app.py"""
    global _db_instance
    
    if _db_instance is None:
        try:
            # Import Database class directly to avoid circular import
            from auth import Database
            _db_instance = Database()
            # Test connection
            temp_conn = _db_instance.get_connection()
            temp_conn.close()
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            _db_instance = None
    
    return _db_instance