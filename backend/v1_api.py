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
from tiered_credit_system import (
    get_feature_cost,
    get_credit_bundles,
    apply_tiered_credit_deduction,
    get_upsell_message,
    MONTHLY_ALLOWANCES
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
    Simplified user entitlements - no trials, basic plan info
    """
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session.get('user_id')
    user_plan = session.get('user_plan', 'bronze')
    
    # Simplified feature limits based on plan
    feature_limits = {
        'bronze': {
            'decoder': 5,
            'fortune': 5,
            'horoscope': 5,
            'creative_writer': 5
        },
        'silver': {
            'decoder': 15,
            'fortune': 12,
            'horoscope': 10,
            'creative_writer': 15
        },
        'gold': {
            'decoder': 100,
            'fortune': 150,
            'horoscope': 50,
            'creative_writer': 75
        }
    }
    
    current_limits = feature_limits.get(user_plan, feature_limits['bronze'])
    
    return jsonify({
        "plan": user_plan,
        "status": "active",
        "tier": user_plan,
        "trial_active": False,  # No trials anymore
        "trial_remaining": 0,
        "ads_enabled": user_plan == 'bronze',
        "features": {
            "decoder": {
                "limit": current_limits['decoder'],
                "used": 0,  # TODO: Get actual usage
                "remaining": current_limits['decoder']
            },
            "fortune": {
                "limit": current_limits['fortune'],
                "used": 0,  # TODO: Get actual usage
                "remaining": current_limits['fortune']
            },
            "horoscope": {
                "limit": current_limits['horoscope'],
                "used": 0,  # TODO: Get actual usage
                "remaining": current_limits['horoscope']
            },
            "creative_writer": {
                "limit": current_limits['creative_writer'],
                "used": 0,  # TODO: Get actual usage
                "remaining": current_limits['creative_writer']
            }
        },
        "access_levels": {
            "bronze_companions": True,
            "silver_companions": user_plan in ['silver', 'gold'],
            "gold_companions": user_plan == 'gold',
            "mini_studio": user_plan == 'gold'
        }
    })

# ===============================
# CREDITS  
# ===============================

@v1_api.route('/credits', methods=['GET'])
def get_credits():
    """Get simplified credit balances"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_plan = session.get('user_plan', 'bronze')
    
    # Simplified credit system
    monthly_allowances = {
        'bronze': 0,
        'silver': 200,
        'gold': 500
    }
    
    return jsonify({
        "monthly": {
            "remaining": monthly_allowances.get(user_plan, 0),
            "max": monthly_allowances.get(user_plan, 0),
            "resets_at": "2025-02-01T00:00:00Z"
        },
        "topups": {
            "remaining": 0,
            "frozen": user_plan == 'bronze'
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
    user_plan = session.get('user_plan', 'bronze')
    
    # Check entitlements
    if not can_access_feature(user_id, 'ai_images'):
        return jsonify({"error": "feature_not_available_on_plan"}), 403
    
    # Use tiered pricing system
    result = apply_tiered_credit_deduction(user_id, 'ai_images', user_plan)
    
    if not result['success']:
        error_response = {"error": result['error']}
        if 'required' in result:
            error_response.update({
                "credits_required": result['required'],
                "credits_available": result['available'],
                "tier_cost": f"This costs {result['required']} credits for {user_plan} tier",
                "max_discount": result.get('tier_discount')
            })
        return jsonify(error_response), 409
    
    # TODO: Perform actual AI generation
    # For now, return mock response
    return jsonify({
        "job_id": f"job_{user_id}_{datetime.now().timestamp()}",
        "result_url": "https://example.com/generated-image.png",
        "credits_spent": result['credits_spent'],
        "credits_remaining": result['remaining_balance'],
        "tier_pricing": f"{user_plan.title()} tier: {result['credits_spent']} credits per image",
        "savings_tip": result.get('tier_discount')
    })

# ===============================
# CREDIT STORE
# ===============================

@v1_api.route('/credits/store', methods=['GET'])
def get_credit_store():
    """Get available credit bundles for user's tier"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session.get('user_id')
    user_plan = session.get('user_plan', 'bronze')
    
    # Bronze users see upsell
    if user_plan == 'bronze':
        return jsonify({
            "available": False,
            "message": "Subscribe to Silver or Gold to buy credits",
            "upgrade_url": "/subscription",
            "plans": [
                {"name": "Silver", "price": "$12.99/mo", "credits": "100/month"},
                {"name": "Gold", "price": "$19.99/mo", "credits": "500/month"}
            ]
        })
    
    # Get bundles and current balance
    bundles = get_credit_bundles(user_plan)
    current_balance = get_user_credits(user_id)
    
    # Check for upsell opportunities
    upsell = get_upsell_message(user_id, user_plan, 0)  # TODO: Calculate recent spending
    
    return jsonify({
        "available": True,
        "current_balance": current_balance,
        "bundles": bundles,
        "upsell": upsell,
        "tier_benefits": {
            "silver": "Silver tier pricing",
            "gold": "Gold tier gets better value!"
        }.get(user_plan)
    })

@v1_api.route('/credits/purchase', methods=['POST'])
def purchase_credits():
    """Purchase credits via Stripe"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json()
    if not data or 'bundle_id' not in data:
        return jsonify({"error": "bundle_id required"}), 400
    
    user_id = session.get('user_id')
    user_plan = session.get('user_plan', 'bronze')
    bundle_id = data['bundle_id']
    
    # Bronze users can't buy credits
    if user_plan == 'bronze':
        return jsonify({"error": "subscription_required"}), 403
    
    # Find the bundle
    bundles = get_credit_bundles(user_plan)
    bundle = next((b for b in bundles if b['id'] == bundle_id), None)
    
    if not bundle:
        return jsonify({"error": "invalid_bundle"}), 400
    
    # TODO: Create Stripe checkout session
    # For now, return mock response
    return jsonify({
        "checkout_url": f"https://checkout.stripe.com/mock/{bundle_id}",
        "bundle": bundle,
        "message": "Redirecting to payment..."
    })

# ===============================
# Helper function for registration
# ===============================

def register_v1_api(app):
    """Register the v1 API blueprint with the Flask app"""
    app.register_blueprint(v1_api)
    logger.info("V1 API registered successfully")