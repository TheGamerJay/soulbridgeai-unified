"""
Social Features API endpoints
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
import logging
import json

logger = logging.getLogger(__name__)

def create_social_api(social_manager, rate_limiter, security_monitor):
    """Create social API blueprint"""
    
    social_api = Blueprint('social', __name__, url_prefix='/api/social')
    
    def require_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    @social_api.route('/profile', methods=['GET'])
    @require_auth
    def get_profile():
        """Get user's social profile"""
        try:
            user_id = session['user_id']
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            profile = social_manager.get_user_profile(user_id)
            
            if not profile:
                return jsonify({'error': 'Profile not found'}), 404
            
            return jsonify({
                'success': True,
                'profile': {
                    'user_id': profile.user_id,
                    'display_name': profile.display_name,
                    'bio': profile.bio,
                    'avatar_url': profile.avatar_url,
                    'mood_sharing_enabled': profile.mood_sharing_enabled,
                    'public_profile': profile.public_profile,
                    'friend_count': profile.friend_count,
                    'joined_date': profile.joined_date.isoformat() if profile.joined_date else None
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/profile', methods=['PUT'])
    @require_auth
    def update_profile():
        """Update user's social profile"""
        try:
            user_id = session['user_id']
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            # Rate limiting (if available)
            if rate_limiter and not rate_limiter.check_rate_limit(f"profile_update_{user_id}", max_requests=10, window=300):
                return jsonify({'error': 'Too many profile updates. Please wait.'}), 429
            
            # Security monitoring (if available)
            if security_monitor:
                security_monitor.log_event(user_id, 'profile_update', {
                    'updated_fields': list(data.keys())
                })
            
            result = social_manager.update_user_profile(user_id, data)
            
            if not result['success']:
                return jsonify({'error': result['error']}), 500
            
            # Get updated profile
            profile = social_manager.get_user_profile(user_id)
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'profile': {
                    'user_id': profile.user_id,
                    'display_name': profile.display_name,
                    'bio': profile.bio,
                    'avatar_url': profile.avatar_url,
                    'mood_sharing_enabled': profile.mood_sharing_enabled,
                    'public_profile': profile.public_profile,
                    'friend_count': profile.friend_count
                }
            })
            
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/friends', methods=['GET'])
    @require_auth
    def get_friends():
        """Get user's friends list"""
        try:
            user_id = session['user_id']
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            friends = social_manager.get_friends_list(user_id)
            
            return jsonify({
                'success': True,
                'friends': friends,
                'count': len(friends)
            })
            
        except Exception as e:
            logger.error(f"Error getting friends: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/friend-requests', methods=['GET'])
    @require_auth
    def get_friend_requests():
        """Get pending friend requests"""
        try:
            user_id = session['user_id']
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            requests = social_manager.get_friend_requests(user_id)
            
            return jsonify({
                'success': True,
                'requests': requests,
                'count': len(requests)
            })
            
        except Exception as e:
            logger.error(f"Error getting friend requests: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/friend-requests', methods=['POST'])
    @require_auth
    def send_friend_request():
        """Send a friend request"""
        try:
            user_id = session['user_id']
            data = request.get_json()
            
            if not data or 'recipient_id' not in data:
                return jsonify({'error': 'Recipient ID required'}), 400
            
            recipient_id = data['recipient_id']
            message = data.get('message', '')
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            # Rate limiting (if available)
            if rate_limiter and not rate_limiter.check_rate_limit(f"friend_request_{user_id}", max_requests=10, window=3600):
                return jsonify({'error': 'Too many friend requests. Please wait.'}), 429
            
            # Security monitoring (if available)
            if security_monitor:
                security_monitor.log_event(user_id, 'friend_request_sent', {
                    'recipient_id': recipient_id
                })
            
            result = social_manager.send_friend_request(user_id, recipient_id, message)
            
            if not result['success']:
                return jsonify({'error': result['error']}), 400
            
            return jsonify({
                'success': True,
                'message': 'Friend request sent successfully',
                'request_id': result['request_id']
            })
            
        except Exception as e:
            logger.error(f"Error sending friend request: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/friend-requests/<request_id>', methods=['PUT'])
    @require_auth
    def respond_to_friend_request(request_id):
        """Respond to a friend request"""
        try:
            user_id = session['user_id']
            data = request.get_json()
            
            if not data or 'response' not in data:
                return jsonify({'error': 'Response required (accept, decline, block)'}), 400
            
            response = data['response']
            
            if response not in ['accept', 'decline', 'block']:
                return jsonify({'error': 'Invalid response'}), 400
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            # Security monitoring (if available)
            if security_monitor:
                security_monitor.log_event(user_id, 'friend_request_response', {
                    'request_id': request_id,
                    'response': response
                })
            
            result = social_manager.respond_to_friend_request(request_id, response, user_id)
            
            if not result['success']:
                return jsonify({'error': result['error']}), 400
            
            return jsonify({
                'success': True,
                'message': f'Friend request {response}ed successfully',
                'status': result['status']
            })
            
        except Exception as e:
            logger.error(f"Error responding to friend request: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/posts', methods=['POST'])
    @require_auth
    def create_post():
        """Create a social post"""
        try:
            user_id = session['user_id']
            data = request.get_json()
            
            if not data or 'content' not in data:
                return jsonify({'error': 'Content required'}), 400
            
            content = data['content'].strip()
            post_type = data.get('post_type', 'reflection')
            visibility = data.get('visibility', 'friends')
            mood_data = data.get('mood_data')
            
            if not content:
                return jsonify({'error': 'Content cannot be empty'}), 400
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            # Rate limiting (if available)
            if rate_limiter and not rate_limiter.check_rate_limit(f"social_post_{user_id}", max_requests=20, window=3600):
                return jsonify({'error': 'Too many posts. Please wait.'}), 429
            
            # Security monitoring (if available)
            if security_monitor:
                security_monitor.log_event(user_id, 'social_post_created', {
                    'post_type': post_type,
                    'visibility': visibility
                })
            
            result = social_manager.create_social_post(user_id, post_type, content, visibility, mood_data)
            
            if not result['success']:
                return jsonify({'error': result['error']}), 400
            
            return jsonify({
                'success': True,
                'message': 'Post created successfully',
                'post_id': result['post_id']
            })
            
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/feed', methods=['GET'])
    @require_auth
    def get_social_feed():
        """Get user's social feed"""
        try:
            user_id = session['user_id']
            limit = min(int(request.args.get('limit', 20)), 50)  # Max 50 posts
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            posts = social_manager.get_social_feed(user_id, limit)
            
            return jsonify({
                'success': True,
                'posts': posts,
                'count': len(posts)
            })
            
        except Exception as e:
            logger.error(f"Error getting social feed: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/posts/<post_id>/like', methods=['POST'])
    @require_auth
    def like_post(post_id):
        """Like or unlike a post"""
        try:
            user_id = session['user_id']
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            # Rate limiting (if available)
            if rate_limiter and not rate_limiter.check_rate_limit(f"post_like_{user_id}", max_requests=100, window=3600):
                return jsonify({'error': 'Too many like actions. Please wait.'}), 429
            
            result = social_manager.like_post(user_id, post_id)
            
            if not result['success']:
                return jsonify({'error': result['error']}), 400
            
            return jsonify({
                'success': True,
                'action': result['action'],
                'likes_count': result['likes_count']
            })
            
        except Exception as e:
            logger.error(f"Error liking post: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/search', methods=['GET'])
    @require_auth
    def search_users():
        """Search for users"""
        try:
            user_id = session['user_id']
            query = request.args.get('q', '').strip()
            limit = min(int(request.args.get('limit', 10)), 20)  # Max 20 results
            
            if not query:
                return jsonify({'error': 'Search query required'}), 400
            
            if len(query) < 2:
                return jsonify({'error': 'Search query too short'}), 400
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            # Rate limiting (if available)
            if rate_limiter and not rate_limiter.check_rate_limit(f"user_search_{user_id}", max_requests=30, window=300):
                return jsonify({'error': 'Too many searches. Please wait.'}), 429
            
            results = social_manager.search_users(query, user_id, limit)
            
            return jsonify({
                'success': True,
                'users': results,
                'count': len(results),
                'query': query
            })
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/stats', methods=['GET'])
    @require_auth
    def get_social_stats():
        """Get user's social statistics"""
        try:
            user_id = session['user_id']
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            profile = social_manager.get_user_profile(user_id)
            friends = social_manager.get_friends_list(user_id)
            pending_requests = social_manager.get_friend_requests(user_id)
            
            stats = {
                'friend_count': profile.friend_count if profile else 0,
                'pending_requests': len(pending_requests),
                'profile_completion': 0
            }
            
            # Calculate profile completion
            if profile:
                completion = 0
                if profile.display_name and profile.display_name != f"User {user_id[:8]}":
                    completion += 25
                if profile.bio:
                    completion += 25
                if profile.avatar_url:
                    completion += 25
                if profile.friend_count > 0:
                    completion += 25
                stats['profile_completion'] = completion
            
            return jsonify({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"Error getting social stats: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/messages', methods=['POST'])
    @require_auth
    def send_message():
        """Send a message to another user"""
        try:
            user_id = session['user_id']
            data = request.get_json()
            
            if not data or 'recipient_id' not in data or 'content' not in data:
                return jsonify({'error': 'Recipient ID and content required'}), 400
            
            recipient_id = data['recipient_id']
            content = data['content'].strip()
            message_type = data.get('message_type', 'text')
            metadata = data.get('metadata')
            
            if not content:
                return jsonify({'error': 'Message content cannot be empty'}), 400
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            # Rate limiting (if available)
            if rate_limiter and not rate_limiter.check_rate_limit(f"send_message_{user_id}", max_requests=50, window=3600):
                return jsonify({'error': 'Too many messages. Please wait.'}), 429
            
            # Security monitoring (if available)
            if security_monitor:
                security_monitor.log_event(user_id, 'message_sent', {
                    'recipient_id': recipient_id,
                    'message_type': message_type
                })
            
            result = social_manager.send_message(user_id, recipient_id, content, message_type, metadata)
            
            if not result['success']:
                return jsonify({'error': result['error']}), 400
            
            return jsonify({
                'success': True,
                'message': 'Message sent successfully',
                'message_id': result['message_id'],
                'conversation_id': result['conversation_id']
            })
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/conversations', methods=['GET'])
    @require_auth
    def get_conversations():
        """Get user's conversations"""
        try:
            user_id = session['user_id']
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            conversations = social_manager.get_conversations(user_id)
            
            return jsonify({
                'success': True,
                'conversations': conversations,
                'count': len(conversations)
            })
            
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/conversations/<conversation_id>/messages', methods=['GET'])
    @require_auth
    def get_messages(conversation_id):
        """Get messages in a conversation"""
        try:
            user_id = session['user_id']
            limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 messages
            before_message_id = request.args.get('before')
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            result = social_manager.get_messages(user_id, conversation_id, limit, before_message_id)
            
            if not result['success']:
                return jsonify({'error': result['error']}), 400
            
            return jsonify({
                'success': True,
                'messages': result['messages'],
                'count': len(result['messages']),
                'conversation_id': conversation_id
            })
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @social_api.route('/messages/<message_id>/read', methods=['PUT'])
    @require_auth
    def mark_message_read(message_id):
        """Mark a message as read"""
        try:
            user_id = session['user_id']
            
            if not social_manager:
                return jsonify({'error': 'Social system unavailable'}), 503
            
            result = social_manager.mark_message_as_read(user_id, message_id)
            
            if not result['success']:
                return jsonify({'error': result['error']}), 400
            
            return jsonify({
                'success': True,
                'message': 'Message marked as read'
            })
            
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return social_api

def init_social_api(social_manager, rate_limiter, security_monitor):
    """Initialize and return social API blueprint"""
    try:
        api = create_social_api(social_manager, rate_limiter, security_monitor)
        logger.info("Social API initialized successfully")
        return api
    except Exception as e:
        logger.error(f"Error initializing social API: {e}")
        return None