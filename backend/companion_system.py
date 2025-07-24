"""
Enhanced Companion Selector System for SoulBridge AI
Netflix-style UI with tier-based access and premium companions
"""
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)

class CompanionTier(Enum):
    FREE = "free"
    GROWTH = "growth" 
    MAX = "max"
    REFERRAL = "referral"

class UnlockType(Enum):
    SUBSCRIPTION = "subscription"
    REFERRAL_POINTS = "referral_points"
    ACHIEVEMENT = "achievement"
    SPECIAL_EVENT = "special_event"

class PersonalityTag(Enum):
    EMPATHETIC = "Empathetic"
    SPIRITUAL = "Spiritual"
    ANALYTICAL = "Analytical"
    MOTIVATIONAL = "Motivational"
    CREATIVE = "Creative"
    WISE = "Wise"
    PLAYFUL = "Playful"
    PROTECTIVE = "Protective"
    HEALING = "Healing"
    ADVENTUROUS = "Adventurous"

@dataclass
class Companion:
    """Individual AI companion definition"""
    companion_id: str
    name: str
    display_name: str
    tier: CompanionTier
    unlock_type: UnlockType
    personality_tags: List[PersonalityTag]
    avatar_image: str
    short_bio: str
    detailed_bio: str
    voice_id: Optional[str]
    ai_personality_mode: str  # Links to our AI personality system
    unlock_requirements: Dict[str, Any]  # Referral points, achievements, etc.
    popularity_score: int  # For "Most Popular" badges
    is_recommended: bool
    special_features: List[str]
    created_at: datetime
    is_active: bool = True

@dataclass 
class UserCompanionAccess:
    """User's companion access and selection"""
    user_id: str
    selected_companion_id: str
    unlocked_companions: List[str]
    subscription_tier: str
    referral_points: int
    achievements_unlocked: List[str]
    last_companion_change: datetime
    trial_companions_used: List[str]  # For "Try Me Today" feature

class CompanionSystem:
    """Enhanced Companion Selector System"""
    
    def __init__(self):
        self.companions = {}
        self.user_access = defaultdict(lambda: None)
        
        # Initialize default companions for each tier
        self._initialize_default_companions()
        
        logger.info("Enhanced Companion System initialized")
    
    def _initialize_default_companions(self):
        """Initialize companions for each subscription tier"""
        
        # FREE TIER COMPANIONS
        free_companions = [
            {
                "companion_id": "companion_sage",
                "name": "Sage", 
                "display_name": "Sage - The Wise Guide",
                "tier": CompanionTier.FREE,
                "unlock_type": UnlockType.SUBSCRIPTION,
                "personality_tags": [PersonalityTag.WISE, PersonalityTag.EMPATHETIC],
                "avatar_image": "/static/logos/Sapphire.png",
                "short_bio": "A gentle, wise companion for life's journey",
                "detailed_bio": "Sage offers thoughtful guidance and emotional support through life's challenges. With deep wisdom and empathetic understanding, Sage helps you find clarity and peace.",
                "voice_id": None,
                "ai_personality_mode": "therapist",
                "unlock_requirements": {"subscription": "free"},
                "popularity_score": 95,
                "is_recommended": True,
                "special_features": ["Meditation guidance", "Life advice", "Emotional support"]
            },
            {
                "companion_id": "companion_spark",
                "name": "Spark",
                "display_name": "Spark - The Motivator", 
                "tier": CompanionTier.FREE,
                "unlock_type": UnlockType.SUBSCRIPTION,
                "personality_tags": [PersonalityTag.MOTIVATIONAL, PersonalityTag.PLAYFUL],
                "avatar_image": "/static/logos/GamerJay Free companion.png",
                "short_bio": "Your energetic companion for motivation and growth",
                "detailed_bio": "Spark brings enthusiasm and motivation to help you achieve your goals. With an upbeat personality and encouraging words, Spark keeps you moving forward.",
                "voice_id": None,
                "ai_personality_mode": "coach",
                "unlock_requirements": {"subscription": "free"},
                "popularity_score": 88,
                "is_recommended": False,
                "special_features": ["Goal setting", "Daily motivation", "Progress tracking"]
            }
        ]
        
        # GROWTH TIER COMPANIONS  
        growth_companions = [
            {
                "companion_id": "companion_luna",
                "name": "Luna",
                "display_name": "Luna - The Spiritual Guide",
                "tier": CompanionTier.GROWTH,
                "unlock_type": UnlockType.SUBSCRIPTION,
                "personality_tags": [PersonalityTag.SPIRITUAL, PersonalityTag.HEALING],
                "avatar_image": "/static/logos/Sky a primum companion.png", 
                "short_bio": "Connect with your spiritual side through Luna's guidance",
                "detailed_bio": "Luna specializes in spiritual growth, mindfulness, and inner healing. She guides you through meditation, chakra work, and connecting with your higher self.",
                "voice_id": "luna_voice_id",
                "ai_personality_mode": "mentor",
                "unlock_requirements": {"subscription": "growth"},
                "popularity_score": 92,
                "is_recommended": True,
                "special_features": ["Spiritual guidance", "Meditation sessions", "Energy healing", "Voice interactions"]
            },
            {
                "companion_id": "companion_atlas",
                "name": "Atlas",
                "display_name": "Atlas - The Analytical Mind",
                "tier": CompanionTier.GROWTH,
                "unlock_type": UnlockType.SUBSCRIPTION,
                "personality_tags": [PersonalityTag.ANALYTICAL, PersonalityTag.WISE],
                "avatar_image": "/static/logos/GamgerJay premium companion.png",
                "short_bio": "Logic and analysis for complex life decisions",
                "detailed_bio": "Atlas excels at breaking down complex problems, analyzing situations objectively, and providing data-driven insights for better decision making.",
                "voice_id": "atlas_voice_id", 
                "ai_personality_mode": "therapist",
                "unlock_requirements": {"subscription": "growth"},
                "popularity_score": 85,
                "is_recommended": False,
                "special_features": ["Problem analysis", "Decision trees", "Logic frameworks", "Voice interactions"]
            }
        ]
        
        # MAX TIER COMPANIONS
        max_companions = [
            {
                "companion_id": "companion_phoenix",
                "name": "Phoenix",
                "display_name": "Phoenix - The Transformer",
                "tier": CompanionTier.MAX,
                "unlock_type": UnlockType.SUBSCRIPTION,
                "personality_tags": [PersonalityTag.HEALING, PersonalityTag.PROTECTIVE, PersonalityTag.WISE],
                "avatar_image": "/static/logos/Crimson a Max companion.png",
                "short_bio": "Rise from challenges stronger than before",
                "detailed_bio": "Phoenix specializes in transformation, trauma healing, and helping you rise stronger from life's challenges. A powerful ally for deep personal growth.",
                "voice_id": "phoenix_voice_id",
                "ai_personality_mode": "therapist",
                "unlock_requirements": {"subscription": "max"},
                "popularity_score": 98,
                "is_recommended": True,
                "special_features": ["Trauma healing", "Transformation coaching", "Crisis support", "Advanced voice AI", "Priority response"]
            },
            {
                "companion_id": "companion_nova",
                "name": "Nova", 
                "display_name": "Nova - The Creative Spark",
                "tier": CompanionTier.MAX,
                "unlock_type": UnlockType.SUBSCRIPTION,
                "personality_tags": [PersonalityTag.CREATIVE, PersonalityTag.ADVENTUROUS, PersonalityTag.PLAYFUL],
                "avatar_image": "/static/logos/Violet a max companion.png",
                "short_bio": "Unleash your creative potential and explore new horizons",
                "detailed_bio": "Nova ignites creativity, encourages artistic expression, and helps you explore new possibilities. Perfect for artists, writers, and creative souls.",
                "voice_id": "nova_voice_id",
                "ai_personality_mode": "friend", 
                "unlock_requirements": {"subscription": "max"},
                "popularity_score": 91,
                "is_recommended": False,
                "special_features": ["Creative exercises", "Art therapy", "Inspiration sessions", "Advanced voice AI", "Custom personality modes"]
            }
        ]
        
        # REFERRAL TIER COMPANIONS
        referral_companions = [
            {
                "companion_id": "companion_blayzo",
                "name": "Blayzo",
                "display_name": "Blayzo - The Community Champion", 
                "tier": CompanionTier.REFERRAL,
                "unlock_type": UnlockType.REFERRAL_POINTS,
                "personality_tags": [PersonalityTag.EMPATHETIC, PersonalityTag.MOTIVATIONAL, PersonalityTag.WISE],
                "avatar_image": "/static/logos/Blayzo Referral.png",
                "short_bio": "Exclusive companion for our community champions",
                "detailed_bio": "Blayzo is a special companion available only to those who help grow our community. With unique insights and exclusive features, Blayzo rewards your dedication to bringing others into the SoulBridge family.",
                "voice_id": "blayzo_voice_id",
                "ai_personality_mode": "mentor",
                "unlock_requirements": {"referral_points": 1000},
                "popularity_score": 100,
                "is_recommended": True,
                "special_features": ["Community insights", "Exclusive content", "Advanced features", "Priority support", "Special voice interactions"]
            }
        ]
        
        # Add all companions to the system
        all_companions = free_companions + growth_companions + max_companions + referral_companions
        
        for comp_data in all_companions:
            companion = Companion(
                companion_id=comp_data["companion_id"],
                name=comp_data["name"],
                display_name=comp_data["display_name"],
                tier=comp_data["tier"],
                unlock_type=comp_data["unlock_type"],
                personality_tags=comp_data["personality_tags"],
                avatar_image=comp_data["avatar_image"],
                short_bio=comp_data["short_bio"],
                detailed_bio=comp_data["detailed_bio"],
                voice_id=comp_data["voice_id"],
                ai_personality_mode=comp_data["ai_personality_mode"],
                unlock_requirements=comp_data["unlock_requirements"],
                popularity_score=comp_data["popularity_score"],
                is_recommended=comp_data["is_recommended"],
                special_features=comp_data["special_features"],
                created_at=datetime.now()
            )
            
            self.companions[companion.companion_id] = companion
            
        logger.info(f"Initialized {len(all_companions)} companions across all tiers")
    
    def get_companions_by_tier(self, tier: CompanionTier) -> List[Dict[str, Any]]:
        """Get all companions for a specific tier"""
        tier_companions = [
            asdict(companion) for companion in self.companions.values()
            if companion.tier == tier and companion.is_active
        ]
        
        # Sort by popularity score
        return sorted(tier_companions, key=lambda x: x['popularity_score'], reverse=True)
    
    def get_user_accessible_companions(self, user_id: str, subscription_tier: str, 
                                     referral_points: int = 0, achievements: List[str] = None) -> Dict[str, List[Dict]]:
        """Get companions accessible to user based on their tier and achievements"""
        achievements = achievements or []
        
        accessible_companions = {
            'free': [],
            'growth': [],
            'max': [],
            'referral': [],
            'locked': []
        }
        
        for companion in self.companions.values():
            if not companion.is_active:
                continue
                
            companion_dict = asdict(companion)
            
            # Check access based on companion tier
            has_access = False
            
            if companion.tier == CompanionTier.FREE:
                has_access = True
            elif companion.tier == CompanionTier.GROWTH:
                has_access = subscription_tier in ['growth', 'max']
            elif companion.tier == CompanionTier.MAX:
                has_access = subscription_tier == 'max'
            elif companion.tier == CompanionTier.REFERRAL:
                required_points = companion.unlock_requirements.get('referral_points', 0)
                has_access = referral_points >= required_points
            
            # Add to appropriate section
            if has_access:
                accessible_companions[companion.tier.value].append(companion_dict)
            else:
                companion_dict['lock_reason'] = self._get_lock_reason(companion, subscription_tier, referral_points)
                accessible_companions['locked'].append(companion_dict)
        
        # Sort each section by popularity
        for section in accessible_companions:
            accessible_companions[section] = sorted(
                accessible_companions[section], 
                key=lambda x: x['popularity_score'], 
                reverse=True
            )
        
        return accessible_companions
    
    def _get_lock_reason(self, companion: Companion, user_tier: str, referral_points: int) -> str:
        """Get the reason why a companion is locked"""
        if companion.tier == CompanionTier.GROWTH:
            return "Requires Growth or Max subscription"
        elif companion.tier == CompanionTier.MAX:
            return "Requires Max subscription" 
        elif companion.tier == CompanionTier.REFERRAL:
            required_points = companion.unlock_requirements.get('referral_points', 0)
            return f"Requires {required_points} referral points (you have {referral_points})"
        return "Locked"
    
    def select_companion(self, user_id: str, companion_id: str, subscription_tier: str, 
                        referral_points: int = 0) -> Dict[str, Any]:
        """Select a companion for the user"""
        if companion_id not in self.companions:
            return {"success": False, "error": "Companion not found"}
        
        companion = self.companions[companion_id]
        
        # Check if user has access
        accessible = self.get_user_accessible_companions(user_id, subscription_tier, referral_points)
        all_accessible = (accessible['free'] + accessible['growth'] + 
                         accessible['max'] + accessible['referral'])
        
        accessible_ids = [comp['companion_id'] for comp in all_accessible]
        
        if companion_id not in accessible_ids:
            return {
                "success": False, 
                "error": "Companion not accessible with current subscription",
                "upgrade_required": True,
                "companion": asdict(companion)
            }
        
        # Update user's selection
        self.user_access[user_id] = UserCompanionAccess(
            user_id=user_id,
            selected_companion_id=companion_id,
            unlocked_companions=accessible_ids,
            subscription_tier=subscription_tier,
            referral_points=referral_points,
            achievements_unlocked=[],
            last_companion_change=datetime.now(),
            trial_companions_used=[]
        )
        
        return {
            "success": True,
            "companion": asdict(companion),
            "message": f"Successfully selected {companion.display_name}"
        }
    
    def get_popular_companions(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get most popular companions across all tiers"""
        popular = sorted(
            [asdict(comp) for comp in self.companions.values() if comp.is_active],
            key=lambda x: x['popularity_score'],
            reverse=True
        )[:limit]
        
        return popular
    
    def get_recommended_companions(self, user_id: str, subscription_tier: str) -> List[Dict[str, Any]]:
        """Get recommended companions for user"""
        accessible = self.get_user_accessible_companions(user_id, subscription_tier)
        all_accessible = (accessible['free'] + accessible['growth'] + 
                         accessible['max'] + accessible['referral'])
        
        recommended = [comp for comp in all_accessible if comp['is_recommended']]
        return recommended[:2]  # Top 2 recommendations
    
    def get_trial_companion(self, user_id: str, companion_id: str) -> Dict[str, Any]:
        """Allow free users to trial a premium companion for limited time"""
        if companion_id not in self.companions:
            return {"success": False, "error": "Companion not found"}
        
        companion = self.companions[companion_id]
        
        # Only allow trials for Growth tier companions
        if companion.tier != CompanionTier.GROWTH:
            return {"success": False, "error": "Trial not available for this companion"}
        
        user_access = self.user_access.get(user_id)
        if user_access and companion_id in user_access.trial_companions_used:
            return {"success": False, "error": "Trial already used for this companion"}
        
        return {
            "success": True,
            "companion": asdict(companion),
            "trial_duration": "24 hours",
            "message": f"Trial access granted for {companion.display_name}"
        }
    
    def get_companion_details(self, companion_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific companion"""
        if companion_id in self.companions:
            return asdict(self.companions[companion_id])
        return None
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get companion system statistics"""
        total_companions = len([c for c in self.companions.values() if c.is_active])
        tier_counts = defaultdict(int)
        
        for companion in self.companions.values():
            if companion.is_active:
                tier_counts[companion.tier.value] += 1
        
        return {
            "total_companions": total_companions,
            "tier_distribution": dict(tier_counts),
            "most_popular": self.get_popular_companions(1)[0] if self.companions else None,
            "total_users_with_selection": len(self.user_access)
        }