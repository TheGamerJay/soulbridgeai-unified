"""
SoulBridge AI - Core Routes
Core application routes (home, navigation, basic pages)
Extracted from monolith app.py with improvements
"""
import logging
from flask import Blueprint, request, session, redirect, render_template

from ..auth.session_manager import requires_login, get_user_id
from .navigation_service import NavigationService
from .page_renderer import PageRenderer

logger = logging.getLogger(__name__)

# Create core routes blueprint
core_bp = Blueprint('core', __name__)

# Initialize core services
navigation_service = NavigationService()
page_renderer = PageRenderer()

@core_bp.route('/', methods=['GET', 'POST'])
def home():
    """Home route - smart redirect based on authentication status"""
    try:
        redirect_url = navigation_service.determine_home_redirect()
        
        # Set return URL if user needs to login
        if redirect_url == "/login" and request.path != "/":
            navigation_service.set_return_url("/intro")
        
        return redirect(redirect_url)
        
    except Exception as e:
        logger.error(f"Home route error: {e}")
        return redirect("/login")

@core_bp.route('/intro')
def intro_page():
    """Welcome/intro page for authenticated users"""
    try:
        # Check route access
        access_check = navigation_service.check_route_access('/intro')
        if not access_check["allowed"]:
            if access_check.get("redirect"):
                return redirect(access_check["redirect"])
            else:
                return page_renderer.render_error_page("Access denied", 403)
        
        # Render intro page
        return page_renderer.render_intro_page()
        
    except Exception as e:
        logger.error(f"Error rendering intro page: {e}")
        return page_renderer.render_error_page("Failed to load welcome page")

@core_bp.route('/login')
def login_page():
    """Login page - always show login form"""
    try:
        # Always show login page, don't redirect if already logged in
        # This prevents redirect loops and ensures users can always access login
        error_message = request.args.get('error')
        return_to = request.args.get('return_to')
        
        return page_renderer.render_login_page(error_message, return_to)
        
    except Exception as e:
        logger.error(f"Error rendering login page: {e}")
        return page_renderer.render_error_page("Login system temporarily unavailable")

@core_bp.route('/register')
def register_page():
    """Registration page"""
    try:
        # If already logged in, redirect to home
        if navigation_service._is_logged_in():
            return redirect("/")
        
        error_message = request.args.get('error')
        return page_renderer.render_register_page(error_message)
        
    except Exception as e:
        logger.error(f"Error rendering register page: {e}")
        return page_renderer.render_error_page("Failed to load registration page")

@core_bp.route('/terms-acceptance')
@requires_login  
def terms_acceptance_page():
    """Terms acceptance page for new users"""
    try:
        # Check if terms already accepted
        if navigation_service._has_accepted_terms():
            return redirect("/intro")
        
        return page_renderer.render_terms_acceptance_page()
        
    except Exception as e:
        logger.error(f"Error rendering terms page: {e}")
        return page_renderer.render_error_page("Failed to load terms page")

@core_bp.route('/subscription')
@requires_login
def subscription_page():
    """Subscription/upgrade page"""
    try:
        feature = request.args.get('feature')
        return page_renderer.render_subscription_page(feature)
        
    except Exception as e:
        logger.error(f"Error rendering subscription page: {e}")
        return page_renderer.render_error_page("Failed to load subscription page")

@core_bp.route('/tiers')
@requires_login
def tiers_page():
    """Tiers information page (redirect to subscription)"""
    try:
        upgrade_required = request.args.get('upgrade_required', 'false').lower() == 'true'
        
        if upgrade_required:
            return redirect("/subscription?upgrade=true")
        else:
            return redirect("/subscription")
        
    except Exception as e:
        logger.error(f"Error in tiers redirect: {e}")
        return redirect("/subscription")

# Debug route for session state
@core_bp.route('/whoami')
def whoami():
    """Debug route to check current session state"""
    return {
        "logged_in": session.get("logged_in"),
        "user_id": session.get("user_id"),
        "email": session.get("email"),
        "terms_accepted": session.get("terms_accepted"),
        "user_plan": session.get("user_plan"),
        "session_keys": list(session.keys()),
        "cookies": list(request.cookies.keys()),
        "path": request.path
    }

# API endpoints for core functionality
@core_bp.route('/api/navigation/menu')
@requires_login
def get_navigation_menu():
    """Get navigation menu for authenticated user"""
    try:
        menu_data = navigation_service.get_navigation_menu()
        
        return {
            "success": True,
            "navigation": menu_data
        }
        
    except Exception as e:
        logger.error(f"Error getting navigation menu: {e}")
        return {
            "success": False,
            "error": "Failed to get navigation menu"
        }, 500

@core_bp.route('/api/user/dashboard')
@requires_login  
def get_user_dashboard():
    """Get dashboard data for intro page"""
    try:
        dashboard_data = navigation_service.get_user_dashboard_data()
        
        return {
            "success": True,
            "dashboard": dashboard_data
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return {
            "success": False,
            "error": "Failed to get dashboard data"
        }, 500

@core_bp.route('/api/page/metadata')
def get_page_metadata():
    """Get metadata for current page"""
    try:
        page_path = request.args.get('path', '/')
        metadata = navigation_service.get_page_metadata(page_path)
        
        return {
            "success": True,
            "metadata": metadata,
            "path": page_path
        }
        
    except Exception as e:
        logger.error(f"Error getting page metadata: {e}")
        return {
            "success": False,
            "error": "Failed to get page metadata"
        }, 500

# Error handlers for core routes
@core_bp.route('/healthcheck')
def backup_health_check():
    """Backup health check endpoint in case health module has issues"""
    from datetime import datetime, timezone
    from flask import jsonify
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'soulbridge-ai-core',
        'version': '1.0.0',
        'message': 'Core service is running'
    })

@core_bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return page_renderer.render_error_page("Page not found", 404), 404

@core_bp.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    return page_renderer.render_error_page("Access forbidden", 403), 403

@core_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return page_renderer.render_error_page("Internal server error", 500), 500

def init_core_system(app):
    """Initialize core routes system"""
    
    # Register global error handlers
    @app.errorhandler(404)
    def global_not_found(error):
        return page_renderer.render_error_page("Page not found", 404), 404
    
    @app.errorhandler(403)
    def global_forbidden(error):
        return page_renderer.render_error_page("Access forbidden", 403), 403
    
    @app.errorhandler(500)
    def global_internal_error(error):
        return page_renderer.render_error_page("Something went wrong", 500), 500
    
    # Set up navigation context processor
    @app.context_processor
    def inject_navigation():
        """Inject navigation data into all templates"""
        try:
            if session.get('user_authenticated'):
                menu_data = navigation_service.get_navigation_menu()
                return {"navigation": menu_data}
            else:
                return {"navigation": {"items": [], "authenticated": False}}
        except Exception as e:
            logger.error(f"Error injecting navigation: {e}")
            return {"navigation": {"items": [], "authenticated": False}}
    
    logger.info("Core routes system initialized successfully")