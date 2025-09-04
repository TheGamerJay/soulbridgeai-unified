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

logger = logging.getLogger(__name__)

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
@requires_login
def user_status():
    """Get current user status"""
    try:
        status = session_api.get_user_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error in user status endpoint: {e}")
        return jsonify({
            "authenticated": False,
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
        from unified_tier_system import get_feature_limit, get_usage_count
        
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        
        # Get limits and usage
        daily_limit = get_feature_limit(user_plan, 'horoscope') 
        usage_today = get_usage_count(user_id, 'horoscope')
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
    """Get user entitlements and trial status - v1 compatibility endpoint"""
    try:
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        trial_expires_at = session.get('trial_expires_at')
        
        return jsonify({
            "logged_in": True,
            "user_id": user_id,
            "user_plan": user_plan,
            "tier": user_plan,
            "trial_active": trial_active,
            "trial_expires_at": trial_expires_at,
            "entitlements": {
                "decoder": {"enabled": True, "limit": "feature" if user_plan == "gold" else "limited"},
                "fortune": {"enabled": True, "limit": "feature" if user_plan == "gold" else "limited"},
                "horoscope": {"enabled": True, "limit": "feature" if user_plan == "gold" else "limited"},
                "creative_writer": {"enabled": True, "limit": "feature" if user_plan == "gold" else "limited"},
                "ai_images": {"enabled": user_plan in ["silver", "gold"], "limit": "credit"},
                "voice_chat": {"enabled": user_plan == "gold", "limit": "credit"},
                "mini_studio": {"enabled": user_plan == "gold", "limit": "credit"}
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting v1 entitlements: {e}")
        return jsonify({
            "logged_in": False,
            "error": "Failed to get entitlements"
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