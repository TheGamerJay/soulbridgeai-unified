# Simple, Clean Authentication System
import bcrypt
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import session, request, jsonify, redirect
import logging

logger = logging.getLogger(__name__)

class SimpleAuth:
    def __init__(self, db):
        self.db = db
    
    def create_user(self, email, password, display_name):
        """Create a new user account"""
        try:
            # Check if user already exists
            if self.user_exists(email):
                return {"success": False, "error": "User already exists"}
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
            
            # Insert into database
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            placeholder = "%s" if hasattr(self.db, 'postgres_url') and self.db.postgres_url else "?"
            
            cursor.execute(f"""
                INSERT INTO users (email, password_hash, display_name, email_verified, created_at)
                VALUES ({placeholder}, {placeholder}, {placeholder}, 1, CURRENT_TIMESTAMP)
            """, (email.lower().strip(), password_hash, display_name))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            logger.info(f"User created successfully: {email}")
            return {"success": True, "user_id": user_id}
            
        except Exception as e:
            logger.error(f"Create user error: {e}")
            return {"success": False, "error": str(e)}
    
    def authenticate(self, email, password):
        """Authenticate user credentials"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            placeholder = "%s" if hasattr(self.db, 'postgres_url') and self.db.postgres_url else "?"
            
            cursor.execute(f"""
                SELECT id, email, password_hash, display_name
                FROM users WHERE email = {placeholder}
            """, (email.lower().strip(),))
            
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data[2].encode('utf-8')):
                logger.info(f"Authentication successful: {email}")
                return {
                    "success": True,
                    "user_id": user_data[0],
                    "email": user_data[1],
                    "display_name": user_data[3]
                }
            else:
                logger.warning(f"Authentication failed: {email}")
                return {"success": False, "error": "Invalid email or password"}
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {"success": False, "error": "Authentication failed"}
    
    def user_exists(self, email):
        """Check if user exists"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            placeholder = "%s" if hasattr(self.db, 'postgres_url') and self.db.postgres_url else "?"
            
            cursor.execute(f"SELECT id FROM users WHERE email = {placeholder}", (email.lower().strip(),))
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"User exists check error: {e}")
            return False
    
    def create_session(self, user_data):
        """Create secure user session"""
        session.permanent = False  # Session ends when browser closes
        session['user_authenticated'] = True
        session['user_id'] = user_data['user_id']
        session['user_email'] = user_data['email']
        session['display_name'] = user_data['display_name']
        session['last_activity'] = datetime.now().isoformat()
        
        logger.info(f"Secure session created for user: {user_data['email']}")
    
    def clear_session(self):
        """Clear user session"""
        user_email = session.get('user_email', 'unknown')
        session.clear()
        logger.info(f"Session cleared for user: {user_email}")
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return session.get('user_authenticated', False) and session.get('user_id')

# Decorator for protected routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_authenticated'):
            if request.is_json:
                return jsonify({"success": False, "error": "Authentication required"}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function