"""
Rate limiting middleware for SoulBridge AI
Implements Redis-based rate limiting with different tiers
"""

import time
import json
import logging
from functools import wraps
from typing import Dict, Optional, Tuple
from flask import request, jsonify, g
import os

# Make Redis optional - use memory fallback if not available
try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-based rate limiter with different rate limits per endpoint and user type"""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize rate limiter with Redis connection"""
        self.redis_client = None
        self.memory_store = {}
        self.enabled = True

        # Try to use Redis if available and URL provided
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                # Test connection
                self.redis_client.ping()
                logger.info("Rate limiter initialized with Redis backend")
            except Exception as e:
                logger.warning(f"Redis connection failed, using memory store: {e}")
                self.redis_client = None
        else:
            if not REDIS_AVAILABLE:
                logger.info("Redis not available, using memory store for rate limiting")
            else:
                logger.info(
                    "No Redis URL provided, using memory store for rate limiting"
                )

    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"rate_limit:{identifier}:{endpoint}"

    def _get_window_start(self, window_size: int) -> int:
        """Get the start of the current time window"""
        return int(time.time()) // window_size * window_size

    def _increment_redis(
        self, key: str, window_size: int, limit: int
    ) -> Tuple[int, int, int]:
        """Increment counter in Redis and return current count, remaining, reset time"""
        window_start = self._get_window_start(window_size)
        window_key = f"{key}:{window_start}"

        pipe = self.redis_client.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, window_size)
        results = pipe.execute()

        current_count = results[0]
        remaining = max(0, limit - current_count)
        reset_time = window_start + window_size

        return current_count, remaining, reset_time

    def _increment_memory(
        self, key: str, window_size: int, limit: int
    ) -> Tuple[int, int, int]:
        """Increment counter in memory store (fallback)"""
        window_start = self._get_window_start(window_size)
        window_key = f"{key}:{window_start}"

        # Clean old entries
        current_time = int(time.time())
        self.memory_store = {
            k: v
            for k, v in self.memory_store.items()
            if int(k.split(":")[-1]) > current_time - window_size
        }

        current_count = self.memory_store.get(window_key, 0) + 1
        self.memory_store[window_key] = current_count

        remaining = max(0, limit - current_count)
        reset_time = window_start + window_size

        return current_count, remaining, reset_time

    def check_rate_limit(
        self, identifier: str, endpoint: str, limit: int, window_size: int = 3600
    ) -> Tuple[bool, Dict]:
        """
        Check if request is within rate limit
        Returns (is_allowed, headers_dict)
        """
        if not self.enabled:
            return True, {}

        key = self._get_key(identifier, endpoint)

        try:
            if self.redis_client:
                current_count, remaining, reset_time = self._increment_redis(
                    key, window_size, limit
                )
            else:
                current_count, remaining, reset_time = self._increment_memory(
                    key, window_size, limit
                )

            headers = {
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time),
                "X-RateLimit-Window": str(window_size),
            }

            is_allowed = current_count <= limit

            if not is_allowed:
                headers["Retry-After"] = str(reset_time - int(time.time()))
                logger.warning(
                    f"Rate limit exceeded for {identifier} on {endpoint}: "
                    f"{current_count}/{limit}"
                )

            return is_allowed, headers

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if rate limiting fails
            return True, {}


# Rate limit configurations for different endpoints
RATE_LIMITS = {
    # Authentication endpoints
    "auth.login": {"limit": 5, "window": 300},  # 5 per 5 minutes
    "auth.register": {"limit": 3, "window": 3600},  # 3 per hour
    "auth.forgot_password": {"limit": 3, "window": 3600},  # 3 per hour
    "auth.reset_password": {"limit": 5, "window": 3600},  # 5 per hour
    # API endpoints
    "api.chat": {"limit": 100, "window": 3600},  # 100 per hour for free users
    "api.chat.premium": {"limit": 1000, "window": 3600},  # 1000 per hour for premium
    "api.profile": {"limit": 50, "window": 3600},  # 50 per hour
    "api.upload": {"limit": 10, "window": 3600},  # 10 uploads per hour
    # Admin endpoints
    "admin.general": {"limit": 200, "window": 3600},  # 200 per hour
    # Contact/Support
    "contact.submit": {"limit": 5, "window": 3600},  # 5 per hour
    # Global fallback
    "global": {"limit": 1000, "window": 3600},  # 1000 per hour default
}

# Initialize global rate limiter
rate_limiter = RateLimiter(os.environ.get("REDIS_URL"))


def get_rate_limit_identifier() -> str:
    """Get identifier for rate limiting (IP + user if available)"""
    # Use user ID if available, otherwise IP
    if hasattr(g, "current_user") and g.current_user:
        return f"user:{g.current_user.get('userID', 'anonymous')}"

    # Get real IP through proxies
    if request.headers.get("X-Forwarded-For"):
        ip = request.headers.get("X-Forwarded-For").split(",")[0].strip()
    elif request.headers.get("X-Real-IP"):
        ip = request.headers.get("X-Real-IP")
    else:
        ip = request.remote_addr

    return f"ip:{ip}"


def get_user_tier() -> str:
    """Determine user tier for rate limiting"""
    if hasattr(g, "current_user") and g.current_user:
        subscription_status = g.current_user.get("subscription_status", "free")
        if subscription_status in ["premium", "premium_annual"]:
            return "premium"
    return "free"


def rate_limit(
    endpoint_key: str = None, custom_limit: int = None, custom_window: int = None
):
    """
    Rate limiting decorator

    Args:
        endpoint_key: Key to lookup rate limits, defaults to route endpoint
        custom_limit: Override rate limit
        custom_window: Override time window
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Skip rate limiting in test mode
            if os.environ.get("TEST_MODE") == "true":
                return f(*args, **kwargs)

            # Determine rate limit key
            key = endpoint_key or request.endpoint or "global"

            # Get user tier for dynamic limits
            user_tier = get_user_tier()
            if user_tier == "premium" and key == "api.chat":
                key = "api.chat.premium"

            # Get rate limit configuration
            config = RATE_LIMITS.get(key, RATE_LIMITS["global"])
            limit = custom_limit or config["limit"]
            window = custom_window or config["window"]

            # Get identifier and check rate limit
            identifier = get_rate_limit_identifier()
            is_allowed, headers = rate_limiter.check_rate_limit(
                identifier, key, limit, window
            )

            # Add rate limit headers to response
            response = f(*args, **kwargs) if is_allowed else None

            if not is_allowed:
                error_response = jsonify(
                    {
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {limit} per {window} seconds",
                        "retry_after": headers.get("Retry-After"),
                        "limit": limit,
                        "window": window,
                    }
                )
                error_response.status_code = 429

                # Add headers to error response
                for header, value in headers.items():
                    error_response.headers[header] = value

                return error_response

            # Add headers to successful response
            if hasattr(response, "headers"):
                for header, value in headers.items():
                    response.headers[header] = value

            return response

        return wrapper

    return decorator


def init_rate_limiting(app):
    """Initialize rate limiting for Flask app"""

    @app.before_request
    def load_user_for_rate_limiting():
        """Load user info for rate limiting before each request"""
        # This will be set by auth middleware if user is authenticated
        g.current_user = None

    @app.after_request
    def add_rate_limit_headers(response):
        """Add rate limit info to all responses"""
        if not hasattr(response, "headers"):
            return response

        # Add general rate limiting info
        response.headers["X-RateLimit-Policy"] = "SoulBridge-AI-v1"
        return response

    logger.info("Rate limiting initialized")
