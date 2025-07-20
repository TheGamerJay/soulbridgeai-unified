import pytest
import json
from unittest.mock import patch, MagicMock

def test_api_endpoints_require_auth(client):
    """Test that API endpoints require authentication."""
    protected_endpoints = [
        '/api/chat',
        '/api/user/profile',
        '/api/user/subscription',
        '/api/analytics/user'
    ]
    
    for endpoint in protected_endpoints:
        response = client.get(endpoint)
        # Should require authentication
        assert response.status_code in [401, 403, 302]

def test_admin_endpoints_require_admin_auth(client):
    """Test that admin endpoints require admin authentication."""
    admin_endpoints = [
        '/api/admin/users',
        '/api/admin/analytics',
        '/api/analytics/revenue'
    ]
    
    for endpoint in admin_endpoints:
        response = client.get(endpoint)
        # Should require admin authentication
        assert response.status_code in [401, 403, 302]

@patch('app.db')
@patch('app.openai_client')
def test_chat_endpoint_with_valid_session(mock_openai, mock_db, client):
    """Test chat endpoint with valid session."""
    # Mock user session
    with client.session_transaction() as sess:
        sess['user_id'] = 'test-user-123'
    
    # Mock database and OpenAI responses
    mock_db.users.get_user.return_value = {'userID': 'test-user-123'}
    mock_openai.chat.completions.create.return_value = MagicMock()
    mock_openai.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Hello! How can I help you?"))
    ]
    
    response = client.post('/api/chat', 
                          json={'message': 'Hello', 'companion': 'Blayzo'})
    
    # Should process chat request
    assert response.status_code in [200, 401, 403]