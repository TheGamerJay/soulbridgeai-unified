"""
Auto-Quota Calculator
Dynamically calculates safe per-user daily message quotas based on remaining budget
"""
import os
import math
import logging
from typing import Dict, Any
from .openai_budget import get_openai_remaining, days_until_reset
from .costing import PRICES

logger = logging.getLogger(__name__)

def auto_quota_tokens(model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Returns a safe per-user-per-day GPT message quota suggestion,
    using remaining $ and days left. Assumes a typical short reply.
    
    Args:
        model: OpenAI model to calculate for (default: gpt-4o-mini)
        
    Returns:
        Dict with quota information and reasoning
    """
    remaining = get_openai_remaining()
    
    if remaining is None:
        # Fallback to static limits from environment
        fallback_quota = int(os.getenv("COMP_MSG_LIMIT_PRO", "25"))
        return {
            "per_user_per_day": fallback_quota,
            "reason": "fallback-no-remaining",
            "static_fallback": True,
            "model": model
        }

    # Keep a buffer - never spend the last dollars
    buffer = float(os.getenv("OPENAI_BUDGET_BUFFER", "1.0"))
    safe = max(0.0, remaining - buffer)

    days = days_until_reset()
    if days <= 0:
        days = 1

    # Estimate average tokens per message (tune as you observe real usage)
    avg_in = 300   # user message + system prompt + context
    avg_out = int(os.getenv("COMP_MAX_TOKENS", "350"))  # cap companion replies

    # Get pricing for the model
    prices = PRICES.get(model) or PRICES["gpt-4o-mini"]
    cost_per_msg = (avg_in / 1000.0) * prices["in"] + (avg_out / 1000.0) * prices["out"]
    
    if cost_per_msg <= 0:
        cost_per_msg = 0.002  # Safety floor

    # Budget per day split across your expected active premium users
    # If you don't know active premium users, set a reasonable divisor
    expected_active_premium = int(os.getenv("EXPECTED_ACTIVE_PREMIUM", "10"))
    
    if expected_active_premium <= 0:
        expected_active_premium = 10  # Safety fallback

    daily_budget = safe / days
    per_user_daily = daily_budget / expected_active_premium / cost_per_msg

    # Clamp to sane range - minimum 3, maximum 100 per user per day
    min_quota = int(os.getenv("MIN_AUTO_QUOTA", "3"))
    max_quota = int(os.getenv("MAX_AUTO_QUOTA", "100"))
    
    q = max(min_quota, min(max_quota, int(math.floor(per_user_daily))))

    logger.info(f"Auto-quota calculated: {q} messages/user/day (${remaining:.2f} remaining, {days} days left)")

    return {
        "per_user_per_day": q,
        "reason": "auto-calculated",
        "remaining": remaining,
        "days": days,
        "cost_per_msg": cost_per_msg,
        "daily_budget": daily_budget,
        "expected_active_premium": expected_active_premium,
        "safe_budget": safe,
        "buffer": buffer,
        "model": model,
        "static_fallback": False
    }

def get_quota_for_plan(plan: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Get quota specifically for a user plan, with plan-specific logic
    
    Args:
        plan: User's subscription plan (bronze, silver, gold)
        model: OpenAI model to calculate for
        
    Returns:
        Quota information for the plan
    """
    plan = (plan or "bronze").lower()
    
    # Free users get static limits (usually 0 for OpenAI usage)
    if plan == "bronze":
        return {
            "per_user_per_day": int(os.getenv("COMP_MSG_LIMIT_FREE", "0")),
            "reason": "bronze-plan-static",
            "plan": plan,
            "uses_openai": False,
            "static_fallback": True
        }
    
    # Silver users get limited access
    elif plan == "silver":
        # Could use auto-quota but with more conservative limits
        auto_result = auto_quota_tokens(model)
        # Cap silver users to lower limits
        silver_max = int(os.getenv("COMP_MSG_LIMIT_SILVER", "15"))
        quota = min(auto_result["per_user_per_day"], silver_max)
        
        return {
            **auto_result,
            "per_user_per_day": quota,
            "plan": plan,
            "capped_at": silver_max,
            "reason": f"auto-capped-for-{plan}"
        }
    
    # Premium users (gold) get full auto-quota
    elif plan in ["gold"]:
        auto_result = auto_quota_tokens(model)
        
        # Apply plan-specific multipliers if desired
        multipliers = {
            "pro": 1.0,
            "vip": 1.2,   # 20% more for VIP
            "gold": 1.5    # 50% more for GOLD
        }
        
        multiplier = multipliers.get(plan, 1.0)
        base_quota = auto_result["per_user_per_day"]
        adjusted_quota = int(base_quota * multiplier)
        
        # Still respect max limits
        max_quota = int(os.getenv("MAX_AUTO_QUOTA", "100"))
        final_quota = min(adjusted_quota, max_quota)
        
        return {
            **auto_result,
            "per_user_per_day": final_quota,
            "plan": plan,
            "multiplier": multiplier,
            "base_quota": base_quota,
            "reason": f"auto-multiplied-for-{plan}"
        }
    
    else:
        # Unknown plan, treat as bronze
        return {
            "per_user_per_day": 0,
            "reason": "unknown-plan-default-bronze",
            "plan": plan,
            "uses_openai": False,
            "static_fallback": True
        }

def get_quota_recommendations() -> Dict[str, Any]:
    """
    Get quota recommendations for all plan types
    """
    plans = ["bronze", "silver", "gold"]
    recommendations = {}
    
    for plan in plans:
        recommendations[plan] = get_quota_for_plan(plan)
    
    # Add system-wide info
    auto_info = auto_quota_tokens()
    
    return {
        "by_plan": recommendations,
        "auto_quota_info": auto_info,
        "budget_window": {
            "remaining": get_openai_remaining(),
            "days_left": days_until_reset(),
            "expected_active_premium": int(os.getenv("EXPECTED_ACTIVE_PREMIUM", "10"))
        },
        "timestamp": auto_info  # Reuse timestamp logic
    }

def validate_quota_settings() -> Dict[str, Any]:
    """
    Validate that quota settings make sense
    """
    issues = []
    warnings = []
    
    # Check environment variables
    try:
        soft_budget = float(os.getenv("OPENAI_SOFT_BUDGET", "10.00"))
        buffer = float(os.getenv("OPENAI_BUDGET_BUFFER", "1.00"))
        
        if buffer >= soft_budget:
            issues.append(f"Buffer (${buffer}) >= soft budget (${soft_budget})")
        
        if soft_budget <= 0:
            issues.append("Soft budget must be positive")
            
        if buffer < 0:
            issues.append("Buffer must be non-negative")
            
    except ValueError as e:
        issues.append(f"Invalid budget values: {e}")
    
    # Check active premium user setting
    try:
        active_premium = int(os.getenv("EXPECTED_ACTIVE_PREMIUM", "10"))
        if active_premium <= 0:
            warnings.append("EXPECTED_ACTIVE_PREMIUM should be > 0")
            
        if active_premium > 1000:
            warnings.append("EXPECTED_ACTIVE_PREMIUM seems very high (>1000)")
            
    except ValueError:
        issues.append("EXPECTED_ACTIVE_PREMIUM must be an integer")
    
    # Check quota limits
    try:
        min_quota = int(os.getenv("MIN_AUTO_QUOTA", "3"))
        max_quota = int(os.getenv("MAX_AUTO_QUOTA", "100"))
        
        if min_quota > max_quota:
            issues.append(f"MIN_AUTO_QUOTA ({min_quota}) > MAX_AUTO_QUOTA ({max_quota})")
            
        if max_quota > 500:
            warnings.append("MAX_AUTO_QUOTA is very high (>500)")
            
    except ValueError:
        issues.append("Quota limit values must be integers")
    
    # Test auto-quota calculation
    try:
        auto_result = auto_quota_tokens()
        if auto_result.get("static_fallback"):
            warnings.append("Auto-quota using fallback (can't check OpenAI balance)")
    except Exception as e:
        issues.append(f"Auto-quota calculation failed: {e}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "settings": {
            "OPENAI_SOFT_BUDGET": os.getenv("OPENAI_SOFT_BUDGET", "10.00"),
            "OPENAI_BUDGET_BUFFER": os.getenv("OPENAI_BUDGET_BUFFER", "1.00"),
            "EXPECTED_ACTIVE_PREMIUM": os.getenv("EXPECTED_ACTIVE_PREMIUM", "10"),
            "MIN_AUTO_QUOTA": os.getenv("MIN_AUTO_QUOTA", "3"),
            "MAX_AUTO_QUOTA": os.getenv("MAX_AUTO_QUOTA", "100")
        }
    }

if __name__ == "__main__":
    # Test the auto-quota system
    print("Testing Auto-Quota Calculator...")
    
    # Validate settings first
    validation = validate_quota_settings()
    print(f"Settings validation: {'✅ Valid' if validation['valid'] else '❌ Issues found'}")
    if validation['issues']:
        print(f"Issues: {validation['issues']}")
    if validation['warnings']:
        print(f"Warnings: {validation['warnings']}")
    
    print(f"\nEnvironment settings: {validation['settings']}")
    
    # Test auto-quota calculation
    print(f"\n--- Auto Quota Calculation ---")
    for model in ["gpt-4o-mini", "gpt-4o"]:
        result = auto_quota_tokens(model)
        print(f"{model}: {result['per_user_per_day']} msgs/user/day")
        print(f"  Reason: {result['reason']}")
        if not result.get('static_fallback'):
            print(f"  Cost/msg: ${result['cost_per_msg']:.4f}")
            print(f"  Days left: {result['days']}")
            print(f"  Remaining: ${result['remaining']:.2f}")
    
    # Test plan-specific quotas
    print(f"\n--- Plan-Specific Quotas ---")
    plans = ["bronze", "silver", "gold"]
    for plan in plans:
        result = get_quota_for_plan(plan)
        print(f"{plan.upper()}: {result['per_user_per_day']} msgs/day ({result['reason']})")
    
    # Get full recommendations
    print(f"\n--- Full Recommendations ---")
    recs = get_quota_recommendations()
    print(f"Budget remaining: ${recs['budget_window']['remaining']:.2f}")
    print(f"Days until reset: {recs['budget_window']['days_left']}")
    print(f"Expected active premium users: {recs['budget_window']['expected_active_premium']}")
    
    print("\nAuto-quota testing completed!")