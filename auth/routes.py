"""
Authentication Routes
Clean, isolated authentication endpoints
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import logging

from shared.middleware.session_manager import SessionManager, login_required
from shared.utils.helpers import validate_email, sanitize_input, get_user_ip, log_action
from .models import UserRepository
from .services import AuthService

logger = logging.getLogger(__name__)

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize services
user_repo = UserRepository()
auth_service = AuthService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login endpoint"""
    if request.method == 'GET':
        # If already logged in, redirect to dashboard
        if SessionManager.is_logged_in():
            return redirect('/')
        return render_template('auth/login.html')
    
    try:
        # Get form data
        data = request.get_json() if request.is_json else request.form
        email = sanitize_input(data.get('email', '')).lower()
        password = data.get('password', '')
        
        # Validate input
        if not email or not password:
            error_msg = 'Email and password are required'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/login.html')
        
        if not validate_email(email):
            error_msg = 'Invalid email format'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/login.html')
        
        # Attempt authentication
        user = auth_service.authenticate_user(email, password)
        
        if user:
            # Login successful
            SessionManager.login_user({
                'id': user.id,
                'email': user.email,
                'user_plan': user.user_plan,
                'trial_active': user.trial_active
            })
            
            # Return appropriate response
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'redirect': '/'
                })
            
            flash('Login successful!', 'success')
            return redirect('/')
        
        else:
            # Login failed
            error_msg = 'Invalid email or password'
            log_action(
                user_id=None,
                action='login_failed',
                details={'email': email, 'ip': get_user_ip(request)}
            )
            
            if request.is_json:
                return jsonify({'error': error_msg}), 401
            flash(error_msg, 'error')
            return render_template('auth/login.html')
    
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        error_msg = 'An error occurred during login'
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
        return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration endpoint"""
    if request.method == 'GET':
        # If already logged in, redirect to dashboard
        if SessionManager.is_logged_in():
            return redirect('/')
        return render_template('auth/register.html')
    
    try:
        # Get form data
        data = request.get_json() if request.is_json else request.form
        email = sanitize_input(data.get('email', '')).lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', password)  # Default to password if not provided
        
        # Validate input
        if not email or not password:
            error_msg = 'Email and password are required'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/register.html')
        
        if not validate_email(email):
            error_msg = 'Invalid email format'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            error_msg = 'Passwords do not match'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/register.html')
        
        # Attempt registration
        user = auth_service.register_user(email, password)
        
        if user:
            # Registration successful - auto login
            SessionManager.login_user({
                'id': user.id,
                'email': user.email,
                'user_plan': user.user_plan,
                'trial_active': user.trial_active
            })
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Registration successful',
                    'redirect': '/'
                })
            
            flash('Registration successful! Welcome to SoulBridge AI!', 'success')
            return redirect('/')
        
        else:
            # Registration failed
            error_msg = 'Registration failed. Email may already be in use.'
            
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/register.html')
    
    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
        error_msg = 'An error occurred during registration'
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
        return render_template('auth/register.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Logout endpoint"""
    try:
        SessionManager.logout_user()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Logged out successfully'})
        
        flash('You have been logged out successfully', 'info')
        return redirect('/login')
    
    except Exception as e:
        logger.error(f"❌ Logout error: {e}")
        if request.is_json:
            return jsonify({'error': 'Logout failed'}), 500
        return redirect('/')

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        user_context = SessionManager.get_user_context()
        return render_template('auth/profile.html', **user_context)
    except Exception as e:
        logger.error(f"❌ Profile page error: {e}")
        flash('Error loading profile', 'error')
        return redirect('/')

@auth_bp.route('/activate-trial', methods=['POST'])
@login_required
def activate_trial():
    """Activate 5-hour trial for bronze users"""
    try:
        user_id = SessionManager.get_user_id()
        user_plan = SessionManager.get_user_plan()
        trial_active = SessionManager.is_trial_active()
        
        # Only bronze users can activate trial
        if user_plan != 'bronze':
            return jsonify({'error': 'Trial only available for Bronze tier users'}), 400
        
        # Check if trial already active
        if trial_active:
            return jsonify({'error': 'Trial is already active'}), 400
        
        # Activate trial
        success = auth_service.activate_trial(user_id)
        
        if success:
            # Update session
            SessionManager.update_session_data({'trial_active': True})
            
            log_action(
                user_id=user_id,
                action='trial_activated',
                details={'ip': get_user_ip(request)}
            )
            
            return jsonify({
                'success': True,
                'message': '5-hour trial activated! You now have Gold tier access.',
                'trial_active': True
            })
        else:
            return jsonify({'error': 'Failed to activate trial'}), 500
    
    except Exception as e:
        logger.error(f"❌ Trial activation error: {e}")
        return jsonify({'error': 'An error occurred'}), 500

@auth_bp.route('/check-session')
def check_session():
    """Check current session status"""
    return jsonify(SessionManager.get_user_context())

# Legacy route redirects for compatibility
@auth_bp.route('/signin')
def signin_redirect():
    """Redirect old signin route to login"""
    return redirect(url_for('auth.login'))

@auth_bp.route('/signup')
def signup_redirect():
    """Redirect old signup route to register"""
    return redirect(url_for('auth.register'))