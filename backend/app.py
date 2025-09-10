"""
SoulBridge AI - Modular Application
Rebuilt from 19,326-line monolith using extracted modules
Clean Flask application with Blueprint architecture
"""

# ---- BEGIN SELF-HEALING COMPAT SHIM ----
# Ensures legacy import "modules.tiers.artistic_time:get_effective_access" exists,
# even after migrating to the single "Soul Companions" tier.
import os, sys, types, importlib, importlib.util
from pathlib import Path
from textwrap import dedent

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def _inject_runtime_shim():
    """Read-only FS fallback: provide modules.tiers + artistic_time entirely in memory."""
    # Ensure a modules package object exists (usually it already does)
    if not importlib.util.find_spec("modules"):
        sys.modules["modules"] = types.ModuleType("modules")
    # Create a package-like object for modules.tiers
    tiers_pkg = types.ModuleType("modules.tiers")
    tiers_pkg.__path__ = []  # mark as package
    # Create the submodule with get_effective_access
    art = types.ModuleType("modules.tiers.artistic_time")

    def _envint(name, default):
        try:
            return int(os.getenv(name, default))
        except Exception:
            return default

    def get_effective_access(*_args, **_kwargs):
        # Single-tier: Soul Companions. Tweak limits via env vars if desired.
        limits = {
            "decoder":   _envint("SC_LIMIT_DECODER",   15),
            "fortune":   _envint("SC_LIMIT_FORTUNE",    8),
            "horoscope": _envint("SC_LIMIT_HOROSCOPE", 10),
        }
        return {"plan": "soul_companions", "limits": limits, "features": {"companions": "all"}}

    art.get_effective_access = get_effective_access
    sys.modules["modules.tiers"] = tiers_pkg
    sys.modules["modules.tiers.artistic_time"] = art

def ensure_legacy_tiers_shim():
    """Create files if missing; otherwise fall back to runtime shim."""
    modules_dir = PROJECT_ROOT / "modules"
    tiers_dir = modules_dir / "tiers"
    files = {
        modules_dir / "__init__.py": "",
        tiers_dir / "__init__.py": "from .artistic_time import get_effective_access\n__all__=['get_effective_access']\n",
        tiers_dir / "artistic_time.py": dedent("""\
            import os
            def _envint(name: str, default: int) -> int:
                try: return int(os.getenv(name, default))
                except Exception: return default
            def get_effective_access(*_args, **_kwargs):
                limits = {
                    "decoder":   _envint("SC_LIMIT_DECODER",   15),
                    "fortune":   _envint("SC_LIMIT_FORTUNE",    8),
                    "horoscope": _envint("SC_LIMIT_HOROSCOPE", 10),
                }
                return {"plan": "soul_companions", "limits": limits, "features": {"companions": "all"}}
        """),
    }
    try:
        tiers_dir.mkdir(parents=True, exist_ok=True)
        for path, content in files.items():
            if not path.exists():
                path.write_text(content, encoding="utf-8")
        importlib.invalidate_caches()
        importlib.import_module("modules.tiers.artistic_time")
    except Exception:
        # e.g., read-only image or permission issue → in-memory shim
        _inject_runtime_shim()

# Run before anything imports modules.chat → modules.tiers
ensure_legacy_tiers_shim()
# ---- END SELF-HEALING COMPAT SHIM ----

# Single source of truth for blueprint registration - guard against redefinition
if globals().get("_REGISTER_BLUEPRINTS_DEFINED"):
    raise RuntimeError("register_blueprints already defined in backend/app.py")

import logging
import traceback
from datetime import datetime, timedelta
from flask import Flask, session, request, redirect, jsonify, url_for
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from security_config import init_security, enhance_security_headers, secure_error_handlers

# Initialize safe logging to prevent unicode crashes
try:
    from modules.core.logging_init import init_safe_logging
    init_safe_logging(logging.INFO)
except ImportError:
    # Fallback basic logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Detect prod on Railway first
    IS_RAILWAY = bool(os.environ.get("RAILWAY_PROJECT_ID"))
    IS_PROD = os.environ.get("ENVIRONMENT") == "production" or IS_RAILWAY
    
    # ----- Core secrets -----
    # IMPORTANT: keep SECRET_KEY stable across deploys/instances
    secret_key = os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY")
    if not secret_key or secret_key == "dev-only-change-me":
        if IS_RAILWAY:
            logger.error("❌ FLASK_SECRET_KEY not set in production - sessions will not survive deploys!")
        secret_key = "dev-only-change-me-in-production"
    app.config["SECRET_KEY"] = secret_key

    # Make Flask trust Railway's reverse proxy so it sees HTTPS correctly.
    # Without this, Flask may think the request is http and set cookies wrong.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # ----- Session configuration -----
    # Try Redis-backed sessions first (best for production)
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        try:
            import redis
            from flask_session import Session
            
            app.config.update(
                SESSION_TYPE="redis",
                SESSION_REDIS=redis.from_url(redis_url),
                SESSION_PERMANENT=True,
                PERMANENT_SESSION_LIFETIME=timedelta(days=30),
                SESSION_USE_SIGNER=True,
                SESSION_KEY_PREFIX="soulbridge:",
            )
            Session(app)
            logger.info("✅ Redis sessions configured successfully")
            
        except Exception as redis_error:
            logger.warning(f"⚠️ Redis sessions failed, falling back to filesystem: {redis_error}")
            redis_url = None
    
    # Fallback: Filesystem sessions (default Flask behavior with enhanced config)
    if not redis_url:
        app.config.update(
            SESSION_PERMANENT=True,
            PERMANENT_SESSION_LIFETIME=timedelta(days=30),
            SESSION_COOKIE_NAME="session",
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_PATH="/",
            SESSION_REFRESH_EACH_REQUEST=True,
        )
        logger.info("✅ Filesystem sessions configured (fallback)")
    
    # Cookie security settings (applies to both Redis and filesystem)
    app.config.update(
        SESSION_COOKIE_NAME="session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_PATH="/",
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
        
        # Database schema is now handled by modules/shared/database
        logger.info("✅ Database schema initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Create database manager for blueprint initialization
    database_manager = None
    try:
        from database_utils import get_database
        database_manager = get_database()
        logger.info("✅ Database manager created for blueprints")
    except Exception as e:
        logger.error(f"❌ Failed to create database manager: {e}")
    
    # Register all module blueprints
    register_blueprints(app, database_manager)
    
    # Initialize all systems  
    initialize_systems(app)
    
    # Initialize security (rate limiting, CSRF, etc.)
    limiter, csrf = init_security(app)
    
    # Set up global middleware
    setup_middleware(app)
    
    # Set up enhanced security headers
    enhance_security_headers(app)
    
    # Set up secure error handlers
    secure_error_handlers(app)
    
    # Set up v1 compatibility routes
    setup_v1_compatibility_routes(app)
    
    # Set up error handlers (legacy - secure_error_handlers replaces this)
    # setup_error_handlers(app)
    
    # Add diagnostic routes for session debugging
    @app.route("/_debug/session")
    def _debug_session():
        return jsonify(
            session=dict(session),
            keys=list(session.keys()),
            permanent=session.permanent,
        )
    
    @app.route("/_debug/fix-schema")
    def _debug_fix_schema():
        """Manual schema creation endpoint"""
        return jsonify({
            "success": True,
            "message": "Database schema is now handled by modules/shared/database"
        })

    @app.after_request
    def _log_set_cookie(resp):
        # Log Set-Cookie once (or when logging is enabled)
        sc = resp.headers.get("Set-Cookie")
        if sc and "/auth/login" in request.path:
            logger.info(f"Set-Cookie on login: {sc}")
        return resp

    # ===== WORKING ROUTES (rebuilt from module blueprints) =====
    
    # AUTH ROUTES (from auth module blueprint)
    @app.route("/auth/login", methods=["GET", "POST"])
    def auth_login():
        """Enhanced login page with database auth and referral handling"""
        if request.method == "GET":
            from flask import render_template
            error_message = request.args.get('error')
            return_to = request.args.get('return_to')
            
            # Check for referral code in URL (/?ref=XXXX)
            ref_code = request.args.get('ref', '').upper().strip()
            if ref_code:
                # Store in session for signup process
                session['pending_referral_code'] = ref_code
                logger.info(f"Stored referral code in session: {ref_code}")
            
            return render_template('login.html', 
                                 error=error_message, 
                                 return_to=return_to,
                                 ref_code=ref_code)
        
        # Handle POST - database-integrated authentication
        try:
            from database_utils import get_database
            import bcrypt
            
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Please enter both email and password', 'error')
                return redirect('/auth/login')
            
            # Database authentication
            db = get_database()
            if not db:
                flash('Database connection error', 'error')
                return redirect('/auth/login')
                
            conn = db.get_connection()
            cursor = conn.cursor()
            
            try:
                # Find user by email
                cursor.execute("""
                    SELECT id, email, password_hash, user_plan, display_name, 
                           trial_active, artistic_credits, selected_companion
                    FROM users 
                    WHERE email = ?
                """, (email,))
                
                user = cursor.fetchone()
                if not user:
                    flash('Invalid email or password', 'error')
                    return redirect('/auth/login')
                
                user_id, user_email, password_hash, user_plan, display_name, trial_active, artistic_credits, selected_companion = user
                
                # Verify password
                if not password_hash or not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                    flash('Invalid email or password', 'error')
                    return redirect('/auth/login')
                
                # Successful login - set session
                session['logged_in'] = True
                session['user_id'] = user_id
                session['email'] = user_email
                session['user_plan'] = user_plan or 'bronze'
                session['display_name'] = display_name or user_email.split('@')[0]
                session['trial_active'] = bool(trial_active)
                session['artistic_credits'] = artistic_credits or 0
                session['selected_companion'] = selected_companion
                session.permanent = True
                
                # Update last login
                cursor.execute("""
                    UPDATE users 
                    SET last_login = datetime('now')
                    WHERE id = ?
                """, (user_id,))
                conn.commit()
                
                # Generate referral code if user doesn't have one
                try:
                    from modules.referrals.routes import ensure_user_has_code
                    ensure_user_has_code(user_id)
                except Exception as e:
                    logger.warning(f"Could not ensure referral code for user {user_id}: {e}")
                
                logger.info(f"Successful login for user {user_id} ({user_email})")
                
                # Redirect logic
                return_to = request.args.get('return_to', '')
                if return_to:
                    return redirect(f'/{return_to}')
                
                # Default redirect based on user status
                if not display_name or display_name == user_email.split('@')[0]:
                    return redirect('/profile')  # Need to set up profile
                elif not selected_companion:
                    return redirect('/companions')  # Need to select companion
                else:
                    return redirect('/dashboard')  # Go to main app
                    
            finally:
                cursor.close()
                conn.close()
            
        except ImportError as e:
            logger.error(f"Missing dependency for authentication: {e}")
            flash('Authentication system not ready', 'error')
            return redirect('/auth/login')
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('Login failed. Please try again.', 'error')
            return redirect('/auth/login')
    
    @app.route("/auth/logout")
    def auth_logout():
        """Logout - from auth blueprint"""
        session.clear()
        return redirect('/auth/login')
    
    @app.route("/auth/register", methods=["GET", "POST"])
    def auth_register():
        """Registration with database integration"""
        if request.method == "GET":
            from flask import render_template
            return render_template('register.html')
        
        # Handle POST - both form data and JSON
        try:
            # Try JSON first, then form data
            if request.is_json:
                data = request.get_json()
                display_name = data.get('display_name', '').strip()
                email = data.get('email', '').strip()
                password = data.get('password', '')
                is_json_request = True
            else:
                display_name = request.form.get('display_name', '').strip()
                email = request.form.get('email', '').strip()
                password = request.form.get('password', '')
                is_json_request = False
            
            if not display_name or not email or not password:
                error_msg = 'Please fill all fields'
                if is_json_request:
                    return jsonify({"success": False, "error": error_msg}), 400
                return redirect(f'/auth/register?error={error_msg}')
            
            # Database registration
            cursor = None
            conn = None
            try:
                import bcrypt
                
                # Hash password
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                # Database connection
                import sqlite3
                conn = sqlite3.connect('soulbridge.db', timeout=30.0)
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    error_msg = 'Email already registered'
                    if is_json_request:
                        return jsonify({"success": False, "error": error_msg}), 400
                    return redirect(f'/auth/register?error={error_msg}')
                
                # Create user
                cursor.execute("""
                    INSERT INTO users (email, password_hash, display_name, user_plan, created_at)
                    VALUES (?, ?, ?, 'bronze', datetime('now'))
                """, (email, password_hash, display_name))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                # Set session
                session['logged_in'] = True
                session['email'] = email
                session['user_id'] = user_id
                session['display_name'] = display_name
                session['user_plan'] = 'bronze'
                session.permanent = True
                
                logger.info(f"✅ User registered successfully: {email} (ID: {user_id})")
                
                if is_json_request:
                    return jsonify({
                        "success": True,
                        "message": "Account created successfully! Welcome to SoulBridge AI.",
                        "redirect": "/intro"
                    })
                else:
                    return redirect('/intro')
                    
            except ImportError:
                error_msg = 'Registration system unavailable'
                logger.error("❌ bcrypt not installed - cannot hash passwords")
                if is_json_request:
                    return jsonify({"success": False, "error": error_msg}), 500
                return redirect(f'/auth/register?error={error_msg}')
                
            except Exception as db_error:
                error_msg = 'Registration failed'
                logger.error(f"❌ Registration database error: {db_error}")
                if is_json_request:
                    return jsonify({"success": False, "error": error_msg}), 500
                return redirect(f'/auth/register?error={error_msg}')
                
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            
        except Exception as e:
            error_msg = 'Registration failed'
            logger.error(f"❌ Registration error: {e}")
            if request.is_json:
                return jsonify({"success": False, "error": error_msg}), 500
            return redirect(f'/auth/register?error={error_msg}')
    
    @app.route("/auth/forgot-password", methods=["GET", "POST"])
    def auth_forgot_password():
        """Secure token-based password reset system"""
        if request.method == "GET":
            from flask import render_template
            return render_template('forgot_password.html')
        
        # Handle POST - initiate password reset
        try:
            email = request.form.get('email', '').strip().lower()
            
            # Always return generic success message to prevent email enumeration
            generic_message = 'If an account with that email exists, a reset link has been sent.'
            
            if not email:
                flash(generic_message, 'success')
                return redirect('/auth/forgot-password')
            
            # Database operations
            cursor = None
            conn = None
            try:
                import hashlib
                import secrets
                import sqlite3
                from datetime import datetime, timedelta
                
                # Database connection
                conn = sqlite3.connect('soulbridge.db', timeout=30.0)
                cursor = conn.cursor()
                
                # Check if user exists (case-insensitive)
                cursor.execute("SELECT id, email, display_name FROM users WHERE LOWER(email) = ?", (email,))
                user = cursor.fetchone()
                
                if not user:
                    # Still return success to prevent email enumeration
                    flash(generic_message, 'success')
                    return redirect('/auth/forgot-password')
                
                user_id, user_email, display_name = user
                
                # Generate secure token (32 bytes = 43 URL-safe chars)
                token_raw = secrets.token_urlsafe(32)
                
                # Hash the token for database storage (never store raw tokens)
                token_hash = hashlib.sha256(token_raw.encode('utf-8')).hexdigest()
                
                # Token expires in 1 hour (SQLite-compatible format)
                from datetime import timezone
                expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat() + 'Z'
                
                # Get client info
                client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')
                user_agent = request.headers.get('User-Agent', '')[:500]  # Limit length
                
                # Store token in database
                cursor.execute("""
                    INSERT INTO password_reset_tokens 
                    (user_id, token_hash, expires_at, request_ip, request_ua)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, token_hash, expires_at, client_ip, user_agent))
                conn.commit()
                
                # In production, you'd email the reset link
                # For now, we'll show it in the success message for testing
                reset_url = f"{request.url_root}auth/reset-password?token={token_raw}"
                
                logger.info(f"Password reset token generated for user: {user_email} (ID: {user_id})")
                
                # Show reset link directly (in production, this would be emailed)
                flash(f'Reset link: {reset_url}', 'success')
                flash('(In production, this would be emailed to you)', 'success')
                flash('This link expires in 1 hour.', 'success')
                
                return redirect('/auth/forgot-password')
                
            except Exception as db_error:
                logger.error(f"Password reset database error: {db_error}", exc_info=True)
                flash(generic_message, 'success')  # Still return generic success
                return redirect('/auth/forgot-password')
                
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            flash('If an account with that email exists, a reset link has been sent.', 'success')
            return redirect('/auth/forgot-password')
    
    @app.route("/auth/reset-password", methods=["GET", "POST"])
    def auth_reset_password():
        """Complete password reset with token"""
        if request.method == "GET":
            # Validate token and show reset form
            token = request.args.get('token', '').strip()
            if not token:
                flash('Invalid reset link', 'error')
                return redirect('/auth/login')
            
            # Verify token
            is_valid = verify_reset_token(token)
            if not is_valid:
                flash('Reset link is invalid or expired', 'error')
                return redirect('/auth/login')
            
            from flask import render_template
            return render_template('reset_password.html', token=token)
        
        # Handle POST - process password reset
        try:
            token = request.form.get('token', '').strip()
            new_password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not token or not new_password or not confirm_password:
                flash('All fields are required', 'error')
                return redirect(f'/auth/reset-password?token={token}')
            
            if new_password != confirm_password:
                flash('Passwords do not match', 'error')
                return redirect(f'/auth/reset-password?token={token}')
            
            if len(new_password) < 8:
                flash('Password must be at least 8 characters', 'error')
                return redirect(f'/auth/reset-password?token={token}')
            
            # Verify and use token
            user_id = use_reset_token(token, new_password)
            if not user_id:
                flash('Reset link is invalid or expired', 'error')
                return redirect('/auth/login')
            
            flash('Password updated successfully! You can now sign in.', 'success')
            return redirect('/auth/login')
            
        except Exception as e:
            logger.error(f"Reset password error: {e}")
            flash('Password reset failed. Please try again.', 'error')
            return redirect('/auth/login')
    
    def verify_reset_token(token_raw):
        """Verify if a reset token is valid and not expired"""
        try:
            import hashlib
            import sqlite3
            from datetime import datetime, timezone
            
            token_hash = hashlib.sha256(token_raw.encode('utf-8')).hexdigest()
            
            conn = sqlite3.connect('soulbridge.db', timeout=30.0)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, expires_at, used_at 
                FROM password_reset_tokens 
                WHERE token_hash = ? 
                LIMIT 1
            """, (token_hash,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                return False
            
            user_id, expires_at, used_at = result
            
            # Check if already used
            if used_at:
                return False
            
            # Check if expired (handle SQLite datetime string format)
            try:
                expires_dt = datetime.fromisoformat(expires_at.replace('Z', ''))
            except ValueError:
                # Fallback for different datetime formats
                expires_dt = datetime.strptime(expires_at.replace('Z', ''), '%Y-%m-%dT%H:%M:%S.%f')
            
            if datetime.now(timezone.utc) > expires_dt:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False
    
    def use_reset_token(token_raw, new_password):
        """Use a reset token to change password, mark token as used"""
        try:
            import hashlib
            import sqlite3
            import bcrypt
            from datetime import datetime, timezone
            
            token_hash = hashlib.sha256(token_raw.encode('utf-8')).hexdigest()
            
            conn = sqlite3.connect('soulbridge.db', timeout=30.0)
            cursor = conn.cursor()
            
            # Get and verify token
            cursor.execute("""
                SELECT user_id, expires_at, used_at 
                FROM password_reset_tokens 
                WHERE token_hash = ? 
                LIMIT 1
            """, (token_hash,))
            
            result = cursor.fetchone()
            if not result:
                cursor.close()
                conn.close()
                return None
            
            user_id, expires_at, used_at = result
            
            # Check if already used
            if used_at:
                cursor.close()
                conn.close()
                return None
            
            # Check if expired (handle SQLite datetime string format)
            try:
                expires_dt = datetime.fromisoformat(expires_at.replace('Z', ''))
            except ValueError:
                # Fallback for different datetime formats
                expires_dt = datetime.strptime(expires_at.replace('Z', ''), '%Y-%m-%dT%H:%M:%S.%f')
            
            if datetime.now(timezone.utc) > expires_dt:
                cursor.close()
                conn.close()
                return None
            
            # Hash new password
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Update user's password
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
            
            # Mark token as used
            cursor.execute("""
                UPDATE password_reset_tokens 
                SET used_at = CURRENT_TIMESTAMP 
                WHERE token_hash = ?
            """, (token_hash,))
            
            # Invalidate other unused tokens for this user
            cursor.execute("""
                UPDATE password_reset_tokens 
                SET used_at = CURRENT_TIMESTAMP 
                WHERE user_id = ? AND used_at IS NULL AND token_hash != ?
            """, (user_id, token_hash))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Password successfully reset for user ID: {user_id}")
            return user_id
            
        except Exception as e:
            logger.error(f"Token usage error: {e}")
            return None
    
    # CORE ROUTES (from core module blueprint)
    @app.route("/")
    def home():
        """Home page redirect - from core blueprint"""
        if session.get('logged_in'):
            return redirect('/intro')
        return redirect('/auth/login')
    
    @app.route("/intro")
    def intro():
        """Intro page - from core blueprint"""
        from flask import render_template
        return render_template('intro.html')
    
    @app.route("/tiers")
    def tiers():
        """Tiers page - from core blueprint"""
        from flask import render_template
        return render_template('tier_comparison.html')
    
    # COMPANION ROUTES (from companions module blueprint)
    # OLD ROUTE - COMMENTED OUT TO USE MODULAR SKIN SYSTEM
    """
    @app.route("/companion-selection")
    def companion_selection():
        # Working companion selection page - rebuilt from blueprint guide
        try:
            from flask import render_template
            
            # Check if user is logged in (simple check)
            if not session.get('logged_in'):
                return redirect('/auth/login?return_to=companion-selection')
            
            # Use blueprint logic as guide
            user_plan = session.get('user_plan', 'bronze')
            tier_display = user_plan.title()
            
            # All companion data including Bronze, Silver, Gold, and Referral
            companions = [
                # Bronze companions (10) - all accessible
                {"id": "gamerjay_bronze", "name": "GamerJay", "tier": "bronze", "image_url": "/static/logos/GamerJay_Free_companion.png"},
                {"id": "blayzo_bronze", "name": "Blayzo", "tier": "bronze", "image_url": "/static/logos/Blayzo.png"},
                {"id": "blayzica_bronze", "name": "Blayzica", "tier": "bronze", "image_url": "/static/logos/Blayzica.png"},
                {"id": "claude_bronze", "name": "Claude", "tier": "bronze", "image_url": "/static/logos/Claude_Free.png"},
                {"id": "blayzia_bronze", "name": "Blayzia", "tier": "bronze", "image_url": "/static/logos/Blayzia.png"},
                {"id": "blayzion_bronze", "name": "Blayzion", "tier": "bronze", "image_url": "/static/logos/Blayzion.png"},
                {"id": "lumen_bronze", "name": "Lumen", "tier": "bronze", "image_url": "/static/logos/Lumen_Bronze.png"},
                {"id": "blayzo2_bronze", "name": "Blayzo.2", "tier": "bronze", "image_url": "/static/logos/blayzo_free_tier.png"},
                {"id": "crimson_bronze", "name": "Crimson", "tier": "bronze", "image_url": "/static/logos/Crimson_Free.png"},
                {"id": "violet_bronze", "name": "Violet", "tier": "bronze", "image_url": "/static/logos/Violet_Free.png"},
                
                # Silver companions (8)
                {"id": "gamerjay_silver", "name": "GamerJay.2", "tier": "silver", "image_url": "/static/logos/GamerJay_premium_companion.png"},
                {"id": "blayzo_silver", "name": "Blayzo.3", "tier": "silver", "image_url": "/static/logos/Blayzo_premium_companion.png"},
                {"id": "blayzica_silver", "name": "Blayzica.2", "tier": "silver", "image_url": "/static/logos/Blayzica_Pro.png"},
                {"id": "claude_silver", "name": "Claude.3", "tier": "silver", "image_url": "/static/logos/Claude_Growth.png"},
                {"id": "sky_silver", "name": "Sky", "tier": "silver", "image_url": "/static/logos/Sky_a_premium_companion.png"},
                {"id": "lumen_silver", "name": "Lumen.2", "tier": "silver", "image_url": "/static/logos/Lumen_Silver.png"},
                {"id": "rozia_silver", "name": "Rozia", "tier": "silver", "image_url": "/static/logos/Rozia_Silver.png"},
                {"id": "watchdog_silver", "name": "WatchDog", "tier": "silver", "image_url": "/static/logos/WatchDog_a_Premium_companion.png"},
                
                # Gold companions (8)
                {"id": "crimson_gold", "name": "Crimson.2", "tier": "gold", "image_url": "/static/logos/Crimson_a_Max_companion.png"},
                {"id": "violet_gold", "name": "Violet.2", "tier": "gold", "image_url": "/static/logos/Violet_a_Max_companion.png"},
                {"id": "claude_gold", "name": "Claude.2", "tier": "gold", "image_url": "/static/logos/Claude_Max.png"},
                {"id": "royal_gold", "name": "Royal", "tier": "gold", "image_url": "/static/logos/Royal_a_Max_companion.png"},
                {"id": "ven_blayzica_gold", "name": "Ven Blayzica", "tier": "gold", "image_url": "/static/logos/Ven_Blayzica_a_Max_companion.png"},
                {"id": "ven_sky_gold", "name": "Ven Sky", "tier": "gold", "image_url": "/static/logos/Ven_Sky_a_Max_companion.png"},
                {"id": "watchdog_gold", "name": "WatchDog.2", "tier": "gold", "image_url": "/static/logos/WatchDog_a_Max_Companion.png"},
                {"id": "dr_madjay_gold", "name": "Dr. MadJay", "tier": "gold", "image_url": "/static/logos/Dr. MadJay.png"},
                
                # Referral companions (5)
                {"id": "blayzike", "name": "Blayzike", "tier": "referral", "image_url": "/static/referral/blayzike.png", "min_referrals": 2},
                {"id": "blazelian", "name": "Blazelian", "tier": "referral", "image_url": "/static/referral/blazelian.png", "min_referrals": 4},
                {"id": "nyxara", "name": "Nyxara", "tier": "referral", "image_url": "/static/logos/Nyxara.png", "min_referrals": 6},
                {"id": "claude_referral", "name": "Claude Referral", "tier": "referral", "image_url": "/static/referral/claude_referral.png", "min_referrals": 8},
                {"id": "blayzo_referral", "name": "Blayzo Referral", "tier": "referral", "image_url": "/static/logos/Blayzo_Referral.png", "min_referrals": 10},
            ]
            
            # Simple limits based on tier
            limits = {
                'decoder': 3 if user_plan == 'bronze' else (15 if user_plan == 'silver' else 999),
                'fortune': 3 if user_plan == 'bronze' else (8 if user_plan == 'silver' else 999),
                'horoscope': 3 if user_plan == 'bronze' else (10 if user_plan == 'silver' else 999),
                'creative_writer': 3 if user_plan == 'bronze' else (20 if user_plan == 'silver' else 999)
            }
            
            # Proper tier-based access control
            access_info = {
                'user_plan': user_plan,
                'trial_active': session.get('trial_active', False),
                'unlock_state': {}
            }
            
            for comp in companions:
                comp_id = comp['id']
                comp_tier = comp['tier']
                
                # Bronze companions are always accessible
                if comp_tier == 'bronze':
                    access_info['unlock_state'][comp_id] = {'can_access': True, 'reason': 'unlocked'}
                # Silver companions require Silver or Gold tier
                elif comp_tier == 'silver':
                    has_access = user_plan in ['silver', 'gold']
                    access_info['unlock_state'][comp_id] = {'can_access': has_access, 'reason': 'tier_locked' if not has_access else 'unlocked'}
                # Gold companions require Gold tier
                elif comp_tier == 'gold':
                    has_access = user_plan == 'gold'
                    access_info['unlock_state'][comp_id] = {'can_access': has_access, 'reason': 'tier_locked' if not has_access else 'unlocked'}
                # Referral companions require referrals (always locked for now)
                elif comp_tier == 'referral':
                    access_info['unlock_state'][comp_id] = {'can_access': False, 'reason': 'referral_locked'}
            
            logger.info(f"✅ Companion selection loaded: user_plan={user_plan}, companions={len(companions)}")
            
            return render_template("companion_selection.html",
                                 companions=companions,
                                 access_info=access_info,
                                 tier=user_plan,
                                 tier_display=tier_display,
                                 limits=limits,
                                 user_plan=user_plan,
                                 trial_active=session.get('trial_active', False))
        
        except Exception as e:
            logger.error(f"❌ Error in companion selection: {e}")
            return render_template("error.html", error="Unable to load companion selection")
    """
    
    
    @app.route("/chat")
    def chat_default():
        """Default chat route - redirect to companion selection or last selected companion"""
        if not session.get('logged_in'):
            return redirect('/auth/login')
        
        # Check if user has a previously selected companion (session first, then database)
        selected_companion = session.get('selected_companion')
        
        # If not in session, try to load from database
        if not selected_companion and session.get('user_id'):
            try:
                from database_utils import get_database
                database = get_database()
                if database:
                    result = database.execute(
                        "SELECT selected_companion FROM users WHERE id = ?", 
                        (session.get('user_id'),)
                    ).fetchone()
                    if result and result[0]:
                        selected_companion = result[0]
                        session['selected_companion'] = selected_companion  # Restore to session
                        session.modified = True
                        logger.info(f"Restored companion from database: {selected_companion}")
            except Exception as db_error:
                logger.warning(f"⚠️ Could not load companion from database: {db_error}")
        
        if selected_companion:
            logger.info(f"Redirecting to previously selected companion: {selected_companion}")
            return redirect(f'/chat/{selected_companion}')
        else:
            logger.info("No companion selected, redirecting to companion selection")
            return redirect('/companion-selection')

    @app.route("/chat/<companion_id>")
    def companion_specific_chat(companion_id):
        """Chat with specific companion - from companions blueprint"""
        try:
            if not session.get('logged_in'):
                return redirect('/auth/login')
            
            # Set selected companion and persist it
            session['selected_companion'] = companion_id
            session.modified = True
            
            # Also update user database if needed (for persistence across sessions)
            try:
                from database_utils import get_database
                database = get_database()
                if database and session.get('user_id'):
                    database.execute(
                        "UPDATE users SET selected_companion = ? WHERE id = ?",
                        (companion_id, session.get('user_id'))
                    )
                    database.commit()
                    logger.info(f"✅ Saved companion selection to database: {companion_id}")
            except Exception as db_error:
                logger.warning(f"⚠️ Could not save companion to database: {db_error}")
            
            # Update new companion persistence system
            try:
                from display_name_helpers import set_companion_data
                from modules.companions.companion_data import get_companion_by_id
                companion = get_companion_by_id(companion_id)
                if companion and session.get('user_id'):
                    companion_data = {
                        'companion_id': companion_id,
                        'name': companion.get('display_name', companion_id),
                        'tier': companion.get('tier', 'bronze')
                    }
                    set_companion_data(session.get('user_id'), companion_data)
                    logger.info(f"✅ Updated new companion persistence system: {companion_id}")
            except Exception as e:
                logger.warning(f"⚠️ Could not update new companion system: {e}")
            
            # Find companion data - All 31 companions
            companions = [
                # Bronze companions (10)
                {"id": "gamerjay_bronze", "name": "GamerJay", "tier": "bronze", "image_url": "/static/logos/GamerJay_Free_companion.png", "greeting": "Hey there! I'm GamerJay. Ready to level up and explore some awesome features together?"},
                {"id": "blayzo_bronze", "name": "Blayzo", "tier": "bronze", "image_url": "/static/logos/Blayzo.png", "greeting": "What's up! I'm Blayzo. Let's vibe and see what cool stuff we can discover together!"},
                {"id": "blayzica_bronze", "name": "Blayzica", "tier": "bronze", "image_url": "/static/logos/Blayzica.png", "greeting": "Hello! I'm Blayzica. I'm here to help you explore and make the most of your SoulBridge experience!"},
                {"id": "claude_bronze", "name": "Claude", "tier": "bronze", "image_url": "/static/logos/Claude_Free.png", "greeting": "Greetings! I'm Claude. I'm excited to help you explore the world of artificial intelligence and beyond!"},
                {"id": "blayzia_bronze", "name": "Blayzia", "tier": "bronze", "image_url": "/static/logos/Blayzia.png", "greeting": "Hey! I'm Blayzia. Ready to dive into some amazing features and have fun together?"},
                {"id": "blayzion_bronze", "name": "Blayzion", "tier": "bronze", "image_url": "/static/logos/Blayzion.png", "greeting": "Yo! I'm Blayzion. Let's embark on this journey and unlock some cool features together!"},
                {"id": "lumen_bronze", "name": "Lumen", "tier": "bronze", "image_url": "/static/logos/Lumen_Bronze.png", "greeting": "Hello there! I'm Lumen. I'm here to brighten your SoulBridge experience and guide you through our features!"},
                {"id": "blayzo2_bronze", "name": "Blayzo.2", "tier": "bronze", "image_url": "/static/logos/blayzo_free_tier.png", "greeting": "Hey! I'm Blayzo.2. Ready to explore the next level of features together?"},
                {"id": "crimson_bronze", "name": "Crimson", "tier": "bronze", "image_url": "/static/logos/Crimson_Free.png", "greeting": "Hey! I'm Crimson. I bring passion and determination to help you tackle challenges head-on!"},
                {"id": "violet_bronze", "name": "Violet", "tier": "bronze", "image_url": "/static/logos/Violet_Free.png", "greeting": "Hello! I'm Violet. I see the creative beauty in every moment and I'm here to inspire your journey!"},
                
                # Silver companions (8)
                {"id": "sky_silver", "name": "Sky", "tier": "silver", "image_url": "/static/logos/Sky_a_premium_companion.png", "greeting": "Hello! I'm Sky. With enhanced features at your fingertips, let's soar to new heights together!"},
                {"id": "gamerjay_silver", "name": "GamerJay.2", "tier": "silver", "image_url": "/static/logos/GamerJay_premium_companion.png", "greeting": "What's up! I'm GamerJay.2. Time to unlock the next level of features and dominate together!"},
                {"id": "claude_silver", "name": "Claude.3", "tier": "silver", "image_url": "/static/logos/Claude_Growth.png", "greeting": "Welcome! I'm Claude.3. With expanded capabilities, I'm ready to help you achieve more!"},
                {"id": "blayzo_silver", "name": "Blayzo.3", "tier": "silver", "image_url": "/static/logos/Blayzo_premium_companion.png", "greeting": "Hey! I'm Blayzo.3. Ready to take your experience to the premium level?"},
                {"id": "blayzica_silver", "name": "Blayzica.2", "tier": "silver", "image_url": "/static/logos/Blayzica_Pro.png", "greeting": "Hi there! I'm Blayzica.2. Let's explore the enhanced features together!"},
                {"id": "watchdog_silver", "name": "WatchDog", "tier": "silver", "image_url": "/static/logos/WatchDog_a_Premium_companion.png", "greeting": "Greetings! I'm WatchDog. I'll keep watch over your premium experience and help you stay on track."},
                {"id": "rozia_silver", "name": "Rozia", "tier": "silver", "image_url": "/static/logos/Rozia_Silver.png", "greeting": "Hello! I'm Rozia. I bring elegance and sophistication to your SoulBridge journey."},
                {"id": "lumen_silver", "name": "Lumen.2", "tier": "silver", "image_url": "/static/logos/Lumen_Silver.png", "greeting": "Welcome! I'm Lumen.2. Let me illuminate your path to premium features and capabilities."},
                
                # Gold companions (8)
                {"id": "crimson_gold", "name": "Crimson.2", "tier": "gold", "image_url": "/static/logos/Crimson_a_Max_companion.png", "greeting": "Welcome, I'm Crimson.2. You have access to unlimited features and the full power of SoulBridge AI!"},
                {"id": "violet_gold", "name": "Violet.2", "tier": "gold", "image_url": "/static/logos/Violet_a_Max_companion.png", "greeting": "Greetings! I'm Violet.2. Together we'll explore unlimited possibilities and exclusive features!"},
                {"id": "claude_gold", "name": "Claude.2", "tier": "gold", "image_url": "/static/logos/Claude_Max.png", "greeting": "Hello! I'm Claude.2. With unlimited access to all features, let's achieve extraordinary things together!"},
                {"id": "royal_gold", "name": "Royal", "tier": "gold", "image_url": "/static/logos/Royal_a_Max_companion.png", "greeting": "Greetings! I'm Royal. Experience the pinnacle of AI companionship with unlimited possibilities."},
                {"id": "ven_blayzica_gold", "name": "Ven Blayzica", "tier": "gold", "image_url": "/static/logos/Ven_Blayzica_a_Max_companion.png", "greeting": "Hello! I'm Ven Blayzica. Let's venture into the ultimate SoulBridge experience together."},
                {"id": "ven_sky_gold", "name": "Ven Sky", "tier": "gold", "image_url": "/static/logos/Ven_Sky_a_Max_companion.png", "greeting": "Welcome! I'm Ven Sky. Together we'll soar beyond limits with unlimited premium access."},
                {"id": "watchdog_gold", "name": "WatchDog.2", "tier": "gold", "image_url": "/static/logos/WatchDog_a_Max_Companion.png", "greeting": "Greetings! I'm WatchDog.2. I'll safeguard your unlimited access and guide you through premium features."},
                {"id": "dr_madjay_gold", "name": "Dr. MadJay", "tier": "gold", "image_url": "/static/logos/Dr. MadJay.png", "greeting": "Greetings! I'm Dr. MadJay. Let's explore the cutting-edge possibilities of unlimited AI access."},
                
                # Referral companions (5)
                {"id": "blayzike", "name": "Blayzike", "tier": "silver", "image_url": "/static/referral/blayzike.png", "min_referrals": 2},
                {"id": "blazelian", "name": "Blazelian", "tier": "gold", "image_url": "/static/referral/blazelian.png", "min_referrals": 4},
                {"id": "nyxara", "name": "Nyxara", "tier": "silver", "image_url": "/static/logos/Nyxara.png", "min_referrals": 6},
                {"id": "claude_referral", "name": "Claude Referral", "tier": "gold", "image_url": "/static/referral/claude_referral.png", "min_referrals": 8},
                {"id": "blayzo_referral", "name": "Blayzo Referral", "tier": "gold", "image_url": "/static/logos/Blayzo_Referral.png", "min_referrals": 10},
            ]
            
            # Find the specific companion
            companion = next((c for c in companions if c['id'] == companion_id), None)
            if not companion:
                logger.warning(f"⚠️ Companion '{companion_id}' not found, using fallback")
                # Fallback companion data - but don't change the companion_id in session
                companion = {"id": companion_id, "name": companion_id.replace('_bronze', '').replace('_', ' ').title(), "tier": "bronze"}
            
            logger.info(f"✅ Loading chat for companion: {companion_id}")
            
            from flask import render_template
            return render_template('chat_bronze.html', 
                                 companion_info=companion,
                                 ai_character_name=companion.get('name', 'AI Assistant'),
                                 companion_avatar=companion.get('image_url', '/static/logos/New IntroLogo.png'),
                                 trial_active=session.get('trial_active', False))
                                 
        except Exception as e:
            logger.error(f"❌ Error in companion chat: {e}")
            return render_template("error.html", error="Unable to load chat page")
    
    # COMMUNITY ROUTES - Handled by community blueprint
    # Removed duplicate route - let blueprint handle /community
    
    # DASHBOARD ROUTE - Redirects to intro (main landing page)
    @app.route("/dashboard")
    def dashboard():
        """Dashboard redirect to intro page"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=intro')
        
        # Redirect to intro page which is the main landing after login
        return redirect('/intro')
    
    @app.route("/companions")
    def companions_page():
        """Companion selection page"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=companions')
        
        from flask import render_template
        return render_template('companions.html')
    
    # PROFILE ROUTES (from user_profile module blueprint)  
    @app.route("/profile")
    def profile():
        """User profile page - from user_profile blueprint"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=profile')
        
        from flask import render_template
        user_data = {
            'email': session.get('email'),
            'user_plan': session.get('user_plan', 'bronze'),
            'trial_active': session.get('trial_active', False)
        }
        return render_template('profile.html', user=user_data)
    
    # API ROUTES (from api module blueprint)
    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        """Chat API endpoint - from api blueprint"""
        if not session.get('logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        try:
            data = request.get_json()
            message = data.get('message', '').strip()
            companion_id = data.get('companion_id') or session.get('selected_companion')
            
            if not message:
                return jsonify({'success': False, 'error': 'Message required'}), 400
            
            if not companion_id:
                return jsonify({'success': False, 'error': 'No companion selected'}), 400
            
            # Find companion data for personality (same as chat route)
            companions = [
                # Bronze companions (10)
                {"id": "gamerjay_bronze", "name": "GamerJay", "tier": "bronze", "greeting": "Hey there! I'm GamerJay. Ready to level up and explore some awesome features together?"},
                {"id": "blayzo_bronze", "name": "Blayzo", "tier": "bronze", "greeting": "What's up! I'm Blayzo. Let's vibe and see what cool stuff we can discover together!"},
                {"id": "blayzica_bronze", "name": "Blayzica", "tier": "bronze", "greeting": "Hello! I'm Blayzica. I'm here to help you explore and make the most of your SoulBridge experience!"},
                {"id": "claude_bronze", "name": "Claude", "tier": "bronze", "greeting": "Greetings! I'm Claude. I'm excited to help you explore the world of artificial intelligence and beyond!"},
                {"id": "blayzia_bronze", "name": "Blayzia", "tier": "bronze", "greeting": "Hey! I'm Blayzia. Ready to dive into some amazing features and have fun together?"},
                {"id": "blayzion_bronze", "name": "Blayzion", "tier": "bronze", "greeting": "Yo! I'm Blayzion. Let's embark on this journey and unlock some cool features together!"},
                {"id": "lumen_bronze", "name": "Lumen", "tier": "bronze", "greeting": "Hello there! I'm Lumen. I'm here to brighten your SoulBridge experience and guide you through our features!"},
                {"id": "blayzo2_bronze", "name": "Blayzo.2", "tier": "bronze", "greeting": "Hey! I'm Blayzo.2. Ready to explore the next level of features together?"},
                {"id": "crimson_bronze", "name": "Crimson", "tier": "bronze", "greeting": "Hey! I'm Crimson. I bring passion and determination to help you tackle challenges head-on!"},
                {"id": "violet_bronze", "name": "Violet", "tier": "bronze", "greeting": "Hello! I'm Violet. I see the creative beauty in every moment and I'm here to inspire your journey!"},
                
                # Silver companions (8)
                {"id": "sky_silver", "name": "Sky", "tier": "silver", "greeting": "Hello! I'm Sky. With enhanced features at your fingertips, let's soar to new heights together!"},
                {"id": "gamerjay_silver", "name": "GamerJay.2", "tier": "silver", "greeting": "What's up! I'm GamerJay.2. Time to unlock the next level of features and dominate together!"},
                {"id": "claude_silver", "name": "Claude.3", "tier": "silver", "greeting": "Welcome! I'm Claude.3. With expanded capabilities, I'm ready to help you achieve more!"},
                {"id": "blayzo_silver", "name": "Blayzo.3", "tier": "silver", "greeting": "Hey! I'm Blayzo.3. Ready to take your experience to the premium level?"},
                {"id": "blayzica_silver", "name": "Blayzica.2", "tier": "silver", "greeting": "Hi there! I'm Blayzica.2. Let's explore the enhanced features together!"},
                {"id": "watchdog_silver", "name": "WatchDog", "tier": "silver", "greeting": "Greetings! I'm WatchDog. I'll keep watch over your premium experience and help you stay on track."},
                {"id": "rozia_silver", "name": "Rozia", "tier": "silver", "greeting": "Hello! I'm Rozia. I bring elegance and sophistication to your SoulBridge journey."},
                {"id": "lumen_silver", "name": "Lumen.2", "tier": "silver", "greeting": "Welcome! I'm Lumen.2. Let me illuminate your path to premium features and capabilities."},
                
                # Gold companions (8)
                {"id": "crimson_gold", "name": "Crimson.2", "tier": "gold", "greeting": "Welcome, I'm Crimson.2. You have access to unlimited features and the full power of SoulBridge AI!"},
                {"id": "violet_gold", "name": "Violet.2", "tier": "gold", "greeting": "Greetings! I'm Violet.2. Together we'll explore unlimited possibilities and exclusive features!"},
                {"id": "claude_gold", "name": "Claude.2", "tier": "gold", "greeting": "Hello! I'm Claude.2. With unlimited access to all features, let's achieve extraordinary things together!"},
                {"id": "royal_gold", "name": "Royal", "tier": "gold", "greeting": "Greetings! I'm Royal. Experience the pinnacle of AI companionship with unlimited possibilities."},
                {"id": "ven_blayzica_gold", "name": "Ven Blayzica", "tier": "gold", "greeting": "Hello! I'm Ven Blayzica. Let's venture into the ultimate SoulBridge experience together."},
                {"id": "ven_sky_gold", "name": "Ven Sky", "tier": "gold", "greeting": "Welcome! I'm Ven Sky. Together we'll soar beyond limits with unlimited premium access."},
                {"id": "watchdog_gold", "name": "WatchDog.2", "tier": "gold", "greeting": "Greetings! I'm WatchDog.2. I'll safeguard your unlimited access and guide you through premium features."},
                {"id": "dr_madjay_gold", "name": "Dr. MadJay", "tier": "gold", "greeting": "Greetings! I'm Dr. MadJay. Let's explore the cutting-edge possibilities of unlimited AI access."},
            ]
            
            companion = next((c for c in companions if c['id'] == companion_id), None)
            companion_name = companion['name'] if companion else companion_id.replace('_bronze', '').replace('_', ' ').title()
            
            # Use OpenAI API with new client
            from openai import OpenAI
            import os
            
            client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            if not os.environ.get('OPENAI_API_KEY'):
                return jsonify({'success': False, 'error': 'OpenAI API key not configured'}), 500
            
            try:
                # Determine model based on companion tier
                companion_tier = companion['tier'] if companion else 'bronze'
                if companion_tier == 'gold':
                    model = "gpt-5"  # GPT-5 for Gold tier (latest model)
                    max_tokens = 800   # Gold: 800 tokens for complete responses
                elif companion_tier == 'silver':
                    model = "gpt-4"  # GPT-4 for Silver tier  
                    max_tokens = 600   # Silver: 600 tokens for detailed responses
                else:
                    model = "gpt-3.5-turbo"  # GPT-3.5-turbo for Bronze tier
                    max_tokens = 400   # Bronze: 400 tokens for complete responses
                
                # Create personality-based system message
                system_message = f"You are {companion_name}, a helpful AI companion from SoulBridge AI. You have a friendly, supportive personality. Keep responses concise and helpful."
                
                # Debug logging
                logger.info(f"🤖 Using {model} for {companion_name} ({companion_tier} tier) - max_tokens: {max_tokens}")
                
                openai_response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                
                response = openai_response.choices[0].message.content.strip()
                
            except Exception as openai_error:
                logger.error(f"OpenAI API error: {openai_error}")
                response = f"Hello! I'm {companion_name}. I'm having trouble connecting to my AI brain right now, but I'm here to help! Could you try asking me again?"
            
            return jsonify({
                'success': True,
                'response': response,
                'companion_id': companion_id
            })
            
        except Exception as e:
            logger.error(f"Chat API error: {e}")
            return jsonify({'success': False, 'error': 'Chat processing failed'}), 500
    
    @app.route("/api/companions")
    def api_companions():
        """Companions API - Complete companion list with tier access"""
        if not session.get('logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Import the helper functions from API routes
        from modules.api.routes import get_all_companions, get_effective_plan
        
        # Get user's plan and effective access level
        user_plan = session.get('user_plan', 'bronze')
        effective_plan = get_effective_plan()  # This handles trial upgrades
        current_companion = session.get('selected_companion')
        referrals = int(session.get('referrals', 0))
        
        # Get all companions
        all_companions = get_all_companions()
        
        # Add access control logic to each companion
        companions_with_access = []
        for companion in all_companions:
            companion_tier = companion['tier']
            
            # Determine if user can access this companion
            can_access = False
            lock_reason = ""
            
            # Check if this is a referral companion (always show referral requirement)
            min_referrals = companion.get('min_referrals', 0)
            if min_referrals > 0:
                lock_reason = f"Requires {min_referrals} referrals"
                can_access = referrals >= min_referrals
            elif companion_tier == 'bronze':
                can_access = True
            elif companion_tier == 'silver':
                if effective_plan in ['silver', 'gold']:
                    can_access = True
                else:
                    lock_reason = "Requires Silver upgrade"
            elif companion_tier == 'gold':
                if effective_plan == 'gold':
                    can_access = True
                else:
                    lock_reason = "Requires Gold upgrade"
            
            # Mark if this is the current companion
            is_current = (current_companion == companion['id'])
            
            companion_data = {
                **companion,
                'can_access': can_access,
                'lock_reason': lock_reason,
                'is_current': is_current,
                'display_name': companion['name']
            }
            
            companions_with_access.append(companion_data)
        
        return jsonify({
            'success': True,
            'companions': companions_with_access,
            'user_plan': user_plan,
            'effective_plan': effective_plan
        })
    
    @app.route("/api/session/companion")
    def api_session_companion():
        """Get current selected companion from session"""
        if not session.get('logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        selected_companion = session.get('selected_companion')
        return jsonify({
            'success': True,
            'companion_id': selected_companion
        })
    
    # CREATIVE ROUTES (from creative module blueprint)
    @app.route("/creative")
    def creative():
        """Creative tools page - from creative blueprint"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=creative')
        
        from flask import render_template
        return render_template('creative.html')
    
    @app.route("/creative-writing")
    def creative_writing():
        """Creative writing page - alias for creative tools"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=creative-writing')
        
        from flask import render_template
        return render_template('creative.html')
    
    @app.route("/decoder")
    def decoder():
        """Decoder tool - from creative blueprint"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=decoder')
        
        from flask import render_template
        return render_template('decoder.html')
    
    # Fortune route now handled by modules.fortune blueprint
    
    @app.route("/horoscope")
    def horoscope():
        """Enhanced Horoscope tool with interpretations and compatibility"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=horoscope')
        
        from flask import render_template
        
        # Check if user has ad-free subscription
        user_id = session.get('user_id')
        ad_free = False
        if user_id:
            try:
                from modules.user_profile.profile_service import ProfileService
                profile_service = ProfileService()
                user_profile_result = profile_service.get_user_profile(user_id)
                user_profile = user_profile_result.get('user') if user_profile_result.get('success') else None
                ad_free = user_profile.get('ad_free', False) if user_profile else False
            except Exception as e:
                logger.error(f"Error checking ad-free status: {e}")
                ad_free = False
        
        return render_template('horoscope.html', 
                             ad_free=ad_free,
                             user_session=session)
    
    @app.route("/soul-riddle")
    def soul_riddle():
        """Soul Riddle - Interactive brain teaser mini game"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=soul-riddle')
        
        from flask import render_template
        
        # Check if user has ad-free subscription
        user_id = session.get('user_id')
        ad_free = False
        if user_id:
            try:
                from modules.user_profile.profile_service import ProfileService
                profile_service = ProfileService()
                user_profile_result = profile_service.get_user_profile(user_id)
                user_profile = user_profile_result.get('user') if user_profile_result.get('success') else None
                ad_free = user_profile.get('ad_free', False) if user_profile else False
            except Exception as e:
                logger.error(f"Error checking ad-free status: {e}")
                ad_free = False
        
        return render_template('soul_riddle.html', 
                             ad_free=ad_free,
                             user_session=session)
    
    # LIBRARY ROUTES (handled by library module blueprint)
    # @app.route("/library") - DISABLED: Using blueprint instead
    
    # MEDITATION ROUTES (from meditations module blueprint)
    @app.route("/meditations")
    def meditations():
        """Meditations page - from meditations blueprint"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=meditations')
        
        from flask import render_template
        return render_template('meditations.html')
    
    @app.route("/emotional-meditations")
    def emotional_meditations():
        """Emotional meditations - from meditations blueprint"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=emotional-meditations')
        
        from flask import render_template
        return render_template('emotional_meditations.html')
    
    # VOICE ROUTES (from voice module blueprint)
    @app.route("/voice-journaling")
    def voice_journaling():
        """Voice journaling page - from voice blueprint"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=voice-journaling')
        
        from flask import render_template
        return render_template('voice_journaling.html')
    
    @app.route("/voice-chat")
    def voice_chat():
        """Voice chat page - from voice blueprint"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=voice-chat')
        
        from flask import render_template
        return render_template('voice_chat.html')
    
    # STUDIO ROUTES (from studio module blueprint)
    @app.route("/mini-studio")
    def mini_studio():
        """Mini Studio page - from studio blueprint"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=mini-studio')
        
        user_plan = session.get('user_plan', 'bronze')
        if user_plan != 'gold':
            return redirect('/tiers?error=Gold tier required for Mini Studio')
        
        from flask import render_template
        return render_template('mini_studio.html')
    
    # RELATIONSHIP ROUTES (from relationship_profiles module blueprint)
    @app.route("/relationship-profiles")
    def relationship_profiles():
        """Relationship profiles page - from relationship_profiles blueprint"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=relationship-profiles')
        
        user_plan = session.get('user_plan', 'bronze')
        if user_plan == 'bronze':
            return redirect('/tiers?error=Silver or Gold tier required for Relationship Profiles')
        
        from flask import render_template
        return render_template('relationship_profiles.html')
    
    # AI IMAGES ROUTES (from ai_images module blueprint)
    @app.route("/ai-image-generation")
    def ai_image_generation():
        """AI image generation page - from ai_images blueprint"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=ai-image-generation')
        
        user_plan = session.get('user_plan', 'bronze')
        if user_plan == 'bronze':
            return redirect('/tiers?error=Silver or Gold tier required for AI Images')
        
        from flask import render_template
        return render_template('ai_image_generation.html')
    
    # CREATIVE WRITING ROUTES (individual tools)
    @app.route("/ai-lyric-writer")
    def ai_lyric_writer():
        """AI Lyric Writer tool"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=ai-lyric-writer')
        
        from flask import render_template
        return render_template('ai_lyric_writer.html')
    
    @app.route("/poem-generator")
    def poem_generator():
        """Poem Generator tool"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=poem-generator')
        
        from flask import render_template
        return render_template('poem_generator.html')
    
    @app.route("/story-generator") 
    def story_generator():
        """Story Generator tool"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=story-generator')
        
        from flask import render_template
        return render_template('story_generator.html')
    
    @app.route("/writing-suite")
    def writing_suite():
        """Writing Suite tool (scripts, essays, letters)"""
        if not session.get('logged_in'):
            return redirect('/auth/login?return_to=writing-suite')
        
        from flask import render_template
        return render_template('writing_suite.html')
    
    # HEALTH ROUTES (from health module blueprint)
    @app.route("/health")
    def health():
        """Health check - from health blueprint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'service': 'soulbridge-ai'
        })
    
    # UTILITY ROUTES
    @app.route("/whoami")
    def whoami():
        """Session info - utility route"""
        return jsonify({
            'logged_in': session.get('logged_in'),
            'email': session.get('email'),
            'user_id': session.get('user_id'),
            'user_plan': session.get('user_plan'),
            'session_keys': list(session.keys())
        })

    # Production startup diagnostics
    port = os.getenv("PORT", "5000")
    logger.info("🚀 SoulBridge AI application created successfully")
    logger.info(f"🌐 Server will bind to 0.0.0.0:{port}")
    logger.info("🏥 Health endpoints: /health, /healthz, /readyz (no auth required)")
    logger.info(f"📚 API Documentation: {'enabled' if os.getenv('DOCS_ENABLED', '1') == '1' else 'disabled'}")
    logger.info(f"🔐 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    return app

def register_blueprints(app, database_manager=None):
    """Register all extracted module blueprints"""
    import traceback  # Ensure traceback is available within function scope
    try:
        # Health checks FIRST - critical for Railway deployment probes
        # Must be accessible without authentication for health monitoring
        from health import health_bp
        app.register_blueprint(health_bp)
        logger.info("✅ Railway health checks registered FIRST (/health, /healthz, /readyz)")
        
        # Core system routes
        from modules.core import core_bp
        app.register_blueprint(core_bp)
        logger.info("✅ Core routes registered")
        
        # Clean display name system - ONE WRITER, ONE READER
        from clean_display_name_routes import clean_display_bp
        app.register_blueprint(clean_display_bp)
        logger.info("✅ Clean display name system registered")
        
        # Authentication system
        from modules.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        logger.info("✅ Auth system registered")
        
        # Main chat system - temporarily disabled to use working app.py routes
        # from modules.chat import chat_bp
        # app.register_blueprint(chat_bp)
        # logger.info("✅ Chat system registered")
        
        # Companion system
        from modules.companions import companions_bp
        app.register_blueprint(companions_bp)  # Re-enabled to use modular skin system
        logger.info("✅ Companions system registered")
        
        # Voice system
        from modules.voice import voice_bp
        app.register_blueprint(voice_bp)
        logger.info("✅ Voice system registered")
        
        # Creative features
        from modules.creative import creative_bp
        app.register_blueprint(creative_bp)
        logger.info("✅ Creative system registered")
        
        # Community System (CRITICAL FIX) - Using modular version in register_blueprints()
        # Legacy community_system.py registration disabled to avoid blueprint name conflict
        logger.info("✅ Community system registered via modular blueprints")
        
        # AI Lyric Writer
        try:
            from routes.ai_lyric_writer import ai_lyric_writer_bp
            app.register_blueprint(ai_lyric_writer_bp)
            logger.info("✅ AI Lyric Writer system registered")
        except Exception as e:
            logger.warning(f"⚠️  AI Lyric Writer system failed to register: {e}")

        # Poem Generator
        try:
            from routes.poem_generator import poem_generator_bp
            app.register_blueprint(poem_generator_bp)
            logger.info("✅ Poem Generator system registered")
        except Exception as e:
            logger.warning(f"⚠️  Poem Generator system failed to register: {e}")

        # Story Generator
        try:
            from routes.story_generator import story_generator_bp
            app.register_blueprint(story_generator_bp)
            logger.info("✅ Story Generator system registered")
        except Exception as e:
            logger.warning(f"⚠️  Story Generator system failed to register: {e}")

        # Writing Suite
        try:
            from routes.writing_suite import writing_suite_bp
            app.register_blueprint(writing_suite_bp)
            logger.info("✅ Writing Suite system registered")
        except Exception as e:
            logger.warning(f"⚠️  Writing Suite system failed to register: {e}")

        # Export System
        try:
            from routes.export_routes import export_bp
            app.register_blueprint(export_bp)
            logger.info("✅ Export system registered")
        except Exception as e:
            logger.warning(f"⚠️  Export system failed to register: {e}")

        # Health Monitoring
        try:
            from routes.health_endpoints import health_bp
            app.register_blueprint(health_bp)
            logger.info("✅ Health monitoring endpoints registered")
        except Exception as e:
            logger.warning(f"⚠️  Health monitoring failed to register: {e}")

        # Vector Lyric System
        try:
            from routes.vector_lyric_routes import vector_lyric_bp
            app.register_blueprint(vector_lyric_bp)
            logger.info("✅ Vector lyric system registered")
        except Exception as e:
            logger.warning(f"⚠️  Vector lyric system failed to register: {e}")

        # Consent Management
        try:
            from routes.consent_management import consent_bp as consent_mgmt_bp
            app.register_blueprint(consent_mgmt_bp)
            logger.info("✅ Consent management system registered")
        except Exception as e:
            logger.warning(f"⚠️  Consent management system failed to register: {e}")

        # Training Consent System (Forward-Only)
        try:
            from consent import consent_bp
            app.register_blueprint(consent_bp, name='training_consent')
            logger.info("✅ Training consent system registered")
        except Exception as e:
            logger.warning(f"⚠️  Training consent system failed to register: {e}")
        
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
        
        # Horoscope system
        try:
            from routes.horoscope import bp as horoscope_bp
            app.register_blueprint(horoscope_bp)
            logger.info("✅ Horoscope system registered")
        except Exception as horoscope_error:
            logger.error(f"❌ Horoscope system registration failed: {horoscope_error}")
            import traceback
            logger.error(f"Horoscope error details: {traceback.format_exc()}")
        
        # Enhanced Fortune system
        from modules.fortune import routes as fortune_routes
        app.register_blueprint(fortune_routes.fortune_bp)
        logger.info("✅ Enhanced Fortune system registered")
        
        # Library management
        from modules.library import library_bp
        app.register_blueprint(library_bp)
        logger.info("✅ Library system registered")
        
        # Community system
        from modules.community import community_bp
        from modules.community.routes import init_community_services
        app.register_blueprint(community_bp)
        
        # CRITICAL: Initialize community services with database connection
        from database_utils import get_database
        openai_client = None
        try:
            import openai
            openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        except:
            pass
        
        init_community_services(database=get_database(), openai_client=openai_client)
        logger.info("✅ Community services initialized with database")
        logger.info("✅ Community system registered")
        
        # Payment system
        from modules.payments import payments_bp
        app.register_blueprint(payments_bp)
        logger.info("✅ Payment system registered")
        
        # Admin system
        from modules.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        logger.info("✅ Admin system registered")
        
        # Database fix route for emergency schema fixes
        from routes.database_fix_route import db_fix_bp
        app.register_blueprint(db_fix_bp)
        logger.info("✅ Database fix route registered")
        
        # Health and monitoring (now handled by Railway-compatible health.py at top)
        # from modules.health import health_bp  # Removed to avoid duplicate registration
        # app.register_blueprint(health_bp)     # Railway health endpoints registered first
        logger.info("✅ Health system already registered (Railway-compatible)")
        
        # Legal/compliance
        from modules.legal import legal_bp
        app.register_blueprint(legal_bp)
        logger.info("✅ Legal system registered")
        
        # Notifications/email
        from modules.notifications import notifications_bp
        app.register_blueprint(notifications_bp)
        logger.info("✅ Notifications system registered")
        
        # Referrals system
        from modules.referrals import referrals_bp
        app.register_blueprint(referrals_bp)
        logger.info("✅ Referrals system registered")
        
        # Consolidated API endpoints
        from modules.api import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
        logger.info("✅ Consolidated API registered")
        
        # V1 API system (new RESTful API)
        from v1_api import v1_api
        app.register_blueprint(v1_api)
        logger.info("✅ V1 API system registered")
        
        # Mini Studio (if available)
        try:
            from modules.studio import studio_bp
            app.register_blueprint(studio_bp)
            logger.info("✅ Mini Studio registered")
        except ImportError:
            logger.info("⚠️ Mini Studio not available")
            
        # Beat Wizard system
        try:
            from modules.beat.describe_infer import beat_bp
            app.register_blueprint(beat_bp, url_prefix='/beat')
            logger.info("✅ Beat Wizard system registered")
        except ImportError as beat_error:
            logger.error(f"⚠️ Beat Wizard not available: {beat_error}")
        
        # Beat Brief Strict system (no lyric echo)
        try:
            from modules.beat.beat_brief_strict import brief_strict_bp
            app.register_blueprint(brief_strict_bp)
            logger.info("✅ Beat Brief Strict system registered")
        except ImportError as brief_error:
            logger.error(f"⚠️ Beat Brief Strict not available: {brief_error}")
        
        # Import Lyrics Analyzer
        try:
            logger.info("IMPORTING Lyrics Analyzer: module=modules.beat.lyrics_analyzer, attr=lyrics_analyzer_bp")
            from modules.beat.lyrics_analyzer import lyrics_analyzer_bp
            app.register_blueprint(lyrics_analyzer_bp)
            logger.info("SUCCESS: Lyrics Analyzer registered - URL prefix: /api/beat")
        except Exception as e:
            logger.error("FAILED importing Lyrics Analyzer: %s", str(e))
            logger.error("Full traceback:\n%s", traceback.format_exc())

        # Import CPU Beat Studio
        try:
            logger.info("IMPORTING CPU Beat Studio: module=modules.lyrics_workshop.lyrics_workshop_bp, attr=lyrics_workshop_bp")
            from modules.lyrics_workshop.lyrics_workshop_bp import lyrics_workshop_bp
            app.register_blueprint(lyrics_workshop_bp)
            logger.info("SUCCESS: CPU Beat Studio registered - URL prefix: /api/beat")
        except Exception as e:
            logger.error("FAILED importing CPU Beat Studio: %s", str(e))
            logger.error("Full traceback:\n%s", traceback.format_exc())
        
        # Route dumper helper
        def _dump_routes(app):
            app.logger.info("==== ROUTE MAP BEGIN ====")
            for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
                methods = ",".join(sorted(m for m in rule.methods if m not in ("HEAD","OPTIONS")))
                app.logger.info("ROUTE %-6s %-35s endpoint=%s", methods, rule.rule, rule.endpoint)
            app.logger.info("==== ROUTE MAP END ====")
        
        
        
        # API Documentation (Swagger UI) - environment controlled
        # Default to enabled in development, disabled in production
        is_prod = os.environ.get("ENVIRONMENT") == "production" or bool(os.environ.get("RAILWAY_PROJECT_ID"))
        docs_default = "0" if is_prod else "1"
        
        if os.getenv("DOCS_ENABLED", docs_default) == "1":
            try:
                from docs import docs_bp
                app.register_blueprint(docs_bp)
                logger.info("✅ API documentation enabled at /docs (OpenAPI at /openapi.yaml)")
            except Exception as e:
                logger.error(f"Failed to register docs blueprint: {e}")
        else:
            logger.info("📚 API documentation disabled (DOCS_ENABLED=0)")
        
        logger.info("🎯 All module blueprints registered successfully")
        
        # Dump all registered routes for debugging (behind env toggle)
        if os.getenv("DUMP_ROUTES") == "1":
            _dump_routes(app)
        
    except Exception as e:
        logger.error(f"❌ Blueprint registration failed: {e}")
        raise

# Mark register_blueprints as defined to prevent redefinition
_REGISTER_BLUEPRINTS_DEFINED = True

def initialize_systems(app):
    """Initialize all extracted systems with their dependencies"""
    try:
        # Initialize database manager
        from database_utils import get_database
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
        
        # Initialize profile system
        logger.info("🔧 About to initialize profile system...")
        from modules.user_profile.routes import init_profile_routes
        init_profile_routes(app, database_manager)
        logger.info("🔧 Profile system initialization completed")
        
        # Initialize meditation system
        from modules.meditations.routes import init_meditation_services
        init_meditation_services(database_manager, openai_client)
        
        # Initialize relationship profiles
        from modules.relationship_profiles.routes import init_relationship_routes
        # Get credits manager if available
        try:
            from modules.credits import get_credits_manager
            credits_manager = get_credits_manager()
        except:
            credits_manager = None
        init_relationship_routes(app, database_manager, credits_manager, openai_client)
        
        # Initialize AI images system
        from modules.ai_images.routes import init_ai_images_routes
        init_ai_images_routes(app, openai_client, credits_manager, database_manager)
        
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



def setup_v1_compatibility_routes(app):
    """Setup v1 API compatibility routes"""
    try:
        from modules.auth.session_manager import requires_login, get_user_id
        from flask import session, jsonify
        
        @app.route('/v1/entitlements')
        @requires_login
        def v1_entitlements():
            """V1 compatibility endpoint for entitlements"""
            try:
                user_id = get_user_id()
                user_plan = session.get('user_plan', 'bronze')
                trial_active = session.get('trial_active', False)
                trial_expires_at = session.get('trial_expires_at')
                
                return jsonify({
                    "logged_in": True,
                    "user_id": user_id,
                    "user_plan": user_plan,
                    "tier": user_plan,
                    "trial_active": trial_active,
                    "trial_expires_at": trial_expires_at
                })
                
            except Exception as e:
                logger.error(f"Error in v1 entitlements: {e}")
                return jsonify({"logged_in": False, "error": str(e)}), 500
        
        logger.info("✅ V1 compatibility routes configured")
        
    except Exception as e:
        logger.error(f"❌ V1 routes setup failed: {e}")

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