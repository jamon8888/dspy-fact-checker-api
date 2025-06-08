"""
Data models for the search module.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import time


class SearchType(str, Enum):
    """Types of search operations."""
    NEURAL = "neural"
    KEYWORD = "keyword"
    SIMILARITY = "similarity"
    WEB = "web"


class SearchQuery(BaseModel):
    """Search query model."""
    query: str = Field(..., description="Search query text")
    max_results: int = Field(10, description="Maximum number of results", ge=1, le=50)
    search_type: SearchType = Field(SearchType.NEURAL, description="Type of search")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    use_autoprompt: bool = Field(True, description="Use Exa.ai autoprompt")
    include_domains: Optional[List[str]] = Field(None, description="Domains to include")
    exclude_domains: Optional[List[str]] = Field(None, description="Domains to exclude")
    start_published_date: Optional[str] = Field(None, description="Start date filter")
    end_published_date: Optional[str] = Field(None, description="End date filter")


class SearchResult(BaseModel):
    """Search result model."""
    title: str = Field(..., description="Result title")
    url: str = Field(..., description="Result URL")
    content: str = Field(..., description="Result content")
    score: float = Field(..., description="Relevance score", ge=0.0, le=1.0)
    source: str = Field(..., description="Search provider")
    published_date: Optional[str] = Field(None, description="Publication date")
    highlights: List[str] = Field(default_factory=list, description="Content highlights")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            # Custom encoders if needed
        }


class DualSearchResult(BaseModel):
    """Result from dual search operation."""
    query: str = Field(..., description="Original search query")
    exa_results: List[SearchResult] = Field(default_factory=list, description="Exa.ai results")
    tavily_results: List[SearchResult] = Field(default_factory=list, description="Tavily results")
    aggregated_results: List[SearchResult] = Field(default_factory=list, description="Combined results")
    search_strategy: str = Field(..., description="Search strategy used")
    processing_time: float = Field(..., description="Total processing time")
    exa_success: bool = Field(True, description="Exa.ai search success")
    tavily_success: bool = Field(True, description="Tavily search success")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Search metadata")
    
    @property
    def total_results(self) -> int:
        """Total number of aggregated results."""
        return len(self.aggregated_results)
    
    @property
    def success_rate(self) -> float:
        """Success rate of search providers."""
        successes = sum([self.exa_success, self.tavily_success])
        return successes / 2.0


class HallucinationResult(BaseModel):
    """Result from hallucination detection."""
    claim: str = Field(..., description="Original claim")
    is_hallucination: bool = Field(..., description="Whether claim is hallucination")
    confidence_score: float = Field(..., description="Confidence in assessment", ge=0.0, le=1.0)
    evidence: List[SearchResult] = Field(default_factory=list, description="Supporting evidence")
    key_facts: List[str] = Field(default_factory=list, description="Extracted key facts")
    analysis: str = Field(..., description="Detailed analysis")
    processing_time: float = Field(..., description="Processing time")
    evidence_consistency: float = Field(..., description="Evidence consistency score", ge=0.0, le=1.0)
    source_credibility: float = Field(..., description="Source credibility score", ge=0.0, le=1.0)
    
    @property
    def risk_level(self) -> str:
        """Risk level based on confidence score."""
        if self.confidence_score >= 0.9:
            return "HIGH" if self.is_hallucination else "LOW"
        elif self.confidence_score >= 0.7:
            return "MEDIUM"
        else:
            return "UNCERTAIN"


class SearchProviderStatus(BaseModel):
    """Status of a search provider."""
    provider_name: str = Field(..., description="Provider name")
    is_healthy: bool = Field(..., description="Provider health status")
    response_time: float = Field(..., description="Average response time")
    success_rate: float = Field(..., description="Success rate", ge=0.0, le=1.0)
    last_check: float = Field(default_factory=time.time, description="Last health check")
    error_message: Optional[str] = Field(None, description="Last error message")


class SearchMetrics(BaseModel):
    """Search operation metrics."""
    total_searches: int = Field(0, description="Total searches performed")
    successful_searches: int = Field(0, description="Successful searches")
    failed_searches: int = Field(0, description="Failed searches")
    average_response_time: float = Field(0.0, description="Average response time")
    cache_hits: int = Field(0, description="Cache hits")
    cache_misses: int = Field(0, description="Cache misses")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_searches == 0:
            return 0.0
        return self.successful_searches / self.total_searches
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return self.cache_hits / total_cache_requests


class EnhancedFactCheckResult(BaseModel):
    """Enhanced fact-checking result with dual search and hallucination detection."""
    claim: str = Field(..., description="Original claim")
    verdict: str = Field(..., description="Fact-check verdict")
    confidence: float = Field(..., description="Overall confidence", ge=0.0, le=1.0)
    hallucination_analysis: HallucinationResult = Field(..., description="Hallucination analysis")
    search_results: DualSearchResult = Field(..., description="Search results")
    evidence_summary: str = Field(..., description="Evidence summary")
    sources_used: List[str] = Field(default_factory=list, description="Search providers used")
    processing_time: float = Field(..., description="Total processing time")
    accuracy_score: float = Field(..., description="Accuracy score", ge=0.0, le=1.0)
    
    @property
    def is_reliable(self) -> bool:
        """Whether the result is considered reliable."""
        return (
            self.confidence >= 0.7 and
            self.hallucination_analysis.confidence_score >= 0.7 and
            self.search_results.success_rate >= 0.5
        )
