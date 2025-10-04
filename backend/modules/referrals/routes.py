"""
SoulBridge AI - Referral System Routes
Handle referral code generation, redemption, and tracking
"""
import logging
import random
import string
from datetime import datetime
from flask import Blueprint, request, session, jsonify
from ..auth.session_manager import requires_login, get_user_id
from database_utils import get_database
from .enhanced_rewards import check_and_grant_enhanced_rewards, get_user_referral_rewards
from database_utils import format_query

logger = logging.getLogger(__name__)

# ------------------ REFERRALS: CONFIG ------------------
REFERRAL_UNLOCK_THRESHOLDS = [2, 5, 8]  # make this match your setup (e.g. 2/5/8 or 2/5/10)
REFERRAL_CODE_LENGTH = 8

# Create blueprint for referral routes
referrals_bp = Blueprint('referrals', __name__, url_prefix='/api/referrals')

def current_user():
    """Get current user ID from session"""
    return get_user_id()

def generate_referral_code(n=REFERRAL_CODE_LENGTH):
    """Generate a unique referral code"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(random.choice(alphabet) for _ in range(n))

def ensure_user_has_code(user_id):
    """Create a unique referral_code for the user if missing."""
    db = get_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user already has a code
        cursor.execute(format_query(SELECT code FROM referral_codes WHERE user_id = ? AND is_active = 1"), (user_id,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Generate unique code
        while True:
            code = generate_referral_code()
            cursor.execute(format_query(SELECT id FROM referral_codes WHERE code = ?"), (code,))
            if not cursor.fetchone():
                break
        
        # Insert new code
        cursor.execute(format_query("""
            INSERT INTO referral_codes (user_id, code, is_active, created_at)
            VALUES (?, ?, 1, ?)
        """), (user_id, code, datetime.utcnow()))
        
        conn.commit()
        return code
        
    except Exception as e:
        logger.error(f"Error ensuring user has code: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_referral_stats(user_id):
    """Get referral statistics for user"""
    db = get_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Count total referrals for this user
        cursor.execute(format_query("""
            SELECT COUNT(*) FROM referrals 
            WHERE referrer_id = ? AND status = 'verified'
        """), (user_id,))
        
        result = cursor.fetchone()
        total = result[0] if result else 0
        
        # Compute unlocked thresholds
        unlocked = [t for t in REFERRAL_UNLOCK_THRESHOLDS if total >= t]
        
        # Find next unlock
        next_unlock = None
        for t in REFERRAL_UNLOCK_THRESHOLDS:
            if total < t:
                next_unlock = {"at": t, "remaining": t - total}
                break
        
        return {
            "total": total,
            "unlocked": unlocked,
            "next_unlock": next_unlock
        }
        
    except Exception as e:
        logger.error(f"Error getting referral stats: {e}")
        return {"total": 0, "unlocked": [], "next_unlock": None}
    finally:
        cursor.close()
        conn.close()

# --------------- ROUTES -----------------

@referrals_bp.route("/me", methods=["GET"])
@requires_login
def referrals_me():
    """Get current user's referral information"""
    user_id = current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Ensure user has a referral code
    code = ensure_user_has_code(user_id)
    if not code:
        return jsonify({"error": "Failed to generate referral code"}), 500
    
    # Get referral stats
    stats = get_referral_stats(user_id)
    
    # Check if user was referred by someone
    db = get_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    referred_by_user_id = None
    try:
        cursor.execute(format_query("""
            SELECT referrer_id FROM referrals 
            WHERE referred_id = ? AND status = 'verified'
        """), (user_id,))
        result = cursor.fetchone()
        if result:
            referred_by_user_id = result[0]
    except Exception as e:
        logger.error(f"Error checking referrer: {e}")
    finally:
        cursor.close()
        conn.close()
    
    # Get user's unlocked rewards (companions + skins) via referrals
    referral_rewards = get_user_referral_rewards(user_id)
    
    return jsonify({
        "code": code,
        "referred_by_user_id": referred_by_user_id,
        "stats": stats,
        "referral_rewards": referral_rewards
    })

@referrals_bp.route("/submit", methods=["POST"])
@requires_login
def referrals_submit():
    """
    Submit referral code
    Body: { "code": "ABCD1234" }
    Rules:
    - user must be logged in
    - they can only be referred once
    - no self-referrals
    - code must exist
    - idempotent (submitting after success returns the same state)
    """
    user_id = current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip().upper()
    if not code:
        return jsonify({"error": "No code provided"}), 400

    db = get_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if already referred
        cursor.execute(format_query("""
            SELECT referrer_id FROM referrals 
            WHERE referred_id = ? AND status = 'verified'
        """), (user_id,))
        
        existing = cursor.fetchone()
        if existing:
            referrer_id = existing[0]
            stats = get_referral_stats(referrer_id)
            return jsonify({
                "ok": True,
                "message": "You have already used a referral code.",
                "referrer_user_id": referrer_id,
                "stats_for_referrer": stats
            }), 200

        # Find referrer by code
        cursor.execute(format_query("""
            SELECT user_id FROM referral_codes 
            WHERE code = ? AND is_active = 1
        """), (code,))
        
        referrer_result = cursor.fetchone()
        if not referrer_result:
            return jsonify({"error": "Invalid referral code"}), 404
        
        referrer_id = referrer_result[0]
        if referrer_id == user_id:
            return jsonify({"error": "You cannot use your own referral code"}), 400

        # Check for existing referral record (idempotency)
        cursor.execute(format_query("""
            SELECT id FROM referrals 
            WHERE referred_id = ?
        """), (user_id,))
        
        if cursor.fetchone():
            stats = get_referral_stats(referrer_id)
            return jsonify({
                "ok": True,
                "message": "Referral already recorded.",
                "referrer_user_id": referrer_id,
                "stats_for_referrer": stats
            }), 200

        # Record referral
        cursor.execute(format_query("""
            INSERT INTO referrals (referrer_id, referred_id, referral_code, status, verified_at, created_at)
            VALUES (?, ?, ?, 'verified', ?, ?)
        """), (referrer_id, user_id, code, datetime.utcnow(), datetime.utcnow()))
        
        # Increment uses count
        cursor.execute(format_query("""
            UPDATE referral_codes 
            SET uses_count = uses_count + 1
            WHERE code = ?
        """), (code,))
        
        conn.commit()
        
        # Get updated stats for referrer
        old_stats = get_referral_stats(referrer_id) 
        new_total = old_stats["total"]
        old_total = new_total - 1  # Previous count before this referral
        
        # Check and grant referral rewards to the referrer (enhanced system)
        new_rewards = check_and_grant_enhanced_rewards(referrer_id, new_total, old_total)
        
        # Get final stats after potential rewards
        stats = get_referral_stats(referrer_id)

        response_data = {
            "ok": True,
            "message": "Referral applied successfully.",
            "referrer_user_id": referrer_id,
            "stats_for_referrer": stats
        }
        
        # Include newly unlocked rewards in response
        if new_rewards and new_rewards.get("total_new", 0) > 0:
            response_data["new_rewards"] = new_rewards
            response_data["message"] += f" {new_rewards['total_new']} new reward(s) unlocked!"
            if new_rewards.get("messages"):
                response_data["reward_messages"] = new_rewards["messages"]

        return jsonify(response_data), 200
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error submitting referral: {e}")
        return jsonify({"error": "Failed to process referral"}), 500
    finally:
        cursor.close()
        conn.close()

@referrals_bp.route("/rewards", methods=["GET"])
@requires_login
def get_user_rewards():
    """Get user's unlocked referral rewards (companions, skins, etc.)"""
    user_id = current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Get user's unlocked rewards (companions + skins)
        referral_rewards = get_user_referral_rewards(user_id)
        
        # Get current referral stats
        stats = get_referral_stats(user_id)
        
        return jsonify({
            "referral_rewards": referral_rewards,
            "stats": stats,
            "total_rewards": referral_rewards.get("total_rewards", 0)
        })
        
    except Exception as e:
        logger.error(f"Error getting user rewards: {e}")
        return jsonify({"error": "Failed to get rewards"}), 500

# Legacy endpoint for backwards compatibility
@referrals_bp.route("/info")
@requires_login
def get_referral_info_api():
    """Legacy API endpoint to get user's referral information"""
    return referrals_me()

# Legacy referral page (if needed)
@referrals_bp.route("/page")
@requires_login  
def referrals_page():
    """Legacy referral dashboard page"""
    from flask import render_template
    user_id = get_user_id()
    code = ensure_user_has_code(user_id)
    stats = get_referral_stats(user_id)
    
    return render_template("referrals.html", 
                         referral_code=code,
                         referral_count=stats["total"])

# Legacy redeem endpoint (redirects to new API)
@referrals_bp.route("/redeem-referral", methods=["POST"])
@requires_login
def redeem_referral():
    """Legacy API endpoint - redirects to new format"""
    return referrals_submit()