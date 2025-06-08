"""
Unified Search Service - Single service with all search providers and capabilities.
Integrates Exa.ai, Tavily, and hallucination detection into existing architecture.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Union
from enum import Enum

from app.core.search.exa_search import ExaSearchProvider
from app.core.search.tavily_search import TavilySearchProvider
from app.core.search.dual_search import DualSearchOrchestrator
from app.core.search.hallucination_detector import HallucinationDetector
from app.core.search.models import SearchQuery, SearchType, SearchResult
from app.core.search.exceptions import SearchProviderError, HallucinationDetectionError
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SearchProvider(str, Enum):
    """Available search providers."""
    EXA = "exa"
    TAVILY = "tavily"
    DUAL = "dual"
    AUTO = "auto"


class SearchMode(str, Enum):
    """Search modes for different use cases."""
    FACT_CHECK = "fact_check"
    RESEARCH = "research"
    HALLUCINATION_CHECK = "hallucination_check"
    GENERAL = "general"


class UnifiedSearchService:
    """
    Unified search service that provides all search capabilities through a single interface.
    
    Features:
    - Multiple search providers (Exa.ai, Tavily, Dual)
    - Intelligent provider selection
    - Hallucination detection
    - Enhanced fact-checking
    - Performance optimization
    """
    
    def __init__(self):
        """Initialize unified search service."""
        self.settings = get_settings()
        
        # Search providers
        self.exa_provider = None
        self.tavily_provider = None
        self.dual_orchestrator = None
        self.hallucination_detector = None
        
        # Service state
        self.initialized = False
        self._search_count = 0
        self._success_count = 0
        
        logger.info("Unified search service initialized")
    
    async def initialize(self):
        """Initialize all search providers."""
        try:
            # Initialize Exa.ai provider
            if self.settings.EXA_API_KEY:
                self.exa_provider = ExaSearchProvider(self.settings.EXA_API_KEY)
                logger.info("Exa.ai provider initialized")
            
            # Initialize Tavily provider
            if self.settings.TAVILY_API_KEY:
                self.tavily_provider = TavilySearchProvider(self.settings.TAVILY_API_KEY)
                logger.info("Tavily provider initialized")
            
            # Initialize dual orchestrator
            if self.exa_provider and self.tavily_provider:
                self.dual_orchestrator = DualSearchOrchestrator(
                    self.exa_provider, self.tavily_provider
                )
                logger.info("Dual search orchestrator initialized")
            
            # Initialize hallucination detector
            if self.exa_provider and self.settings.HALLUCINATION_DETECTION_ENABLED:
                self.hallucination_detector = HallucinationDetector(
                    self.exa_provider,
                    self.settings.HALLUCINATION_CONFIDENCE_THRESHOLD
                )
                logger.info("Hallucination detector initialized")
            
            self.initialized = True
            logger.info("Unified search service fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize unified search service: {e}")
            raise
    
    async def search(
        self,
        query: str,
        provider: SearchProvider = SearchProvider.AUTO,
        mode: SearchMode = SearchMode.GENERAL,
        max_results: int = 10,
        search_type: SearchType = SearchType.NEURAL,
        include_hallucination_check: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Unified search method that handles all search scenarios.
        
        Args:
            query: Search query
            provider: Which provider to use (auto-selects if AUTO)
            mode: Search mode for different use cases
            max_results: Maximum number of results
            search_type: Type of search (neural, keyword, etc.)
            include_hallucination_check: Whether to include hallucination detection
            **kwargs: Additional search parameters
            
        Returns:
            Unified search results with all relevant information
        """
        start_time = time.time()
        self._search_count += 1
        
        try:
            if not self.initialized:
                await self.initialize()
            
            # Auto-select provider based on mode and availability
            selected_provider = self._select_provider(provider, mode)
            
            # Create search query
            search_query = SearchQuery(
                query=query,
                search_type=search_type,
                max_results=max_results,
                **kwargs
            )
            
            # Execute search based on selected provider
            search_results = await self._execute_search(selected_provider, search_query)
            
            # Add hallucination detection if requested or mode requires it
            hallucination_result = None
            if include_hallucination_check or mode == SearchMode.HALLUCINATION_CHECK:
                hallucination_result = await self._check_hallucination(query)
            
            # Process results based on mode
            processed_results = await self._process_results(
                search_results, hallucination_result, mode, query
            )
            
            processing_time = time.time() - start_time
            self._success_count += 1
            
            return {
                "success": True,
                "query": query,
                "provider_used": selected_provider,
                "mode": mode,
                "processing_time": processing_time,
                "results": processed_results,
                "hallucination_analysis": hallucination_result,
                "metadata": {
                    "total_results": len(search_results) if isinstance(search_results, list) else search_results.total_results if hasattr(search_results, 'total_results') else 0,
                    "search_type": search_type,
                    "timestamp": time.time()
                }
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Unified search failed: {e}")
            
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__,
                "processing_time": processing_time,
                "provider_attempted": provider,
                "mode": mode
            }
    
    async def fact_check(
        self,
        claim: str,
        provider: SearchProvider = SearchProvider.AUTO,
        include_hallucination_check: bool = True,
        confidence_threshold: float = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Enhanced fact-checking using unified search capabilities.
        
        Args:
            claim: Claim to fact-check
            provider: Search provider to use
            include_hallucination_check: Whether to include hallucination detection
            confidence_threshold: Confidence threshold for verdict
            **kwargs: Additional parameters
            
        Returns:
            Comprehensive fact-checking results
        """
        return await self.search(
            query=claim,
            provider=provider,
            mode=SearchMode.FACT_CHECK,
            include_hallucination_check=include_hallucination_check,
            confidence_threshold=confidence_threshold,
            **kwargs
        )
    
    async def research(
        self,
        topic: str,
        provider: SearchProvider = SearchProvider.DUAL,
        max_results: int = 20,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Research mode for comprehensive information gathering.
        
        Args:
            topic: Research topic
            provider: Search provider to use
            max_results: Maximum number of results
            **kwargs: Additional parameters
            
        Returns:
            Research results with comprehensive information
        """
        return await self.search(
            query=topic,
            provider=provider,
            mode=SearchMode.RESEARCH,
            max_results=max_results,
            **kwargs
        )
    
    def _select_provider(self, provider: SearchProvider, mode: SearchMode) -> str:
        """Select the best provider based on mode and availability."""
        if provider != SearchProvider.AUTO:
            return provider.value
        
        # Auto-selection logic based on mode
        if mode == SearchMode.HALLUCINATION_CHECK:
            return SearchProvider.EXA.value if self.exa_provider else SearchProvider.TAVILY.value
        
        elif mode == SearchMode.FACT_CHECK:
            return SearchProvider.DUAL.value if self.dual_orchestrator else SearchProvider.EXA.value
        
        elif mode == SearchMode.RESEARCH:
            return SearchProvider.DUAL.value if self.dual_orchestrator else SearchProvider.TAVILY.value
        
        else:  # GENERAL
            # Prefer Exa for semantic understanding, fallback to Tavily
            return SearchProvider.EXA.value if self.exa_provider else SearchProvider.TAVILY.value
    
    async def _execute_search(self, provider: str, query: SearchQuery) -> Union[List[SearchResult], Any]:
        """Execute search with the selected provider."""
        if provider == SearchProvider.EXA.value and self.exa_provider:
            return await self.exa_provider.search(query)
        
        elif provider == SearchProvider.TAVILY.value and self.tavily_provider:
            return await self.tavily_provider.search(query)
        
        elif provider == SearchProvider.DUAL.value and self.dual_orchestrator:
            return await self.dual_orchestrator.search(query, strategy="intelligent")
        
        else:
            # Fallback to any available provider
            if self.exa_provider:
                return await self.exa_provider.search(query)
            elif self.tavily_provider:
                return await self.tavily_provider.search(query)
            else:
                raise SearchProviderError("No search providers available")
    
    async def _check_hallucination(self, claim: str) -> Optional[Dict[str, Any]]:
        """Check for hallucinations if detector is available."""
        if not self.hallucination_detector:
            return None
        
        try:
            result = await self.hallucination_detector.detect_hallucination(claim)
            return {
                "is_hallucination": result.is_hallucination,
                "confidence_score": result.confidence_score,
                "risk_level": result.risk_level,
                "key_facts": result.key_facts,
                "evidence_count": len(result.evidence),
                "analysis": result.analysis
            }
        except Exception as e:
            logger.warning(f"Hallucination detection failed: {e}")
            return None
    
    async def _process_results(
        self,
        search_results: Union[List[SearchResult], Any],
        hallucination_result: Optional[Dict[str, Any]],
        mode: SearchMode,
        query: str
    ) -> Dict[str, Any]:
        """Process search results based on the mode."""
        
        if mode == SearchMode.FACT_CHECK:
            return await self._process_fact_check_results(
                search_results, hallucination_result, query
            )
        
        elif mode == SearchMode.RESEARCH:
            return await self._process_research_results(search_results)
        
        elif mode == SearchMode.HALLUCINATION_CHECK:
            return {
                "hallucination_analysis": hallucination_result,
                "supporting_evidence": self._extract_evidence_summary(search_results)
            }
        
        else:  # GENERAL
            return await self._process_general_results(search_results)
    
    async def _process_fact_check_results(
        self,
        search_results: Union[List[SearchResult], Any],
        hallucination_result: Optional[Dict[str, Any]],
        claim: str
    ) -> Dict[str, Any]:
        """Process results for fact-checking mode."""
        
        # Extract evidence from search results
        evidence = self._extract_evidence_summary(search_results)
        
        # Calculate confidence based on evidence and hallucination analysis
        confidence = self._calculate_fact_check_confidence(evidence, hallucination_result)
        
        # Determine verdict
        verdict = self._determine_verdict(confidence, hallucination_result)
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "evidence_summary": evidence,
            "hallucination_analysis": hallucination_result,
            "sources_count": len(evidence.get("sources", [])),
            "recommendation": self._get_fact_check_recommendation(verdict, confidence)
        }
    
    async def _process_research_results(self, search_results: Union[List[SearchResult], Any]) -> Dict[str, Any]:
        """Process results for research mode."""
        evidence = self._extract_evidence_summary(search_results)
        
        return {
            "research_summary": evidence,
            "key_topics": self._extract_key_topics(search_results),
            "source_diversity": self._analyze_source_diversity(search_results),
            "information_quality": self._assess_information_quality(search_results)
        }
    
    async def _process_general_results(self, search_results: Union[List[SearchResult], Any]) -> Dict[str, Any]:
        """Process results for general search mode."""
        return {
            "search_results": self._format_search_results(search_results),
            "summary": self._generate_search_summary(search_results)
        }
    
    def _extract_evidence_summary(self, search_results: Union[List[SearchResult], Any]) -> Dict[str, Any]:
        """Extract evidence summary from search results."""
        if hasattr(search_results, 'aggregated_results'):
            results = search_results.aggregated_results
        elif isinstance(search_results, list):
            results = search_results
        else:
            results = []
        
        return {
            "total_sources": len(results),
            "sources": [
                {
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    "score": result.score,
                    "source": result.source
                }
                for result in results[:5]  # Top 5 sources
            ],
            "source_types": list(set(result.source for result in results))
        }
    
    def _calculate_fact_check_confidence(
        self,
        evidence: Dict[str, Any],
        hallucination_result: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for fact-checking."""
        base_confidence = min(1.0, evidence["total_sources"] / 5.0)  # More sources = higher confidence
        
        if hallucination_result:
            hallucination_factor = 1.0 - hallucination_result["confidence_score"] if hallucination_result["is_hallucination"] else hallucination_result["confidence_score"]
            return (base_confidence + hallucination_factor) / 2
        
        return base_confidence
    
    def _determine_verdict(self, confidence: float, hallucination_result: Optional[Dict[str, Any]]) -> str:
        """Determine fact-check verdict."""
        if hallucination_result and hallucination_result["is_hallucination"] and hallucination_result["confidence_score"] > 0.8:
            return "False - Likely Hallucination"
        
        if confidence >= 0.8:
            return "True"
        elif confidence >= 0.6:
            return "Partially True"
        elif confidence >= 0.4:
            return "Unverifiable"
        else:
            return "False"
    
    def _get_fact_check_recommendation(self, verdict: str, confidence: float) -> str:
        """Get recommendation based on verdict and confidence."""
        if verdict == "True":
            return "High confidence in accuracy. Claim appears to be factual."
        elif verdict == "Partially True":
            return "Moderate confidence. Claim has some factual basis but may need verification."
        elif verdict == "Unverifiable":
            return "Low confidence. Insufficient evidence to verify claim."
        else:
            return "Claim appears to be false or misleading. Exercise caution."
    
    def _format_search_results(self, search_results: Union[List[SearchResult], Any]) -> List[Dict[str, Any]]:
        """Format search results for API response."""
        if hasattr(search_results, 'aggregated_results'):
            results = search_results.aggregated_results
        elif isinstance(search_results, list):
            results = search_results
        else:
            results = []
        
        return [
            {
                "title": result.title,
                "url": result.url,
                "content": result.content,
                "score": result.score,
                "source": result.source,
                "highlights": result.highlights,
                "published_date": result.published_date
            }
            for result in results
        ]
    
    def _generate_search_summary(self, search_results: Union[List[SearchResult], Any]) -> str:
        """Generate a summary of search results."""
        if hasattr(search_results, 'total_results'):
            total = search_results.total_results
        elif isinstance(search_results, list):
            total = len(search_results)
        else:
            total = 0
        
        return f"Found {total} relevant results from multiple sources."
    
    def _extract_key_topics(self, search_results: Union[List[SearchResult], Any]) -> List[str]:
        """Extract key topics from search results."""
        # Simple implementation - in production would use NLP
        return ["topic1", "topic2", "topic3"]  # Placeholder
    
    def _analyze_source_diversity(self, search_results: Union[List[SearchResult], Any]) -> Dict[str, Any]:
        """Analyze diversity of sources."""
        return {"diversity_score": 0.8, "unique_domains": 5}  # Placeholder
    
    def _assess_information_quality(self, search_results: Union[List[SearchResult], Any]) -> Dict[str, Any]:
        """Assess quality of information."""
        return {"quality_score": 0.85, "credibility_score": 0.9}  # Placeholder
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status."""
        return {
            "initialized": self.initialized,
            "providers_available": {
                "exa": self.exa_provider is not None,
                "tavily": self.tavily_provider is not None,
                "dual": self.dual_orchestrator is not None,
                "hallucination_detector": self.hallucination_detector is not None
            },
            "statistics": {
                "total_searches": self._search_count,
                "successful_searches": self._success_count,
                "success_rate": self._success_count / self._search_count if self._search_count > 0 else 0.0
            }
        }


# Global service instance
unified_search_service = UnifiedSearchService()
