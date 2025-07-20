"""
Real-time Features & WebSocket Infrastructure for SoulBridge AI
Provides WebSocket communication, live notifications, and collaborative features
"""

import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict
from dataclasses import dataclass, asdict
from flask import request, session
from functools import wraps

# Make Flask-SocketIO optional for environments where it's not available
try:
    from flask_socketio import SocketIO, emit, join_room, leave_room, rooms, disconnect
    SOCKETIO_AVAILABLE = True
except ImportError:
    # Create mock objects for testing/environments without SocketIO
    SocketIO = None
    emit = lambda *args, **kwargs: None
    join_room = lambda *args, **kwargs: None
    leave_room = lambda *args, **kwargs: None
    rooms = lambda *args, **kwargs: []
    disconnect = lambda *args, **kwargs: None
    SOCKETIO_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class UserPresence:
    """User presence information"""
    user_id: str
    session_id: str
    status: str  # online, away, busy, offline
    last_seen: datetime
    current_room: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class LiveNotification:
    """Live notification structure"""
    notification_id: str
    user_id: str
    type: str
    title: str
    message: str
    data: Dict[str, Any]
    created_at: datetime
    read: bool = False
    expires_at: Optional[datetime] = None


@dataclass
class ChatMessage:
    """Real-time chat message"""
    message_id: str
    user_id: str
    room_id: str
    content: str
    message_type: str  # text, system, typing, status
    timestamp: datetime
    metadata: Dict[str, Any]


class RealTimeManager:
    """Manages real-time features and WebSocket connections"""
    
    def __init__(self, socketio: SocketIO, db_manager=None):
        self.socketio = socketio
        self.db = db_manager
        
        # In-memory stores for real-time data
        self.user_sessions: Dict[str, Set[str]] = defaultdict(set)  # user_id -> session_ids
        self.session_users: Dict[str, str] = {}  # session_id -> user_id
        self.user_presence: Dict[str, UserPresence] = {}
        self.room_members: Dict[str, Set[str]] = defaultdict(set)  # room_id -> user_ids
        self.typing_users: Dict[str, Dict[str, float]] = defaultdict(dict)  # room_id -> {user_id: timestamp}
        self.notifications: Dict[str, List[LiveNotification]] = defaultdict(list)  # user_id -> notifications
        
        # Setup SocketIO event handlers
        self._setup_event_handlers()
        
        # Cleanup task interval
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        
    def _setup_event_handlers(self):
        """Set up WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect(auth=None):
            """Handle client connection"""
            try:
                session_id = request.sid
                user_id = self._get_user_from_session()
                
                if not user_id:
                    logger.warning(f"Unauthenticated connection attempt: {session_id}")
                    return False
                
                # Store session mapping
                self.user_sessions[user_id].add(session_id)
                self.session_users[session_id] = user_id
                
                # Update presence
                self._update_user_presence(user_id, session_id, 'online')
                
                # Join user's personal room
                join_room(f"user_{user_id}")
                
                # Send pending notifications
                self._send_pending_notifications(user_id)
                
                # Broadcast presence update
                self._broadcast_presence_update(user_id, 'online')
                
                logger.info(f"User {user_id} connected with session {session_id}")
                
                emit('connection_confirmed', {
                    'user_id': user_id,
                    'session_id': session_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error handling connection: {e}")
                return False
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            try:
                session_id = request.sid
                user_id = self.session_users.get(session_id)
                
                if user_id:
                    # Remove session mapping
                    self.user_sessions[user_id].discard(session_id)
                    del self.session_users[session_id]
                    
                    # Update presence if no other sessions
                    if not self.user_sessions[user_id]:
                        self._update_user_presence(user_id, session_id, 'offline')
                        self._broadcast_presence_update(user_id, 'offline')
                    
                    # Clean up typing indicators
                    self._cleanup_typing_for_user(user_id)
                    
                    logger.info(f"User {user_id} disconnected session {session_id}")
                
            except Exception as e:
                logger.error(f"Error handling disconnection: {e}")
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """Handle joining a room"""
            try:
                room_id = data.get('room_id')
                user_id = self._get_user_from_session()
                
                if not user_id or not room_id:
                    emit('error', {'message': 'Invalid room join request'})
                    return
                
                # Validate room access
                if not self._can_access_room(user_id, room_id):
                    emit('error', {'message': 'Access denied to room'})
                    return
                
                join_room(room_id)
                self.room_members[room_id].add(user_id)
                
                # Update user presence
                if user_id in self.user_presence:
                    self.user_presence[user_id].current_room = room_id
                
                # Notify room members
                emit('user_joined_room', {
                    'user_id': user_id,
                    'room_id': room_id,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=room_id)
                
                logger.info(f"User {user_id} joined room {room_id}")
                
            except Exception as e:
                logger.error(f"Error handling room join: {e}")
                emit('error', {'message': 'Failed to join room'})
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """Handle leaving a room"""
            try:
                room_id = data.get('room_id')
                user_id = self._get_user_from_session()
                
                if not user_id or not room_id:
                    return
                
                leave_room(room_id)
                self.room_members[room_id].discard(user_id)
                
                # Update user presence
                if user_id in self.user_presence:
                    self.user_presence[user_id].current_room = None
                
                # Stop typing if user was typing
                self._stop_typing(user_id, room_id)
                
                # Notify room members
                emit('user_left_room', {
                    'user_id': user_id,
                    'room_id': room_id,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=room_id)
                
                logger.info(f"User {user_id} left room {room_id}")
                
            except Exception as e:
                logger.error(f"Error handling room leave: {e}")
        
        @self.socketio.on('typing_start')
        def handle_typing_start(data):
            """Handle typing indicator start"""
            try:
                room_id = data.get('room_id')
                user_id = self._get_user_from_session()
                
                if not user_id or not room_id:
                    return
                
                # Record typing
                self.typing_users[room_id][user_id] = time.time()
                
                # Broadcast typing indicator
                emit('user_typing', {
                    'user_id': user_id,
                    'room_id': room_id,
                    'is_typing': True
                }, room=room_id, include_self=False)
                
            except Exception as e:
                logger.error(f"Error handling typing start: {e}")
        
        @self.socketio.on('typing_stop')
        def handle_typing_stop(data):
            """Handle typing indicator stop"""
            try:
                room_id = data.get('room_id')
                user_id = self._get_user_from_session()
                
                if not user_id or not room_id:
                    return
                
                self._stop_typing(user_id, room_id)
                
            except Exception as e:
                logger.error(f"Error handling typing stop: {e}")
        
        @self.socketio.on('send_message')
        def handle_send_message(data):
            """Handle real-time message sending"""
            try:
                user_id = self._get_user_from_session()
                room_id = data.get('room_id')
                content = data.get('content', '').strip()
                message_type = data.get('type', 'text')
                
                if not user_id or not room_id or not content:
                    emit('error', {'message': 'Invalid message data'})
                    return
                
                # Validate room access
                if not self._can_access_room(user_id, room_id):
                    emit('error', {'message': 'Access denied to room'})
                    return
                
                # Create message
                message = ChatMessage(
                    message_id=f"msg_{uuid.uuid4().hex[:8]}",
                    user_id=user_id,
                    room_id=room_id,
                    content=content,
                    message_type=message_type,
                    timestamp=datetime.utcnow(),
                    metadata=data.get('metadata', {})
                )
                
                # Store message if database available
                if self.db:
                    self._store_message(message)
                
                # Stop typing indicator
                self._stop_typing(user_id, room_id)
                
                # Broadcast message
                emit('new_message', asdict(message), room=room_id)
                
                logger.info(f"Message sent by {user_id} in room {room_id}")
                
            except Exception as e:
                logger.error(f"Error handling message send: {e}")
                emit('error', {'message': 'Failed to send message'})
        
        @self.socketio.on('update_presence')
        def handle_update_presence(data):
            """Handle presence status update"""
            try:
                user_id = self._get_user_from_session()
                status = data.get('status', 'online')
                metadata = data.get('metadata', {})
                
                if not user_id:
                    return
                
                self._update_user_presence(user_id, request.sid, status, metadata)
                self._broadcast_presence_update(user_id, status, metadata)
                
            except Exception as e:
                logger.error(f"Error handling presence update: {e}")
        
        @self.socketio.on('ping')
        def handle_ping():
            """Handle ping for keepalive"""
            emit('pong', {'timestamp': datetime.utcnow().isoformat()})
    
    def _get_user_from_session(self) -> Optional[str]:
        """Get user ID from Flask session"""
        try:
            # Check Flask session for authenticated user
            if hasattr(session, 'get') and session.get('user_id'):
                return session.get('user_id')
            
            # Alternative: check custom auth header
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                # You could validate JWT token here
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user from session: {e}")
            return None
    
    def _can_access_room(self, user_id: str, room_id: str) -> bool:
        """Check if user can access a room"""
        try:
            # Basic room access logic - extend as needed
            if room_id.startswith(f"user_{user_id}"):
                return True  # User's personal room
            
            if room_id.startswith("chat_"):
                return True  # Public chat rooms
            
            if room_id.startswith("admin_"):
                # Check if user is admin
                return self._is_admin_user(user_id)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking room access: {e}")
            return False
    
    def _is_admin_user(self, user_id: str) -> bool:
        """Check if user is admin"""
        # Implement admin check logic
        # Could check database or session data
        return False
    
    def _update_user_presence(self, user_id: str, session_id: str, status: str, metadata: Dict = None):
        """Update user presence information"""
        try:
            self.user_presence[user_id] = UserPresence(
                user_id=user_id,
                session_id=session_id,
                status=status,
                last_seen=datetime.utcnow(),
                current_room=self.user_presence.get(user_id, UserPresence(user_id, session_id, status, datetime.utcnow(), None, {})).current_room,
                metadata=metadata or {}
            )
            
        except Exception as e:
            logger.error(f"Error updating user presence: {e}")
    
    def _broadcast_presence_update(self, user_id: str, status: str, metadata: Dict = None):
        """Broadcast presence update to relevant users"""
        try:
            presence_data = {
                'user_id': user_id,
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            # Broadcast to all rooms where user is a member
            for room_id, members in self.room_members.items():
                if user_id in members:
                    self.socketio.emit('presence_update', presence_data, room=room_id)
            
        except Exception as e:
            logger.error(f"Error broadcasting presence update: {e}")
    
    def _stop_typing(self, user_id: str, room_id: str):
        """Stop typing indicator for user in room"""
        try:
            if room_id in self.typing_users and user_id in self.typing_users[room_id]:
                del self.typing_users[room_id][user_id]
                
                # Broadcast typing stopped
                self.socketio.emit('user_typing', {
                    'user_id': user_id,
                    'room_id': room_id,
                    'is_typing': False
                }, room=room_id, include_self=False)
            
        except Exception as e:
            logger.error(f"Error stopping typing indicator: {e}")
    
    def _cleanup_typing_for_user(self, user_id: str):
        """Clean up typing indicators for disconnected user"""
        try:
            for room_id in list(self.typing_users.keys()):
                if user_id in self.typing_users[room_id]:
                    self._stop_typing(user_id, room_id)
                    
        except Exception as e:
            logger.error(f"Error cleaning up typing indicators: {e}")
    
    def _store_message(self, message: ChatMessage):
        """Store message in database"""
        try:
            if not self.db:
                return
            
            # Store in database - implement based on your schema
            # This would typically go in a messages table
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                INSERT INTO chat_messages (
                    message_id, user_id, room_id, content, message_type, 
                    timestamp, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    message.message_id,
                    message.user_id,
                    message.room_id,
                    message.content,
                    message.message_type,
                    message.timestamp,
                    json.dumps(message.metadata)
                )
            )
            
        except Exception as e:
            logger.error(f"Error storing message: {e}")
    
    def _send_pending_notifications(self, user_id: str):
        """Send pending notifications to newly connected user"""
        try:
            if user_id in self.notifications:
                for notification in self.notifications[user_id]:
                    if not notification.read and (not notification.expires_at or notification.expires_at > datetime.utcnow()):
                        self.socketio.emit('notification', asdict(notification), room=f"user_{user_id}")
            
        except Exception as e:
            logger.error(f"Error sending pending notifications: {e}")
    
    # Public methods for sending notifications and messages
    
    def send_notification(self, user_id: str, notification_type: str, title: str, message: str, data: Dict = None):
        """Send real-time notification to user"""
        try:
            notification = LiveNotification(
                notification_id=f"notif_{uuid.uuid4().hex[:8]}",
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                data=data or {},
                created_at=datetime.utcnow()
            )
            
            # Store notification
            self.notifications[user_id].append(notification)
            
            # Send immediately if user is online
            if user_id in self.user_sessions and self.user_sessions[user_id]:
                self.socketio.emit('notification', asdict(notification), room=f"user_{user_id}")
            
            logger.info(f"Notification sent to {user_id}: {title}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def broadcast_to_room(self, room_id: str, event: str, data: Dict):
        """Broadcast event to all users in room"""
        try:
            self.socketio.emit(event, data, room=room_id)
            logger.info(f"Broadcasted {event} to room {room_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting to room: {e}")
    
    def broadcast_to_admins(self, event: str, data: Dict):
        """Broadcast event to all admin users"""
        try:
            self.socketio.emit(event, data, room="admin_room")
            logger.info(f"Broadcasted {event} to admins")
            
        except Exception as e:
            logger.error(f"Error broadcasting to admins: {e}")
    
    def get_online_users(self) -> List[Dict]:
        """Get list of currently online users"""
        try:
            online_users = []
            for user_id, presence in self.user_presence.items():
                if presence.status == 'online' and user_id in self.user_sessions:
                    online_users.append({
                        'user_id': user_id,
                        'status': presence.status,
                        'last_seen': presence.last_seen.isoformat(),
                        'current_room': presence.current_room,
                        'session_count': len(self.user_sessions[user_id])
                    })
            
            return online_users
            
        except Exception as e:
            logger.error(f"Error getting online users: {e}")
            return []
    
    def cleanup_stale_data(self):
        """Clean up stale typing indicators and old notifications"""
        try:
            current_time = time.time()
            
            # Skip if cleanup was recent
            if current_time - self.last_cleanup < self.cleanup_interval:
                return
            
            # Clean up stale typing indicators (older than 30 seconds)
            typing_timeout = 30
            for room_id in list(self.typing_users.keys()):
                for user_id in list(self.typing_users[room_id].keys()):
                    if current_time - self.typing_users[room_id][user_id] > typing_timeout:
                        self._stop_typing(user_id, room_id)
            
            # Clean up old notifications (older than 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            for user_id in list(self.notifications.keys()):
                self.notifications[user_id] = [
                    notif for notif in self.notifications[user_id]
                    if notif.created_at > cutoff_time
                ]
            
            self.last_cleanup = current_time
            logger.info("Completed real-time data cleanup")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global real-time manager instance
realtime_manager = None


def init_realtime_features(app, socketio: SocketIO = None, db_manager=None):
    """Initialize real-time features for Flask app"""
    global realtime_manager
    
    if not SOCKETIO_AVAILABLE:
        logger.warning("Flask-SocketIO not available - real-time features disabled")
        return None
    
    if not socketio:
        logger.warning("No SocketIO instance provided - real-time features disabled")
        return None
    
    realtime_manager = RealTimeManager(socketio, db_manager)
    
    # Add periodic cleanup task
    @socketio.on('connect')
    def trigger_cleanup():
        if realtime_manager:
            realtime_manager.cleanup_stale_data()
    
    logger.info("Real-time features initialized with WebSocket support")
    
    return realtime_manager