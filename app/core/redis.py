"""
Redis connection and caching utilities for the DSPy-Enhanced Fact-Checker API Platform.
"""

import redis.asyncio as redis
import json
import pickle
import logging
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
redis_pool = None


async def init_redis():
    """Initialize Redis connection pool."""
    global redis_pool
    
    settings = get_settings()
    
    try:
        # Parse Redis URL
        redis_url = settings.REDIS_URL
        logger.info(f"Initializing Redis connection to: {redis_url}")
        
        # Create connection pool
        redis_pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=20,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30
        )
        
        # Test connection
        async with redis.Redis(connection_pool=redis_pool) as client:
            await client.ping()
            
        logger.info("Redis connection pool initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise


async def close_redis():
    """Close Redis connection pool."""
    global redis_pool
    
    if redis_pool:
        try:
            await redis_pool.disconnect()
            redis_pool = None
            logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


@asynccontextmanager
async def get_redis_client():
    """Get Redis client from connection pool."""
    global redis_pool
    
    if redis_pool is None:
        await init_redis()
    
    client = redis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()


class RedisCache:
    """Redis-based caching utility."""
    
    def __init__(self, prefix: str = "fact_checker"):
        self.prefix = prefix
    
    def _make_key(self, key: str) -> str:
        """Create a prefixed cache key."""
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            async with get_redis_client() as client:
                value = await client.get(self._make_key(key))
                if value is None:
                    return default
                
                # Try to deserialize as JSON first, then pickle
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return pickle.loads(value)
                    
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        serialize_method: str = "json"
    ) -> bool:
        """Set value in cache."""
        try:
            async with get_redis_client() as client:
                # Serialize value
                if serialize_method == "json":
                    try:
                        serialized_value = json.dumps(value, default=str)
                    except (TypeError, ValueError):
                        # Fallback to pickle for complex objects
                        serialized_value = pickle.dumps(value)
                else:
                    serialized_value = pickle.dumps(value)
                
                # Set with optional TTL
                if ttl:
                    await client.setex(self._make_key(key), ttl, serialized_value)
                else:
                    await client.set(self._make_key(key), serialized_value)
                
                return True
                
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            async with get_redis_client() as client:
                result = await client.delete(self._make_key(key))
                return result > 0
                
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            async with get_redis_client() as client:
                result = await client.exists(self._make_key(key))
                return result > 0
                
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value in cache."""
        try:
            async with get_redis_client() as client:
                result = await client.incrby(self._make_key(key), amount)
                return result
                
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key."""
        try:
            async with get_redis_client() as client:
                result = await client.expire(self._make_key(key), ttl)
                return result
                
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get time to live for a key."""
        try:
            async with get_redis_client() as client:
                result = await client.ttl(self._make_key(key))
                return result if result >= 0 else None
                
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return None
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern."""
        try:
            async with get_redis_client() as client:
                keys = await client.keys(self._make_key(pattern))
                if keys:
                    result = await client.delete(*keys)
                    return result
                return 0
                
        except Exception as e:
            logger.error(f"Cache clear pattern error for pattern {pattern}: {e}")
            return 0


class SessionManager:
    """Redis-based session management."""
    
    def __init__(self, prefix: str = "session"):
        self.cache = RedisCache(prefix)
        self.default_ttl = 3600  # 1 hour
    
    async def create_session(
        self, 
        session_id: str, 
        data: Dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """Create a new session."""
        session_data = {
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            "data": data
        }
        
        return await self.cache.set(
            session_id, 
            session_data, 
            ttl or self.default_ttl
        )
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        session_data = await self.cache.get(session_id)
        if session_data:
            # Update last accessed time
            session_data["last_accessed"] = datetime.utcnow().isoformat()
            await self.cache.set(session_id, session_data, self.default_ttl)
            return session_data.get("data", {})
        return None
    
    async def update_session(
        self, 
        session_id: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Update session data."""
        session_data = await self.cache.get(session_id)
        if session_data:
            session_data["data"].update(data)
            session_data["last_accessed"] = datetime.utcnow().isoformat()
            return await self.cache.set(session_id, session_data, self.default_ttl)
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        return await self.cache.delete(session_id)
    
    async def extend_session(self, session_id: str, ttl: int) -> bool:
        """Extend session expiration time."""
        return await self.cache.expire(session_id, ttl)


class RateLimiter:
    """Redis-based rate limiting."""
    
    def __init__(self, prefix: str = "rate_limit"):
        self.cache = RedisCache(prefix)
    
    async def is_allowed(
        self, 
        identifier: str, 
        limit: int, 
        window: int
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            identifier: Unique identifier (e.g., IP address, user ID)
            limit: Maximum number of requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, info_dict)
        """
        try:
            async with get_redis_client() as client:
                current_time = int(datetime.utcnow().timestamp())
                window_start = current_time - window
                
                # Use sliding window log approach
                key = self._make_key(identifier)
                
                # Remove old entries
                await client.zremrangebyscore(key, 0, window_start)
                
                # Count current requests
                current_count = await client.zcard(key)
                
                if current_count < limit:
                    # Add current request
                    await client.zadd(key, {str(current_time): current_time})
                    await client.expire(key, window)
                    
                    return True, {
                        "allowed": True,
                        "limit": limit,
                        "remaining": limit - current_count - 1,
                        "reset_time": current_time + window
                    }
                else:
                    # Get oldest entry to calculate reset time
                    oldest = await client.zrange(key, 0, 0, withscores=True)
                    reset_time = int(oldest[0][1]) + window if oldest else current_time + window
                    
                    return False, {
                        "allowed": False,
                        "limit": limit,
                        "remaining": 0,
                        "reset_time": reset_time
                    }
                    
        except Exception as e:
            logger.error(f"Rate limiter error for {identifier}: {e}")
            # Allow request on error to avoid blocking legitimate traffic
            return True, {
                "allowed": True,
                "limit": limit,
                "remaining": limit - 1,
                "reset_time": current_time + window,
                "error": str(e)
            }
    
    def _make_key(self, identifier: str) -> str:
        """Create rate limit key."""
        return f"rate_limit:{identifier}"


class RedisHealthCheck:
    """Redis health check utilities."""
    
    @staticmethod
    async def check_connection() -> bool:
        """Check if Redis connection is healthy."""
        try:
            async with get_redis_client() as client:
                await client.ping()
                return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    @staticmethod
    async def get_info() -> Dict[str, Any]:
        """Get Redis server information."""
        try:
            async with get_redis_client() as client:
                info = await client.info()
                return {
                    "status": "connected",
                    "version": info.get("redis_version", "unknown"),
                    "memory_used": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "uptime": info.get("uptime_in_seconds", 0)
                }
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Global instances
cache = RedisCache()
session_manager = SessionManager()
rate_limiter = RateLimiter()


# FastAPI dependency
async def get_cache() -> RedisCache:
    """FastAPI dependency for cache."""
    return cache


async def get_session_manager() -> SessionManager:
    """FastAPI dependency for session manager."""
    return session_manager


async def get_rate_limiter() -> RateLimiter:
    """FastAPI dependency for rate limiter."""
    return rate_limiter
