#!/usr/bin/env python3
"""
Referral API Endpoints for SoulBridge AI
Implements fraud-protected referral creation and management using new utilities
"""

import logging
from flask import Blueprint, jsonify, request, session
from datetime_utils import iso_z
from referral_utils import (
    create_referral_safe, reset_user_trial, get_referral_stats, 
    get_user_trial_status, DuplicateReferralError, FraudReferralError, ReferralError
)

logger = logging.getLogger(__name__)

# Create blueprint
referral_api_bp = Blueprint('referral_api', __name__, url_prefix='/api/referrals')

def get_client_info(request):
    """Extract client IP and User-Agent for fraud protection"""
    # Try to get real IP (accounting for proxies)
    client_ip = (
        request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or
        request.headers.get('X-Real-IP', '') or
        request.environ.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or
        request.environ.get('REMOTE_ADDR', 'unknown')
    )
    
    user_agent = request.headers.get('User-Agent', 'unknown')[:500]
    
    return client_ip, user_agent

@referral_api_bp.route('/create', methods=['POST'])
def create_referral():
    """
    Create a new referral with fraud protection
    
    Request body:
    {
        "referred_email": "friend@example.com",
        "referral_code": "REF12345" (optional)
    }
    """
    if not session.get('user_id'):
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    try:
        data = request.get_json()
        if not data or not data.get('referred_email'):
            return jsonify({"success": False, "error": "referred_email is required"}), 400
        
        user_id = session.get('user_id')
        user_email = session.get('user_email')
        referred_email = data['referred_email'].strip()
        referral_code = data.get('referral_code', f'REF{user_id}')
        
        if not user_email:
            return jsonify({"success": False, "error": "User email not found in session"}), 401
        
        # Get client info for fraud protection
        client_ip, user_agent = get_client_info(request)
        
        # Get database connection
        from database_utils import get_database
        db = get_database()
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 500
        
        conn = db.get_connection()
        
        # Create referral with fraud protection
        referral = create_referral_safe(
            conn, user_email, referred_email, referral_code, client_ip, user_agent
        )
        
        conn.close()
        
        return jsonify({
            "success": True,
            "referral": referral,
            "message": f"Successfully invited {referred_email}"
        })
        
    except DuplicateReferralError as e:
        return jsonify({"success": False, "error": str(e), "error_type": "duplicate"}), 409
    except FraudReferralError as e:
        return jsonify({"success": False, "error": str(e), "error_type": "fraud"}), 400
    except Exception as e:
        logger.error(f"❌ Failed to create referral: {e}")
        return jsonify({"success": False, "error": "Failed to create referral"}), 500

@referral_api_bp.route('/stats', methods=['GET'])
def get_referral_statistics():
    """Get referral statistics for current user"""
    if not session.get('user_id'):
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    try:
        user_id = session.get('user_id')
        
        # Get database connection
        from database_utils import get_database
        db = get_database()
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 500
        
        conn = db.get_connection()
        stats = get_referral_stats(conn, user_id)
        conn.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get referral stats: {e}")
        return jsonify({"success": False, "error": "Failed to get referral statistics"}), 500

@referral_api_bp.route('/trial/status', methods=['GET'])
def get_trial_status():
    """Get user's current trial status with proper ISO Z timestamps"""
    if not session.get('user_id'):
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    try:
        user_id = session.get('user_id')
        
        # Get database connection
        from database_utils import get_database
        db = get_database()
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 500
        
        conn = db.get_connection()
        trial_status = get_user_trial_status(conn, user_id)
        conn.close()
        
        return jsonify({
            "success": True,
            "trial": trial_status
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get trial status: {e}")
        return jsonify({"success": False, "error": "Failed to get trial status"}), 500

@referral_api_bp.route('/trial/reset', methods=['POST'])
def reset_trial():
    """
    Reset user's trial (admin/testing only)
    
    Request body:
    {
        "user_id": 123 (optional, defaults to current user),
        "hours": 5 (optional, defaults to 5),
        "credits": 60 (optional, defaults to 60)
    }
    """
    if not session.get('user_id'):
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    try:
        data = request.get_json() or {}
        
        # For security, only allow admins to reset other users' trials
        # For now, just allow users to reset their own
        target_user_id = session.get('user_id')
        hours = data.get('hours', 5)
        credits = data.get('credits', 60)
        
        # Validate inputs
        if not (1 <= hours <= 168):  # 1 hour to 1 week
            return jsonify({"success": False, "error": "hours must be between 1 and 168"}), 400
        if not (1 <= credits <= 1000):  # Reasonable credit range
            return jsonify({"success": False, "error": "credits must be between 1 and 1000"}), 400
        
        # Get database connection
        from database_utils import get_database
        db = get_database()
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 500
        
        conn = db.get_connection()
        trial = reset_user_trial(conn, target_user_id, hours, credits)
        conn.close()
        
        return jsonify({
            "success": True,
            "trial": trial,
            "message": f"Trial reset successfully: {hours}h, {credits} credits"
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to reset trial: {e}")
        return jsonify({"success": False, "error": "Failed to reset trial"}), 500

@referral_api_bp.route('/dashboard', methods=['GET'])  
def referral_dashboard():
    """
    Get referral dashboard data (updated version using new utilities)
    Replaces the old dashboard endpoint with proper error handling and ISO Z timestamps
    """
    if not session.get('user_id'):
        return jsonify({"success": False, "error": "Authentication required"}), 401
    
    try:
        user_id = session.get('user_id')
        
        # Get database connection
        from database_utils import get_database
        db = get_database()
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 500
        
        conn = db.get_connection()
        
        # Get referral stats and trial status
        stats = get_referral_stats(conn, user_id)
        trial_status = get_user_trial_status(conn, user_id)
        
        conn.close()
        
        # Combine the data for dashboard
        dashboard_data = {
            "referral_stats": {
                "total_referrals": stats.get('total_referrals', 0),
                "pending_referrals": stats.get('pending_referrals', 0), 
                "verified_referrals": stats.get('verified_referrals', 0),
                "rewarded_referrals": stats.get('rewarded_referrals', 0),
                "recent_referrals": stats.get('recent_referrals', [])
            },
            "trial": trial_status,
            "user": {
                "user_id": user_id,
                "email": stats.get('user_email', session.get('user_email'))
            },
            "timestamps": {
                "first_referral_at": stats.get('first_referral_at'),
                "latest_referral_at": stats.get('latest_referral_at')
            }
        }
        
        return jsonify({
            "success": True,
            "dashboard": dashboard_data
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get referral dashboard: {e}")
        return jsonify({"success": False, "error": "Failed to load dashboard"}), 500