# routes_me.py
# Lightweight /api/me endpoint for frontend access data

from flask import Blueprint, jsonify, session, request
import logging
from datetime import datetime, timezone, timedelta
# from app_core import current_user  # Avoid SQLAlchemy issues
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
        user_plan = session.get('user_plan', 'bronze')
        trial_active = bool(session.get('trial_active', False))
        trial_expires_at = session.get('trial_expires_at')
        
        # Map legacy plan names to current names (for migration compatibility)
        plan_mapping = {
            'free': 'bronze',
            'growth': 'silver', 
            'max': 'gold',
            'bronze': 'bronze',
            'silver': 'silver',
            'gold': 'gold'
        }
        plan = plan_mapping.get(user_plan, 'bronze')
        
        # Build access permissions from session data
        unlocked_tiers = ["bronze"]
        accessible_companion_tiers = ["bronze"]
        
        if plan in ['silver', 'gold'] or trial_active:
            unlocked_tiers.append("silver")
            accessible_companion_tiers.append("silver")
        
        if plan in ['gold'] or trial_active:
            unlocked_tiers.append("gold")
            accessible_companion_tiers.append("gold")
        
        # Set limits based on ACTUAL PLAN only (trial only unlocks access, not limits)
        if plan == 'gold':
            limits = {"decoder": 999, "fortune": 999, "horoscope": 999, "creative_writer": 999}
        elif plan == 'silver':
            limits = {"decoder": 15, "fortune": 8, "horoscope": 10, "creative_writer": 15}
        else:  # Bronze tier (trial users keep Bronze limits)
            limits = {"decoder": 3, "fortune": 3, "horoscope": 3, "creative_writer": 3}
        
        # Restore trial credits if session is missing them but trial is active
        trial_credits = session.get('trial_credits')
        if trial_active and (trial_credits is None or trial_credits == 0) and trial_expires_at:
            # Session lost trial credits but trial is still active
            now = datetime.now(timezone.utc)
            
            # Handle trial_expires_at - it might be a string or datetime object
            if isinstance(trial_expires_at, str):
                expires_dt = datetime.fromisoformat(trial_expires_at.replace("Z", "+00:00"))
            else:
                expires_dt = trial_expires_at
            
            # Check if trial has actually expired
            if now >= expires_dt:
                # Trial time is up - credits should be 0
                trial_credits = 0
                logger.info(f"⏰ Trial expired for user {uid}")
            else:
                # Trial still active - restore full credits (only usage should reduce them)
                trial_credits = 60
                logger.info(f"🔄 Restored full trial credits for user {uid}: {trial_credits}")
            
            session['trial_credits'] = trial_credits
        
        # Ensure trial_credits is always a number for the response
        if trial_credits is None:
            trial_credits = 0
        
        access = {
            "plan": plan,
            "trial_live": trial_active,
            "unlocked_tiers": unlocked_tiers,
            "accessible_companion_tiers": accessible_companion_tiers,
            "limits": limits,
            "trial_credits": trial_credits
        }
        
        # Get trainer credits from session (includes trial credits)
        artistic_time = session.get('artistic_time', 0)
        if access.get('trial_credits', 0) > 0:
            artistic_time += access['trial_credits']
        
        # Build response
        user_data = {
            "id": uid,
            "email": session.get("email", "unknown@soulbridgeai.com"),
            "displayName": session.get("display_name", "User"),
            "plan": plan,
            "artistic_time": artistic_time,
            "profileImage": session.get("profile_image", "/static/logos/IntroLogo.png"),
            "companion": session.get("selected_companion", "Blayzo")  # Current companion
        }
        
        access_data = {
            "trial_live": access.get("trial_live", False),
            "unlocked_tiers": access.get("unlocked_tiers", [plan]),
            "accessible_companion_tiers": access.get("accessible_companion_tiers", [plan]),
            "limits": access.get("limits", {"decoder": 3, "fortune": 3, "horoscope": 3, "creative_writer": 3}),
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
        # Get user ID from session (avoid SQLAlchemy issues)
        uid = session.get('user_id')
        
        if not uid:
            return jsonify({
                "success": False,
                "error": "Not authenticated"
            }), 401
        
        # Get trial state
        trial_active, trial_expires_at = db_get_trial_state(uid)
        
        # Get user plan to determine trial eligibility
        plan = db_get_user_plan(uid)
        
        # Only Bronze users can use trial (support legacy 'free' name)
        trial_eligible = (plan in ["bronze", "free"])
        
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
        # Get user ID from session (avoid SQLAlchemy issues)
        uid = session.get('user_id')
        
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
        # Get user ID from session (avoid SQLAlchemy issues)
        uid = session.get('user_id')
        
        if not uid:
            return jsonify({
                "success": False,
                "error": "Not authenticated"
            }), 401
        
        # Get current user plan
        plan = db_get_user_plan(uid)
        
        # Only Bronze users can activate trial (support legacy 'free' name)
        if plan not in ["bronze", "free"]:
            return jsonify({
                "success": False,
                "error": f"Trial is only available for Bronze users. You have {plan.title()} tier."
            }), 400
        
        # Check session trial state first (might be stale)
        session_trial = session.get('trial_active', False)
        session_expires = session.get('trial_expires_at')
        logger.info(f"🔍 SESSION DEBUG: trial_active={session_trial}, trial_expires_at={session_expires}")
        
        # Check if user already has an active trial
        trial_active, trial_expires_at = db_get_trial_state(uid)
        logger.info(f"🔍 DATABASE DEBUG: user_id={uid}, trial_active={trial_active}, trial_expires_at={trial_expires_at}")
        
        # Sync session with database state
        was_restored = False
        if not trial_active and session_trial:
            logger.info(f"🧹 CLEANING: Removing stale session trial data")
            session['trial_active'] = False
            session.pop('trial_expires_at', None)
            session.pop('trial_started_at', None)
            session.pop('trial_credits', None)
        elif trial_active and not session_trial and trial_expires_at:
            # Database shows active trial but session doesn't - restore to session
            now = datetime.now(timezone.utc)
            if now < trial_expires_at:
                logger.info(f"🔄 RESTORING: Database trial is active, updating session and database credits")
                session['trial_active'] = True
                session['trial_expires_at'] = trial_expires_at.isoformat()
                session['trial_credits'] = 60  # Restore full credits
                
                # Also restore trial credits in database if needed
                try:
                    if db.use_postgres:
                        cursor.execute("UPDATE users SET trial_credits = COALESCE(trial_credits, %s) WHERE id = %s", (60, uid))
                    else:
                        cursor.execute("UPDATE users SET trial_credits = COALESCE(trial_credits, ?) WHERE id = ?", (60, uid))
                    conn.commit()
                    logger.info(f"💳 Ensured trial credits in database for user {uid}")
                except Exception as e:
                    logger.error(f"Failed to restore trial credits in database: {e}")
                
                was_restored = True
        
        if trial_active and trial_expires_at and datetime.now(timezone.utc) < trial_expires_at:
            # If we just restored the trial to session, return success instead of error
            if was_restored:
                remaining_hours = (trial_expires_at - datetime.now(timezone.utc)).total_seconds() / 3600
                return jsonify({
                    "success": True,
                    "message": "Trial restored successfully!",
                    "trial": {
                        "active": True,
                        "expires_at": trial_expires_at.isoformat(),
                        "credits_granted": 60,
                        "unlocked_tiers": ["bronze", "silver", "gold"],
                        "hours_remaining": round(remaining_hours, 1)
                    }
                })
            else:
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
        
        # Initialize 60 trial credits in database (required for artistic_time_system)
        db = get_database()
        if db:
            try:
                conn = db.get_connection()
                cursor = conn.cursor()
                
                if db.use_postgres:
                    cursor.execute("UPDATE users SET trial_credits = %s WHERE id = %s", (60, uid))
                else:
                    cursor.execute("UPDATE users SET trial_credits = ? WHERE id = ?", (60, uid))
                
                conn.commit()
                conn.close()
                logger.info(f"💳 Initialized 60 trial credits in database for user {uid}")
            except Exception as e:
                logger.error(f"Failed to initialize trial credits in database: {e}")
        
        # Grant 60 trial credits in session (for backwards compatibility)
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
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in /api/trial/activate endpoint: {e}")
        logger.error(f"Full traceback: {error_details}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@bp_me.route("/trial/reset-session", methods=["POST"])
def trial_reset_session():
    """
    Reset trial session data (for debugging stale session issues).
    """
    try:
        uid = session.get('user_id')
        if not uid:
            return jsonify({"success": False, "error": "Not authenticated"}), 401
        
        # Clear all trial-related session data
        session['trial_active'] = False
        session.pop('trial_expires_at', None)
        session.pop('trial_started_at', None)
        session.pop('trial_credits', None)
        session.pop('trial_used_permanently', None)
        
        logger.info(f"🧹 RESET: Cleared all trial session data for user {uid}")
        
        return jsonify({
            "success": True,
            "message": "Trial session data cleared successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in trial session reset: {e}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@bp_me.route("/trial/reset", methods=["POST"])
def trial_reset():
    """
    Reset trial eligibility for testing (admin/dev function).
    """
    try:
        uid = session.get('user_id')
        if not uid:
            return jsonify({"success": False, "error": "Not authenticated"}), 401
        
        # Reset trial eligibility in database
        from database_utils import get_database
        db = get_database()
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 500
            
        conn = db.get_connection()
        try:
            # Clear all trial data - make user eligible again
            from sql_utils import adapt_placeholders, to_db_bool
            cursor = conn.cursor()
            q = "UPDATE users SET trial_active = %s, trial_started_at = NULL, trial_expires_at = NULL, trial_used_permanently = %s, trial_companion = NULL WHERE id = %s"
            q = adapt_placeholders(db, q)
            cursor.execute(q, (to_db_bool(db, False), to_db_bool(db, False), uid))
            conn.commit()
            
            # Clear session data too
            session['trial_active'] = False
            session.pop('trial_expires_at', None)
            session.pop('trial_started_at', None)
            session.pop('trial_credits', None)
            session['trial_used_permanently'] = False
            
            logger.info(f"🔄 RESET: Full trial reset completed for user {uid}")
            
            return jsonify({
                "success": True,
                "message": "Trial eligibility reset successfully! You can now activate your trial."
            })
            
        finally:
            conn.close()
        
    except Exception as e:
        logger.error(f"Error in trial reset: {e}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@bp_me.route("/trial/nuclear-reset", methods=["POST"])
def trial_nuclear_reset():
    """
    Nuclear option: Complete session wipe and trial reset.
    """
    try:
        uid = session.get('user_id')
        email = session.get('user_email')
        
        if not uid:
            return jsonify({"success": False, "error": "Not authenticated"}), 401
        
        # Reset in database
        from database_utils import get_database
        db = get_database()
        if db:
            conn = db.get_connection()
            try:
                from sql_utils import adapt_placeholders, to_db_bool
                cursor = conn.cursor()
                q = "UPDATE users SET trial_active = %s, trial_started_at = NULL, trial_expires_at = NULL, trial_used_permanently = %s, trial_companion = NULL WHERE id = %s"
                q = adapt_placeholders(db, q)
                cursor.execute(q, (to_db_bool(db, False), to_db_bool(db, False), uid))
                conn.commit()
                logger.info(f"💥 NUCLEAR: Database trial reset for user {uid}")
            finally:
                conn.close()
        
        # Nuclear session clear - remove EVERYTHING trial-related
        trial_keys = [k for k in session.keys() if 'trial' in k.lower()]
        for key in trial_keys:
            session.pop(key, None)
        
        # Force set to safe values
        session['trial_active'] = False
        session['trial_used_permanently'] = False
        
        logger.info(f"💥 NUCLEAR: Complete session reset for user {uid} ({email})")
        
        return jsonify({
            "success": True,
            "message": "Nuclear reset complete! Try trial activation now.",
            "cleared_keys": trial_keys
        })
        
    except Exception as e:
        logger.error(f"Error in nuclear reset: {e}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@bp_me.route("/trial/debug", methods=["GET"])
def trial_debug():
    """
    Debug endpoint to see all trial-related data.
    """
    try:
        uid = session.get('user_id')
        if not uid:
            return jsonify({"error": "Not authenticated"}), 401
            
        # Get all session data
        session_data = {k: v for k, v in session.items() if 'trial' in k.lower()}
        
        # Get database data
        from database_utils import get_database
        db = get_database()
        db_data = {}
        
        if db:
            conn = db.get_connection()
            try:
                from sql_utils import adapt_placeholders
                cursor = conn.cursor()
                q = "SELECT trial_active, trial_expires_at, trial_started_at, trial_used_permanently FROM users WHERE id = %s"
                q = adapt_placeholders(db, q)
                cursor.execute(q, (uid,))
                row = cursor.fetchone()
                
                if row:
                    db_data = {
                        "trial_active": bool(row[0]) if row[0] is not None else None,
                        "trial_expires_at": str(row[1]) if row[1] else None,
                        "trial_started_at": str(row[2]) if row[2] else None,
                        "trial_used_permanently": bool(row[3]) if row[3] is not None else None
                    }
            finally:
                conn.close()
        
        # Get what db_get_trial_state returns
        from db_users import db_get_trial_state
        trial_active, trial_expires_at = db_get_trial_state(uid)
        
        return jsonify({
            "user_id": uid,
            "session_data": session_data,
            "database_data": db_data,
            "db_get_trial_state": {
                "trial_active": trial_active,
                "trial_expires_at": str(trial_expires_at) if trial_expires_at else None
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@bp_me.route("/credits/purchase", methods=["POST"])
def credits_purchase():
    """
    Create Stripe checkout session for credit purchase.
    Only available for Silver and Gold tier subscribers.
    """
    try:
        # Get user ID from session (avoid SQLAlchemy issues)
        uid = session.get('user_id')
        
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
        
        # Check user plan - only Silver/Gold can purchase credits (support legacy names)
        plan = db_get_user_plan(uid)
        if plan not in ['silver', 'gold', 'growth', 'max']:
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

@bp_me.route("/trial/sql-reset", methods=["POST"])
def trial_sql_reset():
    """SQL-based trial reset for production database"""
    try:
        uid = session.get('user_id')
        
        if not uid or uid != 104:  # Security check
            return jsonify({"success": False, "error": "Not authorized"}), 403
        
        from database_utils import get_database
        db = get_database()
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 500
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Use PostgreSQL-compatible SQL
        sql = """
            UPDATE users SET 
                trial_active = %s,
                trial_used_permanently = %s,
                trial_expires_at = NULL,
                trial_started_at = NULL,
                trial_start = NULL,
                trial_companion = NULL
            WHERE id = %s
        """
        
        cursor.execute(sql, (False, False, uid))
        conn.commit()
        conn.close()
        
        # Clear session
        session.pop('trial_active', None)
        session.pop('trial_expires_at', None)
        session.pop('trial_started_at', None)
        session.pop('trial_credits', None)
        
        logger.info(f"🔧 SQL reset complete for user {uid}")
        
        return jsonify({
            "success": True,
            "message": "Trial reset complete via SQL - you can now activate fresh trial"
        })
        
    except Exception as e:
        logger.error(f"SQL reset error: {e}")
        return jsonify({
            "success": False,
            "error": f"SQL reset failed: {str(e)}"
        }), 500