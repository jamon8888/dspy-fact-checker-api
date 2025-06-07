"""
URL processing Pydantic models for the DSPy-Enhanced Fact-Checker API Platform.
"""

from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from .base import BaseResponse, ProcessingStatus, Priority, TimestampMixin


class ContentType(str, Enum):
    """Supported web content types."""
    
    NEWS_ARTICLE = "news_article"
    BLOG_POST = "blog_post"
    ACADEMIC_PAPER = "academic_paper"
    WIKIPEDIA = "wikipedia"
    SOCIAL_MEDIA = "social_media"
    GOVERNMENT_DOCUMENT = "government_document"
    FORUM_POST = "forum_post"
    UNKNOWN = "unknown"


class ExtractionMethod(str, Enum):
    """Content extraction methods."""
    
    NEWSPAPER = "newspaper"
    READABILITY = "readability"
    TRAFILATURA = "trafilatura"
    CUSTOM = "custom"
    HYBRID = "hybrid"


class URLProcessingRequest(BaseModel):
    """URL processing request model."""
    
    url: HttpUrl = Field(..., description="URL to process for fact-checking")
    extract_links: bool = Field(default=False, description="Extract and process linked content")
    follow_redirects: bool = Field(default=True, description="Follow URL redirects")
    confidence_threshold: float = Field(
        default=0.7, 
        ge=0.0, 
        le=1.0, 
        description="Minimum confidence threshold"
    )
    priority: Priority = Field(default=Priority.NORMAL, description="Processing priority")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook URL for completion notification")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format and accessibility."""
        url_str = str(v)
        
        # Basic validation
        if not url_str.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        
        # Check for common invalid patterns
        invalid_patterns = ['localhost', '127.0.0.1', '0.0.0.0']
        if any(pattern in url_str.lower() for pattern in invalid_patterns):
            raise ValueError("Local URLs are not allowed")
        
        return v


class URLAnalysis(BaseModel):
    """URL analysis results."""
    
    final_url: str = Field(..., description="Final URL after redirects")
    domain: str = Field(..., description="Domain name")
    is_accessible: bool = Field(..., description="Whether URL is accessible")
    response_code: int = Field(..., description="HTTP response code")
    content_type: ContentType = Field(..., description="Detected content type")
    estimated_processing_time: int = Field(..., description="Estimated processing time in seconds")
    security_check: Dict[str, Any] = Field(..., description="Security analysis results")
    credibility_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Source credibility score")


class ExtractedWebContent(BaseModel):
    """Extracted web content model."""
    
    title: Optional[str] = Field(None, description="Page title")
    author: Optional[str] = Field(None, description="Content author")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    content: str = Field(..., description="Extracted text content")
    summary: Optional[str] = Field(None, description="Content summary")
    tags: List[str] = Field(default_factory=list, description="Content tags")
    images: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted images")
    links: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted links")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    extraction_method: ExtractionMethod = Field(..., description="Extraction method used")
    extraction_confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")


class SourceAnalysis(BaseModel):
    """Source credibility analysis."""
    
    credibility_score: float = Field(..., ge=0.0, le=1.0, description="Overall credibility score")
    bias_rating: Optional[str] = Field(None, description="Bias rating")
    factual_reporting: Optional[str] = Field(None, description="Factual reporting rating")
    domain_age: Optional[str] = Field(None, description="Domain age")
    alexa_rank: Optional[int] = Field(None, description="Alexa ranking")
    social_media_presence: Optional[str] = Field(None, description="Social media presence")
    fact_check_history: Dict[str, Any] = Field(default_factory=dict, description="Historical fact-checking data")
    recommendation: str = Field(..., description="Source reliability recommendation")


class URLClaimResult(BaseModel):
    """URL-specific claim verification result."""
    
    claim: str = Field(..., description="The factual claim")
    verdict: str = Field(
        ..., 
        pattern="^(SUPPORTED|REFUTED|INSUFFICIENT_EVIDENCE|CONFLICTING)$",
        description="Verification verdict"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in verification")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    sources: List[str] = Field(default_factory=list, description="Evidence sources")
    context: Optional[str] = Field(None, description="Claim context from content")
    cross_references: List[str] = Field(default_factory=list, description="Cross-reference URLs")


class URLProcessingResponse(BaseResponse):
    """URL processing response model."""
    
    processing_id: str = Field(..., description="Unique processing identifier")
    url: str = Field(..., description="Original URL")
    url_analysis: URLAnalysis = Field(..., description="URL analysis results")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated completion time in seconds")


class URLFactCheckResult(BaseModel):
    """Complete URL fact-checking result."""
    
    processing_id: str = Field(..., description="Processing identifier")
    url: str = Field(..., description="Original URL")
    extracted_content: ExtractedWebContent = Field(..., description="Extracted content")
    source_analysis: SourceAnalysis = Field(..., description="Source credibility analysis")
    claims: List[URLClaimResult] = Field(..., description="Verified claims")
    overall_verdict: str = Field(
        ...,
        pattern="^(MOSTLY_ACCURATE|MIXED|MOSTLY_INACCURATE|INSUFFICIENT_INFO)$",
        description="Overall content verdict"
    )
    accuracy_score: float = Field(..., ge=0.0, le=1.0, description="Overall accuracy score")
    processing_stats: Dict[str, Any] = Field(..., description="Processing statistics")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for readers")


class URLProcessingStatus(BaseModel, TimestampMixin):
    """URL processing status model."""
    
    processing_id: str = Field(..., description="Processing identifier")
    status: ProcessingStatus = Field(..., description="Current processing status")
    progress: float = Field(..., ge=0.0, le=100.0, description="Processing progress percentage")
    current_stage: Optional[str] = Field(None, description="Current processing stage")
    content_extracted: bool = Field(default=False, description="Whether content has been extracted")
    claims_detected: int = Field(default=0, description="Number of claims detected")
    verification_complete: bool = Field(default=False, description="Whether verification is complete")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated completion time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    processing_time: Optional[float] = Field(None, description="Total processing time in seconds")


class BatchURLRequest(BaseModel):
    """Batch URL processing request."""
    
    urls: List[URLProcessingRequest] = Field(
        ..., 
        min_items=1, 
        max_items=10, 
        description="List of URLs to process"
    )
    batch_priority: Priority = Field(default=Priority.NORMAL, description="Batch processing priority")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook URL for batch completion")


class BatchURLResponse(BaseResponse):
    """Batch URL processing response."""
    
    batch_id: str = Field(..., description="Unique batch identifier")
    urls_accepted: int = Field(..., description="Number of URLs accepted for processing")
    processing_ids: List[Dict[str, Any]] = Field(..., description="Individual processing IDs")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated batch completion time")


class DomainAnalysisRequest(BaseModel):
    """Domain analysis request model."""
    
    domain: str = Field(..., description="Domain to analyze")
    include_subdomains: bool = Field(default=False, description="Include subdomain analysis")
    
    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain format."""
        # Remove protocol if present
        domain = v.lower().replace('http://', '').replace('https://', '')
        
        # Remove path if present
        domain = domain.split('/')[0]
        
        # Basic domain validation
        if not domain or '.' not in domain:
            raise ValueError("Invalid domain format")
        
        return domain


class DomainAnalysisResponse(BaseResponse):
    """Domain analysis response model."""
    
    domain: str = Field(..., description="Analyzed domain")
    credibility_score: float = Field(..., ge=0.0, le=1.0, description="Domain credibility score")
    bias_rating: Optional[str] = Field(None, description="Political bias rating")
    factual_reporting: Optional[str] = Field(None, description="Factual reporting quality")
    domain_info: Dict[str, Any] = Field(..., description="Domain information")
    fact_check_history: Dict[str, Any] = Field(..., description="Historical fact-checking data")
    recommendation: str = Field(..., description="Overall recommendation")
    analysis_date: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")


class URLSearchRequest(BaseModel):
    """URL search request model."""
    
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    domain_filter: Optional[str] = Field(None, description="Filter by domain")
    content_type_filter: Optional[ContentType] = Field(None, description="Filter by content type")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="Date range filter")
    credibility_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum credibility score")
    pagination: Optional[Dict[str, int]] = Field(None, description="Pagination parameters")


class URLSearchResult(BaseModel):
    """URL search result model."""
    
    processing_id: str = Field(..., description="Processing identifier")
    url: str = Field(..., description="Original URL")
    title: Optional[str] = Field(None, description="Content title")
    snippet: Optional[str] = Field(None, description="Content snippet")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Search relevance score")
    credibility_score: float = Field(..., ge=0.0, le=1.0, description="Source credibility score")
    content_type: ContentType = Field(..., description="Content type")
    processing_date: datetime = Field(..., description="Processing date")


class URLSearchResponse(BaseResponse):
    """URL search response model."""
    
    query: str = Field(..., description="Original search query")
    results: List[URLSearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    search_time: float = Field(..., description="Search execution time in seconds")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")
