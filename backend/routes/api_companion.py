"""
Production-Grade Companion API
Handles companion chat requests with routing, caching, and quota management
"""
import logging
from flask import Blueprint, request, jsonify, session
from companion_router import get_companion_router
from quota_limits import get_quota_status
from studio.cache import get_cache_stats, clear_cache
from billing.openai_budget import get_budget_status, get_budget_window_info
from billing.auto_quota import get_quota_for_plan, get_quota_recommendations
from billing.costing import get_spend_stats

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('api_companion', __name__)

def _filter_debug_fields(response):
    """
    Remove debug/admin fields from API response for regular users
    Keeps essential user-facing info but hides internal system details
    """
    if not isinstance(response, dict):
        return response
    
    # Fields to remove for non-admin users
    debug_fields = {
        # Router/system debug info
        "router_decision", "cache_hit", "quota_checked",
        "cost_tracked", "cost_breakdown", "cost_tracking_error",
        
        # Detailed quota/budget internals
        "quota_info", "auto_quota", "budget_window", "spend_stats",
        "enhancement_level", "fallback_recommended", "error_recovery",
        
        # Technical model details
        "model", "tokens_used", "prompt_tokens", "completion_tokens",
        "finish_reason", "response_time",
        
        # Internal routing notes
        "note", "limit", "used", "source_details", "provider_fallback"
    }
    
    # Create filtered response
    filtered = response.copy()
    
    # Remove debug fields
    for field in debug_fields:
        filtered.pop(field, None)
    
    # Keep essential user-facing info but simplify
    if "quota_after" in filtered:
        # Simplify quota info to just what users need
        quota = filtered["quota_after"]
        if isinstance(quota, dict):
            filtered["remaining_messages"] = max(0, quota.get("limit", 0) - quota.get("used", 0))
        filtered.pop("quota_after", None)
    
    # Add user-friendly provider indicator
    if response.get("router_decision") == "openai":
        filtered["powered_by"] = "Premium"
    elif response.get("router_decision") == "local":
        filtered["powered_by"] = "Standard"
    elif response.get("router_decision") == "cache":
        filtered["powered_by"] = "Instant"
    
    # Keep success, response, character - the essentials
    essential_fields = {"success", "response", "character", "user_context", "powered_by", "remaining_messages"}
    
    # For errors, also keep error info
    if not response.get("success", False):
        essential_fields.update({"error", "message"})
    
    # Only return essential fields
    final_response = {k: v for k, v in filtered.items() if k in essential_fields}
    
    return final_response

@bp.route('/api/companion/chat', methods=['POST'])
def companion_chat():
    """
    Main companion chat endpoint
    
    Expected JSON body:
    {
        "message": "User message",
        "character": "Blayzo" (optional),
        "context": "Previous conversation context" (optional),
        "force_provider": "openai" or "local" (optional),
        "quality_preference": "fast", "quality", or "auto" (optional)
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "missing_message",
                "message": "Message is required"
            }), 400
        
        message = data['message'].strip()
        if not message:
            return jsonify({
                "success": False,
                "error": "empty_message", 
                "message": "Message cannot be empty"
            }), 400
        
        # Extract parameters
        character = data.get('character', 'Blayzo')
        context = data.get('context', '')
        force_provider = data.get('force_provider')  # None, 'openai', or 'local'
        quality_preference = data.get('quality_preference', 'auto')  # 'fast', 'quality', 'auto'
        
        # Get user info from session (with fallback)
        user_id = session.get('user_id', 'anonymous')
        user_plan = session.get('user_plan', 'free')
        
        # Validate character
        valid_characters = ['Blayzo', 'Blayzica', 'Crimson', 'Violet']
        if character not in valid_characters:
            return jsonify({
                "success": False,
                "error": "invalid_character",
                "message": f"Character must be one of: {', '.join(valid_characters)}",
                "valid_characters": valid_characters
            }), 400
        
        # Validate force_provider
        if force_provider and force_provider not in ['openai', 'local']:
            return jsonify({
                "success": False,
                "error": "invalid_force_provider",
                "message": "force_provider must be 'openai' or 'local'"
            }), 400
        
        # Validate quality_preference  
        if quality_preference not in ['fast', 'quality', 'auto']:
            return jsonify({
                "success": False,
                "error": "invalid_quality_preference",
                "message": "quality_preference must be 'fast', 'quality', or 'auto'"
            }), 400
        
        # Get router and process request
        router = get_companion_router()
        
        response = router.route_request(
            message=message,
            character=character,
            context=context,
            user_id=user_id,
            user_plan=user_plan,
            force_provider=force_provider,
            quality_preference=quality_preference
        )
        
        # Add user context to response
        response['user_context'] = {
            'user_id': user_id,
            'user_plan': user_plan,
            'character': character
        }
        
        # Filter debug fields for non-admin users
        is_admin = bool(session.get("is_admin", False))
        if not is_admin:
            response = _filter_debug_fields(response)
        
        # Set appropriate HTTP status code
        if response.get('success', False):
            status_code = 200
        elif response.get('error') == 'quota_exceeded':
            status_code = 429  # Too Many Requests
        else:
            status_code = 500
        
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Companion chat API error: {e}")
        return jsonify({
            "success": False,
            "error": "internal_error",
            "message": "Internal server error occurred"
        }), 500

@bp.route('/api/companion/status', methods=['GET'])
def companion_status():
    """Get companion system status and configuration"""
    try:
        router = get_companion_router()
        
        # Get user info
        user_id = session.get('user_id', 'anonymous') 
        user_plan = session.get('user_plan', 'free')
        
        # Get comprehensive status
        router_status = router.get_router_status()
        quota_status = get_quota_status(user_id, user_plan)
        cache_stats = get_cache_stats()
        budget_status = get_budget_status()
        budget_window = get_budget_window_info()
        spend_stats = get_spend_stats()
        
        # Get plan-specific quota info
        plan_quota_info = get_quota_for_plan(user_plan)
        
        # Check if user is admin
        is_admin = bool(session.get("is_admin", False))
        
        response_data = {
            "success": True,
            "user": {
                "user_id": user_id,
                "user_plan": user_plan
            },
            "available_characters": ["Blayzo", "Blayzica", "Crimson", "Violet"],
            "quality_options": ["fast", "quality", "auto"]
        }
        
        # Add basic quota info for all users
        response_data["quota"] = {
            "daily_limit": quota_status.get("daily_limit", 0),
            "remaining": quota_status.get("remaining", 0),
            "over_limit": quota_status.get("over_limit", False)
        }
        
        # Add admin-only debug info
        if is_admin:
            response_data.update({
                "router": router_status,
                "full_quota": quota_status,
                "plan_quota": plan_quota_info,
                "cache": cache_stats,
                "budget": budget_status,
                "budget_window": budget_window,
                "spend_stats": spend_stats,
                "force_provider_options": ["openai", "local"]
            })
        else:
            # Add user-friendly provider status
            openai_available = router_status.get("providers", {}).get("openai", {}).get("available", False)
            if user_plan in ["vip", "max", "pro"]:
                response_data["provider_status"] = "Premium" if openai_available else "Standard"
            else:
                response_data["provider_status"] = "Standard"
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Status API error: {e}")
        return jsonify({
            "success": False,
            "error": "internal_error",
            "message": "Could not retrieve system status"
        }), 500

@bp.route('/api/companion/quota', methods=['GET'])
def companion_quota():
    """Get detailed quota information for the user"""
    try:
        user_id = session.get('user_id', 'anonymous')
        user_plan = session.get('user_plan', 'free')
        
        quota_status = get_quota_status(user_id, user_plan)
        plan_quota_info = get_quota_for_plan(user_plan)
        
        # Get quota recommendations for all plans (useful for upgrade prompts)
        quota_recommendations = get_quota_recommendations()
        
        return jsonify({
            "success": True,
            "quota": quota_status,
            "plan_quota": plan_quota_info,
            "all_plan_quotas": quota_recommendations["by_plan"],
            "auto_quota_info": quota_recommendations["auto_quota_info"],
            "budget_window": quota_recommendations["budget_window"]
        })
        
    except Exception as e:
        logger.error(f"Quota API error: {e}")
        return jsonify({
            "success": False,
            "error": "internal_error",
            "message": "Could not retrieve quota information"
        }), 500

@bp.route('/api/companion/recommendation', methods=['GET'])
def companion_recommendation():
    """Get routing recommendation for the current user"""
    try:
        user_id = session.get('user_id', 'anonymous')
        user_plan = session.get('user_plan', 'free')
        
        router = get_companion_router()
        recommendation = router.get_routing_recommendation(user_plan, user_id)
        
        return jsonify({
            "success": True,
            "recommendation": recommendation
        })
        
    except Exception as e:
        logger.error(f"Recommendation API error: {e}")
        return jsonify({
            "success": False,
            "error": "internal_error",
            "message": "Could not generate recommendation"
        }), 500

# Admin endpoints - require admin session
def _require_admin():
    """Check if user is admin, return error response if not"""
    if not bool(session.get("is_admin", False)):
        return jsonify({
            "success": False,
            "error": "access_denied",
            "message": "Admin access required"
        }), 403
    return None

@bp.route('/api/companion/admin/debug', methods=['GET'])
def admin_debug_panel():
    """Get full debug information (admin only)"""
    admin_check = _require_admin()
    if admin_check:
        return admin_check
    
    try:
        router = get_companion_router()
        
        # Get user info
        user_id = session.get('user_id', 'admin_user')
        user_plan = session.get('user_plan', 'max')
        
        # Get ALL the debug info
        router_status = router.get_router_status()
        quota_status = get_quota_status(user_id, user_plan)
        cache_stats = get_cache_stats()
        budget_status = get_budget_status()
        budget_window = get_budget_window_info()
        spend_stats = get_spend_stats()
        plan_quota_info = get_quota_for_plan(user_plan)
        quota_recommendations = get_quota_recommendations()
        
        return jsonify({
            "success": True,
            "debug_panel": {
                "user": {
                    "user_id": user_id,
                    "user_plan": user_plan,
                    "is_admin": True
                },
                "router": router_status,
                "quota": quota_status,
                "plan_quota": plan_quota_info,
                "quota_recommendations": quota_recommendations,
                "cache": cache_stats,
                "budget": budget_status,
                "budget_window": budget_window,
                "spend_stats": spend_stats,
                "alerts": {
                    "budget_low": not budget_status.get("safe", True),
                    "approaching_spend_limit": spend_stats.get("approaching_limit", False),
                    "over_budget": spend_stats.get("over_budget", False)
                },
                "system_health": {
                    "redis_available": cache_stats.get("available", False),
                    "openai_available": router_status.get("providers", {}).get("openai", {}).get("available", False),
                    "local_ai_available": router_status.get("providers", {}).get("local", {}).get("available", False)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Admin debug panel error: {e}")
        return jsonify({
            "success": False,
            "error": "internal_error",
            "message": "Could not retrieve debug information"
        }), 500

@bp.route('/api/companion/admin/cache/clear', methods=['POST'])
def admin_clear_cache():
    """Clear old cache entries (admin only)"""
    admin_check = _require_admin()
    if admin_check:
        return admin_check
        
    try:
        max_age_days = request.json.get('max_age_days', 7) if request.json else 7
        
        cleared = clear_cache(max_age_days)
        
        return jsonify({
            "success": True,
            "message": f"Cleared {cleared} cache entries older than {max_age_days} days",
            "entries_cleared": cleared
        })
        
    except Exception as e:
        logger.error(f"Cache clear API error: {e}")
        return jsonify({
            "success": False,
            "error": "internal_error",
            "message": "Could not clear cache"
        }), 500

@bp.route('/api/companion/admin/stats', methods=['GET'])
def admin_stats():
    """Get comprehensive system statistics (admin only)"""
    admin_check = _require_admin()
    if admin_check:
        return admin_check
        
    try:
        router = get_companion_router()
        
        # Get all available stats
        router_status = router.get_router_status()
        cache_stats = get_cache_stats()
        budget_status = get_budget_status()
        budget_window = get_budget_window_info()
        spend_stats = get_spend_stats()
        
        # Get quota recommendations for monitoring
        quota_recommendations = get_quota_recommendations()
        
        # Could add more detailed stats here:
        # - Request volume by plan type
        # - Cache hit ratios
        # - Error rates
        # - Response times
        
        return jsonify({
            "success": True,
            "stats": {
                "router": router_status,
                "cache": cache_stats,
                "budget": budget_status,
                "budget_window": budget_window,
                "spend_stats": spend_stats,
                "quota_system": quota_recommendations,
                "system": {
                    "available_characters": ["Blayzo", "Blayzica", "Crimson", "Violet"],
                    "supported_plans": ["free", "growth", "pro", "vip", "max"],
                    "api_version": "2.0",
                    "features": ["auto_quota", "cost_tracking", "budget_protection", "redis_caching"]
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Admin stats API error: {e}")
        return jsonify({
            "success": False,
            "error": "internal_error",
            "message": "Could not retrieve admin stats"
        }), 500

@bp.route('/api/companion/admin/budget', methods=['GET'])
def admin_budget():
    """Get detailed budget and spending information (admin only)"""
    admin_check = _require_admin()
    if admin_check:
        return admin_check
        
    try:
        budget_status = get_budget_status()
        budget_window = get_budget_window_info()
        spend_stats = get_spend_stats()
        
        # Get quota info for monitoring
        quota_recommendations = get_quota_recommendations()
        
        return jsonify({
            "success": True,
            "budget": {
                "status": budget_status,
                "window": budget_window,
                "spend": spend_stats,
                "quota_system": quota_recommendations,
                "alerts": {
                    "approaching_limit": spend_stats.get("approaching_limit", False),
                    "over_budget": spend_stats.get("over_budget", False),
                    "budget_safe": budget_status.get("safe", False)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Admin budget API error: {e}")
        return jsonify({
            "success": False,
            "error": "internal_error",
            "message": "Could not retrieve budget information"
        }), 500

# Health check endpoint
@bp.route('/api/companion/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    try:
        router = get_companion_router()
        
        # Basic health checks
        local_available = router.local_client.is_available()
        openai_available = router.openai_client.is_available()
        
        return jsonify({
            "success": True,
            "health": "ok",
            "providers": {
                "local_ai": local_available,
                "openai": openai_available
            },
            "timestamp": router.local_client.simple_ai.request_count  # Use as simple counter
        })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "success": False,
            "health": "error",
            "error": str(e)
        }), 500

if __name__ == "__main__":
    # Test the API endpoints (for development)
    from flask import Flask
    
    app = Flask(__name__)
    app.secret_key = "test_secret_key_for_development"
    app.register_blueprint(bp)
    
    print("Testing Companion API...")
    
    with app.test_client() as client:
        # Test health check
        print("Testing health check...")
        response = client.get('/api/companion/health')
        print(f"Health: {response.status_code} - {response.get_json()}")
        
        # Test status
        print("\nTesting status...")
        response = client.get('/api/companion/status')
        print(f"Status: {response.status_code} - {response.get_json()}")
        
        # Test chat (should fail without message)
        print("\nTesting chat without message...")
        response = client.post('/api/companion/chat', json={})
        print(f"Chat (no message): {response.status_code} - {response.get_json()}")
        
        # Test chat with message
        print("\nTesting chat with message...")
        response = client.post('/api/companion/chat', json={
            "message": "Hello, I need some support today",
            "character": "Blayzo"
        })
        print(f"Chat (with message): {response.status_code}")
        if response.get_json():
            result = response.get_json()
            print(f"Success: {result.get('success', False)}")
            if result.get('success', False):
                print(f"Response: {result.get('response', 'No response')[:100]}...")
            else:
                print(f"Error: {result.get('error', 'No error info')}")
    
    print("\nAPI testing completed!")