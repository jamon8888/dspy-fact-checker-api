"""
Content Extraction API Endpoints

API endpoints for URL content extraction and text processing.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Form, Body
from pydantic import BaseModel, HttpUrl, Field, validator

from app.services.content_extraction_service import ContentExtractionService
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get content extraction service
def get_content_extraction_service() -> ContentExtractionService:
    return ContentExtractionService()


# Request/Response Models
class URLExtractionRequest(BaseModel):
    """Request model for URL content extraction."""
    url: HttpUrl = Field(..., description="URL to extract content from")
    extraction_strategy: str = Field(default="auto", description="Extraction strategy")
    timeout_seconds: float = Field(default=30.0, ge=1.0, le=300.0, description="Timeout in seconds")
    quality_threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Quality threshold")
    include_metadata: bool = Field(default=True, description="Include metadata in response")
    include_images: bool = Field(default=False, description="Include image URLs")
    
    @validator('extraction_strategy')
    def validate_strategy(cls, v):
        valid_strategies = ['auto', 'newspaper', 'readability', 'trafilatura', 'custom']
        if v not in valid_strategies:
            raise ValueError(f"Strategy must be one of: {valid_strategies}")
        return v


class TextProcessingRequest(BaseModel):
    """Request model for text processing."""
    text: str = Field(..., min_length=10, max_length=1000000, description="Text to process")
    segmentation_strategy: str = Field(default="paragraph", description="Segmentation strategy")
    detect_language: bool = Field(default=True, description="Detect text language")
    detect_claims: bool = Field(default=True, description="Detect potential claims")
    analyze_structure: bool = Field(default=True, description="Analyze text structure")
    claim_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Claim confidence threshold")
    min_segment_length: int = Field(default=50, ge=10, description="Minimum segment length")
    max_segment_length: int = Field(default=5000, ge=100, description="Maximum segment length")
    
    @validator('segmentation_strategy')
    def validate_segmentation(cls, v):
        valid_strategies = ['paragraph', 'sentence', 'semantic', 'topic', 'claim_based']
        if v not in valid_strategies:
            raise ValueError(f"Segmentation strategy must be one of: {valid_strategies}")
        return v


class KeyInformationRequest(BaseModel):
    """Request model for key information extraction."""
    text: str = Field(..., min_length=10, max_length=1000000, description="Text to analyze")


class ContentExtractionResponse(BaseModel):
    """Response model for content extraction operations."""
    success: bool
    operation_id: Optional[str] = None
    processing_time: float
    processed_at: str
    error: Optional[str] = None
    error_type: Optional[str] = None


@router.post("/extract-url", response_model=Dict[str, Any])
async def extract_url_content(
    request: URLExtractionRequest,
    service: ContentExtractionService = Depends(get_content_extraction_service)
):
    """
    Extract content from a URL using multiple extraction strategies.
    
    This endpoint supports various extraction strategies:
    - **auto**: Automatically select the best strategy based on content type
    - **newspaper**: Use newspaper3k for news articles
    - **readability**: Use readability-lxml for general content
    - **trafilatura**: Use trafilatura for blog posts and articles
    - **custom**: Use custom BeautifulSoup-based extraction
    
    Features:
    - Quality assessment and fallback strategies
    - Language detection
    - Content type classification
    - Metadata extraction
    - Caching for performance
    """
    try:
        result = await service.extract_url_content(
            url=str(request.url),
            extraction_strategy=request.extraction_strategy,
            timeout_seconds=request.timeout_seconds,
            quality_threshold=request.quality_threshold,
            include_metadata=request.include_metadata,
            include_images=request.include_images
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": result.get("error", "URL extraction failed"),
                    "error_type": result.get("error_type", "ExtractionError"),
                    "url": str(request.url)
                }
            )
    
    except Exception as e:
        logger.error(f"URL extraction endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during URL extraction",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.post("/process-text", response_model=Dict[str, Any])
async def process_text_content(
    request: TextProcessingRequest,
    service: ContentExtractionService = Depends(get_content_extraction_service)
):
    """
    Process text content with comprehensive analysis.
    
    This endpoint provides advanced text processing capabilities:
    - **Text segmentation**: Multiple strategies for breaking text into segments
    - **Language detection**: Automatic language identification
    - **Claim detection**: Identify potential factual claims
    - **Structure analysis**: Analyze document structure and complexity
    - **Content cleaning**: Remove boilerplate and normalize text
    
    Segmentation strategies:
    - **paragraph**: Segment by paragraphs
    - **sentence**: Group sentences into segments
    - **semantic**: Segment by semantic coherence (advanced)
    - **topic**: Segment by topic boundaries (advanced)
    - **claim_based**: Segment around factual claims
    """
    try:
        result = await service.process_text_content(
            text=request.text,
            segmentation_strategy=request.segmentation_strategy,
            detect_language=request.detect_language,
            detect_claims=request.detect_claims,
            analyze_structure=request.analyze_structure,
            claim_confidence_threshold=request.claim_confidence_threshold,
            min_segment_length=request.min_segment_length,
            max_segment_length=request.max_segment_length
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": result.get("error", "Text processing failed"),
                    "error_type": result.get("error_type", "ProcessingError")
                }
            )
    
    except Exception as e:
        logger.error(f"Text processing endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during text processing",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.post("/extract-key-info", response_model=Dict[str, Any])
async def extract_key_information(
    request: KeyInformationRequest,
    service: ContentExtractionService = Depends(get_content_extraction_service)
):
    """
    Extract key information from text for fact-checking.
    
    This endpoint analyzes text to extract:
    - **High-confidence factual claims**
    - **Key entities and keywords**
    - **Language and complexity metrics**
    - **Structured information for fact-checking**
    
    Optimized for fact-checking workflows by focusing on:
    - Claims with high confidence scores
    - Factual statements that can be verified
    - Named entities and important keywords
    - Content structure and readability
    """
    try:
        result = await service.extract_key_information(request.text)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": result.get("error", "Key information extraction failed"),
                    "error_type": result.get("error_type", "ExtractionError")
                }
            )
    
    except Exception as e:
        logger.error(f"Key information extraction endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during key information extraction",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_extraction_capabilities(
    service: ContentExtractionService = Depends(get_content_extraction_service)
):
    """
    Get information about content extraction capabilities.
    
    Returns detailed information about:
    - Available URL extraction strategies
    - Supported content types
    - Text processing capabilities
    - Language support
    - Performance characteristics
    """
    try:
        capabilities = await service.get_extraction_capabilities()
        return {
            "success": True,
            "capabilities": capabilities,
            "service_info": {
                "name": "Content Extraction Service",
                "version": "1.0.0",
                "description": "Advanced URL content extraction and text processing for fact-checking"
            }
        }
    
    except Exception as e:
        logger.error(f"Capabilities endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error retrieving capabilities",
                "error_code": "INTERNAL_ERROR"
            }
        )


# Form-based endpoints for easier testing
@router.post("/extract-url-form")
async def extract_url_content_form(
    url: str = Form(..., description="URL to extract content from"),
    extraction_strategy: str = Form("auto", description="Extraction strategy"),
    timeout_seconds: float = Form(30.0, description="Timeout in seconds"),
    quality_threshold: float = Form(0.3, description="Quality threshold"),
    include_metadata: bool = Form(True, description="Include metadata"),
    include_images: bool = Form(False, description="Include images"),
    service: ContentExtractionService = Depends(get_content_extraction_service)
):
    """Form-based URL content extraction for easy testing."""
    request = URLExtractionRequest(
        url=url,
        extraction_strategy=extraction_strategy,
        timeout_seconds=timeout_seconds,
        quality_threshold=quality_threshold,
        include_metadata=include_metadata,
        include_images=include_images
    )
    return await extract_url_content(request, service)


@router.post("/process-text-form")
async def process_text_content_form(
    text: str = Form(..., description="Text to process"),
    segmentation_strategy: str = Form("paragraph", description="Segmentation strategy"),
    detect_language: bool = Form(True, description="Detect language"),
    detect_claims: bool = Form(True, description="Detect claims"),
    analyze_structure: bool = Form(True, description="Analyze structure"),
    claim_confidence_threshold: float = Form(0.5, description="Claim confidence threshold"),
    service: ContentExtractionService = Depends(get_content_extraction_service)
):
    """Form-based text processing for easy testing."""
    request = TextProcessingRequest(
        text=text,
        segmentation_strategy=segmentation_strategy,
        detect_language=detect_language,
        detect_claims=detect_claims,
        analyze_structure=analyze_structure,
        claim_confidence_threshold=claim_confidence_threshold
    )
    return await process_text_content(request, service)
