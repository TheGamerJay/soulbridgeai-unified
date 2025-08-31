"""
SoulBridge AI - Admin Utilities
Extracted from app.py monolith using strategic bulk extraction
"""
import logging
from ..shared.database import get_database

logger = logging.getLogger(__name__)

def get_total_users() -> int:
    """Get total number of users in the system"""
    try:
        db = get_database()
        if not db:
            return 0
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
        
    except Exception as e:
        logger.error(f"Error getting total users: {e}")
        return 0

def get_active_sessions_count() -> int:
    """Get count of active user sessions"""
    try:
        # This would count active sessions from session storage
        # Placeholder implementation for now
        return 0
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        return 0

def get_active_users_count() -> int:
    """Get count of users active in last 24 hours"""
    try:
        db = get_database()
        if not db:
            return 0
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgres:
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) 
                FROM user_activity 
                WHERE activity_time >= NOW() - INTERVAL '24 hours'
            """)
        else:
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) 
                FROM user_activity 
                WHERE activity_time >= datetime('now', '-24 hours')
            """)
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
        
    except Exception as e:
        logger.error(f"Error getting active users: {e}")
        return 0

def check_database_health() -> dict:
    """Check database connection and basic health"""
    try:
        db = get_database()
        if not db:
            return {"status": "ERROR", "message": "No database connection"}
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {"status": "OK", "message": "Database connection healthy"}
        else:
            return {"status": "WARNING", "message": "Database query failed"}
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "ERROR", "message": f"Database error: {str(e)[:100]}"}

def get_premium_conversions() -> int:
    """Get number of premium conversions"""
    try:
        db = get_database()
        if not db:
            return 0
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Count users who upgraded from bronze to silver/gold
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE user_plan IN ('silver', 'gold')
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
        
    except Exception as e:
        logger.error(f"Error getting premium conversions: {e}")
        return 0

def get_trial_statistics() -> dict:
    """Get comprehensive trial system statistics"""
    try:
        db = get_database()
        if not db:
            return {}
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Active trials
        if db.use_postgres:
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE trial_active = TRUE 
                AND trial_expires_at > NOW()
            """)
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE trial_active = 1 
                AND trial_expires_at > datetime('now')
            """)
        
        stats['active_trials'] = cursor.fetchone()[0]
        
        # Expired trials
        if db.use_postgres:
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE trial_active = FALSE 
                AND trial_expires_at IS NOT NULL
            """)
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE trial_active = 0 
                AND trial_expires_at IS NOT NULL
            """)
        
        stats['expired_trials'] = cursor.fetchone()[0]
        
        # Total trial users
        cursor.execute("SELECT COUNT(*) FROM users WHERE trial_expires_at IS NOT NULL")
        stats['total_trial_users'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting trial statistics: {e}")
        return {}

def get_system_stats() -> dict:
    """Get comprehensive system statistics for admin dashboard"""
    try:
        return {
            'total_users': get_total_users(),
            'active_sessions': get_active_sessions_count(),
            'active_users': get_active_users_count(),
            'database_status': check_database_health(),
            'premium_conversions': get_premium_conversions(),
            'trial_stats': get_trial_statistics()
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {}

def get_user_management_stats() -> dict:
    """Get user management statistics"""
    try:
        db = get_database()
        if not db:
            return {}
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Users by plan type
        cursor.execute("""
            SELECT user_plan, COUNT(*) 
            FROM users 
            GROUP BY user_plan
        """)
        
        plan_counts = dict(cursor.fetchall())
        stats['users_by_plan'] = plan_counts
        
        # Recent registrations (last 7 days)
        if db.use_postgres:
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """)
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE created_at >= date('now', '-7 days')
            """)
        
        stats['recent_registrations'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting user management stats: {e}")
        return {}