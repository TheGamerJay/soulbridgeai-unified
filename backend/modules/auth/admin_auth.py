"""
SoulBridge AI - Admin Authentication Module
Extracted from app.py monolith for modular architecture
"""
import time
import logging
from functools import wraps
from flask import session, request, jsonify

logger = logging.getLogger(__name__)

# Admin login rate limiting storage
admin_login_attempts = {}

def require_admin_auth():
    """Strong admin authentication decorator with time-limited sessions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if admin session exists and is valid
            if not session.get('is_admin'):
                logger.warning(f"🔒 Unauthorized admin access attempt to {request.endpoint} from {request.remote_addr}")
                return jsonify({"error": "Admin authentication required"}), 401
            
            # Check session timestamp (admin sessions expire after 1 hour)
            admin_login_time = session.get('admin_login_time')
            if not admin_login_time:
                logger.warning(f"🔒 Invalid admin session (no timestamp) for {request.endpoint}")
                session.clear()
                return jsonify({"error": "Admin session expired"}), 401
            
            # Check if session has expired (1 hour = 3600 seconds)
            if time.time() - admin_login_time > 3600:
                logger.warning(f"🔒 Expired admin session for {request.endpoint}")
                session.clear()
                return jsonify({"error": "Admin session expired"}), 401
            
            # Check for specific admin user ID (additional security layer)
            if not session.get('admin_user_id'):
                logger.warning(f"🔒 Invalid admin session (no user ID) for {request.endpoint}")
                session.clear()
                return jsonify({"error": "Invalid admin session"}), 401
            
            # Update last activity timestamp
            session['admin_last_activity'] = time.time()
            
            logger.info(f"🔑 Admin access granted to {request.endpoint} for user {session.get('admin_user_id')}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def is_admin_rate_limited(ip_address: str) -> bool:
    """Check if IP address is rate limited for admin login attempts"""
    current_time = time.time()
    
    # Clean old attempts (older than 15 minutes)
    cutoff_time = current_time - 900  # 15 minutes
    admin_login_attempts[ip_address] = [
        attempt_time for attempt_time in admin_login_attempts.get(ip_address, [])
        if attempt_time > cutoff_time
    ]
    
    # Check if this IP has too many recent attempts
    recent_attempts = len(admin_login_attempts.get(ip_address, []))
    
    if recent_attempts >= 5:  # Max 5 attempts per 15 minutes
        logger.warning(f"🔒 Admin login rate limited for IP: {ip_address} ({recent_attempts} attempts)")
        return True
    
    return False

def record_admin_login_attempt(ip_address: str):
    """Record admin login attempt for rate limiting"""
    current_time = time.time()
    
    if ip_address not in admin_login_attempts:
        admin_login_attempts[ip_address] = []
    
    admin_login_attempts[ip_address].append(current_time)
    logger.info(f"🔍 Admin login attempt recorded for IP: {ip_address}")

def setup_admin_session(admin_user_id: str, email: str):
    """Set up admin session with proper security"""
    current_time = time.time()
    
    session['is_admin'] = True
    session['admin_user_id'] = admin_user_id
    session['admin_email'] = email
    session['admin_login_time'] = current_time
    session['admin_last_activity'] = current_time
    session.permanent = False  # Admin sessions expire when browser closes
    
    logger.info(f"🔑 Admin session established for {email} (ID: {admin_user_id})")

def clear_admin_session():
    """Clear admin session data"""
    admin_email = session.get('admin_email', 'unknown')
    
    # Clear admin-specific session data
    admin_keys = ['is_admin', 'admin_user_id', 'admin_email', 'admin_login_time', 'admin_last_activity']
    for key in admin_keys:
        session.pop(key, None)
    
    logger.info(f"🔑 Admin session cleared for {admin_email}")

def is_admin_session_valid() -> bool:
    """Check if current admin session is valid"""
    if not session.get('is_admin'):
        return False
    
    admin_login_time = session.get('admin_login_time')
    if not admin_login_time:
        return False
    
    # Check if session has expired (1 hour = 3600 seconds)
    if time.time() - admin_login_time > 3600:
        return False
    
    # Check for admin user ID
    if not session.get('admin_user_id'):
        return False
    
    return True

def get_admin_session_info() -> dict:
    """Get current admin session information"""
    if not is_admin_session_valid():
        return {"valid": False}
    
    admin_login_time = session.get('admin_login_time', 0)
    current_time = time.time()
    session_age = current_time - admin_login_time
    time_remaining = 3600 - session_age  # 1 hour session
    
    return {
        "valid": True,
        "admin_user_id": session.get('admin_user_id'),
        "admin_email": session.get('admin_email'),
        "session_age_seconds": int(session_age),
        "time_remaining_seconds": int(max(0, time_remaining)),
        "last_activity": session.get('admin_last_activity', admin_login_time)
    }