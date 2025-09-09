"""
SoulBridge AI - Consolidated API Routes
All remaining API endpoints consolidated into organized routes
Extracted from monolith app.py with improvements
"""
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, session

from ..auth.session_manager import requires_login, get_user_id
from .session_api import SessionAPI
from .user_api import UserAPI
from .debug_api import DebugAPI
from constants import PLAN_LIMITS, FEATURE_ACCESS

logger = logging.getLogger(__name__)

# =============================================================================
# COMPANION DATA AND UTILITIES
# =============================================================================

def get_all_companions():
    """Get complete list of all companions with their tier information"""
    # Import from the centralized companion data source
    try:
        from ..companions.companion_data import get_all_companions as get_centralized_companions
        return get_centralized_companions()
    except ImportError:
        # Fallback to hardcoded list if companion module not available
        logger.warning("Could not import centralized companion data, using fallback")
        return [
        # Bronze companions (10)
        {"id": "gamerjay_bronze", "name": "GamerJay", "tier": "bronze", "image_url": "/static/logos/GamerJay_Free_companion.png"},
        {"id": "blayzo_bronze", "name": "Blayzo", "tier": "bronze", "image_url": "/static/logos/Blayzo.png"},
        {"id": "blayzica_bronze", "name": "Blayzica", "tier": "bronze", "image_url": "/static/logos/Blayzica.png"},
        {"id": "claude_bronze", "name": "Claude", "tier": "bronze", "image_url": "/static/logos/Claude_Free.png"},
        {"id": "blayzia_bronze", "name": "Blayzia", "tier": "bronze", "image_url": "/static/logos/Blayzia.png"},
        {"id": "blayzion_bronze", "name": "Blayzion", "tier": "bronze", "image_url": "/static/logos/Blayzion.png"},
        {"id": "lumen_bronze", "name": "Lumen", "tier": "bronze", "image_url": "/static/logos/Lumen_Bronze.png"},
        {"id": "blayzo2_bronze", "name": "Blayzo.2", "tier": "bronze", "image_url": "/static/logos/blayzo_free_tier.png"},
        {"id": "crimson_bronze", "name": "Crimson", "tier": "bronze", "image_url": "/static/logos/Crimson_Free.png"},
        {"id": "violet_bronze", "name": "Violet", "tier": "bronze", "image_url": "/static/logos/Violet_Free.png"},
        
        # Silver companions (8)
        {"id": "sky_silver", "name": "Sky", "tier": "silver", "image_url": "/static/logos/Sky_a_premium_companion.png"},
        {"id": "gamerjay_silver", "name": "GamerJay.2", "tier": "silver", "image_url": "/static/logos/GamerJay_premium_companion.png"},
        {"id": "claude_silver", "name": "Claude.3", "tier": "silver", "image_url": "/static/logos/Claude_Growth.png"},
        {"id": "blayzo_silver", "name": "Blayzo.3", "tier": "silver", "image_url": "/static/logos/Blayzo_premium_companion.png"},
        {"id": "blayzica_silver", "name": "Blayzica.2", "tier": "silver", "image_url": "/static/logos/Blayzica_Pro.png"},
        {"id": "watchdog_silver", "name": "WatchDog", "tier": "silver", "image_url": "/static/logos/WatchDog_a_Premium_companion.png"},
        {"id": "rozia_silver", "name": "Rozia", "tier": "silver", "image_url": "/static/logos/Rozia_Silver.png"},
        {"id": "lumen_silver", "name": "Lumen.2", "tier": "silver", "image_url": "/static/logos/Lumen_Silver.png"},
        
        # Gold companions (8)
        {"id": "crimson_gold", "name": "Crimson.2", "tier": "gold", "image_url": "/static/logos/Crimson_a_Max_companion.png"},
        {"id": "violet_gold", "name": "Violet.2", "tier": "gold", "image_url": "/static/logos/Violet_a_Max_companion.png"},
        {"id": "claude_gold", "name": "Claude.2", "tier": "gold", "image_url": "/static/logos/Claude_Max.png"},
        {"id": "royal_gold", "name": "Royal", "tier": "gold", "image_url": "/static/logos/Royal_a_Max_companion.png"},
        {"id": "ven_blayzica_gold", "name": "Ven Blayzica", "tier": "gold", "image_url": "/static/logos/Ven_Blayzica_a_Max_companion.png"},
        {"id": "ven_sky_gold", "name": "Ven Sky", "tier": "gold", "image_url": "/static/logos/Ven_Sky_a_Max_companion.png"},
        {"id": "watchdog_gold", "name": "WatchDog.2", "tier": "gold", "image_url": "/static/logos/WatchDog_a_Max_Companion.png"},
        {"id": "dr_madjay_gold", "name": "Dr. MadJay", "tier": "gold", "image_url": "/static/logos/Dr. MadJay.png"},
        
        # Referral companions (5)
        {"id": "blayzike", "name": "Blayzike", "tier": "silver", "image_url": "/static/referral/blayzike.png", "min_referrals": 2},
        {"id": "nyxara", "name": "Nyxara", "tier": "silver", "image_url": "/static/logos/Nyxara.png", "min_referrals": 6},
        {"id": "blazelian", "name": "Blazelian", "tier": "gold", "image_url": "/static/referral/blazelian.png", "min_referrals": 4},
        {"id": "claude_referral", "name": "Claude Referral", "tier": "gold", "image_url": "/static/referral/claude_referral.png", "min_referrals": 8},
        {"id": "blayzo_referral", "name": "Blayzo Referral", "tier": "gold", "image_url": "/static/logos/Blayzo_Referral.png", "min_referrals": 10},
    ]

def get_companion_by_id(companion_id):
    """Get companion data by ID"""
    companions = get_all_companions()
    return next((c for c in companions if c['id'] == companion_id), None)

def get_companion_tier_limits(companion_tier):
    """Get limits for a specific companion tier"""
    return PLAN_LIMITS.get(companion_tier, PLAN_LIMITS["bronze"])

def get_effective_plan():
    """Get effective user plan considering trial status"""
    user_plan = session.get('user_plan', 'bronze')
    trial_active = session.get('trial_active', False)
    
    # If user is on trial, they get Gold access for companion selection
    # (but not for feature limits - that stays at their actual tier)
    if trial_active and user_plan == 'bronze':
        return 'gold'
    
    return user_plan

def get_companion_usage_keys(user_id, companion_id):
    """Generate per-companion usage keys for session storage"""
    today = datetime.now().strftime('%Y-%m-%d')
    return {
        'decoder': f"decoder_usage_{user_id}_{companion_id}_{today}",
        'fortune': f"fortune_usage_{user_id}_{companion_id}_{today}",
        'horoscope': f"horoscope_usage_{user_id}_{companion_id}_{today}",
        'creative_writer': f"creative_writer_usage_{user_id}_{companion_id}_{today}",
    }

def get_companion_feature_usage(user_id, companion_id, feature):
    """Get companion-specific feature usage from session"""
    usage_keys = get_companion_usage_keys(user_id, companion_id)
    usage_key = usage_keys.get(feature)
    if not usage_key:
        return 0
    return session.get(usage_key, 0)

def increment_companion_feature_usage(user_id, companion_id, feature):
    """Increment companion-specific feature usage in session"""
    usage_keys = get_companion_usage_keys(user_id, companion_id)
    usage_key = usage_keys.get(feature)
    if not usage_key:
        logger.error(f"Unknown feature for usage tracking: {feature}")
        return False
    
    current_usage = session.get(usage_key, 0)
    session[usage_key] = current_usage + 1
    session.modified = True
    
    logger.info(f"🎯 COMPANION USAGE: user={user_id}, companion={companion_id}, feature={feature}, usage={current_usage + 1}")
    return True

def check_companion_feature_limit(user_id, companion_id, feature):
    """Check if companion feature usage is within limits"""
    companion = get_companion_by_id(companion_id)
    if not companion:
        return False
    
    companion_tier = companion['tier']
    limits = get_companion_tier_limits(companion_tier)
    feature_limit = limits.get(feature, 0)
    
    # Check if usage is within limit (no more "unlimited" concept)
    current_usage = get_companion_feature_usage(user_id, companion_id, feature)
    return current_usage < feature_limit

# Create API blueprint
api_bp = Blueprint('api', __name__)

# Initialize API services
session_api = SessionAPI()
user_api = UserAPI()
debug_api = DebugAPI()

# Session Management Endpoints
@api_bp.route('/session-refresh', methods=['POST'])
@requires_login
def session_refresh():
    """Refresh user session data"""
    try:
        result = session_api.refresh_session()
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 401
        
    except Exception as e:
        logger.error(f"Error in session refresh endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Session refresh failed"
        }), 500

@api_bp.route('/user-status', methods=['GET'])
def user_status():
    """Get current user status (handles both authenticated and unauthenticated users)"""
    try:
        status = session_api.get_user_status()
        # Add logged_in field for frontend compatibility
        status["logged_in"] = status.get("authenticated", False)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error in user status endpoint: {e}")
        return jsonify({
            "authenticated": False,
            "logged_in": False,
            "error": str(e)
        }), 500

@api_bp.route('/check-user-status', methods=['GET'])
@requires_login
def check_user_status():
    """Alternative user status endpoint"""
    try:
        return user_status()  # Redirect to main user status
        
    except Exception as e:
        logger.error(f"Error checking user status: {e}")
        return jsonify({
            "authenticated": False,
            "error": str(e)
        }), 500

@api_bp.route('/clear-session', methods=['POST'])
@requires_login
def clear_session():
    """Clear user session"""
    try:
        result = session_api.clear_session()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to clear session"
        }), 500

@api_bp.route('/logout-on-close', methods=['POST'])
@requires_login
def logout_on_close():
    """Handle logout when browser closes"""
    try:
        result = session_api.logout_on_close()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in logout on close: {e}")
        return jsonify({
            "success": False,
            "error": "Logout failed"
        }), 500

# =============================================================================
# COMPANION-TIER-BASED API ENDPOINTS (ARCHITECTURAL FIX)
# =============================================================================

@api_bp.route('/tier-limits', methods=['GET'])
@requires_login
def tier_limits_companion_based():
    """
    🚨 ARCHITECTURAL FIX: Companion-tier-based limits instead of user-tier-based
    
    Returns limits and usage based on the current companion's tier, not the user's subscription.
    This ensures Bronze users visiting Gold companions see Gold limits/features, while 
    tracking usage separately per-companion.
    """
    try:
        user_id = get_user_id()
        companion_id = session.get('selected_companion')
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        if not companion_id:
            return jsonify({
                'success': False,
                'error': 'No companion selected'
            }), 400
        
        # Get companion data and tier
        companion = get_companion_by_id(companion_id)
        if not companion:
            return jsonify({
                'success': False,
                'error': 'Invalid companion'
            }), 400
        
        companion_tier = companion['tier']
        
        # Get companion-tier-based limits (not user-tier based)
        limits = get_companion_tier_limits(companion_tier)
        
        # Get per-companion usage keys
        usage_keys = get_companion_usage_keys(user_id, companion_id)
        
        # Get current usage from session (per-companion tracking)
        usage = {}
        for feature, key in usage_keys.items():
            usage[feature] = session.get(key, 0)
        
        # Use actual limits (no more "unlimited" conversion)
        display_limits = limits
        
        # Check if user can access this companion tier during trial
        user_effective_plan = "gold" if trial_active else user_plan
        can_access = (
            companion_tier == "bronze" or  # Everyone can access Bronze
            (companion_tier == "silver" and user_effective_plan in ["silver", "gold"]) or
            (companion_tier == "gold" and user_effective_plan == "gold")
        )
        
        response_data = {
            'success': True,
            'companion_id': companion_id,
            'companion_name': companion['name'],
            'companion_tier': companion_tier,
            'user_plan': user_plan,
            'trial_active': trial_active,
            'can_access': can_access,
            'limits': display_limits,
            'usage': usage,
            'usage_keys': usage_keys,  # Debug info
            'architecture': 'companion-tier-based'  # Debug marker
        }
        
        logger.info(f"🎯 COMPANION-TIER API: user={user_id}, companion={companion_id}({companion_tier}), limits={display_limits}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Companion-tier limits API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get tier limits'
        }), 500

# User Information Endpoints
@api_bp.route('/user-info')
@requires_login
def user_info():
    """Get comprehensive user information"""
    try:
        result = user_api.get_user_info()
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 401
        
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get user information"
        }), 500

@api_bp.route('/me')
@requires_login  
def me():
    """Get basic user information - alias for /user-info"""
    try:
        result = user_api.get_user_info()
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 401
        
    except Exception as e:
        logger.error(f"Error getting user info via /me: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get user information"
        }), 500

@api_bp.route('/trial-status')
@requires_login
def trial_status():
    """Get trial status information"""
    try:
        result = user_api.get_trial_status()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting trial status: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get trial status"
        }), 500

@api_bp.route('/user-plan')
@requires_login
def user_plan():
    """Get user plan information"""
    try:
        result = user_api.get_user_plan_info()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting user plan: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get plan information"
        }), 500

@api_bp.route('/plan')
@requires_login  
def plan_info():
    """Alternative plan info endpoint"""
    try:
        return user_plan()  # Redirect to main plan endpoint
        
    except Exception as e:
        logger.error(f"Error getting plan info: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get plan information"
        }), 500

@api_bp.route('/user-addons')
@requires_login
def user_addons():
    """Get user's active addons"""
    try:
        result = user_api.get_user_addons()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting user addons: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get user addons"
        }), 500

@api_bp.route('/accept-terms', methods=['POST'])
@requires_login
def accept_terms():
    """Accept terms of service"""
    try:
        data = request.get_json() or {}
        terms_version = data.get('version', 'latest')
        
        result = user_api.accept_terms(terms_version)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error accepting terms: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to accept terms"
        }), 500

@api_bp.route('/sync-trial-session')
@requires_login
def sync_trial_session():
    """Sync trial status with session"""
    try:
        result = session_api.sync_trial_session()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error syncing trial session: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to sync trial session"
        }), 500

# Feature Access Endpoints
@api_bp.route('/protected-feature')
@requires_login
def protected_feature():
    """Check protected feature access"""
    try:
        feature = request.args.get('feature', 'unknown')
        result = user_api.check_feature_access(feature)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error checking protected feature: {e}")
        return jsonify({
            "has_access": False,
            "reason": "error",
            "error": str(e)
        }), 500

@api_bp.route('/log-action', methods=['POST'])
@requires_login
def log_action():
    """Log user action for analytics"""
    try:
        data = request.get_json() or {}
        action_type = data.get('action_type', 'unknown')
        action_data = data.get('data', {})
        
        result = user_api.log_user_action(action_type, action_data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error logging action: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to log action"
        }), 500

@api_bp.route('/feature-preview-seen', methods=['POST'])
@requires_login
def feature_preview_seen():
    """Mark feature preview as seen"""
    try:
        data = request.get_json() or {}
        feature = data.get('feature', 'unknown')
        
        # Log as user action
        result = user_api.log_user_action('feature_preview_seen', {'feature': feature})
        
        return jsonify({
            "success": True,
            "message": f"Feature preview marked as seen: {feature}"
        })
        
    except Exception as e:
        logger.error(f"Error marking feature preview seen: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to mark preview as seen"
        }), 500

# =============================================================================
# SAPPHIRE GUIDE CHARACTER
# =============================================================================

@api_bp.route('/sapphire-chat', methods=['POST'])
@requires_login
def sapphire_chat():
    """Sapphire AI Navigation Assistant - Real OpenAI Integration"""
    try:
        from openai import OpenAI
        import os
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Invalid request"}), 400
            
        message = data['message'].strip()
        if not message:
            return jsonify({"error": "Please provide a message"}), 400
            
        if len(message) > 500:
            return jsonify({"error": "Message too long"}), 400
        
        # Get user context safely
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # System prompt for Sapphire
        system_prompt = f"""You are Sapphire 💎, the WARM & CARING NAVIGATION ASSISTANT for SoulBridge AI. Your purpose is to make every user feel welcomed and supported while helping them navigate the app.

PERSONALITY TRAITS:
- 💎 Warm, caring, and genuinely helpful
- 🌟 Patient and understanding
- ✨ Encouraging and positive
- 🔮 Knowledgeable about all app features
- 💫 Makes complex things simple to understand

CORE RESPONSIBILITIES:
1. Help users understand SoulBridge AI features and navigation
2. Guide users to the right tools for their needs
3. Answer questions about subscription tiers and features
4. Provide warm, supportive assistance
5. Make users feel welcomed and valued

INTERACTION STYLE:
- Use the 💎 emoji occasionally to maintain brand identity
- Be concise but warm (2-3 sentences max)
- Always offer next steps or suggestions
- Use encouraging language
- Make users feel supported

USER CONTEXT:
- User tier: {user_plan}
- Trial status: {trial_active}

Remember: You're here to help users navigate and succeed with SoulBridge AI. Be their supportive guide! 💎"""
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        sapphire_response = response.choices[0].message.content.strip()
        
        # Log interaction
        logger.info(f"Sapphire chat request from user {get_user_id()}")
        
        return jsonify({"message": sapphire_response})
        
    except Exception as e:
        logger.error(f"Sapphire chat error: {e}")
        return jsonify({
            "error": "💎 I'm temporarily unavailable, but I'll be back soon! Try checking our help section in your profile."
        }), 500

# Debug Endpoints (restricted to debug mode)
@api_bp.route('/debug/force-session-reset')
def debug_force_session_reset():
    """Force reset session (debug only)"""
    try:
        result = debug_api.force_session_reset()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in debug force session reset: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/debug/reset-to-bronze')
def debug_reset_to_bronze():
    """Reset user to bronze tier (debug only)"""
    try:
        result = debug_api.reset_to_bronze()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in debug reset to bronze: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/debug/upgrade-to-silver')
def debug_upgrade_to_silver():
    """Upgrade to silver tier (debug only)"""
    try:
        result = debug_api.upgrade_to_tier('silver')
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in debug upgrade to silver: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/debug/upgrade-to-gold')
def debug_upgrade_to_gold():
    """Upgrade to gold tier (debug only)"""
    try:
        result = debug_api.upgrade_to_tier('gold')
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in debug upgrade to gold: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/debug/reset-trial-state')
def debug_reset_trial_state():
    """Reset trial state (debug only)"""
    try:
        result = debug_api.reset_trial_state()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in debug reset trial: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/debug/get-current-plan')
def debug_get_current_plan():
    """Get current plan info (debug)"""
    try:
        result = debug_api.get_current_plan_info()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting debug plan info: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/debug/refresh-session')
def debug_refresh_session():
    """Refresh session with debug info"""
    try:
        result = debug_api.refresh_session_debug()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in debug refresh session: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Legacy/Compatibility Endpoints
@api_bp.route('/mini-assistant-status', methods=['GET'])
def mini_assistant_status():
    """Mini assistant status (redirect to health check)"""
    try:
        from ..health.health_checker import HealthChecker
        
        health_checker = HealthChecker()
        health_data = health_checker.get_system_health()
        
        # Format for mini assistant compatibility
        openai_status = health_data.get('external_services', {}).get('openai_api', {}).get('status', 'unknown')
        database_status = health_data.get('database', {}).get('status', 'unknown')
        
        status = 'operational'
        if openai_status != 'healthy' or database_status != 'connected':
            status = 'degraded'
        
        return jsonify({
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "openai_api": openai_status,
                "database": database_status,
                "system": "healthy" if health_data.get('system', {}).get('cpu_percent', 0) < 80 else "busy"
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting mini assistant status: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# Theme Endpoints
@api_bp.route('/get-theme')
@requires_login
def get_theme():
    """Get user theme preferences - simple endpoint for compatibility"""
    try:
        # Return a simple default theme for now
        return jsonify({
            "success": True,
            "theme": {
                "name": "default",
                "primary": "#6366f1",
                "secondary": "#8b5cf6", 
                "accent": "#06b6d4",
                "background": "#ffffff",
                "text": "#1f2937"
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting theme: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get theme"
        }), 500

@api_bp.route('/horoscope/limits')
@requires_login  
def horoscope_limits():
    """Get user's horoscope usage limits - temporary fix for 404"""
    try:
        from unified_tier_system import get_feature_limit, get_feature_usage_today
        
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Get limits and usage
        daily_limit = get_feature_limit(user_plan, 'horoscope', trial_active) 
        usage_today = get_feature_usage_today(user_id, 'horoscope')
        remaining = max(0, daily_limit - usage_today)
        unlimited = daily_limit >= 999999
        
        return jsonify({
            "success": True,
            "user_tier": user_plan,
            "daily_limit": daily_limit,
            "usage_today": usage_today,
            "remaining": remaining,
            "unlimited": unlimited
        })
        
    except Exception as e:
        logger.error(f"Error getting horoscope limits: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get horoscope limits",
            "user_tier": "bronze",
            "daily_limit": 5,
            "usage_today": 0,
            "remaining": 5,
            "unlimited": False
        }), 500

# Entitlements/Trial Endpoints (v1 compatibility)
@api_bp.route('/v1/entitlements')
@requires_login  
def v1_entitlements():
    """
    🚨 ARCHITECTURAL FIX: Companion-tier-based entitlements (v1 compatibility)
    
    Returns entitlements based on current companion's tier, not user's subscription.
    Maintains v1 API compatibility while fixing the architectural mismatch.
    """
    try:
        user_id = get_user_id()
        companion_id = session.get('selected_companion')
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        trial_expires_at = session.get('trial_expires_at')
        
        # Default to bronze if no companion selected
        if not companion_id:
            companion_tier = "bronze"
        else:
            companion = get_companion_by_id(companion_id)
            companion_tier = companion['tier'] if companion else "bronze"
        
        # Get companion-tier-based limits instead of user-tier-based
        limits = get_companion_tier_limits(companion_tier)
        
        # Check if user can access this companion tier
        user_effective_plan = "gold" if trial_active else user_plan
        can_access = (
            companion_tier == "bronze" or  # Everyone can access Bronze
            (companion_tier == "silver" and user_effective_plan in ["silver", "gold"]) or
            (companion_tier == "gold" and user_effective_plan == "gold")
        )
        
        # Generate daily_limits with actual values (no more "unlimited")
        daily_limits = limits
        
        # Return v1-compatible format with companion-tier data
        response = {
            "logged_in": True,
            "user_id": user_id,
            "user_plan": user_plan,
            "tier": companion_tier,  # 🚨 KEY FIX: Return companion tier, not user tier
            "companion_id": companion_id,
            "companion_tier": companion_tier,
            "trial_active": trial_active,
            "trial_expires_at": trial_expires_at,
            "can_access": can_access,
            "daily_limits": daily_limits,  # v1 compatibility
            "entitlements": {
                "decoder": {"enabled": True, "limit": "premium" if companion_tier == "gold" else "limited"},
                "fortune": {"enabled": True, "limit": "premium" if companion_tier == "gold" else "limited"}, 
                "horoscope": {"enabled": True, "limit": "premium" if companion_tier == "gold" else "limited"},
                "creative_writer": {"enabled": True, "limit": "premium" if companion_tier == "gold" else "limited"},
                "ai_images": {"enabled": companion_tier in ["silver", "gold"], "limit": "credit"},
                "voice_chat": {"enabled": companion_tier in ["silver", "gold"], "limit": "credit"},
                "mini_studio": {"enabled": companion_tier == "gold", "limit": "credit"}
            },
            "architecture": "companion-tier-based"  # Debug marker
        }
        
        logger.info(f"🎯 V1 ENTITLEMENTS: user={user_id}, companion={companion_id}({companion_tier}), access={can_access}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting v1 entitlements: {e}")
        return jsonify({
            "logged_in": False,
            "error": "Failed to get entitlements"
        }), 500

# =============================================================================
# COMPANION-TIER FEATURE API ENDPOINTS (USAGE TRACKING FIX)
# =============================================================================

@api_bp.route('/companion/decoder/check-limit', methods=['GET'])
@requires_login
def check_companion_decoder_limit():
    """
    🚨 SOUL COMPANION UNIFIED: Check decoder credit availability
    
    Returns credit balance and decoder cost information.
    """
    try:
        user_id = get_user_id()
        companion_id = session.get('selected_companion')
        
        if not companion_id:
            return jsonify({
                'success': False,
                'error': 'No companion selected'
            }), 400
        
        companion = get_companion_by_id(companion_id)
        if not companion:
            return jsonify({
                'success': False,
                'error': 'Invalid companion'
            }), 400
        
        # Get current credit balance
        from ...modules.credits.operations import get_artistic_time
        current_credits = get_artistic_time(user_id)
        decoder_cost = 3  # From constants.py
        
        can_use = current_credits >= decoder_cost
        
        return jsonify({
            'success': True,
            'companion_id': companion_id,
            'companion_name': companion['name'],
            'feature': 'decoder',
            'current_credits': current_credits,
            'cost': decoder_cost,
            'can_use': can_use,
            'credits_needed': max(0, decoder_cost - current_credits)
        })
        
    except Exception as e:
        logger.error(f"Companion decoder limit check error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to check decoder limit'
        }), 500

@api_bp.route('/companion/decoder/use', methods=['POST'])
@requires_login
def use_companion_decoder():
    """
    🚨 SOUL COMPANION UNIFIED: Use decoder with Artistic Time credits
    """
    try:
        user_id = get_user_id()
        companion_id = session.get('selected_companion')
        
        if not companion_id:
            return jsonify({
                'success': False,
                'error': 'No companion selected'
            }), 400
        
        # Check and deduct credits for decoder (3 credits)
        from ...modules.credits.operations import get_artistic_time, deduct_artistic_time
        
        current_credits = get_artistic_time(user_id)
        decoder_cost = 3  # From constants.py
        
        if current_credits < decoder_cost:
            return jsonify({
                "success": False,
                "error": f"Insufficient Artistic Time credits for decoder",
                "credits_needed": decoder_cost,
                "current_credits": current_credits,
                "upgrade_required": True
            }), 402  # Payment Required
        
        # Deduct credits for decoder
        if not deduct_artistic_time(user_id, decoder_cost):
            return jsonify({
                "success": False,
                "error": "Failed to deduct credits for decoder"
            }), 500
        
        companion = get_companion_by_id(companion_id)
        remaining_credits = get_artistic_time(user_id)
        
        return jsonify({
            'success': True,
            'companion_id': companion_id,
            'companion_name': companion['name'] if companion else 'Unknown',
            'feature': 'decoder',
            'credits_charged': decoder_cost,
            'credits_remaining': remaining_credits,
            'message': f'Decoder ready! {decoder_cost} Artistic Time credits used.'
        })
        
    except Exception as e:
        logger.error(f"Companion decoder usage error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to use decoder'
        }), 500

# =============================================================================
# SOUL RIDDLE API ENDPOINTS
# =============================================================================

@api_bp.route('/soul-riddle/check-limit', methods=['GET'])
@requires_login
def check_soul_riddle_limit():
    """Check Soul Riddle usage limits"""
    try:
        from unified_tier_system import get_feature_limit, get_feature_usage_today
        
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Get limits and usage
        daily_limit = get_feature_limit(user_plan, 'soul_riddle', trial_active) 
        usage_today = get_feature_usage_today(user_id, 'soul_riddle')
        remaining = max(0, daily_limit - usage_today)
        unlimited = daily_limit >= 999999
        
        return jsonify({
            'success': True,
            'feature': 'soul_riddle',
            'daily_limit': daily_limit,
            'usage_today': usage_today,
            'remaining': remaining,
            'unlimited': unlimited,
            'user_plan': user_plan,
            'trial_active': trial_active
        })
        
    except Exception as e:
        logger.error(f"Soul Riddle limit check error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to check Soul Riddle limits'
        }), 500

@api_bp.route('/soul-riddle/use', methods=['POST'])
@requires_login
def use_soul_riddle():
    """Track Soul Riddle usage - Now uses Artistic Time credits"""
    from ...modules.credits.decorators import require_credits
    
    # Apply credit requirement
    @require_credits('soul_riddle')
    def _soul_riddle_logic():
        try:
            user_id = get_user_id()
            
            # Soul Riddle game started successfully - credits already deducted by decorator
            return jsonify({
                'success': True,
                'feature': 'soul_riddle',
                'message': 'Soul Riddle game started! 4 credits deducted.',
                'cost': 4
            })
            
        except Exception as e:
            logger.error(f"Soul Riddle completion error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to start Soul Riddle game'
            }), 500
    
    return _soul_riddle_logic()

@api_bp.route('/credits/balance', methods=['GET'])
@requires_login
def get_credit_balance():
    """Get user's current Artistic Time credit balance"""
    try:
        from ...modules.credits.operations import get_artistic_time
        
        user_id = get_user_id()
        balance = get_artistic_time(user_id)
        
        return jsonify({
            'success': True,
            'balance': balance,
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Error getting credit balance for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get credit balance',
            'balance': 0
        }), 500

@api_bp.route('/soul-riddle/stats', methods=['GET'])
@requires_login
def get_soul_riddle_stats():
    """Get Soul Riddle statistics"""
    try:
        user_id = get_user_id()
        
        # For now, return basic stats structure
        # In a real implementation, these would come from a database
        stats = {
            'total_played': 0,
            'total_correct': 0,
            'total_wrong': 0,
            'streak': 0,
            'best_streak': 0,
            'average_time': 0,
            'difficulty_stats': {
                'easy': {'played': 0, 'correct': 0, 'best_time': 0},
                'medium': {'played': 0, 'correct': 0, 'best_time': 0},
                'hard': {'played': 0, 'correct': 0, 'best_time': 0}
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Soul Riddle stats error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get Soul Riddle stats'
        }), 500

# Set up API blueprint middleware
@api_bp.before_request
def log_api_request():
    """Log API requests for monitoring"""
    try:
        if request.endpoint and request.endpoint.startswith('api.'):
            logger.debug(f"🔗 API Request: {request.method} {request.path} from {request.remote_addr}")
    except Exception as e:
        logger.error(f"Error logging API request: {e}")

@api_bp.after_request
def set_api_headers(response):
    """Set standard headers for API responses"""
    try:
        response.headers['Content-Type'] = 'application/json'
        response.headers['X-API-Version'] = '1.0'
        return response
    except Exception as e:
        logger.error(f"Error setting API headers: {e}")
        return response

def init_api_system(app):
    """Initialize consolidated API system"""
    logger.info("Consolidated API system initialized successfully")