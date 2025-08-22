"""
User Quota Management System
Tracks daily usage limits per user with Redis or file fallback
"""
import os
import time
import json
import logging
from typing import Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try Redis first, fallback to file-based storage
try:
    from redis import Redis
    redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    redis_client = Redis.from_url(redis_url, decode_responses=True)
    # Test connection
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("✅ Redis connected for quota management")
except Exception as e:
    logger.warning(f"Redis not available, using file storage: {e}")
    redis_client = None
    REDIS_AVAILABLE = False
    
    # File-based fallback
    QUOTA_DIR = os.path.join(os.path.dirname(__file__), "data", "quotas")
    os.makedirs(QUOTA_DIR, exist_ok=True)

def companion_limit_for(plan: str) -> int:
    """Get daily companion message limit for a user plan"""
    plan = (plan or "bronze").lower()
    
    if plan in ["gold"]:
        return int(os.getenv("COMP_MSG_LIMIT_GOLD", "50"))
    elif plan in ["silver"]:
        return int(os.getenv("COMP_MSG_LIMIT_SILVER", "25"))
    else:  # bronze
        return int(os.getenv("COMP_MSG_LIMIT_BRONZE", "0"))

def _get_today_key() -> str:
    """Get today's date key for quota tracking"""
    return time.strftime("%Y-%m-%d")

def _redis_bump_and_check(user_id: str, plan: str) -> Tuple[int, int]:
    """Redis-based quota tracking"""
    today = _get_today_key()
    key = f"quota:{user_id}:companion:{today}"
    
    with redis_client.pipeline() as pipe:
        pipe.incr(key, 1)
        pipe.expire(key, 60 * 60 * 24 + 60)  # 24 hours + buffer
        used, _ = pipe.execute()
    
    limit = companion_limit_for(plan)
    return int(used), int(limit)

def _file_bump_and_check(user_id: str, plan: str) -> Tuple[int, int]:
    """File-based quota tracking fallback"""
    today = _get_today_key()
    quota_file = os.path.join(QUOTA_DIR, f"{user_id}_{today}.json")
    
    # Read current usage
    try:
        with open(quota_file, 'r') as f:
            data = json.load(f)
            used = data.get('used', 0)
    except (FileNotFoundError, json.JSONDecodeError):
        used = 0
    
    # Increment usage
    used += 1
    
    # Save back to file
    try:
        with open(quota_file, 'w') as f:
            json.dump({
                'used': used,
                'date': today,
                'user_id': user_id,
                'plan': plan
            }, f)
    except Exception as e:
        logger.error(f"Error saving quota file: {e}")
    
    limit = companion_limit_for(plan)
    return used, limit

def bump_and_check(user_id: str, plan: str) -> Tuple[int, int]:
    """
    Increment user's daily companion usage and return (used_today, limit_today)
    
    Args:
        user_id: User identifier
        plan: User's subscription plan
        
    Returns:
        Tuple of (used_count, daily_limit)
    """
    try:
        if REDIS_AVAILABLE:
            return _redis_bump_and_check(user_id, plan)
        else:
            return _file_bump_and_check(user_id, plan)
    except Exception as e:
        logger.error(f"Error in quota tracking: {e}")
        # Return conservative fallback
        limit = companion_limit_for(plan)
        return 999, limit  # Assume over limit to be safe

def get_usage(user_id: str, plan: str) -> Tuple[int, int]:
    """
    Get current usage without incrementing
    
    Returns:
        Tuple of (used_count, daily_limit)
    """
    try:
        today = _get_today_key()
        limit = companion_limit_for(plan)
        
        if REDIS_AVAILABLE:
            key = f"quota:{user_id}:companion:{today}"
            used = redis_client.get(key)
            used = int(used) if used else 0
        else:
            quota_file = os.path.join(QUOTA_DIR, f"{user_id}_{today}.json")
            try:
                with open(quota_file, 'r') as f:
                    data = json.load(f)
                    used = data.get('used', 0)
            except (FileNotFoundError, json.JSONDecodeError):
                used = 0
        
        return used, limit
        
    except Exception as e:
        logger.error(f"Error getting usage: {e}")
        limit = companion_limit_for(plan)
        return 0, limit

def cleanup_old_quotas():
    """Clean up old quota files (file storage only)"""
    if REDIS_AVAILABLE:
        return  # Redis handles expiration automatically
    
    try:
        cutoff_date = datetime.now() - timedelta(days=7)  # Keep 7 days
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        for filename in os.listdir(QUOTA_DIR):
            if filename.endswith('.json'):
                # Extract date from filename
                parts = filename.split('_')
                if len(parts) >= 2:
                    file_date = parts[-1].replace('.json', '')
                    if file_date < cutoff_str:
                        os.remove(os.path.join(QUOTA_DIR, filename))
                        logger.info(f"Cleaned up old quota file: {filename}")
    
    except Exception as e:
        logger.error(f"Error cleaning up quota files: {e}")

def get_quota_status(user_id: str, plan: str) -> dict:
    """Get detailed quota status for a user"""
    used, limit = get_usage(user_id, plan)
    
    return {
        "user_id": user_id,
        "plan": plan,
        "used_today": used,
        "daily_limit": limit,
        "remaining": max(0, limit - used),
        "over_limit": used >= limit if limit > 0 else False,
        "storage_type": "redis" if REDIS_AVAILABLE else "file",
        "date": _get_today_key()
    }

if __name__ == "__main__":
    # Test the quota system
    print("Testing Quota Management System...")
    
    test_user = "test_user_123"
    test_plan = "silver"
    
    print(f"Storage type: {'Redis' if REDIS_AVAILABLE else 'File-based'}")
    
    # Get initial status
    status = get_quota_status(test_user, test_plan)
    print(f"Initial status: {status}")
    
    # Test quota increment
    used, limit = bump_and_check(test_user, test_plan)
    print(f"After increment: used={used}, limit={limit}")
    
    # Get final status
    final_status = get_quota_status(test_user, test_plan)
    print(f"Final status: {final_status}")
    
    # Test plan limits
    for plan in ["bronze", "silver", "gold"]:
        limit = companion_limit_for(plan)
        print(f"Plan '{plan}' daily limit: {limit}")