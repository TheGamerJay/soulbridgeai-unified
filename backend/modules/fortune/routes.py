"""
SoulBridge AI - Enhanced Fortune Routes
Deterministic tarot readings with multiple spreads
"""
import logging
from flask import Blueprint, request, jsonify, session, render_template, redirect
from ..auth.session_manager import requires_login
from ..creative.usage_tracker import CreativeUsageTracker
from ..creative.features_config import get_feature_limit
from .fortune_service import FortuneService

logger = logging.getLogger(__name__)

# Create blueprint - Note: No url_prefix so we can handle both page and API routes
fortune_bp = Blueprint('fortune', __name__)

# Initialize services
fortune_service = FortuneService()
usage_tracker = CreativeUsageTracker()

@fortune_bp.route('/fortune')
@requires_login
def fortune_page():
    """Main fortune page - Enhanced Tarot tool with multiple spreads"""
    # Check if user has ad-free subscription
    user_id = session.get('user_id')
    ad_free = False
    if user_id:
        try:
            from ..user_profile.profile_service import ProfileService
            profile_service = ProfileService()
            user_profile_result = profile_service.get_user_profile(user_id)
            user_profile = user_profile_result.get('user') if user_profile_result.get('success') else None
            ad_free = user_profile.get('ad_free', False) if user_profile else False
        except Exception as e:
            logger.error(f"Error checking ad-free status: {e}")
            ad_free = False
    
    return render_template('fortune.html', 
                         ad_free=ad_free,
                         user_session=session)

@fortune_bp.route('/api/fortune/spreads', methods=['GET'])
def get_spreads():
    """Get available tarot spreads"""
    try:
        spreads = fortune_service.get_available_spreads()
        return jsonify({"success": True, "spreads": spreads}), 200
    except Exception as e:
        logger.error(f"Error getting spreads: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@fortune_bp.route('/api/fortune/reading', methods=['POST'])
def generate_reading():
    """Generate deterministic tarot reading"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        user_id = session.get('user_id')
        
        # Check usage limits only if user is logged in
        if user_id:
            from ..user_profile.profile_service import ProfileService
            profile_service = ProfileService()
            user_profile_result = profile_service.get_user_profile(user_id)
            user_profile = user_profile_result.get('user') if user_profile_result.get('success') else None
            user_plan = user_profile.get('plan', 'bronze') if user_profile else 'bronze'
            trial_active = user_profile.get('trial_active', False) if user_profile else False
            
            if not usage_tracker.can_use_feature(user_id, 'fortune', user_plan, trial_active):
                limit = get_feature_limit('fortune', user_plan, trial_active)
                return jsonify({
                    "success": False, 
                    "error": f"Daily fortune limit reached ({limit} uses). Upgrade for more readings."
                }), 429
        else:
            # Default for logged out users
            user_plan = 'bronze'
            trial_active = False

        # Get parameters
        question = data.get('question', '').strip()
        spread_type = data.get('spread_type', 'three')
        reversals = data.get('reversals', True)
        clarifiers = data.get('clarifiers', 0)
        include_interpretation = data.get('interpretation', True)
        
        # Validate tier access for spreads
        spread_tier_requirements = {
            'celtic': 'silver',  # Celtic Cross requires Silver+
            'grand': 'gold'      # 21-card Grand requires Gold
        }
        
        if spread_type in spread_tier_requirements:
            required_tier = spread_tier_requirements[spread_type]
            tier_order = {'bronze': 0, 'silver': 1, 'gold': 2}
            
            if tier_order.get(user_plan, 0) < tier_order.get(required_tier, 0):
                return jsonify({
                    "success": False, 
                    "error": f"The {spread_type.title()} spread requires {required_tier.title()} tier or higher. Upgrade to access this premium spread."
                }), 403
        
        # Generate reading
        result = fortune_service.generate_fortune(
            question=question,
            user_id=user_id or 0,  # Use 0 for logged out users
            spread_type=spread_type
        )
        
        if result.get('success', False):
            # Record usage only if user is logged in
            if user_id:
                usage_tracker.record_usage(user_id, 'fortune')
                
                # Track cost (minimal for deterministic readings)
                try:
                    from ...billing.costing import track_horoscope_cost
                    track_horoscope_cost(user_id, 'fortune', result)
                except Exception as cost_error:
                    logger.warning(f"Cost tracking failed: {cost_error}")
            
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error generating fortune reading: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@fortune_bp.route('/api/fortune/interpret', methods=['POST'])
@requires_login
def interpret_reading():
    """Generate interpretation for an existing reading"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No reading data provided"}), 400
            
        if not data.get('cards'):
            return jsonify({"success": False, "error": "No cards found in reading data"}), 400
        
        interpretation = fortune_service.generate_interpretation(data)
        
        return jsonify({
            "success": True,
            "interpretation": interpretation
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating interpretation: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@fortune_bp.route('/api/fortune/limits', methods=['GET'])
def get_limits():
    """Get user's fortune usage limits"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                "success": True,
                "daily_limit": 5,
                "usage_today": 0,
                "remaining": 5,
                "unlimited": False,
                "message": "Login to track your usage"
            }), 200
            
        try:
            from ..user_profile.profile_service import ProfileService
            profile_service = ProfileService()
            user_profile_result = profile_service.get_user_profile(user_id)
            user_profile = user_profile_result.get('user') if user_profile_result.get('success') else None
            user_plan = user_profile.get('plan', 'bronze') if user_profile else 'bronze'
            trial_active = user_profile.get('trial_active', False) if user_profile else False
        except Exception:
            # Fallback to default values if profile service fails
            user_plan = 'bronze'
            trial_active = False
        
        limit = get_feature_limit('fortune', user_plan, trial_active)
        usage_today = usage_tracker.get_usage_today(user_id, 'fortune')
        
        return jsonify({
            "success": True,
            "daily_limit": limit,
            "usage_today": usage_today,
            "remaining": max(0, limit - usage_today) if limit < 999 else 999,
            "unlimited": limit >= 999,
            "user_tier": user_plan
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting limits: {e}")
        return jsonify({"success": False, "error": str(e)}), 500