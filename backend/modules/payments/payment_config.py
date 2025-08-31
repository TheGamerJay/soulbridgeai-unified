"""
SoulBridge AI - Payment Configuration
Extracted from app.py monolith for modular architecture
"""
import os
import logging

logger = logging.getLogger(__name__)

# Plan pricing in cents
PLAN_PRICES = {
    "monthly": {
        "silver": 1299,  # $12.99/month
        "gold": 1999     # $19.99/month
    },
    "yearly": {
        "silver": 11700,  # $117/year (25% savings)
        "gold": 18000     # $180/year (25% savings)
    }
}

# Plan display names
PLAN_NAMES = {
    "silver": "Silver Plan",
    "gold": "Gold Plan"
}

# Valid plans for payment
VALID_PLANS = ["silver", "gold"]

# Valid billing periods
VALID_BILLING_PERIODS = ["monthly", "yearly"]

# Ad-free upgrade pricing
ADFREE_PRICE = 500  # $5.00/month

def get_stripe_config() -> dict:
    """Get Stripe configuration from environment"""
    return {
        'secret_key': os.environ.get('STRIPE_SECRET_KEY'),
        'publishable_key': os.environ.get('STRIPE_PUBLISHABLE_KEY'),
        'webhook_secret': os.environ.get('STRIPE_WEBHOOK_SECRET'),
    }

def is_stripe_configured() -> bool:
    """Check if Stripe is properly configured"""
    config = get_stripe_config()
    return bool(config['secret_key'] and config['publishable_key'])

def get_plan_price(plan_type: str, billing: str) -> int:
    """Get price for plan in cents"""
    if plan_type not in VALID_PLANS or billing not in VALID_BILLING_PERIODS:
        return 0
    return PLAN_PRICES[billing][plan_type]

def get_plan_name(plan_type: str) -> str:
    """Get display name for plan"""
    return PLAN_NAMES.get(plan_type, f"{plan_type.title()} Plan")

def validate_plan_request(plan_type: str, billing: str) -> tuple:
    """Validate plan and billing parameters"""
    if plan_type not in VALID_PLANS:
        return False, f"Invalid plan type. Must be one of: {', '.join(VALID_PLANS)}"
    
    if billing not in VALID_BILLING_PERIODS:
        return False, f"Invalid billing period. Must be one of: {', '.join(VALID_BILLING_PERIODS)}"
    
    return True, "Valid"

def get_success_url(base_url: str, plan_type: str) -> str:
    """Generate success URL for Stripe checkout"""
    return f"{base_url}payment/success?session_id={{CHECKOUT_SESSION_ID}}&plan={plan_type}"

def get_cancel_url(base_url: str, plan_type: str) -> str:
    """Generate cancel URL for Stripe checkout"""
    return f"{base_url}payment/cancel?plan={plan_type}"