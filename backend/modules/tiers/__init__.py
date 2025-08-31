"""
SoulBridge AI - Tiers Module
Tier system, trials, and artistic time management
"""

from .artistic_time import (
    get_artistic_time,
    deduct_artistic_time,
    get_feature_cost,
    get_monthly_allowance,
    ARTISTIC_TIME_COSTS,
    TIER_ARTISTIC_TIME,
    TRIAL_ARTISTIC_TIME
)

__all__ = [
    'get_artistic_time',
    'deduct_artistic_time', 
    'get_feature_cost',
    'get_monthly_allowance',
    'ARTISTIC_TIME_COSTS',
    'TIER_ARTISTIC_TIME',
    'TRIAL_ARTISTIC_TIME'
]