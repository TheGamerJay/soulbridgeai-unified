#!/usr/bin/env python3
"""
============================================
📦 Unified Tier + Trial + Credits System
============================================
Single clean block that merges credits + daily limits with correct Bronze/Silver/Gold isolation and trial behavior.

This fixes:
- Silver showing Bronze limits
- Gold showing wrong features  
- Trial unlocking features but keeping plan limits
- Credits applying only to premium features
- No more "∞ unlimited" mix-up
"""

from datetime import datetime, timedelta
from flask import session
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)

def ensure_database_schema():
    """
    Ensure all required tables and columns exist for the unified tier system
    """
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("📊 SCHEMA: No DATABASE_URL found")
            return False
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        logger.info("📊 SCHEMA: Starting database schema migration")
        
        # Create feature_usage table if it doesn't exist
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feature_usage (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    feature VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("📊 SCHEMA: feature_usage table created/verified")
        except Exception as e:
            logger.error(f"📊 SCHEMA ERROR creating feature_usage: {e}")
            conn.rollback()
        
        # Add missing columns to users table one by one
        missing_columns = [
            ('timezone', 'VARCHAR(50) DEFAULT \'America/New_York\''),
            ('credits', 'INTEGER DEFAULT 0'),
            ('last_credit_reset', 'TIMESTAMP'),
            ('purchased_credits', 'INTEGER DEFAULT 0'),
            ('trial_active', 'INTEGER DEFAULT 0'),
            ('trial_started_at', 'TIMESTAMP'),
            ('trial_expires_at', 'TIMESTAMP'),
            ('trial_used_permanently', 'INTEGER DEFAULT 0')
        ]
        
        for column_name, column_def in missing_columns:
            try:
                # Check if column exists first to avoid errors
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = %s
                """, (column_name,))
                
                if cur.fetchone():
                    logger.info(f"📊 SCHEMA: Column users.{column_name} already exists")
                else:
                    # Column doesn't exist, add it
                    cur.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
                    conn.commit()
                    logger.info(f"📊 SCHEMA: Added column users.{column_name}")
                    
            except Exception as e:
                logger.error(f"📊 SCHEMA ERROR with users.{column_name}: {e}")
                conn.rollback()
        
        # Create index for performance
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_feature_usage_user_feature_date ON feature_usage(user_id, feature, DATE(created_at))")
            conn.commit()
            logger.info("📊 SCHEMA: Index created/verified")
        except Exception as e:
            logger.error(f"📊 SCHEMA ERROR creating index: {e}")
            conn.rollback()
        
        # Create tier_limits table for proper per-tier limit management
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tier_limits (
                    id SERIAL PRIMARY KEY,
                    tier TEXT NOT NULL CHECK (tier IN ('bronze','silver','gold')),
                    feature TEXT NOT NULL CHECK (feature IN ('decoder','fortune','horoscope')),
                    daily_limit INTEGER,
                    UNIQUE (tier, feature)
                )
            """)
            conn.commit()
            logger.info("📊 SCHEMA: tier_limits table created/verified")
            
            # Seed default limits
            default_limits = [
                ('bronze','decoder',3), ('bronze','fortune',2), ('bronze','horoscope',3),
                ('silver','decoder',15), ('silver','fortune',8), ('silver','horoscope',10),
                ('gold','decoder',None), ('gold','fortune',None), ('gold','horoscope',None)
            ]
            
            for tier, feature, limit in default_limits:
                cur.execute("""
                    INSERT INTO tier_limits (tier, feature, daily_limit)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (tier, feature) DO NOTHING
                """, (tier, feature, limit))
            conn.commit()
            logger.info("📊 SCHEMA: Default tier limits seeded")
            
        except Exception as e:
            logger.error(f"📊 SCHEMA ERROR creating tier_limits: {e}")
            conn.rollback()
        
        conn.close()
        logger.info("📊 SCHEMA: Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"📊 SCHEMA ERROR: {e}")
        return False

def get_limits_for_tier(tier: str) -> dict:
    """Get feature limits for a specific tier from database"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            # PostgreSQL
            import psycopg2
            from psycopg2.extras import RealDictCursor
            conn = psycopg2.connect(database_url)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT feature, daily_limit
                    FROM tier_limits
                    WHERE tier = %s
                    ORDER BY feature
                """, (tier,))
                rows = cur.fetchall()
            conn.close()
        else:
            # SQLite
            import sqlite3
            conn = sqlite3.connect('soulbridge.db')
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT feature, daily_limit
                FROM tier_limits
                WHERE tier = ?
                ORDER BY feature
            """, (tier,))
            rows = cur.fetchall()
            conn.close()
        
        # Return dict like {'decoder': 3, 'fortune': 2, 'horoscope': 3}
        return {row['feature']: row['daily_limit'] for row in rows}
        
    except Exception as e:
        logger.error(f"📊 ERROR getting limits for tier {tier}: {e}")
        # Fallback to hardcoded limits
        return DAILY_LIMITS.get(tier, DAILY_LIMITS.get('bronze', {}))

def set_limits_for_tier(tier: str, limits: dict) -> bool:
    """Set feature limits for a specific tier in database"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            # PostgreSQL
            import psycopg2
            conn = psycopg2.connect(database_url)
            with conn.cursor() as cur:
                for feature, daily_limit in limits.items():
                    cur.execute("""
                        INSERT INTO tier_limits (tier, feature, daily_limit)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (tier, feature)
                        DO UPDATE SET daily_limit = EXCLUDED.daily_limit
                    """, (tier, feature, daily_limit))
            conn.commit()
            conn.close()
        else:
            # SQLite
            import sqlite3
            conn = sqlite3.connect('soulbridge.db')
            cur = conn.cursor()
            for feature, daily_limit in limits.items():
                cur.execute("""
                    INSERT OR REPLACE INTO tier_limits (tier, feature, daily_limit)
                    VALUES (?, ?, ?)
                """, (tier, feature, daily_limit))
            conn.commit()
            conn.close()
        
        logger.info(f"📊 Updated limits for tier {tier}: {limits}")
        return True
        
    except Exception as e:
        logger.error(f"📊 ERROR setting limits for tier {tier}: {e}")
        return False

def get_user_timezone(user_id):
    """Get user's timezone, default to Eastern Time"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return 'America/New_York'  # Default fallback
            
        # Ensure schema exists first
        ensure_database_schema()
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Try to get user's timezone from database
        cur.execute("SELECT timezone FROM users WHERE id = %s", (user_id,))
        result = cur.fetchone()
        conn.close()
        
        if result and result[0]:
            return result[0]
        else:
            return 'America/New_York'  # Default to Eastern Time
            
    except Exception as e:
        logger.error(f"Error getting user timezone: {e}")
        return 'America/New_York'  # Default fallback

def check_active_subscription(user_id, plan):
    """
    Check if user has an active subscription for the given plan
    Returns True if user has active subscription OR is in grace period, False if cancelled/expired
    """
    try:
        # Use new subscription manager for grace period support
        from subscription_manager import check_subscription_status
        
        status = check_subscription_status(user_id)
        
        # User has active subscription or is in grace period for this plan
        if status.get("active") and status.get("plan") == plan:
            grace_period = status.get("grace_period", False)
            logger.info(f"🔍 SUBSCRIPTION CHECK: User {user_id} plan {plan} - Active: True, Grace: {grace_period}")
            return True
        
        # Fallback to old subscription table check if new system fails
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return False
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Check subscriptions table for active subscription
        cur.execute("""
            SELECT status, plan_type FROM subscriptions 
            WHERE user_id = %s AND plan_type = %s 
            ORDER BY created_at DESC LIMIT 1
        """, (user_id, plan))
        
        result = cur.fetchone()
        conn.close()
        
        if result:
            status_val, plan_type = result
            # Active subscription means status is 'active' and plan matches
            is_active = (status_val == 'active' and plan_type == plan)
            logger.info(f"🔍 SUBSCRIPTION CHECK (FALLBACK): User {user_id} plan {plan} - Status: {status_val}, Active: {is_active}")
            return is_active
        else:
            # No subscription record found - likely free user or trial
            logger.info(f"🔍 SUBSCRIPTION CHECK: User {user_id} plan {plan} - No subscription record found")
            return False
            
    except Exception as e:
        logger.error(f"Error checking subscription status: {e}")
        return False

# DAILY LIMITS (non-credit features)
DAILY_LIMITS = {
    "bronze":  {"decoder": 3,  "fortune": 2,  "horoscope": 3, "creative_writer": 2},    # Bronze tier
    "silver":  {"decoder": 15, "fortune": 8,  "horoscope": 10, "creative_writer": 20},  # Silver tier  
    "gold":    {"decoder": 999999, "fortune": 999, "horoscope": 999999, "creative_writer": 999999}  # Gold tier
}

# MONTHLY CREDITS (premium features)
MONTHLY_CREDITS = {
    "bronze": 0,      # Bronze tier gets no monthly credits
    "silver": 200,    # 200 credits/month for Silver
    "gold":   500     # 500 credits/month for Gold
}

# FEATURES THAT REQUIRE CREDITS
CREDIT_FEATURES = ["ai_images", "voice_journaling", "relationship_profiles", "meditations"]

# EFFECTIVE PLAN (trial never changes what tier you are)
def get_effective_plan(user_plan: str, trial_active: bool) -> str:
    """
    5hr trial unlocks gold tier features but keeps actual plan limits
    - For feature access: trial gives gold tier access
    - For usage limits: always use actual plan (handled separately)
    """
    # DEBUG: Log the function call
    logger.info(f"🎯 GET_EFFECTIVE_PLAN DEBUG: user_plan='{user_plan}', trial_active={trial_active}")
    
    if trial_active and user_plan in ["bronze"]:
        logger.info(f"🎯 GET_EFFECTIVE_PLAN: Returning 'gold' for bronze user on trial")
        return "gold"  # Unlock all features during trial
    
    logger.info(f"🎯 GET_EFFECTIVE_PLAN: Returning '{user_plan}' (no trial or already premium)")
    return user_plan  # Non-trial or already premium users

# GET DAILY LIMITS (always based on actual plan, not trial)
def get_feature_limit(user_plan: str, feature: str, trial_active: bool = False) -> int:
    """
    Get feature limits based on subscription plan from database
    TRIAL DOES NOT CHANGE DAILY LIMITS - trial only unlocks access to companions/features
    Per CLAUDE.md: Trial gives 60 credits + companion access, but Bronze users keep Bronze limits
    """
    # ALWAYS use actual user plan for daily limits, regardless of trial
    # Trial unlocks access but doesn't change usage limits
    plan = user_plan
    
    # Get limits from database first, fallback to hardcoded
    try:
        db_limits = get_limits_for_tier(plan)
        limit = db_limits.get(feature)
        
        # Handle None (unlimited) vs missing feature
        if limit is None and feature in db_limits:
            return 999999  # Unlimited represented as large number for UI compatibility
        elif limit is not None:
            return limit
        else:
            # Feature not found in database, use hardcoded fallback
            return DAILY_LIMITS.get(plan, {}).get(feature, 0)
            
    except Exception as e:
        logger.error(f"📊 ERROR getting feature limit for {plan}/{feature}: {e}")
        # Fallback to hardcoded limits
        return DAILY_LIMITS.get(plan, {}).get(feature, 0)

# GET TRIAL TRAINER TIME (60 credits for free users during 5hr trial)
def get_trial_trainer_time(user_id):
    """
    Get trainer time credits for bronze users during 5hr trial
    Returns 60 credits for Mini Studio access during trial period
    SECURITY: Validates trial status against database, not session
    """
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return 0
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Check actual trial status from database, not session
        cur.execute("""
            SELECT user_plan, trial_active, trial_started_at 
            FROM users WHERE id = %s
        """, (user_id,))
        result = cur.fetchone()
        conn.close()
        
        if not result:
            return 0
            
        user_plan, trial_active, trial_started_at = result
        
        # Verify trial is actually active and not expired
        if user_plan in ["bronze"] and trial_active and trial_started_at:
            # Simple inline trial check (avoiding circular imports)
            from datetime import datetime, timezone
            try:
                if isinstance(trial_started_at, str):
                    started = datetime.fromisoformat(trial_started_at.replace('Z', '+00:00'))
                else:
                    started = trial_started_at
                
                # Check if trial is still within 5-hour window
                elapsed = datetime.now(timezone.utc) - started
                if elapsed.total_seconds() < 5 * 3600:  # 5 hours
                    return 60
            except Exception as e:
                logger.error(f"Error checking trial time: {e}")
                pass
        
        return 0
            
    except Exception as e:
        logger.error(f"Error getting trial trainer time: {e}")
        return 0

# GET CREDITS FOR USER (resets monthly with NO ROLLOVER, based on actual plan)
def get_user_credits(user_id):
    """
    Get user's available credits, auto-reset monthly based on actual plan
    IMPORTANT: Credits DO NOT roll over - any unused credits are lost at reset
    Trial users get 60 trainer time credits during trial
    """
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return 0
            
        # Ensure schema exists first
        ensure_database_schema()
        
        # For trial users, give them 60 trainer time (validates against database)
        trial_credits = get_trial_trainer_time(user_id)
        if trial_credits > 0:
            logger.info(f"🎯 TRIAL CREDITS: User {user_id} gets {trial_credits} trainer time during trial")
            return trial_credits
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute("""
            SELECT credits, last_credit_reset, plan_type, purchased_credits FROM users WHERE id = %s
        """, (user_id,))
        row = cur.fetchone()
        
        if not row:
            conn.close()
            return 0
            
        credits, last_reset, plan_type, purchased_credits = row
        plan = plan_type or session.get("user_plan", "bronze")
        purchased_credits = purchased_credits or 0

        now = datetime.utcnow()

        # Reset if 1 month has passed - ONLY FOR ACTIVE SUBSCRIBERS  
        # Fix datetime vs date comparison issue
        if not last_reset:
            needs_reset = True
        else:
            # Convert last_reset to datetime if it's a date object
            if hasattr(last_reset, 'date'):
                # It's already a datetime
                reset_datetime = last_reset
            else:
                # It's a date, convert to datetime
                reset_datetime = datetime.combine(last_reset, datetime.min.time())
            
            needs_reset = (now - reset_datetime).days >= 30
        
        if needs_reset:
            # Check if user has active subscription before resetting
            subscription_active = check_active_subscription(user_id, plan)
            
            if subscription_active and plan in ['silver', 'gold']:
                # ACTIVE SUBSCRIBER: Reset to plan allowance (no rollover)
                plan_credits = MONTHLY_CREDITS.get(plan, 0)
                
                # Log credit loss if user had unused credits
                old_total = (credits or 0) + purchased_credits
                if old_total > 0:
                    logger.info(f"💳 CREDITS LOST: Active subscriber {user_id} lost {old_total} unused credits (no rollover policy)")
                
                cur.execute("""
                    UPDATE users
                    SET credits = %s, last_credit_reset = %s, purchased_credits = 0
                    WHERE id = %s
                """, (plan_credits, now, user_id))
                conn.commit()
                logger.info(f"💳 CREDITS RESET: Active subscriber {user_id} ({plan}) reset to {plan_credits} credits")
                
                conn.close()
                return plan_credits
            else:
                # CANCELLED/FREE USER: No reset, just update timestamp, keep current credits until month end
                cur.execute("""
                    UPDATE users
                    SET last_credit_reset = %s
                    WHERE id = %s
                """, (now, user_id))
                conn.commit()
                logger.info(f"💳 NO RESET: Cancelled/Free user {user_id} keeps current credits until month end")
                
                # Return current credits (they keep what they have until month end)
                total_credits = (credits or 0) + purchased_credits
                conn.close()
                return total_credits
        else:
            # Return total of plan credits + purchased credits
            total_credits = (credits or 0) + purchased_credits
            conn.close()
            return total_credits

    except Exception as e:
        logger.error(f"Error getting user credits: {e}")
        return 0

# DEDUCT CREDITS WHEN USING PREMIUM FEATURE  
def deduct_credits(user_id, amount):
    """
    Deduct credits for premium feature usage with atomic transaction safety
    Prioritizes purchased credits first, then plan credits
    Returns True if successful, False if insufficient credits
    """
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return False
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Start atomic transaction
        cur.execute("BEGIN")
        
        # Lock the user row to prevent race conditions
        cur.execute("SELECT credits, purchased_credits FROM users WHERE id = %s FOR UPDATE", (user_id,))
        row = cur.fetchone()
        
        if not row:
            cur.execute("ROLLBACK")
            conn.close()
            return False

        plan_credits = row[0] or 0
        purchased_credits = row[1] or 0
        total_credits = plan_credits + purchased_credits
        
        if total_credits >= amount:
            # Deduct from purchased credits first (they don't rollover)
            if purchased_credits >= amount:
                new_purchased = purchased_credits - amount
                cur.execute("UPDATE users SET purchased_credits = %s WHERE id = %s", (new_purchased, user_id))
                logger.info(f"💳 PURCHASED CREDITS USED: User {user_id} spent {amount} purchased credits, {new_purchased} purchased remaining")
            else:
                # Use all purchased credits, then deduct from plan credits
                remaining_to_deduct = amount - purchased_credits
                new_plan_credits = plan_credits - remaining_to_deduct
                cur.execute("UPDATE users SET purchased_credits = 0, credits = %s WHERE id = %s", (new_plan_credits, user_id))
                logger.info(f"💳 MIXED CREDITS USED: User {user_id} spent {purchased_credits} purchased + {remaining_to_deduct} plan credits")
            
            # Commit the atomic transaction
            cur.execute("COMMIT")
            conn.close()
            return True
        else:
            # Not enough credits - rollback transaction
            cur.execute("ROLLBACK")
            conn.close()
            logger.warning(f"💳 INSUFFICIENT CREDITS: User {user_id} has {total_credits} total, needs {amount}")
            return False
        
    except Exception as e:
        # Ensure rollback on any error
        try:
            cur.execute("ROLLBACK")
        except:
            pass
        logger.error(f"Error deducting credits: {e}")
        return False

# CHECK IF USER CAN ACCESS FEATURE
def can_access_feature(user_id, feature):
    """
    Unified feature access check combining daily limits and credits
    Trial unlocks feature access but keeps plan limits/credits
    """
    try:
        trial_active = session.get("trial_active", False)
        plan = session.get("user_plan", "bronze")
        effective_plan = get_effective_plan(plan, trial_active)

        # Daily limit features (decoder, fortune, horoscope, creative_writer)
        if feature in ["decoder", "fortune", "horoscope", "creative_writer"]:
            if feature == "decoder":
                # Decoder available to all tiers
                limit = get_feature_limit(plan, feature, trial_active)
                return limit > 0
            elif feature in ["fortune", "horoscope"]:
                # Fortune/Horoscope: Trial removes the lock for bronze users
                if plan == "bronze" and trial_active:
                    # Bronze user on trial can use these features (lock removed)
                    limit = get_feature_limit(plan, feature, trial_active)
                    return limit > 0
                elif plan in ["silver", "gold"]:
                    # Silver/Gold users always have access
                    limit = get_feature_limit(plan, feature, trial_active)
                    return limit > 0
                else:
                    # Bronze user without trial - locked
                    return False
            elif feature == "creative_writer":
                # Creative writer available to all tiers (with different limits)
                limit = get_feature_limit(plan, feature, trial_active)
                return limit > 0

        # Credit-based features (AI images, voice journaling, etc.)
        if feature in CREDIT_FEATURES:
            # Trial removes the lock for bronze users
            if plan == "bronze" and trial_active:
                # Bronze user on trial can use these features (but with 0 credits)
                credits = get_user_credits(user_id)
                return credits >= 0  # Allow access even with 0 credits during trial
            elif plan in ["silver", "gold"]:
                # Silver/Gold users always have access
                credits = get_user_credits(user_id)
                return credits > 0
            else:
                # Bronze user without trial - locked
                return False
        
        # Mini Studio (gold tier exclusive with trainer time)
        if feature == "mini_studio":
            if plan == "gold":
                # Gold users have full access with their trainer time
                return True
            elif plan == "bronze" and trial_active:
                # Bronze users on trial get 60 trainer time to taste Mini Studio
                return True  # Access granted, will handle trainer time separately
            else:
                # Silver users and bronze users without trial - no access
                return False

        # All other features: Trial removes locks for bronze users
        if plan == "bronze" and trial_active:
            return True  # Trial removes all locks
        return plan in ["silver", "gold"]
        
    except Exception as e:
        logger.error(f"Error checking feature access: {e}")
        return False

# GET FEATURE USAGE FOR TODAY
def get_feature_usage_today(user_id, feature):
    """
    Get how many times a feature was used today
    """
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return 0
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Get user's timezone for personalized daily reset
        user_timezone = get_user_timezone(user_id)
        
        # Set session timezone to user's timezone
        cur.execute(f"SET TIME ZONE '{user_timezone}'")
        
        # Get today's date in user's timezone
        cur.execute("SELECT CURRENT_DATE")
        today_user_tz = cur.fetchone()[0]
        
        # Count usage for today in user's timezone
        cur.execute("""
            SELECT COUNT(*) FROM feature_usage 
            WHERE user_id = %s AND feature = %s 
            AND DATE(created_at AT TIME ZONE 'UTC' AT TIME ZONE %s) = %s
        """, (user_id, feature, user_timezone, today_user_tz))
        
        result = cur.fetchone()
        conn.close()
        
        return result[0] if result else 0
        
    except Exception as e:
        logger.error(f"Error getting feature usage: {e}")
        return 0

# INCREMENT FEATURE USAGE
def increment_feature_usage(user_id, feature):
    """
    Record feature usage for daily limit tracking
    """
    try:
        logger.info(f"📊 INCREMENT_FEATURE_USAGE: user_id={user_id}, feature={feature}")
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("📊 INCREMENT_FEATURE_USAGE: No DATABASE_URL")
            return False
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Ensure schema exists first
        ensure_database_schema()
        
        # Insert usage record
        logger.info(f"📊 INCREMENT_FEATURE_USAGE: Inserting record for user {user_id}, feature {feature}")
        cur.execute("""
            INSERT INTO feature_usage (user_id, feature)
            VALUES (%s, %s)
        """, (user_id, feature))
        
        conn.commit()
        logger.info(f"📊 INCREMENT_FEATURE_USAGE: Successfully inserted and committed for user {user_id}, feature {feature}")
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"📊 INCREMENT_FEATURE_USAGE ERROR: {e}")
        return False

# UNIFIED TIER STATUS FOR API RESPONSES
def get_tier_status(user_id):
    """
    Get complete tier status including limits, credits, and feature access
    """
    try:
        # Ensure database schema is up to date
        ensure_database_schema()
        trial_active = session.get("trial_active", False)
        plan = session.get("user_plan", "bronze")
        effective_plan = get_effective_plan(plan, trial_active)
        
        # DEBUG: Log what we got from session
        logger.info(f"🔍 UNIFIED DEBUG: user_id={user_id}, plan='{plan}', trial={trial_active}, effective='{effective_plan}'")
        
        # Get current usage from session for creative_writer (matches app.py implementation)
        decoder_usage = get_feature_usage_today(user_id, "decoder")
        fortune_usage = get_feature_usage_today(user_id, "fortune") 
        horoscope_usage = get_feature_usage_today(user_id, "horoscope")
        
        # Creative writer uses session-based tracking like in app.py
        today_str = datetime.now().strftime("%Y-%m-%d")
        creative_usage_key = f'creative_usage_{user_id}_{today_str}'
        creative_usage = session.get(creative_usage_key, 0)
        
        # Get limits (always based on actual plan)
        decoder_limit = get_feature_limit(plan, "decoder", trial_active)
        fortune_limit = get_feature_limit(plan, "fortune", trial_active)
        horoscope_limit = get_feature_limit(plan, "horoscope", trial_active)
        creative_limit = get_feature_limit(plan, "creative_writer", trial_active)
        
        # DEBUG: Log limits calculation
        logger.info(f"🎯 LIMITS DEBUG: actual_plan='{plan}', effective_plan='{effective_plan}', trial={trial_active}")
        logger.info(f"🎯 LIMITS VALUES: decoder={decoder_limit}, fortune={fortune_limit}, horoscope={horoscope_limit}, creative={creative_limit}")
        
        # Get credits
        credits = get_user_credits(user_id)
        
        return {
            "user_plan": plan,
            "effective_plan": effective_plan,
            "trial_active": trial_active,
            "limits": {
                "decoder": decoder_limit,
                "fortune": fortune_limit,
                "horoscope": horoscope_limit,
                "creative_writer": creative_limit
            },
            "usage": {
                "decoder": decoder_usage,
                "fortune": fortune_usage,
                "horoscope": horoscope_usage,
                "creative_writer": creative_usage
            },
            "credits": credits,
            "feature_access": {
                "decoder": can_access_feature(user_id, "decoder"),
                "fortune": can_access_feature(user_id, "fortune"),
                "horoscope": can_access_feature(user_id, "horoscope"),
                "creative_writer": can_access_feature(user_id, "creative_writer"),
                "ai_images": can_access_feature(user_id, "ai_images"),
                "voice_journaling": can_access_feature(user_id, "voice_journaling"),
                "music_studio": can_access_feature(user_id, "music_studio")
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting tier status: {e}")
        return {
            "user_plan": "bronze",
            "effective_plan": "bronze", 
            "trial_active": False,
            "limits": DAILY_LIMITS["bronze"],
            "usage": {"decoder": 0, "fortune": 0, "horoscope": 0},
            "credits": 0,
            "feature_access": {}
        }