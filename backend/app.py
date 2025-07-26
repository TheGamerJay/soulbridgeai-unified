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

def login_success_response(redirect_to="/"):
    """Return appropriate response for successful login (JSON for AJAX, redirect for forms)"""
    # Simple check: if browser sent form data, redirect. If AJAX, return JSON.
    user_agent = request.headers.get('User-Agent', '')
    # Regular browsers doing form submission vs AJAX fetch calls
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'fetch' in user_agent.lower():
        return jsonify({"success": True, "redirect": redirect_to})
    else:
        return redirect(redirect_to)

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

@app.route("/")
def home():
    """Home route - redirect to login for security"""
    try:
        # Always require authentication for home page
        if not is_logged_in():
            return redirect("/login")
            
        # Ensure services are initialized for authenticated users
        if not services["database"]:
            initialize_services()
        
        user_plan = get_user_plan()
        
        # Allow all authenticated users to access the main app
        # Foundation plan users get access to basic features
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

@app.route("/auth/forgot-password")
def forgot_password_page():
    """Forgot password page (coming soon)"""
    try:
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
                    text-align: center;
                    background: rgba(0,0,0,0.8);
                    padding: 3rem;
                    border-radius: 16px;
                    border: 2px solid #22d3ee;
                    backdrop-filter: blur(15px);
                }
                h1 { color: #22d3ee; margin-bottom: 1.5rem; }
                p { margin: 1rem 0; line-height: 1.6; }
                .back-link { 
                    display: inline-block;
                    margin-top: 2rem;
                    padding: 12px 24px;
                    background: rgba(34, 211, 238, 0.1);
                    border: 2px solid #22d3ee;
                    color: #22d3ee; 
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    transition: all 0.3s ease;
                }
                .back-link:hover {
                    background: rgba(34, 211, 238, 0.2);
                    transform: translateY(-2px);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔐 Password Reset</h1>
                <p><strong>Password reset functionality is currently being developed!</strong></p>
                <p>For now, please try logging in with your existing credentials or contact support if you need assistance.</p>
                <a href="/login" class="back-link">← Back to Login</a>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Forgot password page error: {e}")
        return redirect("/login")

# ========================================
# OAUTH ROUTES
# ========================================

# Google OAuth routes removed - was causing issues

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
        
        # Create appropriate success message and redirect
        if plan_type == "foundation":
            message = "Welcome to SoulBridge AI! Your free plan is now active."
            redirect_url = "/?show_intro=true"
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
            
            return jsonify({
                "success": True,
                "database_path": db.db_path,
                "database_exists": os.path.exists(db.db_path),
                "user_count": user_count,
                "subscription_count": subscription_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            return jsonify({"success": False, "error": "Database unavailable"}), 503
            
    except Exception as e:
        logger.error(f"Database status error: {e}")
        return jsonify({"success": False, "error": "Status check failed"}), 500

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