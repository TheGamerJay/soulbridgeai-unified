#!/usr/bin/env python3
"""
Create Artistic Time Credit System Database Schema
Phase 1: Foundation for Soul Companions + Credit System
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_utils import get_database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_credit_system_tables():
    """Create all tables needed for the Artistic Time credit system"""
    
    db = get_database()
    if not db:
        logger.error("Cannot connect to database")
        return False
    
    conn = db.get_connection()
    cur = conn.cursor()
    
    try:
        logger.info("Creating Artistic Time credit system tables...")
        
        # 1. User Credits Table - Track credit balances and signup bonus
        logger.info("Creating user_credits table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_credits (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                credits_remaining INTEGER NOT NULL DEFAULT 0,
                last_reset_at TIMESTAMP,
                signup_bonus_used BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Credit Ledger - Complete audit trail of all credit transactions
        logger.info("Creating credit_ledger table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS credit_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                delta INTEGER NOT NULL,
                reason TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_credit_ledger_user 
            ON credit_ledger(user_id, created_at)
        """)
        
        # 3. Device Fingerprints - Anti-abuse tracking
        logger.info("Creating device_fingerprints table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS device_fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                fingerprint_sha256 TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (fingerprint_sha256)
            )
        """)
        
        # 4. IP Grants - Track IP addresses that received free credits
        logger.info("Creating ip_grants table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ip_grants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                granted BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for IP lookups
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_ip_grants_ip ON ip_grants(ip)
        """)
        
        # 5. Enhance existing stripe_subscriptions table if it exists
        logger.info("Enhancing stripe_subscriptions table...")
        try:
            cur.execute("""
                ALTER TABLE stripe_subscriptions 
                ADD COLUMN cadence TEXT
            """)
            logger.info("Added cadence column to stripe_subscriptions")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                logger.info("Cadence column already exists in stripe_subscriptions")
            else:
                logger.warning(f"Could not add cadence column: {e}")
        
        # 6. Rate Limiting Table - For signup abuse prevention
        logger.info("Creating rate_limits table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                key TEXT PRIMARY KEY,
                count INTEGER NOT NULL,
                window_end TIMESTAMP NOT NULL
            )
        """)
        
        # Initialize existing user with credit balance (user_id 104)
        logger.info("Initializing existing user credit balance...")
        cur.execute("""
            INSERT OR IGNORE INTO user_credits (user_id, credits_remaining, signup_bonus_used)
            VALUES (104, 100, TRUE)
        """)
        
        # Add initial ledger entry for the existing user
        cur.execute("""
            INSERT INTO credit_ledger (user_id, delta, reason, metadata)
            SELECT 104, 100, 'system_migration', '{"source": "initial_setup"}'
            WHERE NOT EXISTS (
                SELECT 1 FROM credit_ledger WHERE user_id = 104 AND reason = 'system_migration'
            )
        """)
        
        conn.commit()
        logger.info("✅ Artistic Time credit system tables created successfully!")
        
        # Verify tables were created
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%credit%' OR name LIKE '%fingerprint%' OR name LIKE '%ip_grants%' OR name LIKE '%rate_limit%'")
        tables = cur.fetchall()
        logger.info(f"Created tables: {[table[0] for table in tables]}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating credit system tables: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_credit_system():
    """Verify the credit system is working correctly"""
    
    db = get_database()
    conn = db.get_connection()
    cur = conn.cursor()
    
    try:
        logger.info("\n🔍 Verifying credit system...")
        
        # Check user credits
        cur.execute("SELECT user_id, credits_remaining, signup_bonus_used FROM user_credits WHERE user_id = 104")
        result = cur.fetchone()
        if result:
            user_id, credits, bonus_used = result
            logger.info(f"User {user_id}: {credits} credits, bonus used: {bonus_used}")
        else:
            logger.warning("No credit record found for user 104")
        
        # Check credit ledger
        cur.execute("SELECT COUNT(*) FROM credit_ledger WHERE user_id = 104")
        ledger_count = cur.fetchone()[0]
        logger.info(f"Credit ledger entries: {ledger_count}")
        
        # List all new tables
        cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND (
                name LIKE '%credit%' OR 
                name LIKE '%fingerprint%' OR 
                name LIKE '%ip_grants%' OR 
                name LIKE '%rate_limit%'
            )
        """)
        tables = cur.fetchall()
        logger.info(f"Credit system tables: {[table[0] for table in tables]}")
        
        logger.info("✅ Credit system verification complete!")
        
    except Exception as e:
        logger.error(f"Error verifying credit system: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("🚀 Setting up Artistic Time Credit System for Soul Companions...")
    
    if create_credit_system_tables():
        verify_credit_system()
        logger.info("\n🎯 Phase 1 Complete: Database foundation ready!")
        logger.info("Next: Create credit management functions and decorators")
    else:
        logger.error("❌ Failed to create credit system")
        sys.exit(1)