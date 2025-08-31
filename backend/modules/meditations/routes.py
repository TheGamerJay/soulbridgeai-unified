"""
SoulBridge AI - Meditations Routes
Flask Blueprint for all meditation-related endpoints
Extracted from backend/app.py
"""
import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify, session, redirect
from database_utils import get_database
from .meditation_service import MeditationService
from .session_tracker import SessionTracker
from .meditation_generator import MeditationGenerator

logger = logging.getLogger(__name__)

# Create Blueprint
meditations_bp = Blueprint('meditations', __name__)

# Initialize services (will be set by the main app)
meditation_service = None
session_tracker = None
meditation_generator = None

def init_meditation_services(database=None, openai_client=None):
    """Initialize meditation services with dependencies"""
    global meditation_service, session_tracker, meditation_generator
    
    try:
        session_tracker = SessionTracker(database)
        meditation_generator = MeditationGenerator(openai_client)
        meditation_service = MeditationService(database, session_tracker, meditation_generator)
        
        # Ensure database schema exists
        if database and session_tracker:
            session_tracker.ensure_database_schema()
        
        logger.info("🧘 Meditation services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize meditation services: {e}")
        return False

def is_logged_in():
    """Check if user is logged in"""
    return session.get('logged_in', False) and session.get('user_id') is not None

def check_and_deduct_credits(user_id: int, feature: str = 'meditations') -> dict:
    """Check and deduct credits for meditation features"""
    try:
        # Import credits functionality
        from ..credits import get_artistic_time, deduct_artistic_time, get_feature_cost
        
        cost = get_feature_cost(feature)
        current_credits = get_artistic_time(user_id)
        
        if current_credits < cost:
            return {
                "success": False,
                "error": f"Insufficient credits. Need {cost} credits, you have {current_credits}.",
                "required": cost,
                "available": current_credits
            }
        
        # Deduct credits
        if not deduct_artistic_time(user_id, cost):
            return {
                "success": False,
                "error": "Failed to deduct credits. Please try again."
            }
        
        logger.info(f"💳 Deducted {cost} credits from user {user_id} for {feature}")
        return {"success": True, "cost": cost}
        
    except ImportError:
        # Fallback if credits module not available
        logger.warning("Credits module not available - allowing meditation access")
        return {"success": True, "cost": 0}
    except Exception as e:
        logger.error(f"Error in credit check/deduction: {e}")
        return {
            "success": False,
            "error": "Credit system temporarily unavailable"
        }

def refund_credits(user_id: int, feature: str = 'meditations', reason: str = '') -> bool:
    """Refund credits if meditation fails"""
    try:
        from ..credits import refund_artistic_time, get_feature_cost
        
        cost = get_feature_cost(feature)
        if refund_artistic_time(user_id, cost, reason):
            logger.info(f"💰 Refunded {cost} credits to user {user_id}: {reason}")
            return True
        else:
            logger.error(f"❌ Failed to refund {cost} credits to user {user_id}")
            return False
            
    except ImportError:
        logger.warning("Credits module not available for refund")
        return True
    except Exception as e:
        logger.error(f"Error in credit refund: {e}")
        return False

# =============================================================================
# MEDITATION PAGES
# =============================================================================

@meditations_bp.route("/emotional-meditations")
def emotional_meditations_page():
    """Emotional meditations main page"""
    try:
        if not is_logged_in():
            return redirect("/login")
        
        if not meditation_service:
            logger.error("Meditation service not initialized")
            return redirect("/subscription?feature=emotional-meditations")
        
        # Check if user has meditation access
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        user_addons = session.get('user_addons', [])
        
        access_result = meditation_service.check_meditation_access(user_plan, trial_active, user_addons)
        
        if not access_result['has_access']:
            return redirect("/subscription?feature=emotional-meditations")
        
        return render_template("emotional_meditations.html")
        
    except Exception as e:
        logger.error(f"Emotional meditations page error: {e}")
        return redirect("/")

# =============================================================================
# MEDITATION API ENDPOINTS
# =============================================================================

@meditations_bp.route("/api/emotional-meditations/categories")
def get_meditation_categories():
    """Get available meditation categories"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not meditation_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        # Check meditation access
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        user_addons = session.get('user_addons', [])
        
        access_result = meditation_service.check_meditation_access(user_plan, trial_active, user_addons)
        
        if not access_result['has_access']:
            return jsonify({
                "success": False, 
                "error": access_result['reason']
            }), 403
        
        # Get available meditations
        meditations_result = meditation_service.get_available_meditations(user_plan)
        
        if not meditations_result['success']:
            return jsonify({"success": False, "error": meditations_result['error']}), 500
        
        return jsonify({
            "success": True,
            "categories": meditations_result['categories'],
            "total_categories": meditations_result['total_categories'],
            "total_sessions": meditations_result['total_sessions']
        })
        
    except Exception as e:
        logger.error(f"Error getting meditation categories: {e}")
        return jsonify({"success": False, "error": "Failed to load meditation categories"}), 500

@meditations_bp.route("/api/emotional-meditations/start", methods=["POST"])
def start_meditation():
    """Start a new meditation session"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not meditation_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
        
        meditation_id = data.get('meditation_id')
        duration = data.get('duration', 'medium')
        
        if not meditation_id:
            return jsonify({"success": False, "error": "Meditation ID required"}), 400
        
        # Check meditation access
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        user_addons = session.get('user_addons', [])
        
        access_result = meditation_service.check_meditation_access(user_plan, trial_active, user_addons)
        
        if not access_result['has_access']:
            return jsonify({
                "success": False, 
                "error": access_result['reason']
            }), 403
        
        # Start meditation session
        user_id = session.get('user_id')
        session_result = meditation_service.start_meditation_session(user_id, meditation_id, duration)
        
        if not session_result['success']:
            return jsonify({"success": False, "error": session_result['error']}), 400
        
        return jsonify({
            "success": True,
            "session": session_result['session'],
            "message": "Meditation session started"
        })
        
    except Exception as e:
        logger.error(f"Error starting meditation: {e}")
        return jsonify({"success": False, "error": "Failed to start meditation"}), 500

@meditations_bp.route("/api/emotional-meditations/save-session", methods=["POST"])
def save_meditation_session():
    """Save completed meditation session"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not meditation_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        # Check meditation access
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        user_addons = session.get('user_addons', [])
        
        access_result = meditation_service.check_meditation_access(user_plan, trial_active, user_addons)
        
        if not access_result['has_access']:
            return jsonify({
                "success": False, 
                "error": access_result['reason']
            }), 403
        
        # Check and deduct credits before processing
        user_id = session.get('user_id')
        credit_result = check_and_deduct_credits(user_id, 'meditations')
        
        if not credit_result['success']:
            return jsonify({
                "success": False,
                "error": credit_result['error']
            }), 403
        
        data = request.get_json()
        if not data:
            # Refund credits if no data provided
            refund_credits(user_id, 'meditations', 'No session data provided')
            return jsonify({"success": False, "error": "No session data provided"}), 400
        
        # Complete meditation session
        complete_result = meditation_service.complete_meditation_session(user_id, data)
        
        if not complete_result['success']:
            # Refund credits if session completion failed
            refund_credits(user_id, 'meditations', 'Session completion failed')
            return jsonify({
                "success": False, 
                "error": complete_result['error']
            }), 500
        
        logger.info(f"🧘✅ Meditation session completed for user {user_id}: {data.get('title', 'Unknown')}")
        
        return jsonify({
            "success": True,
            "message": "Meditation session saved successfully",
            "session": complete_result['session']
        })
        
    except Exception as e:
        logger.error(f"Meditation session save error: {e}")
        
        # Refund credits since meditation save failed
        user_id = session.get('user_id')
        if user_id:
            refund_credits(user_id, 'meditations', 'Meditation session save failed')
        
        return jsonify({
            "success": False, 
            "error": "Failed to save session. Your credits have been refunded."
        }), 500

@meditations_bp.route("/api/emotional-meditations/stats", methods=["GET"])
def get_meditation_stats():
    """Get user's meditation statistics"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not meditation_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        # Check meditation access
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        user_addons = session.get('user_addons', [])
        
        access_result = meditation_service.check_meditation_access(user_plan, trial_active, user_addons)
        
        if not access_result['has_access']:
            return jsonify({
                "success": False, 
                "error": access_result['reason']
            }), 403
        
        # Get user statistics
        user_id = session.get('user_id')
        stats_result = meditation_service.get_user_meditation_stats(user_id)
        
        if not stats_result['success']:
            return jsonify({"success": False, "error": stats_result['error']}), 500
        
        return jsonify({
            "success": True,
            "stats": stats_result['stats'],
            "achievements": stats_result.get('achievements', []),
            "next_goals": stats_result.get('next_goals', [])
        })
        
    except Exception as e:
        logger.error(f"Meditation stats error: {e}")
        return jsonify({"success": False, "error": "Failed to fetch stats"}), 500

@meditations_bp.route("/api/emotional-meditations/recommendations")
def get_meditation_recommendations():
    """Get personalized meditation recommendations"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not meditation_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        # Check meditation access
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        user_addons = session.get('user_addons', [])
        
        access_result = meditation_service.check_meditation_access(user_plan, trial_active, user_addons)
        
        if not access_result['has_access']:
            return jsonify({
                "success": False, 
                "error": access_result['reason']
            }), 403
        
        # Get recommendations
        user_id = session.get('user_id')
        context = request.args.get('context', '')
        
        recs_result = meditation_service.get_meditation_recommendations(user_id, context)
        
        if not recs_result['success']:
            return jsonify({"success": False, "error": recs_result['error']}), 500
        
        return jsonify({
            "success": True,
            "recommendations": recs_result['recommendations'],
            "personalized": recs_result.get('personalized', False),
            "context": recs_result.get('context', '')
        })
        
    except Exception as e:
        logger.error(f"Error getting meditation recommendations: {e}")
        return jsonify({"success": False, "error": "Failed to get recommendations"}), 500

@meditations_bp.route("/api/emotional-meditations/content/<meditation_id>")
def get_meditation_content(meditation_id):
    """Get meditation script/content for a specific meditation"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not meditation_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        # Check meditation access
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        user_addons = session.get('user_addons', [])
        
        access_result = meditation_service.check_meditation_access(user_plan, trial_active, user_addons)
        
        if not access_result['has_access']:
            return jsonify({
                "success": False, 
                "error": access_result['reason']
            }), 403
        
        # Get meditation content
        user_id = session.get('user_id')
        content_result = meditation_service.get_meditation_content(meditation_id, user_id)
        
        if not content_result['success']:
            return jsonify({"success": False, "error": content_result['error']}), 404
        
        return jsonify({
            "success": True,
            "meditation": content_result['meditation']
        })
        
    except Exception as e:
        logger.error(f"Error getting meditation content for {meditation_id}: {e}")
        return jsonify({"success": False, "error": "Failed to load meditation content"}), 500

@meditations_bp.route("/api/emotional-meditations/history")
def get_meditation_history():
    """Get user's meditation session history"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not session_tracker:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        # Check meditation access
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        user_addons = session.get('user_addons', [])
        
        if not meditation_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        access_result = meditation_service.check_meditation_access(user_plan, trial_active, user_addons)
        
        if not access_result['has_access']:
            return jsonify({
                "success": False, 
                "error": access_result['reason']
            }), 403
        
        # Get session history
        user_id = session.get('user_id')
        limit = int(request.args.get('limit', 20))
        
        history_result = session_tracker.get_user_sessions(user_id, limit)
        
        if not history_result['success']:
            return jsonify({"success": False, "error": history_result['error']}), 500
        
        return jsonify({
            "success": True,
            "sessions": history_result['sessions'],
            "total_count": history_result['total_count']
        })
        
    except Exception as e:
        logger.error(f"Error getting meditation history: {e}")
        return jsonify({"success": False, "error": "Failed to load meditation history"}), 500

@meditations_bp.route("/api/emotional-meditations/rate-session", methods=["POST"])
def rate_meditation_session():
    """Rate a completed meditation session"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not session_tracker:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
        
        session_id = data.get('session_id')
        rating = data.get('rating')
        notes = data.get('notes', '')
        
        if not session_id or not rating:
            return jsonify({"success": False, "error": "Session ID and rating required"}), 400
        
        # Update session rating
        user_id = session.get('user_id')
        rating_result = session_tracker.update_session_rating(session_id, user_id, rating, notes)
        
        if not rating_result['success']:
            return jsonify({"success": False, "error": rating_result['error']}), 400
        
        return jsonify({
            "success": True,
            "message": "Session rating updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error rating meditation session: {e}")
        return jsonify({"success": False, "error": "Failed to save rating"}), 500

# =============================================================================
# MEDITATION ANALYTICS ENDPOINTS
# =============================================================================

@meditations_bp.route("/api/emotional-meditations/analytics/categories")
def get_category_analytics():
    """Get meditation analytics by category"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not session_tracker:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        # Check meditation access
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        user_addons = session.get('user_addons', [])
        
        if not meditation_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        access_result = meditation_service.check_meditation_access(user_plan, trial_active, user_addons)
        
        if not access_result['has_access']:
            return jsonify({
                "success": False, 
                "error": access_result['reason']
            }), 403
        
        # Get category statistics
        user_id = session.get('user_id')
        category_result = session_tracker.get_category_stats(user_id)
        
        if not category_result['success']:
            return jsonify({"success": False, "error": category_result['error']}), 500
        
        return jsonify({
            "success": True,
            "categories": category_result['categories']
        })
        
    except Exception as e:
        logger.error(f"Error getting category analytics: {e}")
        return jsonify({"success": False, "error": "Failed to load category analytics"}), 500

@meditations_bp.route("/api/emotional-meditations/analytics/timeline")
def get_meditation_timeline():
    """Get meditation timeline analytics"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not session_tracker:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        # Check meditation access
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        user_addons = session.get('user_addons', [])
        
        if not meditation_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        access_result = meditation_service.check_meditation_access(user_plan, trial_active, user_addons)
        
        if not access_result['has_access']:
            return jsonify({
                "success": False, 
                "error": access_result['reason']
            }), 403
        
        # Get timeline data
        user_id = session.get('user_id')
        days = int(request.args.get('days', 30))
        
        timeline_result = session_tracker.get_meditation_history(user_id, days)
        
        if not timeline_result['success']:
            return jsonify({"success": False, "error": timeline_result['error']}), 500
        
        return jsonify({
            "success": True,
            "timeline": timeline_result['history'],
            "days_with_sessions": timeline_result['days_with_sessions'],
            "total_days": timeline_result['total_days']
        })
        
    except Exception as e:
        logger.error(f"Error getting meditation timeline: {e}")
        return jsonify({"success": False, "error": "Failed to load meditation timeline"}), 500

# =============================================================================
# AI MEDITATION GENERATION ENDPOINTS
# =============================================================================

@meditations_bp.route("/api/emotional-meditations/generate-custom", methods=["POST"])
def generate_custom_meditation():
    """Generate a custom meditation based on user input"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not meditation_generator:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        # Check meditation access
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        user_addons = session.get('user_addons', [])
        
        if not meditation_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        access_result = meditation_service.check_meditation_access(user_plan, trial_active, user_addons)
        
        if not access_result['has_access']:
            return jsonify({
                "success": False, 
                "error": access_result['reason']
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
        
        # Check and deduct credits for custom generation (higher cost)
        user_id = session.get('user_id')
        credit_result = check_and_deduct_credits(user_id, 'meditations')  # Same cost for now
        
        if not credit_result['success']:
            return jsonify({
                "success": False,
                "error": credit_result['error']
            }), 403
        
        # Generate custom meditation
        meditation_theme = data.get('theme', 'stress')
        duration = int(data.get('duration', 10))
        
        # Create custom meditation ID
        custom_id = f"custom-{meditation_theme}-{int(datetime.now().timestamp())}"
        
        generation_result = meditation_generator.generate_meditation_script(
            custom_id, user_id, duration
        )
        
        if not generation_result['success']:
            # Refund credits if generation failed
            refund_credits(user_id, 'meditations', 'Custom meditation generation failed')
            return jsonify({
                "success": False, 
                "error": generation_result['error']
            }), 500
        
        logger.info(f"🤖 Generated custom meditation for user {user_id}: {meditation_theme}")
        
        return jsonify({
            "success": True,
            "meditation": generation_result['script'],
            "generation_method": generation_result.get('generation_method', 'unknown')
        })
        
    except Exception as e:
        logger.error(f"Error generating custom meditation: {e}")
        
        # Refund credits since generation failed
        user_id = session.get('user_id')
        if user_id:
            refund_credits(user_id, 'meditations', 'Custom meditation generation error')
        
        return jsonify({"success": False, "error": "Failed to generate custom meditation"}), 500

@meditations_bp.route("/api/emotional-meditations/variations/<meditation_id>")
def get_meditation_variations(meditation_id):
    """Get variations of a specific meditation"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not meditation_generator:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        # Check meditation access
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        user_addons = session.get('user_addons', [])
        
        if not meditation_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        access_result = meditation_service.check_meditation_access(user_plan, trial_active, user_addons)
        
        if not access_result['has_access']:
            return jsonify({
                "success": False, 
                "error": access_result['reason']
            }), 403
        
        # Generate variations
        count = int(request.args.get('count', 3))
        variations_result = meditation_generator.generate_meditation_variations(meditation_id, count)
        
        if not variations_result['success']:
            return jsonify({"success": False, "error": variations_result['error']}), 500
        
        return jsonify({
            "success": True,
            "variations": variations_result['variations'],
            "base_meditation": variations_result['base_meditation']
        })
        
    except Exception as e:
        logger.error(f"Error getting meditation variations: {e}")
        return jsonify({"success": False, "error": "Failed to generate variations"}), 500

# =============================================================================
# BLUEPRINT REGISTRATION HELPER
# =============================================================================

def register_meditation_routes(app, database=None, openai_client=None):
    """Register meditation routes with the Flask app"""
    try:
        # Initialize services
        if not init_meditation_services(database, openai_client):
            logger.error("Failed to initialize meditation services")
            return False
        
        # Register blueprint
        app.register_blueprint(meditations_bp)
        
        logger.info("🧘 Meditation routes registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to register meditation routes: {e}")
        return False