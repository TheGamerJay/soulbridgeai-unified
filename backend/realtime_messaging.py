"""
Real-Time Messaging System with WebSocket Support
Live messaging, typing indicators, read receipts, and real-time notifications
"""
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from flask import session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)

@dataclass
class OnlineUser:
    user_id: str
    socket_id: str
    last_seen: datetime
    current_mood: Optional[str] = None
    status: str = "online"  # online, away, busy, invisible

@dataclass
class TypingEvent:
    conversation_id: str
    user_id: str
    username: str
    timestamp: datetime

@dataclass
class ReadReceipt:
    message_id: str
    user_id: str
    read_at: datetime

class RealtimeMessaging:
    def __init__(self, socketio: SocketIO, social_manager=None, notification_manager=None):
        self.socketio = socketio
        self.social_manager = social_manager
        self.notification_manager = notification_manager
        
        # Track online users and their activities
        self.online_users: Dict[str, OnlineUser] = {}  # user_id -> OnlineUser
        self.user_sockets: Dict[str, str] = {}  # socket_id -> user_id
        self.user_rooms: Dict[str, Set[str]] = {}  # user_id -> set of room_ids
        
        # Track typing indicators
        self.typing_users: Dict[str, Dict[str, TypingEvent]] = {}  # conversation_id -> {user_id -> TypingEvent}
        
        # Initialize WebSocket event handlers
        self._register_handlers()
        
        logger.info("Real-time messaging system initialized")
    
    def _register_handlers(self):
        """Register all WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle new WebSocket connection"""
            try:
                # Check authentication
                if 'user_id' not in session:
                    logger.warning(f"Unauthenticated WebSocket connection attempt from {request.sid}")
                    disconnect()
                    return False
                
                user_id = session['user_id']
                socket_id = request.sid
                
                # Add user to online users
                self.online_users[user_id] = OnlineUser(
                    user_id=user_id,
                    socket_id=socket_id,
                    last_seen=datetime.now(),
                    status="online"
                )
                self.user_sockets[socket_id] = user_id
                self.user_rooms[user_id] = set()
                
                # Join user's personal room for direct notifications
                join_room(f"user_{user_id}")
                
                # Notify friends that user came online
                self._broadcast_user_status(user_id, "online")
                
                logger.info(f"User {user_id} connected with socket {socket_id}")
                
                # Send initial data
                emit('connection_established', {
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat(),
                    'online_friends': self._get_online_friends(user_id)
                })
                
            except Exception as e:
                logger.error(f"Error in connect handler: {e}")
                disconnect()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle WebSocket disconnection"""
            try:
                socket_id = request.sid
                user_id = self.user_sockets.get(socket_id)
                
                if user_id:
                    # Remove from online users
                    if user_id in self.online_users:
                        del self.online_users[user_id]
                    
                    if socket_id in self.user_sockets:
                        del self.user_sockets[socket_id]
                    
                    # Clear typing indicators
                    self._clear_user_typing(user_id)
                    
                    # Leave all rooms
                    if user_id in self.user_rooms:
                        for room in self.user_rooms[user_id]:
                            leave_room(room)
                        del self.user_rooms[user_id]
                    
                    # Notify friends that user went offline
                    self._broadcast_user_status(user_id, "offline")
                    
                    logger.info(f"User {user_id} disconnected")
                
            except Exception as e:
                logger.error(f"Error in disconnect handler: {e}")
        
        @self.socketio.on('join_conversation')
        def handle_join_conversation(data):
            """Join a conversation room for real-time messaging"""
            try:
                user_id = session.get('user_id')
                conversation_id = data.get('conversation_id')
                
                if not user_id or not conversation_id:
                    emit('error', {'message': 'Invalid join request'})
                    return
                
                # Verify user has access to this conversation
                if self.social_manager:
                    # Get conversation to verify access
                    conv_query = "SELECT user1_id, user2_id FROM conversations WHERE id = ?"
                    conv_result = self.social_manager.db.fetch_one(conv_query, (conversation_id,))
                    
                    if not conv_result or user_id not in [conv_result[0], conv_result[1]]:
                        emit('error', {'message': 'Access denied to conversation'})
                        return
                
                # Join the conversation room
                room_name = f"conversation_{conversation_id}"
                join_room(room_name)
                
                if user_id in self.user_rooms:
                    self.user_rooms[user_id].add(room_name)
                
                logger.info(f"User {user_id} joined conversation {conversation_id}")
                emit('conversation_joined', {'conversation_id': conversation_id})
                
                # Mark messages as read when joining
                if self.social_manager:
                    self.social_manager._mark_messages_as_read(user_id, conversation_id)
                
            except Exception as e:
                logger.error(f"Error joining conversation: {e}")
                emit('error', {'message': 'Failed to join conversation'})
        
        @self.socketio.on('leave_conversation')
        def handle_leave_conversation(data):
            """Leave a conversation room"""
            try:
                user_id = session.get('user_id')
                conversation_id = data.get('conversation_id')
                
                if not user_id or not conversation_id:
                    return
                
                room_name = f"conversation_{conversation_id}"
                leave_room(room_name)
                
                if user_id in self.user_rooms and room_name in self.user_rooms[user_id]:
                    self.user_rooms[user_id].remove(room_name)
                
                # Clear typing indicator
                self._clear_typing_in_conversation(conversation_id, user_id)
                
                logger.info(f"User {user_id} left conversation {conversation_id}")
                emit('conversation_left', {'conversation_id': conversation_id})
                
            except Exception as e:
                logger.error(f"Error leaving conversation: {e}")
        
        @self.socketio.on('send_message')
        def handle_send_message(data):
            """Handle real-time message sending"""
            try:
                user_id = session.get('user_id')
                
                if not user_id:
                    emit('error', {'message': 'Authentication required'})
                    return
                
                recipient_id = data.get('recipient_id')
                content = data.get('content', '').strip()
                message_type = data.get('message_type', 'text')
                metadata = data.get('metadata')
                
                if not recipient_id or not content:
                    emit('error', {'message': 'Recipient and content required'})
                    return
                
                # Use existing social manager to send message
                if not self.social_manager:
                    emit('error', {'message': 'Messaging system unavailable'})
                    return
                
                result = self.social_manager.send_message(user_id, recipient_id, content, message_type, metadata)
                
                if not result['success']:
                    emit('error', {'message': result['error']})
                    return
                
                # Get the full message data
                message_id = result['message_id']
                conversation_id = result['conversation_id']
                
                # Create message object for real-time broadcast
                message_data = {
                    'id': message_id,
                    'conversation_id': conversation_id,
                    'sender_id': user_id,
                    'recipient_id': recipient_id,
                    'content': content,
                    'message_type': message_type,
                    'metadata': metadata,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'sent'
                }
                
                # Clear typing indicator
                self._clear_typing_in_conversation(conversation_id, user_id)
                
                # Broadcast to conversation room
                room_name = f"conversation_{conversation_id}"
                self.socketio.emit('new_message', message_data, room=room_name)
                
                # Send notification to recipient if not in conversation
                if recipient_id in self.online_users:
                    recipient_room = f"user_{recipient_id}"
                    self.socketio.emit('new_message_notification', {
                        'conversation_id': conversation_id,
                        'sender_id': user_id,
                        'preview': content[:50] + "..." if len(content) > 50 else content,
                        'timestamp': datetime.now().isoformat()
                    }, room=recipient_room)
                
                logger.info(f"Real-time message sent: {user_id} -> {recipient_id}")
                emit('message_sent', {'message_id': message_id, 'conversation_id': conversation_id})
                
            except Exception as e:
                logger.error(f"Error sending real-time message: {e}")
                emit('error', {'message': 'Failed to send message'})
        
        @self.socketio.on('typing_start')
        def handle_typing_start(data):
            """Handle typing indicator start"""
            try:
                user_id = session.get('user_id')
                conversation_id = data.get('conversation_id')
                
                if not user_id or not conversation_id:
                    return
                
                # Get user profile for display name
                username = "Unknown User"
                if self.social_manager:
                    profile = self.social_manager.get_user_profile(user_id)
                    if profile:
                        username = profile.display_name
                
                typing_event = TypingEvent(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    username=username,
                    timestamp=datetime.now()
                )
                
                # Store typing event
                if conversation_id not in self.typing_users:
                    self.typing_users[conversation_id] = {}
                self.typing_users[conversation_id][user_id] = typing_event
                
                # Broadcast to conversation room (exclude sender)
                room_name = f"conversation_{conversation_id}"
                self.socketio.emit('user_typing', {
                    'conversation_id': conversation_id,
                    'user_id': user_id,
                    'username': username,
                    'timestamp': typing_event.timestamp.isoformat()
                }, room=room_name, include_self=False)
                
            except Exception as e:
                logger.error(f"Error handling typing start: {e}")
        
        @self.socketio.on('typing_stop')
        def handle_typing_stop(data):
            """Handle typing indicator stop"""
            try:
                user_id = session.get('user_id')
                conversation_id = data.get('conversation_id')
                
                if not user_id or not conversation_id:
                    return
                
                # Remove typing event
                self._clear_typing_in_conversation(conversation_id, user_id)
                
                # Broadcast stop typing to conversation room
                room_name = f"conversation_{conversation_id}"
                self.socketio.emit('user_stopped_typing', {
                    'conversation_id': conversation_id,
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat()
                }, room=room_name, include_self=False)
                
            except Exception as e:
                logger.error(f"Error handling typing stop: {e}")
        
        @self.socketio.on('mark_message_read')
        def handle_mark_message_read(data):
            """Handle marking message as read with real-time receipt"""
            try:
                user_id = session.get('user_id')
                message_id = data.get('message_id')
                conversation_id = data.get('conversation_id')
                
                if not user_id or not message_id:
                    return
                
                # Mark message as read in database
                if self.social_manager:
                    result = self.social_manager.mark_message_as_read(user_id, message_id)
                    
                    if result['success']:
                        # Send read receipt to conversation
                        room_name = f"conversation_{conversation_id}"
                        self.socketio.emit('message_read', {
                            'message_id': message_id,
                            'reader_id': user_id,
                            'read_at': datetime.now().isoformat()
                        }, room=room_name, include_self=False)
                
            except Exception as e:
                logger.error(f"Error marking message as read: {e}")
        
        @self.socketio.on('update_mood')
        def handle_update_mood(data):
            """Handle live mood updates"""
            try:
                user_id = session.get('user_id')
                mood = data.get('mood')
                mood_score = data.get('mood_score')
                
                if not user_id or not mood:
                    return
                
                # Update user's current mood
                if user_id in self.online_users:
                    self.online_users[user_id].current_mood = mood
                
                # Broadcast mood update to friends
                self._broadcast_mood_update(user_id, mood, mood_score)
                
                logger.info(f"User {user_id} updated mood to {mood}")
                emit('mood_updated', {'mood': mood, 'timestamp': datetime.now().isoformat()})
                
            except Exception as e:
                logger.error(f"Error updating mood: {e}")
        
        @self.socketio.on('get_online_friends')
        def handle_get_online_friends():
            """Get list of online friends"""
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return
                
                online_friends = self._get_online_friends(user_id)
                emit('online_friends', {'friends': online_friends})
                
            except Exception as e:
                logger.error(f"Error getting online friends: {e}")
    
    def _get_online_friends(self, user_id: str) -> List[Dict]:
        """Get list of user's friends who are currently online"""
        try:
            if not self.social_manager:
                return []
            
            # Get user's friends
            friends = self.social_manager.get_friends_list(user_id)
            online_friends = []
            
            for friend in friends:
                friend_id = friend['user_id']
                if friend_id in self.online_users:
                    online_user = self.online_users[friend_id]
                    online_friends.append({
                        'user_id': friend_id,
                        'display_name': friend['display_name'],
                        'avatar_url': friend['avatar_url'],
                        'status': online_user.status,
                        'current_mood': online_user.current_mood,
                        'last_seen': online_user.last_seen.isoformat()
                    })
            
            return online_friends
            
        except Exception as e:
            logger.error(f"Error getting online friends: {e}")
            return []
    
    def _broadcast_user_status(self, user_id: str, status: str):
        """Broadcast user status change to their friends"""
        try:
            if not self.social_manager:
                return
            
            # Get user's friends
            friends = self.social_manager.get_friends_list(user_id)
            
            # Get user profile for broadcast
            profile = self.social_manager.get_user_profile(user_id)
            username = profile.display_name if profile else "Unknown User"
            
            status_data = {
                'user_id': user_id,
                'username': username,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send to each online friend
            for friend in friends:
                friend_id = friend['user_id']
                if friend_id in self.online_users:
                    friend_room = f"user_{friend_id}"
                    self.socketio.emit('friend_status_changed', status_data, room=friend_room)
            
        except Exception as e:
            logger.error(f"Error broadcasting user status: {e}")
    
    def _broadcast_mood_update(self, user_id: str, mood: str, mood_score: Optional[float] = None):
        """Broadcast mood update to user's friends"""
        try:
            if not self.social_manager:
                return
            
            # Get user's friends
            friends = self.social_manager.get_friends_list(user_id)
            
            # Get user profile
            profile = self.social_manager.get_user_profile(user_id)
            username = profile.display_name if profile else "Unknown User"
            
            mood_data = {
                'user_id': user_id,
                'username': username,
                'mood': mood,
                'mood_score': mood_score,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send to each online friend
            for friend in friends:
                friend_id = friend['user_id']
                if friend_id in self.online_users:
                    friend_room = f"user_{friend_id}"
                    self.socketio.emit('friend_mood_updated', mood_data, room=friend_room)
            
        except Exception as e:
            logger.error(f"Error broadcasting mood update: {e}")
    
    def _clear_typing_in_conversation(self, conversation_id: str, user_id: str):
        """Clear typing indicator for user in conversation"""
        try:
            if conversation_id in self.typing_users and user_id in self.typing_users[conversation_id]:
                del self.typing_users[conversation_id][user_id]
                
                if not self.typing_users[conversation_id]:
                    del self.typing_users[conversation_id]
            
        except Exception as e:
            logger.error(f"Error clearing typing indicator: {e}")
    
    def _clear_user_typing(self, user_id: str):
        """Clear all typing indicators for a user"""
        try:
            conversations_to_update = []
            
            for conversation_id, typing_users in self.typing_users.items():
                if user_id in typing_users:
                    conversations_to_update.append(conversation_id)
            
            for conversation_id in conversations_to_update:
                self._clear_typing_in_conversation(conversation_id, user_id)
                
                # Broadcast stop typing
                room_name = f"conversation_{conversation_id}"
                self.socketio.emit('user_stopped_typing', {
                    'conversation_id': conversation_id,
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat()
                }, room=room_name)
            
        except Exception as e:
            logger.error(f"Error clearing user typing indicators: {e}")
    
    def send_notification(self, user_id: str, notification_data: Dict):
        """Send real-time notification to user"""
        try:
            if user_id in self.online_users:
                user_room = f"user_{user_id}"
                self.socketio.emit('notification', notification_data, room=user_room)
                logger.info(f"Real-time notification sent to {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending real-time notification: {e}")
    
    def get_online_users_count(self) -> int:
        """Get total number of online users"""
        return len(self.online_users)
    
    def get_active_conversations(self) -> int:
        """Get number of active conversations"""
        return len(self.typing_users)
    
    def cleanup_stale_connections(self):
        """Clean up stale connections and typing indicators"""
        try:
            now = datetime.now()
            stale_timeout = timedelta(minutes=5)
            
            # Clean up stale typing indicators
            stale_conversations = []
            for conversation_id, typing_users in self.typing_users.items():
                stale_users = []
                for user_id, typing_event in typing_users.items():
                    if now - typing_event.timestamp > stale_timeout:
                        stale_users.append(user_id)
                
                for user_id in stale_users:
                    self._clear_typing_in_conversation(conversation_id, user_id)
                
                if not self.typing_users.get(conversation_id):
                    stale_conversations.append(conversation_id)
            
            for conversation_id in stale_conversations:
                if conversation_id in self.typing_users:
                    del self.typing_users[conversation_id]
            
            logger.info("Cleaned up stale real-time connections")
            
        except Exception as e:
            logger.error(f"Error cleaning up stale connections: {e}")

# Global instance
realtime_messaging = None

def init_realtime_messaging(socketio: SocketIO, social_manager=None, notification_manager=None):
    """Initialize real-time messaging system"""
    global realtime_messaging
    try:
        realtime_messaging = RealtimeMessaging(socketio, social_manager, notification_manager)
        logger.info("Real-time messaging system initialized successfully")
        return realtime_messaging
    except Exception as e:
        logger.error(f"Error initializing real-time messaging: {e}")
        return None

def get_realtime_messaging():
    """Get real-time messaging instance"""
    return realtime_messaging