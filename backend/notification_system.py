# Real-time Notifications & Alerts System
import os
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import asyncio
import threading
import time
from database_utils import format_query

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of notifications"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    REMINDER = "reminder"
    SYSTEM = "system"
    USER_ACTION = "user_action"
    AI_INSIGHT = "ai_insight"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationChannel(Enum):
    """Notification delivery channels"""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    WEBHOOK = "webhook"

@dataclass
class Notification:
    """Notification data structure"""
    id: str
    user_id: str
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority
    channels: List[NotificationChannel]
    data: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_channels: List[str] = None
    retry_count: int = 0
    is_persistent: bool = True
    action_url: Optional[str] = None
    
    def __post_init__(self):
        if self.failed_channels is None:
            self.failed_channels = []

@dataclass
class NotificationPreferences:
    """User notification preferences"""
    user_id: str
    email_enabled: bool = True
    push_enabled: bool = True
    sms_enabled: bool = False
    in_app_enabled: bool = True
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    frequency_limit: int = 10  # Max notifications per hour
    priority_threshold: NotificationPriority = NotificationPriority.LOW
    blocked_types: List[NotificationType] = None
    
    def __post_init__(self):
        if self.blocked_types is None:
            self.blocked_types = []

class NotificationTemplate:
    """Template for generating notifications"""
    
    @staticmethod
    def conversation_reminder(user_id: str, companion_name: str) -> Notification:
        """Template for conversation reminder"""
        return Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=f"{companion_name} misses you!",
            message=f"It's been a while since your last conversation with {companion_name}. They're here whenever you're ready to chat.",
            type=NotificationType.REMINDER,
            priority=NotificationPriority.LOW,
            channels=[NotificationChannel.IN_APP, NotificationChannel.PUSH],
            data={"companion": companion_name, "type": "conversation_reminder"},
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=1),
            action_url="/chat"
        )
    
    @staticmethod
    def mood_check_in(user_id: str) -> Notification:
        """Template for mood check-in"""
        return Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="How are you feeling today?",
            message="Take a moment to check in with yourself. Your emotional wellbeing matters.",
            type=NotificationType.REMINDER,
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.IN_APP, NotificationChannel.PUSH],
            data={"type": "mood_check"},
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=12),
            action_url="/mood-tracker"
        )
    
    @staticmethod
    def ai_insight(user_id: str, insight: str) -> Notification:
        """Template for AI-generated insights"""
        return Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="Personal Insight",
            message=insight,
            type=NotificationType.AI_INSIGHT,
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.IN_APP],
            data={"type": "ai_insight", "insight": insight},
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7),
            action_url="/insights"
        )
    
    @staticmethod
    def system_maintenance(title: str, message: str, start_time: datetime) -> Notification:
        """Template for system maintenance alerts"""
        return Notification(
            id=str(uuid.uuid4()),
            user_id="*",  # Broadcast to all users
            title=title,
            message=message,
            type=NotificationType.SYSTEM,
            priority=NotificationPriority.HIGH,
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            data={"type": "maintenance", "start_time": start_time.isoformat()},
            created_at=datetime.now(),
            expires_at=start_time + timedelta(hours=6),
            is_persistent=True
        )

class NotificationManager:
    """Manages notifications and alerts"""
    
    def __init__(self, db_manager=None, email_service=None):
        self.db = db_manager
        self.email_service = email_service
        self.active_notifications: Dict[str, List[Notification]] = defaultdict(list)
        self.user_preferences: Dict[str, NotificationPreferences] = {}
        self.delivery_queue: List[Notification] = []
        self.rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        self.notification_handlers = {
            NotificationChannel.IN_APP: self._deliver_in_app,
            NotificationChannel.EMAIL: self._deliver_email,
            NotificationChannel.PUSH: self._deliver_push,
            NotificationChannel.SMS: self._deliver_sms,
            NotificationChannel.WEBHOOK: self._deliver_webhook
        }
        
        # Start background processor
        self._start_background_processor()
    
    def _start_background_processor(self):
        """Start background thread for processing notifications"""
        def processor():
            while True:
                try:
                    self._process_delivery_queue()
                    self._cleanup_expired_notifications()
                    time.sleep(10)  # Process every 10 seconds
                except Exception as e:
                    logger.error(f"Error in notification processor: {e}")
                    time.sleep(30)  # Wait longer on error
        
        thread = threading.Thread(target=processor, daemon=True)
        thread.start()
        logger.info("Notification background processor started")
    
    def create_notification(self, notification: Notification) -> bool:
        """Create and queue a notification"""
        try:
            # Validate notification
            if not self._validate_notification(notification):
                return False
            
            # Check user preferences
            if not self._check_user_preferences(notification):
                logger.info(f"Notification blocked by user preferences: {notification.id}")
                return False
            
            # Check rate limits
            if not self._check_rate_limit(notification.user_id):
                logger.info(f"Notification rate limited: {notification.id}")
                return False
            
            # Store in database
            if self.db:
                self._store_notification(notification)
            
            # Add to active notifications
            self.active_notifications[notification.user_id].append(notification)
            
            # Queue for delivery
            self.delivery_queue.append(notification)
            
            logger.info(f"Notification created: {notification.id} for user {notification.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating notification {notification.id}: {e}")
            return False
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        try:
            notifications = []
            
            # Get from active notifications
            user_notifications = self.active_notifications.get(user_id, [])
            
            for notification in user_notifications:
                if unread_only and notification.read_at:
                    continue
                
                notifications.append({
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "type": notification.type.value,
                    "priority": notification.priority.value,
                    "created_at": notification.created_at.isoformat(),
                    "read_at": notification.read_at.isoformat() if notification.read_at else None,
                    "action_url": notification.action_url,
                    "data": notification.data
                })
            
            # Sort by creation time (newest first)
            notifications.sort(key=lambda x: x["created_at"], reverse=True)
            
            return notifications[:limit]
            
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {e}")
            return []
    
    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        try:
            user_notifications = self.active_notifications.get(user_id, [])
            
            for notification in user_notifications:
                if notification.id == notification_id:
                    notification.read_at = datetime.now()
                    
                    # Update in database
                    if self.db:
                        self._update_notification_read_status(notification_id, notification.read_at)
                    
                    logger.info(f"Notification marked as read: {notification_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking notification as read {notification_id}: {e}")
            return False
    
    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for user"""
        try:
            user_notifications = self.active_notifications.get(user_id, [])
            return len([n for n in user_notifications if not n.read_at])
        except Exception as e:
            logger.error(f"Error getting unread count for user {user_id}: {e}")
            return 0
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user notification preferences"""
        try:
            current_prefs = self.user_preferences.get(user_id, NotificationPreferences(user_id))
            
            # Update preferences
            for key, value in preferences.items():
                if hasattr(current_prefs, key):
                    setattr(current_prefs, key, value)
            
            self.user_preferences[user_id] = current_prefs
            
            # Store in database
            if self.db:
                self._store_user_preferences(current_prefs)
            
            logger.info(f"Updated notification preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {e}")
            return False
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user notification preferences"""
        try:
            prefs = self.user_preferences.get(user_id)
            if not prefs:
                # Load from database or create default
                prefs = self._load_user_preferences(user_id)
                self.user_preferences[user_id] = prefs
            
            return asdict(prefs)
            
        except Exception as e:
            logger.error(f"Error getting preferences for user {user_id}: {e}")
            return asdict(NotificationPreferences(user_id))
    
    def send_bulk_notification(self, notification_template: Notification, user_ids: List[str]) -> Dict[str, bool]:
        """Send notification to multiple users"""
        results = {}
        
        for user_id in user_ids:
            # Create copy of template for each user
            notification = Notification(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=notification_template.title,
                message=notification_template.message,
                type=notification_template.type,
                priority=notification_template.priority,
                channels=notification_template.channels,
                data=notification_template.data,
                created_at=datetime.now(),
                expires_at=notification_template.expires_at,
                is_persistent=notification_template.is_persistent,
                action_url=notification_template.action_url
            )
            
            results[user_id] = self.create_notification(notification)
        
        return results
    
    def _validate_notification(self, notification: Notification) -> bool:
        """Validate notification data"""
        if not notification.user_id or not notification.title or not notification.message:
            return False
        
        if not notification.channels:
            return False
        
        return True
    
    def _check_user_preferences(self, notification: Notification) -> bool:
        """Check if notification is allowed by user preferences"""
        prefs = self.user_preferences.get(notification.user_id)
        if not prefs:
            return True  # Allow if no preferences set
        
        # Check if notification type is blocked
        if notification.type in prefs.blocked_types:
            return False
        
        # Check priority threshold
        priority_order = [NotificationPriority.LOW, NotificationPriority.MEDIUM, 
                         NotificationPriority.HIGH, NotificationPriority.CRITICAL]
        
        if priority_order.index(notification.priority) < priority_order.index(prefs.priority_threshold):
            return False
        
        # Check quiet hours
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        if prefs.quiet_hours_start <= prefs.quiet_hours_end:
            # Same day quiet hours
            if prefs.quiet_hours_start <= current_time <= prefs.quiet_hours_end:
                # Only allow critical notifications during quiet hours
                return notification.priority == NotificationPriority.CRITICAL
        else:
            # Overnight quiet hours
            if current_time >= prefs.quiet_hours_start or current_time <= prefs.quiet_hours_end:
                return notification.priority == NotificationPriority.CRITICAL
        
        return True
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check rate limiting for user"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        self.rate_limits[user_id] = [
            timestamp for timestamp in self.rate_limits[user_id]
            if timestamp > hour_ago
        ]
        
        prefs = self.user_preferences.get(user_id, NotificationPreferences(user_id))
        
        if len(self.rate_limits[user_id]) >= prefs.frequency_limit:
            return False
        
        # Add current timestamp
        self.rate_limits[user_id].append(now)
        return True
    
    def _process_delivery_queue(self):
        """Process notifications in delivery queue"""
        while self.delivery_queue:
            notification = self.delivery_queue.pop(0)
            
            try:
                self._deliver_notification(notification)
            except Exception as e:
                logger.error(f"Error delivering notification {notification.id}: {e}")
                
                # Retry logic
                if notification.retry_count < 3:
                    notification.retry_count += 1
                    self.delivery_queue.append(notification)
    
    def _deliver_notification(self, notification: Notification):
        """Deliver notification through specified channels"""
        success_channels = []
        
        for channel in notification.channels:
            try:
                handler = self.notification_handlers.get(channel)
                if handler and handler(notification):
                    success_channels.append(channel.value)
                else:
                    notification.failed_channels.append(channel.value)
            except Exception as e:
                logger.error(f"Error delivering via {channel.value}: {e}")
                notification.failed_channels.append(channel.value)
        
        if success_channels:
            notification.delivered_at = datetime.now()
            logger.info(f"Notification {notification.id} delivered via {success_channels}")
    
    def _deliver_in_app(self, notification: Notification) -> bool:
        """Deliver in-app notification"""
        # In-app notifications are already stored in active_notifications
        return True
    
    def _deliver_email(self, notification: Notification) -> bool:
        """Deliver email notification"""
        if not self.email_service:
            return False
        
        try:
            # Get user email from database
            user_email = self._get_user_email(notification.user_id)
            if not user_email:
                return False
            
            result = self.email_service.send_email(
                to_email=user_email,
                subject=notification.title,
                text_content=notification.message
            )
            
            return result.get("success", False)
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    def _deliver_push(self, notification: Notification) -> bool:
        """Deliver push notification"""
        # Placeholder for push notification implementation
        # Would integrate with FCM, APNs, or web push service
        logger.info(f"Push notification sent: {notification.title}")
        return True
    
    def _deliver_sms(self, notification: Notification) -> bool:
        """Deliver SMS notification"""
        # Placeholder for SMS implementation
        # Would integrate with Twilio, AWS SNS, etc.
        logger.info(f"SMS notification sent: {notification.title}")
        return True
    
    def _deliver_webhook(self, notification: Notification) -> bool:
        """Deliver webhook notification"""
        # Placeholder for webhook implementation
        logger.info(f"Webhook notification sent: {notification.title}")
        return True
    
    def _cleanup_expired_notifications(self):
        """Remove expired notifications"""
        now = datetime.now()
        
        for user_id in list(self.active_notifications.keys()):
            notifications = self.active_notifications[user_id]
            
            # Remove expired notifications
            active = [
                n for n in notifications
                if not n.expires_at or n.expires_at > now
            ]
            
            self.active_notifications[user_id] = active
            
            # Remove empty user entries
            if not active:
                del self.active_notifications[user_id]
    
    def _store_notification(self, notification: Notification):
        """Store notification in database"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(format_query("""
                INSERT INTO notifications (
                    id, user_id, title, message, type, priority, channels,
                    data, created_at, expires_at, is_persistent, action_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """), (
                notification.id,
                notification.user_id,
                notification.title,
                notification.message,
                notification.type.value,
                notification.priority.value,
                json.dumps([c.value for c in notification.channels]),
                json.dumps(notification.data),
                notification.created_at.isoformat(),
                notification.expires_at.isoformat() if notification.expires_at else None,
                notification.is_persistent,
                notification.action_url
            ))
            self.db.connection.commit()
        except Exception as e:
            logger.error(f"Error storing notification in database: {e}")
    
    def _update_notification_read_status(self, notification_id: str, read_at: datetime):
        """Update notification read status in database"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(format_query("""
                UPDATE notifications 
                SET read_at = ? 
                WHERE id = ?
            """), (read_at.isoformat(), notification_id))
            self.db.connection.commit()
        except Exception as e:
            logger.error(f"Error updating notification read status: {e}")
    
    def _store_user_preferences(self, preferences: NotificationPreferences):
        """Store user preferences in database"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(format_query("""
                INSERT OR REPLACE INTO notification_preferences (
                    user_id, email_enabled, push_enabled, sms_enabled, in_app_enabled,
                    quiet_hours_start, quiet_hours_end, frequency_limit, priority_threshold,
                    blocked_types
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """), (
                preferences.user_id,
                preferences.email_enabled,
                preferences.push_enabled,
                preferences.sms_enabled,
                preferences.in_app_enabled,
                preferences.quiet_hours_start,
                preferences.quiet_hours_end,
                preferences.frequency_limit,
                preferences.priority_threshold.value,
                json.dumps([t.value for t in preferences.blocked_types])
            ))
            self.db.connection.commit()
        except Exception as e:
            logger.error(f"Error storing user preferences: {e}")
    
    def _load_user_preferences(self, user_id: str) -> NotificationPreferences:
        """Load user preferences from database"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(format_query("""
                SELECT * FROM notification_preferences WHERE user_id = ?
            """), (user_id,))
            
            row = cursor.fetchone()
            if row:
                return NotificationPreferences(
                    user_id=row[0],
                    email_enabled=bool(row[1]),
                    push_enabled=bool(row[2]),
                    sms_enabled=bool(row[3]),
                    in_app_enabled=bool(row[4]),
                    quiet_hours_start=row[5],
                    quiet_hours_end=row[6],
                    frequency_limit=row[7],
                    priority_threshold=NotificationPriority(row[8]),
                    blocked_types=[NotificationType(t) for t in json.loads(row[9] or "[]")]
                )
            
        except Exception as e:
            logger.error(f"Error loading user preferences: {e}")
        
        # Return default preferences
        return NotificationPreferences(user_id)
    
    def _get_user_email(self, user_id: str) -> Optional[str]:
        """Get user email from database"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(format_query(SELECT email FROM users WHERE id = ?"), (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error getting user email: {e}")
            return None

# Notification automation helpers
class NotificationAutomation:
    """Automated notification triggers"""
    
    def __init__(self, notification_manager: NotificationManager, db_manager=None):
        self.notification_manager = notification_manager
        self.db = db_manager
    
    def schedule_conversation_reminders(self):
        """Schedule reminders for inactive users"""
        try:
            if not self.db:
                return
            
            cursor = self.db.connection.cursor()
            
            # Find users who haven't had conversations in 3 days
            cursor.execute("""
                SELECT DISTINCT u.id, u.display_name, c.ai_companion
                FROM users u
                LEFT JOIN conversations c ON u.id = c.user_id
                WHERE u.id NOT IN (
                    SELECT user_id FROM conversations 
                    WHERE created_at > datetime('now', '-3 days')
                )
                AND u.created_at < datetime('now', '-1 day')
                ORDER BY u.id
            """)
            
            for row in cursor.fetchall():
                user_id, display_name, last_companion = row
                companion_name = last_companion or "Blayzo"
                
                notification = NotificationTemplate.conversation_reminder(user_id, companion_name)
                self.notification_manager.create_notification(notification)
            
            logger.info("Scheduled conversation reminders")
            
        except Exception as e:
            logger.error(f"Error scheduling conversation reminders: {e}")
    
    def schedule_mood_check_ins(self):
        """Schedule daily mood check-ins"""
        try:
            if not self.db:
                return
            
            cursor = self.db.connection.cursor()
            
            # Get active users (had activity in last 7 days)
            cursor.execute("""
                SELECT DISTINCT user_id
                FROM conversations 
                WHERE created_at > datetime('now', '-7 days')
            """)
            
            for row in cursor.fetchall():
                user_id = row[0]
                
                # Check if user already has a recent mood check notification
                notifications = self.notification_manager.get_user_notifications(user_id, unread_only=True)
                has_mood_check = any(n.get("data", {}).get("type") == "mood_check" for n in notifications)
                
                if not has_mood_check:
                    notification = NotificationTemplate.mood_check_in(user_id)
                    self.notification_manager.create_notification(notification)
            
            logger.info("Scheduled mood check-ins")
            
        except Exception as e:
            logger.error(f"Error scheduling mood check-ins: {e}")