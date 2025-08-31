"""
SoulBridge AI - Modular Application
Rebuilt from 19,326-line monolith using extracted modules
Clean Flask application with Blueprint architecture
"""
import os
import logging
from datetime import datetime, timedelta
from flask import Flask, session, request, redirect, jsonify, url_for
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # ----- Core secrets -----
    # IMPORTANT: keep SECRET_KEY stable across deploys/instances
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")

    # Detect prod on Railway
    IS_RAILWAY = bool(os.environ.get("RAILWAY_PROJECT_ID"))
    IS_PROD = os.environ.get("ENVIRONMENT") == "production" or IS_RAILWAY

    # Make Flask trust Railway's reverse proxy so it sees HTTPS correctly.
    # Without this, Flask may think the request is http and set cookies wrong.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # ----- Session cookie settings -----
    # Use sane defaults that work for normal same-site navigations (form POST -> redirect -> GET).
    app.config.update(
        SESSION_COOKIE_NAME="session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_PATH="/",
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        SESSION_REFRESH_EACH_REQUEST=True,
    )

    if IS_PROD:
        # Let the browser decide the correct host; avoids domain mismatch across custom domains / *.railway.app
        app.config["SESSION_COOKIE_DOMAIN"] = None

        # If your origin is HTTPS (custom domain with TLS or *.railway.app over HTTPS):
        # Preferred, secure setup:
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # great for normal same-site redirects

        # ---- TEMPORARY DIAGNOSTIC SWITCH ----
        # If cookies still don't stick, toggle these 2 lines *temporarily* and retest:
        # app.config["SESSION_COOKIE_SECURE"] = False   # TEMP TEST ONLY
        # app.config["SESSION_COOKIE_SAMESITE"] = "Lax" # keep Lax for same-site
    else:
        # Local dev often runs http://localhost → cookie must not be Secure there
        app.config["SESSION_COOKIE_SECURE"] = False
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
        app.config["SESSION_COOKIE_DOMAIN"] = None
    
    # Auto-cleanup configuration
    app.config['AUTO_START_MONITORING'] = True
    app.config['AUTO_CLEANUP_CHAT_SESSIONS'] = True
    app.config['AUTO_CLEANUP_ANALYTICS'] = True
    
    # Enable CORS for development
    if os.environ.get('ENVIRONMENT') != 'production':
        CORS(app, supports_credentials=True)
    
    # Initialize database system
    try:
        from modules.shared.database import init_database_system
        init_database_system(app)
        logger.info("✅ Database system initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Register all module blueprints
    register_blueprints(app)
    
    # Initialize all systems
    initialize_systems(app)
    
    # Set up global middleware
    setup_middleware(app)
    
    # Set up error handlers
    setup_error_handlers(app)
    
    # Add diagnostic routes for session debugging
    @app.route("/_debug/session")
    def _debug_session():
        return jsonify(
            session=dict(session),
            keys=list(session.keys()),
            permanent=session.permanent,
        )

    @app.after_request
    def _log_set_cookie(resp):
        # Log Set-Cookie once (or when logging is enabled)
        sc = resp.headers.get("Set-Cookie")
        if sc and "/auth/login" in request.path:
            logger.info(f"Set-Cookie on login: {sc}")
        return resp

    logger.info("🚀 SoulBridge AI application created successfully")
    return app

def register_blueprints(app):
    """Register all extracted module blueprints"""
    try:
        # Core system routes
        from modules.core import core_bp
        app.register_blueprint(core_bp)
        logger.info("✅ Core routes registered")
        
        # Authentication system
        from modules.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        logger.info("✅ Auth system registered")
        
        # Main chat system
        from modules.chat import chat_bp
        app.register_blueprint(chat_bp)
        logger.info("✅ Chat system registered")
        
        # Companion system
        from modules.companions import companions_bp
        app.register_blueprint(companions_bp)
        logger.info("✅ Companions system registered")
        
        # Voice system
        from modules.voice import voice_bp
        app.register_blueprint(voice_bp)
        logger.info("✅ Voice system registered")
        
        # Creative features
        from modules.creative import creative_bp
        app.register_blueprint(creative_bp)
        logger.info("✅ Creative system registered")
        
        # AI Images
        from modules.ai_images import ai_images_bp
        app.register_blueprint(ai_images_bp)
        logger.info("✅ AI Images system registered")
        
        # Analytics dashboard
        from modules.analytics import analytics_bp
        app.register_blueprint(analytics_bp)
        logger.info("✅ Analytics system registered")
        
        # User profiles
        from modules.user_profile import profile_bp
        app.register_blueprint(profile_bp)
        logger.info("✅ User Profile system registered")
        
        # Relationship profiles
        from modules.relationship_profiles import relationship_bp
        app.register_blueprint(relationship_bp)
        logger.info("✅ Relationship Profiles registered")
        
        # Meditations
        from modules.meditations import meditations_bp
        app.register_blueprint(meditations_bp)
        logger.info("✅ Meditations system registered")
        
        # Library management
        from modules.library import library_bp
        app.register_blueprint(library_bp)
        logger.info("✅ Library system registered")
        
        # Community system
        from modules.community import community_bp
        app.register_blueprint(community_bp)
        logger.info("✅ Community system registered")
        
        # Payment system
        from modules.payments import payments_bp
        app.register_blueprint(payments_bp)
        logger.info("✅ Payment system registered")
        
        # Admin system
        from modules.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        logger.info("✅ Admin system registered")
        
        # Health and monitoring
        from modules.health import health_bp
        app.register_blueprint(health_bp)
        logger.info("✅ Health system registered")
        
        # Legal/compliance
        from modules.legal import legal_bp
        app.register_blueprint(legal_bp)
        logger.info("✅ Legal system registered")
        
        # Notifications/email
        from modules.notifications import notifications_bp
        app.register_blueprint(notifications_bp)
        logger.info("✅ Notifications system registered")
        
        # Consolidated API endpoints
        from modules.api import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
        logger.info("✅ Consolidated API registered")
        
        # Mini Studio (if available)
        try:
            from modules.studio import studio_bp
            app.register_blueprint(studio_bp)
            logger.info("✅ Mini Studio registered")
        except ImportError:
            logger.info("⚠️ Mini Studio not available")
        
        logger.info("🎯 All module blueprints registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Blueprint registration failed: {e}")
        raise

def initialize_systems(app):
    """Initialize all extracted systems with their dependencies"""
    try:
        # Initialize database manager
        from modules.shared.database import get_database
        database_manager = get_database()
        
        # Initialize OpenAI client
        openai_client = None
        try:
            from openai import OpenAI
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                openai_client = OpenAI(api_key=api_key)
                logger.info("✅ OpenAI client initialized")
        except ImportError:
            logger.warning("OpenAI package not available")
        
        # Initialize health system
        from modules.health import init_health_system
        init_health_system(app, database_manager, openai_client)
        
        # Initialize chat system
        from modules.chat import init_chat_system
        init_chat_system(app, database_manager, openai_client)
        
        # Initialize analytics system
        from modules.analytics import init_analytics_system
        init_analytics_system(app)
        
        # Initialize core system
        from modules.core import init_core_system
        init_core_system(app)
        
        # Initialize API system
        from modules.api import init_api_system
        init_api_system(app)
        
        # Initialize legal system
        from modules.legal.routes import init_legal_services
        init_legal_services(database_manager)
        
        logger.info("🔧 All systems initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ System initialization failed: {e}")
        raise

def setup_middleware(app):
    """Set up global middleware"""
    try:
        @app.before_request
        def ensure_session_persistence():
            """Simple auth guard for pages only - APIs handle their own auth"""
            try:
                # Define paths that don't need authentication
                PUBLIC_PATHS = (
                    "/login", "/auth/login", "/auth/register", "/auth/logout",
                    "/static", "/assets", "/favicon", "/whoami", "/health", 
                    "/debug-session", "/", "/api"
                )
                
                # Let public paths and API routes through
                if any(request.path.startswith(p) for p in PUBLIC_PATHS):
                    return  # Allow through
                
                # Only check auth for main application pages
                # (like /intro, /profile, etc - not API routes)
                if not request.path.startswith('/api'):
                    logged_in = session.get("logged_in")
                    user_id = session.get("user_id") 
                    email = session.get("email")
                    
                    # Debug session state
                    logger.info(f"[AUTH_GUARD] Checking {request.path}: logged_in={logged_in}, user_id={user_id}, email={email}, session_keys={list(session.keys())}")
                    
                    # If not authenticated, redirect to login
                    if not (logged_in and user_id and email):
                        logger.info(f"[AUTH_GUARD] Page {request.path} requires auth - redirecting to login")
                        return redirect(f"/auth/login?return_to={request.path.lstrip('/')}")
                
                # Let everything else through (including API routes)
                return
                
            except Exception as e:
                logger.error(f"Middleware error: {e}")
        
        @app.after_request
        def after_request(response):
            """Set response headers"""
            try:
                # Security headers
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'DENY'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                
                # Cache control for static files
                if request.path.startswith('/static/'):
                    response.headers['Cache-Control'] = 'public, max-age=86400'  # 24 hours
                
                return response
            except Exception as e:
                logger.error(f"After request error: {e}")
                return response
        
        logger.info("🛡️ Global middleware configured")
        
    except Exception as e:
        logger.error(f"❌ Middleware setup failed: {e}")

def setup_error_handlers(app):
    """Set up global error handlers"""
    try:
        from modules.core.page_renderer import PageRenderer
        page_renderer = PageRenderer()
        
        @app.errorhandler(404)
        def not_found_error(error):
            logger.warning(f"404 Error: {request.path}")
            return page_renderer.render_error_page("Page not found", 404), 404
        
        @app.errorhandler(403)
        def forbidden_error(error):
            logger.warning(f"403 Error: {request.path}")
            return page_renderer.render_error_page("Access forbidden", 403), 403
        
        @app.errorhandler(500)
        def internal_error(error):
            logger.error(f"500 Error: {request.path} - {str(error)}")
            return page_renderer.render_error_page("Internal server error", 500), 500
        
        @app.errorhandler(Exception)
        def handle_exception(error):
            logger.error(f"Unhandled exception: {str(error)}")
            return page_renderer.render_error_page("Something went wrong", 500), 500
        
        logger.info("🚨 Global error handlers configured")
        
    except Exception as e:
        logger.error(f"❌ Error handler setup failed: {e}")

# Create the application
app = create_app()

if __name__ == "__main__":
    # Development server
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG_MODE", "false").lower() == "true"
    
    logger.info(f"🌟 Starting SoulBridge AI on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)