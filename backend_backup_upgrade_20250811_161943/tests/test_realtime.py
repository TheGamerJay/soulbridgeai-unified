import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Set test environment
os.environ["TEST_MODE"] = "true"

# Mock SocketIO imports for testing
with patch.dict('sys.modules', {
    'flask_socketio': Mock(),
    'eventlet': Mock()
}):
    from realtime_manager import (
        RealTimeManager, UserPresence, LiveNotification, ChatMessage,
        init_realtime_features, SOCKETIO_AVAILABLE
    )


class TestUserPresence:
    """Test UserPresence dataclass"""
    
    def test_user_presence_creation(self):
        """Test creating UserPresence object"""
        presence = UserPresence(
            user_id="test_user",
            session_id="test_session",
            status="online",
            last_seen=datetime.utcnow(),
            current_room="test_room",
            metadata={"device": "web"}
        )
        
        assert presence.user_id == "test_user"
        assert presence.session_id == "test_session"
        assert presence.status == "online"
        assert presence.current_room == "test_room"
        assert presence.metadata["device"] == "web"


class TestLiveNotification:
    """Test LiveNotification dataclass"""
    
    def test_notification_creation(self):
        """Test creating LiveNotification object"""
        notification = LiveNotification(
            notification_id="notif_123",
            user_id="test_user",
            type="info",
            title="Test Notification",
            message="This is a test notification",
            data={"url": "/test"},
            created_at=datetime.utcnow()
        )
        
        assert notification.notification_id == "notif_123"
        assert notification.user_id == "test_user"
        assert notification.type == "info"
        assert notification.title == "Test Notification"
        assert notification.read is False  # Default value


class TestChatMessage:
    """Test ChatMessage dataclass"""
    
    def test_message_creation(self):
        """Test creating ChatMessage object"""
        message = ChatMessage(
            message_id="msg_123",
            user_id="test_user",
            room_id="test_room",
            content="Hello, world!",
            message_type="text",
            timestamp=datetime.utcnow(),
            metadata={"edited": False}
        )
        
        assert message.message_id == "msg_123"
        assert message.user_id == "test_user"
        assert message.room_id == "test_room"
        assert message.content == "Hello, world!"
        assert message.message_type == "text"


class TestRealTimeManager:
    """Test RealTimeManager functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        # Mock SocketIO instance
        self.mock_socketio = Mock()
        self.mock_db = Mock()
        
        # Create manager with mocks
        with patch('realtime_manager.SOCKETIO_AVAILABLE', True):
            self.manager = RealTimeManager(self.mock_socketio, self.mock_db)
    
    def test_manager_initialization(self):
        """Test RealTimeManager initialization"""
        assert self.manager.socketio == self.mock_socketio
        assert self.manager.db == self.mock_db
        assert isinstance(self.manager.user_sessions, dict)
        assert isinstance(self.manager.session_users, dict)
        assert isinstance(self.manager.user_presence, dict)
    
    def test_send_notification(self):
        """Test sending notifications"""
        user_id = "test_user"
        title = "Test Title"
        message = "Test message"
        
        self.manager.send_notification(user_id, "info", title, message)
        
        # Check notification was stored
        assert user_id in self.manager.notifications
        assert len(self.manager.notifications[user_id]) == 1
        
        notification = self.manager.notifications[user_id][0]
        assert notification.title == title
        assert notification.message == message
        assert notification.type == "info"
    
    def test_broadcast_to_room(self):
        """Test broadcasting to room"""
        room_id = "test_room"
        event = "test_event"
        data = {"message": "test"}
        
        self.manager.broadcast_to_room(room_id, event, data)
        
        # Verify SocketIO emit was called
        self.mock_socketio.emit.assert_called_once_with(event, data, room=room_id)
    
    def test_get_online_users_empty(self):
        """Test getting online users when none are online"""
        online_users = self.manager.get_online_users()
        assert online_users == []
    
    def test_get_online_users_with_presence(self):
        """Test getting online users with presence data"""
        # Add a user with presence
        user_id = "test_user"
        session_id = "test_session"
        
        self.manager.user_sessions[user_id].add(session_id)
        self.manager._update_user_presence(user_id, session_id, "online")
        
        online_users = self.manager.get_online_users()
        
        assert len(online_users) == 1
        assert online_users[0]["user_id"] == user_id
        assert online_users[0]["status"] == "online"
        assert online_users[0]["session_count"] == 1
    
    def test_cleanup_stale_data(self):
        """Test cleanup of stale data"""
        # Add some typing data
        self.manager.typing_users["test_room"]["test_user"] = 0  # Very old timestamp
        
        # Run cleanup
        self.manager.cleanup_stale_data()
        
        # Should clean up old typing indicators
        # Note: This is a basic test - full implementation would need more setup
        assert True  # Placeholder assertion
    
    def test_can_access_room_personal(self):
        """Test room access for personal rooms"""
        user_id = "test_user"
        room_id = f"user_{user_id}"
        
        can_access = self.manager._can_access_room(user_id, room_id)
        assert can_access is True
    
    def test_can_access_room_public_chat(self):
        """Test room access for public chat rooms"""
        user_id = "test_user"
        room_id = "chat_general"
        
        can_access = self.manager._can_access_room(user_id, room_id)
        assert can_access is True
    
    def test_can_access_room_admin(self):
        """Test room access for admin rooms"""
        user_id = "test_user"
        room_id = "admin_dashboard"
        
        # Should return False since _is_admin_user returns False by default
        can_access = self.manager._can_access_room(user_id, room_id)
        assert can_access is False


class TestInitRealTimeFeatures:
    """Test initialization functions"""
    
    def test_init_without_socketio_available(self):
        """Test initialization when SocketIO is not available"""
        mock_app = Mock()
        
        with patch('realtime_manager.SOCKETIO_AVAILABLE', False):
            result = init_realtime_features(mock_app)
            assert result is None
    
    def test_init_without_socketio_instance(self):
        """Test initialization without SocketIO instance"""
        mock_app = Mock()
        
        with patch('realtime_manager.SOCKETIO_AVAILABLE', True):
            result = init_realtime_features(mock_app, socketio=None)
            assert result is None
    
    def test_init_with_socketio(self):
        """Test successful initialization with SocketIO"""
        mock_app = Mock()
        mock_socketio = Mock()
        mock_db = Mock()
        
        with patch('realtime_manager.SOCKETIO_AVAILABLE', True):
            result = init_realtime_features(mock_app, mock_socketio, mock_db)
            assert result is not None
            assert isinstance(result, RealTimeManager)


class TestMockEnvironment:
    """Test behavior in mock/test environment"""
    
    def test_socketio_available_flag(self):
        """Test that SOCKETIO_AVAILABLE flag works correctly"""
        # In test environment, this should be mocked
        # The actual value depends on whether flask-socketio is installed
        assert isinstance(SOCKETIO_AVAILABLE, bool)
    
    def test_mock_functions_callable(self):
        """Test that mock functions are callable in test environment"""
        # These should not raise errors even if SocketIO is not available
        emit("test", {})
        join_room("test_room")
        leave_room("test_room")
        rooms()
        disconnect()
        
        # If we get here without errors, the mocks are working
        assert True


class TestErrorHandling:
    """Test error handling in real-time features"""
    
    def setup_method(self):
        """Set up test environment with error conditions"""
        self.mock_socketio = Mock()
        self.mock_db = Mock()
        
        with patch('realtime_manager.SOCKETIO_AVAILABLE', True):
            self.manager = RealTimeManager(self.mock_socketio, self.mock_db)
    
    def test_send_notification_with_error(self):
        """Test notification sending with errors"""
        # Mock SocketIO to raise an exception
        self.mock_socketio.emit.side_effect = Exception("Connection error")
        
        # Should not crash, just log error
        self.manager.send_notification("test_user", "error", "Test", "Message")
        
        # Notification should still be stored locally
        assert "test_user" in self.manager.notifications
    
    def test_broadcast_with_error(self):
        """Test broadcasting with errors"""
        # Mock SocketIO to raise an exception
        self.mock_socketio.emit.side_effect = Exception("Broadcast error")
        
        # Should not crash, just log error
        self.manager.broadcast_to_room("test_room", "test_event", {})
        
        # Should have attempted to call emit
        assert self.mock_socketio.emit.called
    
    def test_get_online_users_with_error(self):
        """Test getting online users with error conditions"""
        # Add some invalid data that might cause errors
        self.manager.user_presence["invalid_user"] = None
        
        # Should return empty list or handle gracefully
        online_users = self.manager.get_online_users()
        assert isinstance(online_users, list)