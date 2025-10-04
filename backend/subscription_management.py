#!/usr/bin/env python3
"""
Subscription Management System - SoulBridge AI
Handles Growth/Max tier subscriptions, billing, and lifecycle management

Features:
1. Subscription creation and upgrades
2. Cancellation with grace periods
3. Credit allocation and reset logic
4. Stripe integration
5. Anti-abuse measures
"""

import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from flask import Blueprint, jsonify, request, session
from database_utils import format_query

logger = logging.getLogger(__name__)

# Create subscription management blueprint
subscription_bp = Blueprint('subscription', __name__, url_prefix='/subscription')

# Subscription pricing (matches CLAUDE.md spec)
SUBSCRIPTION_PLANS = {
    'growth': {
        'monthly': {'price': 12.99, 'credits': 100, 'stripe_price_id': 'price_growth_monthly'},
        'yearly': {'price': 117.00, 'credits': 100, 'stripe_price_id': 'price_growth_yearly', 'savings': 0.25}
    },
    'max': {
        'monthly': {'price': 19.99, 'credits': 500, 'stripe_price_id': 'price_max_monthly'},
        'yearly': {'price': 180.00, 'credits': 500, 'stripe_price_id': 'price_max_yearly', 'savings': 0.25}
    }
}

# ===============================
# SUBSCRIPTION MANAGEMENT ENDPOINTS
# ===============================

@subscription_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """Get available subscription plans and pricing"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_plan = session.get('user_plan', 'free')
    
    # Add user-specific context to plans
    plans = {}
    for plan_name, plan_data in SUBSCRIPTION_PLANS.items():
        plans[plan_name] = {
            'monthly': {
                'price': plan_data['monthly']['price'],
                'credits': plan_data['monthly']['credits'],
                'available': user_plan == 'free' or (user_plan == 'growth' and plan_name == 'max')
            },
            'yearly': {
                'price': plan_data['yearly']['price'],
                'credits': plan_data['yearly']['credits'],
                'savings_percent': int(plan_data['yearly']['savings'] * 100),
                'monthly_equivalent': round(plan_data['yearly']['price'] / 12, 2),
                'available': user_plan == 'free' or (user_plan == 'growth' and plan_name == 'max')
            }
        }
    
    return jsonify({
        'plans': plans,
        'current_plan': user_plan,
        'upgrade_available': user_plan in ['free', 'growth']
    })

@subscription_bp.route('/upgrade', methods=['POST'])
def upgrade_subscription():
    """Create or upgrade a subscription"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request data required"}), 400
    
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    current_plan = session.get('user_plan', 'free')
    
    plan_type = data.get('plan_type')  # 'growth' or 'max'
    billing_interval = data.get('billing_interval', 'monthly')  # 'monthly' or 'yearly'
    
    # Validation
    if plan_type not in SUBSCRIPTION_PLANS:
        return jsonify({"error": "Invalid plan type"}), 400
    
    if billing_interval not in ['monthly', 'yearly']:
        return jsonify({"error": "Invalid billing interval"}), 400
    
    # Check upgrade eligibility
    if current_plan == 'max':
        return jsonify({"error": "Already on highest tier"}), 409
    
    if current_plan == 'growth' and plan_type == 'growth':
        return jsonify({"error": "Already on Growth plan"}), 409
    
    try:
        # Create Stripe checkout session
        checkout_data = create_stripe_checkout_session(
            user_id, user_email, plan_type, billing_interval
        )
        
        if not checkout_data['success']:
            return jsonify({"error": checkout_data['error']}), 500
        
        # Log subscription attempt
        log_subscription_event(user_id, 'upgrade_initiated', {
            'plan_type': plan_type,
            'billing_interval': billing_interval,
            'current_plan': current_plan
        })
        
        return jsonify({
            'checkout_url': checkout_data['checkout_url'],
            'session_id': checkout_data['session_id'],
            'plan': {
                'type': plan_type,
                'billing': billing_interval,
                'price': SUBSCRIPTION_PLANS[plan_type][billing_interval]['price'],
                'credits': SUBSCRIPTION_PLANS[plan_type][billing_interval]['credits']
            }
        })
        
    except Exception as e:
        logger.error(f"Subscription upgrade failed: {e}")
        return jsonify({"error": "Upgrade failed"}), 500

@subscription_bp.route('/cancel', methods=['POST'])
def cancel_subscription():
    """Cancel user's subscription (keeps benefits until period end)"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session.get('user_id')
    current_plan = session.get('user_plan', 'free')
    
    if current_plan == 'free':
        return jsonify({"error": "No active subscription to cancel"}), 409
    
    try:
        # Get user's subscription
        from subscriptions_referrals_cosmetics_schema import get_user_subscription
        subscription = get_user_subscription(user_id)
        
        if not subscription:
            return jsonify({"error": "No active subscription found"}), 404
        
        # Cancel with Stripe
        cancel_result = cancel_stripe_subscription(subscription['stripe_subscription_id'])
        
        if not cancel_result['success']:
            return jsonify({"error": cancel_result['error']}), 500
        
        # Update database
        update_subscription_cancellation(subscription['id'], datetime.now(timezone.utc))
        
        # Log cancellation
        log_subscription_event(user_id, 'canceled', {
            'plan_type': subscription['plan_type'],
            'billing_interval': subscription['billing_interval'],
            'period_end': subscription['current_period_end']
        })
        
        return jsonify({
            'canceled': True,
            'effective_date': subscription['current_period_end'],
            'message': f"Your {subscription['plan_type'].title()} subscription has been canceled. You'll keep all benefits until {subscription['current_period_end']}."
        })
        
    except Exception as e:
        logger.error(f"Subscription cancellation failed: {e}")
        return jsonify({"error": "Cancellation failed"}), 500

@subscription_bp.route('/status', methods=['GET'])
def get_subscription_status():
    """Get detailed subscription status and billing info"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session.get('user_id')
    
    try:
        # Get subscription from database
        from subscriptions_referrals_cosmetics_schema import get_user_subscription
        subscription = get_user_subscription(user_id)
        
        if not subscription:
            return jsonify({
                'has_subscription': False,
                'plan': 'free',
                'status': 'active'
            })
        
        # Calculate next billing date
        next_billing = subscription['current_period_end']
        days_until_billing = (datetime.fromisoformat(next_billing) - datetime.now(timezone.utc)).days
        
        return jsonify({
            'has_subscription': True,
            'plan': subscription['plan_type'],
            'billing_interval': subscription['billing_interval'],
            'status': subscription['status'],
            'current_period_start': subscription['current_period_start'],
            'current_period_end': subscription['current_period_end'],
            'next_billing_date': next_billing,
            'days_until_billing': max(0, days_until_billing),
            'cancel_at_period_end': subscription['cancel_at_period_end'],
            'canceled_at': subscription['canceled_at'],
            'can_purchase_credits': subscription['status'] == 'active'
        })
        
    except Exception as e:
        logger.error(f"Failed to get subscription status: {e}")
        return jsonify({"error": "Status check failed"}), 500

# ===============================
# STRIPE INTEGRATION
# ===============================

def create_stripe_checkout_session(user_id: int, user_email: str, plan_type: str, billing_interval: str) -> Dict[str, Any]:
    """Create Stripe checkout session for subscription"""
    try:
        import stripe
        
        # Get plan details
        plan_data = SUBSCRIPTION_PLANS[plan_type][billing_interval]
        price_id = plan_data['stripe_price_id']
        
        # TODO: Set your Stripe secret key
        # stripe.api_key = "sk_test_..."
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer_email=user_email,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f'https://soulbridgeai.com/subscription/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url='https://soulbridgeai.com/subscription/cancel',
            metadata={
                'user_id': str(user_id),
                'plan_type': plan_type,
                'billing_interval': billing_interval
            }
        )
        
        return {
            'success': True,
            'checkout_url': session.url,
            'session_id': session.id
        }
        
    except Exception as e:
        logger.error(f"Stripe session creation failed: {e}")
        return {
            'success': False,
            'error': 'Payment system unavailable'
        }

def cancel_stripe_subscription(stripe_subscription_id: str) -> Dict[str, Any]:
    """Cancel Stripe subscription"""
    try:
        import stripe
        
        # Cancel at period end (keeps benefits until billing cycle ends)
        subscription = stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        return {
            'success': True,
            'period_end': subscription.current_period_end
        }
        
    except Exception as e:
        logger.error(f"Stripe cancellation failed: {e}")
        return {
            'success': False,
            'error': 'Cancellation system unavailable'
        }

# ===============================
# DATABASE OPERATIONS
# ===============================

def create_subscription_record(user_id: int, stripe_data: Dict[str, Any]) -> bool:
    """Create subscription record in database"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Calculate period dates
        period_start = datetime.fromtimestamp(stripe_data['current_period_start'], tz=timezone.utc)
        period_end = datetime.fromtimestamp(stripe_data['current_period_end'], tz=timezone.utc)
        
        cursor.execute(format_query("""
            INSERT INTO subscriptions (
                user_id, stripe_subscription_id, stripe_customer_id, 
                plan_type, billing_interval, status,
                current_period_start, current_period_end
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """), (
            user_id,
            stripe_data['id'],
            stripe_data['customer'],
            stripe_data['metadata']['plan_type'],
            stripe_data['metadata']['billing_interval'],
            stripe_data['status'],
            period_start,
            period_end
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Subscription created for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create subscription record: {e}")
        return False

def update_subscription_cancellation(subscription_id: int, canceled_at: datetime) -> bool:
    """Update subscription with cancellation details"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(format_query("""
            UPDATE subscriptions 
            SET cancel_at_period_end = TRUE, canceled_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """), (canceled_at, subscription_id))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update subscription cancellation: {e}")
        return False

def log_subscription_event(user_id: int, action: str, metadata: Dict[str, Any]) -> None:
    """Log subscription events for audit trail"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(format_query("""
            INSERT INTO subscription_history (user_id, action, metadata)
            VALUES (?, ?, ?)
        """), (user_id, action, json.dumps(metadata)))
        
        conn.commit()
        conn.close()
        
        logger.info(f"📝 Logged subscription event: {action} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to log subscription event: {e}")

# ===============================
# CREDIT ALLOCATION SYSTEM  
# ===============================

def allocate_monthly_credits(user_id: int, plan_type: str) -> bool:
    """Allocate monthly credits based on subscription plan"""
    try:
        from unified_tier_system import add_credits
        
        # Get credit allocation for plan
        if plan_type == 'growth':
            credits_to_add = 100
        elif plan_type == 'max':
            credits_to_add = 500
        else:
            return False  # Free users don't get monthly credits
        
        # Add credits to user's account
        success = add_credits(user_id, credits_to_add)
        
        if success:
            # Log credit allocation
            from tiered_credit_system import log_credit_transaction
            log_credit_transaction(user_id, "earned", credits_to_add, "monthly_allowance")
            
            logger.info(f"💰 Allocated {credits_to_add} monthly credits to user {user_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to allocate monthly credits: {e}")
        return False

def reset_monthly_credits_for_all_users():
    """Reset monthly credits for all active subscribers (run monthly)"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get all active subscribers
        cursor.execute(format_query("""
            SELECT user_id, plan_type 
            FROM subscriptions 
            WHERE status = 'active' AND cancel_at_period_end = FALSE
        """)
        
        subscribers = cursor.fetchall()
        conn.close()
        
        reset_count = 0
        for user_id, plan_type in subscribers:
            if allocate_monthly_credits(user_id, plan_type):
                reset_count += 1
        
        logger.info(f"🔄 Reset monthly credits for {reset_count} subscribers")
        return True
        
    except Exception as e:
        logger.error(f"Failed to reset monthly credits: {e}")
        return False

# ===============================
# ANTI-ABUSE MEASURES
# ===============================

def validate_subscription_eligibility(user_id: int) -> Tuple[bool, str]:
    """Validate user eligibility for subscription (anti-abuse)"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return False, "System unavailable"
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check for recent cancellations (prevent immediate re-subscription abuse)
        cursor.execute("""
            SELECT COUNT(*) FROM subscriptions 
            WHERE user_id = ? AND canceled_at > datetime('now', '-7 days')
        """, (user_id,))
        
        recent_cancellations = cursor.fetchone()[0]
        
        if recent_cancellations > 0:
            conn.close()
            return False, "Must wait 7 days after cancellation before resubscribing"
        
        # Check for excessive subscription churn
        cursor.execute(format_query("""
            SELECT COUNT(*) FROM subscription_history 
            WHERE user_id = ? AND action IN ('canceled', 'upgrade_initiated') 
            AND created_at > datetime('now', '-30 days')
        """), (user_id,))
        
        recent_changes = cursor.fetchone()[0]
        
        if recent_changes > 3:
            conn.close()
            return False, "Too many subscription changes this month"
        
        conn.close()
        return True, "Eligible"
        
    except Exception as e:
        logger.error(f"Subscription eligibility check failed: {e}")
        return False, "Validation failed"

# Export blueprint for app registration
def register_subscription_management(app):
    """Register subscription management blueprint with Flask app"""
    app.register_blueprint(subscription_bp)
    logger.info("📊 Subscription management registered successfully")