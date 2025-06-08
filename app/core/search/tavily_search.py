"""
Tavily search provider implementation.
"""

import asyncio
import time
import logging
from typing import List, Optional, Dict, Any

try:
    from tavily import TavilyClient
except ImportError:
    try:
        # Alternative import for different package versions
        from langchain_tavily import TavilySearch
        TavilyClient = None
    except ImportError:
        TavilyClient = None
        TavilySearch = None

from .base_search import BaseSearchProvider
from .models import SearchQuery, SearchResult, SearchType
from .exceptions import SearchProviderError, SearchRateLimitError, SearchConfigurationError
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TavilySearchProvider(BaseSearchProvider):
    """Tavily search provider for web search capabilities."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily search provider.
        
        Args:
            api_key: Tavily API key (optional, will use settings if not provided)
            
        Raises:
            SearchConfigurationError: If Tavily is not available or API key is missing
        """
        if TavilyClient is None and TavilySearch is None:
            raise SearchConfigurationError(
                "Tavily package not installed. Install with: pip install tavily-python"
            )
        
        settings = get_settings()
        
        # Use provided API key or get from settings
        self.api_key = api_key or settings.TAVILY_API_KEY
        if not self.api_key:
            raise SearchConfigurationError("TAVILY_API_KEY not configured")
        
        # Initialize base class
        super().__init__(
            name="tavily",
            timeout=30,  # Default timeout for Tavily
            max_retries=3
        )
        
        # Initialize Tavily client
        if TavilyClient:
            self.client = TavilyClient(api_key=self.api_key)
            self.use_langchain = False
        else:
            self.client = TavilySearch(
                api_key=self.api_key,
                max_results=10,
                search_depth="basic",
                topic="general"
            )
            self.use_langchain = True
        
        # Settings
        self.settings = settings
        
        logger.info(f"Tavily search provider initialized (langchain={self.use_langchain})")
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Execute Tavily search.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
            
        Raises:
            SearchProviderError: If search fails
        """
        try:
            start_time = time.time()
            
            if self.use_langchain:
                results = await self._search_with_langchain(query)
            else:
                results = await self._search_with_client(query)
            
            processing_time = time.time() - start_time
            
            # Parse results
            search_results = [
                self._parse_result(result, processing_time, i) 
                for i, result in enumerate(results)
            ]
            
            logger.info(
                f"Tavily search completed: "
                f"{len(search_results)} results in {processing_time:.2f}s"
            )
            
            return search_results
            
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            
            # Check for rate limiting
            if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                raise SearchRateLimitError(
                    f"Tavily rate limit exceeded: {e}",
                    provider=self.name,
                    retry_after=60
                )
            
            raise SearchProviderError(
                f"Tavily search failed: {e}",
                provider=self.name,
                original_error=e
            )
    
    async def _search_with_client(self, query: SearchQuery) -> List[Dict[str, Any]]:
        """
        Execute search using TavilyClient.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        search_params = {
            "query": query.query,
            "max_results": query.max_results,
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": True,
            "include_images": False
        }
        
        # Add domain filters if specified
        if query.include_domains:
            search_params["include_domains"] = query.include_domains
        
        if query.exclude_domains:
            search_params["exclude_domains"] = query.exclude_domains
        
        # Execute search in thread pool to avoid blocking
        response = await asyncio.to_thread(
            self.client.search,
            **search_params
        )
        
        # Extract results from response
        if isinstance(response, dict) and "results" in response:
            return response["results"]
        elif isinstance(response, list):
            return response
        else:
            return []
    
    async def _search_with_langchain(self, query: SearchQuery) -> List[Dict[str, Any]]:
        """
        Execute search using LangChain TavilySearch.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        # Update max_results for this query
        self.client.max_results = query.max_results
        
        # Execute search
        response = await self.client.ainvoke(query.query)
        
        # Parse response
        if isinstance(response, dict) and "results" in response:
            return response["results"]
        elif isinstance(response, list):
            return response
        else:
            return []
    
    def _parse_result(self, result: Dict[str, Any], processing_time: float, index: int) -> SearchResult:
        """
        Parse Tavily result into SearchResult model.
        
        Args:
            result: Tavily result dictionary
            processing_time: Time taken for search
            index: Result index for scoring
            
        Returns:
            Parsed search result
        """
        # Calculate score based on position (higher for earlier results)
        score = max(0.1, 1.0 - (index * 0.1))
        
        return SearchResult(
            title=result.get("title", "") or "",
            url=result.get("url", ""),
            content=result.get("content", "") or result.get("raw_content", "") or "",
            score=result.get("score", score),
            source="tavily",
            published_date=result.get("published_date"),
            highlights=[],  # Tavily doesn't provide highlights
            metadata={
                "processing_time": processing_time,
                "search_depth": "basic",
                "search_type": "web",
                "index": index,
                "raw_content_available": "raw_content" in result
            }
        )
    
    async def health_check(self) -> bool:
        """
        Check Tavily API health.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Perform a simple test search
            test_query = SearchQuery(
                query="test health check",
                max_results=1,
                search_type=SearchType.WEB
            )
            
            results = await self.search(test_query)
            return len(results) >= 0  # Even 0 results is a successful response
            
        except Exception as e:
            logger.error(f"Tavily health check failed: {e}")
            return False
    
    async def get_search_capabilities(self) -> Dict[str, Any]:
        """
        Get Tavily search capabilities.
        
        Returns:
            Dictionary of capabilities
        """
        return {
            "provider": "tavily",
            "search_types": [SearchType.WEB, SearchType.KEYWORD],
            "supports_autoprompt": False,
            "supports_domain_filtering": True,
            "supports_date_filtering": False,
            "supports_highlights": False,
            "supports_raw_content": True,
            "max_results_per_query": 20,
            "search_depths": ["basic", "advanced"],
            "topics": ["general", "news"]
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"TavilySearchProvider(langchain={self.use_langchain})"
