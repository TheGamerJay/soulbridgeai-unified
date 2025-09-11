"""
SoulBridge AI - Unified Tier System (Compatibility Layer)
Temporary compatibility module for the Soul Companions system transition
Provides backward compatibility for old imports while the system is being updated

IMPORTANT: This is a compatibility layer. New code should use the modular system:
- modules.credits.operations for credit operations
- modules.auth.access_control for access control
- modules.creative.features_config for feature limits
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ================================================================================
# SCHEMA INITIALIZATION (Addressing the DATABASE_URL schema issue)
# ================================================================================

# Check for Railway PostgreSQL connection
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    logger.info("📊 SCHEMA: Connected to Railway PostgreSQL")
    try:
        # Initialize database schema if needed
        from modules.shared.database import get_database
        db = get_database()
        if db:
            logger.info("📊 SCHEMA: Database connection verified")
        else:
            logger.warning("📊 SCHEMA: Database connection failed")
    except Exception as e:
        logger.error(f"📊 SCHEMA: Database initialization error: {e}")
else:
    logger.info("📊 SCHEMA: Using local SQLite database")

# ================================================================================
# COMPATIBILITY FUNCTIONS
# ================================================================================

def get_effective_plan(user_plan: str, trial_active: bool = False) -> str:
    """
    Get the effective plan for companion access
    During trial, Bronze users get Gold access for companions only
    """
    if user_plan == 'bronze' and trial_active:
        return 'gold'  # Trial gives Gold companion access
    return user_plan

def get_feature_limit(user_plan: str, feature: str) -> int:
    """Get feature usage limit for a plan"""
    try:
        from modules.creative.features_config import CREATIVE_LIMITS
        
        limits = {
            'decoder': CREATIVE_LIMITS.get('decoder', {}),
            'fortune': CREATIVE_LIMITS.get('fortune', {}),
            'horoscope': CREATIVE_LIMITS.get('horoscope', {}),
            'creative_writer': CREATIVE_LIMITS.get('creative_writing', {}),
            'creative_writing': CREATIVE_LIMITS.get('creative_writing', {}),
        }
        
        feature_limits = limits.get(feature, {})
        return feature_limits.get(user_plan, 5)  # Default to 5 for Bronze
        
    except ImportError:
        # Fallback limits if creative config not available
        fallback_limits = {
            'bronze': 5,
            'silver': 15,
            'gold': 100
        }
        return fallback_limits.get(user_plan, 5)

def get_feature_usage_today(user_id: int, feature: str) -> int:
    """Get today's feature usage count"""
    try:
        from modules.creative.usage_tracker import get_daily_usage
        return get_daily_usage(user_id, feature)
    except ImportError:
        # Fallback - check database directly
        try:
            from modules.shared.database import get_database
            db = get_database()
            if db:
                conn = db.get_connection()
                cursor = conn.cursor()
                
                # Check usage for today
                today = datetime.now().strftime('%Y-%m-%d')
                if db.use_postgres:
                    cursor.execute("SELECT COUNT(*) FROM feature_usage WHERE user_id = %s AND feature = %s AND DATE(created_at) = %s", (user_id, feature, today))
                else:
                    cursor.execute("SELECT COUNT(*) FROM feature_usage WHERE user_id = ? AND feature = ? AND DATE(created_at) = ?", (user_id, feature, today))
                
                result = cursor.fetchone()
                conn.close()
                return result[0] if result else 0
        except Exception as e:
            logger.warning(f"Could not get feature usage: {e}")
            return 0
        
        return 0

def get_user_credits(user_id: int) -> int:
    """Get user's artistic time credits"""
    try:
        from modules.credits.operations import get_artistic_time
        return get_artistic_time(user_id)
    except ImportError:
        logger.warning("Credits operations not available, returning 0")
        return 0

def deduct_credits(user_id: int, amount: int) -> bool:
    """Deduct artistic time credits"""
    try:
        from modules.credits.operations import deduct_artistic_time
        return deduct_artistic_time(user_id, amount)
    except ImportError:
        logger.warning("Credits operations not available")
        return False

def add_credits(user_id: int, amount: int, reason: str = "refund") -> bool:
    """Add artistic time credits (refund)"""
    try:
        from modules.credits.operations import refund_artistic_time
        return refund_artistic_time(user_id, amount, reason)
    except ImportError:
        logger.warning("Credits operations not available")
        return False

def get_trial_trainer_time(user_id: int) -> int:
    """Get trial trainer time credits"""
    try:
        from modules.credits.constants import TRIAL_ARTISTIC_TIME
        return TRIAL_ARTISTIC_TIME
    except ImportError:
        logger.warning("Trial system not available, returning default 60")
        return 60

def can_access_feature(user_plan: str, feature: str, trial_active: bool = False) -> bool:
    """Check if user can access a specific feature"""
    effective_plan = get_effective_plan(user_plan, trial_active)
    
    # All users can access basic features
    basic_features = ['decoder', 'fortune', 'horoscope', 'creative_writing']
    if feature in basic_features:
        return True
    
    # Premium features require Silver or Gold
    premium_features = ['ai_images', 'voice_journaling', 'relationship_profiles', 'meditations']
    if feature in premium_features:
        return effective_plan in ['silver', 'gold']
    
    # Gold exclusive features
    gold_features = ['mini_studio', 'voice_chat']
    if feature in gold_features:
        return effective_plan == 'gold'
    
    # Default to allow access
    return True

def ensure_database_schema():
    """Ensure database schema is properly initialized"""
    try:
        from modules.shared.database import get_database
        db = get_database()
        if db:
            # Run Railway-specific schema fixes if in Railway environment
            if DATABASE_URL:
                logger.info("🔧 Running Railway schema fixes...")
                try:
                    from fix_railway_schema_issues import fix_railway_schema
                    fix_railway_schema()
                except Exception as schema_error:
                    logger.warning(f"Schema fix warning: {schema_error}")
            
            logger.info("✅ Database schema verified")
            return True
        else:
            logger.error("❌ Database connection failed")
            return False
    except Exception as e:
        logger.error(f"❌ Database schema error: {e}")
        return False

# ================================================================================
# COMPATIBILITY CONSTANTS
# ================================================================================

DAILY_LIMITS = {
    'bronze': {
        'decoder': 5,
        'fortune': 5,
        'horoscope': 5,
        'creative_writing': 5
    },
    'silver': {
        'decoder': 15,
        'fortune': 12,
        'horoscope': 10,
        'creative_writing': 15
    },
    'gold': {
        'decoder': 100,
        'fortune': 150,
        'horoscope': 50,
        'creative_writing': 75
    }
}

MONTHLY_CREDITS = {
    'bronze': 0,
    'silver': 200,
    'gold': 500
}

# Initialize database schema on import - TEMPORARILY DISABLED to fix Railway schema errors
# try:
#     ensure_database_schema()
# except Exception as e:
#     logger.warning(f"Schema initialization warning: {e}")
logger.info("🚨 Database schema auto-initialization DISABLED - use manual endpoints to fix schema")
logger.info("🔧 Railway deployment fix - schema initialization bypass active")

logger.info("🔄 Unified tier system compatibility layer loaded")