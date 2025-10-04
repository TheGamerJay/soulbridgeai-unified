"""
SoulBridge AI - Usage Tracker
Tracks user activity and interactions across all features
Extracted from monolith with improvements
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from database_utils import format_query

logger = logging.getLogger(__name__)

class UsageTracker:
    """Tracks user activity and feature usage across the platform"""
    
    def __init__(self):
        self.tracked_features = {
            'chat', 'voice_chat', 'voice_journaling', 'ai_images', 
            'creative_writing', 'decoder', 'fortune', 'horoscope',
            'meditations', 'relationships', 'mini_studio', 'library'
        }
        
    def track_feature_usage(self, user_id: int, feature_type: str, 
                          session_data: Optional[Dict[str, Any]] = None) -> bool:
        """Track a feature usage event"""
        try:
            if feature_type not in self.tracked_features:
                logger.warning(f"Unknown feature type for tracking: {feature_type}")
                return False
            
            activity_data = {
                'user_id': user_id,
                'feature_type': feature_type,
                'created_at': datetime.now(timezone.utc),
                'session_duration_seconds': session_data.get('duration_seconds', 0) if session_data else 0,
                'metadata': session_data or {}
            }
            
            return self._save_activity_log(activity_data)
            
        except Exception as e:
            logger.error(f"Error tracking feature usage: {e}")
            return False
    
    def track_chat_interaction(self, user_id: int, companion_id: str, 
                             message_length: int, response_time_ms: Optional[int] = None) -> bool:
        """Track chat interaction specifically"""
        try:
            session_data = {
                'companion_id': companion_id,
                'message_length': message_length,
                'response_time_ms': response_time_ms,
                'interaction_type': 'chat_message'
            }
            
            return self.track_feature_usage(user_id, 'chat', session_data)
            
        except Exception as e:
            logger.error(f"Error tracking chat interaction: {e}")
            return False
    
    def track_voice_interaction(self, user_id: int, feature_type: str, 
                              audio_duration_seconds: int, processing_time_ms: Optional[int] = None) -> bool:
        """Track voice-related interactions"""
        try:
            if feature_type not in ['voice_chat', 'voice_journaling']:
                return False
                
            session_data = {
                'audio_duration_seconds': audio_duration_seconds,
                'processing_time_ms': processing_time_ms,
                'interaction_type': 'voice_processing'
            }
            
            return self.track_feature_usage(user_id, feature_type, session_data)
            
        except Exception as e:
            logger.error(f"Error tracking voice interaction: {e}")
            return False
    
    def track_creative_session(self, user_id: int, feature_type: str, 
                             content_length: int, generation_time_ms: Optional[int] = None) -> bool:
        """Track creative feature usage (writing, images, etc.)"""
        try:
            if feature_type not in ['creative_writing', 'ai_images', 'decoder', 'fortune', 'horoscope']:
                return False
                
            session_data = {
                'content_length': content_length,
                'generation_time_ms': generation_time_ms,
                'interaction_type': 'content_generation'
            }
            
            return self.track_feature_usage(user_id, feature_type, session_data)
            
        except Exception as e:
            logger.error(f"Error tracking creative session: {e}")
            return False
    
    def track_meditation_session(self, user_id: int, meditation_id: str, 
                                duration_completed_seconds: int, completed: bool = True) -> bool:
        """Track meditation session"""
        try:
            session_data = {
                'meditation_id': meditation_id,
                'duration_completed_seconds': duration_completed_seconds,
                'completed': completed,
                'interaction_type': 'meditation_session'
            }
            
            return self.track_feature_usage(user_id, 'meditations', session_data)
            
        except Exception as e:
            logger.error(f"Error tracking meditation session: {e}")
            return False
    
    def track_page_view(self, user_id: int, page_name: str, 
                       duration_seconds: Optional[int] = None) -> bool:
        """Track page views and time spent"""
        try:
            session_data = {
                'page_name': page_name,
                'duration_seconds': duration_seconds or 0,
                'interaction_type': 'page_view'
            }
            
            # Map page to feature type
            page_feature_map = {
                'chat': 'chat',
                'voice-chat': 'voice_chat',
                'voice-journaling': 'voice_journaling',
                'ai-images': 'ai_images',
                'creative-writer': 'creative_writing',
                'decoder': 'decoder',
                'fortune': 'fortune',
                'horoscope': 'horoscope',
                'meditations': 'meditations',
                'relationships': 'relationships',
                'mini-studio': 'mini_studio',
                'library': 'library',
                'analytics': 'analytics'
            }
            
            feature_type = page_feature_map.get(page_name, 'other')
            return self.track_feature_usage(user_id, feature_type, session_data)
            
        except Exception as e:
            logger.error(f"Error tracking page view: {e}")
            return False
    
    def track_subscription_event(self, user_id: int, event_type: str, 
                                plan_type: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Track subscription-related events"""
        try:
            session_data = {
                'event_type': event_type,  # upgrade, downgrade, cancel, reactivate
                'plan_type': plan_type,
                'interaction_type': 'subscription_event',
                'metadata': metadata or {}
            }
            
            return self.track_feature_usage(user_id, 'subscription', session_data)
            
        except Exception as e:
            logger.error(f"Error tracking subscription event: {e}")
            return False
    
    def _save_activity_log(self, activity_data: Dict[str, Any]) -> bool:
        """Save activity log to database"""
        try:
            from ..shared.database import get_database
            import json
            
            db = get_database()
            if not db:
                return False
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Insert activity record
            if db.db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO user_activity_log 
                    (user_id, feature_type, created_at, session_duration_seconds, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    activity_data['user_id'],
                    activity_data['feature_type'],
                    activity_data['created_at'],
                    activity_data['session_duration_seconds'],
                    json.dumps(activity_data['metadata'])
                ))
            else:
                cursor.execute(format_query("""
                    INSERT INTO user_activity_log
                    (user_id, feature_type, created_at, session_duration_seconds, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """), (
                    activity_data['user_id'],
                    activity_data['feature_type'],
                    activity_data['created_at'].isoformat(),
                    activity_data['session_duration_seconds'],
                    json.dumps(activity_data['metadata'])
                ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"📊 Tracked {activity_data['feature_type']} usage for user {activity_data['user_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving activity log: {e}")
            return False
    
    def get_user_activity_summary(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """Get user's recent activity summary"""
        try:
            from ..shared.database import get_database
            from datetime import timedelta
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT
                        feature_type,
                        COUNT(*) as usage_count,
                        SUM(session_duration_seconds) as total_time_seconds,
                        MAX(created_at) as last_used
                    FROM user_activity_log
                    WHERE user_id = %s AND created_at >= %s
                    GROUP BY feature_type
                    ORDER BY usage_count DESC
                """, (user_id, start_date))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        feature_type,
                        COUNT(*) as usage_count,
                        SUM(session_duration_seconds) as total_time_seconds,
                        MAX(created_at) as last_used
                    FROM user_activity_log 
                    WHERE user_id = ? AND created_at >= ?
                    GROUP BY feature_type
                    ORDER BY usage_count DESC
                """), (user_id, start_date.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            summary = {
                'period_days': days,
                'total_features_used': len(rows),
                'features': []
            }
            
            for row in rows:
                feature_type, usage_count, total_time, last_used = row
                
                summary['features'].append({
                    'feature': feature_type,
                    'usage_count': usage_count,
                    'total_time_seconds': total_time or 0,
                    'total_time_minutes': round((total_time or 0) / 60, 1),
                    'last_used': str(last_used) if last_used else None,
                    'avg_session_time': round((total_time or 0) / usage_count, 1) if usage_count > 0 else 0
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting activity summary: {e}")
            return {}
    
    def get_feature_popularity(self, days: int = 30, limit: int = 10) -> Dict[str, Any]:
        """Get overall feature popularity across all users"""
        try:
            from ..shared.database import get_database
            from datetime import timedelta
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT
                        feature_type,
                        COUNT(*) as total_usage,
                        COUNT(DISTINCT user_id) as unique_users,
                        AVG(session_duration_seconds) as avg_session_duration
                    FROM user_activity_log
                    WHERE created_at >= %s
                    GROUP BY feature_type
                    ORDER BY total_usage DESC
                    LIMIT %s
                """, (start_date, limit))
            else:
                cursor.execute(format_query("""
                    SELECT
                        feature_type,
                        COUNT(*) as total_usage,
                        COUNT(DISTINCT user_id) as unique_users,
                        AVG(session_duration_seconds) as avg_session_duration
                    FROM user_activity_log
                    WHERE created_at >= ?
                    GROUP BY feature_type
                    ORDER BY total_usage DESC
                    LIMIT ?
                """), (start_date.isoformat(), limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            popularity = {
                'period_days': days,
                'features': []
            }
            
            total_usage = sum(row[1] for row in rows) if rows else 1
            
            for row in rows:
                feature_type, usage_count, unique_users, avg_duration = row
                
                popularity['features'].append({
                    'feature': feature_type,
                    'total_usage': usage_count,
                    'unique_users': unique_users,
                    'avg_session_duration': round(avg_duration or 0, 1),
                    'percentage_of_total': round((usage_count / total_usage) * 100, 1),
                    'usage_per_user': round(usage_count / max(unique_users, 1), 1)
                })
            
            return popularity
            
        except Exception as e:
            logger.error(f"Error getting feature popularity: {e}")
            return {}
    
    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """Clean up old activity logs"""
        try:
            from ..shared.database import get_database
            from datetime import timedelta
            
            db = get_database()
            if not db:
                return 0
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    DELETE FROM user_activity_log
                    WHERE created_at < %s
                """, (cutoff_date,))
            else:
                cursor.execute(format_query("""
                    DELETE FROM user_activity_log
                    WHERE created_at < ?
                """), (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"🧹 Cleaned up {deleted_count} old activity log entries (older than {days_to_keep} days)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            return 0