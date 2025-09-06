# =========================
# SoulBridge AI — Updated Tier System V2 Architecture Reference
# Clean, Modern Implementation with Current Business Logic (2025)
# Bronze (Ad-supported) / Silver (Subscription) / Gold (Premium Subscription)
# =========================

# -------------------------
# models.py
# -------------------------
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, UniqueConstraint
from sqlalchemy.sql import func
# assume `db` is your SQLAlchemy instance

class Tier(str, Enum):
    BRONZE = "bronze"  # Ad-supported, daily limits
    SILVER = "silver"  # $12.99/month, enhanced limits + credits
    GOLD   = "gold"    # $19.99/month, unlimited + exclusive features

class Feature(str, Enum):
    DECODER         = "decoder"
    FORTUNE         = "fortune"
    HOROSCOPE       = "horoscope"
    CREATIVE_WRITER = "creative_writer"
    SOUL_RIDDLE     = "soul_riddle"
    CHAT            = "chat"
    VOICE_CHAT      = "voice_chat"
    AI_IMAGES       = "ai_images"
    VOICE_JOURNALING = "voice_journaling"
    MEDITATIONS     = "meditations"
    RELATIONSHIPS   = "relationships"
    MINI_STUDIO     = "mini_studio"  # Gold exclusive
    ANALYTICS       = "analytics"

class Usage(db.Model):
    __tablename__ = 'feature_usage'
    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, index=True, nullable=False)
    tier       = Column(String,  index=True, nullable=False)   # bronze|silver|gold
    feature    = Column(String,  index=True, nullable=False)   # decoder|fortune|...
    usage_date = Column(DateTime(timezone=True), server_default=func.current_date(), nullable=False)
    usage_count = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('user_id', 'tier', 'feature', 'usage_date', name='uq_usage_user_tier_feature_date'),)

class ArtisticTimeCredits(db.Model):
    __tablename__ = 'artistic_time_credits'
    id              = Column(Integer, primary_key=True)
    user_id         = Column(Integer, index=True, nullable=False, unique=True)
    monthly_credits = Column(Integer, default=0, nullable=False)  # Silver: 200, Gold: 500
    purchased_credits = Column(Integer, default=0, nullable=False)  # Extra purchased credits
    used_credits    = Column(Integer, default=0, nullable=False)
    last_reset      = Column(DateTime(timezone=True), server_default=func.now())
    billing_cycle   = Column(String, default='monthly')  # monthly|yearly

class TrialState(db.Model):
    __tablename__ = 'trial_state'
    id                    = Column(Integer, primary_key=True)
    user_id               = Column(Integer, index=True, nullable=False, unique=True)
    trial_active          = Column(Boolean, default=False, nullable=False)
    trial_started_at      = Column(DateTime(timezone=True))
    trial_expires_at      = Column(DateTime(timezone=True))
    trial_credits_granted = Column(Integer, default=60)  # 60 artistic time for trial
    trial_credits_used    = Column(Integer, default=0)
    trial_used_permanently = Column(Boolean, default=False)  # One-time trial flag

# -------------------------
# app_config.py (Updated with Current SoulBridge AI Logic)
# -------------------------

# Updated limits matching current SoulBridge AI system
TIER_LIMITS = {
    'bronze': {
        'decoder': 5, 'fortune': 5, 'horoscope': 5, 'creative_writer': 5, 'soul_riddle': 3,
        'chat': None,  # Unlimited chat with ads
        'voice_chat': 0, 'ai_images': 0, 'voice_journaling': 0, 'meditations': 0, 
        'relationships': 0, 'mini_studio': 0, 'analytics': 0
    },
    'silver': {
        'decoder': 15, 'fortune': 8, 'horoscope': 10, 'creative_writer': 20, 'soul_riddle': 20,
        'chat': None, 'voice_chat': None, 'ai_images': None, 'voice_journaling': None,
        'meditations': None, 'relationships': None, 'analytics': None,
        'mini_studio': 0,  # Gold exclusive
        'monthly_artistic_time': 200
    },
    'gold': {
        'decoder': 999, 'fortune': 999, 'horoscope': 999, 'creative_writer': 999, 'soul_riddle': 999,
        'chat': None, 'voice_chat': None, 'ai_images': None, 'voice_journaling': None,
        'meditations': None, 'relationships': None, 'analytics': None, 'mini_studio': None,
        'monthly_artistic_time': 500
    }
}

# Current companion system with tier-based access
COMPANIONS_BY_TIER = {
    'bronze': [
        "gamerjay_free", "blayzo", "claude_free", "violet_free", "crimson_free",
        "blayzia", "blayzike", "blayzion", "blazelian", "bronze_creative_writing"
    ],
    'silver': [
        "claude_silver", "lumen_silver", "rozia_silver", "sky_premium", 
        "violet_silver", "watchdog_premium", "silver_creative_writing"
    ],
    'gold': [
        "claude_gold", "blayzo_gold", "violet_gold", "crimson_max", "royal_max",
        "ven_blayzica_max", "ven_sky_max", "watchdog_max", "gold_creative_writing"
    ],
    'referral': [
        "blayzo_referral", "claude_referral"  # Unlocked via referral system
    ]
}

# Credit-based features (require artistic time)
CREDIT_FEATURES = {
    'ai_images': {'bronze': 1, 'silver': 1, 'gold': 1},  # Cost per use
    'voice_journaling': {'bronze': 2, 'silver': 1, 'gold': 1},
    'mini_studio': {'bronze': 5, 'silver': 3, 'gold': 2},  # Gold exclusive access
}

# Ad configuration
AD_CONFIG = {
    'bronze': {
        'show_ads': True,
        'ad_frequency': 'every_feature_use',  # Show ad before each feature
        'ad_types': ['banner', 'interstitial']
    },
    'silver': {'show_ads': False},
    'gold': {'show_ads': False}
}

# Plan pricing (current)
PLAN_PRICING = {
    'silver': {'monthly': 12.99, 'yearly': 117.00},  # 25% savings
    'gold': {'monthly': 19.99, 'yearly': 180.00}     # 25% savings
}

# -------------------------
# tier_helpers.py (Updated Business Logic)
# -------------------------
from datetime import datetime, timezone, timedelta
from flask_login import current_user
from models import TrialState, ArtisticTimeCredits
from app_config import TIER_LIMITS, COMPANIONS_BY_TIER, AD_CONFIG, CREDIT_FEATURES

def get_user_plan(user) -> str:
    """Get user's actual subscription plan"""
    return getattr(user, "user_plan", "bronze") or "bronze"

def get_effective_tier(user) -> str:
    """Return actual tier - Bronze/Silver/Gold ONLY. Trial never changes this."""
    return get_user_plan(user).lower()

def get_trial_state(user) -> dict:
    """Get comprehensive trial state"""
    ts = TrialState.query.filter_by(user_id=user.id).first()
    if not ts:
        # Check if user is eligible (Bronze only, hasn't used trial)
        user_plan = get_user_plan(user)
        if user_plan == 'bronze':
            return {"active": False, "eligible": True, "credits_remaining": 0}
        else:
            return {"active": False, "eligible": False, "credits_remaining": 0}
    
    now = datetime.now(timezone.utc)
    active = bool(
        ts.trial_active and 
        ts.trial_expires_at and 
        ts.trial_expires_at > now and
        not ts.trial_used_permanently
    )
    
    credits_remaining = max(0, ts.trial_credits_granted - ts.trial_credits_used) if active else 0
    
    return {
        "active": active,
        "eligible": not ts.trial_used_permanently and get_user_plan(user) == 'bronze',
        "expires_at": ts.trial_expires_at.isoformat() if ts.trial_expires_at else None,
        "credits_remaining": credits_remaining,
        "time_remaining_hours": max(0, (ts.trial_expires_at - now).total_seconds() / 3600) if active else 0
    }

def get_artistic_time_balance(user) -> dict:
    """Get artistic time credit balance for Silver/Gold users"""
    user_plan = get_user_plan(user)
    if user_plan == 'bronze':
        trial = get_trial_state(user)
        return {"balance": trial.get("credits_remaining", 0), "type": "trial"}
    
    credits = ArtisticTimeCredits.query.filter_by(user_id=user.id).first()
    if not credits:
        return {"balance": 0, "type": "subscription"}
    
    # Check if monthly reset needed
    now = datetime.now(timezone.utc)
    if credits.last_reset.month != now.month or credits.last_reset.year != now.year:
        # Reset monthly credits
        monthly_amount = TIER_LIMITS[user_plan].get('monthly_artistic_time', 0)
        credits.monthly_credits = monthly_amount
        credits.used_credits = 0
        credits.last_reset = now
        db.session.commit()
    
    total_available = credits.monthly_credits + credits.purchased_credits - credits.used_credits
    return {"balance": max(0, total_available), "type": "subscription"}

def can_access_feature(user, feature: str) -> dict:
    """Check if user can access a feature based on tier + trial"""
    tier = get_effective_tier(user)
    trial = get_trial_state(user)
    limits = TIER_LIMITS[tier]
    
    # Check if feature exists for this tier
    if feature not in limits:
        return {"access": False, "reason": "feature_not_found"}
    
    feature_limit = limits[feature]
    
    # If feature is blocked for this tier (0 limit)
    if feature_limit == 0:
        # Trial can unlock Silver/Gold features for Bronze users
        if tier == 'bronze' and trial.get("active"):
            # Check if feature is available in Silver or Gold
            silver_limit = TIER_LIMITS['silver'].get(feature, 0)
            gold_limit = TIER_LIMITS['gold'].get(feature, 0)
            if silver_limit > 0 or gold_limit is None:
                return {"access": True, "reason": "trial_unlock", "requires_credits": feature in CREDIT_FEATURES}
        
        return {"access": False, "reason": "tier_restricted", "upgrade_to": "silver" if tier == "bronze" else "gold"}
    
    # Feature is available for this tier
    if feature_limit is None:  # Unlimited
        return {"access": True, "reason": "unlimited"}
    
    # Check daily usage limits
    from usage_service import get_daily_usage
    used_today = get_daily_usage(user.id, tier, feature)
    remaining = max(0, feature_limit - used_today)
    
    return {
        "access": remaining > 0,
        "reason": "daily_limit" if remaining == 0 else "within_limit",
        "remaining": remaining,
        "limit": feature_limit,
        "used": used_today
    }

def visible_companions_for(user) -> set:
    """Get all companions user can see (tier + trial + referral)"""
    tier = get_effective_tier(user)
    visible = set(COMPANIONS_BY_TIER[tier])
    
    # Trial unlocks companion visibility only
    trial = get_trial_state(user)
    if trial.get("active"):
        visible |= set(COMPANIONS_BY_TIER['silver'])
        visible |= set(COMPANIONS_BY_TIER['gold'])
    
    # Add referral companions if user has referrals
    # (Add your referral logic here)
    
    return visible

def should_show_ads(user) -> bool:
    """Determine if ads should be shown to user"""
    tier = get_effective_tier(user)
    return AD_CONFIG[tier].get('show_ads', False)

# -------------------------
# usage_service.py (Updated with Daily Usage Tracking)
# -------------------------
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from models import Usage, ArtisticTimeCredits, TrialState, db
from datetime import date

def get_daily_usage(user_id: int, tier: str, feature: str, usage_date: date = None) -> int:
    """Get usage count for specific date (defaults to today)"""
    if usage_date is None:
        usage_date = date.today()
    
    row = Usage.query.filter_by(
        user_id=user_id, 
        tier=tier, 
        feature=feature,
        usage_date=usage_date
    ).first()
    
    return row.usage_count if row else 0

def increment_daily_usage(user_id: int, tier: str, feature: str, delta: int = 1) -> int:
    """Thread-safe daily usage increment"""
    today = date.today()
    
    # Use pessimistic locking to avoid race conditions
    row = Usage.query.filter_by(
        user_id=user_id, 
        tier=tier, 
        feature=feature,
        usage_date=today
    ).with_for_update().first()
    
    if not row:
        row = Usage(user_id=user_id, tier=tier, feature=feature, usage_date=today, usage_count=0)
        db.session.add(row)
        try:
            db.session.flush()
        except IntegrityError:
            db.session.rollback()
            row = Usage.query.filter_by(
                user_id=user_id, tier=tier, feature=feature, usage_date=today
            ).with_for_update().first()
    
    row.usage_count += delta
    db.session.commit()
    return row.usage_count

def consume_artistic_time(user_id: int, amount: int) -> bool:
    """Consume artistic time credits (trial or subscription)"""
    from tier_helpers import get_user_plan, get_trial_state
    
    user_plan = get_user_plan(user_id)  # Need to get user object or pass plan
    
    if user_plan == 'bronze':
        # Use trial credits
        trial = TrialState.query.filter_by(user_id=user_id).first()
        if not trial or not trial.trial_active:
            return False
        
        available = trial.trial_credits_granted - trial.trial_credits_used
        if available < amount:
            return False
        
        trial.trial_credits_used += amount
        db.session.commit()
        return True
    
    else:
        # Use subscription credits
        credits = ArtisticTimeCredits.query.filter_by(user_id=user_id).first()
        if not credits:
            return False
        
        available = credits.monthly_credits + credits.purchased_credits - credits.used_credits
        if available < amount:
            return False
        
        credits.used_credits += amount
        db.session.commit()
        return True

def check_feature_access(user_id: int, tier: str, feature: str) -> dict:
    """Comprehensive feature access check"""
    from tier_helpers import can_access_feature
    # This would need user object - simplified for reference
    pass

# -------------------------
# app.py (Updated API Endpoints)
# -------------------------
from flask import jsonify, request
from flask_login import login_required, current_user
from tier_helpers import (
    get_effective_tier, get_trial_state, get_artistic_time_balance,
    can_access_feature, visible_companions_for, should_show_ads
)
from usage_service import increment_daily_usage, consume_artistic_time

@app.route('/api/user/status', methods=['GET'])
@login_required
def api_user_status():
    """Comprehensive user status endpoint"""
    user = current_user
    tier = get_effective_tier(user)
    trial = get_trial_state(user)
    credits = get_artistic_time_balance(user)
    
    # Get daily usage for all features
    usage_today = {}
    for feature in TIER_LIMITS[tier].keys():
        if TIER_LIMITS[tier][feature] is not None:  # Skip unlimited features
            usage_today[feature] = get_daily_usage(user.id, tier, feature)
    
    return jsonify({
        "ok": True,
        "user_id": user.id,
        "tier": tier,
        "trial": trial,
        "credits": credits,
        "usage_today": usage_today,
        "show_ads": should_show_ads(user),
        "limits": TIER_LIMITS[tier]
    })

@app.route('/api/companions', methods=['GET'])
@login_required
def api_companions():
    """Get visible companions with access control"""
    user = current_user
    tier = get_effective_tier(user)
    trial = get_trial_state(user)
    visible_ids = visible_companions_for(user)
    
    # Build companion list with metadata
    companions = []
    for comp_id in visible_ids:
        # Get companion data from your registry
        comp_data = get_companion_data(comp_id)  # Your existing function
        companions.append({
            **comp_data,
            "can_access": True,
            "tier_required": get_companion_tier(comp_id),
            "is_current": comp_id == user.selected_companion
        })
    
    return jsonify({
        "ok": True,
        "tier": tier,
        "trial_active": trial.get("active", False),
        "companions": companions
    })

@app.route('/api/<feature>/use', methods=['POST'])
@login_required
def api_use_feature(feature):
    """Generic feature usage endpoint with tier checking"""
    user = current_user
    tier = get_effective_tier(user)
    
    # Check if user can access this feature
    access = can_access_feature(user, feature)
    if not access["access"]:
        return jsonify({
            "ok": False, 
            "error": access["reason"],
            "tier": tier,
            **access
        }), 403
    
    # Check if feature requires credits
    if feature in CREDIT_FEATURES:
        cost = CREDIT_FEATURES[feature].get(tier, 0)
        if cost > 0:
            credits = get_artistic_time_balance(user)
            if credits["balance"] < cost:
                return jsonify({
                    "ok": False,
                    "error": "insufficient_credits",
                    "required": cost,
                    "available": credits["balance"]
                }), 402
            
            # Consume credits
            if not consume_artistic_time(user.id, cost):
                return jsonify({"ok": False, "error": "credit_consumption_failed"}), 500
    
    # For daily-limited features, increment usage
    if TIER_LIMITS[tier].get(feature) is not None:
        new_usage = increment_daily_usage(user.id, tier, feature)
        
        # Check if we've hit the limit
        limit = TIER_LIMITS[tier][feature]
        if new_usage > limit:
            return jsonify({
                "ok": False,
                "error": "daily_limit_exceeded",
                "limit": limit,
                "used": new_usage
            }), 429
    
    # Perform the actual feature work here
    # ... feature-specific logic ...
    
    return jsonify({
        "ok": True,
        "tier": tier,
        "usage_remaining": access.get("remaining", None),
        "show_ad": should_show_ads(user)
    })

# -------------------------
# React Frontend Integration (Updated)
# -------------------------
"""
// src/hooks/useSoulBridge.js
import React from 'react'

export function useSoulBridge() {
  const [status, setStatus] = React.useState(null)
  const [loading, setLoading] = React.useState(true)

  React.useEffect(() => {
    fetch('/api/user/status')
      .then(r => r.json())
      .then(data => {
        if (data.ok) setStatus(data)
        setLoading(false)
      })
  }, [])

  const useFeature = async (feature) => {
    const response = await fetch(`/api/${feature}/use`, { method: 'POST' })
    const data = await response.json()
    
    if (data.show_ad) {
      // Show ad before feature use
      await showAd()
    }
    
    // Refresh status after use
    if (data.ok) {
      const statusResponse = await fetch('/api/user/status')
      const statusData = await statusResponse.json()
      if (statusData.ok) setStatus(statusData)
    }
    
    return data
  }

  return { status, loading, useFeature }
}
"""

# -------------------------
# Database Migration SQL
# -------------------------
"""
-- Create updated tables
CREATE TABLE IF NOT EXISTS feature_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    tier VARCHAR(20) NOT NULL,
    feature VARCHAR(50) NOT NULL,
    usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
    usage_count INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, tier, feature, usage_date)
);

CREATE TABLE IF NOT EXISTS artistic_time_credits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    monthly_credits INTEGER DEFAULT 0,
    purchased_credits INTEGER DEFAULT 0,
    used_credits INTEGER DEFAULT 0,
    last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    billing_cycle VARCHAR(20) DEFAULT 'monthly'
);

CREATE TABLE IF NOT EXISTS trial_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    trial_active BOOLEAN DEFAULT FALSE,
    trial_started_at TIMESTAMP,
    trial_expires_at TIMESTAMP,
    trial_credits_granted INTEGER DEFAULT 60,
    trial_credits_used INTEGER DEFAULT 0,
    trial_used_permanently BOOLEAN DEFAULT FALSE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_feature_usage_user_date ON feature_usage(user_id, usage_date);
CREATE INDEX IF NOT EXISTS idx_feature_usage_tier_feature ON feature_usage(tier, feature);
CREATE INDEX IF NOT EXISTS idx_artistic_time_user ON artistic_time_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_trial_state_user ON trial_state(user_id);
"""

# =========================
# This updated architecture provides:
# 1. Clean tier isolation (Bronze/Silver/Gold)
# 2. Proper trial system (5-hour + 60 credits for Bronze users)
# 3. Artistic time credit system for Silver/Gold
# 4. Ad-supported Bronze tier
# 5. Thread-safe daily usage tracking
# 6. Credit-based premium features
# 7. Comprehensive companion access control
# 8. Modern SQLAlchemy patterns
# 9. Current SoulBridge AI business logic (2025)
# 10. Race-condition safe operations
# =========================