"""
SoulBridge AI - Companion Manager
Manages community avatar companions and access control
Extracted from backend/app.py with improvements
"""
import logging
from typing import Dict, Any, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class CompanionManager:
    """Manager for community companions and avatar selection"""
    
    def __init__(self):
        self.companions_data = self._load_companions_data()
        self.tier_hierarchy = ['bronze', 'silver', 'gold']
        self.referral_thresholds = {
            "blayzike": 2,
            "blazelian": 4,
            "claude_referral": 8,
            "blayzo_skin": 10
        }
    
    def _load_companions_data(self) -> List[Dict[str, Any]]:
        """Load companions data (extracted from COMPANIONS_NEW)"""
        return [
            # Bronze tier - 10 companions
            {"id":"gamerjay_bronze","name":"GamerJay","tier":"bronze","image_url":"/static/logos/GamerJay_Free_companion.png","min_referrals":0,"greeting":"Hey there! I'm GamerJay. Ready to level up and explore some awesome features together?"},
            {"id":"blayzo_bronze","name":"Blayzo","tier":"bronze","image_url":"/static/logos/Blayzo.png","min_referrals":0,"greeting":"What's up! I'm Blayzo. Let's vibe and see what cool stuff we can discover together!"},
            {"id":"blayzica_bronze","name":"Blayzica","tier":"bronze","image_url":"/static/logos/Blayzica.png","min_referrals":0,"greeting":"Hello! I'm Blayzica. I'm here to help you explore and make the most of your SoulBridge experience!"},
            {"id":"claude_bronze","name":"Claude","tier":"bronze","image_url":"/static/logos/Claude_Free.png","min_referrals":0,"greeting":"Greetings! I'm Claude. I'm excited to help you explore the world of artificial intelligence and beyond!"},
            {"id":"blayzia_bronze","name":"Blayzia","tier":"bronze","image_url":"/static/logos/Blayzia.png","min_referrals":0,"greeting":"Hey! I'm Blayzia. Ready to dive into some amazing features and have fun together?"},
            {"id":"blayzion_bronze","name":"Blayzion","tier":"bronze","image_url":"/static/logos/Blayzion.png","min_referrals":0,"greeting":"Yo! I'm Blayzion. Let's embark on this journey and unlock some cool features together!"},
            {"id":"lumen_bronze","name":"Lumen","tier":"bronze","image_url":"/static/logos/Lumen_Bronze.png","min_referrals":0,"greeting":"Hello there! I'm Lumen. I'm here to brighten your SoulBridge experience and guide you through our features!"},
            {"id":"blayzo2_bronze","name":"Blayzo.2","tier":"bronze","image_url":"/static/logos/blayzo_free_tier.png","min_referrals":0,"greeting":"Hey! I'm Blayzo.2. Ready to explore the next level of features together?"},
            {"id":"crimson_bronze","name":"Crimson","tier":"bronze","image_url":"/static/logos/Crimson_Free.png","min_referrals":0,"greeting":"Hey! I'm Crimson. I bring passion and determination to help you tackle challenges head-on!"},
            {"id":"violet_bronze","name":"Violet","tier":"bronze","image_url":"/static/logos/Violet_Free.png","min_referrals":0,"greeting":"Hello! I'm Violet. I see the creative beauty in every moment and I'm here to inspire your journey!"},
            
            # Silver tier - 8 companions
            {"id":"gamerjay_silver","name":"GamerJay.2","tier":"silver","image_url":"/static/logos/GamerJay_premium_companion.png","min_referrals":0,"greeting":"What's up! I'm GamerJay.2. Time to unlock the next level of features and dominate together!"},
            {"id":"blayzo_silver","name":"Blayzo.3","tier":"silver","image_url":"/static/logos/Blayzo_premium_companion.png","min_referrals":0,"greeting":"Hey! I'm Blayzo.3. Ready to take your experience to the premium level?"},
            {"id":"blayzica_silver","name":"Blayzica.2","tier":"silver","image_url":"/static/logos/Blayzica_Pro.png","min_referrals":0,"greeting":"Hi there! I'm Blayzica.2. Let's explore the enhanced features together!"},
            {"id":"claude_silver","name":"Claude.3","tier":"silver","image_url":"/static/logos/Claude_Growth.png","min_referrals":0,"greeting":"Welcome! I'm Claude.3. With expanded capabilities, I'm ready to help you achieve more!"},
            {"id":"sky_silver","name":"Sky","tier":"silver","image_url":"/static/logos/Sky_a_premium_companion.png","min_referrals":0,"greeting":"Hello! I'm Sky. Ready to soar to new heights with your Silver experience?"},
            {"id":"lumen_silver","name":"Lumen.2","tier":"silver","image_url":"/static/logos/Lumen_Silver.png","min_referrals":0,"greeting":"Welcome! I'm Lumen.2. Let me illuminate your path to premium features and capabilities."},
            {"id":"rozia_silver","name":"Rozia","tier":"silver","image_url":"/static/logos/Rozia_Silver.png","min_referrals":0,"greeting":"Hello! I'm Rozia. Ready for an elegant Silver-tier experience!"},
            {"id":"watchdog_silver","name":"WatchDog","tier":"silver","image_url":"/static/logos/WatchDog_a_Premium_companion.png","min_referrals":0,"greeting":"Hello! I'm WatchDog. I'll keep watch over your Silver experience!"},
            
            # Gold tier - 8 companions
            {"id":"crimson_gold","name":"Crimson.2","tier":"gold","image_url":"/static/logos/Crimson_a_Max_companion.png","min_referrals":0,"greeting":"Welcome, I'm Crimson.2. You have access to unlimited features and the full power of SoulBridge AI!"},
            {"id":"violet_gold","name":"Violet.2","tier":"gold","image_url":"/static/logos/Violet_a_Max_companion.png","min_referrals":0,"greeting":"Greetings! I'm Violet.2. Together we'll explore unlimited possibilities and exclusive features!"},
            {"id":"claude_gold","name":"Claude.2","tier":"gold","image_url":"/static/logos/Claude_Max.png","min_referrals":0,"greeting":"Hello! I'm Claude.2. With unlimited access to all features, let's achieve extraordinary things together!"},
            {"id":"royal_gold","name":"Royal","tier":"gold","image_url":"/static/logos/Royal_a_Max_companion.png","min_referrals":0,"greeting":"Greetings! I'm Royal. Experience the pinnacle of AI companionship with unlimited possibilities."},
            {"id":"ven_blayzica_gold","name":"Ven Blayzica","tier":"gold","image_url":"/static/logos/Ven_Blayzica_a_Max_companion.png","min_referrals":0,"greeting":"Hello! I'm Ven Blayzica. Let's venture into the ultimate SoulBridge experience together."},
            {"id":"ven_sky_gold","name":"Ven Sky","tier":"gold","image_url":"/static/logos/Ven_Sky_a_Max_companion.png","min_referrals":0,"greeting":"Welcome! I'm Ven Sky. Together we'll soar beyond limits with unlimited premium access."},
            {"id":"watchdog_gold","name":"WatchDog.2","tier":"gold","image_url":"/static/logos/WatchDog_a_Max_Companion.png","min_referrals":0,"greeting":"Greetings! I'm WatchDog.2. I'll safeguard your unlimited access and guide you through premium features."},
            {"id":"dr_madjay_gold","name":"Dr. MadJay","tier":"gold","image_url": "/static/logos/Dr. MadJay.png","min_referrals":0,"greeting":"Greetings! I'm Dr. MadJay. Let's explore the cutting-edge possibilities of unlimited AI access."},
            
            # Referral-locked companions
            {"id":"blayzike","name":"Blayzike","tier":"silver","image_url":"/static/referral/blayzike.png","min_referrals":2},
            {"id":"blazelian","name":"Blazelian","tier":"gold","image_url":"/static/referral/blazelian.png","min_referrals":4},
            {"id":"nyxara","name":"Nyxara","tier":"silver","image_url":"/static/logos/Nyxara.png","min_referrals":6},
            {"id":"claude_referral","name":"Claude Referral","tier":"gold","image_url":"/static/referral/claude_referral.png","min_referrals":8},
            {"id":"blayzo_referral","name":"Blayzo Referral","tier":"gold","image_url":"/static/logos/Blayzo_Referral.png","min_referrals":10},
        ]
    
    def get_companions_by_id(self) -> Dict[str, Dict[str, Any]]:
        """Get companions indexed by ID"""
        return {c["id"]: c for c in self.companions_data}
    
    def can_user_access_companion(self, user_plan: str, trial_active: bool, 
                                 referrals: int, companion_id: str) -> bool:
        """Check if user can access a specific companion"""
        try:
            companion = next((c for c in self.companions_data if c["id"] == companion_id), None)
            if not companion:
                return False
            
            return self._check_companion_access(user_plan, trial_active, referrals, companion)
            
        except Exception as e:
            logger.error(f"Failed to check companion access: {e}")
            return False
    
    def _check_companion_access(self, user_plan: str, trial_active: bool, 
                              referrals: int, companion: Dict[str, Any]) -> bool:
        """Internal method to check companion access"""
        try:
            companion_tier = companion["tier"]
            min_referrals = companion.get("min_referrals", 0)
            
            # Check referral requirements first
            if min_referrals > 0 and referrals < min_referrals:
                return False
            
            # Determine effective plan (trial gives Gold access for companions)
            if trial_active and user_plan == 'bronze':
                effective_plan = 'gold'
            else:
                effective_plan = user_plan
            
            # Check tier access
            user_tier_level = self._get_tier_level(effective_plan)
            companion_tier_level = self._get_tier_level(companion_tier)
            
            return user_tier_level >= companion_tier_level
            
        except Exception as e:
            logger.error(f"Failed to check companion access: {e}")
            return False
    
    def _get_tier_level(self, tier: str) -> int:
        """Get numerical level for tier comparison"""
        try:
            return self.tier_hierarchy.index(tier.lower())
        except ValueError:
            return 0  # Default to bronze level
    
    def get_available_companions(self, user_plan: str, trial_active: bool, 
                                referrals: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available companions organized by category"""
        try:
            categorized_companions = {
                'bronze': [],
                'silver': [], 
                'gold': [],
                'referral': []
            }
            
            for companion in self.companions_data:
                can_access = self._check_companion_access(
                    user_plan, trial_active, referrals, companion
                )
                
                companion_data = {
                    'id': companion['id'],
                    'name': companion['name'],
                    'tier': companion['tier'],
                    'image_url': companion['image_url'],
                    'greeting': companion.get('greeting', ''),
                    'min_referrals': companion.get('min_referrals', 0),
                    'locked': not can_access,
                    'lock_reason': self._get_lock_reason(user_plan, trial_active, referrals, companion)
                }
                
                # Categorize companion
                if companion.get('min_referrals', 0) > 0:
                    categorized_companions['referral'].append(companion_data)
                else:
                    tier = companion['tier']
                    if tier in categorized_companions:
                        categorized_companions[tier].append(companion_data)
            
            # Sort companions within each category
            for category in categorized_companions:
                categorized_companions[category].sort(key=lambda x: x['name'])
            
            return categorized_companions
            
        except Exception as e:
            logger.error(f"Failed to get available companions: {e}")
            return {'bronze': [], 'silver': [], 'gold': [], 'referral': []}
    
    def get_community_companions(self, user_plan: str, trial_active: bool, 
                               referrals: int) -> List[Dict[str, Any]]:
        """Get companions available for community avatar selection"""
        try:
            companions = []
            
            for companion in self.companions_data:
                can_access = self._check_companion_access(
                    user_plan, trial_active, referrals, companion
                )
                
                companion_data = {
                    'slug': companion['id'],  # Use 'id' as 'slug' for template compatibility
                    'name': companion['name'],
                    'tier': companion['tier'],
                    'image_url': companion['image_url'],
                    'locked': not can_access,
                    'lock_reason': self._get_lock_reason(user_plan, trial_active, referrals, companion),
                    'min_referrals': companion.get('min_referrals', 0)
                }
                
                companions.append(companion_data)
            
            # Sort by tier and then by name
            companions.sort(key=lambda x: (self._get_tier_level(x['tier']), x['name']))
            
            logger.info(f"👥 Retrieved {len(companions)} community companions for user plan: {user_plan}")
            
            return companions
            
        except Exception as e:
            logger.error(f"Failed to get community companions: {e}")
            return []
    
    def _get_lock_reason(self, user_plan: str, trial_active: bool, 
                        referrals: int, companion: Dict[str, Any]) -> str:
        """Get reason why companion is locked"""
        try:
            min_referrals = companion.get('min_referrals', 0)
            companion_tier = companion['tier']
            
            # Check referral requirements - referral companions ALWAYS show referral requirements
            if min_referrals > 0:
                return f"Requires {min_referrals} referrals"
            
            # Check tier requirements (only for non-referral companions)
            effective_plan = 'gold' if (trial_active and user_plan == 'bronze') else user_plan
            
            if companion_tier == 'silver' and effective_plan == 'bronze':
                return "Requires Silver upgrade"
            elif companion_tier == 'gold' and effective_plan in ['bronze', 'silver']:
                return "Requires Gold upgrade"
            
            return ""
            
        except Exception as e:
            logger.error(f"Failed to get lock reason: {e}")
            return "Access restricted"
    
    def get_companion_by_id(self, companion_id: str) -> Optional[Dict[str, Any]]:
        """Get companion data by ID"""
        try:
            return next((c for c in self.companions_data if c["id"] == companion_id), None)
        except Exception as e:
            logger.error(f"Failed to get companion by ID: {e}")
            return None
    
    def get_companion_tier(self, companion_id: str) -> str:
        """Get companion's tier"""
        try:
            companion = self.get_companion_by_id(companion_id)
            return companion['tier'] if companion else 'bronze'
        except Exception as e:
            logger.error(f"Failed to get companion tier: {e}")
            return 'bronze'
    
    def validate_companion_selection(self, user_plan: str, trial_active: bool,
                                   referrals: int, companion_id: str) -> Dict[str, Any]:
        """Validate a companion selection for avatar setting"""
        try:
            companion = self.get_companion_by_id(companion_id)
            
            if not companion:
                return {
                    'valid': False,
                    'error': 'Companion not found'
                }
            
            can_access = self._check_companion_access(
                user_plan, trial_active, referrals, companion
            )
            
            if not can_access:
                lock_reason = self._get_lock_reason(user_plan, trial_active, referrals, companion)
                return {
                    'valid': False,
                    'error': f'Cannot access companion: {lock_reason}'
                }
            
            return {
                'valid': True,
                'companion': companion
            }
            
        except Exception as e:
            logger.error(f"Failed to validate companion selection: {e}")
            return {
                'valid': False,
                'error': 'Validation failed'
            }
    
    def get_companion_stats(self) -> Dict[str, Any]:
        """Get statistics about companions"""
        try:
            stats = {
                'total_companions': len(self.companions_data),
                'by_tier': {},
                'referral_companions': 0,
                'free_companions': 0
            }
            
            for companion in self.companions_data:
                tier = companion['tier']
                min_referrals = companion.get('min_referrals', 0)
                
                # Count by tier
                stats['by_tier'][tier] = stats['by_tier'].get(tier, 0) + 1
                
                # Count referral vs free
                if min_referrals > 0:
                    stats['referral_companions'] += 1
                else:
                    stats['free_companions'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get companion stats: {e}")
            return {}
    
    def search_companions(self, query: str, user_plan: str = None, 
                         trial_active: bool = False, referrals: int = 0) -> List[Dict[str, Any]]:
        """Search companions by name or tier"""
        try:
            if not query.strip():
                return []
            
            query_lower = query.lower().strip()
            matching_companions = []
            
            for companion in self.companions_data:
                # Search in name and tier
                name_match = query_lower in companion['name'].lower()
                tier_match = query_lower in companion['tier'].lower()
                
                if name_match or tier_match:
                    companion_data = companion.copy()
                    
                    # Add access info if user info provided
                    if user_plan is not None:
                        can_access = self._check_companion_access(
                            user_plan, trial_active, referrals, companion
                        )
                        companion_data['locked'] = not can_access
                        companion_data['lock_reason'] = self._get_lock_reason(
                            user_plan, trial_active, referrals, companion
                        )
                    
                    matching_companions.append(companion_data)
            
            # Sort by tier and name
            matching_companions.sort(key=lambda x: (self._get_tier_level(x['tier']), x['name']))
            
            return matching_companions
            
        except Exception as e:
            logger.error(f"Failed to search companions: {e}")
            return []