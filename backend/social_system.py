"""
Social Features and User Connections System
Friend connections, mood sharing, and community features
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class FriendshipStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    BLOCKED = "blocked"

class PostVisibility(Enum):
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"

class PostType(Enum):
    MOOD = "mood"
    ACHIEVEMENT = "achievement"
    REFLECTION = "reflection"
    MILESTONE = "milestone"

@dataclass
class FriendRequest:
    id: str
    requester_id: str
    recipient_id: str
    status: FriendshipStatus
    message: Optional[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class Friendship:
    id: str
    user1_id: str
    user2_id: str
    created_at: datetime
    last_interaction: Optional[datetime] = None

@dataclass
class SocialPost:
    id: str
    user_id: str
    post_type: PostType
    content: str
    visibility: PostVisibility
    mood_data: Optional[Dict] = None
    created_at: datetime = None
    likes_count: int = 0
    comments_count: int = 0

@dataclass
class UserProfile:
    user_id: str
    display_name: str
    bio: Optional[str]
    avatar_url: Optional[str]
    mood_sharing_enabled: bool
    public_profile: bool
    friend_count: int = 0
    joined_date: Optional[datetime] = None

class SocialManager:
    def __init__(self, db_manager, preferences_manager, notification_manager=None):
        self.db = db_manager
        self.preferences = preferences_manager
        self.notifications = notification_manager
        
    def send_friend_request(self, requester_id: str, recipient_id: str, message: str = None) -> Dict[str, Any]:
        """Send a friend request to another user"""
        try:
            if not self.db:
                return {'success': False, 'error': 'Database unavailable'}
            
            # Check if already friends or request exists
            existing = self._check_existing_connection(requester_id, recipient_id)
            if existing:
                return {'success': False, 'error': existing}
            
            # Check if user is trying to add themselves
            if requester_id == recipient_id:
                return {'success': False, 'error': 'Cannot add yourself as friend'}
            
            # Check privacy settings
            recipient_prefs = self.preferences.get_user_preferences(recipient_id) if self.preferences else {}
            privacy = recipient_prefs.get('privacy', {})
            
            if privacy.get('profile_visibility') == 'private':
                return {'success': False, 'error': 'User has private profile'}
            
            # Create friend request
            request_id = str(uuid.uuid4())
            request = FriendRequest(
                id=request_id,
                requester_id=requester_id,
                recipient_id=recipient_id,
                status=FriendshipStatus.PENDING,
                message=message,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            query = """
            INSERT INTO friend_requests 
            (id, requester_id, recipient_id, status, message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                request.id, request.requester_id, request.recipient_id,
                request.status.value, request.message, request.created_at, request.updated_at
            ))
            
            # Send notification
            if self.notifications:
                requester_profile = self.get_user_profile(requester_id)
                self.notifications.send_notification(
                    user_id=recipient_id,
                    title="New Friend Request",
                    message=f"{requester_profile.display_name} wants to connect with you",
                    notification_type="friend_request",
                    metadata={'request_id': request_id, 'requester_id': requester_id}
                )
            
            logger.info(f"Friend request sent from {requester_id} to {recipient_id}")
            return {'success': True, 'request_id': request_id}
            
        except Exception as e:
            logger.error(f"Error sending friend request: {e}")
            return {'success': False, 'error': 'Failed to send friend request'}
    
    def respond_to_friend_request(self, request_id: str, response: str, user_id: str) -> Dict[str, Any]:
        """Accept, decline, or block a friend request"""
        try:
            if not self.db:
                return {'success': False, 'error': 'Database unavailable'}
            
            if response not in ['accept', 'decline', 'block']:
                return {'success': False, 'error': 'Invalid response'}
            
            # Get friend request
            query = "SELECT * FROM friend_requests WHERE id = ? AND recipient_id = ?"
            result = self.db.fetch_one(query, (request_id, user_id))
            
            if not result:
                return {'success': False, 'error': 'Friend request not found'}
            
            request_data = result
            if request_data[3] != 'pending':  # status
                return {'success': False, 'error': 'Request already processed'}
            
            # Update request status
            status_map = {
                'accept': FriendshipStatus.ACCEPTED,
                'decline': FriendshipStatus.DECLINED,
                'block': FriendshipStatus.BLOCKED
            }
            
            new_status = status_map[response]
            update_query = """
            UPDATE friend_requests 
            SET status = ?, updated_at = ?
            WHERE id = ?
            """
            
            self.db.execute_query(update_query, (new_status.value, datetime.now(), request_id))
            
            # If accepted, create friendship
            if response == 'accept':
                friendship_id = str(uuid.uuid4())
                friendship_query = """
                INSERT INTO friendships (id, user1_id, user2_id, created_at)
                VALUES (?, ?, ?, ?)
                """
                
                self.db.execute_query(friendship_query, (
                    friendship_id, request_data[1], request_data[2], datetime.now()
                ))
                
                # Update friend counts
                self._update_friend_count(request_data[1])
                self._update_friend_count(request_data[2])
                
                # Send notification to requester
                if self.notifications:
                    recipient_profile = self.get_user_profile(user_id)
                    self.notifications.send_notification(
                        user_id=request_data[1],
                        title="Friend Request Accepted",
                        message=f"{recipient_profile.display_name} accepted your friend request",
                        notification_type="friend_accepted",
                        metadata={'friend_id': user_id}
                    )
            
            logger.info(f"Friend request {request_id} {response}ed by {user_id}")
            return {'success': True, 'status': new_status.value}
            
        except Exception as e:
            logger.error(f"Error responding to friend request: {e}")
            return {'success': False, 'error': 'Failed to process response'}
    
    def get_friend_requests(self, user_id: str) -> List[Dict[str, Any]]:
        """Get pending friend requests for user"""
        try:
            if not self.db:
                return []
            
            # Get incoming requests
            query = """
            SELECT fr.id, fr.requester_id, fr.message, fr.created_at,
                   up.display_name, up.avatar_url
            FROM friend_requests fr
            LEFT JOIN user_profiles up ON fr.requester_id = up.user_id
            WHERE fr.recipient_id = ? AND fr.status = 'pending'
            ORDER BY fr.created_at DESC
            """
            
            results = self.db.fetch_all(query, (user_id,))
            
            requests = []
            for row in results:
                requests.append({
                    'id': row[0],
                    'requester_id': row[1],
                    'message': row[2],
                    'created_at': row[3],
                    'requester_name': row[4] or 'Unknown User',
                    'requester_avatar': row[5]
                })
            
            return requests
            
        except Exception as e:
            logger.error(f"Error getting friend requests: {e}")
            return []
    
    def get_friends_list(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's friends list"""
        try:
            if not self.db:
                return []
            
            query = """
            SELECT CASE 
                WHEN f.user1_id = ? THEN f.user2_id 
                ELSE f.user1_id 
            END as friend_id,
            f.created_at, f.last_interaction,
            up.display_name, up.avatar_url, up.bio
            FROM friendships f
            LEFT JOIN user_profiles up ON (
                CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END = up.user_id
            )
            WHERE f.user1_id = ? OR f.user2_id = ?
            ORDER BY f.last_interaction DESC, f.created_at DESC
            """
            
            results = self.db.fetch_all(query, (user_id, user_id, user_id, user_id))
            
            friends = []
            for row in results:
                friends.append({
                    'user_id': row[0],
                    'friendship_since': row[1],
                    'last_interaction': row[2],
                    'display_name': row[3] or 'Unknown User',
                    'avatar_url': row[4],
                    'bio': row[5]
                })
            
            return friends
            
        except Exception as e:
            logger.error(f"Error getting friends list: {e}")
            return []
    
    def create_social_post(self, user_id: str, post_type: str, content: str, 
                          visibility: str = "friends", mood_data: Dict = None) -> Dict[str, Any]:
        """Create a social post"""
        try:
            if not self.db:
                return {'success': False, 'error': 'Database unavailable'}
            
            # Validate inputs
            if post_type not in [e.value for e in PostType]:
                return {'success': False, 'error': 'Invalid post type'}
            
            if visibility not in [e.value for e in PostVisibility]:
                return {'success': False, 'error': 'Invalid visibility'}
            
            if not content.strip():
                return {'success': False, 'error': 'Content cannot be empty'}
            
            # Check privacy settings
            user_prefs = self.preferences.get_user_preferences(user_id) if self.preferences else {}
            privacy = user_prefs.get('privacy', {})
            
            if post_type == 'mood' and not privacy.get('mood_sharing', True):
                return {'success': False, 'error': 'Mood sharing is disabled'}
            
            # Create post
            post_id = str(uuid.uuid4())
            post = SocialPost(
                id=post_id,
                user_id=user_id,
                post_type=PostType(post_type),
                content=content,
                visibility=PostVisibility(visibility),
                mood_data=mood_data,
                created_at=datetime.now()
            )
            
            query = """
            INSERT INTO social_posts 
            (id, user_id, post_type, content, visibility, mood_data, created_at, likes_count, comments_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                post.id, post.user_id, post.post_type.value, post.content,
                post.visibility.value, json.dumps(post.mood_data) if post.mood_data else None,
                post.created_at, 0, 0
            ))
            
            logger.info(f"Social post created by {user_id}: {post_id}")
            return {'success': True, 'post_id': post_id}
            
        except Exception as e:
            logger.error(f"Error creating social post: {e}")
            return {'success': False, 'error': 'Failed to create post'}
    
    def get_social_feed(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get social feed for user (friends' posts)"""
        try:
            if not self.db:
                return []
            
            # Get posts from friends and user's own posts
            query = """
            SELECT sp.id, sp.user_id, sp.post_type, sp.content, sp.visibility,
                   sp.mood_data, sp.created_at, sp.likes_count, sp.comments_count,
                   up.display_name, up.avatar_url
            FROM social_posts sp
            LEFT JOIN user_profiles up ON sp.user_id = up.user_id
            WHERE (
                sp.user_id = ?
                OR (
                    sp.user_id IN (
                        SELECT CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END
                        FROM friendships f
                        WHERE f.user1_id = ? OR f.user2_id = ?
                    )
                    AND sp.visibility IN ('public', 'friends')
                )
            )
            ORDER BY sp.created_at DESC
            LIMIT ?
            """
            
            results = self.db.fetch_all(query, (user_id, user_id, user_id, user_id, limit))
            
            posts = []
            for row in results:
                mood_data = None
                if row[5]:
                    try:
                        mood_data = json.loads(row[5])
                    except json.JSONDecodeError:
                        pass
                
                posts.append({
                    'id': row[0],
                    'user_id': row[1],
                    'post_type': row[2],
                    'content': row[3],
                    'visibility': row[4],
                    'mood_data': mood_data,
                    'created_at': row[6],
                    'likes_count': row[7],
                    'comments_count': row[8],
                    'author_name': row[9] or 'Unknown User',
                    'author_avatar': row[10],
                    'is_own_post': row[1] == user_id
                })
            
            return posts
            
        except Exception as e:
            logger.error(f"Error getting social feed: {e}")
            return []
    
    def like_post(self, user_id: str, post_id: str) -> Dict[str, Any]:
        """Like or unlike a social post"""
        try:
            if not self.db:
                return {'success': False, 'error': 'Database unavailable'}
            
            # Check if already liked
            like_check = "SELECT id FROM post_likes WHERE user_id = ? AND post_id = ?"
            existing_like = self.db.fetch_one(like_check, (user_id, post_id))
            
            if existing_like:
                # Unlike
                self.db.execute_query("DELETE FROM post_likes WHERE user_id = ? AND post_id = ?", 
                                    (user_id, post_id))
                self.db.execute_query("UPDATE social_posts SET likes_count = likes_count - 1 WHERE id = ?",
                                    (post_id,))
                action = 'unliked'
            else:
                # Like
                like_id = str(uuid.uuid4())
                self.db.execute_query("INSERT INTO post_likes (id, user_id, post_id, created_at) VALUES (?, ?, ?, ?)",
                                    (like_id, user_id, post_id, datetime.now()))
                self.db.execute_query("UPDATE social_posts SET likes_count = likes_count + 1 WHERE id = ?",
                                    (post_id,))
                action = 'liked'
            
            # Get updated like count
            count_query = "SELECT likes_count FROM social_posts WHERE id = ?"
            count_result = self.db.fetch_one(count_query, (post_id,))
            likes_count = count_result[0] if count_result else 0
            
            return {'success': True, 'action': action, 'likes_count': likes_count}
            
        except Exception as e:
            logger.error(f"Error liking post: {e}")
            return {'success': False, 'error': 'Failed to like post'}
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user's social profile"""
        try:
            if not self.db:
                return None
            
            query = """
            SELECT user_id, display_name, bio, avatar_url, mood_sharing_enabled, 
                   public_profile, friend_count, joined_date
            FROM user_profiles 
            WHERE user_id = ?
            """
            
            result = self.db.fetch_one(query, (user_id,))
            
            if result:
                return UserProfile(
                    user_id=result[0],
                    display_name=result[1] or f"User {user_id[:8]}",
                    bio=result[2],
                    avatar_url=result[3],
                    mood_sharing_enabled=bool(result[4]),
                    public_profile=bool(result[5]),
                    friend_count=result[6] or 0,
                    joined_date=result[7]
                )
            else:
                # Create default profile
                return self._create_default_profile(user_id)
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user's social profile"""
        try:
            if not self.db:
                return {'success': False, 'error': 'Database unavailable'}
            
            # Get existing profile
            existing = self.get_user_profile(user_id)
            if not existing:
                existing = self._create_default_profile(user_id)
            
            # Update fields
            display_name = profile_data.get('display_name', existing.display_name)
            bio = profile_data.get('bio', existing.bio)
            avatar_url = profile_data.get('avatar_url', existing.avatar_url)
            mood_sharing = profile_data.get('mood_sharing_enabled', existing.mood_sharing_enabled)
            public_profile = profile_data.get('public_profile', existing.public_profile)
            
            query = """
            INSERT OR REPLACE INTO user_profiles 
            (user_id, display_name, bio, avatar_url, mood_sharing_enabled, public_profile, friend_count, joined_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                user_id, display_name, bio, avatar_url, mood_sharing, public_profile,
                existing.friend_count, existing.joined_date or datetime.now()
            ))
            
            logger.info(f"Profile updated for user {user_id}")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return {'success': False, 'error': 'Failed to update profile'}
    
    def search_users(self, query: str, current_user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for users by name"""
        try:
            if not self.db:
                return []
            
            search_query = """
            SELECT user_id, display_name, bio, avatar_url, public_profile
            FROM user_profiles 
            WHERE (display_name LIKE ? OR bio LIKE ?) 
            AND user_id != ?
            AND public_profile = 1
            LIMIT ?
            """
            
            search_term = f"%{query}%"
            results = self.db.fetch_all(search_query, (search_term, search_term, current_user_id, limit))
            
            users = []
            for row in results:
                # Check if already friends
                friendship_status = self._check_friendship_status(current_user_id, row[0])
                
                users.append({
                    'user_id': row[0],
                    'display_name': row[1],
                    'bio': row[2],
                    'avatar_url': row[3],
                    'friendship_status': friendship_status
                })
            
            return users
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
    def _check_existing_connection(self, user1_id: str, user2_id: str) -> Optional[str]:
        """Check if connection already exists between users"""
        try:
            # Check friendship
            friendship_query = """
            SELECT id FROM friendships 
            WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
            """
            friendship = self.db.fetch_one(friendship_query, (user1_id, user2_id, user2_id, user1_id))
            
            if friendship:
                return "Already friends"
            
            # Check pending request
            request_query = """
            SELECT status FROM friend_requests 
            WHERE ((requester_id = ? AND recipient_id = ?) OR (requester_id = ? AND recipient_id = ?))
            AND status = 'pending'
            """
            request = self.db.fetch_one(request_query, (user1_id, user2_id, user2_id, user1_id))
            
            if request:
                return "Friend request pending"
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing connection: {e}")
            return "Error checking connection"
    
    def _check_friendship_status(self, user1_id: str, user2_id: str) -> str:
        """Check friendship status between two users"""
        try:
            # Check if friends
            friendship_query = """
            SELECT id FROM friendships 
            WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
            """
            friendship = self.db.fetch_one(friendship_query, (user1_id, user2_id, user2_id, user1_id))
            
            if friendship:
                return "friends"
            
            # Check pending requests
            outgoing_query = "SELECT id FROM friend_requests WHERE requester_id = ? AND recipient_id = ? AND status = 'pending'"
            incoming_query = "SELECT id FROM friend_requests WHERE requester_id = ? AND recipient_id = ? AND status = 'pending'"
            
            outgoing = self.db.fetch_one(outgoing_query, (user1_id, user2_id))
            incoming = self.db.fetch_one(incoming_query, (user2_id, user1_id))
            
            if outgoing:
                return "request_sent"
            elif incoming:
                return "request_received"
            else:
                return "none"
                
        except Exception as e:
            logger.error(f"Error checking friendship status: {e}")
            return "error"
    
    def _update_friend_count(self, user_id: str):
        """Update friend count for user"""
        try:
            count_query = """
            SELECT COUNT(*) FROM friendships 
            WHERE user1_id = ? OR user2_id = ?
            """
            result = self.db.fetch_one(count_query, (user_id, user_id))
            count = result[0] if result else 0
            
            update_query = "UPDATE user_profiles SET friend_count = ? WHERE user_id = ?"
            self.db.execute_query(update_query, (count, user_id))
            
        except Exception as e:
            logger.error(f"Error updating friend count: {e}")
    
    def _create_default_profile(self, user_id: str) -> UserProfile:
        """Create default profile for user"""
        try:
            profile = UserProfile(
                user_id=user_id,
                display_name=f"User {user_id[:8]}",
                bio=None,
                avatar_url=None,
                mood_sharing_enabled=True,
                public_profile=True,
                friend_count=0,
                joined_date=datetime.now()
            )
            
            if self.db:
                query = """
                INSERT OR IGNORE INTO user_profiles 
                (user_id, display_name, bio, avatar_url, mood_sharing_enabled, public_profile, friend_count, joined_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                self.db.execute_query(query, (
                    profile.user_id, profile.display_name, profile.bio, profile.avatar_url,
                    profile.mood_sharing_enabled, profile.public_profile, profile.friend_count, profile.joined_date
                ))
            
            return profile
            
        except Exception as e:
            logger.error(f"Error creating default profile: {e}")
            return UserProfile(
                user_id=user_id,
                display_name=f"User {user_id[:8]}",
                bio=None,
                avatar_url=None,
                mood_sharing_enabled=True,
                public_profile=True
            )

def init_social_database(db_connection):
    """Initialize social system database tables"""
    try:
        # User profiles table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                bio TEXT,
                avatar_url TEXT,
                mood_sharing_enabled BOOLEAN DEFAULT 1,
                public_profile BOOLEAN DEFAULT 1,
                friend_count INTEGER DEFAULT 0,
                joined_date DATETIME,
                INDEX(display_name),
                INDEX(public_profile)
            )
        ''')
        
        # Friend requests table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS friend_requests (
                id TEXT PRIMARY KEY,
                requester_id TEXT NOT NULL,
                recipient_id TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                INDEX(requester_id),
                INDEX(recipient_id),
                INDEX(status)
            )
        ''')
        
        # Friendships table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS friendships (
                id TEXT PRIMARY KEY,
                user1_id TEXT NOT NULL,
                user2_id TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                last_interaction DATETIME,
                INDEX(user1_id),
                INDEX(user2_id)
            )
        ''')
        
        # Social posts table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS social_posts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                post_type TEXT NOT NULL,
                content TEXT NOT NULL,
                visibility TEXT NOT NULL,
                mood_data TEXT,
                created_at DATETIME NOT NULL,
                likes_count INTEGER DEFAULT 0,
                comments_count INTEGER DEFAULT 0,
                INDEX(user_id),
                INDEX(created_at),
                INDEX(visibility)
            )
        ''')
        
        # Post likes table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS post_likes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                post_id TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                UNIQUE(user_id, post_id),
                INDEX(user_id),
                INDEX(post_id)
            )
        ''')
        
        db_connection.commit()
        logger.info("Social system database tables initialized")
        
    except Exception as e:
        logger.error(f"Error initializing social database: {e}")

# Global instance
social_manager_instance = None

def init_social_manager(db_manager, preferences_manager, notification_manager=None):
    """Initialize social manager"""
    global social_manager_instance
    try:
        social_manager_instance = SocialManager(db_manager, preferences_manager, notification_manager)
        logger.info("Social manager initialized successfully")
        return social_manager_instance
    except Exception as e:
        logger.error(f"Error initializing social manager: {e}")
        return None

def get_social_manager():
    """Get social manager instance"""
    return social_manager_instance