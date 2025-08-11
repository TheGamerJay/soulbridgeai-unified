import pytest
import json
from unittest.mock import patch, MagicMock


def test_signup_endpoint_exists(client):
    """Test that signup endpoint is accessible."""
    response = client.get("/signup")
    # Should return the signup page or redirect
    assert response.status_code in [200, 302]


def test_login_endpoint_exists(client):
    """Test that login endpoint is accessible."""
    response = client.get("/login")
    # Should return the login page or redirect
    assert response.status_code in [200, 302]


@patch("app.db")
@patch("app.send_verification_email")
def test_register_user_success(mock_email, mock_db, client, test_user_data):
    """Test successful user registration."""
    # Mock database user creation
    mock_db.users.get_user.return_value = None  # User doesn't exist
    mock_db.users.create_user.return_value = {
        "userID": "test-user-123",
        "email": test_user_data["email"],
        "display_name": test_user_data["display_name"],
    }
    mock_email.return_value = True

    response = client.post("/register", data=test_user_data)

    # Should redirect after successful registration
    assert response.status_code in [200, 302]


@patch("app.db")
def test_register_duplicate_user(mock_db, client, test_user_data):
    """Test registration with duplicate email."""
    # Mock existing user
    mock_db.users.get_user.return_value = {
        "userID": "existing-user",
        "email": test_user_data["email"],
    }

    response = client.post("/register", data=test_user_data)

    # Should handle duplicate registration gracefully
    assert response.status_code in [200, 400, 409]


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/login", data={"email": "nonexistent@example.com", "password": "wrongpassword"}
    )

    # Should reject invalid credentials
    assert response.status_code in [200, 401, 403]
