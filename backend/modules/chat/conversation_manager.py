"""
SoulBridge AI - Conversation Manager
Manages conversation state, history, and context for chat sessions
Extracted from monolith app.py with improvements
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from database_utils import format_query

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages conversation context and state"""
    
    def __init__(self):
        self.active_sessions = {}  # In-memory session storage
        
    def start_conversation_session(self, user_id: int, companion_id: str) -> str:
        """Start a new conversation session"""
        try:
            session_id = f"{user_id}_{companion_id}_{int(datetime.now().timestamp())}"
            
            self.active_sessions[session_id] = {
                'user_id': user_id,
                'companion_id': companion_id,
                'started_at': datetime.now(),
                'last_activity': datetime.now(),
                'message_count': 0,
                'context': {}
            }
            
            logger.info(f"🗣️ Started conversation session {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting conversation session: {e}")
            return None
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update last activity for a session"""
        try:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['last_activity'] = datetime.now()
                self.active_sessions[session_id]['message_count'] += 1
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
            return False
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get context for a conversation session"""
        try:
            if session_id in self.active_sessions:
                return self.active_sessions[session_id]['context']
            return {}
            
        except Exception as e:
            logger.error(f"Error getting session context: {e}")
            return {}
    
    def set_session_context(self, session_id: str, context_key: str, context_value: Any) -> bool:
        """Set context value for a session"""
        try:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['context'][context_key] = context_value
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error setting session context: {e}")
            return False
    
    def end_conversation_session(self, session_id: str) -> bool:
        """End a conversation session"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                duration = datetime.now() - session['started_at']
                
                logger.info(f"🔚 Ended conversation session {session_id} - Duration: {duration}, Messages: {session['message_count']}")
                
                # Save session summary to database
                self._save_session_summary(session_id, session, duration)
                
                del self.active_sessions[session_id]
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error ending conversation session: {e}")
            return False
    
    def cleanup_inactive_sessions(self, max_inactive_hours: int = 2) -> int:
        """Clean up inactive sessions"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_inactive_hours)
            inactive_sessions = []
            
            for session_id, session in self.active_sessions.items():
                if session['last_activity'] < cutoff_time:
                    inactive_sessions.append(session_id)
            
            # End inactive sessions
            for session_id in inactive_sessions:
                self.end_conversation_session(session_id)
            
            logger.info(f"🧹 Cleaned up {len(inactive_sessions)} inactive conversation sessions")
            return len(inactive_sessions)
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive sessions: {e}")
            return 0
    
    def get_conversation_summary(self, user_id: int, companion_id: str, days: int = 7) -> Dict[str, Any]:
        """Get conversation summary for recent period"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {"total_messages": 0, "conversation_days": 0}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get recent conversation stats
            start_date = datetime.now() - timedelta(days=days)
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_messages,
                        COUNT(DISTINCT DATE(created_at)) as conversation_days,
                        MIN(created_at) as first_message,
                        MAX(created_at) as last_message
                    FROM chat_conversations 
                    WHERE user_id = %s AND companion_id = %s 
                    AND created_at >= %s
                """, (user_id, companion_id, start_date))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        COUNT(*) as total_messages,
                        COUNT(DISTINCT DATE(created_at)) as conversation_days,
                        MIN(created_at) as first_message,
                        MAX(created_at) as last_message
                    FROM chat_conversations 
                    WHERE user_id = ? AND companion_id = ? 
                    AND created_at >= ?
                """), (user_id, companion_id, start_date.isoformat()))
            
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0] > 0:
                return {
                    "total_messages": row[0],
                    "conversation_days": row[1],
                    "first_message": row[2],
                    "last_message": row[3],
                    "period_days": days
                }
            else:
                return {"total_messages": 0, "conversation_days": 0, "period_days": days}
                
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return {"total_messages": 0, "conversation_days": 0, "period_days": days}
    
    def get_active_sessions_count(self) -> int:
        """Get count of active conversation sessions"""
        return len(self.active_sessions)
    
    def get_user_active_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get active sessions for a specific user"""
        try:
            user_sessions = []
            
            for session_id, session in self.active_sessions.items():
                if session['user_id'] == user_id:
                    user_sessions.append({
                        'session_id': session_id,
                        'companion_id': session['companion_id'],
                        'started_at': session['started_at'],
                        'last_activity': session['last_activity'],
                        'message_count': session['message_count']
                    })
            
            return user_sessions
            
        except Exception as e:
            logger.error(f"Error getting user active sessions: {e}")
            return []
    
    def _save_session_summary(self, session_id: str, session: Dict[str, Any], duration: timedelta):
        """Save session summary to database"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Save session summary
            summary_data = {
                'session_id': session_id,
                'user_id': session['user_id'],
                'companion_id': session['companion_id'],
                'started_at': session['started_at'].isoformat(),
                'duration_seconds': int(duration.total_seconds()),
                'message_count': session['message_count'],
                'context': session['context']
            }
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO conversation_sessions
                    (session_id, user_id, companion_id, started_at, duration_seconds, message_count, context_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id) DO NOTHING
                """, (
                    session_id,
                    session['user_id'],
                    session['companion_id'],
                    session['started_at'],
                    int(duration.total_seconds()),
                    session['message_count'],
                    json.dumps(session['context'])
                ))
            else:
                cursor.execute(format_query("""
                    INSERT OR IGNORE INTO conversation_sessions 
                    (session_id, user_id, companion_id, started_at, duration_seconds, message_count, context_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """), (
                    session_id,
                    session['user_id'],
                    session['companion_id'],
                    session['started_at'].isoformat(),
                    int(duration.total_seconds()),
                    session['message_count'],
                    json.dumps(session['context'])
                ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"💾 Saved session summary for {session_id}")
            
        except Exception as e:
            logger.error(f"Error saving session summary: {e}")
    
    def get_conversation_insights(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get conversation insights and patterns"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Get conversation patterns
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        companion_id,
                        COUNT(*) as message_count,
                        COUNT(DISTINCT DATE(created_at)) as active_days,
                        AVG(LENGTH(user_message)) as avg_message_length
                    FROM chat_conversations 
                    WHERE user_id = %s AND created_at >= %s
                    GROUP BY companion_id
                    ORDER BY message_count DESC
                """, (user_id, start_date))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        companion_id,
                        COUNT(*) as message_count,
                        COUNT(DISTINCT DATE(created_at)) as active_days,
                        AVG(LENGTH(user_message)) as avg_message_length
                    FROM chat_conversations 
                    WHERE user_id = ? AND created_at >= ?
                    GROUP BY companion_id
                    ORDER BY message_count DESC
                """), (user_id, start_date.isoformat()))
            
            companion_stats = cursor.fetchall()
            conn.close()
            
            # Format insights
            insights = {
                "period_days": days,
                "total_companions": len(companion_stats),
                "companions": []
            }
            
            total_messages = sum(row[1] for row in companion_stats)
            
            for row in companion_stats:
                companion_id, msg_count, active_days, avg_length = row
                
                insights["companions"].append({
                    "companion_id": companion_id,
                    "message_count": msg_count,
                    "active_days": active_days,
                    "avg_message_length": round(avg_length, 1) if avg_length else 0,
                    "percentage_of_conversations": round((msg_count / total_messages) * 100, 1) if total_messages > 0 else 0
                })
            
            insights["total_messages"] = total_messages
            return insights
            
        except Exception as e:
            logger.error(f"Error getting conversation insights: {e}")
            return {}