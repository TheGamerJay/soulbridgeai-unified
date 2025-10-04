# Notification Scheduler for Automated Tasks
import os
import logging
import threading
import time
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from notification_system import NotificationManager, NotificationTemplate, NotificationAutomation
from database_utils import format_query

logger = logging.getLogger(__name__)

class NotificationScheduler:
    """Automated notification scheduler"""
    
    def __init__(self, notification_manager: NotificationManager, db_manager=None):
        self.notification_manager = notification_manager
        self.db = db_manager
        self.automation = NotificationAutomation(notification_manager, db_manager)
        self.is_running = False
        self.scheduler_thread = None
        
        # Configure scheduled tasks
        self._setup_schedules()
    
    def _setup_schedules(self):
        """Setup all scheduled notification tasks"""
        
        # Daily mood check-ins at 9 AM
        schedule.every().day.at("09:00").do(self._schedule_mood_check_ins)
        
        # Conversation reminders - every 6 hours
        schedule.every(6).hours.do(self._schedule_conversation_reminders)
        
        # Weekly engagement summary - Sundays at 10 AM
        schedule.every().sunday.at("10:00").do(self._schedule_weekly_summaries)
        
        # Daily AI insights - every day at 7 PM
        schedule.every().day.at("19:00").do(self._schedule_daily_insights)
        
        # Cleanup expired notifications - every hour
        schedule.every().hour.do(self._cleanup_expired_notifications)
        
        # User retention campaigns - Tuesdays and Fridays at 2 PM
        schedule.every().tuesday.at("14:00").do(self._schedule_retention_campaigns)
        schedule.every().friday.at("14:00").do(self._schedule_retention_campaigns)
        
        logger.info("Notification scheduler configured with automated tasks")
    
    def start(self):
        """Start the notification scheduler"""
        if self.is_running:
            logger.warning("Notification scheduler is already running")
            return
        
        self.is_running = True
        
        def run_scheduler():
            logger.info("Notification scheduler started")
            while self.is_running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Error in notification scheduler: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
            
            logger.info("Notification scheduler stopped")
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop(self):
        """Stop the notification scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Notification scheduler stopped")
    
    def _schedule_mood_check_ins(self):
        """Schedule daily mood check-in notifications"""
        try:
            logger.info("Scheduling daily mood check-ins")
            self.automation.schedule_mood_check_ins()
        except Exception as e:
            logger.error(f"Error scheduling mood check-ins: {e}")
    
    def _schedule_conversation_reminders(self):
        """Schedule conversation reminder notifications"""
        try:
            logger.info("Scheduling conversation reminders")
            self.automation.schedule_conversation_reminders()
        except Exception as e:
            logger.error(f"Error scheduling conversation reminders: {e}")
    
    def _schedule_weekly_summaries(self):
        """Schedule weekly engagement summaries"""
        try:
            logger.info("Scheduling weekly engagement summaries")
            
            if not self.db:
                return
            
            cursor = self.db.connection.cursor()
            
            # Get active users from the past week
            cursor.execute("""
                SELECT DISTINCT u.id, u.display_name, COUNT(c.id) as conversation_count
                FROM users u
                LEFT JOIN conversations c ON u.id = c.user_id 
                    AND c.created_at > datetime('now', '-7 days')
                WHERE u.created_at < datetime('now', '-7 days')
                GROUP BY u.id, u.display_name
                HAVING conversation_count > 0
            """)
            
            for row in cursor.fetchall():
                user_id, display_name, conversation_count = row
                
                summary_message = f"""
                Hi {display_name or 'there'}! 
                
                Here's your weekly recap:
                • You had {conversation_count} meaningful conversations this week
                • Your emotional journey continues to evolve
                • Keep up the great progress with your AI companions!
                
                Ready for another week of growth and connection?
                """.strip()
                
                notification = NotificationTemplate.ai_insight(user_id, summary_message)
                notification.title = "Your Weekly Journey Recap"
                self.notification_manager.create_notification(notification)
            
            logger.info("Weekly summaries scheduled successfully")
            
        except Exception as e:
            logger.error(f"Error scheduling weekly summaries: {e}")
    
    def _schedule_daily_insights(self):
        """Schedule daily AI-generated insights"""
        try:
            logger.info("Scheduling daily AI insights")
            
            if not self.db:
                return
            
            cursor = self.db.connection.cursor()
            
            # Get users who had conversations today
            cursor.execute("""
                SELECT DISTINCT u.id, u.display_name
                FROM users u
                INNER JOIN conversations c ON u.id = c.user_id
                WHERE DATE(c.created_at) = DATE('now')
            """)
            
            insights = [
                "Remember that every conversation is a step toward better emotional understanding.",
                "Your willingness to explore your feelings shows incredible courage and self-awareness.",
                "Small daily check-ins with yourself can lead to profound personal growth.",
                "The journey of self-discovery is unique to you - embrace your own pace.",
                "Your emotional intelligence grows stronger with each meaningful conversation.",
                "Taking time for reflection today can bring clarity to tomorrow's challenges.",
                "Your openness to AI companionship shows an innovative approach to wellbeing.",
                "Every question you ask about yourself brings you closer to authentic living."
            ]
            
            import random
            
            for row in cursor.fetchall():
                user_id, display_name = row
                
                # Select a random insight
                insight = random.choice(insights)
                
                notification = NotificationTemplate.ai_insight(user_id, insight)
                self.notification_manager.create_notification(notification)
            
            logger.info("Daily insights scheduled successfully")
            
        except Exception as e:
            logger.error(f"Error scheduling daily insights: {e}")
    
    def _schedule_retention_campaigns(self):
        """Schedule user retention campaigns"""
        try:
            logger.info("Scheduling retention campaigns")
            
            if not self.db:
                return
            
            cursor = self.db.connection.cursor()
            
            # Find users at risk of churning (no activity in 7+ days but were active before)
            cursor.execute("""
                SELECT u.id, u.display_name, u.email
                FROM users u
                WHERE u.id NOT IN (
                    SELECT user_id FROM conversations 
                    WHERE created_at > datetime('now', '-7 days')
                )
                AND u.id IN (
                    SELECT user_id FROM conversations 
                    WHERE created_at > datetime('now', '-30 days')
                )
                AND u.created_at < datetime('now', '-7 days')
            """)
            
            retention_messages = [
                "We miss you! Your AI companions are wondering how you've been. Come back for a quick chat.",
                "Life gets busy, but taking a moment for yourself is always worth it. Your companions are here when you're ready.",
                "Remember that conversation you had last week? Your AI companion learned something new about helping people like you.",
                "Sometimes the best conversations happen when we need them most. Your AI friends are just a click away.",
                "Your emotional journey doesn't have to pause. Come back and continue where you left off."
            ]
            
            import random
            
            for row in cursor.fetchall():
                user_id, display_name, email = row
                
                message = random.choice(retention_messages)
                
                notification = NotificationTemplate.conversation_reminder(user_id, "your AI companion")
                notification.title = "We miss you at SoulBridge AI"
                notification.message = message
                self.notification_manager.create_notification(notification)
            
            logger.info("Retention campaigns scheduled successfully")
            
        except Exception as e:
            logger.error(f"Error scheduling retention campaigns: {e}")
    
    def _cleanup_expired_notifications(self):
        """Clean up expired notifications"""
        try:
            logger.info("Cleaning up expired notifications")
            
            if not self.db:
                return
            
            cursor = self.db.connection.cursor()
            
            # Delete expired notifications
            cursor.execute("""
                DELETE FROM notifications 
                WHERE expires_at IS NOT NULL 
                AND expires_at < datetime('now')
                AND is_persistent = 0
            """)
            
            deleted_count = cursor.rowcount
            self.db.connection.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired notifications")
            
        except Exception as e:
            logger.error(f"Error cleaning up notifications: {e}")
    
    def schedule_custom_notification(self, user_id: str, notification_type: str, delay_minutes: int = 0):
        """Schedule a custom notification for a specific user"""
        try:
            def send_notification():
                if notification_type == "welcome":
                    # Welcome notification for new users
                    notification = NotificationTemplate.ai_insight(
                        user_id,
                        "Welcome to SoulBridge AI! Your journey toward better emotional understanding starts here. Feel free to start a conversation with Blayzo or Blayzica whenever you're ready."
                    )
                    notification.title = "Welcome to SoulBridge AI!"
                    
                elif notification_type == "first_conversation":
                    # Encouragement after first conversation
                    notification = NotificationTemplate.ai_insight(
                        user_id,
                        "Great job on your first conversation! The more you chat with your AI companions, the better they'll understand how to support you."
                    )
                    notification.title = "You're off to a great start!"
                    
                elif notification_type == "milestone":
                    # Milestone celebration
                    notification = NotificationTemplate.ai_insight(
                        user_id,
                        "Congratulations! You've reached an important milestone in your emotional journey. Your commitment to self-reflection is inspiring."
                    )
                    notification.title = "Milestone Achievement!"
                    
                else:
                    logger.warning(f"Unknown notification type: {notification_type}")
                    return
                
                self.notification_manager.create_notification(notification)
                logger.info(f"Custom notification sent to user {user_id}: {notification_type}")
            
            if delay_minutes > 0:
                # Schedule for later
                timer = threading.Timer(delay_minutes * 60, send_notification)
                timer.start()
                logger.info(f"Scheduled {notification_type} notification for user {user_id} in {delay_minutes} minutes")
            else:
                # Send immediately
                send_notification()
        
        except Exception as e:
            logger.error(f"Error scheduling custom notification: {e}")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status and statistics"""
        try:
            return {
                "is_running": self.is_running,
                "scheduled_jobs": len(schedule.jobs),
                "next_run": str(schedule.next_run()) if schedule.jobs else None,
                "job_details": [
                    {
                        "function": job.job_func.__name__,
                        "interval": str(job.interval),
                        "unit": job.unit,
                        "next_run": str(job.next_run)
                    }
                    for job in schedule.jobs
                ]
            }
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {"error": str(e)}

# Global scheduler instance
notification_scheduler_instance = None

def init_notification_scheduler(notification_manager: NotificationManager, db_manager=None):
    """Initialize and start the notification scheduler"""
    global notification_scheduler_instance
    
    try:
        notification_scheduler_instance = NotificationScheduler(notification_manager, db_manager)
        notification_scheduler_instance.start()
        logger.info("Notification scheduler initialized and started")
        return notification_scheduler_instance
    except Exception as e:
        logger.error(f"Error initializing notification scheduler: {e}")
        return None

def get_notification_scheduler():
    """Get the global notification scheduler instance"""
    return notification_scheduler_instance