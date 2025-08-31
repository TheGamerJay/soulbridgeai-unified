"""
SoulBridge AI - Companion Access Control
Extracted from app.py monolith for modular architecture
"""
import logging
from flask import session
from .companion_data import get_companion_by_id, get_companions_by_tier, get_referral_companions

logger = logging.getLogger(__name__)

def get_effective_plan(user_plan: str, trial_active: bool) -> str:
    """Get effective plan for companion access (trial gives Gold access for companions only)"""
    if trial_active and user_plan == 'bronze':
        return 'gold'  # Trial users get Gold companion access
    return user_plan

def can_access_companion(user_plan: str, companion_tier: str, trial_active: bool) -> bool:
    """Check if user can access a companion based on tier"""
    effective_plan = get_effective_plan(user_plan, trial_active)
    
    # Bronze can access bronze companions
    if companion_tier == 'bronze':
        return True
    
    # Silver can access bronze and silver companions  
    if companion_tier == 'silver':
        return effective_plan in ['silver', 'gold']
    
    # Gold can access all companions
    if companion_tier == 'gold':
        return effective_plan == 'gold'
    
    return False

def user_can_access_companion(user_plan: str, trial_active: bool, referrals: int, comp: dict) -> bool:
    """Check if user can access a specific companion (including referral requirements)"""
    # Check tier access first
    if not can_access_companion(user_plan, comp["tier"], trial_active):
        return False
    
    # Check referral requirements
    if comp.get("min_referrals", 0) > referrals:
        return False
    
    return True

def companion_unlock_state_new(user_plan: str, trial_active: bool, referrals: int) -> dict:
    """Get unlock state for all companions"""
    from .companion_data import get_all_companions
    
    companions = get_all_companions()
    unlock_state = {}
    
    for comp in companions:
        comp_id = comp["id"]
        can_access = user_can_access_companion(user_plan, trial_active, referrals, comp)
        
        # Determine unlock reason
        if can_access:
            unlock_state[comp_id] = "unlocked"
        elif comp.get("min_referrals", 0) > referrals:
            unlock_state[comp_id] = f"referrals_needed_{comp['min_referrals']}"
        else:
            # Tier locked
            if comp["tier"] == "silver":
                unlock_state[comp_id] = "silver_tier_needed"
            elif comp["tier"] == "gold":
                unlock_state[comp_id] = "gold_tier_needed"
            else:
                unlock_state[comp_id] = "locked"
    
    return unlock_state

def get_access_matrix_new(user_plan: str, trial_active: bool) -> dict:
    """Get access matrix for user"""
    effective_plan = get_effective_plan(user_plan, trial_active)
    
    return {
        "can_access_bronze": True,  # Everyone can access bronze
        "can_access_silver": effective_plan in ['silver', 'gold'],
        "can_access_gold": effective_plan == 'gold',
        "effective_plan": effective_plan,
        "trial_active": trial_active
    }

def allowed_tiers_for_plan(plan: str) -> list:
    """Get allowed tiers for a plan"""
    if plan == 'bronze':
        return ['bronze']
    elif plan == 'silver':
        return ['bronze', 'silver']
    elif plan == 'gold':
        return ['bronze', 'silver', 'gold']
    else:
        return ['bronze']  # Default fallback

def get_user_companion_access() -> dict:
    """Get current user's companion access from session"""
    user_plan = session.get('user_plan', 'bronze')
    trial_active = session.get('trial_active', False)
    
    # Get referral count (would need to be implemented)
    referrals = 0  # Placeholder
    
    return {
        'user_plan': user_plan,
        'trial_active': trial_active,
        'referrals': referrals,
        'access_matrix': get_access_matrix_new(user_plan, trial_active),
        'unlock_state': companion_unlock_state_new(user_plan, trial_active, referrals)
    }

def require_companion_access(companion_id: str) -> bool:
    """Check if current user can access a specific companion"""
    # Sapphire is the special guide companion - available to all authenticated users
    if companion_id == 'sapphire':
        return True
    
    companion = get_companion_by_id(companion_id)
    if not companion:
        return False
    
    user_plan = session.get('user_plan', 'bronze')
    trial_active = session.get('trial_active', False)
    referrals = 0  # Placeholder - would get from database
    
    return user_can_access_companion(user_plan, trial_active, referrals, companion)