"""
SoulBridge AI - Message Handler
Handles message processing, validation, and usage tracking for chat
Extracted from monolith app.py with improvements
"""
import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from database_utils import format_query

logger = logging.getLogger(__name__)

class MessageHandler:
    """Handles message processing and validation"""
    
    def __init__(self):
        self.rate_limits = {
            'bronze': {'messages_per_hour': 30, 'max_message_length': 500},
            'silver': {'messages_per_hour': 100, 'max_message_length': 1000}, 
            'gold': {'messages_per_hour': 999, 'max_message_length': 2000}
        }
        
    def validate_message(self, message: str, user_id: int, user_plan: str, 
                        trial_active: bool = False) -> Dict[str, Any]:
        """Validate incoming chat message"""
        try:
            # Get effective plan for limits
            effective_plan = 'gold' if (trial_active and user_plan == 'bronze') else user_plan
            limits = self.rate_limits.get(effective_plan, self.rate_limits['bronze'])
            
            # Basic validation
            if not message or not message.strip():
                return {"valid": False, "error": "Message cannot be empty"}
            
            message = message.strip()
            
            # Length validation
            if len(message) > limits['max_message_length']:
                return {
                    "valid": False, 
                    "error": f"Message too long (max {limits['max_message_length']} characters for {effective_plan} tier)"
                }
            
            # Content validation
            if self._contains_inappropriate_content(message):
                return {"valid": False, "error": "Message contains inappropriate content"}
            
            # Rate limiting
            rate_check = self._check_rate_limit(user_id, effective_plan)
            if not rate_check["allowed"]:
                return {
                    "valid": False,
                    "error": f"Rate limit exceeded. Try again in {rate_check['reset_minutes']} minutes."
                }
            
            # Spam detection
            if self._is_spam_message(message, user_id):
                return {"valid": False, "error": "Message appears to be spam"}
            
            return {
                "valid": True,
                "cleaned_message": message,
                "effective_plan": effective_plan,
                "message_length": len(message)
            }
            
        except Exception as e:
            logger.error(f"Error validating message: {e}")
            return {"valid": False, "error": "Message validation failed"}
    
    def _contains_inappropriate_content(self, message: str) -> bool:
        """Basic inappropriate content filter"""
        try:
            # Simple keyword-based filtering
            inappropriate_patterns = [
                r'\b(spam|scam|click here|buy now|urgent|winner)\b',
                r'https?://(?!(?:www\.)?(?:soulbridgeai\.com|localhost))',  # External links
                r'\b\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{4}\b',  # Phone numbers
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            ]
            
            for pattern in inappropriate_patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking inappropriate content: {e}")
            return False
    
    def _check_rate_limit(self, user_id: int, user_plan: str) -> Dict[str, Any]:
        """Check if user has exceeded rate limits"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {"allowed": True}  # Allow if can't check
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Check messages in last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT COUNT(*) FROM chat_conversations 
                    WHERE user_id = %s AND created_at >= %s
                """, (user_id, one_hour_ago))
            else:
                cursor.execute(format_query("""
                    SELECT COUNT(*) FROM chat_conversations 
                    WHERE user_id = ? AND created_at >= ?
                """), (user_id, one_hour_ago.isoformat()))
            
            message_count = cursor.fetchone()[0]
            conn.close()
            
            limits = self.rate_limits.get(user_plan, self.rate_limits['bronze'])
            messages_allowed = limits['messages_per_hour']
            
            if message_count >= messages_allowed:
                return {
                    "allowed": False,
                    "messages_sent": message_count,
                    "limit": messages_allowed,
                    "reset_minutes": 60
                }
            
            return {
                "allowed": True,
                "messages_sent": message_count,
                "limit": messages_allowed,
                "remaining": messages_allowed - message_count
            }
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return {"allowed": True}  # Allow if error checking
    
    def _is_spam_message(self, message: str, user_id: int) -> bool:
        """Detect spam messages"""
        try:
            # Check for repeated messages
            if self._is_repeated_message(message, user_id):
                return True
            
            # Check for excessive capitals
            if len(message) > 20 and sum(1 for c in message if c.isupper()) / len(message) > 0.7:
                return True
            
            # Check for excessive repetition within message
            words = message.lower().split()
            if len(words) > 3:
                unique_words = set(words)
                if len(unique_words) / len(words) < 0.5:  # Less than 50% unique words
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking spam: {e}")
            return False
    
    def _is_repeated_message(self, message: str, user_id: int) -> bool:
        """Check if user is sending the same message repeatedly"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return False
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Check last 5 messages
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT user_message FROM chat_conversations
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 5
                """, (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT user_message FROM chat_conversations
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT 5
                """), (user_id,))
            
            recent_messages = [row[0].lower().strip() for row in cursor.fetchall()]
            conn.close()
            
            # Check if current message matches recent ones
            message_lower = message.lower().strip()
            repeated_count = sum(1 for msg in recent_messages if msg == message_lower)
            
            return repeated_count >= 3  # Spam if same message 3+ times in last 5
            
        except Exception as e:
            logger.error(f"Error checking repeated message: {e}")
            return False
    
    def track_message_usage(self, user_id: int, companion_id: str, message_length: int, 
                          model_used: str, tokens_used: Optional[int] = None) -> bool:
        """Track message usage for analytics"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return False
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Insert usage record
            usage_data = {
                'user_id': user_id,
                'companion_id': companion_id,
                'message_length': message_length,
                'model_used': model_used,
                'tokens_used': tokens_used,
                'timestamp': datetime.now()
            }
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO chat_usage_tracking
                    (user_id, companion_id, message_length, model_used, tokens_used, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    user_id, companion_id, message_length,
                    model_used, tokens_used, usage_data['timestamp']
                ))
            else:
                cursor.execute(format_query("""
                    INSERT INTO chat_usage_tracking
                    (user_id, companion_id, message_length, model_used, tokens_used, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """), (
                    user_id, companion_id, message_length,
                    model_used, tokens_used, usage_data['timestamp'].isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"📊 Tracked usage: User {user_id}, {message_length} chars, {model_used}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking message usage: {e}")
            return False
    
    def get_user_message_stats(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """Get user's message statistics"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_messages,
                        AVG(LENGTH(user_message)) as avg_message_length,
                        COUNT(DISTINCT companion_id) as companions_used,
                        COUNT(DISTINCT DATE(created_at)) as active_days
                    FROM chat_conversations 
                    WHERE user_id = %s AND created_at >= %s
                """, (user_id, start_date))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        COUNT(*) as total_messages,
                        AVG(LENGTH(user_message)) as avg_message_length,
                        COUNT(DISTINCT companion_id) as companions_used,
                        COUNT(DISTINCT DATE(created_at)) as active_days
                    FROM chat_conversations 
                    WHERE user_id = ? AND created_at >= ?
                """), (user_id, start_date.isoformat()))
            
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0] > 0:
                return {
                    "period_days": days,
                    "total_messages": row[0],
                    "avg_message_length": round(row[1], 1) if row[1] else 0,
                    "companions_used": row[2],
                    "active_days": row[3],
                    "messages_per_day": round(row[0] / max(row[3], 1), 1)
                }
            else:
                return {
                    "period_days": days,
                    "total_messages": 0,
                    "avg_message_length": 0,
                    "companions_used": 0,
                    "active_days": 0,
                    "messages_per_day": 0
                }
                
        except Exception as e:
            logger.error(f"Error getting message stats: {e}")
            return {}
    
    def get_rate_limit_info(self, user_id: int, user_plan: str) -> Dict[str, Any]:
        """Get current rate limit status for user"""
        try:
            rate_check = self._check_rate_limit(user_id, user_plan)
            limits = self.rate_limits.get(user_plan, self.rate_limits['bronze'])
            
            return {
                "tier": user_plan,
                "hourly_limit": limits['messages_per_hour'],
                "max_message_length": limits['max_message_length'],
                "current_usage": rate_check.get('messages_sent', 0),
                "remaining": rate_check.get('remaining', 0),
                "rate_limited": not rate_check.get('allowed', True),
                "reset_minutes": rate_check.get('reset_minutes', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            return {}