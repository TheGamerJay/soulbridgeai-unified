# Notification API Endpoints
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Blueprint, jsonify, request, session
from notification_system import (
    NotificationManager, NotificationTemplate, NotificationType, 
    NotificationPriority, NotificationChannel, NotificationAutomation
)

logger = logging.getLogger(__name__)

notifications_api = Blueprint('notifications', __name__, url_prefix='/api/notifications')

class NotificationAPI:
    """API handler for notifications"""
    
    def __init__(self, db_manager=None, email_service=None):
        self.notification_manager = NotificationManager(db_manager, email_service)
        self.automation = NotificationAutomation(self.notification_manager, db_manager)
    
    def get_manager(self):
        """Get notification manager instance"""
        return self.notification_manager

# Global notification API instance
notification_api_instance = None

def init_notification_api(db_manager=None, email_service=None):
    """Initialize notification API"""
    global notification_api_instance
    notification_api_instance = NotificationAPI(db_manager, email_service)
    return notification_api_instance

@notifications_api.route('/', methods=['GET'])
def get_notifications():
    """Get user notifications"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = request.args.get('limit', 50, type=int)
        
        if not notification_api_instance:
            return jsonify({"error": "Notification service not initialized"}), 500
        
        notifications = notification_api_instance.notification_manager.get_user_notifications(
            user_id, unread_only, limit
        )
        
        return jsonify({
            "notifications": notifications,
            "count": len(notifications),
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({"error": str(e)}), 500

@notifications_api.route('/unread-count', methods=['GET'])
def get_unread_count():
    """Get count of unread notifications"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        if not notification_api_instance:
            return jsonify({"error": "Notification service not initialized"}), 500
        
        count = notification_api_instance.notification_manager.get_unread_count(user_id)
        
        return jsonify({
            "unread_count": count,
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        return jsonify({"error": str(e)}), 500

@notifications_api.route('/<notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        if not notification_api_instance:
            return jsonify({"error": "Notification service not initialized"}), 500
        
        success = notification_api_instance.notification_manager.mark_notification_read(
            notification_id, user_id
        )
        
        if success:
            return jsonify({
                "message": "Notification marked as read",
                "status": "success"
            })
        else:
            return jsonify({"error": "Notification not found"}), 404
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return jsonify({"error": str(e)}), 500

@notifications_api.route('/preferences', methods=['GET'])
def get_notification_preferences():
    """Get user notification preferences"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        if not notification_api_instance:
            return jsonify({"error": "Notification service not initialized"}), 500
        
        preferences = notification_api_instance.notification_manager.get_user_preferences(user_id)
        
        return jsonify({
            "preferences": preferences,
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        return jsonify({"error": str(e)}), 500

@notifications_api.route('/preferences', methods=['POST'])
def update_notification_preferences():
    """Update user notification preferences"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        if not notification_api_instance:
            return jsonify({"error": "Notification service not initialized"}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        success = notification_api_instance.notification_manager.update_user_preferences(
            user_id, data
        )
        
        if success:
            return jsonify({
                "message": "Preferences updated successfully",
                "status": "success"
            })
        else:
            return jsonify({"error": "Failed to update preferences"}), 500
        
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        return jsonify({"error": str(e)}), 500

@notifications_api.route('/test', methods=['POST'])
def send_test_notification():
    """Send a test notification (for development/testing)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        if not notification_api_instance:
            return jsonify({"error": "Notification service not initialized"}), 500
        
        data = request.get_json() or {}
        
        # Create test notification
        notification = NotificationTemplate.ai_insight(
            user_id, 
            data.get('message', 'This is a test notification from SoulBridge AI!')
        )
        
        success = notification_api_instance.notification_manager.create_notification(notification)
        
        if success:
            return jsonify({
                "message": "Test notification sent",
                "notification_id": notification.id,
                "status": "success"
            })
        else:
            return jsonify({"error": "Failed to send test notification"}), 500
        
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        return jsonify({"error": str(e)}), 500

# Admin endpoints
@notifications_api.route('/admin/broadcast', methods=['POST'])
def admin_broadcast_notification():
    """Send broadcast notification to all users (admin only)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        # Check if user is admin (you would implement proper admin check)
        if not session.get('is_admin'):
            return jsonify({"error": "Admin access required"}), 403
        
        if not notification_api_instance:
            return jsonify({"error": "Notification service not initialized"}), 500
        
        data = request.get_json()
        if not data or not data.get('title') or not data.get('message'):
            return jsonify({"error": "Title and message are required"}), 400
        
        # Get all user IDs from database
        try:
            cursor = notification_api_instance.notification_manager.db.connection.cursor()
            cursor.execute("SELECT id FROM users WHERE is_active = 1")
            user_ids = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user list: {e}")
            return jsonify({"error": "Failed to get user list"}), 500
        
        # Create broadcast notification template
        notification_template = NotificationTemplate.system_maintenance(
            data['title'],
            data['message'],
            datetime.now()
        )
        
        # Send to all users
        results = notification_api_instance.notification_manager.send_bulk_notification(
            notification_template, user_ids
        )
        
        success_count = sum(1 for success in results.values() if success)
        
        return jsonify({
            "message": f"Broadcast sent to {success_count}/{len(user_ids)} users",
            "results": results,
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error sending broadcast notification: {e}")
        return jsonify({"error": str(e)}), 500

@notifications_api.route('/admin/automation/trigger', methods=['POST'])
def admin_trigger_automation():
    """Trigger automated notification workflows (admin only)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        if not session.get('is_admin'):
            return jsonify({"error": "Admin access required"}), 403
        
        if not notification_api_instance:
            return jsonify({"error": "Notification service not initialized"}), 500
        
        data = request.get_json() or {}
        automation_type = data.get('type')
        
        if automation_type == 'conversation_reminders':
            notification_api_instance.automation.schedule_conversation_reminders()
            message = "Conversation reminders scheduled"
        elif automation_type == 'mood_check_ins':
            notification_api_instance.automation.schedule_mood_check_ins()
            message = "Mood check-ins scheduled"
        else:
            return jsonify({"error": "Invalid automation type"}), 400
        
        return jsonify({
            "message": message,
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error triggering automation: {e}")
        return jsonify({"error": str(e)}), 500

# WebSocket support for real-time notifications (placeholder)
class NotificationWebSocket:
    """WebSocket handler for real-time notifications"""
    
    def __init__(self, notification_manager: NotificationManager):
        self.notification_manager = notification_manager
        self.connected_users: Dict[str, Any] = {}
    
    def connect_user(self, user_id: str, websocket):
        """Connect user to WebSocket for real-time notifications"""
        self.connected_users[user_id] = websocket
        logger.info(f"User {user_id} connected to notification WebSocket")
    
    def disconnect_user(self, user_id: str):
        """Disconnect user from WebSocket"""
        if user_id in self.connected_users:
            del self.connected_users[user_id]
            logger.info(f"User {user_id} disconnected from notification WebSocket")
    
    def send_real_time_notification(self, user_id: str, notification_data: Dict[str, Any]):
        """Send real-time notification to connected user"""
        if user_id in self.connected_users:
            try:
                websocket = self.connected_users[user_id]
                # Send notification data through WebSocket
                # Implementation would depend on your WebSocket library
                logger.info(f"Real-time notification sent to user {user_id}")
                return True
            except Exception as e:
                logger.error(f"Error sending real-time notification: {e}")
                # Remove disconnected user
                self.disconnect_user(user_id)
        
        return False

# Database schema initialization
def init_notification_database(db_connection):
    """Initialize notification-related database tables"""
    cursor = db_connection.cursor()
    
    # Notifications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT NOT NULL,
            priority TEXT NOT NULL,
            channels TEXT NOT NULL,
            data TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            read_at TEXT,
            delivered_at TEXT,
            failed_channels TEXT,
            retry_count INTEGER DEFAULT 0,
            is_persistent BOOLEAN DEFAULT 1,
            action_url TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Notification preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_preferences (
            user_id TEXT PRIMARY KEY,
            email_enabled BOOLEAN DEFAULT 1,
            push_enabled BOOLEAN DEFAULT 1,
            sms_enabled BOOLEAN DEFAULT 0,
            in_app_enabled BOOLEAN DEFAULT 1,
            quiet_hours_start TEXT DEFAULT '22:00',
            quiet_hours_end TEXT DEFAULT '08:00',
            frequency_limit INTEGER DEFAULT 10,
            priority_threshold TEXT DEFAULT 'low',
            blocked_types TEXT DEFAULT '[]',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Notification delivery log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_delivery_log (
            id TEXT PRIMARY KEY,
            notification_id TEXT NOT NULL,
            channel TEXT NOT NULL,
            status TEXT NOT NULL,
            delivered_at TEXT,
            error_message TEXT,
            FOREIGN KEY (notification_id) REFERENCES notifications (id)
        )
    """)
    
    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_user_id 
        ON notifications (user_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_created_at 
        ON notifications (created_at)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_read_at 
        ON notifications (read_at)
    """)
    
    db_connection.commit()
    logger.info("Notification database schema initialized")