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
import json

# Try to import PostgreSQL support
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

os.system("cls" if os.name == "nt" else "clear")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    filename="soulbridge.log",
    filemode="a",
)

ENCRYPTION_KEY = os.environ.get("DATA_ENCRYPTION_KEY")


def get_cipher():
    if ENCRYPTION_KEY:
        return Fernet(ENCRYPTION_KEY)
    else:
        raise ValueError(
            "Encryption key not set. Please set DATA_ENCRYPTION_KEY in your environment."
        )


class Database:
    def __init__(self, db_path=None):
        # Check for PostgreSQL database URL first (production)
        self.postgres_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
        self.use_postgres = bool(self.postgres_url and POSTGRES_AVAILABLE)
        
        if self.use_postgres:
            print(f"Using PostgreSQL database: {self.postgres_url[:30]}...")
            self.db_path = None
        else:
            # Fallback to SQLite
            if db_path is None:
                if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'):
                    # Production: try multiple persistent paths
                    possible_paths = [
                        "/data/soulbridge.db",
                        "/app/data/soulbridge.db", 
                        "/tmp/persistent/soulbridge.db",
                        "/var/lib/soulbridge/soulbridge.db"
                    ]
                    
                    db_path = None
                    for path in possible_paths:
                        try:
                            # Create directory if it doesn't exist
                            directory = os.path.dirname(path)
                            os.makedirs(directory, exist_ok=True)
                            
                            # Test if we can write to this location
                            test_file = path + "_test"
                            with open(test_file, 'w') as f:
                                f.write("test")
                            os.remove(test_file)
                            
                            db_path = path
                            print(f"Using persistent SQLite path: {db_path}")
                            break
                        except Exception as e:
                            print(f"Cannot use path {path}: {e}")
                            continue
                    
                    # If no persistent path works, fall back to Railway app directory
                    if not db_path:
                        db_path = "/app/soulbridge.db"
                        print(f"Using fallback SQLite path: {db_path}")
                else:
                    # Development: use local file
                    db_path = "soulbridge.db"
                    print(f"Using development SQLite path: {db_path}")
            
            self.db_path = db_path
            
            # Create backup before initializing (if database exists)
            if self.db_path and os.path.exists(self.db_path):
                self.backup_database()
        
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if self.use_postgres:
            # PostgreSQL table creation
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    email_verified INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trial_start TIMESTAMP,
                    ip_address TEXT
                )
                """
            )
        else:
            # SQLite table creation
            cursor.execute(
                """
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
                """
            )

        if self.use_postgres:
            # PostgreSQL table creation
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    plan_type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    stripe_customer_id TEXT,
                    stripe_subscription_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS payment_events (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    email VARCHAR(255) NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    plan_type VARCHAR(50),
                    amount REAL,
                    currency VARCHAR(10) DEFAULT 'usd',
                    stripe_event_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        else:
            # SQLite table creation
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    email TEXT NOT NULL,
                    plan_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    stripe_customer_id TEXT,
                    stripe_subscription_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS payment_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    email TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    plan_type TEXT,
                    amount REAL,
                    currency TEXT DEFAULT 'usd',
                    stripe_event_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

        conn.commit()
        conn.close()

    def get_connection(self):
        """Get database connection"""
        if self.use_postgres:
            return psycopg2.connect(self.postgres_url)
        else:
            return sqlite3.connect(self.db_path)
    
    def backup_database(self, backup_path=None):
        """Create a backup of the database"""
        if not backup_path:
            backup_path = f"{self.db_path}.backup.{int(time.time())}"
        
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return None
    
    def restore_database(self, backup_path):
        """Restore database from backup"""
        try:
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, self.db_path)
                logger.info(f"Database restored from: {backup_path}")
                return True
            else:
                logger.error(f"Backup file not found: {backup_path}")
                return False
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
    
    def export_users_to_json(self):
        """Export all users to JSON for backup"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Export users
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            
            # Export subscriptions
            cursor.execute("SELECT * FROM subscriptions")
            subscriptions = cursor.fetchall()
            
            # Export payment events  
            cursor.execute("SELECT * FROM payment_events")
            payment_events = cursor.fetchall()
            
            conn.close()
            
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "users": users,
                "subscriptions": subscriptions,
                "payment_events": payment_events
            }
            
            return backup_data
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return None


class User:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def authenticate(db, email, password):
        """Authenticate user with email and password"""
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, email, password_hash, display_name, email_verified, created_at FROM users WHERE email = ?",
            (email,),
        )
        user_data = cursor.fetchone()
        conn.close()

        if user_data and bcrypt.checkpw(password.encode("utf-8"), user_data[2].encode("utf-8")):
            # Return user data tuple (compatible with existing code)
            return user_data
        return None

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, email, display_name, email_verified, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            # Return user data tuple (compatible with existing code)
            return user_data
        return None

    def user_exists(self, email):
        """Check if user exists by email"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            conn.close()
            raise e

    def create_user(self, email, password, display_name):
        """Create new user and return user ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Hash the password using bcrypt
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            
            # Insert the new user
            cursor.execute(
                "INSERT INTO users (email, password_hash, display_name) VALUES (?, ?, ?)",
                (email, password_hash, display_name)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except Exception as e:
            conn.rollback()
            conn.close()
            raise e

    def create_password_reset_token(self, email):
        """Create a password reset token for the given email"""
        import secrets
        from datetime import datetime, timedelta

        # Check if user exists
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if not cursor.fetchone():
            conn.close()
            return {"success": False, "error": "Email not found"}

        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)  # 1 hour expiry

        try:
            # Delete any existing tokens for this email
            cursor.execute(
                "DELETE FROM password_reset_tokens WHERE email = ?", (email,)
            )

            # Insert new token
            cursor.execute(
                """
                INSERT INTO password_reset_tokens (email, token, expires_at)
                VALUES (?, ?, ?)
            """,
                (email, token, expires_at),
            )

            conn.commit()
            conn.close()

            return {"success": True, "token": token}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def verify_reset_token(self, token):
        """Verify if a reset token is valid and not expired"""
        from datetime import datetime, timedelta

        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT email, expires_at, used FROM password_reset_tokens 
                WHERE token = ?
            """,
                (token,),
            )

            result = cursor.fetchone()
            conn.close()

            if not result:
                return {"success": False, "error": "Invalid token"}

            email, expires_at, used = result

            if used:
                return {"success": False, "error": "Token already used"}

            # Check if token is expired
            try:
                if isinstance(expires_at, str):
                    expires_datetime = (
                        datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                        if "Z" in expires_at
                        else datetime.fromisoformat(expires_at)
                    )
                else:
                    # If it's already a datetime object from SQLite
                    expires_datetime = expires_at
            except ValueError:
                # Handle any datetime parsing issues
                expires_datetime = datetime.now() - timedelta(
                    seconds=1
                )  # Make it expired

            if expires_datetime < datetime.now():
                return {"success": False, "error": "Token expired"}

            return {"success": True, "email": email}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def reset_password(self, token, new_password):
        """Reset password using a valid token"""
        import bcrypt

        # Verify token first
        token_result = self.verify_reset_token(token)
        if not token_result["success"]:
            return token_result

        email = token_result["email"]

        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            # Hash the new password
            password_hash = bcrypt.hashpw(
                new_password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            # Update the user's password
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE email = ?",
                (password_hash, email),
            )

            # Mark the token as used
            cursor.execute(
                "UPDATE password_reset_tokens SET used = 1 WHERE token = ?", (token,)
            )

            conn.commit()
            conn.close()

            return {"success": True, "message": "Password reset successfully"}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}


class TagManager:
    def __init__(self, db):
        self.db = db


class MoodTracker:
    def __init__(self, db):
        self.db = db


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"success": False, "error": "Authentication required"}), 401
        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    if "user_id" in session:
        db = Database()
        user_manager = User(db)
        return user_manager.get_user_by_id(session["user_id"])


class ConversationManager:
    def __init__(self, db):
        self.db = db


# End of file (leave blank or just Python comments)
