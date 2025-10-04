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


def get_db_connection():
    """Get database connection for direct SQL queries"""
    db = get_database()
    if db:
        return db.get_connection()
    else:
        raise Exception("Database not initialized")


def is_postgres():
    """Check if we're using PostgreSQL"""
    db = get_database()
    if db and hasattr(db, 'use_postgres'):
        return db.use_postgres
    return False


def get_placeholder():
    """Get the correct parameter placeholder for current database"""
    return "%s" if is_postgres() else "?"


def format_query(query):
    """Convert SQLite ? placeholders to PostgreSQL %s if needed"""
    if is_postgres():
        # Replace all ? with %s for PostgreSQL
        return query.replace('?', '%s')
    return query