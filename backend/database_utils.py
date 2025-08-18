# Database utilities module
# Simple wrapper to provide database access

def get_database():
    """Get database instance from main app"""
    try:
        from app import get_database as app_get_database
        return app_get_database()
    except ImportError:
        # Fallback if app is not available
        return None