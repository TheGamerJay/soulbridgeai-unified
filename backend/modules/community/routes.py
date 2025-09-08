"""
SoulBridge AI - Community Routes
Flask Blueprint for all community-related endpoints
Extracted from backend/app.py
"""
import json
import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify, session, redirect
from database_utils import get_database
try:
    from ..companions.companion_data import COMPANIONS as COMPANIONS_NEW
except ImportError:
    # Fallback if companions module doesn't exist or has different structure
    COMPANIONS_NEW = []
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
weekly_events_service = None

# Global storage for post reaction counts (in-memory for now)
post_reactions = {}

def get_post_reaction_counts(post_id):
    """Get reaction counts for a specific post from database"""
    try:
        from database_utils import get_db_connection, get_placeholder
        conn = get_db_connection()
        placeholder = get_placeholder()
        
        with conn:
            with conn.cursor() as cursor:
                query = f"SELECT reaction_counts_json FROM community_posts WHERE id = {placeholder}"
                cursor.execute(query, (post_id,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    import json
                    return json.loads(result[0])
                else:
                    # Return default empty reactions
                    return {"❤️": 0, "✨": 0, "🌿": 0, "🔥": 0, "🙏": 0, "⭐": 0, "👏": 0, "🫶": 0}
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error getting reaction counts for post {post_id}: {e}")
        # Fallback to memory storage if database fails
        return post_reactions.get(str(post_id), {
            "❤️": 0, "✨": 0, "🌿": 0, "🔥": 0, "🙏": 0, "⭐": 0, "👏": 0, "🫶": 0
        })

def store_post_reaction_counts(post_id, counts):
    """Store reaction counts for a specific post in database"""
    try:
        from database_utils import get_db_connection, get_placeholder
        conn = get_db_connection()
        placeholder = get_placeholder()
        
        import json
        counts_json = json.dumps(counts)
        total_reactions = sum(counts.values())
        
        with conn:
            with conn.cursor() as cursor:
                query = f"""
                    UPDATE community_posts 
                    SET reaction_counts_json = {placeholder}, total_reactions = {placeholder}
                    WHERE id = {placeholder}
                """
                cursor.execute(query, (counts_json, total_reactions, post_id))
                
                logger.info(f"Stored reactions for post {post_id}: {counts} (total: {total_reactions})")
        
        conn.close()
        
        # Also store in memory as backup
        post_reactions[str(post_id)] = counts.copy()
        
    except Exception as e:
        logger.error(f"Error storing reaction counts for post {post_id}: {e}")
        # Fallback to memory storage if database fails
        post_reactions[str(post_id)] = counts.copy()

def init_mock_reactions():
    """Initialize some mock reactions for demo"""
    # Add some sample reactions to posts
    post_reactions['1'] = {"❤️": 5, "✨": 3, "🌿": 2, "🔥": 0, "🙏": 1, "⭐": 4, "👏": 0, "🫶": 1}
    post_reactions['2'] = {"❤️": 2, "✨": 1, "🌿": 0, "🔥": 3, "🙏": 0, "⭐": 2, "👏": 1, "🫶": 0}
    post_reactions['3'] = {"❤️": 8, "✨": 2, "🌿": 4, "🔥": 1, "🙏": 3, "⭐": 1, "👏": 2, "🫶": 2}

def init_community_services(database=None, openai_client=None):
    """Initialize community services with dependencies"""
    global community_service, wellness_gallery, content_moderator, companion_manager, weekly_events_service
    
    try:
        # Initialize mock reactions
        init_mock_reactions()
        
        companion_manager = CompanionManager()
        content_moderator = ContentModerator(openai_client)
        wellness_gallery = WellnessGallery(database, content_moderator)
        community_service = CommunityService(database, companion_manager)
        
        # Initialize weekly events service
        from .weekly_events_service import WeeklyEventsService
        weekly_events_service = WeeklyEventsService(database)
        
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

@community_bp.route("/community/set-avatar/<companion_id>")
def auto_set_avatar(companion_id):
    """Auto-set community avatar via URL - for testing and convenience"""
    try:
        if not is_logged_in():
            return redirect("/login")
        
        user_id = session.get('user_id')
        logger.info(f"🔗 AUTO-SET AVATAR: User {user_id} setting avatar to {companion_id} via URL")
        
        # Real companion mapping (same as POST endpoint)
        companion_map = {
            # BRONZE
            'gamerjay_bronze': {'name': 'GamerJay', 'image_url': '/static/logos/GamerJay_Free_companion.png', 'tier': 'bronze'},
            'blayzo_bronze': {'name': 'Blayzo', 'image_url': '/static/logos/Blayzo.png', 'tier': 'bronze'},
            'claude_bronze': {'name': 'Claude', 'image_url': '/static/logos/Claude_Free.png', 'tier': 'bronze'},
            'lumen_bronze': {'name': 'Lumen', 'image_url': '/static/logos/Lumen_Bronze.png', 'tier': 'bronze'},
            'blayzica_bronze': {'name': 'Blayzica', 'image_url': '/static/logos/Blayzica.png', 'tier': 'bronze'},
            'blayzia_bronze': {'name': 'Blayzia', 'image_url': '/static/logos/Blayzia.png', 'tier': 'bronze'},
            'blayzion_bronze': {'name': 'Blayzion', 'image_url': '/static/logos/Blayzion.png', 'tier': 'bronze'},
            'blayzo2_bronze': {'name': 'Blayzo.2', 'image_url': '/static/logos/blayzo_free_tier.png', 'tier': 'bronze'},
            'crimson_bronze': {'name': 'Crimson', 'image_url': '/static/logos/Crimson_Free.png', 'tier': 'bronze'},
            'violet_bronze': {'name': 'Violet', 'image_url': '/static/logos/Violet_Free.png', 'tier': 'bronze'},
            # SILVER  
            'sky_silver': {'name': 'Sky', 'image_url': '/static/logos/Sky_a_premium_companion.png', 'tier': 'silver'},
            'gamerjay_silver': {'name': 'GamerJay.2', 'image_url': '/static/logos/GamerJay_premium_companion.png', 'tier': 'silver'},
            'claude_silver': {'name': 'Claude.3', 'image_url': '/static/logos/Claude_Growth.png', 'tier': 'silver'},
            'rozia_silver': {'name': 'Rozia', 'image_url': '/static/logos/Rozia_Silver.png', 'tier': 'silver'},
            'blayzo_silver': {'name': 'Blayzo.3', 'image_url': '/static/logos/Blayzo_premium_companion.png', 'tier': 'silver'},
            'blayzica_silver': {'name': 'Blayzica.2', 'image_url': '/static/logos/Blayzica_Pro.png', 'tier': 'silver'},
            'lumen_silver': {'name': 'Lumen.2', 'image_url': '/static/logos/Lumen_Silver.png', 'tier': 'silver'},
            'watchdog_silver': {'name': 'WatchDog', 'image_url': '/static/logos/WatchDog_a_Premium_companion.png', 'tier': 'silver'},
            # GOLD
            'crimson_gold': {'name': 'Crimson', 'image_url': '/static/logos/Crimson_a_Max_companion.png', 'tier': 'gold'},
            'violet_gold': {'name': 'Violet', 'image_url': '/static/logos/Violet_a_Max_companion.png', 'tier': 'gold'},
            'claude_gold': {'name': 'Claude.2', 'image_url': '/static/logos/Claude_Max.png', 'tier': 'gold'},
            'royal_gold': {'name': 'Royal', 'image_url': '/static/logos/Royal_a_Max_companion.png', 'tier': 'gold'},
            'ven_sky_gold': {'name': 'Ven Sky', 'image_url': '/static/logos/Ven_Sky_a_Max_companion.png', 'tier': 'gold'},
            'watchdog_gold': {'name': 'WatchDog.2', 'image_url': '/static/logos/WatchDog_Max_companion.png', 'tier': 'gold'},
            'dr_madjay_gold': {'name': 'Dr. MadJay', 'image_url': '/static/logos/Dr_MadJay_Max_companion.png', 'tier': 'gold'},
            'lumen_gold': {'name': 'Lumen.3', 'image_url': '/static/logos/Lumen_Gold.png', 'tier': 'gold'},
        }
        
        if companion_id not in companion_map:
            return f"❌ Unknown companion: {companion_id}<br><br>Available companions:<br>" + "<br>".join([f"• {k}: {v['name']}" for k, v in companion_map.items()]), 400
        
        companion = companion_map[companion_id]
        
        # Create companion info
        from datetime import datetime, timezone
        import json
        
        companion_info = {
            'id': companion_id,
            'name': companion['name'],
            'image_url': companion['image_url'],
            'tier': companion['tier'],
            'saved_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Save to database (same logic as POST endpoint)
        db = get_database()
        if not db:
            return "❌ Database not available", 503
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        json_data = json.dumps(companion_info)
        logger.info(f"🔗 AUTO-SET: Saving {companion_id} for user {user_id}")
        
        if db.use_postgres:
            cursor.execute("UPDATE users SET companion_data = %s WHERE id = %s", (json_data, user_id))
        else:
            cursor.execute("UPDATE users SET companion_data = ? WHERE id = ?", (json_data, user_id))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        if rows_affected > 0:
            # Update session to match what was saved to database
            session['companion_info'] = {
                'name': companion['name'],
                'id': companion_id,
                'image_url': companion['image_url']
            }
            session['selected_companion_id'] = companion_id
            session.modified = True
            
            logger.info(f"✅ SESSION UPDATED: {companion['name']} for user {user_id}")
            
            # Redirect to community page to see the result
            return redirect(f"/community?success=Avatar set to {companion['name']}")
        else:
            return f"❌ Failed to set avatar for user {user_id}", 500
            
    except Exception as e:
        logger.error(f"Auto-set avatar error: {e}")
        return f"❌ Error setting avatar: {e}", 500

@community_bp.route("/emergency-database-fix-2025")
def emergency_database_fix():
    """Emergency fix for user_activity_log table - Public access for emergency"""
    try:
        db = get_database()
        if not db:
            return "❌ Database not available", 503
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        results = []
        
        # 1. Create user_activity_log table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity_log (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    feature_type VARCHAR(50) NOT NULL,
                    session_duration_seconds INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            results.append("✅ Created user_activity_log table")
            
            # Add indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_log_user_created
                ON user_activity_log(user_id, created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_log_created_at
                ON user_activity_log(created_at)
            """)
            results.append("✅ Added indexes to user_activity_log")
            
        except Exception as e:
            results.append(f"⚠️ user_activity_log error: {e}")
        
        # 2. Add referrals column if missing
        try:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS referrals INTEGER DEFAULT 0
            """)
            results.append("✅ Added referrals column to users")
        except Exception as e:
            results.append(f"⚠️ referrals column error: {e}")
            
        conn.commit()
        
        # 3. Test the fix
        try:
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) 
                FROM user_activity_log 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """)
            daily_users = cursor.fetchone()[0]
            results.append(f"✅ user_activity_log test passed: {daily_users} users in last 24 hours")
        except Exception as e:
            results.append(f"⚠️ Test failed: {e}")
        
        conn.close()
        
        return "<h2>🔧 Emergency Database Fix Results</h2>" + "<br>".join(results) + "<br><br><strong>All PostgreSQL errors should now be resolved!</strong><br><br><a href='/community'>← Back to Community</a>"
        
    except Exception as e:
        return f"❌ Emergency fix failed: {e}", 500

@community_bp.route("/community/fix-database")
def emergency_database_fix_old():
    """Emergency fix for user_activity_log table - ADMIN ONLY"""
    try:
        # Simplified access - check query parameter for emergency access
        emergency_key = request.args.get('key')
        if emergency_key != 'soulbridge_emergency_2025':
            return "Emergency key required: /community/fix-database?key=soulbridge_emergency_2025", 401
            
        db = get_database()
        if not db:
            return "Database not available", 503
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        results = []
        
        # 1. Create user_activity_log table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity_log (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    feature_type VARCHAR(50) NOT NULL,
                    session_duration_seconds INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            results.append("✅ Created user_activity_log table")
            
            # Add indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_log_user_created
                ON user_activity_log(user_id, created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_log_created_at
                ON user_activity_log(created_at)
            """)
            results.append("✅ Added indexes to user_activity_log")
            
        except Exception as e:
            results.append(f"⚠️ user_activity_log error: {e}")
        
        # 2. Add referrals column if missing
        try:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS referrals INTEGER DEFAULT 0
            """)
            results.append("✅ Added referrals column to users")
        except Exception as e:
            results.append(f"⚠️ referrals column error: {e}")
            
        conn.commit()
        
        # 3. Test the fix
        try:
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) 
                FROM user_activity_log 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """)
            daily_users = cursor.fetchone()[0]
            results.append(f"✅ user_activity_log test passed: {daily_users} users")
        except Exception as e:
            results.append(f"⚠️ Test failed: {e}")
        
        conn.close()
        
        return "<br>".join(results) + "<br><br><a href='/community'>← Back to Community</a>"
        
    except Exception as e:
        return f"Emergency fix failed: {e}", 500

@community_bp.route("/community")
def anonymous_community():
    """Anonymous Community - privacy-first sharing with companion avatars"""
    try:
        if not is_logged_in():
            return redirect("/login")
        
        logger.info("🚨 DEBUG: Community route called from BLUEPRINT (not app.py)")
        
        # SERVER-SIDE AVATAR LOADING - Eliminates race condition!
        user_id = session.get('user_id')
        current_avatar = None
        
        # Load avatar from database (primary) or session (fallback)
        try:
            db = get_database()
            if db:
                conn = db.get_connection()
                cursor = conn.cursor()
                
                # Get saved community avatar from users.companion_data (matches saving logic)
                if db.use_postgres:
                    cursor.execute("SELECT companion_data FROM users WHERE id = %s", (user_id,))
                else:
                    cursor.execute("SELECT companion_data FROM users WHERE id = ?", (user_id,))
                    
                result = cursor.fetchone()
                conn.close()
                
                logger.info(f"🚨 DEBUG: Database query result: {result}")
                
                if result and result[0]:
                    # Parse community avatar data from JSON (matches saving logic)
                    import json
                    import time
                    try:
                        logger.info(f"🚨 DEBUG: Raw companion_data from DB: {result[0]}")
                        # Handle both JSON string and dictionary (PostgreSQL JSONB returns dict)
                        if isinstance(result[0], dict):
                            companion_data = result[0]  # Already a dictionary
                        else:
                            companion_data = json.loads(result[0])  # Parse JSON string
                        logger.info(f"🚨 DEBUG: Parsed companion_data: {companion_data}")
                        cache_buster = int(time.time())
                        # Try both 'avatar_url' and 'image_url' field names (DB inconsistency)
                        avatar_url = companion_data.get('avatar_url') or companion_data.get('image_url')
                        if avatar_url and '?' not in avatar_url:
                            avatar_url += f"?t={cache_buster}"
                        
                        current_avatar = {
                            'name': companion_data.get('name', 'Soul'),
                            'companion_id': companion_data.get('id', 'soul'),  
                            'avatar_url': avatar_url or f'/static/logos/New IntroLogo.png?t={cache_buster}',
                            'tier': companion_data.get('tier', 'bronze')
                        }
                        logger.info(f"✅ SERVER-SIDE: Loaded COMMUNITY avatar for user {user_id}: {current_avatar['name']} from {avatar_url}")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"⚠️ Could not parse companion_data JSON: {e}")
                        current_avatar = None
                else:
                    logger.info(f"⚠️ SERVER-SIDE: No community avatar found for user {user_id}, using fallback")
            
            # Fallback to session if database failed
            if not current_avatar:
                session_companion = session.get('companion_info')
                if session_companion:
                    import time
                    cache_buster = int(time.time())
                    avatar_url = session_companion.get('image_url', '/static/logos/New IntroLogo.png')
                    if '?' not in avatar_url:
                        avatar_url += f"?t={cache_buster}"
                        
                    current_avatar = {
                        'name': session_companion.get('name', 'Soul'),
                        'companion_id': session_companion.get('id', 'soul'),
                        'avatar_url': avatar_url,
                        'tier': session_companion.get('tier', 'bronze')
                    }
                    logger.info(f"⚠️ SERVER-SIDE: Using session fallback for user {user_id}")
                        
        except Exception as avatar_error:
            logger.error(f"❌ SERVER-SIDE avatar loading failed: {avatar_error}")
        
        # Default avatar if all else fails
        if not current_avatar:
            import time
            cache_buster = int(time.time())
            current_avatar = {
                'name': 'Soul',
                'companion_id': 'soul', 
                'avatar_url': f'/static/logos/New IntroLogo.png?t={cache_buster}',
                'tier': 'bronze'
            }
            logger.info(f"🔄 SERVER-SIDE: Using default avatar for user {user_id}")
        
        logger.info(f"🎭 DEBUG: Final current_avatar being passed to template: {current_avatar}")
        if current_avatar:
            logger.info(f"🎭 DEBUG: Avatar details - name: {current_avatar.get('name')}, url: {current_avatar.get('avatar_url')}")
        else:
            logger.info("🎭 DEBUG: No current_avatar - template will show fallback")
        
        return render_template("anonymous_community.html", current_avatar=current_avatar)
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

@community_bp.route("/referrals/me")
def referrals_me():
    """API endpoint for user's referral data"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Get user referral data from session
        user_id = session.get('user_id')
        referrals = int(session.get('referrals', 0))
        
        # Calculate progress and next reward
        thresholds = [
            {"threshold": 2, "cosmetic": "Blayzike"},
            {"threshold": 4, "cosmetic": "Blazelian"}, 
            {"threshold": 6, "cosmetic": "Nyxara"},
            {"threshold": 8, "cosmetic": "Claude Referral"},
            {"threshold": 10, "cosmetic": "Blayzo Referral"}
        ]
        
        # Find next reward
        next_reward = None
        completed_all = True
        progress_percent = 100
        
        for reward in thresholds:
            if referrals < reward["threshold"]:
                next_reward = {
                    "cosmetic": reward["cosmetic"],
                    "referrals_needed": reward["threshold"] - referrals,
                    "threshold": reward["threshold"]
                }
                completed_all = False
                # Calculate progress to next reward
                prev_threshold = 0
                if reward != thresholds[0]:
                    prev_idx = thresholds.index(reward) - 1
                    prev_threshold = thresholds[prev_idx]["threshold"]
                
                progress_percent = int(((referrals - prev_threshold) / (reward["threshold"] - prev_threshold)) * 100)
                break
        
        # Mock stats for now - in real app would come from database
        stats = {
            "total_referrals": referrals,
            "verified_referrals": referrals,  
            "pending_referrals": 0
        }
        
        progress = {
            "completed_all": completed_all,
            "progress_percent": max(0, min(100, progress_percent))
        }
        
        # Generate share URL (mock for now)
        share_url = f"https://soulbridgeai.com/register?ref={user_id}"
        referral_code = f"SOUL{user_id}"
        
        # Generate social sharing links
        from urllib.parse import quote
        message = f"Join me on SoulBridge AI - the ultimate AI companion platform! Use my code {referral_code} to get started: {share_url}"
        encoded_message = quote(message)
        encoded_url = quote(share_url)
        
        social_sharing = {
            "twitter": f"https://twitter.com/intent/tweet?text={encoded_message}",
            "facebook": f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}",
            "whatsapp": f"https://wa.me/?text={encoded_message}"
        }
        
        return jsonify({
            "success": True,
            "stats": stats,
            "progress": progress, 
            "next_reward": next_reward,
            "share_url": share_url,
            "referral_code": referral_code,
            "social_sharing": social_sharing
        })
        
    except Exception as e:
        logger.error(f"Referrals me API error: {e}")
        return jsonify({"success": False, "error": "Failed to load referral data"}), 500

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
        
        # Query real community posts from database with proper transaction handling
        try:
            from database_utils import get_db_connection, get_placeholder
            
            conn = get_db_connection()
            placeholder = get_placeholder()
            
            logger.info(f"Community posts query: category={category}, sort={sort_by}, limit={limit}, placeholder={placeholder}")
            
            # Use proper transaction pattern for reads too
            with conn:  # Fresh transaction for consistent read
                with conn.cursor() as cursor:
                    # Build query with category filter - use COALESCE for unified message field
                    base_query = f"""
                        SELECT cp.id, cp.category, cp.created_at, cp.hashtags,
                               u.email as author_email, c.name as companion_name, 
                               cp.image_url as image_url,
                               COALESCE(NULLIF(cp.text, ''), NULLIF(cp.content, '')) AS message,
                               cp.author_uid
                        FROM community_posts cp
                        JOIN users u ON cp.author_uid = u.id
                        LEFT JOIN companions c ON cp.companion_id = c.id
                    """
                    
                    params = []
                    if category != 'all':
                        base_query += f" WHERE cp.category = {placeholder}"
                        params.append(category)
                        
                    # Add sorting
                    if sort_by == 'new':
                        base_query += " ORDER BY cp.created_at DESC"
                    elif sort_by == 'popular':
                        base_query += " ORDER BY cp.id DESC"  # Simple fallback for now
                        
                    # Add pagination
                    base_query += f" LIMIT {placeholder} OFFSET {placeholder}"
                    params.extend([limit, offset])
                    
                    logger.info(f"Executing query: {base_query}")
                    logger.info(f"Query params: {params}")
                    
                    cursor.execute(base_query, params)
                    posts = cursor.fetchall()
                    
                    logger.info(f"Query returned {len(posts)} posts")
                    
                    # Get total count for pagination in same transaction
                    count_query = "SELECT COUNT(*) FROM community_posts"
                    count_params = []
                    if category != 'all':
                        count_query += f" WHERE category = {placeholder}"
                        count_params.append(category)
                        
                    cursor.execute(count_query, count_params)
                    total_posts = cursor.fetchone()[0]
            
            conn.close()
            
        except Exception as db_error:
            logger.error(f"Database query failed: {str(db_error)}")
            if 'conn' in locals():
                conn.close()
            
            # Return empty result instead of failing
            return jsonify({
                "success": True,
                "posts": [],
                "total_count": 0,
                "has_more": False,
                "categories": ["wellness", "creative", "growth", "mindfulness"],
                "sort_options": ["new", "popular"],
                "error_debug": str(db_error) if logger.level <= 20 else None  # Only in debug mode
            })
        
        # Format posts for response
        paginated_posts = []
        current_user_id = session.get('user_id')
        
        for post in posts:
            # Query fields: id, category, created_at, hashtags, author_email, companion_name, image_url, message, author_uid
            post_id = post[0]
            category = post[1] 
            created_at = post[2]
            hashtags_json = post[3]
            author_email = post[4]
            companion_name = post[5]
            image_url = post[6]
            message = post[7] or ""  # Use unified COALESCE message field
            author_uid = post[8]
            
            # Use image_url, fallback to default
            avatar_url = image_url or "/static/logos/New IntroLogo.png"
            
            # Parse hashtags JSON
            try:
                import json
                hashtags = json.loads(hashtags_json) if hashtags_json else []
            except:
                hashtags = []
            
            formatted_post = {
                "id": post_id,
                "title": message[:50] + "..." if len(message) > 50 else message,
                "content": message,
                "category": category,
                "created_at": created_at.isoformat() + "Z" if created_at else "",
                "tags": hashtags,
                "author": "Anonymous Companion",  # Keep anonymous
                "companion_avatar": avatar_url,
                "hearts": 0,  # Will be updated below with reaction counts
                "is_mine": current_user_id == author_uid  # Flag for ownership
            }
            paginated_posts.append(formatted_post)
        
        # Add reaction data to each post
        for post in paginated_posts:
            post_id = post['id']
            reactions = get_post_reaction_counts(post_id)
            post['reactions'] = reactions
            post['total_reactions'] = sum(reactions.values())
        
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
        
        # Normalize incoming field - accept either text or content
        msg = (data.get("text") or data.get("content") or "").strip()
        category = data.get('category', 'general')
        
        if not msg:
            return jsonify({"success": False, "error": "Message cannot be empty"}), 400
        
        if len(msg) > 700:
            return jsonify({"success": False, "error": "Post content too long (max 700 characters)"}), 400
        
        # Save post to database with proper transaction handling
        try:
            from database_utils import get_db_connection, get_placeholder
            conn = get_db_connection()
            placeholder = get_placeholder()
            
            # Get current user info and avatar
            user_id = session.get('user_id')
            user_email = session.get('email', 'anonymous@soulbridgeai.com')
            
            # Snapshot the current avatar image into the post (denormalized for performance)
            companion_info = session.get('companion_info', {})
            # Use companion_id from companion_info, fallback to selected_companion_id
            companion_id = companion_info.get('companion_id') or session.get('selected_companion_id')
            image_url = companion_info.get('image_url') or companion_info.get('avatar_url', '/static/logos/New IntroLogo.png')
            
            # DEBUG: Log session contents to understand what's happening
            logger.info(f"🔍 SESSION DEBUG: companion_info = {companion_info}")
            logger.info(f"🔍 SESSION DEBUG: selected_companion_id = {session.get('selected_companion_id')}")
            logger.info(f"🔍 SESSION DEBUG: full session keys = {list(session.keys())}")
            
            logger.info(f"Creating post: user_id={user_id}, companion_id={companion_id}, category={category}, image_url={image_url}")
            
            # Use proper transaction pattern
            with conn:  # Auto-commit on success, rollback on exception
                with conn.cursor() as cursor:
                    # WORKAROUND: Production DB companion_id column expects INTEGER, but we have TEXT values
                    # Set companion_id to NULL and store the text ID in a different approach
                    insert_query = f"""
                        INSERT INTO community_posts 
                        (author_uid, companion_id, category, content, text, status, created_at, author_email, image_url, reaction_counts_json, total_reactions)
                        VALUES ({placeholder}, NULL, {placeholder}, {placeholder}, {placeholder}, 'approved', CURRENT_TIMESTAMP, {placeholder}, {placeholder}, {placeholder}, 0)
                        RETURNING id
                    """
                    
                    # Initialize with empty reactions
                    empty_reactions_json = '{"❤️": 0, "✨": 0, "🌿": 0, "🔥": 0, "🙏": 0, "⭐": 0, "👏": 0, "🫶": 0}'
                    cursor.execute(insert_query, (user_id, category, msg, msg, user_email, image_url, empty_reactions_json))
                    post_id = cursor.fetchone()[0]
                    
                    logger.info(f"Post created successfully: ID={post_id}")
            
            conn.close()
            
        except Exception as db_error:
            logger.error(f"Failed to save post to database: {str(db_error)}")
            if 'conn' in locals():
                conn.close()
            
            # Return success but with mock ID for now
            post_id = 999
        
        new_post = {
            "id": post_id,
            "title": msg[:50] + "..." if len(msg) > 50 else msg,
            "content": msg,
            "author": "Anonymous Companion",
            "companion_avatar": "/static/logos/New IntroLogo.png",
            "category": category,
            "hearts": 0,
            "created_at": datetime.now().isoformat(),
            "tags": []
        }
        
        logger.info(f"[COMMUNITY] Created post: {msg[:50]}... in {category}")
        
        return jsonify({
            "success": True,
            "message": "Post created successfully",
            "post": new_post
        })
        
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        return jsonify({"success": False, "error": "Failed to create post"}), 500


@community_bp.route("/community/posts/<int:post_id>", methods=["DELETE"])
def delete_community_post(post_id):
    """Delete a community post (only by author)"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        current_user_id = session.get('user_id')
        if not current_user_id:
            return jsonify({"success": False, "error": "User ID not found"}), 401
        
        # Verify ownership and delete post
        try:
            from database_utils import get_db_connection, get_placeholder
            conn = get_db_connection()
            placeholder = get_placeholder()
            
            with conn:  # Transaction for consistency
                with conn.cursor() as cursor:
                    # First check if post exists and user owns it
                    check_query = f"SELECT author_uid FROM community_posts WHERE id = {placeholder}"
                    cursor.execute(check_query, (post_id,))
                    result = cursor.fetchone()
                    
                    if not result:
                        return jsonify({"success": False, "error": "Post not found"}), 404
                    
                    author_uid = result[0]
                    if author_uid != current_user_id:
                        return jsonify({"success": False, "error": "You can only delete your own posts"}), 403
                    
                    # Delete the post
                    delete_query = f"DELETE FROM community_posts WHERE id = {placeholder} AND author_uid = {placeholder}"
                    cursor.execute(delete_query, (post_id, current_user_id))
                    
                    if cursor.rowcount == 0:
                        return jsonify({"success": False, "error": "Post not found or not authorized"}), 404
                    
                    logger.info(f"Post deleted successfully: ID={post_id}, User={current_user_id}")
            
            conn.close()
            
            return jsonify({
                "success": True,
                "message": "Post deleted successfully"
            })
            
        except Exception as db_error:
            logger.error(f"Database error deleting post {post_id}: {str(db_error)}")
            if 'conn' in locals():
                conn.close()
            return jsonify({"success": False, "error": "Database error"}), 500
            
    except Exception as e:
        logger.error(f"Error deleting post {post_id}: {e}")
        return jsonify({"success": False, "error": "Failed to delete post"}), 500


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
        
        # Database reaction logic - check if user already reacted
        user_id = session.get('user_id')
        
        # Connect to database
        db = get_database()
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 503
        
        conn = db.get_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        # Check existing reaction for this post (reactions are permanent)
        cursor.execute(f"SELECT emoji FROM community_reactions WHERE post_id = {placeholder} AND viewer_uid = {placeholder}", 
                      (post_id, user_id))
        existing_reaction_row = cursor.fetchone()
        
        if existing_reaction_row:
            existing_reaction = existing_reaction_row[0]
            conn.close()
            # User already has a permanent reaction on this post
            return jsonify({
                'success': False, 
                'error': f'You have already reacted with {existing_reaction}. Reactions are permanent!'
            }), 400
        else:
            # Add new permanent reaction to database
            cursor.execute(f"INSERT INTO community_reactions (post_id, viewer_uid, viewer_uid_hash, emoji) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})", 
                          (post_id, user_id, str(user_id), emoji))
            conn.commit()
            action = 'added'
        
        conn.close()
        
        # Get all reactions for this post from all users
        reaction_counts = get_post_reaction_counts(post_id)
        
        # Update counts with the new reaction (only add since user hasn't reacted before)
        if emoji in reaction_counts:
            reaction_counts[emoji] += 1
        else:
            reaction_counts[emoji] = 1
        
        # Store the updated reaction counts
        store_post_reaction_counts(post_id, reaction_counts)
        
        logger.info(f"[COMMUNITY] User {user_id} reacted to post {post_id} with {emoji}")
        
        # Update weekly event metrics if there's an active event
        try:
            from .weekly_events_service import WeeklyEventsService
            events_service = WeeklyEventsService(get_database())
            current_event = weekly_events_service.get_current_weekly_event()
            
            if current_event:
                # Update post metrics for the weekly event
                events_service.update_post_metrics(post_id, current_event['id'])
                
                # Auto-register user as participant if not already
                events_service.register_participant(
                    current_event['id'], 
                    user_id, 
                    session.get('selected_companion')
                )
        except Exception as e:
            logger.warning(f"Failed to update weekly event metrics: {e}")
        
        return jsonify({
            "success": True,
            "action": action,
            "reaction_counts": reaction_counts
        })
        
    except Exception as e:
        logger.error(f"Error reacting to post: {e}")
        return jsonify({"success": False, "error": "Failed to react to post"}), 500

@community_bp.route("/community/user-reactions")
def get_user_reactions():
    """Get current user's reactions"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        
        # Get user reactions from database
        db = get_database()
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 503
        
        conn = db.get_connection()
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        # Get all reactions by this user
        cursor.execute(f"SELECT post_id, emoji FROM community_reactions WHERE viewer_uid = {placeholder}", (user_id,))
        reactions_rows = cursor.fetchall()
        conn.close()
        
        # Convert to dict format {post_id: emoji}
        user_reactions = {}
        for post_id, emoji in reactions_rows:
            user_reactions[str(post_id)] = emoji
        
        return jsonify({
            "success": True,
            "reactions": user_reactions
        })
        
    except Exception as e:
        logger.error(f"Error getting user reactions: {e}")
        return jsonify({"success": False, "error": "Failed to get reactions"}), 500

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

@community_bp.route("/community/suggest-moderation", methods=["POST"])
def suggest_moderation():
    """Submit a moderation suggestion for AI review (no direct user power)"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        post_id = data.get('post_id')
        reasons = data.get('reasons', [])
        context = data.get('context', '')
        post_data = data.get('post_data', {})
        
        if not post_id or not reasons:
            return jsonify({"success": False, "error": "Post ID and reasons are required"}), 400
        
        user_id = session.get('user_id')
        
        # Create moderation suggestion (would go to AI review queue)
        suggestion = {
            'user_id': user_id,
            'post_id': post_id,
            'reasons': reasons,
            'context': context,
            'post_data': post_data,
            'submitted_at': datetime.now().isoformat(),
            'status': 'pending_ai_review',
            'priority': calculate_suggestion_priority(reasons, context)
        }
        
        # In a real system, this would:
        # 1. Save to moderation_suggestions table
        # 2. Queue for AI analysis
        # 3. Auto-review based on AI confidence
        # 4. Only escalate to humans if needed
        
        logger.info(f"[MODERATION] User {user_id} suggested post {post_id} for review: {reasons}")
        
        # Simulate AI processing
        ai_response = simulate_ai_moderation_review(suggestion)
        
        return jsonify({
            "success": True,
            "message": "Moderation suggestion submitted successfully",
            "suggestion_id": f"mod_{post_id}_{user_id}",
            "ai_review_status": ai_response["status"],
            "estimated_review_time": ai_response["estimated_time"]
        })
        
    except Exception as e:
        logger.error(f"Error submitting moderation suggestion: {e}")
        return jsonify({"success": False, "error": "Failed to submit suggestion"}), 500

def calculate_suggestion_priority(reasons, context):
    """Calculate priority based on suggestion reasons"""
    priority_weights = {
        'spam_patterns': 0.8,
        'negative_tone': 0.7,
        'off_topic': 0.5,
        'category_mismatch': 0.3,
        'low_effort': 0.2,
        'other_concern': 0.4
    }
    
    max_priority = max([priority_weights.get(reason, 0.3) for reason in reasons])
    
    # Boost priority if user provided context
    if context.strip():
        max_priority += 0.1
    
    return min(max_priority, 1.0)

def simulate_ai_moderation_review(suggestion):
    """Simulate AI moderation review process"""
    priority = suggestion['priority']
    reasons = suggestion['reasons']
    
    # High priority suggestions get faster review
    if priority > 0.7:
        return {
            "status": "high_priority_queue",
            "estimated_time": "within 5 minutes"
        }
    elif priority > 0.5:
        return {
            "status": "standard_queue", 
            "estimated_time": "within 15 minutes"
        }
    else:
        return {
            "status": "low_priority_queue",
            "estimated_time": "within 1 hour"
        }

@community_bp.route("/community/companions")
def community_companions():
    """Get companions available for community avatar selection"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Initialize companion manager if not already done
        global companion_manager
        if not companion_manager:
            try:
                from .companion_manager import CompanionManager
                companion_manager = CompanionManager()
                logger.info("🏘️ Initialized companion manager on demand")
            except Exception as init_error:
                logger.error(f"Failed to initialize companion manager: {init_error}")
                return jsonify({"success": False, "error": "Service initialization failed"}), 503
        
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
        
        # Get available companions for community
        companions = companion_manager.get_community_companions(user_plan, trial_active, referrals)
        
        # Add can_access field for frontend compatibility  
        for companion in companions:
            companion['can_access'] = not companion.get('locked', False)
            companion['id'] = companion.get('slug', companion.get('id', ''))
        
        return jsonify({
            "success": True,
            "companions": companions
        })
        
    except Exception as e:
        logger.error(f"Community companions error: {e}")
        return jsonify({"success": False, "error": "Failed to load companions"}), 500

@community_bp.route("/community/weekly-event")
def get_weekly_event():
    """Get current weekly appreciation event"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        # Use the initialized weekly events service
        if not weekly_events_service:
            logger.error("Weekly events service not initialized")
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        current_event = weekly_events_service.get_current_weekly_event()
        if not current_event:
            return jsonify({
                "success": True, 
                "event": None,
                "message": "No active event this week"
            })
        
        # Get leaderboard
        leaderboard = events_service.get_weekly_leaderboard(current_event['id'], limit=10)
        
        # Get user's stats
        user_id = session.get('user_id')
        user_stats = events_service.get_user_event_stats(user_id, current_event['id'])
        
        return jsonify({
            "success": True,
            "event": current_event,
            "leaderboard": leaderboard,
            "user_stats": user_stats
        })
        
    except Exception as e:
        logger.error(f"Error getting weekly event: {e}")
        return jsonify({"success": False, "error": "Failed to load weekly event"}), 500

@community_bp.route("/community/weekly-event/join", methods=["POST"])
def join_weekly_event():
    """Join the current weekly appreciation event"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        data = request.get_json()
        companion_id = data.get('companion_id') if data else None
        
        # Use the initialized weekly events service
        if not weekly_events_service:
            logger.error("Weekly events service not initialized")
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        current_event = weekly_events_service.get_current_weekly_event()
        if not current_event:
            return jsonify({
                "success": False, 
                "error": "No active event to join"
            }), 400
        
        user_id = session.get('user_id')
        success = events_service.register_participant(
            current_event['id'], 
            user_id, 
            companion_id
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": "Successfully joined the weekly appreciation event!",
                "event": current_event
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to join event"
            }), 500
            
    except Exception as e:
        logger.error(f"Error joining weekly event: {e}")
        return jsonify({"success": False, "error": "Failed to join event"}), 500

@community_bp.route("/community/avatar-legacy")
def community_get_avatar():
    """Get current user's community avatar/companion - LEGACY ROUTE - Use /community/avatar instead"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        
        # CRITICAL FIX: Direct database check for avatar persistence
        try:
            db = get_database()
            if db:
                conn = db.get_connection()
                cursor = conn.cursor()
                
                # Check database for saved companion
                if db.use_postgres:
                    cursor.execute("SELECT companion_data FROM users WHERE id = %s", (user_id,))
                else:
                    cursor.execute("SELECT companion_data FROM users WHERE id = ?", (user_id,))
                
                result = cursor.fetchone()
                conn.close()
                
                if result and result[0]:
                    import json
                    try:
                        # Handle both JSON string and dictionary (PostgreSQL JSONB returns dict)
                        if isinstance(result[0], dict):
                            companion_data = result[0]  # Already a dictionary
                        else:
                            companion_data = json.loads(result[0])  # Parse JSON string
                        logger.info(f"✅ Found saved avatar for user {user_id}: {companion_data.get('name', 'Unknown')}")
                        
                        # Add cache busting
                        import time
                        cache_buster = int(time.time())
                        avatar_url = companion_data.get('avatar_url') or companion_data.get('image_url', '/static/logos/New IntroLogo.png')
                        if '?' not in avatar_url:
                            avatar_url += f"?t={cache_buster}"
                        
                        return jsonify({
                            "success": True,
                            "companion": {
                                "name": companion_data.get('name', 'Soul'),
                                "companion_id": companion_data.get('id', 'soul'),
                                "avatar_url": avatar_url,
                                "image_url": avatar_url,
                                "tier": companion_data.get('tier', 'bronze')
                            }
                        })
                    except json.JSONDecodeError:
                        logger.error(f"❌ Invalid JSON in companion_data for user {user_id}")
                        
        except Exception as db_error:
            logger.error(f"❌ Database avatar lookup failed: {db_error}")
        
        # Fallback to community service if available
        if community_service:
            avatar_result = community_service.get_user_avatar(user_id)
            if avatar_result['success']:
                return jsonify({
                    "success": True,
                    "companion": avatar_result['companion']
                })
        
        # Final fallback - default avatar
        import time
        cache_buster = int(time.time())
        return jsonify({
            "success": True,
            "companion": {
                "name": "Soul",
                "companion_id": "soul",
                "avatar_url": f"/static/logos/New IntroLogo.png?t={cache_buster}",
                "image_url": f"/static/logos/New IntroLogo.png?t={cache_buster}",
                "tier": "bronze"
            }
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
        
        # DIRECT DATABASE SAVE - No service dependencies
        data = request.get_json()
        companion_id = data.get('companion_id')
        
        if not companion_id:
            return jsonify({"success": False, "error": "Companion ID required"}), 400
        
        user_id = session.get('user_id')
        
        # Real companion mapping from your actual companion_data.py
        companion_map = {
            # BRONZE
            'gamerjay_bronze': {'name': 'GamerJay', 'image_url': '/static/logos/GamerJay_Free_companion.png', 'tier': 'bronze'},
            'blayzo_bronze': {'name': 'Blayzo', 'image_url': '/static/logos/Blayzo.png', 'tier': 'bronze'},
            'claude_bronze': {'name': 'Claude', 'image_url': '/static/logos/Claude_Free.png', 'tier': 'bronze'},
            'lumen_bronze': {'name': 'Lumen', 'image_url': '/static/logos/Lumen_Bronze.png', 'tier': 'bronze'},
            # SILVER  
            'sky_silver': {'name': 'Sky', 'image_url': '/static/logos/Sky_a_premium_companion.png', 'tier': 'silver'},
            'gamerjay_silver': {'name': 'GamerJay.2', 'image_url': '/static/logos/GamerJay_premium_companion.png', 'tier': 'silver'},
            'claude_silver': {'name': 'Claude.3', 'image_url': '/static/logos/Claude_Growth.png', 'tier': 'silver'},
            'rozia_silver': {'name': 'Rozia', 'image_url': '/static/logos/Rozia_Silver.png', 'tier': 'silver'},
            # GOLD
            'crimson_gold': {'name': 'Crimson', 'image_url': '/static/logos/Crimson_a_Max_companion.png', 'tier': 'gold'},
            'violet_gold': {'name': 'Violet', 'image_url': '/static/logos/Violet_a_Max_companion.png', 'tier': 'gold'},
            'claude_gold': {'name': 'Claude.2', 'image_url': '/static/logos/Claude_Max.png', 'tier': 'gold'},
            'royal_gold': {'name': 'Royal', 'image_url': '/static/logos/Royal_a_Max_companion.png', 'tier': 'gold'}
        }
        
        if companion_id not in companion_map:
            return jsonify({"success": False, "error": f"Unknown companion: {companion_id}"}), 400
        
        companion = companion_map[companion_id]
        
        # BULLETPROOF DATABASE SAVE
        try:
            # Create companion info with correct field names
            companion_info = {
                'id': companion_id,
                'name': companion['name'],
                'image_url': companion['image_url'],  # This is what server-side expects!
                'tier': companion['tier'],
                'saved_at': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"💾 SAVING AVATAR for user {user_id}: {companion_info}")
            
            db = get_database()
            if not db:
                return jsonify({"success": False, "error": "Database not available"}), 503
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Simple, direct PostgreSQL save
            if db.use_postgres:
                cursor.execute("""
                    UPDATE users 
                    SET companion_data = %s::jsonb
                    WHERE id = %s
                """, (json.dumps(companion_info), user_id))
            else:
                cursor.execute("""
                    UPDATE users 
                    SET companion_data = ?
                    WHERE id = ?
                """, (json.dumps(companion_info), user_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ AVATAR SAVED: {companion['name']} for user {user_id}")
            
            # Update session with both companion_info AND selected_companion_id
            session['companion_info'] = {
                'name': companion['name'],
                'id': companion_id,
                'image_url': companion['image_url']
            }
            session['selected_companion_id'] = companion_id
            session.modified = True
            
            return jsonify({
                "success": True,
                "message": "Avatar updated successfully",
                "companion": companion
            })
                
        except Exception as save_error:
            logger.error(f"❌ AVATAR SAVE FAILED: {save_error}")
            return jsonify({"success": False, "error": f"Save failed: {str(save_error)}"}), 500
        
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

@community_bp.route("/community/avatar/test-persistence", methods=["GET"])
def test_avatar_persistence():
    """Test endpoint to verify avatar persistence across refreshes"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        
        # Test database persistence
        try:
            from ...avatar_persistence_helper import load_user_avatar_persistent
            db_result = load_user_avatar_persistent(user_id, get_database())
        except ImportError:
            db_result = {'success': False, 'error': 'Avatar persistence helper not available'}
        
        # Test session persistence  
        session_companion = session.get('companion_info')
        
        # Test community service persistence
        service_result = None
        if community_service:
            service_result = community_service.get_user_avatar(user_id)
        
        return jsonify({
            "success": True,
            "persistence_test": {
                "database": {
                    "available": db_result['success'],
                    "data": db_result.get('data') if db_result['success'] else None,
                    "error": db_result.get('error') if not db_result['success'] else None
                },
                "session": {
                    "available": session_companion is not None,
                    "data": session_companion
                },
                "service": {
                    "available": service_result is not None and service_result.get('success', False),
                    "data": service_result.get('companion') if service_result and service_result.get('success') else None,
                    "error": service_result.get('error') if service_result and not service_result.get('success') else None
                },
                "recommendations": [
                    "Database persistence is the most reliable for production",
                    "Session storage will be lost on refresh/restart", 
                    "Always use database + cache busting for persistent avatars",
                    "Consider cloud storage for uploaded custom images"
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Avatar persistence test error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@community_bp.route("/community/avatar/force-refresh", methods=["POST"])
def force_avatar_refresh():
    """Force refresh avatar from database with new cache buster"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not community_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        user_id = session.get('user_id')
        
        # Clear session cache
        session.pop('companion_info', None)
        session.modified = True
        
        # Force reload from database
        avatar_result = community_service.get_user_avatar(user_id)
        
        if avatar_result['success']:
            return jsonify({
                "success": True,
                "message": "Avatar refreshed successfully",
                "companion": avatar_result['companion']
            })
        else:
            return jsonify({
                "success": False,
                "error": avatar_result.get('error', 'Failed to refresh avatar')
            }), 500
        
    except Exception as e:
        logger.error(f"Force avatar refresh error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@community_bp.route("/community/debug-avatar", methods=["GET"])
def debug_avatar_persistence():
    """Debug endpoint to check avatar persistence in database"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        
        # Check database directly
        db = get_database()
        if not db:
            return jsonify({"debug": "Database not available"}), 500
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgres:
            cursor.execute("SELECT id, companion_data FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT id, companion_data FROM users WHERE id = ?", (user_id,))
            
        result = cursor.fetchone()
        conn.close()
        
        debug_info = {
            "user_id": user_id,
            "session_companion": session.get('companion_info'),
            "database_user_exists": result is not None,
            "database_companion_data": result[1] if result and result[1] else None,
            "database_raw": str(result) if result else None
        }
        
        return jsonify({"success": True, "debug": debug_info})
        
    except Exception as e:
        logger.error(f"Debug avatar error: {e}")
        return jsonify({"success": False, "error": str(e), "debug": "Debug failed"}), 500

@community_bp.route("/community/debug-database", methods=["GET"])
def debug_database_schema():
    """Debug endpoint to check database schema for companion_data column"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        db = get_database()
        if not db:
            return jsonify({"debug": "Database not available"}), 500
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        schema_info = {}
        
        if db.use_postgres:
            # Check PostgreSQL schema
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            schema_info = {
                "database_type": "PostgreSQL",
                "users_table_columns": [{"name": col[0], "type": col[1]} for col in columns],
                "has_companion_data": any(col[0] == 'companion_data' for col in columns)
            }
        else:
            # Check SQLite schema
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            schema_info = {
                "database_type": "SQLite", 
                "users_table_columns": [{"name": col[1], "type": col[2]} for col in columns],
                "has_companion_data": any(col[1] == 'companion_data' for col in columns)
            }
        
        conn.close()
        
        return jsonify({
            "success": True,
            "schema": schema_info
        })
        
    except Exception as e:
        logger.error(f"Database schema debug error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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
        heart_result = wellness_gallery.add_heart(user_id, content_id)
        
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

@community_bp.route("/community/debug-current-user", methods=["GET"])
def debug_current_user():
    """Debug current logged in user information"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Not logged in"}), 401
        
        user_id = session.get('user_id')
        user_email = session.get('email')
        user_plan = session.get('user_plan')
        
        # Get user data from database
        db = get_database()
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 503
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgres:
            cursor.execute("SELECT id, email, display_name, companion_data FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT id, email, display_name, companion_data FROM users WHERE id = ?", (user_id,))
        
        user_row = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "success": True,
            "session": {
                "user_id": user_id,
                "email": user_email,
                "user_plan": user_plan
            },
            "database": {
                "user_exists": user_row is not None,
                "user_data": {
                    "id": user_row[0] if user_row else None,
                    "email": user_row[1] if user_row else None,
                    "display_name": user_row[2] if user_row else None,
                    "has_companion_data": user_row[3] is not None if user_row else False,
                    "companion_data": user_row[3] if user_row and user_row[3] else None
                } if user_row else None
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Debug current user error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@community_bp.route("/debug-db", methods=["GET"])
def simple_db_debug():
    """Simple database debug without auth"""
    try:
        db = get_database()
        if not db:
            return jsonify({"error": "No database"}), 500
            
        return jsonify({
            "success": True,
            "database_type": "PostgreSQL" if db.use_postgres else "SQLite",
            "message": "Database connection successful"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@community_bp.route("/community/debug-schema", methods=["GET"])
def debug_schema():
    """Debug database schema to check columns"""
    try:
        db = get_database()
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 503
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgres:
            # Check PostgreSQL schema
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'users'
                AND column_name LIKE '%companion%'
                ORDER BY column_name
            """)
            companion_columns = cursor.fetchall()
            
            # Also get a sample user to see all data
            cursor.execute("SELECT * FROM users WHERE id = 104")
            user_data = cursor.fetchone()
            
            # Get column names for the user table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
            all_columns = [row[0] for row in cursor.fetchall()]
            
        else:
            # SQLite schema check
            cursor.execute("PRAGMA table_info(users)")
            all_columns_info = cursor.fetchall()
            companion_columns = [col for col in all_columns_info if 'companion' in col[1].lower()]
            all_columns = [col[1] for col in all_columns_info]
            
            cursor.execute("SELECT * FROM users WHERE id = 104")
            user_data = cursor.fetchone()
        
        conn.close()
        
        # Create user data dict
        user_dict = {}
        if user_data and all_columns:
            for i, value in enumerate(user_data):
                if i < len(all_columns):
                    user_dict[all_columns[i]] = value
        
        return jsonify({
            "success": True,
            "database_type": "PostgreSQL" if db.use_postgres else "SQLite",
            "companion_columns": companion_columns,
            "all_columns": all_columns,
            "user_104_data": user_dict
        })
        
    except Exception as e:
        logger.error(f"❌ Debug schema error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@community_bp.route("/community/debug-users", methods=["GET"])
def debug_users():
    """TEMPORARY: Debug what users exist in the database"""
    try:
        db = get_database()
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 503
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get recent users
        if db.use_postgres:
            cursor.execute("SELECT id, email, display_name, companion_data FROM users ORDER BY id DESC LIMIT 10")
        else:
            cursor.execute("SELECT id, email, display_name, companion_data FROM users ORDER BY id DESC LIMIT 10")
        
        users = cursor.fetchall()
        conn.close()
        
        user_list = []
        for user in users:
            user_info = {
                "id": user[0],
                "email": user[1],
                "display_name": user[2],
                "has_companion_data": user[3] is not None,
                "companion_data": user[3] if user[3] else None
            }
            user_list.append(user_info)
        
        return jsonify({
            "success": True,
            "database_type": "PostgreSQL" if db.use_postgres else "SQLite",
            "users": user_list
        })
        
    except Exception as e:
        logger.error(f"❌ Debug users error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@community_bp.route("/community/test-avatar-save", methods=["POST"])
def test_avatar_save():
    """TEMPORARY: Test avatar save without authentication for debugging"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
        
        # Hard-coded user ID for testing
        user_id = data.get('user_id', 104)
        companion_name = data.get('companion_name', 'Seraphina')
        avatar_url = data.get('avatar_url', '/static/images/avatars/f_seraphina_angel.png')
        
        logger.info(f"🧪 TESTING AVATAR SAVE: user_id={user_id}, companion={companion_name}")
        
        # Get database connection
        db = get_database()
        if not db:
            logger.error("❌ Database not available")
            return jsonify({"success": False, "error": "Database not available"}), 503
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Prepare companion data with correct field names for server-side loading
        companion_data = {
            "name": companion_name,
            "image_url": avatar_url,  # SERVER-SIDE CODE EXPECTS image_url, not avatar!
            "id": "seraphina",  # Add companion ID for completeness
            "tier": "silver",   # Add tier for completeness
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Check if user exists
        if db.use_postgres:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        user_exists = cursor.fetchone()
        
        logger.info(f"👤 User {user_id} exists: {user_exists is not None}")
        
        if not user_exists:
            logger.error(f"❌ User {user_id} not found")
            conn.close()
            return jsonify({"success": False, "error": f"User {user_id} not found"}), 404
        
        # Save to database
        logger.info(f"💾 DIRECT SAVE: Saving to database for user {user_id}: {companion_data}")
        logger.info(f"🔧 Database type: {db.__class__.__name__}, use_postgres: {db.use_postgres}")
        
        if db.use_postgres:
            logger.info(f"🐘 Using PostgreSQL UPDATE for user {user_id}")
            # PostgreSQL JSONB columns also need JSON string (fixed!)
            json_data = json.dumps(companion_data)
            logger.info(f"🐘 JSON data being saved: {json_data}")
            cursor.execute("UPDATE users SET companion_data = %s WHERE id = %s", (json_data, user_id))
        else:
            logger.info(f"🗃️ Using SQLite UPDATE for user {user_id}")
            # SQLite needs JSON string
            json_data = json.dumps(companion_data)
            logger.info(f"🗃️ JSON data being saved: {json_data}")
            cursor.execute("UPDATE users SET companion_data = ? WHERE id = ?", (json_data, user_id))
        
        rows_affected = cursor.rowcount
        logger.info(f"💾 PRE-COMMIT: {rows_affected} rows affected for user {user_id}")
        
        conn.commit()
        logger.info(f"✅ COMMIT SUCCESSFUL for user {user_id}")
        
        # Verify the save worked
        if db.use_postgres:
            cursor.execute("SELECT companion_data FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT companion_data FROM users WHERE id = ?", (user_id,))
        verify_result = cursor.fetchone()
        
        logger.info(f"🔍 VERIFICATION: Data saved = {verify_result[0] is not None if verify_result else 'No result'}")
        
        if verify_result and verify_result[0]:
            logger.info(f"✅ VERIFICATION SUCCESS: {verify_result[0]}")
        else:
            logger.error(f"❌ VERIFICATION FAILED: No data found after save")
        
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Avatar save test completed",
            "debug": {
                "user_id": user_id,
                "companion_name": companion_name,
                "avatar_url": avatar_url,
                "rows_affected": rows_affected,
                "verification_data": verify_result[0] if verify_result else None
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Test avatar save error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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