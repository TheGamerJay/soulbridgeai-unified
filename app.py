"""
SoulBridge AI - Modular Application Entry Point
Clean, maintainable Flask application with isolated modules
"""
from flask import Flask, render_template, request, jsonify
import os
import logging
from logging.handlers import RotatingFileHandler

# Import shared components
from shared.config.settings import config, validate_required_env_vars
from shared.middleware.session_manager import SessionManager, before_request_handler
from shared.database.connection import get_database

# Import module blueprints
from auth.routes import auth_bp
from companions.routes import companions_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__, static_folder='backend/static')
    
    # Configure app
    app.secret_key = config.SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    
    # Setup logging
    if not app.debug:
        file_handler = RotatingFileHandler('logs/soulbridge.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('SoulBridge AI startup')
    
    # Validate environment
    try:
        validate_required_env_vars()
    except ValueError as e:
        logger.error(f"❌ Environment validation failed: {e}")
        raise
    
    # Initialize database
    try:
        db = get_database()
        logger.info("✅ Database connection initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Register before request handler
    app.before_request(before_request_handler)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(companions_bp)
    
    # Core routes
    @app.route('/')
    def index():
        """Home page"""
        try:
            user_context = SessionManager.get_user_context()
            
            if user_context['is_logged_in']:
                return render_template('dashboard.html', **user_context)
            else:
                return render_template('index.html')
        
        except Exception as e:
            logger.error(f"❌ Index route error: {e}")
            return render_template('error.html', error="An error occurred"), 500
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        try:
            # Test database connection
            db = get_database()
            db.execute_query("SELECT 1", fetch='one')
            
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'modules': ['auth', 'companions', 'shared']
            })
        
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500
    
    @app.route('/about')
    def about():
        """About page"""
        return render_template('about.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """404 error handler"""
        logger.warning(f"404 error: {request.url}")
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 error handler"""
        logger.error(f"500 error: {error}")
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        """403 error handler"""
        logger.warning(f"403 error: {request.url}")
        return render_template('errors/403.html'), 403
    
    # Development routes (debug mode only)
    if app.debug:
        @app.route('/debug/session')
        def debug_session():
            """Debug session data"""
            return jsonify(SessionManager.get_user_context())
        
        @app.route('/debug/config')
        def debug_config():
            """Debug configuration (safe values only)"""
            return jsonify({
                'debug': app.config.get('DEBUG'),
                'secret_key_length': len(app.secret_key),
                'database_type': 'postgresql' if config.DATABASE_URL.startswith('postgresql') else 'sqlite'
            })
    
    logger.info("✅ SoulBridge AI modular application created successfully")
    return app

# Create application instance
app = create_app()

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=config.DEBUG)