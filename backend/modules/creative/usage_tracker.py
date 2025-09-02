"""
SoulBridge AI - Creative Features Usage Tracker
Extracted from app.py monolith using strategic bulk extraction
"""
import logging
from datetime import datetime, date
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    # Fall back to built-in zoneinfo (Python 3.9+)
    try:
        from zoneinfo import ZoneInfo
        PYTZ_AVAILABLE = False
    except ImportError:
        # Ultimate fallback - use UTC
        import datetime as dt
        PYTZ_AVAILABLE = False
        ZoneInfo = None

from ..shared.database import get_database
from .features_config import get_feature_limit

logger = logging.getLogger(__name__)

class CreativeUsageTracker:
    """Tracks usage of creative features with daily limits"""
    
    def __init__(self):
        self.db = get_database()
        if PYTZ_AVAILABLE:
            self.est_tz = pytz.timezone('US/Eastern')
        elif ZoneInfo:
            try:
                self.est_tz = ZoneInfo('US/Eastern')
            except Exception:
                # Fallback if timezone not found
                self.est_tz = None
        else:
            # Fallback to UTC
            self.est_tz = None
    
    def get_est_date(self) -> date:
        """Get current date in Eastern Time (resets at 12 EST)"""
        if PYTZ_AVAILABLE:
            utc_now = datetime.now(pytz.UTC)
            est_now = utc_now.astimezone(self.est_tz)
            return est_now.date()
        elif ZoneInfo and self.est_tz:
            from datetime import timezone
            utc_now = datetime.now(timezone.utc)
            est_now = utc_now.astimezone(self.est_tz)
            return est_now.date()
        else:
            # Fallback to UTC date
            logger.warning("Using UTC date as fallback - Eastern Time zone not available")
            return datetime.utcnow().date()
    
    def get_usage_today(self, user_id: int, feature: str) -> int:
        """Get user's usage count for a feature today"""
        try:
            if not self.db:
                return 0
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            today = self.get_est_date()
            
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT usage_count FROM feature_usage
                    WHERE user_id = %s AND feature_name = %s AND usage_date = %s
                """, (user_id, feature, today))
            else:
                cursor.execute("""
                    SELECT usage_count FROM feature_usage
                    WHERE user_id = ? AND feature_name = ? AND usage_date = ?
                """, (user_id, feature, today))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting usage for {feature}: {e}")
            return 0
    
    def can_use_feature(self, user_id: int, feature: str, user_plan: str, trial_active: bool) -> bool:
        """Check if user can use a feature (within daily limits)"""
        try:
            daily_limit = get_feature_limit(feature, user_plan, trial_active)
            
            # Unlimited access
            if daily_limit >= 999:
                return True
            
            usage_today = self.get_usage_today(user_id, feature)
            return usage_today < daily_limit
            
        except Exception as e:
            logger.error(f"Error checking feature access for {feature}: {e}")
            return False
    
    def record_usage(self, user_id: int, feature: str) -> bool:
        """Record usage of a feature"""
        try:
            if not self.db:
                return False
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            today = self.get_est_date()
            now = datetime.now()
            
            # Check if record exists for today
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT usage_count FROM feature_usage
                    WHERE user_id = %s AND feature_name = %s AND usage_date = %s
                """, (user_id, feature, today))
            else:
                cursor.execute("""
                    SELECT usage_count FROM feature_usage
                    WHERE user_id = ? AND feature_name = ? AND usage_date = ?
                """, (user_id, feature, today))
            
            result = cursor.fetchone()
            
            if result:
                # Update existing record
                new_count = result[0] + 1
                if self.db.use_postgres:
                    cursor.execute("""
                        UPDATE feature_usage 
                        SET usage_count = %s, last_used_at = %s
                        WHERE user_id = %s AND feature_name = %s AND usage_date = %s
                    """, (new_count, now, user_id, feature, today))
                else:
                    cursor.execute("""
                        UPDATE feature_usage 
                        SET usage_count = ?, last_used_at = ?
                        WHERE user_id = ? AND feature_name = ? AND usage_date = ?
                    """, (new_count, now, user_id, feature, today))
            else:
                # Create new record
                if self.db.use_postgres:
                    cursor.execute("""
                        INSERT INTO feature_usage (user_id, feature_name, usage_date, usage_count, last_used_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, feature, today, 1, now))
                else:
                    cursor.execute("""
                        INSERT INTO feature_usage (user_id, feature_name, usage_date, usage_count, last_used_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, feature, today, 1, now))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded usage: user {user_id} used {feature}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording usage for {feature}: {e}")
            return False
    
    def get_usage_stats(self, user_id: int, days: int = 7) -> dict:
        """Get usage statistics for a user over specified days"""
        try:
            if not self.db:
                return {}
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get usage stats for last N days
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT feature_name, SUM(usage_count) as total_usage
                    FROM feature_usage
                    WHERE user_id = %s AND usage_date >= CURRENT_DATE - INTERVAL '%s days'
                    GROUP BY feature_name
                """, (user_id, days))
            else:
                cursor.execute("""
                    SELECT feature_name, SUM(usage_count) as total_usage
                    FROM feature_usage
                    WHERE user_id = ? AND usage_date >= date('now', '-%s days')
                    GROUP BY feature_name
                """, (user_id, days))
            
            stats = {}
            for row in cursor.fetchall():
                feature_name, total_usage = row
                stats[feature_name] = total_usage
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return {}
    
    def reset_usage_for_user(self, user_id: int, feature: str = None) -> bool:
        """Reset usage for a user (admin function)"""
        try:
            if not self.db:
                return False
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            today = self.get_est_date()
            
            if feature:
                # Reset specific feature
                if self.db.use_postgres:
                    cursor.execute("""
                        DELETE FROM feature_usage
                        WHERE user_id = %s AND feature_name = %s AND usage_date = %s
                    """, (user_id, feature, today))
                else:
                    cursor.execute("""
                        DELETE FROM feature_usage
                        WHERE user_id = ? AND feature_name = ? AND usage_date = ?
                    """, (user_id, feature, today))
            else:
                # Reset all features for today
                if self.db.use_postgres:
                    cursor.execute("""
                        DELETE FROM feature_usage
                        WHERE user_id = %s AND usage_date = %s
                    """, (user_id, today))
                else:
                    cursor.execute("""
                        DELETE FROM feature_usage
                        WHERE user_id = ? AND usage_date = ?
                    """, (user_id, today))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Reset usage for user {user_id}, feature: {feature or 'all'}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting usage: {e}")
            return False
    
    def get_all_usage_today(self, user_id: int) -> dict:
        """Get usage for all features today"""
        try:
            from .features_config import get_all_creative_features
            
            usage = {}
            for feature in get_all_creative_features():
                usage[feature] = self.get_usage_today(user_id, feature)
            
            return usage
            
        except Exception as e:
            logger.error(f"Error getting all usage: {e}")
            return {}
    
    def cleanup_old_usage(self, days_to_keep: int = 30) -> int:
        """Clean up old usage records (maintenance function)"""
        try:
            if not self.db:
                return 0
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Delete records older than specified days
            if self.db.use_postgres:
                cursor.execute("""
                    DELETE FROM feature_usage
                    WHERE usage_date < CURRENT_DATE - INTERVAL '%s days'
                """, (days_to_keep,))
            else:
                cursor.execute("""
                    DELETE FROM feature_usage
                    WHERE usage_date < date('now', '-%s days')
                """, (days_to_keep,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} old usage records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old usage: {e}")
            return 0