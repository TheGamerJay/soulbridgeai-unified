"""
SoulBridge AI - Analytics Service
Core analytics functionality for usage tracking and insights
Extracted from routes_analytics.py with improvements
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Main analytics service for user insights and usage tracking"""
    
    def __init__(self):
        self.supported_periods = [1, 7, 14, 30, 60, 90]
        
    def get_user_usage_analytics(self, user_id: int, period_days: int = 7, 
                               include_details: bool = False) -> Dict[str, Any]:
        """Get comprehensive usage analytics for a user"""
        try:
            # Validate period
            if period_days not in self.supported_periods:
                period_days = min(self.supported_periods, key=lambda x: abs(x - period_days))
            
            analytics = {
                "user_id": user_id,
                "period_days": period_days,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "overview": self._get_usage_overview(user_id, period_days),
                "features": self._get_feature_usage(user_id, period_days),
                "companions": self._get_companion_usage(user_id, period_days),
                "trends": self._get_usage_trends(user_id, period_days) if include_details else None
            }
            
            if include_details:
                analytics["detailed_breakdown"] = self._get_detailed_breakdown(user_id, period_days)
                analytics["activity_heatmap"] = self._get_activity_heatmap(user_id, period_days)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return self._get_fallback_analytics(user_id, period_days)
    
    def _get_usage_overview(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Get high-level usage overview"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now(timezone.utc) - timedelta(days=period_days)
            
            # Get overall activity metrics
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT DATE(created_at)) as active_days,
                        COUNT(*) as total_interactions,
                        COUNT(DISTINCT feature_type) as features_used
                    FROM user_activity_log 
                    WHERE user_id = %s AND created_at >= %s
                """, (user_id, start_date))
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT DATE(created_at)) as active_days,
                        COUNT(*) as total_interactions,
                        COUNT(DISTINCT feature_type) as features_used
                    FROM user_activity_log 
                    WHERE user_id = ? AND created_at >= ?
                """, (user_id, start_date.isoformat()))
            
            row = cursor.fetchone()
            
            if row:
                active_days, total_interactions, features_used = row
                
                overview = {
                    "active_days": active_days or 0,
                    "total_interactions": total_interactions or 0,
                    "features_used": features_used or 0,
                    "avg_interactions_per_day": round((total_interactions or 0) / max(active_days or 1, 1), 1),
                    "engagement_score": self._calculate_engagement_score(active_days, total_interactions, period_days)
                }
            else:
                overview = {
                    "active_days": 0,
                    "total_interactions": 0,
                    "features_used": 0,
                    "avg_interactions_per_day": 0,
                    "engagement_score": 0
                }
            
            conn.close()
            return overview
            
        except Exception as e:
            logger.error(f"Error getting usage overview: {e}")
            return {}
    
    def _get_feature_usage(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Get feature usage breakdown"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now(timezone.utc) - timedelta(days=period_days)
            
            # Get feature usage stats
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        feature_type,
                        COUNT(*) as usage_count,
                        COUNT(DISTINCT DATE(created_at)) as days_used,
                        AVG(session_duration_seconds) as avg_session_duration
                    FROM user_activity_log 
                    WHERE user_id = %s AND created_at >= %s
                    GROUP BY feature_type
                    ORDER BY usage_count DESC
                """, (user_id, start_date))
            else:
                cursor.execute("""
                    SELECT 
                        feature_type,
                        COUNT(*) as usage_count,
                        COUNT(DISTINCT DATE(created_at)) as days_used,
                        AVG(session_duration_seconds) as avg_session_duration
                    FROM user_activity_log 
                    WHERE user_id = ? AND created_at >= ?
                    GROUP BY feature_type
                    ORDER BY usage_count DESC
                """, (user_id, start_date.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            features = []
            total_usage = sum(row[1] for row in rows) if rows else 1
            
            for row in rows:
                feature_type, usage_count, days_used, avg_duration = row
                
                features.append({
                    "feature": feature_type,
                    "usage_count": usage_count,
                    "days_used": days_used,
                    "avg_session_duration": round(avg_duration or 0, 1),
                    "percentage_of_total": round((usage_count / total_usage) * 100, 1)
                })
            
            return {
                "total_features_used": len(features),
                "top_features": features[:5],
                "all_features": features
            }
            
        except Exception as e:
            logger.error(f"Error getting feature usage: {e}")
            return {}
    
    def _get_companion_usage(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Get companion interaction analytics"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now(timezone.utc) - timedelta(days=period_days)
            
            # Get companion chat stats
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        companion_id,
                        COUNT(*) as message_count,
                        COUNT(DISTINCT DATE(created_at)) as chat_days,
                        AVG(LENGTH(user_message)) as avg_message_length
                    FROM chat_conversations 
                    WHERE user_id = %s AND created_at >= %s
                    GROUP BY companion_id
                    ORDER BY message_count DESC
                """, (user_id, start_date))
            else:
                cursor.execute("""
                    SELECT 
                        companion_id,
                        COUNT(*) as message_count,
                        COUNT(DISTINCT DATE(created_at)) as chat_days,
                        AVG(LENGTH(user_message)) as avg_message_length
                    FROM chat_conversations 
                    WHERE user_id = ? AND created_at >= ?
                    GROUP BY companion_id
                    ORDER BY message_count DESC
                """, (user_id, start_date.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            companions = []
            total_messages = sum(row[1] for row in rows) if rows else 1
            
            for row in rows:
                companion_id, message_count, chat_days, avg_length = row
                
                # Get companion details
                from ..companions.companion_data import get_companion_by_id
                companion = get_companion_by_id(companion_id)
                
                companions.append({
                    "companion_id": companion_id,
                    "companion_name": companion.get('name', companion_id) if companion else companion_id,
                    "message_count": message_count,
                    "chat_days": chat_days,
                    "avg_message_length": round(avg_length or 0, 1),
                    "percentage_of_conversations": round((message_count / total_messages) * 100, 1)
                })
            
            return {
                "total_companions_used": len(companions),
                "total_messages": total_messages,
                "most_used_companion": companions[0] if companions else None,
                "companions": companions
            }
            
        except Exception as e:
            logger.error(f"Error getting companion usage: {e}")
            return {}
    
    def _get_usage_trends(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Get usage trends over time"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now(timezone.utc) - timedelta(days=period_days)
            
            # Get daily activity trends
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as activity_date,
                        COUNT(*) as interactions,
                        COUNT(DISTINCT feature_type) as features_used
                    FROM user_activity_log 
                    WHERE user_id = %s AND created_at >= %s
                    GROUP BY DATE(created_at)
                    ORDER BY activity_date
                """, (user_id, start_date))
            else:
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as activity_date,
                        COUNT(*) as interactions,
                        COUNT(DISTINCT feature_type) as features_used
                    FROM user_activity_log 
                    WHERE user_id = ? AND created_at >= ?
                    GROUP BY DATE(created_at)
                    ORDER BY activity_date
                """, (user_id, start_date.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            daily_trends = []
            for row in rows:
                activity_date, interactions, features_used = row
                daily_trends.append({
                    "date": str(activity_date),
                    "interactions": interactions,
                    "features_used": features_used
                })
            
            # Calculate trend metrics
            if len(daily_trends) >= 2:
                recent_avg = sum(d['interactions'] for d in daily_trends[-3:]) / min(len(daily_trends), 3)
                early_avg = sum(d['interactions'] for d in daily_trends[:3]) / min(len(daily_trends), 3)
                trend_direction = "increasing" if recent_avg > early_avg else "decreasing" if recent_avg < early_avg else "stable"
            else:
                trend_direction = "insufficient_data"
            
            return {
                "daily_activity": daily_trends,
                "trend_direction": trend_direction,
                "peak_activity_day": max(daily_trends, key=lambda x: x['interactions']) if daily_trends else None,
                "most_diverse_day": max(daily_trends, key=lambda x: x['features_used']) if daily_trends else None
            }
            
        except Exception as e:
            logger.error(f"Error getting usage trends: {e}")
            return {}
    
    def _get_detailed_breakdown(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Get detailed usage breakdown"""
        try:
            # This would include more granular analytics like:
            # - Hour-by-hour usage patterns
            # - Feature transition flows
            # - Session depth analysis
            # - Response time metrics
            
            return {
                "note": "Detailed breakdown analysis",
                "hourly_patterns": self._get_hourly_patterns(user_id, period_days),
                "session_analysis": self._get_session_analysis(user_id, period_days)
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed breakdown: {e}")
            return {}
    
    def _get_activity_heatmap(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Generate activity heatmap data"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now(timezone.utc) - timedelta(days=period_days)
            
            # Get activity by hour and day of week
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        EXTRACT(DOW FROM created_at) as day_of_week,
                        EXTRACT(HOUR FROM created_at) as hour_of_day,
                        COUNT(*) as activity_count
                    FROM user_activity_log 
                    WHERE user_id = %s AND created_at >= %s
                    GROUP BY EXTRACT(DOW FROM created_at), EXTRACT(HOUR FROM created_at)
                    ORDER BY day_of_week, hour_of_day
                """, (user_id, start_date))
            else:
                cursor.execute("""
                    SELECT 
                        strftime('%w', created_at) as day_of_week,
                        strftime('%H', created_at) as hour_of_day,
                        COUNT(*) as activity_count
                    FROM user_activity_log 
                    WHERE user_id = ? AND created_at >= ?
                    GROUP BY strftime('%w', created_at), strftime('%H', created_at)
                    ORDER BY day_of_week, hour_of_day
                """, (user_id, start_date.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            heatmap_data = []
            for row in rows:
                day_of_week, hour_of_day, activity_count = row
                heatmap_data.append({
                    "day": int(day_of_week),
                    "hour": int(hour_of_day),
                    "activity": activity_count
                })
            
            return {
                "heatmap_data": heatmap_data,
                "total_data_points": len(heatmap_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting activity heatmap: {e}")
            return {}
    
    def _get_hourly_patterns(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Get hourly usage patterns"""
        try:
            # Implementation for hourly pattern analysis
            return {"note": "Hourly patterns analysis"}
        except Exception as e:
            logger.error(f"Error getting hourly patterns: {e}")
            return {}
    
    def _get_session_analysis(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Get session depth and flow analysis"""
        try:
            # Implementation for session analysis
            return {"note": "Session analysis"}
        except Exception as e:
            logger.error(f"Error getting session analysis: {e}")
            return {}
    
    def _calculate_engagement_score(self, active_days: int, total_interactions: int, period_days: int) -> float:
        """Calculate user engagement score (0-100)"""
        try:
            if period_days == 0 or active_days == 0:
                return 0.0
            
            # Engagement factors
            consistency_score = (active_days / period_days) * 40  # Up to 40 points for consistency
            activity_score = min((total_interactions / period_days) * 20, 40)  # Up to 40 points for activity
            frequency_score = min(active_days * 2, 20)  # Up to 20 points for frequency
            
            total_score = consistency_score + activity_score + frequency_score
            return round(min(total_score, 100), 1)
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.0
    
    def _get_fallback_analytics(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Fallback analytics when database is unavailable"""
        return {
            "user_id": user_id,
            "period_days": period_days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overview": {
                "active_days": 0,
                "total_interactions": 0,
                "features_used": 0,
                "avg_interactions_per_day": 0,
                "engagement_score": 0
            },
            "features": {"total_features_used": 0, "top_features": [], "all_features": []},
            "companions": {"total_companions_used": 0, "total_messages": 0, "companions": []},
            "note": "Analytics temporarily unavailable - showing default values"
        }