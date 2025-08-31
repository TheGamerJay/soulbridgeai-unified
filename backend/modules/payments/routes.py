"""
SoulBridge AI - Payment Routes
Extracted from app.py monolith for modular architecture
"""
import logging
from flask import Blueprint, render_template, request, session, jsonify, redirect, flash
from ..auth.session_manager import requires_login, get_user_id, get_user_email
from .stripe_service import StripeService
from .payment_config import validate_plan_request, VALID_PLANS

logger = logging.getLogger(__name__)

# Create blueprint for payment routes
payments_bp = Blueprint('payments', __name__)

@payments_bp.route("/payment")
@requires_login
def payment_page():
    """Payment selection page"""
    try:
        return render_template("payment.html")
        
    except Exception as e:
        logger.error(f"Error loading payment page: {e}")
        return render_template("error.html", error="Unable to load payment page")

@payments_bp.route("/api/create-checkout-session", methods=["POST"])
@requires_login
def create_checkout_session():
    """Create Stripe checkout session for plan subscription"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
        
        plan_type = data.get("plan_type")
        billing = data.get("billing", "monthly")
        
        # Validate plan request
        is_valid, error_msg = validate_plan_request(plan_type, billing)
        if not is_valid:
            return jsonify({"success": False, "error": error_msg}), 400
        
        # Get user email
        user_email = get_user_email()
        if not user_email:
            return jsonify({"success": False, "error": "User email not found"}), 400
        
        # Create Stripe checkout session
        stripe_service = StripeService()
        
        if not stripe_service.is_configured():
            return jsonify({
                "success": False, 
                "error": "Payment processing is being configured. Please try again later."
            }), 503
        
        result = stripe_service.create_subscription_checkout(plan_type, billing, user_email)
        
        if result["success"]:
            logger.info(f"Checkout session created for {user_email}: {plan_type} ({billing})")
            return jsonify(result)
        else:
            logger.error(f"Checkout session creation failed: {result['error']}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return jsonify({
            "success": False, 
            "error": "Payment system temporarily unavailable"
        }), 500

@payments_bp.route("/buy-credits")
@requires_login
def buy_credits_page():
    """Credit purchase page"""
    try:
        # Only Silver and Gold subscribers can buy credits
        user_plan = session.get('user_plan', 'bronze')
        if user_plan == 'bronze':
            flash("Credit purchases are available for Silver and Gold subscribers only.", "info")
            return redirect("/plan-selection")
        
        return render_template("buy_credits.html")
        
    except Exception as e:
        logger.error(f"Error loading buy credits page: {e}")
        return render_template("error.html", error="Unable to load credits page")

@payments_bp.route("/api/buy-credits", methods=["POST"])
@requires_login
def api_buy_credits():
    """API endpoint for credit purchase"""
    try:
        # Only Silver and Gold subscribers can buy credits
        user_plan = session.get('user_plan', 'bronze')
        if user_plan == 'bronze':
            return jsonify({
                "success": False, 
                "error": "Credit purchases are available for Silver and Gold subscribers only."
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
        
        credit_amount = data.get("credit_amount", 50)  # Default 50 credits
        credit_price = data.get("credit_price", 500)   # Default $5.00
        
        # Validate credit purchase
        if credit_amount <= 0 or credit_price <= 0:
            return jsonify({"success": False, "error": "Invalid credit amount or price"}), 400
        
        user_email = get_user_email()
        if not user_email:
            return jsonify({"success": False, "error": "User email not found"}), 400
        
        # Create Stripe checkout for credits
        stripe_service = StripeService()
        
        if not stripe_service.is_configured():
            return jsonify({
                "success": False, 
                "error": "Payment processing is being configured. Please try again later."
            }), 503
        
        result = stripe_service.create_credits_checkout(credit_amount, credit_price, user_email)
        
        if result["success"]:
            logger.info(f"Credits checkout created for {user_email}: {credit_amount} credits")
            return jsonify(result)
        else:
            logger.error(f"Credits checkout creation failed: {result['error']}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error creating credits checkout: {e}")
        return jsonify({
            "success": False, 
            "error": "Credit purchase system temporarily unavailable"
        }), 500

@payments_bp.route("/api/billing/checkout-session/adfree", methods=["POST"])
@requires_login
def create_adfree_checkout():
    """Create ad-free subscription checkout"""
    try:
        # Only Bronze users can subscribe to ad-free
        user_plan = session.get('user_plan', 'bronze')
        if user_plan != 'bronze':
            return jsonify({
                "success": False, 
                "error": "Ad-free subscription is only available for Bronze tier users."
            }), 403
        
        user_email = get_user_email()
        if not user_email:
            return jsonify({"success": False, "error": "User email not found"}), 400
        
        # Create Stripe checkout for ad-free
        stripe_service = StripeService()
        
        if not stripe_service.is_configured():
            return jsonify({
                "success": False, 
                "error": "Payment processing is being configured. Please try again later."
            }), 503
        
        result = stripe_service.create_adfree_checkout(user_email)
        
        if result["success"]:
            logger.info(f"Ad-free checkout created for {user_email}")
            return jsonify(result)
        else:
            logger.error(f"Ad-free checkout creation failed: {result['error']}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error creating ad-free checkout: {e}")
        return jsonify({
            "success": False, 
            "error": "Ad-free subscription system temporarily unavailable"
        }), 500

@payments_bp.route("/payment/success")
@requires_login
def payment_success():
    """Payment success page"""
    try:
        session_id = request.args.get('session_id')
        plan = request.args.get('plan')
        
        if not session_id:
            flash("Payment session not found.", "error")
            return redirect("/plan-selection")
        
        # Verify payment with Stripe (optional)
        stripe_service = StripeService()
        if stripe_service.is_configured():
            result = stripe_service.retrieve_session(session_id)
            if not result["success"]:
                logger.warning(f"Could not verify payment session: {session_id}")
        
        # Show success message
        if plan == "adfree":
            flash("Ad-free subscription activated! Ads have been removed.", "success")
        else:
            plan_display = plan.title() if plan else "Premium"
            flash(f"{plan_display} subscription activated! Enjoy your enhanced features.", "success")
        
        return render_template("payment_success.html", plan=plan)
        
    except Exception as e:
        logger.error(f"Error in payment success: {e}")
        flash("Payment completed, but there was an issue loading the confirmation page.", "warning")
        return redirect("/profile")

@payments_bp.route("/payment/cancel")
@requires_login 
def payment_cancel():
    """Payment cancellation page"""
    try:
        plan = request.args.get('plan')
        flash("Payment was cancelled. You can try again anytime.", "info")
        return render_template("payment_cancel.html", plan=plan)
        
    except Exception as e:
        logger.error(f"Error in payment cancel: {e}")
        return redirect("/plan-selection")

@payments_bp.route("/credits/success")
@requires_login
def credits_success():
    """Credit purchase success page"""
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            flash("Credit purchase session not found.", "error")
            return redirect("/buy-credits")
        
        flash("Credits purchased successfully! They have been added to your account.", "success")
        return render_template("credits_success.html")
        
    except Exception as e:
        logger.error(f"Error in credits success: {e}")
        flash("Credits purchased successfully!", "success")
        return redirect("/profile")

@payments_bp.route("/api/user-credits", methods=["GET"])
@requires_login
def get_user_credits():
    """Get user's current credit balance"""
    try:
        user_id = get_user_id()
        if not user_id:
            return jsonify({"success": False, "error": "User not found"}), 400
        
        # Get credits from artistic time system
        from ..tiers.artistic_time import get_artistic_time
        total_credits = get_artistic_time(user_id)
        
        return jsonify({
            "success": True,
            "total_credits": total_credits,
            "user_plan": session.get('user_plan', 'bronze'),
            "trial_active": session.get('trial_active', False)
        })
        
    except Exception as e:
        logger.error(f"Error getting user credits: {e}")
        return jsonify({"success": False, "error": "Failed to get credits"}), 500

@payments_bp.route("/api/refresh-user-credits", methods=["POST"])
@requires_login
def refresh_user_credits():
    """Force refresh user's artistic time data from database"""
    try:
        user_id = get_user_id()
        if not user_id:
            return jsonify({"success": False, "error": "User ID not found"}), 400
        
        # Force initialize/refresh user data
        from ..shared.database import get_database
        from ..tiers.artistic_time import ensure_user_data_initialized, get_artistic_time
        
        db = get_database()
        if db:
            ensure_user_data_initialized(user_id, db)
        
        # Get fresh artistic time
        total_credits = get_artistic_time(user_id)
        
        logger.info(f"🔄 CREDITS REFRESHED - User {user_id}: {total_credits} artistic time")
        
        return jsonify({
            "success": True,
            "credits": total_credits,
            "message": "Credits refreshed successfully"
        })
        
    except Exception as e:
        logger.error(f"Error refreshing user credits: {e}")
        return jsonify({"success": False, "error": "Failed to refresh credits"}), 500