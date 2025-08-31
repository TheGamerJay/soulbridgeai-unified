"""
SoulBridge AI - Authentication Routes Module
Extracted from app.py monolith for modular architecture
"""
import os
import logging
from datetime import datetime, timezone
from flask import Blueprint, request, session, redirect, flash, jsonify, render_template
from .auth_service import AuthService
from .session_manager import setup_user_session, requires_login
from ..shared.database import get_database
from unified_tier_system import get_effective_plan

logger = logging.getLogger(__name__)

# Create blueprint for auth routes  
auth_bp = Blueprint('auth', __name__)

def parse_request_data():
    """Parse request data for email/password - extracted utility function"""
    try:
        if request.is_json:
            data = request.get_json()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            return email, password, data
        else:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            return email, password, request.form
    except Exception as e:
        logger.error(f"Error parsing request data: {e}")
        return '', '', {}

@auth_bp.route("/auth/login", methods=["POST"])
def auth_login():
    """Login authentication - process POST only"""
    # Handle POST requests - process login
    try:
        logger.info(f"[LOGIN] Received {request.method} request at /auth/login from {request.remote_addr}")
        email, password, _ = parse_request_data()
        logger.info(f"[LOGIN] Parsed email: {email}, password: {'***' if password else None}")
        
        if not email or not password:
            logger.warning(f"[LOGIN] Missing email or password. Email: {email}, Password present: {bool(password)}")
            error_msg = "Email and password required"
            
            if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                return jsonify({"success": False, "error": error_msg}), 400
            else:
                flash(error_msg, "error")
                return redirect("/login")
        
        # Initialize auth service
        auth_service = AuthService()
        
        # Try to authenticate
        result = auth_service.authenticate(email, password)
        logger.info(f"[LOGIN] Authentication result: {result}")
        
        if result["success"]:
            logger.info(f"[LOGIN] Authenticated successfully for {email}, setting up session...")
            
            # Set up user session
            setup_user_session(
                email=result["email"],
                user_id=result["user_id"]
            )
            
            # Set user plan with proper migration
            auth_service.migrate_legacy_plan(result)
            
            # Restore trial status from database
            auth_service.restore_trial_status(email)
            
            # Restore artistic time and trial credits
            auth_service.restore_artistic_time(result.get("user_id"))
            
            # Set isolated tier access flags
            auth_service.set_tier_access_flags()
            
            # Determine redirect URL
            redirect_url = "/terms-acceptance" if not has_accepted_terms() else "/intro"
            
            if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                return jsonify({"success": True, "redirect": redirect_url})
            else:
                logger.info(f"[LOGIN] Redirecting to {redirect_url} after successful login.")
                return redirect(redirect_url)
        else:
            logger.warning(f"[LOGIN] Login failed: {email}")
            
            if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                return jsonify({"success": False, "error": result["error"]}), 401
            else:
                logger.warning(f"[LOGIN] Flashing error: {result['error']}")
                flash(result["error"], "error")
                return redirect("/login")
                
    except Exception as e:
        logger.error(f"[LOGIN] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
        error_msg = "Login system temporarily unavailable"
        if request.headers.get('Content-Type') == 'application/json' or request.is_json:
            return jsonify({"success": False, "error": error_msg}), 500
        else:
            flash(error_msg, "error")
            return redirect("/login")

@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """Logout route - clear session and redirect"""
    try:
        user_id = session.get('user_id')
        email = session.get('email')
        
        logger.info(f"[LOGOUT] User {email} (ID: {user_id}) logging out")
        
        # Clear session
        session.clear()
        
        logger.info("[LOGOUT] Session cleared successfully")
        return redirect("/")
        
    except Exception as e:
        logger.error(f"[LOGOUT] Error during logout: {e}")
        # Force clear session even if error
        session.clear()
        return redirect("/")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration route"""
    if request.method == "GET":
        return render_template("register.html")
    
    try:
        email, password, form_data = parse_request_data()
        
        if not email or not password:
            flash("Email and password are required", "error")
            return redirect("/register")
        
        auth_service = AuthService()
        result = auth_service.register_user(email, password, form_data)
        
        if result["success"]:
            logger.info(f"[REGISTER] Successfully registered user: {email}")
            flash("Registration successful! Please log in.", "success")
            return redirect("/login")
        else:
            logger.warning(f"[REGISTER] Registration failed for {email}: {result['error']}")
            flash(result["error"], "error")
            return redirect("/register")
            
    except Exception as e:
        logger.error(f"[REGISTER] Unexpected error: {e}")
        flash("Registration system temporarily unavailable", "error")
        return redirect("/register")

# Add more auth routes as needed...