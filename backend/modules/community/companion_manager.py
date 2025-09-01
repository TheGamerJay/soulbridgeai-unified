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
            "blazelian": 5,
            "claude_referral": 8,
            "blayzo_skin": 10
        }
    
    def _load_companions_data(self) -> List[Dict[str, Any]]:
        """Load companions data (extracted from COMPANIONS_NEW)"""
        return [
            # Bronze tier - 8 companions
            {"id":"gamerjay_bronze","name":"GamerJay","tier":"bronze","image_url":"/static/logos/GamerJay_Free_companion.png","min_referrals":0,"greeting":"Hey there! I'm GamerJay. Ready to level up and explore some awesome features together?"},
            {"id":"blayzo_bronze","name":"Blayzo","tier":"bronze","image_url":"/static/logos/Blayzo.png","min_referrals":0,"greeting":"What's up! I'm Blayzo. Let's vibe and see what cool stuff we can discover together!"},
            {"id":"blayzica_bronze","name":"Blayzica","tier":"bronze","image_url":"/static/logos/Blayzica.png","min_referrals":0,"greeting":"Hello! I'm Blayzica. I'm here to help you explore and make the most of your SoulBridge experience!"},
            {"id":"claude_bronze","name":"Claude","tier":"bronze","image_url":"/static/logos/Claude_Free.png","min_referrals":0,"greeting":"Greetings! I'm Claude. I'm excited to help you explore the world of artificial intelligence and beyond!"},
            {"id":"violet_bronze","name":"Violet","tier":"bronze","image_url":"/static/logos/Violet_Free.png","min_referrals":0,"greeting":"Hi! I'm Violet. Let's discover new possibilities and grow together on this journey!"},
            {"id":"crimson_bronze","name":"Crimson","tier":"bronze","image_url":"/static/logos/Crimson_Free.png","min_referrals":0,"greeting":"Hello! I'm Crimson. I'm here to add some energy and excitement to your SoulBridge adventure!"},
            {"id":"lumen_bronze","name":"Lumen","tier":"bronze","image_url":"/static/logos/Lumen_Bronze.png","min_referrals":0,"greeting":"Hello! I'm Lumen. Ready to illuminate your SoulBridge experience?"},
            {"id":"blayzo2_bronze","name":"Blayzo.2","tier":"bronze","image_url":"/static/logos/blayzo_free_tier.png","min_referrals":0,"greeting":"What's good! I'm Blayzo.2, the upgraded free version. Let's vibe and explore together!"},
            
            # Silver tier - 8 companions
            {"id":"gamerjay_silver","name":"GamerJay Silver","tier":"silver","image_url":"/static/logos/GamerJay_Silver.png","min_referrals":0,"greeting":"Hey there, Silver member! I'm GamerJay Silver. Ready to unlock some premium gaming experiences?"},
            {"id":"blayzo_silver","name":"Blayzo Silver","tier":"silver","image_url":"/static/logos/Blayzo_Silver.png","min_referrals":0,"greeting":"What's up, Silver! I'm Blayzo Silver. Let's dive into some exclusive content together!"},
            {"id":"blayzica_silver","name":"Blayzica Silver","tier":"silver","image_url":"/static/logos/Blayzica_Silver.png","min_referrals":0,"greeting":"Hello, Silver member! I'm Blayzica Silver. Ready to explore premium features with style?"},
            {"id":"claude_silver","name":"Claude Silver","tier":"silver","image_url":"/static/logos/Claude_Silver.png","min_referrals":0,"greeting":"Greetings, Silver member! I'm Claude Silver. Let's unlock advanced AI capabilities together!"},
            {"id":"sky_silver","name":"Sky","tier":"silver","image_url":"/static/logos/Sky_a_premium_companion.png","min_referrals":0,"greeting":"Hello! I'm Sky. Ready to soar to new heights with your Silver experience?"},
            {"id":"lumen2_silver","name":"Lumen.2","tier":"silver","image_url":"/static/logos/Lumen_Silver.png","min_referrals":0,"greeting":"Hello! I'm Lumen.2, the upgraded version. Let me illuminate your premium experience!"},
            {"id":"rozia_silver","name":"Rozia","tier":"silver","image_url":"/static/logos/Rozia_Silver.png","min_referrals":0,"greeting":"Hello! I'm Rozia. Ready for an elegant Silver-tier experience!"},
            {"id":"watchdog_silver","name":"WatchDog","tier":"silver","image_url":"/static/logos/WatchDog_a_Premium_companion.png","min_referrals":0,"greeting":"Hello! I'm WatchDog. I'll keep watch over your Silver experience!"},
            
            # Gold tier - 8 companions  
            {"id":"gamerjay_gold","name":"GamerJay Gold","tier":"gold","image_url":"/static/logos/GamerJay_Gold.png","min_referrals":0,"greeting":"Hey there, Gold member! I'm GamerJay Gold. Welcome to the ultimate gaming experience!"},
            {"id":"blayzo_gold","name":"Blayzo Gold","tier":"gold","image_url":"/static/logos/Blayzo_Gold.png","min_referrals":0,"greeting":"What's up, Gold! I'm Blayzo Gold. Let's unlock the full potential of your premium experience!"},
            {"id":"blayzica_gold","name":"Blayzica Gold","tier":"gold","image_url":"/static/logos/Blayzica_Gold.png","min_referrals":0,"greeting":"Hello, Gold member! I'm Blayzica Gold. Ready for the ultimate premium experience?"},
            {"id":"claude_gold","name":"Claude Gold","tier":"gold","image_url":"/static/logos/Claude_Gold.png","min_referrals":0,"greeting":"Greetings, Gold member! I'm Claude Gold. Let's explore unlimited AI capabilities together!"},
            {"id":"watchdog2_gold","name":"WatchDog.2","tier":"gold","image_url":"/static/logos/WatchDog_a_Max_Companion.png","min_referrals":0,"greeting":"Hello! I'm WatchDog.2, the ultimate protection companion. Ultimate security for your Gold experience!"},
            {"id":"royal_gold","name":"Royal","tier":"gold","image_url":"/static/logos/Royal_a_Max_companion.png","min_referrals":0,"greeting":"Hello! I'm Royal. Welcome to the ultimate royal Gold experience!"},
            {"id":"ven_blayzica_gold","name":"Ven Blayzica","tier":"gold","image_url":"/static/logos/Ven_Blayzica_a_Max_companion.png","min_referrals":0,"greeting":"Hello! I'm Ven Blayzica. Ready for the ultimate Ven experience?"},
            {"id":"ven_sky_gold","name":"Ven Sky","tier":"gold","image_url":"/static/logos/Ven_Sky_a_Max_companion.png","min_referrals":0,"greeting":"Hello! I'm Ven Sky. Let's reach the ultimate heights together!"},
            
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
            
            # Check referral requirements
            if min_referrals > 0 and referrals < min_referrals:
                return f"Requires {min_referrals} referrals"
            
            # Check tier requirements
            effective_plan = 'gold' if (trial_active and user_plan == 'bronze') else user_plan
            
            if companion_tier == 'silver' and effective_plan == 'bronze':
                return "Requires Silver or Gold tier"
            elif companion_tier == 'gold' and effective_plan in ['bronze', 'silver']:
                return "Requires Gold tier"
            
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