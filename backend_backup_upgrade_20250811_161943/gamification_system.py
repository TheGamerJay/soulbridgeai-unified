"""
Gamification System for SoulBridge AI
Achievement badges, user levels, milestones, and reward mechanics
"""
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class BadgeCategory(Enum):
    ENGAGEMENT = "engagement"
    WELLNESS = "wellness"
    COMMUNITY = "community"
    STREAK = "streak"
    MILESTONE = "milestone"
    SPECIAL = "special"
    SEASONAL = "seasonal"

class BadgeRarity(Enum):
    COMMON = {"name": "Common", "color": "#87CEEB", "points": 10}
    RARE = {"name": "Rare", "color": "#32CD32", "points": 25}
    EPIC = {"name": "Epic", "color": "#9370DB", "points": 50}
    LEGENDARY = {"name": "Legendary", "color": "#FFD700", "points": 100}
    MYTHIC = {"name": "Mythic", "color": "#FF6347", "points": 250}

@dataclass
class Achievement:
    """Individual achievement/badge definition"""
    badge_id: str
    name: str
    description: str
    category: BadgeCategory
    rarity: BadgeRarity
    icon: str
    requirements: Dict[str, Any]
    reward_points: int
    created_date: datetime
    is_hidden: bool = False  # Hidden until unlocked
    is_repeatable: bool = False

@dataclass 
class UserBadge:
    """User's earned badge record"""
    user_id: str
    badge_id: str
    earned_date: datetime
    progress_data: Dict[str, Any]
    times_earned: int = 1

@dataclass
class UserLevel:
    """User progression level"""
    user_id: str
    current_level: int
    total_points: int
    points_to_next_level: int
    title: str
    benefits: List[str]

class GamificationSystem:
    """Comprehensive gamification system with badges, achievements, and levels"""
    
    def __init__(self):
        self.achievements = {}
        self.user_progress = {}
        self.level_thresholds = self._define_level_system()
        self._initialize_achievements()
        
    def _define_level_system(self) -> Dict[int, Dict]:
        """Define user level progression system"""
        return {
            1: {"title": "Newcomer", "points_required": 0, "benefits": ["Basic chat access"]},
            2: {"title": "Seeker", "points_required": 100, "benefits": ["Profile customization"]},
            3: {"title": "Explorer", "points_required": 250, "benefits": ["Community access"]},
            4: {"title": "Supporter", "points_required": 500, "benefits": ["Group therapy rooms"]},
            5: {"title": "Helper", "points_required": 1000, "benefits": ["Mentor others"]},
            6: {"title": "Guardian", "points_required": 2000, "benefits": ["Create communities"]},
            7: {"title": "Sage", "points_required": 4000, "benefits": ["Advanced AI modes"]},
            8: {"title": "Luminary", "points_required": 7500, "benefits": ["Beta features"]},
            9: {"title": "Master", "points_required": 12000, "benefits": ["VIP support"]},
            10: {"title": "Transcendent", "points_required": 20000, "benefits": ["All premium features"]}
        }
    
    def _initialize_achievements(self):
        """Initialize all available achievements"""
        # Engagement Badges
        self._add_achievement("first_chat", "First Steps", "Send your first message to an AI companion", 
                            BadgeCategory.ENGAGEMENT, BadgeRarity.COMMON, "💬", {"messages_sent": 1})
        
        self._add_achievement("chatty", "Chatty", "Send 100 messages", 
                            BadgeCategory.ENGAGEMENT, BadgeRarity.RARE, "💭", {"messages_sent": 100})
        
        self._add_achievement("conversationalist", "Conversationalist", "Send 1000 messages", 
                            BadgeCategory.ENGAGEMENT, BadgeRarity.EPIC, "🗣️", {"messages_sent": 1000})
        
        # Streak Badges
        self._add_achievement("consistent", "Getting Consistent", "Maintain a 7-day check-in streak", 
                            BadgeCategory.STREAK, BadgeRarity.COMMON, "🔥", {"check_in_streak": 7})
        
        self._add_achievement("dedicated", "Dedicated Soul", "Maintain a 30-day check-in streak", 
                            BadgeCategory.STREAK, BadgeRarity.RARE, "⭐", {"check_in_streak": 30})
        
        self._add_achievement("unwavering", "Unwavering Spirit", "Maintain a 100-day check-in streak", 
                            BadgeCategory.STREAK, BadgeRarity.LEGENDARY, "👑", {"check_in_streak": 100})
        
        # Community Badges  
        self._add_achievement("community_joiner", "Community Explorer", "Join your first community", 
                            BadgeCategory.COMMUNITY, BadgeRarity.COMMON, "🏘️", {"communities_joined": 1})
        
        self._add_achievement("helpful_member", "Helpful Member", "Receive 10 likes on community posts", 
                            BadgeCategory.COMMUNITY, BadgeRarity.RARE, "👍", {"community_likes_received": 10})
        
        self._add_achievement("community_leader", "Community Leader", "Create a community with 50+ members", 
                            BadgeCategory.COMMUNITY, BadgeRarity.EPIC, "🚀", {"community_members_attracted": 50})
        
        # Wellness Badges
        self._add_achievement("wellness_warrior", "Wellness Warrior", "Complete 5 wellness challenges", 
                            BadgeCategory.WELLNESS, BadgeRarity.RARE, "🌟", {"challenges_completed": 5})
        
        self._add_achievement("mindful_soul", "Mindful Soul", "Practice meditation for 30 consecutive days", 
                            BadgeCategory.WELLNESS, BadgeRarity.EPIC, "🧘", {"meditation_streak": 30})
        
        # Milestone Badges
        self._add_achievement("first_month", "First Month", "Use SoulBridge AI for 30 days", 
                            BadgeCategory.MILESTONE, BadgeRarity.COMMON, "📅", {"days_active": 30})
        
        self._add_achievement("loyal_user", "Loyal Companion", "Use SoulBridge AI for 365 days", 
                            BadgeCategory.MILESTONE, BadgeRarity.LEGENDARY, "💎", {"days_active": 365})
        
        # Special Badges
        self._add_achievement("early_adopter", "Early Adopter", "Joined during beta phase", 
                            BadgeCategory.SPECIAL, BadgeRarity.MYTHIC, "🌅", {"joined_before": "2025-12-31"})
        
        self._add_achievement("referral_champion", "Referral Champion", "Refer 10 friends who join", 
                            BadgeCategory.SPECIAL, BadgeRarity.EPIC, "🎁", {"successful_referrals": 10})
    
    def _add_achievement(self, badge_id: str, name: str, description: str, 
                        category: BadgeCategory, rarity: BadgeRarity, icon: str, 
                        requirements: Dict[str, Any], is_hidden: bool = False, 
                        is_repeatable: bool = False):
        """Add achievement to the system"""
        achievement = Achievement(
            badge_id=badge_id,
            name=name,
            description=description,
            category=category,
            rarity=rarity,
            icon=icon,
            requirements=requirements,
            reward_points=rarity.value["points"],
            created_date=datetime.now(),
            is_hidden=is_hidden,
            is_repeatable=is_repeatable
        )
        self.achievements[badge_id] = achievement
    
    def check_achievements(self, user_id: str, activity_data: Dict[str, Any]) -> List[str]:
        """Check if user has unlocked any new achievements"""
        newly_earned = []
        
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {
                "badges": [],
                "stats": {},
                "level_data": {"level": 1, "points": 0}
            }
        
        user_data = self.user_progress[user_id]
        earned_badge_ids = [badge.badge_id for badge in user_data["badges"]]
        
        for badge_id, achievement in self.achievements.items():
            # Skip if already earned and not repeatable
            if badge_id in earned_badge_ids and not achievement.is_repeatable:
                continue
                
            # Check if requirements are met
            if self._check_requirements(activity_data, achievement.requirements):
                # Award the badge
                user_badge = UserBadge(
                    user_id=user_id,
                    badge_id=badge_id,
                    earned_date=datetime.now(),
                    progress_data=activity_data.copy(),
                    times_earned=1 if badge_id not in earned_badge_ids else user_data["badges"][-1].times_earned + 1
                )
                
                user_data["badges"].append(user_badge)
                user_data["level_data"]["points"] += achievement.reward_points
                
                newly_earned.append(badge_id)
                logger.info(f"User {user_id} earned achievement: {achievement.name}")
        
        # Update user level if necessary
        self._update_user_level(user_id)
        
        return newly_earned
    
    def _check_requirements(self, user_data: Dict[str, Any], requirements: Dict[str, Any]) -> bool:
        """Check if user meets achievement requirements"""
        for req_key, req_value in requirements.items():
            user_value = user_data.get(req_key, 0)
            
            if req_key == "joined_before":
                # Special case for date comparison
                user_join_date = user_data.get("join_date", datetime.now())
                required_date = datetime.strptime(req_value, "%Y-%m-%d")
                if user_join_date > required_date:
                    return False
            else:
                # Numeric comparison
                if user_value < req_value:
                    return False
        
        return True
    
    def _update_user_level(self, user_id: str):
        """Update user level based on total points"""
        user_data = self.user_progress[user_id]
        current_points = user_data["level_data"]["points"]
        current_level = user_data["level_data"]["level"]
        
        # Find the highest level the user qualifies for
        new_level = current_level
        for level, level_data in self.level_thresholds.items():
            if current_points >= level_data["points_required"] and level > new_level:
                new_level = level
        
        if new_level > current_level:
            user_data["level_data"]["level"] = new_level
            logger.info(f"User {user_id} leveled up to level {new_level}")
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user's gamification profile"""
        if user_id not in self.user_progress:
            return {
                "level": 1,
                "title": "Newcomer", 
                "total_points": 0,
                "badges": [],
                "progress_to_next_level": 100
            }
        
        user_data = self.user_progress[user_id]
        current_level = user_data["level_data"]["level"]
        current_points = user_data["level_data"]["points"]
        
        # Calculate progress to next level
        next_level = current_level + 1
        if next_level in self.level_thresholds:
            points_needed = self.level_thresholds[next_level]["points_required"] - current_points
        else:
            points_needed = 0  # Max level reached
        
        return {
            "level": current_level,
            "title": self.level_thresholds[current_level]["title"],
            "total_points": current_points,
            "badges": [asdict(badge) for badge in user_data["badges"]],
            "progress_to_next_level": points_needed,
            "benefits": self.level_thresholds[current_level]["benefits"]
        }
    
    def get_available_achievements(self, user_id: str, include_hidden: bool = False) -> List[Dict]:
        """Get all available achievements for display"""
        achievements_list = []
        user_badges = []
        
        if user_id in self.user_progress:
            user_badges = [badge.badge_id for badge in self.user_progress[user_id]["badges"]]
        
        for badge_id, achievement in self.achievements.items():
            if achievement.is_hidden and not include_hidden and badge_id not in user_badges:
                continue
                
            achievement_dict = asdict(achievement)
            achievement_dict["earned"] = badge_id in user_badges
            achievement_dict["rarity_info"] = achievement.rarity.value
            achievements_list.append(achievement_dict)
        
        return achievements_list
    
    def get_leaderboard(self, limit: int = 50) -> List[Dict]:
        """Get points leaderboard"""
        leaderboard = []
        
        for user_id, user_data in self.user_progress.items():
            leaderboard.append({
                "user_id": user_id,
                "level": user_data["level_data"]["level"],
                "title": self.level_thresholds[user_data["level_data"]["level"]]["title"],
                "total_points": user_data["level_data"]["points"],
                "badge_count": len(user_data["badges"])
            })
        
        # Sort by points descending
        leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
        
        return leaderboard[:limit]
    
    def award_manual_points(self, user_id: str, points: int, reason: str = "Manual award"):
        """Manually award points to user"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {
                "badges": [],
                "stats": {},
                "level_data": {"level": 1, "points": 0}
            }
        
        self.user_progress[user_id]["level_data"]["points"] += points
        self._update_user_level(user_id)
        
        logger.info(f"Awarded {points} points to user {user_id}: {reason}")
        
    def simulate_user_activity(self, user_id: str) -> Dict[str, Any]:
        """Simulate user activity for testing achievements"""
        activity = {
            "messages_sent": random.randint(1, 1500),
            "check_in_streak": random.randint(1, 150),
            "communities_joined": random.randint(0, 10),
            "community_likes_received": random.randint(0, 25),
            "challenges_completed": random.randint(0, 15),
            "days_active": random.randint(1, 400),
            "successful_referrals": random.randint(0, 15),
            "join_date": datetime.now() - timedelta(days=random.randint(1, 400))
        }
        
        newly_earned = self.check_achievements(user_id, activity)
        return {
            "activity": activity,
            "newly_earned_badges": newly_earned,
            "profile": self.get_user_profile(user_id)
        }