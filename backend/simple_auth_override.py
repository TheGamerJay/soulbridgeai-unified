from flask import request, render_template, redirect, session, jsonify
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def simple_auth_login():
    """Ultra-simple login that bypasses all authentication"""
    if request.method == "GET":
        return render_template("simple_login.html")
    
    # POST - process simple login
    email = request.form.get("email", "").strip().lower()
    if not email:
        return render_template("simple_login.html", message="Email required", success=False)
    
    # Create session for any email (bypass authentication)
    session.clear()
    session['user_authenticated'] = True
    session['user_email'] = email
    session['email'] = email
    session['user_id'] = 104 if email == 'dagamerjay13@gmail.com' else 1
    session['display_name'] = 'User'
    session['session_version'] = "2025-08-28-simple"
    session['last_activity'] = datetime.now().isoformat()
    
    # Set tier based on email
    if email == 'dagamerjay13@gmail.com':
        session['user_plan'] = 'gold'
        session['trial_active'] = False
    elif email == 'aceelnene@gmail.com':
        session['user_plan'] = 'bronze'
        session['trial_active'] = True  # Give trial access
    else:
        session['user_plan'] = 'bronze'
        session['trial_active'] = False
    
    session.modified = True
    
    logger.info(f"✅ Simple login successful: {email} -> {session['user_plan']} tier")
    
    return redirect("/chat-unified")