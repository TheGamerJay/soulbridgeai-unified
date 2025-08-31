"""
SoulBridge AI - Credits System Module
Unified artistic time/credit system consolidated from scattered implementations
Handles all credit operations: get, deduct, refund, reset, costs
"""

from .credit_manager import CreditManager
from .constants import (
    ARTISTIC_TIME_COSTS,
    TIER_ARTISTIC_TIME,
    TRIAL_ARTISTIC_TIME,
    AI_IMAGE_COST
)
from .operations import (
    get_artistic_time,
    deduct_artistic_time,
    refund_artistic_time,
    get_feature_cost,
    get_monthly_allowance,
    ensure_user_data_initialized
)

__all__ = [
    'CreditManager',
    'ARTISTIC_TIME_COSTS',
    'TIER_ARTISTIC_TIME', 
    'TRIAL_ARTISTIC_TIME',
    'AI_IMAGE_COST',
    'get_artistic_time',
    'deduct_artistic_time',
    'refund_artistic_time',
    'get_feature_cost',
    'get_monthly_allowance',
    'ensure_user_data_initialized'
]