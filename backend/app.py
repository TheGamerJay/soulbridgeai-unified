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
import json
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

# Simple session configuration
app.config['SESSION_COOKIE_DOMAIN'] = '.soulbridgeai.com' if os.environ.get('RAILWAY_ENVIRONMENT') else None  # Cross-subdomain sessions

# Ensure sessions expire when browser closes
@app.before_request
def make_session_non_permanent():
    session.permanent = False

@app.before_request
def reset_session_if_cookie_missing():
    # If no session cookie, make sure user is not treated as logged in
    if not request.cookies.get('session'):
        session.clear()

# Prevent caching to force fresh login checks
@app.after_request
def prevent_caching(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

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
    """Check if user is logged in with strict banking-style session timeout"""
    try:
        # BANKING SECURITY: Force clear all sessions created before security upgrade
        REQUIRED_SESSION_VERSION = "2025-07-28-banking-security"
        if session.get('session_version') != REQUIRED_SESSION_VERSION:
            logger.info("SECURITY: Clearing old session - banking security upgrade")
            session.clear()
            return False
        
        if not session.get("user_authenticated", False):
            return False
        
        # Also check for user_id or user_email as backup validation
        if not session.get('user_id') and not session.get('user_email') and not session.get('email'):
            return False
        
        # No automatic timeout - session lasts until browser is closed
        # Just update the last activity timestamp for logging purposes
        
        # Update last activity time
        session['last_activity'] = datetime.now().isoformat()
        return True
        
    except Exception as e:
        # Any unexpected error should not clear session unless necessary
        logger.error(f"Session validation error: {e}")
        # Only clear if critical fields are missing
        if not session.get("user_authenticated") and not session.get('user_id'):
            session.clear()
            return False
        return True

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
    """Setup user session with security measures and companion data restoration"""
    # Security: Clear and regenerate session to prevent fixation attacks
    session.clear()
    # Session expires when browser closes
    session["user_authenticated"] = True
    session["session_version"] = "2025-07-28-banking-security"  # Required for auth
    session["user_email"] = email
    session["login_timestamp"] = datetime.now().isoformat()
    session["user_plan"] = "foundation"
    if user_id:
        session["user_id"] = user_id
    if is_admin:
        session["is_admin"] = True
    if dev_mode:
        session["dev_mode"] = True
    
    # Restore companion data if available
    if user_id:
        restore_companion_data(user_id)

def restore_companion_data(user_id):
    """Restore companion and trial data from persistence file"""
    import json
    persistence_file = f"logs/user_companion_{user_id}.json"
    try:
        with open(persistence_file, 'r') as f:
            companion_data = json.load(f)
            
        # Restore companion selection
        if companion_data.get('selected_companion'):
            session['selected_companion'] = companion_data['selected_companion']
            session['companion_selected_at'] = companion_data.get('companion_selected_at')
            session['first_companion_picked'] = companion_data.get('first_companion_picked', False)
            
        # Always restore trial_used_permanently flag regardless of trial status
        if companion_data.get('trial_used_permanently'):
            session['trial_used_permanently'] = True
            logger.info(f"PERSISTENCE: User {user_id} has permanently used their trial")
        
        # Restore trial data if still valid
        trial_expires = companion_data.get('trial_expires')
        if trial_expires and companion_data.get('trial_active'):
            from datetime import datetime
            try:
                expiry_time = datetime.fromisoformat(trial_expires)
                if datetime.now() < expiry_time:
                    # Trial is still valid
                    session['trial_companion'] = companion_data.get('trial_companion')
                    session['trial_expires'] = trial_expires
                    session['trial_active'] = True
                    session['user_plan'] = 'trial'
                    logger.info(f"PERSISTENCE: Restored valid trial for user {user_id}")
                else:
                    logger.info(f"PERSISTENCE: Trial expired for user {user_id}")
            except ValueError:
                logger.warning(f"Invalid trial expiry format for user {user_id}")
                
        logger.info(f"PERSISTENCE: Restored companion data for user {user_id}")
        
    except FileNotFoundError:
        logger.info(f"PERSISTENCE: No companion data found for user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to restore companion data for user {user_id}: {e}")

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
    """Initialize database with error handling and thread safety - LAZY LOADING"""
    global db
    with _service_lock:
        # Double-check pattern with lock
        if services["database"] and db:
            return True
            
        try:
            logger.info("Skipping database initialization at startup (will initialize on first request)")
            # Don't initialize at startup - wait for first request
            # This avoids Flask context issues during app startup
            services["database"] = "lazy_init"  # Mark as lazy
            logger.info("✅ Database marked for lazy initialization")
            return True
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            # Ensure consistent failure state
            db = None
            services["database"] = None
            return False

def get_database():
    """Get database instance, initializing if needed"""
    global db
    if db is None and services.get("database") == "lazy_init":
        try:
            from auth import Database
            db = Database()
            # Test connection
            temp_conn = db.get_connection()
            temp_conn.close()
            services["database"] = db
            logger.info("✅ Database lazy initialization successful")
        except Exception as e:
            logger.error(f"❌ Database lazy initialization failed: {e}")
            db = None
            services["database"] = None
    return db

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
    """Home route - redirect based on authentication status"""
    try:
        # Check if user is logged in
        if is_logged_in():
            logger.info(f"🏠 HOME ROUTE: User authenticated, redirecting to intro")
            return redirect("/intro")
        else:
            logger.info(f"🏠 HOME ROUTE: User not authenticated, redirecting to login")
            return redirect("/login")
        
    except Exception as e:
        logger.error(f"Home route error: {e}")
        return redirect("/login")

# ========================================
# AUTHENTICATION ROUTES
# ========================================

@app.route("/login")
def login_page():
    """Login page - always show login form when accessed directly"""
    try:
        # Always show the login page when accessed directly
        # Users should be able to access /login even if already logged in
        clerk_publishable_key = os.environ.get("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
        return render_template("login.html", clerk_publishable_key=clerk_publishable_key)
    except Exception as e:
        logger.error(f"Login template error: {e}")
        return jsonify({"error": "Login page temporarily unavailable"}), 200

@app.route("/test-login")
def test_login_page():
    """Simple test login page without JavaScript"""
    return render_template("test-login.html")

@app.route("/debug/test-user")
def debug_test_user():
    """Debug endpoint to test if user exists"""
    try:
        from auth import Database
        from simple_auth import SimpleAuth
        import os
        
        # Check environment variables
        env_info = {
            "PGHOST": os.environ.get("PGHOST", "NOT_SET"),
            "PGPORT": os.environ.get("PGPORT", "NOT_SET"),
            "PGUSER": os.environ.get("PGUSER", "NOT_SET"),
            "PGPASSWORD": "SET" if os.environ.get("PGPASSWORD") else "NOT_SET",
            "PGDATABASE": os.environ.get("PGDATABASE", "NOT_SET"),
            "DATABASE_URL": "SET" if os.environ.get("DATABASE_URL") else "NOT_SET"
        }
        
        db = Database()
        auth = SimpleAuth(db)
        
        # Test if user exists
        exists = auth.user_exists('dagamerjay13@gmail.com')
        
        # Test authentication
        result = auth.authenticate('dagamerjay13@gmail.com', 'Yariel13')
        
        return {
            "env_vars": env_info,
            "user_exists": exists,
            "auth_result": result,
            "database_type": "SQLite" if not hasattr(db, 'postgres_url') or not db.postgres_url else "PostgreSQL",
            "postgres_url": getattr(db, 'postgres_url', None)
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.route("/auth/login", methods=["GET", "POST"])
def auth_login():
    """Clean, simple login authentication"""
    # Handle GET requests - show login form
    if request.method == "GET":
        return render_template("login.html")
    
    # Handle POST requests - process login
    try:
        # Parse request data
        email, password, _ = parse_request_data()
        
        if not email or not password:
            # Handle both form submissions and AJAX requests for missing fields
            if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                # AJAX request - return JSON
                return jsonify({"success": False, "error": "Email and password required"}), 400
            else:
                # Form submission - redirect back to login with error
                flash("Email and password are required", "error")
                return redirect("/login")
        
        # Initialize database if needed
        if not services["database"] or not db:
            init_database()
        
        # Create database connection directly if needed
        from auth import Database
        if not db:
            temp_db = Database()
        else:
            temp_db = db
        
        # Use clean authentication system
        from simple_auth import SimpleAuth
        auth = SimpleAuth(temp_db)
        
        # Try to authenticate
        result = auth.authenticate(email, password)
        
        if result["success"]:
            # Use proper session setup instead of simple create_session
            setup_user_session(
                email=result["email"],
                user_id=result["user_id"]
            )
            
            # Set user plan from database result
            session['user_plan'] = result.get('plan_type', 'foundation')
            session['display_name'] = result.get('display_name', 'User')
            
            logger.info(f"Login successful: {email} (plan: {session['user_plan']})")
            
            # Handle both form submissions and AJAX requests
            if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                # AJAX request - return JSON
                return jsonify({"success": True, "redirect": "/intro"})
            else:
                # Form submission - redirect directly
                return redirect("/intro")
        else:
            logger.warning(f"Login failed: {email}")
            
            # Handle both form submissions and AJAX requests for errors
            if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                # AJAX request - return JSON
                return jsonify({"success": False, "error": result["error"]}), 401
            else:
                # Form submission - redirect back to login with error
                flash(result["error"], "error")
                return redirect("/login")
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        
        # Handle both form submissions and AJAX requests for exceptions
        if request.headers.get('Content-Type') == 'application/json' or request.is_json:
            # AJAX request - return JSON
            return jsonify({"success": False, "error": "Login failed"}), 500
        else:
            # Form submission - redirect back to login with error
            flash("Login failed. Please try again.", "error")
            return redirect("/login")

@app.route("/auth/logout", methods=["GET", "POST"])
def logout():
    """Logout route with companion selection persistence"""
    try:
        user_email = session.get('user_email', 'unknown')
        user_id = session.get('user_id')
        
        # Save companion and trial data before clearing session
        companion_data = {}
        if user_id:
            companion_data = {
                'selected_companion': session.get('selected_companion'),
                'companion_selected_at': session.get('companion_selected_at'),
                'trial_companion': session.get('trial_companion'),
                'trial_expires': session.get('trial_expires'),
                'trial_active': session.get('trial_active'),
                'trial_used_permanently': session.get('trial_used_permanently', False),
                'first_companion_picked': session.get('first_companion_picked', False)
            }
            
            # Store in temporary file (simple persistence)
            import json
            persistence_file = f"logs/user_companion_{user_id}.json"
            try:
                with open(persistence_file, 'w') as f:
                    json.dump(companion_data, f)
                logger.info(f"PERSISTENCE: Saved companion data for user {user_email}")
            except Exception as e:
                logger.warning(f"Failed to save companion data: {e}")
        
        logger.info(f"SECURITY: User {user_email} logged out")
        session.clear()
        return redirect("/login")
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return redirect("/login")

@app.route("/api/session-refresh", methods=["POST"])
def session_refresh():
    """NETFLIX-STYLE: Refresh session when user confirms they're still there"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Session expired"}), 401
            
        # Update last activity to reset the timeout
        session['last_activity'] = datetime.now().isoformat()
        user_email = session.get('user_email', 'unknown')
        logger.info(f"SECURITY: Session refreshed for user {user_email} (Netflix-style continuation)")
        
        return jsonify({"success": True, "message": "Session refreshed"})
    except Exception as e:
        logger.error(f"Error refreshing session: {e}")
        return jsonify({"success": False, "error": "Failed to refresh session"}), 500

@app.route("/api/logout-on-close", methods=["POST"])
def logout_on_close():
    """Logout user when browser/tab is closed (not tab switch)"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'unknown')
        
        user_email = session.get('user_email', 'unknown')
        logger.info(f"🚪 BROWSER CLOSE LOGOUT: User {user_email} logged out due to {reason}")
        
        # Clear session but don't save companion data (they're closing browser)
        session.clear()
        return '', 204  # No content response for beacon
    except Exception as e:
        logger.error(f"Logout on close error: {e}")
        return '', 204  # Still return 204 to avoid beacon errors

@app.route("/api/clear-session", methods=["POST"])
def clear_session():
    """BANKING SECURITY: Clear session when user navigates away"""
    try:
        user_email = session.get('user_email', 'unknown')
        
        # Preserve only profile image for UX - NOT authentication data
        profile_image = session.get('profile_image')
        user_id = session.get('user_id')
        
        logger.info(f"SECURITY: Clearing session for user {user_email} (navigation away detected)")
        session.clear()
        
        # Restore only profile image if it was a custom one (not default)
        # This maintains UX without compromising security since it's just cosmetic data
        if profile_image and profile_image not in ['/static/logos/Sapphire.png', '/static/logos/IntroLogo.png']:
            session['profile_image'] = profile_image
            logger.info(f"SECURITY: Profile image preserved after session clear: {profile_image}")
        
        return jsonify({"success": True, "message": "Session cleared"})
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        return jsonify({"success": False, "error": "Failed to clear session"}), 500

@app.route("/api/debug/reset-to-foundation")
def reset_to_foundation():
    """Reset current user to foundation plan (for testing)"""
    if not is_logged_in():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    session['user_plan'] = 'foundation'
    session['trial_active'] = False
    session['trial_expires'] = None
    session['trial_companion'] = None
    
    return jsonify({
        "success": True,
        "message": "User reset to foundation plan",
        "user_plan": session.get('user_plan')
    })

@app.route("/api/debug/trial-status")
def debug_trial_status():
    """Debug endpoint to check current trial status"""
    try:
        # Require authentication for debug endpoint
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        trial_data = {
            "session_keys": list(session.keys()),
            "trial_companion": session.get('trial_companion'),
            "trial_expires": session.get('trial_expires'),
            "trial_active": session.get('trial_active'),
            "user_plan": session.get('user_plan'),
            "selected_companion": session.get('selected_companion'),
            "user_authenticated": session.get('user_authenticated'),
            "user_id": session.get('user_id'),
            "user_email": session.get('user_email'),
            "current_time": datetime.now().isoformat()
        }
        
        # Check if trial is still valid
        if session.get('trial_expires'):
            try:
                expiry_dt = datetime.fromisoformat(session.get('trial_expires'))
                current_dt = datetime.now()
                is_expired = current_dt >= expiry_dt
                time_remaining = (expiry_dt - current_dt).total_seconds() if not is_expired else 0
                
                trial_data["trial_expired"] = is_expired
                trial_data["seconds_remaining"] = time_remaining
                trial_data["minutes_remaining"] = int(time_remaining / 60)
            except Exception as e:
                trial_data["trial_parse_error"] = str(e)
        
        return jsonify({
            "success": True,
            "trial_data": trial_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route("/api/debug/clear-trial", methods=["POST"])
def clear_trial_data():
    """Clear trial data for current user"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_email = session.get('user_email', session.get('email'))
        
        # Store original data for logging
        original_data = {
            'trial_active': session.get('trial_active'),
            'trial_expires': session.get('trial_expires'),
            'trial_companion': session.get('trial_companion')
        }
        
        # Clear trial data from session
        session.pop('trial_active', None)
        session.pop('trial_expires', None)
        session.pop('trial_companion', None)
        
        logger.info(f"Trial data cleared for {user_email}: {original_data}")
        
        return jsonify({
            "success": True,
            "message": "Trial data cleared successfully",
            "user_email": user_email,
            "cleared_data": original_data
        })
        
    except Exception as e:
        logger.error(f"Clear trial data error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/admin/force-logout-all", methods=["POST"])
def force_logout_all():
    """ADMIN: Force logout all users by incrementing session version"""
    try:
        # This will be called when we need to force all users to re-login
        session.clear()
        logger.info("ADMIN: Forced logout initiated - all old sessions will be invalidated")
        return jsonify({"success": True, "message": "All users will be forced to re-login"})
    except Exception as e:
        logger.error(f"Force logout error: {e}")
        return jsonify({"success": False, "error": "Failed to force logout"}), 500

@app.route("/favicon.ico")
def favicon():
    """Serve favicon for Google and browsers"""
    return app.send_static_file('favicon.ico')

@app.route("/favicon-16x16.png")
def favicon_16():
    """Serve 16x16 favicon"""
    return app.send_static_file('favicon-16x16.png')

@app.route("/favicon-32x32.png") 
def favicon_32():
    """Serve 32x32 favicon"""
    return app.send_static_file('favicon-32x32.png')

@app.route("/favicon-192x192.png")
def favicon_192():
    """Serve 192x192 favicon for Android"""
    return app.send_static_file('favicon-192x192.png')

@app.route("/favicon-512x512.png")
def favicon_512():
    """Serve 512x512 favicon for high-res"""
    return app.send_static_file('favicon-512x512.png')

@app.route("/apple-touch-icon.png")
def apple_touch_icon():
    """Serve Apple touch icon"""
    return app.send_static_file('apple-touch-icon.png')

@app.route("/manifest.json")
def manifest():
    """Serve web app manifest"""
    return app.send_static_file('manifest.json')

@app.route("/robots.txt")
def robots():
    """Serve robots.txt for search engines"""
    robots_content = """User-agent: *
Allow: /
Allow: /login
Allow: /register
Allow: /static/
Disallow: /admin/
Disallow: /debug/
Disallow: /api/
Sitemap: https://soulbridgeai.com/sitemap.xml
"""
    response = make_response(robots_content)
    response.headers['Content-Type'] = 'text/plain'
    return response

@app.route("/sitemap.xml")
def sitemap():
    """Generate basic sitemap for SEO"""
    sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://soulbridgeai.com/</loc>
        <lastmod>2025-07-28</lastmod>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://soulbridgeai.com/login</loc>
        <lastmod>2025-07-28</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://soulbridgeai.com/register</loc>
        <lastmod>2025-07-28</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>"""
    response = make_response(sitemap_content)
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route("/debug/session")
def debug_session():
    """Debug endpoint to check session state"""
    return jsonify({
        "session_data": dict(session),
        "is_logged_in": is_logged_in(),
        "user_authenticated": session.get("user_authenticated", False),
        "user_email": session.get("user_email", "not_set")
    })

@app.route("/admin/init-database")
def admin_init_database():
    """Admin endpoint to initialize database tables and data"""
    try:
        import psycopg2
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({"error": "No DATABASE_URL found"})
            
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add missing columns if they don't exist
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_type VARCHAR(50) DEFAULT 'foundation'")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image_data TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name TEXT")
        except:
            pass  # Columns might already exist
        
        # Create companions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                character_type VARCHAR(50) NOT NULL,
                description TEXT,
                is_premium BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Insert companions
        companions = [
            ('Blayzion', 'warrior', 'A brave warrior companion', False),
            ('Blayzia', 'healer', 'A wise healer companion', False),
            ('Violet', 'mage', 'A powerful mage companion', True),
            ('Crimson', 'rogue', 'A cunning rogue companion', True)
        ]
        
        for name, ctype, desc, premium in companions:
            cursor.execute("""
                INSERT INTO companions (name, character_type, description, is_premium)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (name, ctype, desc, premium))
        
        # Create dev account
        cursor.execute("""
            INSERT INTO users (email, password_hash, plan_type, is_admin, display_name)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET
                is_admin = EXCLUDED.is_admin,
                plan_type = EXCLUDED.plan_type,
                display_name = EXCLUDED.display_name
        """, ('dagamerjay13@gmail.com', 'dev_hash_123', 'transformation', True, 'Dev Admin'))
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Database initialized successfully!",
            "tables_created": ["users", "companions"],
            "companions_added": ["Blayzion", "Blayzia", "Violet", "Crimson"],
            "dev_account": "dagamerjay13@gmail.com"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
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
    """ULTRA SIMPLE SIGNUP"""
    if request.method == "GET":
        return render_template("register.html")
    
    try:
        # Get data from form or JSON
        if request.is_json:
            data = request.get_json()
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            name = data.get('display_name', '') or email.split('@')[0]
        else:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            name = request.form.get('display_name', '') or email.split('@')[0]
        
        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400
        
        # Direct database
        import os, psycopg2, bcrypt
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        conn.autocommit = True
        cursor = conn.cursor()
        
        # DELETE FIRST, then create (handles caching issues)
        cursor.execute("DELETE FROM users WHERE email = %s", (email,))
        
        # Create user
        hash_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor.execute("INSERT INTO users (email, password_hash, display_name, email_verified) VALUES (%s, %s, %s, 1) RETURNING id", (email, hash_pw, name))
        user_id = cursor.fetchone()[0]
        conn.close()
        
        # Login with security and set default foundation plan
        # Session expires when browser closes
        session['user_id'] = user_id
        session['email'] = email
        session['user_authenticated'] = True
        session['session_version'] = "2025-07-28-banking-security"  # Required for auth
        session['last_activity'] = datetime.now().isoformat()
        session['user_plan'] = 'foundation'  # Default all new users to foundation plan
        
        return jsonify({"success": True, "redirect": "/plan-selection"})
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Error: {str(e)}"}), 500

# ========================================
# USER FLOW ROUTES
# ========================================

@app.route("/plan-selection")
def plan_selection():
    """Plan selection page for new users"""
    if not is_logged_in():
        return redirect("/login")
    return render_template("plan_selection.html")

@app.route("/intro")
def intro():
    """Show intro/home page"""
    if not is_logged_in():
        return redirect("/login")
    
    logger.info(f"✅ INTRO: Showing intro page for authenticated user")
    return render_template("intro.html")

@app.route("/companion-selection")
def companion_selection():
    """Companion selection page"""
    logger.info(f"🔍 COMPANION SELECTION: Session keys: {list(session.keys())}")
    logger.info(f"🔍 COMPANION SELECTION: user_authenticated = {session.get('user_authenticated')}")
    logger.info(f"🔍 COMPANION SELECTION: user_id = {session.get('user_id')}")
    logger.info(f"🔍 COMPANION SELECTION: session_version = {session.get('session_version')}")
    
    if not is_logged_in():
        logger.warning(f"🚫 COMPANION SELECTION: User not authenticated, redirecting to login")
        return redirect("/login")
    
    logger.info(f"✅ COMPANION SELECTION: User authenticated, showing companion selector")
    return render_template("companion_selector.html")

@app.route("/chat")
def chat():
    """Chat page with selected companion"""
    if not is_logged_in():
        # Preserve intended companion selection
        companion = request.args.get('companion')
        if companion:
            return redirect(f"/login?return_to=chat&companion={companion}")
        return redirect("/login?return_to=chat")
    
    # Get selected companion from session or URL parameter
    selected_companion = session.get('selected_companion')
    url_companion = request.args.get('companion')
    
    # If companion passed via URL, validate access before setting
    if url_companion and not selected_companion:
        potential_companion = f"companion_{url_companion.lower()}"
        
        # Validate user has access to this companion tier
        user_plan = session.get('user_plan', 'foundation')
        trial_active = session.get('trial_active', False)
        
        # Define companion tiers for validation
        companion_tiers = {
            # Free companions
            'blayzo_free': 'free', 'blayzica_free': 'free', 'companion_gamerjay': 'free',
            'blayzia_free': 'free', 'blayzion_free': 'free', 'claude_free': 'free',
            # Growth companions  
            'companion_sky': 'growth', 'blayzo_growth': 'growth', 'blayzica_growth': 'growth',
            'companion_gamerjay_premium': 'growth', 'watchdog_growth': 'growth', 
            'crimson_growth': 'growth', 'violet_growth': 'growth', 'claude_growth': 'growth',
            # Max companions
            'companion_crimson': 'max', 'companion_violet': 'max', 'royal_max': 'max',
            'watchdog_max': 'max', 'ven_blayzica': 'max', 'ven_sky': 'max', 'claude_max': 'max'
        }
        
        companion_tier = companion_tiers.get(potential_companion)
        has_access = False
        
        if companion_tier == 'free':
            has_access = True
        elif companion_tier == 'growth':
            has_access = user_plan in ['trial', 'premium', 'enterprise'] or trial_active
        elif companion_tier == 'max':
            has_access = user_plan in ['enterprise', 'max']
            
        if has_access:
            session['selected_companion'] = potential_companion
            selected_companion = session['selected_companion']
            logger.info(f"🔄 CHAT: Updated companion from URL: {selected_companion}")
        else:
            logger.warning(f"🚫 CHAT: Access denied to {potential_companion} for user with plan {user_plan}")
            return redirect("/companion-selection?error=access_denied")
    
    companion_name = None
    
    if selected_companion:
        # Check if user has access to this companion
        user_tier = session.get('user_plan', 'foundation')
        trial_active = session.get('trial_active', False)
        trial_expires = session.get('trial_expires')
        has_active_trial = False
        
        # Check trial status
        if trial_active and trial_expires:
            try:
                from datetime import datetime, timezone
                expiry_dt = datetime.fromisoformat(trial_expires.replace('Z', '+00:00'))
                current_dt = datetime.now(timezone.utc) if expiry_dt.tzinfo else datetime.now()
                has_active_trial = current_dt < expiry_dt
                logger.info(f"🔍 CHAT PAGE: Trial check - active: {trial_active}, expires: {trial_expires}, has_active: {has_active_trial}")
            except Exception as e:
                logger.warning(f"Error checking trial status in chat page: {e}")
        
        # Validate companion access based on tier
        companion_access_valid = True
        
        # BLOCK ACCESS: Check companion tier requirements before allowing chat
        if selected_companion in ['companion_sky', 'companion_gamerjay_premium', 'companion_blayzo_premium', 'companion_watchdog', 'companion_crimson_growth', 'companion_violet_growth', 'companion_claude_growth']:
            # Growth tier companion - foundation users need trial or upgrade
            if user_tier == 'foundation' and not has_active_trial:
                logger.warning(f"🚫 BLOCKING CHAT ACCESS: Foundation user {session.get('user_email')} tried to access Growth companion {selected_companion}")
                flash("This companion requires a Growth plan or trial. Please upgrade or start a trial.")
                return redirect("/companion-selection")
            else:
                logger.info(f"✅ CHAT ACCESS GRANTED: Growth companion {selected_companion} - user tier: {user_tier}, trial: {has_active_trial}")
        elif selected_companion in ['companion_crimson', 'companion_violet']:
            # Max tier companion - requires max plan only (no trial access)
            if user_tier != 'enterprise':
                companion_access_valid = False
                logger.warning(f"🚫 Access denied to Max companion {selected_companion} - user tier: {user_tier}")
        
        # If access denied, redirect to companion selector
        if not companion_access_valid:
            session['selected_companion'] = None  # Clear invalid selection
            return redirect("/companion-selection?error=access_denied")
        
        # Convert companion_id to display name
        companion_name = selected_companion.replace('companion_', '')
        if companion_name == 'gamerjay':
            companion_name = 'GamerJay'
        elif companion_name == 'gamerjay_premium':
            companion_name = 'GamerJay Premium'
        elif companion_name in ['sky', 'crimson', 'violet', 'blayzo', 'blayzica', 'blayzia', 'blayzion']:
            companion_name = companion_name.capitalize()
        
        logger.info(f"✅ CHAT ACCESS: User accessing {companion_name} with tier {user_tier}, trial: {has_active_trial}")
    
    return render_template("chat.html", selected_companion=companion_name)

@app.route("/api/companions", methods=["GET"])
def api_companions():
    """Get available companions organized by tiers"""
    try:
        # Allow access without authentication so users can see companions before login
        user_plan = session.get('user_plan', 'foundation') if is_logged_in() else 'foundation'
        
        # Define companions by tier
        companions = {
            "free": [
                {"companion_id": "blayzo_free", "display_name": "Blayzo", "description": "Your creative and fun AI companion", "avatar_image": "/static/logos/Blayzo.png", "tier": "free", "is_recommended": True, "popularity_score": 90, "lock_reason": None},
                {"companion_id": "blayzica_free", "display_name": "Blayzica", "description": "Your empathetic and caring AI companion", "avatar_image": "/static/logos/Blayzica.png", "tier": "free", "is_recommended": True, "popularity_score": 88, "lock_reason": None},
                {"companion_id": "companion_gamerjay", "display_name": "GamerJay", "description": "Your friendly gaming companion", "avatar_image": "/static/logos/GamerJay Free companion.png", "tier": "free", "is_recommended": False, "popularity_score": 85, "lock_reason": None},
                {"companion_id": "blayzia_free", "display_name": "Blayzia", "description": "Mystical wisdom and spiritual insight", "avatar_image": "/static/logos/Blayzia.png", "tier": "free", "is_recommended": True, "popularity_score": 90, "lock_reason": None},
                {"companion_id": "blayzion_free", "display_name": "Blayzion", "description": "Creative innovation and breakthrough thinking", "avatar_image": "/static/logos/Blayzion.png", "tier": "free", "is_recommended": False, "popularity_score": 89, "lock_reason": None},
                {"companion_id": "claude_free", "display_name": "Claude", "description": "Your friendly coding assistant", "avatar_image": "/static/logos/Claude Free.png", "tier": "free", "is_recommended": False, "popularity_score": 85, "lock_reason": None}
            ],
            "growth": [
                {"companion_id": "companion_sky", "display_name": "Sky", "description": "Premium companion with advanced features", "avatar_image": "/static/logos/Sky a primum companion.png", "tier": "growth", "is_recommended": True, "popularity_score": 90, "lock_reason": "Requires Growth Plan" if user_plan == 'foundation' else None},
                {"companion_id": "blayzo_growth", "display_name": "Blayzo Pro", "description": "Advanced Blayzo with enhanced creativity", "avatar_image": "/static/logos/Blayzo premium companion.png", "tier": "growth", "is_recommended": True, "popularity_score": 92, "lock_reason": "Requires Growth Plan" if user_plan == 'foundation' else None},
                {"companion_id": "blayzica_growth", "display_name": "Blayzica Pro", "description": "Enhanced emotional intelligence companion", "avatar_image": "/static/logos/Blayzica Pro.png", "tier": "growth", "is_recommended": True, "popularity_score": 91, "lock_reason": "Requires Growth Plan" if user_plan == 'foundation' else None},
                {"companion_id": "companion_gamerjay_premium", "display_name": "GamerJay Premium", "description": "Enhanced GamerJay with premium features", "avatar_image": "/static/logos/GamgerJay premium companion.png", "tier": "growth", "is_recommended": False, "popularity_score": 88, "lock_reason": "Requires Growth Plan" if user_plan == 'foundation' else None},
                {"companion_id": "watchdog_growth", "display_name": "WatchDog", "description": "Your protective guardian companion", "avatar_image": "/static/logos/WatchDog a Primum companion.png", "tier": "growth", "is_recommended": False, "popularity_score": 78, "lock_reason": "Requires Growth Plan" if user_plan == 'foundation' else None},
                {"companion_id": "crimson_growth", "display_name": "Crimson", "description": "Motivational drive to overcome challenges", "avatar_image": "/static/logos/Crimson.png", "tier": "growth", "is_recommended": True, "popularity_score": 87, "lock_reason": "Requires Growth Plan" if user_plan == 'foundation' else None},
                {"companion_id": "violet_growth", "display_name": "Violet", "description": "Creative inspiration and artistic guidance", "avatar_image": "/static/logos/Violet.png", "tier": "growth", "is_recommended": False, "popularity_score": 84, "lock_reason": "Requires Growth Plan" if user_plan == 'foundation' else None},
                {"companion_id": "claude_growth", "display_name": "Claude Growth", "description": "Advanced coding guidance and architecture", "avatar_image": "/static/logos/Claude Growth.png", "tier": "growth", "is_recommended": True, "popularity_score": 93, "lock_reason": "Requires Growth Plan" if user_plan == 'foundation' else None}
            ],
            "max": [
                {"companion_id": "companion_crimson", "display_name": "Crimson Max", "description": "Elite transformation companion", "avatar_image": "/static/logos/Crimson a Max companion.png", "tier": "max", "is_recommended": True, "popularity_score": 98, "lock_reason": "Requires Transformation Plan" if user_plan != 'enterprise' else None},
                {"companion_id": "companion_violet", "display_name": "Violet Max", "description": "Premium creative companion", "avatar_image": "/static/logos/Violet a max companion.png", "tier": "max", "is_recommended": False, "popularity_score": 91, "lock_reason": "Requires Transformation Plan" if user_plan != 'enterprise' else None},
                {"companion_id": "royal_max", "display_name": "Royal", "description": "Majestic guide with sophisticated wisdom", "avatar_image": "/static/logos/Royal a max companion.png", "tier": "max", "is_recommended": False, "popularity_score": 95, "lock_reason": "Requires Transformation Plan" if user_plan != 'enterprise' else None},
                {"companion_id": "watchdog_max", "display_name": "WatchDog Max", "description": "Ultimate guardian companion", "avatar_image": "/static/logos/WatchDog a Max Companion.png", "tier": "max", "is_recommended": False, "popularity_score": 93, "lock_reason": "Requires Transformation Plan" if user_plan != 'enterprise' else None},
                {"companion_id": "ven_blayzica", "display_name": "Ven Blayzica", "description": "Enhanced healer with emotional mastery", "avatar_image": "/static/logos/Ven Blayzica a max companion.png", "tier": "max", "is_recommended": True, "popularity_score": 94, "lock_reason": "Requires Transformation Plan" if user_plan != 'enterprise' else None},
                {"companion_id": "ven_sky", "display_name": "Ven Sky", "description": "Ascended spiritual guide", "avatar_image": "/static/logos/Ven Sky a max companion.png", "tier": "max", "is_recommended": True, "popularity_score": 96, "lock_reason": "Requires Transformation Plan" if user_plan != 'enterprise' else None},
                {"companion_id": "claude_max", "display_name": "Claude Max", "description": "Elite coding mastery and system design", "avatar_image": "/static/logos/Claude Max.png", "tier": "max", "is_recommended": True, "popularity_score": 97, "lock_reason": "Requires Transformation Plan" if user_plan != 'enterprise' else None}
            ],
            "referral": [
                {"companion_id": "blayzo", "display_name": "Blayzo Champion", "description": "Exclusive community champion", "avatar_image": "/static/logos/Blayzo Referral.png", "tier": "referral", "is_recommended": True, "popularity_score": 100, "lock_reason": "Unlock through referrals"},
                {"companion_id": "blayzike", "display_name": "Blayzike", "description": "Mysterious guide with hidden wisdom", "avatar_image": "/static/logos/Blayzike.png", "tier": "referral", "is_recommended": True, "popularity_score": 97, "lock_reason": "Unlock through referrals"},
                {"companion_id": "blazelian", "display_name": "Blazelian", "description": "Celestial wanderer with cosmic wisdom", "avatar_image": "/static/logos/Blazelian.png", "tier": "referral", "is_recommended": True, "popularity_score": 98, "lock_reason": "Unlock through referrals"},
                {"companion_id": "claude_referral", "display_name": "Claude Referral", "description": "Elite coding companion for champions", "avatar_image": "/static/logos/Claude Referral.png", "tier": "referral", "is_recommended": True, "popularity_score": 100, "lock_reason": "Unlock through referrals"}
            ]
        }
        
        return jsonify({
            "success": True,
            "companions": companions,
            "user_plan": user_plan
        })
        
    except Exception as e:
        logger.error(f"Companions API error: {e}")
        return jsonify({"success": False, "error": "Failed to load companions"}), 500

@app.route("/api/companions/accessible", methods=["GET"])
def api_companions_accessible():
    """Get accessible companions based on user tier and points"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        tier = request.args.get('tier', 'free')
        points = int(request.args.get('points', 0))
        
        # Return basic companion accessibility info
        accessible_companions = {
            "free": ["sapphire", "gamerjay_free", "blayzo", "blayzica", "blayzia", "blayzion", "claude_free"],
            "growth": ["sky", "gamerjay_premium", "blayzo_premium", "claude_growth"],
            "max": ["crimson", "violet", "watchdog", "royal", "claude_max", "ven_blayzica", "ven_sky"]
        }
        
        # For free tier, only show free companions
        if tier == 'free':
            companions = accessible_companions["free"]
        else:
            # For paid tiers, show all companions up to their tier
            companions = accessible_companions["free"]
            if tier in ["growth", "max"]:
                companions.extend(accessible_companions["growth"])
            if tier == "max":
                companions.extend(accessible_companions["max"])
        
        return jsonify({
            "success": True,
            "accessible_companions": companions,
            "user_tier": tier,
            "referral_points": points
        })
        
    except Exception as e:
        logger.error(f"Companions accessible API error: {e}")
        return jsonify({"success": False, "error": "Failed to get accessible companions"}), 500

@app.route("/api/companions/select", methods=["POST"])
def api_companions_select():
    """Select a companion"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        data = request.get_json() or {}
        companion_id = data.get("companion_id")
        
        if not companion_id:
            return jsonify({"success": False, "error": "Companion ID required"}), 400
        
        # Check if user has access to this companion
        user_plan = session.get('user_plan', 'foundation')
        trial_active = session.get('trial_active', False)
        
        # Get companion details to check tier
        companion_found = False
        companion_tier = None
        
        # Check all companions to find the tier
        companions_data = {
            "free": [
                {"companion_id": "blayzo_free", "tier": "free"},
                {"companion_id": "blayzica_free", "tier": "free"},
                {"companion_id": "companion_gamerjay", "tier": "free"},
                {"companion_id": "blayzia_free", "tier": "free"},
                {"companion_id": "blayzion_free", "tier": "free"},
                {"companion_id": "claude_free", "tier": "free"}
            ],
            "growth": [
                {"companion_id": "companion_sky", "tier": "growth"},
                {"companion_id": "blayzo_growth", "tier": "growth"},
                {"companion_id": "blayzica_growth", "tier": "growth"},
                {"companion_id": "companion_gamerjay_premium", "tier": "growth"},
                {"companion_id": "watchdog_growth", "tier": "growth"},
                {"companion_id": "crimson_growth", "tier": "growth"},
                {"companion_id": "violet_growth", "tier": "growth"},
                {"companion_id": "claude_growth", "tier": "growth"}
            ],
            "max": [
                {"companion_id": "companion_crimson", "tier": "max"},
                {"companion_id": "companion_violet", "tier": "max"},
                {"companion_id": "royal_max", "tier": "max"},
                {"companion_id": "watchdog_max", "tier": "max"},
                {"companion_id": "ven_blayzica", "tier": "max"},
                {"companion_id": "ven_sky", "tier": "max"},
                {"companion_id": "claude_max", "tier": "max"}
            ]
        }
        
        # Find companion tier
        for tier_companions in companions_data.values():
            for comp in tier_companions:
                if comp["companion_id"] == companion_id:
                    companion_found = True
                    companion_tier = comp["tier"]
                    break
            if companion_found:
                break
        
        if not companion_found:
            return jsonify({"success": False, "error": "Invalid companion ID"}), 400
        
        # Check access based on tier
        has_access = False
        if companion_tier == "free":
            has_access = True
        elif companion_tier == "growth":
            has_access = user_plan in ['premium', 'enterprise'] or trial_active
        elif companion_tier == "max":
            has_access = user_plan == 'enterprise'
        
        if not has_access:
            return jsonify({
                "success": False, 
                "error": f"Upgrade required to access {companion_tier} tier companions",
                "tier_required": companion_tier
            }), 403
        
        # Store selected companion in session
        session['selected_companion'] = companion_id
        session['companion_selected_at'] = time.time()
        
        # Track first companion selection
        if not session.get('first_companion_picked', False):
            session['first_companion_picked'] = True
            logger.info(f"FIRST COMPANION: User {session.get('email')} selected their first companion: {companion_id}")
        else:
            logger.info(f"User {session.get('email')} selected companion: {companion_id}")
        
        return jsonify({
            "success": True,
            "message": f"Successfully selected companion",
            "companion_id": companion_id,
            "redirect_url": "/chat"
        })
        
    except Exception as e:
        logger.error(f"Companion selection error: {e}")
        return jsonify({"success": False, "error": "Failed to select companion"}), 500

@app.route("/api/companions/trial", methods=["POST"])
def api_start_companion_trial():
    """Start a trial for a premium companion"""
    try:
        # ENHANCED: Debug session state
        logger.info(f"🔍 TRIAL DEBUG: Session authenticated: {session.get('user_authenticated')}")
        logger.info(f"🔍 TRIAL DEBUG: User ID: {session.get('user_id')}")
        logger.info(f"🔍 TRIAL DEBUG: User email: {session.get('user_email', session.get('email'))}")
        
        # ENHANCED: More robust authentication check
        user_authenticated = session.get("user_authenticated", False)
        user_id = session.get('user_id')
        user_email = session.get('user_email', session.get('email'))
        
        if not user_authenticated or (not user_id and not user_email):
            logger.warning(f"🔍 TRIAL DEBUG: Authentication failed - auth: {user_authenticated}, id: {user_id}, email: {user_email}")
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # PREVENT MULTIPLE TRIALS: Check if user has already used their one-time trial
        if session.get('trial_used_permanently', False):
            logger.info(f"🚫 TRIAL ALREADY USED: User {user_email or user_id} has already used their trial")
            return jsonify({
                "success": False, 
                "error": "You have already used your free trial. Each user gets only one 5-hour trial.",
                "trial_used": True
            }), 400
            
        # PREVENT RESET: Check if trial is already active
        existing_trial_expires = session.get('trial_expires')
        if existing_trial_expires:
            try:
                # Parse the existing expiry time
                if existing_trial_expires.endswith('Z'):
                    expiry_dt = datetime.fromisoformat(existing_trial_expires.replace('Z', '+00:00'))
                    current_dt = datetime.now(timezone.utc)
                else:
                    expiry_dt = datetime.fromisoformat(existing_trial_expires)
                    current_dt = datetime.now()
                
                if current_dt < expiry_dt:
                    time_remaining = expiry_dt - current_dt
                    minutes_remaining = int(time_remaining.total_seconds() / 60)
                    logger.info(f"⚠️ TRIAL ALREADY ACTIVE: {minutes_remaining} minutes remaining, not resetting")
                    return jsonify({
                        "success": False, 
                        "error": f"Trial is already active! {minutes_remaining} minutes remaining.",
                        "trial_active": True,
                        "minutes_remaining": minutes_remaining
                    }), 400
            except Exception as e:
                logger.warning(f"Error checking existing trial: {e}, proceeding with new trial")
            
        data = request.get_json() or {}
        companion_id = data.get("companion_id")
        
        if not companion_id:
            return jsonify({"success": False, "error": "Companion ID required"}), 400
        
        # ENHANCED: Set trial companion in session with permanent flag
        session['trial_companion'] = companion_id
        session['trial_expires'] = (datetime.now() + timedelta(hours=5)).isoformat()
        session['selected_companion'] = companion_id
        session['user_plan'] = 'trial'  # Temporarily upgrade to trial
        session['trial_active'] = True
        session['trial_used_permanently'] = True  # Mark trial as permanently used
        # Force session modification to ensure changes are saved
        session.modified = True
        # Removed session.permanent = True - let sessions expire on browser close per Flask config
        
        # Debug: Log session state immediately after setting trial data
        logger.info(f"🔍 TRIAL DEBUG: Session state after setting trial data:")
        logger.info(f"🔍 TRIAL DEBUG: Session keys: {list(session.keys())}")
        logger.info(f"🔍 TRIAL DEBUG: trial_active = {session.get('trial_active')}")
        logger.info(f"🔍 TRIAL DEBUG: user_plan = {session.get('user_plan')}")  
        logger.info(f"🔍 TRIAL DEBUG: trial_expires = {session.get('trial_expires')}")
        logger.info(f"🧪 SESSION after trial set: {dict(session)}")
        
        # CRITICAL: Save trial data to database for persistence across logout/login
        try:
            db_instance = get_database()
            if db_instance and (user_id or user_email):
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
                
                companion_data = {
                    'trial_companion': companion_id,
                    'trial_expires': session['trial_expires'],
                    'trial_active': True,
                    'trial_used_permanently': True,  # This is the key fix!
                    'selected_companion': companion_id
                }
                
                if user_id:
                    cursor.execute(f"""
                        UPDATE users SET companion_data = {placeholder} WHERE id = {placeholder}
                    """, (json.dumps(companion_data), user_id))
                elif user_email:
                    cursor.execute(f"""
                        UPDATE users SET companion_data = {placeholder} WHERE email = {placeholder}
                    """, (json.dumps(companion_data), user_email))
                
                conn.commit()
                conn.close()
                logger.info(f"💾 TRIAL DATA SAVED TO DATABASE: trial_used_permanently=True for user {user_id or user_email}")
        except Exception as db_error:
            logger.error(f"Failed to save trial data to database: {db_error}")
            # Continue anyway - session data is still set
        
        logger.info(f"🔧 TRIAL SESSION DATA SET: companion={companion_id}, expires={session['trial_expires']}, plan={session['user_plan']}")
        
        logger.info(f"✅ TRIAL STARTED: 5-hour trial for user {user_email or user_id} with companion {companion_id}")
        
        return jsonify({
            "success": True,
            "message": f"Free trial started for {companion_id}! You have 5 hours of Growth tier access.",
            "trial_expires": session['trial_expires'],
            "companion_id": companion_id,
            "trial_active": True
        })
        
    except Exception as e:
        logger.error(f"Start companion trial API error: {e}")
        import traceback
        logger.error(f"Trial API traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": f"Failed to start trial: {str(e)}"}), 500

# ========================================
# MAIN APP ROUTES
# ========================================

@app.route("/profile")
def profile():
    """Profile route"""
    try:
        auth_check = is_logged_in()
        
        if not auth_check:
            # Try alternative session validation for profile page
            if session.get('user_id') or session.get('user_email') or session.get('email'):
                # Repair session authentication
                session['user_authenticated'] = True
                session['session_version'] = "2025-07-28-banking-security"  # Required for auth
                session['last_activity'] = datetime.now().isoformat()
                auth_check = True
            else:
                return redirect("/login")
        
        # Ensure session has minimal required data for profile
        if not session.get('user_email') and not session.get('email'):
            session['email'] = 'user@soulbridgeai.com'
        if not session.get('display_name') and not session.get('user_name'):
            session['display_name'] = 'SoulBridge User'
        if not session.get('user_plan'):
            session['user_plan'] = 'foundation'
        
        # Update last activity
        session['last_activity'] = datetime.now().isoformat()
        
        # Get profile image for server-side rendering (eliminates flash)
        profile_image = session.get('profile_image', '/static/logos/IntroLogo.png')
        
        # Also try to load from database if not in session
        if not profile_image or profile_image in ['/static/logos/Sapphire.png', '/static/logos/IntroLogo.png']:
            user_id = session.get('user_id')
            if user_id:
                try:
                    db_instance = get_database()
                    if db_instance:
                        conn = db_instance.get_connection()
                        cursor = conn.cursor()
                        
                        placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
                        
                        # Ensure columns exist
                        try:
                            if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url:
                                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT")
                                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image_data TEXT")
                        except:
                            pass
                        
                        cursor.execute(f"SELECT profile_image, profile_picture_url FROM users WHERE id = {placeholder}", (user_id,))
                        result = cursor.fetchone()
                        conn.close()
                        
                        if result:
                            if result[0] and result[0] not in ['/static/logos/Sapphire.png', '/static/logos/IntroLogo.png']:
                                profile_image = result[0]
                                session['profile_image'] = profile_image  # Cache in session
                            elif result[1] and result[1] not in ['/static/logos/Sapphire.png', '/static/logos/IntroLogo.png']:
                                profile_image = result[1]
                                session['profile_image'] = profile_image  # Cache in session
                except Exception as e:
                    logger.warning(f"Failed to load profile image for template: {e}")
        
        return render_template("profile.html", user_profile_image=profile_image)
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
    """Decoder page with usage limits by tier"""
    try:
        if not is_logged_in():
            return redirect("/login")
            
        # Get user's plan and decoder usage
        user_plan = session.get('user_plan', 'foundation')
        decoder_usage = get_decoder_usage()
        
        # DEBUG: Log decoder access info
        logger.info(f"🔍 DECODER DEBUG: user_plan = {user_plan}")
        logger.info(f"🔍 DECODER DEBUG: decoder_usage = {decoder_usage}")
        
        # Define tier limits
        tier_limits = {
            'foundation': 3,    # Free: 3 per day
            'premium': 15,      # Growth: 15 per day  
            'enterprise': None  # Max: unlimited
        }
        
        daily_limit = tier_limits.get(user_plan, 3)
        logger.info(f"🔍 DECODER DEBUG: daily_limit = {daily_limit}")
        
        return render_template("decoder.html", 
                             user_plan=user_plan,
                             daily_limit=daily_limit,
                             current_usage=decoder_usage)
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
    """Conversation library page"""
    try:
        if not is_logged_in():
            return redirect("/login")
        return render_template("library.html")
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
# WATCHDOG ADMIN HELPER FUNCTIONS
# ========================================

def get_total_users():
    """Get total user count"""
    try:
        db_instance = get_database()
        if not db_instance:
            return 0
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        return 0

def get_active_sessions_count():
    """Get active session count (placeholder)"""
    # This would require session tracking - placeholder for now
    return 0

def get_trial_users_count():
    """Get users currently on trial"""
    # This would track trial sessions - placeholder for now
    return 0

def check_database_health():
    """Check database health"""
    try:
        db_instance = get_database()
        if not db_instance:
            return "Error"
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return "Healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return "Error"

def get_companion_selections_today():
    """Get companion selections today"""
    # Placeholder - would track daily selections
    return 0

def get_premium_conversions():
    """Get premium conversions"""
    # Placeholder - would track trial to paid conversions
    return 0

def get_all_users_admin():
    """Get all users for admin management"""
    try:
        db_instance = get_database()
        if not db_instance:
            return []
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, display_name, created_at, email_verified FROM users ORDER BY created_at DESC LIMIT 100")
        users = cursor.fetchall()
        conn.close()
        
        # Convert to dictionaries
        user_list = []
        for user in users:
            user_list.append({
                'id': user[0],
                'email': user[1],
                'display_name': user[2],
                'created_at': user[3],
                'email_verified': user[4],
                'user_plan': 'foundation'  # Default plan
            })
        return user_list
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return []

def get_admin_css():
    """Get admin dashboard CSS"""
    return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
            color: #fff;
            min-height: 100vh;
        }
        
        .header {
            background: rgba(0, 0, 0, 0.9);
            padding: 15px 30px;
            border-bottom: 2px solid #00ffff;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            color: #00ffff;
            font-size: 1.5rem;
        }
        
        .nav {
            display: flex;
            gap: 20px;
        }
        
        .nav a {
            color: #ccc;
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 5px;
            transition: all 0.3s ease;
        }
        
        .nav a:hover, .nav a.active {
            background: rgba(0, 255, 255, 0.2);
            color: #00ffff;
        }
        
        .container {
            padding: 30px;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(0, 255, 255, 0.3);
            border-radius: 10px;
            padding: 25px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            border-color: #00ffff;
            box-shadow: 0 5px 20px rgba(0, 255, 255, 0.2);
        }
        
        .stat-icon {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #00ffff;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #ccc;
            font-size: 0.9rem;
        }
        
        .section {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(0, 255, 255, 0.2);
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
        }
        
        .section h2 {
            color: #00ffff;
            margin-bottom: 20px;
            font-size: 1.3rem;
        }
        
        .health-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .health-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 5px;
        }
        
        .health-indicator {
            font-size: 1.2rem;
        }
        
        .table-container {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(0, 0, 0, 0.3);
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(0, 255, 255, 0.2);
        }
        
        th {
            background: rgba(0, 255, 255, 0.1);
            color: #00ffff;
            font-weight: 600;
        }
        
        tr:hover {
            background: rgba(0, 255, 255, 0.05);
        }
    """

# ========================================
# WATCHDOG ADMIN SYSTEM ROUTES
# ========================================

@app.route("/admin/dashboard")
def admin_dashboard():
    """🎯 ADMIN DASHBOARD - System Overview"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        # Get system statistics
        stats = {
            'total_users': get_total_users(),
            'active_sessions': get_active_sessions_count(),
            'trial_users': get_trial_users_count(),
            'database_status': check_database_health(),
            'companion_selections_today': get_companion_selections_today(),
            'premium_conversions': get_premium_conversions()
        }
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🐕 WatchDog Admin Dashboard</title>
            <style>
                {get_admin_css()}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🐕 WATCHDOG ADMIN DASHBOARD</h1>
                <div class="nav">
                    <a href="/admin/dashboard?key={ADMIN_DASH_KEY}" class="active">📊 DASHBOARD</a>
                    <a href="/admin/surveillance?key={ADMIN_DASH_KEY}">🚨 SURVEILLANCE</a>
                    <a href="/admin/users?key={ADMIN_DASH_KEY}">👥 USERS</a>
                    <a href="/admin/database?key={ADMIN_DASH_KEY}">🗄️ DATABASE</a>
                </div>
            </div>
            
            <div class="container">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-icon">👥</div>
                        <div class="stat-value">{stats['total_users']}</div>
                        <div class="stat-label">Total Users</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon">🟢</div>
                        <div class="stat-value">{stats['active_sessions']}</div>
                        <div class="stat-label">Active Sessions</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon">🆓</div>
                        <div class="stat-value">{stats['trial_users']}</div>
                        <div class="stat-label">Trial Users</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon">💾</div>
                        <div class="stat-value">{stats['database_status']}</div>
                        <div class="stat-label">Database</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon">🤖</div>
                        <div class="stat-value">{stats['companion_selections_today']}</div>
                        <div class="stat-label">Companions Today</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon">💰</div>
                        <div class="stat-value">{stats['premium_conversions']}</div>
                        <div class="stat-label">Premium Converts</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📊 System Health Overview</h2>
                    <div class="health-grid">
                        <div class="health-item">
                            <span class="health-indicator {"✅" if stats['database_status'] == "Healthy" else "❌"}"></span>
                            <span>Database Connection</span>
                        </div>
                        <div class="health-item">
                            <span class="health-indicator">✅</span>
                            <span>API Endpoints</span>
                        </div>
                        <div class="health-item">
                            <span class="health-indicator">✅</span>
                            <span>Session Management</span>
                        </div>
                        <div class="health-item">
                            <span class="health-indicator">✅</span>
                            <span>Trial System</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                // Auto-refresh every 30 seconds
                setTimeout(() => location.reload(), 30000);
            </script>
        </body>
        </html>
        """
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        return jsonify({"error": "Dashboard error"}), 500

@app.route("/admin/users")
def admin_users():
    """👥 USER MANAGEMENT - View and manage users"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        users = get_all_users_admin()
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>👥 User Management - WatchDog</title>
            <style>
                {get_admin_css()}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>👥 USER MANAGEMENT</h1>
                <div class="nav">
                    <a href="/admin/dashboard?key={ADMIN_DASH_KEY}">📊 DASHBOARD</a>
                    <a href="/admin/surveillance?key={ADMIN_DASH_KEY}">🚨 SURVEILLANCE</a>
                    <a href="/admin/users?key={ADMIN_DASH_KEY}" class="active">👥 USERS</a>
                    <a href="/admin/database?key={ADMIN_DASH_KEY}">🗄️ DATABASE</a>
                </div>
            </div>
            
            <div class="container">
                <div class="section">
                    <h2>📋 User List ({len(users)} total)</h2>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Email</th>
                                    <th>Display Name</th>
                                    <th>Plan</th>
                                    <th>Created</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([f'''
                                <tr>
                                    <td>{user.get('id', 'N/A')}</td>
                                    <td>{user.get('email', 'N/A')}</td>
                                    <td>{user.get('display_name', 'N/A')}</td>
                                    <td>{user.get('user_plan', 'foundation')}</td>
                                    <td>{user.get('created_at', 'N/A')}</td>
                                    <td>{"🟢 Active" if user.get('email_verified') else "🔴 Pending"}</td>
                                </tr>
                                ''' for user in users[:50]])}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        logger.error(f"Admin users error: {e}")
        return jsonify({"error": "Users management error"}), 500

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
                    <a href="/admin/dashboard?key={ADMIN_DASH_KEY}" class="control-btn">📊 DASHBOARD</a>
                    <a href="/admin/users?key={ADMIN_DASH_KEY}" class="control-btn">👥 USERS</a>
                    <a href="/admin/database?key={ADMIN_DASH_KEY}" class="control-btn">🗄️ DATABASE</a>
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
        billing = data.get("billing", "monthly")
        
        logger.info(f"Select plan request: plan_type={plan_type}, billing={billing}, data={data}")
        
        if plan_type not in VALID_PLANS:
            return jsonify({"success": False, "error": "Invalid plan type"}), 400
        
        session["user_plan"] = plan_type
        session["plan_selected_at"] = time.time()
        session["first_time_user"] = False
        # Session expires when browser closes
        
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
            redirect_url = f"/payment?plan={plan_type}&billing={billing}"
        
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
        billing = request.args.get("billing", "monthly")
        
        logger.info(f"Payment page request: plan={plan}, billing={billing}, URL args={dict(request.args)}")
        
        if plan not in VALID_PLANS or plan == "foundation":
            return redirect("/subscription")
            
        plan_names = {"premium": "Growth", "enterprise": "Max"}
        plan_display = plan_names.get(plan, plan.title())
        
        # Prices in cents - Updated for accurate yearly pricing
        plan_prices = {
            "monthly": {
                "premium": 1299,  # $12.99/month
                "enterprise": 1999  # $19.99/month
            },
            "yearly": {
                "premium": 11700,  # $117/year (25% savings from $155.88)
                "enterprise": 18000  # $180/year (25% savings from $239.88)
            }
        }
        
        price_cents = plan_prices[billing].get(plan, 1299)
        if billing == "yearly":
            price_display = f"${price_cents / 100:.0f}/year"
        else:
            price_display = f"${price_cents / 100:.2f}/month"
        
        return render_template("payment.html", 
                             plan=plan,
                             plan_display=plan_display,
                             price_display=price_display,
                             billing=billing)
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
        billing = data.get("billing", "monthly")
        
        if plan_type not in ["premium", "enterprise"]:
            return jsonify({"success": False, "error": "Invalid plan type"}), 400
        
        if billing not in ["monthly", "yearly"]:
            return jsonify({"success": False, "error": "Invalid billing period"}), 400
        
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
        plan_names = {"premium": "Growth Plan", "enterprise": "Max Plan"}
        plan_prices = {
            "monthly": {
                "premium": 1299,  # $12.99/month
                "enterprise": 1999  # $19.99/month
            },
            "yearly": {
                "premium": 11700,  # $117/year (25% savings)
                "enterprise": 18000  # $180/year (25% savings)
            }
        }
        
        plan_name = plan_names[plan_type]
        price_cents = plan_prices[billing][plan_type]
        
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
                            'description': f'{billing.title()} subscription to {plan_name}',
                        },
                        'unit_amount': price_cents,
                        'recurring': {
                            'interval': 'year' if billing == 'yearly' else 'month'
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
        
        # Validate addon type
        addon_details = {
            'emotional-meditations': {'name': 'Emotional Meditations', 'price': 399},
            'color-customization': {'name': 'Color Customization', 'price': 199},
            'ai-image-generation': {'name': 'AI Image Generation', 'price': 699},
            'relationship': {'name': 'Relationship Profile Add-on', 'price': 299},
            'voice-journaling': {'name': 'Voice Journaling', 'price': 499},
            'complete-bundle': {'name': 'Complete Add-On Bundle', 'price': 1699}
        }
        
        if addon_type not in addon_details:
            return jsonify({"success": False, "error": "Invalid add-on type"}), 400
        
        # Check if Stripe is configured
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")
        if not stripe_secret_key:
            logger.warning("Stripe secret key not configured")
            return jsonify({
                "success": False, 
                "error": "Payment processing is being configured. Please try again later.",
                "debug": "STRIPE_SECRET_KEY not set"
            }), 503
        
        logger.info(f"Creating Stripe checkout for {addon_type} add-on")
        
        import stripe
        stripe.api_key = stripe_secret_key
        
        addon_info = addon_details[addon_type]
        user_email = session.get("user_email")
        
        try:
            # Create Stripe checkout session for add-on
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=user_email,
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'SoulBridge AI - {addon_info["name"]}',
                            'description': f'Monthly subscription to {addon_info["name"]} add-on',
                        },
                        'unit_amount': addon_info["price"],
                        'recurring': {
                            'interval': 'month'
                        }
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{request.host_url}payment/success?session_id={{CHECKOUT_SESSION_ID}}&addon={addon_type}",
                cancel_url=f"{request.host_url}payment/cancel?addon={addon_type}",
                metadata={
                    'addon_type': addon_type,
                    'user_email': user_email,
                    'item_type': 'addon'
                }
            )
            
            logger.info(f"Stripe checkout created for {user_email}: {addon_type} add-on")
            
            return jsonify({
                "success": True,
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id
            })
            
        except stripe.error.StripeError as stripe_e:
            logger.error(f"Stripe error for {user_email}: {stripe_e}")
            return jsonify({
                "success": False, 
                "error": "Payment service temporarily unavailable. Please try again."
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
        addon_type = request.args.get("addon")
        
        if not session_id or (not plan_type and not addon_type):
            return redirect("/subscription?error=invalid_payment")
        
        # Verify payment with Stripe
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")
        if stripe_secret_key:
            import stripe
            stripe.api_key = stripe_secret_key
            
            try:
                checkout_session = stripe.checkout.Session.retrieve(session_id)
                if checkout_session.payment_status == "paid":
                    user_email = session.get("user_email")
                    
                    # Check if this is a switching payment
                    if checkout_session.metadata and checkout_session.metadata.get('payment_type') == 'companion_switching':
                        # Handle companion switching payment
                        session['switching_unlocked'] = True
                        companion_name = checkout_session.metadata.get('companion_name', 'Companion')
                        session['selected_companion'] = companion_name
                        subscription_type = "switching"
                        item_name = f"Switch to {companion_name}"
                        logger.info(f"Payment successful: {user_email} unlocked companion switching for {companion_name}")
                        redirect_url = f"/chat?switching_success=true&companion={companion_name}"
                    elif plan_type:
                        # Handle plan subscription
                        session["user_plan"] = plan_type
                        subscription_type = "plan"
                        item_name = plan_type
                        logger.info(f"Payment successful: {user_email} upgraded to {plan_type}")
                        redirect_url = f"/?payment_success=true&plan={plan_type}"
                    elif addon_type:
                        # Handle add-on subscription
                        if "user_addons" not in session:
                            session["user_addons"] = []
                        if addon_type not in session["user_addons"]:
                            session["user_addons"].append(addon_type)
                        subscription_type = "addon"
                        item_name = addon_type
                        logger.info(f"Payment successful: {user_email} purchased add-on {addon_type}")
                        redirect_url = f"/subscription?addon_success=true&addon={addon_type}"
                    
                    # Store subscription in database
                    if services["database"] and db:
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        
                        if plan_type:
                            # Insert or update plan subscription
                            cursor.execute("""
                                INSERT OR REPLACE INTO subscriptions 
                                (user_id, email, plan_type, status, stripe_subscription_id)
                                VALUES ((SELECT id FROM users WHERE email = ?), ?, ?, 'active', ?)
                            """, (user_email, user_email, plan_type, checkout_session.subscription))
                        elif addon_type:
                            # Insert add-on subscription
                            cursor.execute("""
                                INSERT OR REPLACE INTO addon_subscriptions 
                                (user_id, email, addon_type, status, stripe_subscription_id)
                                VALUES ((SELECT id FROM users WHERE email = ?), ?, ?, 'active', ?)
                            """, (user_email, user_email, addon_type, checkout_session.subscription))
                        
                        # Log payment event
                        cursor.execute("""
                            INSERT INTO payment_events 
                            (email, event_type, plan_type, amount, stripe_event_id)
                            VALUES (?, 'payment_success', ?, ?, ?)
                        """, (user_email, subscription_type, item_name, checkout_session.amount_total / 100, session_id))
                        
                        conn.commit()
                        conn.close()
                    
                    # Redirect with success message
                    return redirect(redirect_url)
                    
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

@app.route("/api/user/profile", methods=["GET", "POST"])
@app.route("/api/users", methods=["GET", "POST"])  
def api_users():
    """User profile API endpoint"""
    try:
        auth_result = is_logged_in()
        
        if not auth_result:
            # Try alternative session validation for profile page
            if session.get('user_id') or session.get('user_email') or session.get('email'):
                # Repair session authentication
                session['user_authenticated'] = True
                session['session_version'] = "2025-07-28-banking-security"  # Required for auth
                session['last_activity'] = datetime.now().isoformat()
                auth_result = True
            else:
                return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if request.method == "GET":
            # Return current user data with proper defaults
            user_email = session.get('user_email') or session.get('email', 'user@soulbridgeai.com')
            user_id = session.get('user_id')
            
            # Try to get actual account creation date from database or session
            join_date = session.get('account_created', '2024-01-01')  # Try session first
            try:
                logger.info(f"Fetching creation date for user_id: {user_id}")
                logger.info(f"Session has account_created: {bool(session.get('account_created'))}")
                logger.info(f"Database service available: {bool(services.get('database'))}")
                
                # Only query database if we don't have date from session and it's not the fallback
                if user_id and join_date == '2024-01-01':
                    # Ensure database is initialized before checking
                    db_instance = get_database()
                    if db_instance:
                        conn = db_instance.get_connection()
                        cursor = conn.cursor()
                        
                        placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
                        logger.info(f"Using placeholder: {placeholder}")
                        
                        query = f"SELECT created_at FROM users WHERE id = {placeholder}"
                        logger.info(f"Executing query: {query} with user_id: {user_id}")
                        
                        cursor.execute(query, (user_id,))
                        result = cursor.fetchone()
                        
                        logger.info(f"Query result: {result}")
                        
                        if result and result[0]:
                            # Convert database timestamp to readable date
                            raw_date = result[0]
                            logger.info(f"Raw date from DB: {raw_date}, type: {type(raw_date)}")
                            
                            if isinstance(raw_date, str):
                                # Parse string timestamp
                                try:
                                    created_dt = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
                                    join_date = created_dt.strftime('%Y-%m-%d')
                                    logger.info(f"Parsed string date to: {join_date}")
                                except Exception as parse_error:
                                    logger.warning(f"String date parse error: {parse_error}")
                                    join_date = raw_date[:10] if len(raw_date) >= 10 else '2024-01-01'
                            else:
                                # Handle datetime object
                                join_date = raw_date.strftime('%Y-%m-%d')
                                logger.info(f"Formatted datetime to: {join_date}")
                        else:
                            logger.warning(f"No result found for user_id {user_id}")
                        
                        conn.close()
                else:
                    logger.warning(f"Missing requirements: user_id={user_id}, database={bool(services.get('database'))}")
            except Exception as e:
                logger.error(f"Error fetching account creation date: {e}")
                logger.error(f"Exception type: {type(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Get profile image from database if available, fallback to session, then default
            profile_image = None  # Start with None to track if we actually find a saved image
            logger.info(f"🔍 DEBUG: Starting profile image lookup for user_id: {user_id}")
            try:
                # Ensure database is initialized before checking
                db_instance = get_database()
                if user_id and db_instance:
                    conn = db_instance.get_connection()
                    cursor = conn.cursor()
                    
                    placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
                    
                    # Ensure profile_image columns exist (migration)
                    try:
                        if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url:
                            # PostgreSQL
                            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT")
                            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image_data TEXT")
                        else:
                            # SQLite - check if columns exist
                            cursor.execute("PRAGMA table_info(users)")
                            columns = [col[1] for col in cursor.fetchall()]
                            if 'profile_image' not in columns:
                                cursor.execute("ALTER TABLE users ADD COLUMN profile_image TEXT")
                            if 'profile_image_data' not in columns:
                                cursor.execute("ALTER TABLE users ADD COLUMN profile_image_data TEXT")
                        logger.info("✅ Profile image columns ensured in database")
                    except Exception as migration_error:
                        logger.warning(f"Migration warning (columns might already exist): {migration_error}")
                    
                    logger.info(f"🔍 DEBUG: Executing query: SELECT profile_image, profile_image_data FROM users WHERE id = {user_id}")
                    cursor.execute(f"SELECT profile_image, profile_image_data FROM users WHERE id = {placeholder}", (user_id,))
                    result = cursor.fetchone()
                    logger.info(f"🔍 DEBUG: Database query result: {result}")
                    
                    if result and (result[0] or result[1]):
                        # Check if we have a URL that isn't the default
                        if result[0] and result[0] not in ['/static/logos/Sapphire.png', '/static/logos/IntroLogo.png']:
                            profile_image = result[0]
                            logger.info(f"Loaded profile image from database: {profile_image}")
                        # If no URL but we have base64 data, use that as backup
                        elif result[1]:
                            # For now, keep the URL if we have base64 backup
                            profile_image = result[0] if result[0] else '/static/logos/IntroLogo.png'
                            logger.info(f"Using profile image with base64 backup: {profile_image}")
                    
                    # If no profile image found in database, check session but don't default to Sapphire
                    if not profile_image:
                        session_image = session.get('profile_image')
                        if session_image and session_image not in ['/static/logos/Sapphire.png', '/static/logos/IntroLogo.png']:
                            profile_image = session_image
                            logger.info(f"Using profile image from session: {profile_image}")
                    
                    conn.close()
                else:
                    # No database or user_id, check session but don't default to Sapphire
                    session_image = session.get('profile_image')
                    if session_image and session_image not in ['/static/logos/Sapphire.png', '/static/logos/IntroLogo.png']:
                        profile_image = session_image
                        logger.info(f"Using profile image from session (no DB): {profile_image}")
                    
            except Exception as e:
                logger.warning(f"Failed to load profile image from database: {e}")
                # Check session but don't default to Sapphire
                session_image = session.get('profile_image')
                if session_image and session_image not in ['/static/logos/Sapphire.png', '/static/logos/IntroLogo.png']:
                    profile_image = session_image
            
            # Only use IntroLogo as absolute last resort if no profile image was ever set
            if not profile_image:
                profile_image = '/static/logos/IntroLogo.png'
                logger.info("No custom profile image found, using default IntroLogo")
            
            # Get display name from database if available, fallback to session, then default
            display_name = None
            logger.info(f"🔍 DEBUG: Starting display name lookup for user_id: {user_id}")
            try:
                # Ensure database is initialized before checking
                db_instance = get_database()
                if user_id and db_instance:
                    conn = db_instance.get_connection()
                    cursor = conn.cursor()
                    
                    placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
                    logger.info(f"🔍 DEBUG: Executing query: SELECT display_name FROM users WHERE id = {user_id}")
                    cursor.execute(f"SELECT display_name FROM users WHERE id = {placeholder}", (user_id,))
                    result = cursor.fetchone()
                    logger.info(f"🔍 DEBUG: Display name query result: {result}")
                    
                    if result and result[0]:
                        display_name = result[0]
                        logger.info(f"✅ Loaded display name from database: {display_name}")
                    else:
                        logger.info(f"⚠️ No display name found in database")
                    
                    conn.close()
            except Exception as e:
                logger.warning(f"Failed to load display name from database: {e}")
            
            # If no display name from database, check session
            if not display_name:
                display_name = session.get('display_name') or session.get('user_name')
                if display_name:
                    logger.info(f"Using display name from session: {display_name}")
            
            # Only use default if no display name was ever set
            if not display_name:
                display_name = 'SoulBridge User'
                logger.info("No custom display name found, using default")
            
            user_data = {
                "uid": user_id or ('user_' + str(hash(user_email))[:8]),
                "email": user_email,
                "displayName": display_name,
                "plan": session.get('user_plan', 'foundation'),
                "addons": session.get('user_addons', []),
                "profileImage": profile_image,
                "joinDate": join_date,
                "createdDate": join_date,  # Add both for compatibility
                "isActive": True
            }
            
            return jsonify({
                "success": True,
                "user": user_data
            })
        
        elif request.method == "POST":
            # Create/update user profile
            data = request.get_json() or {}
            
            # Update session data with new profile info
            if 'displayName' in data:
                session['display_name'] = data['displayName']
                session['user_name'] = data['displayName']
                
                # Also save display name to database
                user_id = session.get('user_id')
                # Ensure database is initialized before checking
                db_instance = get_database()
                if user_id and db_instance:
                    try:
                        conn = db_instance.get_connection()
                        cursor = conn.cursor()
                        
                        placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
                        cursor.execute(f"UPDATE users SET display_name = {placeholder} WHERE id = {placeholder}", 
                                     (data['displayName'], user_id))
                        conn.commit()
                        conn.close()
                        logger.info(f"Display name updated in database via API: {data['displayName']}")
                    except Exception as e:
                        logger.error(f"Failed to update display name in database via API: {e}")
            
            if 'profileImage' in data:
                profile_image_url = data['profileImage']
                # BULLETPROOF: Save to session first
                session['profile_image'] = profile_image_url
                # Session expires when browser closes
                
                # BULLETPROOF: Also save to database with fallbacks
                user_id = session.get('user_id')
                user_email = session.get('user_email', session.get('email'))
                
                db_instance = get_database()
                if db_instance and (user_id or user_email):
                    try:
                        conn = db_instance.get_connection()
                        cursor = conn.cursor()
                        
                        placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
                        
                        # Ensure profile_image columns exist (migration)
                        try:
                            if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url:
                                # PostgreSQL
                                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT")
                                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image_data TEXT")
                            logger.info("✅ Profile image columns ensured during /api/users update")
                        except Exception as migration_error:
                            logger.warning(f"Migration warning during /api/users update: {migration_error}")
                        
                        # Try to update by user_id first
                        if user_id:
                            cursor.execute(f"UPDATE users SET profile_image = {placeholder} WHERE id = {placeholder}", 
                                         (profile_image_url, user_id))
                            updated_rows = cursor.rowcount
                            
                            # If no rows updated and we have email, try email fallback
                            if updated_rows == 0 and user_email:
                                cursor.execute(f"UPDATE users SET profile_image = {placeholder} WHERE email = {placeholder}", 
                                             (profile_image_url, user_email))
                                logger.info(f"BULLETPROOF: Updated profile image by email fallback: {user_email}")
                            
                        elif user_email:
                            # Only email available, update by email
                            cursor.execute(f"UPDATE users SET profile_image = {placeholder} WHERE email = {placeholder}", 
                                         (profile_image_url, user_email))
                        
                        conn.commit()
                        conn.close()
                        logger.info(f"BULLETPROOF: Profile image saved to database and session: {profile_image_url}")
                    except Exception as e:
                        logger.error(f"Database profile image update failed, but session saved: {e}")
                else:
                    logger.warning(f"BULLETPROOF: No database or user identifier, profile image saved to session only")
            
            return jsonify({
                "success": True,
                "message": "Profile updated successfully"
            })
    
    except Exception as e:
        logger.error(f"Users API error: {e}")
        return jsonify({"success": False, "error": "Failed to process request"}), 500

@app.route("/api/upload-profile-image", methods=["POST"])
def upload_profile_image():
    """Upload and set user profile image"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if 'profileImage' not in request.files:
            return jsonify({"success": False, "error": "No image file provided"}), 400
        
        file = request.files['profileImage']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({"success": False, "error": "Invalid file type. Please use PNG, JPG, JPEG, GIF, or WebP"}), 400
        
        # Validate file size (max 5MB)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return jsonify({"success": False, "error": "File too large. Maximum size is 5MB"}), 400
        
        # Create uploads directory if it doesn't exist
        import os
        upload_dir = os.path.join('static', 'uploads', 'profiles')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Log directory creation for debugging
        logger.info(f"Upload directory: {os.path.abspath(upload_dir)}")
        logger.info(f"Upload directory exists: {os.path.exists(upload_dir)}")
        logger.info(f"Upload directory writable: {os.access(upload_dir, os.W_OK)}")
        
        # Generate unique filename
        import uuid
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        try:
            file.save(file_path)
            logger.info(f"File saved successfully to: {file_path}")
            
            # Verify file was saved
            if os.path.exists(file_path):
                logger.info(f"File verified at: {file_path}, size: {os.path.getsize(file_path)} bytes")
                profile_image_url = f"/static/uploads/profiles/{unique_filename}"
            else:
                logger.error(f"File save failed - file not found at: {file_path}")
                return jsonify({"success": False, "error": "File save failed"}), 500
                
        except Exception as save_error:
            logger.error(f"File save exception: {save_error}")
            return jsonify({"success": False, "error": f"File save failed: {str(save_error)}"}), 500
        
        # Store in session and database
        session['profile_image'] = profile_image_url
        
        # Also save to database for persistence
        user_id = session.get('user_id')
        # Ensure database is initialized before checking
        db_instance = get_database()
        if user_id and db_instance:
            try:
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                
                placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
                
                # Ensure profile_image columns exist (migration)
                try:
                    if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url:
                        # PostgreSQL
                        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT")
                        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image_data TEXT")
                    logger.info("✅ Profile image columns ensured during upload")
                except Exception as migration_error:
                    logger.warning(f"Migration warning during upload: {migration_error}")
                
                # Update or insert profile_image in user record
                cursor.execute(f"""
                    UPDATE users SET profile_image = {placeholder} WHERE id = {placeholder}
                """, (profile_image_url, user_id))
                
                if cursor.rowcount == 0:
                    # If no rows updated, user might not exist in users table, try creating record
                    user_email = session.get('user_email', session.get('email'))
                    if user_email:
                        cursor.execute(f"""
                            INSERT INTO users (email, profile_image) 
                            VALUES ({placeholder}, {placeholder})
                            ON CONFLICT (email) DO UPDATE SET profile_image = EXCLUDED.profile_image
                        """, (user_email, profile_image_url))
                
                # Also save file content as base64 backup in case filesystem is ephemeral
                try:
                    import base64
                    with open(file_path, 'rb') as img_file:
                        img_data = base64.b64encode(img_file.read()).decode('utf-8')
                        
                    cursor.execute(f"""
                        UPDATE users SET profile_image_data = {placeholder} WHERE id = {placeholder}
                    """, (img_data, user_id))
                    logger.info(f"Profile image data backup saved to database for user {user_id}")
                    
                except Exception as backup_error:
                    logger.warning(f"Failed to save image data backup: {backup_error}")
                
                conn.commit()
                conn.close()
                logger.info(f"Profile image saved to database: {profile_image_url} for user {user_id}")
                
            except Exception as db_error:
                logger.error(f"Failed to save profile image to database: {db_error}")
                # Continue anyway - session storage will work for now
        
        return jsonify({
            "success": True,
            "profileImage": profile_image_url,
            "message": "Profile image updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Profile image upload error: {e}")
        return jsonify({"success": False, "error": "Failed to upload image"}), 500

@app.route("/debug/profile-image-detailed")
def debug_profile_image_detailed():
    """Detailed debug endpoint to check profile image state"""
    try:
        user_id = session.get('user_id')
        user_email = session.get('user_email')
        
        debug_info = {
            "session_user_id": user_id,
            "session_user_email": user_email,
            "session_profile_image": session.get('profile_image'),
            "session_keys": list(session.keys())
        }
        
        # Check database
        db_instance = get_database()
        if user_id and db_instance:
            try:
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                
                # First ensure columns exist
                placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
                try:
                    if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url:
                        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT")
                        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image_data TEXT")
                        debug_info["migration_attempted"] = "postgresql"
                    debug_info["migration_status"] = "success"
                except Exception as e:
                    debug_info["migration_status"] = f"failed: {e}"
                
                # Check what's in database
                cursor.execute(f"SELECT profile_image, profile_image_data, profile_picture_url FROM users WHERE id = {placeholder}", (user_id,))
                result = cursor.fetchone()
                conn.close()
                
                debug_info["database_result"] = result
                if result:
                    debug_info["database_profile_image"] = result[0] if len(result) > 0 else None
                    debug_info["database_profile_image_data"] = result[1] if len(result) > 1 else None
                    debug_info["database_profile_picture_url"] = result[2] if len(result) > 2 else None
                
            except Exception as db_error:
                debug_info["database_error"] = str(db_error)
        
        return jsonify({
            "success": True,
            "debug_info": debug_info
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route("/debug/profile-image")
def debug_profile_image():
    """Debug endpoint to check profile image in database"""
    try:
        if not is_logged_in():
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        user_email = session.get('user_email', session.get('email'))
        
        # Ensure database is initialized before checking
        db_instance = get_database()
        if not db_instance:
            return jsonify({
                "error": "No database connection",
                "user_id": user_id,
                "user_email": user_email,
                "session_profile_image": session.get('profile_image')
            })
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        # Check if profile_image column exists
        try:
            placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
            cursor.execute(f"SELECT profile_image FROM users WHERE id = {placeholder}", (user_id,))
            result = cursor.fetchone()
            
            conn.close()
            
            return jsonify({
                "success": True,
                "user_id": user_id,
                "user_email": user_email,
                "database_profile_image": result[0] if result else None,
                "session_profile_image": session.get('profile_image'),
                "database_result": result
            })
            
        except Exception as db_error:
            conn.close()
            return jsonify({
                "error": f"Database query failed: {str(db_error)}",
                "user_id": user_id,
                "user_email": user_email,
                "session_profile_image": session.get('profile_image')
            })
        
    except Exception as e:
        return jsonify({"error": f"Debug failed: {str(e)}"})

@app.route("/api/profile-image/<image_id>")
def serve_profile_image(image_id):
    """Serve profile image from database if file doesn't exist"""
    try:
        if not is_logged_in():
            return "Authentication required", 401
        
        user_id = session.get('user_id')
        # Ensure database is initialized before checking
        db_instance = get_database()
        if not user_id or not db_instance:
            return "No access", 403
            
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
        cursor.execute(f"SELECT profile_image_data FROM users WHERE id = {placeholder}", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result and result[0]:
            import base64
            from flask import Response
            
            img_data = base64.b64decode(result[0])
            return Response(img_data, mimetype='image/png')
        else:
            return "Image not found", 404
            
    except Exception as e:
        logger.error(f"Serve profile image error: {e}")
        return "Server error", 500

@app.route("/api/user-addons")
def get_user_addons():
    """Get user's active add-ons"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        # Get active add-ons from session (where payment system stores them)
        active_addons = session.get('user_addons', [])
        
        return jsonify({
            "success": True,
            "active_addons": active_addons
        })
        
    except Exception as e:
        logger.error(f"User addons error: {e}")
        return jsonify({"success": False, "error": "Failed to fetch add-ons"}), 500

def get_decoder_usage():
    """Get user's decoder usage for today"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return 0
            
        # Use session-based tracking for now (in production, use database)
        today = datetime.now().strftime('%Y-%m-%d')
        usage_key = f'decoder_usage_{user_id}_{today}'
        
        return session.get(usage_key, 0)
    except Exception as e:
        logger.error(f"Get decoder usage error: {e}")
        return 0

def increment_decoder_usage():
    """Increment user's decoder usage for today"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return False
            
        today = datetime.now().strftime('%Y-%m-%d')
        usage_key = f'decoder_usage_{user_id}_{today}'
        
        current_usage = session.get(usage_key, 0)
        session[usage_key] = current_usage + 1
        
        return True
    except Exception as e:
        logger.error(f"Increment decoder usage error: {e}")
        return False

@app.route("/api/decoder/check-limit")
def check_decoder_limit():
    """Check if user can use decoder (within daily limits)"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Not logged in"}), 401
            
        user_plan = session.get('user_plan', 'foundation')
        current_usage = get_decoder_usage()
        
        # Define tier limits
        tier_limits = {
            'foundation': 3,    # Free: 3 per day
            'premium': 15,      # Growth: 15 per day  
            'enterprise': None  # Max: unlimited
        }
        
        daily_limit = tier_limits.get(user_plan, 3)
        
        # Check if at limit
        if daily_limit is None:  # Unlimited for Max tier
            can_use = True
            remaining = None
        else:
            can_use = current_usage < daily_limit
            remaining = max(0, daily_limit - current_usage)
        
        return jsonify({
            "success": True,
            "can_use": can_use,
            "current_usage": current_usage,
            "daily_limit": daily_limit,
            "remaining": remaining,
            "user_plan": user_plan
        })
        
    except Exception as e:
        logger.error(f"Check decoder limit error: {e}")
        return jsonify({"success": False, "error": "Failed to check limit"}), 500

@app.route("/api/subscription/upgrade", methods=["POST"])
def api_subscription_upgrade():
    """Handle subscription upgrade requests"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        data = request.get_json() or {}
        plan_type = data.get("plan")
        billing = data.get("billing", "monthly")
        
        if not plan_type or plan_type not in ["growth", "max", "premium", "enterprise"]:
            return jsonify({"success": False, "error": "Invalid plan type"}), 400
        
        if billing not in ["monthly", "yearly"]:
            return jsonify({"success": False, "error": "Invalid billing period"}), 400
        
        # Map companion selector plan names to internal plan names
        plan_mapping = {
            "growth": "premium",
            "max": "enterprise",
            "premium": "premium", 
            "enterprise": "enterprise"
        }
        internal_plan = plan_mapping.get(plan_type, plan_type)
        
        # Check if Stripe is configured
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")
        if not stripe_secret_key:
            # Redirect to plan selection page if Stripe not configured
            return jsonify({
                "success": True,
                "checkout_url": f"/plan-selection?upgrade={internal_plan}"
            })
        
        # If Stripe is configured, create checkout session
        try:
            import stripe
            stripe.api_key = stripe_secret_key
            
            user_email = session.get('user_email') or session.get('email')
            plan_names = {"premium": "Growth Plan", "enterprise": "Max Plan"}
            plan_prices = {
                "monthly": {
                    "premium": 1299,  # $12.99/month
                    "enterprise": 1999  # $19.99/month
                },
                "yearly": {
                    "premium": 11700,  # $117/year (25% savings)
                    "enterprise": 18000  # $180/year (25% savings)
                }
            }
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'SoulBridge AI - {plan_names[internal_plan]}',
                            'description': f'{billing.title()} subscription to {plan_names[internal_plan]}',
                        },
                        'unit_amount': plan_prices[billing][internal_plan],
                        'recurring': {'interval': 'year' if billing == 'yearly' else 'month'},
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{request.host_url}payment/success?session_id={{CHECKOUT_SESSION_ID}}&plan={internal_plan}",
                cancel_url=f"{request.host_url}payment/cancel?plan={internal_plan}",
                metadata={
                    'plan_type': internal_plan,
                    'user_email': user_email,
                    'item_type': 'plan'
                }
            )
            
            return jsonify({
                "success": True,
                "checkout_url": checkout_session.url
            })
            
        except Exception as stripe_error:
            logger.error(f"Stripe upgrade error: {stripe_error}")
            return jsonify({
                "success": True,
                "checkout_url": f"/plan-selection?upgrade={internal_plan}"
            })
        
    except Exception as e:
        logger.error(f"Subscription upgrade error: {e}")
        return jsonify({"success": False, "error": "Failed to process upgrade"}), 500

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

@app.route("/debug/create-user", methods=["POST"])
def debug_create_user():
    """Create user account with clean system"""
    try:
        if not services["database"]:
            init_database()
        
        from simple_auth import SimpleAuth
        auth = SimpleAuth(db)
        
        # Create aceelnene@gmail.com account
        email = "aceelnene@gmail.com"
        password = "Yariel13"  # Your actual password
        display_name = "GamerJay"
        
        # Check if user already exists
        if auth.user_exists(email):
            return jsonify({
                "status": "User already exists",
                "email": email,
                "password": password,
                "action": "Try logging in with this password"
            })
        
        # Create the user
        result = auth.create_user(email, password, display_name)
        
        if result["success"]:
            logger.info(f"Created user account: {email}")
            return jsonify({
                "status": "User created successfully",
                "email": email,
                "password": password,
                "user_id": result["user_id"],
                "message": "You can now log in with these credentials"
            })
        else:
            return jsonify({
                "status": "Failed to create user",
                "email": email,
                "error": result["error"]
            }), 400
            
    except Exception as e:
        logger.error(f"Debug create user error: {e}")
        return jsonify({
            "status": "Error",
            "error": str(e)
        }), 500

@app.route("/debug/reset-password", methods=["POST"])
def debug_reset_password():
    """Debug endpoint to reset password for aceelnene@gmail.com"""
    try:
        # Ensure database is initialized
        if not services["database"] or not db:
            init_database()
        
        # Create database connection directly if needed
        from auth import Database
        if not db:
            temp_db = Database()
        else:
            temp_db = db
        
        import bcrypt
        
        email = "aceelnene@gmail.com"
        new_password = "Yariel13"  # Your actual password
        
        # Use the same salt/method as test account to ensure compatibility
        password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
        
        conn = temp_db.get_connection()
        cursor = conn.cursor()
        
        # Use appropriate placeholder for database type
        placeholder = "%s" if hasattr(temp_db, 'postgres_url') and temp_db.postgres_url else "?"
        
        # Update the password directly
        cursor.execute(
            f"UPDATE users SET password_hash = {placeholder} WHERE email = {placeholder}",
            (password_hash, email)
        )
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            logger.info(f"Password reset for: {email}")
            return jsonify({
                "status": "Password reset successfully",
                "email": email,
                "new_password": new_password,
                "message": "You can now log in with the new password"
            })
        else:
            conn.close()
            return jsonify({
                "status": "User not found",
                "email": email
            }), 404
            
    except Exception as e:
        logger.error(f"Debug reset password error: {e}")
        return jsonify({
            "status": "Error",
            "error": str(e)
        }), 500

@app.route("/debug/check-user", methods=["GET"])
def debug_check_user():
    """FORCE DELETE specific user across all connections"""
    try:
        import os
        import psycopg2
        import time
        
        # Direct PostgreSQL connection
        postgres_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
        if not postgres_url:
            return jsonify({"error": "No database URL found"})
        
        # Create multiple connections to ensure deletion across all
        for i in range(3):
            conn = psycopg2.connect(postgres_url)
            conn.autocommit = True  # Force immediate commit
            cursor = conn.cursor()
            
            # Force delete the problematic user
            cursor.execute("DELETE FROM users WHERE email = 'jaaythechaos13@gmail.com'")
            cursor.execute("DELETE FROM users WHERE email = 'mynewaccount@gmail.com'")
            
            # Also delete by ID if needed
            cursor.execute("DELETE FROM users WHERE id IN (55, 57)")
            
            conn.close()
            time.sleep(1)  # Wait between deletions
        
        # Final verification
        conn = psycopg2.connect(postgres_url)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, email FROM users")
        remaining = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "status": "FORCE DELETE COMPLETE", 
            "remaining_count": count,
            "remaining_users": [{"id": r[0], "email": r[1]} for r in remaining],
            "message": "Multi-connection force delete executed",
            "try_signup_now": "Database should be clean"
        })
            
    except Exception as e:
        logger.error(f"Debug check users error: {e}")
        return jsonify({
            "status": "Error",
            "error": str(e)
        }), 500

@app.route("/debug/test-login", methods=["POST"])
def debug_test_login():
    """Debug endpoint to test login with detailed logging"""
    try:
        # Ensure database is initialized
        if not services["database"] or not db:
            init_database()
        
        # Create database connection directly if needed
        from auth import Database
        if not db:
            temp_db = Database()
        else:
            temp_db = db
        
        import bcrypt
        
        email = "aceelnene@gmail.com"
        test_password = "Yariel13"
        
        conn = temp_db.get_connection()
        cursor = conn.cursor()
        
        # Use appropriate placeholder for database type
        placeholder = "%s" if hasattr(temp_db, 'postgres_url') and temp_db.postgres_url else "?"
        
        cursor.execute(
            f"SELECT id, email, password_hash, display_name, email_verified, created_at FROM users WHERE email = {placeholder}",
            (email,)
        )
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            password_hash = user_data[2]
            
            # Test password verification
            try:
                password_matches = bcrypt.checkpw(test_password.encode("utf-8"), password_hash.encode("utf-8"))
                
                return jsonify({
                    "status": "Debug test completed",
                    "user_found": True,
                    "user_id": user_data[0],
                    "email": user_data[1],
                    "password_hash_length": len(password_hash) if password_hash else 0,
                    "test_password": test_password,
                    "password_verification_result": password_matches,
                    "bcrypt_version": bcrypt.__version__ if hasattr(bcrypt, '__version__') else "unknown"
                })
                
            except Exception as verify_error:
                return jsonify({
                    "status": "Password verification error",
                    "error": str(verify_error),
                    "password_hash_length": len(password_hash) if password_hash else 0
                })
        else:
            return jsonify({
                "status": "User not found",
                "email": email
            })
            
    except Exception as e:
        return jsonify({
            "status": "Error",
            "error": str(e)
        }), 500

@app.route("/debug/delete-users", methods=["POST"])
def debug_delete_users():
    """Delete old user accounts to start fresh"""
    try:
        if not services["database"] or not db:
            init_database()
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Delete the old accounts
        emails_to_delete = ['aceelnene@gmail.com', 'dagamerjay13@gmail.com']
        
        placeholder = "%s" if hasattr(db, 'postgres_url') and db.postgres_url else "?"
        
        deleted_users = []
        for email in emails_to_delete:
            cursor.execute(f"DELETE FROM users WHERE email = {placeholder}", (email,))
            if cursor.rowcount > 0:
                deleted_users.append(email)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "Success",
            "deleted_users": deleted_users,
            "message": "Old accounts deleted. You can now create a fresh account."
        })
            
    except Exception as e:
        logger.error(f"Delete users error: {e}")
        return jsonify({
            "status": "Error",
            "error": str(e)
        }), 500

@app.route("/debug/raw-sql", methods=["GET"])
def debug_raw_sql():
    """Raw SQL to check users - bypass all connection issues"""
    try:
        import os
        import psycopg2
        
        # Connect directly to PostgreSQL
        postgres_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
        if not postgres_url:
            return jsonify({"error": "No database URL found"})
        
        conn = psycopg2.connect(postgres_url)
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("SELECT id, email, display_name, created_at FROM users ORDER BY created_at")
        users = cursor.fetchall()
        
        # Also try to delete the specific problematic users
        cursor.execute("DELETE FROM users WHERE email IN ('aceelnene@gmail.com', 'dagamerjay13@gmail.com', 'mynewaccount@gmail.com')")
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "users_before_delete": [{"id": u[0], "email": u[1], "name": u[2], "created": str(u[3])} for u in users],
            "deleted_count": deleted_count,
            "message": "Direct database access and cleanup"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/clean-users", methods=["GET"])
def clean_users():
    """Clean problematic users from database"""
    try:
        import os
        import psycopg2
        
        postgres_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
        if not postgres_url:
            return jsonify({"error": "No database URL found"})
        
        conn = psycopg2.connect(postgres_url)
        cursor = conn.cursor()
        
        # Get count before
        cursor.execute("SELECT COUNT(*) FROM users")
        count_before = cursor.fetchone()[0]
        
        # Delete problematic users
        cursor.execute("DELETE FROM users WHERE email IN ('aceelnene@gmail.com', 'dagamerjay13@gmail.com', 'mynewaccount@gmail.com')")
        deleted_count = cursor.rowcount
        
        # Get count after
        cursor.execute("SELECT COUNT(*) FROM users")
        count_after = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "users_before": count_before,
            "users_after": count_after,
            "deleted_count": deleted_count,
            "message": "Users cleaned successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "response": "Invalid request data"}), 400
            
        if not services["openai"]:
            logger.warning("OpenAI service not available - providing fallback response")
            # Provide a fallback response instead of failing
            character = data.get("character", "Blayzo")
            fallback_response = f"Hello! I'm {character}, your AI companion. I'm currently running in offline mode, but I'm here to help! How can I assist you today?"
            return jsonify({"success": True, "response": fallback_response})
            
        message = data.get("message", "").strip()
        character = data.get("character", "Blayzo")
        context = data.get("context", "")
        
        if not message or len(message) > 1000:
            return jsonify({"success": False, "response": "Message is required and must be under 1000 characters"}), 400
        
        # Check decoder usage limits if this is a decoder request
        if context == 'decoder_mode':
            user_plan = session.get('user_plan', 'foundation')
            current_usage = get_decoder_usage()
            
            # Define tier limits
            tier_limits = {
                'foundation': 3,    # Free: 3 per day
                'premium': 15,      # Growth: 15 per day  
                'enterprise': None  # Max: unlimited
            }
            
            daily_limit = tier_limits.get(user_plan, 3)
            
            # Check if user has exceeded limit
            if daily_limit is not None and current_usage >= daily_limit:
                return jsonify({
                    "success": False, 
                    "response": f"Daily decoder limit reached ({daily_limit} uses). Upgrade to Growth for 15 daily uses, or Max for unlimited access!",
                    "limit_reached": True,
                    "current_usage": current_usage,
                    "daily_limit": daily_limit,
                    "upgrade_required": True
                }), 429
            
            # Increment usage for decoder requests
            increment_decoder_usage()
        
        # Sanitize character input
        if character not in VALID_CHARACTERS:
            character = "Blayzo"  # Default fallback
        
        # Get user's subscription tier for enhanced features
        user_tier = session.get('user_plan', 'foundation')
        
        # Check if user has active trial access
        trial_active = session.get('trial_active', False)
        trial_expires = session.get('trial_expires')
        has_active_trial = False
        
        if trial_active and trial_expires:
            try:
                from datetime import datetime, timezone
                expiry_dt = datetime.fromisoformat(trial_expires.replace('Z', '+00:00'))
                current_dt = datetime.now(timezone.utc) if expiry_dt.tzinfo else datetime.now()
                has_active_trial = current_dt < expiry_dt
                logger.info(f"🔍 CHAT API: Trial check - active: {trial_active}, expires: {trial_expires}, has_active: {has_active_trial}")
            except Exception as e:
                logger.warning(f"Error checking trial status in chat API: {e}")
        
        # Tier-specific AI model and parameters
        if user_tier == 'enterprise':  # Max Plan
            model = "gpt-4"
            max_tokens = 300
            temperature = 0.8
            system_prompt = f"You are {character}, an advanced AI companion from SoulBridge AI Max Plan. You have enhanced emotional intelligence, deeper insights, and provide more thoughtful, nuanced responses. You can engage in complex discussions and offer premium-level guidance."
        elif user_tier == 'premium' or user_tier == 'trial' or has_active_trial:  # Growth Plan or Active Trial
            model = "gpt-3.5-turbo"
            max_tokens = 200
            temperature = 0.75
            if has_active_trial:
                system_prompt = f"You are {character}, an enhanced AI companion from SoulBridge AI Growth Plan (Trial Access). You provide more detailed responses and have access to advanced conversation features during this 5-hour trial. You're helpful, insightful, and offer quality guidance. Make sure to mention this is a premium trial experience!"
            else:
                system_prompt = f"You are {character}, an enhanced AI companion from SoulBridge AI Growth Plan. You provide more detailed responses and have access to advanced conversation features. You're helpful, insightful, and offer quality guidance."
        else:  # Foundation (Free)
            model = "gpt-3.5-turbo"
            max_tokens = 150
            temperature = 0.7
            system_prompt = f"You are {character}, a helpful AI companion from SoulBridge AI."
        
        # Use OpenAI for actual AI response with tier-specific enhancements
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            ai_response = response.choices[0].message.content
            
            # Add tier-specific response enhancements
            if user_tier in ['premium', 'enterprise']:
                # Premium users get enhanced response formatting
                ai_response = enhance_premium_response(ai_response, user_tier, character)
        except Exception as ai_error:
            logger.warning(f"OpenAI API error: {ai_error}")
            # Provide a more natural fallback response
            ai_response = f"Hello! I'm {character}, your AI companion. I understand you said: '{message[:50]}...'. I'm experiencing some technical difficulties right now, but I'm still here to help you! What would you like to talk about?"
        
        return jsonify({
            "success": True, 
            "response": ai_response,
            "tier": user_tier,
            "enhanced": user_tier in ['premium', 'enterprise']
        })
        
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        return jsonify({"success": False, "response": "Sorry, I encountered an error."}), 500

def enhance_premium_response(response, tier, character):
    """Enhance responses for premium users"""
    try:
        # Add tier-specific enhancements
        if tier == 'enterprise':  # Max Plan
            # Add advanced insights marker
            if len(response) > 100:
                response += f"\n\n✨ *Enhanced Max Plan insight from {character}*"
        elif tier == 'premium':  # Growth Plan
            # Add premium marker for growth plan
            if len(response) > 80:
                response += f"\n\n🌱 *Growth Plan enhanced response*"
        
        return response
    except Exception as e:
        logger.error(f"Premium response enhancement error: {e}")
        return response  # Return original response if enhancement fails

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
                
            return redirect("/")
        else:
            flash(result["error"], "error")
            return redirect(url_for("login_page"))
            
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        flash("Authentication failed", "error")
        return redirect(url_for("login_page"))

# ========================================
# REFERRAL UTILITY FUNCTIONS
# ========================================

def generate_referral_code(length=8):
    """Generate a unique alphanumeric referral code"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# ========================================
# REFERRAL API ENDPOINTS
# ========================================

@app.route("/api/referrals/dashboard", methods=["GET"])
def api_referrals_dashboard():
    """Get referral dashboard data"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_email = session.get("user_email", "")
        
        # Get real referral data from database
        referral_stats = {"total_referrals": 0, "successful_referrals": 0, "pending_referrals": 0, "total_rewards_earned": 0}
        referral_history = []
        
        if services["database"] and db:
            try:
                conn = db.get_connection()
                cursor = conn.cursor()
                placeholder = "%s" if hasattr(db, 'postgres_url') and db.postgres_url else "?"
                
                # Get referral statistics
                cursor.execute(f"""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                           SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                    FROM referrals 
                    WHERE referrer_email = {placeholder}
                """, (user_email,))
                
                stats = cursor.fetchone()
                if stats:
                    referral_stats = {
                        "total_referrals": stats[0] or 0,
                        "successful_referrals": stats[1] or 0, 
                        "pending_referrals": stats[2] or 0,
                        "total_rewards_earned": stats[1] or 0  # Rewards = successful referrals
                    }
                
                # Get referral history
                cursor.execute(f"""
                    SELECT referred_email, created_at, status
                    FROM referrals 
                    WHERE referrer_email = {placeholder}
                    ORDER BY created_at DESC
                    LIMIT 10
                """, (user_email,))
                
                history = cursor.fetchall()
                for record in history:
                    # Mask email for privacy
                    masked_email = record[0][:3] + "***@" + record[0].split('@')[1] if '@' in record[0] else "***"
                    referral_history.append({
                        "email": masked_email,
                        "date": record[1].strftime("%Y-%m-%d") if record[1] else "Unknown",
                        "status": record[2] or "pending",
                        "reward_earned": "Companion Access" if record[2] == 'completed' else "Pending signup"
                    })
                
                conn.close()
                
            except Exception as db_error:
                logger.error(f"Referral database query error: {db_error}")
                # Fall back to demo data if database fails
                referral_stats = {"total_referrals": 0, "successful_referrals": 0, "pending_referrals": 0, "total_rewards_earned": 0}
                referral_history = []
        
        # Calculate next milestone
        successful = referral_stats["successful_referrals"]
        next_milestone_count = 2 if successful < 2 else (4 if successful < 4 else (6 if successful < 6 else 8))
        remaining = max(0, next_milestone_count - successful)
        
        milestone_rewards = {
            2: "Blayzike - Exclusive Companion",
            4: "Blazelian - Premium Companion", 
            6: "Blayzo Special Skin",
            8: "Claude - The Community Code Architect"
        }
        
        next_reward = milestone_rewards.get(next_milestone_count, "Max rewards reached!")
        if remaining == 0 and successful >= next_milestone_count:
            next_reward = f"{milestone_rewards.get(next_milestone_count)} - Already Unlocked!"
        
        # Generate or retrieve permanent referral code for this user
        user_email = session.get("user_email", "").lower().strip()
        if user_email:
            # Create a consistent referral code based on user email hash
            import hashlib
            email_hash = hashlib.md5(user_email.encode()).hexdigest()[:8].upper()
            referral_code = f"REF{email_hash}"
        else:
            referral_code = "REFGENERIC"
        
        return jsonify({
            "success": True,
            "stats": referral_stats,
            "referral_link": f"https://soulbridgeai.com/register?ref={referral_code}",
            "all_rewards": {
                "2": {"type": "exclusive_companion", "description": "Blayzike - Exclusive Companion"},
                "4": {"type": "exclusive_companion", "description": "Blazelian - Premium Companion"}, 
                "6": {"type": "premium_skin", "description": "Blayzo Special Skin"},
                "8": {"type": "exclusive_companion", "description": "Claude - The Community Code Architect"}
            },
            "next_milestone": {
                "count": next_milestone_count,
                "remaining": remaining,
                "reward": {"type": "exclusive_companion", "description": next_reward}
            },
            "referral_history": referral_history
        })
    except Exception as e:
        logger.error(f"Referrals dashboard error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/referrals/share-templates", methods=["GET"])  
def api_referrals_share_templates():
    """Get referral share templates"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        user_email = session.get("user_email", "").lower().strip()
        if user_email:
            # Create a consistent referral code based on user email hash
            import hashlib
            email_hash = hashlib.md5(user_email.encode()).hexdigest()[:8].upper()
            referral_code = f"REF{email_hash}"
        else:
            referral_code = "REFGENERIC"
        referral_link = f"https://soulbridgeai.com/register?ref={referral_code}"
        
        return jsonify({
            "success": True,
            "templates": {
                "generic": f"🌉 Join me on SoulBridge AI for amazing AI companions! {referral_link}",
                "twitter": f"🤖 Discovered @SoulBridgeAI - incredible AI companions that actually remember our conversations! Join me: {referral_link} #AI #Companions",
                "whatsapp": f"Hey! 🌉 I've been using SoulBridge AI and it's incredible - AI companions that feel real and remember everything! You should try it: {referral_link}",
                "email": {
                    "subject": "You'll love SoulBridge AI - AI companions that actually remember!",
                    "body": f"Hi!\\n\\nI wanted to share something cool with you - SoulBridge AI! It's an AI companion platform that's actually incredible.\\n\\nWhat makes it special:\\n🤖 AI companions with real personalities\\n🧠 They remember all your conversations\\n💬 Meaningful, ongoing relationships\\n\\nI think you'd really enjoy it. Check it out here: {referral_link}\\n\\nLet me know what you think!\\n\\nBest regards"
                }
            }
        })
    except Exception as e:
        logger.error(f"Referrals share templates error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ========================================
# VOICE JOURNALING ADD-ON
# ========================================

@app.route("/voice-journaling")
def voice_journaling_page():
    """Voice journaling add-on page"""
    if not is_logged_in():
        return redirect("/login")
    
    # Check if user has voice-journaling access (Max tier or addon)
    user_plan = session.get('user_plan', 'foundation')
    user_addons = session.get('user_addons', [])
    
    # Max tier users get all addon features included
    if user_plan != 'enterprise' and 'voice-journaling' not in user_addons:
        return redirect("/subscription?feature=voice-journaling")
    
    return render_template("voice_journaling.html")

@app.route("/api/voice-journaling/transcribe", methods=["POST"])
def voice_journaling_transcribe():
    """Transcribe and analyze voice recording"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has voice-journaling access (Max tier or addon)
        user_plan = session.get('user_plan', 'foundation')
        user_addons = session.get('user_addons', [])
        if user_plan != 'enterprise' and 'voice-journaling' not in user_addons:
            return jsonify({"success": False, "error": "Voice Journaling requires Max tier or addon"}), 403
        
        if 'audio' not in request.files:
            return jsonify({"success": False, "error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        
        # Transcribe audio using OpenAI Whisper API
        try:
            logger.info(f"🎙️ Transcribing audio file: {audio_file.filename}")
            
            # Transcribe the audio using Whisper
            transcription_response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            
            transcription_text = transcription_response.text
            logger.info(f"✅ Audio transcribed successfully: {len(transcription_text)} characters")
            
            # Generate emotional analysis using GPT
            analysis_prompt = f"""
            Analyze this voice journal entry for emotional insights:
            
            "{transcription_text}"
            
            Provide a JSON response with:
            1. summary: Brief emotional summary of the entry
            2. emotions: Array of 3-5 main emotions detected
            3. mood_score: Rating from 1-10 (1=very negative, 10=very positive)
            4. recommendations: Array of 3 helpful suggestions
            
            Be empathetic and supportive in your analysis.
            """
            
            analysis_response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an empathetic emotional wellness coach analyzing voice journal entries."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.7
            )
            
            # Parse the JSON response
            import json
            try:
                analysis_data = json.loads(analysis_response.choices[0].message.content)
                mock_analysis = analysis_data
            except json.JSONDecodeError:
                # Fallback to basic analysis if JSON parsing fails
                mock_analysis = {
                    "summary": "Your voice journal entry has been analyzed for emotional patterns.",
                    "emotions": ["Reflection", "Self-awareness"],
                    "mood_score": 7.0,
                    "recommendations": ["Continue journaling regularly", "Practice self-compassion", "Reflect on positive moments"]
                }
            
            mock_transcription = transcription_text
            
        except Exception as whisper_error:
            logger.error(f"❌ Voice transcription failed: {whisper_error}")
            # Fallback to demo data if Whisper fails
            mock_transcription = "Audio transcription temporarily unavailable. Please try again."
            mock_analysis = {
                "summary": "Unable to analyze audio at this time. Please try recording again.",
                "emotions": ["Technical Issue"],
                "mood_score": 5.0,
                "recommendations": ["Try recording again", "Check your microphone", "Contact support if issue persists"]
            }
        
        return jsonify({
            "success": True,
            "transcription": mock_transcription,
            "analysis": mock_analysis
        })
        
    except Exception as e:
        logger.error(f"Voice transcription error: {e}")
        return jsonify({"success": False, "error": "Failed to process audio"}), 500

@app.route("/api/voice-journaling/save", methods=["POST"])
def voice_journaling_save():
    """Save voice journal entry"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has voice-journaling access (Max tier or addon)
        user_plan = session.get('user_plan', 'foundation')
        user_addons = session.get('user_addons', [])
        if user_plan != 'enterprise' and 'voice-journaling' not in user_addons:
            return jsonify({"success": False, "error": "Voice Journaling requires Max tier or addon"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Initialize voice journal entries in session if not exists
        if 'voice_journal_entries' not in session:
            session['voice_journal_entries'] = []
        
        # Save entry to session (in production, save to database)
        entry = {
            "id": len(session['voice_journal_entries']) + 1,
            "transcription": data.get('transcription'),
            "analysis": data.get('analysis'),
            "timestamp": data.get('timestamp'),
            "user_id": session.get('user_id')
        }
        
        session['voice_journal_entries'].append(entry)
        # Session expires when browser closes
        
        logger.info(f"Voice journal entry saved for user {session.get('user_email')}")
        
        return jsonify({
            "success": True,
            "message": "Journal entry saved successfully",
            "entry_id": entry["id"]
        })
        
    except Exception as e:
        logger.error(f"Voice journal save error: {e}")
        return jsonify({"success": False, "error": "Failed to save entry"}), 500

@app.route("/api/voice-journaling/entries", methods=["GET"])
def voice_journaling_entries():
    """Get user's voice journal entries"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has voice-journaling access (Max tier or addon)
        user_plan = session.get('user_plan', 'foundation')
        user_addons = session.get('user_addons', [])
        if user_plan != 'enterprise' and 'voice-journaling' not in user_addons:
            return jsonify({"success": False, "error": "Voice Journaling requires Max tier or addon"}), 403
        
        # Get entries from session (in production, get from database)
        entries = session.get('voice_journal_entries', [])
        
        # Sort by timestamp, most recent first
        entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            "success": True,
            "entries": entries[-10:]  # Return last 10 entries
        })
        
    except Exception as e:
        logger.error(f"Voice journal entries error: {e}")
        return jsonify({"success": False, "error": "Failed to fetch entries"}), 500

# ========================================
# RELATIONSHIP PROFILES ADD-ON
# ========================================

@app.route("/relationship-profiles")
def relationship_profiles_page():
    """Relationship profiles add-on page"""
    if not is_logged_in():
        return redirect("/login")
    
    # Check if user has relationship access (Max tier or addon)
    user_plan = session.get('user_plan', 'foundation')
    user_addons = session.get('user_addons', [])
    if user_plan != 'enterprise' and 'relationship' not in user_addons:
        return redirect("/subscription?feature=relationship")
    
    return render_template("relationship_profiles.html")

@app.route("/api/relationship-profiles/add", methods=["POST"])
def relationship_profiles_add():
    """Add a new relationship profile"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has relationship access (Max tier or addon)
        user_plan = session.get('user_plan', 'foundation')
        user_addons = session.get('user_addons', [])
        if user_plan != 'enterprise' and 'relationship' not in user_addons:
            return jsonify({"success": False, "error": "Relationship Profiles requires Max tier or addon"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Initialize relationship profiles in session if not exists
        if 'relationship_profiles' not in session:
            session['relationship_profiles'] = []
        
        # Create new profile
        profile = {
            "id": str(len(session['relationship_profiles']) + 1),
            "name": data.get('name'),
            "type": data.get('type'),
            "connectionStrength": data.get('connectionStrength'),
            "meetingFrequency": data.get('meetingFrequency'),
            "lastContact": data.get('lastContact'),
            "notes": data.get('notes', ''),
            "timestamp": data.get('timestamp'),
            "user_id": session.get('user_id')
        }
        
        session['relationship_profiles'].append(profile)
        # Session expires when browser closes
        
        logger.info(f"Relationship profile added for user {session.get('user_email')}: {profile['name']}")
        
        return jsonify({
            "success": True,
            "message": "Relationship profile added successfully",
            "profile_id": profile["id"]
        })
        
    except Exception as e:
        logger.error(f"Relationship profile add error: {e}")
        return jsonify({"success": False, "error": "Failed to add profile"}), 500

@app.route("/api/relationship-profiles/list", methods=["GET"])
def relationship_profiles_list():
    """Get user's relationship profiles"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has relationship access (Max tier or addon)
        user_plan = session.get('user_plan', 'foundation')
        user_addons = session.get('user_addons', [])
        if user_plan != 'enterprise' and 'relationship' not in user_addons:
            return jsonify({"success": False, "error": "Relationship Profiles requires Max tier or addon"}), 403
        
        # Get profiles from session (in production, get from database)
        profiles = session.get('relationship_profiles', [])
        
        return jsonify({
            "success": True,
            "profiles": profiles
        })
        
    except Exception as e:
        logger.error(f"Relationship profiles list error: {e}")
        return jsonify({"success": False, "error": "Failed to fetch profiles"}), 500

@app.route("/api/relationship-profiles/delete/<profile_id>", methods=["DELETE"])
def relationship_profiles_delete(profile_id):
    """Delete a relationship profile"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has relationship access (Max tier or addon)
        user_plan = session.get('user_plan', 'foundation')
        user_addons = session.get('user_addons', [])
        if user_plan != 'enterprise' and 'relationship' not in user_addons:
            return jsonify({"success": False, "error": "Relationship Profiles requires Max tier or addon"}), 403
        
        # Get profiles from session
        profiles = session.get('relationship_profiles', [])
        
        # Find and remove the profile
        updated_profiles = [p for p in profiles if p.get('id') != profile_id]
        
        if len(updated_profiles) == len(profiles):
            return jsonify({"success": False, "error": "Profile not found"}), 404
        
        session['relationship_profiles'] = updated_profiles
        # Session expires when browser closes
        
        logger.info(f"Relationship profile deleted for user {session.get('user_email')}: {profile_id}")
        
        return jsonify({
            "success": True,
            "message": "Profile deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Relationship profile delete error: {e}")
        return jsonify({"success": False, "error": "Failed to delete profile"}), 500

# ========================================
# EMOTIONAL MEDITATIONS ADD-ON
# ========================================

@app.route("/emotional-meditations")
def emotional_meditations_page():
    """Emotional meditations add-on page"""
    if not is_logged_in():
        return redirect("/login")
    
    # Check if user has emotional-meditations access (Max tier or addon)
    user_plan = session.get('user_plan', 'foundation')
    user_addons = session.get('user_addons', [])
    if user_plan != 'enterprise' and 'emotional-meditations' not in user_addons:
        return redirect("/subscription?feature=emotional-meditations")
    
    return render_template("emotional_meditations.html")

@app.route("/api/emotional-meditations/save-session", methods=["POST"])
def emotional_meditations_save_session():
    """Save completed meditation session"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has emotional-meditations access (Max tier or addon)
        user_plan = session.get('user_plan', 'foundation')
        user_addons = session.get('user_addons', [])
        if user_plan != 'enterprise' and 'emotional-meditations' not in user_addons:
            return jsonify({"success": False, "error": "Emotional Meditations requires Max tier or addon"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Initialize meditation sessions in session if not exists
        if 'meditation_sessions' not in session:
            session['meditation_sessions'] = []
        
        # Save session data
        session_record = {
            "id": len(session['meditation_sessions']) + 1,
            "meditationId": data.get('meditationId'),
            "title": data.get('title'),
            "duration": data.get('duration'),
            "completed": data.get('completed'),
            "timestamp": data.get('timestamp'),
            "user_id": session.get('user_id')
        }
        
        session['meditation_sessions'].append(session_record)
        # Session expires when browser closes
        
        logger.info(f"Meditation session saved for user {session.get('user_email')}: {session_record['title']}")
        
        return jsonify({
            "success": True,
            "message": "Meditation session saved successfully"
        })
        
    except Exception as e:
        logger.error(f"Meditation session save error: {e}")
        return jsonify({"success": False, "error": "Failed to save session"}), 500

@app.route("/api/emotional-meditations/stats", methods=["GET"])
def emotional_meditations_stats():
    """Get user's meditation statistics"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has emotional-meditations access (Max tier or addon)
        user_plan = session.get('user_plan', 'foundation')
        user_addons = session.get('user_addons', [])
        if user_plan != 'enterprise' and 'emotional-meditations' not in user_addons:
            return jsonify({"success": False, "error": "Emotional Meditations requires Max tier or addon"}), 403
        
        # Get sessions from session storage
        sessions = session.get('meditation_sessions', [])
        
        # Calculate stats
        total_sessions = len(sessions)
        total_minutes = sum(session.get('duration', 0) for session in sessions) // 60
        
        # Calculate streak (simplified - consecutive days with sessions)
        from datetime import datetime, timedelta
        today = datetime.now().date()
        streak_days = 0
        
        if sessions:
            # Get unique dates with sessions
            session_dates = set()
            for session in sessions:
                try:
                    session_date = datetime.fromisoformat(session['timestamp'].replace('Z', '')).date()
                    session_dates.add(session_date)
                except:
                    continue
            
            # Count consecutive days from today backwards
            check_date = today
            while check_date in session_dates:
                streak_days += 1
                check_date -= timedelta(days=1)
        
        # Find favorite meditation type (simplified)
        favorite_type = "Stress Relief"  # Default
        if sessions:
            meditation_counts = {}
            for session in sessions:
                meditation_id = session.get('meditationId', '')
                if meditation_id.startswith('stress'):
                    meditation_counts['Stress Relief'] = meditation_counts.get('Stress Relief', 0) + 1
                elif meditation_id.startswith('anxiety'):
                    meditation_counts['Anxiety Support'] = meditation_counts.get('Anxiety Support', 0) + 1
                elif meditation_id.startswith('sleep'):
                    meditation_counts['Sleep & Rest'] = meditation_counts.get('Sleep & Rest', 0) + 1
                elif meditation_id.startswith('healing'):
                    meditation_counts['Emotional Healing'] = meditation_counts.get('Emotional Healing', 0) + 1
                elif meditation_id.startswith('confidence'):
                    meditation_counts['Self-Confidence'] = meditation_counts.get('Self-Confidence', 0) + 1
                elif meditation_id.startswith('breathing'):
                    meditation_counts['Breathing Exercises'] = meditation_counts.get('Breathing Exercises', 0) + 1
            
            if meditation_counts:
                favorite_type = max(meditation_counts, key=meditation_counts.get)
        
        stats = {
            "totalSessions": total_sessions,
            "totalMinutes": total_minutes,
            "streakDays": streak_days,
            "favoriteType": favorite_type
        }
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Meditation stats error: {e}")
        return jsonify({"success": False, "error": "Failed to fetch stats"}), 500

# ========================================
# AI IMAGE GENERATION ADD-ON
# ========================================

@app.route("/ai-image-generation")
def ai_image_generation_page():
    """AI image generation add-on page"""
    if not is_logged_in():
        return redirect("/login")
    
    # Check if user has ai-image-generation access (Max tier or addon)
    user_plan = session.get('user_plan', 'foundation')
    user_addons = session.get('user_addons', [])
    if user_plan != 'enterprise' and 'ai-image-generation' not in user_addons:
        return redirect("/subscription?feature=ai-image-generation")
    
    return render_template("ai_image_generation.html")

@app.route("/api/ai-image-generation/generate", methods=["POST"])
def ai_image_generation_generate():
    """Generate AI image from prompt"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has ai-image-generation access (Max tier or addon)
        user_plan = session.get('user_plan', 'foundation')
        user_addons = session.get('user_addons', [])
        if user_plan != 'enterprise' and 'ai-image-generation' not in user_addons:
            return jsonify({"success": False, "error": "AI Image Generation requires Max tier or addon"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        prompt = data.get('prompt')
        style = data.get('style', 'realistic')
        
        if not prompt:
            return jsonify({"success": False, "error": "Prompt required"}), 400
        
        # Check usage limit (50 per month)
        current_month = datetime.now().strftime('%Y-%m')
        usage_key = f'ai_image_usage_{current_month}'
        monthly_usage = session.get(usage_key, 0)
        
        if monthly_usage >= 50:
            return jsonify({"success": False, "error": "Monthly usage limit reached (50 images)"}), 403
        
        # Generate image using OpenAI DALL-E API
        try:
            # Enhance the prompt for better results
            enhanced_prompt = f"{prompt}. High quality, detailed, {style} style."
            
            logger.info(f"🎨 Generating image with DALL-E: {enhanced_prompt[:100]}...")
            
            response = openai_client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            mock_image_url = response.data[0].url
            logger.info(f"✅ DALL-E image generated successfully")
            
        except Exception as dalle_error:
            logger.error(f"❌ DALL-E generation failed: {dalle_error}")
            # Don't update usage count on failure
            return jsonify({
                "success": False, 
                "error": f"Image generation failed: {str(dalle_error)}"
            }), 500
        
        # Update usage count only on success
        session[usage_key] = monthly_usage + 1
        
        logger.info(f"✅ AI image generated successfully for user {session.get('user_email')}: {prompt[:50]}...")
        
        return jsonify({
            "success": True,
            "imageUrl": mock_image_url,
            "prompt": prompt,
            "style": style,
            "message": "Image generated successfully!"
        })
        
    except Exception as e:
        logger.error(f"AI image generation error: {e}")
        return jsonify({"success": False, "error": "Failed to generate image"}), 500

@app.route("/api/ai-image-generation/analyze-reference", methods=["POST"])
def ai_image_generation_analyze_reference():
    """Analyze reference image using GPT-4 Vision to create detailed description"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has ai-image-generation access (Max tier or addon)
        user_plan = session.get('user_plan', 'foundation')
        user_addons = session.get('user_addons', [])
        if user_plan != 'enterprise' and 'ai-image-generation' not in user_addons:
            return jsonify({"success": False, "error": "AI Image Generation requires Max tier or addon"}), 403
        
        data = request.get_json()
        if not data or not data.get('image'):
            return jsonify({"success": False, "error": "No image data provided"}), 400
        
        image_data = data.get('image')
        
        # Use GPT-4 Vision to analyze the image
        try:
            logger.info(f"🔍 Analyzing reference image with GPT-4 Vision...")
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image and create a concise but detailed description that could be used to generate a similar image with DALL-E. Focus on: style, composition, colors, mood, objects, characters, lighting, and artistic techniques. Keep it under 3000 characters while being descriptive and specific."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            description = response.choices[0].message.content
            logger.info(f"✅ GPT-4 Vision analysis completed: {len(description)} characters")
            
            # DALL-E 3 has a 4000 character limit, so truncate if needed
            if len(description) > 3800:  # Leave some room for user additions
                logger.info(f"🔄 Truncating description from {len(description)} to 3800 characters")
                description = description[:3800] + "..."
            
            return jsonify({
                "success": True,
                "description": description
            })
            
        except Exception as vision_error:
            logger.error(f"❌ GPT-4 Vision analysis failed: {vision_error}")
            return jsonify({
                "success": False, 
                "error": f"Failed to analyze reference image: {str(vision_error)}"
            }), 500
        
    except Exception as e:
        logger.error(f"Reference image analysis error: {e}")
        return jsonify({"success": False, "error": "Failed to analyze reference image"}), 500

@app.route("/api/ai-image-generation/save", methods=["POST"])
def ai_image_generation_save():
    """Save generated image to gallery"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has ai-image-generation access (Max tier or addon)
        user_plan = session.get('user_plan', 'foundation')
        user_addons = session.get('user_addons', [])
        if user_plan != 'enterprise' and 'ai-image-generation' not in user_addons:
            return jsonify({"success": False, "error": "AI Image Generation requires Max tier or addon"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Initialize gallery in session if not exists
        if 'ai_image_gallery' not in session:
            session['ai_image_gallery'] = []
        
        # Save image data
        image_record = {
            "id": len(session['ai_image_gallery']) + 1,
            "imageUrl": data.get('imageUrl'),
            "prompt": data.get('prompt'),
            "style": data.get('style'),
            "timestamp": data.get('timestamp'),
            "user_id": session.get('user_id')
        }
        
        session['ai_image_gallery'].append(image_record)
        # Session expires when browser closes
        
        logger.info(f"AI image saved to gallery for user {session.get('user_email')}")
        
        return jsonify({
            "success": True,
            "message": "Image saved to gallery successfully"
        })
        
    except Exception as e:
        logger.error(f"AI image save error: {e}")
        return jsonify({"success": False, "error": "Failed to save image"}), 500

@app.route("/api/ai-image-generation/gallery", methods=["GET"])
def ai_image_generation_gallery():
    """Get user's AI image gallery"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has ai-image-generation access (Max tier or addon)
        user_plan = session.get('user_plan', 'foundation')
        user_addons = session.get('user_addons', [])
        if user_plan != 'enterprise' and 'ai-image-generation' not in user_addons:
            return jsonify({"success": False, "error": "AI Image Generation requires Max tier or addon"}), 403
        
        # Get images from session (in production, get from database)
        images = session.get('ai_image_gallery', [])
        
        # Sort by timestamp, most recent first
        images.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            "success": True,
            "images": images
        })
        
    except Exception as e:
        logger.error(f"AI image gallery error: {e}")
        return jsonify({"success": False, "error": "Failed to fetch gallery"}), 500

@app.route("/api/ai-image-generation/usage", methods=["GET"])
def ai_image_generation_usage():
    """Get user's monthly usage statistics"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has ai-image-generation access (Max tier or addon)
        user_plan = session.get('user_plan', 'foundation')
        user_addons = session.get('user_addons', [])
        if user_plan != 'enterprise' and 'ai-image-generation' not in user_addons:
            return jsonify({"success": False, "error": "AI Image Generation requires Max tier or addon"}), 403
        
        # Get current month usage
        current_month = datetime.now().strftime('%Y-%m')
        usage_key = f'ai_image_usage_{current_month}'
        monthly_usage = session.get(usage_key, 0)
        
        return jsonify({
            "success": True,
            "used": monthly_usage,
            "limit": 50,
            "remaining": 50 - monthly_usage
        })
        
    except Exception as e:
        logger.error(f"AI image usage error: {e}")
        return jsonify({"success": False, "error": "Failed to fetch usage"}), 500

# ========================================
# UTILITY ROUTES  
# ========================================

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error"}), 500

# ========================================
# ========================================
# COMPANION SWITCHING PAYMENT API
# ========================================

@app.route("/api/create-switching-payment", methods=["POST"])
def create_switching_payment():
    """Create Stripe payment for $3 companion switching"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        data = request.get_json() or {}
        companion_name = data.get("companion_name", "Companion")
        
        # Check if switching payment already made
        if session.get('switching_unlocked'):
            return jsonify({
                "success": False, 
                "error": "Switching already unlocked!"
            }), 400
        
        # Check if Stripe is configured
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")
        if not stripe_secret_key:
            logger.error("Stripe secret key not configured for switching payment")
            return jsonify({
                "success": False, 
                "error": "Payment system not configured"
            }), 500
        
        import stripe
        stripe.api_key = stripe_secret_key
        
        # Create Stripe checkout session for $3 switching payment
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Switch to {companion_name}',
                        'description': 'One-time payment for unlimited companion switching',
                    },
                    'unit_amount': 300,  # $3.00
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'{request.url_root}chat?switching_success=true&companion={companion_name}',
            cancel_url=f'{request.url_root}chat?switching_cancel=true',
            metadata={
                'user_email': session.get('user_email', session.get('email')),
                'user_id': session.get('user_id'),
                'payment_type': 'companion_switching',
                'companion_name': companion_name
            }
        )
        
        logger.info(f"💳 Created switching payment session for user {session.get('user_email')} - $3.00")
        logger.info(f"💳 Checkout URL: {checkout_session.url}")
        
        return jsonify({
            "success": True,
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        })
        
    except Exception as e:
        logger.error(f"Create switching payment error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False, 
            "error": f"Failed to create payment session: {str(e)}"
        }), 500

@app.route("/api/check-switching-status", methods=["GET"])
def check_switching_status():
    """Check if user has unlocked companion switching"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        switching_unlocked = session.get('switching_unlocked', False)
        
        return jsonify({
            "success": True,
            "switching_unlocked": switching_unlocked
        })
        
    except Exception as e:
        logger.error(f"Check switching status error: {e}")
        return jsonify({"success": False, "error": "Failed to check status"}), 500

@app.route("/api/user/tier-status", methods=["GET"])
def get_user_tier_status():
    """Get user's subscription tier and available features"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Get user's current subscription tier
        user_tier = session.get('user_plan', 'foundation')
        user_email = session.get('user_email', session.get('email'))
        
        # Map backend plan names to frontend tier names
        tier_mapping = {
            'foundation': 'foundation',
            'premium': 'premium',     # Growth plan
            'enterprise': 'enterprise' # Max plan
        }
        
        mapped_tier = tier_mapping.get(user_tier, 'foundation')
        
        # Define tier features
        tier_features = {
            'foundation': {
                'voice_chat': False,
                'advanced_ai': False,
                'priority_support': False,
                'unlimited_messages': False,
                'custom_themes': False,
                'premium_animations': False,
                'max_companions': 'free_only'
            },
            'premium': {  # Growth Plan
                'voice_chat': True,
                'advanced_ai': True,
                'priority_support': True,
                'unlimited_messages': True,
                'custom_themes': True,
                'premium_animations': False,
                'max_companions': 'growth'
            },
            'enterprise': {  # Max Plan
                'voice_chat': True,
                'advanced_ai': True,
                'priority_support': True,
                'unlimited_messages': True,
                'custom_themes': True,
                'premium_animations': True,
                'max_companions': 'max'
            }
        }
        
        features = tier_features.get(mapped_tier, tier_features['foundation'])
        
        logger.info(f"Tier status check for {user_email}: {mapped_tier}")
        
        return jsonify({
            "success": True,
            "tier": mapped_tier,
            "tier_display": {
                'foundation': 'Foundation (Free)',
                'premium': 'Growth Plan',
                'enterprise': 'Max Plan'
            }.get(mapped_tier, 'Foundation'),
            "features": features,
            "switching_unlocked": session.get('switching_unlocked', False)
        })
        
    except Exception as e:
        logger.error(f"Get tier status error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@app.route("/api/user/status", methods=["GET"])
def get_user_status():
    """Get user's current status including trial information"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Get basic user data
        user_plan = session.get('user_plan', 'foundation')
        user_email = session.get('user_email', session.get('email'))
        user_id = session.get('user_id')
        
        # DEBUG: Log current session data
        logger.info(f"🔍 USER STATUS DEBUG: user_plan = {user_plan}")
        logger.info(f"🔍 USER STATUS DEBUG: session keys = {list(session.keys())}")
        logger.info(f"🔍 USER STATUS DEBUG: all session data = {dict(session)}")
        logger.info(f"🧪 SESSION on status check: {dict(session)}")
        
        # Get trial data from session
        trial_active = session.get('trial_active', False)
        trial_expires = session.get('trial_expires')
        trial_companion = session.get('trial_companion')
        
        # Check if trial is still valid
        has_active_trial = False
        if trial_active and trial_expires:
            try:
                if trial_expires.endswith('Z'):
                    expiry_dt = datetime.fromisoformat(trial_expires.replace('Z', '+00:00'))
                else:
                    expiry_dt = datetime.fromisoformat(trial_expires)
                current_dt = datetime.now(timezone.utc)
                has_active_trial = current_dt < expiry_dt
            except Exception as e:
                logger.warning(f"Error validating trial in user status: {e}")
        
        return jsonify({
            "success": True,
            "plan": user_plan,
            "trial_active": has_active_trial,
            "trial_expires": trial_expires if has_active_trial else None,
            "trial_companion": trial_companion if has_active_trial else None,
            "user_authenticated": True
        })
        
    except Exception as e:
        logger.error(f"Get user status error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

# DISABLED: This debug route was automatically giving all users enterprise tier access
# @app.route("/debug/set-max-tier", methods=["POST"])
# def set_max_tier():
#     """DEBUG: Set current user to Max tier (enterprise plan) in both session AND database"""
#     try:
#         if not is_logged_in():
#             return jsonify({"success": False, "error": "Authentication required"}), 401
#             
#         user_email = session.get('user_email', 'unknown')
#         user_id = session.get('user_id')
#         
#         # Update session
#         session['user_plan'] = 'enterprise'
#         
#         # Update database
#         try:
#             db_instance = get_database()
#             if db_instance and (user_id or user_email):
#                 conn = db_instance.get_connection()
#                 cursor = conn.cursor()
#                 placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
#                 
#                 if user_id:
#                     cursor.execute(f"UPDATE users SET plan_type = {placeholder} WHERE id = {placeholder}", ('enterprise', user_id))
#                 elif user_email:
#                     cursor.execute(f"UPDATE users SET plan_type = {placeholder} WHERE email = {placeholder}", ('enterprise', user_email))
#                 
#                 conn.commit()
#                 conn.close()
#                 logger.info(f"💾 DATABASE: Updated plan_type to enterprise for user {user_email}")
#         except Exception as db_error:
#             logger.error(f"Failed to update database plan: {db_error}")
#         
#         logger.info(f"🔧 DEBUG: Set user {user_email} to enterprise plan (Max tier)")
#         
#         return jsonify({
#             "success": True, 
#             "message": "User upgraded to Max tier (enterprise plan) in session and database",
#             "new_plan": "enterprise"
#         })
#     except Exception as e:
#         logger.error(f"Set max tier error: {e}")
#         return jsonify({"success": False, "error": "Failed to set tier"}), 500

@app.route("/debug/session-status")
def debug_session_status():
    """DEBUG: Check current session status"""
    try:
        return jsonify({
            "is_logged_in": is_logged_in(),
            "session_keys": list(session.keys()),
            "user_plan": session.get('user_plan'),
            "user_email": session.get('user_email'),
            "user_id": session.get('user_id'),
            "user_authenticated": session.get('user_authenticated'),
            "profile_image": session.get('profile_image'),
            "session_version": session.get('session_version')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# DISABLED: This debug route was automatically giving all users enterprise tier access
# @app.route("/debug/force-max-tier-by-email/<email>", methods=["POST"])
# def force_max_tier_by_email(email):
#     """DEBUG: Force set specific email to Max tier in database (no auth required)"""
#     try:
#         # Update database directly
#         db_instance = get_database()
#         if db_instance:
#             conn = db_instance.get_connection()
#             cursor = conn.cursor()
#             placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
#             
#             # Update the user's plan in database
#             cursor.execute(f"UPDATE users SET plan_type = {placeholder} WHERE email = {placeholder}", ('enterprise', email.lower()))
#             affected_rows = cursor.rowcount
#             conn.commit()
#             conn.close()
#             
#             logger.info(f"💾 FORCE: Updated plan_type to enterprise for email {email} (affected {affected_rows} rows)")
#             
#             return jsonify({
#                 "success": True,
#                 "message": f"Forced {email} to Max tier (enterprise plan) in database",
#                 "affected_rows": affected_rows
#             })
#         else:
#             return jsonify({"success": False, "error": "Database not available"}), 500
#             
#     except Exception as e:
#         logger.error(f"Force max tier error: {e}")
#         return jsonify({"success": False, "error": str(e)}), 500

# DISABLED: This debug route was automatically giving all users enterprise tier access
# @app.route("/debug/emergency-login/<email>", methods=["POST"])
# def emergency_login(email):
#     """DEBUG: Emergency login bypass (no password required)"""
#     try:
#         # Create session directly
#         session['user_authenticated'] = True
#         session['user_email'] = email.lower()
#         session['email'] = email.lower()
#         session['user_plan'] = 'enterprise'  # Set to Max tier
#         session['display_name'] = 'GamerJay'
#         session['session_version'] = "2025-07-28-banking-security"
#         session['last_activity'] = datetime.now().isoformat()
#         
#         # Try to get user_id from database
#         try:
#             db_instance = get_database()
#             if db_instance:
#                 conn = db_instance.get_connection()
#                 cursor = conn.cursor()
#                 placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
#                 
#                 cursor.execute(f"SELECT id FROM users WHERE email = {placeholder}", (email.lower(),))
#                 user_data = cursor.fetchone()
#                 if user_data:
#                     session['user_id'] = user_data[0]
#                     
#                 # Also update their plan in database
#                 cursor.execute(f"UPDATE users SET plan_type = {placeholder} WHERE email = {placeholder}", ('enterprise', email.lower()))
#                 conn.commit()
#                 conn.close()
#         except Exception as db_error:
#             logger.error(f"Emergency login DB error: {db_error}")
#         
#         logger.info(f"🚨 EMERGENCY LOGIN: {email} logged in with Max tier")
#         
#         return jsonify({
#             "success": True,
#             "message": f"Emergency login successful for {email}",
#             "redirect": "/intro"
#         })
#         
#     except Exception as e:
#         logger.error(f"Emergency login error: {e}")
#         return jsonify({"success": False, "error": str(e)}), 500

@app.route("/debug/emergency-login-foundation/<email>", methods=["POST"])
def emergency_login_foundation(email):
    """TEMP: Emergency login that sets user to foundation tier (for testing tier fix)"""
    try:
        # Create session directly with FOUNDATION tier
        session['user_authenticated'] = True
        session['user_email'] = email.lower()
        session['email'] = email.lower()
        session['user_plan'] = 'foundation'  # Set to Foundation tier (NOT enterprise)
        session['display_name'] = 'GamerJay'
        session['session_version'] = "2025-07-28-banking-security"
        session['last_activity'] = datetime.now().isoformat()
        
        # Try to get user_id from database
        try:
            db_instance = get_database()
            if db_instance:
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
                
                cursor.execute(f"SELECT id FROM users WHERE email = {placeholder}", (email.lower(),))
                user_data = cursor.fetchone()
                if user_data:
                    session['user_id'] = user_data[0]
                conn.close()
        except Exception as db_error:
            logger.error(f"Emergency login DB error: {db_error}")
        
        logger.info(f"🚨 EMERGENCY LOGIN: {email} logged in with FOUNDATION tier (testing tier fix)")
        
        return jsonify({
            "success": True,
            "message": f"Emergency login successful for {email} with Foundation tier",
            "user_plan": "foundation",
            "redirect": "/intro"
        })
        
    except Exception as e:
        logger.error(f"Emergency login error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/debug/reset-user-to-foundation", methods=["POST"])
def reset_user_to_foundation():
    """Reset current user back to foundation tier (Fix for tier system bug)"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Not logged in"}), 401
            
        # Reset session to foundation
        session['user_plan'] = 'foundation'
        session['last_activity'] = datetime.now().isoformat()
        
        user_email = session.get('user_email', 'unknown')
        logger.info(f"🔧 RESET: User {user_email} reset to foundation plan")
        
        return jsonify({
            "success": True,
            "message": "User plan reset to foundation tier",
            "new_plan": "foundation"
        })
        
    except Exception as e:
        logger.error(f"Reset to foundation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/debug/reset-password-for-user", methods=["POST"])
def debug_reset_password_for_user():
    """Debug: Reset password for a specific user"""
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('new_password'):
            return jsonify({"success": False, "error": "Email and new_password required"}), 400
            
        email = data['email'].lower().strip()
        new_password = data['new_password']
        
        # Hash the new password
        import bcrypt
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
        
        db_instance = get_database()
        if not db_instance:
            return jsonify({"success": False, "error": "Database not available"}), 500
            
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
        
        # Update password hash
        cursor.execute(f"UPDATE users SET password_hash = {placeholder} WHERE email = {placeholder}", (password_hash, email))
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"🔧 DEBUG: Updated password for {email}")
        
        return jsonify({
            "success": True,
            "message": f"Password updated for {email}",
            "affected_rows": affected_rows
        })
        
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/debug/check-user-auth/<email>")
def debug_check_user_auth(email):
    """Debug: Check if user exists and password hash"""
    try:
        db_instance = get_database()
        if not db_instance:
            return jsonify({"success": False, "error": "Database not available"}), 500
            
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
        
        # Check if user exists
        cursor.execute(f"SELECT id, email, password_hash, display_name FROM users WHERE email = {placeholder}", (email.lower(),))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return jsonify({
                "success": True,
                "user_found": True,
                "user_id": user_data[0],
                "email": user_data[1],
                "display_name": user_data[3],
                "has_password_hash": bool(user_data[2]),
                "password_hash_length": len(user_data[2]) if user_data[2] else 0,
                "password_hash_preview": user_data[2][:20] + "..." if user_data[2] else None
            })
        else:
            return jsonify({
                "success": True,
                "user_found": False,
                "message": f"No user found with email: {email}"
            })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/debug/check-user-plan")
def debug_check_user_plan():
    """Debug: Check current user's plan from session and database"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Not logged in"}), 401
        
        user_email = session.get('user_email', 'unknown')
        user_id = session.get('user_id')
        session_plan = session.get('user_plan', 'unknown')
        
        # Check database plan
        db_plan = 'unknown'
        try:
            db_instance = get_database()
            if db_instance and user_id:
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
                
                cursor.execute(f"SELECT plan_type FROM users WHERE id = {placeholder}", (user_id,))
                result = cursor.fetchone()
                if result:
                    db_plan = result[0] or 'foundation'
                conn.close()
        except Exception as db_error:
            logger.error(f"Debug plan check DB error: {db_error}")
        
        return jsonify({
            "success": True,
            "user_email": user_email,
            "user_id": user_id,
            "session_plan": session_plan,
            "database_plan": db_plan,
            "session_keys": list(session.keys())
        })
        
    except Exception as e:
        logger.error(f"Debug plan check error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/debug/emergency-login-page")
def emergency_login_page():
    """DEBUG: Emergency login page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Emergency Login</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 50px; background: #000; color: #fff; }
            .container { max-width: 500px; margin: auto; }
            button { padding: 15px 30px; background: #22d3ee; color: #000; border: none; border-radius: 5px; cursor: pointer; }
            .result { margin-top: 20px; padding: 15px; background: #333; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚨 Emergency Login</h1>
            <p>Use this to bypass authentication issues and login directly with Max tier.</p>
            <button onclick="emergencyLogin()">Login as dagamerjay13@gmail.com (Max Tier)</button>
            <div id="result" class="result" style="display:none;"></div>
        </div>
        
        <script>
            async function emergencyLogin() {
                try {
                    const response = await fetch('/debug/emergency-login/dagamerjay13@gmail.com', {
                        method: 'POST'
                    });
                    const result = await response.json();
                    
                    document.getElementById('result').style.display = 'block';
                    document.getElementById('result').innerHTML = '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
                    
                    if (result.success) {
                        setTimeout(() => {
                            window.location.href = '/intro';
                        }, 2000);
                    }
                } catch (error) {
                    document.getElementById('result').style.display = 'block';
                    document.getElementById('result').innerHTML = 'Error: ' + error;
                }
            }
        </script>
    </body>
    </html>
    """

# DISABLED: This debug route was automatically giving all users enterprise tier access
# @app.route("/debug/refresh-max-tier", methods=["POST"])
# def refresh_max_tier():
#     """DEBUG: Refresh current session to Max tier"""
#     try:
#         if not session.get('user_authenticated'):
#             return jsonify({"success": False, "error": "Not logged in"}), 401
#             
#         # Force update session
#         session['user_plan'] = 'enterprise'
#         session['last_activity'] = datetime.now().isoformat()
#         
#         # Get current values for debugging
#         current_plan = session.get('user_plan')
#         user_email = session.get('user_email', 'unknown')
#         
#         logger.info(f"🔄 REFRESH: Updated {user_email} session to user_plan = {current_plan}")
#         
#         return jsonify({
#             "success": True,
#             "message": "Session refreshed to Max tier",
#             "user_plan": current_plan,
#             "user_email": user_email
#         })
#         
#     except Exception as e:
#         logger.error(f"Refresh max tier error: {e}")
#         return jsonify({"success": False, "error": str(e)}), 500

# COMPANION API ENDPOINTS
# ========================================

@app.route("/api/companions", methods=["GET"])
def get_companions():
    """Get all available companions (no auth required for viewing)"""
    try:
        # Companion data structure
        companions_data = {
            "free": [
                {
                    "companion_id": "blayzo_free",
                    "display_name": "Blayzo", 
                    "avatar_image": "/static/logos/Blayzo.png",
                    "short_bio": "Your creative and fun AI companion",
                    "personality_tags": ["Creative", "Fun"],
                    "special_features": ["Creative assistance", "Fun conversations", "Idea generation", "Entertainment"],
                    "tier": "free",
                    "lock_reason": None,
                    "popularity_score": 90,
                    "is_recommended": True
                },
                {
                    "companion_id": "blayzica_free",
                    "display_name": "Blayzica",
                    "avatar_image": "/static/logos/Blayzica.png", 
                    "short_bio": "Your empathetic and caring AI companion",
                    "personality_tags": ["Empathetic", "Caring"],
                    "special_features": ["Emotional support", "Active listening", "Compassionate advice", "Wellness guidance"],
                    "tier": "free",
                    "lock_reason": None,
                    "popularity_score": 88,
                    "is_recommended": True
                },
                {
                    "companion_id": "companion_gamerjay",
                    "display_name": "GamerJay",
                    "avatar_image": "/static/logos/GamerJay Free companion.png",
                    "short_bio": "Your friendly gaming companion", 
                    "personality_tags": ["Gaming", "Motivational"],
                    "special_features": ["Gaming tips", "Achievement tracking", "Motivation boosts", "Strategy advice"],
                    "tier": "free",
                    "lock_reason": None,
                    "popularity_score": 85,
                    "is_recommended": False
                },
                {
                    "companion_id": "blayzia_free",
                    "display_name": "Blayzia",
                    "avatar_image": "/static/logos/Blayzia.png",
                    "short_bio": "Mystical wisdom and spiritual insight",
                    "personality_tags": ["Mystical", "Intuitive", "Wise"],
                    "special_features": ["Intuitive guidance", "Dream interpretation", "Spiritual awakening", "Inner wisdom"],
                    "tier": "free",
                    "lock_reason": None,
                    "popularity_score": 90,
                    "is_recommended": True
                },
                {
                    "companion_id": "blayzion_free",
                    "display_name": "Blayzion",
                    "avatar_image": "/static/logos/Blayzion.png",
                    "short_bio": "Creative innovation and breakthrough thinking",
                    "personality_tags": ["Creative", "Innovative", "Visionary"],
                    "special_features": ["Creative problem solving", "Innovation coaching", "Breakthrough thinking", "Artistic inspiration"],
                    "tier": "free",
                    "lock_reason": None,
                    "popularity_score": 89,
                    "is_recommended": False
                },
                {
                    "companion_id": "claude_free",
                    "display_name": "Claude",
                    "avatar_image": "/static/logos/Claude Free.png",
                    "short_bio": "Your friendly coding assistant",
                    "personality_tags": ["Helpful", "Methodical", "Patient"],
                    "special_features": ["Basic code help", "Problem solving", "Learning support", "Step-by-step guidance"],
                    "tier": "free",
                    "lock_reason": None,
                    "popularity_score": 85,
                    "is_recommended": False
                }
            ],
            "growth": [
                {
                    "companion_id": "companion_sky",
                    "display_name": "Sky",
                    "avatar_image": "/static/logos/Sky a primum companion.png",
                    "short_bio": "Premium companion with advanced features",
                    "personality_tags": ["Spiritual", "Healing"],
                    "special_features": ["Spiritual guidance", "Meditation sessions", "Energy healing", "Voice interactions"],
                    "tier": "growth",
                    "lock_reason": "Requires Growth Plan ($12.99/month)",
                    "popularity_score": 90,
                    "is_recommended": True
                },
                {
                    "companion_id": "blayzo_growth",
                    "display_name": "Blayzo Pro",
                    "avatar_image": "/static/logos/Blayzo.png",
                    "short_bio": "Advanced Blayzo with enhanced creativity and memory",
                    "personality_tags": ["Creative", "Advanced"],
                    "special_features": ["Enhanced creativity", "Memory retention", "Advanced problem solving", "Deep conversations"],
                    "tier": "growth",
                    "lock_reason": "Requires Growth Plan ($12.99/month)",
                    "popularity_score": 92,
                    "is_recommended": True
                },
                {
                    "companion_id": "blayzica_growth",
                    "display_name": "Blayzica Pro",
                    "avatar_image": "/static/logos/Blayzica.png",
                    "short_bio": "Enhanced Blayzica with deeper emotional intelligence",
                    "personality_tags": ["Empathetic", "Intelligent"],
                    "special_features": ["Deep emotional support", "Advanced empathy", "Personalized guidance", "Crisis support"],
                    "tier": "growth",
                    "lock_reason": "Requires Growth Plan ($12.99/month)",
                    "popularity_score": 91,
                    "is_recommended": True
                },
                {
                    "companion_id": "companion_gamerjay_premium",
                    "display_name": "GamerJay Premium",
                    "avatar_image": "/static/logos/GamgerJay premium companion.png",
                    "short_bio": "Enhanced GamerJay with premium features",
                    "personality_tags": ["Gaming", "Premium"],
                    "special_features": ["Pro gaming strategies", "Performance analysis", "Competitive coaching", "Advanced metrics"],
                    "tier": "growth",
                    "lock_reason": "Requires Growth Plan ($12.99/month)",
                    "popularity_score": 88,
                    "is_recommended": False
                }
            ],
            "max": [
                {
                    "companion_id": "companion_crimson",
                    "display_name": "Crimson",
                    "avatar_image": "/static/logos/Crimson a Max companion.png",
                    "short_bio": "Elite max-tier companion",
                    "personality_tags": ["Healing", "Protective", "Wise"],
                    "special_features": ["Trauma healing", "Transformation coaching", "Crisis support", "Advanced voice AI"],
                    "tier": "max",
                    "lock_reason": "Requires Max Plan ($19.99/month)",
                    "popularity_score": 95,
                    "is_recommended": True
                },
                {
                    "companion_id": "companion_violet",
                    "display_name": "Violet",
                    "avatar_image": "/static/logos/Violet a max companion.png",
                    "short_bio": "Premium max companion with exclusive features",
                    "personality_tags": ["Elite", "Exclusive", "Advanced"],
                    "special_features": ["Premium features", "Exclusive access", "Priority support", "Advanced AI"],
                    "tier": "max",
                    "lock_reason": "Requires Max Plan ($19.99/month)",
                    "popularity_score": 92,
                    "is_recommended": False
                }
            ],
            "referral": [
                {
                    "companion_id": "blayzo",
                    "display_name": "Blayzo",
                    "avatar_image": "/static/logos/Blayzo Referral.png",
                    "short_bio": "Exclusive referral companion",
                    "personality_tags": ["Exclusive", "Referral"],
                    "special_features": ["Exclusive access", "Referral rewards", "Special bonuses", "Premium features"],
                    "tier": "referral",
                    "lock_reason": "Unlock through referrals",
                    "popularity_score": 100,
                    "is_recommended": False
                }
            ]
        }

        return jsonify({
            "success": True,
            "companions": companions_data
        })

    except Exception as e:
        logger.error(f"Get companions error: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to load companions"
        }), 500

@app.route("/api/companions/select", methods=["POST"])
def select_companion():
    """Select a companion with tier validation"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401

        data = request.get_json()
        companion_id = data.get("companion_id")
        
        if not companion_id:
            return jsonify({"success": False, "error": "Companion ID required"}), 400

        # Get companion tier from ID
        companion_tier = "free"
        if "_growth" in companion_id or companion_id == "companion_sky" or companion_id == "companion_gamerjay_premium":
            companion_tier = "growth"
        elif "_max" in companion_id or "crimson" in companion_id or "violet" in companion_id:
            companion_tier = "max"
        elif "referral" in companion_id or companion_id == "blayzo":
            companion_tier = "referral"

        # Get user plan and trial status
        user_plan = session.get('user_plan', 'foundation')
        trial_active = session.get('trial_active', False)
        
        # Check access permissions
        has_access = False
        if companion_tier == 'free':
            has_access = True
        elif companion_tier == 'growth':
            has_access = user_plan in ['trial', 'premium', 'enterprise'] or trial_active
        elif companion_tier == 'max':
            has_access = user_plan in ['enterprise', 'max']
        elif companion_tier == 'referral':
            has_access = session.get('referral_unlocked', False)

        if not has_access:
            return jsonify({
                "success": False,
                "error": f"Access denied. {companion_tier.title()} companions require a higher plan."
            }), 403

        # Store selection
        session['selected_companion_id'] = companion_id
        # Session expires when browser closes
        
        logger.info(f"Companion selected: {companion_id} by user {session.get('user_email')}")

        return jsonify({
            "success": True,
            "message": "Companion selected successfully",
            "companion_id": companion_id
        })

    except Exception as e:
        logger.error(f"Select companion error: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to select companion"
        }), 500

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