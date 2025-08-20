#!/usr/bin/env python3
"""
Tiered Credit Pricing System - SoulBridge AI
Implements different credit costs per feature based on user tier
Creates upgrade incentives by making Max tier more cost-effective
"""

import logging
from datetime import datetime
from flask import session

logger = logging.getLogger(__name__)

# TIERED CREDIT COSTS (per feature, per tier)
CREDIT_COSTS = {
    "ai_images": {
        "bronze": 999,  # Not available to Bronze (locked)
        "free": 999,    # Legacy support - same as bronze 
        "silver": 5,    # Silver pays more (was: growth)
        "growth": 5,    # Legacy support - same as silver
        "gold": 2,      # Gold gets 60% discount (was: max)
        "max": 2        # Legacy support - same as gold
    },
    "voice_journaling": {
        "bronze": 999,  # Not available to Bronze (locked)
        "free": 999,    # Legacy support - same as bronze
        "silver": 4,    # Silver pays more (was: growth)
        "growth": 4,    # Legacy support - same as silver  
        "gold": 2,      # Gold gets 50% discount (was: max)
        "max": 2        # Legacy support - same as gold
    },
    "relationship_profiles": {
        "bronze": 999,  # Not available to Bronze (locked)
        "free": 999,    # Legacy support - same as bronze
        "silver": 8,    # Silver pays more (was: growth)
        "growth": 8,    # Legacy support - same as silver
        "gold": 3,      # Gold gets 62% discount (was: max)
        "max": 3        # Legacy support - same as gold
    },
    "meditations": {
        "bronze": 999,  # Not available to Bronze (locked)
        "free": 999,    # Legacy support - same as bronze
        "silver": 6,    # Silver pays more (was: growth)
        "growth": 6,    # Legacy support - same as silver
        "gold": 2,      # Gold gets 66% discount (was: max)
        "max": 2        # Legacy support - same as gold
    },
    "mini_studio": {
        "bronze": 999,  # Not available to Bronze (locked)
        "free": 999,    # Legacy support - same as bronze
        "silver": 999,  # Not available to Silver
        "growth": 999,  # Legacy support - same as silver
        "gold": 3,      # Exclusive to Gold (was: max)
        "max": 3        # Legacy support - same as gold
    }
}

# MONTHLY CREDIT ALLOWANCES
MONTHLY_ALLOWANCES = {
    "bronze": 0,    # Bronze tier gets no monthly credits
    "free": 0,      # Legacy support - same as bronze
    "silver": 100,  # Silver tier gets 100 monthly credits (was: growth)
    "growth": 100,  # Legacy support - same as silver
    "gold": 500,    # Gold tier gets 500 monthly credits (was: max)
    "max": 500      # Legacy support - same as gold
}

# CREDIT STORE BUNDLES (tier-specific pricing)
CREDIT_BUNDLES = {
    "silver": [
        {"credits": 50, "price": 4.99, "id": "silver_small"},
        {"credits": 120, "price": 9.99, "id": "silver_medium"}, 
        {"credits": 300, "price": 19.99, "id": "silver_large"}
    ],
    "growth": [  # Legacy support - same as silver
        {"credits": 50, "price": 4.99, "id": "growth_small"},
        {"credits": 120, "price": 9.99, "id": "growth_medium"}, 
        {"credits": 300, "price": 19.99, "id": "growth_large"}
    ],
    "gold": [
        {"credits": 150, "price": 4.99, "id": "gold_small"},   # Better value
        {"credits": 400, "price": 9.99, "id": "gold_medium"},  # Better value
        {"credits": 1000, "price": 19.99, "id": "gold_large"} # Better value
    ],
    "max": [  # Legacy support - same as gold
        {"credits": 150, "price": 4.99, "id": "max_small"},   # Better value
        {"credits": 400, "price": 9.99, "id": "max_medium"},  # Better value
        {"credits": 1000, "price": 19.99, "id": "max_large"} # Better value
    ]
}

def get_feature_cost(feature_name: str, user_plan: str) -> int:
    """
    Get the credit cost for a feature based on user's tier
    Returns higher cost for Growth, lower cost for Max
    """
    if feature_name not in CREDIT_COSTS:
        logger.warning(f"Unknown feature for credit cost: {feature_name}")
        return 1  # Default cost
    
    if user_plan not in CREDIT_COSTS[feature_name]:
        logger.warning(f"Unknown plan {user_plan} for feature {feature_name}")
        # Default to silver pricing if plan unknown (fallback order: silver -> growth -> bronze -> free)
        return CREDIT_COSTS[feature_name].get("silver", 
               CREDIT_COSTS[feature_name].get("growth",
               CREDIT_COSTS[feature_name].get("bronze",
               CREDIT_COSTS[feature_name].get("free", 1))))
    
    cost = CREDIT_COSTS[feature_name][user_plan]
    logger.info(f"💳 {feature_name} costs {cost} credits for {user_plan} tier")
    return cost

def calculate_savings_analysis(user_id: int, user_plan: str, monthly_usage: dict) -> dict:
    """
    Calculate how much a Growth user would save by upgrading to Max
    Used for upsell messaging
    
    monthly_usage = {
        "ai_images": 20,
        "voice_journaling": 10, 
        "meditations": 5,
        "relationship_profiles": 2
    }
    """
    if user_plan != "growth":
        return {"eligible": False}
    
    growth_total = 0
    max_total = 0
    
    for feature, usage_count in monthly_usage.items():
        if feature in CREDIT_COSTS:
            growth_cost = CREDIT_COSTS[feature]["growth"] * usage_count
            max_cost = CREDIT_COSTS[feature]["max"] * usage_count
            
            growth_total += growth_cost
            max_total += max_cost
    
    # Calculate if Growth user needs to buy topups
    growth_allowance = MONTHLY_ALLOWANCES["growth"]  # 100 credits
    max_allowance = MONTHLY_ALLOWANCES["max"]        # 500 credits
    
    growth_overage = max(0, growth_total - growth_allowance)
    max_overage = max(0, max_total - max_allowance)
    
    # Estimate topup costs (assuming $0.10 per credit)
    topup_cost_per_credit = 0.10
    
    growth_monthly_cost = 12.99 + (growth_overage * topup_cost_per_credit)
    max_monthly_cost = 19.99 + (max_overage * topup_cost_per_credit)
    
    savings = growth_monthly_cost - max_monthly_cost
    
    return {
        "eligible": True,
        "growth_credits_needed": growth_total,
        "max_credits_needed": max_total,
        "growth_overage": growth_overage,
        "max_overage": max_overage,
        "growth_monthly_cost": round(growth_monthly_cost, 2),
        "max_monthly_cost": round(max_monthly_cost, 2),
        "monthly_savings": round(savings, 2),
        "yearly_savings": round(savings * 12, 2),
        "should_show_upsell": savings > 5.00  # Show upsell if saves $5+/month
    }

def get_credit_bundles(user_plan: str) -> list:
    """Get available credit bundles for user's tier"""
    if user_plan not in CREDIT_BUNDLES:
        return []
    
    return CREDIT_BUNDLES[user_plan]

def log_credit_transaction(user_id: int, transaction_type: str, amount: int, feature: str = None, cost_per_credit: float = None):
    """
    Log credit transactions for analytics and refund tracking
    
    transaction_type: "earned", "spent", "purchased", "expired"
    """
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            logger.error("Database not available for credit transaction logging")
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Create transactions table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                transaction_type VARCHAR(20) NOT NULL,
                amount INTEGER NOT NULL,
                feature VARCHAR(50),
                cost_per_credit DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Insert transaction
        cursor.execute("""
            INSERT INTO credit_transactions 
            (user_id, transaction_type, amount, feature, cost_per_credit, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id, 
            transaction_type, 
            amount, 
            feature, 
            cost_per_credit,
            f"Session: {session.get('session_version', 'unknown')}"
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"💳 TRANSACTION: User {user_id} {transaction_type} {amount} credits for {feature}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to log credit transaction: {e}")
        return False

def get_upsell_message(user_id: int, user_plan: str, recent_spending: float) -> dict:
    """
    Generate personalized upsell messages based on user behavior
    """
    if user_plan != "growth":
        return {"show_upsell": False}
    
    # Heavy spender upsell
    if recent_spending > 15.00:  # Spent $15+ on topups this month
        potential_max_savings = recent_spending - 7.00  # Rough estimate
        return {
            "show_upsell": True,
            "type": "heavy_spender",
            "title": "You're spending too much on credits!",
            "message": f"You've spent ${recent_spending:.2f} on top-ups this month. Max tier would save you ~${potential_max_savings:.2f}/month with cheaper credit costs.",
            "cta": "Upgrade to Max & Save Money",
            "urgency": "high"
        }
    
    # Feature-specific upsell
    elif recent_spending > 5.00:
        return {
            "show_upsell": True,
            "type": "moderate_user", 
            "title": "Max tier = better value",
            "message": f"You've spent ${recent_spending:.2f} on credits. Max users get 60% cheaper credit costs + 5x monthly allowance.",
            "cta": "See Max Benefits",
            "urgency": "medium"
        }
    
    return {"show_upsell": False}

def apply_tiered_credit_deduction(user_id: int, feature_name: str, user_plan: str) -> dict:
    """
    Deduct credits using tiered pricing system
    Returns success status and transaction details
    """
    cost = get_feature_cost(feature_name, user_plan)
    
    # Import existing credit system
    from unified_tier_system import get_user_credits, deduct_credits
    
    # Check if user has enough credits
    current_credits = get_user_credits(user_id)
    if current_credits < cost:
        return {
            "success": False,
            "error": "insufficient_credits",
            "required": cost,
            "available": current_credits,
            "deficit": cost - current_credits
        }
    
    # Deduct credits
    success = deduct_credits(user_id, cost)
    if not success:
        return {
            "success": False,
            "error": "deduction_failed"
        }
    
    # Log transaction
    log_credit_transaction(user_id, "spent", cost, feature_name)
    
    # Get updated balance
    new_balance = get_user_credits(user_id)
    
    return {
        "success": True,
        "credits_spent": cost,
        "remaining_balance": new_balance,
        "tier_discount": f"Max users pay only {CREDIT_COSTS[feature_name]['max']} credits!" if user_plan == "growth" else None
    }