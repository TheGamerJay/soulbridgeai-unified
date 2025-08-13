"""
Cost Estimator + Rolling Usage Tracker
Estimates costs and tracks spending for OpenAI API usage
"""
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Redis connection with fallback
try:
    from redis import Redis
    redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    r = Redis.from_url(redis_url, decode_responses=True)
    # Test connection
    r.ping()
    REDIS_AVAILABLE = True
    logger.info("✅ Redis connected for spend tracking")
except Exception as e:
    logger.warning(f"Redis not available for spend tracking: {e}")
    r = None
    REDIS_AVAILABLE = False
    
    # File-based fallback for spend tracking
    import json
    from datetime import datetime
    SPEND_DIR = os.path.join(os.path.dirname(__file__), "data", "spend")
    os.makedirs(SPEND_DIR, exist_ok=True)

# Read prices from env ($ / 1K tokens)
def _pf(name: str, default: float) -> float:
    """Parse float from environment variable"""
    return float(os.getenv(name, str(default)))

PRICES = {
    "gpt-4o-mini": {
        "in": _pf("PRICE_GPT4O_MINI_IN", 0.0005), 
        "out": _pf("PRICE_GPT4O_MINI_OUT", 0.0015)
    },
    "gpt-4o": {
        "in": _pf("PRICE_GPT4O_IN", 0.005), 
        "out": _pf("PRICE_GPT4O_OUT", 0.015)
    },
    # Add more models as needed
    "gpt-3.5-turbo": {
        "in": _pf("PRICE_GPT35_IN", 0.001), 
        "out": _pf("PRICE_GPT35_OUT", 0.002)
    }
}

def estimate_cost(model: str, prompt_toks: int, completion_toks: int) -> float:
    """
    Estimate cost for a GPT API call
    
    Args:
        model: Model name (e.g., "gpt-4o-mini", "gpt-4o")
        prompt_toks: Number of prompt tokens
        completion_toks: Number of completion tokens
        
    Returns:
        Estimated cost in USD
    """
    # Get pricing for model, fallback to gpt-4o-mini if unknown
    p = PRICES.get(model) or PRICES.get("gpt-4o-mini")
    
    cost = (prompt_toks / 1000.0) * p["in"] + (completion_toks / 1000.0) * p["out"]
    
    logger.debug(f"Cost estimate for {model}: {prompt_toks}+{completion_toks} tokens = ${cost:.4f}")
    return cost

def add_spend(amount: float) -> bool:
    """
    Add spending amount to rolling monthly total
    
    Args:
        amount: Amount spent in USD
        
    Returns:
        True if successfully recorded, False otherwise
    """
    try:
        if REDIS_AVAILABLE:
            # Track rolling spend this month (coarse). Reset key monthly if you want.
            key = "spend:openai:month"
            pipe = r.pipeline()
            pipe.incrbyfloat(key, amount)
            pipe.execute()
            logger.info(f"Added ${amount:.4f} to monthly spend (Redis)")
        else:
            # File-based fallback
            from datetime import datetime
            month_key = datetime.now().strftime("%Y-%m")
            spend_file = os.path.join(SPEND_DIR, f"spend_{month_key}.json")
            
            # Read current spend
            current_spend = 0.0
            if os.path.exists(spend_file):
                try:
                    with open(spend_file, 'r') as f:
                        data = json.load(f)
                        current_spend = data.get("total_spend", 0.0)
                except (FileNotFoundError, json.JSONDecodeError):
                    current_spend = 0.0
            
            # Update spend
            current_spend += amount
            
            # Save back
            with open(spend_file, 'w') as f:
                json.dump({
                    "total_spend": current_spend,
                    "month": month_key,
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2)
            
            logger.info(f"Added ${amount:.4f} to monthly spend (file: {month_key})")
        
        return True
        
    except Exception as e:
        logger.error(f"Error adding spend: {e}")
        return False

def get_spend() -> float:
    """
    Get current monthly spending total
    
    Returns:
        Total spending this month in USD
    """
    try:
        if REDIS_AVAILABLE:
            v = r.get("spend:openai:month")
            spend = float(v) if v else 0.0
        else:
            # File-based fallback
            from datetime import datetime
            month_key = datetime.now().strftime("%Y-%m")
            spend_file = os.path.join(SPEND_DIR, f"spend_{month_key}.json")
            
            if os.path.exists(spend_file):
                with open(spend_file, 'r') as f:
                    data = json.load(f)
                    spend = data.get("total_spend", 0.0)
            else:
                spend = 0.0
        
        logger.debug(f"Current monthly spend: ${spend:.4f}")
        return spend
        
    except Exception as e:
        logger.error(f"Error getting spend: {e}")
        return 0.0

def get_spend_stats() -> Dict[str, Any]:
    """Get detailed spending statistics"""
    current_spend = get_spend()
    soft_budget = float(os.getenv("OPENAI_SOFT_BUDGET", "10.00"))
    buffer = float(os.getenv("OPENAI_BUDGET_BUFFER", "1.00"))
    
    return {
        "current_month_spend": current_spend,
        "soft_budget": soft_budget,
        "buffer": buffer,
        "budget_used_percent": (current_spend / soft_budget * 100) if soft_budget > 0 else 0,
        "approaching_limit": current_spend >= (soft_budget * 0.8),  # 80% threshold
        "over_budget": current_spend >= soft_budget,
        "storage_type": "redis" if REDIS_AVAILABLE else "file"
    }

def reset_monthly_spend() -> bool:
    """
    Reset monthly spend counter (useful for new month)
    
    Returns:
        True if reset successfully
    """
    try:
        if REDIS_AVAILABLE:
            r.delete("spend:openai:month")
            logger.info("Reset monthly spend counter (Redis)")
        else:
            # For file-based, we rely on month-specific files
            logger.info("File-based spend tracking uses monthly files automatically")
        
        return True
        
    except Exception as e:
        logger.error(f"Error resetting monthly spend: {e}")
        return False

def cleanup_old_spend_files(keep_months: int = 6) -> int:
    """
    Clean up old spend files (file storage only)
    
    Args:
        keep_months: Number of months to keep
        
    Returns:
        Number of files cleaned up
    """
    if REDIS_AVAILABLE:
        return 0  # Redis doesn't need cleanup
    
    try:
        from datetime import datetime, timedelta
        import os
        
        cutoff_date = datetime.now() - timedelta(days=keep_months * 30)  # Rough month calculation
        cutoff_str = cutoff_date.strftime("%Y-%m")
        
        cleaned = 0
        for filename in os.listdir(SPEND_DIR):
            if filename.startswith("spend_") and filename.endswith(".json"):
                # Extract month from filename
                try:
                    month_part = filename.replace("spend_", "").replace(".json", "")
                    if month_part < cutoff_str:
                        os.remove(os.path.join(SPEND_DIR, filename))
                        cleaned += 1
                        logger.info(f"Cleaned up old spend file: {filename}")
                except Exception:
                    continue
        
        return cleaned
        
    except Exception as e:
        logger.error(f"Error cleaning up spend files: {e}")
        return 0

if __name__ == "__main__":
    # Test the costing system
    print("Testing Cost Estimation and Spend Tracking...")
    
    print(f"Storage type: {'Redis' if REDIS_AVAILABLE else 'File-based'}")
    print(f"Model prices: {PRICES}")
    
    # Test cost estimation
    models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    for model in models:
        cost = estimate_cost(model, 300, 150)  # 300 input, 150 output tokens
        print(f"{model}: 300+150 tokens = ${cost:.4f}")
    
    # Test spend tracking
    print(f"\nCurrent spend: ${get_spend():.4f}")
    
    # Add some test spending
    test_spend = 0.05
    print(f"Adding test spend: ${test_spend:.4f}")
    add_spend(test_spend)
    
    print(f"New spend total: ${get_spend():.4f}")
    
    # Get stats
    stats = get_spend_stats()
    print(f"Spend stats: {stats}")
    
    print("\nCost estimation and spend tracking test completed!")