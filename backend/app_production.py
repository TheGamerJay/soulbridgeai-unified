"""
Production-optimized SoulBridge AI Flask App
Prioritizes fast startup and health check responsiveness
"""
import os
import sys
import logging
import time
from datetime import datetime
from flask import Flask, jsonify, render_template, request, session, redirect, url_for

# Configure minimal logging for startup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create Flask app immediately
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "railway-production-secret-key-2024")

# Global variables for lazy loading
db = None
openai_client = None
email_service = None
socketio = None

# Health check endpoint - MUST be available immediately
@app.route("/health")
def health():
    """Ultra-simple health check for Railway - prioritize speed"""
    try:
        return jsonify({
            "status": "healthy",
            "service": "SoulBridge AI",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime": time.time()
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return "OK", 200

@app.route("/")
def home():
    """Simple home route"""
    try:
        # Initialize dependencies if needed
        if not db:
            init_core_dependencies()
        return render_template("chat.html")
    except Exception as e:
        logger.error(f"Home route error: {e}")
        return jsonify({"error": "Service temporarily unavailable"}), 503

def init_core_dependencies():
    """Initialize core dependencies lazily"""
    global db, openai_client, email_service, socketio
    
    try:
        logger.info("Initializing core dependencies...")
        
        # Initialize database
        if not db:
            try:
                from database import Database
                db = Database()
                logger.info("✅ Database initialized")
            except Exception as e:
                logger.warning(f"⚠️ Database init failed: {e}")
                db = None
        
        # Initialize OpenAI
        if not openai_client and os.environ.get("OPENAI_API_KEY"):
            try:
                import openai
                openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                logger.info("✅ OpenAI initialized")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI init failed: {e}")
                openai_client = None
        
        # Initialize email service
        if not email_service:
            try:
                from email_service import EmailService
                email_service = EmailService()
                logger.info("✅ Email service initialized")
            except Exception as e:
                logger.warning(f"⚠️ Email service init failed: {e}")
                email_service = None
                
        # Initialize SocketIO last (most complex)
        if not socketio:
            try:
                from flask_socketio import SocketIO
                socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)
                logger.info("✅ SocketIO initialized")
            except Exception as e:
                logger.warning(f"⚠️ SocketIO init failed: {e}")
                socketio = None
        
        logger.info("Core dependencies initialization complete")
        
    except Exception as e:
        logger.error(f"Dependency initialization failed: {e}")

# Import and register routes after basic setup
def register_routes():
    """Register all routes from main app"""
    try:
        logger.info("Registering routes...")
        
        # Import main app routes
        from app import app as main_app
        
        # Copy main app routes to this app
        for rule in main_app.url_map.iter_rules():
            if rule.endpoint not in ['health', 'static']:  # Don't override health check
                try:
                    view_func = main_app.view_functions[rule.endpoint]
                    app.add_url_rule(
                        rule.rule, 
                        rule.endpoint, 
                        view_func, 
                        methods=rule.methods
                    )
                except Exception as e:
                    logger.warning(f"Failed to register route {rule.rule}: {e}")
        
        logger.info("Routes registered successfully")
        
    except Exception as e:
        logger.error(f"Route registration failed: {e}")

# Lazy initialization for non-critical components
@app.before_first_request
def before_first_request():
    """Initialize complex dependencies after first request"""
    try:
        init_core_dependencies()
        register_routes()
    except Exception as e:
        logger.error(f"Before first request failed: {e}")

# Alternative route registration using direct import
@app.route("/login")
def login():
    """Login route"""
    try:
        if not db:
            init_core_dependencies()
        return render_template("login.html")
    except Exception as e:
        logger.error(f"Login route error: {e}")
        return jsonify({"error": "Service temporarily unavailable"}), 503

@app.route("/register")
def register():
    """Register route"""
    try:
        if not db:
            init_core_dependencies()
        return render_template("register.html")
    except Exception as e:
        logger.error(f"Register route error: {e}")
        return jsonify({"error": "Service temporarily unavailable"}), 503

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting SoulBridge AI on port {port}")
    
    # Start with minimal configuration for fast startup
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)