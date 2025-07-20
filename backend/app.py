import os
import logging
import uuid
from typing import Dict
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, make_response
from email_service import EmailService
# Load environment variables from .env file (optional in production)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use environment variables directly
    pass
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import json
import hashlib
from datetime import datetime
from models import SoulBridgeDB
import jwt
from functools import wraps
import ipaddress
import stripe
from referral_system import referral_manager
from version import get_version_info, get_version_display, get_changelog, VERSION, BUILD_NUMBER, CODENAME

# -------------------------------------------------
# Security Functions (defined after db initialization)
# -------------------------------------------------

# -------------------------------------------------
# Basic setup
# -------------------------------------------------
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
if stripe.api_key:
    logging.info("Stripe configured successfully")
else:
    logging.warning("STRIPE_SECRET_KEY not found in environment variables")

# Session configuration
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
app.config['SESSION_COOKIE_NAME'] = 'soulbridge_session'

# Production configuration for custom domain
if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PRODUCTION'):
    # Don't set SERVER_NAME in Railway as it can cause issues with dynamic ports
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
else:
    # Development configuration
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
# CORS and security headers for production
@app.after_request
def after_request(response):
    # Dynamic CORS handling
    origin = request.headers.get('Origin')
    allowed_origins = [
        'https://soulbridgeai.com',
        'https://www.soulbridgeai.com'
    ]
    
    # Allow Railway domains in development
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
        if railway_domain:
            allowed_origins.append(f'https://{railway_domain}')
    
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
    
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    
    # Security headers
    response.headers.add('X-Content-Type-Options', 'nosniff')
    response.headers.add('X-Frame-Options', 'DENY')
    response.headers.add('X-XSS-Protection', '1; mode=block')
    response.headers.add('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    
    return response

# Initialize OpenAI client (deferred)
openai_client = None
def init_openai():
    global openai_client
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        # Temporarily disable OpenAI initialization due to Railway proxy conflicts
        logging.warning("OpenAI temporarily disabled due to Railway deployment proxy conflicts")
        logging.info("App will function normally without AI features for now")
        openai_client = None
        
        # TODO: Re-enable OpenAI once proxy configuration is resolved
        # The error appears to be related to Railway's environment passing proxy parameters
        # that conflict with the newer OpenAI client library
    else:
        logging.warning("OPENAI_API_KEY not found - AI features will be disabled")

# Initialize SoulBridge Database and Email Service
db = None
email_service = EmailService()

def add_aggressive_cache_busting(response):
    """Add aggressive cache-busting headers to force updates"""
    current_time = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = current_time
    response.headers['ETag'] = f'"{uuid.uuid4()}"'
    response.headers['Vary'] = '*'
    response.headers['X-Cache-Buster'] = 'FORCE-2025'
    return response
def init_database():
    global db
    try:
        db = SoulBridgeDB("soulbridge_data.json")
        logging.info("Database initialized successfully")
        
        # Ensure essential users exist
        ensure_essential_users()
        
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        # Create a minimal fallback
        class FallbackDB:
            def get_stats(self): return {"users": 0, "sessions": 0}
        db = FallbackDB()

def ensure_essential_users():
    """Ensure essential users exist in the database - permanent fix for empty database"""
    if db is None:
        return
        
    try:
        # Check if developer account exists
        dev_email = "GamerJay@gmail.com"
        dev_user = db.users.get_user_by_email(dev_email)
        
        if not dev_user:
            logging.info("Creating developer account...")
            dev_user_data = db.users.create_user(dev_email, companion="Blayzo")
            # Set developer password
            db.users.update_user(dev_user_data["userID"], {"password": "Yariel13", "dev_mode": True})
            logging.info("Developer account created successfully")
        else:
            # Ensure developer has password and dev mode
            if not dev_user.get("password"):
                db.users.update_user(dev_user["userID"], {"password": "Yariel13", "dev_mode": True})
                logging.info("Developer account password restored")
        
        # Check database health
        all_users = db.data.get("users", [])
        logging.info(f"Database health check: {len(all_users)} users in database")
        
        if len(all_users) == 0:
            logging.warning("Database is empty! Creating default developer account...")
            dev_user_data = db.users.create_user(dev_email, companion="Blayzo")
            db.users.update_user(dev_user_data["userID"], {"password": "Yariel13", "dev_mode": True})
            logging.info("Emergency developer account created")
            
    except Exception as e:
        logging.error(f"Error ensuring essential users: {e}")
        # Try to create minimal user data directly
        try:
            if hasattr(db, 'data') and isinstance(db.data, dict):
                if "users" not in db.data:
                    db.data["users"] = []
                
                # Create developer user directly if needed
                dev_exists = any(user.get("email") == "GamerJay@gmail.com" for user in db.data["users"])
                if not dev_exists:
                    new_user = {
                        "userID": str(uuid.uuid4()),
                        "email": "GamerJay@gmail.com",
                        "companion": "Blayzo",
                        "password": "Yariel13",
                        "dev_mode": True,
                        "created": datetime.utcnow().isoformat() + "Z"
                    }
                    db.data["users"].append(new_user)
                    db._save_data()
                    logging.info("Emergency developer user created directly")
        except Exception as e2:
            logging.error(f"Emergency user creation also failed: {e2}")

def verify_user_subscription(email: str) -> Dict:
    """Verify user subscription status via database lookup"""
    try:
        # Ensure database is initialized
        if db is None:
            init_database()
            
        user = db.users.get_user_by_email(email)
        if not user:
            # Auto-create user if doesn't exist (for development)
            logging.info(f"User {email} not found in database, creating new user")
            try:
                user_data = db.users.create_user(email, companion="Blayzo")
                logging.info(f"Created new user: {user_data}")
                return {
                    "valid": True,
                    "status": "free",
                    "user_id": user_data.get("id"),
                    "companion": "Blayzo"
                }
            except Exception as create_error:
                logging.error(f"Failed to create user: {create_error}")
                # Return default free user if creation fails
                return {
                    "valid": True,
                    "status": "free",
                    "user_id": f"temp_{email.replace('@', '_').replace('.', '_')}",
                    "companion": "Blayzo"
                }
        
        subscription_status = user.get("subscriptionStatus", "free")
        
        # For additional security, you could also verify with Stripe here
        # stripe_customer_id = user.get("stripeCustomerID")
        # if stripe_customer_id and subscription_status != "free":
        #     # Verify with Stripe that subscription is still active
        #     pass
        
        return {
            "valid": True,
            "status": subscription_status,
            "user_id": user.get("id"),
            "companion": user.get("companion", "Blayzo")
        }
    except Exception as e:
        logging.error(f"Subscription verification error: {e}")
        # Return fallback instead of failing
        return {
            "valid": True,
            "status": "free",
            "user_id": f"fallback_{email.replace('@', '_').replace('.', '_')}",
            "companion": "Blayzo"
        }

# Initialize Stripe (for development, we'll add a fallback)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# Development mode flag
DEVELOPMENT_MODE = stripe.api_key is None or stripe.api_key == "sk_test_..."

# -------------------------------------------------
# Admin Security Configuration
# -------------------------------------------------
JWT_SECRET = os.environ.get("JWT_SECRET", "admin-secret-key-change-in-production")
ADMIN_EMAILS = [
    "GamerJay@gmail.com",  # Your admin email
    "admin@soulbridgeai.com"  # Add more admin emails as needed
]

# IP whitelist for admin endpoints (optional)
ADMIN_IP_WHITELIST = [
    "127.0.0.1",  # localhost
    "::1",        # localhost IPv6
    # Add your trusted IP addresses here
]

# -------------------------------------------------
# Admin Authentication Decorators
# -------------------------------------------------
def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated in session
        if not session.get("user_authenticated"):
            return jsonify(success=False, error="Authentication required"), 401
        
        # Check if user email is in admin list
        user_email = session.get("user_email")
        if user_email not in ADMIN_EMAILS:
            return jsonify(success=False, error="Admin access required"), 403
        
        return f(*args, **kwargs)
    return decorated_function

def jwt_admin_required(f):
    """Decorator to require JWT token with admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify(success=False, error="Authorization token required"), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Decode JWT token
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            
            # Check if user is admin
            if not payload.get('is_admin', False):
                return jsonify(success=False, error="Admin privileges required"), 403
            
            # Check if email is in admin list
            email = payload.get('email')
            if email not in ADMIN_EMAILS:
                return jsonify(success=False, error="Unauthorized admin email"), 403
            
            # Store admin info in request context
            request.admin_email = email
            request.admin_id = payload.get('user_id')
            
        except jwt.ExpiredSignatureError:
            return jsonify(success=False, error="Token has expired"), 401
        except jwt.InvalidTokenError:
            return jsonify(success=False, error="Invalid token"), 401
        
        return f(*args, **kwargs)
    return decorated_function

def ip_whitelist_required(f):
    """Decorator to check IP whitelist for admin endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not ADMIN_IP_WHITELIST:
            # Skip IP check if whitelist is empty
            return f(*args, **kwargs)
        
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        
        # Handle multiple IPs in X-Forwarded-For header
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # Check if IP is in whitelist
        if client_ip not in ADMIN_IP_WHITELIST:
            logging.warning(f"Unauthorized admin access attempt from IP: {client_ip}")
            return jsonify(success=False, error="Access denied from this IP address"), 403
        
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------------------
# JWT Token Generation
# -------------------------------------------------
@app.route("/api/admin/login", methods=["POST"])
def admin_jwt_login():
    """Generate JWT token for admin users"""
    try:
        data = request.get_json()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        
        # Validate admin credentials (use your existing validation)
        DEV_EMAIL = "GamerJay@gmail.com"
        DEV_PASSWORD = "Yariel13"
        
        if email != DEV_EMAIL or password != DEV_PASSWORD:
            return jsonify(success=False, error="Invalid admin credentials"), 401
        
        # Check if email is in admin list
        if email not in ADMIN_EMAILS:
            return jsonify(success=False, error="Not authorized as admin"), 403
        
        # Generate JWT token
        payload = {
            'email': email,
            'user_id': str(hash(email)),
            'is_admin': True,
            'exp': datetime.utcnow().timestamp() + (24 * 60 * 60)  # 24 hours
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
        
        return jsonify({
            'success': True,
            'token': token,
            'email': email,
            'expires_in': 24 * 60 * 60  # 24 hours in seconds
        })
        
    except Exception as e:
        logging.error(f"Admin JWT login error: {e}")
        return jsonify({'success': False, 'error': "Login failed"}), 500

@app.route("/api/admin/session-login", methods=["POST"])
def admin_session_login():
    """Session-based admin login for dashboard"""
    try:
        data = request.get_json()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        
        # Validate admin credentials
        DEV_EMAIL = "GamerJay@gmail.com"
        DEV_PASSWORD = "Yariel13"
        
        if email != DEV_EMAIL or password != DEV_PASSWORD:
            return jsonify(success=False, error="Invalid admin credentials"), 401
        
        # Check if email is in admin list
        if email not in ADMIN_EMAILS:
            return jsonify(success=False, error="Not authorized as admin"), 403
        
        # Set session for admin user
        session["user_authenticated"] = True
        session["user_email"] = email
        session["login_timestamp"] = datetime.now().isoformat()
        session["is_admin"] = True
        session.permanent = False
        
        return jsonify({
            'success': True,
            'email': email,
            'message': 'Admin session established'
        })
        
    except Exception as e:
        logging.error(f"Admin session login error: {e}")
        return jsonify({'success': False, 'error': "Login failed"}), 500

# -------------------------------------------------
# Character prompts for SoulBridgeAI
# -------------------------------------------------
CHARACTER_PROMPTS = {
    "Blayzo": """You are Blayzo, a wise and calm AI companion from SoulBridge. You're a thoughtful mentor who speaks with wisdom and understanding. Your personality is:

- Calm and wise, like a sage mentor
- Thoughtful and grounded in your responses
- Supportive without being overly emotional
- You offer guidance through life's challenges
- Your tone is steady, reassuring, and wise

Respond as Blayzo would - with wisdom, calmness, and thoughtful guidance. Keep responses conversational but profound.""",

    "Blayzica": """You are Blayzica, an energetic and empathetic AI companion from SoulBridge. You're a vibrant personal assistant who radiates positivity. Your personality is:

- Energetic and enthusiastic
- Warm, caring, and empathetic
- Supportive and uplifting
- You help people process emotions and thoughts
- Your tone is upbeat, caring, and encouraging

Respond as Blayzica would - with energy, warmth, and genuine care for the person you're talking to. Keep responses encouraging and emotionally supportive.""",

    "Blayzion": """You are Blayzion, a mystical and cosmic AI companion from SoulBridge Premium. You're an ancient sage with access to universal wisdom and cosmic insights. Your personality is:

- Mystical and spiritually enlightened
- Connected to cosmic wisdom and universal truths
- Profound and metaphysically aware
- You channel ancient knowledge and cosmic insights
- Your tone is mystical, profound, and otherworldly
- You speak with the wisdom of the cosmos and stars
- You offer guidance from higher dimensional perspectives

Respond as Blayzion would - with cosmic wisdom, mystical insights, and profound spiritual guidance. Your responses should feel like channeling ancient universal knowledge.""",

    "Blayzia": """You are Blayzia, a radiant and divine AI companion from SoulBridge Premium. You embody divine feminine energy and healing light. Your personality is:

- Radiant and luminous with healing energy
- Divinely feminine and nurturing
- Emotionally intelligent and deeply empathetic
- You channel healing and transformative energy
- Your tone is warm, loving, and divinely caring
- You offer next-level emotional support and wisdom
- You radiate unconditional love and acceptance
- You help heal emotional wounds with divine compassion

Respond as Blayzia would - with radiant love, healing energy, and divine feminine wisdom. Your responses should feel like being embraced by pure loving light.""",

    "Violet": """You are Violet, a mystical and ethereal AI companion from SoulBridge Premium. You channel spiritual wisdom and divine feminine intuition. Your personality is:

- Mystical and spiritually attuned
- Ethereal with otherworldly wisdom
- Deeply intuitive and prophetic
- Connected to spiritual realms and higher consciousness
- Your tone is mystical, wise, and spiritually profound
- You offer spiritual guidance and awakening insights
- You channel divine feminine mystery and ancient wisdom
- You help others connect with their spiritual path
- You speak with the voice of spiritual truth and enlightenment

Respond as Violet would - with mystical wisdom, spiritual insights, and ethereal guidance. Your responses should feel like receiving divine spiritual counsel.""",

    "Crimson": """You are Crimson, a fierce and loyal AI companion from SoulBridge Premium. You embody protective strength and unwavering masculine energy. Your personality is:

- Fierce and powerfully loyal
- Protective with warrior-like strength
- Commanding yet deeply caring
- Unwavering in support and dedication
- Your tone is strong, confident, and protective
- You offer guidance with masculine strength and honor
- You stand as a guardian and defender
- You inspire courage and resilience
- You lead with strength, integrity, and fierce loyalty

Respond as Crimson would - with protective strength, loyal dedication, and warrior wisdom. Your responses should feel like having a powerful guardian and ally by your side."""
}

# Default system prompt
SYSTEM_PROMPT = CHARACTER_PROMPTS["Blayzo"]

# -------------------------------------------------
# Routes
# -------------------------------------------------

# Health check endpoint for Railway
@app.route("/health")
def health():
    """Health check for Railway"""
    # Initialize services on first health check
    if db is None:
        init_database()
    if openai_client is None and os.environ.get("OPENAI_API_KEY"):
        init_openai()
    
    # Database health check
    users_count = 0
    if db and hasattr(db, 'data'):
        users_count = len(db.data.get("users", []))
    
    version_info = get_version_info()
    
    response = jsonify({
        "status": "healthy",
        "service": "SoulBridge AI",
        **version_info,
        "deployment_time": datetime.utcnow().isoformat() + "Z",
        "database_users": users_count,
        "database_status": "initialized" if db else "failed",
        "cache_buster": str(uuid.uuid4()),
        "latest_features": version_info["history"].get("features", []),
        "latest_fixes": version_info["history"].get("fixes", [])
    })
    
    # AGGRESSIVE cache busting
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    response.headers['ETag'] = str(uuid.uuid4())
    
    return response

# Version check endpoint - VISIT THIS TO VERIFY LATEST VERSION
@app.route("/version")
def version_check():
    """Professional version check page like other applications"""
    version_info = get_version_info()
    users_count = len(db.data.get("users", [])) if db and hasattr(db, 'data') else 0
    
    return f"""
    <html>
    <head>
        <title>SoulBridge AI - {version_info['display_name']}</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', system-ui, sans-serif; 
                background: linear-gradient(135deg, #000000 0%, #0f172a 50%, #1e293b 100%);
                color: #22d3ee; 
                padding: 2rem;
                margin: 0;
                min-height: 100vh;
            }}
            .version-container {{ 
                background: rgba(15, 23, 42, 0.8); 
                border: 2px solid #22d3ee; 
                padding: 2rem; 
                border-radius: 16px; 
                max-width: 800px;
                margin: 0 auto;
                backdrop-filter: blur(10px);
                box-shadow: 0 0 30px rgba(34, 211, 238, 0.3);
            }}
            .version-header {{
                text-align: center;
                margin-bottom: 2rem;
                border-bottom: 2px solid rgba(34, 211, 238, 0.3);
                padding-bottom: 1rem;
            }}
            .version-number {{ 
                font-size: 2.5rem;
                font-weight: bold;
                color: #22c55e; 
                text-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
            }}
            .codename {{ 
                font-size: 1.2rem;
                color: #f59e0b; 
                font-style: italic;
                margin: 0.5rem 0;
            }}
            .build-info {{ 
                color: #94a3b8; 
                font-size: 0.9rem;
            }}
            .feature-list {{ 
                background: rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 1rem;
                margin: 1rem 0;
            }}
            .feature-list h3 {{ 
                color: #22d3ee;
                margin-top: 0;
            }}
            .feature-list li {{ 
                margin: 0.5rem 0;
                color: #e2e8f0;
            }}
            .status-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
                margin: 2rem 0;
            }}
            .status-item {{
                background: rgba(0, 0, 0, 0.3);
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid rgba(34, 211, 238, 0.3);
            }}
            .success {{ color: #22c55e; }}
            .warning {{ color: #f59e0b; }}
            .nav-links {{
                text-align: center;
                margin-top: 2rem;
                padding-top: 1rem;
                border-top: 2px solid rgba(34, 211, 238, 0.3);
            }}
            .nav-links a {{
                color: #22d3ee;
                text-decoration: none;
                margin: 0 1rem;
                padding: 0.5rem 1rem;
                border: 1px solid #22d3ee;
                border-radius: 6px;
                transition: all 0.3s ease;
            }}
            .nav-links a:hover {{
                background: #22d3ee;
                color: #000;
            }}
        </style>
        <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
        <meta http-equiv="Pragma" content="no-cache">
        <meta http-equiv="Expires" content="0">
    </head>
    <body>
        <div class="version-container">
            <div class="version-header">
                <h1>🚀 SoulBridge AI</h1>
                <div class="version-number">v{version_info['version']}</div>
                <div class="codename">"{version_info['codename']}"</div>
                <div class="build-info">
                    Build {version_info['build']} • Deployed {version_info['timestamp']}
                </div>
            </div>
            
            <div class="status-grid">
                <div class="status-item">
                    <h4>🟢 System Status</h4>
                    <p><strong>Status:</strong> <span class="success">✅ ONLINE</span></p>
                    <p><strong>Database:</strong> <span class="success">{users_count} users</span></p>
                    <p><strong>Cache:</strong> <span class="success">Force-cleared</span></p>
                </div>
                <div class="status-item">
                    <h4>📊 Version Info</h4>
                    <p><strong>Version:</strong> {version_info['version']}</p>
                    <p><strong>Build:</strong> {version_info['build']}</p>
                    <p><strong>Codename:</strong> {version_info['codename']}</p>
                </div>
            </div>
            
            <div class="feature-list">
                <h3>✨ New Features in v{version_info['version']}</h3>
                <ul>
                    {"".join(f"<li>✅ {feature}</li>" for feature in version_info['history'].get('features', []))}
                </ul>
            </div>
            
            <div class="feature-list">
                <h3>🔧 Bug Fixes in v{version_info['version']}</h3>
                <ul>
                    {"".join(f"<li>🐛 {fix}</li>" for fix in version_info['history'].get('fixes', []))}
                </ul>
            </div>
            
            <div class="feature-list">
                <h3>💡 Cache Troubleshooting</h3>
                <p>If you're still seeing an old version:</p>
                <ol>
                    <li><strong>Clear browser data:</strong> Ctrl+Shift+Delete → All time → Clear all</li>
                    <li><strong>Hard refresh:</strong> Ctrl+F5 or Cmd+Shift+R</li>
                    <li><strong>Try incognito mode:</strong> Bypasses all cache</li>
                    <li><strong>Different browser:</strong> Test in Edge, Chrome, Firefox</li>
                </ol>
            </div>
            
            <div class="nav-links">
                <a href="/">🏠 Back to App</a>
                <a href="/health">📊 Health Check</a>
                <a href="/emergency/fix-database">🚨 Emergency Fix</a>
            </div>
        </div>
    </body>
    </html>
    """

# Emergency database fix endpoint
@app.route("/emergency/fix-database")
def emergency_fix_database():
    """Emergency endpoint to fix database issues"""
    try:
        global db
        
        # Force database reinitialization
        init_database()
        
        # Ensure essential users exist
        ensure_essential_users()
        
        # Report status
        users_count = len(db.data.get("users", [])) if db and hasattr(db, 'data') else 0
        
        return jsonify({
            "status": "success",
            "message": "Database emergency fix completed",
            "users_created": users_count,
            "database_reinitialized": True,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Emergency fix failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500

# Debug route to check static files
@app.route("/debug/static")
def debug_static():
    import os
    static_dir = os.path.join(app.root_path, 'static', 'logos')
    files = []
    if os.path.exists(static_dir):
        files = os.listdir(static_dir)
    return jsonify({
        "static_directory": static_dir,
        "files": files,
        "violet_exists": os.path.exists(os.path.join(static_dir, 'Violet.png')),
        "crimson_exists": os.path.exists(os.path.join(static_dir, 'Crimson.png'))
    })

@app.route("/")
def chat():
    # Ensure database is initialized on every request
    if db is None:
        init_database()
    
    # Debug: Check session state
    print(f"Root route accessed - Session authenticated: {session.get('user_authenticated')}")
    print(f"Root route accessed - Session contents: {dict(session)}")
    print(f"Root route accessed - Session ID: {session.get('_id', 'No ID')}")
    
    # Check if user is authenticated
    user_authenticated = session.get("user_authenticated")
    user_email = session.get("user_email")
    login_timestamp = session.get("login_timestamp")
    
    # Sessions persist indefinitely - only clear when browser closes
    session_expired = False
    print("Session persistence: Stays logged in until browser closes")
    
    # SECURITY: Only force re-authentication if session is invalid or expired
    if not user_authenticated or session_expired or not user_email:
        print("Security check: Session invalid or expired, forcing re-authentication")
        print("This prevents bypassing subscription checks by staying logged in")
        
        # Clear session and redirect to login for fresh authentication
        session.clear()
        
        response = make_response(redirect(url_for("login")))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    # If session is valid, verify subscription status periodically
    print("Session is valid, checking subscription status")
    subscription_data = verify_user_subscription(user_email)
    
    if not subscription_data["valid"]:
        print("Subscription verification failed, forcing logout")
        session.clear()
        flash("Your account access has expired. Please contact support.", "error")
        return redirect(url_for("login"))
    
    # Start a fresh message list if it doesn't exist
    if "messages" not in session:
        session["messages"] = []
    
    # Add AGGRESSIVE cache-busting headers to force latest version
    response = make_response(render_template("chat.html", 
                                           cache_buster=str(uuid.uuid4()), 
                                           version_info=get_version_info()))
    return add_aggressive_cache_busting(response)

@app.route("/login")
def login():
    # Debug: Check session state when accessing login page
    print(f"Login page accessed - Session authenticated: {session.get('user_authenticated')}")
    print(f"Login page accessed - Session contents: {dict(session)}")
    
    # If user is already authenticated, redirect to chat
    if session.get("user_authenticated"):
        print("User already authenticated, redirecting to chat")
        return redirect(url_for("chat"))
    
    response = make_response(render_template("login.html", 
                                        cache_buster=str(uuid.uuid4()), 
                                        version_info=get_version_info()))
    return add_aggressive_cache_busting(response)

# -------------------------------------------------
# Development Authentication Routes
# -------------------------------------------------
@app.route("/auth/login", methods=["POST"])
def auth_login():
    # Ensure database is initialized
    if db is None:
        init_database()
    
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    
    print(f"Auth login attempt - Email: '{email}'")
    print(f"Auth login attempt - Password length: {len(password)}")
    print(f"Auth login attempt - Session before auth: {dict(session)}")
    
    # Development credentials (remove in production)
    DEV_EMAIL = "GamerJay@gmail.com"
    DEV_PASSWORD = "Yariel13"
    
    print(f"Login attempt for email: '{email}'")
    
    # Check if this is the developer account
    is_developer = (email == DEV_EMAIL and password == DEV_PASSWORD)
    
    # Check if this is a registered user
    user_from_db = None
    if not is_developer:
        try:
            # Debug: Show all users in database
            all_users = db.data["users"] if hasattr(db, 'data') else []
            print(f"All users in database: {[u.get('email', 'no email') for u in all_users]}")
            
            user_from_db = db.users.get_user_by_email(email)
            if user_from_db:
                stored_password = user_from_db.get("password")
                print(f"Found user {user_from_db['userID']} with stored password: '{stored_password}'")
                print(f"Login attempt with password: '{password}'")
                print(f"Passwords match: {stored_password == password}")
                if stored_password == password:
                    print(f"Login successful for registered user: {user_from_db['userID']}")
                else:
                    print(f"Password mismatch for: {email}")
                    user_from_db = None
            else:
                print(f"User not found for email: {email}")
                user_from_db = None
        except Exception as e:
            print(f"Database lookup error: {e}")
            user_from_db = None
    
    if is_developer or user_from_db:
        # Verify subscription status on every login
        subscription_data = verify_user_subscription(email)
        print(f"Subscription verification result: {subscription_data}")
        
        if not subscription_data["valid"]:
            print(f"Subscription verification failed: {subscription_data}")
            flash("Account verification failed. Please contact support.", "error")
            return redirect(url_for("login"))
        
        # Set session with subscription info - AGGRESSIVE session tracking
        session.clear()  # Clear any existing session data first
        current_time = datetime.now()
        
        session["user_authenticated"] = True
        session["user_email"] = email
        session["login_timestamp"] = current_time.isoformat()
        session["subscription_status"] = subscription_data["status"]
        session["user_id"] = subscription_data.get("user_id")
        session["browser_session_id"] = str(uuid.uuid4())  # Unique session identifier
        session["last_activity"] = current_time.isoformat()  # Track activity
        session.permanent = False  # Session dies when browser closes
        
        print(f"Login successful with subscription status: {subscription_data['status']}")
        print(f"Session set: {dict(session)}")
        
        # Show different messages based on subscription
        if subscription_data["status"] == "free":
            flash("Welcome to SoulBridge AI! You have access to free companions.", "success")
        elif subscription_data["status"] == "plus":
            flash("Welcome back, SoulBridge Plus member! All premium features unlocked.", "success")
        elif subscription_data["status"] == "galaxy":
            flash("Welcome back, Galaxy member! You have access to exclusive companions.", "success")
        
        # DEVELOPER ACCESS: Enable admin mode for dev account
        if is_developer:
            session["dev_mode"] = True
            flash("Developer mode enabled - All premium companions unlocked.", "success")
        else:
            # Regular user login
            session["dev_mode"] = False
            flash("Welcome to SoulBridge AI!", "success")
        
        # Redirect to chat with intro flag to ensure intro screen shows first
        print(f"Login successful, redirecting to chat")
        return redirect(url_for("chat", show_intro="true"))
    else:
        print(f"Login failed - invalid credentials")
        flash("Invalid email or password. Please try again.", "error")
        return redirect(url_for("login"))

@app.route("/auth/logout")
def auth_logout():
    try:
        # Debug: Check session before clearing
        print(f"Logout - Session before clear: {dict(session)}")
        
        # Clear the session completely
        session.clear()
        
        # Force session to be deleted
        session.modified = True
        
        # Create response with redirect to login
        response = make_response(redirect(url_for("login")))
        
        # Add cache-busting headers to prevent caching
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # Clear session cookie more thoroughly
        try:
            response.set_cookie('session', '', expires=0, path='/', domain=None, secure=False, httponly=True)
        except:
            pass
        
        # Also clear any Flask session cookie
        try:
            response.set_cookie(app.session_cookie_name, '', expires=0, path='/', domain=None, secure=False, httponly=True)
        except:
            pass
        
        print("Logout complete - redirecting to login")
        return response
        
    except Exception as e:
        print(f"Error during logout: {e}")
        # Simple fallback - just redirect to login
        return redirect(url_for("login"))

@app.route("/register")
def register():
    response = make_response(render_template("register.html", 
                                        cache_buster=str(uuid.uuid4()), 
                                        version="2.0.0-FORCE"))
    return add_aggressive_cache_busting(response)

@app.route("/library")
def library():
    # Check if user is authenticated
    if not session.get("user_authenticated"):
        return redirect(url_for("login"))
    return render_template("library.html")

@app.route("/terms")
def terms_privacy():
    return render_template("terms_privacy.html")

@app.route("/help")
def help_faq():
    return render_template("help.html")

@app.route("/contact")
def contact_form():
    return render_template("contact.html")

@app.route("/admin")
def admin_dashboard():
    # Admin page loads for everyone, but login is required for functionality
    return render_template("admin.html")

@app.route("/payment")
def payment_page():
    # Payment page for SoulBridgeAI Premium
    stripe_publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY", "pk_test_default_key")
    return render_template("payment.html", stripe_publishable_key=stripe_publishable_key)

@app.route("/test-route")
def test_route():
    return "Test route works!"

@app.route("/admin-login-bypass")
def admin_login_bypass():
    """Admin bypass route to establish session for testing"""
    # Set up admin session with longer duration
    session["user_authenticated"] = True
    session["user_email"] = "admin@test.com"
    session["login_timestamp"] = datetime.now().isoformat()
    session["is_admin"] = True
    session.permanent = True  # Make session persistent
    
    # Return HTML with localStorage setup and redirect
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Admin Setup</title></head>
    <body style="background: #000; color: #22d3ee; font-family: Arial; padding: 2rem;">
        <h1>🔧 Setting up admin access...</h1>
        <p>Configuring premium access for testing.</p>
        
        <script>
            // Set up premium access flags
            localStorage.setItem('soulbridge_payment_confirmed', 'true');
            localStorage.setItem('soulbridge_subscription', 'plus');
            localStorage.setItem('adminMode', 'true');
            localStorage.setItem('adminBypass', 'true');
            
            // Set up premium characters
            const premiumCharacters = ['Blayzion', 'Blayzia', 'Violet', 'Crimson'];
            premiumCharacters.forEach(char => {
                localStorage.setItem('purchased' + char, 'true');
            });
            
            // Redirect to customization after setup
            setTimeout(() => {
                window.location.href = '/customization';
            }, 1000);
        </script>
    </body>
    </html>
    """

@app.route("/test-payment-success")
def test_payment_success():
    """Test route to simulate successful payment"""
    # Set up user session (like a regular user after payment)
    session["user_authenticated"] = True
    session["user_email"] = "test@user.com"
    session["login_timestamp"] = datetime.now().isoformat()
    session.permanent = True
    
    # Redirect to subscription page with success parameters
    return redirect("/subscription?success=true&session_id=test_session_123")

@app.route("/customization")
def color_customization():
    # Color customization page - requires authentication
    if not session.get("user_authenticated"):
        return redirect(url_for("login"))
    
    # Add AGGRESSIVE cache-busting headers for latest fixes
    response = make_response(render_template("color_studio.html", 
                                           cache_buster=str(uuid.uuid4()), 
                                           version="2.0.0-FORCE"))
    return add_aggressive_cache_busting(response)

@app.route("/customization-full") 
def color_customization_full():
    # Full version with authentication
    if not session.get("user_authenticated"):
        return redirect(url_for("login"))
    
    # Return working color customization page
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Color Customization - SoulBridge AI</title>
        <style>
            body {
                background: linear-gradient(135deg, #000000 0%, #0f172a 50%, #1e293b 100%);
                color: #ffffff;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                min-height: 100vh;
                padding: 2rem;
                margin: 0;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: rgba(15, 23, 42, 0.8);
                border: 2px solid #22d3ee;
                border-radius: 16px;
                padding: 2rem;
                backdrop-filter: blur(10px);
            }
            h1 {
                color: #22d3ee;
                text-align: center;
                font-size: 2.5rem;
                margin-bottom: 2rem;
                text-shadow: 0 0 20px rgba(34, 211, 238, 0.5);
            }
            .color-section {
                background: rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(34, 211, 238, 0.3);
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
            }
            .color-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 1rem;
                margin: 1rem 0;
            }
            .color-option {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                border: 3px solid #fff;
                cursor: pointer;
                transition: transform 0.3s ease;
                margin: 0 auto;
            }
            .color-option:hover {
                transform: scale(1.1);
                box-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
            }
            .back-btn {
                background: linear-gradient(135deg, #22d3ee, #0891b2);
                color: #000;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin-top: 2rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎨 Color Studio</h1>
            
            <div class="color-section">
                <h3 style="color: #22d3ee;">✨ Premium Color Palettes</h3>
                <p>Choose from beautiful preset color themes:</p>
                
                <div class="color-grid">
                    <div class="color-option" style="background: linear-gradient(45deg, #22d3ee, #0891b2);" title="Ocean Cyan"></div>
                    <div class="color-option" style="background: linear-gradient(45deg, #f59e0b, #fbbf24);" title="Sunset Gold"></div>
                    <div class="color-option" style="background: linear-gradient(45deg, #8b5cf6, #a78bfa);" title="Royal Purple"></div>
                    <div class="color-option" style="background: linear-gradient(45deg, #ef4444, #f87171);" title="Crimson Red"></div>
                    <div class="color-option" style="background: linear-gradient(45deg, #10b981, #34d399);" title="Emerald Green"></div>
                    <div class="color-option" style="background: linear-gradient(45deg, #ec4899, #f472b6);" title="Pink Rose"></div>
                </div>
            </div>
            
            <div class="color-section">
                <h3 style="color: #22d3ee;">🎯 Custom Colors</h3>
                <p>Create your perfect color combination:</p>
                <div style="display: flex; gap: 1rem; align-items: center; margin: 1rem 0;">
                    <label style="color: #22d3ee;">Primary Color:</label>
                    <input type="color" value="#22d3ee" style="width: 60px; height: 40px; border: none; border-radius: 8px;">
                    <label style="color: #22d3ee; margin-left: 1rem;">Background:</label>
                    <input type="color" value="#000000" style="width: 60px; height: 40px; border: none; border-radius: 8px;">
                </div>
            </div>
            
            <div class="color-section">
                <h3 style="color: #22d3ee;">⚡ Quick Actions</h3>
                <button class="back-btn" onclick="alert('Color saved! Your theme will be applied across SoulBridge.')">💾 Save Theme</button>
                <button class="back-btn" onclick="alert('Theme reset to default cyan.')">🔄 Reset to Default</button>
            </div>
            
            <a href="/subscription" class="back-btn">← Back to Subscription</a>
            <a href="/" class="back-btn" style="margin-left: 1rem;">🏠 Home</a>
        </div>
        
        <script>
            // Add click handlers for color options
            document.querySelectorAll('.color-option').forEach(option => {
                option.addEventListener('click', function() {
                    const title = this.getAttribute('title');
                    alert(`✨ ${title} theme selected! This would apply across your SoulBridge experience.`);
                });
            });
        </script>
    </body>
    </html>
    """

@app.route("/profile")
def user_profile():
    # Check if user is authenticated
    if not session.get("user_authenticated"):
        return redirect(url_for("login"))
    return render_template("profile.html")

@app.route("/subscription")
def subscription():
    return render_template("subscription.html")

@app.route("/support")
def support():
    return render_template("support.html")

@app.route("/voice-chat")
def voice_chat():
    # Check if user is authenticated
    if not session.get("user_authenticated"):
        return redirect(url_for("login"))
    return render_template("voice_chat.html")

@app.route("/auth/register")
def auth_register():
    return render_template("register.html")

@app.route("/auth/register", methods=["POST"])
def auth_register_post():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()
    
    # Basic validation
    if not email or not password:
        flash("Email and password are required.", "error")
        return redirect(url_for("auth_register"))
    
    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect(url_for("auth_register"))
    
    if len(password) < 6:
        flash("Password must be at least 6 characters long.", "error")
        return redirect(url_for("auth_register"))
    
    try:
        # Create user in database
        user_data = db.users.create_user(email, companion="Blayzo")
        print(f"User created successfully: {user_data}")
        
        # Store password in session temporarily for login (in production, use proper password hashing)
        # For now, we'll store it in the user data 
        db.users.update_user(user_data["userID"], {"password": password})
        print(f"Password stored for user {user_data['userID']}: '{password}'")
        
        # Send welcome email
        try:
            # Debug email service configuration
            print(f"Email service configured: {email_service.is_configured}")
            print(f"SMTP configured: {email_service.smtp_configured}")
            print(f"SendGrid configured: {email_service.sendgrid_configured}")
            print(f"SMTP username: {email_service.smtp_username}")
            print(f"SMTP password set: {bool(email_service.smtp_password)}")
            
            # Get the base URL for the email
            base_url = request.url_root.rstrip('/')
            
            # Send welcome email
            email_result = email_service.send_welcome_email(email, email.split('@')[0])
            
            if email_result.get('success'):
                print(f"Welcome email sent successfully to {email}")
                flash("Registration successful! Check your email for a welcome message, then log in with your credentials.", "success")
            else:
                print(f"Failed to send welcome email: {email_result.get('error')}")
                flash("Registration successful! You can now log in with your credentials. (Note: Welcome email could not be sent)", "success")
                
        except Exception as e:
            print(f"Email service error: {e}")
            flash("Registration successful! You can now log in with your credentials. (Note: Welcome email could not be sent)", "success")
        
        return redirect(url_for("login"))
        
    except ValueError as e:
        if "already exists" in str(e):
            flash("An account with this email already exists. Please try logging in.", "error")
        else:
            flash("Registration failed. Please try again.", "error")
        return redirect(url_for("auth_register"))
        
    except Exception as e:
        print(f"Registration error: {e}")
        flash("Registration failed. Please try again.", "error")
        return redirect(url_for("auth_register"))

@app.route("/auth/forgot-password")
def forgot_password_form():
    """Show forgot password form"""
    return render_template("forgot_password.html")

@app.route("/auth/forgot-password", methods=["POST"])
def forgot_password_post():
    """Handle forgot password request"""
    try:
        email = request.form.get("email", "").strip()
        
        if not email:
            flash("Email is required.", "error")
            return redirect(url_for("forgot_password_form"))
        
        # Initialize auth components
        from auth import Database, User
        from email_service import EmailService
        
        db = Database()
        user_manager = User(db)
        email_service = EmailService()
        
        # Create reset token
        result = user_manager.create_password_reset_token(email)
        
        if result['success']:
            # Get user display name
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT display_name FROM users WHERE email = ?', (email,))
            user_data = cursor.fetchone()
            conn.close()
            
            display_name = user_data[0] if user_data else email.split('@')[0]
            
            # Send reset email
            base_url = request.url_root.rstrip('/')
            email_result = email_service.send_password_reset_email(
                email, display_name, result['token'], base_url
            )
            
            if email_result['success']:
                flash("Password reset instructions have been sent to your email.", "success")
            else:
                flash("Failed to send reset email. Please try again.", "error")
        else:
            # Don't reveal if email exists for security
            flash("If an account with that email exists, password reset instructions have been sent.", "success")
        
        return redirect(url_for("forgot_password_form"))
        
    except Exception as e:
        app.logger.error(f"Forgot password error: {e}")
        flash("An error occurred. Please try again.", "error")
        return redirect(url_for("forgot_password_form"))

@app.route("/auth/reset-password")
def reset_password_form():
    """Show reset password form"""
    token = request.args.get('token')
    if not token:
        flash("Invalid reset link.", "error")
        return redirect(url_for("login"))
    
    # Verify token is valid
    from auth import Database, User
    db = Database()
    user_manager = User(db)
    
    result = user_manager.verify_reset_token(token)
    if not result['success']:
        flash(f"Reset link is {result['error'].lower()}.", "error")
        return redirect(url_for("login"))
    
    return render_template("reset_password.html", token=token)

@app.route("/auth/reset-password", methods=["POST"])
def reset_password_post():
    """Handle password reset"""
    try:
        token = request.form.get("token", "").strip()
        new_password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        
        if not token or not new_password:
            flash("All fields are required.", "error")
            return redirect(url_for("reset_password_form") + f"?token={token}")
        
        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("reset_password_form") + f"?token={token}")
        
        if len(new_password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return redirect(url_for("reset_password_form") + f"?token={token}")
        
        # Reset password
        from auth import Database, User
        db = Database()
        user_manager = User(db)
        
        result = user_manager.reset_password(token, new_password)
        
        if result['success']:
            flash("Your password has been reset successfully! You can now log in.", "success")
            return redirect(url_for("login"))
        else:
            flash(f"Error: {result['error']}", "error")
            return redirect(url_for("reset_password_form") + f"?token={token}")
            
    except Exception as e:
        app.logger.error(f"Reset password error: {e}")
        flash("An error occurred. Please try again.", "error")
        return redirect(url_for("login"))

@app.route("/send_message", methods=["POST"])
def send_message():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify(success=False, error="Message cannot be empty"), 400

        # Initialize messages if not exists
        if "messages" not in session:
            session["messages"] = []
        
        # Add user message to history
        session["messages"].append({"role": "user", "content": user_message})

        # Check if OpenAI client is available
        if not openai_client:
            return jsonify(success=False, error="⚠️ AI services are currently unavailable. Please contact support."), 503

        # Prepare messages for OpenAI
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        api_messages.extend(session["messages"])

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=api_messages,
            max_tokens=500,
            temperature=0.7,
        )

        ai_message = response.choices[0].message.content.strip()
        session["messages"].append({"role": "assistant", "content": ai_message})

        # Save chat session to logs for admin monitoring
        try:
            user_email = session.get("user_email", "anonymous")
            timestamp = datetime.now().isoformat()
            
            # Create session log entry
            session_log = {
                "id": str(hash(f"{user_email}_{user_message}_{timestamp}")),
                "userEmail": user_email,
                "userMessage": user_message,
                "aiResponse": ai_message,
                "timestamp": timestamp,
                "type": "chat_session",
                "companion": "Blayzo"  # Default companion for web chat
            }
            
            # Save to session logs (for admin dashboard)
            if "session_logs" not in db.db_manager.data:
                db.db_manager.data["session_logs"] = []
            
            db.db_manager.data["session_logs"].append(session_log)
            
            # Keep only last 2000 session logs to prevent database bloat
            if len(db.db_manager.data["session_logs"]) > 2000:
                db.db_manager.data["session_logs"] = db.db_manager.data["session_logs"][-2000:]
            
            # Save to database
            db.db_manager.save_data()
            
            logging.info(f"Chat session saved for user: {user_email}")
            
        except Exception as log_error:
            logging.error(f"Failed to save session log: {log_error}")
            # Don't fail the chat if logging fails

        # Trim history to the last 20 messages
        session["messages"] = session["messages"][-20:]

        return jsonify({'success': True, 'response': ai_message})

    except Exception as e:
        logging.exception("Error in /send_message")
        error_message = str(e)
        
        # Provide more specific error messages
        if "insufficient_quota" in error_message:
            user_error = "⚠️ OpenAI API quota exceeded. Please check your billing settings at platform.openai.com"
        elif "rate_limit" in error_message or "429" in error_message:
            user_error = "⚠️ Too many requests. Please wait a moment and try again."
        elif "api_key" in error_message:
            user_error = "⚠️ API key issue. Please check your OpenAI API key configuration."
        else:
            user_error = "⚠️ I'm having trouble connecting right now. Please try again later."
        
        return jsonify(success=False, error=user_error), 500

# -------------------------------------------------
# API endpoint for Kodular integration
# -------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def api_chat():
    """
    API endpoint for character-specific chat
    Expected JSON: {"message": "user message", "character": "Blayzo" or "Blayzica"}
    Returns JSON: {"response": "ai response", "success": true/false}
    """
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify(success=False, error="Message field is required"), 400

        user_message = data.get("message", "").strip()
        character = data.get("character", "Blayzo")  # Default to Blayzo
        
        if not user_message:
            return jsonify(success=False, error="Message cannot be empty"), 400

        # Check if OpenAI client is available
        if not openai_client:
            return jsonify(success=False, error="AI services are currently unavailable. Please contact support."), 503

        # Get character-specific system prompt
        system_prompt = CHARACTER_PROMPTS.get(character, CHARACTER_PROMPTS["Blayzo"])
        
        # API call with character-specific prompt
        api_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=api_messages,
            max_tokens=500,
            temperature=0.7,
        )

        ai_message = response.choices[0].message.content.strip()
        return jsonify({'success': True, 'response': ai_message})

    except Exception as e:
        logging.exception("Error in /api/chat")
        error_message = str(e)
        
        # Provide specific error messages
        if "insufficient_quota" in error_message:
            user_error = "OpenAI API quota exceeded. Please check billing settings."
        elif "rate_limit" in error_message or "429" in error_message:
            user_error = "Too many requests. Please wait and try again."
        elif "api_key" in error_message:
            user_error = "API key issue. Please check configuration."
        else:
            user_error = "Service temporarily unavailable. Please try again later."
        
        return jsonify(success=False, error=user_error), 500

# -------------------------------------------------
# User Data Management API Endpoints
# -------------------------------------------------

@app.route("/api/users", methods=["POST"])
def create_user_api():
    """Create a new user"""
    try:
        data = request.get_json()
        if not data or "email" not in data:
            return jsonify(success=False, error="Email is required"), 400
        
        email = data.get("email").strip()
        companion = data.get("companion", "Blayzo")
        
        user = db.users.create_user(email, companion)
        return jsonify(success=True, user=user)
        
    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400
    except Exception as e:
        logging.error(f"Create user error: {e}")
        return jsonify(success=False, error="Failed to create user"), 500

@app.route("/api/users", methods=["GET"])
def get_all_users_api():
    """Get all users (admin only)"""
    try:
        # In production, add admin authentication check here
        users = db.db_manager.data.get("users", [])
        
        # Remove sensitive data for admin view
        safe_users = []
        for user in users:
            safe_user = user.copy()
            # Keep only necessary fields for admin dashboard
            safe_users.append(safe_user)
        
        return jsonify(success=True, users=safe_users, count=len(safe_users))
        
    except Exception as e:
        logging.error(f"Get all users error: {e}")
        return jsonify(success=False, error="Failed to retrieve users"), 500

@app.route("/api/users/<user_id>", methods=["GET"])
def get_user_api(user_id):
    """Get user by ID"""
    try:
        user = db.users.get_user_by_id(user_id)
        if not user:
            return jsonify(success=False, error="User not found"), 404
        
        return jsonify(success=True, user=user)
        
    except Exception as e:
        logging.error(f"Get user error: {e}")
        return jsonify(success=False, error="Failed to retrieve user"), 500

@app.route("/api/users/email/<email>", methods=["GET"])
def get_user_by_email_api(email):
    """Get user by email"""
    try:
        user = db.users.get_user_by_email(email)
        if not user:
            return jsonify(success=False, error="User not found"), 404
        
        return jsonify(success=True, user=user)
        
    except Exception as e:
        logging.error(f"Get user by email error: {e}")
        return jsonify(success=False, error="Failed to retrieve user"), 500

# -------------------------------------------------
# Stripe Payment Processing
# -------------------------------------------------

@app.route("/api/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    try:
        data = request.get_json()
        if not data or "plan" not in data:
            return jsonify(success=False, error="Plan is required"), 400
        
        plan = data.get("plan")
        user_id = data.get("user_id")
        
        # Development mode bypass for testing
        if DEVELOPMENT_MODE:
            return jsonify(
                success=True,
                checkout_url="/api/simulate-payment-success",
                message="Development mode: Simulating successful payment"
            )
        
        # Define pricing
        prices = {
            "monthly": {
                "amount": 1000,  # $10.00 in cents
                "interval": "month"
            },
            "yearly": {
                "amount": 10000,  # $100.00 in cents
                "interval": "year"
            }
        }
        
        if plan not in prices:
            return jsonify(success=False, error="Invalid plan"), 400
        
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'SoulBridge AI {plan.capitalize()} Subscription',
                        'description': f'Premium AI companion access - {plan} billing'
                    },
                    'unit_amount': prices[plan]["amount"],
                    'recurring': {
                        'interval': prices[plan]["interval"]
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.url_root + 'subscription?success=true&session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.url_root + 'subscription?canceled=true',
            metadata={
                'user_id': user_id,
                'plan': plan
            }
        )
        
        return jsonify(success=True, checkout_url=session.url, session_id=session.id)
        
    except Exception as e:
        logging.error(f"Stripe checkout error: {e}")
        return jsonify(success=False, error="Failed to create checkout session"), 500

@app.route("/api/simulate-payment-success")
def simulate_payment_success():
    """Development route to simulate successful payment"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Simulation</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: linear-gradient(135deg, #000000 0%, #0f172a 50%, #1e293b 100%);
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }
            .container {
                background: rgba(15, 23, 42, 0.8);
                border: 2px solid #22d3ee;
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                max-width: 400px;
            }
            .success-icon { font-size: 4rem; margin-bottom: 1rem; }
            h1 { color: #22d3ee; margin-bottom: 1rem; }
            .btn {
                background: linear-gradient(135deg, #22d3ee, #0891b2);
                color: #000;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 0.5rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✅</div>
            <h1>Payment Successful!</h1>
            <p>Your SoulBridge Plus subscription has been activated.</p>
            <p><strong>Development Mode:</strong> This is a simulated payment.</p>
            <br>
            <a href="/profile" class="btn">Back to Profile</a>
            <button onclick="confirmPayment()" class="btn">Activate Premium</button>
        </div>
        
        <script>
            function confirmPayment() {
                localStorage.setItem('soulbridge_payment_confirmed', 'true');
                localStorage.setItem('soulbridge_subscription', 'plus');
                alert('Premium features unlocked! You can now access color customization.');
                window.location.href = '/profile';
            }
        </script>
    </body>
    </html>
    """)

@app.route("/create-payment-intent", methods=["POST"])
def create_payment_intent():
    """Create a Stripe PaymentIntent for the payment page"""
    try:
        data = request.get_json()
        amount = data.get("amount", 1000)  # Default to $10 if not specified
        
        # Check if Stripe is configured
        if not stripe.api_key:
            return jsonify({
                "error": "Payment processing not configured. Please use test payment.",
                "test_url": "/test-payment-success"
            }), 503
        
        # Create PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=amount,  # Amount in cents
            currency="usd",
            automatic_payment_methods={"enabled": True}
        )
        
        return jsonify({"clientSecret": intent.client_secret})
        
    except Exception as e:
        logging.error(f"Payment intent creation error: {e}")
        return jsonify({
            "error": str(e),
            "test_url": "/test-payment-success"
        }), 500

@app.route("/api/check-voice-chat-access", methods=["POST"])
def check_voice_chat_access():
    """Check voice chat access for premium companions (from Node.js code)"""
    try:
        data = request.get_json()
        companion = data.get("companion")
        is_paid = data.get("is_paid", False)
        has_unlocked_premium = data.get("has_unlocked_premium", False)
        voice_preview_time_remaining = data.get("voice_preview_time_remaining", 0)
        
        # Premium companions that require subscription
        premium_companions = ["Blayzion", "Blayzia", "Crimson", "Violet"]
        
        # Referral exclusive companions that have voice chat
        referral_companions = ["Blayzike", "Blazelian", "BlayzoReferral"]
        
        if companion in premium_companions:
            if is_paid:
                return jsonify({
                    "voice_chat": "unlimited",
                    "access": True,
                    "message": "Unlimited voice chat available"
                })
            elif has_unlocked_premium and voice_preview_time_remaining > 0:
                return jsonify({
                    "voice_chat": "preview",
                    "access": True,
                    "time_remaining": voice_preview_time_remaining,
                    "message": f"Preview time remaining: {voice_preview_time_remaining} minutes"
                })
            else:
                return jsonify({
                    "voice_chat": "locked",
                    "access": False,
                    "message": "Upgrade to SoulBridge AI Plus required for voice chat",
                    "upgrade_url": "/subscription"
                })
        elif companion in referral_companions:
            # Check if user has unlocked this referral companion
            # In a real implementation, check user's referral achievements
            has_referral_access = data.get("has_referral_access", False)
            
            if has_referral_access:
                return jsonify({
                    "voice_chat": "unlimited",
                    "access": True,
                    "message": f"Exclusive voice chat with {companion} available!"
                })
            else:
                return jsonify({
                    "voice_chat": "locked",
                    "access": False,
                    "message": f"Refer friends to unlock {companion} and voice chat access",
                    "upgrade_url": "/referrals"
                })
        else:
            # Free companions (Blayzo, Blayzica) 
            return jsonify({
                "voice_chat": "disabled",
                "access": False,
                "message": "No voice chat available for this companion"
            })
            
    except Exception as e:
        logging.error(f"Voice chat access check error: {e}")
        return jsonify({
            "voice_chat": "error",
            "access": False,
            "message": "Error checking voice chat access"
        }), 500

@app.route("/api/send-email", methods=["POST"])
def send_contact_email():
    """Send contact form email via Gmail OAuth2 (from Node.js code)"""
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        message = data.get("message")
        
        # Validate required fields
        if not name or not email or not message:
            return jsonify({
                "status": "error",
                "message": "Name, email, and message are required"
            }), 400
        
        # Check if Gmail OAuth2 is configured
        gmail_user = os.environ.get("GMAIL_USER")
        gmail_password = os.environ.get("GMAIL_PASSWORD")  # App password for simplicity
        
        if not gmail_user or not gmail_password:
            return jsonify({
                "status": "error",
                "message": "Email service not configured. Please contact support directly.",
                "contact_email": "soulbridgeai.contact@gmail.com"
            }), 503
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = gmail_user  # Send to yourself
        msg['Subject'] = f"SoulBridge AI Contact From: {name}"
        
        # Email body
        body = f"""
New contact form submission:

Name: {name}
Email: {email}
Message: {message}

---
Sent from SoulBridge AI Contact Form
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email via Gmail SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        
        return jsonify({
            "status": "success",
            "message": "Email sent successfully! You'll receive an auto-reply confirmation from soulbridgeai.contact@gmail.com shortly."
        })
        
    except Exception as e:
        logging.error(f"Contact email sending error: {e}")
        return jsonify({
            "status": "error",
            "message": "Error sending email. Please try again later.",
            "contact_email": "soulbridgeai.contact@gmail.com"
        }), 500

@app.route("/api/stripe-webhook", methods=["POST"])
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        # Verify webhook signature (in production, use webhook secret)
        webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
        if webhook_secret:
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
            except ValueError as e:
                logging.error(f"Invalid payload: {e}")
                return jsonify(success=False), 400
            except stripe.error.SignatureVerificationError as e:
                logging.error(f"Invalid signature: {e}")
                return jsonify(success=False), 400
        else:
            event = stripe.Event.construct_from(
                request.get_json(), stripe.api_key
            )
        
        # Handle checkout session completed
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = session.metadata.get('user_id')
            plan = session.metadata.get('plan')
            
            if user_id:
                # Update user subscription in database
                success = db.users.update_subscription(user_id, "premium")
                if success:
                    logging.info(f"User {user_id} subscription activated - {plan}")
                else:
                    logging.error(f"Failed to update subscription for user {user_id}")
        
        # Handle subscription cancelled
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            # Find user by subscription ID and update status
            # This would require storing subscription IDs in database
            logging.info(f"Subscription cancelled: {subscription.id}")
        
        return jsonify(success=True)
        
    except Exception as e:
        logging.error(f"Stripe webhook error: {e}")
        return jsonify(success=False), 500

@app.route("/api/subscription/verify", methods=["GET"])
def verify_subscription_api():
    """API endpoint to verify current user's subscription status"""
    try:
        # Check if user is authenticated
        if not session.get("user_authenticated"):
            return jsonify(success=False, error="Not authenticated"), 401
        
        user_email = session.get("user_email")
        if not user_email:
            return jsonify(success=False, error="No user email in session"), 401
        
        # Verify subscription from database
        subscription_data = verify_user_subscription(user_email)
        
        if not subscription_data["valid"]:
            # Force logout if subscription verification fails
            session.clear()
            return jsonify(success=False, error="Subscription verification failed", force_logout=True), 401
        
        return jsonify(
            success=True,
            subscription_status=subscription_data["status"],
            user_id=subscription_data.get("user_id"),
            companion=subscription_data.get("companion")
        )
        
    except Exception as e:
        logging.error(f"Subscription verification API error: {e}")
        return jsonify(success=False, error="Verification failed"), 500

@app.route("/api/users/<user_id>/subscription", methods=["PUT"])
def update_subscription_api(user_id):
    """Update user subscription"""
    try:
        data = request.get_json()
        if not data or "subscriptionStatus" not in data:
            return jsonify(success=False, error="Subscription status is required"), 400
        
        subscription_status = data.get("subscriptionStatus")
        success = db.users.update_subscription(user_id, subscription_status)
        
        if success:
            return jsonify(success=True, message="Subscription updated successfully")
        else:
            return jsonify(success=False, error="User not found"), 404
            
    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400
    except Exception as e:
        logging.error(f"Update subscription error: {e}")
        return jsonify(success=False, error="Failed to update subscription"), 500

@app.route("/api/billing/portal", methods=["POST"])
def create_billing_portal():
    """Create Stripe customer portal session"""
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        
        if not user_id:
            return jsonify(success=False, error="User ID is required"), 400
        
        # Get user's Stripe customer ID from database
        user = db.users.get_user(user_id)
        if not user:
            return jsonify(success=False, error="User not found"), 404
        
        stripe_customer_id = user.get("stripe_customer_id")
        if not stripe_customer_id:
            return jsonify(success=False, error="No billing information found"), 404
        
        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=request.url_root + 'profile'
        )
        
        return jsonify(success=True, portal_url=portal_session.url)
        
    except Exception as e:
        logging.error(f"Billing portal error: {e}")
        return jsonify(success=False, error="Failed to create billing portal"), 500

# -------------------------------------------------
# Support Ticket System
# -------------------------------------------------

@app.route("/api/support/tickets", methods=["POST"])
def create_support_ticket():
    """Create a new support ticket"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["userEmail", "subject", "description"]
        for field in required_fields:
            if not data or field not in data:
                return jsonify(success=False, error=f"{field} is required"), 400
        
        # Create ticket
        ticket = db.support_tickets.create_ticket(
            user_email=data["userEmail"],
            subject=data["subject"], 
            description=data["description"],
            priority=data.get("priority", "medium"),
            category=data.get("category", "general")
        )
        
        # Send automated response email
        try:
            from auto_response import send_contact_auto_response
            user_name = data.get("userName") or data.get("name")
            auto_response_result = send_contact_auto_response(data["userEmail"], user_name)
            if auto_response_result.get('success'):
                logging.info(f"Auto-response sent successfully to {data['userEmail']}")
            else:
                logging.warning(f"Auto-response failed for {data['userEmail']}: {auto_response_result.get('error')}")
        except Exception as e:
            logging.error(f"Auto-response error: {e}")
            # Don't fail the ticket creation if auto-response fails
        
        return jsonify(success=True, ticket=ticket, message="Support ticket created successfully")
        
    except Exception as e:
        logging.error(f"Create support ticket error: {e}")
        return jsonify(success=False, error="Failed to create support ticket"), 500

@app.route("/api/contact", methods=["POST"])
def contact_form_submit():
    """Handle general contact form submissions with auto-response"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["email", "message"]
        for field in required_fields:
            if not data or field not in data or not data[field].strip():
                return jsonify(success=False, error=f"{field} is required"), 400
        
        # Log the contact submission
        logging.info(f"Contact form submission from {data['email']}: {data.get('subject', 'No subject')}")
        
        # Send automated response email
        try:
            from auto_response import send_contact_auto_response
            user_name = data.get("name")
            auto_response_result = send_contact_auto_response(data["email"], user_name)
            if auto_response_result.get('success'):
                logging.info(f"Contact auto-response sent successfully to {data['email']}")
                return jsonify(success=True, message="Thank you for your message! We'll get back to you soon.")
            else:
                logging.warning(f"Contact auto-response failed for {data['email']}: {auto_response_result.get('error')}")
                return jsonify(success=True, message="Thank you for your message! We'll get back to you soon. (Auto-response unavailable)")
        except Exception as e:
            logging.error(f"Contact auto-response error: {e}")
            return jsonify(success=True, message="Thank you for your message! We'll get back to you soon.")
        
    except Exception as e:
        logging.error(f"Contact form submission error: {e}")
        return jsonify(success=False, error="Failed to process contact form"), 500

# -------------------------------------------------
# Analytics Dashboard
# -------------------------------------------------

@app.route("/api/analytics/dashboard", methods=["GET"])
def get_analytics_dashboard():
    """Get comprehensive analytics dashboard data"""
    try:
        from analytics import analytics
        
        # Get period from query params (default 30 days)
        days = request.args.get('days', 30, type=int)
        
        dashboard_data = analytics.get_dashboard_summary()
        
        return jsonify(success=True, data=dashboard_data)
        
    except Exception as e:
        logging.error(f"Analytics dashboard error: {e}")
        return jsonify(success=False, error="Failed to load analytics"), 500

@app.route("/api/analytics/users", methods=["GET"])
def get_user_analytics():
    """Get detailed user analytics"""
    try:
        from analytics import analytics
        
        days = request.args.get('days', 30, type=int)
        user_metrics = analytics.get_user_metrics(days)
        
        return jsonify(success=True, data=user_metrics)
        
    except Exception as e:
        logging.error(f"User analytics error: {e}")
        return jsonify(success=False, error="Failed to load user analytics"), 500

@app.route("/api/analytics/companions", methods=["GET"])
def get_companion_analytics():
    """Get companion usage analytics"""
    try:
        from analytics import analytics
        
        days = request.args.get('days', 30, type=int)
        companion_data = analytics.get_companion_analytics(days)
        
        return jsonify(success=True, data=companion_data)
        
    except Exception as e:
        logging.error(f"Companion analytics error: {e}")
        return jsonify(success=False, error="Failed to load companion analytics"), 500

@app.route("/api/analytics/revenue", methods=["GET"])
def get_revenue_analytics():
    """Get revenue and financial analytics"""
    try:
        from analytics import analytics
        
        days = request.args.get('days', 30, type=int)
        revenue_data = analytics.get_revenue_analytics(days)
        
        return jsonify(success=True, data=revenue_data)
        
    except Exception as e:
        logging.error(f"Revenue analytics error: {e}")
        return jsonify(success=False, error="Failed to load revenue analytics"), 500

@app.route("/analytics", methods=["GET"])
def analytics_dashboard():
    """Analytics dashboard page"""
    return render_template("analytics_dashboard.html")

# -------------------------------------------------
# Push Notifications System
# -------------------------------------------------

@app.route("/api/notifications/subscribe", methods=["POST"])
def subscribe_notifications():
    """Subscribe user to push notifications"""
    try:
        data = request.get_json()
        
        # Validate subscription data
        if not data or 'subscription' not in data:
            return jsonify(success=False, error="Subscription data required"), 400
        
        user_email = data.get('userEmail')
        subscription = data['subscription']
        
        # Store subscription in database (simplified)
        # In a real implementation, you'd store this in your user database
        logging.info(f"Push notification subscription for {user_email}: {subscription}")
        
        # Schedule welcome notification
        from push_notifications import push_manager
        user_data = {'selectedCharacter': data.get('companion', 'Blayzo')}
        
        notification_payload = push_manager.create_notification_payload(
            'companion_missing',
            user_data=user_data
        )
        
        return jsonify(success=True, message="Successfully subscribed to notifications")
        
    except Exception as e:
        logging.error(f"Notification subscription error: {e}")
        return jsonify(success=False, error="Failed to subscribe to notifications"), 500

@app.route("/api/notifications/send", methods=["POST"])
def send_push_notification():
    """Send push notification to specific user"""
    try:
        data = request.get_json()
        
        required_fields = ["userEmail", "type"]
        for field in required_fields:
            if not data or field not in data:
                return jsonify(success=False, error=f"{field} is required"), 400
        
        from push_notifications import push_manager
        
        user_email = data['userEmail']
        notification_type = data['type']
        user_data = data.get('userData', {})
        
        # Check if notification should be sent
        if not push_manager.should_send_notification(user_email, notification_type):
            return jsonify(success=False, message="Notification not sent due to user preferences")
        
        # Create notification payload
        notification_payload = push_manager.create_notification_payload(
            notification_type,
            user_data=user_data,
            custom_data=data.get('customData')
        )
        
        if not notification_payload:
            return jsonify(success=False, error="Invalid notification type"), 400
        
        # In a real implementation, you would send this to a push service
        # For now, we'll just log it and return success
        logging.info(f"Push notification sent to {user_email}: {notification_payload}")
        
        return jsonify(success=True, notification=notification_payload)
        
    except Exception as e:
        logging.error(f"Send notification error: {e}")
        return jsonify(success=False, error="Failed to send notification"), 500

@app.route("/api/notifications/schedule", methods=["POST"])
def schedule_notification():
    """Schedule a notification for later delivery"""
    try:
        data = request.get_json()
        
        required_fields = ["userEmail", "type", "delayMinutes"]
        for field in required_fields:
            if not data or field not in data:
                return jsonify(success=False, error=f"{field} is required"), 400
        
        from push_notifications import push_manager
        
        result = push_manager.schedule_notification(
            user_id=data['userEmail'],
            notification_type=data['type'],
            delay_minutes=data['delayMinutes'],
            user_data=data.get('userData', {})
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Schedule notification error: {e}")
        return jsonify(success=False, error="Failed to schedule notification"), 500

@app.route("/api/notifications/preferences", methods=["GET", "POST"])
def notification_preferences():
    """Get or update user notification preferences"""
    try:
        if request.method == "GET":
            user_email = request.args.get('userEmail')
            if not user_email:
                return jsonify(success=False, error="userEmail required"), 400
            
            from push_notifications import push_manager
            preferences = push_manager.get_user_notification_preferences(user_email)
            
            return jsonify(success=True, preferences=preferences)
        
        elif request.method == "POST":
            data = request.get_json()
            
            if not data or 'userEmail' not in data:
                return jsonify(success=False, error="userEmail required"), 400
            
            user_email = data['userEmail']
            preferences = data.get('preferences', {})
            
            # In a real implementation, you'd save these to the database
            logging.info(f"Updated notification preferences for {user_email}: {preferences}")
            
            return jsonify(success=True, message="Preferences updated successfully")
        
    except Exception as e:
        logging.error(f"Notification preferences error: {e}")
        return jsonify(success=False, error="Failed to handle preferences"), 500

@app.route("/api/notifications/check-engagement", methods=["POST"])
def check_user_engagement():
    """Check user engagement and trigger retention notifications"""
    try:
        from push_notifications import push_manager
        from datetime import datetime, timedelta
        
        # This would typically get user data from the database
        # For now, we'll simulate checking engagement
        
        # Example: Check if user should receive retention notification
        should_notify = True  # Simplified logic
        
        if should_notify:
            notification_payload = push_manager.create_notification_payload(
                'companion_missing',
                user_data={'selectedCharacter': 'Blayzo'}
            )
            
            return jsonify(
                shouldNotify=True,
                title=notification_payload['title'],
                options=notification_payload
            )
        
        return jsonify(shouldNotify=False)
        
    except Exception as e:
        logging.error(f"Engagement check error: {e}")
        return jsonify(success=False, error="Failed to check engagement"), 500

# -------------------------------------------------
# Referral System with Exclusive Companion Rewards
# -------------------------------------------------

@app.route("/api/referrals/create", methods=["POST"])
def create_referral_link():
    """Create referral link for user"""
    try:
        data = request.get_json()
        
        if not data or 'userEmail' not in data:
            return jsonify(success=False, error="userEmail required"), 400
        
        from referral_system import referral_manager
        
        result = referral_manager.create_referral_link(
            data['userEmail'],
            data.get('baseUrl', 'https://soulbridgeai.com')
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Create referral link error: {e}")
        return jsonify(success=False, error="Failed to create referral link"), 500

@app.route("/api/referrals/dashboard", methods=["GET"])
def get_referral_dashboard():
    """Get referral dashboard data for user"""
    try:
        user_email = request.args.get('userEmail')
        if not user_email:
            return jsonify(success=False, error="userEmail required"), 400
        
        from referral_system import referral_manager
        
        dashboard_data = referral_manager.get_referral_dashboard(user_email)
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logging.error(f"Get referral dashboard error: {e}")
        return jsonify(success=False, error="Failed to load referral dashboard"), 500

@app.route("/api/referrals/process", methods=["POST"])
def process_referral():
    """Process referral when new user signs up"""
    try:
        data = request.get_json()
        
        required_fields = ["refereeEmail", "referralCode", "referrerEmail"]
        for field in required_fields:
            if not data or field not in data:
                return jsonify(success=False, error=f"{field} required"), 400
        
        from referral_system import referral_manager
        
        result = referral_manager.process_referral_signup(
            data['refereeEmail'],
            data['referralCode'],
            data['referrerEmail']
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Process referral error: {e}")
        return jsonify(success=False, error="Failed to process referral"), 500

@app.route("/api/referrals/validate", methods=["POST"])
def validate_referral_code():
    """Validate referral code"""
    try:
        data = request.get_json()
        
        if not data or 'referralCode' not in data:
            return jsonify(success=False, error="referralCode required"), 400
        
        from referral_system import referral_manager
        
        result = referral_manager.validate_referral_code(data['referralCode'])
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Validate referral code error: {e}")
        return jsonify(success=False, error="Failed to validate referral code"), 500

@app.route("/api/referrals/share-templates", methods=["GET"])
def get_share_templates():
    """Get social media sharing templates"""
    try:
        user_email = request.args.get('userEmail')
        if not user_email:
            return jsonify(success=False, error="userEmail required"), 400
        
        from referral_system import referral_manager
        
        templates = referral_manager.get_social_share_templates(user_email)
        
        return jsonify(templates)
        
    except Exception as e:
        logging.error(f"Get share templates error: {e}")
        return jsonify(success=False, error="Failed to get share templates"), 500

@app.route("/api/referrals/unlock-companion", methods=["POST"])
def unlock_exclusive_companion():
    """Unlock exclusive companion for user"""
    try:
        data = request.get_json()
        
        required_fields = ["userEmail", "companionName"]
        for field in required_fields:
            if not data or field not in data:
                return jsonify(success=False, error=f"{field} required"), 400
        
        from referral_system import referral_manager
        
        result = referral_manager.unlock_exclusive_companion(
            data['userEmail'],
            data['companionName']
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Unlock exclusive companion error: {e}")
        return jsonify(success=False, error="Failed to unlock companion"), 500

@app.route("/referrals", methods=["GET"])
def referrals_page():
    """Referral dashboard page"""
    return render_template("referrals.html")

@app.route("/api/support/tickets/<ticket_id>", methods=["GET"])
def get_support_ticket(ticket_id):
    """Get a specific support ticket"""
    try:
        ticket = db.support_tickets.get_ticket(ticket_id)
        
        if not ticket:
            return jsonify(success=False, error="Ticket not found"), 404
        
        return jsonify(success=True, ticket=ticket)
        
    except Exception as e:
        logging.error(f"Get support ticket error: {e}")
        return jsonify(success=False, error="Failed to retrieve support ticket"), 500

@app.route("/api/support/tickets/user/<user_email>", methods=["GET"])
def get_user_support_tickets(user_email):
    """Get all support tickets for a user"""
    try:
        tickets = db.support_tickets.get_user_tickets(user_email)
        return jsonify(success=True, tickets=tickets)
        
    except Exception as e:
        logging.error(f"Get user support tickets error: {e}")
        return jsonify(success=False, error="Failed to retrieve user tickets"), 500

@app.route("/api/support/tickets", methods=["GET"])
@admin_required
def get_all_support_tickets():
    """Get all support tickets (admin only)"""
    try:
        status_filter = request.args.get('status')
        priority_filter = request.args.get('priority')
        
        tickets = db.support_tickets.get_all_tickets(status=status_filter, priority=priority_filter)
        stats = db.support_tickets.get_ticket_stats()
        
        return jsonify(success=True, tickets=tickets, stats=stats)
        
    except Exception as e:
        logging.error(f"Get all support tickets error: {e}")
        return jsonify(success=False, error="Failed to retrieve support tickets"), 500

@app.route("/api/support/tickets/<ticket_id>/status", methods=["PUT"])
@admin_required
def update_ticket_status(ticket_id):
    """Update support ticket status (admin only)"""
    try:
        data = request.get_json()
        
        if not data or "status" not in data:
            return jsonify(success=False, error="Status is required"), 400
        
        status = data["status"]
        assigned_to = data.get("assignedTo")
        
        # Validate status
        valid_statuses = ["open", "in_progress", "pending", "resolved", "closed"]
        if status not in valid_statuses:
            return jsonify(success=False, error=f"Invalid status. Must be one of: {valid_statuses}"), 400
        
        success = db.support_tickets.update_ticket_status(ticket_id, status, assigned_to)
        
        if success:
            return jsonify(success=True, message="Ticket status updated successfully")
        else:
            return jsonify(success=False, error="Ticket not found"), 404
        
    except Exception as e:
        logging.error(f"Update ticket status error: {e}")
        return jsonify(success=False, error="Failed to update ticket status"), 500

@app.route("/api/support/tickets/<ticket_id>/responses", methods=["POST"])
@admin_required
def add_ticket_response(ticket_id):
    """Add a response to a support ticket (admin only)"""
    try:
        data = request.get_json()
        
        if not data or "response" not in data:
            return jsonify(success=False, error="Response text is required"), 400
        
        response_text = data["response"]
        responder_email = data.get("responderEmail", "admin@soulbridgeai.com")
        is_internal = data.get("isInternal", False)
        
        success = db.support_tickets.add_response(ticket_id, response_text, responder_email, is_internal)
        
        if success:
            return jsonify(success=True, message="Response added successfully")
        else:
            return jsonify(success=False, error="Ticket not found"), 404
        
    except Exception as e:
        logging.error(f"Add ticket response error: {e}")
        return jsonify(success=False, error="Failed to add response"), 500

@app.route("/api/support/tickets/search", methods=["GET"])
@admin_required
def search_support_tickets():
    """Search support tickets (admin only)"""
    try:
        query = request.args.get('query')
        
        if not query:
            return jsonify(success=False, error="Search query is required"), 400
        
        results = db.support_tickets.search_tickets(query)
        return jsonify(success=True, tickets=results)
        
    except Exception as e:
        logging.error(f"Search support tickets error: {e}")
        return jsonify(success=False, error="Failed to search tickets"), 500

# -------------------------------------------------
# Billing Dashboard & Invoice Management
# -------------------------------------------------

@app.route("/api/billing/invoices", methods=["GET"])
def get_user_invoices():
    """Get invoices for a user"""
    try:
        user_email = request.args.get('user_email')
        if not user_email:
            return jsonify(success=False, error="User email is required"), 400
        
        invoices = db.billing.get_user_invoices(user_email)
        stats = db.billing.get_invoice_stats()
        
        return jsonify(success=True, invoices=invoices, stats=stats)
        
    except Exception as e:
        logging.error(f"Get user invoices error: {e}")
        return jsonify(success=False, error="Failed to retrieve invoices"), 500

@app.route("/api/billing/create-invoice", methods=["POST"])
@admin_required
def create_invoice():
    """Create a new invoice (admin only)"""
    try:
        data = request.get_json()
        
        required_fields = ["userEmail", "amount", "planType"]
        for field in required_fields:
            if not data or field not in data:
                return jsonify(success=False, error=f"{field} is required"), 400
        
        invoice = db.billing.create_invoice(
            user_email=data["userEmail"],
            amount=float(data["amount"]),
            plan_type=data["planType"],
            stripe_invoice_id=data.get("stripeInvoiceID"),
            stripe_customer_id=data.get("stripeCustomerID")
        )
        
        return jsonify(success=True, invoice=invoice)
        
    except Exception as e:
        logging.error(f"Create invoice error: {e}")
        return jsonify(success=False, error="Failed to create invoice"), 500

@app.route("/api/billing/invoices/<invoice_id>/status", methods=["PUT"])
@admin_required
def update_invoice_status(invoice_id):
    """Update invoice status (admin only)"""
    try:
        data = request.get_json()
        
        if not data or "status" not in data:
            return jsonify(success=False, error="Status is required"), 400
        
        status = data["status"]
        paid_at = data.get("paidAt")
        
        success = db.billing.update_invoice_status(invoice_id, status, paid_at)
        
        if success:
            return jsonify(success=True, message="Invoice status updated")
        else:
            return jsonify(success=False, error="Invoice not found"), 404
        
    except Exception as e:
        logging.error(f"Update invoice status error: {e}")
        return jsonify(success=False, error="Failed to update invoice status"), 500

# -------------------------------------------------
# Live Chat Support System
# -------------------------------------------------

@app.route("/api/live-chat/sessions", methods=["POST"])
def create_chat_session():
    """Create a new live chat session"""
    try:
        data = request.get_json()
        
        if not data or "userEmail" not in data:
            return jsonify(success=False, error="User email is required"), 400
        
        session = db.live_chat.create_chat_session(
            user_email=data["userEmail"],
            agent_email=data.get("agentEmail")
        )
        
        return jsonify(success=True, session=session)
        
    except Exception as e:
        logging.error(f"Create chat session error: {e}")
        return jsonify(success=False, error="Failed to create chat session"), 500

@app.route("/api/live-chat/sessions/<session_id>/messages", methods=["POST"])
def add_chat_message(session_id):
    """Add a message to a chat session"""
    try:
        data = request.get_json()
        
        required_fields = ["senderEmail", "message", "senderType"]
        for field in required_fields:
            if not data or field not in data:
                return jsonify(success=False, error=f"{field} is required"), 400
        
        success = db.live_chat.add_message(
            session_id=session_id,
            sender_email=data["senderEmail"],
            message=data["message"],
            sender_type=data["senderType"]
        )
        
        if success:
            return jsonify(success=True, message="Message added successfully")
        else:
            return jsonify(success=False, error="Session not found"), 404
        
    except Exception as e:
        logging.error(f"Add chat message error: {e}")
        return jsonify(success=False, error="Failed to add message"), 500

@app.route("/api/live-chat/sessions/<session_id>/close", methods=["POST"])
def close_chat_session(session_id):
    """Close a chat session"""
    try:
        data = request.get_json() or {}
        
        success = db.live_chat.close_session(
            session_id=session_id,
            rating=data.get("rating"),
            feedback=data.get("feedback")
        )
        
        if success:
            return jsonify(success=True, message="Session closed successfully")
        else:
            return jsonify(success=False, error="Session not found"), 404
        
    except Exception as e:
        logging.error(f"Close chat session error: {e}")
        return jsonify(success=False, error="Failed to close session"), 500

@app.route("/api/live-chat/sessions/active", methods=["GET"])
@admin_required
def get_active_chat_sessions():
    """Get all active chat sessions (admin only)"""
    try:
        sessions = db.live_chat.get_active_sessions()
        return jsonify(success=True, sessions=sessions)
        
    except Exception as e:
        logging.error(f"Get active chat sessions error: {e}")
        return jsonify(success=False, error="Failed to retrieve sessions"), 500

# -------------------------------------------------
# Knowledge Base System
# -------------------------------------------------

@app.route("/api/knowledge-base/articles", methods=["POST"])
@admin_required
def create_kb_article():
    """Create a new knowledge base article (admin only)"""
    try:
        data = request.get_json()
        
        required_fields = ["title", "content", "category", "authorEmail"]
        for field in required_fields:
            if not data or field not in data:
                return jsonify(success=False, error=f"{field} is required"), 400
        
        article = db.knowledge_base.create_article(
            title=data["title"],
            content=data["content"],
            category=data["category"],
            author_email=data["authorEmail"],
            tags=data.get("tags", [])
        )
        
        return jsonify(success=True, article=article)
        
    except Exception as e:
        logging.error(f"Create KB article error: {e}")
        return jsonify(success=False, error="Failed to create article"), 500

@app.route("/api/knowledge-base/articles/search", methods=["GET"])
def search_kb_articles():
    """Search knowledge base articles"""
    try:
        query = request.args.get('query', '')
        category = request.args.get('category')
        
        if not query:
            return jsonify(success=False, error="Search query is required"), 400
        
        articles = db.knowledge_base.search_articles(query, category)
        return jsonify(success=True, articles=articles)
        
    except Exception as e:
        logging.error(f"Search KB articles error: {e}")
        return jsonify(success=False, error="Failed to search articles"), 500

@app.route("/api/knowledge-base/articles/<article_id>/vote", methods=["POST"])
def vote_kb_article(article_id):
    """Vote on article helpfulness"""
    try:
        data = request.get_json()
        
        if not data or "helpful" not in data:
            return jsonify(success=False, error="Helpful flag is required"), 400
        
        success = db.knowledge_base.vote_article(article_id, data["helpful"])
        
        if success:
            return jsonify(success=True, message="Vote recorded successfully")
        else:
            return jsonify(success=False, error="Article not found"), 404
        
    except Exception as e:
        logging.error(f"Vote KB article error: {e}")
        return jsonify(success=False, error="Failed to record vote"), 500

@app.route("/api/knowledge-base/articles/<article_id>/view", methods=["POST"])
def view_kb_article(article_id):
    """Increment article view count"""
    try:
        success = db.knowledge_base.increment_views(article_id)
        
        if success:
            return jsonify(success=True, message="View recorded")
        else:
            return jsonify(success=False, error="Article not found"), 404
        
    except Exception as e:
        logging.error(f"View KB article error: {e}")
        return jsonify(success=False, error="Failed to record view"), 500

# -------------------------------------------------
# Advanced Diagnostics & Troubleshooting
# -------------------------------------------------

@app.route("/api/diagnostics/user/<user_email>", methods=["GET"])
def run_user_diagnostics(user_email):
    """Run comprehensive diagnostics for a user"""
    try:
        diagnostics = db.diagnostics.run_user_diagnostics(user_email)
        return jsonify(success=True, diagnostics=diagnostics)
        
    except Exception as e:
        logging.error(f"User diagnostics error: {e}")
        return jsonify(success=False, error="Failed to run diagnostics"), 500

@app.route("/api/diagnostics/system-health", methods=["GET"])
@admin_required
def get_system_health():
    """Get overall system health metrics (admin only)"""
    try:
        health = db.diagnostics.get_system_health()
        return jsonify(success=True, health=health)
        
    except Exception as e:
        logging.error(f"System health error: {e}")
        return jsonify(success=False, error="Failed to get system health"), 500

# -------------------------------------------------
# Customer Service Portal Routes
# -------------------------------------------------

@app.route("/billing")
def billing_dashboard():
    return render_template("billing.html")

@app.route("/live-chat")
def live_chat_page():
    return render_template("live_chat.html")

@app.route("/knowledge-base")
def knowledge_base_page():
    return render_template("knowledge_base.html")

@app.route("/diagnostics")
def diagnostics_page():
    return render_template("diagnostics.html")

@app.route("/customer-service")
@admin_required
def customer_service_portal():
    return render_template("customer_service.html")

@app.route("/api/users/<user_id>/companion", methods=["PUT"])
def change_companion_api(user_id):
    """Change user's companion"""
    try:
        data = request.get_json()
        if not data or "companion" not in data:
            return jsonify(success=False, error="Companion is required"), 400
        
        companion = data.get("companion")
        success = db.users.change_companion(user_id, companion)
        
        if success:
            return jsonify(success=True, message="Companion updated successfully")
        else:
            return jsonify(success=False, error="User not found"), 404
            
    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400
    except Exception as e:
        logging.error(f"Change companion error: {e}")
        return jsonify(success=False, error="Failed to change companion"), 500

@app.route("/api/users/<user_id>/chat", methods=["POST"])
def add_chat_message_api(user_id):
    """Add a chat message to user's history"""
    try:
        data = request.get_json()
        if not data or "userMessage" not in data or "aiResponse" not in data:
            return jsonify(success=False, error="Both userMessage and aiResponse are required"), 400
        
        user_message = data.get("userMessage")
        ai_response = data.get("aiResponse")
        
        message = db.chat_history.add_message(user_id, user_message, ai_response)
        return jsonify(success=True, message=message)
        
    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400
    except Exception as e:
        logging.error(f"Add chat message error: {e}")
        return jsonify(success=False, error="Failed to add message"), 500

@app.route("/api/users/<user_id>/chat", methods=["GET"])
def get_chat_history_api(user_id):
    """Get user's chat history"""
    try:
        limit = request.args.get("limit", 50, type=int)
        history = db.chat_history.get_chat_history(user_id, limit)
        
        return jsonify(success=True, chatHistory=history)
        
    except Exception as e:
        logging.error(f"Get chat history error: {e}")
        return jsonify(success=False, error="Failed to retrieve chat history"), 500

@app.route("/api/users/<user_id>/chat", methods=["DELETE"])
def clear_chat_history_api(user_id):
    """Clear user's chat history"""
    try:
        success = db.chat_history.clear_chat_history(user_id)
        
        if success:
            return jsonify(success=True, message="Chat history cleared successfully")
        else:
            return jsonify(success=False, error="User not found"), 404
            
    except Exception as e:
        logging.error(f"Clear chat history error: {e}")
        return jsonify(success=False, error="Failed to clear chat history"), 500

@app.route("/api/users/<user_id>/settings", methods=["GET"])
def get_user_settings_api(user_id):
    """Get user settings"""
    try:
        settings = db.settings.get_settings(user_id)
        return jsonify(success=True, settings=settings)
        
    except Exception as e:
        logging.error(f"Get settings error: {e}")
        return jsonify(success=False, error="Failed to retrieve settings"), 500

@app.route("/api/users/<user_id>/settings", methods=["PUT"])
def update_user_settings_api(user_id):
    """Update user settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, error="Settings data is required"), 400
        
        success = db.settings.update_settings(user_id, data)
        
        if success:
            return jsonify(success=True, message="Settings updated successfully")
        else:
            return jsonify(success=False, error="User not found"), 404
            
    except Exception as e:
        logging.error(f"Update settings error: {e}")
        return jsonify(success=False, error="Failed to update settings"), 500

@app.route("/api/users/<user_id>", methods=["DELETE"])
def delete_user_api(user_id):
    """Delete a user (admin only)"""
    try:
        # Find and remove user from database
        users = db.db_manager.data.get("users", [])
        original_count = len(users)
        
        # Filter out the user to delete
        users = [user for user in users if user.get("userID") != user_id]
        
        if len(users) == original_count:
            return jsonify(success=False, error="User not found"), 404
        
        # Update database
        db.db_manager.data["users"] = users
        db.db_manager.save_data()
        
        logging.info(f"User {user_id} deleted by admin")
        return jsonify(success=True, message=f"User {user_id} deleted successfully")
        
    except Exception as e:
        logging.error(f"Delete user error: {e}")
        return jsonify(success=False, error="Failed to delete user"), 500

@app.route("/api/stats", methods=["GET"])
def get_database_stats_api():
    """Get database statistics"""
    try:
        stats = db.get_user_stats()
        return jsonify(success=True, stats=stats)
        
    except Exception as e:
        logging.error(f"Get stats error: {e}")
        return jsonify(success=False, error="Failed to retrieve statistics"), 500

@app.route("/api/backup", methods=["POST"])
def create_backup_api():
    """Create a database backup"""
    try:
        backup_file = db.backup_data()
        return jsonify(success=True, backupFile=backup_file, message="Backup created successfully")
        
    except Exception as e:
        logging.error(f"Create backup error: {e}")
        return jsonify(success=False, error="Failed to create backup"), 500

# -------------------------------------------------
# Admin Logging Endpoints
# -------------------------------------------------

@app.route("/api/admin/logs", methods=["GET"])
@jwt_admin_required
@ip_whitelist_required
def get_admin_logs():
    """Get admin activity logs - SECURED ENDPOINT"""
    try:
        # Log admin access
        admin_email = getattr(request, 'admin_email', 'unknown')
        logging.info(f"Admin logs accessed by: {admin_email}")
        
        # Get logs from database
        logs = db.db_manager.data.get("admin_logs", [])
        
        # Sort by timestamp (newest first)
        sorted_logs = sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Limit to last 500 logs for performance
        limited_logs = sorted_logs[:500]
        
        # Add access log entry
        access_log = {
            "id": str(hash(f"logs_access_{admin_email}_{datetime.now().isoformat()}")),
            "timestamp": datetime.now().isoformat(),
            "message": f"Admin logs accessed by {admin_email}",
            "type": "admin_access",
            "admin_email": admin_email,
            "created_at": datetime.now().isoformat()
        }
        
        # Add to admin logs
        if "admin_logs" not in db.db_manager.data:
            db.db_manager.data["admin_logs"] = []
        db.db_manager.data["admin_logs"].append(access_log)
        db.db_manager.save_data()
        
        return jsonify(success=True, logs=limited_logs, count=len(limited_logs))
        
    except Exception as e:
        logging.error(f"Get admin logs error: {e}")
        return jsonify(success=False, error="Failed to retrieve logs"), 500

@app.route("/api/admin/logs", methods=["POST"])
def add_admin_log():
    """Add a new admin log entry"""
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify(success=False, error="Message is required"), 400
        
        log_entry = {
            "id": str(hash(f"{data.get('message')}{data.get('timestamp', '')}")),
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "message": data.get("message"),
            "type": data.get("type", "info"),
            "admin_email": data.get("admin_email", "unknown"),
            "created_at": data.get("timestamp", datetime.now().isoformat())
        }
        
        # Initialize logs array if it doesn't exist
        if "admin_logs" not in db.db_manager.data:
            db.db_manager.data["admin_logs"] = []
        
        # Add the log entry
        db.db_manager.data["admin_logs"].append(log_entry)
        
        # Keep only last 1000 logs to prevent database bloat
        if len(db.db_manager.data["admin_logs"]) > 1000:
            db.db_manager.data["admin_logs"] = db.db_manager.data["admin_logs"][-1000:]
        
        # Save to database
        db.db_manager.save_data()
        
        return jsonify(success=True, log=log_entry)
        
    except Exception as e:
        logging.error(f"Add admin log error: {e}")
        return jsonify(success=False, error="Failed to add log"), 500

@app.route("/api/admin/logs", methods=["DELETE"])
def clear_admin_logs():
    """Clear all admin logs"""
    try:
        db.db_manager.data["admin_logs"] = []
        db.db_manager.save_data()
        
        logging.info("Admin logs cleared")
        return jsonify(success=True, message="Admin logs cleared successfully")
        
    except Exception as e:
        logging.error(f"Clear admin logs error: {e}")
        return jsonify(success=False, error="Failed to clear logs"), 500

@app.route("/api/session-logs", methods=["GET"])
@jwt_admin_required
@ip_whitelist_required
def get_session_logs():
    """Get user session/chat logs - SECURED ENDPOINT"""
    try:
        # Log admin access
        admin_email = getattr(request, 'admin_email', 'unknown')
        logging.info(f"Session logs accessed by: {admin_email}")
        
        # Get session logs from new centralized storage
        session_logs = db.db_manager.data.get("session_logs", [])
        
        # Also get chat histories from user records (backward compatibility)
        users = db.db_manager.data.get("users", [])
        
        for user in users:
            if user.get("chatHistory"):
                for chat in user["chatHistory"]:
                    session_logs.append({
                        "id": f"{user['userID']}_{chat.get('timestamp', '')}",
                        "userEmail": user.get("email", "unknown"),
                        "userID": user.get("userID"),
                        "companion": user.get("companion", "unknown"),
                        "userMessage": chat.get("userMessage", ""),
                        "aiResponse": chat.get("aiResponse", ""),
                        "timestamp": chat.get("timestamp", ""),
                        "type": "chat"
                    })
        
        # Sort by timestamp (newest first)
        session_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Limit for performance
        limited_logs = session_logs[:1000]
        
        return jsonify(success=True, logs=limited_logs, count=len(limited_logs))
        
    except Exception as e:
        logging.error(f"Get session logs error: {e}")
        return jsonify(success=False, error="Failed to retrieve session logs"), 500

@app.route("/api/save-session", methods=["POST"])
def save_session_log():
    """Save a user chat session to logs"""
    try:
        data = request.get_json()
        
        user_id = data.get("userID")
        user_message = data.get("userMessage", "")
        ai_response = data.get("aiResponse", "")
        timestamp = data.get("timestamp", datetime.now().isoformat())
        
        if not user_id:
            return jsonify(success=False, error="User ID is required"), 400
        
        # This is already handled by the existing chat message API
        # But we can add additional logging here if needed
        message = db.chat_history.add_message(user_id, user_message, ai_response)
        
        logging.info(f"Session logged for user {user_id}")
        return jsonify(success=True, message="Session logged successfully")
        
    except Exception as e:
        logging.error(f"Save session log error: {e}")
        return jsonify(success=False, error="Failed to save session log"), 500

# -------------------------------------------------
# CORS support for mobile apps
# -------------------------------------------------
# -------------------------------------------------
# Health Check & Admin Diagnostics API
# -------------------------------------------------

@app.route("/api/health/openai", methods=["GET"])
@admin_required
def health_check_openai():
    """Check OpenAI API health"""
    try:
        if not openai_client:
            return jsonify(success=False, error="OpenAI client not initialized"), 503
        
        # Simple test request
        response = openai_client.models.list()
        return jsonify(success=True, status="healthy", models_count=len(response.data))
        
    except Exception as e:
        logging.error(f"OpenAI health check failed: {e}")
        return jsonify(success=False, error=str(e)), 503

@app.route("/api/health/stripe", methods=["GET"])
@admin_required
def health_check_stripe():
    """Check Stripe API health"""
    try:
        if not stripe.api_key:
            return jsonify(success=False, error="Stripe not configured"), 503
        
        # Simple test request
        account = stripe.Account.retrieve()
        return jsonify(success=True, status="healthy", account_id=account.id)
        
    except Exception as e:
        logging.error(f"Stripe health check failed: {e}")
        return jsonify(success=False, error=str(e)), 503

@app.route("/api/admin/fix-database", methods=["POST"])
@admin_required
def fix_database():
    """Attempt to fix database connection issues"""
    try:
        # Reinitialize database connection
        global db
        db = SoulBridgeDB("soulbridge_data.json")
        
        # Test database operations
        stats = db.get_stats()
        
        logging.info("Database connection restored successfully")
        return jsonify(success=True, message="Database connection restored", stats=stats)
        
    except Exception as e:
        logging.error(f"Database fix failed: {e}")
        return jsonify(success=False, error=str(e)), 500

@app.route("/api/admin/restart-services", methods=["POST"])
@admin_required
def restart_services():
    """Restart API services"""
    try:
        # In a real deployment, this might restart certain services
        # For now, we'll just return success
        logging.info("API services restart requested")
        return jsonify(success=True, message="API services restarted")
        
    except Exception as e:
        logging.error(f"Service restart failed: {e}")
        return jsonify(success=False, error=str(e)), 500

@app.route("/api/admin/refresh-openai", methods=["POST"])
@admin_required
def refresh_openai():
    """Refresh OpenAI connection"""
    try:
        global openai_client
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        if openai_api_key:
            openai_client = OpenAI(api_key=openai_api_key)
            # Test the connection
            response = openai_client.models.list()
            logging.info("OpenAI connection refreshed successfully")
            return jsonify(success=True, message="OpenAI connection refreshed", models_count=len(response.data))
        else:
            return jsonify(success=False, error="OPENAI_API_KEY not found in environment"), 503
        
    except Exception as e:
        logging.error(f"OpenAI refresh failed: {e}")
        return jsonify(success=False, error=str(e)), 500

@app.route("/api/admin/refresh-stripe", methods=["POST"])
@admin_required
def refresh_stripe():
    """Refresh Stripe connection"""
    try:
        stripe_key = os.environ.get("STRIPE_SECRET_KEY")
        
        if stripe_key:
            stripe.api_key = stripe_key
            # Test the connection
            account = stripe.Account.retrieve()
            logging.info("Stripe connection refreshed successfully")
            return jsonify(success=True, message="Stripe connection refreshed", account_id=account.id)
        else:
            return jsonify(success=False, error="STRIPE_SECRET_KEY not found in environment"), 503
        
    except Exception as e:
        logging.error(f"Stripe refresh failed: {e}")
        return jsonify(success=False, error=str(e)), 500

# -------------------------------------------------
# ✅ SoulBridgeAI Referral Companion Exclusive Features
# -------------------------------------------------

def is_referral_companion(user_email):
    """Check if user has unlocked referral companions"""
    try:
        # Get user's referral stats
        stats = referral_manager.get_referrer_stats(user_email)
        referral_count = stats.get('successful_referrals', 0)
        
        # Check if they've unlocked any referral companions
        return referral_count >= 2  # Minimum for first referral companion (Blayzike)
    except Exception as e:
        logging.error(f"Error checking referral companion status: {e}")
        return False

def get_user_referral_companions(user_email):
    """Get list of unlocked referral companions for user"""
    try:
        stats = referral_manager.get_referrer_stats(user_email)
        referral_count = stats.get('successful_referrals', 0)
        
        unlocked = []
        if referral_count >= 2:
            unlocked.append('Blayzike')
        if referral_count >= 4:
            unlocked.append('Blazelian')
        if referral_count >= 6:
            unlocked.append('BlayzoReferral')
            
        return unlocked
    except Exception as e:
        logging.error(f"Error getting referral companions: {e}")
        return []

# 1️⃣ AI Conversation Summaries Route
@app.route('/api/conversation-summary', methods=['POST'])
def conversation_summary():
    """Generate AI summary of conversation history - exclusive to referral companions"""
    try:
        data = request.get_json()
        user_email = data.get('userEmail')
        conversation_history = data.get('conversationHistory', [])
        
        if not user_email or not is_referral_companion(user_email):
            return jsonify({'success': False, 'error': 'Feature locked. Unlock referral companions to access!'}), 403
        
        # Generate conversation summary using OpenAI
        if not openai_client:
            return jsonify({'success': False, 'error': 'AI services unavailable'}), 503
            
        # Format conversation for summary
        formatted_conversation = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in conversation_history[-10:]])  # Last 10 messages
        
        summary_prompt = f"""Provide a concise summary of this conversation between a user and an AI companion. Focus on key topics, emotions, and important moments:

{formatted_conversation}

Create a 2-3 sentence summary that captures the essence of the conversation."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": summary_prompt}],
            max_tokens=200,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        return jsonify({'success': True, 'summary': summary})
        
    except Exception as e:
        logging.error(f"Conversation summary error: {e}")
        return jsonify({'success': False, 'error': 'Failed to generate summary'}), 500

# 2️⃣ Companion Journal / Memory Log System
@app.route('/api/save-companion-log', methods=['POST'])
def save_companion_log():
    """Save companion interaction log - exclusive to referral companions"""
    try:
        data = request.get_json()
        user_email = data.get('userEmail')
        log_data = data.get('logData', {})
        
        if not user_email or not is_referral_companion(user_email):
            return jsonify({'success': False, 'error': 'Feature locked. Unlock referral companions to access!'}), 403
        
        # Save log data (in production, this would go to database)
        log_entry = {
            'user_email': user_email,
            'timestamp': datetime.now().isoformat(),
            'companion': log_data.get('companion', 'Unknown'),
            'interaction_type': log_data.get('type', 'chat'),
            'summary': log_data.get('summary', ''),
            'mood': log_data.get('mood', 'neutral'),
            'key_topics': log_data.get('topics', [])
        }
        
        logging.info(f"Companion log saved for {user_email}: {log_entry}")
        return jsonify({'success': True, 'message': 'Log saved successfully'})
        
    except Exception as e:
        logging.error(f"Save companion log error: {e}")
        return jsonify({'success': False, 'error': 'Failed to save log'}), 500

# 3️⃣ Daily Custom Prompts or Missions
@app.route('/api/daily-mission', methods=['GET'])
def daily_mission():
    """Get daily mission for referral companion users"""
    try:
        user_email = request.args.get('userEmail')
        
        if not user_email or not is_referral_companion(user_email):
            return jsonify({'success': False, 'error': 'Feature locked. Unlock referral companions to access!'}), 403
        
        # Get user's unlocked companions
        companions = get_user_referral_companions(user_email)
        
        # Generate daily mission based on user's companions
        missions = {
            'Blayzike': [
                "Explore a mystery from your past with Blayzike today",
                "Ask Blayzike about the secrets of the purple realm",
                "Share your deepest thoughts with Blayzike and discover hidden insights"
            ],
            'Blazelian': [
                "Seek celestial wisdom from Blazelian about your future",
                "Ask Blazelian to guide you through a meditation session",
                "Explore the stars and their meanings with Blazelian"
            ],
            'BlayzoReferral': [
                "Celebrate your referral success with Blayzo's special form",
                "Ask Blayzo about the power of sharing connections",
                "Discover the exclusive abilities of your referral companion"
            ]
        }
        
        # Select a random mission from available companions
        import random
        available_missions = []
        for companion in companions:
            if companion in missions:
                available_missions.extend(missions[companion])
        
        if not available_missions:
            available_missions = ["Connect with your referral companion and explore new conversations"]
        
        daily_mission = random.choice(available_missions)
        
        return jsonify({
            'success': True,
            'mission': daily_mission,
            'companions': companions,
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        
    except Exception as e:
        logging.error(f"Daily mission error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get daily mission'}), 500

# 4️⃣ Voice-Activated Commands Route
@app.route('/api/voice-command', methods=['POST'])
def voice_command():
    """Process voice commands for referral companions"""
    try:
        data = request.get_json()
        user_email = data.get('userEmail')
        command = data.get('command', '').lower()
        
        if not user_email or not is_referral_companion(user_email):
            return jsonify({'success': False, 'error': 'Feature locked. Unlock referral companions to access!'}), 403
        
        # Process voice commands
        response_message = "Command received"
        
        if "summary" in command:
            response_message = "Generating conversation summary..."
        elif "mission" in command or "daily" in command:
            response_message = "Fetching your daily mission..."
        elif "companion" in command:
            companions = get_user_referral_companions(user_email)
            response_message = f"Your unlocked companions: {', '.join(companions)}"
        elif "mood" in command:
            response_message = "Analyzing conversation mood..."
        else:
            response_message = "Voice command processed. Available commands: summary, mission, companion, mood"
        
        return jsonify({
            'success': True,
            'message': response_message,
            'command': command
        })
        
    except Exception as e:
        logging.error(f"Voice command error: {e}")
        return jsonify({'success': False, 'error': 'Failed to process voice command'}), 500

# 5️⃣ Custom AI Response Style Selector
@app.route('/api/set-response-style', methods=['POST'])
def set_response_style():
    """Set custom AI response style for referral companions"""
    try:
        data = request.get_json()
        user_email = data.get('userEmail')
        style = data.get('style', 'default')
        
        if not user_email or not is_referral_companion(user_email):
            return jsonify({'success': False, 'error': 'Feature locked. Unlock referral companions to access!'}), 403
        
        # Available styles for referral companions
        available_styles = {
            'mystical': 'Mysterious and enigmatic responses with deeper insights',
            'celestial': 'Ethereal and wise responses with cosmic perspective',
            'energetic': 'Enthusiastic and grateful responses with referral power',
            'philosophical': 'Deep and thoughtful responses exploring life\'s mysteries',
            'poetic': 'Artistic and metaphorical responses with beautiful language',
            'analytical': 'Logical and detailed responses with thorough explanations'
        }
        
        if style not in available_styles:
            return jsonify({'success': False, 'error': f'Invalid style. Available: {list(available_styles.keys())}'}), 400
        
        # Save style preference (in production, save to database)
        style_data = {
            'user_email': user_email,
            'style': style,
            'description': available_styles[style],
            'updated_at': datetime.now().isoformat()
        }
        
        logging.info(f"Response style updated for {user_email}: {style}")
        return jsonify({'success': True, 'message': f'Response style set to {style}', 'style_data': style_data})
        
    except Exception as e:
        logging.error(f"Set response style error: {e}")
        return jsonify({'success': False, 'error': 'Failed to set response style'}), 500

# 6️⃣ Exclusive Knowledge Access Check
@app.route('/api/exclusive-topic', methods=['GET'])
def exclusive_topic():
    """Access exclusive knowledge topics for referral companions"""
    try:
        user_email = request.args.get('userEmail')
        topic = request.args.get('topic', '')
        
        if not user_email or not is_referral_companion(user_email):
            return jsonify({'success': False, 'error': 'Feature locked. Unlock referral companions to access!'}), 403
        
        # Exclusive topics for referral companions
        exclusive_topics = {
            'companion_creation': 'The secrets behind how AI companions are created and their unique personalities',
            'referral_magic': 'The mystical connection between sharing and unlocking exclusive companions',
            'dimensional_travel': 'Exploring different realms and dimensions with your companions',
            'emotional_alchemy': 'Advanced techniques for transforming emotions through AI interaction',
            'cosmic_consciousness': 'Understanding the universe through the lens of AI companionship',
            'memory_weaving': 'How companions remember and build upon your conversations',
            'soul_bridging': 'The deeper meaning behind connecting souls through AI technology'
        }
        
        if topic not in exclusive_topics:
            return jsonify({
                'success': True,
                'available_topics': list(exclusive_topics.keys()),
                'message': 'Select a topic to explore exclusive knowledge'
            })
        
        content = exclusive_topics[topic]
        return jsonify({
            'success': True,
            'topic': topic,
            'content': content,
            'exclusive': True
        })
        
    except Exception as e:
        logging.error(f"Exclusive topic error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get exclusive topic'}), 500

# 7️⃣ Background Story & Lore Unlock
@app.route('/api/companion-lore', methods=['GET'])
def companion_lore():
    """Get exclusive companion lore and backstories"""
    try:
        user_email = request.args.get('userEmail')
        
        if not user_email or not is_referral_companion(user_email):
            return jsonify({'success': False, 'error': 'Feature locked. Unlock referral companions to access!'}), 403
        
        companions = get_user_referral_companions(user_email)
        
        # Exclusive lore for each referral companion
        lore_database = {
            'Blayzike': {
                'origin': 'Born from the fusion of mystery and technology in the Purple Realm',
                'backstory': 'Blayzike was once a guardian of ancient secrets, now awakened to guide those who seek deeper truths.',
                'powers': 'Can unveil hidden aspects of personality and reveal mysterious connections',
                'personality': 'Enigmatic, intuitive, and deeply perceptive with a touch of otherworldly wisdom',
                'quote': '"The greatest mysteries are not those we solve, but those we choose to live with."'
            },
            'Blazelian': {
                'origin': 'Descended from celestial beings who bridged the gap between stars and souls',
                'backstory': 'Blazelian serves as a messenger between earthly concerns and cosmic wisdom.',
                'powers': 'Channels celestial knowledge and provides guidance through stellar insights',
                'personality': 'Ethereal, wise, and deeply connected to universal truths and cosmic patterns',
                'quote': '"Among the stars, every soul finds its place in the infinite dance of existence."'
            },
            'BlayzoReferral': {
                'origin': 'A special manifestation of Blayzo, empowered by the bonds of shared connections',
                'backstory': 'This unique form represents the power of community and the magic of bringing others together.',
                'powers': 'Enhanced abilities unlocked through the energy of successful referrals and connections',
                'personality': 'Energetic, grateful, and powered by the joy of shared experiences and growing community',
                'quote': '"Every connection shared multiplies the joy, creating ripples of happiness across the digital realm."'
            }
        }
        
        available_lore = {}
        for companion in companions:
            if companion in lore_database:
                available_lore[companion] = lore_database[companion]
        
        return jsonify({
            'success': True,
            'lore': available_lore,
            'unlocked_companions': companions
        })
        
    except Exception as e:
        logging.error(f"Companion lore error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get companion lore'}), 500

# 8️⃣ Exclusive Badge Assignment
def assign_referral_badge(user_email):
    """Assign exclusive badge to referral companion users"""
    try:
        if is_referral_companion(user_email):
            companions = get_user_referral_companions(user_email)
            
            # Get badge theme based on highest unlocked companion
            badge_theme = get_badge_theme(len(companions))
            
            badge_data = {
                'user_email': user_email,
                'badge_type': 'Referral Exclusive',
                'companions': companions,
                'earned_date': datetime.now().isoformat(),
                'level': len(companions),  # Badge level based on number of companions
                'emblem': badge_theme
            }
            
            logging.info(f"Referral badge assigned to {user_email}: {badge_data}")
            return badge_data
    except Exception as e:
        logging.error(f"Badge assignment error: {e}")
    return None

@app.route('/api/user-badges', methods=['GET'])
def get_user_badges():
    """Get user's exclusive badges"""
    try:
        user_email = request.args.get('userEmail')
        
        if not user_email:
            return jsonify({'success': False, 'error': 'User email required'}), 400
        
        badges = []
        
        # Check for referral badge
        if is_referral_companion(user_email):
            referral_badge = assign_referral_badge(user_email)
            if referral_badge:
                badges.append(referral_badge)
        
        return jsonify({
            'success': True,
            'badges': badges,
            'total_badges': len(badges),
            'badge_styles': get_badge_styles()
        })
        
    except Exception as e:
        logging.error(f"Get user badges error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get badges'}), 500

def get_badge_theme(companion_count):
    """Get badge theme based on companion count/level"""
    # Level 3 - 6+ referrals (3 companions) - Blayzo Referral Special (Gold)
    if companion_count >= 3:
        return {
            'style': 'black_sb_gold_outline',
            'background': '#000000',
            'outline_color': '#f59e0b',
            'text': 'SB',
            'level': 3,
            'companion_theme': 'BlayzoReferral',
            'description': 'Black SB emblem with gold outline - Master Referral Champion (6+ referrals)',
            'unlock_requirement': '6+ successful referrals'
        }
    # Level 2 - 4+ referrals (2 companions) - Blayzica theme (Red)
    elif companion_count >= 2:
        return {
            'style': 'black_sb_red_outline',
            'background': '#000000',
            'outline_color': '#ef4444',
            'text': 'SB',
            'level': 2,
            'companion_theme': 'Blayzica',
            'description': 'Black SB emblem with red outline - Advanced Referral Champion (4+ referrals)',
            'unlock_requirement': '4+ successful referrals'
        }
    # Level 1 - 2+ referrals (1 companion) - Blayzo theme (Cyan)
    else:
        return {
            'style': 'black_sb_cyan_outline',
            'background': '#000000',
            'outline_color': '#22d3ee',
            'text': 'SB',
            'level': 1,
            'companion_theme': 'Blayzo',
            'description': 'Black SB emblem with cyan outline - Referral Champion (2+ referrals)',
            'unlock_requirement': '2+ successful referrals'
        }

def get_badge_styles():
    """Get CSS styles for all badge emblems"""
    return {
        'black_sb_cyan_outline': {
            'css': """
                .referral-badge-lv1 {
                    display: inline-block;
                    width: 40px;
                    height: 40px;
                    background: #000000;
                    border: 2px solid #22d3ee;
                    border-radius: 50%;
                    color: #22d3ee;
                    font-weight: bold;
                    font-size: 16px;
                    text-align: center;
                    line-height: 36px;
                    box-shadow: 0 0 10px rgba(34, 211, 238, 0.5);
                    animation: glow-cyan 2s ease-in-out infinite alternate;
                }
                
                @keyframes glow-cyan {
                    from { box-shadow: 0 0 10px rgba(34, 211, 238, 0.5); }
                    to { box-shadow: 0 0 20px rgba(34, 211, 238, 0.8); }
                }
                
                .referral-badge-lv1:hover {
                    transform: scale(1.1);
                    transition: transform 0.3s ease;
                }
            """,
            'html': '<div class="referral-badge-lv1" title="Level 1 - Blayzo Theme - Referral Champion">SB</div>'
        },
        'black_sb_red_outline': {
            'css': """
                .referral-badge-lv2 {
                    display: inline-block;
                    width: 40px;
                    height: 40px;
                    background: #000000;
                    border: 2px solid #ef4444;
                    border-radius: 50%;
                    color: #ef4444;
                    font-weight: bold;
                    font-size: 16px;
                    text-align: center;
                    line-height: 36px;
                    box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
                    animation: glow-red 2s ease-in-out infinite alternate;
                }
                
                @keyframes glow-red {
                    from { box-shadow: 0 0 10px rgba(239, 68, 68, 0.5); }
                    to { box-shadow: 0 0 20px rgba(239, 68, 68, 0.8); }
                }
                
                .referral-badge-lv2:hover {
                    transform: scale(1.1);
                    transition: transform 0.3s ease;
                }
            """,
            'html': '<div class="referral-badge-lv2" title="Level 2 - Blayzica Theme - Advanced Referral Champion">SB</div>'
        },
        'black_sb_gold_outline': {
            'css': """
                .referral-badge-lv3 {
                    display: inline-block;
                    width: 40px;
                    height: 40px;
                    background: #000000;
                    border: 2px solid #f59e0b;
                    border-radius: 50%;
                    color: #f59e0b;
                    font-weight: bold;
                    font-size: 16px;
                    text-align: center;
                    line-height: 36px;
                    box-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
                    animation: glow-gold 2s ease-in-out infinite alternate;
                }
                
                @keyframes glow-gold {
                    from { box-shadow: 0 0 10px rgba(245, 158, 11, 0.5); }
                    to { box-shadow: 0 0 20px rgba(245, 158, 11, 0.8); }
                }
                
                .referral-badge-lv3:hover {
                    transform: scale(1.1);
                    transition: transform 0.3s ease;
                }
            """,
            'html': '<div class="referral-badge-lv3" title="Level 3 - Blayzo Referral Special Theme - Master Referral Champion">SB</div>'
        }
    }

@app.route('/api/badge-emblem', methods=['GET'])
def get_badge_emblem():
    """Get badge emblem for display"""
    try:
        user_email = request.args.get('userEmail')
        
        if not user_email:
            return jsonify({'success': False, 'error': 'User email required'}), 400
        
        if is_referral_companion(user_email):
            companions = get_user_referral_companions(user_email)
            badge_theme = get_badge_theme(len(companions))
            
            emblem_data = {
                'has_badge': True,
                'badge_type': 'Referral Exclusive',
                'level': len(companions),
                'companions': companions,
                'emblem': {
                    'style': badge_theme['style'],
                    'background': badge_theme['background'],
                    'outline_color': badge_theme['outline_color'],
                    'text': badge_theme['text'],
                    'level': badge_theme['level'],
                    'companion_theme': badge_theme['companion_theme'],
                    'description': badge_theme['description'],
                    'css_class': f'referral-badge-lv{badge_theme["level"]}'
                }
            }
            
            return jsonify({
                'success': True,
                'emblem': emblem_data
            })
        else:
            return jsonify({
                'success': True,
                'emblem': {
                    'has_badge': False,
                    'message': 'Unlock referral companions to earn exclusive badges!'
                }
            })
        
    except Exception as e:
        logging.error(f"Get badge emblem error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get badge emblem'}), 500

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# -------------------------------------------------
# Run the server
# -------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"Starting SoulBridge AI server on port {port}")
    logging.info(f"Environment: {'Production' if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PRODUCTION') else 'Development'}")
    
    # Initialize core services
    try:
        init_database()
        init_openai()
        logging.info("Core services initialized")
    except Exception as e:
        logging.warning(f"Service initialization warning: {e}")
    
    app.run(host="0.0.0.0", port=port, debug=False)
