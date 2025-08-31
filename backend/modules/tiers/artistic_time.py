"""
SoulBridge AI - Artistic Time System (DEPRECATED)
This module is being replaced by the new unified credits system.
Please import from modules.credits instead.
"""
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

# DEPRECATED: Use modules.credits.constants instead
from ..credits.constants import (
    ARTISTIC_TIME_COSTS,
    TIER_ARTISTIC_TIME,
    TRIAL_ARTISTIC_TIME
)

logger.warning("modules.tiers.artistic_time is deprecated. Use modules.credits instead.")

# DEPRECATED: Import from new credits module
from ..credits.operations import (
    ensure_user_data_initialized,
    get_artistic_time,
    deduct_artistic_time,
    get_feature_cost,
    get_monthly_allowance
)

# Import from access.py for compatibility
from access import get_effective_access, get_feature_limit

# Additional compatibility functions
def get_feature_usage_today(user_id, feature_type):
    """Get today's usage for a feature - compatibility wrapper"""
    # This would connect to usage tracking in practice
    return 0

# AI Image limits - compatibility
AI_IMAGE_LIMITS = {
    'bronze': 0,
    'silver': 10,
    'gold': 999
}