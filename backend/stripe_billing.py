"""
Enhanced Stripe Billing System for Ad-Free Subscriptions
Handles $5/month ad-free plan with proper webhook integration
"""
import os
import sqlite3
import psycopg2
import logging
from flask import Blueprint, request, jsonify, session
from typing import Optional, Dict, Any
from database_utils import format_query

# Stripe import with fallback
try:
    import stripe
except ImportError:
    stripe = None

logger = logging.getLogger(__name__)

# Create blueprint
bp_billing = Blueprint("billing", __name__, url_prefix="/api/billing")

# Stripe configuration
if stripe:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PRICE_ADFREE = os.getenv("STRIPE_PRICE_ADFREE", "price_1234567890")  # Your price ID
SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", "https://soulbridgeai.com/account?billing=success")
CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "https://soulbridgeai.com/account?billing=cancel")
PORTAL_RETURN_URL = os.getenv("STRIPE_PORTAL_RETURN_URL", "https://soulbridgeai.com/account")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

def get_db_connection():
    """Get database connection (SQLite or PostgreSQL)"""
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgresql'):
        return psycopg2.connect(database_url)
    else:
        db_path = os.path.join(os.path.dirname(__file__), 'soulbridge.db')
        return sqlite3.connect(db_path)

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Use correct placeholder based on database type
        database_url = os.getenv('DATABASE_URL')
        if database_url and database_url.startswith('postgresql'):
            placeholder = "%s"
        else:
            placeholder = "?"
            
        cursor.execute(f'''
            SELECT id, email, stripe_customer_id, stripe_subscription_id, ad_free, plan_type
            FROM users WHERE email = {placeholder}
        ''', (email,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'email': result[1], 
                'stripe_customer_id': result[2],
                'stripe_subscription_id': result[3],
                'ad_free': bool(result[4]),
                'plan_type': result[5]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Use correct placeholder based on database type
        database_url = os.getenv('DATABASE_URL')
        if database_url and database_url.startswith('postgresql'):
            placeholder = "%s"
        else:
            placeholder = "?"
            
        cursor.execute(f'''
            SELECT id, email, stripe_customer_id, stripe_subscription_id, ad_free, plan_type
            FROM users WHERE id = {placeholder}
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'email': result[1],
                'stripe_customer_id': result[2], 
                'stripe_subscription_id': result[3],
                'ad_free': bool(result[4]),
                'plan_type': result[5]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None

def update_user_ad_status(user_id: int, ad_free: bool, stripe_customer_id: str = None, stripe_subscription_id: str = None):
    """Update user's ad-free status and Stripe IDs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        updates = ["ad_free = ?"]
        params = [ad_free]
        
        if stripe_customer_id is not None:
            updates.append("stripe_customer_id = ?")
            params.append(stripe_customer_id)
            
        if stripe_subscription_id is not None:
            updates.append("stripe_subscription_id = ?") 
            params.append(stripe_subscription_id)
            
        params.append(user_id)
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        logger.info(f"Updated user {user_id}: ad_free={ad_free}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating user ad status: {e}")
        return False

def get_or_create_stripe_customer(user: Dict[str, Any]) -> Optional[str]:
    """Get existing Stripe customer or create new one"""
    if not stripe:
        logger.error("Stripe not available")
        return None
        
    if user.get('stripe_customer_id'):
        return user['stripe_customer_id']
        
    try:
        customer = stripe.Customer.create(
            email=user['email'],
            metadata={"app_user_id": str(user['id'])}
        )
        
        # Update user with customer ID
        update_user_ad_status(user['id'], user.get('ad_free', False), customer.id)
        
        return customer.id
        
    except Exception as e:
        logger.error(f"Error creating Stripe customer: {e}")
        return None

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current logged-in user"""
    # Debug: Log all session keys to understand what's available
    logger.info(f"🔍 BILLING DEBUG: Session keys: {list(session.keys())}")
    logger.info(f"🔍 BILLING DEBUG: user_authenticated={session.get('user_authenticated')}")
    logger.info(f"🔍 BILLING DEBUG: user_email={session.get('user_email')}")
    logger.info(f"🔍 BILLING DEBUG: user_id={session.get('user_id')}")
    
    # Try multiple possible session key combinations
    is_authenticated = (
        session.get('user_authenticated') or 
        session.get('logged_in') or
        session.get('user_id')
    )
    
    if not is_authenticated:
        logger.warning("🚫 BILLING: User not authenticated")
        return None
        
    email = session.get('user_email') or session.get('email')
    user_id = session.get('user_id')
    
    if not email and not user_id:
        logger.warning("🚫 BILLING: No email or user_id in session")
        return None
    
    # If we have user_id, try to get user by ID first (more reliable)
    if user_id:
        logger.info(f"🔍 BILLING: Getting user by ID: {user_id}")
        return get_user_by_id(user_id)
    
    # Fallback to email lookup
    logger.info(f"🔍 BILLING: Getting user by email: {email}")
    return get_user_by_email(email)

@bp_billing.route("/checkout-session/adfree", methods=["POST"])
def create_checkout_session_adfree():
    """Create Stripe checkout session for ad-free subscription"""
    if not stripe:
        return jsonify({"error": "Stripe not configured"}), 500
        
    user = get_current_user()
    if not user:
        return jsonify({"error": "Authentication required"}), 401
        
    # Check if user already has ad-free
    if user.get('ad_free'):
        return jsonify({"error": "Already subscribed to ad-free"}), 400
        
    customer_id = get_or_create_stripe_customer(user)
    if not customer_id:
        return jsonify({"error": "Failed to create customer"}), 500
        
    try:
        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": PRICE_ADFREE, "quantity": 1}],
            allow_promotion_codes=True,
            success_url=SUCCESS_URL,
            cancel_url=CANCEL_URL,
            subscription_data={"metadata": {"app_user_id": str(user['id'])}},
            metadata={"plan": "ad_free", "app_user_id": str(user['id'])}
        )
        
        logger.info(f"Created checkout session for user {user['id']}: {checkout_session.id}")
        return jsonify({"url": checkout_session.url})
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return jsonify({"error": "Failed to create checkout session"}), 500

@bp_billing.route("/portal", methods=["POST"])
def billing_portal():
    """Create Stripe billing portal session"""
    if not stripe:
        return jsonify({"error": "Stripe not configured"}), 500
        
    user = get_current_user()
    if not user or not user.get('stripe_customer_id'):
        return jsonify({"error": "No customer account found"}), 400
        
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=user['stripe_customer_id'],
            return_url=PORTAL_RETURN_URL
        )
        
        return jsonify({"url": portal_session.url})
        
    except Exception as e:
        logger.error(f"Error creating portal session: {e}")
        return jsonify({"error": "Failed to create portal session"}), 500

@bp_billing.route("/status")
def billing_status():
    """Get user's billing status"""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Authentication required"}), 401
        
    return jsonify({
        "ad_free": user.get('ad_free', False),
        "has_stripe_customer": bool(user.get('stripe_customer_id')),
        "has_subscription": bool(user.get('stripe_subscription_id'))
    })

@bp_billing.route("/webhook", methods=["POST"])
def stripe_webhook():
    """Handle Stripe webhooks for subscription events"""
    if not stripe or not WEBHOOK_SECRET:
        logger.error("Stripe webhook not properly configured")
        return "Webhook not configured", 400
        
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature", "")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except ValueError:
        logger.error("Invalid payload in webhook")
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in webhook")
        return "Invalid signature", 400
    
    def set_user_ad_free(app_user_id: int, ad_free: bool, subscription_id: str = None):
        """Helper to update user ad-free status"""
        user = get_user_by_id(app_user_id)
        if not user:
            logger.warning(f"User {app_user_id} not found for webhook")
            return
            
        update_user_ad_status(
            user_id=app_user_id,
            ad_free=ad_free,
            stripe_subscription_id=subscription_id
        )
        
        logger.info(f"Webhook updated user {app_user_id}: ad_free={ad_free}")
    
    event_type = event["type"]
    event_data = event["data"]["object"]
    
    logger.info(f"Processing webhook: {event_type}")
    
    # Handle subscription creation and updates
    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        subscription = event_data
        status = subscription.get("status")
        app_user_id = subscription.get("metadata", {}).get("app_user_id")
        
        if not app_user_id:
            logger.warning("No app_user_id in subscription metadata")
            return "OK", 200
            
        try:
            app_user_id = int(app_user_id)
        except ValueError:
            logger.warning(f"Invalid app_user_id: {app_user_id}")
            return "OK", 200
            
        # Check if this is our ad-free price
        line_items = subscription.get("items", {}).get("data", [])
        price_ids = [item["price"]["id"] for item in line_items]
        
        if PRICE_ADFREE in price_ids:
            is_active = status in ("active", "trialing")
            set_user_ad_free(app_user_id, is_active, subscription["id"])
    
    # Handle subscription deletion (cancellation)
    elif event_type == "customer.subscription.deleted":
        subscription = event_data
        app_user_id = subscription.get("metadata", {}).get("app_user_id")
        
        if app_user_id:
            try:
                app_user_id = int(app_user_id)
                set_user_ad_free(app_user_id, False, None)
            except ValueError:
                logger.warning(f"Invalid app_user_id in deletion: {app_user_id}")
    
    # Handle payment failures
    elif event_type == "invoice.payment_failed":
        invoice = event_data
        subscription_id = invoice.get("subscription")
        
        if subscription_id:
            # Find user by subscription ID and disable ad-free
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    format_query("SELECT id FROM users WHERE stripe_subscription_id = ?"),
                    (subscription_id,)
                )
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    user_id = result[0]
                    set_user_ad_free(user_id, False)
                    logger.info(f"Disabled ad-free for user {user_id} due to payment failure")
                    
            except Exception as e:
                logger.error(f"Error handling payment failure: {e}")
    
    return "OK", 200

# Error handlers
@bp_billing.errorhandler(Exception)
def handle_billing_error(error):
    logger.error(f"Billing error: {error}")
    return jsonify({"error": "Internal billing error"}), 500