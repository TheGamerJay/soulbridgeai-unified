#!/usr/bin/env python3
"""
SoulBridge AI - Production Ready App
Combines working initialization with all essential routes
"""

# CRITICAL: eventlet monkey patching MUST be first for Gunicorn compatibility
import eventlet
eventlet.monkey_patch()

import os
import sys
import logging
import time
import uuid
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, flash, make_response

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "railway-production-secret-key-2024")

# Global variables for services
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

def is_logged_in():
    """Check if user is logged in"""
    return session.get("user_authenticated", False)

def get_user_plan():
    """Get user's selected plan"""
    return session.get("user_plan", "foundation")

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
    
    return results

# ========================================
# CORE ROUTES
# ========================================

@app.route("/health")
def health():
    """Production health check with service status"""
    return jsonify({
        "status": "healthy",
        "service": "SoulBridge AI", 
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {name: service is not None for name, service in services.items()}
    }), 200

@app.route("/")
def home():
    """Home route with plan checking"""
    try:
        if not services["database"]:
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

# ========================================
# AUTHENTICATION ROUTES
# ========================================

@app.route("/login")
def login_page():
    """Login page"""
    try:
        return render_template("login.html")
    except Exception as e:
        logger.error(f"Login template error: {e}")
        return jsonify({"error": "Login page temporarily unavailable"}), 200

@app.route("/auth/login", methods=["POST"])
def auth_login():
    """Handle login authentication"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            email = data.get("email", "").strip()
            password = data.get("password", "").strip()
        else:
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()
        
        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400
        
        # Initialize database if needed
        if not services["database"]:
            init_database()
        
        # Developer credentials from environment (secure)
        DEV_EMAIL = os.environ.get("DEV_EMAIL")
        DEV_PASSWORD = os.environ.get("DEV_PASSWORD")
        
        # Check if this is the developer account
        is_developer = False
        if DEV_EMAIL and DEV_PASSWORD and email == DEV_EMAIL:
            is_developer = password == DEV_PASSWORD
            logger.info(f"Developer login attempt: {is_developer}")
        
        if is_developer:
            # Set session for developer
            session["user_authenticated"] = True
            session["user_email"] = email
            session["login_timestamp"] = datetime.now().isoformat()
            session["is_admin"] = True
            session["dev_mode"] = True
            session.permanent = False
            logger.info("Developer login successful")
            return jsonify({"success": True, "redirect": "/"})
        
        # For regular users, check database if available
        if services["database"] and db:
            try:
                # Use the authentication system from auth.py
                from auth import User
                user_data = User.authenticate(db, email, password)
                
                if user_data:
                    # Set session for authenticated user
                    session["user_authenticated"] = True
                    session["user_email"] = email
                    session["login_timestamp"] = datetime.now().isoformat()
                    session["user_id"] = user_data[0]  # user ID from database
                    session.permanent = False
                    
                    # Restore user plan if exists
                    session["user_plan"] = session.get("user_plan", "foundation")
                    
                    logger.info(f"User login successful: {email}")
                    return jsonify({"success": True, "redirect": "/"})
                else:
                    logger.warning(f"Failed login attempt for: {email}")
                    return jsonify({"success": False, "error": "Invalid email or password"}), 401
                    
            except Exception as db_error:
                logger.error(f"Database authentication error: {db_error}")
                # Fall through to basic auth if database fails
        
        # Fallback: Basic authentication for testing (if no database)
        # This should be removed in production
        if email == "test@example.com" and password == "test123":
            session["user_authenticated"] = True
            session["user_email"] = email
            session["user_plan"] = "foundation"
            session.permanent = False
            logger.warning("Using fallback test authentication - NOT FOR PRODUCTION")
            return jsonify({"success": True, "redirect": "/"})
        
        # Authentication failed
        logger.warning(f"Authentication failed for: {email}")
        return jsonify({"success": False, "error": "Invalid email or password"}), 401
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"success": False, "error": "Login failed"}), 500

@app.route("/auth/logout")
def logout():
    """Logout route"""
    try:
        session.clear()
        return redirect("/login")
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return redirect("/login")

@app.route("/register")  
def register_page():
    """Register page"""
    try:
        return render_template("register.html")
    except Exception as e:
        logger.error(f"Register template error: {e}")
        return jsonify({"error": "Register page temporarily unavailable"}), 200

# ========================================
# MAIN APP ROUTES
# ========================================

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

@app.route("/subscription")
def subscription():
    """Subscription route"""
    try:
        return render_template("subscription.html")
    except Exception as e:
        logger.error(f"Subscription template error: {e}")
        return jsonify({"error": "Subscription page temporarily unavailable"}), 200

@app.route("/community-dashboard")
def community_dashboard():
    """Community dashboard route"""
    try:
        if not is_logged_in():
            return redirect("/login")
        return render_template("community_dashboard.html")
    except Exception as e:
        logger.error(f"Community dashboard error: {e}")
        return jsonify({"error": "Community dashboard temporarily unavailable"}), 200
        
@app.route("/referrals")
def referrals():
    """Referrals route"""
    try:
        return render_template("referrals.html")
    except Exception as e:
        logger.error(f"Referrals template error: {e}")
        return jsonify({"error": "Referrals page temporarily unavailable"}), 200

@app.route("/decoder")
def decoder():
    """Decoder page"""
    try:
        return render_template("decoder.html")
    except Exception as e:
        logger.error(f"Decoder template error: {e}")
        return jsonify({"error": "Decoder temporarily unavailable"}), 200

# ========================================
# API ROUTES
# ========================================

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

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Chat API endpoint"""
    try:
        if not services["openai"]:
            return jsonify({"success": False, "response": "AI service temporarily unavailable"}), 503
            
        data = request.get_json()
        message = data.get("message", "")
        character = data.get("character", "Blayzo")
        
        if not message:
            return jsonify({"success": False, "response": "Message is required"}), 400
        
        # Simple AI response (you can enhance this)
        response = f"Hello! I'm {character}. Thanks for your message: '{message}'. How can I help you today?"
        
        return jsonify({"success": True, "response": response})
        
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        return jsonify({"success": False, "response": "Sorry, I encountered an error."}), 500

# ========================================
# UTILITY ROUTES  
# ========================================

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error"}), 500

# ========================================
# APPLICATION STARTUP
# ========================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting SoulBridge AI on port {port}")
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