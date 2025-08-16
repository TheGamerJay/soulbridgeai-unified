#!/usr/bin/env python3
"""
Enhanced Webhook Handlers for Subscription Management
Handles Stripe webhooks with proper grace period logic
"""

import os
import logging
from datetime import datetime
from subscription_manager import cancel_subscription, ensure_subscription_schema

logger = logging.getLogger(__name__)

def handle_subscription_cancelled(event_data):
    """
    Handle customer.subscription.updated webhook when subscription is cancelled
    Implements grace period - user keeps benefits until current period ends
    """
    try:
        subscription = event_data
        
        # Get subscription details
        subscription_id = subscription.get("id")
        status = subscription.get("status")
        cancel_at_period_end = subscription.get("cancel_at_period_end", False)
        current_period_end = subscription.get("current_period_end")
        
        # Get user info from metadata
        metadata = subscription.get("metadata", {})
        app_user_id = metadata.get("app_user_id")
        
        if not app_user_id:
            logger.warning(f"No app_user_id in subscription {subscription_id} metadata")
            return False
        
        try:
            user_id = int(app_user_id)
        except ValueError:
            logger.warning(f"Invalid app_user_id in subscription {subscription_id}: {app_user_id}")
            return False
        
        # Convert timestamp to datetime
        if current_period_end:
            period_end_date = datetime.fromtimestamp(current_period_end)
        else:
            # Default to 30 days from now if no period end
            from datetime import timedelta
            period_end_date = datetime.utcnow() + timedelta(days=30)
        
        # Determine plan type from subscription items
        plan_type = "free"  # Default
        items = subscription.get("items", {}).get("data", [])
        for item in items:
            price_id = item.get("price", {}).get("id", "")
            if "growth" in price_id.lower() or "premium" in price_id.lower():
                plan_type = "growth"
            elif "max" in price_id.lower() or "enterprise" in price_id.lower():
                plan_type = "max"
            elif "ad" in price_id.lower() and "free" in price_id.lower():
                plan_type = "ad_free"
        
        # Handle cancellation based on status
        if cancel_at_period_end or status == "canceled":
            # Subscription is cancelled - implement grace period
            success = cancel_subscription(user_id, plan_type, period_end_date)
            
            if success:
                logger.info(f"🚫 WEBHOOK: Subscription {subscription_id} cancelled for user {user_id}, grace period until {period_end_date}")
                return True
            else:
                logger.error(f"Failed to cancel subscription for user {user_id}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling subscription cancelled webhook: {e}")
        return False

def handle_subscription_deleted(event_data):
    """
    Handle customer.subscription.deleted webhook
    This fires when subscription is permanently deleted (after grace period)
    """
    try:
        subscription = event_data
        subscription_id = subscription.get("id")
        
        # Get user info from metadata
        metadata = subscription.get("metadata", {})
        app_user_id = metadata.get("app_user_id")
        
        if app_user_id:
            try:
                user_id = int(app_user_id)
                
                # Force revert to free tier (grace period should already be handled)
                from subscription_manager import revert_to_free
                revert_to_free(user_id)
                
                logger.info(f"🗑️ WEBHOOK: Subscription {subscription_id} deleted, user {user_id} reverted to free")
                return True
                
            except ValueError:
                logger.warning(f"Invalid app_user_id in deleted subscription: {app_user_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling subscription deleted webhook: {e}")
        return False

def handle_invoice_payment_failed(event_data):
    """
    Handle invoice.payment_failed webhook
    Grace period should continue until subscription is actually cancelled
    """
    try:
        invoice = event_data
        subscription_id = invoice.get("subscription")
        
        if subscription_id:
            logger.info(f"💳 WEBHOOK: Payment failed for subscription {subscription_id}")
            # Note: Don't immediately cancel - Stripe will retry and may cancel later
            # Grace period logic will handle the eventual cancellation
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling payment failed webhook: {e}")
        return False

def register_webhook_handlers(app):
    """
    Register webhook handlers with Flask app
    """
    @app.route('/webhooks/stripe', methods=['POST'])
    def stripe_webhook():
        import stripe
        from flask import request, jsonify
        
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            return jsonify({"error": "Invalid payload"}), 400
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            return jsonify({"error": "Invalid signature"}), 400
        
        # Handle different webhook events
        event_type = event['type']
        event_data = event['data']['object']
        
        logger.info(f"📨 WEBHOOK: Received {event_type}")
        
        if event_type == 'customer.subscription.updated':
            handle_subscription_cancelled(event_data)
        elif event_type == 'customer.subscription.deleted':
            handle_subscription_deleted(event_data)
        elif event_type == 'invoice.payment_failed':
            handle_invoice_payment_failed(event_data)
        else:
            logger.info(f"📨 WEBHOOK: Unhandled event type {event_type}")
        
        return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    # Test schema creation
    ensure_subscription_schema()
    print("✅ Webhook handlers ready")