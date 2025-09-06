"""
SoulBridge AI - Stripe Payment Service
Extracted from app.py monolith for modular architecture
"""
import os
import logging
from flask import session, request
from .payment_config import (
    get_stripe_config, 
    is_stripe_configured,
    get_plan_price,
    get_plan_name,
    get_success_url,
    get_cancel_url,
    ADFREE_PRICE
)

logger = logging.getLogger(__name__)

class StripeService:
    """Handles Stripe payment processing"""
    
    def __init__(self):
        self.config = get_stripe_config()
        if self.config['secret_key']:
            import stripe
            stripe.api_key = self.config['secret_key']
            self.stripe = stripe
        else:
            self.stripe = None
    
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured"""
        return is_stripe_configured()
    
    def create_subscription_checkout(self, plan_type: str, billing: str, user_email: str) -> dict:
        """Create Stripe checkout session for subscription"""
        try:
            if not self.stripe:
                return {
                    "success": False,
                    "error": "Payment processing is being configured. Please try again later."
                }
            
            plan_name = get_plan_name(plan_type)
            price_cents = get_plan_price(plan_type, billing)
            base_url = request.host_url
            
            # Create checkout session
            checkout_session = self.stripe.checkout.Session.create(
                customer_email=user_email,
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'SoulBridge AI - {plan_name}',
                            'description': f'{billing.title()} subscription to {plan_name}',
                        },
                        'unit_amount': price_cents,
                        'recurring': {
                            'interval': 'year' if billing == 'yearly' else 'month'
                        }
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=get_success_url(base_url, plan_type),
                cancel_url=get_cancel_url(base_url, plan_type),
                metadata={
                    'plan_type': plan_type,
                    'user_email': user_email,
                    'billing_period': billing
                }
            )
            
            logger.info(f"Stripe subscription checkout created for {user_email}: {plan_type} ({billing})")
            
            return {
                "success": True,
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id
            }
            
        except Exception as e:
            logger.error(f"Stripe subscription checkout error: {e}")
            return {
                "success": False,
                "error": "Failed to create payment session"
            }
    
    def create_credits_checkout(self, credit_amount: int, credit_price: int, user_email: str) -> dict:
        """Create Stripe checkout session for credit purchase"""
        try:
            if not self.stripe:
                return {
                    "success": False,
                    "error": "Payment processing is being configured. Please try again later."
                }
            
            base_url = request.host_url
            
            # Create checkout session for one-time payment
            checkout_session = self.stripe.checkout.Session.create(
                customer_email=user_email,
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'SoulBridge AI - Artistic Time Credits',
                            'description': f'{credit_amount} additional artistic time credits',
                        },
                        'unit_amount': credit_price,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{base_url}credits/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{base_url}buy-credits",
                metadata={
                    'user_email': user_email,
                    'credit_amount': str(credit_amount),
                    'purchase_type': 'credits'
                }
            )
            
            logger.info(f"Stripe credits checkout created for {user_email}: {credit_amount} credits")
            
            return {
                "success": True,
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id
            }
            
        except Exception as e:
            logger.error(f"Stripe credits checkout error: {e}")
            return {
                "success": False,
                "error": "Failed to create payment session"
            }
    
    def create_adfree_checkout(self, user_email: str, billing: str = 'monthly') -> dict:
        """Create Stripe checkout session for ad-free subscription"""
        try:
            if not self.stripe:
                return {
                    "success": False,
                    "error": "Payment processing is being configured. Please try again later."
                }
            
            base_url = request.host_url
            
            # Calculate pricing based on billing period
            if billing == 'yearly':
                # Yearly pricing: $45/year (25% savings from $60)
                unit_amount = 4500  # $45.00
                interval = 'year'
                description = 'Remove ads from Bronze tier experience (Annual)'
            else:
                # Monthly pricing: $5/month
                unit_amount = ADFREE_PRICE  # $5.00
                interval = 'month'
                description = 'Remove ads from Bronze tier experience (Monthly)'
            
            # Create checkout session for ad-free subscription
            checkout_session = self.stripe.checkout.Session.create(
                customer_email=user_email,
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'SoulBridge AI - Ad-Free Experience',
                            'description': description,
                        },
                        'unit_amount': unit_amount,
                        'recurring': {
                            'interval': interval
                        }
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{base_url}payment/success?session_id={{CHECKOUT_SESSION_ID}}&plan=adfree",
                cancel_url=f"{base_url}plan-selection",
                metadata={
                    'user_email': user_email,
                    'subscription_type': 'adfree'
                }
            )
            
            logger.info(f"Stripe ad-free checkout created for {user_email}")
            
            return {
                "success": True,
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id
            }
            
        except Exception as e:
            logger.error(f"Stripe ad-free checkout error: {e}")
            return {
                "success": False,
                "error": "Failed to create payment session"
            }
    
    def retrieve_session(self, session_id: str) -> dict:
        """Retrieve Stripe checkout session"""
        try:
            if not self.stripe:
                return {"success": False, "error": "Stripe not configured"}
            
            session = self.stripe.checkout.Session.retrieve(session_id)
            return {"success": True, "session": session}
            
        except Exception as e:
            logger.error(f"Error retrieving Stripe session {session_id}: {e}")
            return {"success": False, "error": "Failed to retrieve session"}
    
    def handle_webhook(self, payload: str, signature: str) -> dict:
        """Handle Stripe webhook events"""
        try:
            if not self.stripe or not self.config['webhook_secret']:
                return {"success": False, "error": "Webhook not configured"}
            
            # Verify webhook signature
            event = self.stripe.Webhook.construct_event(
                payload, signature, self.config['webhook_secret']
            )
            
            logger.info(f"Stripe webhook received: {event['type']}")
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                return self._handle_checkout_completed(event)
            elif event['type'] == 'customer.subscription.updated':
                return self._handle_subscription_updated(event)
            elif event['type'] == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(event)
            else:
                logger.info(f"Unhandled webhook event type: {event['type']}")
                return {"success": True, "message": "Event type not handled"}
            
        except Exception as e:
            logger.error(f"Webhook handling error: {e}")
            return {"success": False, "error": "Webhook processing failed"}
    
    def _handle_checkout_completed(self, event) -> dict:
        """Handle successful checkout completion"""
        try:
            session = event['data']['object']
            metadata = session.get('metadata', {})
            
            logger.info(f"Checkout completed: {metadata}")
            
            # This would update user's subscription in database
            # Implementation would be extracted from the monolith
            
            return {"success": True, "message": "Checkout processed"}
            
        except Exception as e:
            logger.error(f"Error handling checkout completion: {e}")
            return {"success": False, "error": "Failed to process checkout"}
    
    def _handle_subscription_updated(self, event) -> dict:
        """Handle subscription updates"""
        # Implementation would be extracted from the monolith
        return {"success": True, "message": "Subscription update processed"}
    
    def _handle_subscription_deleted(self, event) -> dict:
        """Handle subscription cancellations"""
        # Implementation would be extracted from the monolith
        return {"success": True, "message": "Subscription deletion processed"}