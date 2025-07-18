# Authentication Models and Database Setup
import sqlite3
import hashlib
import secrets
import time
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import session, request, jsonify, g
from markupsafe import escape
from email_validator import validate_email, EmailNotValidError
import bcrypt
import os
import base64
from cryptography.fernet import Fernet
import shutil

os.system('cls' if os.name == 'nt' else 'clear')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    filename='soulbridge.log',
    filemode='a'
)

ENCRYPTION_KEY = os.environ.get('DATA_ENCRYPTION_KEY')

def get_cipher():
    if ENCRYPTION_KEY:
        return Fernet(ENCRYPTION_KEY)
    else:
        raise ValueError("Encryption key not set. Please set DATA_ENCRYPTION_KEY in your environment.")

class Database:
    def __init__(self, db_path='soulbridge.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                email_verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                trial_start TIMESTAMP,
                ip_address TEXT
            )
        ''')
        
        # Create password reset tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

class User:
    def __init__(self, db):
        self.db = db
    
    @staticmethod
    def authenticate(db, email, password):
        """Authenticate user with email and password"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, email, password_hash, display_name, email_verified, trial_start, ip_address FROM users WHERE email = ?', (email,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data[2]):
            # Return user object
            user = User(db)
            user.id = user_data[0]
            user.email = user_data[1]
            user.display_name = user_data[3]
            user.email_verified = bool(user_data[4])
            user.trial_start = user_data[5]
            user.ip_address = user_data[6]
            return user
        return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, email, display_name, email_verified, trial_start, ip_address FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            user = User(self.db)
            user.id = user_data[0]
            user.email = user_data[1]
            user.display_name = user_data[2]
            user.email_verified = bool(user_data[3])
            user.trial_start = user_data[4]
            user.ip_address = user_data[5]
            return user
        return None
    
    def create_password_reset_token(self, email):
        """Create a password reset token for the given email"""
        import secrets
        from datetime import datetime, timedelta
        
        # Check if user exists
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if not cursor.fetchone():
            conn.close()
            return {'success': False, 'error': 'Email not found'}
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)  # 1 hour expiry
        
        try:
            # Delete any existing tokens for this email
            cursor.execute('DELETE FROM password_reset_tokens WHERE email = ?', (email,))
            
            # Insert new token
            cursor.execute('''
                INSERT INTO password_reset_tokens (email, token, expires_at)
                VALUES (?, ?, ?)
            ''', (email, token, expires_at))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'token': token}
            
        except Exception as e:
            conn.close()
            return {'success': False, 'error': str(e)}
    
    def verify_reset_token(self, token):
        """Verify if a reset token is valid and not expired"""
        from datetime import datetime, timedelta
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT email, expires_at, used FROM password_reset_tokens 
                WHERE token = ?
            ''', (token,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return {'success': False, 'error': 'Invalid token'}
            
            email, expires_at, used = result
            
            if used:
                return {'success': False, 'error': 'Token already used'}
            
            # Check if token is expired
            try:
                if isinstance(expires_at, str):
                    expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00')) if 'Z' in expires_at else datetime.fromisoformat(expires_at)
                else:
                    # If it's already a datetime object from SQLite
                    expires_datetime = expires_at
            except ValueError:
                # Handle any datetime parsing issues
                expires_datetime = datetime.now() - timedelta(seconds=1)  # Make it expired
            
            if expires_datetime < datetime.now():
                return {'success': False, 'error': 'Token expired'}
            
            return {'success': True, 'email': email}
            
        except Exception as e:
            conn.close()
            return {'success': False, 'error': str(e)}
    
    def reset_password(self, token, new_password):
        """Reset password using a valid token"""
        import bcrypt
        
        # Verify token first
        token_result = self.verify_reset_token(token)
        if not token_result['success']:
            return token_result
        
        email = token_result['email']
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Hash the new password
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Update the user's password
            cursor.execute('UPDATE users SET password_hash = ? WHERE email = ?', (password_hash, email))
            
            # Mark the token as used
            cursor.execute('UPDATE password_reset_tokens SET used = 1 WHERE token = ?', (token,))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Password reset successfully'}
            
        except Exception as e:
            conn.close()
            return {'success': False, 'error': str(e)}

class TagManager:
    def __init__(self, db):
        self.db = db

class MoodTracker:
    def __init__(self, db):
        self.db = db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        db = Database()
        user_manager = User(db)
        return user_manager.get_user_by_id(session['user_id'])
class ConversationManager:
    def __init__(self, db):
        self.db = db

# End of file (leave blank or just Python comments)