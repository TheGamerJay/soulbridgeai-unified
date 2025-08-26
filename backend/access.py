# access.py
# Trial-aware access control for Bronze/Silver/Gold tier system

from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Tier limits based on CLAUDE.md specification
TIER_LIMITS = {
    "bronze": {
        "decoder": 3,
        "fortune": 2,
        "horoscope": 3,
        "creative_writer": 3,
        "credits": 0,
        "premium_features": False,
        "mini_studio": False,
        "ads": True
    },
    "silver": {
        "decoder": 15,
        "fortune": 8,
        "horoscope": 10,
        "creative_writer": 15,
        "credits": 100,
        "premium_features": True,
        "mini_studio": False,
        "ads": False
    },
    "gold": {
        "decoder": float("inf"),
        "fortune": float("inf"),
        "horoscope": float("inf"),
        "creative_writer": float("inf"),
        "credits": 500,
        "premium_features": True,
        "mini_studio": True,
        "ads": False
    },
}

# Companion tier access mapping
COMPANION_TIERS = {
    "bronze": ["bronze"],
    "silver": ["bronze", "silver"],
    "gold": ["bronze", "silver", "gold"]
}

def is_trial_live(trial_active, trial_expires_at):
    """
    Check if 5-hour trial is currently active.
    Returns True if trial is active and not expired.
    """
    if not trial_active or not trial_expires_at:
        return False
    
    try:
        # trial_expires_at may be str or datetime from DB; normalize
        if isinstance(trial_expires_at, str):
            trial_expires_at = datetime.fromisoformat(trial_expires_at.replace("Z", "+00:00"))
        
        now = datetime.now(timezone.utc)
        is_live = trial_expires_at > now
        
        logger.info(f"Trial status check: active={trial_active}, expires={trial_expires_at}, now={now}, live={is_live}")
        return is_live
        
    except Exception as e:
        logger.warning(f"Trial status check failed: {e}")
        return False

def get_effective_access(plan: str, trial_active=False, trial_expires_at=None):
    """
    Get effective access permissions for a user.
    
    Key principles:
    1. Trial unlocks ACCESS to Silver/Gold tiers (can click/explore)
    2. Trial NEVER changes usage limits (always from real plan)
    3. Only Bronze users can activate trial
    4. Trial gives 60 trainer credits for premium features
    
    Args:
        plan: User's actual subscription plan (bronze/silver/gold)
        trial_active: Whether 5-hour trial is active
        trial_expires_at: When trial expires
    
    Returns:
        dict with access permissions and limits
    """
    # Normalize plan
    plan = (plan or "bronze").lower()
    if plan not in TIER_LIMITS:
        logger.warning(f"Unknown plan '{plan}', defaulting to bronze")
        plan = "bronze"
    
    # Check if trial is currently live
    trial_live = is_trial_live(trial_active, trial_expires_at)
    
    # Determine which tiers are unlocked (clickable in UI)
    if trial_live and plan == "bronze":
        # Bronze users with active trial can access all tiers
        unlocked_tiers = ["bronze", "silver", "gold"]
        trial_credits = 60  # Trial gives 60 trainer credits
    else:
        # Normal access based on subscription plan
        unlocked_tiers = COMPANION_TIERS.get(plan, ["bronze"])
        trial_credits = 0
    
    # Usage limits ALWAYS come from real plan (trial never upgrades limits)
    limits = TIER_LIMITS.get(plan, TIER_LIMITS["bronze"]).copy()
    
    # Add trial credits if applicable
    if trial_live and plan == "bronze":
        limits["trial_credits"] = trial_credits
    
    # Companion access
    accessible_companion_tiers = unlocked_tiers
    
    return {
        "plan": plan,
        "trial_live": trial_live,
        "unlocked_tiers": unlocked_tiers,
        "accessible_companion_tiers": accessible_companion_tiers,
        "limits": limits,
        "trial_credits": trial_credits
    }

def get_effective_plan(plan: str, trial_active=False, trial_expires_at=None):
    """
    Get effective plan for companion access (used by existing get_effective_plan function).
    During trial, Bronze users get "gold" access for companion selection.
    """
    plan = (plan or "bronze").lower()
    trial_live = is_trial_live(trial_active, trial_expires_at)
    
    if trial_live and plan == "bronze":
        return "gold"  # Trial unlocks Gold-level companion access
    
    return plan

def can_access_tier(user_plan: str, requested_tier: str, trial_active=False, trial_expires_at=None):
    """
    Check if user can access a specific tier.
    """
    access = get_effective_access(user_plan, trial_active, trial_expires_at)
    return requested_tier.lower() in access["unlocked_tiers"]

def get_feature_limit(user_plan: str, feature: str, trial_active=False, trial_expires_at=None):
    """
    Get usage limit for a specific feature.
    Always based on real plan, never trial.
    """
    # Normalize plan names (handle legacy/inconsistent naming)
    plan = (user_plan or "bronze").lower()
    plan_mapping = {
        'bronze': 'bronze',
        'silver': 'silver', 
        'gold': 'gold'
    }
    plan = plan_mapping.get(plan, plan)
    
    limits = TIER_LIMITS.get(plan, TIER_LIMITS["bronze"])
    return limits.get(feature, 0)

def has_premium_features(user_plan: str, trial_active=False, trial_expires_at=None):
    """
    Check if user has access to premium features (AI images, voice journaling, etc.)
    Trial users get access through trial credits.
    """
    plan = (user_plan or "bronze").lower()
    trial_live = is_trial_live(trial_active, trial_expires_at)
    
    # Silver/Gold plans have premium features
    if plan in ["silver", "gold"]:
        return True
    
    # Bronze users get premium features during trial (with trial credits)
    if trial_live and plan == "bronze":
        return True
    
    return False

def has_mini_studio_access(user_plan: str, trial_active=False, trial_expires_at=None):
    """
    Check if user has access to Mini Studio (Gold tier exclusive).
    Trial users get access during trial period.
    """
    plan = (user_plan or "bronze").lower()
    trial_live = is_trial_live(trial_active, trial_expires_at)
    
    # Gold plan has mini studio
    if plan == "gold":
        return True
    
    # Bronze users get mini studio during trial
    if trial_live and plan == "bronze":
        return True
    
    return False

def should_show_ads(user_plan: str, trial_active=False, trial_expires_at=None):
    """
    Check if user should see ads.
    Only Bronze users without ad-free addon see ads.
    Trial temporarily removes ads.
    """
    plan = (user_plan or "bronze").lower()
    trial_live = is_trial_live(trial_active, trial_expires_at)
    
    # Silver/Gold never see ads
    if plan in ["silver", "gold"]:
        return False
    
    # Bronze users don't see ads during trial
    if trial_live and plan == "bronze":
        return False
    
    # Bronze users see ads (unless they have ad-free addon - checked elsewhere)
    return plan == "bronze"