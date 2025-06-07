"""
Content Extraction Data Models

Pydantic models for content extraction and text processing operations.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator
from enum import Enum


class ExtractionStrategy(str, Enum):
    """Available content extraction strategies."""
    NEWSPAPER = "newspaper"
    READABILITY = "readability"
    TRAFILATURA = "trafilatura"
    CUSTOM = "custom"
    AUTO = "auto"


class ContentType(str, Enum):
    """Detected content types."""
    NEWS_ARTICLE = "news_article"
    BLOG_POST = "blog_post"
    ACADEMIC_PAPER = "academic_paper"
    WIKIPEDIA = "wikipedia"
    SOCIAL_MEDIA = "social_media"
    FORUM_POST = "forum_post"
    PRODUCT_PAGE = "product_page"
    DOCUMENTATION = "documentation"
    GENERAL = "general"


class SegmentationStrategy(str, Enum):
    """Text segmentation strategies."""
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"
    SEMANTIC = "semantic"
    TOPIC = "topic"
    CLAIM_BASED = "claim_based"


class ExtractionOptions(BaseModel):
    """Options for URL content extraction."""
    
    strategy: ExtractionStrategy = ExtractionStrategy.AUTO
    timeout_seconds: float = Field(default=30.0, ge=1.0, le=300.0)
    max_content_length: int = Field(default=1000000, ge=1000)
    include_metadata: bool = True
    include_images: bool = False
    include_links: bool = False
    quality_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    user_agent: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    follow_redirects: bool = True
    verify_ssl: bool = True


class TextProcessingOptions(BaseModel):
    """Options for text processing."""
    
    segmentation_strategy: SegmentationStrategy = SegmentationStrategy.PARAGRAPH
    detect_language: bool = True
    detect_claims: bool = True
    analyze_structure: bool = True
    min_segment_length: int = Field(default=50, ge=10)
    max_segment_length: int = Field(default=5000, ge=100)
    claim_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    include_statistics: bool = True


class LanguageInfo(BaseModel):
    """Language detection information."""
    
    language: str = Field(..., description="ISO 639-1 language code")
    confidence: float = Field(..., ge=0.0, le=1.0)
    detected_languages: List[Dict[str, float]] = Field(default_factory=list)


class URLAnalysis(BaseModel):
    """URL analysis results."""
    
    url: str
    domain: str
    content_type: ContentType
    is_news_site: bool = False
    is_academic: bool = False
    is_social_media: bool = False
    trust_score: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContentStructure(BaseModel):
    """Content structure analysis."""
    
    has_title: bool = False
    has_headings: bool = False
    has_paragraphs: bool = False
    has_lists: bool = False
    has_tables: bool = False
    heading_count: int = 0
    paragraph_count: int = 0
    list_count: int = 0
    table_count: int = 0
    estimated_reading_time: float = 0.0
    complexity_score: float = Field(default=0.5, ge=0.0, le=1.0)


class TextSegment(BaseModel):
    """A segment of processed text."""
    
    text: str
    start_position: int
    end_position: int
    segment_type: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PotentialClaim(BaseModel):
    """A potential factual claim detected in text."""
    
    text: str
    start_position: int
    end_position: int
    confidence: float = Field(..., ge=0.0, le=1.0)
    claim_type: str = "factual"
    context: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)


class ExtractedWebContent(BaseModel):
    """Extracted web content with metadata."""
    
    url: str
    title: Optional[str] = None
    content: str
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    extraction_method: ExtractionStrategy
    content_type: ContentType
    quality_score: float = Field(..., ge=0.0, le=1.0)
    language: Optional[LanguageInfo] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    images: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    processing_time: float = 0.0


class ProcessedTextContent(BaseModel):
    """Processed text content with analysis."""
    
    original_text: str
    cleaned_text: str
    language: Optional[LanguageInfo] = None
    structure: ContentStructure
    segments: List[TextSegment] = Field(default_factory=list)
    potential_claims: List[PotentialClaim] = Field(default_factory=list)
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_timestamp: datetime = Field(default_factory=datetime.now)
    processing_time: float = 0.0
    
    @validator('segments')
    def validate_segments(cls, v):
        """Ensure segments are properly ordered."""
        if len(v) > 1:
            for i in range(1, len(v)):
                if v[i].start_position < v[i-1].end_position:
                    raise ValueError("Segments must be non-overlapping and ordered")
        return v
