#!/usr/bin/env python3
"""
Hybrid SoulBridge AI App - Working gradual initialization with main app routes
Uses proven working initialization but adds full functionality
"""
import os
import sys
import logging
import time
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request, session, redirect

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "railway-production-secret-key-2024")

# Global variables for services (proven working pattern)
services = {
    "database": None,
    "openai": None, 
    "email": None,
    "socketio": None
}

# Global service instances
db = None
openai_client = None
email_service = None
socketio = None

@app.route("/health")
def health():
    """Production health check with service status"""
    return jsonify({
        "status": "healthy",
        "service": "SoulBridge AI",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {name: service is not None for name, service in services.items()}
    }), 200

def init_database():
    """Initialize database with error handling"""
    global db
    try:
        logger.info("Initializing database...")
        from auth import Database
        db = Database()
        services["database"] = db
        logger.info("✅ Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        services["database"] = None
        return False

def init_openai():
    """Initialize OpenAI with error handling"""
    global openai_client
    try:
        if not os.environ.get("OPENAI_API_KEY"):
            logger.warning("OpenAI API key not provided")
            return False
            
        logger.info("Initializing OpenAI...")
        import openai
        openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        services["openai"] = openai_client
        logger.info("✅ OpenAI initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ OpenAI initialization failed: {e}")
        services["openai"] = None
        return False

def init_email():
    """Initialize email service with error handling"""
    global email_service
    try:
        logger.info("Initializing email service...")
        from email_service import EmailService
        email_service = EmailService()
        services["email"] = email_service
        logger.info("✅ Email service initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Email service initialization failed: {e}")
        services["email"] = None
        return False

def init_socketio():
    """Initialize SocketIO with error handling"""
    global socketio
    try:
        logger.info("Initializing SocketIO...")
        from flask_socketio import SocketIO
        socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)
        services["socketio"] = socketio
        logger.info("✅ SocketIO initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ SocketIO initialization failed: {e}")
        services["socketio"] = None
        return False

def initialize_services():
    """Initialize all services with graceful fallback"""
    logger.info("🚀 Starting SoulBridge AI service initialization...")
    
    # Initialize in order of dependency
    init_functions = [
        ("Database", init_database),
        ("OpenAI", init_openai), 
        ("Email", init_email),
        ("SocketIO", init_socketio),
    ]
    
    results = {}
    for service_name, init_func in init_functions:
        try:
            results[service_name] = init_func()
        except Exception as e:
            logger.error(f"Service {service_name} initialization crashed: {e}")
            results[service_name] = False
    
    # Log results
    working = sum(results.values())
    total = len(results)
    logger.info(f"📊 Service initialization complete: {working}/{total} services operational")
    
    for service_name, success in results.items():
        status = "✅" if success else "❌"
        logger.info(f"  {service_name}: {status}")
    
    return results

# Helper functions from main app
def is_logged_in():
    """Check if user is logged in"""
    return session.get("user_authenticated", False)

def get_user_plan():
    """Get user's selected plan"""
    return session.get("user_plan", "foundation")

# Import essential routes from main app
@app.route("/")
def home():
    """Home route with plan checking"""
    try:
        if not db:
            initialize_services()
            
        user_authenticated = is_logged_in()
        user_plan = get_user_plan()
        
        # Check if user needs to select a plan
        if user_authenticated and not user_plan:
            return redirect("/subscription")
            
        return render_template("chat.html")
    except Exception as e:
        logger.error(f"Home route error: {e}")
        return jsonify({"error": "Service temporarily unavailable"}), 503

@app.route("/login")
def login():
    """Login route"""
    try:
        return render_template("login.html")
    except Exception as e:
        logger.error(f"Login template error: {e}")
        return jsonify({"error": "Login page temporarily unavailable"}), 200

@app.route("/register")  
def register():
    """Register route"""
    try:
        return render_template("register.html")
    except Exception as e:
        logger.error(f"Register template error: {e}")
        return jsonify({"error": "Register page temporarily unavailable"}), 200

@app.route("/subscription")
def subscription():
    """Subscription route"""
    try:
        return render_template("subscription.html")
    except Exception as e:
        logger.error(f"Subscription template error: {e}")
        return jsonify({"error": "Subscription page temporarily unavailable"}), 200

@app.route("/profile")
def profile():
    """Profile route"""
    try:
        if not is_logged_in():
            return redirect("/login")
        return render_template("profile.html")
    except Exception as e:
        logger.error(f"Profile template error: {e}")
        return jsonify({"error": "Profile page temporarily unavailable"}), 200

# API routes
@app.route("/api/select-plan", methods=["POST"])
def select_plan():
    """Plan selection API"""
    try:
        data = request.get_json()
        plan_type = data.get("plan_type", "foundation")
        
        session["user_plan"] = plan_type
        session["plan_selected_at"] = time.time()
        session["first_time_user"] = False
        
        return jsonify({
            "success": True,
            "plan": plan_type,
            "redirect": "/"
        })
    except Exception as e:
        logger.error(f"Plan selection error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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
    logger.info(f"Starting SoulBridge AI Hybrid on port {port}")
    logger.info(f"Environment: {'Production' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Development'}")
    
    # Initialize services but don't fail if they don't work
    service_results = initialize_services()
    
    # Start the server regardless of service status
    logger.info("🌟 Starting Flask server...")
    
    # Use SocketIO if available, otherwise fall back to regular Flask
    if services["socketio"]:
        logger.info("Using SocketIO server")
        socketio.run(app, host="0.0.0.0", port=port, debug=False)
    else:
        logger.info("Using regular Flask server")
        app.run(host="0.0.0.0", port=port, debug=False, threaded=True, use_reloader=False)