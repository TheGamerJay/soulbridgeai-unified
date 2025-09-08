"""
SoulBridge AI - User Profile Routes
All user profile management endpoints extracted from backend/app.py
Flask Blueprint for modular architecture
Fixed: Global declaration syntax error resolved
"""
import logging
from flask import Blueprint, request, jsonify, session, redirect, render_template, Response
from .profile_service import ProfileService
from .theme_manager import ThemeManager
from .image_manager import ProfileImageManager

logger = logging.getLogger(__name__)

# Create Blueprint
profile_bp = Blueprint('profile', __name__)

# Initialize services (to be configured in main app)
profile_service = None
theme_manager = None
image_manager = None

def init_profile_routes(app, database):
    """Initialize profile routes with dependencies"""
    global profile_service, theme_manager, image_manager
    
    logger.info("🚀 ENTERING init_profile_routes function...")
    logger.info(f"🚀 Received app: {app}")
    logger.info(f"🚀 Received database: {database}")
    
    try:
        logger.info("🚀 Starting profile routes initialization...")
        profile_service = ProfileService(database)
        logger.info("✅ ProfileService created")
        
        theme_manager = ThemeManager(database)
        logger.info("✅ ThemeManager created")
        
        image_manager = ProfileImageManager(database)
        logger.info("✅ ProfileImageManager created")
        
        # Blueprint already registered in main app - just initialize services
        logger.info("✅ Profile routes initialized successfully")
    except Exception as e:
        logger.error(f"❌ Profile routes initialization failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session and session.get('user_id') is not None

# ================================
# MAIN PROFILE PAGES
# ================================

@profile_bp.route("/profile")
def profile_page():
    """User profile page"""
    try:
        if not is_logged_in():
            return redirect("/login")
        
        # Check terms acceptance
        # TODO: Add terms check from main app if needed
        
        # Get user data for profile
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Determine effective plan for companion access
        if trial_active and user_plan == 'bronze':
            effective_plan = 'gold'
        else:
            effective_plan = user_plan
        
        # Set access flags for profile page - trial does NOT modify Bronze features
        session['access_bronze'] = True
        session['access_silver'] = user_plan in ['silver', 'gold']  # NO trial modification
        session['access_gold'] = user_plan == 'gold'  # NO trial modification
        session['companion_access'] = effective_plan  # Trial DOES affect companion access
        
        logger.info(f"✅ PROFILE: user_plan={user_plan}, trial_active={trial_active}, effective_plan={effective_plan}")
        
        # Get user profile data for template
        user_id = session.get('user_id')
        user_email = session.get('user_email', '')
        user_data = None
        
        if profile_service:
            profile_result = profile_service.get_user_profile(user_id)
            if profile_result['success']:
                user_data = profile_result['user']
        
        # Get last used chat companion (not community avatar)
        last_chat_companion = session.get('selected_companion')
        
        # If not in session, try to get from database
        if not last_chat_companion and user_id:
            try:
                from database_utils import get_database
                database = get_database()
                if database:
                    result = database.execute(
                        "SELECT selected_companion FROM users WHERE id = ?", 
                        (user_id,)
                    ).fetchone()
                    if result and result[0]:
                        last_chat_companion = result[0]
                        logger.info(f"Retrieved last chat companion from database: {last_chat_companion}")
            except Exception as e:
                logger.warning(f"Could not retrieve last chat companion: {e}")
        
        logger.info(f"📋 Profile page - last chat companion: {last_chat_companion}")
        
        return render_template("profile.html", user=user_data, user_email=user_email, 
                             last_chat_companion=last_chat_companion)
        
    except Exception as e:
        logger.error(f"❌ PROFILE ERROR: {e}")
        import traceback
        logger.error(f"❌ PROFILE TRACEBACK: {traceback.format_exc()}")
        return f"<h1>Profile Error</h1><p>Error: {str(e)}</p>", 500

# ================================
# PROFILE DATA API
# ================================

@profile_bp.route("/api/users", methods=["GET", "POST"])
@profile_bp.route("/api/user/profile", methods=["GET", "POST"])
def api_user_profile():
    """User profile API endpoint"""
    global profile_service
    
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not profile_service:
            logger.error("Profile service is None - attempting to initialize...")
            # Try to initialize the service if not already done
            try:
                from flask import current_app
                from database_utils import get_database
                
                # Try multiple methods to get database
                database = None
                if hasattr(current_app, 'database_manager'):
                    database = current_app.database_manager
                    logger.info("Found database_manager in current_app")
                else:
                    # Fallback to direct database connection
                    database = get_database()
                    logger.info("Using direct database connection as fallback")
                
                if database:
                    profile_service = ProfileService(database)
                    logger.info("Profile service re-initialized successfully")
                else:
                    logger.error("No database connection available")
                    return jsonify({"success": False, "error": "Database service not available"}), 503
                    
            except Exception as init_error:
                logger.error(f"Failed to re-initialize profile service: {init_error}")
                return jsonify({"success": False, "error": "Profile service initialization failed"}), 503
        
        user_id = session.get('user_id')
        
        if request.method == "GET":
            # Get user profile
            result = profile_service.get_user_profile(user_id, include_access=True)
            
            if result['success']:
                # Add current companion info from session
                companion_info = session.get('companion_info', {
                    'name': 'Soul',
                    'companion_id': 'soul',
                    'avatar_url': '/static/companions/soul.png'
                })
                result['user']['companion'] = companion_info
                
                logger.info(f"👤 Profile data for user {user_id}: companion={companion_info}")
            
            return jsonify(result)
            
        elif request.method == "POST":
            # Update user profile
            data = request.get_json() or {}
            
            # Handle display name update DIRECTLY
            if 'displayName' in data:
                result = profile_service.set_display_name(user_id, data['displayName'])
                
                # Only sync session if database update succeeded
                if result.get('success'):
                    session['display_name'] = data['displayName'].strip()
                    session['user_name'] = data['displayName'].strip()  
                    session.modified = True
                    logger.info(f"✅ DIRECT: User ID {user_id} display name saved and synced")
                
                return jsonify(result)
            else:
                # Handle other profile updates normally
                result = profile_service.update_profile(user_id, data)
                return jsonify(result)
    
    except Exception as e:
        logger.error(f"Profile API error: {e}")
        return jsonify({"success": False, "error": "Failed to process request"}), 500

@profile_bp.route("/api/user/stats", methods=["GET"])
def get_user_stats():
    """Get user profile statistics"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not profile_service:
            return jsonify({"success": False, "error": "Profile service not available"}), 503
        
        user_id = session.get('user_id')
        result = profile_service.get_profile_stats(user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"User stats error: {e}")
        return jsonify({"success": False, "error": "Failed to get user statistics"}), 500

# ================================
# PROFILE IMAGE MANAGEMENT
# ================================

@profile_bp.route("/api/upload-profile-image", methods=["POST"])
def upload_profile_image():
    """Upload and set user profile image"""
    global image_manager
    
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Lazy initialization of image manager if not initialized
        if not image_manager:
            logger.error("📷 ProfileImageManager is None - attempting to initialize...")
            try:
                from flask import current_app
                from database_utils import get_database
                
                # Try multiple methods to get database
                database = None
                if hasattr(current_app, 'database_manager'):
                    database = current_app.database_manager
                    logger.info("Found database_manager in current_app for image manager")
                else:
                    # Fallback to direct database connection
                    database = get_database()
                    logger.info("Using direct database connection as fallback for image manager")
                
                if database:
                    image_manager = ProfileImageManager(database)
                    logger.info("📷 ProfileImageManager initialized lazily")
                else:
                    logger.error("No database connection available for ProfileImageManager")
                    return jsonify({"success": False, "error": "Database service not available"}), 503
                    
            except Exception as init_error:
                logger.error(f"Failed to initialize ProfileImageManager: {init_error}")
                return jsonify({"success": False, "error": "Image service initialization failed"}), 503
        
        file = request.files.get('profileImage')
        if not file or file.filename == '':
            return jsonify({"success": False, "error": "No image file provided"}), 400
        
        user_id = session.get('user_id')
        result = image_manager.upload_profile_image(user_id, file)
        
        # Update session if successful
        if result['success']:
            session['profile_image'] = result['profileImage']
            session.modified = True
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Profile image upload error: {e}")
        return jsonify({"success": False, "error": "Server error"}), 500

@profile_bp.route("/api/profile-image/<int:user_id>")
def serve_profile_image(user_id):
    """Serve user's profile image"""
    global image_manager
    
    try:
        # Lazy initialization of image manager if not initialized
        if not image_manager:
            logger.warning("📷 ProfileImageManager is None for serve - attempting to initialize...")
            try:
                from flask import current_app
                from database_utils import get_database
                
                # Try multiple methods to get database
                database = None
                if hasattr(current_app, 'database_manager'):
                    database = current_app.database_manager
                else:
                    # Fallback to direct database connection
                    database = get_database()
                
                if database:
                    image_manager = ProfileImageManager(database)
                    logger.info("📷 ProfileImageManager initialized lazily for serve")
                else:
                    logger.error("No database connection available for ProfileImageManager serve")
                    return redirect('/static/logos/New IntroLogo.png')
                    
            except Exception as init_error:
                logger.error(f"Failed to initialize ProfileImageManager for serve: {init_error}")
                return redirect('/static/logos/New IntroLogo.png')
        
        image_bytes, mime_type = image_manager.serve_profile_image(user_id)
        
        if image_bytes:
            return Response(image_bytes, mimetype=mime_type)
        else:
            return redirect('/static/logos/New IntroLogo.png')
        
    except Exception as e:
        logger.error(f"Serve profile image error: {e}")
        return redirect('/static/logos/New IntroLogo.png')

@profile_bp.route("/api/delete-profile-image", methods=["DELETE"])
def delete_profile_image():
    """Delete user's profile image"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not image_manager:
            return jsonify({"success": False, "error": "Image service not available"}), 503
        
        user_id = session.get('user_id')
        result = image_manager.delete_profile_image(user_id)
        
        # Update session if successful
        if result['success']:
            session.pop('profile_image', None)
            session.modified = True
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Delete profile image error: {e}")
        return jsonify({"success": False, "error": "Failed to delete image"}), 500

@profile_bp.route("/api/profile-image/stats", methods=["GET"])
def get_profile_image_stats():
    """Get profile image statistics"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not image_manager:
            return jsonify({"success": False, "error": "Image service not available"}), 503
        
        user_id = session.get('user_id')
        result = image_manager.get_image_stats(user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Image stats error: {e}")
        return jsonify({"success": False, "error": "Failed to get image stats"}), 500

# ================================
# THEME MANAGEMENT
# ================================

@profile_bp.route("/theme-palette")
def theme_palette_page():
    """Theme palette page - redirects to tier-specific routes"""
    if not is_logged_in():
        return redirect("/login")
        
    user_plan = session.get('user_plan', 'bronze')
    trial_active = session.get('trial_active', False)
    
    # Redirect to appropriate tier
    if user_plan == 'gold' or (trial_active and user_plan == 'bronze'):
        return redirect("/theme-palette/gold")
    elif user_plan == 'silver':
        return redirect("/theme-palette/silver")
    else:
        return redirect("/subscription?feature=theme-palette")

@profile_bp.route("/theme-palette/silver")
def theme_palette_silver():
    """Theme palette Silver tier page"""
    if not is_logged_in():
        return redirect("/login")
    
    user_plan = session.get('user_plan', 'bronze')
    trial_active = session.get('trial_active', False)
    
    if user_plan not in ['silver', 'gold'] and not trial_active:
        return redirect("/subscription?feature=theme-palette")
    
    return render_template("theme_palette.html", tier="silver")

@profile_bp.route("/theme-palette/gold")
def theme_palette_gold():
    """Theme palette Gold tier page"""
    if not is_logged_in():
        return redirect("/login")
    
    user_plan = session.get('user_plan', 'bronze')
    trial_active = session.get('trial_active', False)
    
    if user_plan not in ['gold'] and not trial_active:
        return redirect("/subscription?feature=theme-palette")
    
    return render_template("theme_palette.html", tier="gold")

@profile_bp.route("/api/user/save-theme", methods=["POST"])
def save_user_theme():
    """Save user's theme preferences for specific tier"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not theme_manager:
            return jsonify({"success": False, "error": "Theme service not available"}), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        user_id = session.get('user_id')
        tier = data.get('tier', 'general')
        
        theme_data = {
            'background': data.get('background', '#0f172a'),
            'text': data.get('text', '#22d3ee'),
            'accent': data.get('accent', '#06b6d4')
        }
        
        result = theme_manager.save_theme(user_id, tier, theme_data)
        
        # Update session cache if successful
        if result['success']:
            if 'user_themes' not in session:
                session['user_themes'] = {}
            session['user_themes'][tier] = theme_data
            session.modified = True
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Save theme error: {e}")
        return jsonify({"success": False, "error": "Failed to save theme"}), 500

@profile_bp.route("/api/user/get-theme", methods=["GET"])
def get_user_theme():
    """Get user's theme preferences for specific tier"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not theme_manager:
            return jsonify({"success": False, "error": "Theme service not available"}), 503
        
        user_id = session.get('user_id')
        tier = request.args.get('tier', 'general')
        
        # Check session cache first
        user_themes = session.get('user_themes', {})
        if tier in user_themes:
            return jsonify({"success": True, "theme": user_themes[tier]})
        
        # Get from database
        result = theme_manager.get_theme(user_id, tier)
        
        # Cache in session if successful
        if result['success']:
            if 'user_themes' not in session:
                session['user_themes'] = {}
            session['user_themes'][tier] = result['theme']
            session.modified = True
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get theme error: {e}")
        return jsonify({"success": False, "error": "Failed to get theme"}), 500

@profile_bp.route("/api/user/get-all-themes", methods=["GET"])
def get_all_user_themes():
    """Get all user's themes across all tiers"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not theme_manager:
            return jsonify({"success": False, "error": "Theme service not available"}), 503
        
        user_id = session.get('user_id')
        result = theme_manager.get_all_themes(user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get all themes error: {e}")
        return jsonify({"success": False, "error": "Failed to get themes"}), 500

@profile_bp.route("/api/user/reset-theme", methods=["POST"])
def reset_user_theme():
    """Reset theme to default for specific tier"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not theme_manager:
            return jsonify({"success": False, "error": "Theme service not available"}), 503
        
        data = request.get_json() or {}
        tier = data.get('tier', 'general')
        
        user_id = session.get('user_id')
        result = theme_manager.reset_theme(user_id, tier)
        
        # Update session cache if successful
        if result['success']:
            user_themes = session.get('user_themes', {})
            if tier in user_themes:
                del user_themes[tier]
                session['user_themes'] = user_themes
                session.modified = True
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Reset theme error: {e}")
        return jsonify({"success": False, "error": "Failed to reset theme"}), 500

@profile_bp.route("/api/theme/presets", methods=["GET"])
def get_theme_presets():
    """Get available theme presets"""
    try:
        if not theme_manager:
            return jsonify({"success": False, "error": "Theme service not available"}), 503
        
        result = theme_manager.get_theme_presets()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get theme presets error: {e}")
        return jsonify({"success": False, "error": "Failed to get presets"}), 500

@profile_bp.route("/api/theme/apply-preset", methods=["POST"])
def apply_theme_preset():
    """Apply a theme preset to user's tier"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not theme_manager:
            return jsonify({"success": False, "error": "Theme service not available"}), 503
        
        data = request.get_json()
        if not data or 'tier' not in data or 'preset_name' not in data:
            return jsonify({"success": False, "error": "Tier and preset_name required"}), 400
        
        user_id = session.get('user_id')
        result = theme_manager.apply_preset(user_id, data['tier'], data['preset_name'])
        
        # Update session cache if successful
        if result['success']:
            # Reload theme into session
            theme_result = theme_manager.get_theme(user_id, data['tier'])
            if theme_result['success']:
                if 'user_themes' not in session:
                    session['user_themes'] = {}
                session['user_themes'][data['tier']] = theme_result['theme']
                session.modified = True
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Apply preset error: {e}")
        return jsonify({"success": False, "error": "Failed to apply preset"}), 500

# ================================
# COMMUNITY AVATAR MANAGEMENT
# ================================

@profile_bp.route("/community/avatar", methods=["GET"])
def get_community_avatar():
    """Get current user's community avatar/companion - PURE: always returns valid record"""
    try:
        logger.info(f"GET /community/avatar user={session.get('user_id')} -> {'authed' if is_logged_in() else 'anon'}")
        
        if not is_logged_in():
            logger.warning(f"GET /community/avatar: User not authenticated, returning 401")
            return jsonify({"success": False, "error": "Authentication required"}), 401

        from database_utils import get_database
        import json

        user_id = session.get("user_id")
        companion_info = None

        try:
            database = get_database()
            if database:
                conn = database.get_connection()
                cursor = conn.cursor()
                uid = int(user_id) if database.use_postgres else user_id

                if database.use_postgres:
                    cursor.execute("SELECT companion_data FROM users WHERE id = %s", (uid,))
                else:
                    cursor.execute("SELECT companion_data FROM users WHERE id = ?", (uid,))
                row = cursor.fetchone()
                conn.close()

                if row and row[0]:
                    companion_info = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    logger.info(f"✅ Avatar loaded from database for user {user_id}")
        except Exception as db_error:
            logger.warning(f"Database avatar load failed for user {user_id}: {db_error}")

        if not companion_info:
            companion_info = {
                "name": "Soul",
                "companion_id": "soul",
                "avatar_url": "/static/companions/soul.png",
                "tier": "bronze"
            }

        # Safety: ensure avatar_url is set when companion_id exists
        if not companion_info.get("avatar_url") and companion_info.get("companion_id"):
            companion_info["avatar_url"] = f"/static/companions/{companion_info['companion_id']}.png"

        # Cache (optional)
        session["companion_info"] = companion_info
        session.modified = True

        return jsonify({"success": True, "companion": companion_info})
        
    except Exception as e:
        logger.error(f"Get community avatar error: {e}")
        return jsonify({"success": False, "error": "Failed to load avatar"}), 500

@profile_bp.route("/community/avatar", methods=["POST"])
def set_community_avatar():
    """Set user's community avatar/companion with database persistence"""
    try:
        logger.info(f"POST /community/avatar user={session.get('user_id')} -> {'authed' if is_logged_in() else 'anon'}")
        
        if not is_logged_in():
            logger.warning(f"POST /community/avatar: User not authenticated, returning 401")
            return jsonify({"success": False, "error": "Authentication required"}), 401

        data = request.get_json() or {}
        companion_id = data.get("companion_id")
        if not companion_id:
            return jsonify({"success": False, "error": "Companion ID required"}), 400

        from database_utils import get_database
        from datetime import datetime
        import json

        user_id = session.get("user_id")
        now_iso = datetime.now().isoformat()

        companion_data = {
            "name": data.get("name", "Soul"),
            "companion_id": companion_id,
            "avatar_url": data.get("avatar_url") or f"/static/companions/{companion_id}.png",
            "tier": data.get("tier", "bronze"),
            "updated_at": now_iso,
        }

        database_saved = False
        try:
            database = get_database()
            if database:
                conn = database.get_connection()
                cursor = conn.cursor()
                payload = json.dumps(companion_data)
                uid = int(user_id) if database.use_postgres else user_id

                if database.use_postgres:
                    cursor.execute(
                        "UPDATE users SET companion_data = %s WHERE id = %s RETURNING id",
                        (payload, uid),
                    )
                    row = cursor.fetchone()
                    if row:
                        conn.commit()
                        database_saved = True
                        logger.info(f"✅ Avatar saved to database for user {user_id}")
                    else:
                        logger.warning(f"⚠️ No user row matched id={uid} when saving companion_data")
                else:
                    cursor.execute("UPDATE users SET companion_data = ? WHERE id = ?", (payload, uid))
                    if cursor.rowcount > 0:
                        conn.commit()
                        database_saved = True
                        logger.info(f"✅ Avatar saved to database for user {user_id}")
                    else:
                        logger.warning(f"⚠️ No user row matched id={uid} when saving companion_data (SQLite)")
                conn.close()
        except Exception as db_error:
            logger.error(f"❌ Database save failed for user {user_id}: {db_error}")

        # Session cache
        session["companion_info"] = companion_data
        session.modified = True

        logger.info(f"POST /community/avatar user={user_id} saved={database_saved} companion={companion_id}")
        
        return jsonify({
            "success": True,
            "message": "Avatar updated",
            "companion": companion_data,
            "database_saved": database_saved
        })
        
    except Exception as e:
        logger.error(f"Set community avatar error: {e}")
        return jsonify({"success": False, "error": "Failed to set avatar"}), 500

@profile_bp.route("/community/avatar/check", methods=["GET"])
def check_avatar_cooldown():
    """Check if user can change avatar (no cooldown for community)"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # No cooldown for community avatar changes
        return jsonify({
            "success": True,
            "can_change": True
        })
        
    except Exception as e:
        logger.error(f"Avatar cooldown check error: {e}")
        return jsonify({"success": False, "error": "Failed to check cooldown"}), 500

@profile_bp.route("/community/avatar/debug", methods=["GET"])
def debug_avatar_database():
    """Debug endpoint to check what's actually in the database"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        
        # Check what's in the database
        from database_utils import get_database
        import json
        
        database = get_database()
        if not database:
            return jsonify({"success": False, "error": "Database not available"}), 503
            
        conn = database.get_connection()
        cursor = conn.cursor()
        
        if database.use_postgres:
            cursor.execute("SELECT id, companion_data FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT id, companion_data FROM users WHERE id = ?", (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            raw_data = result[1]
            parsed_data = None
            data_type = type(raw_data).__name__
            
            try:
                if isinstance(raw_data, dict):
                    parsed_data = raw_data
                elif raw_data:
                    parsed_data = json.loads(raw_data)
            except Exception as parse_error:
                parsed_data = f"Parse error: {parse_error}"
            
            return jsonify({
                "success": True,
                "debug_info": {
                    "user_id": user_id,
                    "raw_data": str(raw_data)[:500],  # Limit size
                    "data_type": data_type,
                    "parsed_data": parsed_data,
                    "database_type": "postgresql" if database.use_postgres else "sqlite"
                }
            })
        else:
            return jsonify({
                "success": True,
                "debug_info": {
                    "user_id": user_id,
                    "raw_data": None,
                    "message": "No data found for user"
                }
            })
        
    except Exception as e:
        logger.error(f"Avatar debug error: {e}")
        return jsonify({"success": False, "error": f"Debug failed: {e}"}), 500

# ================================
# UTILITY FUNCTIONS
# ================================

def load_user_theme_into_session(user_id: int) -> None:
    """Load user's theme preferences into session (for use during login)"""
    try:
        if theme_manager:
            theme_manager.load_theme_into_session(user_id, session)
    except Exception as e:
        logger.warning(f"Failed to load theme into session: {e}")

def preserve_profile_data_in_session() -> dict:
    """Preserve important profile data during session operations"""
    try:
        if profile_service:
            return profile_service.preserve_session_profile_data(session)
        return {}
    except Exception as e:
        logger.warning(f"Failed to preserve profile data: {e}")
        return {}

def restore_profile_data_to_session(preserved_data: dict) -> None:
    """Restore preserved profile data to session"""
    try:
        if profile_service:
            profile_service.restore_session_profile_data(session, preserved_data)
    except Exception as e:
        logger.warning(f"Failed to restore profile data: {e}")