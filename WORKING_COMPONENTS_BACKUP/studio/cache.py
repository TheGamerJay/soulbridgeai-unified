"""
Response Caching System
Caches companion responses to improve performance and reduce API costs
"""
import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any
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
    logger.info("✅ Redis connected for caching")
except Exception as e:
    logger.warning(f"Redis not available, using file storage: {e}")
    redis_client = None
    REDIS_AVAILABLE = False
    
    # File-based fallback
    CACHE_DIR = os.path.join(os.path.dirname(__file__), "data", "cache")
    os.makedirs(CACHE_DIR, exist_ok=True)

def _generate_cache_key(message: str, character: str, context: str = "") -> str:
    """Generate consistent cache key for request"""
    # Normalize inputs
    message_norm = message.lower().strip()
    character_norm = character.lower().strip()
    context_norm = context.lower().strip()
    
    # Create hash of combined inputs
    combined = f"{message_norm}|{character_norm}|{context_norm}"
    return hashlib.md5(combined.encode()).hexdigest()

def get_cached_response(message: str, character: str, context: str = "", max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
    """
    Get cached response if available and not expired
    
    Args:
        message: User message
        character: Character name
        context: Additional context
        max_age_hours: Maximum age in hours before cache expires
        
    Returns:
        Cached response dict or None if not found/expired
    """
    try:
        cache_key = _generate_cache_key(message, character, context)
        
        if REDIS_AVAILABLE:
            # Redis implementation
            cached_data = redis_client.get(f"companion_cache:{cache_key}")
            if cached_data:
                data = json.loads(cached_data)
                cached_time = datetime.fromisoformat(data["cached_at"])
                
                if datetime.now() - cached_time < timedelta(hours=max_age_hours):
                    logger.info(f"Cache hit for key: {cache_key[:8]}...")
                    return data["response"]
                else:
                    # Expired, remove it
                    redis_client.delete(f"companion_cache:{cache_key}")
                    logger.info(f"Cache expired for key: {cache_key[:8]}...")
        else:
            # File-based implementation
            cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cached_time = datetime.fromisoformat(data["cached_at"])
                    
                    if datetime.now() - cached_time < timedelta(hours=max_age_hours):
                        logger.info(f"Cache hit for file: {cache_key[:8]}...")
                        return data["response"]
                    else:
                        # Expired, remove it
                        os.remove(cache_file)
                        logger.info(f"Cache expired for file: {cache_key[:8]}...")
        
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving cache: {e}")
        return None

def cache_response(message: str, character: str, response: Dict[str, Any], context: str = "") -> bool:
    """
    Cache a response for future use
    
    Args:
        message: User message
        character: Character name  
        response: Response to cache
        context: Additional context
        
    Returns:
        True if cached successfully, False otherwise
    """
    try:
        cache_key = _generate_cache_key(message, character, context)
        
        cache_data = {
            "response": response,
            "cached_at": datetime.now().isoformat(),
            "message": message,
            "character": character,
            "context": context
        }
        
        if REDIS_AVAILABLE:
            # Redis implementation with expiration
            cache_ttl = int(os.getenv("CACHE_TTL_HOURS", "24")) * 3600  # Convert to seconds
            redis_client.setex(
                f"companion_cache:{cache_key}",
                cache_ttl,
                json.dumps(cache_data, ensure_ascii=False)
            )
            logger.info(f"Cached response to Redis: {cache_key[:8]}...")
        else:
            # File-based implementation
            cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Cached response to file: {cache_key[:8]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Error caching response: {e}")
        return False

def clear_cache(max_age_days: int = 7) -> int:
    """
    Clear old cache entries
    
    Args:
        max_age_days: Maximum age in days before clearing
        
    Returns:
        Number of entries cleared
    """
    cleared = 0
    
    try:
        if REDIS_AVAILABLE:
            # Redis handles expiration automatically
            # But we can manually scan and delete old entries if needed
            cursor = 0
            while True:
                cursor, keys = redis_client.scan(cursor, match="companion_cache:*", count=100)
                
                for key in keys:
                    try:
                        data = redis_client.get(key)
                        if data:
                            cache_data = json.loads(data)
                            cached_time = datetime.fromisoformat(cache_data["cached_at"])
                            
                            if datetime.now() - cached_time > timedelta(days=max_age_days):
                                redis_client.delete(key)
                                cleared += 1
                    except Exception:
                        # If we can't parse it, delete it
                        redis_client.delete(key)
                        cleared += 1
                
                if cursor == 0:
                    break
        else:
            # File-based cleanup
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            
            for filename in os.listdir(CACHE_DIR):
                if filename.endswith('.json'):
                    file_path = os.path.join(CACHE_DIR, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            cached_time = datetime.fromisoformat(data["cached_at"])
                            
                            if cached_time < cutoff_time:
                                os.remove(file_path)
                                cleared += 1
                    except Exception:
                        # If we can't parse it, delete it
                        os.remove(file_path)
                        cleared += 1
        
        logger.info(f"Cleared {cleared} old cache entries")
        return cleared
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return 0

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    try:
        if REDIS_AVAILABLE:
            # Count Redis cache entries
            cursor = 0
            count = 0
            total_size = 0
            
            while True:
                cursor, keys = redis_client.scan(cursor, match="companion_cache:*", count=100)
                count += len(keys)
                
                for key in keys:
                    try:
                        data = redis_client.get(key)
                        if data:
                            total_size += len(data.encode('utf-8'))
                    except Exception:
                        pass
                
                if cursor == 0:
                    break
            
            return {
                "storage_type": "redis",
                "entries": count,
                "total_size_bytes": total_size,
                "available": True
            }
        else:
            # Count file cache entries
            count = 0
            total_size = 0
            
            for filename in os.listdir(CACHE_DIR):
                if filename.endswith('.json'):
                    file_path = os.path.join(CACHE_DIR, filename)
                    try:
                        count += 1
                        total_size += os.path.getsize(file_path)
                    except Exception:
                        pass
            
            return {
                "storage_type": "file",
                "entries": count,
                "total_size_bytes": total_size,
                "cache_dir": CACHE_DIR,
                "available": True
            }
            
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {
            "storage_type": "redis" if REDIS_AVAILABLE else "file",
            "entries": 0,
            "total_size_bytes": 0,
            "available": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # Test the caching system
    print("Testing Response Caching System...")
    
    print(f"Storage type: {'Redis' if REDIS_AVAILABLE else 'File-based'}")
    
    # Test data
    test_message = "Hello, how are you?"
    test_character = "Blayzo"
    test_response = {
        "success": True,
        "response": "Hello! I'm doing well, thank you for asking!",
        "model": "test_model",
        "response_time": 0.5
    }
    
    # Test caching
    print(f"\nTesting cache with message: '{test_message}'")
    
    # Should be cache miss first time
    cached = get_cached_response(test_message, test_character)
    print(f"First lookup (should be None): {cached}")
    
    # Cache the response
    success = cache_response(test_message, test_character, test_response)
    print(f"Caching successful: {success}")
    
    # Should be cache hit now
    cached = get_cached_response(test_message, test_character)
    print(f"Second lookup (should be hit): {cached is not None}")
    
    if cached:
        print(f"Cached response: {cached['response']}")
    
    # Get stats
    stats = get_cache_stats()
    print(f"\nCache stats: {stats}")
    
    # Test cleanup (won't clear recent entries)
    cleared = clear_cache(max_age_days=0.001)  # Very short time for testing
    print(f"Cleared {cleared} entries")