# =====================================
# 📁 FILE: backend/routes/mini_studio.py
# =====================================
from flask import Blueprint, render_template, redirect, session
import logging

logger = logging.getLogger(__name__)

def is_logged_in():
    return session.get('user_id') is not None

def get_effective_plan(user_plan, trial_active):
    """Get effective plan considering trial status"""
    if trial_active and user_plan == "bronze":
        return "gold"
    return user_plan

bp = Blueprint("mini_studio", __name__)

@bp.route("/mini-studio")
def mini_studio():
    """Mini Studio - Professional music creation environment (Max users only)"""
    if not is_logged_in():
        return redirect("/login?return_to=mini-studio")
    
    # Check access permissions
    user_plan = session.get('user_plan', 'free')
    trial_active = session.get('trial_active', False)
    effective_plan = get_effective_plan(user_plan, trial_active)
    user_id = session.get('user_id')
    
    # Mini studio is Gold tier exclusive + trial users get access
    if effective_plan != 'gold':
        return redirect("/tiers?upgrade=gold")
    
    # Get user credits (trainer time for mini studio)
    try:
        from unified_tier_system import get_user_credits, get_trial_trainer_time
        credits = get_user_credits(user_id) if user_id else 0
        
        # For trial users, they get 60 "trainer time" credits specifically for mini studio
        if user_plan == 'free' and trial_active:
            trial_credits = get_trial_trainer_time(user_id)
            credits = max(credits, trial_credits)  # Use trial credits if higher
    except ImportError:
        credits = 60 if (user_plan == 'free' and trial_active) else 0
    
    return render_template("mini_studio.html", credits=credits)