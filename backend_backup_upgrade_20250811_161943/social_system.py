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

# Import content filter for message safety
try:
    from ai_content_filter import content_filter
    CONTENT_FILTER_AVAILABLE = True
except ImportError:
    content_filter = None
    CONTENT_FILTER_AVAILABLE = False

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

class MessageType(Enum):
    TEXT = "text"
    MOOD_SHARE = "mood_share"
    ACHIEVEMENT_SHARE = "achievement_share"

class MessageStatus(Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"

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
class Message:
    id: str
    sender_id: str
    recipient_id: str
    message_type: MessageType
    content: str
    metadata: Optional[Dict] = None
    status: MessageStatus = MessageStatus.SENT
    created_at: datetime = None
    read_at: Optional[datetime] = None
    is_flagged: bool = False
    content_safe: bool = True
    moderation_score: Optional[float] = None

@dataclass
class MessageReport:
    id: str
    message_id: str
    reporter_id: str
    reported_user_id: str
    reason: str
    description: Optional[str] = None
    status: str = "pending"  # pending, reviewed, resolved, dismissed
    created_at: datetime = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

@dataclass
class Conversation:
    id: str
    user1_id: str
    user2_id: str
    last_message_id: Optional[str] = None
    last_message_at: Optional[datetime] = None
    user1_unread_count: int = 0
    user2_unread_count: int = 0
    created_at: datetime = None

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
    
    def send_message(self, sender_id: str, recipient_id: str, content: str, message_type: str = "text", metadata: Dict = None) -> Dict[str, Any]:
        """Send a message to another user"""
        try:
            if not self.db:
                return {'success': False, 'error': 'Database unavailable'}
            
            # Validate message type
            if message_type not in [e.value for e in MessageType]:
                return {'success': False, 'error': 'Invalid message type'}
            
            # Check if users are friends
            friendship_status = self._check_friendship_status(sender_id, recipient_id)
            if friendship_status != "friends":
                return {'success': False, 'error': 'Can only message friends'}
            
            # Check privacy settings
            recipient_prefs = self.preferences.get_user_preferences(recipient_id) if self.preferences else {}
            privacy = recipient_prefs.get('privacy', {})
            
            if not privacy.get('allow_messages', True):
                return {'success': False, 'error': 'User has disabled messages'}
            
            # Content safety check
            content_safe = True
            moderation_score = None
            if CONTENT_FILTER_AVAILABLE and content_filter:
                is_safe, refusal_message = content_filter.check_content(content, "Blayzo", sender_id)
                if not is_safe:
                    logger.warning(f"Message blocked by content filter: {sender_id} -> {recipient_id}")
                    return {'success': False, 'error': 'Message content violates community guidelines'}
                
                # Get content analysis for scoring
                try:
                    analysis = content_filter._analyze_content_advanced(content, "Blayzo", sender_id)
                    moderation_score = analysis.confidence if analysis else None
                    content_safe = analysis.is_safe if analysis else True
                except Exception as e:
                    logger.warning(f"Error getting content analysis: {e}")
            
            # Create or get conversation
            conversation_id = self._get_or_create_conversation(sender_id, recipient_id)
            
            # Create message
            message_id = str(uuid.uuid4())
            message = Message(
                id=message_id,
                sender_id=sender_id,
                recipient_id=recipient_id,
                message_type=MessageType(message_type),
                content=content.strip(),
                metadata=metadata,
                status=MessageStatus.SENT,
                created_at=datetime.now(),
                content_safe=content_safe,
                moderation_score=moderation_score
            )
            
            # Insert message
            query = """
            INSERT INTO messages 
            (id, conversation_id, sender_id, recipient_id, message_type, content, metadata, status, created_at, is_flagged, content_safe, moderation_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                message.id, conversation_id, message.sender_id, message.recipient_id,
                message.message_type.value, message.content, 
                json.dumps(message.metadata) if message.metadata else None,
                message.status.value, message.created_at, False, content_safe, moderation_score
            ))
            
            # Update conversation
            self._update_conversation(conversation_id, message_id, sender_id, recipient_id)
            
            # Send notification
            if self.notifications:
                sender_profile = self.get_user_profile(sender_id)
                self.notifications.send_notification(
                    user_id=recipient_id,
                    title=f"New message from {sender_profile.display_name}",
                    message=content[:100] + "..." if len(content) > 100 else content,
                    notification_type="message",
                    metadata={'message_id': message_id, 'sender_id': sender_id, 'conversation_id': conversation_id}
                )
            
            logger.info(f"Message sent from {sender_id} to {recipient_id}")
            return {'success': True, 'message_id': message_id, 'conversation_id': conversation_id}
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {'success': False, 'error': 'Failed to send message'}
    
    def get_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's conversations"""
        try:
            if not self.db:
                return []
            
            query = """
            SELECT c.id, c.user1_id, c.user2_id, c.last_message_id, c.last_message_at,
                   c.user1_unread_count, c.user2_unread_count,
                   m.content as last_message, m.sender_id as last_sender,
                   up.display_name, up.avatar_url
            FROM conversations c
            LEFT JOIN messages m ON c.last_message_id = m.id
            LEFT JOIN user_profiles up ON (
                CASE WHEN c.user1_id = ? THEN c.user2_id ELSE c.user1_id END = up.user_id
            )
            WHERE c.user1_id = ? OR c.user2_id = ?
            ORDER BY c.last_message_at DESC
            """
            
            results = self.db.fetch_all(query, (user_id, user_id, user_id))
            
            conversations = []
            for row in results:
                other_user_id = row[2] if row[1] == user_id else row[1]
                unread_count = row[6] if row[1] == user_id else row[5]
                
                conversations.append({
                    'id': row[0],
                    'other_user_id': other_user_id,
                    'other_user_name': row[9] or 'Unknown User',
                    'other_user_avatar': row[10],
                    'last_message': row[7],
                    'last_message_sender': row[8],
                    'last_message_at': row[4],
                    'unread_count': unread_count,
                    'is_last_message_mine': row[8] == user_id if row[8] else False
                })
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return []
    
    def get_messages(self, user_id: str, conversation_id: str, limit: int = 50, before_message_id: str = None) -> Dict[str, Any]:
        """Get messages in a conversation"""
        try:
            if not self.db:
                return {'success': False, 'error': 'Database unavailable'}
            
            # Verify user is part of conversation
            conv_query = "SELECT user1_id, user2_id FROM conversations WHERE id = ?"
            conv_result = self.db.fetch_one(conv_query, (conversation_id,))
            
            if not conv_result or user_id not in [conv_result[0], conv_result[1]]:
                return {'success': False, 'error': 'Conversation not found'}
            
            # Build query
            base_query = """
            SELECT m.id, m.sender_id, m.recipient_id, m.message_type, m.content, 
                   m.metadata, m.status, m.created_at, m.read_at,
                   up.display_name, up.avatar_url
            FROM messages m
            LEFT JOIN user_profiles up ON m.sender_id = up.user_id
            WHERE m.conversation_id = ?
            """
            
            params = [conversation_id]
            
            if before_message_id:
                # Get timestamp of before_message_id for pagination
                timestamp_query = "SELECT created_at FROM messages WHERE id = ?"
                timestamp_result = self.db.fetch_one(timestamp_query, (before_message_id,))
                if timestamp_result:
                    base_query += " AND m.created_at < ?"
                    params.append(timestamp_result[0])
            
            base_query += " ORDER BY m.created_at DESC LIMIT ?"
            params.append(limit)
            
            results = self.db.fetch_all(base_query, params)
            
            messages = []
            for row in results:
                metadata = None
                if row[5]:
                    try:
                        metadata = json.loads(row[5])
                    except json.JSONDecodeError:
                        pass
                
                messages.append({
                    'id': row[0],
                    'sender_id': row[1],
                    'recipient_id': row[2],
                    'message_type': row[3],
                    'content': row[4],
                    'metadata': metadata,
                    'status': row[6],
                    'created_at': row[7],
                    'read_at': row[8],
                    'sender_name': row[9] or 'Unknown User',
                    'sender_avatar': row[10],
                    'is_mine': row[1] == user_id
                })
            
            # Mark messages as read
            self._mark_messages_as_read(user_id, conversation_id)
            
            # Reverse to show oldest first
            messages.reverse()
            
            return {'success': True, 'messages': messages}
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return {'success': False, 'error': 'Failed to get messages'}
    
    def mark_message_as_read(self, user_id: str, message_id: str) -> Dict[str, Any]:
        """Mark a specific message as read"""
        try:
            if not self.db:
                return {'success': False, 'error': 'Database unavailable'}
            
            # Verify user is recipient
            query = "SELECT recipient_id, conversation_id FROM messages WHERE id = ?"
            result = self.db.fetch_one(query, (message_id,))
            
            if not result or result[0] != user_id:
                return {'success': False, 'error': 'Message not found'}
            
            # Update message status
            update_query = """
            UPDATE messages 
            SET status = ?, read_at = ?
            WHERE id = ? AND recipient_id = ? AND status != 'read'
            """
            
            self.db.execute_query(update_query, (
                MessageStatus.READ.value, datetime.now(), message_id, user_id
            ))
            
            # Update conversation unread count
            self._update_unread_count(result[1], user_id)
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return {'success': False, 'error': 'Failed to mark message as read'}
    
    def _get_or_create_conversation(self, user1_id: str, user2_id: str) -> str:
        """Get existing conversation or create new one"""
        try:
            # Check for existing conversation
            query = """
            SELECT id FROM conversations 
            WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
            """
            result = self.db.fetch_one(query, (user1_id, user2_id, user2_id, user1_id))
            
            if result:
                return result[0]
            
            # Create new conversation
            conversation_id = str(uuid.uuid4())
            conversation = Conversation(
                id=conversation_id,
                user1_id=user1_id,
                user2_id=user2_id,
                created_at=datetime.now()
            )
            
            insert_query = """
            INSERT INTO conversations (id, user1_id, user2_id, created_at)
            VALUES (?, ?, ?, ?)
            """
            
            self.db.execute_query(insert_query, (
                conversation.id, conversation.user1_id, conversation.user2_id, conversation.created_at
            ))
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error getting/creating conversation: {e}")
            raise
    
    def _update_conversation(self, conversation_id: str, message_id: str, sender_id: str, recipient_id: str):
        """Update conversation with latest message"""
        try:
            query = """
            UPDATE conversations 
            SET last_message_id = ?, 
                last_message_at = ?,
                user1_unread_count = CASE 
                    WHEN user1_id = ? THEN user1_unread_count 
                    ELSE user1_unread_count + 1 
                END,
                user2_unread_count = CASE 
                    WHEN user2_id = ? THEN user2_unread_count 
                    ELSE user2_unread_count + 1 
                END
            WHERE id = ?
            """
            
            self.db.execute_query(query, (
                message_id, datetime.now(), sender_id, sender_id, conversation_id
            ))
            
        except Exception as e:
            logger.error(f"Error updating conversation: {e}")
    
    def _mark_messages_as_read(self, user_id: str, conversation_id: str):
        """Mark all unread messages in conversation as read"""
        try:
            # Mark messages as read
            query = """
            UPDATE messages 
            SET status = ?, read_at = ?
            WHERE conversation_id = ? AND recipient_id = ? AND status != 'read'
            """
            
            self.db.execute_query(query, (
                MessageStatus.READ.value, datetime.now(), conversation_id, user_id
            ))
            
            # Reset unread count
            self._update_unread_count(conversation_id, user_id)
            
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")
    
    def _update_unread_count(self, conversation_id: str, user_id: str):
        """Reset unread count for user in conversation"""
        try:
            query = """
            UPDATE conversations 
            SET user1_unread_count = CASE WHEN user1_id = ? THEN 0 ELSE user1_unread_count END,
                user2_unread_count = CASE WHEN user2_id = ? THEN 0 ELSE user2_unread_count END
            WHERE id = ?
            """
            
            self.db.execute_query(query, (user_id, user_id, conversation_id))
            
        except Exception as e:
            logger.error(f"Error updating unread count: {e}")
    
    def report_message(self, reporter_id: str, message_id: str, reason: str, description: str = "") -> Dict[str, Any]:
        """Report a message for inappropriate content"""
        try:
            if not self.db:
                return {'success': False, 'error': 'Database unavailable'}
            
            # Get message details
            message_query = "SELECT sender_id, recipient_id, content FROM messages WHERE id = ?"
            message_result = self.db.fetch_one(message_query, (message_id,))
            
            if not message_result:
                return {'success': False, 'error': 'Message not found'}
            
            reported_user_id = message_result[0]  # sender_id
            recipient_id = message_result[1]
            
            # Verify reporter has access to this message (is sender or recipient)
            if reporter_id not in [reported_user_id, recipient_id]:
                return {'success': False, 'error': 'You can only report messages you have access to'}
            
            # Check if already reported by this user
            existing_query = "SELECT id FROM message_reports WHERE message_id = ? AND reporter_id = ?"
            existing = self.db.fetch_one(existing_query, (message_id, reporter_id))
            
            if existing:
                return {'success': False, 'error': 'You have already reported this message'}
            
            # Create report
            report_id = str(uuid.uuid4())
            report = MessageReport(
                id=report_id,
                message_id=message_id,
                reporter_id=reporter_id,
                reported_user_id=reported_user_id,
                reason=reason,
                description=description,
                status="pending",
                created_at=datetime.now()
            )
            
            # Insert report
            report_query = """
            INSERT INTO message_reports 
            (id, message_id, reporter_id, reported_user_id, reason, description, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(report_query, (
                report.id, report.message_id, report.reporter_id, report.reported_user_id,
                report.reason, report.description, report.status, report.created_at
            ))
            
            # Flag the message
            flag_query = "UPDATE messages SET is_flagged = 1 WHERE id = ?"
            self.db.execute_query(flag_query, (message_id,))
            
            # Send notification to admins/moderators
            if self.notifications:
                self.notifications.send_notification(
                    user_id="admin",  # Special admin notification
                    title="Message Reported",
                    message=f"Message reported for: {reason}",
                    notification_type="moderation",
                    metadata={'report_id': report_id, 'message_id': message_id}
                )
            
            logger.info(f"Message reported: {message_id} by {reporter_id} for {reason}")
            return {'success': True, 'report_id': report_id}
            
        except Exception as e:
            logger.error(f"Error reporting message: {e}")
            return {'success': False, 'error': 'Failed to report message'}
    
    def get_message_reports(self, admin_user_id: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Get message reports (admin only)"""
        try:
            if not self.db:
                return []
            
            # TODO: Add admin permission check
            # if not self._is_admin(admin_user_id):
            #     return []
            
            base_query = """
            SELECT mr.id, mr.message_id, mr.reporter_id, mr.reported_user_id, mr.reason, 
                   mr.description, mr.status, mr.created_at, mr.reviewed_at, mr.reviewed_by,
                   m.content, m.created_at as message_date,
                   up1.display_name as reporter_name,
                   up2.display_name as reported_name
            FROM message_reports mr
            LEFT JOIN messages m ON mr.message_id = m.id
            LEFT JOIN user_profiles up1 ON mr.reporter_id = up1.user_id
            LEFT JOIN user_profiles up2 ON mr.reported_user_id = up2.user_id
            """
            
            params = []
            if status:
                base_query += " WHERE mr.status = ?"
                params.append(status)
            
            base_query += " ORDER BY mr.created_at DESC"
            
            results = self.db.fetch_all(base_query, params)
            
            reports = []
            for row in results:
                reports.append({
                    'id': row[0],
                    'message_id': row[1],
                    'reporter_id': row[2],
                    'reported_user_id': row[3],
                    'reason': row[4],
                    'description': row[5],
                    'status': row[6],
                    'created_at': row[7],
                    'reviewed_at': row[8],
                    'reviewed_by': row[9],
                    'message_content': row[10],
                    'message_date': row[11],
                    'reporter_name': row[12] or 'Unknown User',
                    'reported_name': row[13] or 'Unknown User'
                })
            
            return reports
            
        except Exception as e:
            logger.error(f"Error getting message reports: {e}")
            return []
    
    def review_message_report(self, report_id: str, action: str, reviewer_id: str) -> Dict[str, Any]:
        """Review a message report (admin only)"""
        try:
            if not self.db:
                return {'success': False, 'error': 'Database unavailable'}
            
            # TODO: Add admin permission check
            # if not self._is_admin(reviewer_id):
            #     return {'success': False, 'error': 'Admin privileges required'}
            
            if action not in ['dismiss', 'warning', 'remove_message', 'suspend_user']:
                return {'success': False, 'error': 'Invalid action'}
            
            # Get report details
            report_query = "SELECT message_id, reported_user_id FROM message_reports WHERE id = ?"
            report_result = self.db.fetch_one(report_query, (report_id,))
            
            if not report_result:
                return {'success': False, 'error': 'Report not found'}
            
            message_id = report_result[0]
            reported_user_id = report_result[1]
            
            # Update report status
            status = "resolved" if action != "dismiss" else "dismissed"
            review_query = """
            UPDATE message_reports 
            SET status = ?, reviewed_at = ?, reviewed_by = ?
            WHERE id = ?
            """
            
            self.db.execute_query(review_query, (
                status, datetime.now(), reviewer_id, report_id
            ))
            
            # Take action based on review
            if action == "remove_message":
                # Soft delete message (mark as removed)
                delete_query = "UPDATE messages SET content = '[Message removed by moderator]', is_flagged = 1 WHERE id = ?"
                self.db.execute_query(delete_query, (message_id,))
            
            elif action == "warning":
                # Send warning notification
                if self.notifications:
                    self.notifications.send_notification(
                        user_id=reported_user_id,
                        title="Community Guidelines Warning",
                        message="Your recent message was reported and found to violate community guidelines. Please review our guidelines.",
                        notification_type="warning",
                        metadata={'report_id': report_id}
                    )
            
            elif action == "suspend_user":
                # TODO: Implement user suspension logic
                pass
            
            logger.info(f"Report {report_id} reviewed with action: {action}")
            return {'success': True, 'action': action}
            
        except Exception as e:
            logger.error(f"Error reviewing message report: {e}")
            return {'success': False, 'error': 'Failed to review report'}

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
        
        # Conversations table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user1_id TEXT NOT NULL,
                user2_id TEXT NOT NULL,
                last_message_id TEXT,
                last_message_at DATETIME,
                user1_unread_count INTEGER DEFAULT 0,
                user2_unread_count INTEGER DEFAULT 0,
                created_at DATETIME NOT NULL,
                INDEX(user1_id),
                INDEX(user2_id),
                INDEX(last_message_at)
            )
        ''')
        
        # Messages table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                recipient_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                status TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                read_at DATETIME,
                is_flagged BOOLEAN DEFAULT 0,
                content_safe BOOLEAN DEFAULT 1,
                moderation_score REAL,
                INDEX(conversation_id),
                INDEX(sender_id),
                INDEX(recipient_id),
                INDEX(created_at),
                INDEX(status),
                INDEX(is_flagged)
            )
        ''')
        
        # Message reports table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS message_reports (
                id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                reporter_id TEXT NOT NULL,
                reported_user_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at DATETIME NOT NULL,
                reviewed_at DATETIME,
                reviewed_by TEXT,
                INDEX(message_id),
                INDEX(reporter_id),
                INDEX(reported_user_id),
                INDEX(status),
                INDEX(created_at)
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