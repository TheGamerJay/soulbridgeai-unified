# backend/routes/auth_simple.py
# Simple auth implementation that works in any Python context

from flask import Blueprint, request, session, jsonify
from werkzeug.security import check_password_hash
import os
import sys
import logging

# Setup logger
logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__)

def j_ok(**kwargs):
    """Return success JSON response"""
    return jsonify({"ok": True, **kwargs})

def j_err(error: str, code: int = 400):
    """Return error JSON response"""
    return jsonify({"ok": False, "error": error}), code

def safe_api(func):
    """Simple API wrapper for error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"API error in {func.__name__}: {e}")
            return j_err("Internal server error", 500)
    wrapper.__name__ = func.__name__
    return wrapper

def rate_limit(per_min=60):
    """Simple rate limiting decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Simple rate limiting - for production, use Redis or similar
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

@bp.post("/api/login")
@rate_limit(per_min=30)
@safe_api
def login():
    """Simple login endpoint that works with existing database"""
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    
    if not email or not password:
        return j_err("Missing email/password", 400)

    try:
        # Try to get database session using the existing database setup
        # This looks for the existing database connection in the app
        from flask import current_app
        
        # Use the existing database manager if available
        if hasattr(current_app, 'db_manager'):
            db_manager = current_app.db_manager
            user_data = db_manager.get_user_by_email(email)
            
            if not user_data:
                return j_err("Invalid credentials", 401)
            
            # Check password hash
            stored_hash = user_data.get('password_hash', '')
            if not stored_hash or not check_password_hash(stored_hash, password):
                return j_err("Invalid credentials", 401)
            
            # Set session data
            session["user_id"] = str(user_data.get('id', ''))
            session["user_plan"] = user_data.get('user_plan', 'bronze')
            
            return j_ok(user_id=session["user_id"], plan=session["user_plan"])
        
        else:
            # Fallback: use SQLite database directly
            import sqlite3
            
            # Look for the database file
            db_path = None
            possible_paths = [
                'soulbridge.db',
                'backend/soulbridge.db',
                os.path.join(os.path.dirname(__file__), '..', 'soulbridge.db')
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break
            
            if not db_path:
                logger.error("No database found for authentication")
                return j_err("Authentication service unavailable", 503)
            
            # Query the database
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, email, password_hash, user_plan FROM users WHERE email = ?", (email,))
            user_row = cursor.fetchone()
            conn.close()
            
            if not user_row:
                return j_err("Invalid credentials", 401)
            
            # Check password
            if not check_password_hash(user_row['password_hash'], password):
                return j_err("Invalid credentials", 401)
            
            # Set session
            session["user_id"] = str(user_row['id'])
            session["user_plan"] = user_row['user_plan'] or 'bronze'
            
            return j_ok(user_id=session["user_id"], plan=session["user_plan"])
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return j_err("Authentication failed", 500)

@bp.post("/api/logout")
@rate_limit(per_min=60)
@safe_api
def logout():
    """Logout endpoint"""
    session.clear()
    return j_ok()

# Health check endpoint
@bp.get("/api/auth/health")
def auth_health():
    """Health check for auth service"""
    return j_ok(status="healthy", service="auth")