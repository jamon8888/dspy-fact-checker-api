"""
Performance optimization utilities for the search module.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable, TypeVar, Generic
from collections import defaultdict, deque
from dataclasses import dataclass
import hashlib
import json

from app.core.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with expiration and metadata."""
    value: T
    created_at: float
    expires_at: float
    access_count: int = 0
    last_accessed: float = 0.0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() > self.expires_at
    
    def access(self) -> T:
        """Access the cached value and update metrics."""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value


class SearchCache:
    """
    High-performance cache for search results with TTL and LRU eviction.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize search cache.
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: deque = deque()
        
        # Metrics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        logger.info(f"Search cache initialized: max_size={max_size}, ttl={default_ttl}s")
    
    def _generate_key(self, query: str, params: Dict[str, Any] = None) -> str:
        """Generate cache key from query and parameters."""
        key_data = {
            "query": query,
            "params": params or {}
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def get(self, query: str, params: Dict[str, Any] = None) -> Optional[Any]:
        """
        Get cached result.
        
        Args:
            query: Search query
            params: Additional parameters
            
        Returns:
            Cached result or None if not found/expired
        """
        key = self._generate_key(query, params)
        
        if key in self._cache:
            entry = self._cache[key]
            
            if entry.is_expired():
                # Remove expired entry
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._misses += 1
                return None
            
            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            self._hits += 1
            return entry.access()
        
        self._misses += 1
        return None
    
    async def set(
        self, 
        query: str, 
        value: Any, 
        params: Dict[str, Any] = None, 
        ttl: Optional[int] = None
    ):
        """
        Set cached result.
        
        Args:
            query: Search query
            value: Result to cache
            params: Additional parameters
            ttl: Time-to-live in seconds
        """
        key = self._generate_key(query, params)
        ttl = ttl or self.default_ttl
        
        # Check if we need to evict entries
        if len(self._cache) >= self.max_size and key not in self._cache:
            await self._evict_lru()
        
        # Create cache entry
        now = time.time()
        entry = CacheEntry(
            value=value,
            created_at=now,
            expires_at=now + ttl,
            access_count=0,
            last_accessed=now
        )
        
        self._cache[key] = entry
        
        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    async def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._access_order:
            return
        
        # Remove oldest entry
        oldest_key = self._access_order.popleft()
        if oldest_key in self._cache:
            del self._cache[oldest_key]
            self._evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": hit_rate,
            "cache_size": len(self._cache),
            "max_size": self.max_size
        }
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._access_order.clear()
        logger.info("Search cache cleared")


class RequestDeduplicator:
    """
    Deduplicates concurrent requests to prevent redundant API calls.
    """
    
    def __init__(self):
        """Initialize request deduplicator."""
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._request_counts = defaultdict(int)
        
        logger.info("Request deduplicator initialized")
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate key for request deduplication."""
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def deduplicate(
        self, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """
        Execute function with request deduplication.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        key = self._generate_key(func.__name__, args, kwargs)
        
        # Check if request is already pending
        if key in self._pending_requests:
            self._request_counts[key] += 1
            logger.debug(f"Deduplicating request: {func.__name__} (count: {self._request_counts[key]})")
            return await self._pending_requests[key]
        
        # Create new request
        future = asyncio.create_task(func(*args, **kwargs))
        self._pending_requests[key] = future
        self._request_counts[key] = 1
        
        try:
            result = await future
            return result
        finally:
            # Clean up
            if key in self._pending_requests:
                del self._pending_requests[key]
            if key in self._request_counts:
                del self._request_counts[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics."""
        return {
            "pending_requests": len(self._pending_requests),
            "total_deduplicated": sum(self._request_counts.values()) - len(self._request_counts)
        }


class PerformanceMonitor:
    """
    Monitors and tracks performance metrics for search operations.
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize performance monitor.
        
        Args:
            window_size: Size of rolling window for metrics
        """
        self.window_size = window_size
        self._response_times: deque = deque(maxlen=window_size)
        self._operation_counts = defaultdict(int)
        self._error_counts = defaultdict(int)
        self._start_time = time.time()
        
        logger.info(f"Performance monitor initialized: window_size={window_size}")
    
    def record_operation(
        self, 
        operation: str, 
        duration: float, 
        success: bool = True,
        error_type: Optional[str] = None
    ):
        """
        Record operation metrics.
        
        Args:
            operation: Operation name
            duration: Operation duration in seconds
            success: Whether operation was successful
            error_type: Type of error if failed
        """
        self._response_times.append(duration)
        self._operation_counts[operation] += 1
        
        if not success and error_type:
            self._error_counts[error_type] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        if not self._response_times:
            return {
                "average_response_time": 0.0,
                "min_response_time": 0.0,
                "max_response_time": 0.0,
                "total_operations": 0,
                "operations_per_second": 0.0,
                "error_rate": 0.0
            }
        
        response_times = list(self._response_times)
        total_operations = sum(self._operation_counts.values())
        total_errors = sum(self._error_counts.values())
        uptime = time.time() - self._start_time
        
        return {
            "average_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "total_operations": total_operations,
            "operations_per_second": total_operations / uptime if uptime > 0 else 0.0,
            "error_rate": total_errors / total_operations if total_operations > 0 else 0.0,
            "operation_counts": dict(self._operation_counts),
            "error_counts": dict(self._error_counts),
            "uptime_seconds": uptime
        }


class SearchPerformanceOptimizer:
    """
    Main performance optimization coordinator for search operations.
    """
    
    def __init__(self):
        """Initialize search performance optimizer."""
        settings = get_settings()
        
        # Initialize components
        self.cache = SearchCache(
            max_size=1000,
            default_ttl=settings.SEARCH_CACHE_TTL
        )
        self.deduplicator = RequestDeduplicator()
        self.monitor = PerformanceMonitor()
        
        logger.info("Search performance optimizer initialized")
    
    async def optimized_search(
        self,
        search_func: Callable,
        query: str,
        params: Dict[str, Any] = None,
        cache_enabled: bool = True,
        deduplicate: bool = True
    ) -> Any:
        """
        Execute optimized search with caching and deduplication.
        
        Args:
            search_func: Search function to execute
            query: Search query
            params: Search parameters
            cache_enabled: Whether to use caching
            deduplicate: Whether to deduplicate requests
            
        Returns:
            Search results
        """
        start_time = time.time()
        operation_name = search_func.__name__
        
        try:
            # Try cache first
            if cache_enabled:
                cached_result = await self.cache.get(query, params)
                if cached_result is not None:
                    duration = time.time() - start_time
                    self.monitor.record_operation(f"{operation_name}_cached", duration)
                    logger.debug(f"Cache hit for {operation_name}: {query[:50]}...")
                    return cached_result
            
            # Execute search with optional deduplication
            if deduplicate:
                result = await self.deduplicator.deduplicate(search_func, query, **params or {})
            else:
                result = await search_func(query, **params or {})
            
            # Cache result
            if cache_enabled and result is not None:
                await self.cache.set(query, result, params)
            
            # Record metrics
            duration = time.time() - start_time
            self.monitor.record_operation(operation_name, duration, success=True)
            
            logger.debug(f"Search completed: {operation_name}, duration={duration:.3f}s")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.monitor.record_operation(
                operation_name, 
                duration, 
                success=False, 
                error_type=type(e).__name__
            )
            logger.error(f"Search failed: {operation_name}, error={e}")
            raise
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        return {
            "cache_stats": self.cache.get_stats(),
            "deduplication_stats": self.deduplicator.get_stats(),
            "performance_metrics": self.monitor.get_metrics()
        }
    
    def reset_stats(self):
        """Reset all performance statistics."""
        self.cache.clear()
        self.monitor = PerformanceMonitor()
        logger.info("Performance stats reset")


# Global performance optimizer instance
search_performance_optimizer = SearchPerformanceOptimizer()
