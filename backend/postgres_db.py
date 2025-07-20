"""
PostgreSQL Database Manager for SoulBridge AI
Replaces JSON file storage with persistent PostgreSQL database
"""

import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict, List, Optional, Union
import uuid


class PostgreSQLManager:
    def __init__(self):
        self.connection = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            # Railway provides DATABASE_URL automatically
            database_url = os.environ.get("DATABASE_URL")
            if not database_url:
                # Fallback for local development
                database_url = (
                    "postgresql://postgres:password@localhost:5432/soulbridge"
                )

            print(f"🔗 Attempting PostgreSQL connection...")
            print(f"🔑 DATABASE_URL present: {bool(database_url)}")

            # Import here to avoid issues if psycopg2 is not available
            import psycopg2
            import psycopg2.extras

            self.connection = psycopg2.connect(database_url)
            self.connection.autocommit = True
            print(f"✅ Connected to PostgreSQL database successfully")

        except ImportError as e:
            print(f"❌ psycopg2 not available: {e}")
            raise
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            print(
                f"🔍 DATABASE_URL format check: {database_url[:50] if database_url else 'None'}..."
            )
            raise

    def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            cursor = self.connection.cursor()

            # Users table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id VARCHAR(50) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255),
                    subscription_status VARCHAR(50) DEFAULT 'free',
                    companion VARCHAR(100) DEFAULT 'Blayzo',
                    chat_history JSONB DEFAULT '[]',
                    settings JSONB DEFAULT '{}',
                    dev_mode BOOLEAN DEFAULT FALSE,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Chat sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id VARCHAR(50) PRIMARY KEY,
                    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
                    messages JSONB DEFAULT '[]',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Support tickets table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS support_tickets (
                    ticket_id VARCHAR(50) PRIMARY KEY,
                    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
                    subject VARCHAR(255),
                    description TEXT,
                    status VARCHAR(50) DEFAULT 'open',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Feature flags table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feature_flags (
                    flag_id VARCHAR(50) PRIMARY KEY,
                    flag_name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    is_enabled BOOLEAN DEFAULT FALSE,
                    rollout_percentage DECIMAL(5,2) DEFAULT 0.0,
                    target_groups JSONB DEFAULT '[]',
                    conditions JSONB DEFAULT '{}',
                    metadata JSONB DEFAULT '{}',
                    created_by VARCHAR(50),
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # A/B test experiments table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ab_experiments (
                    experiment_id VARCHAR(50) PRIMARY KEY,
                    experiment_name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT FALSE,
                    variants JSONB NOT NULL,
                    traffic_allocation JSONB DEFAULT '{}',
                    target_criteria JSONB DEFAULT '{}',
                    success_metrics JSONB DEFAULT '[]',
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    created_by VARCHAR(50),
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # User feature assignments table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_feature_assignments (
                    assignment_id VARCHAR(50) PRIMARY KEY,
                    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
                    flag_name VARCHAR(100),
                    experiment_id VARCHAR(50),
                    variant_name VARCHAR(100),
                    is_enabled BOOLEAN DEFAULT FALSE,
                    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, flag_name)
                )
            """
            )

            # Feature usage analytics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feature_usage_analytics (
                    usage_id VARCHAR(50) PRIMARY KEY,
                    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
                    flag_name VARCHAR(100),
                    experiment_id VARCHAR(50),
                    variant_name VARCHAR(100),
                    event_type VARCHAR(50),
                    event_data JSONB DEFAULT '{}',
                    session_id VARCHAR(50),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes for performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_feature_flags_name ON feature_flags(flag_name)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_assignments_user_flag ON user_feature_assignments(user_id, flag_name)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_usage_analytics_user_flag ON feature_usage_analytics(user_id, flag_name, timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_ab_experiments_active ON ab_experiments(is_active, start_date, end_date)"
            )

            print("✅ Database tables created/verified (including feature flags)")

        except Exception as e:
            print(f"❌ Failed to create tables: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()


class PostgreSQLUser:
    def __init__(self, db_manager: PostgreSQLManager):
        self.db = db_manager

    def create_user(self, email: str, companion: str = "Blayzo") -> Dict:
        """Create a new user"""
        user_id = f"uid{uuid.uuid4().hex[:8]}"

        # Check if user already exists
        if self.get_user_by_email(email):
            raise ValueError("User with this email already exists")

        try:
            cursor = self.db.connection.cursor()

            # Default settings
            default_settings = {
                "colorPalette": self._get_companion_color(companion),
                "voiceEnabled": True,
                "historySaving": True,
            }

            cursor.execute(
                """
                INSERT INTO users (user_id, email, companion, settings)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id, email, subscription_status, companion, chat_history, settings, created_date
            """,
                (user_id, email, companion, json.dumps(default_settings)),
            )

            result = cursor.fetchone()

            new_user = {
                "userID": result[0],
                "email": result[1],
                "subscriptionStatus": result[2],
                "companion": result[3],
                "chatHistory": result[4] or [],
                "settings": result[5] or default_settings,
                "createdDate": result[6].isoformat() + "Z",
            }

            print(f"✅ User created in PostgreSQL: {user_id}")
            return new_user

        except Exception as e:
            print(f"❌ Failed to create user: {e}")
            raise

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            cursor = self.db.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            cursor.execute(
                """
                SELECT user_id, email, password, subscription_status, companion, 
                       chat_history, settings, dev_mode, created_date
                FROM users WHERE LOWER(email) = LOWER(%s)
            """,
                (email,),
            )

            result = cursor.fetchone()
            if result:
                return {
                    "userID": result["user_id"],
                    "email": result["email"],
                    "password": result["password"],
                    "subscriptionStatus": result["subscription_status"],
                    "companion": result["companion"],
                    "chatHistory": result["chat_history"] or [],
                    "settings": result["settings"] or {},
                    "dev_mode": result["dev_mode"],
                    "createdDate": result["created_date"].isoformat() + "Z",
                }
            return None

        except Exception as e:
            print(f"❌ Failed to get user by email: {e}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by userID"""
        try:
            cursor = self.db.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            cursor.execute(
                """
                SELECT user_id, email, password, subscription_status, companion, 
                       chat_history, settings, dev_mode, created_date
                FROM users WHERE user_id = %s
            """,
                (user_id,),
            )

            result = cursor.fetchone()
            if result:
                return {
                    "userID": result["user_id"],
                    "email": result["email"],
                    "password": result["password"],
                    "subscriptionStatus": result["subscription_status"],
                    "companion": result["companion"],
                    "chatHistory": result["chat_history"] or [],
                    "settings": result["settings"] or {},
                    "dev_mode": result["dev_mode"],
                    "createdDate": result["created_date"].isoformat() + "Z",
                }
            return None

        except Exception as e:
            print(f"❌ Failed to get user by ID: {e}")
            return None

    def update_user(self, user_id: str, updates: Dict) -> bool:
        """Update user data"""
        try:
            cursor = self.db.connection.cursor()

            # Build dynamic update query
            set_clauses = []
            values = []

            for key, value in updates.items():
                if key == "userID":  # Skip userID updates
                    continue
                elif key in ["chatHistory", "settings"]:
                    set_clauses.append(
                        f"{key.lower().replace('history', '_history')} = %s"
                    )
                    values.append(
                        json.dumps(value) if isinstance(value, (dict, list)) else value
                    )
                elif key == "subscriptionStatus":
                    set_clauses.append("subscription_status = %s")
                    values.append(value)
                elif key == "dev_mode":
                    set_clauses.append("dev_mode = %s")
                    values.append(value)
                else:
                    set_clauses.append(f"{key} = %s")
                    values.append(value)

            if not set_clauses:
                return True

            set_clauses.append("updated_date = CURRENT_TIMESTAMP")
            values.append(user_id)

            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = %s"
            cursor.execute(query, values)

            print(f"✅ User updated in PostgreSQL: {user_id}")
            return cursor.rowcount > 0

        except Exception as e:
            print(f"❌ Failed to update user: {e}")
            return False

    def _get_companion_color(self, companion: str) -> str:
        """Get color palette for companion"""
        color_map = {"Blayzo": "cyan", "Blayzion": "blue", "Blayzia": "pink"}
        return color_map.get(companion, "cyan")


class SoulBridgePostgreSQL:
    """Main PostgreSQL database interface for SoulBridge AI"""

    def __init__(self):
        self.db_manager = PostgreSQLManager()
        self.users = PostgreSQLUser(self.db_manager)

    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM chat_sessions")
            session_count = cursor.fetchone()[0]

            return {"users": user_count, "sessions": session_count}
        except Exception as e:
            print(f"❌ Failed to get stats: {e}")
            return {"users": 0, "sessions": 0}

    def close(self):
        """Close database connection"""
        self.db_manager.close()
