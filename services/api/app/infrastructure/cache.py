"""
Redis caching utilities for frequently accessed data.
"""
from typing import Optional, Any, Callable
from functools import wraps
import json
import hashlib
import time
from datetime import timedelta
import structlog
from app.config import settings

logger = structlog.get_logger()

# Redis client (lazy initialization)
_redis_client = None


def get_redis():
    """Get Redis client (lazy initialization)"""
    global _redis_client
    
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            _redis_client.ping()
            logger.info("redis_connected")
        except Exception as e:
            logger.warning("redis_connection_failed", exc_info=e)
            _redis_client = None
    
    return _redis_client


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_str = ":".join(key_parts)
    return hashlib.md5(key_str.encode()).hexdigest()


def cache_result(ttl_seconds: int = 3600, key_prefix: str = ""):
    """
    Decorator to cache function results in Redis.
    
    Usage:
        @cache_result(ttl_seconds=3600, key_prefix="tenant_settings")
        async def get_tenant_settings(tenant_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis = get_redis()
            
            if redis is None:
                # No caching if Redis unavailable
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_k = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            try:
                # Try to get from cache
                cached = redis.get(cache_k)
                if cached:
                    logger.debug("cache_hit", key=cache_k)
                    return json.loads(cached)
            
            except Exception as e:
                logger.warning("cache_get_failed", key=cache_k, exc_info=e)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            try:
                # Store in cache
                redis.setex(cache_k, ttl_seconds, json.dumps(result, default=str))
                logger.debug("cache_set", key=cache_k, ttl=ttl_seconds)
            
            except Exception as e:
                logger.warning("cache_set_failed", key=cache_k, exc_info=e)
            
            return result
        
        return wrapper
    
    return decorator


def invalidate_cache(key_pattern: str):
    """
    Invalidate cache keys matching pattern.
    
    Usage:
        invalidate_cache("tenant_settings:*")
    """
    redis = get_redis()
    
    if redis is None:
        return
    
    try:
        keys = redis.keys(key_pattern)
        if keys:
            redis.delete(*keys)
            logger.info("cache_invalidated", pattern=key_pattern, count=len(keys))
    
    except Exception as e:
        logger.warning("cache_invalidation_failed", pattern=key_pattern, exc_info=e)


class RateLimiter:
    """
    Redis-based rate limiter using sliding window.
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis()
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check if rate limit is exceeded.
        
        Returns:
            (allowed: bool, remaining: int)
        """
        if self.redis is None:
            # No rate limiting if Redis unavailable
            return True, max_requests
        
        try:
            now = int(time.time())
            window_start = now - window_seconds
            
            # Remove old entries
            self.redis.zremrangebyscore(key, 0, window_start)
            
            # Count requests in window
            current_count = self.redis.zcard(key)
            
            if current_count >= max_requests:
                return False, 0
            
            # Add current request
            self.redis.zadd(key, {str(now): now})
            self.redis.expire(key, window_seconds)
            
            remaining = max_requests - current_count - 1
            return True, remaining
        
        except Exception as e:
            logger.warning("rate_limit_check_failed", key=key, exc_info=e)
            return True, max_requests


# Global rate limiter
rate_limiter = RateLimiter()
