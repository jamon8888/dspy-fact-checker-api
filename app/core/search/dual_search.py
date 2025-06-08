"""
Dual search orchestrator for combining Exa.ai and Tavily search results.
"""

import asyncio
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict

from .exa_search import ExaSearchProvider
from .tavily_search import TavilySearchProvider
from .models import SearchQuery, SearchResult, DualSearchResult, SearchType
from .exceptions import SearchOrchestrationError, SearchProviderError
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class DualSearchOrchestrator:
    """
    Orchestrates dual search operations across Exa.ai and Tavily providers.
    
    Supports multiple search strategies:
    - Parallel: Execute both searches simultaneously
    - Sequential: Execute searches one after another
    - Intelligent: Choose strategy based on query characteristics
    """
    
    def __init__(
        self,
        exa_provider: ExaSearchProvider,
        tavily_provider: TavilySearchProvider
    ):
        """
        Initialize dual search orchestrator.
        
        Args:
            exa_provider: Exa.ai search provider
            tavily_provider: Tavily search provider
        """
        self.exa_provider = exa_provider
        self.tavily_provider = tavily_provider
        self.settings = get_settings()
        
        # Search metrics
        self._search_count = 0
        self._success_count = 0
        self._total_time = 0.0
        
        logger.info("Dual search orchestrator initialized")
    
    async def search(
        self,
        query: SearchQuery,
        strategy: str = "parallel",
        require_both: bool = False
    ) -> DualSearchResult:
        """
        Execute dual search across both providers.
        
        Args:
            query: Search query
            strategy: Search strategy ("parallel", "sequential", "intelligent")
            require_both: Whether both providers must succeed
            
        Returns:
            Dual search result
            
        Raises:
            SearchOrchestrationError: If search orchestration fails
        """
        start_time = time.time()
        self._search_count += 1
        
        try:
            logger.info(f"Starting dual search with strategy: {strategy}")
            
            # Route to appropriate search strategy
            if strategy == "parallel":
                result = await self._parallel_search(query, require_both)
            elif strategy == "sequential":
                result = await self._sequential_search(query, require_both)
            elif strategy == "intelligent":
                result = await self._intelligent_search(query, require_both)
            else:
                raise SearchOrchestrationError(f"Unknown search strategy: {strategy}")
            
            # Update metrics
            processing_time = time.time() - start_time
            self._total_time += processing_time
            self._success_count += 1
            
            # Update result with timing
            result.processing_time = processing_time
            result.search_strategy = strategy
            
            logger.info(
                f"Dual search completed: {result.total_results} total results, "
                f"exa_success={result.exa_success}, tavily_success={result.tavily_success}, "
                f"time={processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Dual search failed: {e}")
            raise SearchOrchestrationError(
                f"Dual search failed: {e}",
                failed_providers=[]
            )
    
    async def _parallel_search(
        self,
        query: SearchQuery,
        require_both: bool = False
    ) -> DualSearchResult:
        """
        Execute parallel search across both providers.
        
        Args:
            query: Search query
            require_both: Whether both providers must succeed
            
        Returns:
            Dual search result
        """
        # Create tasks for both searches
        exa_task = asyncio.create_task(self._safe_exa_search(query))
        tavily_task = asyncio.create_task(self._safe_tavily_search(query))
        
        # Wait for both searches with timeout
        try:
            exa_results, tavily_results = await asyncio.wait_for(
                asyncio.gather(exa_task, tavily_task, return_exceptions=True),
                timeout=self.settings.DUAL_SEARCH_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning(f"Dual search timeout after {self.settings.DUAL_SEARCH_TIMEOUT}s")
            exa_results = []
            tavily_results = []
        
        # Handle exceptions
        exa_success = not isinstance(exa_results, Exception)
        tavily_success = not isinstance(tavily_results, Exception)
        
        if isinstance(exa_results, Exception):
            logger.warning(f"Exa search failed: {exa_results}")
            exa_results = []
        
        if isinstance(tavily_results, Exception):
            logger.warning(f"Tavily search failed: {tavily_results}")
            tavily_results = []
        
        # Check if we meet requirements
        if require_both and (not exa_success or not tavily_success):
            failed_providers = []
            if not exa_success:
                failed_providers.append("exa")
            if not tavily_success:
                failed_providers.append("tavily")
            
            raise SearchOrchestrationError(
                "Both providers required but one or more failed",
                failed_providers=failed_providers
            )
        
        # Aggregate results
        aggregated_results = await self._aggregate_results(exa_results, tavily_results)
        
        return DualSearchResult(
            query=query.query,
            exa_results=exa_results,
            tavily_results=tavily_results,
            aggregated_results=aggregated_results,
            search_strategy="parallel",
            processing_time=0.0,  # Will be set by caller
            exa_success=exa_success,
            tavily_success=tavily_success,
            metadata={
                "require_both": require_both,
                "timeout": self.settings.DUAL_SEARCH_TIMEOUT
            }
        )
    
    async def _sequential_search(
        self,
        query: SearchQuery,
        require_both: bool = False
    ) -> DualSearchResult:
        """
        Execute sequential search (Exa first, then Tavily).
        
        Args:
            query: Search query
            require_both: Whether both providers must succeed
            
        Returns:
            Dual search result
        """
        exa_results = []
        tavily_results = []
        exa_success = False
        tavily_success = False
        
        # Search with Exa first
        try:
            exa_results = await self._safe_exa_search(query)
            exa_success = True
        except Exception as e:
            logger.warning(f"Exa search failed in sequential mode: {e}")
            if require_both:
                raise SearchOrchestrationError(
                    "Exa search failed and both providers required",
                    failed_providers=["exa"]
                )
        
        # Search with Tavily second
        try:
            tavily_results = await self._safe_tavily_search(query)
            tavily_success = True
        except Exception as e:
            logger.warning(f"Tavily search failed in sequential mode: {e}")
            if require_both:
                raise SearchOrchestrationError(
                    "Tavily search failed and both providers required",
                    failed_providers=["tavily"]
                )
        
        # Aggregate results
        aggregated_results = await self._aggregate_results(exa_results, tavily_results)
        
        return DualSearchResult(
            query=query.query,
            exa_results=exa_results,
            tavily_results=tavily_results,
            aggregated_results=aggregated_results,
            search_strategy="sequential",
            processing_time=0.0,  # Will be set by caller
            exa_success=exa_success,
            tavily_success=tavily_success,
            metadata={
                "require_both": require_both,
                "execution_order": ["exa", "tavily"]
            }
        )
    
    async def _intelligent_search(
        self,
        query: SearchQuery,
        require_both: bool = False
    ) -> DualSearchResult:
        """
        Execute intelligent search with dynamic strategy selection.
        
        Args:
            query: Search query
            require_both: Whether both providers must succeed
            
        Returns:
            Dual search result
        """
        # Analyze query to determine best strategy
        strategy = self._analyze_query_for_strategy(query)
        
        if strategy == "exa_only":
            # Use only Exa for semantic/neural queries
            exa_results = await self._safe_exa_search(query)
            tavily_results = []
            
            aggregated_results = exa_results
            
            return DualSearchResult(
                query=query.query,
                exa_results=exa_results,
                tavily_results=tavily_results,
                aggregated_results=aggregated_results,
                search_strategy="intelligent_exa_only",
                processing_time=0.0,
                exa_success=True,
                tavily_success=True,  # Not attempted, so not failed
                metadata={
                    "intelligent_choice": "exa_only",
                    "reasoning": "Query best suited for neural search"
                }
            )
        
        elif strategy == "tavily_only":
            # Use only Tavily for factual/news queries
            tavily_results = await self._safe_tavily_search(query)
            exa_results = []
            
            aggregated_results = tavily_results
            
            return DualSearchResult(
                query=query.query,
                exa_results=exa_results,
                tavily_results=tavily_results,
                aggregated_results=aggregated_results,
                search_strategy="intelligent_tavily_only",
                processing_time=0.0,
                exa_success=True,  # Not attempted, so not failed
                tavily_success=True,
                metadata={
                    "intelligent_choice": "tavily_only",
                    "reasoning": "Query best suited for web search"
                }
            )
        
        else:
            # Use parallel search for complex queries
            return await self._parallel_search(query, require_both)
    
    def _analyze_query_for_strategy(self, query: SearchQuery) -> str:
        """
        Analyze query to determine optimal search strategy.
        
        Args:
            query: Search query
            
        Returns:
            Recommended strategy
        """
        query_text = query.query.lower()
        
        # Keywords that suggest neural search (Exa) is better
        neural_keywords = {
            'concept', 'meaning', 'definition', 'explain', 'understand',
            'theory', 'philosophy', 'analysis', 'interpretation', 'semantic'
        }
        
        # Keywords that suggest web search (Tavily) is better
        web_keywords = {
            'news', 'recent', 'latest', 'current', 'today', 'yesterday',
            'breaking', 'update', 'announcement', 'report', 'price', 'stock'
        }
        
        # Check for neural search indicators
        if any(keyword in query_text for keyword in neural_keywords):
            return "exa_only"
        
        # Check for web search indicators
        if any(keyword in query_text for keyword in web_keywords):
            return "tavily_only"
        
        # Check query type
        if query.search_type == SearchType.NEURAL:
            return "exa_only"
        elif query.search_type == SearchType.WEB:
            return "tavily_only"
        
        # Default to parallel for complex queries
        return "parallel"
    
    async def _safe_exa_search(self, query: SearchQuery) -> List[SearchResult]:
        """Safely execute Exa search with error handling."""
        try:
            return await self.exa_provider.search_with_retry(query)
        except Exception as e:
            logger.warning(f"Exa search failed: {e}")
            raise
    
    async def _safe_tavily_search(self, query: SearchQuery) -> List[SearchResult]:
        """Safely execute Tavily search with error handling."""
        try:
            # Convert neural search to web search for Tavily
            tavily_query = SearchQuery(
                query=query.query,
                max_results=query.max_results,
                search_type=SearchType.WEB,
                filters=query.filters,
                include_domains=query.include_domains,
                exclude_domains=query.exclude_domains
            )
            return await self.tavily_provider.search_with_retry(tavily_query)
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
            raise
    
    async def _aggregate_results(
        self,
        exa_results: List[SearchResult],
        tavily_results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Aggregate and rank results from both providers.
        
        Args:
            exa_results: Results from Exa.ai
            tavily_results: Results from Tavily
            
        Returns:
            Aggregated and ranked results
        """
        if not self.settings.SEARCH_RESULT_AGGREGATION:
            # Simple concatenation if aggregation is disabled
            return exa_results + tavily_results
        
        # Combine all results
        all_results = exa_results + tavily_results
        
        # Remove duplicates based on URL similarity
        unique_results = self._deduplicate_results(all_results)
        
        # Score and rank results
        scored_results = self._score_results(unique_results)
        
        # Sort by score (descending)
        scored_results.sort(key=lambda x: x.score, reverse=True)
        
        # Limit to max results
        max_results = self.settings.SEARCH_MAX_RESULTS
        return scored_results[:max_results]
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on URL similarity."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            # Normalize URL for comparison
            normalized_url = result.url.lower().rstrip('/')
            
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_results.append(result)
        
        return unique_results
    
    def _score_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Score results based on multiple factors.
        
        Args:
            results: List of search results
            
        Returns:
            Results with updated scores
        """
        for result in results:
            # Base score from provider
            base_score = result.score
            
            # Boost Exa results slightly for semantic relevance
            if result.source == "exa":
                base_score *= 1.1
            
            # Boost results with highlights
            if result.highlights:
                base_score *= 1.05
            
            # Boost results with recent dates
            if result.published_date:
                # Simple recency boost (would be more sophisticated in production)
                base_score *= 1.02
            
            # Update the score
            result.score = min(1.0, base_score)
        
        return results
    
    async def get_orchestrator_stats(self) -> Dict[str, Any]:
        """
        Get orchestrator statistics.
        
        Returns:
            Dictionary with orchestrator stats
        """
        avg_time = self._total_time / self._search_count if self._search_count > 0 else 0.0
        success_rate = self._success_count / self._search_count if self._search_count > 0 else 0.0
        
        exa_status = await self.exa_provider.get_status()
        tavily_status = await self.tavily_provider.get_status()
        
        return {
            "total_searches": self._search_count,
            "successful_searches": self._success_count,
            "success_rate": success_rate,
            "average_response_time": avg_time,
            "exa_provider_status": exa_status.dict(),
            "tavily_provider_status": tavily_status.dict(),
            "settings": {
                "dual_search_timeout": self.settings.DUAL_SEARCH_TIMEOUT,
                "result_aggregation": self.settings.SEARCH_RESULT_AGGREGATION,
                "intelligent_routing": self.settings.INTELLIGENT_ROUTING_ENABLED
            }
        }
    
    def reset_stats(self):
        """Reset orchestrator statistics."""
        self._search_count = 0
        self._success_count = 0
        self._total_time = 0.0
        
        # Reset provider stats too
        self.exa_provider.reset_metrics()
        self.tavily_provider.reset_metrics()
        
        logger.info("Dual search orchestrator stats reset")
