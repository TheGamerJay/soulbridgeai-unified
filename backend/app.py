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

# Configure logging first
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not installed, relying on system environment variables")

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
app.config['SESSION_COOKIE_PATH'] = '/'  # Ensure cookie works for all paths
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

# Admin and surveillance constants
ADMIN_DASH_KEY = os.environ.get("ADMIN_DASH_KEY", "soulbridge_admin_2024")
MAINTENANCE_LOG_FILE = "logs/maintenance_log.txt"
THREAT_LOG_FILE = "logs/threat_log.txt"
TRAP_LOG_FILE = "logs/trap_log.txt"

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Enhanced surveillance system with Flask context safety
class BasicSurveillanceSystem:
    def __init__(self):
        self.system_start_time = datetime.now()
        self.blocked_ips = set()
        self.security_threats = []
        self.maintenance_log = []
        self.emergency_mode = False
        self.critical_errors_count = 0
        self.watchdog_enabled = True
        self.last_health_check = datetime.now()
        
    def write_to_log_file(self, log_file, entry):
        """Write entry to log file with error handling"""
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except Exception as e:
            # Use basic print instead of logger to avoid potential Flask context issues
            print(f"Failed to write to log {log_file}: {e}")
    
    def log_maintenance(self, action, details):
        """Log maintenance action safely"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"[{timestamp}] 🔧 {action}: {details}"
            self.maintenance_log.append(entry)
            # Keep only last 1000 entries in memory
            if len(self.maintenance_log) > 1000:
                self.maintenance_log = self.maintenance_log[-1000:]
            self.write_to_log_file(MAINTENANCE_LOG_FILE, entry)
        except Exception as e:
            print(f"Error logging maintenance: {e}")
    
    def log_threat(self, ip_address, threat_details, severity="medium"):
        """Log security threat safely"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"[{timestamp}] 🚨 THREAT ({severity.upper()}): {ip_address} - {threat_details}"
            self.security_threats.append({
                'timestamp': datetime.now(),
                'ip': ip_address,
                'details': threat_details,
                'severity': severity
            })
            # Keep only last 500 threats in memory
            if len(self.security_threats) > 500:
                self.security_threats = self.security_threats[-500:]
            self.write_to_log_file(THREAT_LOG_FILE, entry)
        except Exception as e:
            print(f"Error logging threat: {e}")
    
    def safe_health_check(self):
        """Perform health check without Flask request context"""
        try:
            self.last_health_check = datetime.now()
            # Basic system health checks that don't require Flask context
            current_time = datetime.now()
            uptime_hours = (current_time - self.system_start_time).total_seconds() / 3600
            
            # Log periodic health status
            if int(uptime_hours) % 1 == 0:  # Every hour
                self.log_maintenance("HEALTH_CHECK", f"System running for {uptime_hours:.1f} hours")
            
            return True
        except Exception as e:
            self.log_maintenance("HEALTH_CHECK_ERROR", f"Health check failed: {e}")
            return False
    
    def get_system_stats(self):
        """Get current system statistics safely"""
        try:
            return {
                'uptime_seconds': (datetime.now() - self.system_start_time).total_seconds(),
                'blocked_ips_count': len(self.blocked_ips),
                'threats_count': len(self.security_threats),
                'emergency_mode': self.emergency_mode,
                'critical_errors': self.critical_errors_count,
                'watchdog_enabled': self.watchdog_enabled
            }
        except Exception as e:
            self.log_maintenance("STATS_ERROR", f"Failed to get stats: {e}")
            return {}

# Initialize basic surveillance system
surveillance_system = BasicSurveillanceSystem()
surveillance_system.log_maintenance("SYSTEM_START", "Basic surveillance system initialized")

def background_monitoring():
    """Background monitoring task that runs safely without Flask context"""
    import time
    
    def monitoring_loop():
        while True:
            try:
                # Perform health check
                surveillance_system.safe_health_check()
                
                # Clean up old logs periodically
                current_time = datetime.now()
                if hasattr(surveillance_system, 'last_cleanup'):
                    time_since_cleanup = (current_time - surveillance_system.last_cleanup).total_seconds()
                else:
                    surveillance_system.last_cleanup = current_time
                    time_since_cleanup = 0
                
                # Clean up every 6 hours
                if time_since_cleanup > 21600:  # 6 hours
                    surveillance_system.log_maintenance("CLEANUP", "Performing periodic cleanup")
                    surveillance_system.last_cleanup = current_time
                
                # Sleep for 5 minutes between checks
                time.sleep(300)
                
            except Exception as e:
                # Log error safely without using Flask logger
                try:
                    surveillance_system.log_maintenance("MONITOR_ERROR", f"Background monitoring error: {e}")
                except:
                    print(f"Background monitoring error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    # Start monitoring in a separate thread
    try:
        import threading
        monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
        surveillance_system.log_maintenance("MONITOR_START", "Background monitoring thread started")
    except Exception as e:
        surveillance_system.log_maintenance("MONITOR_START_ERROR", f"Failed to start background monitoring: {e}")

# Start background monitoring
background_monitoring()

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
    session.permanent = False  # Session expires when browser closes
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

def login_success_response(redirect_to="/"):
    """Return appropriate response for successful login (JSON for AJAX, redirect for forms)"""
    # Check if request expects JSON response (AJAX/fetch) vs HTML redirect (form)
    accept_header = request.headers.get('Accept', '')
    
    # If Accept header includes application/json, it's likely an AJAX request
    if 'application/json' in accept_header:
        return jsonify({"success": True, "redirect": redirect_to})
    else:
        # Regular form submission - browser expects redirect with 303 See Other for proper GET
        return redirect(redirect_to, code=303)

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
            
        socketio = SocketIO(
            app, 
            cors_allowed_origins=allowed_origins, 
            logger=False, 
            engineio_logger=False
        )
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

@app.route("/", methods=["GET", "POST"])
def home():
    """Home route - require login then show intro"""
    try:
        # Require authentication for main app access
        logger.info(f"Home route: Checking authentication - Session: {dict(session)}")
        
        if not is_logged_in():
            logger.info(f"Home route: User not authenticated, redirecting to login")
            return redirect("/login")
        
        # User is authenticated - show the intro/chat interface
        logger.info(f"Home route: User authenticated, showing chat interface")
        
        # Initialize services if needed
        if not services["database"]:
            initialize_services()
        
        # Show chat page with proper authentication
        return render_template("chat.html")
        
    except Exception as e:
        logger.error(f"Home route error: {e}")
        return redirect("/login")

# ========================================
# AUTHENTICATION ROUTES
# ========================================

@app.route("/login")
def login_page():
    """Login page"""
    try:
        clerk_publishable_key = os.environ.get("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
        return render_template("login.html", clerk_publishable_key=clerk_publishable_key)
    except Exception as e:
        logger.error(f"Login template error: {e}")
        return jsonify({"error": "Login page temporarily unavailable"}), 200

@app.route("/auth/login", methods=["GET", "POST"])
def auth_login():
    """Handle login authentication"""
    # Handle GET requests - show login form
    if request.method == "GET":
        return render_template("login.html")
    
    # Handle POST requests - process login
    try:
        # Parse request data
        email, password, _ = parse_request_data()
        
        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400
        
        # Normalize email to lowercase for consistency
        email = email.lower().strip()
        
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
            # Return JSON for AJAX requests
            return jsonify({"success": True, "redirect": "/"})
        
        # For regular users, check database if available
        if services["database"] and db:
            try:
                # Use the authentication system from auth.py
                from auth import User
                user = User(db)
                user_data = User.authenticate(db, email, password)
                
                if user_data:
                    setup_user_session(email, user_id=user_data[0])
                    logger.info(f"User login successful: {email}")
                    
                    return login_success_response()
                else:
                    logger.warning(f"Failed login attempt for: {email} (user exists: {user.user_exists(email)})")
                    return jsonify({"success": False, "error": "Invalid email or password"}), 401
                    
            except Exception as db_error:
                logger.error(f"Database authentication error: {db_error}")
                # Fall through to basic auth if database fails
        
        # Fallback: Basic authentication for testing and initial setup
        if email == "test@example.com" and password == "test123":
            # Always allow test credentials and create user if needed
            try:
                if services["database"] and db:
                    from auth import User
                    user = User(db)
                    if not user.user_exists(email):
                        # Create the test user if it doesn't exist
                        user_id = user.create_user(email, password, "Test User")
                        logger.info("Created test user in database")
                        setup_user_session(email, user_id=user_id)
                        
                        # Always return JSON for consistency
                        return jsonify({"success": True, "redirect": "/"})
                    else:
                        # Test user exists, try to authenticate with database
                        user_data = User.authenticate(db, email, password)
                        if user_data:
                            setup_user_session(email, user_id=user_data[0])
                        else:
                            # Database authentication failed, but allow test user anyway
                            setup_user_session(email)
                        
                        # Always return JSON for consistency
                        return jsonify({"success": True, "redirect": "/"})
                else:
                    # Database not available, use fallback
                    setup_user_session(email)
                    logger.warning("Database not available, using fallback test authentication")
                    
                    # Always return JSON for consistency
                    return jsonify({"success": True, "redirect": "/"})
            except Exception as e:
                logger.error(f"Error with test user authentication: {e}")
                # Even if there's an error, allow test credentials to work
                setup_user_session(email)
                logger.warning("Using emergency fallback test authentication")
                
                # Always return JSON for consistency
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

@app.route("/auth/logout", methods=["GET", "POST"])
def logout():
    """Logout route"""
    try:
        session.clear()
        return redirect("/login")
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return redirect("/login")

@app.route("/debug/session")
def debug_session():
    """Debug endpoint to check session state"""
    return jsonify({
        "session_data": dict(session),
        "is_logged_in": is_logged_in(),
        "user_authenticated": session.get("user_authenticated", False),
        "user_email": session.get("user_email", "not_set")
    })


@app.route("/register")  
def register_page():
    """Register page"""
    try:
        clerk_publishable_key = os.environ.get("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
        return render_template("register.html", clerk_publishable_key=clerk_publishable_key)
    except Exception as e:
        logger.error(f"Register template error: {e}")
        return jsonify({"error": "Register page temporarily unavailable"}), 200

@app.route("/auth/register", methods=["GET", "POST"])
def auth_register():
    """Handle user registration"""
    # Handle GET requests - show registration form
    if request.method == "GET":
        return render_template("register.html")
    
    # Handle POST requests - process registration
    try:
        # Parse request data
        email, password, display_name = parse_request_data()
        
        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400
        
        # Normalize email to lowercase for consistency
        email = email.lower().strip()
            
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
                    logger.warning(f"Registration attempt for existing user: {email}")
                    return jsonify({"success": False, "error": "User already exists"}), 409
                
                # Create new user
                user_id = user.create_user(email, password, display_name)
                
                if user_id:
                    # Auto-login after registration
                    setup_user_session(email, user_id=user_id)
                    logger.info(f"User registered and logged in: {email}")
                    
                    # Initialize email service if needed and send welcome email
                    try:
                        if not services["email"]:
                            init_email()
                        
                        if services["email"] and email_service:
                            result = email_service.send_welcome_email(email, display_name)
                            if result.get("success"):
                                logger.info(f"Welcome email sent to {email}")
                            else:
                                logger.warning(f"Welcome email failed for {email}: {result.get('error')}")
                        else:
                            logger.warning(f"Email service not available for welcome email to {email}")
                    except Exception as e:
                        logger.error(f"Welcome email error for {email}: {e}")
                    
                    # New users should go to plan selection  
                    return jsonify({"success": True, "redirect": "/subscription"})
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
# ADDITIONAL ROUTES
# ========================================

@app.route("/help")
def help_page():
    """Help and support page"""
    try:
        if not is_logged_in():
            return redirect("/login")
        return render_template("help.html")
    except Exception as e:
        logger.error(f"Help page error: {e}")
        # Fallback to simple help content
        return """
        <html><head><title>Help - SoulBridge AI</title></head>
        <body style="font-family: Arial; padding: 20px; background: #0f172a; color: #e2e8f0;">
            <h1 style="color: #22d3ee;">SoulBridge AI Help</h1>
            <p>Welcome to SoulBridge AI! Here are some quick tips:</p>
            <ul>
                <li>Choose your AI companion from the character selection screen</li>
                <li>Start conversations by typing in the chat box</li>
                <li>Use the navigation assistant (Sapphire) for help with features</li>
                <li>Access your profile and settings from the top menu</li>
            </ul>
            <a href="/" style="color: #22d3ee;">← Back to Chat</a>
        </body></html>
        """

@app.route("/terms")
def terms_page():
    """Terms of service and privacy policy"""
    try:
        return render_template("terms.html")
    except Exception as e:
        logger.error(f"Terms page error: {e}")
        # Fallback to simple terms content
        return """
        <html><head><title>Terms & Privacy - SoulBridge AI</title></head>
        <body style="font-family: Arial; padding: 20px; background: #0f172a; color: #e2e8f0;">
            <h1 style="color: #22d3ee;">Terms of Service & Privacy Policy</h1>
            <h2>Terms of Service</h2>
            <p>By using SoulBridge AI, you agree to use our service responsibly and in accordance with applicable laws.</p>
            <h2>Privacy Policy</h2>
            <p>We respect your privacy. Your conversations are private and we don't share your personal data with third parties.</p>
            <a href="/register" style="color: #22d3ee;">← Back to Registration</a>
        </body></html>
        """

@app.route("/library")
def library_page():
    """Conversation library (coming soon)"""
    try:
        if not is_logged_in():
            return redirect("/login")
        return jsonify({"message": "Library feature coming soon!", "redirect": "/"}), 200
    except Exception as e:
        logger.error(f"Library page error: {e}")
        return redirect("/")

@app.route("/voice-chat")
def voice_chat_page():
    """Voice chat feature (coming soon)"""
    try:
        if not is_logged_in():
            return redirect("/login")
        return jsonify({"message": "Voice chat feature coming soon!", "redirect": "/"}), 200
    except Exception as e:
        logger.error(f"Voice chat page error: {e}")
        return redirect("/")

@app.route("/auth/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Working password reset functionality"""
    if request.method == "GET":
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset - SoulBridge AI</title>
            <style>
                body { 
                    font-family: system-ui, -apple-system, sans-serif; 
                    padding: 40px 20px; 
                    background: linear-gradient(135deg, #000000 0%, #0f172a 50%, #1e293b 100%); 
                    color: #e2e8f0; 
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0;
                }
                .container {
                    max-width: 500px;
                    background: rgba(0,0,0,0.8);
                    padding: 3rem;
                    border-radius: 16px;
                    border: 2px solid #22d3ee;
                    backdrop-filter: blur(15px);
                }
                h1 { color: #22d3ee; margin-bottom: 1.5rem; text-align: center; }
                .form-group { margin-bottom: 1.5rem; }
                label { display: block; margin-bottom: 0.5rem; color: #22d3ee; font-weight: 600; }
                input { 
                    width: 100%; 
                    padding: 12px; 
                    border: 2px solid #374151; 
                    border-radius: 8px; 
                    background: rgba(0,0,0,0.5);
                    color: #e2e8f0;
                    font-size: 16px;
                }
                input:focus { border-color: #22d3ee; outline: none; }
                .btn { 
                    width: 100%;
                    padding: 12px 24px;
                    background: #22d3ee;
                    color: #000;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }
                .btn:hover { background: #06b6d4; transform: translateY(-2px); }
                .btn:disabled { background: #374151; cursor: not-allowed; }
                .back-link { 
                    display: block;
                    text-align: center;
                    margin-top: 2rem;
                    color: #22d3ee; 
                    text-decoration: none;
                }
                .message { padding: 1rem; margin: 1rem 0; border-radius: 8px; text-align: center; }
                .error { background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; color: #fca5a5; }
                .success { background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; color: #6ee7b7; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔐 Reset Password</h1>
                <form id="resetForm">
                    <div class="form-group">
                        <label for="email">Email Address</label>
                        <input type="email" id="email" name="email" required placeholder="Enter your email">
                    </div>
                    <button type="submit" class="btn" id="resetBtn">Send Reset Instructions</button>
                </form>
                <a href="/login" class="back-link">← Back to Login</a>
                
                <script>
                document.getElementById('resetForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    const btn = document.getElementById('resetBtn');
                    const email = document.getElementById('email').value;
                    
                    btn.disabled = true;
                    btn.textContent = 'Sending...';
                    
                    try {
                        const response = await fetch('/auth/forgot-password', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email })
                        });
                        
                        const data = await response.json();
                        
                        const message = document.createElement('div');
                        message.className = data.success ? 'message success' : 'message error';
                        message.textContent = data.message;
                        
                        const form = document.getElementById('resetForm');
                        form.parentNode.insertBefore(message, form);
                        
                        if (data.success) {
                            form.style.display = 'none';
                        }
                    } catch (error) {
                        alert('Network error. Please try again.');
                    }
                    
                    btn.disabled = false;
                    btn.textContent = 'Send Reset Instructions';
                });
                </script>
            </div>
        </body>
        </html>
        """
    
    # Handle POST request
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        
        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400
        
        # Initialize database if needed
        if not services["database"]:
            init_database()
        
        if services["database"] and db:
            from auth import User
            import secrets
            user = User(db)
            
            # Check if user exists
            if user.user_exists(email):
                try:
                    # Generate secure reset token
                    reset_token = secrets.token_urlsafe(32)
                    
                    # Store token in database with expiration
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    
                    # Get user details
                    if db.use_postgres:
                        cursor.execute("SELECT display_name FROM users WHERE email = %s", (email,))
                    else:
                        cursor.execute("SELECT display_name FROM users WHERE email = ?", (email,))
                    user_data = cursor.fetchone()
                    display_name = user_data[0] if user_data else "User"
                    
                    # Store reset token (expires in 1 hour)
                    from datetime import datetime, timedelta
                    expires_at = datetime.now() + timedelta(hours=1)
                    
                    if db.use_postgres:
                        cursor.execute("""
                            INSERT INTO password_reset_tokens (email, token, expires_at, created_at)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (email) DO UPDATE SET
                            token = EXCLUDED.token,
                            expires_at = EXCLUDED.expires_at,
                            created_at = EXCLUDED.created_at
                        """, (email, reset_token, expires_at, datetime.now()))
                    else:
                        cursor.execute("""
                            INSERT OR REPLACE INTO password_reset_tokens (email, token, expires_at, created_at)
                            VALUES (?, ?, ?, ?)
                        """, (email, reset_token, expires_at, datetime.now()))
                    
                    conn.commit()
                    conn.close()
                    
                    # Send reset email
                    if not services["email"]:
                        init_email()
                    
                    if services["email"] and email_service:
                        base_url = request.host_url.rstrip('/')
                        result = email_service.send_password_reset_email(
                            email, display_name, reset_token, base_url
                        )
                        
                        if result.get("success"):
                            logger.info(f"Password reset email sent to: {email}")
                            surveillance_system.log_maintenance("PASSWORD_RESET_EMAIL_SENT", f"Reset email sent to {email}")
                        else:
                            logger.error(f"Failed to send reset email to {email}: {result.get('error')}")
                            surveillance_system.log_maintenance("PASSWORD_RESET_EMAIL_FAILED", f"Failed to send reset email to {email}")
                    else:
                        logger.error("Email service not available for password reset")
                        surveillance_system.log_maintenance("PASSWORD_RESET_EMAIL_SERVICE_UNAVAILABLE", f"Email service unavailable for {email}")
                    
                    return jsonify({
                        "success": True, 
                        "message": "If an account with that email exists, password reset instructions have been sent."
                    })
                    
                except Exception as e:
                    logger.error(f"Password reset token generation failed: {e}")
                    return jsonify({
                        "success": False, 
                        "message": "Failed to process reset request. Please try again."
                    }), 500
            else:
                # Don't reveal if email exists or not for security
                return jsonify({
                    "success": True, 
                    "message": "If an account with that email exists, password reset instructions have been sent."
                })
        else:
            return jsonify({"success": False, "message": "Service temporarily unavailable"}), 503
            
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        return jsonify({"success": False, "message": "Reset request failed"}), 500

@app.route("/auth/reset-password", methods=["GET", "POST"])
def reset_password():
    """Handle password reset with token"""
    if request.method == "GET":
        token = request.args.get("token")
        if not token:
            return redirect("/auth/forgot-password")
        
        # Verify token exists and is not expired
        if not services["database"]:
            init_database()
        
        if services["database"] and db:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if db.use_postgres:
                cursor.execute("""
                    SELECT email, expires_at FROM password_reset_tokens 
                    WHERE token = %s AND expires_at > NOW()
                """, (token,))
            else:
                cursor.execute("""
                    SELECT email, expires_at FROM password_reset_tokens 
                    WHERE token = ? AND expires_at > DATETIME('now')
                """, (token,))
            
            token_data = cursor.fetchone()
            conn.close()
            
            if not token_data:
                return """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Invalid Reset Link - SoulBridge AI</title>
                    <style>
                        body { 
                            font-family: system-ui, -apple-system, sans-serif; 
                            padding: 40px 20px; 
                            background: linear-gradient(135deg, #000000 0%, #0f172a 50%, #1e293b 100%); 
                            color: #e2e8f0; 
                            min-height: 100vh;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            margin: 0;
                        }
                        .container {
                            max-width: 500px;
                            text-align: center;
                            background: rgba(0,0,0,0.8);
                            padding: 3rem;
                            border-radius: 16px;
                            border: 2px solid #ef4444;
                            backdrop-filter: blur(15px);
                        }
                        h1 { color: #ef4444; margin-bottom: 1.5rem; }
                        .btn { 
                            display: inline-block;
                            margin-top: 2rem;
                            padding: 12px 24px;
                            background: #22d3ee;
                            color: #000;
                            text-decoration: none;
                            border-radius: 8px;
                            font-weight: 600;
                            transition: all 0.3s ease;
                        }
                        .btn:hover { background: #06b6d4; transform: translateY(-2px); }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>⚠️ Invalid or Expired Link</h1>
                        <p>This password reset link is invalid or has expired.</p>
                        <p>Reset links expire after 1 hour for security.</p>
                        <a href="/auth/forgot-password" class="btn">Request New Reset Link</a>
                    </div>
                </body>
                </html>
                """
            
            email = token_data[0]
            
            return f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Set New Password - SoulBridge AI</title>
                <style>
                    body {{ 
                        font-family: system-ui, -apple-system, sans-serif; 
                        padding: 40px 20px; 
                        background: linear-gradient(135deg, #000000 0%, #0f172a 50%, #1e293b 100%); 
                        color: #e2e8f0; 
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0;
                    }}
                    .container {{
                        max-width: 500px;
                        background: rgba(0,0,0,0.8);
                        padding: 3rem;
                        border-radius: 16px;
                        border: 2px solid #22d3ee;
                        backdrop-filter: blur(15px);
                    }}
                    h1 {{ color: #22d3ee; margin-bottom: 1.5rem; text-align: center; }}
                    .form-group {{ margin-bottom: 1.5rem; }}
                    label {{ display: block; margin-bottom: 0.5rem; color: #22d3ee; font-weight: 600; }}
                    input {{ 
                        width: 100%; 
                        padding: 12px; 
                        border: 2px solid #374151; 
                        border-radius: 8px; 
                        background: rgba(0,0,0,0.5);
                        color: #e2e8f0;
                        font-size: 16px;
                    }}
                    input:focus {{ border-color: #22d3ee; outline: none; }}
                    .btn {{ 
                        width: 100%;
                        padding: 12px 24px;
                        background: #22d3ee;
                        color: #000;
                        border: none;
                        border-radius: 8px;
                        font-weight: 600;
                        font-size: 16px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    }}
                    .btn:hover {{ background: #06b6d4; transform: translateY(-2px); }}
                    .btn:disabled {{ background: #374151; cursor: not-allowed; }}
                    .message {{ padding: 1rem; margin: 1rem 0; border-radius: 8px; text-align: center; }}
                    .error {{ background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; color: #fca5a5; }}
                    .success {{ background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; color: #6ee7b7; }}
                    .password-requirements {{
                        font-size: 14px;
                        color: #94a3b8;
                        margin-top: 0.5rem;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔐 Set New Password</h1>
                    <p style="text-align: center; margin-bottom: 2rem; color: #94a3b8;">
                        Setting password for: <strong style="color: #22d3ee;">{email}</strong>
                    </p>
                    <form id="resetForm">
                        <input type="hidden" id="token" value="{token}">
                        <div class="form-group">
                            <label for="password">New Password</label>
                            <input type="password" id="password" name="password" required 
                                   placeholder="Enter new password" minlength="8">
                            <div class="password-requirements">
                                Password must be at least 8 characters long
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="confirmPassword">Confirm Password</label>
                            <input type="password" id="confirmPassword" name="confirmPassword" required 
                                   placeholder="Confirm new password">
                        </div>
                        <button type="submit" class="btn" id="resetBtn">Update Password</button>
                    </form>
                    
                    <script>
                    document.getElementById('resetForm').addEventListener('submit', async function(e) {{
                        e.preventDefault();
                        const btn = document.getElementById('resetBtn');
                        const password = document.getElementById('password').value;
                        const confirmPassword = document.getElementById('confirmPassword').value;
                        const token = document.getElementById('token').value;
                        
                        // Clear any existing messages
                        const existingMessages = document.querySelectorAll('.message');
                        existingMessages.forEach(msg => msg.remove());
                        
                        if (password !== confirmPassword) {{
                            const message = document.createElement('div');
                            message.className = 'message error';
                            message.textContent = 'Passwords do not match';
                            document.querySelector('.container').insertBefore(message, document.getElementById('resetForm'));
                            return;
                        }}
                        
                        if (password.length < 8) {{
                            const message = document.createElement('div');
                            message.className = 'message error';
                            message.textContent = 'Password must be at least 8 characters long';
                            document.querySelector('.container').insertBefore(message, document.getElementById('resetForm'));
                            return;
                        }}
                        
                        btn.disabled = true;
                        btn.textContent = 'Updating...';
                        
                        try {{
                            const response = await fetch('/auth/reset-password', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{ token, password }})
                            }});
                            
                            const data = await response.json();
                            
                            const message = document.createElement('div');
                            message.className = data.success ? 'message success' : 'message error';
                            message.textContent = data.message;
                            
                            document.querySelector('.container').insertBefore(message, document.getElementById('resetForm'));
                            
                            if (data.success) {{
                                document.getElementById('resetForm').style.display = 'none';
                                setTimeout(() => {{
                                    window.location.href = '/login';
                                }}, 3000);
                            }}
                        }} catch (error) {{
                            const message = document.createElement('div');
                            message.className = 'message error';
                            message.textContent = 'Network error. Please try again.';
                            document.querySelector('.container').insertBefore(message, document.getElementById('resetForm'));
                        }}
                        
                        btn.disabled = false;
                        btn.textContent = 'Update Password';
                    }});
                    </script>
                </div>
            </body>
            </html>
            """
        else:
            return redirect("/auth/forgot-password")
    
    # Handle POST request (actual password update)
    try:
        data = request.get_json()
        token = data.get("token")
        new_password = data.get("password")
        
        if not token or not new_password:
            return jsonify({"success": False, "message": "Token and password required"}), 400
        
        if len(new_password) < 8:
            return jsonify({"success": False, "message": "Password must be at least 8 characters long"}), 400
        
        if not services["database"]:
            init_database()
        
        if services["database"] and db:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Verify token and get email
            if db.use_postgres:
                cursor.execute("""
                    SELECT email FROM password_reset_tokens 
                    WHERE token = %s AND expires_at > NOW()
                """, (token,))
            else:
                cursor.execute("""
                    SELECT email FROM password_reset_tokens 
                    WHERE token = ? AND expires_at > DATETIME('now')
                """, (token,))
            
            token_data = cursor.fetchone()
            
            if not token_data:
                conn.close()
                return jsonify({"success": False, "message": "Invalid or expired token"}), 400
            
            email = token_data[0]
            
            # Hash the new password
            import bcrypt
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Update user password
            if db.use_postgres:
                cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (password_hash, email))
            else:
                cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (password_hash, email))
            
            # Delete the used token
            if db.use_postgres:
                cursor.execute("DELETE FROM password_reset_tokens WHERE token = %s", (token,))
            else:
                cursor.execute("DELETE FROM password_reset_tokens WHERE token = ?", (token,))
            
            conn.commit()
            conn.close()
            
            # Log the password reset
            logger.info(f"Password reset completed for: {email}")
            surveillance_system.log_maintenance("PASSWORD_RESET_COMPLETED", f"Password updated for {email}")
            
            return jsonify({
                "success": True,
                "message": "Password updated successfully! Redirecting to login..."
            })
        else:
            return jsonify({"success": False, "message": "Service temporarily unavailable"}), 503
            
    except Exception as e:
        logger.error(f"Password reset completion error: {e}")
        return jsonify({"success": False, "message": "Failed to update password"}), 500

# ========================================
# OAUTH ROUTES
# ========================================

# Google OAuth routes removed - was causing issues

# ========================================
# ADMIN SURVEILLANCE ROUTES
# ========================================

@app.route("/admin/surveillance")
def admin_surveillance():
    """🚨 SURVEILLANCE COMMAND CENTER - Complete Security Dashboard"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        # Read all log files
        maintenance_logs = []
        threat_logs = []
        trap_logs = []
        
        try:
            with open(MAINTENANCE_LOG_FILE, "r", encoding="utf-8") as f:
                maintenance_logs = f.readlines()[-50:]
        except FileNotFoundError:
            maintenance_logs = ["No maintenance logs available yet."]
            
        try:
            with open(THREAT_LOG_FILE, "r", encoding="utf-8") as f:
                threat_logs = f.readlines()[-30:]
        except FileNotFoundError:
            threat_logs = ["No threat logs available yet."]
            
        try:
            with open(TRAP_LOG_FILE, "r", encoding="utf-8") as f:
                trap_logs = f.readlines()[-20:]
        except FileNotFoundError:
            trap_logs = ["No trap logs available yet."]
        
        # Calculate system metrics
        uptime = int((datetime.now() - surveillance_system.system_start_time).total_seconds())
        uptime_str = f"{uptime//3600}h {(uptime%3600)//60}m {uptime%60}s"
        
        # Generate comprehensive surveillance dashboard
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🚨 SoulBridge AI - SURVEILLANCE COMMAND CENTER</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Courier New', monospace; 
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    color: #e2e8f0; 
                    overflow-x: auto;
                }}
                
                .command-center {{
                    min-height: 100vh;
                    padding: 20px;
                    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="%23374151" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>') repeat;
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 3px solid #22d3ee;
                    padding-bottom: 20px;
                }}
                
                .header h1 {{
                    color: #22d3ee;
                    font-size: 2.5em;
                    text-shadow: 0 0 10px #22d3ee;
                    animation: pulse 2s infinite;
                }}
                
                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; }}
                    50% {{ opacity: 0.7; }}
                }}
                
                .status-bar {{
                    background: #1e293b;
                    border: 2px solid #374151;
                    border-radius: 10px;
                    padding: 15px;
                    margin-bottom: 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    flex-wrap: wrap;
                }}
                
                .status-indicator {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-weight: bold;
                }}
                
                .status-light {{
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    animation: blink 1.5s infinite;
                }}
                
                .green {{ background: #10b981; }}
                .red {{ background: #ef4444; }}
                .yellow {{ background: #f59e0b; }}
                
                @keyframes blink {{
                    0%, 50% {{ opacity: 1; }}
                    51%, 100% {{ opacity: 0.3; }}
                }}
                
                .grid-container {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 20px;
                }}
                
                .panel {{
                    background: rgba(30, 41, 59, 0.95);
                    border: 2px solid #374151;
                    border-radius: 10px;
                    padding: 20px;
                    backdrop-filter: blur(10px);
                }}
                
                .panel h2 {{
                    color: #22d3ee;
                    margin-bottom: 15px;
                    border-bottom: 1px solid #374151;
                    padding-bottom: 10px;
                }}
                
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 20px;
                }}
                
                .metric-card {{
                    background: #374151;
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 4px solid #22d3ee;
                    text-align: center;
                }}
                
                .metric-value {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #22d3ee;
                }}
                
                .metric-label {{
                    font-size: 0.9em;
                    color: #94a3b8;
                    margin-top: 5px;
                }}
                
                .log-container {{
                    max-height: 300px;
                    overflow-y: auto;
                    background: #0f172a;
                    border: 1px solid #374151;
                    border-radius: 5px;
                    padding: 10px;
                    font-family: 'Courier New', monospace;
                    font-size: 11px;
                }}
                
                .log-entry {{
                    padding: 3px 0;
                    border-bottom: 1px solid #1e293b;
                    word-wrap: break-word;
                }}
                
                .threat {{ color: #ef4444; background: rgba(239, 68, 68, 0.1); }}
                .warning {{ color: #f59e0b; background: rgba(245, 158, 11, 0.1); }}
                .info {{ color: #10b981; background: rgba(16, 185, 129, 0.1); }}
                .honeypot {{ color: #f59e0b; background: rgba(245, 158, 11, 0.2); border-left: 3px solid #f59e0b; }}
                
                .controls {{
                    text-align: center;
                    margin: 20px 0;
                }}
                
                .control-btn {{
                    background: #374151;
                    color: #22d3ee;
                    border: 2px solid #22d3ee;
                    padding: 10px 20px;
                    margin: 0 10px;
                    border-radius: 5px;
                    text-decoration: none;
                    display: inline-block;
                    transition: all 0.3s;
                }}
                
                .control-btn:hover {{
                    background: #22d3ee;
                    color: #0f172a;
                }}
                
                @media (max-width: 768px) {{
                    .grid-container {{ grid-template-columns: 1fr; }}
                    .metrics-grid {{ grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }}
                    .status-bar {{ flex-direction: column; gap: 10px; }}
                }}
            </style>
        </head>
        <body>
            <div class="command-center">
                <div class="header">
                    <h1>🚨 SURVEILLANCE COMMAND CENTER</h1>
                    <p>SoulBridge AI Security Operations Center</p>
                </div>
                
                <div class="status-bar">
                    <div class="status-indicator">
                        <div class="status-light green"></div>
                        WATCHDOG: ACTIVE
                    </div>
                    <div class="status-indicator">
                        <div class="status-light {'green' if not surveillance_system.emergency_mode else 'red'}"></div>
                        SYSTEM: {'NORMAL' if not surveillance_system.emergency_mode else 'EMERGENCY'}
                    </div>
                    <div class="status-indicator">
                        <div class="status-light {'yellow' if len(surveillance_system.blocked_ips) > 0 else 'green'}"></div>
                        THREATS: {'DETECTED' if len(surveillance_system.blocked_ips) > 0 else 'CLEAR'}
                    </div>
                    <div class="status-indicator">
                        UPTIME: {uptime_str}
                    </div>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{len(surveillance_system.blocked_ips)}</div>
                        <div class="metric-label">🚫 BLOCKED IPs</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{len(surveillance_system.security_threats)}</div>
                        <div class="metric-label">⚠️ TOTAL THREATS</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{len(maintenance_logs)}</div>
                        <div class="metric-label">🔧 MAINTENANCE LOGS</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{surveillance_system.critical_errors_count}</div>
                        <div class="metric-label">🔥 CRITICAL ERRORS</div>
                    </div>
                </div>
                
                <div class="controls">
                    <a href="/admin/surveillance?key={ADMIN_DASH_KEY}" class="control-btn">🔄 REFRESH</a>
                    <a href="/health" class="control-btn">💓 HEALTH CHECK</a>
                </div>
                
                <div class="grid-container">
                    <div class="panel">
                        <h2>🔧 MAINTENANCE LOG</h2>
                        <div class="log-container">
                            {''.join([f'<div class="log-entry info">{log.strip()}</div>' for log in maintenance_logs[-30:]])}
                        </div>
                    </div>
                    
                    <div class="panel">
                        <h2>🚨 THREAT LOG</h2>
                        <div class="log-container">
                            {''.join([f'<div class="log-entry threat">{log.strip()}</div>' for log in threat_logs[-20:]])}
                        </div>
                    </div>
                </div>
                
                <div class="panel">
                    <h2>🛡️ BLOCKED IP ADDRESSES</h2>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px; padding: 10px;">
                        {' '.join([f'<span style="background: #374151; padding: 5px 10px; border-radius: 3px; font-family: monospace; color: #ef4444;">{ip}</span>' for ip in list(surveillance_system.blocked_ips)[-20:]]) if surveillance_system.blocked_ips else '<span style="color: #10b981;">✅ No blocked IPs - System secure</span>'}
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding: 20px; background: rgba(30, 41, 59, 0.5); border-radius: 10px;">
                    <p style="color: #94a3b8; font-size: 0.9em;">
                        🔒 SoulBridge AI Security System - Real-time monitoring active<br>
                        System uptime: {uptime_str} | Last refresh: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    </p>
                </div>
            </div>
            
            <script>
                // Auto-refresh every 30 seconds
                setTimeout(function() {{
                    window.location.reload();
                }}, 30000);
            </script>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        logger.error(f"Surveillance dashboard error: {e}")
        return jsonify({"error": "Surveillance system error", "details": str(e)}), 500

# ========================================
# API ROUTES
# ========================================

@app.route("/api/select-plan", methods=["POST"])
def select_plan():
    """Plan selection API"""
    try:
        logger.info(f"Plan selection request - Session data: {dict(session)}")
        if not is_logged_in():
            logger.error(f"Plan selection failed - User not authenticated. Session: {dict(session)}")
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
        session.permanent = False  # Session expires when browser closes
        
        logger.info(f"Plan selected: {plan_type} by {session.get('user_email')}")
        logger.info(f"Session after plan selection: {dict(session)}")
        
        # Create appropriate success message and redirect
        if plan_type == "foundation":
            message = "Welcome to SoulBridge AI! Your free plan is now active."
            # Redirect back to subscription page with success message
            redirect_url = "/subscription?plan_selected=foundation"
        else:
            plan_names = {"premium": "Growth", "enterprise": "Transformation"}
            plan_display = plan_names.get(plan_type, plan_type.title())
            message = f"Great choice! {plan_display} plan selected. Complete payment to activate premium features."
            # Redirect paid plan users to real payment processing
            redirect_url = f"/payment?plan={plan_type}"
        
        return jsonify({
            "success": True,
            "plan": plan_type,
            "message": message,
            "redirect": redirect_url
        })
    except Exception as e:
        logger.error(f"Plan selection error: {e}")
        return jsonify({"success": False, "error": "Plan selection failed"}), 500

@app.route("/payment")
def payment_page():
    """Payment setup page with real Stripe integration"""
    try:
        if not is_logged_in():
            return redirect("/login")
        
        plan = request.args.get("plan", "premium")
        if plan not in VALID_PLANS or plan == "foundation":
            return redirect("/subscription")
            
        plan_names = {"premium": "Growth", "enterprise": "Transformation"}
        plan_display = plan_names.get(plan, plan.title())
        
        # Prices in cents
        plan_prices = {
            "premium": 1299,  # $12.99
            "enterprise": 1999  # $19.99
        }
        
        price_cents = plan_prices.get(plan, 1299)
        price_display = f"${price_cents / 100:.2f}"
        
        return render_template("payment.html", 
                             plan=plan,
                             plan_display=plan_display,
                             price_display=price_display)
    except Exception as e:
        logger.error(f"Payment page error: {e}")
        return redirect("/subscription")

@app.route("/api/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """Create Stripe checkout session for plan subscription"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
            
        plan_type = data.get("plan_type")
        if plan_type not in ["premium", "enterprise"]:
            return jsonify({"success": False, "error": "Invalid plan type"}), 400
        
        # Check if Stripe is configured
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")
        if not stripe_secret_key:
            logger.warning("Stripe secret key not configured")
            return jsonify({
                "success": False, 
                "error": "Payment processing is being configured. Please try again later.",
                "debug": "STRIPE_SECRET_KEY not set"
            }), 503
        
        logger.info(f"Creating Stripe checkout for {plan_type} plan")
        
        import stripe
        stripe.api_key = stripe_secret_key
        
        # Plan details
        plan_names = {"premium": "Growth Plan", "enterprise": "Transformation Plan"}
        plan_prices = {"premium": 1299, "enterprise": 1999}  # Prices in cents
        
        plan_name = plan_names[plan_type]
        price_cents = plan_prices[plan_type]
        
        user_email = session.get("user_email")
        
        try:
            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=user_email,
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'SoulBridge AI - {plan_name}',
                            'description': f'Monthly subscription to {plan_name}',
                        },
                        'unit_amount': price_cents,
                        'recurring': {
                            'interval': 'month'
                        }
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{request.host_url}payment/success?session_id={{CHECKOUT_SESSION_ID}}&plan={plan_type}",
                cancel_url=f"{request.host_url}payment/cancel?plan={plan_type}",
                metadata={
                    'plan_type': plan_type,
                    'user_email': user_email
                }
            )
            
            logger.info(f"Stripe checkout created for {user_email}: {plan_type}")
            
            return jsonify({
                "success": True,
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id
            })
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return jsonify({
                "success": False,
                "error": "Payment system error. Please try again."
            }), 500
        
    except Exception as e:
        logger.error(f"Checkout session error: {e}")
        return jsonify({"success": False, "error": "Checkout failed"}), 500

@app.route("/api/create-addon-checkout", methods=["POST"])
def create_addon_checkout():
    """Create checkout session for add-ons"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
            
        addon_type = data.get("addon_type")
        
        # Add-ons will use same Stripe integration
        logger.info(f"Add-on checkout requested: {addon_type} by {session.get('user_email')}")
        return jsonify({
            "success": False, 
            "error": "Add-on payments coming soon! Focus on main plans for now."
        }), 503
        
    except Exception as e:
        logger.error(f"Add-on checkout error: {e}")
        return jsonify({"success": False, "error": "Checkout failed"}), 500

@app.route("/payment/success")
def payment_success():
    """Handle successful payment"""
    try:
        if not is_logged_in():
            return redirect("/login")
            
        session_id = request.args.get("session_id")
        plan_type = request.args.get("plan")
        
        if not session_id or not plan_type:
            return redirect("/subscription?error=invalid_payment")
        
        # Verify payment with Stripe
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")
        if stripe_secret_key:
            import stripe
            stripe.api_key = stripe_secret_key
            
            try:
                checkout_session = stripe.checkout.Session.retrieve(session_id)
                if checkout_session.payment_status == "paid":
                    # Update user plan in session and database
                    session["user_plan"] = plan_type
                    user_email = session.get("user_email")
                    
                    # Store subscription in database
                    if services["database"] and db:
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        
                        # Insert or update subscription
                        cursor.execute("""
                            INSERT OR REPLACE INTO subscriptions 
                            (user_id, email, plan_type, status, stripe_subscription_id)
                            VALUES ((SELECT id FROM users WHERE email = ?), ?, ?, 'active', ?)
                        """, (user_email, user_email, plan_type, checkout_session.subscription))
                        
                        # Log payment event
                        cursor.execute("""
                            INSERT INTO payment_events 
                            (email, event_type, plan_type, amount, stripe_event_id)
                            VALUES (?, 'payment_success', ?, ?, ?)
                        """, (user_email, plan_type, checkout_session.amount_total / 100, session_id))
                        
                        conn.commit()
                        conn.close()
                    
                    logger.info(f"Payment successful: {user_email} upgraded to {plan_type}")
                    
                    # Redirect to app with premium access
                    return redirect("/?payment_success=true&plan=" + plan_type)
                    
            except Exception as e:
                logger.error(f"Payment verification error: {e}")
        
        # Fallback - redirect to subscription page with error
        return redirect("/subscription?error=payment_verification")
        
    except Exception as e:
        logger.error(f"Payment success handler error: {e}")
        return redirect("/subscription?error=payment_error")

@app.route("/payment/cancel")  
def payment_cancel():
    """Handle cancelled payment"""
    try:
        plan_type = request.args.get("plan", "premium")
        logger.info(f"Payment cancelled for plan: {plan_type}")
        return redirect(f"/subscription?cancelled=true&plan={plan_type}")
    except Exception as e:
        logger.error(f"Payment cancel handler error: {e}")
        return redirect("/subscription")

@app.route("/api/user-addons")
def get_user_addons():
    """Get user's active add-ons"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        # For now, return empty add-ons since payment isn't set up
        return jsonify({
            "success": True,
            "active_addons": []
        })
        
    except Exception as e:
        logger.error(f"User addons error: {e}")
        return jsonify({"success": False, "error": "Failed to fetch add-ons"}), 500

@app.route("/emergency-user-create", methods=["GET", "POST"])
def emergency_user_create():
    """Emergency endpoint to recreate user account"""
    try:
        if request.method == "GET":
            return """
            <html><head><title>Emergency User Creation</title></head>
            <body style="font-family: Arial; padding: 40px; background: #0f172a; color: #e2e8f0;">
                <h1 style="color: #22d3ee;">Emergency User Creation</h1>
                <form method="POST" style="max-width: 400px;">
                    <p>Create user account when database issues occur:</p>
                    <input type="email" name="email" placeholder="Email" required 
                           style="width: 100%; padding: 10px; margin: 10px 0; background: #1e293b; color: #e2e8f0; border: 1px solid #22d3ee; border-radius: 5px;">
                    <input type="password" name="password" placeholder="Password" required
                           style="width: 100%; padding: 10px; margin: 10px 0; background: #1e293b; color: #e2e8f0; border: 1px solid #22d3ee; border-radius: 5px;">
                    <input type="text" name="display_name" placeholder="Display Name" required
                           style="width: 100%; padding: 10px; margin: 10px 0; background: #1e293b; color: #e2e8f0; border: 1px solid #22d3ee; border-radius: 5px;">
                    <button type="submit" style="width: 100%; padding: 12px; background: #22d3ee; color: #000; border: none; border-radius: 5px; font-weight: bold;">Create User</button>
                </form>
            </body></html>
            """
        
        # POST - create user
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        display_name = request.form.get("display_name", "").strip()
        
        if not email or not password or not display_name:
            return "All fields required", 400
            
        # Initialize database if needed
        if not services["database"]:
            init_database()
            
        if services["database"] and db:
            from auth import User
            user = User(db)
            
            try:
                # Create user
                user_id = user.create_user(email, password, display_name)
                
                # Auto-login
                setup_user_session(email, user_id=user_id)
                
                logger.info(f"Emergency user created: {email}")
                return f"""
                <html><head><title>Success</title></head>
                <body style="font-family: Arial; padding: 40px; background: #0f172a; color: #e2e8f0; text-align: center;">
                    <h1 style="color: #10b981;">Success!</h1>
                    <p>User account created and logged in.</p>
                    <a href="/" style="display: inline-block; margin-top: 20px; padding: 12px 24px; background: #22d3ee; color: #000; text-decoration: none; border-radius: 8px; font-weight: bold;">Go to App</a>
                </body></html>
                """
                
            except Exception as e:
                logger.error(f"Emergency user creation failed: {e}")
                return f"User creation failed: {e}", 500
        else:
            return "Database not available", 503
            
    except Exception as e:
        logger.error(f"Emergency user creation error: {e}")
        return f"Error: {e}", 500

@app.route("/api/recover-subscription", methods=["POST"])
def recover_subscription():
    """Recover subscription for users who lost database access"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        data = request.get_json()
        email = session.get("user_email")
        
        if not email:
            return jsonify({"success": False, "error": "No email in session"}), 400
            
        # Initialize database
        if not services["database"]:
            init_database()
            
        if services["database"] and db:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Check for existing subscription records by email
            cursor.execute(
                "SELECT plan_type, status, stripe_customer_id FROM subscriptions WHERE email = ? AND status = 'active'",
                (email,)
            )
            subscription = cursor.fetchone()
            
            if subscription:
                plan_type, status, stripe_customer_id = subscription
                session["user_plan"] = plan_type
                logger.info(f"Subscription recovered for {email}: {plan_type}")
                
                conn.close()
                return jsonify({
                    "success": True,
                    "message": f"Subscription recovered! Your {plan_type} plan is active.",
                    "plan": plan_type
                })
            else:
                conn.close()
                return jsonify({
                    "success": False,
                    "message": "No active subscription found. Contact support if you believe this is an error."
                })
        else:
            return jsonify({"success": False, "error": "Database unavailable"}), 503
            
    except Exception as e:
        logger.error(f"Subscription recovery error: {e}")
        return jsonify({"success": False, "error": "Recovery failed"}), 500

@app.route("/api/backup-database", methods=["POST"])
def backup_database():
    """Create database backup (admin only)"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        # Only allow admin users
        if not session.get("is_admin"):
            return jsonify({"success": False, "error": "Admin access required"}), 403
            
        if not services["database"]:
            init_database()
            
        if services["database"] and db:
            backup_path = db.backup_database()
            json_backup = db.export_users_to_json()
            
            return jsonify({
                "success": True,
                "backup_path": backup_path,
                "user_count": len(json_backup["users"]) if json_backup else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            return jsonify({"success": False, "error": "Database unavailable"}), 503
            
    except Exception as e:
        logger.error(f"Database backup error: {e}")
        return jsonify({"success": False, "error": "Backup failed"}), 500

@app.route("/debug", methods=["GET"])
def debug_info():
    """Simple debug endpoint to test routing"""
    # Check database configuration
    database_url = os.environ.get("DATABASE_URL")
    postgres_url = os.environ.get("POSTGRES_URL") 
    railway_env = os.environ.get("RAILWAY_ENVIRONMENT")
    
    # Initialize database to check what's being used
    if not services["database"]:
        init_database()
    
    db_info = "Unknown"
    if services["database"] and db:
        if hasattr(db, 'use_postgres'):
            if db.use_postgres:
                db_info = f"PostgreSQL - {db.postgres_url[:50]}..." if db.postgres_url else "PostgreSQL (no URL)"
            else:
                db_info = f"SQLite - {db.db_path}"
        else:
            db_info = "Database object missing postgres info"
    
    return jsonify({
        "status": "API routing working",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": railway_env,
        "database_url_present": bool(database_url),
        "postgres_url_present": bool(postgres_url),
        "database_url_preview": database_url[:30] + "..." if database_url else None,
        "postgres_url_preview": postgres_url[:30] + "..." if postgres_url else None,
        "current_database": db_info,
        "services_database": bool(services["database"])
    })

@app.route("/stripe-status", methods=["GET"])
def stripe_status():
    """Check Stripe configuration status - public endpoint for debugging"""
    try:
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")
        stripe_publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY")
        
        return jsonify({
            "success": True,
            "stripe_secret_configured": bool(stripe_secret_key),
            "stripe_publishable_configured": bool(stripe_publishable_key),
            "secret_key_preview": stripe_secret_key[:12] + "..." if stripe_secret_key else None,
            "publishable_key_preview": stripe_publishable_key[:12] + "..." if stripe_publishable_key else None,
            "environment": os.environ.get("RAILWAY_ENVIRONMENT", "development"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Stripe status error: {e}")
        return jsonify({
            "success": False, 
            "error": "Status check failed",
            "exception": str(e)
        }), 500

@app.route("/api/test-stripe", methods=["POST"])
def test_stripe():
    """Test Stripe connectivity (admin only)"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        # Only allow admin users
        if not session.get("is_admin"):
            return jsonify({"success": False, "error": "Admin access required"}), 403
            
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")
        if not stripe_secret_key:
            return jsonify({
                "success": False, 
                "error": "STRIPE_SECRET_KEY not configured"
            })
        
        import stripe
        stripe.api_key = stripe_secret_key
        
        # Test API call to verify connectivity
        try:
            # List first few payment methods to test API
            test_result = stripe.PaymentMethod.list(limit=1)
            
            return jsonify({
                "success": True,
                "message": "Stripe API connectivity verified",
                "stripe_connected": True,
                "api_version": stripe.api_version,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API test failed: {e}")
            return jsonify({
                "success": False,
                "error": f"Stripe API error: {str(e)}",
                "stripe_connected": False
            })
        
    except Exception as e:
        logger.error(f"Stripe test error: {e}")
        return jsonify({"success": False, "error": "Test failed"}), 500

@app.route("/api/database-status", methods=["GET"])
def database_status():
    """Get database status and health"""
    try:
        if not services["database"]:
            init_database()
            
        if services["database"] and db:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get user count
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            # Get subscription count  
            cursor.execute("SELECT COUNT(*) FROM subscriptions")
            subscription_count = cursor.fetchone()[0]
            
            conn.close()
            
            db_info = {
                "success": True,
                "user_count": user_count,
                "subscription_count": subscription_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "database_type": "PostgreSQL" if db.use_postgres else "SQLite"
            }
            
            if db.use_postgres:
                db_info["postgres_url_masked"] = db.postgres_url[:30] + "..." if db.postgres_url else None
            else:
                db_info["database_path"] = db.db_path
                db_info["database_exists"] = os.path.exists(db.db_path)
            
            return jsonify(db_info)
        else:
            return jsonify({
                "success": False, 
                "error": "Database unavailable",
                "services_database": bool(services["database"]),
                "db_object": bool(db)
            }), 503
            
    except Exception as e:
        logger.error(f"Database status error: {e}")
        return jsonify({
            "success": False, 
            "error": "Status check failed",
            "error_details": str(e),
            "error_type": type(e).__name__
        }), 500

@app.route("/api/database-reconnect", methods=["POST"])
def database_reconnect():
    """Force reconnect to database - admin only"""
    try:
        if not is_logged_in() or not session.get("is_admin"):
            return jsonify({"success": False, "error": "Admin access required"}), 403
        
        global db, services
        
        # Clear current database connection
        db = None
        services["database"] = None
        
        # Force reinitialize
        success = init_database()
        
        if success:
            return jsonify({
                "success": True,
                "message": "Database reconnected successfully",
                "database_type": "PostgreSQL" if db.use_postgres else "SQLite"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Database reconnection failed"
            }), 500
            
    except Exception as e:
        logger.error(f"Database reconnect error: {e}")
        return jsonify({
            "success": False,
            "error": "Reconnection failed",
            "details": str(e)
        }), 500

@app.route("/admin/database")
def database_admin():
    """Database administration interface - admin only"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    # For database admin, allow direct key access without login requirement
    # This bypasses the normal admin session check since you have the admin key
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🗄️ Database Admin - SoulBridge AI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Courier New', monospace; 
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: #e2e8f0; 
                padding: 20px;
            }
            
            .admin-header {
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 3px solid #22d3ee;
                padding-bottom: 20px;
            }
            
            .admin-header h1 {
                color: #22d3ee;
                font-size: 2.5em;
                text-shadow: 0 0 10px #22d3ee;
            }
            
            .query-container {
                background: rgba(30, 41, 59, 0.95);
                border: 2px solid #374151;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .query-textarea {
                width: 100%;
                height: 200px;
                background: #0f172a;
                border: 1px solid #374151;
                border-radius: 5px;
                color: #e2e8f0;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                padding: 15px;
                resize: vertical;
            }
            
            .btn {
                background: #22d3ee;
                color: #0f172a;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                margin: 5px;
                transition: all 0.3s;
            }
            
            .btn:hover {
                background: #06b6d4;
                transform: translateY(-2px);
            }
            
            .btn-danger {
                background: #ef4444;
                color: white;
            }
            
            .btn-danger:hover {
                background: #dc2626;
            }
            
            .results-container {
                background: #0f172a;
                border: 1px solid #374151;
                border-radius: 5px;
                padding: 15px;
                margin-top: 20px;
                max-height: 400px;
                overflow-y: auto;
            }
            
            .results-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
            }
            
            .results-table th, .results-table td {
                border: 1px solid #374151;
                padding: 8px;
                text-align: left;
            }
            
            .results-table th {
                background: #374151;
                color: #22d3ee;
                font-weight: bold;
            }
            
            .quick-queries {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                margin: 20px 0;
            }
            
            .error { color: #ef4444; }
            .success { color: #10b981; }
            
            pre {
                background: #1e293b;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                white-space: pre-wrap;
            }
        </style>
    </head>
    <body>
        <div class="admin-header">
            <h1>🗄️ DATABASE ADMIN</h1>
            <p>PostgreSQL Query Interface</p>
        </div>
        
        <div class="query-container">
            <h2 style="color: #22d3ee; margin-bottom: 15px;">SQL Query</h2>
            <textarea id="queryText" class="query-textarea" placeholder="Enter your SQL query here...
Example: SELECT * FROM users LIMIT 10;"></textarea>
            
            <div style="margin-top: 15px;">
                <button class="btn" onclick="executeQuery()">🔍 Execute Query</button>
                <button class="btn" onclick="clearQuery()">🧹 Clear</button>
                <button class="btn btn-danger" onclick="confirmDangerous()" style="margin-left: 20px;">⚠️ Execute Dangerous</button>
            </div>
        </div>
        
        <div class="query-container">
            <h3 style="color: #22d3ee; margin-bottom: 15px;">Quick Queries</h3>
            <div class="quick-queries">
                <button class="btn" onclick="quickQuery('SELECT * FROM users ORDER BY created_at DESC LIMIT 10;')">📋 Recent Users</button>
                <button class="btn" onclick="quickQuery('SELECT COUNT(*) as user_count FROM users;')">👥 User Count</button>
                <button class="btn" onclick="quickQuery('SELECT * FROM subscriptions ORDER BY created_at DESC LIMIT 10;')">💳 Subscriptions</button>
                <button class="btn" onclick="quickQuery('SELECT table_name FROM information_schema.tables WHERE table_schema = \\'public\\';')">📊 Show Tables</button>
                <button class="btn" onclick="quickQuery('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = \\'users\\';')">🔍 User Columns</button>
                <button class="btn" onclick="quickQuery('SELECT email, display_name, created_at FROM users WHERE created_at > NOW() - INTERVAL \\'7 days\\';')">📅 Recent 7 Days</button>
            </div>
        </div>
        
        <div id="results" class="results-container" style="display: none;">
            <h3 style="color: #22d3ee; margin-bottom: 15px;">Query Results</h3>
            <div id="resultsContent"></div>
        </div>
        
        <script>
            // Get admin key from URL params
            const urlParams = new URLSearchParams(window.location.search);
            const adminKey = urlParams.get('key') || 'soulbridge_admin_2024';
            
            function executeQuery(dangerous = false) {
                const query = document.getElementById('queryText').value.trim();
                if (!query) {
                    alert('Please enter a query');
                    return;
                }
                
                const resultsDiv = document.getElementById('results');
                const resultsContent = document.getElementById('resultsContent');
                
                resultsContent.innerHTML = '<p style="color: #f59e0b;">Executing query...</p>';
                resultsDiv.style.display = 'block';
                
                fetch(`/api/database-query?key=${adminKey}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Admin-Key': adminKey
                    },
                    body: JSON.stringify({ 
                        query: query,
                        dangerous: dangerous
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayResults(data);
                    } else {
                        resultsContent.innerHTML = `<p class="error">Error: ${data.error}</p>`;
                    }
                })
                .catch(error => {
                    resultsContent.innerHTML = `<p class="error">Network Error: ${error.message}</p>`;
                });
            }
            
            function displayResults(data) {
                const resultsContent = document.getElementById('resultsContent');
                
                if (data.rows && data.rows.length > 0) {
                    let html = `<p class="success">Query executed successfully. ${data.row_count} rows returned.</p>`;
                    
                    if (data.columns && data.columns.length > 0) {
                        html += '<table class="results-table"><thead><tr>';
                        data.columns.forEach(col => {
                            html += `<th>${col}</th>`;
                        });
                        html += '</tr></thead><tbody>';
                        
                        data.rows.forEach(row => {
                            html += '<tr>';
                            row.forEach(cell => {
                                html += `<td>${cell !== null ? String(cell) : '<i>NULL</i>'}</td>`;
                            });
                            html += '</tr>';
                        });
                        html += '</tbody></table>';
                    } else {
                        html += '<pre>' + JSON.stringify(data.rows, null, 2) + '</pre>';
                    }
                    
                    resultsContent.innerHTML = html;
                } else if (data.affected_rows !== undefined) {
                    resultsContent.innerHTML = `<p class="success">Query executed successfully. ${data.affected_rows} rows affected.</p>`;
                } else {
                    resultsContent.innerHTML = '<p class="success">Query executed successfully.</p>';
                }
            }
            
            function quickQuery(query) {
                document.getElementById('queryText').value = query;
                executeQuery();
            }
            
            function clearQuery() {
                document.getElementById('queryText').value = '';
                document.getElementById('results').style.display = 'none';
            }
            
            function confirmDangerous() {
                if (confirm('⚠️ WARNING: This will execute potentially dangerous queries (UPDATE, DELETE, DROP, etc.)\\n\\nAre you absolutely sure?')) {
                    executeQuery(true);
                }
            }
        </script>
    </body>
    </html>
    """

@app.route("/api/database-query", methods=["POST"])
def database_query():
    """Execute database query - admin only"""
    try:
        # Allow access with admin key or admin session
        admin_key = request.headers.get('X-Admin-Key') or request.args.get('key')
        has_admin_session = is_logged_in() and session.get("is_admin")
        
        if not (admin_key == ADMIN_DASH_KEY or has_admin_session):
            return jsonify({"success": False, "error": "Admin access required"}), 403
        
        data = request.get_json()
        if not data or not data.get("query"):
            return jsonify({"success": False, "error": "Query required"}), 400
        
        query = data["query"].strip()
        dangerous = data.get("dangerous", False)
        
        # Safety check for dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'CREATE']
        is_dangerous = any(keyword in query.upper() for keyword in dangerous_keywords)
        
        if is_dangerous and not dangerous:
            return jsonify({
                "success": False,
                "error": "Dangerous query detected. Use 'Execute Dangerous' button to proceed.",
                "dangerous_detected": True
            }), 400
        
        if not services["database"] or not db:
            return jsonify({"success": False, "error": "Database not available"}), 503
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Execute query
        cursor.execute(query)
        
        # Handle different types of queries
        if query.upper().strip().startswith('SELECT') or query.upper().strip().startswith('WITH'):
            # SELECT queries - fetch results
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            result = {
                "success": True,
                "rows": rows,
                "columns": columns,
                "row_count": len(rows),
                "query_type": "SELECT"
            }
        else:
            # INSERT, UPDATE, DELETE queries - get affected rows
            conn.commit()
            affected_rows = cursor.rowcount
            
            result = {
                "success": True,
                "affected_rows": affected_rows,
                "query_type": "MODIFY"
            }
        
        cursor.close()
        conn.close()
        
        # Log the query for security audit
        surveillance_system.log_maintenance("DATABASE_QUERY", f"Admin executed: {query[:100]}...")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Database query error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }), 500

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
# OAUTH ROUTES
# ========================================

@app.route("/auth/oauth/<provider>")
def oauth_login(provider):
    """Initiate OAuth login"""
    try:
        # Validate provider
        if provider != "google":
            flash("Invalid OAuth provider", "error")
            return redirect(url_for("login_page"))
        
        # Initialize database if needed
        if not services["database"]:
            init_database()
            
        if not services["database"] or not db:
            flash("Service temporarily unavailable", "error")
            return redirect(url_for("login_page"))
            
        from oauth import OAuthManager
        oauth_manager = OAuthManager(db)
        
        # Check if provider is configured
        if not oauth_manager.is_provider_configured(provider):
            flash(f"{provider.title()} sign-in is not configured", "error")
            return redirect(url_for("login_page"))
        
        # Get redirect URI - use hardcoded HTTPS URL for production
        redirect_uri = "https://soulbridgeai.com/api/oauth/callback"
        logger.info(f"🔗 OAuth redirect URI: {redirect_uri}")
        
        # Generate authorization URL
        result = oauth_manager.get_auth_url(provider, redirect_uri)
        if result["success"]:
            logger.info(f"🌐 OAuth auth URL: {result['auth_url']}")
        else:
            logger.error(f"❌ OAuth URL generation failed: {result['error']}")
        
        if result["success"]:
            return redirect(result["auth_url"])
        else:
            flash(result["error"], "error")
            return redirect(url_for("login_page"))
            
    except Exception as e:
        logger.error(f"OAuth login error for {provider}: {e}")
        flash("Authentication service error", "error")
        return redirect(url_for("login_page"))

@app.route("/api/oauth/callback")
def oauth_callback():
    """Handle OAuth callback"""
    try:
        provider = request.args.get("state", "").split("-")[0] if "-" in request.args.get("state", "") else "google"
        code = request.args.get("code")
        state = request.args.get("state")
        error = request.args.get("error")
        
        if error:
            flash(f"OAuth error: {error}", "error")
            return redirect(url_for("login_page"))
            
        if not code or not state:
            flash("Invalid OAuth callback", "error")
            return redirect(url_for("login_page"))
            
        # Initialize database if needed
        if not services["database"]:
            init_database()
            
        if not services["database"] or not db:
            flash("Service temporarily unavailable", "error")
            return redirect(url_for("login_page"))
            
        from oauth import OAuthManager
        oauth_manager = OAuthManager(db)
        
        # Get redirect URI - use hardcoded HTTPS URL for production
        redirect_uri = "https://soulbridgeai.com/api/oauth/callback"
        
        # Handle callback
        result = oauth_manager.handle_callback(provider, code, state, redirect_uri)
        
        if result["success"]:
            user = result["user"]
            
            # Setup user session
            setup_user_session(
                email=user["email"],
                user_id=user["id"]
            )
            
            if result.get("is_new_user"):
                flash(f"Welcome! Your account has been created using {provider.title()}.", "success")
            else:
                flash(f"Welcome back! Signed in with {provider.title()}.", "success")
                
            return redirect(url_for("profile"))
        else:
            flash(result["error"], "error")
            return redirect(url_for("login_page"))
            
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        flash("Authentication failed", "error")
        return redirect(url_for("login_page"))

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
    
    # Use regular Flask for stability (SocketIO available but not used for startup)
    logger.info("Using regular Flask server for stability")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True, use_reloader=False)