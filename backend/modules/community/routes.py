"""
SoulBridge AI - Community Routes
Flask Blueprint for all community-related endpoints
Extracted from backend/app.py
"""
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect
from database_utils import get_database
from ..companions.companion_data import COMPANIONS as COMPANIONS_NEW
from constants import PLAN_LIMITS
from .community_service import CommunityService
from .wellness_gallery import WellnessGallery
from .content_moderator import ContentModerator
from .companion_manager import CompanionManager

logger = logging.getLogger(__name__)

# Create Blueprint
community_bp = Blueprint('community', __name__)

# Initialize services (will be set by the main app)
community_service = None
wellness_gallery = None
content_moderator = None
companion_manager = None

def init_community_services(database=None, openai_client=None):
    """Initialize community services with dependencies"""
    global community_service, wellness_gallery, content_moderator, companion_manager
    
    try:
        companion_manager = CompanionManager()
        content_moderator = ContentModerator(openai_client)
        wellness_gallery = WellnessGallery(database, content_moderator)
        community_service = CommunityService(database, companion_manager)
        
        logger.info("🏘️ Community services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize community services: {e}")
        return False

def is_logged_in():
    """Check if user is logged in"""
    return session.get('logged_in', False) and session.get('user_id') is not None

def get_effective_plan(user_plan: str, trial_active: bool) -> str:
    """Get effective plan considering trial status"""
    if trial_active and user_plan == 'bronze':
        return 'gold'  # Trial gives Gold access
    return user_plan

def get_feature_limit(plan: str, feature: str) -> int:
    """Get feature limit for a plan"""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["bronze"]).get(feature, 0)

# =============================================================================
# COMMUNITY PAGES
# =============================================================================

@community_bp.route("/community")
def anonymous_community():
    """Anonymous Community - privacy-first sharing with companion avatars"""
    try:
        if not is_logged_in():
            return redirect("/login")
        
        return render_template("anonymous_community.html")
    except Exception as e:
        logger.error(f"Community page error: {e}")
        return redirect("/")

@community_bp.route("/community-dashboard")
def community_dashboard():
    """Wellness Gallery route (replaces old community dashboard)"""
    try:
        if not is_logged_in():
            return redirect("/login")
        return render_template("wellness_gallery.html")
    except Exception as e:
        logger.error(f"Wellness Gallery error: {e}")
        return redirect("/")

@community_bp.route("/wellness-gallery")
def wellness_gallery_page():
    """Direct route to wellness gallery"""
    try:
        if not is_logged_in():
            return redirect("/login")
        return render_template("wellness_gallery.html")
    except Exception as e:
        logger.error(f"Wellness Gallery error: {e}")
        return redirect("/")

@community_bp.route("/referrals")
def referrals_page():
    """Referrals page for earning cosmetic companions"""
    try:
        if not is_logged_in():
            return redirect("/login")
        return render_template("referrals.html")
    except Exception as e:
        logger.error(f"Referrals template error: {e}")
        return jsonify({"error": "Referrals page temporarily unavailable"}), 500

@community_bp.route("/referral")
def referral_redirect():
    """Redirect /referral to /referrals for backward compatibility"""
    return redirect("/referrals", 301)

# =============================================================================
# COMMUNITY API ENDPOINTS
# =============================================================================

@community_bp.route("/community/posts")
def community_posts():
    """Get community posts with filtering and pagination"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Parse query parameters
        category = request.args.get('category', 'all')
        sort_by = request.args.get('sort', 'new')
        limit = min(int(request.args.get('limit', 20)), 50)  # Max 50 items
        offset = int(request.args.get('offset', 0))
        
        # Mock community posts data for now
        mock_posts = [
            {
                "id": 1,
                "title": "Finding Peace Through Meditation",
                "content": "Today I discovered a wonderful guided meditation that helped me find inner calm...",
                "author": "Anonymous Companion",
                "companion_avatar": "/static/images/companions/aurora.png",
                "category": "wellness",
                "hearts": 12,
                "created_at": "2024-01-15T10:30:00Z",
                "tags": ["meditation", "mindfulness", "peace"]
            },
            {
                "id": 2,
                "title": "Creative Writing Journey",
                "content": "Sharing my latest poem about self-discovery and growth...",
                "author": "Anonymous Companion", 
                "companion_avatar": "/static/images/companions/sage.png",
                "category": "creative",
                "hearts": 8,
                "created_at": "2024-01-14T14:20:00Z",
                "tags": ["poetry", "creativity", "growth"]
            },
            {
                "id": 3,
                "title": "Daily Reflection Practice",
                "content": "How I started my morning reflection routine and the positive changes it brought...",
                "author": "Anonymous Companion",
                "companion_avatar": "/static/images/companions/luna.png", 
                "category": "wellness",
                "hearts": 15,
                "created_at": "2024-01-13T09:15:00Z",
                "tags": ["reflection", "morning", "routine"]
            },
            {
                "id": 4,
                "title": "Artistic Expression",
                "content": "Created this beautiful mandala during my art therapy session...",
                "author": "Anonymous Companion",
                "companion_avatar": "/static/images/companions/phoenix.png",
                "category": "creative", 
                "hearts": 20,
                "created_at": "2024-01-12T16:45:00Z",
                "tags": ["art", "therapy", "mandala"]
            }
        ]
        
        # Filter by category if specified
        if category != 'all':
            mock_posts = [post for post in mock_posts if post['category'] == category]
        
        # Sort posts
        if sort_by == 'popular':
            mock_posts.sort(key=lambda x: x['hearts'], reverse=True)
        elif sort_by == 'new':
            mock_posts.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Apply pagination
        total_posts = len(mock_posts)
        paginated_posts = mock_posts[offset:offset + limit]
        
        return jsonify({
            "success": True,
            "posts": paginated_posts,
            "total_count": total_posts,
            "has_more": offset + limit < total_posts,
            "categories": ["wellness", "creative", "growth", "mindfulness"],
            "sort_options": ["new", "popular"]
        })
        
    except Exception as e:
        logger.error(f"Community posts error: {e}")
        return jsonify({"success": False, "error": "Failed to load community posts"}), 500

@community_bp.route("/community/posts", methods=["POST"])
def create_community_post():
    """Create a new community post"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        text = data.get('text', '').strip()
        category = data.get('category', 'general')
        
        if not text:
            return jsonify({"success": False, "error": "Post content is required"}), 400
        
        if len(text) > 700:
            return jsonify({"success": False, "error": "Post content too long (max 700 characters)"}), 400
        
        # Mock post creation - in real app would save to database
        new_post = {
            "id": 999,  # Mock ID
            "title": text[:50] + "..." if len(text) > 50 else text,
            "content": text,
            "author": "Anonymous Companion",
            "companion_avatar": "/static/logos/New IntroLogo.png",
            "category": category,
            "hearts": 0,
            "created_at": datetime.now().isoformat(),
            "tags": []
        }
        
        logger.info(f"[COMMUNITY] Created post: {text[:50]}... in {category}")
        
        return jsonify({
            "success": True,
            "message": "Post created successfully",
            "post": new_post
        })
        
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        return jsonify({"success": False, "error": "Failed to create post"}), 500

@community_bp.route("/community/posts/<int:post_id>/react", methods=["POST"])
def react_to_post(post_id):
    """Add reaction to a post"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        emoji = data.get('emoji', '')
        if not emoji:
            return jsonify({"success": False, "error": "Emoji is required"}), 400
        
        # Mock reaction logic - in real app would save to database
        user_id = session.get('user_id')
        
        # Simulate toggling reaction
        action = 'added'  # Could be 'added' or 'removed'
        
        # Mock reaction counts
        reaction_counts = {
            "❤️": 5,
            "✨": 3, 
            "🌿": 2,
            "🔥": 8,
            "🙏": 1,
            "⭐": 0,
            "👏": 4,
            "🫶": 2
        }
        
        if emoji in reaction_counts:
            if action == 'added':
                reaction_counts[emoji] += 1
            else:
                reaction_counts[emoji] = max(0, reaction_counts[emoji] - 1)
        
        logger.info(f"[COMMUNITY] User {user_id} reacted to post {post_id} with {emoji}")
        
        return jsonify({
            "success": True,
            "action": action,
            "reaction_counts": reaction_counts
        })
        
    except Exception as e:
        logger.error(f"Error reacting to post: {e}")
        return jsonify({"success": False, "error": "Failed to react to post"}), 500

@community_bp.route("/community/posts/<int:post_id>/flag-category", methods=["POST"])
def flag_post_category(post_id):
    """Flag a post for category mismatch"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        current_category = data.get('current_category')
        suggested_category = data.get('suggested_category')
        reason = data.get('reason', 'category_mismatch')
        
        # Mock flagging logic - in real app would save to moderation queue
        user_id = session.get('user_id')
        
        logger.info(f"[COMMUNITY] User {user_id} flagged post {post_id}: {current_category} -> {suggested_category}")
        
        return jsonify({
            "success": True,
            "message": "Category flag submitted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error flagging post category: {e}")
        return jsonify({"success": False, "error": "Failed to flag post"}), 500

@community_bp.route("/community/posts/<int:post_id>/report", methods=["POST"])
def report_post(post_id):
    """Report a post for inappropriate content"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        reason = data.get('reason', '')
        notes = data.get('notes', '')
        
        if not reason:
            return jsonify({"success": False, "error": "Report reason is required"}), 400
        
        # Mock reporting logic - in real app would save to moderation queue
        user_id = session.get('user_id')
        
        logger.info(f"[COMMUNITY] User {user_id} reported post {post_id}: {reason}")
        
        return jsonify({
            "success": True,
            "message": "Report submitted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error reporting post: {e}")
        return jsonify({"success": False, "error": "Failed to report post"}), 500

@community_bp.route("/community/mute", methods=["POST"])
def mute_content():
    """Mute content (author, companion, or category)"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        mute_type = data.get('type', '')
        target = data.get('target', '')
        duration_days = data.get('duration_days', 7)
        reason = data.get('reason', 'User preference')
        
        if not mute_type or not target:
            return jsonify({"success": False, "error": "Mute type and target are required"}), 400
        
        # Mock muting logic - in real app would save to user preferences
        user_id = session.get('user_id')
        
        logger.info(f"[COMMUNITY] User {user_id} muted {mute_type}: {target} for {duration_days} days")
        
        return jsonify({
            "success": True,
            "message": f"{mute_type.title()} muted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error muting content: {e}")
        return jsonify({"success": False, "error": "Failed to mute content"}), 500

@community_bp.route("/community/companions")
def community_companions():
    """Get companions available for community avatar selection"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not companion_manager:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        user_plan = session.get("user_plan", "bronze")
        trial_active = bool(session.get("trial_active", False))
        referrals = int(session.get("referrals", 0))
        
        # Get referral count from database if available
        try:
            db_instance = get_database()
            if db_instance:
                user_id = session.get('user_id')
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                if db_instance.use_postgres:
                    cursor.execute("SELECT referral_points FROM users WHERE id = %s", (user_id,))
                else:
                    cursor.execute("SELECT referral_points FROM users WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                if result:
                    referrals = result[0] or 0
                conn.close()
        except Exception as e:
            logger.error(f"Error getting referral count: {e}")
        
        # Get available companions
        companions_result = companion_manager.get_available_companions(user_plan, trial_active, referrals)
        
        if not companions_result['success']:
            return jsonify({"success": False, "error": companions_result['error']}), 500
        
        return jsonify({
            "success": True,
            "companions": companions_result['companions']
        })
        
    except Exception as e:
        logger.error(f"Community companions error: {e}")
        return jsonify({"success": False, "error": "Failed to load companions"}), 500

@community_bp.route("/community/avatar")
def community_get_avatar():
    """Get current user's community avatar/companion"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not community_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        user_id = session.get('user_id')
        avatar_result = community_service.get_user_avatar(user_id)
        
        if not avatar_result['success']:
            return jsonify({"success": False, "error": avatar_result['error']}), 500
        
        return jsonify({
            "success": True,
            "companion": avatar_result['companion']
        })
        
    except Exception as e:
        logger.error(f"Community get avatar error: {e}")
        return jsonify({"success": False, "error": "Failed to load avatar"}), 500

@community_bp.route("/community/avatar", methods=["POST"])
def community_set_avatar():
    """Set user's community avatar/companion"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not community_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        data = request.get_json()
        companion_id = data.get('companion_id')
        
        if not companion_id:
            return jsonify({"success": False, "error": "Companion ID required"}), 400
        
        user_id = session.get('user_id')
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Verify trial status with database to prevent stale session access
        try:
            db_instance = get_database()
            if db_instance:
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                if db_instance.use_postgres:
                    cursor.execute("SELECT user_plan, trial_active FROM users WHERE id = %s", (user_id,))
                else:
                    cursor.execute("SELECT user_plan, trial_active FROM users WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                if result:
                    db_user_plan, db_trial_active = result
                    # Use database values if they differ from session
                    if db_user_plan != user_plan or bool(db_trial_active) != trial_active:
                        logger.warning(f"🔧 AVATAR SET: Session mismatch - using database values")
                        user_plan = db_user_plan
                        trial_active = bool(db_trial_active)
                        session['user_plan'] = user_plan
                        session['trial_active'] = trial_active
                        session.modified = True
                conn.close()
        except Exception as e:
            logger.error(f"Error verifying trial status in avatar set: {e}")
        
        # Find companion data
        companion_data = None
        for c in COMPANIONS_NEW:
            if c['id'] == companion_id:
                companion_data = {
                    'companion_id': c['id'],
                    'name': c['name'],
                    'avatar_url': c['image_url'],
                    'tier': c['tier']
                }
                break
        
        if not companion_data:
            return jsonify({"success": False, "error": "Invalid companion ID"}), 400
        
        # Set avatar using community service
        set_result = community_service.set_user_avatar(user_id, companion_data)
        
        if not set_result['success']:
            return jsonify({"success": False, "error": set_result['error']}), 403
        
        # Update session with new companion info
        session['companion_info'] = {
            'name': companion_data['name'],
            'id': companion_data['companion_id'],
            'image_url': companion_data['avatar_url']
        }
        session.modified = True
        
        return jsonify({
            "success": True,
            "message": "Avatar updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Community set avatar error: {e}")
        return jsonify({"success": False, "error": "Failed to update avatar"}), 500

@community_bp.route("/community/avatar/check")
def community_avatar_cooldown():
    """Check if user can change avatar (no cooldown for community)"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not community_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        user_id = session.get('user_id')
        cooldown_result = community_service.can_change_avatar(user_id)
        
        if not cooldown_result['success']:
            return jsonify({"success": False, "error": cooldown_result['error']}), 500
        
        return jsonify({
            "success": True,
            "can_change": cooldown_result['can_change']
        })
        
    except Exception as e:
        logger.error(f"Community avatar cooldown error: {e}")
        return jsonify({"success": False, "error": "Failed to check cooldown"}), 500

# =============================================================================
# WELLNESS GALLERY API ENDPOINTS
# =============================================================================

@community_bp.route("/api/share-to-wellness-gallery", methods=["POST"])
def api_share_to_wellness_gallery():
    """Share creative content to the anonymous wellness gallery"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not wellness_gallery:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        # Check if user has access (Silver/Gold tiers or active trial)
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        effective_plan = get_effective_plan(user_plan, trial_active)
        if effective_plan == 'bronze' and not trial_active:
            return jsonify({"success": False, "error": "Wellness Gallery sharing requires Silver or Gold tier"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
        
        user_id = session.get('user_id')
        share_result = wellness_gallery.share_content(user_id, data)
        
        if not share_result['success']:
            return jsonify({"success": False, "error": share_result['error']}), 400
        
        return jsonify({
            "success": True,
            "message": "Content shared successfully",
            "content_id": share_result.get('content_id')
        })
        
    except Exception as e:
        logger.error(f"Share to wellness gallery error: {e}")
        return jsonify({"success": False, "error": "Failed to share content"}), 500

@community_bp.route("/api/wellness-gallery", methods=["GET"])
def api_get_wellness_gallery():
    """Get approved content from wellness gallery"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not wellness_gallery:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        # Parse query parameters
        theme_filter = request.args.get('theme', 'all')
        content_type_filter = request.args.get('type', 'all')
        limit = min(int(request.args.get('limit', 20)), 50)  # Max 50 items
        
        filters = {
            'theme': theme_filter if theme_filter != 'all' else None,
            'content_type': content_type_filter if content_type_filter != 'all' else None,
            'limit': limit
        }
        
        gallery_result = wellness_gallery.get_gallery_content(filters)
        
        if not gallery_result['success']:
            return jsonify({"success": False, "error": gallery_result['error']}), 500
        
        return jsonify({
            "success": True,
            "content": gallery_result['content'],
            "total_count": gallery_result.get('total_count', len(gallery_result['content'])),
            "themes": community_service.get_community_themes() if community_service else [],
            "content_types": community_service.get_content_types() if community_service else []
        })
        
    except Exception as e:
        logger.error(f"Get wellness gallery error: {e}")
        return jsonify({"success": False, "error": "Failed to load gallery"}), 500

@community_bp.route("/api/wellness-gallery/heart", methods=["POST"])
def api_heart_wellness_content():
    """Add a heart to wellness gallery content"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not wellness_gallery:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        data = request.get_json()
        content_id = data.get("content_id")
        
        if not content_id:
            return jsonify({"success": False, "error": "Content ID required"}), 400
        
        user_id = session.get('user_id')
        heart_result = wellness_gallery.heart_content(user_id, content_id)
        
        if not heart_result['success']:
            return jsonify({"success": False, "error": heart_result['error']}), 404 if 'not found' in heart_result.get('error', '').lower() else 500
        
        return jsonify({
            "success": True,
            "message": "Content hearted successfully",
            "new_hearts_count": heart_result.get('hearts_count', 0)
        })
        
    except Exception as e:
        logger.error(f"Heart wellness content error: {e}")
        return jsonify({"success": False, "error": "Failed to heart content"}), 500

# =============================================================================
# REFERRALS API ENDPOINTS
# =============================================================================

@community_bp.route("/api/referrals/dashboard")
def api_referrals_dashboard():
    """Get referral dashboard data"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        
        # Get referral data from database
        referral_data = {
            'referral_code': f"SOUL{user_id}",  # Generate simple referral code
            'total_referrals': 0,
            'successful_referrals': 0,
            'referral_points': 0,
            'available_rewards': [],
            'claimed_rewards': []
        }
        
        try:
            db_instance = get_database()
            if db_instance:
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                
                # Get user referral data
                if db_instance.use_postgres:
                    cursor.execute("""
                        SELECT referral_points, referral_code 
                        FROM users WHERE id = %s
                    """, (user_id,))
                else:
                    cursor.execute("""
                        SELECT referral_points, referral_code 
                        FROM users WHERE id = ?
                    """, (user_id,))
                
                result = cursor.fetchone()
                if result:
                    points, code = result
                    referral_data['referral_points'] = points or 0
                    if code:
                        referral_data['referral_code'] = code
                
                conn.close()
                
        except Exception as e:
            logger.error(f"Error fetching referral data: {e}")
        
        # Get available companion rewards
        if companion_manager:
            rewards_result = companion_manager.get_referral_rewards()
            if rewards_result['success']:
                referral_data['available_rewards'] = rewards_result['rewards']
        
        return jsonify({
            "success": True,
            "referrals": referral_data
        })
        
    except Exception as e:
        logger.error(f"Referrals dashboard error: {e}")
        return jsonify({"success": False, "error": "Failed to load referral data"}), 500

@community_bp.route("/api/referrals/share-templates")
def api_referrals_share_templates():
    """Get referral share templates"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        referral_code = f"SOUL{user_id}"
        
        # Try to get actual referral code from database
        try:
            db_instance = get_database()
            if db_instance:
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                
                if db_instance.use_postgres:
                    cursor.execute("SELECT referral_code FROM users WHERE id = %s", (user_id,))
                else:
                    cursor.execute("SELECT referral_code FROM users WHERE id = ?", (user_id,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    referral_code = result[0]
                
                conn.close()
                
        except Exception as e:
            logger.error(f"Error fetching referral code: {e}")
        
        # Generate share templates
        base_url = "https://soulbridgeai.com"  # Update with actual domain
        referral_url = f"{base_url}/register?ref={referral_code}"
        
        templates = [
            {
                "platform": "twitter",
                "text": f"🌟 Discover SoulBridge AI - your personal wellness companion! Join me on this journey of growth and self-discovery. {referral_url} #SoulBridgeAI #Wellness #AI",
                "url": referral_url
            },
            {
                "platform": "facebook",
                "text": f"I've been using SoulBridge AI for my wellness journey and it's been amazing! Check it out and start your own path to growth: {referral_url}",
                "url": referral_url
            },
            {
                "platform": "email",
                "subject": "Discover SoulBridge AI - Your Personal Wellness Companion",
                "text": f"Hi there!\n\nI wanted to share something amazing with you - SoulBridge AI has been a game-changer for my wellness journey. It's like having a personal AI companion that helps with mindfulness, creative writing, and personal growth.\n\nI thought you might enjoy it too! You can check it out here: {referral_url}\n\nBest regards!",
                "url": referral_url
            },
            {
                "platform": "whatsapp",
                "text": f"Hey! 👋 I've been using SoulBridge AI for wellness and personal growth - it's incredible! You should check it out: {referral_url}",
                "url": f"https://wa.me/?text={referral_url}"
            }
        ]
        
        return jsonify({
            "success": True,
            "referral_code": referral_code,
            "referral_url": referral_url,
            "templates": templates
        })
        
    except Exception as e:
        logger.error(f"Referral templates error: {e}")
        return jsonify({"success": False, "error": "Failed to generate share templates"}), 500

# =============================================================================
# COMMUNITY STATS AND UTILITIES
# =============================================================================

@community_bp.route("/api/community/stats")
def api_community_stats():
    """Get community statistics"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not community_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        user_id = session.get('user_id')
        stats_result = community_service.get_community_stats(user_id)
        
        if not stats_result['success']:
            return jsonify({"success": False, "error": stats_result['error']}), 500
        
        return jsonify({
            "success": True,
            "stats": stats_result['stats']
        })
        
    except Exception as e:
        logger.error(f"Community stats error: {e}")
        return jsonify({"success": False, "error": "Failed to load community stats"}), 500

@community_bp.route("/api/community/access")
def api_community_access():
    """Validate user's access to community features"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not community_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        access_result = community_service.validate_community_access(user_plan, trial_active)
        
        if not access_result['success']:
            return jsonify({"success": False, "error": access_result['error']}), 500
        
        return jsonify({
            "success": True,
            "access": access_result['access']
        })
        
    except Exception as e:
        logger.error(f"Community access validation error: {e}")
        return jsonify({"success": False, "error": "Failed to validate access"}), 500

# =============================================================================
# BLUEPRINT REGISTRATION HELPER
# =============================================================================

def register_community_routes(app, database=None, openai_client=None):
    """Register community routes with the Flask app"""
    try:
        # Initialize services
        if not init_community_services(database, openai_client):
            logger.error("Failed to initialize community services")
            return False
        
        # Register blueprint
        app.register_blueprint(community_bp)
        
        logger.info("🏘️ Community routes registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to register community routes: {e}")
        return False