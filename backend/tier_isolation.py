#!/usr/bin/env python3
"""
TIER ISOLATION SYSTEM - Complete separation of Bronze, Silver, and Gold tiers
No shared session data, no cross-contamination, perfect isolation
"""

from flask import session
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class TierSystem:
    """Base class for tier-specific functionality"""
    
    def __init__(self, tier_name: str):
        self.tier_name = tier_name
        self.session_key = f'tier_{tier_name}'
    
    def get_session_data(self) -> Dict[str, Any]:
        """Get tier-specific session data"""
        return session.get(self.session_key, {})
    
    def set_session_data(self, data: Dict[str, Any]):
        """
        Set tier-specific session data.
        Only the TierManager should ever call this method directly.
        If you see this being called elsewhere, it is a bug.
        """
        # Safety assertion: only allow from TierManager context
        import inspect
        stack = inspect.stack()
        allowed_callers = ["initialize_user_for_tier", "initialize_trial_user", "clear_session_data"]
        if not any(frame.function in allowed_callers for frame in stack[:5]):
            raise RuntimeError("Tier session keys must only be set by TierManager methods!")
        session[self.session_key] = data
        session.modified = True
    
    def clear_session_data(self):
        """Clear tier-specific session data"""
        if self.session_key in session:
            del session[self.session_key]
        session.modified = True

class BronzeTier(TierSystem):
    """Bronze tier - completely isolated system"""
    
    def __init__(self):
        super().__init__('bronze')
        self.features = [
            'basic_chat',
            'blayzo_companion', 
            'blayzica_companion',
            'gamerjay_companion'
        ]
        self.limits = {
            'decoder': 3,
            'fortune': 2,
            'horoscope': 3,
            'companions': ['blayzo_free', 'blayzica_free', 'companion_gamerjay']
        }
    
    def can_access_feature(self, feature: str) -> bool:
        """Check if bronze tier can access a feature"""
        return feature in self.features
    
    def get_available_companions(self) -> List[str]:
        """Get bronze tier companions only"""
        return self.limits['companions']
    
    def get_feature_limit(self, feature: str) -> int:
        """Get bronze tier limits"""
        return self.limits.get(feature, 0)
    
    def initialize_user_session(self, user_data: Dict[str, Any]):
        """Initialize bronze tier user session"""
        tier_session = {
            'user_id': user_data.get('user_id'),
            'user_email': user_data.get('user_email'),
            'user_plan': user_data.get('user_plan', 'bronze'),  # Store original plan for limits
            'tier': 'bronze',
            'features': self.features,
            'limits': self.limits,
            'usage': {
                'decoder': 0,
                'fortune': 0,
                'horoscope': 0
            },
            'selected_companion': 'blayzo_free'
        }
        self.set_session_data(tier_session)
        logger.info(f"✅ FREE TIER: Initialized session for user {user_data.get('user_email')}")

class GrowthTier(TierSystem):
    """Growth tier - completely isolated system"""
    
    def __init__(self):
        super().__init__('silver')
        self.features = [
            'basic_chat',
            'premium_chat',
            'decoder_mode',
            'creative_writing',
            'all_free_companions',
            'premium_companions'
        ]
        self.limits = {
            'decoder': 15,
            'fortune': 8,
            'horoscope': 10,
            'companions': [
                # Free companions
                'blayzo_free', 'blayzica_free', 'companion_gamerjay',
                # Growth companions  
                'companion_sky', 'blayzo_premium', 'blayzica_growth', 
                'gamerjay_premium', 'watchdog_growth', 'crimson_growth', 
                'violet_growth', 'claude_growth'
            ]
        }
    
    def can_access_feature(self, feature: str) -> bool:
        """Check if silver tier can access a feature"""
        return feature in self.features
    
    def get_available_companions(self) -> List[str]:
        """Get silver tier companions"""
        return self.limits['companions']
    
    def get_feature_limit(self, feature: str) -> int:
        """Get silver tier limits"""
        return self.limits.get(feature, 0)
    
    def initialize_user_session(self, user_data: Dict[str, Any]):
        """Initialize silver tier user session"""
        tier_session = {
            'user_id': user_data.get('user_id'),
            'user_email': user_data.get('user_email'),
            'user_plan': user_data.get('user_plan', 'silver'),  # Store original plan for limits
            'tier': 'silver',
            'features': self.features,
            'limits': self.limits,
            'usage': {
                'decoder': 0,
                'fortune': 0,
                'horoscope': 0
            },
            'selected_companion': 'companion_sky'  # Default silver companion
        }
        self.set_session_data(tier_session)
        logger.info(f"✅ GROWTH TIER: Initialized session for user {user_data.get('user_email')}")

class MaxTier(TierSystem):
    """Max tier - completely isolated system"""
    
    def __init__(self):
        super().__init__('gold')
        self.features = [
            'basic_chat',
            'premium_chat',
            'decoder_mode',
            'creative_writing',
            'fortune_telling',
            'horoscope',
            'all_companions',
            'voice_chat',
            'priority_support',
            'mini_studio'  # Added for Max tier UI button
        ]
        self.limits = {
            'decoder': 999999,
            'fortune': 999999,
            'horoscope': 999999,
            'companions': [
                # Free companions
                'blayzo_free', 'blayzica_free', 'companion_gamerjay',
                # Growth companions
                'companion_sky', 'blayzo_premium', 'blayzica_growth', 
                'gamerjay_premium', 'watchdog_growth', 'crimson_growth', 
                'violet_growth', 'claude_growth',
                # Max companions
                'companion_crimson', 'companion_violet', 'royal_max', 
                'watchdog_max', 'ven_blayzica', 'ven_sky', 'claude_max'
            ]
        }
    
    def can_access_feature(self, feature: str) -> bool:
        """Check if gold tier can access a feature"""
        return feature in self.features
    
    def get_available_companions(self) -> List[str]:
        """Get all companions for gold tier"""
        return self.limits['companions']
    
    def get_feature_limit(self, feature: str) -> int:
        """Get gold tier limits (unlimited)"""
        return self.limits.get(feature, 999999)
    
    def initialize_user_session(self, user_data: Dict[str, Any]):
        """Initialize gold tier user session"""
        tier_session = {
            'user_id': user_data.get('user_id'),
            'user_email': user_data.get('user_email'),
            'user_plan': user_data.get('user_plan', 'gold'),  # Store original plan for limits
            'tier': 'gold',
            'features': self.features,
            'limits': self.limits,
            'usage': {
                'decoder': 0,
                'fortune': 0,
                'horoscope': 0
            },
            'selected_companion': 'companion_crimson'  # Default gold companion
        }
        self.set_session_data(tier_session)
        logger.info(f"✅ MAX TIER: Initialized session for user {user_data.get('user_email')}")

class SilverTier(TierSystem):
    """Silver tier - completely isolated system (was Growth)"""
    
    def __init__(self):
        super().__init__('silver')
        self.features = [
            'basic_chat',
            'premium_chat',
            'decoder_mode',
            'creative_writing',
            'all_free_companions',
            'premium_companions'
        ]
        self.limits = {
            'decoder': 15,
            'fortune': 8,
            'horoscope': 10,
            'companions': [
                # Bronze companions
                'blayzo_free', 'blayzica_free', 'companion_gamerjay',
                # Silver companions  
                'companion_sky', 'blayzo_premium', 'blayzica_growth', 
                'gamerjay_premium', 'watchdog_growth', 'crimson_growth', 
                'violet_growth', 'claude_growth'
            ]
        }
    
    def can_access_feature(self, feature: str) -> bool:
        """Check if silver tier can access a feature"""
        return feature in self.features
    
    def get_available_companions(self) -> List[str]:
        """Get silver tier companions"""
        return self.limits['companions']
    
    def get_feature_limit(self, feature: str) -> int:
        """Get silver tier limits"""
        return self.limits.get(feature, 0)
    
    def initialize_user_session(self, user_data: Dict[str, Any]):
        """Initialize silver tier user session"""
        tier_session = {
            'user_id': user_data.get('user_id'),
            'user_email': user_data.get('user_email'),
            'user_plan': user_data.get('user_plan', 'silver'),  # Store original plan for limits
            'tier': 'silver',
            'features': self.features,
            'limits': self.limits,
            'usage': {
                'decoder': 0,
                'fortune': 0,
                'horoscope': 0
            },
            'selected_companion': 'companion_sky'  # Default silver companion
        }
        self.set_session_data(tier_session)
        logger.info(f"✅ SILVER TIER: Initialized session for user {user_data.get('user_email')}")

class GoldTier(TierSystem):
    """Gold tier - completely isolated system (was Max)"""
    
    def __init__(self):
        super().__init__('gold')
        self.features = [
            'basic_chat',
            'premium_chat',
            'decoder_mode',
            'creative_writing',
            'fortune_telling',
            'horoscope',
            'all_companions',
            'voice_chat',
            'priority_support',
            'mini_studio'  # Added for Gold tier UI button
        ]
        self.limits = {
            'decoder': 999999,
            'fortune': 999999,
            'horoscope': 999999,
            'companions': [
                # Bronze companions
                'blayzo_free', 'blayzica_free', 'companion_gamerjay',
                # Silver companions
                'companion_sky', 'blayzo_premium', 'blayzica_growth', 
                'gamerjay_premium', 'watchdog_growth', 'crimson_growth', 
                'violet_growth', 'claude_growth',
                # Gold companions
                'companion_crimson', 'companion_violet', 'royal_max', 
                'watchdog_max', 'ven_blayzica', 'ven_sky', 'claude_max'
            ]
        }
    
    def can_access_feature(self, feature: str) -> bool:
        """Check if gold tier can access a feature"""
        return feature in self.features
    
    def get_available_companions(self) -> List[str]:
        """Get all companions for gold tier"""
        return self.limits['companions']
    
    def get_feature_limit(self, feature: str) -> int:
        """Get gold tier limits (unlimited)"""
        return self.limits.get(feature, 999999)
    
    def initialize_user_session(self, user_data: Dict[str, Any]):
        """Initialize gold tier user session"""
        tier_session = {
            'user_id': user_data.get('user_id'),
            'user_email': user_data.get('user_email'),
            'user_plan': user_data.get('user_plan', 'gold'),  # Store original plan for limits
            'tier': 'gold',
            'features': self.features,
            'limits': self.limits,
            'usage': {
                'decoder': 0,
                'fortune': 0,
                'horoscope': 0
            },
            'selected_companion': 'companion_crimson'  # Default gold companion
        }
        self.set_session_data(tier_session)
        logger.info(f"✅ GOLD TIER: Initialized session for user {user_data.get('user_email')}")

class TierManager:
    """Manages tier detection and routing"""
    
    def __init__(self):
        self.tiers = {
            'bronze': BronzeTier(),
            'silver': SilverTier(), 
            'gold': GoldTier()
        }
    
    def get_user_tier(self, user_plan: str, trial_active: bool = False) -> str:
        """Determine user's tier (simple, no complex logic)"""
        # During trial, users get gold tier access
        if trial_active:
            return 'gold'
        
        # Map plan to tier directly (with legacy support)
        tier_mapping = {
            # New naming
            'bronze': 'bronze',
            'silver': 'silver',
            'gold': 'gold',
            # Legacy naming
            'free': 'bronze',
            'growth': 'silver',
            'max': 'gold'
        }
        
        return tier_mapping.get(user_plan, 'bronze')
    
    def clear_all_tier_sessions(self):
        """Clear all tier session keys from the session (strong isolation)"""
        for tier in self.tiers:
            self.tiers[tier].clear_session_data()

    def initialize_user_for_tier(self, user_data: Dict[str, Any], tier_name: str):
        """Initialize user session for specific tier, enforcing strong isolation"""
        self.clear_all_tier_sessions()
        if tier_name in self.tiers:
            # Special handling for trial users - they get access to gold tier companions
            # but keep their original plan limits to avoid false hope
            if user_data.get('trial_active', False):
                self.initialize_trial_user(user_data, tier_name)
            else:
                # Initialize the correct tier normally
                self.tiers[tier_name].initialize_user_session(user_data)
            logger.info(f"🔒 TIER ISOLATION: User initialized for {tier_name.upper()} tier only")
        else:
            logger.error(f"❌ Unknown tier: {tier_name}")
    
    def initialize_trial_user(self, user_data: Dict[str, Any], access_tier: str):
        """Initialize trial user with gold tier access but original plan limits"""
        original_plan = user_data.get('user_plan', 'bronze')
        
        # Get the limits from the user's original tier
        original_tier_system = self.tiers[original_plan]
        
        # Get the companions from the gold tier
        gold_tier_system = self.tiers['gold']
        
        # Create hybrid session: Gold companions + Original limits
        tier_session = {
            'user_id': user_data.get('user_id'),
            'user_email': user_data.get('user_email'),
            'user_plan': original_plan,  # Store original plan for limits
            'tier': access_tier,  # Gold tier for access
            'features': gold_tier_system.features,  # Gold tier features
            'limits': original_tier_system.limits,  # Original tier limits (IMPORTANT!)
            'companions': gold_tier_system.limits['companions'],  # Gold tier companions
            'usage': {
                'decoder': 0,
                'fortune': 0,
                'horoscope': 0
            },
            'selected_companion': 'companion_crimson',  # Default gold companion
            'trial_mode': True  # Flag to indicate this is a trial session
        }
        
        # Use the access tier's session key
        self.tiers[access_tier].set_session_data(tier_session)
        logger.info(f"✨ TRIAL MODE: User {user_data.get('user_email')} gets {access_tier.upper()} access with {original_plan.upper()} limits")
    
    def get_tier_system(self, tier_name: str) -> TierSystem:
        """Get the tier system for a specific tier"""
        return self.tiers.get(tier_name, self.tiers['bronze'])

# Global tier manager instance
tier_manager = TierManager()

def get_current_user_tier() -> str:
    """Get current user's tier from session"""
    # If trial is active, user gets gold tier access
    trial_active = session.get('trial_active', False)
    if trial_active:
        return 'gold'
    
    # DEBUG: Log all tier sessions to see contamination
    active_tiers = []
    all_tier_names = ['bronze', 'silver', 'gold']
    for tier_name in all_tier_names:
        tier_session = session.get(f'tier_{tier_name}', {})
        if tier_session and tier_session.get('user_id'):
            active_tiers.append(tier_name)
    
    if len(active_tiers) > 1:
        logger.warning(f"🚨 TIER CONTAMINATION: Multiple active tiers detected: {active_tiers}")
    
    # Check each tier session to see which one is active
    # IMPORTANT: Check in reverse order (gold -> silver -> bronze) so highest tier wins
    priority_order = ['gold', 'silver', 'bronze']
    for tier_name in priority_order:
        tier_session = session.get(f'tier_{tier_name}', {})
        if tier_session and tier_session.get('user_id'):
            logger.info(f"🎯 TIER DETECTED: {tier_name} (active_tiers: {active_tiers})")
            # Return tier name directly
            return tier_name
    
    logger.info(f"🎯 TIER DETECTED: bronze (default, active_tiers: {active_tiers})")
    return 'bronze'  # Default to bronze if no tier is active

def get_current_tier_system() -> TierSystem:
    """Get current user's tier system"""
    current_tier = get_current_user_tier()
    return tier_manager.get_tier_system(current_tier)