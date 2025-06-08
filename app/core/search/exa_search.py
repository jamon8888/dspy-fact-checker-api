"""
Exa.ai search provider implementation.
"""

import asyncio
import time
import logging
from typing import List, Optional, Dict, Any
from asyncio_throttle import Throttler

try:
    from exa_py import Exa
except ImportError:
    Exa = None

from .base_search import BaseSearchProvider
from .models import SearchQuery, SearchResult, SearchType
from .exceptions import SearchProviderError, SearchRateLimitError, SearchConfigurationError
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ExaSearchProvider(BaseSearchProvider):
    """Exa.ai search provider with neural search capabilities."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Exa.ai search provider.
        
        Args:
            api_key: Exa.ai API key (optional, will use settings if not provided)
            
        Raises:
            SearchConfigurationError: If Exa.ai is not available or API key is missing
        """
        if Exa is None:
            raise SearchConfigurationError(
                "exa-py package not installed. Install with: pip install exa-py"
            )
        
        settings = get_settings()
        
        # Use provided API key or get from settings
        self.api_key = api_key or settings.EXA_API_KEY
        if not self.api_key:
            raise SearchConfigurationError("EXA_API_KEY not configured")
        
        # Initialize base class
        super().__init__(
            name="exa",
            timeout=settings.EXA_TIMEOUT,
            max_retries=settings.EXA_MAX_RETRIES
        )
        
        # Initialize Exa client
        self.client = Exa(api_key=self.api_key)
        
        # Rate limiting
        self.throttler = Throttler(
            rate_limit=settings.EXA_RATE_LIMIT_CALLS,
            period=settings.EXA_RATE_LIMIT_PERIOD
        )
        
        # Settings
        self.settings = settings
        
        logger.info(f"Exa.ai search provider initialized with rate limit: {settings.EXA_RATE_LIMIT_CALLS}/{settings.EXA_RATE_LIMIT_PERIOD}s")
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Execute Exa.ai search.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
            
        Raises:
            SearchProviderError: If search fails
        """
        async with self.throttler:
            try:
                start_time = time.time()
                
                # Route to appropriate search method
                if query.search_type == SearchType.NEURAL:
                    results = await self._neural_search(query)
                elif query.search_type == SearchType.SIMILARITY:
                    results = await self._similarity_search(query)
                elif query.search_type == SearchType.KEYWORD:
                    results = await self._keyword_search(query)
                else:
                    # Default to neural search
                    results = await self._neural_search(query)
                
                processing_time = time.time() - start_time
                
                # Parse results
                search_results = [
                    self._parse_result(result, processing_time) 
                    for result in results.results
                ]
                
                logger.info(
                    f"Exa.ai {query.search_type} search completed: "
                    f"{len(search_results)} results in {processing_time:.2f}s"
                )
                
                return search_results
                
            except Exception as e:
                logger.error(f"Exa.ai search failed: {e}")
                
                # Check for rate limiting
                if "rate limit" in str(e).lower():
                    raise SearchRateLimitError(
                        f"Exa.ai rate limit exceeded: {e}",
                        provider=self.name,
                        retry_after=60
                    )
                
                raise SearchProviderError(
                    f"Exa.ai search failed: {e}",
                    provider=self.name,
                    original_error=e
                )
    
    async def _neural_search(self, query: SearchQuery) -> Any:
        """
        Execute neural search using Exa.ai.
        
        Args:
            query: Search query
            
        Returns:
            Exa.ai search results
        """
        search_params = {
            "query": query.query,
            "num_results": query.max_results,
            "use_autoprompt": query.use_autoprompt,
            "text": True,
            "highlights": True
        }
        
        # Add optional filters
        if query.include_domains:
            search_params["include_domains"] = query.include_domains
        
        if query.exclude_domains:
            search_params["exclude_domains"] = query.exclude_domains
        
        if query.start_published_date:
            search_params["start_published_date"] = query.start_published_date
        
        if query.end_published_date:
            search_params["end_published_date"] = query.end_published_date
        
        # Execute search in thread pool to avoid blocking
        return await asyncio.to_thread(
            self.client.search_and_contents,
            **search_params
        )
    
    async def _similarity_search(self, query: SearchQuery) -> Any:
        """
        Execute similarity search for hallucination detection.
        
        Args:
            query: Search query
            
        Returns:
            Exa.ai search results
        """
        # For similarity search, we need a URL to compare against
        # This is typically used for hallucination detection
        if "url" not in query.filters:
            # Fall back to neural search if no URL provided
            return await self._neural_search(query)
        
        url = query.filters["url"]
        
        search_params = {
            "url": url,
            "num_results": query.max_results,
            "text": True,
            "highlights": True
        }
        
        return await asyncio.to_thread(
            self.client.find_similar_and_contents,
            **search_params
        )
    
    async def _keyword_search(self, query: SearchQuery) -> Any:
        """
        Execute keyword search (fallback method).
        
        Args:
            query: Search query
            
        Returns:
            Exa.ai search results
        """
        # Exa.ai doesn't have a separate keyword search
        # Use neural search without autoprompt for more literal matching
        search_params = {
            "query": query.query,
            "num_results": query.max_results,
            "use_autoprompt": False,  # More literal matching
            "text": True,
            "highlights": True
        }
        
        # Add optional filters
        if query.include_domains:
            search_params["include_domains"] = query.include_domains
        
        if query.exclude_domains:
            search_params["exclude_domains"] = query.exclude_domains
        
        return await asyncio.to_thread(
            self.client.search_and_contents,
            **search_params
        )
    
    def _parse_result(self, result: Any, processing_time: float) -> SearchResult:
        """
        Parse Exa.ai result into SearchResult model.
        
        Args:
            result: Exa.ai result object
            processing_time: Time taken for search
            
        Returns:
            Parsed search result
        """
        return SearchResult(
            title=getattr(result, 'title', '') or '',
            url=getattr(result, 'url', ''),
            content=getattr(result, 'text', '') or '',
            score=getattr(result, 'score', 0.0) or 0.0,
            source="exa",
            published_date=getattr(result, 'published_date', None),
            highlights=getattr(result, 'highlights', []) or [],
            metadata={
                "processing_time": processing_time,
                "autoprompt_used": True,
                "search_type": "neural",
                "id": getattr(result, 'id', None),
                "author": getattr(result, 'author', None)
            }
        )
    
    async def health_check(self) -> bool:
        """
        Check Exa.ai API health.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Perform a simple test search
            test_query = SearchQuery(
                query="test health check",
                max_results=1,
                search_type=SearchType.NEURAL
            )
            
            results = await self.search(test_query)
            return len(results) >= 0  # Even 0 results is a successful response
            
        except Exception as e:
            logger.error(f"Exa.ai health check failed: {e}")
            return False
    
    async def get_search_capabilities(self) -> Dict[str, Any]:
        """
        Get Exa.ai search capabilities.
        
        Returns:
            Dictionary of capabilities
        """
        return {
            "provider": "exa",
            "search_types": [SearchType.NEURAL, SearchType.SIMILARITY, SearchType.KEYWORD],
            "supports_autoprompt": True,
            "supports_domain_filtering": True,
            "supports_date_filtering": True,
            "supports_highlights": True,
            "max_results_per_query": 50,
            "rate_limit": {
                "calls": self.settings.EXA_RATE_LIMIT_CALLS,
                "period": self.settings.EXA_RATE_LIMIT_PERIOD
            }
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"ExaSearchProvider(rate_limit={self.settings.EXA_RATE_LIMIT_CALLS}/{self.settings.EXA_RATE_LIMIT_PERIOD}s)"
