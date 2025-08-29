"""
Session Management Middleware
Centralized session handling for all modules
"""
import functools
from flask import session, request, jsonify, redirect, url_for
from typing import Optional, Dict, Any, Callable
import logging
from datetime import datetime, timezone

from ..database.connection import get_database
from ..utils.helpers import log_action, get_user_ip

logger = logging.getLogger(__name__)

class SessionManager:
    """Centralized session management"""
    
    @staticmethod
    def is_logged_in() -> bool:
        """Check if user is logged in"""
        return 'user_id' in session and session.get('user_id') is not None
    
    @staticmethod
    def get_user_id() -> Optional[str]:
        """Get current user ID from session"""
        return session.get('user_id')
    
    @staticmethod
    def get_user_email() -> Optional[str]:
        """Get current user email from session"""
        return session.get('email')
    
    @staticmethod
    def get_user_plan() -> str:
        """Get current user plan from session"""
        return session.get('user_plan', 'bronze')
    
    @staticmethod
    def is_trial_active() -> bool:
        """Check if user has active trial"""
        return session.get('trial_active', False)
    
    @staticmethod
    def login_user(user_data: Dict[str, Any]) -> None:
        """Log in user and set session data"""
        session['user_id'] = user_data['id']
        session['email'] = user_data['email']
        session['user_plan'] = user_data.get('user_plan', 'bronze')
        session['trial_active'] = user_data.get('trial_active', False)
        session['last_login'] = datetime.now(timezone.utc).isoformat()
        session.permanent = True
        
        log_action(
            user_id=user_data['id'],
            action='user_login',
            details={
                'email': user_data['email'],
                'plan': user_data.get('user_plan', 'bronze'),
                'ip': get_user_ip(request)
            }
        )
        logger.info(f"✅ User logged in: {user_data['email']} (ID: {user_data['id']})")
    
    @staticmethod
    def logout_user() -> None:
        """Log out user and clear session"""
        user_id = session.get('user_id')
        email = session.get('email')
        
        # Clear all session data
        session.clear()
        
        log_action(
            user_id=user_id,
            action='user_logout',
            details={
                'email': email,
                'ip': get_user_ip(request)
            }
        )
        logger.info(f"✅ User logged out: {email} (ID: {user_id})")
    
    @staticmethod
    def update_session_data(updates: Dict[str, Any]) -> None:
        """Update session data"""
        for key, value in updates.items():
            session[key] = value
        session.modified = True
        logger.debug(f"📝 Session updated: {list(updates.keys())}")
    
    @staticmethod
    def get_user_context() -> Dict[str, Any]:
        """Get complete user context for templates"""
        return {
            'is_logged_in': SessionManager.is_logged_in(),
            'user_id': SessionManager.get_user_id(),
            'email': SessionManager.get_user_email(),
            'user_plan': SessionManager.get_user_plan(),
            'trial_active': SessionManager.is_trial_active(),
            'effective_plan': get_effective_plan(
                SessionManager.get_user_plan(),
                SessionManager.is_trial_active()
            )
        }

def get_effective_plan(user_plan: str, trial_active: bool) -> str:
    """Get effective plan - Bronze users with active trial get Gold access"""
    if trial_active and user_plan == "bronze":
        return "gold"
    return user_plan

def login_required(f: Callable) -> Callable:
    """Decorator to require login for routes"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not SessionManager.is_logged_in():
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def plan_required(required_plan: str):
    """Decorator to require specific plan level"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not SessionManager.is_logged_in():
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('auth.login'))
            
            user_plan = SessionManager.get_user_plan()
            trial_active = SessionManager.is_trial_active()
            effective_plan = get_effective_plan(user_plan, trial_active)
            
            # Check tier hierarchy
            tier_hierarchy = {'bronze': 1, 'silver': 2, 'gold': 3}
            
            if tier_hierarchy.get(effective_plan, 0) < tier_hierarchy.get(required_plan, 999):
                if request.is_json:
                    return jsonify({
                        'error': f'{required_plan.title()} tier required',
                        'current_plan': effective_plan,
                        'required_plan': required_plan
                    }), 403
                return redirect(url_for('tiers.upgrade'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def refresh_user_data():
    """Refresh user data from database"""
    if not SessionManager.is_logged_in():
        return
    
    user_id = SessionManager.get_user_id()
    if not user_id:
        return
    
    try:
        db = get_database()
        user_data = db.execute_query(
            "SELECT id, email, user_plan, trial_active, trial_expires_at FROM users WHERE id = ?",
            (user_id,),
            fetch='one'
        )
        
        if user_data:
            # Update session with fresh data
            SessionManager.update_session_data({
                'user_plan': user_data[2] if isinstance(user_data, tuple) else user_data['user_plan'],
                'trial_active': user_data[3] if isinstance(user_data, tuple) else user_data['trial_active']
            })
            logger.debug(f"🔄 User data refreshed for user {user_id}")
        else:
            # User not found - logout
            logger.warning(f"⚠️ User {user_id} not found in database - logging out")
            SessionManager.logout_user()
    
    except Exception as e:
        logger.error(f"❌ Failed to refresh user data for user {user_id}: {e}")

def before_request_handler():
    """Handler to run before each request"""
    # Refresh user data periodically
    if SessionManager.is_logged_in():
        last_refresh = session.get('last_data_refresh')
        now = datetime.now(timezone.utc).isoformat()
        
        # Refresh every 5 minutes
        if not last_refresh or (datetime.fromisoformat(now) - datetime.fromisoformat(last_refresh)).seconds > 300:
            refresh_user_data()
            session['last_data_refresh'] = now

# Export commonly used functions
session_manager = SessionManager()