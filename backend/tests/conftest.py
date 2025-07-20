import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from app import app, init_database, init_openai

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Create a temporary database file
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    
    with app.test_client() as client:
        with app.app_context():
            # Mock database and OpenAI initialization
            with patch('app.init_database') as mock_db, \
                 patch('app.init_openai') as mock_openai:
                mock_db.return_value = None
                mock_openai.return_value = None
                yield client
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

@pytest.fixture
def mock_db():
    """Mock database for testing."""
    mock = MagicMock()
    mock.users = MagicMock()
    mock.users.create_user.return_value = {
        'userID': 'test-user-123',
        'email': 'test@example.com',
        'display_name': 'Test User'
    }
    mock.users.get_user.return_value = None
    return mock

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    mock = MagicMock()
    mock.chat.completions.create.return_value = MagicMock()
    mock.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Test AI response"))
    ]
    return mock

@pytest.fixture
def test_user_data():
    """Test user data for registration/login tests."""
    return {
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'display_name': 'Test User'
    }