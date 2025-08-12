#!/usr/bin/env python3
"""
============================================
📦 Unified Tier + Trial + Credits System
============================================
Single clean block that merges credits + daily limits with correct Free/Growth/Max isolation and trial behavior.

This fixes:
- Growth showing Free limits
- Max showing wrong features  
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

# DAILY LIMITS (non-credit features)
DAILY_LIMITS = {
    "free":    {"decoder": 3,  "fortune": 2,  "horoscope": 3},
    "growth":  {"decoder": 15, "fortune": 8,  "horoscope": 10},
    "max":     {"decoder": 999999, "fortune": 999999, "horoscope": 999999}
}

# MONTHLY CREDITS (premium features)
MONTHLY_CREDITS = {
    "free":   0,
    "growth": 100,    # 100 credits/month for Growth
    "max":    500     # 500 credits/month for Max
}

# FEATURES THAT REQUIRE CREDITS
CREDIT_FEATURES = ["ai_images", "voice_journaling", "music_studio", "relationship_profiles", "meditations"]

# EFFECTIVE PLAN (trial unlocks features, keeps limits/credits of actual plan)
def get_effective_plan(user_plan: str, trial_active: bool) -> str:
    """
    Trial unlocks Max FEATURES but keeps your plan's LIMITS and CREDITS
    This prevents trial abuse while giving full feature access
    """
    return "max" if trial_active else user_plan

# GET DAILY LIMITS (always based on actual plan, not trial)
def get_feature_limit(user_plan: str, feature: str, trial_active: bool = False) -> int:
    """
    Daily limits are always based on your actual subscription plan
    Trial does NOT increase daily limits - only unlocks features
    """
    plan = user_plan  # Always use actual plan for limits, never "max" during trial
    return DAILY_LIMITS.get(plan, {}).get(feature, 0)

# GET CREDITS FOR USER (resets monthly, based on actual plan)
def get_user_credits(user_id):
    """
    Get user's available credits, auto-reset monthly based on actual plan
    Trial users keep their plan's credit allocation
    """
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return 0
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute("""
            SELECT credits, last_credit_reset, plan_type FROM users WHERE id = %s
        """, (user_id,))
        row = cur.fetchone()
        
        if not row:
            conn.close()
            return 0
            
        credits, last_reset, plan_type = row
        plan = plan_type or session.get("user_plan", "free")

        now = datetime.utcnow()

        # Reset if 1 month has passed
        if not last_reset or (now - last_reset).days >= 30:
            credits = MONTHLY_CREDITS.get(plan, 0)
            cur.execute("""
                UPDATE users
                SET credits = %s, last_credit_reset = %s
                WHERE id = %s
            """, (credits, now, user_id))
            conn.commit()
            logger.info(f"💳 CREDITS RESET: User {user_id} ({plan}) reset to {credits} credits")

        conn.close()
        return credits or 0
        
    except Exception as e:
        logger.error(f"Error getting user credits: {e}")
        return 0

# DEDUCT CREDITS WHEN USING PREMIUM FEATURE
def deduct_credits(user_id, amount):
    """
    Deduct credits for premium feature usage
    Returns True if successful, False if insufficient credits
    """
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return False
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute("SELECT credits FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        
        if not row:
            conn.close()
            return False

        credits = row[0] or 0
        if credits >= amount:
            new_credits = credits - amount
            cur.execute("UPDATE users SET credits = %s WHERE id = %s", (new_credits, user_id))
            conn.commit()
            conn.close()
            logger.info(f"💳 CREDITS DEDUCTED: User {user_id} spent {amount} credits, {new_credits} remaining")
            return True

        conn.close()
        logger.warning(f"💳 INSUFFICIENT CREDITS: User {user_id} has {credits}, needs {amount}")
        return False
        
    except Exception as e:
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
        plan = session.get("user_plan", "free")
        effective_plan = get_effective_plan(plan, trial_active)

        # Daily limit features (decoder, fortune, horoscope)
        if feature in ["decoder", "fortune", "horoscope"]:
            # Feature access based on effective plan (trial unlocks)
            if effective_plan not in ["growth", "max"] and feature != "decoder":
                if feature == "fortune" and effective_plan == "free":
                    return False
                if feature == "horoscope" and effective_plan == "free":
                    return False
            
            # Limit based on actual plan (trial doesn't increase limits)
            limit = get_feature_limit(plan, feature, trial_active)
            return limit > 0

        # Credit-based features (AI images, voice journaling, etc.)
        if feature in CREDIT_FEATURES:
            # Feature access based on effective plan (trial unlocks)
            if effective_plan not in ["growth", "max"]:
                return False
                
            # Credit availability based on actual plan
            credits = get_user_credits(user_id)
            return credits > 0

        # All other features default to plan-based access
        return effective_plan in ["growth", "max"]
        
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
        
        today = datetime.utcnow().date()
        cur.execute("""
            SELECT COUNT(*) FROM feature_usage 
            WHERE user_id = %s AND feature = %s AND DATE(created_at) = %s
        """, (user_id, feature, today))
        
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
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return False
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Create feature_usage table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feature_usage (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                feature VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert usage record
        cur.execute("""
            INSERT INTO feature_usage (user_id, feature)
            VALUES (%s, %s)
        """, (user_id, feature))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error incrementing feature usage: {e}")
        return False

# UNIFIED TIER STATUS FOR API RESPONSES
def get_tier_status(user_id):
    """
    Get complete tier status including limits, credits, and feature access
    """
    try:
        trial_active = session.get("trial_active", False)
        plan = session.get("user_plan", "free")
        effective_plan = get_effective_plan(plan, trial_active)
        
        # DEBUG: Log what we got from session
        logger.info(f"🔍 UNIFIED DEBUG: user_id={user_id}, plan='{plan}', trial={trial_active}, effective='{effective_plan}'")
        
        # Get current usage
        decoder_usage = get_feature_usage_today(user_id, "decoder")
        fortune_usage = get_feature_usage_today(user_id, "fortune") 
        horoscope_usage = get_feature_usage_today(user_id, "horoscope")
        
        # Get limits (always based on actual plan)
        decoder_limit = get_feature_limit(plan, "decoder")
        fortune_limit = get_feature_limit(plan, "fortune")
        horoscope_limit = get_feature_limit(plan, "horoscope")
        
        # Get credits
        credits = get_user_credits(user_id)
        
        return {
            "user_plan": plan,
            "effective_plan": effective_plan,
            "trial_active": trial_active,
            "limits": {
                "decoder": decoder_limit,
                "fortune": fortune_limit,
                "horoscope": horoscope_limit
            },
            "usage": {
                "decoder": decoder_usage,
                "fortune": fortune_usage,
                "horoscope": horoscope_usage
            },
            "credits": credits,
            "feature_access": {
                "decoder": can_access_feature(user_id, "decoder"),
                "fortune": can_access_feature(user_id, "fortune"),
                "horoscope": can_access_feature(user_id, "horoscope"),
                "ai_images": can_access_feature(user_id, "ai_images"),
                "voice_journaling": can_access_feature(user_id, "voice_journaling"),
                "music_studio": can_access_feature(user_id, "music_studio")
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting tier status: {e}")
        return {
            "user_plan": "free",
            "effective_plan": "free", 
            "trial_active": False,
            "limits": DAILY_LIMITS["free"],
            "usage": {"decoder": 0, "fortune": 0, "horoscope": 0},
            "credits": 0,
            "feature_access": {}
        }