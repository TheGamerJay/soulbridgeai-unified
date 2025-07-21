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
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, flash, make_response

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create Flask app with secure session configuration
app = Flask(__name__)

# Security: Use strong secret key or generate one
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    import secrets
    secret_key = secrets.token_hex(32)
    logger.warning("Generated temporary secret key - set SECRET_KEY environment variable for production")

app.secret_key = secret_key

# Security: Configure session cookies
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = bool(os.environ.get('RAILWAY_ENVIRONMENT'))  # HTTPS in production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Global variables for services
services = {
    "database": None,
    "openai": None, 
    "email": None,
    "socketio": None
}

# Global service instances and thread safety
import threading
db = None
openai_client = None
email_service = None
socketio = None
_service_lock = threading.RLock()

# Constants
VALID_CHARACTERS = ["Blayzo", "Sapphire", "Violet", "Crimson", "Blayzia", "Blayzica", "Blayzike", "Blayzion", "Blazelian"]
VALID_PLANS = ["foundation", "premium", "enterprise"]

def is_logged_in():
    """Check if user is logged in"""
    return session.get("user_authenticated", False)

def get_user_plan():
    """Get user's selected plan"""
    return session.get("user_plan", "foundation")

def parse_request_data():
    """Parse request data from both JSON and form data"""
    if request.is_json:
        data = request.get_json()
        return data.get("email", "").strip(), data.get("password", "").strip(), data.get("display_name", "").strip()
    else:
        return (request.form.get("email", "").strip(), 
                request.form.get("password", "").strip(),
                request.form.get("display_name", "").strip())

def setup_user_session(email, user_id=None, is_admin=False, dev_mode=False):
    """Setup user session with security measures"""
    # Security: Clear and regenerate session to prevent fixation attacks
    session.clear()
    session.permanent = True  # Use configured timeout
    session["user_authenticated"] = True
    session["user_email"] = email
    session["login_timestamp"] = datetime.now().isoformat()
    session["user_plan"] = "foundation"
    if user_id:
        session["user_id"] = user_id
    if is_admin:
        session["is_admin"] = True
    if dev_mode:
        session["dev_mode"] = True

def init_database():
    """Initialize database with error handling and thread safety"""
    global db
    with _service_lock:
        # Double-check pattern with lock
        if services["database"] and db:
            return True
            
        try:
            logger.info("Initializing database...")
            from auth import Database
            temp_db = Database()
            # Test database connectivity
            temp_conn = temp_db.get_connection()
            temp_conn.close()
            
            # Only update globals if successful
            db = temp_db
            services["database"] = temp_db
            logger.info("✅ Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            # Ensure consistent failure state
            db = None
            services["database"] = None
            return False

def init_openai():
    """Initialize OpenAI with error handling and thread safety"""
    global openai_client
    with _service_lock:
        if services["openai"] and openai_client:
            return True
            
        try:
            if not os.environ.get("OPENAI_API_KEY"):
                logger.warning("OpenAI API key not provided")
                # Consistent failure state
                openai_client = None
                services["openai"] = None
                return False
                
            logger.info("Initializing OpenAI...")
            import openai
            temp_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            # Only update globals if successful
            openai_client = temp_client
            services["openai"] = temp_client
            logger.info("✅ OpenAI initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ OpenAI initialization failed: {e}")
            # Ensure consistent failure state
            openai_client = None
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
        # Use environment-specific CORS settings for security
        allowed_origins = []
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            # Production - only allow specific domains
            allowed_origins = ["https://*.railway.app", "https://soulbridgeai.com"]
        else:
            # Development - allow local development
            allowed_origins = ["http://localhost:*", "http://127.0.0.1:*"]
            
        socketio = SocketIO(app, cors_allowed_origins=allowed_origins, logger=False, engineio_logger=False)
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
    """Production health check with service status and lazy initialization"""
    try:
        # Ensure services are initialized
        if not any(services.values()):
            logger.info("Lazy initializing services for health check...")
            initialize_services()
            
        return jsonify({
            "status": "healthy",
            "service": "SoulBridge AI", 
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {name: service is not None for name, service in services.items()}
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "service": "SoulBridge AI",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

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
        # Parse request data
        email, password, _ = parse_request_data()
        
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
            setup_user_session(email, is_admin=True, dev_mode=True)
            logger.info("Developer login successful")
            return jsonify({"success": True, "redirect": "/"})
        
        # For regular users, check database if available
        if services["database"] and db:
            try:
                # Use the authentication system from auth.py
                from auth import User
                user_data = User.authenticate(db, email, password)
                
                if user_data:
                    setup_user_session(email, user_id=user_data[0])
                    logger.info(f"User login successful: {email}")
                    return jsonify({"success": True, "redirect": "/"})
                else:
                    logger.warning(f"Failed login attempt for: {email}")
                    return jsonify({"success": False, "error": "Invalid email or password"}), 401
                    
            except Exception as db_error:
                logger.error(f"Database authentication error: {db_error}")
                # Fall through to basic auth if database fails
        
        # Fallback: Basic authentication for testing (ONLY if database fails)
        if not os.environ.get('RAILWAY_ENVIRONMENT'):  # Only in development
            if email == "test@example.com" and password == "test123":
                setup_user_session(email)
                logger.warning("Using development test authentication")
                return jsonify({"success": True, "redirect": "/"})
        
        # Authentication failed
        logger.warning(f"Authentication failed for user")  # Don't log email for security
        return jsonify({
            "success": False, 
            "error": "Invalid email or password"
        }), 401
        
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

@app.route("/auth/register", methods=["POST"])
def auth_register():
    """Handle user registration"""
    try:
        # Parse request data
        email, password, display_name = parse_request_data()
        
        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400
            
        if not display_name:
            display_name = email.split('@')[0]  # Use email prefix as default name
        
        # Initialize database if needed
        if not services["database"]:
            init_database()
        
        if services["database"] and db:
            try:
                from auth import User
                user = User(db)
                
                # Check if user already exists
                if user.user_exists(email):
                    return jsonify({"success": False, "error": "User already exists"}), 409
                
                # Create new user
                user_id = user.create_user(email, password, display_name)
                
                if user_id:
                    # Auto-login after registration
                    setup_user_session(email, user_id=user_id)
                    logger.info(f"User registered and logged in: {email}")
                    return jsonify({"success": True, "redirect": "/"})
                else:
                    return jsonify({"success": False, "error": "Registration failed"}), 500
                    
            except Exception as db_error:
                logger.error(f"Registration database error: {db_error}")
                return jsonify({"success": False, "error": "Registration failed"}), 500
        else:
            return jsonify({"success": False, "error": "Registration service unavailable"}), 503
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"success": False, "error": "Registration failed"}), 500

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
        if not is_logged_in():
            return redirect("/login")
        return render_template("referrals.html")
    except Exception as e:
        logger.error(f"Referrals template error: {e}")
        return jsonify({"error": "Referrals page temporarily unavailable"}), 500

@app.route("/decoder")
def decoder():
    """Decoder page"""
    try:
        if not is_logged_in():
            return redirect("/login")
        return render_template("decoder.html")
    except Exception as e:
        logger.error(f"Decoder template error: {e}")
        return jsonify({"error": "Decoder temporarily unavailable"}), 500

# ========================================
# API ROUTES
# ========================================

@app.route("/api/select-plan", methods=["POST"])
def select_plan():
    """Plan selection API"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
            
        plan_type = data.get("plan_type", "foundation")
        
        if plan_type not in VALID_PLANS:
            return jsonify({"success": False, "error": "Invalid plan type"}), 400
        
        session["user_plan"] = plan_type
        session["plan_selected_at"] = time.time()
        session["first_time_user"] = False
        
        logger.info(f"Plan selected: {plan_type} by {session.get('user_email')}")
        
        return jsonify({
            "success": True,
            "plan": plan_type,
            "redirect": "/"
        })
    except Exception as e:
        logger.error(f"Plan selection error: {e}")
        return jsonify({"success": False, "error": "Plan selection failed"}), 500

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Chat API endpoint"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "response": "Authentication required"}), 401
            
        if not services["openai"]:
            return jsonify({"success": False, "response": "AI service temporarily unavailable"}), 503
            
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "response": "Invalid request data"}), 400
            
        message = data.get("message", "").strip()
        character = data.get("character", "Blayzo")
        
        if not message or len(message) > 1000:
            return jsonify({"success": False, "response": "Message is required and must be under 1000 characters"}), 400
        
        # Sanitize character input
        if character not in VALID_CHARACTERS:
            character = "Blayzo"  # Default fallback
        
        # Use OpenAI for actual AI response
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are {character}, a helpful AI companion from SoulBridge AI."},
                    {"role": "user", "content": message}
                ],
                max_tokens=150,
                temperature=0.7
            )
            ai_response = response.choices[0].message.content
        except Exception as ai_error:
            logger.warning(f"OpenAI API error: {ai_error}")
            ai_response = f"Hello! I'm {character}. Thanks for your message: '{message}'. How can I help you today?"
        
        return jsonify({"success": True, "response": ai_response})
        
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

# Services will be initialized on first request to avoid blocking module import

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting SoulBridge AI on port {port}")
    logger.info(f"Environment: {'Production' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Development'}")
    
    # Initialize services for standalone execution
    logger.info("🚀 Initializing services...")
    initialize_services()
    
    # Start the server
    logger.info("🌟 Starting Flask server...")
    
    # Use SocketIO if available, otherwise fall back to regular Flask
    if services["socketio"] and socketio:
        logger.info("Using SocketIO server")
        socketio.run(app, host="0.0.0.0", port=port, debug=False)
    else:
        logger.info("Using regular Flask server")
        app.run(host="0.0.0.0", port=port, debug=False, threaded=True, use_reloader=False)