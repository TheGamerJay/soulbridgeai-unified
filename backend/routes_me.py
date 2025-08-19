# routes_me.py
# Lightweight /api/me endpoint for frontend access data

from flask import Blueprint, jsonify, session, request
import logging
from datetime import datetime, timezone, timedelta
from app_core import current_user
from db_users import db_get_trial_state, db_get_user_plan, db_set_trial, db_fetch_user_row
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
        # Get user data from session (avoid DB calls to prevent SQLAlchemy issues)
        uid = session.get('user_id')
        user_authenticated = session.get('user_authenticated', False)
        
        if not uid or not user_authenticated:
            return jsonify({
                "success": False,
                "error": "Not authenticated"
            }), 401
        
        # Get all data from session to avoid database calls
        user_plan = session.get('user_plan', 'free')
        trial_active = bool(session.get('trial_active', False))
        trial_expires_at = session.get('trial_expires_at')
        
        # Map internal plan names to display names
        plan_mapping = {
            'free': 'bronze',
            'growth': 'silver',
            'max': 'gold'
        }
        plan = plan_mapping.get(user_plan, 'bronze')
        
        # Build access permissions from session data
        unlocked_tiers = ["bronze"]
        accessible_companion_tiers = ["bronze"]
        
        if user_plan in ['growth', 'max'] or trial_active:
            unlocked_tiers.append("silver")
            accessible_companion_tiers.append("silver")
        
        if user_plan == 'max' or trial_active:
            unlocked_tiers.append("gold")
            accessible_companion_tiers.append("gold")
        
        # Set limits based on plan
        if user_plan == 'max':
            limits = {"decoder": 999999, "fortune": 999999, "horoscope": 999999, "creative_writer": 999999}
        elif user_plan == 'growth':
            limits = {"decoder": 15, "fortune": 8, "horoscope": 10, "creative_writer": 20}
        else:
            limits = {"decoder": 3, "fortune": 2, "horoscope": 3, "creative_writer": 2}
        
        access = {
            "plan": plan,
            "trial_live": trial_active,
            "unlocked_tiers": unlocked_tiers,
            "accessible_companion_tiers": accessible_companion_tiers,
            "limits": limits,
            "trial_credits": 0
        }
        
        # Get trainer credits from session (includes trial credits)
        trainer_credits = session.get('trainer_credits', 0)
        if access.get('trial_credits', 0) > 0:
            trainer_credits += access['trial_credits']
        
        # Build response
        user_data = {
            "id": uid,
            "email": session.get("email", "unknown@soulbridgeai.com"),
            "displayName": session.get("display_name", "User"),
            "plan": plan,
            "trainer_credits": trainer_credits
        }
        
        access_data = {
            "trial_live": access.get("trial_live", False),
            "unlocked_tiers": access.get("unlocked_tiers", [plan]),
            "accessible_companion_tiers": access.get("accessible_companion_tiers", [plan]),
            "limits": access.get("limits", {"decoder": 3, "fortune": 2, "horoscope": 3, "creative_writer": 2}),
            "trial_credits": access.get("trial_credits", 0)
        }
        
        # Add trial information (always include for Bronze users)
        trial_data = None
        if plan == "bronze":
            # Handle trial_expires_at - it might be a string or datetime object
            expires_at_str = None
            if trial_expires_at:
                if isinstance(trial_expires_at, str):
                    expires_at_str = trial_expires_at
                else:
                    expires_at_str = trial_expires_at.isoformat()
            
            trial_data = {
                "active": trial_active,
                "eligible": True,  # Simplified for now
                "expires_at": expires_at_str,
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
        import traceback
        logger.error(f"Error in /api/me endpoint: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
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

@bp_me.route("/trial/activate", methods=["POST"])
def trial_activate():
    """
    Activate 5-hour trial for Bronze users.
    
    Requirements:
    - User must be Bronze tier
    - User must not have used trial before
    - Grants 60 trainer credits for 5 hours
    - Unlocks Silver/Gold tier access temporarily
    """
    try:
        cu = current_user()
        uid = cu.get("id")
        
        if not uid:
            return jsonify({
                "success": False,
                "error": "Not authenticated"
            }), 401
        
        # Get current user plan
        plan = db_get_user_plan(uid)
        
        # Only Bronze users can activate trial
        if plan != "bronze":
            return jsonify({
                "success": False,
                "error": f"Trial is only available for Bronze users. You have {plan.title()} tier."
            }), 400
        
        # Check if user already has an active trial
        trial_active, trial_expires_at = db_get_trial_state(uid)
        if trial_active and trial_expires_at and datetime.now(timezone.utc) < trial_expires_at:
            return jsonify({
                "success": False,
                "error": "You already have an active trial."
            }), 400
        
        # Check if user has used their trial before (one-time only)
        # Use session data to check if they've used trial permanently
        user_data = db_fetch_user_row(uid)
        if user_data and user_data.get('trial_used_permanently'):
            return jsonify({
                "success": False,
                "error": "You have already used your 5-hour trial. Each user can only use the trial once."
            }), 400
        
        # Activate 5-hour trial
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=5)
        
        # Set trial in database
        if not db_set_trial(uid, True, expires_at):
            return jsonify({
                "success": False,
                "error": "Failed to activate trial. Please try again."
            }), 500
        
        # Grant 60 trial credits in session
        session['trial_credits'] = 60
        session['trial_active'] = True
        session['trial_expires_at'] = expires_at.isoformat()
        
        logger.info(f"✅ Trial activated for user {uid}: 5 hours, 60 credits, expires at {expires_at}")
        
        return jsonify({
            "success": True,
            "message": "5-hour trial activated successfully!",
            "trial": {
                "active": True,
                "expires_at": expires_at.isoformat(),
                "credits_granted": 60,
                "unlocked_tiers": ["bronze", "silver", "gold"],
                "hours_remaining": 5.0
            }
        })
        
    except Exception as e:
        logger.error(f"Error in /api/trial/activate endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@bp_me.route("/credits/purchase", methods=["POST"])
def credits_purchase():
    """
    Create Stripe checkout session for credit purchase.
    Only available for Silver and Gold tier subscribers.
    """
    try:
        cu = current_user()
        uid = cu.get("id")
        
        if not uid:
            return jsonify({
                "success": False,
                "error": "Not authenticated"
            }), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        credits = data.get('credits')
        price = data.get('price')
        package_type = data.get('package_type', 'basic')
        
        if not credits or not price:
            return jsonify({
                "success": False,
                "error": "Credits and price are required"
            }), 400
        
        # Validate credit amounts and prices
        valid_packages = {
            'basic': {'credits': 350, 'price': 4.99},
            'popular': {'credits': 750, 'price': 9.99},
            'value': {'credits': 1200, 'price': 14.99}
        }
        
        if package_type not in valid_packages:
            return jsonify({
                "success": False,
                "error": "Invalid package type"
            }), 400
        
        expected = valid_packages[package_type]
        if credits != expected['credits'] or abs(price - expected['price']) > 0.01:
            return jsonify({
                "success": False,
                "error": "Invalid credit package parameters"
            }), 400
        
        # Check user plan - only Silver/Gold can purchase credits
        plan = db_get_user_plan(uid)
        if plan not in ['silver', 'gold']:
            return jsonify({
                "success": False,
                "error": "Credit purchases are only available for Silver and Gold subscribers"
            }), 403
        
        # Create Stripe checkout session
        import stripe
        import os
        
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        if not stripe.api_key:
            return jsonify({
                "success": False,
                "error": "Payment system not configured"
            }), 500
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{credits} Trainer Credits',
                        'description': f'Additional trainer time credits for SoulBridge AI - {package_type.title()} package'
                    },
                    'unit_amount': int(price * 100),  # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{os.environ.get('APP_DOMAIN', 'https://soulbridgeai.com')}/purchase-credits?success=true&credits={credits}",
            cancel_url=f"{os.environ.get('APP_DOMAIN', 'https://soulbridgeai.com')}/purchase-credits?cancelled=true",
            metadata={
                'user_id': str(uid),
                'credits': str(credits),
                'package_type': package_type,
                'type': 'credit_purchase'
            }
        )
        
        logger.info(f"💳 Created credit purchase checkout for user {uid}: {credits} credits for ${price}")
        
        return jsonify({
            "success": True,
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        })
        
    except Exception as e:
        logger.error(f"Error in /api/credits/purchase endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to create checkout session"
        }), 500