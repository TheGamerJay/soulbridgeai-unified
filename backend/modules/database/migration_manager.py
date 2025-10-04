"""
SoulBridge AI - Migration Manager
Comprehensive database migration system for modular architecture
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from database_utils import format_query

logger = logging.getLogger(__name__)

class MigrationManager:
    """Central migration management for SoulBridge AI"""
    
    def __init__(self, database=None):
        self.database = database
        self.migrations = {}
        self._load_migrations()
    
    def _load_migrations(self):
        """Load all available migrations"""
        self.migrations = {
            # Core system migrations
            "001_create_migration_tracking": {
                "description": "Create migration tracking table",
                "sql_postgres": """
                    CREATE TABLE IF NOT EXISTS migration_history (
                        id SERIAL PRIMARY KEY,
                        migration_name VARCHAR(255) UNIQUE NOT NULL,
                        description TEXT,
                        module VARCHAR(100),
                        applied_at TIMESTAMPTZ DEFAULT NOW(),
                        rollback_sql TEXT,
                        checksum VARCHAR(64)
                    );
                    CREATE INDEX IF NOT EXISTS idx_migration_history_name ON migration_history(migration_name);
                """,
                "sql_sqlite": """
                    CREATE TABLE IF NOT EXISTS migration_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        migration_name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        module TEXT,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        rollback_sql TEXT,
                        checksum TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_migration_history_name ON migration_history(migration_name);
                """,
                "module": "core"
            },
            
            # Clean up deprecated columns 
            "002_cleanup_deprecated_user_columns": {
                "description": "Remove deprecated user table columns that conflict with modular system",
                "sql_postgres": """
                    -- Remove deprecated columns that are now handled by modules
                    ALTER TABLE users DROP COLUMN IF EXISTS plan_type CASCADE;
                    ALTER TABLE users DROP COLUMN IF EXISTS trial_companion CASCADE;
                    ALTER TABLE users DROP COLUMN IF EXISTS companion_data CASCADE;
                    ALTER TABLE users DROP COLUMN IF EXISTS feature_preview_seen CASCADE;
                    ALTER TABLE users DROP COLUMN IF EXISTS trial_warning_sent CASCADE;
                    
                    -- Standardize remaining columns
                    ALTER TABLE users ALTER COLUMN trial_active TYPE BOOLEAN USING CASE WHEN trial_active = 1 THEN TRUE ELSE FALSE END;
                    ALTER TABLE users ALTER COLUMN email_verified TYPE BOOLEAN USING CASE WHEN email_verified = 1 THEN TRUE ELSE FALSE END;
                    ALTER TABLE users ALTER COLUMN is_admin TYPE BOOLEAN USING CASE WHEN is_admin = 1 THEN TRUE ELSE FALSE END;
                    ALTER TABLE users ALTER COLUMN terms_accepted TYPE BOOLEAN USING CASE WHEN terms_accepted = 1 THEN TRUE ELSE FALSE END;
                """,
                "sql_sqlite": """
                    -- SQLite doesn't support DROP COLUMN easily, so we'll rename deprecated columns
                    -- Create new clean users table
                    CREATE TABLE users_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        display_name TEXT,
                        email_verified BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        trial_start TIMESTAMP,
                        ip_address TEXT,
                        profile_image TEXT,
                        profile_image_data TEXT,
                        profile_image_filename TEXT,
                        trial_started_at TIMESTAMP,
                        trial_used_permanently BOOLEAN DEFAULT FALSE,
                        trial_expires_at TIMESTAMP,
                        user_plan TEXT DEFAULT 'bronze',
                        trial_active BOOLEAN DEFAULT FALSE,
                        is_admin BOOLEAN DEFAULT FALSE,
                        decoder_used INTEGER DEFAULT 0,
                        fortune_used INTEGER DEFAULT 0,
                        horoscope_used INTEGER DEFAULT 0,
                        referral_count INTEGER DEFAULT 0,
                        ad_free BOOLEAN DEFAULT FALSE,
                        plan TEXT DEFAULT 'bronze',
                        stripe_customer_id TEXT,
                        artistic_time INTEGER DEFAULT 0,
                        trial_credits INTEGER DEFAULT 0,
                        last_credit_reset DATE,
                        credits INTEGER DEFAULT 0,
                        purchased_credits INTEGER DEFAULT 0,
                        terms_accepted BOOLEAN DEFAULT FALSE,
                        terms_accepted_at TIMESTAMP,
                        terms_version TEXT,
                        terms_language TEXT DEFAULT 'en'
                    );
                    
                    -- Copy data from old table (excluding deprecated columns)
                    INSERT INTO users_new (
                        id, email, password_hash, display_name, email_verified, created_at,
                        trial_start, ip_address, profile_image, profile_image_data, profile_image_filename,
                        trial_started_at, trial_used_permanently, trial_expires_at, user_plan,
                        trial_active, is_admin, decoder_used, fortune_used, horoscope_used,
                        referral_count, ad_free, plan, stripe_customer_id, artistic_time,
                        trial_credits, last_credit_reset, credits, purchased_credits,
                        terms_accepted, terms_accepted_at, terms_version, terms_language
                    )
                    SELECT 
                        id, email, password_hash, display_name, 
                        CASE WHEN email_verified = 1 THEN TRUE ELSE FALSE END,
                        created_at, trial_start, ip_address, profile_image, profile_image_data, 
                        profile_image_filename, trial_started_at, trial_used_permanently, 
                        trial_expires_at, COALESCE(user_plan, 'bronze'),
                        CASE WHEN trial_active = 1 THEN TRUE ELSE FALSE END,
                        CASE WHEN is_admin = 1 THEN TRUE ELSE FALSE END,
                        COALESCE(decoder_used, 0), COALESCE(fortune_used, 0), COALESCE(horoscope_used, 0),
                        COALESCE(referral_count, 0), COALESCE(ad_free, FALSE), COALESCE(plan, 'bronze'),
                        stripe_customer_id, COALESCE(artistic_time, 0), COALESCE(trial_credits, 0),
                        last_credit_reset, COALESCE(credits, 0), COALESCE(purchased_credits, 0),
                        CASE WHEN terms_accepted = 1 THEN TRUE ELSE FALSE END,
                        terms_accepted_at, terms_version, COALESCE(terms_language, 'en')
                    FROM users;
                    
                    -- Replace old table
                    DROP TABLE users;
                    ALTER TABLE users_new RENAME TO users;
                    
                    -- Recreate indexes
                    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                    CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);
                """,
                "rollback_sql": "-- This migration cannot be easily rolled back",
                "module": "core"
            },
            
            # Voice module support
            "003_voice_module_support": {
                "description": "Add tables for voice journaling and chat features",
                "sql_postgres": """
                    CREATE TABLE IF NOT EXISTS voice_journal_entries (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        transcription TEXT NOT NULL,
                        analysis_summary TEXT,
                        emotions JSONB,
                        mood_score DECIMAL(3,1),
                        recommendations JSONB,
                        audio_duration DECIMAL(8,2),
                        processing_provider VARCHAR(50),
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS idx_voice_journal_user_id ON voice_journal_entries(user_id);
                    CREATE INDEX IF NOT EXISTS idx_voice_journal_created_at ON voice_journal_entries(created_at);
                    
                    CREATE TABLE IF NOT EXISTS voice_chat_sessions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        companion_id VARCHAR(50) NOT NULL,
                        session_start TIMESTAMPTZ DEFAULT NOW(),
                        session_end TIMESTAMPTZ,
                        message_count INTEGER DEFAULT 0,
                        total_duration DECIMAL(10,2) DEFAULT 0,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS idx_voice_chat_user_id ON voice_chat_sessions(user_id);
                    CREATE INDEX IF NOT EXISTS idx_voice_chat_companion ON voice_chat_sessions(companion_id);
                """,
                "sql_sqlite": """
                    CREATE TABLE IF NOT EXISTS voice_journal_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        transcription TEXT NOT NULL,
                        analysis_summary TEXT,
                        emotions TEXT, -- JSON string in SQLite
                        mood_score REAL,
                        recommendations TEXT, -- JSON string in SQLite
                        audio_duration REAL,
                        processing_provider TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_voice_journal_user_id ON voice_journal_entries(user_id);
                    CREATE INDEX IF NOT EXISTS idx_voice_journal_created_at ON voice_journal_entries(created_at);
                    
                    CREATE TABLE IF NOT EXISTS voice_chat_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        companion_id TEXT NOT NULL,
                        session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_end TIMESTAMP,
                        message_count INTEGER DEFAULT 0,
                        total_duration REAL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_voice_chat_user_id ON voice_chat_sessions(user_id);
                    CREATE INDEX IF NOT EXISTS idx_voice_chat_companion ON voice_chat_sessions(companion_id);
                """,
                "module": "voice"
            },
            
            # Notifications module support
            "004_notifications_module_support": {
                "description": "Add email tracking and notification preferences",
                "sql_postgres": """
                    CREATE TABLE IF NOT EXISTS email_sent_log (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        recipient_email VARCHAR(255) NOT NULL,
                        email_type VARCHAR(100) NOT NULL,
                        subject VARCHAR(500),
                        provider VARCHAR(50),
                        provider_id VARCHAR(255),
                        sent_at TIMESTAMPTZ DEFAULT NOW(),
                        delivery_status VARCHAR(50) DEFAULT 'sent',
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0
                    );
                    CREATE INDEX IF NOT EXISTS idx_email_log_user_id ON email_sent_log(user_id);
                    CREATE INDEX IF NOT EXISTS idx_email_log_type ON email_sent_log(email_type);
                    CREATE INDEX IF NOT EXISTS idx_email_log_sent_at ON email_sent_log(sent_at);
                    
                    CREATE TABLE IF NOT EXISTS user_notification_preferences (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        email_welcome BOOLEAN DEFAULT TRUE,
                        email_password_reset BOOLEAN DEFAULT TRUE,
                        email_trial_warning BOOLEAN DEFAULT TRUE,
                        email_subscription_updates BOOLEAN DEFAULT TRUE,
                        email_marketing BOOLEAN DEFAULT FALSE,
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_notification_prefs_user_id ON user_notification_preferences(user_id);
                """,
                "sql_sqlite": """
                    CREATE TABLE IF NOT EXISTS email_sent_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        recipient_email TEXT NOT NULL,
                        email_type TEXT NOT NULL,
                        subject TEXT,
                        provider TEXT,
                        provider_id TEXT,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        delivery_status TEXT DEFAULT 'sent',
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0
                    );
                    CREATE INDEX IF NOT EXISTS idx_email_log_user_id ON email_sent_log(user_id);
                    CREATE INDEX IF NOT EXISTS idx_email_log_type ON email_sent_log(email_type);
                    CREATE INDEX IF NOT EXISTS idx_email_log_sent_at ON email_sent_log(sent_at);
                    
                    CREATE TABLE IF NOT EXISTS user_notification_preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        email_welcome BOOLEAN DEFAULT TRUE,
                        email_password_reset BOOLEAN DEFAULT TRUE,
                        email_trial_warning BOOLEAN DEFAULT TRUE,
                        email_subscription_updates BOOLEAN DEFAULT TRUE,
                        email_marketing BOOLEAN DEFAULT FALSE,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_notification_prefs_user_id ON user_notification_preferences(user_id);
                """,
                "module": "notifications"
            },
            
            # Credit system consolidation
            "005_credits_system_consolidation": {
                "description": "Consolidate and clean up credit system columns",
                "sql_postgres": """
                    -- Add missing credit columns if they don't exist
                    ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_credits INTEGER DEFAULT 0;
                    ALTER TABLE users ADD COLUMN IF NOT EXISTS credits_reset_date DATE;
                    
                    -- Create credit transaction log
                    CREATE TABLE IF NOT EXISTS credit_transactions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        transaction_type VARCHAR(50) NOT NULL, -- 'deduct', 'refund', 'grant', 'reset'
                        feature VARCHAR(100), -- feature that used/granted credits
                        amount INTEGER NOT NULL,
                        balance_before INTEGER NOT NULL,
                        balance_after INTEGER NOT NULL,
                        reason VARCHAR(255),
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
                    CREATE INDEX IF NOT EXISTS idx_credit_transactions_type ON credit_transactions(transaction_type);
                    CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at);
                """,
                "sql_sqlite": """
                    -- SQLite ALTER TABLE ADD COLUMN is supported
                    ALTER TABLE users ADD COLUMN monthly_credits INTEGER DEFAULT 0;
                    ALTER TABLE users ADD COLUMN credits_reset_date DATE;
                    
                    -- Create credit transaction log
                    CREATE TABLE IF NOT EXISTS credit_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        transaction_type TEXT NOT NULL, -- 'deduct', 'refund', 'grant', 'reset'
                        feature TEXT, -- feature that used/granted credits
                        amount INTEGER NOT NULL,
                        balance_before INTEGER NOT NULL,
                        balance_after INTEGER NOT NULL,
                        reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
                    CREATE INDEX IF NOT EXISTS idx_credit_transactions_type ON credit_transactions(transaction_type);
                    CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at);
                """,
                "module": "credits"
            }
        }
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations"""
        try:
            if not self.database:
                return []
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Check if migration_history table exists
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                cursor.execute(format_query("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'migration_history'
                    )
                """))
            else:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='migration_history'
                """)
            
            if not cursor.fetchone():
                conn.close()
                return []
            
            # Get applied migrations
            cursor.execute("SELECT migration_name FROM migration_history ORDER BY applied_at")
            applied = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return applied
            
        except Exception as e:
            logger.error(f"Error getting applied migrations: {e}")
            return []
    
    def get_pending_migrations(self) -> List[Dict[str, Any]]:
        """Get list of pending migrations"""
        applied = self.get_applied_migrations()
        pending = []
        
        for name, migration in self.migrations.items():
            if name not in applied:
                pending.append({
                    "name": name,
                    "description": migration["description"],
                    "module": migration["module"]
                })
        
        return pending
    
    def apply_migration(self, migration_name: str) -> bool:
        """Apply a specific migration"""
        if migration_name not in self.migrations:
            logger.error(f"Migration {migration_name} not found")
            return False
        
        migration = self.migrations[migration_name]
        
        try:
            if not self.database:
                logger.error("Database not available")
                return False
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Determine which SQL to use
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                sql = migration["sql_postgres"]
            else:
                sql = migration["sql_sqlite"]
            
            # Execute migration SQL
            cursor.executescript(sql) if hasattr(cursor, 'executescript') else cursor.execute(sql)
            
            # Record migration as applied
            cursor.execute("""
                INSERT INTO migration_history (migration_name, description, module, rollback_sql)
                VALUES (?, ?, ?, ?)
            """, (
                migration_name,
                migration["description"],
                migration["module"],
                migration.get("rollback_sql", "")
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Applied migration: {migration_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply migration {migration_name}: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def apply_all_pending(self) -> Dict[str, Any]:
        """Apply all pending migrations"""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return {"success": True, "applied": 0, "skipped": 0, "failed": 0}
        
        applied_count = 0
        failed_count = 0
        
        for migration in pending:
            if self.apply_migration(migration["name"]):
                applied_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Migration summary: {applied_count} applied, {failed_count} failed")
        
        return {
            "success": failed_count == 0,
            "applied": applied_count,
            "failed": failed_count,
            "total_pending": len(pending)
        }
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get comprehensive migration status"""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        # Group by module
        modules = {}
        for name, migration in self.migrations.items():
            module = migration["module"]
            if module not in modules:
                modules[module] = {"total": 0, "applied": 0, "pending": 0}
            
            modules[module]["total"] += 1
            if name in applied:
                modules[module]["applied"] += 1
            else:
                modules[module]["pending"] += 1
        
        return {
            "total_migrations": len(self.migrations),
            "applied_migrations": len(applied),
            "pending_migrations": len(pending),
            "modules": modules,
            "applied_list": applied,
            "pending_list": [m["name"] for m in pending]
        }