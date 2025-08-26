# Analytics and User Insights System
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import db
import json


class AnalyticsManager:
    def __init__(self):
        self.db = db

    def get_user_metrics(self, days: int = 30) -> Dict:
        """Get comprehensive user engagement metrics"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Get all users and filter by date
            all_users = self.db.users.get_all_users()
            total_users = len(all_users)

            # Calculate new users in period
            new_users = 0
            active_users = set()
            premium_users = 0

            for user in all_users:
                # Check if user is premium
                if user.get("isPremium") or user.get("subscription_status") == "active":
                    premium_users += 1

                # Count new users (simplified - using email as registration indicator)
                if user.get("created_at"):
                    try:
                        created_date = datetime.fromisoformat(
                            user["created_at"].replace("Z", "+00:00")
                        )
                        if created_date >= start_date:
                            new_users += 1
                    except:
                            # Ignore users with invalid created_at
                            ...

            # Get conversation metrics
            conversation_metrics = self._get_conversation_metrics(days)

            # Calculate retention and engagement
            daily_active = self._estimate_daily_active_users()
            monthly_active = self._estimate_monthly_active_users()

            return {
                "period_days": days,
                "total_users": total_users,
                "new_users": new_users,
                "premium_users": premium_users,
                "free_users": total_users - premium_users,
                "premium_conversion_rate": (
                    round((premium_users / total_users * 100), 2)
                    if total_users > 0
                    else 0
                ),
                "daily_active_users": daily_active,
                "monthly_active_users": monthly_active,
                "engagement_rate": (
                    round((daily_active / total_users * 100), 2)
                    if total_users > 0
                    else 0
                ),
                "conversations": conversation_metrics,
            }

        except Exception as e:
            logging.error(f"Analytics user metrics error: {e}")
            return {"error": str(e)}

    def get_companion_analytics(self, days: int = 30) -> Dict:
        """Get analytics about companion usage and popularity"""
        try:
            companions = [
                "Blayzo",
                "Blayzica",
                "Crimson",
                "Violet",
                "Blayzion",
                "Blayzia",
            ]

            # Get companion selection data from localStorage or user preferences
            all_users = self.db.users.get_all_users()

            companion_stats = {}
            for companion in companions:
                companion_stats[companion] = {
                    "total_selections": 0,
                    "active_users": 0,
                    "is_premium": companion
                    in ["Crimson", "Violet", "Blayzion", "Blayzia"],
                    "estimated_conversations": 0,
                }

            # Analyze user companion preferences
            for user in all_users:
                selected_companion = user.get("selectedCharacter") or user.get(
                    "favorite_companion"
                )
                if selected_companion and selected_companion in companions:
                    companion_stats[selected_companion]["total_selections"] += 1
                    companion_stats[selected_companion]["active_users"] += 1

            # Calculate estimated conversations (simplified)
            total_conversations = self._estimate_total_conversations()
            total_selections = sum(
                stats["total_selections"] for stats in companion_stats.values()
            )

            if total_selections > 0:
                for companion in companions:
                    selection_ratio = (
                        companion_stats[companion]["total_selections"]
                        / total_selections
                    )
                    companion_stats[companion]["estimated_conversations"] = int(
                        total_conversations * selection_ratio
                    )

            return {
                "period_days": days,
                "companions": companion_stats,
                "most_popular": max(
                    companion_stats.keys(),
                    key=lambda x: companion_stats[x]["total_selections"],
                ),
                "total_companion_interactions": total_conversations,
            }

        except Exception as e:
            logging.error(f"Companion analytics error: {e}")
            return {"error": str(e)}

    def get_revenue_analytics(self, days: int = 30) -> Dict:
        """Get revenue and subscription analytics"""
        try:
            all_users = self.db.users.get_all_users()

            # Revenue calculations (simplified)
            premium_users = 0
            estimated_monthly_revenue = 0
            estimated_yearly_revenue = 0

            # Premium companion purchases
            premium_companion_purchases = 0
            switching_purchases = 0

            for user in all_users:
                # Check premium status
                if user.get("isPremium") or user.get("subscription_status") == "active":
                    premium_users += 1

                    # Estimate subscription revenue
                    subscription_type = user.get("subscription_type", "monthly")
                    if subscription_type == "monthly":
                        estimated_monthly_revenue += 10
                        estimated_yearly_revenue += 120
                    elif subscription_type == "yearly":
                        estimated_monthly_revenue += 8.33  # $100/12
                        estimated_yearly_revenue += 100

                # Check for premium companion purchases
                purchased_companions = []
                for companion in ["Crimson", "Violet", "Blayzion", "Blayzia"]:
                    if user.get(f"purchased{companion}"):
                        purchased_companions.append(companion)
                        premium_companion_purchases += 5  # $5 per companion

                # Estimate switching fees (simplified)
                if user.get("has_switched_companions"):
                    switching_purchases += 3  # $3 switching fee

            # Calculate metrics
            total_revenue = (
                estimated_monthly_revenue
                + premium_companion_purchases
                + switching_purchases
            )
            avg_revenue_per_user = total_revenue / len(all_users) if all_users else 0

            return {
                "period_days": days,
                "premium_subscribers": premium_users,
                "subscription_revenue": estimated_monthly_revenue,
                "companion_purchases_revenue": premium_companion_purchases,
                "switching_revenue": switching_purchases,
                "total_revenue": total_revenue,
                "avg_revenue_per_user": round(avg_revenue_per_user, 2),
                "conversion_rate": (
                    round((premium_users / len(all_users) * 100), 2) if all_users else 0
                ),
                "projected_monthly_revenue": estimated_monthly_revenue,
                "projected_yearly_revenue": estimated_yearly_revenue,
            }

        except Exception as e:
            logging.error(f"Revenue analytics error: {e}")
            return {"error": str(e)}

    def get_usage_patterns(self, days: int = 7) -> Dict:
        """Get user behavior and usage patterns"""
        try:
            # This would typically analyze chat logs, session times, etc.
            # For now, we'll provide estimated patterns

            patterns = {
                "peak_hours": [19, 20, 21, 22],  # 7-10 PM
                "average_session_length": 15,  # minutes
                "average_messages_per_session": 12,
                "most_active_days": ["Friday", "Saturday", "Sunday"],
                "user_retention": {
                    "day_1": 85,  # percentage
                    "day_7": 45,
                    "day_30": 25,
                },
                "feature_usage": {
                    "chat": 100,
                    "companion_switching": 15,
                    "profile_customization": 30,
                    "conversation_saving": 60,
                },
            }

            return patterns

        except Exception as e:
            logging.error(f"Usage patterns error: {e}")
            return {"error": str(e)}

    def _get_conversation_metrics(self, days: int) -> Dict:
        """Get conversation-related metrics"""
        # Simplified conversation metrics
        # In a real implementation, this would analyze chat logs
        estimated_total = self._estimate_total_conversations()

        return {
            "total_conversations": estimated_total,
            "avg_conversations_per_user": round(
                estimated_total / max(1, len(self.db.users.get_all_users())), 1
            ),
            "avg_messages_per_conversation": 8.5,
            "total_messages": int(estimated_total * 8.5),
        }

    def _estimate_daily_active_users(self) -> int:
        """Estimate daily active users"""
        total_users = len(self.db.users.get_all_users())
        # Estimate 15-20% of users are daily active
        return int(total_users * 0.18)

    def _estimate_monthly_active_users(self) -> int:
        """Estimate monthly active users"""
        total_users = len(self.db.users.get_all_users())
        # Estimate 60-70% of users are monthly active
        return int(total_users * 0.65)

    def _estimate_total_conversations(self) -> int:
        """Estimate total conversations"""
        total_users = len(self.db.users.get_all_users())
        # Estimate each user has had 3-5 conversations on average
        return int(total_users * 4.2)

    def log_user_action(self, user_email: str, action: str, details: Dict = None):
        """Log user actions for analytics"""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "user_email": user_email,
                "action": action,
                "details": details or {},
            }

            # In a real implementation, this would go to a dedicated analytics database
            logging.info(f"User action logged: {json.dumps(log_entry)}")

        except Exception as e:
            logging.error(f"Action logging error: {e}")

    def get_dashboard_summary(self) -> Dict:
        """Get comprehensive dashboard summary"""
        try:
            user_metrics = self.get_user_metrics(30)
            companion_analytics = self.get_companion_analytics(30)
            revenue_analytics = self.get_revenue_analytics(30)
            usage_patterns = self.get_usage_patterns(7)

            return {
                "users": user_metrics,
                "companions": companion_analytics,
                "revenue": revenue_analytics,
                "usage": usage_patterns,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logging.error(f"Dashboard summary error: {e}")
            return {"error": str(e)}


# Global instance
analytics = AnalyticsManager()
