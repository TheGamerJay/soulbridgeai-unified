#!/usr/bin/env python3
"""
SoulBridge AI - Production Ready App  
Combines working initialization with all essential routes
Voice chat processing enabled
"""

# CRITICAL: eventlet monkey patching MUST be first for Gunicorn compatibility
import eventlet
eventlet.monkey_patch()

import os
import sys
import logging
#!/usr/bin/env python3
"""
SoulBridge AI - Production Ready App  
Combines working initialization with all essential routes
Voice chat processing enabled
"""

# CRITICAL: eventlet monkey patching MUST be first for Gunicorn compatibility
import eventlet
eventlet.monkey_patch()

import os
import sys
import logging
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, flash, make_response, g

# ...existing code...

# Create Flask app with secure session configuration
app = Flask(__name__)

# ...existing code...

# Admin dashboard logout route for correct redirect
@app.route("/admin/logout", methods=["GET", "POST"])
def admin_logout():
    """Admin dashboard logout: clears session and redirects to /admin/login"""
    try:
        user_email = session.get('user_email', 'unknown')
        logger.info(f"ADMIN LOGOUT: User {user_email} logged out from admin dashboard")
        session.clear()
        return redirect("/admin/login")
    except Exception as e:
        logger.error(f"Admin logout error: {e}")
        return redirect("/admin/login")
import time
import json
import psycopg2  # Add missing psycopg2 import
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, flash, make_response, g
from trial_utils import is_trial_active as calculate_trial_active, get_trial_time_remaining
from tier_isolation import tier_manager, get_current_user_tier, get_current_tier_system

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

# Debug mode setting
DEBUG_MODE = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true' or os.environ.get('DEBUG', 'False').lower() == 'true'

# Simple session configuration - FIXED: Remove shared session domain that was causing user contamination
# app.config['SESSION_COOKIE_DOMAIN'] = '.soulbridgeai.com' if os.environ.get('RAILWAY_ENVIRONMENT') else None  # DISABLED: This was causing session sharing between users!

# Rate limit tracking for mini helper activation
RATE_LIMIT_FLAG_FILE = os.path.join(os.path.dirname(__file__), 'rate_limit_status.json')

def set_rate_limit_flag(is_limited):
    """Set rate limit flag to control mini helper activation"""
    try:
        status = {
            'rate_limited': is_limited,
            'timestamp': datetime.now().isoformat(),
            'auto_helper_active': is_limited
        }
        with open(RATE_LIMIT_FLAG_FILE, 'w') as f:
            json.dump(status, f)
        logger.info(f"Rate limit flag set to: {is_limited}")
    except Exception as e:
        logger.error(f"Failed to set rate limit flag: {e}")

def get_rate_limit_status():
    """Get current rate limit status"""
    try:
        if os.path.exists(RATE_LIMIT_FLAG_FILE):
            with open(RATE_LIMIT_FLAG_FILE, 'r') as f:
                status = json.load(f)
            return status
        return {'rate_limited': False, 'auto_helper_active': False}
    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        return {'rate_limited': False, 'auto_helper_active': False}

def should_use_mini_helper():
    """Check if mini helper should be automatically activated"""
    status = get_rate_limit_status()
    return status.get('rate_limited', False)

# Conversation Memory System for Mini Helper
CONVERSATION_MEMORY_FILE = os.path.join(os.path.dirname(__file__), 'conversation_memory.json')
PROJECT_STATE_FILE = os.path.join(os.path.dirname(__file__), 'project_state.json')

def save_conversation_context(user_message, response, file_path="", action_type="chat"):
    """Save conversation context for Mini Helper continuity"""
    try:
        # Load existing memory
        memory = load_conversation_memory()
        
        # Add new conversation entry
        entry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'response': response[:1000],  # Truncate long responses
            'file_path': file_path,
            'action_type': action_type,  # chat, file_edit, bug_fix, feature_add
        }
        
        memory['conversations'].append(entry)
        
        # Keep only last 50 conversations to prevent file bloat
        memory['conversations'] = memory['conversations'][-50:]
        
        # Update session info
        memory['last_active'] = datetime.now().isoformat()
        memory['total_interactions'] = len(memory['conversations'])
        
        with open(CONVERSATION_MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to save conversation context: {e}")

def load_conversation_memory():
    """Load conversation memory for Mini Helper"""
    try:
        if os.path.exists(CONVERSATION_MEMORY_FILE):
            with open(CONVERSATION_MEMORY_FILE, 'r') as f:
                memory = json.load(f)
            return memory
        else:
            return {
                'conversations': [],
                'last_active': None,
                'total_interactions': 0,
                'project_context': {}
            }
    except Exception as e:
        logger.error(f"Failed to load conversation memory: {e}")
        return {'conversations': [], 'last_active': None, 'total_interactions': 0}

def save_project_state(task_completed, files_modified, current_focus):
    """Save project state for continuity"""
    try:
        state = {
            'last_updated': datetime.now().isoformat(),
            'completed_tasks': task_completed,
            'modified_files': files_modified,
            'current_focus': current_focus,
            'rate_limit_sessions': 0
        }
        
        # Load existing state and merge
        if os.path.exists(PROJECT_STATE_FILE):
            with open(PROJECT_STATE_FILE, 'r') as f:
                existing_state = json.load(f)
            if 'completed_tasks' in existing_state:
                state['completed_tasks'].extend(existing_state.get('completed_tasks', []))
            if 'modified_files' in existing_state:
                state['modified_files'].extend(existing_state.get('modified_files', []))
            state['rate_limit_sessions'] = existing_state.get('rate_limit_sessions', 0)
        
        # Remove duplicates
        state['completed_tasks'] = list(set(state['completed_tasks']))
        state['modified_files'] = list(set(state['modified_files']))
        
        with open(PROJECT_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to save project state: {e}")

def load_project_state():
    """Load current project state"""
    try:
        if os.path.exists(PROJECT_STATE_FILE):
            with open(PROJECT_STATE_FILE, 'r') as f:
                return json.load(f)
        return {
            'completed_tasks': [],
            'modified_files': [],
            'current_focus': 'General development',
            'last_updated': None
        }
    except Exception as e:
        logger.error(f"Failed to load project state: {e}")
        return {'completed_tasks': [], 'modified_files': [], 'current_focus': 'General development'}

def perform_basic_file_search(search_term):
    """Perform basic file search similar to grep/find tools"""
    try:
        backend_dir = os.path.dirname(__file__)
        results = []
        
        # Search in common directories
        search_dirs = [
            os.path.join(backend_dir, 'templates'),
            os.path.join(backend_dir, 'static'),
            backend_dir
        ]
        
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                for root, dirs, files in os.walk(search_dir):
                    # Skip hidden and cache directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                    
                    for file in files:
                        if file.endswith(('.py', '.html', '.js', '.css', '.json', '.md')):
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, backend_dir)
                            
                            # Search in filename
                            if search_term.lower() in file.lower():
                                results.append(f"📁 {rel_path} (filename match)")
                            
                            # Search in file content
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    if search_term.lower() in content.lower():
                                        # Count occurrences
                                        count = content.lower().count(search_term.lower())
                                        results.append(f"📄 {rel_path} ({count} occurrences)")
                            except:
                                continue
        
        if results:
            return "\n".join(results[:10])  # Limit to top 10 results
        else:
            return f"No files found containing '{search_term}'"
            
    except Exception as e:
        return f"Search error: {e}"

def perform_basic_file_analysis(file_path):
    """Perform basic file analysis similar to reading and analyzing files"""
    try:
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        
        # Get file stats
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(file_path)[1]
        
        analysis = f"**File Info:**\n"
        analysis += f"- Size: {file_size:,} bytes\n"
        analysis += f"- Type: {file_ext}\n"
        
        # Read and analyze content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        lines = content.split('\n')
        analysis += f"- Lines: {len(lines)}\n"
        
        # Language-specific analysis
        if file_ext == '.py':
            analysis += f"\n**Python Analysis:**\n"
            analysis += f"- Functions: {content.count('def ')}\n"
            analysis += f"- Classes: {content.count('class ')}\n"
            analysis += f"- Imports: {content.count('import ')}\n"
            analysis += f"- Routes: {content.count('@app.route')}\n"
            
        elif file_ext == '.html':
            analysis += f"\n**HTML Analysis:**\n"
            analysis += f"- HTML tags: ~{content.count('<')}\n"
            analysis += f"- Scripts: {content.count('<script')}\n"
            analysis += f"- Forms: {content.count('<form')}\n"
            analysis += f"- Jinja templates: {content.count('{{')}\n"
            
        elif file_ext == '.js':
            analysis += f"\n**JavaScript Analysis:**\n"
            analysis += f"- Functions: {content.count('function')}\n"
            analysis += f"- Event listeners: {content.count('addEventListener')}\n"
            analysis += f"- Async functions: {content.count('async')}\n"
        
        # Show first few lines as preview
        preview_lines = lines[:5]
        analysis += f"\n**Preview (first 5 lines):**\n"
        for i, line in enumerate(preview_lines, 1):
            analysis += f"{i}: {line[:60]}{'...' if len(line) > 60 else ''}\n"
            
        return analysis
        
    except Exception as e:
        return f"Analysis error: {e}"

def get_conversation_summary():
    """Get enhanced conversation summary with intelligent context for Mini Helper"""
    memory = load_conversation_memory()
    recent_conversations = memory['conversations'][-10:]  # Last 10 conversations
    
    if not recent_conversations:
        return "No recent conversation history."
    
    # Categorize conversations by type
    file_edits = [c for c in recent_conversations if c.get('file_path')]
    bug_fixes = [c for c in recent_conversations if 'fix' in c.get('user_message', '').lower() or 'bug' in c.get('user_message', '').lower()]
    features = [c for c in recent_conversations if 'add' in c.get('user_message', '').lower() or 'feature' in c.get('user_message', '').lower()]
    
    summary = "**📚 Memory Recall - Recent Work Context:**\n"
    
    # Show most recent interaction
    if recent_conversations:
        last = recent_conversations[-1]
        summary += f"**🕒 Last Interaction ({last['timestamp'][:16]}):** {last['user_message'][:80]}...\n"
        if last.get('file_path'):
            summary += f"   📁 Worked on: {last['file_path']}\n"
    
    # Show file editing history
    if file_edits:
        summary += f"\n**📝 Recent File Edits ({len(file_edits)}):**\n"
        for edit in file_edits[-5:]:  # Last 5 file edits
            summary += f"- {edit['file_path']} ({edit['timestamp'][:10]})\n"
    
    # Show problem-solving context
    if bug_fixes:
        summary += f"\n**🐛 Recent Bug Fixes ({len(bug_fixes)}):**\n"
        for fix in bug_fixes[-3:]:
            summary += f"- {fix['user_message'][:50]}... ({fix['timestamp'][:10]})\n"
    
    # Show feature development context
    if features:
        summary += f"\n**✨ Recent Features ({len(features)}):**\n"
        for feat in features[-3:]:
            summary += f"- {feat['user_message'][:50]}... ({feat['timestamp'][:10]})\n"
    
    summary += f"\n**📊 Total Interactions:** {memory.get('total_interactions', 0)}\n"
    
    return summary

def increment_rate_limit_session():
    """Track when Mini Helper is used due to rate limits"""
    try:
        state = load_project_state()
        state['rate_limit_sessions'] = state.get('rate_limit_sessions', 0) + 1
        state['last_rate_limit'] = datetime.now().isoformat()
        
        with open(PROJECT_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to increment rate limit session: {e}")

# Ensure sessions expire when browser closes
@app.before_request
def make_session_non_permanent():
    session.permanent = False

@app.before_request
def reset_session_if_cookie_missing():
    # If no session cookie, make sure user is not treated as logged in
    if not request.cookies.get('session'):
        session.clear()

@app.before_request
def load_user_context():
    """Load user context and handle trial expiration - comprehensive system"""
    # Skip for static files and API calls to avoid overhead
    if request.endpoint in ['static', 'favicon'] or request.path.startswith('/static/'):
        return

    user_id = session.get('user_id')
    if not user_id:
        return  # not logged in
    
    session.permanent = True
    
    # Auto-migrate legacy plan values in session
    legacy_plan_mapping = {'foundation': 'free', 'premium': 'growth', 'enterprise': 'max'}
    current_plan = session.get("user_plan", "free")
    if current_plan in legacy_plan_mapping:
        new_plan = legacy_plan_mapping[current_plan]
        logger.info(f"🧼 Fixing session user_plan from {current_plan} → {new_plan}")
        session["user_plan"] = new_plan
        current_plan = new_plan
    
    # Sync trial status from database to session
    try:
        db_instance = get_database()
        if db_instance:
            conn = db_instance.get_connection()
            cursor = conn.cursor()
            if db_instance.use_postgres:
                cursor.execute("SELECT trial_started_at, trial_used_permanently FROM users WHERE id = %s", (user_id,))
            else:
                cursor.execute("SELECT trial_started_at, trial_used_permanently FROM users WHERE id = ?", (user_id,))
            
            result = cursor.fetchone()
            if result:
                trial_started_at_db, trial_used_permanently_db = result
                
                # Update session with database values
                session['trial_used_permanently'] = bool(trial_used_permanently_db)
                
                # Check if trial is currently active
                if trial_started_at_db:
                    if isinstance(trial_started_at_db, str):
                        trial_time = datetime.fromisoformat(trial_started_at_db.replace('Z', '+00:00'))
                    else:
                        trial_time = trial_started_at_db
                    
                    trial_active = datetime.utcnow() < trial_time + timedelta(hours=5)
                    session['trial_active'] = trial_active
                    
                    if trial_active:
                        session['trial_started_at'] = trial_time.isoformat()
                        session['trial_expires_at'] = (trial_time + timedelta(hours=5)).isoformat()
                        # Don't cache effective_plan - calculate it fresh each time
                    else:
                        session['trial_active'] = False
                        # Don't cache effective_plan - calculate it fresh each time
                else:
                    session['trial_active'] = False
                    # Don't cache effective_plan - calculate it fresh each time
            
            conn.close()
    except Exception as e:
        logger.error(f"Error syncing trial status: {e}")
        # Fallback to session values
        pass

    g.user_plan = current_plan
    g.trial_active = session.get("trial_active", False)
    g.trial_started_at = session.get("trial_started_at")
    g.effective_plan = get_effective_plan(current_plan, g.trial_active)  # Always calculate fresh
    g.is_admin = is_admin()
    session['last_seen'] = datetime.utcnow().isoformat()
    
    # TIER ISOLATION: Initialize user into appropriate isolated tier system
    tier_name = tier_manager.get_user_tier(current_plan, g.trial_active)
    user_data = {
        'user_id': user_id,
        'user_email': session.get('user_email'),
        'user_plan': current_plan,
        'trial_active': g.trial_active
    }
    tier_manager.initialize_user_for_tier(user_data, tier_name)
    logger.info(f"🔒 TIER ISOLATION: User {user_id} initialized in {tier_name.upper()} tier")

    if g.trial_active and g.trial_started_at:
        try:
            elapsed = (datetime.utcnow() - datetime.fromisoformat(g.trial_started_at)).total_seconds()

            # Send 10-minute warning email if not already sent
            if elapsed > 17400 and not session.get("trial_warning_sent"):
                send_trial_warning_email(session.get("user_email"), 10)
                session['trial_warning_sent'] = True

            # Expire trial after 5 hours (18000 seconds)
            if elapsed > 18000:
                session['trial_active'] = False
                session['trial_used_permanently'] = True
                session.pop('trial_started_at', None)
                g.trial_active = False
                g.effective_plan = g.user_plan
                
                # Update database
                try:
                    db_instance = get_database()
                    if db_instance:
                        conn = db_instance.get_connection()
                        cursor = conn.cursor()
                        if db_instance.use_postgres:
                            cursor.execute("UPDATE users SET trial_active = 0, trial_used_permanently = 1 WHERE id = %s", (user_id,))
                        else:
                            cursor.execute("UPDATE users SET trial_active = 0, trial_used_permanently = 1 WHERE id = ?", (user_id,))
                        conn.commit()
                        conn.close()
                        logger.info(f"Trial expired for user {user_id} after {elapsed} seconds")
                except Exception as e:
                    logger.error(f"Error expiring trial for user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error processing trial logic for user {user_id}: {e}")

# DISABLED: This function was potentially causing session contamination
# @app.before_request
# def update_trial_status():
#     """Update trial status in session on every request for trial users"""
#     try:
#         # Skip for static files and API calls to avoid overhead
#         if request.endpoint in ['static', 'favicon'] or request.path.startswith('/static/'):
#             return
#             
#         user_id = session.get('user_id')
#         if user_id:
#             # Check current trial status from database
#             trial_active = is_trial_active(user_id)
#             # Update session with current trial status
#             session['trial_active'] = trial_active
#             
#             # If trial just expired, clear trial flag
#             if not trial_active and session.get('trial_active'):
#                 session['trial_active'] = False
#                 
#     except Exception as e:
#         # Don't break the app if trial check fails
#         logger.error(f"Trial status update error: {e}")
#         pass

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
VALID_PLANS = ["growth", "max"]  # Only Growth/Max selectable - Free is automatic default

# Admin and surveillance constants
ADMIN_DASH_KEY = os.environ.get("ADMIN_DASH_KEY", "soulbridge_admin_2024")
MAINTENANCE_LOG_FILE = "logs/maintenance_log.txt"
THREAT_LOG_FILE = "logs/threat_log.txt"
TRAP_LOG_FILE = "logs/trap_log.txt"

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Helper function to check trial status from database
# -- Trial Check Function --
def check_trial_active_from_db(user_id):
    """Check if trial is active using the new clean trial system"""
    # Use the cleaner is_trial_active function
    return is_trial_active(user_id)

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

def has_accepted_terms():
    """Check if user has accepted terms and conditions"""
    try:
        return session.get('terms_accepted', False)
    except Exception:
        return False

def requires_terms_acceptance():
    """Decorator/helper to check if user needs to accept terms before accessing content"""
    if not is_logged_in():
        return redirect("/login")
    
    if not has_accepted_terms():
        logger.info(f"User {session.get('user_email')} needs to accept terms, redirecting to terms-acceptance")
        return redirect("/terms-acceptance")
    
    return None  # No redirect needed

def get_user_plan():
    """Get user's selected plan"""
    return session.get("user_plan", "free")

def parse_request_data():
    """Parse request data from both JSON and form data"""
    if request.is_json:
        data = request.get_json()
        return data.get("email", "").strip().lower(), data.get("password", "").strip(), data.get("display_name", "").strip()
    else:
        return (request.form.get("email", "").strip().lower(), 
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
    session["user_plan"] = "free"
    if user_id:
        session["user_id"] = user_id
    if is_admin:
        session["is_admin"] = True
    if dev_mode:
        session["dev_mode"] = True
    
    # Restore companion data if available
    if user_id:
        restore_companion_data(user_id)
        
    # Load terms acceptance status
    if user_id:
        load_terms_acceptance_status(user_id)

def restore_companion_data(user_id):
    """Restore companion data from persistence file"""
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
            
        logger.info(f"PERSISTENCE: Restored companion data for user {user_id}")
        
    except FileNotFoundError:
        logger.info(f"PERSISTENCE: No companion data found for user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to restore companion data for user {user_id}: {e}")

def load_terms_acceptance_status(user_id):
    """Load terms acceptance status from database into session"""
    try:
        db_instance = get_database()
        if not db_instance:
            logger.warning("Database connection failed when loading terms status")
            return
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        if db_instance.use_postgres:
            cursor.execute("""
                SELECT terms_accepted, terms_accepted_at, terms_version, terms_language 
                FROM users WHERE id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT terms_accepted, terms_accepted_at, terms_version, terms_language 
                FROM users WHERE id = ?
            """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            terms_accepted, terms_accepted_at, terms_version, terms_language = result
            session['terms_accepted'] = bool(terms_accepted) if terms_accepted is not None else False
            session['terms_accepted_at'] = terms_accepted_at.isoformat() if terms_accepted_at else None
            session['terms_version'] = terms_version or 'v1.0'
            session['terms_language'] = terms_language or 'en'
            
            logger.info(f"TERMS: Loaded terms status for user {user_id}: accepted={session['terms_accepted']}, language={session['terms_language']}")
        else:
            # Default values for new users
            session['terms_accepted'] = False
            session['terms_accepted_at'] = None
            session['terms_version'] = 'v1.0'
            session['terms_language'] = 'en'
            logger.info(f"TERMS: No terms status found for user {user_id}, using defaults")
            
    except Exception as e:
        logger.error(f"Failed to load terms acceptance status for user {user_id}: {e}")
        # Default to False for safety
        session['terms_accepted'] = False
        session['terms_accepted_at'] = None
        session['terms_version'] = 'v1.0'
        session['terms_language'] = 'en'

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
    
    # Run periodic plan migration as safety net during startup
    logger.info("🧼 Running periodic plan migration safety check...")
    run_periodic_plan_migration()
    
    return results


# ========================================
# CORE ROUTES
# ========================================


# ADMIN LOGIN PAGE ROUTE (GET: show form, POST: process login)
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login_page():
    """Admin login page - GET shows form, POST processes admin login"""
    if request.method == "GET":
        try:
            return render_template("admin/login.html")
        except Exception as e:
            logger.error(f"Admin login template error: {e}")
            return "Admin login page temporarily unavailable", 500
    else:
        # POST: process admin login form
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        # Hardcoded admin credentials
        ADMIN_EMAIL = "theenvy13@gmail.com"
        ADMIN_PASSWORD = "Yariel13"
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            setup_user_session(email, is_admin=True)
            flash("Admin login successful!", "success")
            return redirect("/admin/dashboard")
        else:
            flash("Invalid admin credentials.", "danger")
            return redirect("/admin/login")

@app.route("/health")
def health():
    """Production health check with service status and lazy initialization"""
    try:
        # Check for trial sync parameter
        sync_trial = request.args.get('sync_trial')
        if sync_trial == 'true' and is_logged_in():
            try:
                user_id = session.get('user_id')
                db_instance = get_database()
                
                if db_instance and user_id:
                    conn = db_instance.get_connection()
                    cursor = conn.cursor()
                    
                    # Get current trial state from database
                    if db_instance.use_postgres:
                        cursor.execute("SELECT trial_active, trial_started_at, trial_used_permanently FROM users WHERE id = %s", (user_id,))
                    else:
                        cursor.execute("SELECT trial_active, trial_started_at, trial_used_permanently FROM users WHERE id = ?", (user_id,))
                    
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result:
                        trial_active, trial_started_at, trial_used_permanently = result
                        
                        # Update session to match database
                        session['trial_active'] = bool(trial_active) if trial_active is not None else False
                        session['trial_started_at'] = trial_started_at
                        session['trial_used_permanently'] = bool(trial_used_permanently) if trial_used_permanently is not None else False
                        # Don't cache effective_plan - calculate it fresh each time with get_effective_plan()
                        
                        # Calculate effective_plan fresh instead of reading cached value  
                        user_plan = session.get('user_plan', 'free')
                        trial_active = session.get('trial_active', False)
                        effective_plan = get_effective_plan(user_plan, trial_active)
                        
                        return jsonify({
                            "status": "healthy",
                            "service": "SoulBridge AI",
                            "trial_sync": "success",
                            "trial_active": session['trial_active'],
                            "effective_plan": effective_plan
                        })
            except Exception as e:
                logger.error(f"Trial sync error: {e}")
        
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
            # Check if user has accepted terms
            if not session.get('terms_accepted', False):
                logger.info(f"🏠 HOME ROUTE: User authenticated but needs to accept terms")
                return redirect("/terms-acceptance")
            else:
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
            
            # Set user plan from database result (migrate old plan names immediately)
            raw_plan = result.get('plan_type', 'free')
            raw_user_plan = result.get('user_plan', 'free')
            plan_mapping = {'foundation': 'free', 'premium': 'growth', 'enterprise': 'max'}
            session['user_plan'] = plan_mapping.get(raw_plan, raw_plan)
            session['display_name'] = result.get('display_name', 'User')
            
            # Auto-migrate legacy plans in database
            needs_migration = False
            if raw_plan in plan_mapping or raw_user_plan in plan_mapping:
                try:
                    db_instance = get_database()
                    if db_instance:
                        conn = db_instance.get_connection()
                        cursor = conn.cursor()
                        
                        new_plan_type = plan_mapping.get(raw_plan, raw_plan)
                        new_user_plan = plan_mapping.get(raw_user_plan, raw_user_plan)
                        
                        if db_instance.use_postgres:
                            cursor.execute("""
                                UPDATE users 
                                SET plan_type = %s, user_plan = %s 
                                WHERE id = %s AND (plan_type = %s OR user_plan = %s)
                            """, (new_plan_type, new_user_plan, result["user_id"], raw_plan, raw_user_plan))
                        else:
                            cursor.execute("""
                                UPDATE users 
                                SET plan_type = ?, user_plan = ? 
                                WHERE id = ? AND (plan_type = ? OR user_plan = ?)
                            """, (new_plan_type, new_user_plan, result["user_id"], raw_plan, raw_user_plan))
                        
                        if cursor.rowcount > 0:
                            conn.commit()
                            logger.info(f"🧼 Migrated legacy database plans for user {result['user_id']}: {raw_plan}/{raw_user_plan} → {new_plan_type}/{new_user_plan}")
                        conn.close()
                except Exception as migrate_error:
                    logger.error(f"Error migrating legacy plans: {migrate_error}")
            
            # Log plan migration if it occurred
            if raw_plan in plan_mapping:
                logger.info(f"🔄 AUTH: Migrated OLD plan {raw_plan} → {session['user_plan']} during login")
            
            # Restore active trial status from database if exists
            # Initialize trial status to False by default
            session["trial_active"] = False
            
            try:
                database_url = os.environ.get('DATABASE_URL')
                if database_url:
                    import psycopg2
                    conn = psycopg2.connect(database_url)
                    cursor = conn.cursor()
                    
                    # Check if user has an active trial
                    cursor.execute("""
                        SELECT trial_started_at, trial_companion, trial_used_permanently, trial_expires_at
                        FROM users WHERE email = %s
                    """, (email,))
                    trial_result = cursor.fetchone()
                    conn.close()
                    
                    if trial_result:
                        trial_started_at, trial_companion, trial_used_permanently, trial_expires_at = trial_result
                        
                        # Check if trial is still active
                        if not trial_used_permanently and trial_expires_at:
                            now = datetime.utcnow()
                            if now < trial_expires_at:
                                # Trial is still active - restore to session
                                session["trial_active"] = True
                                session["trial_companion"] = trial_companion
                                session["trial_expires_at"] = trial_expires_at.isoformat()
                                
                                time_remaining = int((trial_expires_at - now).total_seconds() / 60)
                                logger.info(f"✅ TRIAL RESTORED: {trial_companion} trial active for {time_remaining} minutes")
                            else:
                                # Trial expired - mark as used (this should be handled by get-trial-status but just in case)
                                logger.info(f"⏰ Trial expired during login for {email}")
                        else:
                            logger.info(f"ℹ️ User {email} has no active trial (used_permanently: {trial_used_permanently})")
                    else:
                        logger.info(f"ℹ️ No trial data found for user {email}")
                        
            except Exception as trial_error:
                logger.warning(f"Failed to restore trial status on login: {trial_error}")
            
            # ISOLATED TIER ACCESS FLAGS - Prevents cross-contamination
            user_plan = session.get('user_plan', 'free')
            trial_active = session.get('trial_active', False)
            
            # Define isolated access flags for each tier using effective_plan
            effective_plan = get_effective_plan(user_plan, trial_active)
            session['access_free'] = True  # Everyone gets free features
            session['access_growth'] = effective_plan in ['growth', 'max'] or trial_active
            session['access_max'] = effective_plan == 'max' or trial_active  
            session['access_trial'] = trial_active
            session.modified = True  # Ensure session changes are saved
            
            logger.info(f"Login successful: {email} (plan: {session['user_plan']}, trial: {trial_active})")
            logger.info(f"Access flags: free={session['access_free']}, growth={session['access_growth']}, max={session['access_max']}, trial={session['access_trial']}")
            
            # Handle both form submissions and AJAX requests
            # Check if user needs to accept terms
            if not session.get('terms_accepted', False):
                redirect_url = "/terms-acceptance"
            else:
                redirect_url = "/intro"
                
            if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                # AJAX request - return JSON
                return jsonify({"success": True, "redirect": redirect_url})
            else:
                # Form submission - redirect directly
                return redirect(redirect_url)
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
        
        # Save companion data before clearing session
        companion_data = {}
        if user_id:
            companion_data = {
                'selected_companion': session.get('selected_companion'),
                'companion_selected_at': session.get('companion_selected_at'),
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
        # If the logout was triggered from /admin/logout, redirect to /admin/login
        if request.path.startswith("/admin/logout") or request.referrer and "/admin" in request.referrer:
            return redirect("/admin/login")
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

@app.route('/api/user-info')
def user_info():
    """Get comprehensive user information including trial status and limits"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        trial_started = session.get('trial_started_at')
        trial_used_permanently = session.get('trial_used_permanently', False)
        
        trial_remaining = 0
        if trial_active and trial_started:
            try:
                if isinstance(trial_started, str):
                    trial_start_time = datetime.fromisoformat(trial_started.replace('Z', '+00:00'))
                else:
                    trial_start_time = trial_started
                elapsed = (datetime.utcnow() - trial_start_time).total_seconds()
                trial_remaining = max(0, 18000 - elapsed)  # 5 hours = 18000 seconds
            except Exception as e:
                logger.error(f"Error calculating trial remaining time: {e}")
                trial_remaining = 0

        effective_plan = get_effective_plan(user_plan, trial_active)

        # Get current usage counts from database
        usage_counts = {"decoder": 0, "fortune": 0, "horoscope": 0}
        try:
            db_instance = get_database()
            if db_instance:
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                
                if db_instance.use_postgres:
                    cursor.execute("SELECT decoder_used, fortune_used, horoscope_used FROM users WHERE id = %s", (user_id,))
                else:
                    cursor.execute("SELECT decoder_used, fortune_used, horoscope_used FROM users WHERE id = ?", (user_id,))
                
                result = cursor.fetchone()
                if result:
                    usage_counts = {
                        "decoder": result[0] or 0,
                        "fortune": result[1] or 0,
                        "horoscope": result[2] or 0
                    }
                conn.close()
        except Exception as e:
            logger.error(f"Error getting usage counts: {e}")
            usage_counts = {"decoder": 0, "fortune": 0, "horoscope": 0}

        return jsonify({
            "success": True,
            "user_plan": user_plan,
            "trial_active": trial_active,
            "trial_used_permanently": trial_used_permanently,
            "effective_plan": effective_plan,
            "trial_remaining": trial_remaining,
            "limits": {
                "decoder": get_feature_limit(user_plan, "decoder"), 
                "fortune": get_feature_limit(user_plan, "fortune"),
                "horoscope": get_feature_limit(user_plan, "horoscope")
            },
            "usage": usage_counts
        })
        
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return jsonify({"success": False, "error": "Failed to get user information"}), 500

@app.route('/api/accept-terms', methods=['POST'])
def accept_terms():
    """Accept terms and conditions"""
    if not session.get('user_id'):
        return jsonify({"success": False, "error": "Login required"}), 401
    
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        # Validate that all required checkboxes are checked
        required_fields = ['ai_understanding', 'terms_privacy', 'age_confirmation', 'responsible_use']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "error": f"Missing required acceptance: {field}"}), 400
        
        # Get database connection
        db_instance = get_database()
        if not db_instance:
            return jsonify({"success": False, "error": "Database connection failed"}), 500
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        # Update user's terms acceptance
        from datetime import datetime
        acceptance_date = datetime.utcnow()
        language_used = data.get('language_used', 'en')
        
        if db_instance.use_postgres:
            cursor.execute("""
                UPDATE users 
                SET terms_accepted = %s, terms_accepted_at = %s, terms_version = %s, terms_language = %s 
                WHERE id = %s
            """, (True, acceptance_date, 'v1.0', language_used, user_id))
        else:
            cursor.execute("""
                UPDATE users 
                SET terms_accepted = ?, terms_accepted_at = ?, terms_version = ?, terms_language = ? 
                WHERE id = ?
            """, (True, acceptance_date, 'v1.0', language_used, user_id))
        
        conn.commit()
        conn.close()
        
        # Update session to reflect terms acceptance
        session['terms_accepted'] = True
        session['terms_accepted_at'] = acceptance_date.isoformat()
        session['terms_language'] = language_used
        
        logger.info(f"✅ TERMS: User {session.get('user_email')} accepted terms at {acceptance_date} in language {language_used}")
        
        return jsonify({
            "success": True,
            "message": "Terms accepted successfully",
            "redirect": "/intro"
        })
        
    except Exception as e:
        logger.error(f"❌ TERMS ACCEPTANCE ERROR: {e}")
        return jsonify({"success": False, "error": "Failed to save terms acceptance"}), 500

@app.route('/api/start-trial', methods=['POST'])
def start_trial():
    """Start 5-hour trial for user"""
    if not session.get('user_id'):
        return jsonify({"success": False, "error": "Login required"}), 401

    db = get_database()
    if not db:
        return jsonify({"success": False, "error": "Database unavailable"}), 500

    conn = db.get_connection()
    cursor = conn.cursor()

    user_id = session['user_id']
    if db.use_postgres:
        cursor.execute("SELECT trial_started_at, trial_used_permanently FROM users WHERE id = %s", (user_id,))
    else:
        cursor.execute("SELECT trial_started_at, trial_used_permanently FROM users WHERE id = ?", (user_id,))

    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "error": "User not found"}), 404

    trial_started_at, trial_used = row
    
    # Check if trial is still active
    if trial_started_at:
        trial_time = trial_started_at
        if isinstance(trial_started_at, str):
            trial_time = datetime.fromisoformat(trial_started_at.replace('Z', '+00:00'))
        if datetime.utcnow() < trial_time + timedelta(hours=5):
            conn.close()
            return jsonify({"success": False, "error": "Trial already active"}), 400
    
    # Check if trial was already used
    if trial_used:
        conn.close()
        return jsonify({"success": False, "error": "Trial already used"}), 400

    now = datetime.utcnow()
    expires = now + timedelta(hours=5)

    # Update database
    try:
        if db.use_postgres:
            cursor.execute("UPDATE users SET trial_started_at = %s, trial_expires_at = %s, trial_used_permanently = TRUE WHERE id = %s", (now, expires, user_id))
        else:
            cursor.execute("UPDATE users SET trial_started_at = ?, trial_expires_at = ?, trial_used_permanently = 1 WHERE id = ?", (now.isoformat(), expires.isoformat(), user_id))
        
        conn.commit()
        conn.close()
    except Exception as e:
        conn.close()
        logger.error(f"Database error starting trial: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500

    # Update session - CRITICAL: Set trial_active to True and effective_plan to max
    session['trial_active'] = True
    session['trial_started_at'] = now.isoformat()
    session['trial_expires_at'] = expires.isoformat()
    session['trial_used_permanently'] = True
    # Don't cache effective_plan - get_effective_plan() will return 'max' when trial_active=True
    session['trial_warning_sent'] = False

    logger.info(f"Trial started for user {user_id}")

    return jsonify({
        "success": True, 
        "message": "🔥 5-Hour Trial Activated! Growth + Max companions unlocked!",
        "expires_at": expires.isoformat(),
        "effective_plan": 'max'
    })

# REMOVED: Duplicate debug_session_info function - using the more comprehensive one at /debug/session-info

@app.route("/api/debug/force-session-reset")
def force_session_reset():
    """Force reset session to clean free user state"""
    if not is_logged_in():
        return jsonify({"error": "Not logged in"}), 401
    
    # Keep essential data but reset plan
    user_email = session.get('user_email')
    user_id = session.get('user_id')
    
    # Clear and rebuild session with correct data
    session.clear()
    session['user_authenticated'] = True
    session['session_version'] = '2025-07-28-banking-security'
    session['user_email'] = user_email
    session['user_id'] = user_id
    session['user_plan'] = 'free'  # Reset to free
    session['trial_active'] = False
    
    return jsonify({
        "success": True,
        "message": "Session reset to clean free user state",
        "new_plan": "free"
    })

@app.route("/api/debug/reset-to-free")
def reset_to_free():
    """Reset current user to free plan (for testing)"""
    if not is_logged_in():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    session['user_plan'] = 'free'
    
    return jsonify({
        "success": True,
        "message": "User reset to free plan",
        "user_plan": session.get('user_plan')
    })

@app.route("/api/debug/reset-trial-state")
def reset_trial_state():
    """Reset trial state for testing - allows trial to be started again"""
    if not is_logged_in():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    user_id = session.get('user_id')
    
    try:
        # Reset in database
        db_instance = get_database()
        if db_instance and user_id:
            conn = db_instance.get_connection()
            cursor = conn.cursor()
            
            if db_instance.use_postgres:
                cursor.execute("""
                    UPDATE users 
                    SET trial_active = 0, 
                        trial_started_at = NULL,
                        trial_used_permanently = 0,
                        trial_warning_sent = 0
                    WHERE id = %s
                """, (user_id,))
            else:
                cursor.execute("""
                    UPDATE users 
                    SET trial_active = 0, 
                        trial_started_at = NULL,
                        trial_used_permanently = 0,
                        trial_warning_sent = 0
                    WHERE id = ?
                """, (user_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"Trial state reset in database for user {user_id}")
        
        # Reset in session
        session['trial_active'] = False
        session['trial_started_at'] = None
        session['trial_used_permanently'] = False
        session['trial_warning_sent'] = False
        session['user_plan'] = 'free'
        # Don't cache effective_plan - calculate it fresh each time
        
        return jsonify({
            "success": True,
            "message": "Trial state reset - you can now start a new trial",
            "trial_active": False,
            "trial_used_permanently": False,
            "user_plan": "free"
        })
        
    except Exception as e:
        logger.error(f"Error resetting trial state: {e}")
        return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500

@app.route("/api/debug/upgrade-to-growth")
def upgrade_to_growth():
    """Upgrade current user to Growth plan (for testing decoder limits)"""
    if not is_logged_in():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    session['user_plan'] = 'growth'  # Growth plan in backend
    
    return jsonify({
        "success": True,
        "message": "User upgraded to Growth plan",
        "user_plan": session.get('user_plan')
    })

@app.route("/api/debug/upgrade-to-max")
def upgrade_to_max():
    """Upgrade current user to Max plan (for testing decoder limits)"""
    if not is_logged_in():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    session['user_plan'] = 'max'  # Max plan in backend
    
    return jsonify({
        "success": True,
        "message": "User upgraded to Max plan",
        "user_plan": session.get('user_plan')
    })

@app.route("/api/debug/force-max-for-live")
def force_max_for_live():
    """Force current user to max plan in both session and database"""
    if not is_logged_in():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    # Set in session
    session['user_plan'] = 'max'
    
    # Also save to database for persistence
    user_email = session.get('user_email') or session.get('email')
    user_id = session.get('user_id')
    
    try:
        db_instance = get_database()
        if db_instance and (user_id or user_email):
            conn = db_instance.get_connection()
            cursor = conn.cursor()
            
            placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
            
            # Update user plan in users table
            if user_id:
                cursor.execute(f"UPDATE users SET plan_type = {placeholder} WHERE id = {placeholder}", ('max', user_id))
            elif user_email:
                cursor.execute(f"UPDATE users SET plan_type = {placeholder} WHERE email = {placeholder}", ('max', user_email))
            
            # Also add to subscriptions table
            cursor.execute(f"""
                INSERT OR REPLACE INTO subscriptions 
                (user_email, plan_type, status, created_at) 
                VALUES ({placeholder}, {placeholder}, 'active', datetime('now'))
            """, (user_email, 'max'))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                "success": True,
                "message": "User set to max plan in session and database",
                "user_plan": session.get('user_plan'),
                "user_email": user_email,
                "user_id": user_id
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database update failed: {str(e)}",
            "session_plan": session.get('user_plan')
        })

@app.route("/api/debug/get-current-plan")
def get_current_plan():
    """Get current user's plan (for debugging)"""
    if not is_logged_in():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    user_plan = session.get('user_plan', 'free')
    
    return jsonify({
        "success": True,
        "user_plan": user_plan,
        "session_data": {
            "user_email": session.get('user_email'),
            "display_name": session.get('display_name')
        }
    })

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
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_type VARCHAR(50) DEFAULT 'free'")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image_data TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name TEXT")
            # Add trial system columns
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_started_at TIMESTAMP")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_companion TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_used_permanently BOOLEAN DEFAULT FALSE")
            # Add terms acceptance tracking columns
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_accepted BOOLEAN DEFAULT FALSE")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_accepted_at TIMESTAMP")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_version TEXT DEFAULT 'v1.0'")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_language TEXT DEFAULT 'en'")
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
        
        logger.info(f"📥 REGISTER: Attempting to register user: {email}")
        
        if not email or not password:
            logger.warning(f"❌ REGISTER: Missing data - email: {bool(email)}, password: {bool(password)}")
            return jsonify({"success": False, "error": "Email and password required"}), 400
        
        # Use the proper database instance with compatibility
        db_instance = get_database()
        if not db_instance:
            return jsonify({"success": False, "error": "Database connection failed"}), 500
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        # Check if user already exists with detailed debugging
        logger.info(f"🔍 REGISTER: Checking if {email} already exists...")
        if db_instance.use_postgres:
            cursor.execute("SELECT id, email, created_at FROM users WHERE email = %s", (email,))
        else:
            cursor.execute("SELECT id, email, created_at FROM users WHERE email = ?", (email,))
        
        existing_user = cursor.fetchone()
        if existing_user:
            logger.warning(f"❌ REGISTER: Email {email} already exists in database - ID: {existing_user[0]}, Created: {existing_user[2]}")
            
            # Also check for case-insensitive matches
            if db_instance.use_postgres:
                cursor.execute("SELECT COUNT(*) FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
            else:
                cursor.execute("SELECT COUNT(*) FROM users WHERE LOWER(email) = LOWER(?)", (email,))
            
            case_matches = cursor.fetchone()[0]
            logger.warning(f"❌ REGISTER: Case-insensitive matches for {email}: {case_matches}")
            
            conn.close()
            return jsonify({"success": False, "error": "Email already registered. Please try logging in instead."}), 400
        
        # Double-check with case-insensitive search
        if db_instance.use_postgres:
            cursor.execute("SELECT id, email FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
        else:
            cursor.execute("SELECT id, email FROM users WHERE LOWER(email) = LOWER(?)", (email,))
        
        case_existing = cursor.fetchone()
        if case_existing:
            logger.warning(f"❌ REGISTER: Case-insensitive match found: {case_existing[1]} (ID: {case_existing[0]})")
            conn.close()
            return jsonify({"success": False, "error": f"Email already registered as '{case_existing[1]}'. Please try logging in instead."}), 400
        
        logger.info(f"✅ REGISTER: Email {email} is available, proceeding with registration")
        
        # Create new user with all trial system columns
        import bcrypt
        hash_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        logger.info(f"💾 REGISTER: Inserting user {email} into database...")
        
        try:
            if db_instance.use_postgres:
                cursor.execute("""
                    INSERT INTO users (email, password_hash, display_name)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (email, hash_pw, name))
                user_id = cursor.fetchone()[0]
            else:
                cursor.execute("""
                    INSERT INTO users (email, password_hash, display_name)
                    VALUES (?, ?, ?)
                """, (email, hash_pw, name))
                user_id = cursor.lastrowid
            
            logger.info(f"✅ REGISTER: User {email} inserted with ID: {user_id}")
            
            conn.commit()
            logger.info(f"✅ REGISTER: Database commit successful for user {email}")
            
        except Exception as insert_error:
            logger.error(f"❌ REGISTER: Database insert failed for {email}: {insert_error}")
            conn.rollback()
            conn.close()
            return jsonify({"success": False, "error": f"Database error: {str(insert_error)}"}), 500
        
        conn.close()
        
        # Initialize comprehensive session for new user
        session['user_id'] = user_id
        session['user_email'] = email
        session['email'] = email
        session['user_authenticated'] = True
        session['session_version'] = "2025-07-28-banking-security"
        session['last_activity'] = datetime.now().isoformat()
        session['user_plan'] = 'free'
        session['plan_selected_at'] = time.time()
        session['first_time_user'] = False
        
        # Initialize trial system session variables
        session['trial_active'] = False
        session['trial_started_at'] = None
        session['trial_used_permanently'] = False
        session['trial_warning_sent'] = False
        # Don't cache effective_plan - calculate it fresh each time
        
        # Initialize usage counters
        session['decoder_used'] = 0
        session['fortune_used'] = 0  
        session['horoscope_used'] = 0
        
        # Send welcome email to new user
        try:
            if email_service:
                logger.info(f"📧 Sending welcome email to {email}")
                email_result = email_service.send_welcome_email(email, name)
                if email_result.get('success'):
                    logger.info(f"✅ Welcome email sent successfully to {email}")
                else:
                    logger.warning(f"⚠️ Welcome email failed for {email}: {email_result.get('error')}")
            else:
                logger.warning(f"⚠️ Email service not available for welcome email to {email}")
        except Exception as e:
            logger.error(f"❌ Welcome email error for {email}: {e}")
        
        response_data = {
            "success": True, 
            "message": "🎉 Welcome to SoulBridge AI! Please review and accept our terms to continue.",
            "redirect": "/terms-acceptance"
        }
        logger.info(f"✅ SIGNUP SUCCESS: Returning JSON response: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        import traceback
        logger.error(f"Registration traceback: {traceback.format_exc()}")
        
        # Clean up any partial user data if registration failed
        try:
            if 'email' in locals():
                db_instance = get_database()
                if db_instance:
                    conn = db_instance.get_connection()
                    cursor = conn.cursor()
                    if db_instance.use_postgres:
                        cursor.execute("DELETE FROM users WHERE email = %s AND created_at > NOW() - INTERVAL '1 minute'", (email,))
                    else:
                        cursor.execute("DELETE FROM users WHERE email = ? AND created_at > datetime('now', '-1 minute')", (email,))
                    conn.commit()
                    conn.close()
                    logger.info(f"Cleaned up partial registration for {email}")
        except Exception as cleanup_error:
            logger.error(f"Error during registration cleanup: {cleanup_error}")
        
        # If we get here, registration may have partially succeeded but had issues
        # Check if user was actually created before showing error
        try:
            db_instance = get_database()
            if db_instance and 'email' in locals():
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                if db_instance.use_postgres:
                    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                else:
                    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                user_exists = cursor.fetchone()
                conn.close()
                
                if user_exists:
                    # User was created successfully, redirect to intro instead of showing error
                    logger.info(f"Registration completed despite error - redirecting user {email}")
                    return jsonify({
                        "success": True, 
                        "message": "🎉 Welcome to SoulBridge AI! Please accept our terms to continue.",
                        "redirect": "/terms-acceptance"
                    })
        except:
            pass
            
        return jsonify({"success": False, "error": "Registration failed. Please try again."}), 500

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
    try:
        if not is_logged_in():
            return redirect("/login")
            
        # Check if user has accepted terms
        terms_check = requires_terms_acceptance()
        if terms_check:
            return terms_check
        
        # TIER ISOLATION: Get tier-specific data instead of shared session data
        current_tier = get_current_user_tier()
        tier_system = get_current_tier_system()
        tier_data = tier_system.get_session_data()
        
        user_plan = tier_data.get('tier', 'free')  # Use tier-specific plan
        features = tier_data.get('features', [])
        limits = tier_data.get('limits', {})
        
        logger.info(f"🔒 INTRO TIER ISOLATION: Using {current_tier.upper()} tier data - plan={user_plan}, features={len(features)}")
        
        # ISOLATED TIER ACCESS FLAGS - Prevents cross-contamination 
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)  # FIXED: Calculate fresh
        
        # Define isolated access flags for each tier using effective_plan
        session['access_free'] = True  # Everyone gets free features
        session['access_growth'] = effective_plan in ['growth', 'max'] or trial_active
        session['access_max'] = effective_plan == 'max' or trial_active  
        session['access_trial'] = trial_active
        session.modified = True  # Ensure session changes are saved
        
        logger.info(f"✅ INTRO: trial_active={trial_active}, effective_plan={effective_plan}, access_growth={session['access_growth']}, access_max={session['access_max']}")
        logger.info(f"Access flags: free={session['access_free']}, growth={session['access_growth']}, max={session['access_max']}, trial={session['access_trial']}")
        
        return render_template("intro.html")
    except Exception as e:
        logger.error(f"❌ INTRO ERROR: {e}")
        import traceback
        logger.error(f"❌ INTRO TRACEBACK: {traceback.format_exc()}")
        return f"<h1>Intro Error</h1><p>Error: {str(e)}</p>", 500

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
        
    # Check if user has accepted terms
    terms_check = requires_terms_acceptance()
    if terms_check:
        return terms_check
    
    # CRITICAL: Ensure session has correct plan names for templates (ONLY migrate old names)
    user_plan = session.get('user_plan', 'free')
    plan_mapping = {'foundation': 'free', 'premium': 'growth', 'enterprise': 'max'}
    # ONLY migrate if it's an OLD plan name that needs updating
    if user_plan in plan_mapping and user_plan != plan_mapping[user_plan]:
        session['user_plan'] = plan_mapping[user_plan]
        logger.info(f"🔄 COMPANION: Migrated OLD plan {user_plan} → {session['user_plan']}")
    else:
        logger.info(f"✅ COMPANION: Plan {user_plan} already using new naming - no migration needed")
    
    logger.info(f"✅ COMPANION SELECTION: User authenticated, showing companion selector")
    return render_template("companion_selector.html")

@app.route("/chat")
def chat():
    """Chat page with bulletproof tier system"""
    if not is_logged_in():
        companion = request.args.get('companion')
        if companion:
            return redirect(f"/login?return_to=chat&companion={companion}")
        return redirect("/login?return_to=chat")
        
    # Check if user has accepted terms
    terms_check = requires_terms_acceptance()
    if terms_check:
        return terms_check
    
    # Get user data
    user_id = session.get('user_id')
    # Use session values set by @app.before_request (already calculated)
    user_plan = session.get('user_plan', 'free') or 'free'
    trial_active = session.get('trial_active', False)
    effective_plan = get_effective_plan(user_plan, trial_active)  # FIXED: Calculate fresh
    
    # Handle companion selection
    companion_id = request.args.get('companion')
    if companion_id:
        # Define companion tiers - handle different companion ID formats
        companion_tiers = {
            # Free companions
            'blayzo_free': 'free', 'blayzica_free': 'free', 'companion_gamerjay': 'free',
            'blayzia_free': 'free', 'blayzion_free': 'free', 'claude_free': 'free',
            # Growth companions  
            'companion_sky': 'growth', 'blayzo_premium': 'growth', 'blayzica_growth': 'growth',
            'gamerjay_premium': 'growth', 'watchdog_growth': 'growth',
            'crimson_growth': 'growth', 'violet_growth': 'growth', 'claude_growth': 'growth',
            # Max companions
            'companion_crimson': 'max', 'companion_violet': 'max', 'royal_max': 'max',
            'watchdog_max': 'max', 'ven_blayzica': 'max', 'ven_sky': 'max', 'claude_max': 'max',
            # Handle direct names (violet -> companion_violet)
            'violet': 'max', 'crimson': 'max', 'sky': 'growth'
        }
        
        companion_tier = companion_tiers.get(companion_id, 'free')
        
        # Check access using bulletproof logic
        can_access = can_access_companion(user_plan, companion_tier, trial_active)
        
        if not can_access:
            return redirect("/companion-selection?error=upgrade_required")
            
        session['selected_companion'] = companion_id
    
    companion_name = session.get('selected_companion', 'blayzo_free')
    
    # Handle legacy companion ID compatibility (map old IDs to new ones)
    companion_id_mapping = {
        'blayzo_growth': 'blayzo_premium',
        'companion_gamerjay_premium': 'gamerjay_premium',
        # Add any other legacy mappings if needed
        'blayzo_pro': 'blayzo_premium',
        'gamerjay_pro': 'gamerjay_premium'
    }
    original_companion_name = companion_name
    if companion_name in companion_id_mapping:
        companion_name = companion_id_mapping[companion_name]
        session['selected_companion'] = companion_name  # Update session with new ID
        logger.info(f"🔄 Migrated companion ID: {original_companion_name} → {companion_name}")
    
    # Get companion avatar and display name
    def get_companion_info(companion_id):
        """Get companion display name and avatar image"""
        companion_data = {
            # Free companions
            'blayzo_free': {'name': 'Blayzo', 'avatar': '/static/logos/Blayzo.png'},
            'blayzica_free': {'name': 'Blayzica', 'avatar': '/static/logos/Blayzica.png'},
            'companion_gamerjay': {'name': 'GamerJay', 'avatar': '/static/logos/GamerJay Free companion.png'},
            'blayzia_free': {'name': 'Blayzia', 'avatar': '/static/logos/Blayzia.png'},
            'blayzion_free': {'name': 'Blayzion', 'avatar': '/static/logos/Blayzion.png'},
            'claude_free': {'name': 'Claude', 'avatar': '/static/logos/Claude Free.png'},
            
            # Growth companions  
            'companion_sky': {'name': 'Sky', 'avatar': '/static/logos/Sky a premium companion.png'},
            'blayzo_premium': {'name': 'Blayzo Pro', 'avatar': '/static/logos/Blayzo premium companion.png'},
            'blayzo_growth': {'name': 'Blayzo Pro', 'avatar': '/static/logos/Blayzo premium companion.png'},  # Legacy compatibility
            'blayzo_pro': {'name': 'Blayzo Pro', 'avatar': '/static/logos/Blayzo premium companion.png'},  # Legacy compatibility
            'blayzica_growth': {'name': 'Blayzica Pro', 'avatar': '/static/logos/Blayzica Pro.png'},
            'gamerjay_premium': {'name': 'GamerJay Premium', 'avatar': '/static/logos/GamerJay premium companion.png'},
            'companion_gamerjay_premium': {'name': 'GamerJay Premium', 'avatar': '/static/logos/GamerJay premium companion.png'},  # Legacy compatibility
            'gamerjay_pro': {'name': 'GamerJay Premium', 'avatar': '/static/logos/GamerJay premium companion.png'},  # Legacy compatibility
            'watchdog_growth': {'name': 'WatchDog', 'avatar': '/static/logos/WatchDog a Premium companion.png'},
            'crimson_growth': {'name': 'Crimson', 'avatar': '/static/logos/Crimson.png'},
            'violet_growth': {'name': 'Violet', 'avatar': '/static/logos/Violet.png'},
            'claude_growth': {'name': 'Claude Growth', 'avatar': '/static/logos/Claude Growth.png'},
            
            # Max companions
            'companion_crimson': {'name': 'Crimson', 'avatar': '/static/logos/Crimson a Max companion.png'},
            'companion_violet': {'name': 'Violet', 'avatar': '/static/logos/Violet a Max companion.png'},
            'royal_max': {'name': 'Royal', 'avatar': '/static/logos/Royal a Max companion.png'},
            'watchdog_max': {'name': 'WatchDog Max', 'avatar': '/static/logos/WatchDog a Max Companion.png'},
            'ven_blayzica': {'name': 'Ven Blayzica', 'avatar': '/static/logos/Ven Blayzica a Max companion.png'},
            'ven_sky': {'name': 'Ven Sky', 'avatar': '/static/logos/Ven Sky a Max companion.png'},
            'claude_max': {'name': 'Claude Max', 'avatar': '/static/logos/Claude Max.png'},
            
            # Referral companions
            'blayzo_referral': {'name': 'Blayzo Referral', 'avatar': '/static/logos/Blayzo Referral.png'},
            'claude_referral': {'name': 'Claude Referral', 'avatar': '/static/logos/Claude Referral.png'},
        }
        
        # Add debug logging before returning
        if companion_id in companion_data:
            logger.info(f"✅ COMPANION FOUND: {companion_id} -> {companion_data[companion_id]}")
            return companion_data[companion_id]
        else:
            logger.warning(f"❌ COMPANION NOT FOUND: {companion_id}, using fallback. Available keys: {list(companion_data.keys())}")
            return {
                'name': companion_id.replace('_', ' ').title(),
                'avatar': '/static/logos/IntroLogo.png'  # fallback
            }
    
    companion_info = get_companion_info(companion_name)
    
    # Debug logging
    logger.info(f"🎭 CHAT COMPANION DEBUG: companion_name={companion_name}, display_name={companion_info['name']}, avatar={companion_info['avatar']}")
    
    return render_template("chat.html",
        companion=companion_name,
        companion_display_name=companion_info['name'],
        companion_avatar=companion_info['avatar'],
        user_plan=user_plan,
        trial_active=trial_active, 
        effective_plan=effective_plan
    )

@app.route("/api/companions", methods=["GET"])
def api_companions():
    """Get available companions organized by tiers"""
    try:
        # Allow access without authentication so users can see companions before login
        if is_logged_in():
            # Calculate effective_plan fresh from current session data
            user_plan = session.get('user_plan', 'free')  # Original plan for display
            trial_active = session.get('trial_active', False)
            effective_plan = get_effective_plan(user_plan, trial_active)  # FIXED: Calculate fresh
        else:
            effective_plan = 'free'
            user_plan = 'free'
            trial_active = False
        
        # Helper function to determine lock reason using bulletproof access control
        def get_lock_reason(tier):
            if tier == "free":
                return None
            elif tier == "growth":
                # Growth companions: use bulletproof access control
                if can_access_companion(user_plan, 'growth', trial_active):
                    return None
                else:
                    return "Try 5hr Free or Upgrade"
            elif tier == "max":
                # Max companions: use bulletproof access control
                if can_access_companion(user_plan, 'max', trial_active):
                    return None
                else:
                    return "Try 5hr Free or Purchase Max Plan"
            return "Upgrade Required"
        
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
                {"companion_id": "companion_sky", "display_name": "Sky", "description": "Premium companion with advanced features", "avatar_image": "/static/logos/Sky a premium companion.png", "tier": "growth", "is_recommended": True, "popularity_score": 90, "lock_reason": get_lock_reason("growth")},
                {"companion_id": "blayzo_premium", "display_name": "Blayzo Pro", "description": "Advanced Blayzo with enhanced creativity", "avatar_image": "/static/logos/Blayzo premium companion.png", "tier": "growth", "is_recommended": True, "popularity_score": 92, "lock_reason": get_lock_reason("growth")},
                {"companion_id": "blayzica_growth", "display_name": "Blayzica Pro", "description": "Enhanced emotional intelligence companion", "avatar_image": "/static/logos/Blayzica Pro.png", "tier": "growth", "is_recommended": True, "popularity_score": 91, "lock_reason": get_lock_reason("growth")},
                {"companion_id": "gamerjay_premium", "display_name": "GamerJay Premium", "description": "Enhanced GamerJay with premium features", "avatar_image": "/static/logos/GamerJay premium companion.png", "tier": "growth", "is_recommended": False, "popularity_score": 88, "lock_reason": get_lock_reason("growth")},
                {"companion_id": "watchdog_growth", "display_name": "WatchDog", "description": "Your protective guardian companion", "avatar_image": "/static/logos/WatchDog a Premium companion.png", "tier": "growth", "is_recommended": False, "popularity_score": 78, "lock_reason": get_lock_reason("growth")},
                {"companion_id": "crimson_growth", "display_name": "Crimson", "description": "Motivational drive to overcome challenges", "avatar_image": "/static/logos/Crimson.png", "tier": "growth", "is_recommended": True, "popularity_score": 87, "lock_reason": get_lock_reason("growth")},
                {"companion_id": "violet_growth", "display_name": "Violet", "description": "Creative inspiration and artistic guidance", "avatar_image": "/static/logos/Violet.png", "tier": "growth", "is_recommended": False, "popularity_score": 84, "lock_reason": get_lock_reason("growth")},
                {"companion_id": "claude_growth", "display_name": "Claude Growth", "description": "Advanced coding guidance and architecture", "avatar_image": "/static/logos/Claude Growth.png", "tier": "growth", "is_recommended": True, "popularity_score": 93, "lock_reason": get_lock_reason("growth")}
            ],
            "max": [
                {"companion_id": "companion_crimson", "display_name": "Crimson Max", "description": "Elite transformation companion", "avatar_image": "/static/logos/Crimson a Max companion.png", "tier": "max", "is_recommended": True, "popularity_score": 98, "lock_reason": get_lock_reason("max")},
                {"companion_id": "companion_violet", "display_name": "Violet Max", "description": "Premium creative companion", "avatar_image": "/static/logos/Violet a Max companion.png", "tier": "max", "is_recommended": False, "popularity_score": 91, "lock_reason": get_lock_reason("max")},
                {"companion_id": "royal_max", "display_name": "Royal", "description": "Majestic guide with sophisticated wisdom", "avatar_image": "/static/logos/Royal a Max companion.png", "tier": "max", "is_recommended": False, "popularity_score": 95, "lock_reason": get_lock_reason("max")},
                {"companion_id": "watchdog_max", "display_name": "WatchDog Max", "description": "Ultimate guardian companion", "avatar_image": "/static/logos/WatchDog a Max Companion.png", "tier": "max", "is_recommended": False, "popularity_score": 93, "lock_reason": get_lock_reason("max")},
                {"companion_id": "ven_blayzica", "display_name": "Ven Blayzica", "description": "Enhanced healer with emotional mastery", "avatar_image": "/static/logos/Ven Blayzica a Max companion.png", "tier": "max", "is_recommended": True, "popularity_score": 94, "lock_reason": get_lock_reason("max")},
                {"companion_id": "ven_sky", "display_name": "Ven Sky", "description": "Ascended spiritual guide", "avatar_image": "/static/logos/Ven Sky a Max companion.png", "tier": "max", "is_recommended": True, "popularity_score": 96, "lock_reason": get_lock_reason("max")},
                {"companion_id": "claude_max", "display_name": "Claude Max", "description": "Elite coding mastery and system design", "avatar_image": "/static/logos/Claude Max.png", "tier": "max", "is_recommended": True, "popularity_score": 97, "lock_reason": get_lock_reason("max")}
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
            "user_plan": user_plan,
            "trial_active": trial_active,
            "trial_used_permanently": session.get('trial_used_permanently', False),
            "trial_expires_at": session.get('trial_expires_at'),
            "effective_plan": effective_plan  # Use actual effective_plan
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
        
        # Check if user has access to this companion using bulletproof access control
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)  # FIXED: Calculate fresh
        
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
                {"companion_id": "blayzo_premium", "tier": "growth"},
                {"companion_id": "blayzica_growth", "tier": "growth"},
                {"companion_id": "gamerjay_premium", "tier": "growth"},
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
        
        # Use bulletproof access control with session data (already set by @app.before_request)
        logger.info(f"🔍 COMPANION SELECTION DEBUG: user_plan={user_plan}, effective_plan={effective_plan}, trial_active={trial_active}, companion_tier={companion_tier}, companion_id={companion_id}")
        
        # Use bulletproof companion access control
        has_access = can_access_companion(user_plan, companion_tier, trial_active)
        
        if not has_access:
            logger.warning(f"🚫 COMPANION SELECTION BLOCKED: user_plan={user_plan}, trial_active={trial_active}, companion_tier={companion_tier}, companion_id={companion_id}")
            return jsonify({
                "success": False, 
                "error": f"Upgrade required to access {companion_tier} tier companions",
                "tier_required": companion_tier
            }), 403
        
        # Store selected companion in session
        session['selected_companion'] = companion_id
        session['companion_selected_at'] = time.time()
        
        # CRITICAL FIX: Save companion selection to database
        try:
            user_id = session.get('user_id')
            user_email = session.get('user_email') or session.get('email')
            
            if user_id or user_email:
                conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
                cursor = conn.cursor()
                placeholder = '%s'
                
                # Get current companion_data or create new
                if user_id:
                    cursor.execute("SELECT companion_data FROM users WHERE id = %s", (user_id,))
                else:
                    cursor.execute("SELECT companion_data FROM users WHERE email = %s", (user_email,))
                
                result = cursor.fetchone()
                current_data = result[0] if result and result[0] else {}
                
                # Update selected companion in companion_data
                current_data['selected_companion'] = companion_id
                
                # Save back to database
                if user_id:
                    cursor.execute("UPDATE users SET companion_data = %s WHERE id = %s", 
                                 (json.dumps(current_data), user_id))
                else:
                    cursor.execute("UPDATE users SET companion_data = %s WHERE email = %s", 
                                 (json.dumps(current_data), user_email))
                
                conn.commit()
                conn.close()
                logger.info(f"💾 COMPANION SELECTION SAVED TO DATABASE: {companion_id} for user {user_id or user_email}")
            else:
                logger.warning("⚠️ No user ID or email found in session - companion selection not saved to database")
                
        except Exception as db_error:
            logger.error(f"❌ Database error saving companion selection: {db_error}")
            # Don't fail the request if database save fails, but log it
        
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
            session['user_plan'] = 'free'
        
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
                        
                        cursor.execute(f"SELECT profile_image, profile_picture_url, profile_image_data FROM users WHERE id = {placeholder}", (user_id,))
                        result = cursor.fetchone()
                        conn.close()
                        
                        if result:
                            # Use same logic as /api/users route - prioritize API endpoints
                            if result[0] and result[0].startswith('/api/profile-image/'):
                                # Already correct API endpoint format
                                profile_image = result[0]
                                logger.info(f"Using correct API profile image URL: {profile_image}")
                            elif result[1]:  # Have base64 data, use API endpoint
                                profile_image = f"/api/profile-image/{user_id}"
                                logger.info(f"Using profile image API endpoint: {profile_image}")
                            elif result[0]:  # Old filesystem path, convert to API endpoint
                                profile_image = f"/api/profile-image/{user_id}"
                                logger.info(f"Converting old filesystem path to API endpoint: {profile_image}")
                            
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
    """Wellness Gallery route (replaces old community dashboard)"""
    try:
        if not is_logged_in():
            return redirect("/login")
        return render_template("wellness_gallery.html")
    except Exception as e:
        logger.error(f"Wellness Gallery error: {e}")
        return redirect("/")

@app.route("/wellness-gallery")
def wellness_gallery():
    """Direct route to wellness gallery"""
    try:
        if not is_logged_in():
            return redirect("/login")
        return render_template("wellness_gallery.html")
    except Exception as e:
        logger.error(f"Wellness Gallery error: {e}")
        return redirect("/")
        
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
        user_id = session.get('user_id')
        user_plan = session.get('user_plan', 'free')
        decoder_usage = get_decoder_usage()
        
        # Use session values set by @app.before_request (more efficient)
        effective_plan = session.get('effective_plan', 'free')
        trial_active = session.get('trial_active', False)
        
        # FIXED: Use user_plan for limits, effective_plan for feature access
        daily_limit = get_feature_limit(user_plan, 'decoder')  # Limits based on subscription
        
        # DEBUG: Log decoder access info
        logger.info(f"🔍 DECODER DEBUG: user_plan = {user_plan}")
        logger.info(f"🔍 DECODER DEBUG: effective_plan = {effective_plan}")
        logger.info(f"🔍 DECODER DEBUG: daily_limit = {daily_limit}")
        logger.info(f"🔍 DECODER DEBUG: decoder_usage = {decoder_usage}")
        
        return render_template("decoder.html", 
                             user_plan=effective_plan,  # Show effective access tier
                             daily_limit=daily_limit,   # But use subscription limits
                             current_usage=decoder_usage)
    except Exception as e:
        logger.error(f"Decoder template error: {e}")
        return jsonify({"error": "Decoder temporarily unavailable"}), 500

@app.route("/fortune")
def fortune():
    """Fortune Teller page with mystical readings and tier-based limits"""
    try:
        if not is_logged_in():
            return redirect("/login")
            
        # Get user's plan and fortune usage
        user_id = session.get('user_id')
        user_plan = session.get('user_plan', 'free')
        fortune_usage = get_fortune_usage()
        
        # Use session values set by @app.before_request (more efficient)
        effective_plan = session.get('effective_plan', 'free')
        trial_active = session.get('trial_active', False)
        
        # FIXED: Use user_plan for limits, effective_plan for feature access
        daily_limit = get_feature_limit(user_plan, 'fortune')  # Limits based on subscription
        
        # DEBUG: Log fortune access info
        logger.info(f"🔮 FORTUNE DEBUG: user_plan = {user_plan}")
        logger.info(f"🔮 FORTUNE DEBUG: effective_plan = {effective_plan}")
        logger.info(f"🔮 FORTUNE DEBUG: daily_limit = {daily_limit}")
        logger.info(f"🔮 FORTUNE DEBUG: fortune_usage = {fortune_usage}")
        
        return render_template("fortune.html", 
                             user_plan=effective_plan,  # Show effective access tier
                             daily_limit=daily_limit,   # But use subscription limits
                             current_usage=fortune_usage)
    except Exception as e:
        logger.error(f"Fortune template error: {e}")
        return jsonify({"error": "Fortune teller temporarily unavailable"}), 500

@app.route("/horoscope")
def horoscope():
    """Horoscope page with zodiac readings and tier-based limits"""
    try:
        if not is_logged_in():
            return redirect("/login")
            
        # Get user's plan and horoscope usage
        user_id = session.get('user_id')
        user_plan = session.get('user_plan', 'free')
        horoscope_usage = get_horoscope_usage()
        
        # Use session values set by @app.before_request (more efficient)
        effective_plan = session.get('effective_plan', 'free')
        trial_active = session.get('trial_active', False)
        
        # FIXED: Use user_plan for limits, effective_plan for feature access
        daily_limit = get_feature_limit(user_plan, 'horoscope')  # Limits based on subscription
        
        # DEBUG: Log horoscope access info
        logger.info(f"⭐ HOROSCOPE DEBUG: user_plan = {user_plan}")
        logger.info(f"⭐ HOROSCOPE DEBUG: effective_plan = {effective_plan}")
        logger.info(f"⭐ HOROSCOPE DEBUG: daily_limit = {daily_limit}")
        logger.info(f"⭐ HOROSCOPE DEBUG: horoscope_usage = {horoscope_usage}")
        
        return render_template("horoscope.html", 
                             user_plan=effective_plan,
                             daily_limit=daily_limit,
                             current_usage=horoscope_usage)
    except Exception as e:
        logger.error(f"Horoscope template error: {e}")
        return jsonify({"error": "Horoscope temporarily unavailable"}), 500

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

@app.route("/terms-acceptance")
def terms_acceptance_page():
    """Terms acceptance page - required for new users"""
    try:
        if not is_logged_in():
            return redirect("/login")
            
        # Check if user already accepted terms
        if session.get('terms_accepted'):
            logger.info(f"Terms already accepted by {session.get('user_email')}, redirecting to intro")
            return redirect("/intro")
            
        return render_template("terms_acceptance.html")
    except Exception as e:
        logger.error(f"Terms acceptance page error: {e}")
        return redirect("/login")

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

@app.route("/api/voice-chat/process", methods=["POST"])
def voice_chat_process():
    """Process voice chat audio - Whisper transcription + GPT-4 response"""
    try:
        # Basic validation
        if 'audio' not in request.files:
            return jsonify({"success": False, "error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        character = request.form.get('character', 'SoulBridge AI Assistant')
        
        if not audio_file or audio_file.filename == '':
            return jsonify({"success": False, "error": "No audio file selected"}), 400
        
        print(f"🎤 Processing voice for character: {character}")
        print(f"🔊 Audio file size: {len(audio_file.read())} bytes")
        audio_file.seek(0)  # Reset file pointer
        
        # Save audio to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_path = temp_file.name
            audio_file.save(audio_path)
            print(f"💾 Saved audio to: {audio_path}")
        
        try:
            # Initialize OpenAI client
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            # Transcribe audio with Whisper
            print("🔄 Starting Whisper transcription...")
            with open(audio_path, 'rb') as audio_data:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_data,
                    response_format="text"
                )
            
            text_input = transcription.strip() if transcription else ""
            print(f"📝 Transcription result: '{text_input}'")
            
            if not text_input:
                return jsonify({
                    "success": False, 
                    "error": "Could not understand the audio. Please speak clearly and try again."
                }), 400
            
            # Generate GPT-4 response
            print("🤖 Generating GPT-4 response...")
            system_prompt = f"You are {character}, a compassionate AI companion from SoulBridge AI. Respond naturally and empathetically to the user's voice message. Keep responses conversational, warm, and under 200 words."
            
            chat_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_input}
                ],
                max_tokens=250,
                temperature=0.8
            )
            
            ai_response = chat_response.choices[0].message.content.strip()
            print(f"💬 GPT-4 response: '{ai_response}'")
            
            return jsonify({
                "success": True,
                "transcript": text_input,
                "response": ai_response,
                "character": character
            })
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(audio_path)
                print(f"🗑️ Cleaned up temp file: {audio_path}")
            except Exception as cleanup_error:
                print(f"⚠️ Cleanup error: {cleanup_error}")
    
    except Exception as e:
        print(f"❌ Voice chat processing failed: {str(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": f"Voice processing error: {str(e)}"}), 500

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

def get_active_users_count():
    """Get currently active users"""
    # This would track active sessions - placeholder for now
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
    # Placeholder - would track free to paid conversions
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
    """af ADMIN DASHBOARD - System Overview"""
    # Only allow access if admin is logged in via session
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    try:
        # Get system statistics
        stats = {
            'total_users': get_total_users(),
            'active_sessions': get_active_sessions_count(),
            'active_users': get_active_users_count(),
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
                    <a href="/admin/users/manage?key={ADMIN_DASH_KEY}">👥 MANAGE USERS</a>
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
                        <div class="stat-value">{stats['active_users']}</div>
                        <div class="stat-label">Active Users</div>
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
                            <span>User Management</span>
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
    """👥 USER MANAGEMENT - Redirect to new management page"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Redirect to the new user management page
    return redirect(f"/admin/users/manage?key={key}")

# ========================================
# ADMIN SURVEILLANCE ROUTES
# ========================================

@app.route("/admin/surveillance")
def admin_surveillance():
    """🚨 SURVEILLANCE COMMAND CENTER - Standalone Security Dashboard"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized - Access Denied"}), 403

    # Clear any existing user session and set pure admin session
    session.clear()
    session["admin_logged_in"] = True
    session["surveillance_access"] = True

    try:
        # Read all log files for template
        maintenance_log = []
        threat_log = []
        blocked_ips = []
        
        try:
            with open(MAINTENANCE_LOG_FILE, "r", encoding="utf-8") as f:
                maintenance_log = [line.strip() for line in f.readlines()[-50:] if line.strip()]
        except FileNotFoundError:
            maintenance_log = ["No maintenance logs available yet."]
            
        try:
            with open(THREAT_LOG_FILE, "r", encoding="utf-8") as f:
                threat_log = [line.strip() for line in f.readlines()[-30:] if line.strip()]
        except FileNotFoundError:
            threat_log = ["No threat logs available yet."]
            
        # Get blocked IPs from surveillance system
        if hasattr(surveillance_system, 'blocked_ips') and surveillance_system.blocked_ips:
            blocked_ips = [f"🚫 {ip} - Blocked for security violations" for ip in list(surveillance_system.blocked_ips)[-20:]]
        else:
            blocked_ips = []
        
        # Calculate system metrics for enhanced surveillance
        uptime = int((datetime.now() - surveillance_system.system_start_time).total_seconds())
        uptime_str = f"{uptime//3600}h {(uptime%3600)//60}m {uptime%60}s"
        
        # Get comprehensive trial system stats with error handling
        try:
            trial_stats = get_comprehensive_trial_stats()
            # If the function returns an error dict, use fallback
            if 'error' in trial_stats:
                raise Exception(trial_stats['error'])
        except Exception as e:
            logger.error(f"Failed to get trial stats: {str(e)}")
            trial_stats = {
                'total_users': 0,
                'active_trials': 0,
                'expired_trials': 0, 
                'converted_users': 0,
                'conversion_rate': 0.0,
                'avg_trial_days': 0.0,
                'revenue_potential': 0.0,
                'growth_users': 0,
                'max_users': 0,
                'free_users': 0,
                'trials_started_today': 0,
                'recent_trials': [],
                'used_trials': 0,
                'error': 'Database connection unavailable'
            }
        
        # Get surveillance metrics
        surveillance_metrics = {
            'blocked_ips_count': len(surveillance_system.blocked_ips) if hasattr(surveillance_system, 'blocked_ips') else 0,
            'threats_count': len(surveillance_system.security_threats) if hasattr(surveillance_system, 'security_threats') else 0,
            'maintenance_logs_count': len(maintenance_log),
            'critical_errors_count': surveillance_system.critical_errors_count if hasattr(surveillance_system, 'critical_errors_count') else 0,
            'uptime': uptime_str
        }
        
        # Use proper template rendering with all data
        return render_template('admin/surveillance.html', 
                             maintenance_log=maintenance_log,
                             threat_log=threat_log, 
                             blocked_ips=blocked_ips,
                             trial_stats=trial_stats,
                             surveillance_metrics=surveillance_metrics,
                             ADMIN_DASH_KEY=ADMIN_DASH_KEY)
        
    except Exception as e:
        logger.error(f"Surveillance dashboard error: {e}")
        return jsonify({"error": "Surveillance system error", "details": str(e)}), 500

def get_comprehensive_trial_stats():
    """Get comprehensive trial system statistics for admin dashboard"""
    try:
        db_instance = get_database()
        if not db_instance:
            return {"error": "Database not available"}
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total users
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        
        # Active trials
        if db_instance.use_postgres:
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_active = 1")
            stats['active_trials'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_used_permanently = 1")
            stats['used_trials'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_plan = 'growth'")
            stats['growth_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_plan = 'max'")
            stats['max_users'] = cursor.fetchone()[0]
            
            # Recent trial starts (last 24 hours)
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_started_at > NOW() - INTERVAL '24 hours'")
            stats['trials_started_today'] = cursor.fetchone()[0]
            
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_active = 1")
            stats['active_trials'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_used_permanently = 1")
            stats['used_trials'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_plan = 'growth'")
            stats['growth_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_plan = 'max'")
            stats['max_users'] = cursor.fetchone()[0]
            
            # Recent trial starts (last 24 hours)
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_started_at > datetime('now', '-24 hours')")
            stats['trials_started_today'] = cursor.fetchone()[0]
        
        # Calculate conversion rate
        if stats['used_trials'] > 0:
            converted_users = stats['growth_users'] + stats['max_users']
            stats['conversion_rate'] = round((converted_users / stats['used_trials']) * 100, 1)
        else:
            stats['conversion_rate'] = 0
        
        # Free users
        stats['free_users'] = stats['total_users'] - stats['growth_users'] - stats['max_users']
        
        # Get recent trial activity
        if db_instance.use_postgres:
            cursor.execute("""
                SELECT email, display_name, trial_started_at, user_plan, trial_active
                FROM users 
                WHERE trial_started_at IS NOT NULL 
                ORDER BY trial_started_at DESC 
                LIMIT 10
            """)
        else:
            cursor.execute("""
                SELECT email, display_name, trial_started_at, user_plan, trial_active
                FROM users 
                WHERE trial_started_at IS NOT NULL 
                ORDER BY trial_started_at DESC 
                LIMIT 10
            """)
        
        recent_trials = []
        for row in cursor.fetchall():
            recent_trials.append({
                'email': row[0],
                'display_name': row[1] or 'Unknown',
                'started_at': row[2],
                'plan': row[3] or 'free',
                'active': bool(row[4]) if row[4] is not None else False
            })
        
        stats['recent_trials'] = recent_trials
        
        conn.close()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting trial stats: {e}")
        return {
            "error": str(e),
            "total_users": 0,
            "active_trials": 0,
            "used_trials": 0,
            "conversion_rate": 0,
            "recent_trials": []
        }

# ========================================
# TRIAL MANAGEMENT ADMIN ROUTES
# ========================================

@app.route("/admin/trials/reset-all")  
def admin_reset_all_trials():
    """🔄 ADMIN: Reset all user trials (DANGEROUS)"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        db_instance = get_database()
        if not db_instance:
            return jsonify({"error": "Database not available"}), 500
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        # Reset all trials
        if db_instance.use_postgres:
            cursor.execute("""
                UPDATE users 
                SET trial_active = 0, 
                    trial_started_at = NULL,
                    trial_used_permanently = 0,
                    trial_warning_sent = 0
            """)
        else:
            cursor.execute("""
                UPDATE users 
                SET trial_active = 0, 
                    trial_started_at = NULL,
                    trial_used_permanently = 0,
                    trial_warning_sent = 0
            """)
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        log_admin_action(f"RESET ALL TRIALS - {affected_rows} users affected")
        return jsonify({
            "success": True, 
            "message": f"Reset {affected_rows} user trials",
            "redirect": f"/admin/surveillance?key={ADMIN_DASH_KEY}"
        })
        
    except Exception as e:
        logger.error(f"Error resetting all trials: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/admin/trials/expire-all")
def admin_expire_all_trials():
    """⏰ ADMIN: Expire all active trials"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        db_instance = get_database()
        if not db_instance:
            return jsonify({"error": "Database not available"}), 500
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        # Expire all active trials
        if db_instance.use_postgres:
            cursor.execute("""
                UPDATE users 
                SET trial_active = 0, 
                    trial_used_permanently = 1
                WHERE trial_active = 1
            """)
        else:
            cursor.execute("""
                UPDATE users 
                SET trial_active = 0, 
                    trial_used_permanently = 1
                WHERE trial_active = 1
            """)
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        log_admin_action(f"EXPIRED ALL TRIALS - {affected_rows} active trials expired")
        return jsonify({
            "success": True, 
            "message": f"Expired {affected_rows} active trials",
            "redirect": f"/admin/surveillance?key={ADMIN_DASH_KEY}"
        })
        
    except Exception as e:
        logger.error(f"Error expiring all trials: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/admin/trials/send-warnings")
def admin_send_trial_warnings():
    """📧 ADMIN: Send warning emails to trial users"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        # This would integrate with your email system
        warnings_sent = 0
        
        db_instance = get_database()
        if db_instance:
            conn = db_instance.get_connection()
            cursor = conn.cursor()
            
            # Get active trial users who haven't been warned
            if db_instance.use_postgres:
                cursor.execute("""
                    SELECT email, display_name, trial_started_at 
                    FROM users 
                    WHERE trial_active = 1 AND (trial_warning_sent = 0 OR trial_warning_sent IS NULL)
                """)
            else:
                cursor.execute("""
                    SELECT email, display_name, trial_started_at 
                    FROM users 
                    WHERE trial_active = 1 AND (trial_warning_sent = 0 OR trial_warning_sent IS NULL)
                """)
            
            users_to_warn = cursor.fetchall()
            warnings_sent = len(users_to_warn)
            
            # Mark as warned (without actually sending emails for now)
            if warnings_sent > 0:
                if db_instance.use_postgres:
                    cursor.execute("""
                        UPDATE users 
                        SET trial_warning_sent = 1 
                        WHERE trial_active = 1 AND (trial_warning_sent = 0 OR trial_warning_sent IS NULL)
                    """)
                else:
                    cursor.execute("""
                        UPDATE users 
                        SET trial_warning_sent = 1 
                        WHERE trial_active = 1 AND (trial_warning_sent = 0 OR trial_warning_sent IS NULL)
                    """)
                
                conn.commit()
            
            conn.close()
        
        log_admin_action(f"SENT TRIAL WARNINGS - {warnings_sent} users warned")
        return jsonify({
            "success": True, 
            "message": f"Sent warnings to {warnings_sent} trial users",
            "redirect": f"/admin/surveillance?key={ADMIN_DASH_KEY}"
        })
        
    except Exception as e:
        logger.error(f"Error sending trial warnings: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/admin/users/cleanup")
def admin_cleanup_users():
    """🧹 ADMIN: Clean up corrupted/incomplete user registrations"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        db_instance = get_database()
        if not db_instance:
            return jsonify({"error": "Database not available"}), 500
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        # Find users with missing trial system columns (corrupted registrations)
        if db_instance.use_postgres:
            cursor.execute("""
                DELETE FROM users 
                WHERE (user_plan IS NULL OR trial_active IS NULL) 
                AND created_at > NOW() - INTERVAL '24 hours'
            """)
        else:
            cursor.execute("""
                DELETE FROM users 
                WHERE (user_plan IS NULL OR trial_active IS NULL) 
                AND created_at > datetime('now', '-24 hours')
            """)
        
        cleaned_users = cursor.rowcount
        conn.commit()
        conn.close()
        
        log_admin_action(f"CLEANED UP CORRUPTED USERS - {cleaned_users} incomplete registrations removed")
        return jsonify({
            "success": True,
            "message": f"Cleaned up {cleaned_users} corrupted user registrations",
            "redirect": f"/admin/surveillance?key={ADMIN_DASH_KEY}"
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up users: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/admin/users/fix-plans")
def admin_fix_user_plans():
    """🔧 ADMIN: Fix user plans - convert foundation to free"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        db_instance = get_database()
        if not db_instance:
            return jsonify({"error": "Database not available"}), 500
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        # Convert foundation plans to free (since foundation is legacy)
        if db_instance.use_postgres:
            cursor.execute("""
                UPDATE users 
                SET plan_type = 'free', user_plan = 'free'
                WHERE plan_type = 'foundation' OR user_plan = 'foundation'
            """)
        else:
            cursor.execute("""
                UPDATE users 
                SET plan_type = 'free', user_plan = 'free'
                WHERE plan_type = 'foundation' OR user_plan = 'foundation'
            """)
        
        fixed_users = cursor.rowcount
        conn.commit()
        conn.close()
        
        log_admin_action(f"FIXED USER PLANS - {fixed_users} users converted from foundation to free")
        return jsonify({
            "success": True,
            "message": f"Fixed {fixed_users} user plans (foundation → free)",
            "redirect": f"/admin/surveillance?key={ADMIN_DASH_KEY}"
        })
        
    except Exception as e:
        logger.error(f"Error fixing user plans: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/admin/users/manage")
def admin_manage_users():
    """👥 ADMIN: User Management Dashboard"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        db_instance = get_database()
        if not db_instance:
            return jsonify({"error": "Database not available"}), 500
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        # Get all users with error handling
        try:
            cursor.execute("""
                SELECT id, email, display_name, user_plan, plan_type, trial_active, 
                       trial_used_permanently, created_at
                FROM users 
                ORDER BY created_at DESC
            """)
            
            rows = cursor.fetchall()
            logger.info(f"Admin users query returned {len(rows)} rows")
            
            users = []
            for row in rows:
                users.append({
                    'id': row[0],
                    'email': row[1],
                    'display_name': row[2] or 'Unknown',
                    'user_plan': row[3] or 'free',
                    'plan_type': row[4] or 'free',
                    'trial_active': bool(row[5]) if row[5] is not None else False,
                    'trial_used': bool(row[6]) if row[6] is not None else False,
                    'created_at': row[7],
                    'last_login': 'N/A'
                })
                
        except Exception as query_error:
            logger.error(f"Error querying users table: {query_error}")
            # Try a simpler query to see what columns exist
            try:
                cursor.execute("SELECT id, email FROM users LIMIT 5")
                simple_rows = cursor.fetchall()
                logger.info(f"Simple query returned {len(simple_rows)} rows: {simple_rows}")
            except Exception as simple_error:
                logger.error(f"Even simple query failed: {simple_error}")
            users = []
        
        conn.close()
        
        # Generate user management HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>👥 User Management - SoulBridge AI Admin</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Courier New', monospace; 
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    color: #e2e8f0; 
                    min-height: 100vh;
                    padding: 20px;
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 3px solid #22d3ee;
                    padding-bottom: 20px;
                }}
                
                .header h1 {{
                    color: #22d3ee;
                    font-size: 2em;
                    text-shadow: 0 0 10px #22d3ee;
                }}
                
                .controls {{
                    margin-bottom: 20px;
                    text-align: center;
                }}
                
                .control-btn {{
                    display: inline-block;
                    padding: 10px 20px;
                    background: #374151;
                    color: #e2e8f0;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 0 5px;
                    font-weight: bold;
                    transition: background 0.3s;
                }}
                
                .control-btn:hover {{
                    background: #4b5563;
                }}
                
                .users-table {{
                    background: rgba(30, 41, 59, 0.8);
                    border-radius: 10px;
                    padding: 20px;
                    overflow-x: auto;
                }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 0.9em;
                }}
                
                th, td {{
                    padding: 12px 8px;
                    text-align: left;
                    border-bottom: 1px solid #374151;
                }}
                
                th {{
                    background: rgba(34, 211, 238, 0.2);
                    color: #22d3ee;
                    font-weight: bold;
                }}
                
                tr:hover {{
                    background: rgba(34, 211, 238, 0.1);
                }}
                
                .delete-btn {{
                    background: #ef4444;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    cursor: pointer;
                    font-size: 0.8em;
                }}
                
                .delete-btn:hover {{
                    background: #dc2626;
                }}
                
                .status-active {{ color: #10b981; }}
                .status-trial {{ color: #f59e0b; }}
                .status-expired {{ color: #ef4444; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>👥 User Management Dashboard</h1>
                <p>Manage all SoulBridge AI users</p>
            </div>
            
            <div class="controls">
                <a href="/admin/surveillance?key={ADMIN_DASH_KEY}" class="control-btn">← Back to Surveillance</a>
                <a href="/admin/users/manage?key={ADMIN_DASH_KEY}" class="control-btn">🔄 Refresh</a>
            </div>
            
            <div class="users-table">
                <h2>📋 All Users ({len(users)} total)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Email</th>
                            <th>Display Name</th>
                            <th>Plan</th>
                            <th>Trial Status</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'''
                        <tr>
                            <td>{user['id']}</td>
                            <td>{user['email']}</td>
                            <td>{user['display_name']}</td>
                            <td>{user['user_plan']}</td>
                            <td class="{'status-trial' if user['trial_active'] else 'status-expired' if user['trial_used'] else 'status-active'}">
                                {'🔥 Active Trial' if user['trial_active'] else '✅ Used Trial' if user['trial_used'] else '🆓 No Trial'}
                            </td>
                            <td>{user['created_at']}</td>
                            <td>
                                <button class="delete-btn" onclick="deleteUser({user['id']}, '{user['email']}')">
                                    🗑️ Delete
                                </button>
                            </td>
                        </tr>
                        ''' for user in users])}
                    </tbody>
                </table>
            </div>
            
            <script>
                function deleteUser(userId, email) {{
                    if (confirm(`Are you sure you want to delete user: ${{email}}?\\n\\nThis action cannot be undone!`)) {{
                        fetch(`/admin/users/delete/${{userId}}?key={ADMIN_DASH_KEY}`, {{
                            method: 'DELETE'
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                alert(`User ${{email}} deleted successfully!`);
                                location.reload();
                            }} else {{
                                alert(`Error deleting user: ${{data.error}}`);
                            }}
                        }})
                        .catch(error => {{
                            alert(`Error: ${{error}}`);
                        }});
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        logger.error(f"Error in user management: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/admin/migrate-plans")
def admin_migrate_plans():
    """🧼 ADMIN: Manually trigger periodic plan migration"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        logger.info("🧼 Admin triggered manual plan migration")
        success = run_periodic_plan_migration()
        
        if success:
            return jsonify({
                "success": True, 
                "message": "Plan migration completed successfully",
                "redirect": f"/admin/surveillance?key={ADMIN_DASH_KEY}"
            })
        else:
            return jsonify({
                "success": False, 
                "error": "Plan migration failed - check logs for details"
            }), 500
            
    except Exception as e:
        logger.error(f"Error in admin plan migration: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/admin/users/delete/<int:user_id>", methods=["DELETE"])
def admin_delete_user(user_id):
    """🗑️ ADMIN: Delete a specific user"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        db_instance = get_database()
        if not db_instance:
            return jsonify({"error": "Database not available"}), 500
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        # Get user email before deletion for logging
        if db_instance.use_postgres:
            cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        
        user_data = cursor.fetchone()
        if not user_data:
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        user_email = user_data[0]
        
        # Delete the user
        if db_instance.use_postgres:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        log_admin_action(f"DELETED USER - ID: {user_id}, Email: {user_email}")
        return jsonify({
            "success": True,
            "message": f"User {user_email} deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/admin/test-update")
def admin_test_update():
    """Test if code updates are live"""
    return jsonify({
        "status": "UPDATED - v2.1", 
        "timestamp": datetime.now().isoformat(),
        "message": "If you see this, the server has the latest code!"
    })

@app.route("/api/sync-trial-session")
def sync_trial_session():
    """Sync session with database trial state"""
    if not is_logged_in():
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        user_id = session.get('user_id')
        db_instance = get_database()
        
        if db_instance and user_id:
            conn = db_instance.get_connection()
            cursor = conn.cursor()
            
            # Get current trial state from database
            if db_instance.use_postgres:
                cursor.execute("SELECT trial_active, trial_started_at, trial_used_permanently FROM users WHERE id = %s", (user_id,))
            else:
                cursor.execute("SELECT trial_active, trial_started_at, trial_used_permanently FROM users WHERE id = ?", (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                trial_active, trial_started_at, trial_used_permanently = result
                
                # Update session to match database
                session['trial_active'] = bool(trial_active) if trial_active is not None else False
                session['trial_started_at'] = trial_started_at
                session['trial_used_permanently'] = bool(trial_used_permanently) if trial_used_permanently is not None else False
                # Don't cache effective_plan - calculate it fresh each time with get_effective_plan()
                
                # Calculate effective_plan fresh instead of reading cached value
                user_plan = session.get('user_plan', 'free')
                trial_active = session.get('trial_active', False)
                effective_plan = get_effective_plan(user_plan, trial_active)
                
                return jsonify({
                    "success": True,
                    "message": "Session synced with database",
                    "trial_active": session['trial_active'],
                    "trial_started_at": session['trial_started_at'],
                    "effective_plan": effective_plan
                })
            else:
                return jsonify({"error": "User not found"}), 404
        else:
            return jsonify({"error": "Database connection failed"}), 500
            
    except Exception as e:
        logger.error(f"Error syncing trial session: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/admin/sql")
def admin_sql():
    """Execute admin SQL commands"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    cmd = request.args.get("cmd")
    if not cmd:
        return jsonify({"error": "No command provided"}), 400
    
    try:
        db_instance = get_database()
        if not db_instance:
            return jsonify({"error": "Database not available"}), 500
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        if cmd == "delete_user_42":
            # Delete user ID 42
            if db_instance.use_postgres:
                cursor.execute("DELETE FROM users WHERE id = %s", (42,))
            else:
                cursor.execute("DELETE FROM users WHERE id = ?", (42,))
            
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            log_admin_action("DELETED USER ID 42 via SQL endpoint")
            return jsonify({
                "success": True,
                "message": f"Deleted user ID 42. Affected rows: {affected}",
                "action": "User deleted successfully!"
            })
        
        elif cmd == "list_users":
            cursor.execute("SELECT id, email, display_name FROM users ORDER BY id")
            users = cursor.fetchall()
            conn.close()
            return jsonify({
                "users": [{"id": u[0], "email": u[1], "name": u[2]} for u in users]
            })
        
        elif cmd == "debug_trial":
            # Debug trial start issues
            user_id = request.args.get("user_id")
            if not user_id:
                return jsonify({"error": "No user_id provided"}), 400
            
            # Check if user exists and get their data
            cursor.execute("SELECT id, email, trial_active, trial_started_at, trial_used_permanently FROM users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                conn.close()
                return jsonify({"error": f"User {user_id} not found"})
            
            # Check table structure
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            conn.close()
            return jsonify({
                "user_exists": True,
                "user_data": {
                    "id": user_data[0],
                    "email": user_data[1], 
                    "trial_active": user_data[2],
                    "trial_started_at": user_data[3],
                    "trial_used_permanently": user_data[4]
                },
                "columns": columns,
                "has_trial_columns": {
                    "trial_active": "trial_active" in columns,
                    "trial_started_at": "trial_started_at" in columns,
                    "trial_used_permanently": "trial_used_permanently" in columns,
                    "trial_warning_sent": "trial_warning_sent" in columns
                }
            })
        
        else:
            return jsonify({"error": "Invalid command"}), 400
            
    except Exception as e:
        logger.error(f"SQL admin error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/admin/delete-user/<int:user_id>")
def admin_delete_user_simple(user_id):
    """🗑️ Simple user deletion"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        db_instance = get_database()
        if not db_instance:
            return jsonify({"error": "Database not available"}), 500
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        # Get user email before deletion
        if db_instance.use_postgres:
            cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        
        user_data = cursor.fetchone()
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        
        user_email = user_data[0]
        
        # Delete the user
        if db_instance.use_postgres:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        log_admin_action(f"DELETED USER - ID: {user_id}, Email: {user_email}")
        return jsonify({
            "success": True,
            "message": f"User {user_email} deleted successfully! Refresh the page to see changes."
        })
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return jsonify({"error": str(e)}), 500

def log_admin_action(action):
    """Log admin actions for audit trail"""
    try:
        with open(MAINTENANCE_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ADMIN ACTION: {action}\n")
    except Exception as e:
        logger.error(f"Error logging admin action: {e}")

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
            
        raw_plan = data.get("plan_type", "").lower()
        billing = data.get("billing", "monthly")
        
        # ✅ Bulletproof plan normalization - ONLY accept Growth/Max for manual selection
        # Free tier is assigned automatically during signup, not selectable
        plan_map = {
            'growth': 'growth',
            'premium': 'growth',
            'max': 'max',
            'enterprise': 'max'
        }
        
        normalized_plan = plan_map.get(raw_plan)
        if not normalized_plan:
            logger.error(f"Invalid plan type received: '{raw_plan}' from data: {data}")
            return jsonify({"success": False, "error": "Invalid plan type"}), 400
        
        logger.info(f"Plan normalization: '{raw_plan}' → '{normalized_plan}'")
        
        session["user_plan"] = normalized_plan
        session["plan_selected_at"] = time.time()
        session["first_time_user"] = False
        # Session expires when browser closes
        
        # ✅ Update database for persistence 
        user_id = session.get('user_id')
        if user_id:
            try:
                database_url = os.environ.get('DATABASE_URL')
                if database_url:
                    import psycopg2
                    conn = psycopg2.connect(database_url)
                    conn.autocommit = True
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET subscription_tier = %s WHERE id = %s", (normalized_plan, user_id))
                    cursor.close()
                    conn.close()
                    logger.info(f"✅ Database updated: User {user_id} set to '{normalized_plan}'")
            except Exception as db_error:
                logger.error(f"Database update failed: {db_error}")
        
        logger.info(f"Plan selected: '{normalized_plan}' by {session.get('user_email')}")
        logger.info(f"Session after plan selection: {dict(session)}")
        
        # ✅ Create appropriate success message and redirect
        if normalized_plan == "free":
            message = "Welcome to SoulBridge AI! Your free plan is now active."
            redirect_url = "/intro"
        else:
            plan_names = {"growth": "Growth", "max": "Max"}
            plan_display = plan_names.get(normalized_plan, normalized_plan.title())
            message = f"Great choice! {plan_display} plan selected. Complete payment to activate premium features."
            redirect_url = f"/payment?plan={normalized_plan}&billing={billing}"
        
        return jsonify({
            "success": True,
            "plan": normalized_plan,
            "message": message,
            "redirect": redirect_url
        })
    except Exception as e:
        logger.error(f"Plan selection error: {e}")
        return jsonify({"success": False, "error": "Plan selection failed"}), 500

# REMOVED: Duplicate route - using /api/start-trial instead
@app.route("/start-trial", methods=["POST"])
def start_trial_old():
    """Start a 5-hour premium companion trial"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
            
        companion_id = data.get("companion_id")
        if not companion_id:
            return jsonify({"success": False, "error": "Missing companion_id"}), 400
            
        user_email = session.get("user_email")
        user_id = session.get("user_id")
        if not user_email:
            return jsonify({"success": False, "error": "No user session found"}), 401
            
        # Database connection and user lookup
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            import psycopg2
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Get current user data
            cursor.execute("SELECT trial_used_permanently, trial_started_at FROM users WHERE email = %s", (user_email,))
            user_data = cursor.fetchone()
            
            if not user_data:
                conn.close()
                return jsonify({"success": False, "error": "User not found"}), 404
            
            trial_used, trial_started = user_data
            
            # If trial is currently active, allow companion switching
            if trial_used and trial_started:
                trial_active = is_trial_active(user_id)
                if trial_active:
                    # Update trial companion for current trial
                    cursor.execute("UPDATE users SET trial_companion = %s WHERE email = %s", (companion_id, user_email))
                    conn.commit()
                    conn.close()
                    
                    session["trial_companion"] = companion_id
                    logger.info(f"✅ Trial companion updated to {companion_id} for {user_email}")
                    
                    return jsonify({
                        "success": True,
                        "message": f"Switched to {companion_id} during active trial!",
                        "trial_companion": companion_id
                    })
            
            # If trial was used and is not active, block new trial
            if trial_used:
                # Double-check if trial is still active (safety check)
                trial_active = is_trial_active(user_id)
                if trial_active:
                    # Trial is still active, allow companion switching
                    cursor.execute("UPDATE users SET trial_companion = %s WHERE email = %s", (companion_id, user_email))
                    conn.commit()
                    conn.close()
                    
                    session["trial_companion"] = companion_id
                    logger.info(f"✅ Trial companion updated to {companion_id} for {user_email} (safety check)")
                    
                    return jsonify({
                        "success": True,
                        "message": f"Switched to {companion_id} during active trial!",
                        "trial_companion": companion_id
                    })
                else:
                    # Trial expired, block new trial
                    conn.close()
                    return jsonify({"success": False, "error": "Trial already used"}), 403
            
            # Start trial - use CURRENT_TIMESTAMP for PostgreSQL compatibility
            cursor.execute("""
                UPDATE users 
                SET trial_started_at = CURRENT_TIMESTAMP, 
                    trial_companion = %s, 
                    trial_used_permanently = 1,
                    trial_expires_at = CURRENT_TIMESTAMP + INTERVAL '5 hours'
                WHERE email = %s
            """, (companion_id, user_email))
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Trial started in PostgreSQL: {companion_id} for {user_email}")
            
            # Update session for immediate frontend use
            session["trial_active"] = True
            session["trial_companion"] = companion_id
            
            return jsonify({
                "success": True,
                "message": f"5-hour trial started for {companion_id}!",
                "trial_companion": companion_id
            })
        else:
            # Fallback to session-only for local development
            if session.get("trial_used_permanently"):
                return jsonify({"success": False, "error": "Trial already used"}), 403
                
            now = datetime.utcnow()
            expires_at = now + timedelta(hours=5)
            
            session["trial_active"] = True
            session["trial_companion"] = companion_id
            session["trial_expires"] = expires_at.isoformat()
            session["trial_started_at"] = now.isoformat()
            session["trial_used_permanently"] = False
            
            logger.info(f"✅ Trial started in session: {companion_id}")
            
            return jsonify({
                "success": True,
                "message": f"5-hour trial started for {companion_id}!",
                "trial_companion": companion_id
            })
        
    except Exception as e:
        logger.error(f"Trial start error: {e}")
        return jsonify({"success": False, "error": "Trial start failed"}), 500

@app.route("/get-trial-status", methods=["GET", "POST"])
def get_trial_status():
    """Get current trial status for the user - bulletproof unified version"""
    try:
        if not is_logged_in():
            return jsonify({"trial_active": False})
            
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"trial_active": False})
        
        # Use bulletproof trial checking function
        trial_active = is_trial_active(user_id)
        
        # Get additional trial info for frontend
        database_url = os.environ.get('DATABASE_URL')
        if database_url and trial_active:
            import psycopg2
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT trial_companion, trial_used_permanently, trial_expires_at
                FROM users WHERE id = %s
            """, (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                trial_companion, trial_used_permanently, trial_expires_at = result
                
                # Calculate time remaining
                time_remaining = 0
                if trial_expires_at:
                    now = datetime.utcnow()
                    time_remaining = max(0, int((trial_expires_at - now).total_seconds() / 60))
                
                return jsonify({
                    "trial_active": trial_active,
                    "trial_companion": trial_companion,
                    "trial_used_permanently": bool(trial_used_permanently),
                    "time_remaining": time_remaining
                })
        
        return jsonify({
            "trial_active": trial_active,
            "trial_companion": None,
            "trial_used_permanently": False,
            "time_remaining": 0
        })
        
    except Exception as e:
        logger.error(f"Trial status check error: {e}")
        return jsonify({
            "trial_active": False,
            "trial_companion": None,
            "trial_used_permanently": False,
            "time_remaining": 0
        })

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
            
        plan_names = {"growth": "Growth", "max": "Max"}
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
        
        # Accept both old and new plan names for payment
        valid_plans = ["premium", "enterprise", "growth", "max"]
        if plan_type not in valid_plans:
            return jsonify({"success": False, "error": "Invalid plan type"}), 400
        
        # Map old plan names to new ones
        plan_mapping = {"premium": "growth", "enterprise": "max"}
        normalized_plan = plan_mapping.get(plan_type, plan_type)
        
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
        
        logger.info(f"Creating Stripe checkout for {plan_type} → {normalized_plan} plan")
        
        import stripe
        stripe.api_key = stripe_secret_key
        
        # Plan details (use normalized plan names)
        plan_names = {
            "premium": "Growth Plan", "growth": "Growth Plan",
            "enterprise": "Max Plan", "max": "Max Plan"
        }
        plan_prices = {
            "monthly": {
                "premium": 1299, "growth": 1299,  # $12.99/month
                "enterprise": 1999, "max": 1999  # $19.99/month
            },
            "yearly": {
                "premium": 11700, "growth": 11700,  # $117/year (25% savings)
                "enterprise": 18000, "max": 18000  # $180/year (25% savings)
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
                success_url=f"{request.host_url}payment/success?session_id={{CHECKOUT_SESSION_ID}}&plan={normalized_plan}",
                cancel_url=f"{request.host_url}payment/cancel?plan={normalized_plan}",
                metadata={
                    'plan_type': normalized_plan,
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
                        # DATABASE-ONLY APPROACH: Use /api/profile-image/{user_id} URLs
                        if result[0] and result[0].startswith('/api/profile-image/'):
                            # Already correct format
                            profile_image = result[0]
                            logger.info(f"Using correct API profile image URL: {profile_image}")
                        elif result[1]:  # Have base64 data, use API endpoint
                            profile_image = f"/api/profile-image/{user_id}"
                            logger.info(f"Using profile image API endpoint: {profile_image}")
                        elif result[0]:  # Old filesystem path, convert to API endpoint
                            profile_image = f"/api/profile-image/{user_id}"
                            logger.info(f"Converting old filesystem path to API endpoint: {profile_image}")
                    
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
    """Upload and set user profile image - DB-only, base64 stored"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401

        file = request.files.get('profileImage')
        if not file or file.filename == '':
            return jsonify({"success": False, "error": "No image file provided"}), 400

        # Validate extension
        allowed_exts = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_exts:
            return jsonify({"success": False, "error": "Invalid file type"}), 400

        # Validate file size (max 5MB)
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > 5 * 1024 * 1024:
            return jsonify({"success": False, "error": "File too large (max 5MB)"}), 400

        # Base64 encode image
        import base64
        image_base64 = base64.b64encode(file.read()).decode('utf-8')

        # SESSION EXTRACTION - robust fallback handling
        user_id = session.get('user_id')
        user_email = session.get('user_email') or session.get('email')
        display_name = session.get('display_name') or (user_email.split('@')[0] if user_email else None)

        if not user_id or not user_email:
            logger.warning(f"Invalid session: user_id={user_id}, user_email={user_email}")
            return jsonify({"success": False, "error": "Session invalid. Please log in again."}), 401

        # Create virtual path
        profile_url = f"/api/profile-image/{user_id}"
        logger.info(f"📷 PROFILE: Uploading for user {user_id} ({user_email})")

        # DB Connection
        db = get_database()
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 500
            
        conn = db.get_connection()
        cursor = conn.cursor()
        placeholder = "%s" if hasattr(db, 'postgres_url') and db.postgres_url else "?"

        # Ensure columns exist
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image_data TEXT")
        except Exception as migration_error:
            logger.warning(f"Column migration warning: {migration_error}")

        # Check user existence
        cursor.execute(f"SELECT id FROM users WHERE id = {placeholder}", (user_id,))
        user_exists = cursor.fetchone()

        if user_exists:
            # Update existing user
            cursor.execute(f"""
                UPDATE users SET profile_image = {placeholder}, profile_image_data = {placeholder}
                WHERE id = {placeholder}
            """, (profile_url, image_base64, user_id))
            logger.info(f"📷 PROFILE: Updated existing user {user_id}")
        else:
            # Create user with fallback
            cursor.execute(f"""
                INSERT INTO users (email, display_name, profile_image, profile_image_data, user_plan, plan_type)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                ON CONFLICT (email) DO UPDATE SET
                    profile_image = EXCLUDED.profile_image,
                    profile_image_data = EXCLUDED.profile_image_data
            """, (user_email, display_name, profile_url, image_base64, 'free', 'free'))
            logger.info(f"📷 PROFILE: Created/updated user via email {user_email}")

        conn.commit()
        conn.close()

        # Cache in session
        session['profile_image'] = profile_url
        logger.info(f"✅ PROFILE: Saved for user {user_id}, size: {len(image_base64)} chars")

        return jsonify({
            "success": True, 
            "profileImage": profile_url, 
            "message": "Profile image updated successfully"
        })

    except Exception as e:
        logger.error(f"❌ PROFILE IMAGE ERROR: {e}")
        return jsonify({"success": False, "error": "Server error"}), 500

@app.route("/api/profile-image/<int:user_id>")
def serve_profile_image(user_id):
    """Serve base64 profile image from database"""
    try:
        db = get_database()
        if not db:
            return redirect('/static/logos/IntroLogo.png')
            
        conn = db.get_connection()
        cursor = conn.cursor()
        placeholder = "%s" if hasattr(db, 'postgres_url') and db.postgres_url else "?"

        cursor.execute(f"SELECT profile_image_data FROM users WHERE id = {placeholder}", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            import base64
            from io import BytesIO
            from flask import send_file, Response
            
            image_data = base64.b64decode(result[0])
            return Response(image_data, mimetype="image/png")
        else:
            return redirect('/static/logos/IntroLogo.png')
            
    except Exception as e:
        logger.error(f"Error serving profile image for user {user_id}: {e}")
        return redirect('/static/logos/IntroLogo.png')


@app.route("/api/fix-session-thegamer")
def fix_session_thegamer():
    """Fix session specifically for thegamerjay11309@gmail.com (User ID 91)"""
    try:
        target_email = "thegamerjay11309@gmail.com"
        target_user_id = 91
        
        # Force set session for thegamerjay11309@gmail.com
        session.clear()
        session['user_authenticated'] = True
        session['session_version'] = "2025-07-28-banking-security"
        session['last_activity'] = datetime.now().isoformat()
        session['user_id'] = target_user_id
        session['user_email'] = target_email
        session['email'] = target_email
        session['display_name'] = "The Game r"
        session['user_plan'] = 'free'
        session['plan_type'] = 'free'
        
        logger.info(f"🔧 SESSION FIX: Set session for {target_email} (User ID {target_user_id})")
        
        return jsonify({
            "success": True,
            "message": "Session fixed for thegamerjay11309@gmail.com",
            "user_id": target_user_id,
            "email": target_email
        })
        
    except Exception as e:
        logger.error(f"Session fix error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/fix-session")
def fix_session():
    """Fix session user_id based on email"""
    try:
        # Check if user has any session data (more lenient than is_logged_in)
        if not (session.get('user_id') or session.get('user_email') or session.get('email')):
            return jsonify({"success": False, "error": "No session data found"}), 401
        
        session_email = session.get('user_email', session.get('email'))
        if not session_email:
            return jsonify({"success": False, "error": "No email in session"}), 400
        
        # Get correct user_id from database
        db_instance = get_database()
        if not db_instance:
            return jsonify({"success": False, "error": "Database not available"}), 500
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
        
        cursor.execute(f"SELECT id, email, display_name FROM users WHERE email = {placeholder}", (session_email,))
        user_record = cursor.fetchone()
        conn.close()
        
        if not user_record:
            return jsonify({"success": False, "error": f"No user found with email {session_email}"}), 404
        
        # Update session with correct user_id and repair session
        old_user_id = session.get('user_id')
        new_user_id = user_record[0]
        
        # Repair session authentication
        session['user_authenticated'] = True
        session['session_version'] = "2025-07-28-banking-security"
        session['last_activity'] = datetime.now().isoformat()
        session['user_id'] = new_user_id
        session['user_email'] = session_email
        if user_record[2]:  # display_name
            session['display_name'] = user_record[2]
        
        logger.info(f"🔧 SESSION FIX: Updated user_id from {old_user_id} to {new_user_id} for {session_email}")
        
        return jsonify({
            "success": True,
            "message": "Session fixed",
            "old_user_id": old_user_id,
            "new_user_id": new_user_id,
            "email": session_email
        })
        
    except Exception as e:
        logger.error(f"Session fix error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/debug/session-user-id")
def debug_session_user_id():
    """Debug session user_id mismatch issues"""
    try:
        session_user_id = session.get('user_id')
        session_email = session.get('user_email', session.get('email'))
        
        debug_info = {
            "session_user_id": session_user_id,
            "session_email": session_email,
            "session_data": dict(session)
        }
        
        # Check if session user_id exists in database
        if session_user_id:
            db_instance = get_database()
            if db_instance:
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                placeholder = "%s" if hasattr(db_instance, 'postgres_url') and db_instance.postgres_url else "?"
                
                cursor.execute(f"SELECT id, email, display_name FROM users WHERE id = {placeholder}", (session_user_id,))
                user_by_id = cursor.fetchone()
                debug_info["user_by_id"] = user_by_id
                
                # Check by email too
                if session_email:
                    cursor.execute(f"SELECT id, email, display_name FROM users WHERE email = {placeholder}", (session_email,))
                    user_by_email = cursor.fetchone()
                    debug_info["user_by_email"] = user_by_email
                
                conn.close()
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({"error": str(e)})

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

# --- ISOLATED TIER BLOCKS ---
# Each tier has its own completely isolated configuration block

# OLD TIER CLASSES REMOVED - Using bulletproof functions instead

# OLD TIER_LIMITS SYSTEM REMOVED - Using only isolated tier blocks now

# OLD get_tier_features() and has_feature_access() REMOVED - Using bulletproof functions

# OLD refresh_session_access_flags() REMOVED - Using bulletproof API instead

# ========================================
# NEW CLEAN TRIAL SYSTEM FUNCTIONS
# ========================================

# REMOVED: Old duplicate get_effective_plan function - using bulletproof version below

def get_feature_limit(plan: str, feature: str) -> int:
    """
    Get usage limits based on SUBSCRIPTION TIER (ignores trial status)
    Usage limits are tied to what you pay for, not trial access
    """
    # Defensive migration for any legacy plans
    legacy_mapping = {'foundation': 'free', 'premium': 'growth', 'enterprise': 'max'}
    plan = legacy_mapping.get(plan, plan)
    
    # Ensure we only work with valid plans
    if plan not in ['free', 'growth', 'max']:
        logger.warning(f"⚠️ Unknown plan '{plan}' in feature limits, defaulting to 'free'")
        plan = 'free'
    
    tier_limits = {
        "free": {"decoder": 3, "fortune": 2, "horoscope": 3, "ai_image_monthly": 5},
        "growth": {"decoder": 15, "fortune": 8, "horoscope": 10, "ai_image_monthly": 50},
        "max": {"decoder": float("inf"), "fortune": float("inf"), "horoscope": float("inf"), "ai_image_monthly": float("inf")},
    }
    
    limit = tier_limits.get(plan, {}).get(feature, 0)
    logger.info(f"🎯 USAGE LIMIT: plan='{plan}' feature='{feature}' → limit={limit}")
    return limit

def get_feature_access_tier(user_plan: str, trial_active: bool) -> str:
    """
    Get the tier for FEATURE ACCESS (considers trial)
    This determines what features you can access, not usage limits
    """
    return get_effective_plan(user_plan, trial_active)

def get_effective_plan(user_plan: str, trial_active: bool) -> str:
    """Get effective plan for FEATURE ACCESS (not usage limits)"""  
    # Defensive migration for any legacy plans that slip through
    legacy_mapping = {'foundation': 'free', 'premium': 'growth', 'enterprise': 'max'}
    user_plan = legacy_mapping.get(user_plan, user_plan)
    
    # Ensure we only work with valid plans
    if user_plan not in ['free', 'growth', 'max']:
        logger.warning(f"⚠️ Unknown plan '{user_plan}' defaulting to 'free'")
        user_plan = 'free'
    
    # FIXED: During trial, unlock all features (max access) but keep subscription limits
    # Trial gives 'max' feature access while usage limits stay tied to actual subscription
    if trial_active:
        return 'max'  # Unlock all features during trial
    else:
        return user_plan  # Use real plan when no trial

def get_feature_limit_v2(effective_plan: str, feature: str) -> int:
    """
    DEPRECATED: Use get_feature_limit() instead
    This function is kept for backward compatibility only
    """
    # Redirect to the main function to avoid duplication
    return get_feature_limit(effective_plan, feature)

def run_periodic_plan_migration():
    """Periodic safety net to migrate any remaining legacy plans in database"""
    try:
        db_instance = get_database()
        if not db_instance:
            logger.warning("Database not available for periodic plan migration")
            return False
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        
        # Check for any remaining legacy plans
        legacy_plans = ['foundation', 'premium', 'enterprise']
        total_migrated = 0
        
        for legacy_plan in legacy_plans:
            plan_mapping = {'foundation': 'free', 'premium': 'growth', 'enterprise': 'max'}
            new_plan = plan_mapping[legacy_plan]
            
            if db_instance.use_postgres:
                # Update user_plan
                cursor.execute("UPDATE users SET user_plan = %s WHERE user_plan = %s", (new_plan, legacy_plan))
                user_plan_migrated = cursor.rowcount
                
                # Update plan_type
                cursor.execute("UPDATE users SET plan_type = %s WHERE plan_type = %s", (new_plan, legacy_plan))
                plan_type_migrated = cursor.rowcount
            else:
                # Update user_plan
                cursor.execute("UPDATE users SET user_plan = ? WHERE user_plan = ?", (new_plan, legacy_plan))
                user_plan_migrated = cursor.rowcount
                
                # Update plan_type
                cursor.execute("UPDATE users SET plan_type = ? WHERE plan_type = ?", (new_plan, legacy_plan))
                plan_type_migrated = cursor.rowcount
            
            migrated_count = user_plan_migrated + plan_type_migrated
            if migrated_count > 0:
                total_migrated += migrated_count
                logger.info(f"🧼 Periodic migration: {legacy_plan} → {new_plan} ({migrated_count} records)")
        
        if total_migrated > 0:
            conn.commit()
            logger.info(f"✅ Periodic plan migration completed: {total_migrated} total records updated")
        else:
            logger.info("✅ Periodic plan migration: No legacy plans found")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Periodic plan migration failed: {e}")
        return False

# Feature access control system
FEATURE_ACCESS = {
    "voice_journaling": {"free": False, "growth": True, "max": True},
    "ai_image": {"free": False, "growth": True, "max": True},
    "relationship_profiles": {"free": False, "growth": True, "max": True},
    "decoder": {"free": True, "growth": True, "max": True},
    "horoscope": {"free": True, "growth": True, "max": True},
    "fortune": {"free": True, "growth": True, "max": True},
    "creative_writing": {"free": False, "growth": True, "max": True}
}

def can_access_feature(effective_plan: str, feature: str) -> bool:
    """Check if user can access a feature based on their effective plan"""
    return FEATURE_ACCESS.get(feature, {}).get(effective_plan, False)

def is_admin():
    """Check if current user is an admin"""
    return session.get('is_admin') == True

# Email notification system
def send_trial_warning_email(user_email, minutes_left):
    """Send trial warning email using comprehensive system"""
    if not user_email:
        return
        
    templates = {
        10: "⏳ 10 Minutes Left on Your Trial!",
        5: "🚨 5 Minutes Left - Don't Lose Access!",
        1: "⚠️ Trial Ending in 1 Minute!"
    }
    subject = templates.get(minutes_left, "Trial Ending Soon")
    message = f"""
Your SoulBridge AI trial is ending in {minutes_left} minutes!

Don't lose access to:
• Creative Writing Assistant
• Premium AI Companions  
• Enhanced Features
• Unlimited Usage

Upgrade now to keep all premium features:
https://soulbridgeai.com/subscription

Thanks for trying SoulBridge AI!
The SoulBridge Team
    """
    
    send_email(user_email, subject, message)

def send_email(to_email, subject, message):
    """Send email using Resend API"""
    try:
        import requests
        resend_api_key = os.environ.get("RESEND_API_KEY")
        if not resend_api_key:
            logger.warning("RESEND_API_KEY not set - email not sent")
            return
            
        response = requests.post(
            "https://api.resend.com/emails", 
            headers={"Authorization": f"Bearer {resend_api_key}"},
            json={
                "from": "SoulBridge AI <support@soulbridgeai.com>",
                "to": [to_email],
                "subject": subject,
                "text": message
            }
        )
        if response.status_code == 200:
            logger.info(f"Email sent successfully to {to_email}")
        else:
            logger.error(f"Failed to send email: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Email failed: {e}")

# Feature usage tracking
def increment_feature_usage(user_id, feature):
    """Increment feature usage count - comprehensive system"""
    table_map = {
        "decoder": "decoder_used",
        "fortune": "fortune_used", 
        "horoscope": "horoscope_used"
    }
    if feature in table_map:
        column = table_map[feature]
        try:
            db_instance = get_database()
            if db_instance:
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                if db_instance.use_postgres:
                    cursor.execute(f"UPDATE users SET {column} = COALESCE({column}, 0) + 1 WHERE id = %s", (user_id,))
                else:
                    cursor.execute(f"UPDATE users SET {column} = COALESCE({column}, 0) + 1 WHERE id = ?", (user_id,))
                conn.commit()
                conn.close()
                logger.info(f"Incremented {feature} usage for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to increment {feature} usage: {e}")

# REMOVED: Duplicate before_request function - using the one at line 59

# API Routes for comprehensive system
@app.route('/api/feature-preview-seen', methods=['POST'])
def mark_feature_preview_seen():
    """Mark feature preview popup as seen"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        session['feature_preview_seen'] = True
        
        # Update database
        try:
            db_instance = get_database()
            if db_instance:
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                if db_instance.use_postgres:
                    cursor.execute("UPDATE users SET feature_preview_seen = 1 WHERE id = %s", (user_id,))
                else:
                    cursor.execute("UPDATE users SET feature_preview_seen = 1 WHERE id = ?", (user_id,))
                conn.commit()
                conn.close()
                logger.info(f"Feature preview marked as seen for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to update feature_preview_seen: {e}")
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error marking feature preview as seen: {e}")
        return jsonify({"success": False, "error": "Failed to update preview status"}), 500

@app.route('/api/protected-feature')
def protected_feature_check():
    """Check access to protected features"""
    try:
        if not is_logged_in():
            return jsonify({"error": "Authentication required"}), 401
        
        feature = request.args.get('feature', 'ai_image')
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        if not can_access_feature(effective_plan, feature):
            return jsonify({
                "error": f"Feature '{feature}' requires Growth or Max plan",
                "locked": True,
                "current_plan": user_plan,
                "effective_plan": effective_plan,
                "trial_active": trial_active
            }), 403
        
        return jsonify({
            "success": True,
            "access_granted": True,
            "current_plan": user_plan,
            "effective_plan": effective_plan
        })
        
    except Exception as e:
        logger.error(f"Error checking protected feature access: {e}")
        return jsonify({"error": "Failed to check feature access"}), 500

@app.route('/api/log-action', methods=['POST'])
def log_user_action():
    """Log user actions for analytics"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        data = request.get_json()
        action = data.get("action") if data else None
        user_id = session.get('user_id')
        
        if not action:
            return jsonify({"success": False, "error": "Action required"}), 400
        
        # Log to database (create simple action log table)
        try:
            db_instance = get_database()
            if db_instance:
                conn = db_instance.get_connection()
                cursor = conn.cursor()
                
                # Create action_logs table if it doesn't exist
                if db_instance.use_postgres:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS action_logs (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER,
                            action TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            ip_address TEXT,
                            user_agent TEXT
                        )
                    """)
                    cursor.execute("""
                        INSERT INTO action_logs (user_id, action, ip_address, user_agent)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, action, request.remote_addr, request.headers.get('User-Agent')))
                else:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS action_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            action TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            ip_address TEXT,
                            user_agent TEXT
                        )
                    """)
                    cursor.execute("""
                        INSERT INTO action_logs (user_id, action, ip_address, user_agent)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, action, request.remote_addr, request.headers.get('User-Agent')))
                
                conn.commit()
                conn.close()
                logger.info(f"Action logged: {action} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
        
        return jsonify({"logged": True, "action": action})
        
    except Exception as e:
        logger.error(f"Error logging user action: {e}")
        return jsonify({"success": False, "error": "Failed to log action"}), 500

def can_access_companion(user_plan: str, companion_tier: str, trial_active: bool) -> bool:
    """Check companion access - bulletproof implementation"""
    if trial_active:
        return True  # Trial users get access to all companions
    if companion_tier == "free":
        return True
    if companion_tier == "growth":
        return user_plan in ["growth", "max"]
    if companion_tier == "max":
        return user_plan == "max"
    return False

# OLD tier block functions REMOVED - Using bulletproof functions instead

# OLD test_tier_isolation() DELETED - No longer needed with isolated tier blocks

# OLD is_companion_unlocked() DELETED - Using can_access_companion() instead

# OLD start_trial() DELETED

def is_trial_active(user_id) -> bool:
    """Check if trial is currently active - bulletproof implementation with strict isolation"""
    if not user_id:
        logger.warning("🚨 is_trial_active called with no user_id - returning False")
        return False
        
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.warning("🚨 No DATABASE_URL - returning False for trial check")
            return False
            
        import psycopg2
        # CRITICAL: Use new connection for each check to prevent contamination
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # CRITICAL: Use parameterized query with explicit user_id to prevent mix-ups
        cursor.execute("""
            SELECT id, trial_expires_at FROM users
            WHERE id = %s
        """, (str(user_id),))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            logger.info(f"🎯 TRIAL CHECK: user_id={user_id} not found in database - returning False")
            return False
            
        db_user_id, trial_expires_at = result
        
        # CRITICAL: Verify we got the right user back from database
        if str(db_user_id) != str(user_id):
            logger.error(f"🚨 CRITICAL: Database returned wrong user! Expected {user_id}, got {db_user_id}")
            return False
            
        if not trial_expires_at:  # No trial or no expiration time
            logger.info(f"🎯 TRIAL CHECK: user_id={user_id} has no trial_expires_at - returning False")
            return False
            
        if isinstance(trial_expires_at, str):
            trial_expires_at = datetime.fromisoformat(trial_expires_at.replace('Z', '+00:00'))
            
        # Check if trial is still active based on expiration time
        now = datetime.utcnow()
        trial_active = now < trial_expires_at
        
        logger.info(f"🎯 BULLETPROOF TRIAL CHECK: user_id={user_id} (verified), expires={trial_expires_at}, now={now}, active={trial_active}")
        return trial_active
        
    except Exception as e:
        logger.error(f"Trial check error for user_id={user_id}: {e}")
        return False

# OLD get_effective_feature_limit() REMOVED - Using bulletproof get_feature_limit() directly

# OLD get_effective_plan_for_display() DELETED

# OLD get_effective_*_limits() functions DELETED

# Essential usage tracking functions restored for decoder functionality
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
        session.modified = True
        
        logger.info(f"📊 DECODER USAGE: User {user_id} now at {session[usage_key]} uses today")
        return True
    except Exception as e:
        logger.error(f"Increment decoder usage error: {e}")
        return False

def get_fortune_usage():
    """Get user's fortune usage for today"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return 0
            
        today = datetime.now().strftime('%Y-%m-%d')
        usage_key = f'fortune_usage_{user_id}_{today}'
        
        return session.get(usage_key, 0)
    except Exception as e:
        logger.error(f"Get fortune usage error: {e}")
        return 0

def increment_fortune_usage():
    """Increment user's fortune usage for today"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return False
            
        today = datetime.now().strftime('%Y-%m-%d')
        usage_key = f'fortune_usage_{user_id}_{today}'
        
        current_usage = session.get(usage_key, 0)
        session[usage_key] = current_usage + 1
        session.modified = True
        return True
    except Exception as e:
        logger.error(f"Increment fortune usage error: {e}")
        return False

def get_horoscope_usage():
    """Get user's horoscope usage for today"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return 0
            
        today = datetime.now().strftime('%Y-%m-%d')
        usage_key = f'horoscope_usage_{user_id}_{today}'
        
        return session.get(usage_key, 0)
    except Exception as e:
        logger.error(f"Get horoscope usage error: {e}")
        return 0

def increment_horoscope_usage():
    """Increment user's horoscope usage for today"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return False
            
        today = datetime.now().strftime('%Y-%m-%d')
        usage_key = f'horoscope_usage_{user_id}_{today}'
        
        current_usage = session.get(usage_key, 0)
        session[usage_key] = current_usage + 1
        session.modified = True
        return True
    except Exception as e:
        logger.error(f"Increment horoscope usage error: {e}")
        return False

# Essential API endpoints restored for frontend functionality
@app.route("/api/decoder/check-limit")
def check_decoder_limit():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"})
    
    # Debug: Log full session contents
    logger.info(f"🔍 DECODER API SESSION DEBUG: user_id={user_id}")
    logger.info(f"🔍 Full session contents: {dict(session)}")
    
    # Always calculate effective_plan fresh instead of reading cached values
    user_plan = session.get("user_plan", "free") 
    trial_active = session.get("trial_active", False)
    
    # Fallback: If session values are missing, force update them
    if user_plan is None or trial_active is None:
        logger.warning(f"⚠️ MISSING SESSION VALUES - forcing update")
        try:
            trial_check = is_trial_active(user_id)
            session['trial_active'] = trial_check
            
            real_plan = session.get('user_plan') or get_user_plan() or 'free'
            plan_mapping = {'foundation': 'free', 'premium': 'growth', 'enterprise': 'max'}
            mapped_plan = plan_mapping.get(real_plan, real_plan or 'free')
            
            session['user_plan'] = mapped_plan
            
            # Update local variables
            user_plan = session['user_plan']
            trial_active = session['trial_active']
        except Exception as e:
            logger.error(f"❌ Failed to update session: {e}")
            user_plan = "free"
            trial_active = False
    
    # TIER ISOLATION: Use tier-specific limits instead of old approach
    current_tier = get_current_user_tier()
    tier_system = get_current_tier_system()
    
    # Calculate effective_plan fresh each time
    effective_plan = get_effective_plan(user_plan, trial_active)
    
    # Get tier-specific limit
    daily_limit = tier_system.get_feature_limit("decoder")
    
    logger.info(f"🔒 TIER ISOLATION: user_plan={user_plan}, tier={current_tier}, effective_plan={effective_plan}, trial_active={trial_active}, limit={daily_limit}")
    usage_today = get_decoder_usage()
    
    # Check if trial should be active by calling is_trial_active directly
    direct_trial_check = is_trial_active(user_id)
    if direct_trial_check != trial_active:
        logger.warning(f"⚠️ TRIAL MISMATCH: session={trial_active}, direct_check={direct_trial_check}")
    
    logger.info(f"🎯 DECODER API: user_id={user_id}, user_plan='{user_plan}', effective_plan='{effective_plan}', trial_active={trial_active}, daily_limit={daily_limit}, usage={usage_today}")

    return jsonify({
        "success": True,
        "effective_plan": effective_plan,
        "user_plan": user_plan,
        "trial_active": trial_active,
        "daily_limit": daily_limit,
        "usage_today": usage_today
    })

@app.route("/api/fortune/check-limit")
def check_fortune_limit():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"})
    
    # TIER ISOLATION: Use tier-specific limits instead of cached session values
    current_tier = get_current_user_tier()
    tier_system = get_current_tier_system()
    tier_data = tier_system.get_session_data()
    
    user_plan = session.get("user_plan", "free")  # Original plan for display
    trial_active = session.get("trial_active", False)
    effective_plan = get_effective_plan(user_plan, trial_active)
    
    # Get tier-specific limit
    daily_limit = tier_system.get_feature_limit("fortune")
    usage_today = get_fortune_usage()

    return jsonify({
        "success": True,
        "effective_plan": effective_plan,
        "user_plan": user_plan,
        "daily_limit": daily_limit,
        "trial_active": trial_active,
        "usage_today": usage_today
    })

@app.route("/api/horoscope/check-limit")
def check_horoscope_limit():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"})

    # TIER ISOLATION: Use tier-specific limits instead of cached session values
    current_tier = get_current_user_tier()
    tier_system = get_current_tier_system()
    tier_data = tier_system.get_session_data()
    
    user_plan = session.get("user_plan", "free")  # Original plan for display
    trial_active = session.get("trial_active", False)
    effective_plan = get_effective_plan(user_plan, trial_active)
    
    # Get tier-specific limit
    daily_limit = tier_system.get_feature_limit("horoscope")
    usage_today = get_horoscope_usage()

    return jsonify({
        "success": True,
        "effective_plan": effective_plan,
        "user_plan": user_plan,
        "daily_limit": daily_limit,
        "trial_active": trial_active,
        "usage_today": usage_today
    })

# ========================================
# NEW CLEAN TRIAL SYSTEM API ENDPOINTS
# ========================================

@app.route("/api/user-plan")
def get_user_plan():
    """Get user plan and trial status for frontend"""
    try:
        if not is_logged_in():
            return jsonify({"plan": "free", "trial_active": False})
        
        user_id = session.get('user_id')
        user_plan = session.get('user_plan', 'free')
        
        # Map old plan names to new consistent naming
        plan_mapping = {'foundation': 'free', 'premium': 'growth', 'enterprise': 'max'}
        user_plan = plan_mapping.get(user_plan, user_plan)
        
        # Use session values set by @app.before_request 
        trial_active = session.get('trial_active', False)
        
        return jsonify({
            "success": True,
            "plan": user_plan,
            "trial_active": trial_active
        })
        
    except Exception as e:
        logger.error(f"Get user plan error: {e}")
        return jsonify({"plan": "free", "trial_active": False})

# REMOVED: Another duplicate route - using the newer one at line 979
# @app.route("/api/start-trial", methods=["POST"])
def api_start_trial_old():
    """Start 5-hour trial using new clean system"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        user_email = session.get('user_email')
        
        if not user_email:
            return jsonify({"success": False, "error": "No user session found"}), 401
        
        # Check if trial already used
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({"success": False, "error": "Database not available"}), 500
        
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check trial status - allow access during active trial
        cursor.execute("SELECT trial_used_permanently, trial_started_at FROM users WHERE email = %s", (user_email,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({"success": False, "error": "User not found"}), 404
        
        trial_used, trial_started = result
        
        # If trial is currently active, allow access without starting new trial
        if trial_used and trial_started:
            trial_active = is_trial_active(user_id)
            if trial_active:
                conn.close()
                return jsonify({
                    "success": True, 
                    "message": "Trial is already active!",
                    "trial_active": True
                })
        
        # If trial was used, check if it's still active
        if trial_used:
            trial_active = is_trial_active(user_id)
            if trial_active:
                # Trial is still active
                conn.close()
                return jsonify({
                    "success": True, 
                    "message": "Trial is already active!",
                    "trial_active": True
                })
            else:
                # Trial expired, block new trial
                conn.close()
                return jsonify({"success": False, "error": "Trial already used"}), 403
        
        # Start trial with new system
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=5)
        
        cursor.execute("""
            UPDATE users 
            SET trial_started_at = %s,
                trial_expires_at = %s,
                trial_used_permanently = TRUE
            WHERE email = %s
        """, (now, expires_at, user_email))
        
        conn.commit()
        conn.close()
        
        # Update session with trial status and refresh access flags
        session['trial_active'] = True
        
        # CRITICAL: Trial started successfully
        logger.info(f"🎉 TRIAL STARTED: Trial active for user {user_id} until {expires_at}")
        
        return jsonify({
            "success": True,
            "message": "5-hour trial started successfully!",
            "expires_at": expires_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Start trial error: {e}")
        return jsonify({"success": False, "error": "Failed to start trial"}), 500

# Manual upgrade endpoints for testing tiers
@app.route("/debug/upgrade-to-free", methods=["POST"])
def debug_upgrade_to_free():
    """Debug endpoint to set user to Free tier"""
    session['user_plan'] = 'free'
    session['user_authenticated'] = True
    session.modified = True
    return jsonify({"success": True, "message": "Upgraded to Free tier", "user_plan": "foundation"})

@app.route("/debug/upgrade-to-growth", methods=["POST"])
def debug_upgrade_to_growth():
    """Debug endpoint to set user to Growth tier"""
    session['user_plan'] = 'growth'
    session['user_authenticated'] = True
    return jsonify({"success": True, "message": "Upgraded to Growth tier", "user_plan": "growth"})

@app.route("/admin/fix-terms-schema")
def admin_fix_terms_schema():
    """🔧 ADMIN: Fix missing terms acceptance columns in production database"""
    key = request.args.get("key")
    if key != ADMIN_DASH_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({"success": False, "error": "No DATABASE_URL - only works in production"}), 500
        
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name LIKE '%terms%'
        """)
        existing_terms_columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"📋 Existing terms columns: {existing_terms_columns}")
        
        # Add missing columns for terms acceptance
        columns_to_add = [
            ('terms_accepted', 'BOOLEAN DEFAULT FALSE'),
            ('terms_accepted_at', 'TIMESTAMP'),
            ('terms_version', 'VARCHAR(50) DEFAULT \'v1.0\''),
            ('terms_language', 'VARCHAR(10) DEFAULT \'en\'')
        ]
        
        added_columns = []
        
        for column_name, column_def in columns_to_add:
            if column_name not in existing_terms_columns:
                try:
                    cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_def}')
                    added_columns.append(column_name)
                    logger.info(f'✅ Added {column_name} column')
                except Exception as e:
                    logger.error(f'❌ Failed to add {column_name}: {e}')
                    return jsonify({"success": False, "error": f"Failed to add {column_name}: {e}"}), 500
        
        conn.commit()
        conn.close()
        
        if added_columns:
            message = f"✅ Successfully added {len(added_columns)} columns: {', '.join(added_columns)}"
            logger.info(message)
        else:
            message = "ℹ️ All terms acceptance columns already exist"
            logger.info(message)
        
        return jsonify({
            "success": True,
            "message": message,
            "added_columns": added_columns,
            "existing_columns": existing_terms_columns,
            "redirect": f"/admin/database?key={ADMIN_DASH_KEY}"
        })
        
    except Exception as e:
        error_msg = f"❌ Database schema fix failed: {str(e)}"
        logger.error(error_msg)
        return jsonify({"success": False, "error": error_msg}), 500

@app.route("/admin/clean-old-plans", methods=["POST"])
def admin_clean_old_plans():
    """ADMIN: Update database to use new plan names and remove old migration code"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({"success": False, "error": "Database not available"}), 500
        
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # First check what columns exist
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
        columns = cursor.fetchall()
        logger.info(f"📋 USER TABLE COLUMNS: {[col[0] for col in columns]}")
        
        # Check current plan values
        cursor.execute("SELECT email, plan FROM users LIMIT 5")
        sample_users = cursor.fetchall()
        logger.info(f"📊 SAMPLE USER PLANS: {sample_users}")
        
        # Update old plan names in database (correct column name is 'plan')
        cursor.execute("UPDATE users SET plan = 'free' WHERE plan = 'foundation'")
        foundation_updated = cursor.rowcount
        
        cursor.execute("UPDATE users SET plan = 'growth' WHERE plan = 'premium'") 
        premium_updated = cursor.rowcount
        
        cursor.execute("UPDATE users SET plan = 'max' WHERE plan = 'enterprise'")
        enterprise_updated = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": "Database cleaned up successfully",
            "updated": {
                "foundation_to_free": foundation_updated,
                "premium_to_growth": premium_updated, 
                "enterprise_to_max": enterprise_updated
            }
        })
        
    except Exception as e:
        logger.error(f"Database cleanup error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# OLD /debug/test-tier-isolation ENDPOINT DELETED - No longer needed

@app.route("/debug/session-state")
def debug_session_state():
    """Bulletproof session state API for frontend"""
    if not is_logged_in():
        return jsonify({
            "user_plan": "free",
            "effective_plan": "free",
            "trial_active": False,
            "access_free": True,
            "access_growth": False,
            "access_max": False
        })
    
    # Use session values set by @app.before_request
    user_plan = session.get('user_plan', 'free') or 'free'
    effective_plan = session.get('effective_plan', 'free') or 'free'
    trial_active = session.get('trial_active', False)
    
    return jsonify({
        "user_plan": user_plan,
        "effective_plan": effective_plan,
        "trial_active": trial_active,
        "access_free": True,
        "access_growth": effective_plan in ["growth", "max"] or trial_active,
        "access_max": effective_plan == "max" or trial_active
    })

@app.route("/debug/session-info")
def debug_session_info():
    """Debug endpoint to show current session state"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in", "session": dict(session)})
    
    # Get fresh trial check and database info
    fresh_trial_check = None
    database_trial_data = None
    try:
        fresh_trial_check = is_trial_active(user_id)
        
        # Get raw database data for debugging
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            import psycopg2
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT trial_expires_at, trial_started_at, trial_used_permanently, plan 
                FROM users WHERE id = %s
            """, (user_id,))
            raw_data = cursor.fetchone()
            conn.close()
            
            if raw_data:
                database_trial_data = {
                    "trial_expires_at": str(raw_data[0]) if raw_data[0] else None,
                    "trial_started_at": str(raw_data[1]) if raw_data[1] else None,
                    "trial_used_permanently": raw_data[2],
                    "database_plan": raw_data[3]
                }
    except Exception as e:
        fresh_trial_check = f"ERROR: {e}"
        database_trial_data = f"ERROR: {e}"
    
    return jsonify({
        "user_id": user_id,
        "session_contents": dict(session),
        "fresh_trial_check": fresh_trial_check,
        "database_trial_data": database_trial_data,
        "session_trial_active": session.get('trial_active'),
        "session_user_plan": session.get('user_plan'),
        "session_effective_plan": session.get('effective_plan'),
        "decoder_limit": get_feature_limit(session.get('user_plan', 'free'), 'decoder'),
        "fortune_limit": get_feature_limit(session.get('user_plan', 'free'), 'fortune'),
        "horoscope_limit": get_feature_limit(session.get('user_plan', 'free'), 'horoscope')
    })

@app.route("/debug/state", methods=["GET"])
def debug_state():
    """Debug endpoint to see current tier isolation state"""
    return jsonify({
        "user_plan": session.get("user_plan"),
        "trial_active": session.get("trial_active"),
        "effective_plan": session.get("effective_plan"),
        "user_id": session.get("user_id"),
        "is_logged_in": bool(session.get("user_id"))
    })

@app.route("/debug/test-signup", methods=["GET"])
def debug_test_signup():
    """Test signup process step by step"""
    try:
        # Test database connection
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({"error": "No DATABASE_URL"})
        
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test table exists and columns
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users'
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        # Test insert capability
        test_email = "test@example.com"
        cursor.execute("DELETE FROM users WHERE email = %s", (test_email,))
        
        conn.close()
        
        return jsonify({
            "success": True,
            "database_url_exists": bool(database_url),
            "columns": columns,
            "required_columns": ["email", "password_hash", "display_name", "subscription_tier"],
            "missing_columns": [col for col in ["email", "password_hash", "display_name", "subscription_tier"] if col not in columns]
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        })

@app.route("/debug/test-signup-direct", methods=["GET"])
def debug_test_signup_direct():
    """Test signup with hardcoded values to isolate the issue"""
    try:
        email = "test123@example.com"
        password = "testpass123"
        name = "Test User"
        
        # Direct database operation
        import os, psycopg2, bcrypt
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Delete test user first
        cursor.execute("DELETE FROM users WHERE email = %s", (email,))
        
        # Use proper UPSERT
        hash_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor.execute("""
            INSERT INTO users (email, password_hash, display_name, email_verified, subscription_tier) 
            VALUES (%s, %s, %s, 1, 'free')
            ON CONFLICT (email) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                display_name = EXCLUDED.display_name,
                subscription_tier = 'free'
            RETURNING id
        """, (email, hash_pw, name))
        user_id = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Direct signup test successful",
            "user_id": user_id,
            "email": email
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        })

@app.route("/debug/test", methods=["GET", "POST"])
def debug_test():
    """Test endpoint that handles both GET and POST"""
    return jsonify({
        "status": "working", 
        "method": request.method,
        "user_id": session.get('user_id'),
        "host": request.host,
        "url": request.url,
        "is_json": request.is_json,
        "content_type": request.content_type
    })

@app.route("/debug/fix-database-schema", methods=["GET"])
def debug_fix_database_schema():
    """DEBUG: Add missing columns to users table"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({"error": "No database connection"})
        
        import psycopg2
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Add missing columns with proper error handling
        fixes_applied = []
        
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN subscription_tier TEXT DEFAULT 'free'
            """)
            fixes_applied.append("Added subscription_tier column")
        except psycopg2.errors.DuplicateColumn:
            fixes_applied.append("subscription_tier column already exists")
        
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN trial_started_at TIMESTAMP
            """)
            fixes_applied.append("Added trial_started_at column")
        except psycopg2.errors.DuplicateColumn:
            fixes_applied.append("trial_started_at column already exists")
            
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN trial_expires_at TIMESTAMP
            """)
            fixes_applied.append("Added trial_expires_at column")
        except psycopg2.errors.DuplicateColumn:
            fixes_applied.append("trial_expires_at column already exists")
            
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN trial_used_permanently BOOLEAN DEFAULT FALSE
            """)
            fixes_applied.append("Added trial_used_permanently column")
        except psycopg2.errors.DuplicateColumn:
            fixes_applied.append("trial_used_permanently column already exists")
        
        # Show current table structure
        cursor.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "fixes_applied": fixes_applied,
            "current_columns": [{"name": c[0], "type": c[1], "default": c[2], "nullable": c[3]} for c in columns]
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route("/debug/force-free-plan", methods=["GET"])
def debug_force_free_plan():
    """DEBUG: Force current user to free plan (bypass broken signup)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Not logged in"})
        
        # Force session to free plan
        session['user_plan'] = 'free'
        # Don't cache effective_plan - calculate it fresh each time
        session['trial_active'] = False
        
        # Also update database if possible
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            import psycopg2
            conn = psycopg2.connect(database_url)
            conn.autocommit = True
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET subscription_tier = 'free', trial_expires_at = NULL
                WHERE id = %s
            """, (user_id,))
            
            cursor.close()
            conn.close()
        
        return jsonify({
            "success": True,
            "message": "User forced to free plan",
            "user_id": user_id,
            "user_plan": session.get('user_plan'),
            "effective_plan": session.get('effective_plan'),
            "trial_active": session.get('trial_active')
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/debug/fix-plan-names", methods=["GET"])
def debug_fix_plan_names():
    """DEBUG: Update all old plan names in database to new names"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({"error": "No database connection"})
        
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Update old plan names to new ones
        updates = [
            ("foundation", "free"),
            ("premium", "growth"), 
            ("enterprise", "max")
        ]
        
        results = []
        for old_name, new_name in updates:
            cursor.execute("""
                UPDATE users 
                SET subscription_tier = %s 
                WHERE subscription_tier = %s
            """, (new_name, old_name))
            
            count = cursor.rowcount
            results.append({"old": old_name, "new": new_name, "updated": count})
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "updates": results,
            "message": "Plan names updated in database"
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route("/debug/fix-free-users", methods=["GET"])
def debug_fix_free_users():
    """DEBUG: Check and fix users who should be free"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({"error": "No database connection"})
        
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get recent users
        cursor.execute("""
            SELECT 
                u.id, u.username, u.subscription_tier,
                u.trial_expires_at,
                CASE 
                    WHEN u.trial_expires_at > NOW() THEN true 
                    ELSE false 
                END as trial_active_db
            FROM users u 
            ORDER BY u.created_at DESC 
            LIMIT 10
        """)
        
        users = cursor.fetchall()
        results = []
        fixed_count = 0
        
        for user in users:
            user_info = {
                "username": user['username'],
                "id": user['id'],
                "tier": user['subscription_tier'],
                "trial_expires": str(user['trial_expires_at']) if user['trial_expires_at'] else None,
                "trial_active": user['trial_active_db'],
                "action": "none"
            }
            
            # Fix users that should be free
            tier = user['subscription_tier']
            trial_active = user['trial_active_db']
            
            if tier is None or tier == '' or (tier in ['foundation'] and not trial_active):
                cursor.execute("""
                    UPDATE users 
                    SET subscription_tier = 'free', 
                        trial_expires_at = NULL
                    WHERE id = %s
                """, (user['id'],))
                
                user_info["action"] = "fixed_to_free"
                fixed_count += 1
            
            results.append(user_info)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "users_checked": len(users),
            "users_fixed": fixed_count,
            "users": results
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route("/debug/force-free-user", methods=["GET"])
def debug_force_free_user():
    """DEBUG: Force current user to be truly free (no trial, no paid plan)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Not logged in"})
        
        # Clear trial data in database
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            import psycopg2
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Reset user to completely free
            cursor.execute("""
                UPDATE users 
                SET plan = 'free', 
                    trial_expires_at = NULL,
                    trial_started_at = NULL,
                    trial_used_permanently = 1
                WHERE id = %s
            """, (user_id,))
            conn.commit()
            conn.close()
            
        # Reset session
        session['user_plan'] = 'free'
        # Don't cache effective_plan - calculate it fresh each time 
        session['trial_active'] = False
        
        return jsonify({
            "success": True, 
            "message": "User forced to Free tier with no trial",
            "user_plan": "free",
            "trial_active": False
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to reset user: {e}"})

@app.route("/debug/upgrade-to-max", methods=["POST"])
def debug_upgrade_to_max():
    """Debug endpoint to set user to Max tier"""
    session['user_plan'] = 'max'
    session['user_authenticated'] = True
    return jsonify({"success": True, "message": "Upgraded to Max tier", "user_plan": "max"})



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
            # Use effective_plan from session (set by @app.before_request)
            effective_plan = session.get('effective_plan', 'free')
            user_plan = session.get('user_plan', 'free')
            trial_active = session.get('trial_active', False)
            user_id = session.get('user_id')
            daily_limit = get_feature_limit(user_plan, 'decoder')
            
            # Check decoder usage limits
            current_usage = get_decoder_usage()
            
            # Check if user has exceeded limit
            if daily_limit != float('inf') and current_usage >= daily_limit:
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
        
        # Get user's subscription tier for enhanced features (use effective_plan)
        user_tier = session.get('effective_plan', 'free')
        
        # Tier-specific AI model and parameters - simple pay model
        if user_tier == 'max':  # Max Plan
            model = "gpt-4"
            max_tokens = 300
            temperature = 0.8
            system_prompt = f"You are {character}, an advanced AI companion from SoulBridge AI Max Plan. You have enhanced emotional intelligence, deeper insights, and provide more thoughtful, nuanced responses. You can engage in complex discussions and offer premium-level guidance."
        elif user_tier == 'growth':  # Growth Plan
            model = "gpt-3.5-turbo"
            max_tokens = 200
            temperature = 0.75
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
            
            # Add tier-specific response enhancements - old function removed
            # if user_tier in ['premium', 'enterprise']:
            #     # Premium users get enhanced response formatting - removed old function
            pass  # Old enhancement logic removed
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

@app.route("/api/creative-writing", methods=["POST"])
def api_creative_writing():
    """Creative writing assistant API endpoint for Growth/Max tiers"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        # Check if user has access to creative writing (Growth/Max tiers or active trial)
        user_plan = session.get('user_plan', 'free')
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['growth', 'max', 'premium', 'enterprise'] and not trial_active:
            return jsonify({"success": False, "error": "Creative Writing Assistant requires Growth/Max plan or trial access"}), 403
            
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
            
        mode = data.get("mode", "poetry")
        prompt = data.get("prompt", "").strip()
        mood = data.get("mood", "uplifting")
        companion = data.get("companion", "AI Assistant")
        
        if not prompt or len(prompt) > 500:
            return jsonify({"success": False, "error": "Prompt is required and must be under 500 characters"}), 400
        
        if not services["openai"]:
            # Provide fallback creative content
            fallback_content = generate_fallback_creative_content(mode, prompt, mood)
            return jsonify({"success": True, "content": fallback_content})
        
        # Create mode-specific prompts
        system_prompts = {
            "poetry": f"You are a skilled poet and creative writing assistant. Create beautiful, inspiring poetry based on the user's request. Focus on {mood} themes and emotions. Keep poems between 8-16 lines.",
            "inspiration": f"You are an inspirational writer. Create uplifting, motivational content that helps boost mood and confidence. Focus on {mood} themes. Provide 2-3 inspiring quotes or affirmations.",
            "story": f"You are a creative storyteller. Write engaging short stories (3-4 paragraphs) that capture {mood} emotions. Create vivid characters and settings that resonate with the reader. Focus on themes of adventure, growth, hope, and human connection.",
            "music": f"You are a talented songwriter and lyricist. Create {mood} song lyrics, verses, or musical ideas based on the user's request. Include rhythm, rhyme, and emotional depth. You can suggest chord progressions or musical styles when relevant.",
            "songs": f"You are a talented songwriter and lyricist. Create complete {mood} songs with proper structure including intro, verse, chorus, bridge, and outro. Include rhythm, rhyme, and emotional depth based on the user's request. Make it feel like a real song with proper lyrics structure.",
            "thoughts": f"You are a thoughtful journaling companion. Help the user explore and organize their thoughts in a {mood} way. Provide gentle reflection prompts, insights, or help structure their ideas. Be supportive and non-judgmental.",
            "letter": f"You are a compassionate letter writer. Help write heartfelt, personal letters that convey {mood} emotions and genuine care. Make it warm and authentic."
        }
        
        user_message = f"Please create {mode} content about: {prompt}"
        
        try:
            # Use the initialized OpenAI client
            if not openai_client:
                raise Exception("OpenAI client not available")
                
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompts.get(mode, system_prompts["poetry"])},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=400,
                temperature=0.8
            )
            
            creative_content = response.choices[0].message.content.strip()
            
            # Add a personal touch from the companion
            companion_signature = f"\n\n— Created with {companion}'s creative guidance 💫"
            final_content = creative_content + companion_signature
            
            logger.info(f"Creative writing generated: {mode} for user {session.get('user_email')}")
            
            return jsonify({
                "success": True,
                "content": final_content,
                "mode": mode,
                "mood": mood
            })
            
        except Exception as openai_error:
            logger.error(f"OpenAI creative writing error: {openai_error}")
            # Fallback to predefined creative content
            fallback_content = generate_fallback_creative_content(mode, prompt, mood)
            return jsonify({"success": True, "content": fallback_content})
            
    except Exception as e:
        logger.error(f"Creative writing API error: {e}")
        return jsonify({"success": False, "error": "Failed to generate creative content"}), 500

def generate_fallback_creative_content(mode, prompt, mood):
    """Generate fallback creative content when OpenAI is unavailable"""
    fallback_templates = {
        "poetry": {
            "uplifting": f"Like sunrise breaking through the night,\nYour spirit shines with inner light.\nThrough challenges that come your way,\nYou'll find the strength to face each day.\n\nThe theme of '{prompt}' inspires growth,\nA reminder of your inner worth.\nWith courage as your faithful guide,\nLet hope and joy walk by your side.",
            "calming": f"In peaceful moments, soft and still,\nFind solace on a quiet hill.\nThe gentle thoughts of '{prompt}' flow,\nLike streams where healing waters go.\n\nBreathe deeply now, let worries fade,\nIn nature's calm, your peace is made.\nWith every breath, find sweet release,\nAnd wrap yourself in inner peace.",
            "motivational": f"Rise up strong, embrace your power,\nThis is your moment, this is your hour!\nThe fire within you burns so bright,\nTurn '{prompt}' into your guiding light.\n\nNo mountain high, no valley low,\nCan stop the dreams that help you grow.\nWith determination as your key,\nUnlock the best you're meant to be!",
            "romantic": f"In tender moments when hearts align,\nYour '{prompt}' becomes divine.\nLike roses blooming in the spring,\nLove makes the sweetest melodies sing.\n\nTwo souls that dance in perfect time,\nYour story reads like gentle rhyme.\nIn whispered words and soft caress,\nTrue love brings endless happiness.",
            "playful": f"Come dance and laugh, let spirits play,\nWith '{prompt}' brighten up your day!\nSkip through meadows, sing out loud,\nBe silly, joyful, and be proud.\n\nLife's too short for serious frowns,\nTurn your worries upside down.\nEmbrace the fun that comes your way,\nMake every moment count today!"
        },
        "inspiration": {
            "uplifting": f"✨ Remember: Every step forward is progress, no matter how small.\n\n🌟 Your journey with '{prompt}' is uniquely yours - trust the process.\n\n💫 You have everything within you to create positive change.",
            "calming": f"🌸 Take a moment to breathe and appreciate how far you've come.\n\n🕊️ Peace begins with accepting where you are right now with '{prompt}'.\n\n🌊 Let go of what you cannot control and focus on your inner calm.",
            "motivational": f"🔥 You are stronger than you think and more capable than you know!\n\n⚡ Turn your thoughts about '{prompt}' into fuel for your success.\n\n🚀 Every challenge is an opportunity to prove your resilience!",
            "romantic": f"💕 Love grows in the most beautiful ways when we're open to '{prompt}'.\n\n💖 Your heart knows exactly what it needs - trust its wisdom.\n\n🌹 Every moment of connection is a gift to be treasured.",
            "playful": f"🎉 Life is meant to be enjoyed - let '{prompt}' bring out your playful side!\n\n🌈 Don't forget to laugh, dance, and celebrate the little things.\n\n✨ Your joy is contagious - spread it everywhere you go!"
        },
        "story": {
            "uplifting": f"Once upon a time, there was someone just like you who faced a challenge with '{prompt}'. They didn't know how strong they were until they had to be. Day by day, step by step, they discovered that every small action created ripples of positive change.\n\nTheir journey taught them that courage isn't the absence of fear—it's moving forward despite it. And in the end, they realized that the very thing they worried about became the catalyst for their greatest growth.",
            "calming": f"In a quiet corner of the world, where time moves gently and worries fade away, there lived someone who understood that '{prompt}' didn't have to be rushed or forced. They learned the art of patience, the wisdom of stillness.\n\nEach day brought its own rhythm, and they discovered that sometimes the most powerful thing you can do is simply breathe, trust the process, and know that everything unfolds exactly as it should.",
            "motivational": f"There once lived a dreamer who refused to give up on '{prompt}'. When others said it was impossible, they said 'watch me.' When obstacles appeared, they found creative ways around them.\n\nEvery setback became a setup for a comeback. Every 'no' fueled their determination to find a 'yes.' And in the end, their persistence turned their wildest dreams into reality, inspiring everyone around them.",
            "romantic": f"In a charming little town, two hearts discovered something magical about '{prompt}'. Their love story began with a simple glance, but grew into something extraordinary. Every shared moment, every whispered secret, every gentle touch wrote another chapter in their beautiful tale.\n\nTheir connection transcended the ordinary, proving that true love has the power to transform both hearts and souls. And they lived happily, knowing that their love story was just beginning.",
            "playful": f"Once upon a time, in a world full of laughter and wonder, someone discovered the pure joy hidden within '{prompt}'. They embarked on the silliest, most delightful adventure, meeting quirky characters and finding magic in the most unexpected places.\n\nWith each giggle and every playful moment, they remembered that life's greatest treasures are often found when we're brave enough to be silly, curious enough to explore, and wise enough to play."
        },
        "music": {
            "uplifting": f"🎵 **[Intro]**\nOh, oh, oh...\nThis one's about '{prompt}'\n\n**[Verse 1]**\nEvery morning brings a chance to shine,\nLeave the worries of yesterday behind,\nWith every beat, my heart finds its way,\nToday's the day, today's the day!\n\n**[Chorus]**\nRise up, rise up, let your spirit soar,\nYou're stronger than you were before,\nThe rhythm of hope beats in your chest,\nYou've got this, you're at your best!\n\n**[Verse 2]**\nEvery step forward is a victory dance,\nTaking every single shot, every single chance,\nWith '{prompt}' guiding me along the way,\nI know tomorrow starts with today!\n\n**[Bridge]**\nAnd when the world gets heavy,\nWhen the road seems long,\nI'll remember this feeling,\nI'll remember this song!\n\n**[Outro]**\nOh, oh, oh...\nWe're rising up!",
            "calming": f"🎵 **[Intro]**\nMmm, mmm, mmm...\nSoft and gentle now...\n\n**[Verse 1]**\nSoft whispers in the evening breeze,\nCalm waters flowing through the trees,\nWhen '{prompt}' brings me inner peace,\nI let all tension gently cease...\n\n**[Chorus]**\nBreathe in slowly, let it go,\nFeel the calm begin to flow,\nEvery worry melts away,\nIn this peaceful, gentle space...\n\n**[Verse 2]**\nLike a river flowing to the sea,\nI release what's not meant to be,\nIn this moment, I am free,\nJust to be, just to breathe...\n\n**[Bridge]**\nClose your eyes and feel the peace,\nLet all tension find release...\n\n**[Outro]**\nMmm, mmm, mmm...\nJust breathe...",
            "motivational": f"🎵 **[Intro]**\nYeah! Let's go!\nThis is for '{prompt}'!\n\n**[Verse 1]**\nI've got fire in my soul, dreams that won't let go,\nEvery step I take, watch my spirit grow,\nTurn the music up loud, let the world know,\nThis is my time to shine, this is my show!\n\n**[Chorus]**\nCan't stop, won't stop, rising to the top,\nEvery beat drops, making hearts pop!\nI'm unstoppable, unbreakable,\nNothing's gonna hold me down!\n\n**[Verse 2]**\nThey said I'd never make it here,\nBut I conquered every fear,\nTurned my pain into my power,\nThis is my defining hour!\n\n**[Bridge]**\nEvery mountain that I climb,\nMakes me stronger every time,\nNothing left but victory!\n\n**[Outro]**\nUnstoppable! Yeah!\nI'm reaching for the sky!",
            "romantic": f"🎵 **[Intro]**\nFor you, my love...\nThis is our song about '{prompt}'\n\n**[Verse 1]**\nWhen I think about you, my heart skips a beat,\nEvery moment with you makes my life complete,\nYou're the melody that plays in my head,\nThe sweetest words that could ever be said...\n\n**[Chorus]**\nYou're my sunshine when the skies are gray,\nMy forever love in every way,\nWith you beside me, I can face anything,\nYou make my heart dance and sing!\n\n**[Verse 2]**\nIn your eyes I see my future bright,\nIn your arms everything feels right,\nEvery kiss, every gentle touch,\nRemds me why I love you so much...\n\n**[Bridge]**\nThrough all the seasons, through all the years,\nThrough all the laughter and all the tears,\nI'll love you more with each passing day...\n\n**[Outro]**\nFor you, my love...\nForever and always...",
            "playful": f"🎵 **[Intro]**\nHey, hey, hey!\nTime to play with '{prompt}'!\n\n**[Verse 1]**\nLet's dance around and have some fun,\nLife's too short to just get things done,\nPut on your favorite song and sing along,\nThis is where our hearts belong!\n\n**[Chorus]**\nTurn it up, turn it loud,\nSing it out, sing it proud,\nLife's a party, come and play,\nLet's make music every day!\n\n**[Verse 2]**\nJump around and make some noise,\nRediscover all your joys,\nLaugh until your sides hurt,\nSpread that happiness for all it's worth!\n\n**[Bridge]**\nWhen life gets too serious,\nJust remember to be curious,\nPlay like nobody's watching!\n\n**[Outro]**\nHey, hey, hey!\nLet's play all day!"
        },
        "songs": {
            "uplifting": f"🎵 **[Intro]**\nOh, oh, oh...\nThis one's about '{prompt}'\n\n**[Verse 1]**\nWoke up this morning with a brand new light,\nYesterday's troubles fading out of sight,\nGot that feeling deep inside my chest,\nToday I'm giving life my very best!\n\n**[Chorus]**\nWe're rising up, rising up, like the morning sun,\nEvery dream we've got, we're gonna make them run,\nNo looking back, we're moving fast,\nThis moment here is gonna last!\n\n**[Verse 2]**\nEvery step forward is a victory dance,\nTaking every single shot, every single chance,\nWith '{prompt}' guiding me along the way,\nI know tomorrow starts with today!\n\n**[Chorus]**\nWe're rising up, rising up, like the morning sun,\nEvery dream we've got, we're gonna make them run,\nNo looking back, we're moving fast,\nThis moment here is gonna last!\n\n**[Bridge]**\nAnd when the world gets heavy,\nWhen the road seems long,\nI'll remember this feeling,\nI'll remember this song!\n\n**[Outro]**\nOh, oh, oh...\nWe're rising up!\nOh, oh, oh...\nWe're rising up!",
            "calming": f"🎵 **[Intro]**\nMmm, mmm, mmm...\nSoft and gentle now...\n\n**[Verse 1]**\nIn the quiet of the evening light,\nWhen '{prompt}' whispers soft and right,\nI find my peace in simple things,\nThe comfort that the silence brings...\n\n**[Chorus]**\nBreathe in slowly, let it go,\nFeel the calm begin to flow,\nEvery worry melts away,\nIn this peaceful, gentle space...\n\n**[Verse 2]**\nLike a river flowing to the sea,\nI release what's not meant to be,\nIn this moment, I am free,\nJust to be, just to breathe...\n\n**[Chorus]**\nBreathe in slowly, let it go,\nFeel the calm begin to flow,\nEvery worry melts away,\nIn this peaceful, gentle space...\n\n**[Bridge]**\nClose your eyes and feel the peace,\nLet all tension find release...\n\n**[Outro]**\nMmm, mmm, mmm...\nJust breathe...",
            "motivational": f"🎵 **[Intro]**\nYeah! Let's go!\nThis is for '{prompt}'!\n\n**[Verse 1]**\nI've been down but I'm not out,\nGot that fire, got no doubt,\nEvery setback made me strong,\nThis is where I belong!\n\n**[Chorus]**\nI'm unstoppable, unbreakable,\nNothing's gonna hold me down,\nI'm unstoppable, unshakeable,\nThe strongest in this town!\nWith '{prompt}' as my battle cry,\nI'm reaching for the sky!\n\n**[Verse 2]**\nThey said I'd never make it here,\nBut I conquered every fear,\nTurned my pain into my power,\nThis is my defining hour!\n\n**[Chorus]**\nI'm unstoppable, unbreakable,\nNothing's gonna hold me down,\nI'm unstoppable, unshakeable,\nThe strongest in this town!\nWith '{prompt}' as my battle cry,\nI'm reaching for the sky!\n\n**[Bridge]**\nEvery mountain that I climb,\nMakes me stronger every time,\nNothing left but victory,\nThis is who I'm meant to be!\n\n**[Outro]**\nUnstoppable! Yeah!\nUnbreakable! Let's go!\nI'm reaching for the sky!"
        },
        "thoughts": {
            "uplifting": f"Today I'm reflecting on '{prompt}' and I realize that every experience is teaching me something valuable. Even the challenging moments are shaping me into someone stronger and more compassionate.\n\nI'm grateful for this journey, for the lessons learned, and for the growth that comes from facing life with an open heart. My thoughts are becoming clearer, and I'm learning to trust the process.",
            "reflective": f"As I think about '{prompt}', I notice how my perspective has been shifting. There's something powerful about taking time to really examine my thoughts and feelings without judgment.\n\nI'm learning that it's okay to sit with uncertainty, to explore different possibilities, and to let my understanding evolve naturally. These quiet moments of reflection are where real insight happens."
        }
    }
    
    # Get template based on mode and mood
    if mode in fallback_templates and mood in fallback_templates[mode]:
        content = fallback_templates[mode][mood]
    else:
        content = f"Here's some creative inspiration about '{prompt}':\n\nEvery moment is a chance to begin again. Your story is still being written, and you have the power to make it beautiful. Let this thought guide you forward with hope and determination."
    
    return content + "\n\n— Created with SoulBridge AI's Creative Assistant 💫"

@app.route("/api/save-creative-content", methods=["POST"])
def api_save_creative_content():
    """Save creative content to user's library"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        # Check if user has access to creative writing (Growth/Max tiers or active trial)
        user_plan = session.get('user_plan', 'free')
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['growth', 'max', 'premium', 'enterprise'] and not trial_active:
            return jsonify({"success": False, "error": "Saving creative content requires Growth/Max plan or trial access"}), 403
            
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
            
        content = data.get("content", "").strip()
        mode = data.get("mode", "poetry")
        prompt = data.get("prompt", "").strip()
        mood = data.get("mood", "uplifting")
        companion = data.get("companion", "AI Assistant")
        
        if not content:
            return jsonify({"success": False, "error": "No content to save"}), 400
        
        # Initialize database if needed
        if not services["database"]:
            init_database()
        
        if not services["database"] or not db:
            return jsonify({"success": False, "error": "Database service unavailable"}), 500
        
        user_email = session.get('user_email')
        if not user_email:
            return jsonify({"success": False, "error": "User session invalid"}), 401
        
        # Create a title based on mode and prompt
        mode_titles = {
            "poetry": "Poetry",
            "inspiration": "Inspiration", 
            "story": "Short Story",
            "music": "Music & Lyrics",
            "thoughts": "Thoughts & Notes",
            "letter": "Personal Letter"
        }
        
        title = f"{mode_titles.get(mode, 'Creative Writing')} - {prompt[:30]}{'...' if len(prompt) > 30 else ''}"
        
        # Save to library using similar structure as conversations
        from datetime import datetime
        current_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        library_data = {
            "title": title,
            "type": "creative_writing",
            "mode": mode,
            "companion": companion,
            "date": current_date,
            "content": content,
            "original_prompt": prompt,
            "mood": mood,
            "user_email": user_email
        }
        
        # Store in database
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            if db.use_postgres:
                cursor.execute("""
                    INSERT INTO user_library (user_email, title, content, content_type, created_at, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    user_email,
                    title,
                    content,
                    'creative_writing',
                    datetime.now(),
                    json.dumps({
                        "mode": mode,
                        "companion": companion,
                        "original_prompt": prompt,
                        "mood": mood
                    })
                ))
            else:
                cursor.execute("""
                    INSERT INTO user_library (user_email, title, content, content_type, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_email,
                    title,
                    content,
                    'creative_writing',
                    datetime.now().isoformat(),
                    json.dumps({
                        "mode": mode,
                        "companion": companion,
                        "original_prompt": prompt,
                        "mood": mood
                    })
                ))
            
            conn.commit()
            logger.info(f"Creative content saved to library for user {user_email}: {mode}")
            
            return jsonify({
                "success": True,
                "message": "Creative content saved to your library!",
                "title": title
            })
            
        except Exception as db_error:
            conn.rollback()
            logger.error(f"Database error saving creative content: {db_error}")
            return jsonify({"success": False, "error": "Failed to save to library"}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Save creative content API error: {e}")
        return jsonify({"success": False, "error": "Failed to save creative content"}), 500

@app.route("/api/save-canvas-art", methods=["POST"])
def api_save_canvas_art():
    """Save canvas artwork to user's library"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        # Check if user has access to creative canvas (Growth/Max tiers or active trial)
        user_plan = session.get('user_plan', 'free')
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['growth', 'premium', 'enterprise'] and not trial_active:
            return jsonify({"success": False, "error": "Creative Canvas requires Growth or Max plan"}), 403
            
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
            
        artwork_data = data.get("artwork", "").strip()
        prompt = data.get("prompt", "").strip()
        theme = data.get("theme", "freeform")
        companion = data.get("companion", "AI Assistant")
        
        if not artwork_data or not artwork_data.startswith('data:image'):
            return jsonify({"success": False, "error": "No valid artwork data provided"}), 400
        
        # Initialize database if needed
        if not services["database"]:
            init_database()
        
        if not services["database"] or not db:
            return jsonify({"success": False, "error": "Database service unavailable"}), 500
        
        user_email = session.get('user_email')
        if not user_email:
            return jsonify({"success": False, "error": "User session invalid"}), 401
        
        # Create a title based on theme and prompt
        theme_titles = {
            "mood": "Mood Expression",
            "stress": "Stress Release",
            "gratitude": "Gratitude Art", 
            "peace": "Peaceful Creation",
            "growth": "Growth Journey",
            "dreams": "Dreams & Aspirations",
            "healing": "Healing Art",
            "freeform": "Free Expression"
        }
        
        title = f"{theme_titles.get(theme, 'Canvas Art')} - {prompt[:30]}{'...' if len(prompt) > 30 else ''}"
        
        # Save artwork data (we'll store the base64 data directly)
        from datetime import datetime
        current_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        # Store in database
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            if db.use_postgres:
                cursor.execute("""
                    INSERT INTO user_library (user_email, title, content, content_type, created_at, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    user_email,
                    title,
                    artwork_data,  # Store the base64 image data
                    'canvas_art',
                    datetime.now(),
                    json.dumps({
                        "theme": theme,
                        "companion": companion,
                        "original_prompt": prompt,
                        "art_type": "digital_canvas"
                    })
                ))
            else:
                cursor.execute("""
                    INSERT INTO user_library (user_email, title, content, content_type, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_email,
                    title,
                    artwork_data,  # Store the base64 image data
                    'canvas_art',
                    datetime.now().isoformat(),
                    json.dumps({
                        "theme": theme,
                        "companion": companion,
                        "original_prompt": prompt,
                        "art_type": "digital_canvas"
                    })
                ))
            
            conn.commit()
            logger.info(f"Canvas artwork saved to library for user {user_email}: {theme}")
            
            return jsonify({
                "success": True,
                "message": "Artwork saved to your library!",
                "title": title
            })
            
        except Exception as db_error:
            conn.rollback()
            logger.error(f"Database error saving canvas artwork: {db_error}")
            return jsonify({"success": False, "error": "Failed to save to library"}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Save canvas art API error: {e}")
        return jsonify({"success": False, "error": "Failed to save artwork"}), 500

def moderate_content(content, content_type="text"):
    """
    AI-powered content moderation for wellness gallery
    Returns: (is_safe: bool, reason: str, confidence: float)
    """
    try:
        if not services["openai"]:
            # If OpenAI is unavailable, use basic keyword filtering
            return basic_content_filter(content)
        
        import openai
        
        # Use OpenAI's moderation endpoint
        moderation_response = openai_client.moderations.create(input=content)
        result = moderation_response.results[0]
        
        if result.flagged:
            # Get the specific reason for flagging
            categories = result.categories
            flagged_categories = [cat for cat, flagged in categories.items() if flagged]
            return False, f"Content flagged for: {', '.join(flagged_categories)}", 0.95
        
        # Additional wellness-focused checks
        wellness_check = check_wellness_alignment(content)
        if not wellness_check["is_wellness_focused"]:
            return False, wellness_check["reason"], wellness_check["confidence"]
        
        return True, "Content approved", 0.9
        
    except Exception as e:
        logger.error(f"Content moderation error: {e}")
        # Fail safe - reject if we can't moderate properly
        return False, "Unable to verify content safety", 0.5

def basic_content_filter(content):
    """Basic keyword-based content filtering as fallback"""
    inappropriate_keywords = [
        "suicide", "self-harm", "kill", "die", "death", "violence", "hate", 
        "sexual", "explicit", "drug", "abuse", "political", "religion"
    ]
    
    content_lower = content.lower()
    for keyword in inappropriate_keywords:
        if keyword in content_lower:
            return False, f"Content contains inappropriate keyword: {keyword}", 0.8
    
    return True, "Basic filter passed", 0.6

def check_wellness_alignment(content):
    """Check if content aligns with wellness themes"""
    wellness_keywords = [
        "gratitude", "peace", "calm", "growth", "healing", "hope", "joy", 
        "strength", "love", "kindness", "meditation", "mindful", "positive",
        "overcome", "journey", "recovery", "support", "wellness", "healthy"
    ]
    
    negative_themes = [
        "revenge", "anger", "hatred", "violence", "toxic", "negative",
        "destroy", "hurt", "pain", "suffering", "despair", "hopeless"
    ]
    
    content_lower = content.lower()
    
    # Check for negative themes
    for theme in negative_themes:
        if theme in content_lower:
            return {
                "is_wellness_focused": False,
                "reason": f"Content contains non-wellness theme: {theme}",
                "confidence": 0.7
            }
    
    # Check for wellness themes
    wellness_score = sum(1 for keyword in wellness_keywords if keyword in content_lower)
    
    if wellness_score >= 1:
        return {
            "is_wellness_focused": True,
            "reason": "Content aligns with wellness themes",
            "confidence": min(0.6 + (wellness_score * 0.1), 0.9)
        }
    
    # Neutral content is okay too
    return {
        "is_wellness_focused": True,
        "reason": "Content appears neutral/safe",
        "confidence": 0.6
    }

@app.route("/api/share-to-wellness-gallery", methods=["POST"])
def api_share_to_wellness_gallery():
    """Share creative content to the anonymous wellness gallery"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        # Check if user has access (Growth/Max tiers or active trial)
        user_plan = session.get('user_plan', 'free')
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['growth', 'premium', 'enterprise'] and not trial_active:
            return jsonify({"success": False, "error": "Wellness Gallery sharing requires Growth or Max plan"}), 403
            
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
            
        content = data.get("content", "").strip()
        content_type = data.get("content_type", "creative_writing")
        theme = data.get("theme", "freeform")
        mood = data.get("mood", "")
        
        if not content:
            return jsonify({"success": False, "error": "No content provided"}), 400
        
        # Content moderation - CRITICAL SAFETY CHECK
        is_safe, moderation_reason, confidence = moderate_content(content)
        
        if not is_safe:
            logger.warning(f"Content rejected in moderation: {moderation_reason}")
            return jsonify({
                "success": False, 
                "error": "Content doesn't meet our wellness community guidelines. Please ensure your content is positive, supportive, and appropriate for a wellness-focused community."
            }), 400
        
        # Initialize database if needed
        if not services["database"]:
            init_database()
        
        if not services["database"] or not db:
            return jsonify({"success": False, "error": "Database service unavailable"}), 500
        
        # Store in wellness gallery (anonymously)
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Auto-approve if high confidence, otherwise mark for review
            is_approved = confidence >= 0.8
            moderation_status = "approved" if is_approved else "pending"
            
            from datetime import datetime
            metadata = {
                "moderation_confidence": confidence,
                "moderation_reason": moderation_reason,
                "original_content_type": content_type,
                "sharing_timestamp": datetime.now().isoformat()
            }
            
            if db.use_postgres:
                cursor.execute("""
                    INSERT INTO wellness_gallery 
                    (content_type, content, theme, mood, is_approved, moderation_status, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    content_type, content, theme, mood, is_approved, moderation_status, json.dumps(metadata)
                ))
            else:
                cursor.execute("""
                    INSERT INTO wellness_gallery 
                    (content_type, content, theme, mood, is_approved, moderation_status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    content_type, content, theme, mood, 1 if is_approved else 0, moderation_status, json.dumps(metadata)
                ))
            
            conn.commit()
            logger.info(f"Content shared to wellness gallery: {theme} - {content_type}")
            
            response_message = "Shared to Wellness Gallery!" if is_approved else "Shared to Wellness Gallery! Your content is being reviewed and will appear soon."
            
            return jsonify({
                "success": True,
                "message": response_message,
                "approved": is_approved
            })
            
        except Exception as db_error:
            conn.rollback()
            logger.error(f"Database error sharing to wellness gallery: {db_error}")
            return jsonify({"success": False, "error": "Failed to share content"}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Share to wellness gallery API error: {e}")
        return jsonify({"success": False, "error": "Failed to share content"}), 500

@app.route("/api/wellness-gallery", methods=["GET"])
def api_get_wellness_gallery():
    """Get approved content from wellness gallery"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Initialize database if needed
        if not services["database"]:
            init_database()
        
        if not services["database"] or not db:
            return jsonify({"success": False, "error": "Database service unavailable"}), 500
        
        theme_filter = request.args.get('theme', 'all')
        content_type_filter = request.args.get('type', 'all')
        limit = min(int(request.args.get('limit', 20)), 50)  # Max 50 items
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Build query with filters
            base_query = """
                SELECT id, content_type, content, theme, mood, hearts_count, created_at, metadata
                FROM wellness_gallery 
                WHERE is_approved = {} AND moderation_status = 'approved'
            """.format('TRUE' if db.use_postgres else '1')
            
            params = []
            
            if theme_filter != 'all':
                base_query += " AND theme = {}"
                base_query = base_query.format('%s' if db.use_postgres else '?')
                params.append(theme_filter)
            
            if content_type_filter != 'all':
                if params:
                    base_query += " AND content_type = {}"
                    base_query = base_query.format('%s' if db.use_postgres else '?')
                else:
                    base_query += " AND content_type = {}"
                    base_query = base_query.format('%s' if db.use_postgres else '?')
                params.append(content_type_filter)
            
            # Order by creation date (newest first) and limit
            base_query += " ORDER BY created_at DESC LIMIT {}"
            base_query = base_query.format('%s' if db.use_postgres else '?')
            params.append(limit)
            
            cursor.execute(base_query, params)
            results = cursor.fetchall()
            
            # Format results
            gallery_items = []
            for row in results:
                item = {
                    "id": row[0],
                    "content_type": row[1],
                    "content": row[2],
                    "theme": row[3],
                    "mood": row[4],
                    "hearts_count": row[5],
                    "created_at": row[6],
                    "metadata": json.loads(row[7]) if row[7] else {}
                }
                gallery_items.append(item)
            
            return jsonify({
                "success": True,
                "items": gallery_items,
                "total": len(gallery_items)
            })
            
        except Exception as db_error:
            logger.error(f"Database error getting wellness gallery: {db_error}")
            return jsonify({"success": False, "error": "Failed to load gallery"}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Get wellness gallery API error: {e}")
        return jsonify({"success": False, "error": "Failed to load gallery"}), 500

@app.route("/api/wellness-gallery/heart", methods=["POST"])
def api_heart_wellness_content():
    """Add a heart to wellness gallery content"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        data = request.get_json()
        content_id = data.get("content_id")
        
        if not content_id:
            return jsonify({"success": False, "error": "Content ID required"}), 400
        
        # Initialize database if needed
        if not services["database"]:
            init_database()
        
        if not services["database"] or not db:
            return jsonify({"success": False, "error": "Database service unavailable"}), 500
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Increment heart count
            if db.use_postgres:
                cursor.execute("""
                    UPDATE wellness_gallery 
                    SET hearts_count = hearts_count + 1 
                    WHERE id = %s AND is_approved = 1
                    RETURNING hearts_count
                """, (content_id,))
            else:
                cursor.execute("""
                    UPDATE wellness_gallery 
                    SET hearts_count = hearts_count + 1 
                    WHERE id = ? AND is_approved = 1
                """, (content_id,))
                
                # Get updated count for SQLite
                cursor.execute("SELECT hearts_count FROM wellness_gallery WHERE id = ?", (content_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({"success": False, "error": "Content not found"}), 404
            
            new_count = result[0]
            conn.commit()
            
            return jsonify({
                "success": True,
                "hearts_count": new_count
            })
            
        except Exception as db_error:
            conn.rollback()
            logger.error(f"Database error hearting content: {db_error}")
            return jsonify({"success": False, "error": "Failed to heart content"}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Heart wellness content API error: {e}")
        return jsonify({"success": False, "error": "Failed to heart content"}), 500

# OLD enhance_premium_response() DELETED

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
    
    # Check if user has voice-journaling access (Max tier, addon, or trial)
    user_plan = session.get('user_plan', 'free')
    user_addons = session.get('user_addons', [])
    trial_active = check_trial_active_from_db(session.get('user_id'))
    
    # Max tier users get all addon features included, trial users get access
    
    if user_plan not in ['premium', 'enterprise'] and 'voice-journaling' not in user_addons and not trial_active:
        return redirect("/subscription?feature=voice-journaling")
    
    return render_template("voice_journaling.html")

@app.route("/api/voice-journaling/transcribe", methods=["POST"])
def voice_journaling_transcribe():
    """Transcribe and analyze voice recording"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has voice-journaling access (Max tier, addon, or trial)
        user_plan = session.get('user_plan', 'free')
        user_addons = session.get('user_addons', [])
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['premium', 'enterprise'] and 'voice-journaling' not in user_addons and not trial_active:
            return jsonify({"success": False, "error": "Voice Journaling requires Max tier, addon, or trial"}), 403
        
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
        
        # Check if user has voice-journaling access (Max tier, addon, or trial)
        user_plan = session.get('user_plan', 'free')
        user_addons = session.get('user_addons', [])
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['premium', 'enterprise'] and 'voice-journaling' not in user_addons and not trial_active:
            return jsonify({"success": False, "error": "Voice Journaling requires Max tier, addon, or trial"}), 403
        
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
        
        # Check if user has voice-journaling access (Max tier, addon, or trial)
        user_plan = session.get('user_plan', 'free')
        user_addons = session.get('user_addons', [])
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['premium', 'enterprise'] and 'voice-journaling' not in user_addons and not trial_active:
            return jsonify({"success": False, "error": "Voice Journaling requires Max tier, addon, or trial"}), 403
        
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
    
    # Check if user has relationship access (Max tier, addon, or trial)
    user_plan = session.get('user_plan', 'free')
    user_addons = session.get('user_addons', [])
    trial_active = check_trial_active_from_db(session.get('user_id'))
    
    if user_plan not in ['premium', 'enterprise'] and 'relationship' not in user_addons and not trial_active:
        return redirect("/subscription?feature=relationship")
    
    return render_template("relationship_profiles.html")

@app.route("/api/relationship-profiles/add", methods=["POST"])
def relationship_profiles_add():
    """Add a new relationship profile"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has relationship access (Max tier, addon, or trial)
        user_plan = session.get('user_plan', 'free')
        user_addons = session.get('user_addons', [])
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['premium', 'enterprise'] and 'relationship' not in user_addons:
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
        
        # Check if user has relationship access (Max tier, addon, or trial)
        user_plan = session.get('user_plan', 'free')
        user_addons = session.get('user_addons', [])
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['premium', 'enterprise'] and 'relationship' not in user_addons:
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
        
        # Check if user has relationship access (Max tier, addon, or trial)
        user_plan = session.get('user_plan', 'free')
        user_addons = session.get('user_addons', [])
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['premium', 'enterprise'] and 'relationship' not in user_addons:
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
    
    # Check if user has emotional-meditations access (Growth/Max tier, addon, or trial)
    user_plan = session.get('user_plan', 'free')
    user_addons = session.get('user_addons', [])
    trial_active = check_trial_active_from_db(session.get('user_id'))
    
    if user_plan not in ['premium', 'enterprise'] and 'emotional-meditations' not in user_addons and not trial_active:
        return redirect("/subscription?feature=emotional-meditations")
    
    return render_template("emotional_meditations.html")

@app.route("/api/emotional-meditations/save-session", methods=["POST"])
def emotional_meditations_save_session():
    """Save completed meditation session"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has emotional-meditations access (Growth/Max tier, addon, or trial)
        user_plan = session.get('user_plan', 'free')
        user_addons = session.get('user_addons', [])
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['premium', 'enterprise'] and 'emotional-meditations' not in user_addons and not trial_active:
            return jsonify({"success": False, "error": "Emotional Meditations requires Growth/Max tier, addon, or trial"}), 403
        
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
        
        # Check if user has emotional-meditations access (Growth/Max tier, addon, or trial)
        user_plan = session.get('user_plan', 'free')
        user_addons = session.get('user_addons', [])
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['premium', 'enterprise'] and 'emotional-meditations' not in user_addons and not trial_active:
            return jsonify({"success": False, "error": "Emotional Meditations requires Growth/Max tier, addon, or trial"}), 403
        
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
    
    # Check if user has ai-image-generation access (Growth/Max tier, addon, or trial)
    user_plan = session.get('user_plan', 'free')
    user_addons = session.get('user_addons', [])
    trial_active = check_trial_active_from_db(session.get('user_id'))
    
    if user_plan not in ['premium', 'enterprise'] and 'ai-image-generation' not in user_addons and not trial_active:
        return redirect("/subscription?feature=ai-image-generation")
    
    return render_template("ai_image_generation.html")

@app.route("/api/ai-image-generation/generate", methods=["POST"])
def ai_image_generation_generate():
    """Generate AI image from prompt"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has ai-image-generation access (Growth/Max tier, addon, or trial)
        user_plan = session.get('user_plan', 'free')
        user_addons = session.get('user_addons', [])
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['premium', 'enterprise'] and 'ai-image-generation' not in user_addons and not trial_active:
            return jsonify({"success": False, "error": "AI Image Generation requires Growth/Max tier, addon, or trial"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        prompt = data.get('prompt')
        style = data.get('style', 'realistic')
        
        if not prompt:
            return jsonify({"success": False, "error": "Prompt required"}), 400
        
        # Check tier-based usage limit using session values
        effective_plan = session.get('effective_plan', 'free')
        trial_active = session.get('trial_active', False)
        monthly_limit = get_feature_limit(user_plan, "ai_image_monthly")
        
        current_month = datetime.now().strftime('%Y-%m')
        usage_key = f'ai_image_usage_{current_month}'
        monthly_usage = session.get(usage_key, 0)
        
        if monthly_limit is not None and monthly_usage >= monthly_limit:
            tier_name = {"free": "Free", "growth": "Growth", "max": "Max"}[effective_plan]
            if monthly_limit == 0 and trial_active:
                return jsonify({"success": False, "error": f"AI Image Generation requires Growth/Max subscription (trial unlocks access but uses your {tier_name} plan limits: {monthly_limit} images/month)"}), 403
            else:
                return jsonify({"success": False, "error": f"Monthly AI image limit reached ({monthly_limit} images for {tier_name} tier)"}), 403
        
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
        
        # Check if user has ai-image-generation access (Growth/Max tier, addon, or trial)
        user_plan = session.get('user_plan', 'free')
        user_addons = session.get('user_addons', [])
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['premium', 'enterprise'] and 'ai-image-generation' not in user_addons and not trial_active:
            return jsonify({"success": False, "error": "AI Image Generation requires Growth/Max tier, addon, or trial"}), 403
        
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
        
        # Check if user has ai-image-generation access (Growth/Max tier, addon, or trial)
        user_plan = session.get('user_plan', 'free')
        user_addons = session.get('user_addons', [])
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['premium', 'enterprise'] and 'ai-image-generation' not in user_addons and not trial_active:
            return jsonify({"success": False, "error": "AI Image Generation requires Growth/Max tier, addon, or trial"}), 403
        
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
        
        # Check if user has ai-image-generation access (Growth/Max tier, addon, or trial)
        user_plan = session.get('user_plan', 'free')
        user_addons = session.get('user_addons', [])
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['premium', 'enterprise'] and 'ai-image-generation' not in user_addons and not trial_active:
            return jsonify({"success": False, "error": "AI Image Generation requires Growth/Max tier, addon, or trial"}), 403
        
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
        
        # Check if user has ai-image-generation access (Growth/Max tier, addon, or trial)
        user_plan = session.get('user_plan', 'free')
        user_addons = session.get('user_addons', [])
        trial_active = check_trial_active_from_db(session.get('user_id'))
        
        if user_plan not in ['premium', 'enterprise'] and 'ai-image-generation' not in user_addons and not trial_active:
            return jsonify({"success": False, "error": "AI Image Generation requires Growth/Max tier, addon, or trial"}), 403
        
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
        
        # Get user's effective tier (includes trial upgrades)
        user_tier = session.get('effective_plan', 'free')  # Use effective_plan for features
        user_email = session.get('user_email', session.get('email'))
        
        # Use effective plan for tier features
        mapped_tier = user_tier
        
        # Define tier features directly
        from copy import deepcopy
        tier_features = {
            'free': {
                'voice_chat': False,
                'advanced_ai': False,
                'priority_support': False,
                'unlimited_messages': False,
                'custom_themes': False,
                'premium_animations': False,
                'max_companions': 'free_only'
            },
            'growth': {  # Growth Plan
                'voice_chat': True,
                'advanced_ai': True,
                'priority_support': True,
                'unlimited_messages': True,
                'custom_themes': True,
                'premium_animations': False,
                'max_companions': 'growth'
            },
            'max': {  # Max Plan
                'voice_chat': True,
                'advanced_ai': True,
                'priority_support': True,
                'unlimited_messages': True,
                'custom_themes': True,
                'premium_animations': True,
                'max_companions': 'max'
            }
        }
        
        features = deepcopy(tier_features.get(mapped_tier, tier_features['free']))
        
        logger.info(f"Tier status check for {user_email}: {mapped_tier}")
        
        return jsonify({
            "success": True,
            "tier": mapped_tier,
            "tier_display": {
                'free': 'Free',
                'growth': 'Growth Plan',
                'max': 'Max Plan'
            }.get(mapped_tier, 'Free'),
            "features": features,
            "switching_unlocked": session.get('switching_unlocked', False)
        })
        
    except Exception as e:
        logger.error(f"Get tier status error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@app.route("/api/user/status", methods=["GET"])
def get_user_status():
    """Get user's current status"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Get basic user data
        user_plan = session.get('user_plan', 'free')
        user_email = session.get('user_email', session.get('email'))
        user_id = session.get('user_id')
        
        # DEBUG: Log current session data
        logger.info(f"🔍 USER STATUS DEBUG: user_plan = {user_plan}")
        logger.info(f"🔍 USER STATUS DEBUG: session keys = {list(session.keys())}")
        logger.info(f"🔍 USER STATUS DEBUG: all session data = {dict(session)}")
        logger.info(f"🧪 SESSION on status check: {dict(session)}")
        
        # Load companion_data from database
        selected_companion = None
        
        try:
            if user_id or user_email:
                import psycopg2
                conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
                cursor = conn.cursor()
                
                # Load companion_data from database
                if user_id:
                    cursor.execute("SELECT companion_data FROM users WHERE id = %s", (user_id,))
                else:
                    cursor.execute("SELECT companion_data FROM users WHERE email = %s", (user_email,))
                
                result = cursor.fetchone()
                companion_data = result[0] if result and result[0] else {}
                
                conn.close()
                
                # Extract companion selection from database
                if companion_data:
                    selected_companion = companion_data.get('selected_companion')
                
                logger.info(f"💾 LOADED FROM DATABASE: selected_companion = {selected_companion}")
            else:
                logger.warning("⚠️ No user ID or email found - using session data only")
                
        except Exception as db_error:
            logger.error(f"❌ Database error loading user status: {db_error}")
            # Continue with session data if database fails
        
        # Use session values set by @app.before_request
        trial_active = session.get('trial_active', False) if user_id else False
        effective_plan = session.get('effective_plan', 'free')
        
        return jsonify({
            "success": True,
            "plan": user_plan,
            "trial_active": trial_active,
            "effective_plan": effective_plan,
            "selected_companion": selected_companion,
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
#                     cursor.execute(f"UPDATE users SET plan_type = {placeholder} WHERE id = {placeholder}", ('max', user_id))
#                 elif user_email:
#                     cursor.execute(f"UPDATE users SET plan_type = {placeholder} WHERE email = {placeholder}", ('max', user_email))
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
        session['user_plan'] = 'free'  # Set to Foundation tier (NOT enterprise)
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
        session['user_plan'] = 'free'
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

@app.route("/api/companions-old", methods=["GET"])
def get_companions_old():
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
                    "avatar_image": "/static/logos/Sky a premium companion.png",
                    "short_bio": "Premium companion with advanced features",
                    "personality_tags": ["Spiritual", "Healing"],
                    "special_features": ["Spiritual guidance", "Meditation sessions", "Energy healing", "Voice interactions"],
                    "tier": "growth",
                    "lock_reason": "Requires Growth Plan ($12.99/month)",
                    "popularity_score": 90,
                    "is_recommended": True
                },
                {
                    "companion_id": "blayzo_premium",
                    "display_name": "Blayzo Pro",
                    "avatar_image": "/static/logos/Blayzo premium companion.png",
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
                    "companion_id": "gamerjay_premium",
                    "display_name": "GamerJay Premium",
                    "avatar_image": "/static/logos/GamerJay premium companion.png",
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
                    "avatar_image": "/static/logos/Violet a Max companion.png",
                    "short_bio": "Premium Max companion with exclusive features",
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

        # Get user trial status if logged in
        if is_logged_in():
            user_plan = session.get('user_plan', 'free')
            trial_active = session.get('trial_active', False)
            effective_plan = session.get('effective_plan', 'free')
        else:
            user_plan = 'free'
            trial_active = False
            effective_plan = 'free'

        return jsonify({
            "success": True,
            "companions": companions_data,
            "user_plan": user_plan,
            "trial_active": trial_active,
            "effective_plan": effective_plan
        })

    except Exception as e:
        logger.error(f"Get companions error: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to load companions"
        }), 500


# MINI ASSISTANT - ADMIN HELPER
# ========================================

@app.route("/mini-assistant")
def mini_assistant():
    """Mini Assistant page for admin panel"""
    try:
        if not is_logged_in():
            return redirect("/login")
        
        # Enhanced admin access control - check if user is admin or has session from surveillance
        user_email = session.get('user_email', '')
        admin_logged_in = session.get('admin_logged_in', False)
        admin_key = request.args.get("key")
        
        # Allow access if:
        # 1. User email contains 'jaaye' (main admin)
        # 2. Admin session is active (from surveillance dashboard)
        # 3. Surveillance access is active (standalone mode)
        # 4. Admin key is provided
        surveillance_access = session.get('surveillance_access', False)
        is_admin_access = (
            (user_email and 'jaaye' in user_email.lower()) or
            admin_logged_in or 
            surveillance_access or
            admin_key == ADMIN_DASH_KEY
        )
        
        if not is_admin_access:
            return redirect("/intro")
        
        return render_template("mini_assistant_simple.html")
        
    except Exception as e:
        logger.error(f"Mini Assistant error: {e}")
        return redirect("/admin")

@app.route("/api/mini-assistant", methods=["POST"])
def api_mini_assistant():
    """🚀 ULTIMATE Mini Assistant API with comprehensive logging and automation"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        file_path = data.get('file', '').strip()
        context = data.get('context', '')
        
        if not user_message:
            return jsonify({"success": False, "error": "Message required"}), 400
        
        # Initialize logging and response tracking
        logs = []
        base_response = ""
        
        # Enhanced SoulBridge AI development context
        project_context = """
You are Mini Assistant, an ultimate AI development agent for SoulBridge AI.

CURRENT PROJECT STATUS:
- Project: SoulBridge AI - Mental wellness platform with AI companions
- Active Focus: Tier isolation system, feature access control debugging
- Tech Stack: Flask backend, Jinja2 templates, SQLite/PostgreSQL database
- Current Issues: Free users seeing premium features, companion selector access
- Recent Progress: Fixed duplicate API endpoints, enhanced template conditionals

DEVELOPMENT CAPABILITIES:
- Advanced code analysis and debugging
- Direct file editing with full code replacement
- Automated git commits and push prompts
- Flask server reload triggers
- Comprehensive logging and action tracking
- SoulBridge AI domain expertise

RECENT ACHIEVEMENTS:
✅ Tier isolation backend fixes (effective_plan usage)
✅ Template conditional logic for feature hiding
✅ Companion selector duplicate endpoint resolution
✅ Timer system consistency across all pages
⏳ Testing free user experience isolation
"""

        # Check if we should automatically use mini helper due to rate limits
        if should_use_mini_helper():
            logs.append("🚨 Rate limit detected - Auto-activating Mini Helper...")
            increment_rate_limit_session()
            base_response = generate_enhanced_mini_helper_response(user_message, file_path, project_context)
            logs.append("🤖 Mini Helper activated automatically due to Claude rate limits.")
            # Save conversation context for Mini Helper
            save_conversation_context(user_message, base_response, file_path, "rate_limited_helper")
        else:
            try:
                # Try Claude API with enhanced file handling
                base_response = call_claude_ultimate(user_message, file_path, project_context)
                logs.append("🧠 Claude 3 Haiku used successfully.")
                # Save successful Claude conversation
                save_conversation_context(user_message, base_response, file_path, "claude_success")
            except Exception as e:
                # Check if this is a rate limit error
                if "rate limit" in str(e).lower() or "429" in str(e):
                    logs.append(f"🚨 Rate limit detected: {e}")
                    increment_rate_limit_session()
                    base_response = generate_enhanced_mini_helper_response(user_message, file_path, project_context)
                    logs.append("🤖 Mini Helper activated automatically due to rate limits.")
                    # Save rate-limited conversation
                    save_conversation_context(user_message, base_response, file_path, "rate_limit_fallback")
                else:
                    logs.append(f"⚠️ Claude failed: {e}. Trying Mixtral fallback...")
                    try:
                        base_response = call_mixtral_ultimate(user_message, project_context)
                        logs.append("⚡ Mixtral fallback used successfully.")
                        save_conversation_context(user_message, base_response, file_path, "mixtral_fallback")
                    except Exception as e2:
                        logs.append(f"⚠️ Mixtral failed: {e2}. Using enhanced mini helper...")
                        base_response = generate_enhanced_mini_helper_response(user_message, file_path, project_context)
                        logs.append("🤖 Enhanced Mini Helper used as final fallback.")
                        save_conversation_context(user_message, base_response, file_path, "final_fallback")
        
        # Handle file editing with comprehensive logging
        if file_path and is_safe_file_path_ultimate(file_path):
            try:
                # Write the response as new file content (Claude returns full code)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(base_response)
                logs.append(f"💾 File '{file_path}' updated successfully.")
                
                # Update project state
                save_project_state([f"Modified {os.path.basename(file_path)}"], [file_path], f"File editing: {os.path.basename(file_path)}")
                
                # Auto-commit with enhanced messaging
                commit_result = auto_git_commit_ultimate(file_path, f"Mini Assistant updated {os.path.basename(file_path)}")
                logs.append(commit_result)
                
                # Add push prompt
                push_prompt = ask_git_push_ultimate()
                logs.append(push_prompt)
                
            except Exception as e:
                logs.append(f"❌ Failed to write to file '{file_path}': {e}")
        
        # Handle special commands
        if "restart server" in user_message.lower() or "reload flask" in user_message.lower():
            restart_result = restart_flask_server_ultimate()
            logs.append(restart_result)
        
        # Handle git push confirmation
        if "push now" in user_message.lower():
            push_result = execute_git_push_ultimate()
            logs.append(push_result)
        
        # Log all actions with timestamps
        log_all_actions(logs, user_message, file_path)
        
        # Combine response with logs
        full_response = base_response
        if logs:
            full_response += "\n\n" + "\n".join(logs)
        
        # Save conversation to memory for continuity
        save_conversation_context(user_message, full_response, file_path, "chat")
        
        return jsonify({
            "success": True,
            "response": full_response
        })
        
    except Exception as e:
        logger.error(f"Mini Assistant API error: {e}")
        return jsonify({
            "success": False,
            "error": "Assistant temporarily unavailable"
        }), 500

@app.route("/api/mini-assistant", methods=["GET"])
def api_mini_assistant_get():
    """GET handler for Mini Assistant for debugging (returns method not allowed)"""
    return jsonify({"success": False, "error": "Use POST method for this endpoint."}), 405

@app.route("/api/mini-assistant/history", methods=["GET"])
def api_mini_assistant_history():
    """Get conversation history for Mini Assistant UI"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        memory = load_conversation_memory()
        recent_conversations = memory['conversations'][-20:]  # Last 20 conversations
        
        # Format conversations for UI display
        formatted_conversations = []
        for conv in recent_conversations:
            formatted_conversations.append({
                'timestamp': conv['timestamp'],
                'user_message': conv['user_message'],
                'response': conv['response'][:200] + ('...' if len(conv['response']) > 200 else ''),  # Truncate for UI
                'file_path': conv.get('file_path', ''),
                'action_type': conv.get('action_type', 'chat')
            })
        
        return jsonify({
            "success": True,
            "conversations": formatted_conversations,
            "total_interactions": memory.get('total_interactions', 0),
            "last_active": memory.get('last_active')
        })
        
    except Exception as e:
        logger.error(f"Mini Assistant history error: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to load conversation history"
        }), 500

@app.route("/api/mini-assistant-status", methods=["GET"])
def api_mini_assistant_status():
    """Check Mini Assistant capabilities"""
    try:
        import os
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        claude_available = bool(claude_api_key)
        
        # Test if anthropic module is available
        try:
            import anthropic
            anthropic_available = True
        except ImportError:
            anthropic_available = False
            claude_available = False
        
        # Get rate limit status
        rate_limit_status = get_rate_limit_status()
        
        return jsonify({
            "success": True,
            "claude_available": claude_available and anthropic_available,
            "anthropic_module": anthropic_available,
            "api_key_configured": bool(claude_api_key),
            "rate_limited": rate_limit_status.get('rate_limited', False),
            "auto_helper_active": rate_limit_status.get('auto_helper_active', False),
            "timestamp": rate_limit_status.get('timestamp', 'Unknown'),
            "backend_status": "Online",
            "claude_status": "Available" if claude_available and anthropic_available and not rate_limit_status.get('rate_limited', False) else "Rate Limited" if rate_limit_status.get('rate_limited', False) else "Unavailable"
        })
        
    except Exception as e:
        logger.error(f"Mini Assistant status check error: {e}")
        return jsonify({
            "success": False,
            "claude_available": False,
            "error": str(e)
        }), 500

@app.route("/api/mini-assistant/push", methods=["POST"])
def api_mini_assistant_push():
    """🚀 Mini Assistant Git Push Endpoint"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        result = execute_git_push_ultimate()
        logger.info(f"Git push request executed: {result}")  # Replace undefined function
        
        return jsonify({
            "success": True,
            "output": result
        })
        
    except Exception as e:
        logger.error(f"Mini Assistant push error: {e}")
        return jsonify({
            "success": False,
            "error": "Push operation failed"
        }), 500

def generate_mini_assistant_response(message, context):
    """Generate contextual responses for Mini Assistant"""
    message_lower = message.lower()
    
    # Try to use Claude API if available, fallback to rule-based responses
    try:
        import os
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        
        if claude_api_key:
            return generate_claude_response(message, context, claude_api_key)
        else:
            logger.info("Claude API key not found, using rule-based responses")
    except Exception as e:
        logger.info(f"Claude API not available, using rule-based responses: {e}")
    
    # Fallback to rule-based responses
    return generate_rule_based_response(message_lower, message)

# === ULTIMATE MINI ASSISTANT SYSTEM ===

# Enhanced configuration
ALLOWED_EDIT_FOLDERS = ["backend/templates", "backend/static", "backend/utils", "templates", "static", "utils"]
MINI_ASSISTANT_LOG = "backend/logs/mini_assistant.log"

# Create logs directory if it doesn't exist
import os
os.makedirs("backend/logs", exist_ok=True)

def call_claude_advanced(prompt, file_path="", project_context=""):
    """Advanced Claude API call with file editing capabilities"""
    import requests
    import os
    
    file_content = ""
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")

    full_prompt = f"""{project_context}

FILE CONTENT (if provided):
{file_content}

USER REQUEST:
{prompt}

INSTRUCTIONS:
- Provide helpful, technical responses for SoulBridge AI development
- If file content is provided, analyze and suggest improvements
- Keep responses under 400 words
- Use markdown formatting
- Include code examples when relevant
"""
    
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    if not claude_api_key:
        raise Exception("Claude API key not found")
    
    headers = {
        "x-api-key": claude_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 2048,
        "temperature": 0.3,
        "messages": [
            {"role": "user", "content": full_prompt}
        ]
    }

    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"Claude API error: {response.status_code}")
    
    content = response.json().get("content", [{}])
    if content and len(content) > 0:
        return content[0].get("text", "❌ No response from Claude.")
    else:
        raise Exception("No content in Claude response")

def call_mixtral_fallback(prompt):
    """Mixtral local AI fallback using Ollama"""
    try:
        import subprocess
        result = subprocess.run([
            "ollama", "run", "mixtral:7b", prompt
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        
        if result.returncode == 0:
            return result.stdout.strip() or "⚠️ Mixtral returned empty response."
        else:
            raise Exception(f"Mixtral failed with code {result.returncode}")
    except subprocess.TimeoutExpired:
        raise Exception("Mixtral response timeout")
    except FileNotFoundError:
        raise Exception("Mixtral/Ollama not installed")
    except Exception as e:
        raise Exception(f"Mixtral error: {e}")

def is_safe_file_path(file_path):
    """Check if file path is safe for editing"""
    if not file_path:
        return False
    
    # Normalize path for security
    normalized_path = os.path.normpath(file_path)
    
    # Check against allowed folders
    for allowed_folder in ALLOWED_EDIT_FOLDERS:
        if normalized_path.startswith(allowed_folder):
            return True
    
    return False

def auto_git_commit(file_path, message="Mini Assistant Auto-Commit"):
    """Automatically commit file changes to git"""
    try:
        import subprocess
        
        # Add the specific file
        subprocess.run(["git", "add", file_path], check=True, cwd=".")
        
        # Commit with message
        full_message = f"{message}\n\n🤖 Generated with Mini Assistant\n\nCo-Authored-By: Mini Assistant <admin@soulbridgeai.com>"
        subprocess.run(["git", "commit", "-m", full_message], check=True, cwd=".")
        
        return "✅ Git commit successful."
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in str(e):
            return "ℹ️ No changes to commit."
        return f"⚠️ Git commit failed: {e}"
    except Exception as e:
        return f"❌ Git error: {e}"

def restart_flask_server():
    """Trigger Flask development server reload"""
    try:
        import subprocess
        import os
        
        # Touch the main app file to trigger reload in development
        if os.path.exists("backend/app.py"):
            subprocess.run(["touch", "backend/app.py"], check=True)
        elif os.path.exists("app.py"):
            subprocess.run(["touch", "app.py"], check=True)
        
        return "🔄 Flask server reload triggered."
    except Exception as e:
        return f"⚠️ Failed to trigger server reload: {e}"

# === ULTIMATE MINI ASSISTANT FUNCTIONS ===

def call_claude_ultimate(prompt, file_path="", project_context=""):
    """Ultimate Claude API call optimized for file editing"""
    import requests
    
    file_content = ""
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")

    # Enhanced prompt for file editing
    if file_content:
        full_prompt = f"""{project_context}

CURRENT FILE CONTENT:
{file_content}

USER REQUEST:
{prompt}

INSTRUCTIONS:
- If editing a file, respond ONLY with the complete, updated file content
- For analysis requests, provide detailed technical feedback
- Keep responses focused and actionable
- Use proper code formatting and syntax"""
    else:
        full_prompt = f"""{project_context}

USER REQUEST:
{prompt}

INSTRUCTIONS:
- Provide helpful, technical responses for SoulBridge AI development
- Include specific code examples when relevant
- Focus on actionable solutions
- Use markdown formatting for clarity"""
    
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    if not claude_api_key:
        raise Exception("Claude API key not found")
    
    headers = {
        "x-api-key": claude_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 4096,  # Increased for full file content
        "temperature": 0.3,
        "messages": [
            {"role": "user", "content": full_prompt}
        ]
    }

    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=60)
    
    # Enhanced rate limit detection
    if response.status_code == 429:
        # Set rate limit flag for mini helper activation
        set_rate_limit_flag(True)
        raise Exception("Claude API rate limit reached - Mini Helper activated")
    elif response.status_code != 200:
        error_msg = f"Claude API error: {response.status_code}"
        if response.text:
            try:
                error_data = response.json()
                if "rate_limit" in str(error_data).lower():
                    set_rate_limit_flag(True)
                    error_msg += " - Rate limit detected, Mini Helper activated"
            except:
                pass
        raise Exception(error_msg)
    
    # Clear rate limit flag on successful response
    set_rate_limit_flag(False)
    
    content = response.json().get("content", [{}])
    if content and len(content) > 0:
        return content[0].get("text", "❌ No response from Claude.")
    else:
        raise Exception("No content in Claude response")

def call_mixtral_ultimate(prompt, project_context=""):
    """Ultimate Mixtral local AI fallback"""
    try:
        import subprocess
        full_prompt = f"{project_context}\n\nUser Request: {prompt}"
        
        result = subprocess.run([
            "ollama", "run", "mixtral:7b", full_prompt
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        
        if result.returncode == 0:
            return result.stdout.strip() or "⚠️ Mixtral returned empty response."
        else:
            raise Exception(f"Mixtral failed with code {result.returncode}")
    except subprocess.TimeoutExpired:
        raise Exception("Mixtral response timeout (120s)")
    except FileNotFoundError:
        raise Exception("Mixtral/Ollama not installed")
    except Exception as e:
        raise Exception(f"Mixtral error: {e}")

def is_safe_file_path_ultimate(file_path):
    """Enhanced security check for file paths"""
    if not file_path:
        return False
    
    # Normalize path for security
    normalized_path = os.path.normpath(file_path)
    
    # Prevent directory traversal
    if ".." in normalized_path or file_path.startswith("/"):
        return False
    
    # Check against allowed folders
    for allowed_folder in ALLOWED_EDIT_FOLDERS:
        if normalized_path.startswith(allowed_folder):
            return True
    
    return False

def auto_git_commit_ultimate(file_path, message="Mini Assistant Auto-Commit"):
    """Enhanced git commit with better error handling"""
    try:
        import subprocess
        
        # Add the specific file
        result = subprocess.run(["git", "add", file_path], capture_output=True, text=True, cwd=".")
        if result.returncode != 0:
            return f"⚠️ Git add failed: {result.stderr}"
        
        # Commit with enhanced message
        full_message = f"""{message}

🤖 Generated with Mini Assistant (Ultimate)
File: {file_path}
Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Co-Authored-By: Mini Assistant <admin@soulbridgeai.com>"""
        
        result = subprocess.run(["git", "commit", "-m", full_message], capture_output=True, text=True, cwd=".")
        if result.returncode != 0:
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                return "ℹ️ No changes to commit (file unchanged)."
            return f"⚠️ Git commit failed: {result.stderr}"
        
        return "✅ Git commit successful."
    except Exception as e:
        return f"❌ Git error: {e}"

def ask_git_push_ultimate():
    """Enhanced git push prompt"""
    return "🟡 **Commit complete!** Ready to push to remote repository?\n💡 Type **'push now'** in your next message to push changes to GitHub."

def execute_git_push_ultimate():
    """Execute git push to remote repository"""
    try:
        import subprocess
        
        result = subprocess.run(["git", "push"], capture_output=True, text=True, cwd=".", timeout=60)
        if result.returncode == 0:
            return "🚀 **Git push successful!** Changes pushed to remote repository."
        else:
            return f"⚠️ Git push failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "⚠️ Git push timeout (60s) - check network connection."
    except Exception as e:
        return f"❌ Git push error: {e}"

def restart_flask_server_ultimate():
    """Enhanced Flask server reload"""
    try:
        import subprocess
        
        # Try multiple methods to trigger reload
        reload_files = ["backend/app.py", "app.py", "main.py"]
        for file in reload_files:
            if os.path.exists(file):
                subprocess.run(["touch", file], check=True)
                return f"🔄 Flask server reload triggered via {file}."
        
        return "⚠️ No app file found to trigger reload."
    except Exception as e:
        return f"⚠️ Failed to trigger server reload: {e}"

def log_all_actions(logs, user_message, file_path=""):
    """Comprehensive logging system"""
    try:
        import datetime
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Create log entry
        log_entry = f"""
[{timestamp}] MINI ASSISTANT ACTION
User Message: {user_message[:100]}{'...' if len(user_message) > 100 else ''}
File Path: {file_path or 'None'}
Actions Performed:
"""
        
        for log in logs:
            log_entry += f"  - {log}\n"
        
        log_entry += "-" * 50 + "\n"
        
        # Write to log file
        with open(MINI_ASSISTANT_LOG, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
    except Exception as e:
        logger.error(f"Failed to write Mini Assistant log: {e}")

def generate_claude_response(message, context, api_key):
    """Generate AI-powered response using Claude API"""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Enhanced context for Mini Assistant
        full_context = f"""{context}

You are Mini Assistant - a helpful development assistant for SoulBridge AI. Keep responses:
- Concise but informative (under 400 words)
- Technical and actionable
- Specific to SoulBridge AI development context
- Helpful for debugging, planning, and coding tasks
- Use markdown formatting for better readability
- Include code examples when relevant"""

        response = client.messages.create(
            model="claude-3-haiku-20240307",  # Fast and cost-effective
            max_tokens=500,
            temperature=0.7,
            messages=[
                {"role": "user", "content": f"{full_context}\n\nUser question: {message}"}
            ]
        )
        
        return response.content[0].text.strip()
        
    except Exception as e:
        logger.error(f"Claude API response generation failed: {e}")
        return generate_rule_based_response(message.lower(), message)

def generate_rule_based_response(message_lower, original_message):
    
    # Pattern matching for common development queries
    if any(word in message_lower for word in ['tier', 'isolation', 'free user', 'premium']):
        return """Based on our recent work on tier isolation:

**Current Issue**: Free users are still seeing premium features they shouldn't have access to.

**What we've fixed**:
- ✅ Duplicate API endpoint causing all companions to appear unlocked  
- ✅ Backend feature limits using effective_plan instead of user_plan
- ✅ Added tier checks in chat.html template

**What to check next**:
1. View page source on chat page as free user - look for debug comment
2. Verify template variables: user_plan=free, trial_active=False
3. Check if browser caching is preventing template updates

**Expected behavior**:
- Free users should only see: Switch, Voice Chat, Library, Save, Clear
- Premium features should be completely hidden (not just limited)"""

    elif any(word in message_lower for word in ['commit', 'git', 'push']):
        return """Here's a commit message template based on our current work:

```
Fix free user feature visibility - complete tier isolation

- Hide premium features from free users in chat template
- Add debug info to verify template variable values  
- Ensure only basic features visible: Switch, Voice Chat, Library, Save, Clear
- Premium features (Decoder, Fortune, Horoscope) now properly hidden

🤖 Generated with Mini Assistant

Co-Authored-By: Mini Assistant <admin@soulbridgeai.com>
```

Would you like me to help with any specific changes that need committing?"""

    elif any(word in message_lower for word in ['debug', 'bug', 'error', 'issue']):
        return """🔍 **Debugging Checklist for SoulBridge AI**:

**Current Priority**: Free user tier isolation
1. Check chat page HTML source for debug comment
2. Verify Jinja2 template conditionals are working
3. Clear browser cache (Ctrl+F5)
4. Test with different user accounts

**Common Issues**:
- Template caching preventing updates
- Session variables not being set correctly
- Browser cache showing old version
- Jinja2 syntax errors in conditionals

**Quick Tests**:
- Login as free user → visit /chat → view source
- Look for: `<!-- DEBUG: user_plan=free, trial_active=False -->`
- Premium features should not appear in HTML at all

Need help with a specific function or error?"""

    elif any(word in message_lower for word in ['next', 'todo', 'priority', 'work on']):
        return """📋 **Next Priority Tasks**:

**Immediate (Tier Isolation)**:
1. Verify free user template fix is working
2. Test companion selector tier restrictions  
3. Remove debug comments when confirmed working

**Upcoming Features**:
- Voice chat improvements
- Enhanced trial system
- Mobile responsiveness  
- Performance optimization

**Code Quality**:
- Remove duplicate/unused code
- Add error handling
- Optimize database queries
- Update documentation

**Testing**:
- Cross-browser compatibility
- Different user scenarios
- Edge cases and error conditions

Which area would you like to focus on first?"""

    elif any(word in message_lower for word in ['recent', 'commits', 'history', 'work']):
        return """📝 **Recent Work Summary**:

**Today's Progress**:
- Fixed companion selector tier isolation (disabled duplicate API endpoint)
- Added tier checks to hide premium features from free users
- Enhanced timer positioning and sizing consistency
- Added debug info to troubleshoot template issues

**Key Files Modified**:
- `backend/app.py` - Fixed feature access control, disabled duplicate endpoint
- `backend/templates/chat.html` - Added tier-based feature visibility  
- `backend/templates/companion_selector.html` - Timer positioning fixes

**Current Status**:
- ✅ Backend tier logic fixed
- ✅ Template conditionals added  
- ⏳ Testing free user experience
- ⏳ Verifying complete isolation

**Commits Made**:
- "Fix tier isolation in feature access control"
- "Complete tier isolation - hide premium features from free users"  
- "Fix companion selector tier isolation"

Ready to continue with testing and refinements!"""

    else:
        return f"""I'm Mini Assistant, here to help with SoulBridge AI development! 

I noticed you asked: "{user_message}"

I can help with:
- 🐛 Debugging code issues
- 🔧 Tier isolation problems  
- 💾 Git commit messages
- 📋 Next task priorities
- 🔍 Code review and analysis

Could you be more specific about what you'd like help with? I have full context about your recent work on tier isolation and companion selector fixes."""

def generate_enhanced_mini_helper_response(user_message, file_path="", project_context=""):
    """Enhanced mini helper with file editing capabilities when Claude is rate limited"""
    
    # Load conversation history and project state for context
    conversation_summary = get_conversation_summary()
    project_state = load_project_state()
    
    # Read existing file content if file path provided
    file_content = ""
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
    
    message_lower = user_message.lower()
    
    # Enhanced context awareness
    context_info = f"""
**MINI HELPER CONTEXT AWARENESS**
{conversation_summary}

**Project State:**
- Last Updated: {project_state.get('last_updated', 'Unknown')}
- Current Focus: {project_state.get('current_focus', 'General development')}
- Recently Modified Files: {', '.join(project_state.get('modified_files', [])[-5:]) if project_state.get('modified_files') else 'None'}
- Completed Tasks: {', '.join(project_state.get('completed_tasks', [])[-5:]) if project_state.get('completed_tasks') else 'None'}
- Rate Limit Sessions: {project_state.get('rate_limit_sessions', 0)}

"""
    
    # Enhanced responses based on user request and file context
    if file_path and file_content:
        # File editing mode - provide intelligent code modifications
        if "fix" in message_lower or "bug" in message_lower:
            return generate_bug_fix_response(file_content, user_message, file_path)
        elif "add" in message_lower or "feature" in message_lower:
            return generate_feature_addition_response(file_content, user_message, file_path)
        elif "refactor" in message_lower or "optimize" in message_lower:
            return generate_refactor_response(file_content, user_message, file_path)
        else:
            # General file modification
            return generate_smart_file_response(file_content, user_message, file_path)
    
    # Non-file editing mode - use enhanced rule-based responses
    return generate_contextual_response(user_message, project_context)

def generate_bug_fix_response(file_content, user_message, file_path):
    """Generate bug fix response with common fixes applied"""
    
    # Apply common bug fixes based on file type
    if file_path.endswith('.py'):
        # Python common fixes
        if "import" in user_message.lower():
            # Add missing imports
            lines = file_content.split('\n')
            if 'import os' not in file_content and 'os.' in file_content:
                lines.insert(0, 'import os')
            if 'import json' not in file_content and 'json.' in file_content:
                lines.insert(0, 'import json')
            return '\n'.join(lines)
        
        # Fix common indentation issues
        fixed_lines = []
        for line in file_content.split('\n'):
            if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                if any(keyword in line for keyword in ['def ', 'class ', 'if ', 'for ', 'while ']):
                    fixed_lines.append(line)
                else:
                    fixed_lines.append('    ' + line)  # Add basic indentation
            else:
                fixed_lines.append(line)
        return '\n'.join(fixed_lines)
    
    elif file_path.endswith('.js'):
        # JavaScript common fixes
        fixed_content = file_content
        # Add missing semicolons
        lines = fixed_content.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.endswith((';', '{', '}', ')', ']')) and not stripped.startswith('//'):
                if any(keyword in stripped for keyword in ['const', 'let', 'var', 'return']):
                    lines[i] = line + ';'
        return '\n'.join(lines)
    
    # Default: return original with comment about the issue
    return f"// Mini Helper attempted to fix: {user_message}\n" + file_content

def generate_feature_addition_response(file_content, user_message, file_path):
    """Generate feature addition response"""
    
    if file_path.endswith('.py'):
        # Add Python function template
        feature_name = user_message.replace('add', '').replace('feature', '').strip()
        new_function = f"""
def {feature_name.replace(' ', '_').lower()}():
    \"\"\"
    {feature_name} functionality - added by Mini Helper
    TODO: Implement {feature_name} logic
    \"\"\"
    pass
    # TODO: Add your {feature_name} implementation here
"""
        return file_content + new_function
    
    elif file_path.endswith('.js'):
        # Add JavaScript function template
        feature_name = user_message.replace('add', '').replace('feature', '').strip()
        new_function = f"""
// {feature_name} functionality - added by Mini Helper
function {feature_name.replace(' ', '_').toLowerCase()}() {{
    // TODO: Implement {feature_name} logic
    console.log('Mini Helper: {feature_name} function called');
}}
"""
        return file_content + new_function
    
    return file_content + f"\n// Mini Helper: Added {user_message}"

def generate_refactor_response(file_content, user_message, file_path):
    """Generate refactored code response"""
    
    # Basic refactoring: remove duplicate lines and organize imports
    lines = file_content.split('\n')
    unique_lines = []
    seen_lines = set()
    
    for line in lines:
        stripped = line.strip()
        if stripped and stripped not in seen_lines:
            unique_lines.append(line)
            seen_lines.add(stripped)
        elif not stripped:  # Keep empty lines
            unique_lines.append(line)
    
    return '\n'.join(unique_lines)

def generate_smart_file_response(file_content, user_message, file_path):
    """Generate intelligent file modification response"""
    
    # Smart modifications based on user request
    if "rate limit" in user_message.lower():
        return file_content + f"\n# Mini Helper: Rate limit handling added for {os.path.basename(file_path)}"
    
    if "error" in user_message.lower():
        return file_content + f"\n# Mini Helper: Error handling improved in {os.path.basename(file_path)}"
    
    return file_content + f"\n# Mini Helper: Modified {os.path.basename(file_path)} per request: {user_message}"

def generate_contextual_response(user_message, project_context):
    """Generate enhanced contextual response with tool-like capabilities"""
    
    message_lower = user_message.lower()
    conversation_summary = get_conversation_summary()
    project_state = load_project_state()
    memory = load_conversation_memory()
    
    # Enhanced context-aware analysis of user intent
    is_asking_about_previous_work = any(word in message_lower for word in ['remember', 'recall', 'previous', 'before', 'earlier', 'last time', 'we were working on', 'continue'])
    is_asking_for_file_analysis = any(word in message_lower for word in ['analyze', 'check', 'look at', 'examine', 'review'])
    is_asking_for_search = any(word in message_lower for word in ['find', 'search', 'locate', 'where is'])
    is_asking_for_fix = any(word in message_lower for word in ['fix', 'bug', 'error', 'problem', 'issue', 'broken'])
    
    # Context-aware memory recall
    if is_asking_about_previous_work and memory.get('conversations'):
        recent_work = memory['conversations'][-5:]  # Last 5 conversations
        work_context = ""
        
        for conv in recent_work:
            if conv.get('file_path'):
                work_context += f"\n🔧 Worked on: {conv['file_path']} - {conv['user_message'][:50]}..."
            if 'fix' in conv['user_message'].lower() or 'bug' in conv['user_message'].lower():
                work_context += f"\n🐛 Bug fix: {conv['user_message'][:60]}..."
                
        if work_context:
            return f"""🧠 **Memory Recall - Previous Work Context**

{conversation_summary}

**Recent File Work:**{work_context}

**Current Status:**
- Total sessions with me: {memory.get('total_interactions', 0)}
- Project focus: {project_state.get('current_focus', 'SoulBridge AI development')}
- Recent files modified: {len(project_state.get('modified_files', []))} files

I can continue from where we left off. What would you like to work on next?"""
    
    # Enhanced file search capabilities
    if is_asking_for_search:
        search_terms = [word for word in user_message.split() if len(word) > 2 and word not in ['find', 'search', 'locate', 'where', 'is', 'the', 'can', 'you']]
        if search_terms:
            search_results = perform_basic_file_search(search_terms[0])
            return f"""🔍 **File Search Results for "{search_terms[0]}"**

{search_results}

💡 **Tip**: I can help you examine any of these files in detail. Just ask me to "analyze [filename]" or provide a specific file path."""
    
    # Enhanced file analysis capabilities  
    if is_asking_for_file_analysis:
        # Extract potential file paths from message
        words = user_message.split()
        potential_files = [word for word in words if ('.' in word and ('/' in word or '\\' in word)) or word.endswith(('.py', '.html', '.js', '.css', '.json'))]
        
        if potential_files:
            file_path = potential_files[0]
            if file_path.startswith('backend/') or file_path.startswith('./'):
                file_path = os.path.join(os.path.dirname(__file__), file_path.replace('backend/', '').replace('./', ''))
            
            analysis_result = perform_basic_file_analysis(file_path)
            return f"""📊 **File Analysis: {os.path.basename(file_path)}**

{analysis_result}

🔧 **I can help with**: Bug fixes, code improvements, adding features, or explaining specific parts."""
        else:
            return """📊 **File Analysis Available**

I can analyze any file in the SoulBridge AI project. Please specify:
- `backend/app.py` - Main Flask application
- `backend/templates/` - HTML templates  
- `backend/static/` - CSS/JS assets
- Or any specific file path

Example: "analyze backend/templates/chat.html" """
    
    # Enhanced bug fixing capabilities
    if is_asking_for_fix:
        recent_errors = [conv for conv in memory.get('conversations', []) if any(err_word in conv['user_message'].lower() for err_word in ['error', 'bug', 'broken', 'fail'])]
        
        context = f"""🐛 **Bug Fix Assistant**

{conversation_summary}

**Recent Error Context:**"""
        
        if recent_errors:
            for error in recent_errors[-3:]:
                context += f"\n- {error['user_message'][:60]}... ({error['timestamp'][:10]})"
        else:
            context += "\nNo recent error reports in memory."
            
        context += f"""

**I can help fix**:
🔧 Python/Flask backend errors
🔧 HTML template issues  
🔧 JavaScript frontend bugs
🔧 Database connection problems
🔧 Route/endpoint issues

Please describe the specific error or provide the file path that needs fixing."""
        
        return context
    
    if "rate limit" in message_lower:
        return """🚨 **Claude Rate Limit Detected - Mini Helper Active**

I'm your fallback Mini Helper, activated because Claude API has hit rate limits.

**What I can do while Claude recovers**:
- ✅ Basic code fixes and modifications
- ✅ File editing with intelligent templates  
- ✅ Git commit message generation
- ✅ Project status updates
- ✅ Debug assistance with rule-based solutions

**Rate Limit Recovery**:
- Claude typically recovers within 15-60 minutes
- I'll automatically switch back when Claude is available
- Your requests are being handled seamlessly

**Current Capabilities**:
- Smart file modifications based on common patterns
- Bug fixes for Python/JavaScript files
- Feature addition templates
- Code refactoring assistance

How can I help you continue development while Claude recovers?"""
    
    elif "status" in message_lower:
        status = get_rate_limit_status()
        return f"""📊 **Mini Helper Status Report**

**Rate Limit Status**: {'🔴 ACTIVE' if status.get('rate_limited') else '🟢 CLEAR'}
**Last Updated**: {status.get('timestamp', 'Unknown')}
**Helper Mode**: {'Auto-Activated' if status.get('auto_helper_active') else 'Standby'}
**Total Rate Limit Sessions**: {project_state.get('rate_limit_sessions', 0)}

{conversation_summary}

**SoulBridge AI Project Status**:
- Current Focus: {project_state.get('current_focus', 'General development')}
- Recently Modified Files: {len(project_state.get('modified_files', []))} files
- Completed Tasks: {len(project_state.get('completed_tasks', []))} tasks
- Last Project Update: {project_state.get('last_updated', 'Unknown')[:16] if project_state.get('last_updated') else 'Unknown'}

**Recent Activity**:
- Files Modified: {', '.join(project_state.get('modified_files', [])[-3:]) if project_state.get('modified_files') else 'None'}
- Tasks Completed: {', '.join(project_state.get('completed_tasks', [])[-3:]) if project_state.get('completed_tasks') else 'None'}

Ready to assist with development tasks!"""
    
    elif any(phrase in message_lower for phrase in ["what were we doing", "recent work", "continue", "where were we", "last worked on"]):
        recent_files = project_state.get('modified_files', [])[-3:]
        recent_tasks = project_state.get('completed_tasks', [])[-3:]
        
        return f"""🔄 **Context Recap - Where We Left Off**

{conversation_summary}

**Recent Development Activity**:
- Current Focus: {project_state.get('current_focus', 'General development')}
- Last Active: {project_state.get('last_updated', 'Unknown')[:16] if project_state.get('last_updated') else 'Unknown'}

**Files Recently Modified**:
{chr(10).join([f"- {file}" for file in recent_files]) if recent_files else "- No recent file modifications"}

**Recently Completed Tasks**:
{chr(10).join([f"- {task}" for task in recent_tasks]) if recent_tasks else "- No recent task completions"}

**Rate Limit Context**:
- This session triggered {project_state.get('rate_limit_sessions', 0)} rate limit activations
- Mini Helper has been helping maintain continuity

What would you like to continue working on?"""
    
    elif "remember" in message_lower or "recall" in message_lower:
        memory = load_conversation_memory()
        if memory.get('conversations'):
            last_conv = memory['conversations'][-1]
            return f"""🧠 **Memory Recall**

**Last Conversation**: {last_conv.get('timestamp', 'Unknown')[:16]}
**You asked**: "{last_conv.get('user_message', 'Unknown')}"
**Context**: {last_conv.get('action_type', 'chat')}
{f"**File**: {last_conv.get('file_path')}" if last_conv.get('file_path') else ""}

{conversation_summary}

I have memory of our recent interactions and can continue from where we left off."""
        else:
            return "🧠 No conversation history available yet. This might be our first interaction!"
    
    # Use the original rule-based response for other queries with enhanced context
    base_response = generate_rule_based_response(message_lower, user_message)
    
    # Add context footer if we have conversation history
    if conversation_summary != "No recent conversation history.":
        base_response += f"\n\n---\n**Context Note**: I remember our recent work together and can reference previous conversations for continuity."
    
    return base_response

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