"""
SoulBridge AI - Dashboard Service
Analytics dashboard data aggregation and visualization support
Extracted from routes_analytics.py with improvements
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database_utils import format_query

logger = logging.getLogger(__name__)

class DashboardService:
    """Service for analytics dashboard data and insights"""
    
    def __init__(self):
        self.default_periods = [7, 30, 90]
        
    def get_dashboard_data(self, user_id: int, period_days: int = 7) -> Dict[str, Any]:
        """Get comprehensive dashboard data for user"""
        try:
            dashboard = {
                "user_id": user_id,
                "period_days": period_days,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "overview": self._get_dashboard_overview(user_id, period_days),
                "usage_metrics": self._get_usage_metrics(user_id, period_days),
                "engagement_insights": self._get_engagement_insights(user_id, period_days),
                "feature_breakdown": self._get_feature_breakdown(user_id, period_days),
                "companion_analytics": self._get_companion_analytics(user_id, period_days),
                "recommendations": self._get_personalized_recommendations(user_id, period_days)
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return self._get_fallback_dashboard(user_id, period_days)
    
    def _get_dashboard_overview(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Get high-level dashboard overview"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now(timezone.utc) - timedelta(days=period_days)
            
            # Get key metrics
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_interactions,
                        COUNT(DISTINCT feature_type) as features_used,
                        COUNT(DISTINCT DATE(created_at)) as active_days,
                        SUM(session_duration_seconds) as total_time_seconds
                    FROM user_activity_log 
                    WHERE user_id = %s AND created_at >= %s
                """, (user_id, start_date))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        COUNT(*) as total_interactions,
                        COUNT(DISTINCT feature_type) as features_used,
                        COUNT(DISTINCT DATE(created_at)) as active_days,
                        SUM(session_duration_seconds) as total_time_seconds
                    FROM user_activity_log 
                    WHERE user_id = ? AND created_at >= ?
                """), (user_id, start_date.isoformat()))
            
            row = cursor.fetchone()
            
            if row:
                total_interactions, features_used, active_days, total_time = row
                
                overview = {
                    "total_interactions": total_interactions or 0,
                    "features_used": features_used or 0,
                    "active_days": active_days or 0,
                    "total_time_minutes": round((total_time or 0) / 60, 1),
                    "avg_interactions_per_day": round((total_interactions or 0) / max(active_days or 1, 1), 1),
                    "avg_session_time": round((total_time or 0) / max(total_interactions or 1, 1), 1),
                    "engagement_level": self._calculate_engagement_level(active_days, total_interactions, period_days)
                }
            else:
                overview = self._get_empty_overview()
            
            # Get companion chat stats
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT COUNT(*) FROM chat_conversations 
                    WHERE user_id = %s AND created_at >= %s
                """), (user_id, start_date))
            else:
                cursor.execute(format_query("""
                    SELECT COUNT(*) FROM chat_conversations 
                    WHERE user_id = ? AND created_at >= ?
                """), (user_id, start_date.isoformat()))
            
            chat_messages = cursor.fetchone()[0] or 0
            overview["chat_messages"] = chat_messages
            
            conn.close()
            return overview
            
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            return self._get_empty_overview()
    
    def _get_usage_metrics(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Get detailed usage metrics"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now(timezone.utc) - timedelta(days=period_days)
            
            # Get daily usage pattern
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as usage_date,
                        COUNT(*) as daily_interactions,
                        COUNT(DISTINCT feature_type) as daily_features,
                        SUM(session_duration_seconds) as daily_time_seconds
                    FROM user_activity_log 
                    WHERE user_id = %s AND created_at >= %s
                    GROUP BY DATE(created_at)
                    ORDER BY usage_date
                """), (user_id, start_date))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        DATE(created_at) as usage_date,
                        COUNT(*) as daily_interactions,
                        COUNT(DISTINCT feature_type) as daily_features,
                        SUM(session_duration_seconds) as daily_time_seconds
                    FROM user_activity_log 
                    WHERE user_id = ? AND created_at >= ?
                    GROUP BY DATE(created_at)
                    ORDER BY usage_date
                """), (user_id, start_date.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            daily_metrics = []
            for row in rows:
                usage_date, interactions, features, time_seconds = row
                daily_metrics.append({
                    "date": str(usage_date),
                    "interactions": interactions,
                    "features_used": features,
                    "time_minutes": round((time_seconds or 0) / 60, 1),
                    "avg_session_time": round((time_seconds or 0) / max(interactions, 1), 1)
                })
            
            # Calculate metrics
            total_interactions = sum(d['interactions'] for d in daily_metrics)
            peak_day = max(daily_metrics, key=lambda x: x['interactions']) if daily_metrics else None
            
            return {
                "daily_breakdown": daily_metrics,
                "peak_activity_day": peak_day,
                "total_interactions": total_interactions,
                "consistency_score": len(daily_metrics) / period_days * 100 if period_days > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting usage metrics: {e}")
            return {}
    
    def _get_engagement_insights(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Get user engagement insights and patterns"""
        try:
            # Get user's tier and subscription info
            from ..auth.session_manager import get_user_plan_info
            plan_info = get_user_plan_info(user_id)
            
            # Calculate engagement metrics
            activity_summary = self.get_user_activity_summary(user_id, period_days)
            
            insights = {
                "user_tier": plan_info.get('plan', 'bronze'),
                "subscription_active": plan_info.get('subscription_active', False),
                "engagement_trends": self._analyze_engagement_trends(activity_summary),
                "usage_patterns": self._analyze_usage_patterns(user_id, period_days),
                "growth_metrics": self._calculate_growth_metrics(user_id, period_days)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting engagement insights: {e}")
            return {}
    
    def _get_feature_breakdown(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Get detailed feature usage breakdown"""
        try:
            from .usage_tracker import UsageTracker
            
            tracker = UsageTracker()
            activity_summary = tracker.get_user_activity_summary(user_id, period_days)
            
            if not activity_summary or not activity_summary.get('features'):
                return {"features": [], "total_features": 0}
            
            # Categorize features
            feature_categories = {
                'communication': ['chat', 'voice_chat'],
                'creative': ['creative_writing', 'ai_images', 'decoder'],
                'wellness': ['meditations', 'voice_journaling', 'horoscope', 'fortune'],
                'social': ['relationships', 'community'],
                'premium': ['mini_studio'],
                'utility': ['library', 'analytics']
            }
            
            categorized_features = {}
            for category, feature_list in feature_categories.items():
                categorized_features[category] = []
                
                for feature_data in activity_summary['features']:
                    if feature_data['feature'] in feature_list:
                        categorized_features[category].append(feature_data)
            
            return {
                "by_category": categorized_features,
                "top_features": activity_summary['features'][:5],
                "total_features": activity_summary['total_features_used']
            }
            
        except Exception as e:
            logger.error(f"Error getting feature breakdown: {e}")
            return {}
    
    def _get_companion_analytics(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Get companion interaction analytics"""
        try:
            from ..chat.conversation_manager import ConversationManager
            
            conversation_manager = ConversationManager()
            insights = conversation_manager.get_conversation_insights(user_id, period_days)
            
            return {
                "companion_insights": insights,
                "favorite_companion": insights.get('companions', [{}])[0].get('companion_id') if insights.get('companions') else None,
                "total_conversations": insights.get('total_messages', 0),
                "companion_diversity": insights.get('total_companions', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting companion analytics: {e}")
            return {}
    
    def _get_personalized_recommendations(self, user_id: int, period_days: int) -> List[Dict[str, Any]]:
        """Generate personalized recommendations based on usage"""
        try:
            recommendations = []
            
            # Get user's activity summary
            from .usage_tracker import UsageTracker
            tracker = UsageTracker()
            activity = tracker.get_user_activity_summary(user_id, period_days)
            
            if not activity or not activity.get('features'):
                return [{
                    "type": "explore",
                    "title": "Start Your SoulBridge Journey",
                    "description": "Try chatting with a companion or explore our creative features!",
                    "action": "visit_companion_selection"
                }]
            
            features_used = {f['feature'] for f in activity['features']}
            
            # Recommend unused features
            if 'chat' not in features_used:
                recommendations.append({
                    "type": "feature",
                    "title": "Try AI Companions",
                    "description": "Connect with our AI companions for personalized conversations and guidance",
                    "action": "visit_companion_selection"
                })
            
            if 'meditations' not in features_used:
                recommendations.append({
                    "type": "wellness",
                    "title": "Explore Guided Meditations",
                    "description": "Discover personalized meditation sessions for stress relief and mindfulness",
                    "action": "visit_meditations"
                })
            
            if 'creative_writing' not in features_used:
                recommendations.append({
                    "type": "creative",
                    "title": "Unleash Your Creativity",
                    "description": "Use our Creative Writer to explore your imagination and express yourself",
                    "action": "visit_creative_writer"
                })
            
            # Usage pattern recommendations
            total_interactions = sum(f['usage_count'] for f in activity['features'])
            if total_interactions < 5:
                recommendations.append({
                    "type": "engagement",
                    "title": "Dive Deeper",
                    "description": "You're just getting started! Try exploring more features to get the full SoulBridge experience",
                    "action": "explore_features"
                })
            
            return recommendations[:3]  # Limit to 3 recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    def _analyze_engagement_trends(self, activity_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user engagement trends"""
        try:
            if not activity_summary or not activity_summary.get('features'):
                return {"trend": "no_data", "score": 0}
            
            # Calculate trend based on activity patterns
            features = activity_summary['features']
            total_usage = sum(f['usage_count'] for f in features)
            
            if total_usage >= 20:
                trend = "high_engagement"
                score = 85
            elif total_usage >= 10:
                trend = "moderate_engagement"
                score = 65
            elif total_usage >= 3:
                trend = "low_engagement"
                score = 35
            else:
                trend = "minimal_engagement"
                score = 15
            
            return {
                "trend": trend,
                "score": score,
                "total_usage": total_usage,
                "features_explored": len(features)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing engagement trends: {e}")
            return {"trend": "unknown", "score": 0}
    
    def _analyze_usage_patterns(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Analyze user's usage patterns"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now(timezone.utc) - timedelta(days=period_days)
            
            # Get hourly usage patterns
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        EXTRACT(HOUR FROM created_at) as hour_of_day,
                        COUNT(*) as usage_count
                    FROM user_activity_log 
                    WHERE user_id = %s AND created_at >= %s
                    GROUP BY EXTRACT(HOUR FROM created_at)
                    ORDER BY usage_count DESC
                """), (user_id, start_date))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        strftime('%H', created_at) as hour_of_day,
                        COUNT(*) as usage_count
                    FROM user_activity_log 
                    WHERE user_id = ? AND created_at >= ?
                    GROUP BY strftime('%H', created_at)
                    ORDER BY usage_count DESC
                """), (user_id, start_date.isoformat()))
            
            hourly_data = cursor.fetchall()
            
            # Get day of week patterns
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        EXTRACT(DOW FROM created_at) as day_of_week,
                        COUNT(*) as usage_count
                    FROM user_activity_log 
                    WHERE user_id = %s AND created_at >= %s
                    GROUP BY EXTRACT(DOW FROM created_at)
                    ORDER BY usage_count DESC
                """), (user_id, start_date))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        strftime('%w', created_at) as day_of_week,
                        COUNT(*) as usage_count
                    FROM user_activity_log 
                    WHERE user_id = ? AND created_at >= ?
                    GROUP BY strftime('%w', created_at)
                    ORDER BY usage_count DESC
                """), (user_id, start_date.isoformat()))
            
            daily_data = cursor.fetchall()
            conn.close()
            
            patterns = {
                "peak_hour": int(hourly_data[0][0]) if hourly_data else None,
                "peak_day": int(daily_data[0][0]) if daily_data else None,
                "hourly_distribution": [{"hour": int(h), "usage": c} for h, c in hourly_data],
                "daily_distribution": [{"day": int(d), "usage": c} for d, c in daily_data]
            }
            
            # Determine usage pattern type
            if patterns["peak_hour"] is not None:
                if 6 <= patterns["peak_hour"] <= 12:
                    pattern_type = "morning_user"
                elif 13 <= patterns["peak_hour"] <= 17:
                    pattern_type = "afternoon_user"
                elif 18 <= patterns["peak_hour"] <= 22:
                    pattern_type = "evening_user"
                else:
                    pattern_type = "night_user"
            else:
                pattern_type = "unknown"
            
            patterns["usage_type"] = pattern_type
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing usage patterns: {e}")
            return {}
    
    def _calculate_growth_metrics(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Calculate user growth and progression metrics"""
        try:
            # Compare current period with previous period
            current_period = period_days
            previous_period = period_days * 2
            
            from .usage_tracker import UsageTracker
            tracker = UsageTracker()
            
            current_summary = tracker.get_user_activity_summary(user_id, current_period)
            previous_summary = tracker.get_user_activity_summary(user_id, previous_period)
            
            # Calculate growth
            current_total = sum(f['usage_count'] for f in current_summary.get('features', []))
            previous_total = sum(f['usage_count'] for f in previous_summary.get('features', []))
            
            # Adjust previous total to compare same time periods
            previous_total = previous_total - current_total if previous_total > current_total else 0
            
            if previous_total > 0:
                growth_rate = ((current_total - previous_total) / previous_total) * 100
            else:
                growth_rate = 100 if current_total > 0 else 0
            
            return {
                "current_period_usage": current_total,
                "previous_period_usage": previous_total,
                "growth_rate_percentage": round(growth_rate, 1),
                "growth_direction": "increasing" if growth_rate > 10 else "decreasing" if growth_rate < -10 else "stable",
                "new_features_tried": len(set(f['feature'] for f in current_summary.get('features', [])) - 
                                         set(f['feature'] for f in previous_summary.get('features', [])))
            }
            
        except Exception as e:
            logger.error(f"Error calculating growth metrics: {e}")
            return {}
    
    def _calculate_engagement_level(self, active_days: int, total_interactions: int, period_days: int) -> str:
        """Calculate engagement level category"""
        try:
            if period_days == 0:
                return "unknown"
            
            consistency = active_days / period_days
            intensity = total_interactions / period_days
            
            if consistency >= 0.8 and intensity >= 3:
                return "highly_engaged"
            elif consistency >= 0.5 and intensity >= 1.5:
                return "moderately_engaged"
            elif consistency >= 0.2 or intensity >= 0.5:
                return "lightly_engaged"
            else:
                return "minimally_engaged"
                
        except Exception as e:
            logger.error(f"Error calculating engagement level: {e}")
            return "unknown"
    
    def _get_empty_overview(self) -> Dict[str, Any]:
        """Get empty overview for new users"""
        return {
            "total_interactions": 0,
            "features_used": 0,
            "active_days": 0,
            "total_time_minutes": 0,
            "avg_interactions_per_day": 0,
            "avg_session_time": 0,
            "engagement_level": "new_user",
            "chat_messages": 0
        }
    
    def _get_fallback_dashboard(self, user_id: int, period_days: int) -> Dict[str, Any]:
        """Fallback dashboard when database is unavailable"""
        return {
            "user_id": user_id,
            "period_days": period_days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overview": self._get_empty_overview(),
            "usage_metrics": {"daily_breakdown": [], "total_interactions": 0},
            "engagement_insights": {"trend": "unknown", "score": 0},
            "feature_breakdown": {"features": [], "total_features": 0},
            "companion_analytics": {"total_conversations": 0},
            "recommendations": [{
                "type": "system",
                "title": "Analytics Temporarily Unavailable",
                "description": "Please try again later",
                "action": "refresh"
            }],
            "note": "Dashboard data temporarily unavailable"
        }
    
    def get_admin_analytics(self, period_days: int = 7) -> Dict[str, Any]:
        """Get system-wide analytics for admin dashboard"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now(timezone.utc) - timedelta(days=period_days)
            
            # Get system-wide metrics
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT user_id) as active_users,
                        COUNT(*) as total_interactions,
                        COUNT(DISTINCT feature_type) as features_used,
                        AVG(session_duration_seconds) as avg_session_duration
                    FROM user_activity_log 
                    WHERE created_at >= %s
                """), (start_date,))
            else:
                cursor.execute(format_query("""
                    SELECT
                        COUNT(DISTINCT user_id) as active_users,
                        COUNT(*) as total_interactions,
                        COUNT(DISTINCT feature_type) as features_used,
                        AVG(session_duration_seconds) as avg_session_duration
                    FROM user_activity_log
                    WHERE created_at >= ?
                """), (start_date.isoformat(),))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                active_users, total_interactions, features_used, avg_duration = row
                
                return {
                    "period_days": period_days,
                    "active_users": active_users or 0,
                    "total_interactions": total_interactions or 0,
                    "features_in_use": features_used or 0,
                    "avg_session_duration": round(avg_duration or 0, 1),
                    "interactions_per_user": round((total_interactions or 0) / max(active_users or 1, 1), 1)
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error getting admin analytics: {e}")
            return {}