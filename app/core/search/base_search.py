"""
Abstract base class for search providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import asyncio
import time
import logging

from .models import SearchQuery, SearchResult, SearchProviderStatus
from .exceptions import SearchProviderError

logger = logging.getLogger(__name__)


class BaseSearchProvider(ABC):
    """Abstract base class for search providers."""
    
    def __init__(self, name: str, timeout: int = 30, max_retries: int = 3):
        """
        Initialize search provider.
        
        Args:
            name: Provider name
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.name = name
        self.timeout = timeout
        self.max_retries = max_retries
        self._last_health_check: Optional[float] = None
        self._is_healthy: bool = True
        self._error_count: int = 0
        self._total_requests: int = 0
        self._successful_requests: int = 0
        self._total_response_time: float = 0.0
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return self.name
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self._total_requests == 0:
            return 1.0
        return self._successful_requests / self._total_requests
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if self._successful_requests == 0:
            return 0.0
        return self._total_response_time / self._successful_requests
    
    @abstractmethod
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Execute search and return results.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
            
        Raises:
            SearchProviderError: If search fails
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if search provider is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    async def search_with_retry(self, query: SearchQuery) -> List[SearchResult]:
        """
        Execute search with retry logic.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
            
        Raises:
            SearchProviderError: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                self._total_requests += 1
                
                # Execute search with timeout
                results = await asyncio.wait_for(
                    self.search(query),
                    timeout=self.timeout
                )
                
                # Track success metrics
                response_time = time.time() - start_time
                self._successful_requests += 1
                self._total_response_time += response_time
                self._error_count = 0  # Reset error count on success
                
                logger.info(
                    f"{self.name} search successful: {len(results)} results in {response_time:.2f}s"
                )
                
                return results
                
            except asyncio.TimeoutError as e:
                last_error = SearchProviderError(
                    f"Search timeout after {self.timeout}s",
                    provider=self.name,
                    original_error=e
                )
                logger.warning(f"{self.name} search timeout (attempt {attempt + 1}/{self.max_retries})")
                
            except Exception as e:
                last_error = SearchProviderError(
                    f"Search failed: {str(e)}",
                    provider=self.name,
                    original_error=e
                )
                logger.warning(
                    f"{self.name} search failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
            
            # Track error
            self._error_count += 1
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        # All retries failed
        self._is_healthy = False
        logger.error(f"{self.name} search failed after {self.max_retries} attempts")
        raise last_error
    
    async def get_status(self) -> SearchProviderStatus:
        """
        Get provider status.
        
        Returns:
            Provider status information
        """
        # Perform health check if needed
        if (
            self._last_health_check is None or
            time.time() - self._last_health_check > 300  # 5 minutes
        ):
            try:
                self._is_healthy = await self.health_check()
                self._last_health_check = time.time()
            except Exception as e:
                self._is_healthy = False
                logger.error(f"{self.name} health check failed: {e}")
        
        return SearchProviderStatus(
            provider_name=self.name,
            is_healthy=self._is_healthy,
            response_time=self.average_response_time,
            success_rate=self.success_rate,
            last_check=self._last_health_check or 0.0,
            error_message=None if self._is_healthy else "Provider unhealthy"
        )
    
    def reset_metrics(self):
        """Reset provider metrics."""
        self._error_count = 0
        self._total_requests = 0
        self._successful_requests = 0
        self._total_response_time = 0.0
        self._last_health_check = None
        self._is_healthy = True
        
        logger.info(f"{self.name} metrics reset")
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name={self.name})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"{self.__class__.__name__}("
            f"name={self.name}, "
            f"timeout={self.timeout}, "
            f"max_retries={self.max_retries}, "
            f"success_rate={self.success_rate:.2f}"
            f")"
        )
