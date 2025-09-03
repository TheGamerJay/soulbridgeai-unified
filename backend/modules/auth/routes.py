"""
SoulBridge AI - Authentication Routes Module
Extracted from app.py monolith for modular architecture
"""
import os
import logging
from datetime import datetime, timezone
from flask import Blueprint, request, session, redirect, flash, jsonify, render_template
from .auth_service import AuthService, has_accepted_terms
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

@auth_bp.route("/login", methods=["GET", "POST"])
def auth_login():
    """Login page and authentication"""
    if request.method == "GET":
        # Display login form
        error_message = request.args.get('error')
        return_to = request.args.get('return_to')
        try:
            from flask import render_template
            return render_template('login.html', error=error_message, return_to=return_to)
        except Exception as e:
            logger.error(f"Error rendering login page: {e}")
            return f"<h1>Login Error</h1><p>{str(e)}</p>"
    
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
                return redirect("/auth/login")
        
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
            
            # Debug session state
            logger.info(f"[LOGIN] Session after setup: logged_in={session.get('logged_in')}, email={session.get('email')}, user_id={session.get('user_id')}")
            
            # Explicitly save session to ensure persistence
            session.modified = True
            session.permanent = False
            
            # Determine redirect URL - bypass terms check to prevent loops
            redirect_url = "/intro"
            logger.info(f"[LOGIN] Bypassing terms check, redirecting to {redirect_url}")
            logger.info(f"[LOGIN] Session explicitly saved: modified={session.modified}, keys={list(session.keys())}")
            
            logger.info(f"[LOGIN] Final redirect URL: {redirect_url}")
            
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
                return redirect("/auth/login")
                
    except Exception as e:
        logger.error(f"[LOGIN] Unexpected error: {e}")
        import traceback
        logger.error(f"[LOGIN] Traceback: {traceback.format_exc()}")
        traceback.print_exc()
        
        error_msg = "Login system temporarily unavailable"
        if request.headers.get('Content-Type') == 'application/json' or request.is_json:
            return jsonify({"success": False, "error": error_msg}), 500
        else:
            flash(error_msg, "error")
            return redirect("/auth/login")

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
        return redirect("/auth/login")
        
    except Exception as e:
        logger.error(f"[LOGOUT] Error during logout: {e}")
        # Force clear session even if error
        session.clear()
        return redirect("/auth/login")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration route"""
    if request.method == "GET":
        return render_template("register.html")
    
    try:
        email, password, form_data = parse_request_data()
        
        if not email or not password:
            flash("Email and password are required", "error")
            return redirect("/auth/register")
        
        auth_service = AuthService()
        result = auth_service.register_user(email, password, form_data)
        
        if result["success"]:
            logger.info(f"[REGISTER] Successfully registered user: {email}")
            flash("Registration successful! Please log in.", "success")
            return redirect("/auth/login")
        else:
            logger.warning(f"[REGISTER] Registration failed for {email}: {result['error']}")
            flash(result["error"], "error")
            return redirect("/auth/register")
            
    except Exception as e:
        logger.error(f"[REGISTER] Unexpected error: {e}")
        flash("Registration system temporarily unavailable", "error")
        return redirect("/auth/register")

# Add more auth routes as needed...