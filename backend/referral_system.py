# Referral System with Exclusive Companion Rewards
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import json


class ReferralManager:
    def __init__(self):
        self.referral_rewards = {
            "referrer": {
                2: {
                    "type": "exclusive_companion",
                    "value": "Blayzike",
                    "description": "Unlock Blayzike companion",
                },
                4: {
                    "type": "exclusive_companion",
                    "value": "Blazelian",
                    "description": "Unlock Blazelian companion",
                },
                6: {
                    "type": "special_skin",
                    "value": "Blayzo_Referral",
                    "description": "Unlock Blayzo special referral skin",
                },
            },
            "referee": {
                "signup": {
                    "type": "welcome_bonus",
                    "value": "none",
                    "description": "Welcome to SoulBridge AI!",
                }
            },
        }

        # Exclusive companion details
        self.exclusive_companions = {
            "Blayzike": {
                "name": "Blayzike",
                "unlock_requirement": 2,
                "description": "A mysterious companion with enigmatic charm, unlocked through sharing SoulBridge AI",
                "greeting": '"Hello there! I\'m Blayzike, your enigmatic companion. Ready to explore the mysteries together?" 🌟',
                "personality": "Mysterious, charming, with an air of intrigue",
                "color": "#8b5cf6",  # Purple theme
                "rarity": "rare",
                "exclusive": True,
                "referral_only": True,
            },
            "Blazelian": {
                "name": "Blazelian",
                "unlock_requirement": 4,
                "description": "An ethereal companion with celestial wisdom, available only to dedicated referrers",
                "greeting": '"Greetings, seeker. I am Blazelian, guardian of celestial knowledge. Let us journey among the stars." ✨',
                "personality": "Ethereal, wise, celestial being with otherworldly knowledge",
                "color": "#06b6d4",  # Cyan theme
                "rarity": "epic",
                "exclusive": True,
                "referral_only": True,
            },
            "Blayzo_Referral": {
                "name": "Blayzo (Referral Special)",
                "unlock_requirement": 6,
                "description": "A special referral skin for Blayzo with unique appearance and exclusive abilities",
                "greeting": '"Yo! Check out my special referral look! Thanks for sharing SoulBridge AI with everyone!" 🎉',
                "personality": "Energetic, grateful, with special referral powers",
                "color": "#f59e0b",  # Gold theme for special skin
                "rarity": "legendary",
                "exclusive": True,
                "referral_only": True,
                "is_skin": True,
                "base_character": "Blayzo",
            },
        }

    def generate_referral_code(self, user_email: str) -> str:
        """Generate unique referral code for user"""
        # Create deterministic but unique code based on email only
        # This ensures each user gets the same code every time, but each user has a unique code

        # Add a secret salt to make codes unpredictable
        salt = "SoulBridge2024_ReferralSalt_XYZ789"
        unique_string = f"{user_email}_{salt}"

        # Generate hash
        hash_obj = hashlib.sha256(unique_string.encode())
        code = hash_obj.hexdigest()[:8].upper()

        # Ensure it starts with letters for better readability
        if code[0].isdigit():
            code = "A" + code[1:]
        if code[1].isdigit():
            code = code[0] + "B" + code[2:]

        return f"SB{code}"

    def create_referral_link(
        self, user_email: str, base_url: str = None
    ) -> Dict:
        """Create referral link for user"""
        try:
            # Use default base URL if none provided
            if base_url is None:
                base_url = "https://soulbridgeai.com"
            
            referral_code = self.generate_referral_code(user_email)
            referral_link = f"{base_url}?ref={referral_code}"

            return {
                "success": True,
                "referral_code": referral_code,
                "referral_link": referral_link,
                "share_message": f"🌟 Join me on SoulBridge AI for amazing AI companion conversations! {referral_link}",
            }

        except Exception as e:
            logging.error(f"Create referral link error: {e}")
            return {"success": False, "error": str(e)}

    def process_referral_signup(
        self, referee_email: str, referral_code: str, referrer_email: str
    ) -> Dict:
        """Process new user signup with referral code"""
        try:
            # Validate referral code
            expected_code = self.generate_referral_code(referrer_email)
            if referral_code != expected_code:
                return {"success": False, "error": "Invalid referral code"}

            # Prevent self-referral
            if referee_email == referrer_email:
                return {"success": False, "error": "Cannot refer yourself"}

            # Record referral
            referral_data = {
                "referrer_email": referrer_email,
                "referee_email": referee_email,
                "referral_code": referral_code,
                "signup_date": datetime.now().isoformat(),
                "status": "completed",
                "referee_reward_claimed": False,
                "referrer_reward_claimed": False,
            }

            # In a real implementation, save to database
            logging.info(f"Referral recorded: {json.dumps(referral_data)}")

            # Give referee their welcome reward
            referee_reward = self.referral_rewards["referee"]["signup"]
            self.grant_reward(referee_email, referee_reward)

            # Update referrer's count and check for rewards
            referrer_stats = self.get_referrer_stats(referrer_email)
            new_count = referrer_stats["successful_referrals"] + 1

            # Check if referrer unlocks new rewards
            rewards_unlocked = self.check_referrer_rewards(referrer_email, new_count)

            return {
                "success": True,
                "referral_data": referral_data,
                "referee_reward": referee_reward,
                "referrer_new_count": new_count,
                "referrer_rewards_unlocked": rewards_unlocked,
            }

        except Exception as e:
            logging.error(f"Process referral signup error: {e}")
            return {"success": False, "error": str(e)}

    def get_referrer_stats(self, user_email: str) -> Dict:
        """Get referral statistics for user"""
        # In a real implementation, query from database
        # For now, return mock data
        return {
            "user_email": user_email,
            "referral_code": self.generate_referral_code(user_email),
            "successful_referrals": 0,  # This would come from database
            "pending_referrals": 0,
            "total_rewards_earned": 0,
            "exclusive_companions_unlocked": [],
            "next_reward_at": 1,
        }

    def check_referrer_rewards(
        self, user_email: str, new_referral_count: int
    ) -> List[Dict]:
        """Check and grant rewards for referrer based on new count"""
        rewards_unlocked = []

        for count, reward in self.referral_rewards["referrer"].items():
            if new_referral_count >= count:
                # Check if this is a new unlock
                previous_count = new_referral_count - 1
                if previous_count < count:
                    # This is a new reward unlock!
                    self.grant_reward(user_email, reward)
                    rewards_unlocked.append(
                        {"milestone": count, "reward": reward, "newly_unlocked": True}
                    )

                    # Special handling for exclusive companion
                    if reward["type"] == "exclusive_companion":
                        companion_name = reward["value"]
                        self.unlock_exclusive_companion(user_email, companion_name)

        return rewards_unlocked

    def unlock_exclusive_companion(self, user_email: str, companion_name: str) -> Dict:
        """Unlock exclusive companion for user"""
        try:
            if companion_name not in self.exclusive_companions:
                return {"success": False, "error": "Companion not found"}

            companion_data = self.exclusive_companions[companion_name]

            # Record unlock
            unlock_data = {
                "user_email": user_email,
                "companion_name": companion_name,
                "unlock_date": datetime.now().isoformat(),
                "unlock_method": "referral_milestone",
                "companion_data": companion_data,
            }

            # In a real implementation, save to user's unlocked companions
            logging.info(f"Exclusive companion unlocked: {json.dumps(unlock_data)}")

            return {
                "success": True,
                "companion_unlocked": companion_data,
                "unlock_data": unlock_data,
            }

        except Exception as e:
            logging.error(f"Unlock exclusive companion error: {e}")
            return {"success": False, "error": str(e)}

    def grant_reward(self, user_email: str, reward: Dict) -> Dict:
        """Grant reward to user"""
        try:
            reward_data = {
                "user_email": user_email,
                "reward_type": reward["type"],
                "reward_value": reward["value"],
                "reward_description": reward["description"],
                "granted_date": datetime.now().isoformat(),
                "expiry_date": None,
            }

            # Calculate expiry for time-based rewards
            if reward["type"] in ["premium_days", "premium_months"]:
                days = (
                    reward["value"]
                    if reward["type"] == "premium_days"
                    else reward["value"] * 30
                )
                expiry_date = datetime.now() + timedelta(days=days)
                reward_data["expiry_date"] = expiry_date.isoformat()

            # In a real implementation, update user's account
            logging.info(f"Reward granted: {json.dumps(reward_data)}")

            return {"success": True, "reward_data": reward_data}

        except Exception as e:
            logging.error(f"Grant reward error: {e}")
            return {"success": False, "error": str(e)}

    def get_referral_dashboard(self, user_email: str) -> Dict:
        """Get comprehensive referral dashboard data"""
        try:
            stats = self.get_referrer_stats(user_email)
            referral_link_data = self.create_referral_link(user_email)

            # Calculate progress to next reward
            current_count = stats["successful_referrals"]
            next_milestone = None
            progress_percentage = 0

            for count in sorted(self.referral_rewards["referrer"].keys()):
                if current_count < count:
                    next_milestone = {
                        "count": count,
                        "reward": self.referral_rewards["referrer"][count],
                        "remaining": count - current_count,
                    }
                    progress_percentage = (current_count / count) * 100
                    break

            # Get unlocked exclusive companions
            unlocked_companions = []
            for companion_name, companion_data in self.exclusive_companions.items():
                if current_count >= companion_data["unlock_requirement"]:
                    unlocked_companions.append(companion_name)

            return {
                "success": True,
                "user_email": user_email,
                "stats": stats,
                "referral_link": referral_link_data.get("referral_link"),
                "referral_code": referral_link_data.get("referral_code"),
                "share_message": referral_link_data.get("share_message"),
                "next_milestone": next_milestone,
                "progress_percentage": progress_percentage,
                "exclusive_companions": self.exclusive_companions,
                "unlocked_companions": unlocked_companions,
                "all_rewards": self.referral_rewards["referrer"],
            }

        except Exception as e:
            logging.error(f"Get referral dashboard error: {e}")
            return {"success": False, "error": str(e)}

    def get_social_share_templates(self, user_email: str) -> Dict:
        """Get social media sharing templates"""
        referral_data = self.create_referral_link(user_email)
        referral_link = referral_data.get("referral_link", "")

        templates = {
            "twitter": f"🤖 I'm chatting with AI companions on @SoulBridgeAI! Join me for amazing conversations: {referral_link} #AICompanion #EmotionalSupport",
            "whatsapp": f"Hey! 😊 I found this amazing AI companion app called SoulBridge AI. The AI companions are so helpful for emotional support and just having great conversations. Want to try it? {referral_link}",
            "email": {
                "subject": "Try SoulBridge AI - Amazing AI Companions!",
                "body": f"Hi!\n\nI've been using SoulBridge AI and it's incredible! The AI companions are so helpful for emotional support, personal growth, and just having meaningful conversations.\n\nI thought you might enjoy it too:\n\n{referral_link}\n\nLet me know what you think!\n\nBest regards",
            },
            "generic": f"🌟 Join me on SoulBridge AI for amazing conversations with AI companions! {referral_link}",
        }

        return {"success": True, "templates": templates, "referral_link": referral_link}

    def validate_referral_code(self, referral_code: str) -> Dict:
        """Validate if referral code exists and get referrer info"""
        try:
            # Extract the hash part
            if not referral_code.startswith("SB") or len(referral_code) != 10:
                return {"success": False, "error": "Invalid referral code format"}

            # In a real implementation, you'd look up the code in database
            # For now, we'll assume it's valid if format is correct
            return {
                "success": True,
                "valid": True,
                "referrer_found": True,
                "bonus_description": "Join SoulBridge AI for amazing AI companion conversations!",
            }

        except Exception as e:
            logging.error(f"Validate referral code error: {e}")
            return {"success": False, "error": str(e)}


# Global instance
referral_manager = ReferralManager()
