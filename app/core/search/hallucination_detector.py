"""
Hallucination detection using Exa.ai's methodology.

This module implements hallucination detection following the approach described in:
https://docs.exa.ai/examples/identifying-hallucinations-with-exa
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
import re

from .exa_search import ExaSearchProvider
from .models import SearchQuery, SearchResult, HallucinationResult, SearchType
from .exceptions import HallucinationDetectionError, SearchProviderError
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class HallucinationDetector:
    """
    Hallucination detector using Exa.ai's neural search capabilities.
    
    Implements the methodology from Exa.ai's hallucination detection guide:
    1. Extract key facts from claims
    2. Search for supporting evidence using neural search
    3. Analyze evidence consistency
    4. Generate hallucination assessment
    """
    
    def __init__(self, exa_client: ExaSearchProvider, confidence_threshold: float = None):
        """
        Initialize hallucination detector.
        
        Args:
            exa_client: Exa.ai search provider
            confidence_threshold: Confidence threshold for hallucination detection
        """
        self.exa_client = exa_client
        self.settings = get_settings()
        self.confidence_threshold = (
            confidence_threshold or 
            self.settings.HALLUCINATION_CONFIDENCE_THRESHOLD
        )
        
        logger.info(
            f"Hallucination detector initialized with threshold: {self.confidence_threshold}"
        )
    
    async def detect_hallucination(
        self, 
        claim: str, 
        context: Optional[str] = None
    ) -> HallucinationResult:
        """
        Detect hallucinations in a claim using Exa.ai's methodology.
        
        Args:
            claim: The claim to analyze
            context: Optional context for the claim
            
        Returns:
            Hallucination detection result
            
        Raises:
            HallucinationDetectionError: If detection fails
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting hallucination detection for claim: {claim[:100]}...")
            
            # Step 1: Extract key facts from claim
            key_facts = await self._extract_key_facts(claim)
            logger.debug(f"Extracted {len(key_facts)} key facts: {key_facts}")
            
            # Step 2: Search for supporting evidence using neural search
            evidence_results = await self._gather_evidence(key_facts, claim)
            logger.debug(f"Gathered {len(evidence_results)} evidence items")
            
            # Step 3: Analyze evidence consistency
            consistency_analysis = await self._analyze_consistency(claim, evidence_results)
            
            # Step 4: Calculate source credibility
            credibility_score = await self._calculate_source_credibility(evidence_results)
            
            # Step 5: Generate final assessment
            is_hallucination = consistency_analysis["score"] < self.confidence_threshold
            analysis = await self._generate_analysis(
                claim, evidence_results, consistency_analysis, credibility_score
            )
            
            processing_time = time.time() - start_time
            
            result = HallucinationResult(
                claim=claim,
                is_hallucination=is_hallucination,
                confidence_score=consistency_analysis["score"],
                evidence=evidence_results,
                key_facts=key_facts,
                analysis=analysis,
                processing_time=processing_time,
                evidence_consistency=consistency_analysis["score"],
                source_credibility=credibility_score
            )
            
            logger.info(
                f"Hallucination detection completed: "
                f"is_hallucination={is_hallucination}, "
                f"confidence={consistency_analysis['score']:.3f}, "
                f"time={processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Hallucination detection failed: {e}")
            raise HallucinationDetectionError(
                f"Hallucination detection failed: {e}",
                provider="exa",
                original_error=e
            )
    
    async def _extract_key_facts(self, claim: str) -> List[str]:
        """
        Extract key facts from a claim for verification.
        
        Args:
            claim: The claim to analyze
            
        Returns:
            List of key facts
        """
        # Simple fact extraction using regex patterns
        # In a production system, this could use NLP models
        
        facts = []
        
        # Extract named entities (simple patterns)
        # People names (capitalized words)
        people = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', claim)
        facts.extend([f"person: {person}" for person in people])
        
        # Organizations (words with "Inc", "Corp", "Company", etc.)
        orgs = re.findall(r'\b[A-Z][a-zA-Z\s]*(Inc|Corp|Company|Organization|Agency)\b', claim)
        facts.extend([f"organization: {org}" for org in orgs])
        
        # Dates (various formats)
        dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}\b|\b[A-Z][a-z]+ \d{1,2}, \d{4}\b', claim)
        facts.extend([f"date: {date}" for date in dates])
        
        # Numbers and statistics
        numbers = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?(?:%|percent|million|billion|thousand)?\b', claim)
        facts.extend([f"statistic: {num}" for num in numbers if len(num) > 2])
        
        # Locations (capitalized words that might be places)
        locations = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', claim)
        # Filter out common words that aren't locations
        common_words = {'The', 'This', 'That', 'These', 'Those', 'And', 'But', 'Or', 'So'}
        locations = [loc for loc in locations if loc not in common_words and len(loc) > 3]
        facts.extend([f"location: {loc}" for loc in locations[:3]])  # Limit to avoid noise
        
        # If no specific facts found, use the claim itself broken into sentences
        if not facts:
            sentences = re.split(r'[.!?]+', claim)
            facts = [sent.strip() for sent in sentences if len(sent.strip()) > 10]
        
        # Limit to most important facts
        return facts[:5]
    
    async def _gather_evidence(self, key_facts: List[str], original_claim: str) -> List[SearchResult]:
        """
        Gather evidence for key facts using neural search.
        
        Args:
            key_facts: List of key facts to search for
            original_claim: Original claim for context
            
        Returns:
            List of search results as evidence
        """
        evidence_results = []
        
        # Search for each key fact
        for fact in key_facts:
            try:
                search_query = SearchQuery(
                    query=fact,
                    search_type=SearchType.NEURAL,
                    max_results=3,
                    use_autoprompt=True
                )
                
                results = await self.exa_client.search(search_query)
                evidence_results.extend(results)
                
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.1)
                
            except SearchProviderError as e:
                logger.warning(f"Failed to search for fact '{fact}': {e}")
                continue
        
        # Also search for the original claim
        try:
            claim_query = SearchQuery(
                query=original_claim,
                search_type=SearchType.NEURAL,
                max_results=5,
                use_autoprompt=True
            )
            
            claim_results = await self.exa_client.search(claim_query)
            evidence_results.extend(claim_results)
            
        except SearchProviderError as e:
            logger.warning(f"Failed to search for original claim: {e}")
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in evidence_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results[:10]  # Limit to top 10 results
    
    async def _analyze_consistency(
        self, 
        claim: str, 
        evidence: List[SearchResult]
    ) -> Dict[str, Any]:
        """
        Analyze consistency between claim and evidence.
        
        Args:
            claim: Original claim
            evidence: List of evidence results
            
        Returns:
            Dictionary with consistency analysis
        """
        if not evidence:
            return {
                "score": 0.0,
                "reasoning": "No evidence found to support or contradict the claim",
                "supporting_count": 0,
                "contradicting_count": 0,
                "neutral_count": 0
            }
        
        # Simple consistency analysis based on keyword overlap
        # In production, this would use more sophisticated NLP
        
        claim_words = set(claim.lower().split())
        supporting_count = 0
        contradicting_count = 0
        neutral_count = 0
        
        contradiction_words = {
            'not', 'no', 'never', 'false', 'incorrect', 'wrong', 'untrue',
            'denied', 'refuted', 'disputed', 'debunked', 'myth'
        }
        
        for result in evidence:
            content_words = set(result.content.lower().split())
            title_words = set(result.title.lower().split())
            all_words = content_words.union(title_words)
            
            # Check for contradictions
            if any(word in all_words for word in contradiction_words):
                # Check if contradiction is about our claim
                overlap = len(claim_words.intersection(all_words))
                if overlap > 2:  # Significant overlap suggests it's about our claim
                    contradicting_count += 1
                else:
                    neutral_count += 1
            else:
                # Check for support
                overlap = len(claim_words.intersection(all_words))
                if overlap > 3:  # Good overlap suggests support
                    supporting_count += 1
                else:
                    neutral_count += 1
        
        total_evidence = len(evidence)
        support_ratio = supporting_count / total_evidence if total_evidence > 0 else 0
        contradiction_ratio = contradicting_count / total_evidence if total_evidence > 0 else 0
        
        # Calculate consistency score
        if contradiction_ratio > 0.3:  # High contradiction
            score = max(0.0, 0.3 - contradiction_ratio)
        elif support_ratio > 0.5:  # Good support
            score = min(1.0, 0.7 + support_ratio * 0.3)
        else:  # Mixed or unclear evidence
            score = 0.5
        
        return {
            "score": score,
            "reasoning": f"Found {supporting_count} supporting, {contradicting_count} contradicting, {neutral_count} neutral evidence items",
            "supporting_count": supporting_count,
            "contradicting_count": contradicting_count,
            "neutral_count": neutral_count,
            "support_ratio": support_ratio,
            "contradiction_ratio": contradiction_ratio
        }
    
    async def _calculate_source_credibility(self, evidence: List[SearchResult]) -> float:
        """
        Calculate overall source credibility score.
        
        Args:
            evidence: List of evidence results
            
        Returns:
            Source credibility score (0.0 to 1.0)
        """
        if not evidence:
            return 0.0
        
        # Simple credibility scoring based on domain reputation
        # In production, this would use a comprehensive domain reputation database
        
        high_credibility_domains = {
            'wikipedia.org', 'britannica.com', 'reuters.com', 'ap.org',
            'bbc.com', 'cnn.com', 'nytimes.com', 'washingtonpost.com',
            'nature.com', 'science.org', 'pubmed.ncbi.nlm.nih.gov',
            'gov', 'edu', 'org'
        }
        
        medium_credibility_domains = {
            'com', 'net', 'info'
        }
        
        total_score = 0.0
        for result in evidence:
            domain = result.url.split('/')[2] if '/' in result.url else result.url
            
            if any(hc_domain in domain for hc_domain in high_credibility_domains):
                total_score += 1.0
            elif any(mc_domain in domain for mc_domain in medium_credibility_domains):
                total_score += 0.6
            else:
                total_score += 0.3
        
        return min(1.0, total_score / len(evidence))
    
    async def _generate_analysis(
        self,
        claim: str,
        evidence: List[SearchResult],
        consistency: Dict[str, Any],
        credibility: float
    ) -> str:
        """
        Generate detailed analysis of hallucination assessment.
        
        Args:
            claim: Original claim
            evidence: Evidence results
            consistency: Consistency analysis
            credibility: Source credibility score
            
        Returns:
            Detailed analysis text
        """
        analysis_parts = [
            f"Claim Analysis: '{claim[:100]}{'...' if len(claim) > 100 else ''}'",
            "",
            f"Evidence Summary:",
            f"- Total evidence sources: {len(evidence)}",
            f"- Supporting evidence: {consistency['supporting_count']}",
            f"- Contradicting evidence: {consistency['contradicting_count']}",
            f"- Neutral evidence: {consistency['neutral_count']}",
            "",
            f"Consistency Score: {consistency['score']:.3f}",
            f"Source Credibility: {credibility:.3f}",
            "",
            f"Assessment: {consistency['reasoning']}",
            "",
            f"Risk Level: {self._get_risk_level(consistency['score'])}",
        ]
        
        if evidence:
            analysis_parts.extend([
                "",
                "Top Evidence Sources:",
            ])
            for i, result in enumerate(evidence[:3], 1):
                analysis_parts.append(f"{i}. {result.title} ({result.url})")
        
        return "\n".join(analysis_parts)
    
    def _get_risk_level(self, confidence_score: float) -> str:
        """Get risk level based on confidence score."""
        if confidence_score >= 0.8:
            return "LOW RISK - High confidence in accuracy"
        elif confidence_score >= 0.6:
            return "MEDIUM RISK - Moderate confidence"
        elif confidence_score >= 0.4:
            return "HIGH RISK - Low confidence"
        else:
            return "VERY HIGH RISK - Very low confidence, likely hallucination"
