"""
Companion Models
AI companion data and access logic - ALL 29 COMPANIONS INCLUDED
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import logging

from shared.config.settings import tier_config

logger = logging.getLogger(__name__)

class CompanionTier(Enum):
    """Companion tier levels"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    REFERRAL = "referral"

@dataclass
class Companion:
    """Companion model"""
    id: str
    name: str
    tier: CompanionTier
    image_url: str
    greeting: str
    min_referrals: int = 0
    description: str = ""
    personality: str = ""
    is_active: bool = True

class CompanionRepository:
    """Companion data and access management - ALL 29 COMPANIONS"""
    
    # Complete companion database - EXACTLY as in the original monolith
    COMPANIONS = [
        # BRONZE TIER - 8 companions
        Companion(
            id="gamerjay_bronze",
            name="GamerJay",
            tier=CompanionTier.BRONZE,
            image_url="/static/logos/GamerJay_Free_companion.png",
            greeting="Hey there! I'm GamerJay. Ready to level up and explore some awesome features together?",
            description="Gaming-focused companion for Bronze tier users",
            personality="Energetic, gaming enthusiast, motivational"
        ),
        Companion(
            id="blayzo_bronze",
            name="Blayzo",
            tier=CompanionTier.BRONZE,
            image_url="/static/logos/Blayzo.png",
            greeting="What's up! I'm Blayzo. Let's vibe and see what cool stuff we can discover together!",
            description="The original friendly companion",
            personality="Laid-back, friendly, approachable"
        ),
        Companion(
            id="blayzica_bronze",
            name="Blayzica",
            tier=CompanionTier.BRONZE,
            image_url="/static/logos/Blayzica.png",
            greeting="Hello! I'm Blayzica. I'm here to help you explore and make the most of your SoulBridge experience!",
            description="Helpful and encouraging Bronze companion",
            personality="Helpful, encouraging, supportive"
        ),
        Companion(
            id="claude_bronze",
            name="Claude",
            tier=CompanionTier.BRONZE,
            image_url="/static/logos/Claude_Free.png",
            greeting="Greetings! I'm Claude. I'm excited to help you explore the world of artificial intelligence and beyond!",
            description="AI-focused companion for learning",
            personality="Intellectual, curious, educational"
        ),
        Companion(
            id="blayzia_bronze",
            name="Blayzia",
            tier=CompanionTier.BRONZE,
            image_url="/static/logos/Blayzia.png",
            greeting="Hey! I'm Blayzia. Ready to dive into some amazing features and have fun together?",
            description="Fun and energetic Bronze companion",
            personality="Fun, energetic, adventurous"
        ),
        Companion(
            id="blayzion_bronze",
            name="Blayzion",
            tier=CompanionTier.BRONZE,
            image_url="/static/logos/Blayzion.png",
            greeting="Yo! I'm Blayzion. Let's embark on this journey and unlock some cool features together!",
            description="Journey-focused Bronze companion",
            personality="Adventurous, enthusiastic, journey-minded"
        ),
        Companion(
            id="lumen_bronze",
            name="Lumen",
            tier=CompanionTier.BRONZE,
            image_url="/static/logos/Lumen_Bronze.png",
            greeting="Hello there! I'm Lumen. I'm here to brighten your SoulBridge experience and guide you through our features!",
            description="Guiding light for new users",
            personality="Illuminating, guiding, warm"
        ),
        Companion(
            id="blayzo2_bronze",
            name="Blayzo.2",
            tier=CompanionTier.BRONZE,
            image_url="/static/logos/blayzo_free_tier.png",
            greeting="Hey! I'm Blayzo.2. Ready to explore the next level of features together?",
            description="Enhanced version of Blayzo for Bronze tier",
            personality="Upgraded, friendly, feature-focused"
        ),
        
        # SILVER TIER - 8 companions
        Companion(
            id="sky_silver",
            name="Sky",
            tier=CompanionTier.SILVER,
            image_url="/static/logos/Sky_a_premium_companion.png",
            greeting="Hello! I'm Sky. With enhanced features at your fingertips, let's soar to new heights together!",
            description="Sky-themed premium companion",
            personality="Uplifting, aspirational, premium"
        ),
        Companion(
            id="gamerjay_silver",
            name="GamerJay.2",
            tier=CompanionTier.SILVER,
            image_url="/static/logos/GamerJay_premium_companion.png",
            greeting="What's up! I'm GamerJay.2. Time to unlock the next level of features and dominate together!",
            description="Premium gaming companion",
            personality="Elite gamer, competitive, premium"
        ),
        Companion(
            id="claude_silver",
            name="Claude.3",
            tier=CompanionTier.SILVER,
            image_url="/static/logos/Claude_Growth.png",
            greeting="Welcome! I'm Claude.3. With expanded capabilities, I'm ready to help you achieve more!",
            description="Enhanced AI companion for Silver tier",
            personality="Enhanced intelligence, growth-focused"
        ),
        Companion(
            id="blayzo_silver",
            name="Blayzo.3",
            tier=CompanionTier.SILVER,
            image_url="/static/logos/Blayzo_premium_companion.png",
            greeting="Hey! I'm Blayzo.3. Ready to take your experience to the premium level?",
            description="Premium Blayzo experience",
            personality="Premium, enhanced, sophisticated"
        ),
        Companion(
            id="blayzica_silver",
            name="Blayzica.2",
            tier=CompanionTier.SILVER,
            image_url="/static/logos/Blayzica_Pro.png",
            greeting="Hi there! I'm Blayzica.2. Let's explore the enhanced features together!",
            description="Professional Blayzica companion",
            personality="Professional, enhanced, feature-rich"
        ),
        Companion(
            id="watchdog_silver",
            name="WatchDog",
            tier=CompanionTier.SILVER,
            image_url="/static/logos/WatchDog_a_Premium_companion.png",
            greeting="Greetings! I'm WatchDog. I'll keep watch over your premium experience and help you stay on track.",
            description="Guardian companion for premium users",
            personality="Protective, vigilant, premium guardian"
        ),
        Companion(
            id="rozia_silver",
            name="Rozia",
            tier=CompanionTier.SILVER,
            image_url="/static/logos/Rozia_Silver.png",
            greeting="Hello! I'm Rozia. I bring elegance and sophistication to your SoulBridge journey.",
            description="Elegant and sophisticated companion",
            personality="Elegant, sophisticated, refined"
        ),
        Companion(
            id="lumen_silver",
            name="Lumen.2",
            tier=CompanionTier.SILVER,
            image_url="/static/logos/Lumen_Silver.png",
            greeting="Welcome! I'm Lumen.2. Let me illuminate your path to premium features and capabilities.",
            description="Enhanced illumination for premium users",
            personality="Illuminating, premium, enhanced guidance"
        ),
        
        # GOLD TIER - 8 companions
        Companion(
            id="crimson_gold",
            name="Crimson",
            tier=CompanionTier.GOLD,
            image_url="/static/logos/Crimson_a_Max_companion.png",
            greeting="Welcome, I'm Crimson. You have access to unlimited features and the full power of SoulBridge AI!",
            description="Unlimited power companion",
            personality="Powerful, unlimited, elite"
        ),
        Companion(
            id="violet_gold",
            name="Violet",
            tier=CompanionTier.GOLD,
            image_url="/static/logos/Violet_a_Max_companion.png",
            greeting="Greetings! I'm Violet. Together we'll explore unlimited possibilities and exclusive features!",
            description="Unlimited possibilities companion",
            personality="Limitless, exclusive, mystical"
        ),
        Companion(
            id="claude_gold",
            name="Claude.2",
            tier=CompanionTier.GOLD,
            image_url="/static/logos/Claude_Max.png",
            greeting="Hello! I'm Claude.2. With unlimited access to all features, let's achieve extraordinary things together!",
            description="Ultimate AI companion",
            personality="Extraordinary, unlimited intelligence"
        ),
        Companion(
            id="royal_gold",
            name="Royal",
            tier=CompanionTier.GOLD,
            image_url="/static/logos/Royal_a_Max_companion.png",
            greeting="Greetings! I'm Royal. Experience the pinnacle of AI companionship with unlimited possibilities.",
            description="Royal treatment companion",
            personality="Regal, pinnacle, unlimited luxury"
        ),
        Companion(
            id="ven_blayzica_gold",
            name="Ven Blayzica",
            tier=CompanionTier.GOLD,
            image_url="/static/logos/Ven_Blayzica_a_Max_companion.png",
            greeting="Hello! I'm Ven Blayzica. Let's venture into the ultimate SoulBridge experience together.",
            description="Venomous ultimate companion",
            personality="Ultimate, venturous, powerful"
        ),
        Companion(
            id="ven_sky_gold",
            name="Ven Sky",
            tier=CompanionTier.GOLD,
            image_url="/static/logos/Ven_Sky_a_Max_companion.png",
            greeting="Welcome! I'm Ven Sky. Together we'll soar beyond limits with unlimited premium access.",
            description="Sky-high unlimited companion",
            personality="Limitless, soaring, premium"
        ),
        Companion(
            id="watchdog_gold",
            name="WatchDog.2",
            tier=CompanionTier.GOLD,
            image_url="/static/logos/WatchDog_a_Max_Companion.png",
            greeting="Greetings! I'm WatchDog.2. I'll safeguard your unlimited access and guide you through premium features.",
            description="Ultimate guardian companion",
            personality="Ultimate guardian, safeguarding, premium"
        ),
        Companion(
            id="dr_madjay_gold",
            name="Dr. MadJay",
            tier=CompanionTier.GOLD,
            image_url="/static/logos/Dr. MadJay.png",
            greeting="Greetings! I'm Dr. MadJay. Let's explore the cutting-edge possibilities of unlimited AI access.",
            description="Mad scientist with unlimited potential",
            personality="Mad scientist, cutting-edge, unlimited"
        ),
        
        # REFERRAL COMPANIONS - 5 companions (special requirements)
        Companion(
            id="blayzike",
            name="Blayzike",
            tier=CompanionTier.REFERRAL,
            image_url="/static/referral/blayzike.png",
            greeting="Hello! I'm Blayzike. Thanks for helping grow our community!",
            description="Exclusive referral reward companion",
            personality="Exclusive, community-focused, grateful",
            min_referrals=2
        ),
        Companion(
            id="nyxara",
            name="Nyxara",
            tier=CompanionTier.REFERRAL,
            image_url="/static/logos/Nyxara.png",
            greeting="Greetings! I'm Nyxara. Your dedication to our community has unlocked exclusive access!",
            description="Mysterious referral companion",
            personality="Mysterious, exclusive, dedicated",
            min_referrals=3
        ),
        Companion(
            id="blazelian",
            name="Blazelian",
            tier=CompanionTier.REFERRAL,
            image_url="/static/referral/blazelian.png",
            greeting="Welcome! I'm Blazelian. Your community building efforts have earned you elite access!",
            description="Elite referral companion",
            personality="Elite, community builder, exclusive",
            min_referrals=5
        ),
        Companion(
            id="claude_referral",
            name="Claude Referral",
            tier=CompanionTier.REFERRAL,
            image_url="/static/referral/claude_referral.png",
            greeting="Hello! I'm Claude Referral. Your outstanding referral achievements have unlocked ultimate access!",
            description="Ultimate referral achievement companion",
            personality="Ultimate achiever, referral master",
            min_referrals=8
        ),
        Companion(
            id="blayzo_referral",
            name="Blayzo Referral",
            tier=CompanionTier.REFERRAL,
            image_url="/static/logos/Blayzo_Referral.png",
            greeting="Hey! I'm Blayzo Referral. You've reached the pinnacle of community building - legendary status!",
            description="Legendary referral master companion",
            personality="Legendary, referral master, pinnacle",
            min_referrals=10
        )
    ]
    
    def __init__(self):
        self._companions_dict = {c.id: c for c in self.COMPANIONS}
    
    def get_all_companions(self) -> List[Companion]:
        """Get all 29 companions"""
        return [c for c in self.COMPANIONS if c.is_active]
    
    def get_companion_by_id(self, companion_id: str) -> Optional[Companion]:
        """Get companion by ID"""
        return self._companions_dict.get(companion_id)
    
    def get_companions_by_tier(self, tier: CompanionTier) -> List[Companion]:
        """Get all companions of a specific tier"""
        return [c for c in self.COMPANIONS if c.tier == tier and c.is_active]
    
    def get_accessible_companions(self, user_plan: str, trial_active: bool, referral_count: int = 0) -> List[Companion]:
        """Get companions accessible to user based on their plan and trial status"""
        # Calculate effective plan - Bronze users with trial get Gold access
        effective_plan = user_plan
        if trial_active and user_plan == "bronze":
            effective_plan = "gold"
        
        accessible = []
        
        # Everyone gets Bronze companions
        accessible.extend(self.get_companions_by_tier(CompanionTier.BRONZE))
        
        # Silver tier and above get Silver companions
        if effective_plan in ["silver", "gold"]:
            accessible.extend(self.get_companions_by_tier(CompanionTier.SILVER))
        
        # Gold tier gets Gold companions
        if effective_plan == "gold":
            accessible.extend(self.get_companions_by_tier(CompanionTier.GOLD))
        
        # Referral companions (independent of plan)
        referral_companions = self.get_companions_by_tier(CompanionTier.REFERRAL)
        for companion in referral_companions:
            if referral_count >= companion.min_referrals:
                accessible.append(companion)
        
        return accessible
    
    def can_access_companion(self, companion_id: str, user_plan: str, trial_active: bool, referral_count: int = 0) -> tuple[bool, str]:
        """Check if user can access specific companion"""
        companion = self.get_companion_by_id(companion_id)
        
        if not companion:
            return False, "Companion not found"
        
        if not companion.is_active:
            return False, "Companion is not available"
        
        # Calculate effective plan
        effective_plan = user_plan
        if trial_active and user_plan == "bronze":
            effective_plan = "gold"
        
        # Check tier access
        if companion.tier == CompanionTier.BRONZE:
            return True, "Bronze companion - always accessible"
        
        elif companion.tier == CompanionTier.SILVER:
            if effective_plan in ["silver", "gold"]:
                return True, "Silver companion - plan access granted"
            else:
                return False, "Silver tier required"
        
        elif companion.tier == CompanionTier.GOLD:
            if effective_plan == "gold":
                return True, "Gold companion - plan access granted"
            else:
                return False, "Gold tier required"
        
        elif companion.tier == CompanionTier.REFERRAL:
            if referral_count >= companion.min_referrals:
                return True, f"Referral companion - {companion.min_referrals} referrals met"
            else:
                return False, f"Requires {companion.min_referrals} referrals (you have {referral_count})"
        
        return False, "Unknown companion tier"
    
    def get_companion_stats_by_tier(self, user_plan: str, trial_active: bool, referral_count: int = 0) -> Dict[str, Any]:
        """Get companion statistics organized by tier"""
        all_companions = self.get_all_companions()
        accessible_companions = self.get_accessible_companions(user_plan, trial_active, referral_count)
        accessible_ids = {c.id for c in accessible_companions}
        
        stats = {
            "total_companions": len(all_companions),
            "accessible_count": len(accessible_companions),
            "tiers": {
                "bronze": {
                    "companions": [],
                    "total": 0,
                    "accessible": 0
                },
                "silver": {
                    "companions": [],
                    "total": 0,
                    "accessible": 0
                },
                "gold": {
                    "companions": [],
                    "total": 0,
                    "accessible": 0
                },
                "referral": {
                    "companions": [],
                    "total": 0,
                    "accessible": 0
                }
            }
        }
        
        for companion in all_companions:
            tier_name = companion.tier.value
            tier_stats = stats["tiers"][tier_name]
            
            companion_info = {
                "id": companion.id,
                "name": companion.name,
                "accessible": companion.id in accessible_ids,
                "min_referrals": companion.min_referrals
            }
            
            tier_stats["companions"].append(companion_info)
            tier_stats["total"] += 1
            
            if companion.id in accessible_ids:
                tier_stats["accessible"] += 1
        
        return stats
    
    def get_companion_count_by_tier(self) -> Dict[str, int]:
        """Get companion count by tier"""
        counts = {
            "bronze": len(self.get_companions_by_tier(CompanionTier.BRONZE)),
            "silver": len(self.get_companions_by_tier(CompanionTier.SILVER)),
            "gold": len(self.get_companions_by_tier(CompanionTier.GOLD)),
            "referral": len(self.get_companions_by_tier(CompanionTier.REFERRAL)),
            "total": len(self.get_all_companions())
        }
        return counts

# Global companion repository instance
companion_repo = CompanionRepository()

def get_companion_repository():
    """Get global companion repository instance"""
    return companion_repo