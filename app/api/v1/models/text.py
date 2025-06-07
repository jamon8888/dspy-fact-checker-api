"""
Text processing Pydantic models for the DSPy-Enhanced Fact-Checker API Platform.
"""

from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from .base import BaseResponse, ProcessingStatus, Priority, TimestampMixin


class OptimizationLevel(str, Enum):
    """Text processing optimization levels."""
    
    FAST = "fast"
    STANDARD = "standard"
    THOROUGH = "thorough"


class TextProcessingRequest(BaseModel):
    """Text processing request model."""
    
    text: str = Field(
        ..., 
        min_length=1, 
        max_length=50000, 
        description="Text content to fact-check"
    )
    context: Optional[str] = Field(
        None, 
        max_length=5000, 
        description="Additional context for fact-checking"
    )
    optimization_level: OptimizationLevel = Field(
        default=OptimizationLevel.STANDARD,
        description="Processing optimization level"
    )
    confidence_threshold: float = Field(
        default=0.7, 
        ge=0.0, 
        le=1.0, 
        description="Minimum confidence threshold"
    )
    priority: Priority = Field(default=Priority.NORMAL, description="Processing priority")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook URL for completion notification")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('text')
    def validate_text_content(cls, v):
        """Validate text content."""
        if not v.strip():
            raise ValueError("Text content cannot be empty or only whitespace")
        return v.strip()


class TextSegment(BaseModel):
    """Text segment model."""
    
    id: str = Field(..., description="Segment identifier")
    text: str = Field(..., description="Segment text")
    start_position: int = Field(..., description="Start position in original text")
    end_position: int = Field(..., description="End position in original text")
    segment_type: str = Field(..., description="Type of segment (paragraph, sentence, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Segmentation confidence")


class ClaimResult(BaseModel):
    """Individual claim verification result."""
    
    claim: str = Field(..., description="The factual claim")
    verdict: str = Field(
        ..., 
        pattern="^(SUPPORTED|REFUTED|INSUFFICIENT_EVIDENCE|CONFLICTING)$",
        description="Verification verdict"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in verification")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    sources: List[str] = Field(default_factory=list, description="Evidence sources")
    context: Optional[str] = Field(None, description="Claim context")
    segment_id: Optional[str] = Field(None, description="Source segment identifier")
    uncertainty_factors: List[str] = Field(default_factory=list, description="Factors contributing to uncertainty")


class TextAnalysis(BaseModel):
    """Text analysis results."""
    
    language: str = Field(..., description="Detected language")
    word_count: int = Field(..., description="Word count")
    character_count: int = Field(..., description="Character count")
    sentence_count: int = Field(..., description="Sentence count")
    paragraph_count: int = Field(..., description="Paragraph count")
    reading_time: float = Field(..., description="Estimated reading time in minutes")
    complexity_score: float = Field(..., ge=0.0, le=1.0, description="Text complexity score")
    topics: List[str] = Field(default_factory=list, description="Identified topics")
    sentiment: Optional[str] = Field(None, description="Overall sentiment")


class TextProcessingResponse(BaseResponse):
    """Text processing response model."""
    
    request_id: str = Field(..., description="Unique request identifier")
    text_analysis: TextAnalysis = Field(..., description="Text analysis results")
    segments: List[TextSegment] = Field(..., description="Text segments")
    claims: List[ClaimResult] = Field(..., description="Verified claims")
    overall_verdict: str = Field(
        ...,
        pattern="^(MOSTLY_ACCURATE|MIXED|MOSTLY_INACCURATE|INSUFFICIENT_INFO)$",
        description="Overall verdict"
    )
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    processing_time: float = Field(..., description="Processing time in seconds")
    claims_analyzed: int = Field(..., description="Number of claims analyzed")
    optimization_level: OptimizationLevel = Field(..., description="Optimization level used")


class TextProcessingStatus(BaseModel, TimestampMixin):
    """Text processing status model."""
    
    request_id: str = Field(..., description="Request identifier")
    status: ProcessingStatus = Field(..., description="Current processing status")
    progress: float = Field(..., ge=0.0, le=100.0, description="Processing progress percentage")
    current_stage: Optional[str] = Field(None, description="Current processing stage")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated completion time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    processing_time: Optional[float] = Field(None, description="Total processing time in seconds")


class BatchTextRequest(BaseModel):
    """Batch text processing request."""
    
    texts: List[TextProcessingRequest] = Field(
        ..., 
        min_items=1, 
        max_items=20, 
        description="List of texts to process"
    )
    batch_optimization_level: OptimizationLevel = Field(
        default=OptimizationLevel.STANDARD,
        description="Batch optimization level"
    )
    priority: Priority = Field(default=Priority.NORMAL, description="Batch processing priority")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook URL for batch completion")


class BatchTextResponse(BaseResponse):
    """Batch text processing response."""
    
    batch_id: str = Field(..., description="Unique batch identifier")
    texts_accepted: int = Field(..., description="Number of texts accepted for processing")
    request_ids: List[Dict[str, Any]] = Field(..., description="Individual request IDs")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated batch completion time")
    estimated_total_cost: Optional[float] = Field(None, description="Estimated total processing cost")


class TextComparisonRequest(BaseModel):
    """Text comparison request model."""
    
    text1: str = Field(..., min_length=1, max_length=25000, description="First text to compare")
    text2: str = Field(..., min_length=1, max_length=25000, description="Second text to compare")
    comparison_type: str = Field(
        default="factual",
        pattern="^(factual|semantic|stylistic|all)$",
        description="Type of comparison to perform"
    )
    confidence_threshold: float = Field(
        default=0.7, 
        ge=0.0, 
        le=1.0, 
        description="Minimum confidence threshold"
    )


class TextComparisonResult(BaseModel):
    """Text comparison result model."""
    
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Overall similarity score")
    factual_consistency: float = Field(..., ge=0.0, le=1.0, description="Factual consistency score")
    semantic_similarity: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity score")
    differences: List[Dict[str, Any]] = Field(..., description="Identified differences")
    common_claims: List[str] = Field(..., description="Common factual claims")
    conflicting_claims: List[Dict[str, Any]] = Field(..., description="Conflicting claims")
    analysis_summary: str = Field(..., description="Summary of comparison analysis")


class TextComparisonResponse(BaseResponse):
    """Text comparison response model."""
    
    request_id: str = Field(..., description="Unique request identifier")
    comparison_result: TextComparisonResult = Field(..., description="Comparison results")
    processing_time: float = Field(..., description="Processing time in seconds")


class TextSummaryRequest(BaseModel):
    """Text summarization request model."""
    
    text: str = Field(..., min_length=100, max_length=50000, description="Text to summarize")
    summary_length: str = Field(
        default="medium",
        pattern="^(short|medium|long)$",
        description="Desired summary length"
    )
    focus_areas: List[str] = Field(
        default_factory=list,
        description="Specific areas to focus on in summary"
    )
    include_fact_check: bool = Field(
        default=True,
        description="Include fact-checking in summary"
    )


class TextSummaryResponse(BaseResponse):
    """Text summarization response model."""
    
    request_id: str = Field(..., description="Unique request identifier")
    summary: str = Field(..., description="Generated summary")
    key_points: List[str] = Field(..., description="Key points extracted")
    fact_check_summary: Optional[str] = Field(None, description="Fact-checking summary")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Summary confidence score")
    compression_ratio: float = Field(..., description="Text compression ratio")
    processing_time: float = Field(..., description="Processing time in seconds")
