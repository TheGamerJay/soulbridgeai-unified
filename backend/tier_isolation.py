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
        """Check if free tier can access a feature"""
        return feature in self.features
    
    def get_available_companions(self) -> List[str]:
        """Get free tier companions only"""
        return self.limits['companions']
    
    def get_feature_limit(self, feature: str) -> int:
        """Get free tier limits"""
        return self.limits.get(feature, 0)
    
    def initialize_user_session(self, user_data: Dict[str, Any]):
        """Initialize free tier user session"""
        tier_session = {
            'user_id': user_data.get('user_id'),
            'user_email': user_data.get('user_email'),
            'user_plan': user_data.get('user_plan', 'free'),  # Store original plan for limits
            'tier': 'free',
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
        super().__init__('growth')
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
        """Check if growth tier can access a feature"""
        return feature in self.features
    
    def get_available_companions(self) -> List[str]:
        """Get growth tier companions"""
        return self.limits['companions']
    
    def get_feature_limit(self, feature: str) -> int:
        """Get growth tier limits"""
        return self.limits.get(feature, 0)
    
    def initialize_user_session(self, user_data: Dict[str, Any]):
        """Initialize growth tier user session"""
        tier_session = {
            'user_id': user_data.get('user_id'),
            'user_email': user_data.get('user_email'),
            'user_plan': user_data.get('user_plan', 'growth'),  # Store original plan for limits
            'tier': 'growth',
            'features': self.features,
            'limits': self.limits,
            'usage': {
                'decoder': 0,
                'fortune': 0,
                'horoscope': 0
            },
            'selected_companion': 'companion_sky'  # Default growth companion
        }
        self.set_session_data(tier_session)
        logger.info(f"✅ GROWTH TIER: Initialized session for user {user_data.get('user_email')}")

class MaxTier(TierSystem):
    """Max tier - completely isolated system"""
    
    def __init__(self):
        super().__init__('max')
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
        """Check if max tier can access a feature"""
        return feature in self.features
    
    def get_available_companions(self) -> List[str]:
        """Get all companions for max tier"""
        return self.limits['companions']
    
    def get_feature_limit(self, feature: str) -> int:
        """Get max tier limits (unlimited)"""
        return self.limits.get(feature, 999999)
    
    def initialize_user_session(self, user_data: Dict[str, Any]):
        """Initialize max tier user session"""
        tier_session = {
            'user_id': user_data.get('user_id'),
            'user_email': user_data.get('user_email'),
            'user_plan': user_data.get('user_plan', 'max'),  # Store original plan for limits
            'tier': 'max',
            'features': self.features,
            'limits': self.limits,
            'usage': {
                'decoder': 0,
                'fortune': 0,
                'horoscope': 0
            },
            'selected_companion': 'companion_crimson'  # Default max companion
        }
        self.set_session_data(tier_session)
        logger.info(f"✅ MAX TIER: Initialized session for user {user_data.get('user_email')}")

class TierManager:
    """Manages tier detection and routing"""
    
    def __init__(self):
        self.tiers = {
            'free': FreeTier(),
            'growth': GrowthTier(), 
            'max': MaxTier()
        }
    
    def get_user_tier(self, user_plan: str, trial_active: bool = False) -> str:
        """Determine user's tier (simple, no complex logic)"""
        # During trial, users get max tier access
        if trial_active:
            return 'max'
        
        # Map plan to tier directly
        tier_mapping = {
            'free': 'free',
            'growth': 'growth',
            'max': 'max'
        }
        
        return tier_mapping.get(user_plan, 'free')
    
    def clear_all_tier_sessions(self):
        """Clear all tier session keys from the session (strong isolation)"""
        for tier in self.tiers:
            self.tiers[tier].clear_session_data()

    def initialize_user_for_tier(self, user_data: Dict[str, Any], tier_name: str):
        """Initialize user session for specific tier, enforcing strong isolation"""
        self.clear_all_tier_sessions()
        if tier_name in self.tiers:
            # Special handling for trial users - they get access to max tier companions
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
        """Initialize trial user with max tier access but original plan limits"""
        original_plan = user_data.get('user_plan', 'free')
        
        # Get the limits from the user's original tier
        original_tier_system = self.tiers[original_plan]
        
        # Get the companions from the max tier
        max_tier_system = self.tiers['max']
        
        # Create hybrid session: Max companions + Original limits
        tier_session = {
            'user_id': user_data.get('user_id'),
            'user_email': user_data.get('user_email'),
            'user_plan': original_plan,  # Store original plan for limits
            'tier': access_tier,  # Max tier for access
            'features': max_tier_system.features,  # Max tier features
            'limits': original_tier_system.limits,  # Original tier limits (IMPORTANT!)
            'companions': max_tier_system.limits['companions'],  # Max tier companions
            'usage': {
                'decoder': 0,
                'fortune': 0,
                'horoscope': 0
            },
            'selected_companion': 'companion_crimson',  # Default max companion
            'trial_mode': True  # Flag to indicate this is a trial session
        }
        
        # Use the access tier's session key
        self.tiers[access_tier].set_session_data(tier_session)
        logger.info(f"✨ TRIAL MODE: User {user_data.get('user_email')} gets {access_tier.upper()} access with {original_plan.upper()} limits")
    
    def get_tier_system(self, tier_name: str) -> TierSystem:
        """Get the tier system for a specific tier"""
        return self.tiers.get(tier_name, self.tiers['free'])

# Global tier manager instance
tier_manager = TierManager()

def get_current_user_tier() -> str:
    """Get current user's tier from session"""
    # If trial is active, user gets max tier access
    trial_active = session.get('trial_active', False)
    if trial_active:
        return 'max'
    
    # DEBUG: Log all tier sessions to see contamination
    active_tiers = []
    for tier_name in ['free', 'growth', 'max']:
        tier_session = session.get(f'tier_{tier_name}', {})
        if tier_session and tier_session.get('user_id'):
            active_tiers.append(tier_name)
    
    if len(active_tiers) > 1:
        logger.warning(f"🚨 TIER CONTAMINATION: Multiple active tiers detected: {active_tiers}")
    
    # Check each tier session to see which one is active
    # IMPORTANT: Check in reverse order (max -> growth -> free) so highest tier wins
    for tier_name in ['max', 'growth', 'free']:
        tier_session = session.get(f'tier_{tier_name}', {})
        if tier_session and tier_session.get('user_id'):
            logger.info(f"🎯 TIER DETECTED: {tier_name} (active_tiers: {active_tiers})")
            return tier_name
    
    logger.info(f"🎯 TIER DETECTED: free (default, active_tiers: {active_tiers})")
    return 'free'  # Default to free if no tier is active

def get_current_tier_system() -> TierSystem:
    """Get current user's tier system"""
    current_tier = get_current_user_tier()
    return tier_manager.get_tier_system(current_tier)