#!/usr/bin/env python3
"""
V1 API Implementation - SoulBridge AI
Implements the proposed API roadmap with clean, RESTful endpoints
"""

from flask import Blueprint, jsonify, request, session
from datetime import datetime, timezone
import logging
from unified_tier_system import (
    get_user_credits, 
    get_effective_plan, 
    get_feature_limit,
    can_access_feature,
    deduct_credits
)

# Create v1 API blueprint
v1_api = Blueprint('v1_api', __name__, url_prefix='/v1')
logger = logging.getLogger(__name__)

# ===============================
# AUTH / USER
# ===============================

@v1_api.route('/me', methods=['GET'])
def get_user_info():
    """Get current user information"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    return jsonify({
        "user_id": session.get('user_id'),
        "email": session.get('user_email'),
        "created_at": session.get('created_at', datetime.now(timezone.utc).isoformat())
    })

# ===============================
# ENTITLEMENTS (single source of truth)
# ===============================

@v1_api.route('/entitlements', methods=['GET'])
def get_entitlements():
    """
    Single source of truth for all user permissions and capabilities
    Consolidates: plan status, credits, feature flags, limits
    """
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session.get('user_id')
    user_plan = session.get('user_plan', 'free')
    trial_active = session.get('trial_active', False)
    trial_expires = session.get('trial_expires_at')
    
    # Get effective plan (trial gives max access)
    effective_plan = get_effective_plan(user_plan, trial_active)
    
    # Determine plan status
    if trial_active:
        plan_status = "trial"
        plan_name = "trial"
    elif user_plan in ['growth', 'max']:
        plan_status = "active"  # TODO: Check subscription status from Stripe
        plan_name = user_plan
    else:
        plan_status = "active"  # Free is always active
        plan_name = "free"
    
    # Get credit balances
    total_credits = get_user_credits(user_id)
    
    # TODO: Break down credits by type (monthly/topups/trial)
    # For now, simplified structure
    credits = {
        "monthly": {
            "remaining": total_credits if user_plan in ['growth', 'max'] else 0,
            "resets_at": "2025-09-16T10:00:00Z"  # TODO: Calculate from subscription
        },
        "topups": {
            "remaining": 0,  # TODO: Implement separate topup tracking
            "frozen": user_plan == 'free'
        },
        "trial": {
            "remaining": total_credits if trial_active else 0,
            "expires_at": trial_expires
        }
    }
    
    # Feature flags based on entitlements
    feature_flags = {
        "advanced_ai": effective_plan in ['growth', 'max', 'trial'] and total_credits > 0,
        "mini_studio": effective_plan == 'max' or (trial_active and total_credits > 0),
        "buy_topups_enabled": user_plan in ['growth', 'max']
    }
    
    # Ads configuration
    ads_enabled = user_plan == 'free'  # TODO: Check ad-free addon
    
    return jsonify({
        "plan": plan_name,
        "status": plan_status,
        "ads_enabled": ads_enabled,
        "period_end": trial_expires if trial_active else "2025-09-16T10:00:00Z",
        "cancel_at_period_end": False,  # TODO: Get from subscription
        "credits": credits,
        "feature_flags": feature_flags,
        "daily_limits": {
            "decoder": {
                "max": get_feature_limit(user_plan, 'decoder'),
                "remaining": get_feature_limit(user_plan, 'decoder') - session.get('decoder_usage', 0)
            },
            "fortune": {
                "max": get_feature_limit(user_plan, 'fortune'),
                "remaining": get_feature_limit(user_plan, 'fortune') - session.get('fortune_usage', 0)
            },
            "horoscope": {
                "max": get_feature_limit(user_plan, 'horoscope'),
                "remaining": get_feature_limit(user_plan, 'horoscope') - session.get('horoscope_usage', 0)
            }
        }
    })

# ===============================
# TRIAL
# ===============================

@v1_api.route('/trial/start', methods=['POST'])
def start_trial():
    """Start 5-hour trial for eligible users"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session.get('user_id')
    user_plan = session.get('user_plan', 'free')
    
    # Check eligibility
    if user_plan in ['growth', 'max']:
        return jsonify({"error": "trial_not_eligible"}), 403
    
    # Check if already used (TODO: Check database)
    if session.get('trial_used_permanently'):
        return jsonify({"error": "trial_already_used"}), 409
    
    # Start trial (simplified - should call existing start_trial logic)
    try:
        # Calculate expiry (5 hours from now)
        expires_at = datetime.now(timezone.utc).isoformat()
        
        # Set trial state
        session['trial_active'] = True
        session['trial_expires_at'] = expires_at
        session['effective_plan'] = 'max'
        
        return jsonify({
            "plan": "trial",
            "period_end": expires_at,
            "granted_credits": {
                "type": "trial",
                "amount": 60,
                "remaining": 60
            },
            "message": "5-hour trial started with 60 credits"
        }), 201
        
    except Exception as e:
        logger.error(f"Trial start failed: {e}")
        return jsonify({"error": "trial_start_failed"}), 500

# ===============================
# CREDITS
# ===============================

@v1_api.route('/credits', methods=['GET'])
def get_credits():
    """Get detailed credit balances"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session.get('user_id')
    user_plan = session.get('user_plan', 'free')
    trial_active = session.get('trial_active', False)
    
    total_credits = get_user_credits(user_id)
    
    return jsonify({
        "monthly": {
            "remaining": total_credits if user_plan in ['growth', 'max'] else 0,
            "resets_at": "2025-09-16T10:00:00Z"  # TODO: Calculate from billing cycle
        },
        "topups": {
            "remaining": 0,  # TODO: Implement separate topup tracking
            "frozen": user_plan == 'free'
        },
        "trial": {
            "remaining": total_credits if trial_active else 0,
            "expires_at": session.get('trial_expires_at')
        }
    })

@v1_api.route('/credits/spend', methods=['POST'])
def spend_credits():
    """
    Centralized credit spending endpoint
    Used by all features that require credits
    """
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json()
    if not data or 'amount' not in data:
        return jsonify({"error": "amount required"}), 400
    
    user_id = session.get('user_id')
    amount = data['amount']
    reason = data.get('reason', 'feature_usage')
    
    # Check if user has enough credits
    current_credits = get_user_credits(user_id)
    if current_credits < amount:
        return jsonify({"error": "insufficient_credits"}), 409
    
    # Deduct credits
    success = deduct_credits(user_id, amount)
    if not success:
        return jsonify({"error": "credit_deduction_failed"}), 500
    
    # Get updated balances
    new_credits = get_user_credits(user_id)
    
    # TODO: Log the transaction for audit trail
    logger.info(f"Credits spent: user={user_id}, amount={amount}, reason={reason}")
    
    return jsonify({
        "deducted": {
            "monthly": amount,  # Simplified - assume monthly bucket
            "topups": 0,
            "trial": 0
        },
        "balances": {
            "monthly": new_credits,
            "topups": 0,
            "trial": 0
        }
    })

# ===============================
# FEATURE EXAMPLE
# ===============================

@v1_api.route('/ai/advanced/generate', methods=['POST'])
def advanced_ai_generate():
    """
    Example of new credit-spending feature pattern
    1. Check entitlements
    2. Spend credits
    3. Perform task
    """
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "prompt required"}), 400
    
    user_id = session.get('user_id')
    credit_cost = data.get('credit_cost', 2)
    
    # Check entitlements
    if not can_access_feature(user_id, 'ai_images'):
        return jsonify({"error": "feature_not_available_on_plan"}), 403
    
    # Check credits
    current_credits = get_user_credits(user_id)
    if current_credits < credit_cost:
        return jsonify({"error": "insufficient_credits"}), 409
    
    # Spend credits
    success = deduct_credits(user_id, credit_cost)
    if not success:
        return jsonify({"error": "insufficient_credits"}), 409
    
    # TODO: Perform actual AI generation
    # For now, return mock response
    return jsonify({
        "job_id": f"job_{user_id}_{datetime.now().timestamp()}",
        "result_url": "https://example.com/generated-image.png",
        "credits_spent": credit_cost,
        "credits_remaining": get_user_credits(user_id)
    })

# ===============================
# Helper function for registration
# ===============================

def register_v1_api(app):
    """Register the v1 API blueprint with the Flask app"""
    app.register_blueprint(v1_api)
    logger.info("V1 API registered successfully")