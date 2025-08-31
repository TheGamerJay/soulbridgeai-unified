"""
SoulBridge AI - Database Connection Module
Extracted from app.py monolith for modular architecture
"""
import os
import logging

logger = logging.getLogger(__name__)

def init_database_system(app):
    """Initialize database system for the application"""
    try:
        # This will use the existing database_utils
        from database_utils import get_database
        db = get_database()
        app.database = db
        logger.info("✅ Database system initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

def get_database():
    """Get database connection - placeholder for now, will import from main app"""
    # This will be implemented to work with the main app's database
    # For now, we'll import from the main app context when needed
    try:
        # Try to get from Flask app context first
        from flask import current_app
        if hasattr(current_app, 'database'):
            return current_app.database
    except:
        pass
    
    # Fallback to database_utils
    try:
        from database_utils import get_database as get_db_fallback
        return get_db_fallback()
    except ImportError:
        logger.error("No database connection available")
        return None