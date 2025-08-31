"""
SoulBridge AI - Companions Module
AI companion system with tier-based access control
"""

from .companion_data import (
    COMPANIONS,
    get_companions_by_tier,
    get_referral_companions, 
    get_companion_by_id,
    get_all_companions,
    get_companion_tiers
)
from .access_control import (
    get_effective_plan,
    can_access_companion,
    user_can_access_companion,
    companion_unlock_state_new,
    get_access_matrix_new,
    allowed_tiers_for_plan,
    get_user_companion_access,
    require_companion_access
)
from .chat_service import CompanionChatService
from .routes import companions_bp
from .companion_utils import (
    get_companion_selections_today,
    track_companion_selection,
    get_user_companion_history,
    get_companion_popularity_stats,
    restore_companion_data,
    get_companion_usage_stats
)

__all__ = [
    'COMPANIONS',
    'get_companions_by_tier',
    'get_referral_companions',
    'get_companion_by_id', 
    'get_all_companions',
    'get_companion_tiers',
    'get_effective_plan',
    'can_access_companion',
    'user_can_access_companion',
    'companion_unlock_state_new',
    'get_access_matrix_new',
    'allowed_tiers_for_plan',
    'get_user_companion_access',
    'require_companion_access',
    'CompanionChatService',
    'companions_bp',
    'get_companion_selections_today',
    'track_companion_selection',
    'get_user_companion_history',
    'get_companion_popularity_stats',
    'restore_companion_data',
    'get_companion_usage_stats'
]