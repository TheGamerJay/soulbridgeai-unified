"""
Community System for SoulBridge AI
Wellness communities, peer support, and group engagement features
"""
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random

logger = logging.getLogger(__name__)

class CommunityType(Enum):
    GENERAL_WELLNESS = "general_wellness"
    ANXIETY_SUPPORT = "anxiety_support"
    DEPRESSION_SUPPORT = "depression_support"
    MEDITATION = "meditation"
    FITNESS = "fitness"
    NUTRITION = "nutrition"
    SLEEP = "sleep"
    STRESS_MANAGEMENT = "stress_management"
    MINDFULNESS = "mindfulness"
    SELF_CARE = "self_care"
    GRIEF_SUPPORT = "grief_support"
    ADDICTION_RECOVERY = "addiction_recovery"
    CHRONIC_ILLNESS = "chronic_illness"
    WORKPLACE_WELLNESS = "workplace_wellness"
    STUDENT_SUPPORT = "student_support"

class MembershipRole(Enum):
    MEMBER = "member"
    MODERATOR = "moderator"
    ADMIN = "admin"
    CREATOR = "creator"

class CommunityVisibility(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    INVITE_ONLY = "invite_only"

@dataclass
class WellnessCommunity:
    community_id: str
    name: str
    description: str
    community_type: CommunityType
    visibility: CommunityVisibility
    creator_id: str
    member_count: int
    max_members: Optional[int]
    guidelines: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    is_verified: bool
    avatar_url: Optional[str]
    cover_image_url: Optional[str]
    weekly_challenge: Optional[str]

@dataclass
class CommunityMembership:
    membership_id: str
    community_id: str
    user_id: str
    role: MembershipRole
    joined_at: datetime
    last_active: datetime
    contribution_score: int
    is_active: bool
    nickname: Optional[str]
    bio: Optional[str]

@dataclass
class CommunityPost:
    post_id: str
    community_id: str
    author_id: str
    title: str
    content: str
    post_type: str  # discussion, question, resource, milestone, support
    tags: List[str]
    upvotes: int
    downvotes: int
    reply_count: int
    is_pinned: bool
    is_anonymous: bool
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

@dataclass
class PeerSupportMatch:
    match_id: str
    user1_id: str
    user2_id: str
    compatibility_score: float
    shared_interests: List[str]
    match_reason: str
    status: str  # pending, active, completed, declined
    matched_at: datetime
    last_interaction: Optional[datetime]
    support_goals: List[str]

@dataclass
class WellnessChallenge:
    challenge_id: str
    title: str
    description: str
    challenge_type: str  # daily, weekly, monthly
    category: str  # fitness, meditation, self_care, etc.
    duration_days: int
    difficulty_level: str  # beginner, intermediate, advanced
    participant_count: int
    max_participants: Optional[int]
    start_date: datetime
    end_date: datetime
    creator_id: str
    reward_points: int
    is_community_challenge: bool
    community_id: Optional[str]

@dataclass
class ChallengeParticipation:
    participation_id: str
    challenge_id: str
    user_id: str
    joined_at: datetime
    progress: float  # 0.0 to 1.0
    current_streak: int
    best_streak: int
    completed: bool
    completed_at: Optional[datetime]
    points_earned: int

class CommunityManager:
    """Manages wellness communities and peer support features"""
    
    def __init__(self, db_manager=None, social_manager=None):
        self.db = db_manager
        self.social_manager = social_manager
        
        # Community categories and their default settings
        self.community_templates = {
            CommunityType.ANXIETY_SUPPORT: {
                'name': 'Anxiety Support Circle',
                'description': 'A safe space for sharing anxiety management strategies and mutual support',
                'guidelines': 'Be kind, respectful, and supportive. Share experiences, not medical advice.',
                'tags': ['anxiety', 'mental-health', 'coping-strategies', 'support'],
                'max_members': 500
            },
            CommunityType.MEDITATION: {
                'name': 'Mindful Meditation Community',
                'description': 'Explore meditation practices, share experiences, and grow together',
                'guidelines': 'Share meditation techniques, experiences, and resources respectfully.',
                'tags': ['meditation', 'mindfulness', 'peace', 'spiritual-growth'],
                'max_members': 1000
            },
            CommunityType.FITNESS: {
                'name': 'Wellness Fitness Group',
                'description': 'Motivation and support for physical wellness and fitness goals',
                'guidelines': 'Encourage healthy habits, share workout tips, celebrate progress.',
                'tags': ['fitness', 'exercise', 'health', 'motivation'],
                'max_members': 2000
            }
        }
        
        logger.info("Community Manager initialized")
    
    def create_community(self, creator_id: str, name: str, description: str, 
                        community_type: CommunityType, visibility: CommunityVisibility = CommunityVisibility.PUBLIC,
                        max_members: Optional[int] = None) -> Optional[str]:
        """Create a new wellness community"""
        try:
            if not self.db:
                return None
            
            community_id = str(uuid.uuid4())
            
            # Get template if available
            template = self.community_templates.get(community_type, {})
            
            community = WellnessCommunity(
                community_id=community_id,
                name=name,
                description=description,
                community_type=community_type,
                visibility=visibility,
                creator_id=creator_id,
                member_count=1,  # Creator is first member
                max_members=max_members or template.get('max_members', 1000),
                guidelines=template.get('guidelines', 'Be respectful and supportive to all members.'),
                tags=template.get('tags', []),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_verified=False,
                avatar_url=None,
                cover_image_url=None,
                weekly_challenge=None
            )
            
            # Store community
            query = """
                INSERT INTO wellness_communities 
                (community_id, name, description, community_type, visibility, creator_id,
                 member_count, max_members, guidelines, tags, created_at, updated_at,
                 is_verified, weekly_challenge)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                community.community_id, community.name, community.description,
                community.community_type.value, community.visibility.value,
                community.creator_id, community.member_count, community.max_members,
                community.guidelines, json.dumps(community.tags),
                community.created_at, community.updated_at, community.is_verified,
                community.weekly_challenge
            ))
            
            # Add creator as admin member
            self.join_community(community_id, creator_id, MembershipRole.CREATOR)
            
            logger.info(f"Community created: {community_id} ({name}) by {creator_id}")
            return community_id
            
        except Exception as e:
            logger.error(f"Error creating community: {e}")
            return None
    
    def join_community(self, community_id: str, user_id: str, 
                      role: MembershipRole = MembershipRole.MEMBER) -> bool:
        """Join a wellness community"""
        try:
            if not self.db:
                return False
            
            # Check if user is already a member
            existing_query = "SELECT membership_id FROM community_memberships WHERE community_id = ? AND user_id = ?"
            existing = self.db.fetch_one(existing_query, (community_id, user_id))
            
            if existing:
                logger.warning(f"User {user_id} already member of community {community_id}")
                return True
            
            # Check community capacity
            community_query = "SELECT member_count, max_members FROM wellness_communities WHERE community_id = ?"
            community_info = self.db.fetch_one(community_query, (community_id,))
            
            if not community_info:
                return False
            
            current_count, max_members = community_info
            if max_members and current_count >= max_members:
                logger.warning(f"Community {community_id} is at capacity")
                return False
            
            # Create membership
            membership_id = str(uuid.uuid4())
            membership = CommunityMembership(
                membership_id=membership_id,
                community_id=community_id,
                user_id=user_id,
                role=role,
                joined_at=datetime.now(),
                last_active=datetime.now(),
                contribution_score=0,
                is_active=True,
                nickname=None,
                bio=None
            )
            
            # Store membership
            query = """
                INSERT INTO community_memberships
                (membership_id, community_id, user_id, role, joined_at, last_active,
                 contribution_score, is_active, nickname, bio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                membership.membership_id, membership.community_id, membership.user_id,
                membership.role.value, membership.joined_at, membership.last_active,
                membership.contribution_score, membership.is_active,
                membership.nickname, membership.bio
            ))
            
            # Update community member count
            self.db.execute_query(
                "UPDATE wellness_communities SET member_count = member_count + 1 WHERE community_id = ?",
                (community_id,)
            )
            
            logger.info(f"User {user_id} joined community {community_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining community: {e}")
            return False
    
    def find_peer_support_matches(self, user_id: str, max_matches: int = 5) -> List[PeerSupportMatch]:
        """Find compatible peers for support matching"""
        try:
            if not self.db:
                return []
            
            # Get user's interests and community memberships
            user_communities_query = """
                SELECT wc.community_type, wc.tags 
                FROM community_memberships cm
                JOIN wellness_communities wc ON cm.community_id = wc.community_id
                WHERE cm.user_id = ? AND cm.is_active = 1
            """
            
            user_communities = self.db.fetch_all(user_communities_query, (user_id,))
            user_interests = set()
            
            for community_type, tags_json in user_communities:
                user_interests.add(community_type)
                if tags_json:
                    tags = json.loads(tags_json)
                    user_interests.update(tags)
            
            if not user_interests:
                return []
            
            # Find potential matches
            potential_matches_query = """
                SELECT DISTINCT cm.user_id, wc.community_type, wc.tags
                FROM community_memberships cm
                JOIN wellness_communities wc ON cm.community_id = wc.community_id
                WHERE cm.user_id != ? AND cm.is_active = 1
                AND cm.user_id NOT IN (
                    SELECT CASE WHEN user1_id = ? THEN user2_id ELSE user1_id END
                    FROM peer_support_matches 
                    WHERE (user1_id = ? OR user2_id = ?) 
                    AND status IN ('active', 'pending')
                )
                LIMIT 50
            """
            
            potential_matches = self.db.fetch_all(potential_matches_query, 
                                                (user_id, user_id, user_id, user_id))
            
            # Calculate compatibility scores
            matches = []
            user_scores = {}
            
            for match_user_id, community_type, tags_json in potential_matches:
                if match_user_id not in user_scores:
                    user_scores[match_user_id] = {
                        'interests': set(),
                        'shared_count': 0
                    }
                
                user_scores[match_user_id]['interests'].add(community_type)
                if tags_json:
                    tags = json.loads(tags_json)
                    user_scores[match_user_id]['interests'].update(tags)
            
            # Create matches with compatibility scores
            for match_user_id, data in user_scores.items():
                shared_interests = user_interests.intersection(data['interests'])
                if len(shared_interests) >= 2:  # Require at least 2 shared interests
                    compatibility_score = len(shared_interests) / len(user_interests.union(data['interests']))
                    
                    match = PeerSupportMatch(
                        match_id=str(uuid.uuid4()),
                        user1_id=user_id,
                        user2_id=match_user_id,
                        compatibility_score=compatibility_score,
                        shared_interests=list(shared_interests),
                        match_reason=f"Shared interests in {', '.join(list(shared_interests)[:3])}",
                        status='pending',
                        matched_at=datetime.now(),
                        last_interaction=None,
                        support_goals=self._generate_support_goals(shared_interests)
                    )
                    
                    matches.append(match)
            
            # Sort by compatibility score and return top matches
            matches.sort(key=lambda m: m.compatibility_score, reverse=True)
            return matches[:max_matches]
            
        except Exception as e:
            logger.error(f"Error finding peer support matches: {e}")
            return []
    
    def create_wellness_challenge(self, creator_id: str, title: str, description: str,
                                challenge_type: str, category: str, duration_days: int,
                                difficulty_level: str = "beginner", community_id: Optional[str] = None) -> Optional[str]:
        """Create a wellness challenge"""
        try:
            if not self.db:
                return None
            
            challenge_id = str(uuid.uuid4())
            start_date = datetime.now()
            end_date = start_date + timedelta(days=duration_days)
            
            # Calculate reward points based on difficulty and duration
            point_multipliers = {'beginner': 1, 'intermediate': 1.5, 'advanced': 2}
            reward_points = int(duration_days * 10 * point_multipliers.get(difficulty_level, 1))
            
            challenge = WellnessChallenge(
                challenge_id=challenge_id,
                title=title,
                description=description,
                challenge_type=challenge_type,
                category=category,
                duration_days=duration_days,
                difficulty_level=difficulty_level,
                participant_count=0,
                max_participants=None,
                start_date=start_date,
                end_date=end_date,
                creator_id=creator_id,
                reward_points=reward_points,
                is_community_challenge=community_id is not None,
                community_id=community_id
            )
            
            # Store challenge
            query = """
                INSERT INTO wellness_challenges
                (challenge_id, title, description, challenge_type, category, duration_days,
                 difficulty_level, participant_count, max_participants, start_date, end_date,
                 creator_id, reward_points, is_community_challenge, community_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                challenge.challenge_id, challenge.title, challenge.description,
                challenge.challenge_type, challenge.category, challenge.duration_days,
                challenge.difficulty_level, challenge.participant_count,
                challenge.max_participants, challenge.start_date, challenge.end_date,
                challenge.creator_id, challenge.reward_points,
                challenge.is_community_challenge, challenge.community_id
            ))
            
            logger.info(f"Wellness challenge created: {challenge_id} ({title})")
            return challenge_id
            
        except Exception as e:
            logger.error(f"Error creating wellness challenge: {e}")
            return None
    
    def get_community_recommendations(self, user_id: str, limit: int = 10) -> List[WellnessCommunity]:
        """Get personalized community recommendations"""
        try:
            if not self.db:
                return []
            
            # Get user's existing communities and mood patterns
            existing_communities_query = """
                SELECT community_id FROM community_memberships WHERE user_id = ? AND is_active = 1
            """
            existing_communities = [row[0] for row in self.db.fetch_all(existing_communities_query, (user_id,))]
            
            # Get user's mood patterns to suggest relevant communities
            mood_patterns_query = """
                SELECT mood, COUNT(*) as frequency 
                FROM mood_entries 
                WHERE user_id = ? AND created_at >= ?
                GROUP BY mood 
                ORDER BY frequency DESC 
                LIMIT 5
            """
            
            week_ago = datetime.now() - timedelta(days=7)
            mood_patterns = self.db.fetch_all(mood_patterns_query, (user_id, week_ago))
            
            # Map moods to community types
            mood_to_community = {
                'anxious': CommunityType.ANXIETY_SUPPORT,
                'stressed': CommunityType.STRESS_MANAGEMENT,
                'sad': CommunityType.DEPRESSION_SUPPORT,
                'peaceful': CommunityType.MEDITATION,
                'energetic': CommunityType.FITNESS
            }
            
            recommended_types = []
            for mood, frequency in mood_patterns:
                if mood in mood_to_community:
                    recommended_types.append(mood_to_community[mood].value)
            
            # If no mood patterns, recommend general communities
            if not recommended_types:
                recommended_types = [CommunityType.GENERAL_WELLNESS.value, CommunityType.MEDITATION.value]
            
            # Build query with exclusions
            exclusion_clause = ""
            query_params = []
            
            if existing_communities:
                placeholders = ','.join(['?' for _ in existing_communities])
                exclusion_clause = f"AND community_id NOT IN ({placeholders})"
                query_params.extend(existing_communities)
            
            # Add recommended types to query
            type_placeholders = ','.join(['?' for _ in recommended_types])
            query_params.extend(recommended_types)
            
            recommendations_query = f"""
                SELECT community_id, name, description, community_type, member_count, tags
                FROM wellness_communities 
                WHERE visibility = 'public' 
                AND community_type IN ({type_placeholders})
                {exclusion_clause}
                ORDER BY member_count DESC, created_at DESC
                LIMIT ?
            """
            
            query_params.append(limit)
            results = self.db.fetch_all(recommendations_query, tuple(query_params))
            
            recommendations = []
            for row in results:
                community = WellnessCommunity(
                    community_id=row[0],
                    name=row[1],
                    description=row[2],
                    community_type=CommunityType(row[3]),
                    visibility=CommunityVisibility.PUBLIC,
                    creator_id="",  # Not needed for recommendations
                    member_count=row[4],
                    max_members=None,
                    guidelines="",
                    tags=json.loads(row[5]) if row[5] else [],
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    is_verified=False,
                    avatar_url=None,
                    cover_image_url=None,
                    weekly_challenge=None
                )
                recommendations.append(community)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting community recommendations: {e}")
            return []
    
    def _generate_support_goals(self, shared_interests: set) -> List[str]:
        """Generate support goals based on shared interests"""
        goal_templates = {
            'anxiety': ['Manage daily anxiety', 'Practice breathing techniques', 'Share coping strategies'],
            'meditation': ['Establish daily practice', 'Explore different techniques', 'Find inner peace'],
            'fitness': ['Stay motivated', 'Set healthy goals', 'Celebrate progress'],
            'stress_management': ['Reduce daily stress', 'Work-life balance', 'Healthy boundaries'],
            'self_care': ['Prioritize self-care', 'Daily wellness habits', 'Self-compassion practice']
        }
        
        goals = []
        for interest in shared_interests:
            if interest in goal_templates:
                goals.extend(goal_templates[interest])
        
        return goals[:3] if goals else ['Mutual support', 'Shared wellness journey', 'Encouragement']

# Database initialization
def init_community_database(db_connection):
    """Initialize community system database tables"""
    try:
        # Wellness communities table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS wellness_communities (
                community_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                community_type TEXT NOT NULL,
                visibility TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                member_count INTEGER DEFAULT 0,
                max_members INTEGER,
                guidelines TEXT,
                tags TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                is_verified BOOLEAN DEFAULT 0,
                avatar_url TEXT,
                cover_image_url TEXT,
                weekly_challenge TEXT,
                INDEX(community_type),
                INDEX(visibility),
                INDEX(creator_id),
                INDEX(created_at)
            )
        ''')
        
        # Community memberships table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS community_memberships (
                membership_id TEXT PRIMARY KEY,
                community_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                joined_at DATETIME NOT NULL,
                last_active DATETIME NOT NULL,
                contribution_score INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                nickname TEXT,
                bio TEXT,
                INDEX(community_id),
                INDEX(user_id),
                INDEX(role),
                UNIQUE(community_id, user_id)
            )
        ''')
        
        # Community posts table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS community_posts (
                post_id TEXT PRIMARY KEY,
                community_id TEXT NOT NULL,
                author_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                post_type TEXT NOT NULL,
                tags TEXT,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                is_pinned BOOLEAN DEFAULT 0,
                is_anonymous BOOLEAN DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                metadata TEXT,
                INDEX(community_id),
                INDEX(author_id),
                INDEX(post_type),
                INDEX(created_at)
            )
        ''')
        
        # Peer support matches table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS peer_support_matches (
                match_id TEXT PRIMARY KEY,
                user1_id TEXT NOT NULL,
                user2_id TEXT NOT NULL,
                compatibility_score REAL NOT NULL,
                shared_interests TEXT,
                match_reason TEXT,
                status TEXT NOT NULL,
                matched_at DATETIME NOT NULL,
                last_interaction DATETIME,
                support_goals TEXT,
                INDEX(user1_id),
                INDEX(user2_id),
                INDEX(status),
                INDEX(matched_at)
            )
        ''')
        
        # Wellness challenges table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS wellness_challenges (
                challenge_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                challenge_type TEXT NOT NULL,
                category TEXT NOT NULL,
                duration_days INTEGER NOT NULL,
                difficulty_level TEXT NOT NULL,
                participant_count INTEGER DEFAULT 0,
                max_participants INTEGER,
                start_date DATETIME NOT NULL,
                end_date DATETIME NOT NULL,
                creator_id TEXT NOT NULL,
                reward_points INTEGER DEFAULT 0,
                is_community_challenge BOOLEAN DEFAULT 0,
                community_id TEXT,
                INDEX(challenge_type),
                INDEX(category),
                INDEX(start_date),
                INDEX(creator_id)
            )
        ''')
        
        # Challenge participation table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS challenge_participation (
                participation_id TEXT PRIMARY KEY,
                challenge_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                joined_at DATETIME NOT NULL,
                progress REAL DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                completed_at DATETIME,
                points_earned INTEGER DEFAULT 0,
                INDEX(challenge_id),
                INDEX(user_id),
                INDEX(completed),
                UNIQUE(challenge_id, user_id)
            )
        ''')
        
        db_connection.commit()
        logger.info("Community system database tables initialized")
        
    except Exception as e:
        logger.error(f"Error initializing community database: {e}")

# Global instance
community_manager = None

def init_community_manager(db_manager=None, social_manager=None):
    """Initialize community manager"""
    global community_manager
    try:
        community_manager = CommunityManager(db_manager, social_manager)
        logger.info("Community manager initialized successfully")
        return community_manager
    except Exception as e:
        logger.error(f"Error initializing community manager: {e}")
        return None

def get_community_manager():
    """Get community manager instance"""
    return community_manager