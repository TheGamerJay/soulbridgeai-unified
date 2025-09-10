"""
SoulBridge AI - Tiered Credit System (Compatibility Layer)
Provides backward compatibility for old tiered_credit_system imports
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Re-export from unified_tier_system for compatibility
from unified_tier_system import (
    get_user_credits,
    deduct_credits,
    add_credits,
    get_effective_plan,
    get_feature_limit,
    can_access_feature,
    DAILY_LIMITS,
    MONTHLY_CREDITS
)

def tier_can_access_premium_feature(user_plan: str, trial_active: bool = False) -> bool:
    """Check if user can access premium features"""
    effective_plan = get_effective_plan(user_plan, trial_active)
    return effective_plan in ['silver', 'gold']

def tier_can_access_gold_feature(user_plan: str, trial_active: bool = False) -> bool:
    """Check if user can access Gold-only features"""
    effective_plan = get_effective_plan(user_plan, trial_active)
    return effective_plan == 'gold'

def get_monthly_credit_allowance(user_plan: str) -> int:
    """Get monthly credit allowance for a plan"""
    return MONTHLY_CREDITS.get(user_plan, 0)

def has_sufficient_credits(user_id: int, required_credits: int) -> bool:
    """Check if user has sufficient credits"""
    current_credits = get_user_credits(user_id)
    return current_credits >= required_credits

def get_tier_limits() -> Dict[str, Dict[str, int]]:
    """Get tier limits dictionary"""
    return DAILY_LIMITS

def is_premium_user(user_plan: str) -> bool:
    """Check if user has a premium plan"""
    return user_plan in ['silver', 'gold']

def get_tier_display_name(user_plan: str) -> str:
    """Get display name for tier"""
    return user_plan.title()

# Additional compatibility functions that might be needed
def check_feature_access(user_id: int, feature: str, user_plan: str, trial_active: bool = False) -> Dict[str, Any]:
    """Check feature access and return status info"""
    can_access = can_access_feature(user_plan, feature, trial_active)
    limit = get_feature_limit(user_plan, feature)
    
    return {
        'can_access': can_access,
        'limit': limit,
        'user_plan': user_plan,
        'effective_plan': get_effective_plan(user_plan, trial_active),
        'is_trial': trial_active and user_plan == 'bronze'
    }

def get_feature_cost(feature: str) -> int:
    """Get the artistic time cost for a specific feature"""
    try:
        from modules.credits.operations import get_feature_cost
        return get_feature_cost(feature)
    except ImportError:
        # Fallback costs for common features
        feature_costs = {
            'ai_images': 5,
            'voice_journaling': 3,
            'relationship_profiles': 2,
            'meditations': 1,
            'mini_studio': 10
        }
        return feature_costs.get(feature, 5)

def get_credit_bundles() -> List[Dict[str, Any]]:
    """Get available credit bundles for purchase"""
    return [
        {'id': 'bundle_50', 'credits': 50, 'price': 5.00, 'name': 'Starter Pack'},
        {'id': 'bundle_100', 'credits': 100, 'price': 9.00, 'name': 'Power Pack'},
        {'id': 'bundle_250', 'credits': 250, 'price': 20.00, 'name': 'Pro Pack'},
        {'id': 'bundle_500', 'credits': 500, 'price': 35.00, 'name': 'Ultimate Pack'}
    ]

def apply_tiered_credit_deduction(user_id: int, feature: str, user_plan: str, trial_active: bool = False) -> Dict[str, Any]:
    """Apply tiered credit deduction for a feature"""
    cost = get_feature_cost(feature)
    
    # Check if user has enough credits
    current_credits = get_user_credits(user_id)
    if current_credits < cost:
        return {
            'success': False,
            'error': 'Insufficient credits',
            'required': cost,
            'available': current_credits
        }
    
    # Deduct credits
    success = deduct_credits(user_id, cost)
    
    return {
        'success': success,
        'credits_deducted': cost if success else 0,
        'remaining_credits': get_user_credits(user_id) if success else current_credits
    }

def get_upsell_message(user_plan: str, feature: str) -> str:
    """Get upsell message for a feature"""
    if user_plan == 'bronze':
        return f"Upgrade to Silver or Gold to access {feature}!"
    elif user_plan == 'silver':
        return f"Upgrade to Gold for unlimited access to {feature}!"
    else:
        return ""

# Monthly allowances - alias for MONTHLY_CREDITS
MONTHLY_ALLOWANCES = MONTHLY_CREDITS

logger.info("🔄 Tiered credit system compatibility layer loaded")