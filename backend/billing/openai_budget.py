"""
OpenAI Budget Monitoring System
Tracks remaining credits and prevents overspending with monthly budget windows
"""
import os
import requests
import logging
import datetime as dt
from typing import Optional

logger = logging.getLogger(__name__)

API = "https://api.openai.com/v1/dashboard/billing/credit_grants"
KEY = os.getenv("OPENAI_API_KEY", "")

def get_openai_remaining() -> Optional[float]:
    """
    Get remaining OpenAI credits to prevent overspending
    Returns None if unable to check (API key missing, network error, etc.)
    """
    if not KEY:
        logger.warning("No OpenAI API key found - budget monitoring disabled")
        return None
    
    try:
        # Check billing/credit_grants endpoint
        response = requests.get(
            API,
            headers={"Authorization": f"Bearer {KEY}"},
            timeout=12
        )
        
        if response.status_code != 200:
            logger.warning(f"OpenAI billing API returned {response.status_code}")
            return None
        
        data = response.json()
        remaining = float(data.get("total_available", 0.0))
        
        logger.info(f"OpenAI remaining credits: ${remaining:.2f}")
        return remaining
        
    except requests.RequestException as e:
        logger.error(f"Network error checking OpenAI budget: {e}")
        return None
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing OpenAI budget response: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error checking OpenAI budget: {e}")
        return None

def days_until_reset(reset_day: int = 1) -> int:
    """
    Calculate days until next month (assumes monthly reset on day 1)
    """
    today = dt.date.today()
    if today.month == 12:
        nextm = dt.date(today.year + 1, 1, 1)
    else:
        nextm = dt.date(today.year, today.month + 1, 1)
    return max(1, (nextm - today).days)

def check_budget_safe(min_remaining: float = None) -> bool:
    """
    Check if it's safe to make OpenAI API calls using soft budget system
    Returns True if budget is safe, False if we should use local AI
    """
    if min_remaining is None:
        min_remaining = float(os.getenv("OPENAI_BUDGET_BUFFER", "1.00"))
    
    remaining = get_openai_remaining()
    
    if remaining is None:
        # If we can't check budget, be conservative and use local
        logger.warning("Unable to check budget - defaulting to local AI")
        return False
    
    is_safe = remaining >= min_remaining
    
    if not is_safe:
        logger.warning(f"Budget protection activated: ${remaining:.2f} < ${min_remaining:.2f}")
    
    return is_safe

def get_budget_window_info() -> dict:
    """
    Get information about current budget window
    """
    remaining = get_openai_remaining()
    soft_budget = float(os.getenv("OPENAI_SOFT_BUDGET", "10.00"))
    buffer = float(os.getenv("OPENAI_BUDGET_BUFFER", "1.00"))
    days_left = days_until_reset()
    
    return {
        "remaining_credits": remaining,
        "soft_budget_monthly": soft_budget,
        "buffer_amount": buffer,
        "days_until_reset": days_left,
        "usable_amount": max(0.0, remaining - buffer) if remaining else 0.0,
        "daily_budget_available": (max(0.0, remaining - buffer) / days_left) if remaining and days_left > 0 else 0.0
    }

def get_budget_status() -> dict:
    """
    Get detailed budget status for monitoring/debugging
    """
    budget_info = get_budget_window_info()
    remaining = budget_info["remaining_credits"]
    buffer = budget_info["buffer_amount"]
    
    if remaining is None:
        return {
            "status": "unknown",
            "remaining": None,
            "safe": False,
            "reason": "Unable to check OpenAI budget",
            "budget_window": budget_info
        }
    
    is_safe = remaining >= buffer
    
    return {
        "status": "safe" if is_safe else "protected",
        "remaining": remaining,
        "min_threshold": buffer,
        "safe": is_safe,
        "reason": "Budget OK" if is_safe else f"Below ${buffer:.2f} buffer threshold",
        "budget_window": budget_info
    }

if __name__ == "__main__":
    # Test the budget monitoring
    print("Testing OpenAI Budget Monitoring...")
    
    status = get_budget_status()
    print(f"Budget Status: {status}")
    
    is_safe = check_budget_safe()
    print(f"Safe to use OpenAI: {is_safe}")
    
    remaining = get_openai_remaining()
    if remaining is not None:
        print(f"Remaining credits: ${remaining:.2f}")
    else:
        print("Could not retrieve budget information")