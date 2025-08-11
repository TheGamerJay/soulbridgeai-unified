# SUPER SIMPLE AUTH - Just Works
import os
import psycopg2
import bcrypt
from flask import session

class SuperSimpleAuth:
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
    
    def get_connection(self):
        """Direct PostgreSQL connection"""
        return psycopg2.connect(self.db_url)
    
    def signup(self, email, password, name=None):
        """Create user account"""
        if not name:
            name = email.split('@')[0]
        
        conn = self.get_connection()
        conn.autocommit = True
        cursor = conn.cursor()
        
        try:
            # Check if exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                conn.close()
                return {"success": False, "error": "Email already exists"}
            
            # Create user
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            cursor.execute("""
                INSERT INTO users (email, password_hash, display_name, email_verified, created_at)
                VALUES (%s, %s, %s, 1, CURRENT_TIMESTAMP)
                RETURNING id
            """, (email, password_hash, name))
            
            user_id = cursor.fetchone()[0]
            conn.close()
            
            return {"success": True, "user_id": user_id}
            
        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}
    
    def login(self, email, password):
        """Login user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id, password_hash, display_name FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                return {"success": False, "error": "Invalid email or password"}
            
            user_id, password_hash, display_name = user
            
            if bcrypt.checkpw(password.encode(), password_hash.encode()):
                # Create session
                session.permanent = True
                session['user_id'] = user_id
                session['email'] = email
                session['display_name'] = display_name
                session['authenticated'] = True
                
                return {"success": True, "user_id": user_id}
            else:
                return {"success": False, "error": "Invalid email or password"}
                
        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}
    
    def logout(self):
        """Logout user"""
        session.clear()
        return {"success": True}
    
    def is_logged_in(self):
        """Check if user is logged in"""
        return session.get('authenticated', False)
    
    def get_current_user(self):
        """Get current user data"""
        if self.is_logged_in():
            return {
                "user_id": session.get('user_id'),
                "email": session.get('email'),
                "display_name": session.get('display_name')
            }
        return None