#!/usr/bin/env python3
"""
Database Schema for Subscriptions + Referrals + Cosmetics System
SoulBridge AI - Complete implementation

This module creates and manages the database tables for:
1. Subscription management (Growth/Max tiers)
2. Referral tracking system with anti-abuse validation
3. Cosmetic companions (Blayzike, Blazelian, Claude, Blayzo)
4. User cosmetic unlocks and equipped items
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def create_subscriptions_tables(db_connection):
    """Create subscription-related tables"""
    cursor = db_connection.cursor()
    
    # Subscriptions table - tracks Growth/Max tier subscriptions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            stripe_subscription_id VARCHAR(255) UNIQUE,
            stripe_customer_id VARCHAR(255),
            plan_type VARCHAR(20) NOT NULL CHECK (plan_type IN ('growth', 'max')),
            billing_interval VARCHAR(10) NOT NULL CHECK (billing_interval IN ('monthly', 'yearly')),
            status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'canceled', 'past_due', 'unpaid')),
            current_period_start TIMESTAMP NOT NULL,
            current_period_end TIMESTAMP NOT NULL,
            cancel_at_period_end BOOLEAN DEFAULT FALSE,
            canceled_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id) -- One subscription per user
        )
    """)
    
    # Subscription history - tracks all subscription changes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscription_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            subscription_id INTEGER,
            action VARCHAR(50) NOT NULL,
            old_plan VARCHAR(20),
            new_plan VARCHAR(20),
            billing_interval VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT, -- JSON for additional data
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL
        )
    """)
    
    logger.info("✅ Subscription tables created successfully")

def create_referrals_tables(db_connection):
    """Create referral system tables"""
    cursor = db_connection.cursor()
    
    # Referrals table - tracks referral relationships
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id SERIAL PRIMARY KEY,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL,
            referral_code VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'rewarded', 'invalid')),
            verification_method VARCHAR(50), -- 'email_phone', 'subscription', etc.
            verified_at TIMESTAMP NULL,
            rewarded_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (referrer_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (referred_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(referrer_id, referred_id), -- Prevent duplicate referrals
            CHECK (referrer_id != referred_id) -- Can't refer yourself
        )
    """)
    
    # Referral codes table - manages unique referral codes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referral_codes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            code VARCHAR(20) NOT NULL UNIQUE,
            uses_count INTEGER DEFAULT 0,
            max_uses INTEGER DEFAULT NULL, -- NULL = unlimited
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NULL,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Referral rewards table - tracks cosmetic unlocks from referrals
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referral_rewards (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            threshold_reached INTEGER NOT NULL, -- 2, 5, 8, 10 referrals
            cosmetic_id INTEGER NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (cosmetic_id) REFERENCES cosmetics(id) ON DELETE CASCADE,
            UNIQUE(user_id, threshold_reached) -- One reward per threshold
        )
    """)
    
    logger.info("✅ Referral tables created successfully")

def create_cosmetics_tables(db_connection):
    """Create cosmetic system tables"""
    cursor = db_connection.cursor()
    
    try:
        # Cosmetics table - defines all available cosmetic companions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cosmetics (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                display_name VARCHAR(100) NOT NULL,
                description TEXT,
                type VARCHAR(20) NOT NULL CHECK (type IN ('companion', 'avatar', 'theme')),
                rarity VARCHAR(20) NOT NULL CHECK (rarity IN ('common', 'rare', 'epic', 'legendary')),
                unlock_method VARCHAR(50) NOT NULL CHECK (unlock_method IN ('referral', 'purchase', 'achievement', 'trial')),
                unlock_requirement TEXT, -- JSON with specific requirements
                image_url VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Ensure cosmetic companions have proper metadata
                CHECK (
                    (type = 'companion' AND unlock_method IN ('referral', 'purchase')) OR
                    type != 'companion'
                )
            )
        """)
        db_connection.commit()
        logger.info("✅ Cosmetics table created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create cosmetics table: {e}")
        raise
    
    try:
        # User cosmetics table - tracks which cosmetics each user has unlocked
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_cosmetics (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                cosmetic_id INTEGER NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                unlock_source VARCHAR(50) NOT NULL, -- 'referral_2', 'referral_5', 'purchase', etc.
                is_equipped BOOLEAN DEFAULT FALSE,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (cosmetic_id) REFERENCES cosmetics(id) ON DELETE CASCADE,
                UNIQUE(user_id, cosmetic_id) -- Can't unlock same cosmetic twice
            )
        """)
        
        # User equipped cosmetics - tracks currently equipped cosmetics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_equipped_cosmetics (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                cosmetic_type VARCHAR(20) NOT NULL,
                cosmetic_id INTEGER NOT NULL,
                equipped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (cosmetic_id) REFERENCES cosmetics(id) ON DELETE CASCADE,
                UNIQUE(user_id, cosmetic_type) -- One equipped item per type
            )
        """)
        
        db_connection.commit()
        logger.info("✅ Cosmetic tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create user cosmetic tables: {e}")
        raise

def insert_default_cosmetics(db_connection):
    """Insert the default referral reward cosmetics"""
    cursor = db_connection.cursor()
    
    # Default cosmetic companions from the spec
    default_cosmetics = [
        {
            'name': 'blayzike',
            'display_name': 'Blayzike',
            'description': 'Unlock this exclusive companion by referring 2 friends to SoulBridge AI',
            'type': 'companion',
            'rarity': 'rare',
            'unlock_method': 'referral',
            'unlock_requirement': '{"referral_threshold": 2}',
            'image_url': '/static/logos/Blayzike_Referral.png'
        },
        {
            'name': 'blazelian',
            'display_name': 'Blazelian',
            'description': 'Unlock this mystical companion by referring 4 friends to SoulBridge AI',
            'type': 'companion',
            'rarity': 'epic',
            'unlock_method': 'referral',
            'unlock_requirement': '{"referral_threshold": 4}',
            'image_url': '/static/logos/Blazelian.png'
        },
        {
            'name': 'nyxara',
            'display_name': 'Nyxara',
            'description': 'Unlock this enigmatic companion by referring 6 friends to SoulBridge AI',
            'type': 'companion',
            'rarity': 'epic',
            'unlock_method': 'referral',
            'unlock_requirement': '{"referral_threshold": 6}',
            'image_url': '/static/logos/Nyxara.png'
        },
        {
            'name': 'claude',
            'display_name': 'Claude',
            'description': 'Unlock the legendary Claude companion by referring 8 friends to SoulBridge AI',
            'type': 'companion',
            'rarity': 'legendary',
            'unlock_method': 'referral',
            'unlock_requirement': '{"referral_threshold": 8}',
            'image_url': '/static/logos/Claude_Referral.png'
        },
        {
            'name': 'blayzo',
            'display_name': 'Blayzo',
            'description': 'The ultimate companion! Unlock by referring 10 friends to SoulBridge AI',
            'type': 'companion',
            'rarity': 'legendary',
            'unlock_method': 'referral',
            'unlock_requirement': '{"referral_threshold": 10}',
            'image_url': '/static/logos/Blayzo_Referral.png'
        }
    ]
    
    for cosmetic in default_cosmetics:
        # Check if cosmetic already exists
        cursor.execute("SELECT id FROM cosmetics WHERE name = %s", (cosmetic['name'],))
        if cursor.fetchone():
            logger.info(f"📦 Cosmetic {cosmetic['name']} already exists, skipping")
            continue
        
        cursor.execute("""
            INSERT INTO cosmetics (name, display_name, description, type, rarity, unlock_method, unlock_requirement, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            cosmetic['name'],
            cosmetic['display_name'],
            cosmetic['description'],
            cosmetic['type'],
            cosmetic['rarity'],
            cosmetic['unlock_method'],
            cosmetic['unlock_requirement'],
            cosmetic['image_url']
        ))
        
        logger.info(f"📦 Created cosmetic: {cosmetic['display_name']}")
    
    db_connection.commit()
    logger.info("✅ Default cosmetics inserted successfully")

def create_indexes(db_connection):
    """Create database indexes for performance"""
    cursor = db_connection.cursor()
    
    # Subscription indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_id ON subscriptions(stripe_subscription_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status)")
    
    # Referral indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_code ON referrals(referral_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status)")
    
    # Cosmetic indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_cosmetics_user ON user_cosmetics(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_cosmetics_equipped ON user_cosmetics(user_id, is_equipped)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_equipped_type ON user_equipped_cosmetics(user_id, cosmetic_type)")
    
    db_connection.commit()
    logger.info("✅ Database indexes created successfully")

def initialize_subscriptions_referrals_cosmetics_schema():
    """
    Main function to initialize the complete schema
    Call this during application startup
    """
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            logger.error("❌ Database not available for schema initialization")
            return False
        
        conn = db.get_connection()
        
        logger.info("🚀 Initializing Subscriptions + Referrals + Cosmetics schema...")
        
        # Create all tables (cosmetics first due to foreign key dependencies)
        create_subscriptions_tables(conn)
        create_cosmetics_tables(conn)
        create_referrals_tables(conn)
        
        # Insert default data
        insert_default_cosmetics(conn)
        
        # Create indexes
        create_indexes(conn)
        
        conn.close()
        
        logger.info("✅ Subscriptions + Referrals + Cosmetics schema initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize schema: {e}")
        return False

# Utility functions for schema management

def get_user_subscription(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user's current subscription details"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return None
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, stripe_subscription_id, stripe_customer_id, plan_type, 
                   billing_interval, status, current_period_start, current_period_end,
                   cancel_at_period_end, canceled_at, created_at
            FROM subscriptions 
            WHERE user_id = ? AND status != 'canceled'
            ORDER BY created_at DESC 
            LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'stripe_subscription_id': row[1],
            'stripe_customer_id': row[2],
            'plan_type': row[3],
            'billing_interval': row[4],
            'status': row[5],
            'current_period_start': row[6],
            'current_period_end': row[7],
            'cancel_at_period_end': row[8],
            'canceled_at': row[9],
            'created_at': row[10]
        }
        
    except Exception as e:
        logger.error(f"Failed to get user subscription: {e}")
        return None

def get_user_referral_stats(user_id: int) -> Dict[str, Any]:
    """Get user's referral statistics"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return {'total_referrals': 0, 'verified_referrals': 0, 'pending_referrals': 0}
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get referral counts
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'verified' THEN 1 ELSE 0 END) as verified,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
            FROM referrals 
            WHERE referrer_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'total_referrals': row[0] or 0,
            'verified_referrals': row[1] or 0, 
            'pending_referrals': row[2] or 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get referral stats: {e}")
        return {'total_referrals': 0, 'verified_referrals': 0, 'pending_referrals': 0}

def get_user_cosmetics(user_id: int) -> Dict[str, Any]:
    """Get user's unlocked and equipped cosmetics"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return {'unlocked': [], 'equipped': {}}
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get unlocked cosmetics
        cursor.execute("""
            SELECT c.id, c.name, c.display_name, c.type, c.rarity, 
                   uc.unlocked_at, uc.unlock_source, uc.is_equipped
            FROM user_cosmetics uc
            JOIN cosmetics c ON uc.cosmetic_id = c.id
            WHERE uc.user_id = ?
            ORDER BY uc.unlocked_at DESC
        """, (user_id,))
        
        unlocked = []
        for row in cursor.fetchall():
            unlocked.append({
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'type': row[3],
                'rarity': row[4],
                'unlocked_at': row[5],
                'unlock_source': row[6],
                'is_equipped': row[7]
            })
        
        # Get equipped cosmetics
        cursor.execute("""
            SELECT uec.cosmetic_type, c.id, c.name, c.display_name
            FROM user_equipped_cosmetics uec
            JOIN cosmetics c ON uec.cosmetic_id = c.id
            WHERE uec.user_id = ?
        """, (user_id,))
        
        equipped = {}
        for row in cursor.fetchall():
            equipped[row[0]] = {
                'id': row[1],
                'name': row[2],
                'display_name': row[3]
            }
        
        conn.close()
        
        return {
            'unlocked': unlocked,
            'equipped': equipped
        }
        
    except Exception as e:
        logger.error(f"Failed to get user cosmetics: {e}")
        return {'unlocked': [], 'equipped': {}}

if __name__ == "__main__":
    # Test schema initialization
    initialize_subscriptions_referrals_cosmetics_schema()