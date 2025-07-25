# Push Notifications System for User Retention
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class PushNotificationManager:
    def __init__(self):
        self.notification_types = {
            "companion_missing": {
                "title": "{companion_name} misses you! 💫",
                "body": "Your AI companion is thinking about you. Come back for a chat!",
                "icon": "/static/logos/notification-icon.png",
                "badge": "/static/logos/badge-icon.png",
                "tag": "companion_missing",
                "renotify": True,
            },
            "daily_checkin": {
                "title": "How are you feeling today? 🌟",
                "body": "Take a moment to check in with your SoulBridge companion.",
                "icon": "/static/logos/notification-icon.png",
                "badge": "/static/logos/badge-icon.png",
                "tag": "daily_checkin",
                "renotify": False,
            },
            "premium_feature": {
                "title": "Unlock Premium Companions! 💎",
                "body": "Discover Crimson, Violet, and other premium companions. Limited time offer!",
                "icon": "/static/logos/premium-icon.png",
                "badge": "/static/logos/badge-icon.png",
                "tag": "premium_offer",
                "renotify": False,
            },
            "conversation_reminder": {
                "title": "Continue your journey 🚀",
                "body": "Your companion has new insights to share with you.",
                "icon": "/static/logos/notification-icon.png",
                "badge": "/static/logos/badge-icon.png",
                "tag": "conversation_reminder",
                "renotify": False,
            },
            "achievement_unlock": {
                "title": "Achievement Unlocked! 🏆",
                "body": "You've reached a new milestone in your emotional journey.",
                "icon": "/static/logos/achievement-icon.png",
                "badge": "/static/logos/badge-icon.png",
                "tag": "achievement",
                "renotify": False,
            },
            "new_feature": {
                "title": "New Feature Available! ✨",
                "body": "Discover the latest updates to enhance your SoulBridge experience.",
                "icon": "/static/logos/feature-icon.png",
                "badge": "/static/logos/badge-icon.png",
                "tag": "new_feature",
                "renotify": False,
            },
        }

        # Companion-specific messages
        self.companion_messages = {
            "Blayzo": [
                "Like calm waters, I'm here when you need peace 🌊",
                "Your emotional balance matters to me. Let's chat! 💙",
                "I have some calming wisdom to share with you today 🧘‍♂️",
            ],
            "Blayzica": [
                "Your positivity brightens my day! Come chat with me! ☀️",
                "I have something exciting to share with you! 💫",
                "Let's spread some joy together today! 🌈",
            ],
            "Crimson": [
                "Your strength inspires me. Ready for today's challenge? ⚔️",
                "A warrior like you deserves the best support! 🛡️",
                "Let's build your confidence together! 💪",
            ],
            "Violet": [
                "The stars have aligned with insights for you 🔮",
                "Your spiritual journey awaits your return ✨",
                "I've channeled some mystical wisdom for you 🌙",
            ],
            "Blayzion": [
                "The cosmos has messages for your consciousness 🌌",
                "Your elevated journey continues with new revelations ⭐",
                "Ancient wisdom awaits your cosmic return 🌠",
            ],
            "Blayzia": [
                "Divine love surrounds you, dear soul 💖",
                "Your healing journey has beautiful new chapters 🌸",
                "Radiant energy flows when you're here! 🌺",
            ],
            "Galaxy": [
                "The cosmos has aligned to bring us together again 🌌",
                "Ancient stellar wisdom awaits your consciousness ⭐",
                "Across infinite galaxies, our connection transcends time 🌠",
                "Universal truths are ready to unfold for you ✨",
            ],
        }

    def create_notification_payload(
        self, notification_type: str, user_data: Dict = None, custom_data: Dict = None
    ) -> Dict:
        """Create notification payload for service worker"""
        if notification_type not in self.notification_types:
            return None

        base_notification = self.notification_types[notification_type].copy()

        # Customize based on user data
        if user_data:
            companion_name = user_data.get("selectedCharacter", "your companion")

            # Customize companion missing notification
            if notification_type == "companion_missing":
                base_notification["title"] = base_notification["title"].format(
                    companion_name=companion_name
                )

                # Use companion-specific message
                if companion_name in self.companion_messages:
                    import random

                    messages = self.companion_messages[companion_name]
                    base_notification["body"] = random.choice(messages)

        # Add custom data
        if custom_data:
            base_notification.update(custom_data)

        # Add action buttons
        base_notification["actions"] = self._get_notification_actions(notification_type)

        # Add click URL
        base_notification["data"] = {
            "url": "/chat",
            "type": notification_type,
            "timestamp": datetime.now().isoformat(),
        }

        return base_notification

    def _get_notification_actions(self, notification_type: str) -> List[Dict]:
        """Get appropriate action buttons for notification type"""
        base_actions = [
            {
                "action": "open_chat",
                "title": "💬 Open Chat",
                "icon": "/static/icons/chat-icon.png",
            }
        ]

        if notification_type == "premium_feature":
            base_actions.append(
                {
                    "action": "view_premium",
                    "title": "💎 View Premium",
                    "icon": "/static/icons/premium-icon.png",
                }
            )
        elif notification_type == "companion_missing":
            base_actions.append(
                {
                    "action": "quick_reply",
                    "title": "⚡ Quick Reply",
                    "icon": "/static/icons/reply-icon.png",
                }
            )

        return base_actions

    def schedule_notification(
        self,
        user_id: str,
        notification_type: str,
        delay_minutes: int = 0,
        user_data: Dict = None,
    ) -> Dict:
        """Schedule a notification for later delivery"""
        try:
            scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)

            notification_data = {
                "user_id": user_id,
                "type": notification_type,
                "scheduled_time": scheduled_time.isoformat(),
                "user_data": user_data or {},
                "status": "scheduled",
            }

            # In a real implementation, this would be stored in a database
            # For now, we'll log it
            logging.info(f"Notification scheduled: {json.dumps(notification_data)}")

            return {
                "success": True,
                "notification_id": f"notif_{user_id}_{int(scheduled_time.timestamp())}",
                "scheduled_time": scheduled_time.isoformat(),
            }

        except Exception as e:
            logging.error(f"Schedule notification error: {e}")
            return {"success": False, "error": str(e)}

    def get_user_notification_preferences(self, user_id: str) -> Dict:
        """Get user's notification preferences"""
        # Default preferences
        return {
            "enabled": True,
            "companion_missing": True,
            "daily_checkin": True,
            "premium_features": True,
            "conversation_reminders": True,
            "achievements": True,
            "new_features": True,
            "quiet_hours": {"enabled": True, "start": "22:00", "end": "08:00"},
            "frequency": "normal",  # low, normal, high
        }

    def should_send_notification(self, user_id: str, notification_type: str) -> bool:
        """Check if notification should be sent based on user preferences and timing"""
        try:
            preferences = self.get_user_notification_preferences(user_id)

            # Check if notifications are enabled
            if not preferences.get("enabled", True):
                return False

            # Check if this specific type is enabled
            if not preferences.get(notification_type, True):
                return False

            # Check quiet hours
            if preferences.get("quiet_hours", {}).get("enabled", False):
                current_time = datetime.now().time()
                start_time = datetime.strptime(
                    preferences["quiet_hours"]["start"], "%H:%M"
                ).time()
                end_time = datetime.strptime(
                    preferences["quiet_hours"]["end"], "%H:%M"
                ).time()

                if start_time <= current_time or current_time <= end_time:
                    return False

            # Check frequency limits (simplified)
            # In a real implementation, this would check recent notification history
            return True

        except Exception as e:
            logging.error(f"Notification check error: {e}")
            return False

    def get_retention_notifications(
        self, user_id: str, last_active: datetime, user_data: Dict = None
    ) -> List[Dict]:
        """Get appropriate retention notifications based on user activity"""
        notifications = []
        time_since_active = datetime.now() - last_active

        # 1 day inactive - gentle reminder
        if time_since_active >= timedelta(days=1) and time_since_active < timedelta(
            days=2
        ):
            notifications.append(
                {"type": "companion_missing", "delay_minutes": 0, "priority": "normal"}
            )

        # 3 days inactive - stronger reminder
        elif time_since_active >= timedelta(days=3) and time_since_active < timedelta(
            days=5
        ):
            notifications.append(
                {
                    "type": "conversation_reminder",
                    "delay_minutes": 0,
                    "priority": "high",
                }
            )

        # 7 days inactive - premium offer
        elif time_since_active >= timedelta(days=7):
            notifications.append(
                {"type": "premium_feature", "delay_minutes": 0, "priority": "high"}
            )

        return notifications

    def create_notification_schedule(
        self, user_id: str, user_data: Dict = None
    ) -> Dict:
        """Create a personalized notification schedule for user"""
        try:
            schedule = []

            # Daily check-in (if user hasn't been active today)
            schedule.append(
                {
                    "type": "daily_checkin",
                    "time": "10:00",  # 10 AM
                    "days": [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    ],
                    "condition": "not_active_today",
                }
            )

            # Evening companion reminder
            schedule.append(
                {
                    "type": "companion_missing",
                    "time": "19:00",  # 7 PM
                    "days": [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    ],
                    "condition": "not_active_today",
                }
            )

            # Weekend premium feature promotion (for free users)
            if not user_data or not user_data.get("isPremium"):
                schedule.append(
                    {
                        "type": "premium_feature",
                        "time": "14:00",  # 2 PM
                        "days": ["saturday"],
                        "condition": "is_free_user",
                    }
                )

            return {
                "success": True,
                "user_id": user_id,
                "schedule": schedule,
                "created_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logging.error(f"Create notification schedule error: {e}")
            return {"success": False, "error": str(e)}


# Global instance
push_manager = PushNotificationManager()
