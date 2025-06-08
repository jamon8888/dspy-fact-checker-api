"""
Exa.ai-enhanced fact-checking service with dual search and hallucination detection.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List

from app.core.search.exa_search import ExaSearchProvider
from app.core.search.tavily_search import TavilySearchProvider
from app.core.search.dual_search import DualSearchOrchestrator
from app.core.search.hallucination_detector import HallucinationDetector
from app.core.search.models import (
    SearchQuery, 
    SearchType, 
    EnhancedFactCheckResult,
    HallucinationResult,
    DualSearchResult
)
from app.core.search.exceptions import SearchProviderError, HallucinationDetectionError
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ExaFactCheckingService:
    """
    Exa.ai-enhanced fact-checking service with dual search and hallucination detection.
    
    Combines Exa.ai neural search and Tavily web search for comprehensive
    fact verification with advanced hallucination detection capabilities.
    """
    
    def __init__(self):
        """Initialize Exa.ai fact-checking service."""
        self.settings = get_settings()
        
        # Initialize search providers
        self.exa_provider = None
        self.tavily_provider = None
        self.dual_orchestrator = None
        self.hallucination_detector = None
        
        # Service metrics
        self._fact_checks_performed = 0
        self._successful_fact_checks = 0
        self._total_processing_time = 0.0
        
        logger.info("Exa.ai fact-checking service initialized")
    
    async def initialize(self):
        """Initialize search providers and components."""
        try:
            # Initialize Exa.ai provider
            if self.settings.EXA_API_KEY:
                self.exa_provider = ExaSearchProvider(self.settings.EXA_API_KEY)
                logger.info("Exa.ai provider initialized")
            else:
                logger.warning("EXA_API_KEY not configured, Exa.ai disabled")
            
            # Initialize Tavily provider
            if self.settings.TAVILY_API_KEY:
                self.tavily_provider = TavilySearchProvider(self.settings.TAVILY_API_KEY)
                logger.info("Tavily provider initialized")
            else:
                logger.warning("TAVILY_API_KEY not configured, Tavily disabled")
            
            # Initialize dual search orchestrator
            if self.exa_provider and self.tavily_provider:
                self.dual_orchestrator = DualSearchOrchestrator(
                    self.exa_provider,
                    self.tavily_provider
                )
                logger.info("Dual search orchestrator initialized")
            
            # Initialize hallucination detector
            if self.exa_provider and self.settings.HALLUCINATION_DETECTION_ENABLED:
                self.hallucination_detector = HallucinationDetector(
                    self.exa_provider,
                    self.settings.HALLUCINATION_CONFIDENCE_THRESHOLD
                )
                logger.info("Hallucination detector initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Exa.ai fact-checking service: {e}")
            raise
    
    async def fact_check_with_exa(
        self,
        claim: str,
        context: Optional[str] = None,
        search_strategy: str = "intelligent",
        require_both_providers: bool = False,
        enable_hallucination_detection: bool = True
    ) -> EnhancedFactCheckResult:
        """
        Perform enhanced fact-checking with Exa.ai and hallucination detection.
        
        Args:
            claim: The claim to fact-check
            context: Optional context for the claim
            search_strategy: Search strategy ("parallel", "sequential", "intelligent")
            require_both_providers: Whether both search providers must succeed
            enable_hallucination_detection: Whether to enable hallucination detection
            
        Returns:
            Enhanced fact-checking result
            
        Raises:
            SearchProviderError: If search fails
            HallucinationDetectionError: If hallucination detection fails
        """
        start_time = time.time()
        self._fact_checks_performed += 1
        
        try:
            logger.info(f"Starting Exa.ai fact-check for claim: {claim[:100]}...")
            
            # Ensure service is initialized
            if not self.dual_orchestrator:
                await self.initialize()
            
            # Step 1: Dual search for evidence
            search_results = await self._perform_dual_search(
                claim, search_strategy, require_both_providers
            )
            
            # Step 2: Hallucination detection (if enabled)
            if enable_hallucination_detection and self.hallucination_detector:
                hallucination_result = await self.hallucination_detector.detect_hallucination(
                    claim, context
                )
            else:
                hallucination_result = self._create_default_hallucination_result(claim)
            
            # Step 3: Analyze fact-check using search results
            fact_check_analysis = await self._analyze_fact_check(claim, search_results)
            
            # Step 4: Calculate enhanced confidence score
            enhanced_confidence = await self._calculate_enhanced_confidence(
                fact_check_analysis, hallucination_result, search_results
            )
            
            # Step 5: Generate evidence summary
            evidence_summary = await self._generate_evidence_summary(
                search_results, hallucination_result
            )
            
            # Step 6: Determine final verdict
            verdict = await self._determine_verdict(
                fact_check_analysis, hallucination_result, enhanced_confidence
            )
            
            # Step 7: Calculate accuracy score
            accuracy_score = await self._calculate_accuracy_score(
                enhanced_confidence, hallucination_result, search_results
            )
            
            processing_time = time.time() - start_time
            self._total_processing_time += processing_time
            self._successful_fact_checks += 1
            
            result = EnhancedFactCheckResult(
                claim=claim,
                verdict=verdict,
                confidence=enhanced_confidence,
                hallucination_analysis=hallucination_result,
                search_results=search_results,
                evidence_summary=evidence_summary,
                sources_used=self._get_sources_used(search_results),
                processing_time=processing_time,
                accuracy_score=accuracy_score
            )
            
            logger.info(
                f"Exa.ai fact-check completed: verdict={verdict}, "
                f"confidence={enhanced_confidence:.3f}, "
                f"hallucination={hallucination_result.is_hallucination}, "
                f"time={processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Exa.ai fact-checking failed: {e}")
            raise
    
    async def check_hallucination_only(
        self,
        claim: str,
        context: Optional[str] = None
    ) -> HallucinationResult:
        """
        Perform only hallucination detection on a claim.
        
        Args:
            claim: The claim to analyze
            context: Optional context for the claim
            
        Returns:
            Hallucination detection result
        """
        if not self.hallucination_detector:
            await self.initialize()
            
        if not self.hallucination_detector:
            raise HallucinationDetectionError("Hallucination detector not available")
        
        return await self.hallucination_detector.detect_hallucination(claim, context)
    
    async def search_with_exa_only(
        self,
        query: str,
        search_type: SearchType = SearchType.NEURAL,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform search using only Exa.ai provider.
        
        Args:
            query: Search query
            search_type: Type of search to perform
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        if not self.exa_provider:
            await self.initialize()
            
        if not self.exa_provider:
            raise SearchProviderError("Exa.ai provider not available")
        
        search_query = SearchQuery(
            query=query,
            search_type=search_type,
            max_results=max_results
        )
        
        results = await self.exa_provider.search(search_query)
        
        return [
            {
                "title": result.title,
                "url": result.url,
                "content": result.content,
                "score": result.score,
                "source": result.source,
                "highlights": result.highlights,
                "metadata": result.metadata
            }
            for result in results
        ]
    
    async def _perform_dual_search(
        self,
        claim: str,
        strategy: str,
        require_both: bool
    ) -> DualSearchResult:
        """Perform dual search for evidence."""
        if not self.dual_orchestrator:
            raise SearchProviderError("Dual search orchestrator not available")
        
        search_query = SearchQuery(
            query=claim,
            max_results=self.settings.SEARCH_MAX_RESULTS,
            search_type=SearchType.NEURAL
        )
        
        return await self.dual_orchestrator.search(
            search_query,
            strategy=strategy,
            require_both=require_both
        )
    
    def _create_default_hallucination_result(self, claim: str) -> HallucinationResult:
        """Create default hallucination result when detection is disabled."""
        return HallucinationResult(
            claim=claim,
            is_hallucination=False,
            confidence_score=0.5,
            evidence=[],
            key_facts=[],
            analysis="Hallucination detection not enabled",
            processing_time=0.0,
            evidence_consistency=0.5,
            source_credibility=0.5
        )
    
    async def _analyze_fact_check(
        self,
        claim: str,
        search_results: DualSearchResult
    ) -> Dict[str, Any]:
        """Analyze fact-check using search results."""
        all_evidence = search_results.aggregated_results
        
        if not all_evidence:
            return {
                "support_score": 0.0,
                "contradiction_score": 0.0,
                "evidence_quality": 0.0,
                "reasoning": "No evidence found"
            }
        
        # Analyze evidence for support/contradiction
        claim_words = set(claim.lower().split())
        support_count = 0
        contradiction_count = 0
        
        contradiction_indicators = {
            'false', 'incorrect', 'wrong', 'untrue', 'myth', 'debunked',
            'not', 'never', 'denied', 'refuted', 'disputed'
        }
        
        for evidence in all_evidence:
            content_words = set(evidence.content.lower().split())
            title_words = set(evidence.title.lower().split())
            all_words = content_words.union(title_words)
            
            # Check overlap with claim
            overlap = len(claim_words.intersection(all_words))
            
            if overlap > 2:  # Significant overlap
                if any(word in all_words for word in contradiction_indicators):
                    contradiction_count += 1
                else:
                    support_count += 1
        
        total_relevant = support_count + contradiction_count
        support_score = support_count / total_relevant if total_relevant > 0 else 0.0
        contradiction_score = contradiction_count / total_relevant if total_relevant > 0 else 0.0
        
        # Calculate evidence quality
        evidence_quality = min(1.0, len(all_evidence) / 5.0)
        
        return {
            "support_score": support_score,
            "contradiction_score": contradiction_score,
            "evidence_quality": evidence_quality,
            "reasoning": f"Found {support_count} supporting and {contradiction_count} contradicting evidence items"
        }
    
    async def _calculate_enhanced_confidence(
        self,
        fact_check_analysis: Dict[str, Any],
        hallucination_result: HallucinationResult,
        search_results: DualSearchResult
    ) -> float:
        """Calculate enhanced confidence score."""
        base_confidence = fact_check_analysis["support_score"]
        
        # Adjust based on hallucination detection
        hallucination_factor = hallucination_result.confidence_score
        if hallucination_result.is_hallucination:
            hallucination_factor = 1.0 - hallucination_factor
        
        # Adjust based on search success
        search_factor = search_results.success_rate
        
        # Adjust based on evidence quality
        evidence_factor = fact_check_analysis["evidence_quality"]
        
        # Combine factors with weights
        enhanced_confidence = (
            base_confidence * 0.4 +
            hallucination_factor * 0.3 +
            search_factor * 0.2 +
            evidence_factor * 0.1
        )
        
        return min(1.0, max(0.0, enhanced_confidence))
    
    async def _generate_evidence_summary(
        self,
        search_results: DualSearchResult,
        hallucination_result: HallucinationResult
    ) -> str:
        """Generate summary of evidence found."""
        summary_parts = []
        
        # Search results summary
        total_results = search_results.total_results
        exa_count = len(search_results.exa_results)
        tavily_count = len(search_results.tavily_results)
        
        summary_parts.append(f"Found {total_results} total evidence sources:")
        summary_parts.append(f"- Exa.ai neural search: {exa_count} results")
        summary_parts.append(f"- Tavily web search: {tavily_count} results")
        
        # Hallucination analysis summary
        summary_parts.append(f"\nHallucination Analysis:")
        summary_parts.append(f"- Risk level: {hallucination_result.risk_level}")
        summary_parts.append(f"- Key facts analyzed: {len(hallucination_result.key_facts)}")
        
        # Top sources
        if search_results.aggregated_results:
            summary_parts.append(f"\nTop Evidence Sources:")
            for i, result in enumerate(search_results.aggregated_results[:3], 1):
                summary_parts.append(f"{i}. {result.title} ({result.source})")
        
        return "\n".join(summary_parts)
    
    async def _determine_verdict(
        self,
        fact_check_analysis: Dict[str, Any],
        hallucination_result: HallucinationResult,
        confidence: float
    ) -> str:
        """Determine final fact-check verdict."""
        if hallucination_result.is_hallucination and hallucination_result.confidence_score > 0.8:
            return "False - Likely Hallucination"
        
        if confidence >= 0.8:
            if fact_check_analysis["support_score"] > fact_check_analysis["contradiction_score"]:
                return "True"
            else:
                return "False"
        elif confidence >= 0.6:
            return "Partially True"
        elif confidence >= 0.4:
            return "Unverifiable"
        else:
            return "False"
    
    async def _calculate_accuracy_score(
        self,
        confidence: float,
        hallucination_result: HallucinationResult,
        search_results: DualSearchResult
    ) -> float:
        """Calculate overall accuracy score."""
        base_accuracy = confidence
        
        # Boost for high-quality hallucination detection
        if hallucination_result.confidence_score > 0.8:
            base_accuracy *= 1.1
        
        # Boost for successful dual search
        if search_results.success_rate == 1.0:
            base_accuracy *= 1.05
        
        return min(1.0, base_accuracy)
    
    def _get_sources_used(self, search_results: DualSearchResult) -> List[str]:
        """Get list of sources used in search."""
        sources = []
        
        if search_results.exa_success and search_results.exa_results:
            sources.append("exa")
        
        if search_results.tavily_success and search_results.tavily_results:
            sources.append("tavily")
        
        return sources
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        avg_time = (
            self._total_processing_time / self._fact_checks_performed 
            if self._fact_checks_performed > 0 else 0.0
        )
        success_rate = (
            self._successful_fact_checks / self._fact_checks_performed 
            if self._fact_checks_performed > 0 else 0.0
        )
        
        stats = {
            "fact_checks_performed": self._fact_checks_performed,
            "successful_fact_checks": self._successful_fact_checks,
            "success_rate": success_rate,
            "average_processing_time": avg_time
        }
        
        # Add orchestrator stats if available
        if self.dual_orchestrator:
            orchestrator_stats = await self.dual_orchestrator.get_orchestrator_stats()
            stats["dual_search_stats"] = orchestrator_stats
        
        return stats


# Global service instance
exa_fact_checking_service = ExaFactCheckingService()
