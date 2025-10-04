"""
SoulBridge AI - Companion Utilities
Extracted from app.py monolith for modular architecture
"""
import logging
from datetime import datetime, date
from ..shared.database import get_database
from database_utils import format_query

logger = logging.getLogger(__name__)

def get_companion_selections_today() -> int:
    """Get number of companion selections made today"""
    try:
        # This would query database for today's companion selections
        # Placeholder implementation for now
        logger.info("Getting companion selections for today")
        return 0
        
    except Exception as e:
        logger.error(f"Error getting companion selections: {e}")
        return 0

def track_companion_selection(user_id: int, companion_id: str):
    """Track when a user selects a companion"""
    try:
        db = get_database()
        if not db:
            logger.warning("No database connection for companion selection tracking")
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Record companion selection
        if db.use_postgres:
            cursor.execute("""
                INSERT INTO companion_selections (user_id, companion_id, selected_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    companion_id = EXCLUDED.companion_id,
                    selected_at = EXCLUDED.selected_at
            """, (user_id, companion_id, datetime.now()))
        else:
            cursor.execute(format_query("""
                INSERT OR REPLACE INTO companion_selections (user_id, companion_id, selected_at)
                VALUES (?, ?, ?)
            """), (user_id, companion_id, datetime.now()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Tracked companion selection: user {user_id} selected {companion_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error tracking companion selection: {e}")
        return False

def get_user_companion_history(user_id: int, limit: int = 10) -> list:
    """Get user's companion selection history"""
    try:
        db = get_database()
        if not db:
            return []
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgres:
            cursor.execute("""
                SELECT companion_id, selected_at
                FROM companion_selections
                WHERE user_id = %s
                ORDER BY selected_at DESC
                LIMIT %s
            """, (user_id, limit))
        else:
            cursor.execute(format_query("""
                SELECT companion_id, selected_at
                FROM companion_selections
                WHERE user_id = ?
                ORDER BY selected_at DESC
                LIMIT ?
            """), (user_id, limit))
        
        history = cursor.fetchall()
        conn.close()
        
        return [{"companion_id": row[0], "selected_at": row[1]} for row in history]
        
    except Exception as e:
        logger.error(f"Error getting companion history: {e}")
        return []

def get_companion_popularity_stats() -> dict:
    """Get companion popularity statistics"""
    try:
        db = get_database()
        if not db:
            return {}
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get selection counts per companion
        if db.use_postgres:
            cursor.execute("""
                SELECT companion_id, COUNT(*) as selection_count
                FROM companion_selections
                WHERE selected_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY companion_id
                ORDER BY selection_count DESC
            """)
        else:
            cursor.execute("""
                SELECT companion_id, COUNT(*) as selection_count
                FROM companion_selections
                WHERE selected_at >= date('now', '-30 days')
                GROUP BY companion_id
                ORDER BY selection_count DESC
            """)
        
        stats = cursor.fetchall()
        conn.close()
        
        return {row[0]: row[1] for row in stats}
        
    except Exception as e:
        logger.error(f"Error getting companion popularity: {e}")
        return {}

def restore_companion_data(user_id: int) -> dict:
    """Restore user's companion data from database"""
    try:
        if not user_id:
            return {}
        
        # Get user's last selected companion
        history = get_user_companion_history(user_id, 1)
        companion_data = {}
        
        if history:
            companion_data['last_selected'] = history[0]['companion_id']
            companion_data['last_selected_at'] = history[0]['selected_at']
            
        logger.info(f"Restored companion data for user {user_id}: {companion_data}")
        return companion_data
        
    except Exception as e:
        logger.error(f"Error restoring companion data for user {user_id}: {e}")
        return {}

def get_companion_usage_stats(companion_id: str, days: int = 30) -> dict:
    """Get usage statistics for a specific companion"""
    try:
        db = get_database()
        if not db:
            return {"selections": 0, "unique_users": 0}
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get selection count and unique users for this companion
        if db.use_postgres:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_selections,
                    COUNT(DISTINCT user_id) as unique_users
                FROM companion_selections
                WHERE companion_id = %s 
                AND selected_at >= CURRENT_DATE - INTERVAL '%s days'
            """), (companion_id, days))
        else:
            cursor.execute(format_query("""
                SELECT 
                    COUNT(*) as total_selections,
                    COUNT(DISTINCT user_id) as unique_users
                FROM companion_selections
                WHERE companion_id = ? 
                AND selected_at >= date('now', '-%s days')
            """), (companion_id, days))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "selections": result[0],
                "unique_users": result[1],
                "companion_id": companion_id,
                "period_days": days
            }
        else:
            return {"selections": 0, "unique_users": 0}
        
    except Exception as e:
        logger.error(f"Error getting companion usage stats: {e}")
        return {"selections": 0, "unique_users": 0}