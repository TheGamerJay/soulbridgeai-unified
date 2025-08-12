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

logger = logging.getLogger(__name__)

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
        # Prefer private endpoint if available to avoid egress fees
        self.postgres_url = None
        
        # Try to construct private URL from individual components first
        if all([os.environ.get('PGHOST'), os.environ.get('PGUSER'), 
                os.environ.get('PGPASSWORD'), os.environ.get('PGDATABASE')]):
            host = os.environ.get('PGHOST')
            user = os.environ.get('PGUSER') 
            password = os.environ.get('PGPASSWORD')
            database = os.environ.get('PGDATABASE')
            port = os.environ.get('PGPORT', '5432')
            
            # Use PostgreSQL connection if all components are available
            self.postgres_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            print(f"Using PostgreSQL private endpoint: {host}")
        
        # Fallback to provided URLs (Railway provides DATABASE_URL automatically)
        if not self.postgres_url:
            self.postgres_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
            if self.postgres_url:
                print(f"Using Railway DATABASE_URL: {self.postgres_url[:50]}...")
        
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
        try:
            print(f"Attempting database connection. PostgreSQL: {self.use_postgres}")
            if self.use_postgres:
                print(f"PostgreSQL URL present: {bool(self.postgres_url)}")
                print(f"psycopg2 available: {POSTGRES_AVAILABLE}")
            
            conn = self.get_connection()
            cursor = conn.cursor()
            print(f"Database connection successful. Using PostgreSQL: {self.use_postgres}")
            
            # Clean up conflicting schema if needed
            if self.use_postgres:
                self._cleanup_conflicting_schema(cursor)
                
        except Exception as e:
            print(f"Database connection failed: {e}")
            print(f"Error type: {type(e).__name__}")
            if hasattr(e, 'args'):
                print(f"Error args: {e.args}")
            raise e

        # Create users table first (required for foreign keys)
        if self.use_postgres:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE,
                    password_hash TEXT,
                    display_name TEXT NOT NULL,
                    email_verified INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trial_start TIMESTAMP,
                    ip_address TEXT,
                    oauth_provider VARCHAR(50),
                    oauth_id VARCHAR(255),
                    profile_picture_url TEXT,
                    last_login TIMESTAMP,
                    companion_data JSONB
                )
                """
            )
        else:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    display_name TEXT NOT NULL,
                    email_verified INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trial_start TIMESTAMP,
                    ip_address TEXT,
                    oauth_provider TEXT,
                    oauth_id TEXT,
                    profile_picture_url TEXT,
                    last_login TIMESTAMP,
                    companion_data TEXT
                )
                """
            )

        # Migrate existing users table to add companion_data column if missing
        try:
            if self.use_postgres:
                cursor.execute("""
                    ALTER TABLE users ADD COLUMN IF NOT EXISTS companion_data JSONB
                """)
            else:
                # SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we need to check first
                cursor.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cursor.fetchall()]
                if 'companion_data' not in columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN companion_data TEXT")
            
            conn.commit()
            logger.info("✅ Database migration: companion_data column added/verified")
        except Exception as e:
            logger.warning(f"⚠️ Migration warning (companion_data column): {e}")
            # Don't fail initialization if migration fails
        
        # Create other tables after users table exists
        if self.use_postgres:
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
                    email VARCHAR(255) NOT NULL UNIQUE,
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

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS oauth_states (
                    id SERIAL PRIMARY KEY,
                    state_token VARCHAR(255) UNIQUE NOT NULL,
                    provider VARCHAR(50) NOT NULL,
                    redirect_url TEXT,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS addon_subscriptions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    addon_type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    stripe_subscription_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_library (
                    id SERIAL PRIMARY KEY,
                    user_email VARCHAR(255) NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_type VARCHAR(50) NOT NULL DEFAULT 'conversation',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS wellness_gallery (
                    id SERIAL PRIMARY KEY,
                    content_type VARCHAR(50) NOT NULL CHECK(content_type IN ('creative_writing', 'canvas_art')),
                    content TEXT NOT NULL,
                    theme VARCHAR(100) NOT NULL,
                    mood VARCHAR(50),
                    is_anonymous BOOLEAN DEFAULT TRUE,
                    hearts_count INTEGER DEFAULT 0,
                    reports_count INTEGER DEFAULT 0,
                    is_featured BOOLEAN DEFAULT FALSE,
                    is_approved BOOLEAN DEFAULT FALSE,
                    is_flagged BOOLEAN DEFAULT FALSE,
                    moderation_status VARCHAR(20) DEFAULT 'pending' CHECK(moderation_status IN ('pending', 'approved', 'rejected', 'flagged')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                )
                """
            )
        else:
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

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS oauth_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state_token TEXT UNIQUE NOT NULL,
                    provider TEXT NOT NULL,
                    redirect_url TEXT,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS addon_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    email TEXT NOT NULL,
                    addon_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    stripe_subscription_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_library (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_type TEXT NOT NULL DEFAULT 'conversation',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS wellness_gallery (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_type TEXT NOT NULL CHECK(content_type IN ('creative_writing', 'canvas_art')),
                    content TEXT NOT NULL,
                    theme TEXT NOT NULL,
                    mood TEXT,
                    is_anonymous INTEGER DEFAULT 1,
                    hearts_count INTEGER DEFAULT 0,
                    reports_count INTEGER DEFAULT 0,
                    is_featured INTEGER DEFAULT 0,
                    is_approved INTEGER DEFAULT 0,
                    is_flagged INTEGER DEFAULT 0,
                    moderation_status TEXT DEFAULT 'pending' CHECK(moderation_status IN ('pending', 'approved', 'rejected', 'flagged')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """
            )

        conn.commit()
        conn.close()

    def _cleanup_conflicting_schema(self, cursor):
        """Clean up conflicting table schemas from previous deployments"""
        try:
            print("CLEANUP: Checking for conflicting table schemas...")
            
            # Simple approach: check if users table has user_id column (old schema)
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'user_id'
            """)
            
            if cursor.fetchone():
                print("CLEANUP: Found old users table with user_id column. Cleaning up schema...")
                
                # Drop all tables that might have conflicts - they'll be recreated
                tables_to_drop = [
                    'chat_sessions', 'support_tickets', 'user_feature_assignments',
                    'feature_usage_analytics', 'chat_messages', 'live_notifications',
                    'user_presence', 'room_memberships', 'chat_rooms', 'ab_experiments',
                    'feature_flags', 'feature_usage_analytics', 'oauth_states',
                    'payment_events', 'subscriptions', 'password_reset_tokens'
                ]
                
                for table in tables_to_drop:
                    cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                    print(f"   Dropped table: {table}")
                
                # Drop and recreate users table with new schema
                cursor.execute("DROP TABLE IF EXISTS users CASCADE")
                print("   Dropped old users table")
                
                # Commit the drops before creating new tables
                cursor.connection.commit()
                print("SUCCESS: Schema cleanup completed - old tables dropped")
            else:
                print("SUCCESS: No conflicting schema found")
                
        except Exception as e:
            print(f"WARNING: Schema cleanup failed (will continue): {e}")
            try:
                # Rollback on error to clear failed transaction
                cursor.connection.rollback()
            except:
                pass

    def get_connection(self):
        """Get database connection"""
        if self.use_postgres:
            try:
                print(f"Connecting to PostgreSQL with URL: {self.postgres_url[:50]}...")
                conn = psycopg2.connect(self.postgres_url)
                print("PostgreSQL connection established successfully")
                return conn
            except Exception as e:
                print(f"PostgreSQL connection error: {e}")
                print(f"PostgreSQL URL: {self.postgres_url}")
                raise e
        else:
            try:
                print(f"Connecting to SQLite at: {self.db_path}")
                conn = sqlite3.connect(self.db_path)
                print("SQLite connection established successfully")
                return conn
            except Exception as e:
                print(f"SQLite connection error: {e}")
                raise e
    
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
    
    def _get_placeholder(self):
        """Get appropriate SQL placeholder for database type"""
        return "%s" if hasattr(self.db, 'postgres_url') and self.db.postgres_url else "?"
    
    def _format_query(self, query):
        """Convert SQLite ? placeholders to appropriate database placeholders"""
        if hasattr(self.db, 'postgres_url') and self.db.postgres_url:
            # Count ? placeholders and replace with %s
            placeholder_count = query.count('?')
            for i in range(placeholder_count):
                query = query.replace('?', '%s', 1)
        return query

    @staticmethod
    def authenticate(db, email, password):
        """Authenticate user with email and password"""
        conn = db.get_connection()
        cursor = conn.cursor()

        # Use appropriate placeholder for database type
        placeholder = "%s" if hasattr(db, 'postgres_url') and db.postgres_url else "?"
        
        cursor.execute(
            f"SELECT id, email, password_hash, display_name, email_verified, created_at, plan_type FROM users WHERE email = {placeholder}",
            (email,),
        )
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            logger.info(f"User found in database: {email}")
            password_hash = user_data[2]
            
            if password_hash is None:
                logger.warning(f"User {email} has no password hash stored")
                return None
                
            try:
                if bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
                    logger.info(f"Password verification successful for: {email}")
                    return user_data
                else:
                    logger.warning(f"Password verification failed for: {email}")
                    return None
            except Exception as e:
                logger.error(f"Password verification error for {email}: {e}")
                return None
        else:
            logger.warning(f"User not found in database: {email}")
            return None

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        query = self._format_query("SELECT id, email, display_name, email_verified, created_at FROM users WHERE id = ?")
        cursor.execute(query, (user_id,))
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
            # Use appropriate placeholder for database type
            placeholder = "%s" if hasattr(self.db, 'postgres_url') and self.db.postgres_url else "?"
            cursor.execute(f"SELECT id FROM users WHERE email = {placeholder}", (email,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            conn.close()
            raise e

    def create_user(self, email=None, password=None, display_name=None, oauth_provider=None, oauth_id=None, profile_picture_url=None):
        """Create new user and return user ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Hash the password using bcrypt (if provided)
            password_hash = None
            if password:
                password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            
            # Insert the new user
            query = self._format_query("""INSERT INTO users 
                   (email, password_hash, display_name, oauth_provider, oauth_id, profile_picture_url, email_verified) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""")
            cursor.execute(query, (email, password_hash, display_name, oauth_provider, oauth_id, profile_picture_url, 1 if oauth_provider else 0))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return {"success": True, "user_id": user_id}
        except Exception as e:
            conn.rollback()
            conn.close()
            return {"success": False, "error": str(e)}

    def get_user_by_oauth(self, provider, oauth_id):
        """Get user by OAuth provider and ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, email, display_name, email_verified, created_at FROM users WHERE oauth_provider = ? AND oauth_id = ?",
            (provider, oauth_id),
        )
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            return {
                "id": user_data[0],
                "email": user_data[1], 
                "display_name": user_data[2],
                "email_verified": user_data[3],
                "created_at": user_data[4]
            }
        return None

    def create_password_reset_token(self, email):
        """Create a password reset token for the given email"""
        import secrets
        from datetime import datetime, timedelta

        # Check if user exists
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Check if user exists
        query1 = self._format_query("SELECT id FROM users WHERE email = ?")
        cursor.execute(query1, (email,))
        if not cursor.fetchone():
            conn.close()
            return {"success": False, "error": "Email not found"}

        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)  # 1 hour expiry

        try:
            # Delete any existing tokens for this email
            query2 = self._format_query("DELETE FROM password_reset_tokens WHERE email = ?")
            cursor.execute(query2, (email,))

            # Insert new token
            query3 = self._format_query("""
                INSERT INTO password_reset_tokens (email, token, expires_at)
                VALUES (?, ?, ?)
            """)
            cursor.execute(query3, (email, token, expires_at))

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
            query = self._format_query("""
                SELECT email, expires_at, used FROM password_reset_tokens 
                WHERE token = ?
            """)
            cursor.execute(query, (token,))

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
            query4 = self._format_query("UPDATE users SET password_hash = ? WHERE email = ?")
            cursor.execute(query4, (password_hash, email))

            # Mark the token as used
            query5 = self._format_query("UPDATE password_reset_tokens SET used = 1 WHERE token = ?")
            cursor.execute(query5, (token,))

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
