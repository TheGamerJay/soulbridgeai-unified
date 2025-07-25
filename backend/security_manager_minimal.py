"""
Minimal Security Manager for SoulBridge AI
Provides basic password hashing without advanced features
"""

import logging
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from flask import session, jsonify

logger = logging.getLogger(__name__)

class SecurityManager:
    """Minimal security manager for basic functionality"""
    
    def __init__(self, db_manager=None, app_name="SoulBridge AI"):
        self.db = db_manager
        self.app_name = app_name
    
    def setup_database_tables(self):
        """Minimal setup - no advanced security tables"""
        logger.info("Using minimal security manager - no advanced features available")
    
    def hash_password(self, password: str) -> str:
        """Hash a password securely"""
        try:
            return generate_password_hash(password, method='pbkdf2:sha256:600000')
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        try:
            # If password_hash doesn't start with hash indicators, it might be plaintext
            if not any(password_hash.startswith(prefix) for prefix in ['pbkdf2:', 'scrypt:', 'argon2:']):
                # This is likely a plaintext password (legacy/development)
                logger.warning("Comparing against plaintext password - this is insecure!")
                return password == password_hash
            
            return check_password_hash(password_hash, password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

# Global security manager instance
security_manager = None

def init_security_features(app, db_manager=None):
    """Initialize minimal security features for Flask app"""
    global security_manager
    
    security_manager = SecurityManager(db_manager, app.config.get('APP_NAME', 'SoulBridge AI'))
    
    # Set up database tables
    if db_manager:
        security_manager.setup_database_tables()
    
    logger.info("Minimal security features initialized")
    
    return security_manager

def require_2fa(f):
    """Decorator placeholder - 2FA not available in minimal mode"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def security_headers(f):
    """Decorator to add security headers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Add security headers
        if hasattr(response, 'headers'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    return decorated_function