# stripe_checkout.py
# Stripe Checkout and Webhook system for Bronze/Silver/Gold subscriptions

import os
import stripe
import logging
from flask import Blueprint, request, jsonify, session
from app_core import current_user
from db_users import (
    db_attach_stripe_customer_id, 
    db_set_user_plan, 
    db_find_user_by_stripe_customer,
    db_get_user_plan
)

logger = logging.getLogger(__name__)

bp_stripe = Blueprint("stripe_checkout", __name__, url_prefix="/api/stripe")

# Stripe Configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Price IDs from environment
PRICE_SILVER_MONTHLY = os.environ.get('PRICE_SILVER_MONTHLY')
PRICE_SILVER_YEARLY = os.environ.get('PRICE_SILVER_YEARLY') 
PRICE_GOLD_MONTHLY = os.environ.get('PRICE_GOLD_MONTHLY')
PRICE_GOLD_YEARLY = os.environ.get('PRICE_GOLD_YEARLY')
PRICE_ADFREE = os.environ.get('PRICE_ADFREE')  # Ad-free addon

# App domain for redirects
APP_DOMAIN = os.environ.get("APP_DOMAIN", "https://soulbridgeai.com")

def set_user_plan(user_id, plan):
    """
    Update user plan in both database and session for instant UI response.
    """
    try:
        # Update database
        if db_set_user_plan(user_id, plan):
            # Mirror to session for instant UI feedback
            session["user_plan"] = plan
            session["plan"] = plan
            logger.info(f"Updated user {user_id} plan to {plan}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to set user plan: {e}")
        return False

@bp_stripe.route("/checkout", methods=["POST"])
def create_checkout():
    """
    Create Stripe Checkout session for Silver/Gold subscriptions.
    """
    try:
        data = request.get_json(force=True)
        plan = (data.get("plan") or "silver").lower()
        billing_cycle = (data.get("billing_cycle") or "monthly").lower()
        
        # Validate plan and billing cycle
        if plan not in ("silver", "gold"):
            return jsonify({"ok": False, "error": "Invalid plan"}), 400
            
        if billing_cycle not in ("monthly", "yearly"):
            return jsonify({"ok": False, "error": "Invalid billing cycle"}), 400

        # Get price ID based on plan and billing cycle
        price_mapping = {
            ("silver", "monthly"): PRICE_SILVER_MONTHLY,
            ("silver", "yearly"): PRICE_SILVER_YEARLY,
            ("gold", "monthly"): PRICE_GOLD_MONTHLY,
            ("gold", "yearly"): PRICE_GOLD_YEARLY,
        }
        
        price_id = price_mapping.get((plan, billing_cycle))
        if not price_id:
            return jsonify({"ok": False, "error": "Price not configured"}), 500

        # Check authentication
        user = current_user()
        if not user.get("id"):
            return jsonify({"ok": False, "error": "Not authenticated"}), 401

        user_id = user["id"]
        user_email = user.get("email")

        # Get or create Stripe customer
        customer_id = session.get("stripe_customer_id")
        if not customer_id:
            try:
                customer = stripe.Customer.create(
                    email=user_email,
                    metadata={"app_user_id": str(user_id)}
                )
                customer_id = customer.id
                db_attach_stripe_customer_id(user_id, customer_id)
                session["stripe_customer_id"] = customer_id
                logger.info(f"Created Stripe customer {customer_id} for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to create Stripe customer: {e}")
                return jsonify({"ok": False, "error": "Failed to create customer"}), 500

        # Create checkout session
        try:
            session_obj = stripe.checkout.Session.create(
                mode="subscription",
                customer=customer_id,
                line_items=[{"price": price_id, "quantity": 1}],
                automatic_payment_methods={"enabled": True},
                locale="auto",
                automatic_tax={"enabled": True},
                billing_address_collection="auto",
                tax_id_collection={"enabled": True},
                customer_update={"address": "auto", "name": "auto"},
                allow_promotion_codes=True,
                success_url=f"{APP_DOMAIN}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{APP_DOMAIN}/billing/cancelled",
                subscription_data={
                    "metadata": {
                        "plan": plan,
                        "billing_cycle": billing_cycle,
                        "app_user_id": str(user_id)
                    }
                },
            )
            
            return jsonify({"ok": True, "url": session_obj.url})
            
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            return jsonify({"ok": False, "error": "Failed to create checkout session"}), 500

    except Exception as e:
        logger.error(f"Checkout endpoint error: {e}")
        return jsonify({"ok": False, "error": "Internal server error"}), 500

@bp_stripe.route("/checkout/adfree", methods=["POST"])
def create_adfree_checkout():
    """
    Create Stripe Checkout session for ad-free addon (Bronze users only).
    """
    try:
        # Check authentication
        user = current_user()
        if not user.get("id"):
            return jsonify({"ok": False, "error": "Not authenticated"}), 401

        user_id = user["id"]
        user_email = user.get("email")
        
        # Check if user is Bronze tier (only Bronze can buy ad-free)
        current_plan = db_get_user_plan(user_id)
        if current_plan != "bronze":
            return jsonify({"ok": False, "error": "Ad-free addon is only for Bronze tier users"}), 400

        # Validate price configuration
        if not PRICE_ADFREE:
            return jsonify({"ok": False, "error": "Ad-free pricing not configured"}), 500

        # Get or create Stripe customer
        customer_id = session.get("stripe_customer_id")
        if not customer_id:
            try:
                customer = stripe.Customer.create(
                    email=user_email,
                    metadata={"app_user_id": str(user_id)}
                )
                customer_id = customer.id
                db_attach_stripe_customer_id(user_id, customer_id)
                session["stripe_customer_id"] = customer_id
            except Exception as e:
                logger.error(f"Failed to create Stripe customer for ad-free: {e}")
                return jsonify({"ok": False, "error": "Failed to create customer"}), 500

        # Create checkout session for ad-free subscription
        try:
            session_obj = stripe.checkout.Session.create(
                mode="subscription",
                customer=customer_id,
                line_items=[{"price": PRICE_ADFREE, "quantity": 1}],
                automatic_payment_methods={"enabled": True},
                locale="auto",
                success_url=f"{APP_DOMAIN}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{APP_DOMAIN}/billing/cancelled",
                subscription_data={
                    "metadata": {
                        "addon": "adfree",
                        "app_user_id": str(user_id)
                    }
                },
            )
            
            return jsonify({"ok": True, "url": session_obj.url})
            
        except Exception as e:
            logger.error(f"Failed to create ad-free checkout session: {e}")
            return jsonify({"ok": False, "error": "Failed to create checkout session"}), 500

    except Exception as e:
        logger.error(f"Ad-free checkout endpoint error: {e}")
        return jsonify({"ok": False, "error": "Internal server error"}), 500

@bp_stripe.route("/webhook", methods=["POST"])
def webhook():
    """
    Handle Stripe webhooks for subscription events.
    """
    payload = request.data
    sig = request.headers.get("Stripe-Signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload=payload, 
            sig_header=sig, 
            secret=STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid webhook payload")
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        return "Invalid signature", 400

    event_type = event["type"]
    event_object = event["data"]["object"]
    
    logger.info(f"Processing Stripe webhook: {event_type}")

    try:
        if event_type == "checkout.session.completed":
            handle_checkout_completed(event_object)
            
        elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
            handle_subscription_updated(event_object)
            
        elif event_type == "customer.subscription.deleted":
            handle_subscription_deleted(event_object)
            
        elif event_type == "invoice.payment_succeeded":
            handle_payment_succeeded(event_object)
            
        elif event_type == "invoice.payment_failed":
            handle_payment_failed(event_object)
            
        else:
            logger.info(f"Unhandled webhook event: {event_type}")

    except Exception as e:
        logger.error(f"Webhook processing error for {event_type}: {e}")
        return "Webhook processing failed", 500

    return jsonify({"received": True})

def handle_checkout_completed(session_obj):
    """Handle successful checkout completion."""
    customer_id = session_obj.get("customer")
    subscription_id = session_obj.get("subscription")
    
    if subscription_id and customer_id:
        # Get subscription details
        subscription = stripe.Subscription.retrieve(subscription_id)
        metadata = subscription.get("metadata", {})
        
        plan = metadata.get("plan")
        addon = metadata.get("addon")
        
        # Find user by customer ID
        user = db_find_user_by_stripe_customer(customer_id)
        
        if user and plan in ("silver", "gold"):
            # Update to Silver/Gold plan
            set_user_plan(user["id"], plan)
            logger.info(f"Checkout completed: User {user['id']} upgraded to {plan}")
            
        elif user and addon == "adfree":
            # Handle ad-free addon (plan stays Bronze, but addon is added)
            # Note: Addon handling would be implemented in session/database
            logger.info(f"Checkout completed: User {user['id']} added ad-free addon")

def handle_subscription_updated(subscription_obj):
    """Handle subscription creation or updates."""
    customer_id = subscription_obj.get("customer")
    status = subscription_obj.get("status")
    
    try:
        # Get price ID from subscription items
        items = subscription_obj.get("items", {}).get("data", [])
        if not items:
            return
            
        price_id = items[0].get("price", {}).get("id")
        
        # Map price ID to plan
        price_to_plan = {
            PRICE_SILVER_MONTHLY: "silver",
            PRICE_SILVER_YEARLY: "silver", 
            PRICE_GOLD_MONTHLY: "gold",
            PRICE_GOLD_YEARLY: "gold",
        }
        
        plan = price_to_plan.get(price_id)
        if not plan:
            # Check if it's ad-free addon
            if price_id == PRICE_ADFREE:
                logger.info(f"Ad-free subscription updated for customer {customer_id}")
                return
            else:
                logger.warning(f"Unknown price ID in subscription: {price_id}")
                return
        
        # Find user
        user = db_find_user_by_stripe_customer(customer_id)
        if not user:
            logger.warning(f"User not found for Stripe customer {customer_id}")
            return
        
        # Update plan based on subscription status
        if status in ("active", "trialing", "past_due"):
            set_user_plan(user["id"], plan)
            logger.info(f"Subscription updated: User {user['id']} plan set to {plan} (status: {status})")
        else:
            # Subscription inactive - revert to Bronze
            set_user_plan(user["id"], "bronze")
            logger.info(f"Subscription updated: User {user['id']} reverted to bronze (status: {status})")
            
    except Exception as e:
        logger.error(f"Error handling subscription update: {e}")

def handle_subscription_deleted(subscription_obj):
    """Handle subscription cancellation."""
    customer_id = subscription_obj.get("customer")
    
    # Find user and revert to Bronze plan
    user = db_find_user_by_stripe_customer(customer_id)
    if user:
        set_user_plan(user["id"], "bronze")
        logger.info(f"Subscription deleted: User {user['id']} reverted to bronze")

def handle_payment_succeeded(invoice_obj):
    """Handle successful payment."""
    customer_id = invoice_obj.get("customer")
    logger.info(f"Payment succeeded for customer {customer_id}")

def handle_payment_failed(invoice_obj):
    """Handle failed payment."""
    customer_id = invoice_obj.get("customer")
    logger.warning(f"Payment failed for customer {customer_id}")
    
    # Optionally implement grace period logic here