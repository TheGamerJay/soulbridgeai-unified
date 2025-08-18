# routes_me.py
# Lightweight /api/me endpoint for frontend access data

from flask import Blueprint, jsonify, session
import logging
from app_core import current_user
from db_users import db_get_trial_state, db_fetch_user_row, db_get_user_plan
from access import get_effective_access

logger = logging.getLogger(__name__)

bp_me = Blueprint("me", __name__, url_prefix="/api")

@bp_me.route("/me", methods=["GET"])
def me():
    """
    Lightweight endpoint for frontend to get user access permissions.
    
    Returns:
        - User basic info (id, email, displayName, plan)
        - Access permissions (trial_live, unlocked_tiers, limits)
        - Trial information
    """
    try:
        # Get current user from session
        cu = current_user()
        uid = cu.get("id")
        
        if not uid:
            return jsonify({
                "success": False,
                "error": "Not authenticated"
            }), 401
        
        # Get user plan (check both new and legacy columns)
        plan = db_get_user_plan(uid)
        
        # Get trial state from database
        trial_active, trial_expires_at = db_get_trial_state(uid)
        
        # Calculate effective access permissions
        access = get_effective_access(plan, trial_active, trial_expires_at)
        
        # Get trainer credits from session (includes trial credits)
        trainer_credits = session.get('trainer_credits', 0)
        if access.get('trial_credits', 0) > 0:
            trainer_credits += access['trial_credits']
        
        # Build response
        user_data = {
            "id": uid,
            "email": cu.get("email"),
            "displayName": cu.get("display_name"),
            "plan": access["plan"],
            "trainer_credits": trainer_credits
        }
        
        access_data = {
            "trial_live": access["trial_live"],
            "unlocked_tiers": access["unlocked_tiers"],
            "accessible_companion_tiers": access["accessible_companion_tiers"],
            "limits": access["limits"],
            "trial_credits": access.get("trial_credits", 0)
        }
        
        # Add trial expiration info if trial is active
        trial_data = None
        if access["trial_live"]:
            trial_data = {
                "active": True,
                "expires_at": trial_expires_at.isoformat() if trial_expires_at else None,
                "credits_remaining": access.get("trial_credits", 0)
            }
        
        response = {
            "success": True,
            "user": user_data,
            "access": access_data
        }
        
        if trial_data:
            response["trial"] = trial_data
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in /api/me endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@bp_me.route("/me/trial-status", methods=["GET"])
def trial_status():
    """
    Get detailed trial status for user.
    Separate endpoint for trial-specific information.
    """
    try:
        cu = current_user()
        uid = cu.get("id")
        
        if not uid:
            return jsonify({
                "success": False,
                "error": "Not authenticated"
            }), 401
        
        # Get trial state
        trial_active, trial_expires_at = db_get_trial_state(uid)
        
        # Get user plan to determine trial eligibility
        plan = db_get_user_plan(uid)
        
        # Only Bronze users can use trial
        trial_eligible = (plan == "bronze")
        
        # Calculate access during trial
        access = get_effective_access(plan, trial_active, trial_expires_at)
        
        trial_info = {
            "eligible": trial_eligible,
            "active": trial_active,
            "live": access["trial_live"],
            "expires_at": trial_expires_at.isoformat() if trial_expires_at else None,
            "credits_available": access.get("trial_credits", 0),
            "unlocked_tiers": access["unlocked_tiers"] if access["trial_live"] else [plan]
        }
        
        return jsonify({
            "success": True,
            "trial": trial_info
        })
        
    except Exception as e:
        logger.error(f"Error in /api/me/trial-status endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@bp_me.route("/me/access-check/<tier>", methods=["GET"])
def access_check(tier):
    """
    Check if user can access a specific tier.
    Used by frontend to enable/disable tier buttons.
    """
    try:
        cu = current_user()
        uid = cu.get("id")
        
        if not uid:
            return jsonify({
                "success": False,
                "error": "Not authenticated"
            }), 401
        
        # Validate tier
        valid_tiers = ["bronze", "silver", "gold"]
        if tier.lower() not in valid_tiers:
            return jsonify({
                "success": False,
                "error": "Invalid tier"
            }), 400
        
        # Get access permissions
        plan = db_get_user_plan(uid)
        trial_active, trial_expires_at = db_get_trial_state(uid)
        access = get_effective_access(plan, trial_active, trial_expires_at)
        
        # Check access
        can_access = tier.lower() in access["unlocked_tiers"]
        
        return jsonify({
            "success": True,
            "tier": tier.lower(),
            "can_access": can_access,
            "user_plan": plan,
            "trial_live": access["trial_live"]
        })
        
    except Exception as e:
        logger.error(f"Error in /api/me/access-check endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500