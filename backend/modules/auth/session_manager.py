"""
SoulBridge AI - Session Management Module
Extracted from app.py monolith for modular architecture
"""
import logging
from datetime import datetime
from flask import session, request, jsonify, redirect
from functools import wraps

logger = logging.getLogger(__name__)

def setup_user_session(email: str, user_id: int = None, is_admin: bool = False, dev_mode: bool = False):
    """Set up user session with proper data initialization"""
    try:
        logger.info(f"[SESSION] Setting up session for {email} (ID: {user_id})")
        
        # Clear existing session first
        session.clear()
        
        # Set basic session data
        session['email'] = email
        session['logged_in'] = True
        session['login_time'] = datetime.now().isoformat()
        session['is_admin'] = is_admin
        session['dev_mode'] = dev_mode
        
        if user_id:
            session['user_id'] = user_id
        
        # Initialize companion data
        restore_companion_data(user_id)
        
        # Load terms acceptance status
        load_terms_acceptance_status(user_id)
        
        session.permanent = True
        session.modified = True
        
        logger.info(f"[SESSION] Session setup complete for {email}")
        
    except Exception as e:
        logger.error(f"[SESSION] Error setting up session for {email}: {e}")
        raise

def restore_companion_data(user_id: int):
    """Restore companion selection data from database"""
    try:
        if not user_id:
            return
            
        # This would restore companion preferences from database
        # Implementation would be extracted from app.py
        logger.info(f"[SESSION] Restoring companion data for user {user_id}")
        
    except Exception as e:
        logger.warning(f"[SESSION] Failed to restore companion data for user {user_id}: {e}")

def load_terms_acceptance_status(user_id: int):
    """Load terms acceptance status from database"""
    try:
        if not user_id:
            return
            
        # This would load terms acceptance from database
        # Implementation would be extracted from app.py
        session['terms_accepted'] = True  # Placeholder
        logger.info(f"[SESSION] Loaded terms acceptance status for user {user_id}")
        
    except Exception as e:
        logger.warning(f"[SESSION] Failed to load terms acceptance for user {user_id}: {e}")

def is_logged_in() -> bool:
    """Check if user is logged in"""
    logged_in = session.get('logged_in', False)
    email = session.get('email')
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[SESSION_CHECK] is_logged_in check: logged_in={logged_in}, email={email}, session_keys={list(session.keys())}")
    
    return logged_in and email is not None

def get_user_id() -> int:
    """Get current user ID from session"""
    return session.get('user_id')

def get_user_email() -> str:
    """Get current user email from session"""
    return session.get('email', '')

def requires_login(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            else:
                return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def requires_admin(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            else:
                return redirect('/login')
                
        if not session.get('is_admin', False):
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            else:
                return redirect('/')
                
        return f(*args, **kwargs)
    return decorated_function

def clear_session():
    """Clear user session"""
    try:
        user_email = session.get('email', 'unknown')
        session.clear()
        logger.info(f"[SESSION] Cleared session for {user_email}")
        
    except Exception as e:
        logger.error(f"[SESSION] Error clearing session: {e}")

def refresh_session():
    """Refresh session data from database"""
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        # This would refresh session data from database
        # Implementation would be extracted from app.py
        logger.info(f"[SESSION] Refreshed session for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"[SESSION] Error refreshing session: {e}")
        return False

def ensure_session_persistence():
    """Ensure session data persistence - middleware function"""
    from flask import request
    
    # Define open paths that don't require authentication
    open_paths = {
        "/api/login", "/api/logout", "/login", "/simple-login", 
        "/auth/login", "/auth/register", "/auth/forgot-password", 
        "/", "/mini-studio", "/mini_studio_health", "/api/stripe-debug", 
        "/api/admin/reset-trial", "/health", "/api/user-status", 
        "/api/check-user-status", "/api/chat", "/api/companion/chat", 
        "/api/companion/status", "/api/companion/quota", "/api/companion/health", 
        "/api/creative-writing", "/api/voice-chat/process", "/api/tier-limits", 
        "/api/trial-status", "/api/user-info", "/api/companions", "/api/companions-test"
    }
    
    # Log auth path debugging
    if "/auth" in request.path:
        logger.debug(f"Auth middleware: path={request.path}, in_open_paths={request.path in open_paths}")
    
    # For now, this is a placeholder for session persistence logic
    # The actual implementation would depend on the Flask app context
    pass

def increment_rate_limit_session():
    """Track when Mini Helper is used due to rate limits"""
    try:
        import json
        from datetime import datetime
        
        # This would load and update project state
        # Implementation would depend on the project state system
        logger.info("[SESSION] Rate limit session incremented")
        
    except Exception as e:
        logger.error(f"[SESSION] Failed to increment rate limit session: {e}")

def get_open_paths():
    """Get list of paths that don't require authentication"""
    return {
        "/api/login", "/api/logout", "/login", "/simple-login", 
        "/auth/login", "/auth/register", "/auth/forgot-password", 
        "/", "/mini-studio", "/mini_studio_health", "/api/stripe-debug", 
        "/api/admin/reset-trial", "/health", "/api/user-status", 
        "/api/check-user-status", "/api/chat", "/api/companion/chat", 
        "/api/companion/status", "/api/companion/quota", "/api/companion/health", 
        "/api/creative-writing", "/api/voice-chat/process", "/api/tier-limits", 
        "/api/trial-status", "/api/user-info", "/api/companions", "/api/companions-test"
    }

def is_open_path(path: str) -> bool:
    """Check if path is open (doesn't require authentication)"""
    return path in get_open_paths()