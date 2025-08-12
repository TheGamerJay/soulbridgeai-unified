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

def check_active_subscription(user_id, plan):
    """
    Check if user has an active subscription for the given plan
    Returns True if user has active subscription, False if cancelled/expired
    """
    try:
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
            status, plan_type = result
            # Active subscription means status is 'active' and plan matches
            is_active = (status == 'active' and plan_type == plan)
            logger.info(f"🔍 SUBSCRIPTION CHECK: User {user_id} plan {plan} - Status: {status}, Active: {is_active}")
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
    "free":    {"decoder": 3,  "fortune": 2,  "horoscope": 3, "creative_writer": 2},
    "growth":  {"decoder": 15, "fortune": 8,  "horoscope": 10, "creative_writer": 20},
    "max":     {"decoder": 999999, "fortune": 999999, "horoscope": 999999, "creative_writer": 999999}
}

# MONTHLY CREDITS (premium features)
MONTHLY_CREDITS = {
    "free":   0,
    "growth": 100,    # 100 credits/month for Growth
    "max":    500     # 500 credits/month for Max
}

# FEATURES THAT REQUIRE CREDITS
CREDIT_FEATURES = ["ai_images", "voice_journaling", "music_studio", "relationship_profiles", "meditations"]

# EFFECTIVE PLAN (trial never changes what tier you are)
def get_effective_plan(user_plan: str, trial_active: bool) -> str:
    """
    5hr trial unlocks max tier features but keeps actual plan limits
    - For feature access: trial gives max tier access
    - For usage limits: always use actual plan (handled separately)
    """
    if trial_active and user_plan == "free":
        return "max"  # Unlock all features during trial
    return user_plan  # Non-trial or already premium users

# GET DAILY LIMITS (always based on actual plan, not trial)
def get_feature_limit(user_plan: str, feature: str, trial_active: bool = False) -> int:
    """
    Daily limits are always based on your actual subscription plan
    Trial does NOT increase daily limits - only unlocks features
    """
    plan = user_plan  # Always use actual plan for limits, never "max" during trial
    return DAILY_LIMITS.get(plan, {}).get(feature, 0)

# GET TRIAL TRAINER TIME (60 credits for free users during 5hr trial)
def get_trial_trainer_time(user_id):
    """
    Get trainer time credits for free users during 5hr trial
    Returns 60 credits for Mini Studio access during trial period
    """
    try:
        trial_active = session.get("trial_active", False)
        plan = session.get("user_plan", "free")
        
        if plan == "free" and trial_active:
            # Free users get 60 trainer time during trial
            return 60
        else:
            # Not applicable for other cases
            return 0
            
    except Exception as e:
        logger.error(f"Error getting trial trainer time: {e}")
        return 0

# GET CREDITS FOR USER (resets monthly with NO ROLLOVER, based on actual plan)
def get_user_credits(user_id):
    """
    Get user's available credits, auto-reset monthly based on actual plan
    IMPORTANT: Credits DO NOT roll over - any unused credits are lost at reset
    Trial users keep their plan's credit allocation
    """
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return 0
            
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
        plan = plan_type or session.get("user_plan", "free")
        purchased_credits = purchased_credits or 0

        now = datetime.utcnow()

        # Reset if 1 month has passed - ONLY FOR ACTIVE SUBSCRIBERS
        if not last_reset or (now - last_reset).days >= 30:
            # Check if user has active subscription before resetting
            subscription_active = check_active_subscription(user_id, plan)
            
            if subscription_active and plan in ['growth', 'max']:
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
    Deduct credits for premium feature usage
    Prioritizes purchased credits first, then plan credits
    Returns True if successful, False if insufficient credits
    """
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return False
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute("SELECT credits, purchased_credits FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        
        if not row:
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
            
            conn.commit()
            conn.close()
            return True

        conn.close()
        logger.warning(f"💳 INSUFFICIENT CREDITS: User {user_id} has {total_credits} total, needs {amount}")
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

        # Daily limit features (decoder, fortune, horoscope, creative_writer)
        if feature in ["decoder", "fortune", "horoscope", "creative_writer"]:
            if feature == "decoder":
                # Decoder available to all tiers
                limit = get_feature_limit(plan, feature, trial_active)
                return limit > 0
            elif feature in ["fortune", "horoscope"]:
                # Fortune/Horoscope: Trial removes the lock for free users
                if plan == "free" and trial_active:
                    # Free user on trial can use these features (lock removed)
                    limit = get_feature_limit(plan, feature, trial_active)
                    return limit > 0
                elif plan in ["growth", "max"]:
                    # Growth/Max users always have access
                    limit = get_feature_limit(plan, feature, trial_active)
                    return limit > 0
                else:
                    # Free user without trial - locked
                    return False
            elif feature == "creative_writer":
                # Creative writer available to all tiers (with different limits)
                limit = get_feature_limit(plan, feature, trial_active)
                return limit > 0

        # Credit-based features (AI images, voice journaling, etc.)
        if feature in CREDIT_FEATURES:
            # Trial removes the lock for free users
            if plan == "free" and trial_active:
                # Free user on trial can use these features (but with 0 credits)
                credits = get_user_credits(user_id)
                return credits >= 0  # Allow access even with 0 credits during trial
            elif plan in ["growth", "max"]:
                # Growth/Max users always have access
                credits = get_user_credits(user_id)
                return credits > 0
            else:
                # Free user without trial - locked
                return False
        
        # Mini Studio (max tier exclusive with trainer time)
        if feature == "mini_studio":
            if plan == "max":
                # Max users have full access with their trainer time
                return True
            elif plan == "free" and trial_active:
                # Free users on trial get 60 trainer time to taste Mini Studio
                return True  # Access granted, will handle trainer time separately
            else:
                # Growth users and free users without trial - no access
                return False

        # All other features: Trial removes locks for free users
        if plan == "free" and trial_active:
            return True  # Trial removes all locks
        return plan in ["growth", "max"]
        
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
        
        # Get current usage from session for creative_writer (matches app.py implementation)
        decoder_usage = get_feature_usage_today(user_id, "decoder")
        fortune_usage = get_feature_usage_today(user_id, "fortune") 
        horoscope_usage = get_feature_usage_today(user_id, "horoscope")
        
        # Creative writer uses session-based tracking like in app.py
        today_str = datetime.now().strftime("%Y-%m-%d")
        creative_usage_key = f'creative_usage_{user_id}_{today_str}'
        creative_usage = session.get(creative_usage_key, 0)
        
        # Get limits (always based on actual plan)
        decoder_limit = get_feature_limit(plan, "decoder")
        fortune_limit = get_feature_limit(plan, "fortune")
        horoscope_limit = get_feature_limit(plan, "horoscope")
        creative_limit = get_feature_limit(plan, "creative_writer")
        
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
            "user_plan": "free",
            "effective_plan": "free", 
            "trial_active": False,
            "limits": DAILY_LIMITS["free"],
            "usage": {"decoder": 0, "fortune": 0, "horoscope": 0},
            "credits": 0,
            "feature_access": {}
        }