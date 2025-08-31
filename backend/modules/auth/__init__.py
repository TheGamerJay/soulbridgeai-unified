"""
SoulBridge AI - Authentication Module
Extracted from app.py monolith for modular architecture
"""

from .routes import auth_bp
from .auth_service import AuthService, has_accepted_terms
from .session_manager import (
    setup_user_session, 
    is_logged_in, 
    get_user_id, 
    get_user_email,
    requires_login, 
    requires_admin, 
    clear_session,
    refresh_session,
    ensure_session_persistence,
    increment_rate_limit_session,
    get_open_paths,
    is_open_path
)
from .admin_auth import (
    require_admin_auth,
    is_admin_rate_limited,
    record_admin_login_attempt,
    setup_admin_session,
    clear_admin_session,
    is_admin_session_valid,
    get_admin_session_info
)

__all__ = [
    'auth_bp',
    'AuthService', 
    'has_accepted_terms',
    'setup_user_session',
    'is_logged_in',
    'get_user_id', 
    'get_user_email',
    'requires_login',
    'requires_admin',
    'clear_session',
    'refresh_session',
    'ensure_session_persistence',
    'increment_rate_limit_session',
    'get_open_paths',
    'is_open_path',
    'require_admin_auth',
    'is_admin_rate_limited',
    'record_admin_login_attempt',
    'setup_admin_session',
    'clear_admin_session',
    'is_admin_session_valid',
    'get_admin_session_info'
]