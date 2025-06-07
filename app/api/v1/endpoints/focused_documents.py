"""
Focused Document Processing API Endpoints

Unified document processing endpoints that handle all supported formats
through the focused document processing pipeline.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from app.services.focused_document_service import FocusedDocumentService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
focused_service = FocusedDocumentService()


class DocumentProcessingRequest(BaseModel):
    """Request model for document processing."""
    
    processing_strategy: str = Field(default="auto", description="Processing strategy")
    quality_threshold: str = Field(default="medium", description="Quality threshold")
    force_ocr: bool = Field(default=False, description="Force OCR processing")
    include_images: bool = Field(default=False, description="Include image extraction")
    include_tables: bool = Field(default=True, description="Include table extraction")
    include_metadata: bool = Field(default=True, description="Include metadata extraction")
    detect_claims: bool = Field(default=True, description="Detect potential claims")
    segmentation_strategy: str = Field(default="paragraph", description="Text segmentation strategy")
    claim_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Claim confidence threshold")
    timeout_seconds: float = Field(default=120.0, ge=1.0, le=600.0, description="Processing timeout")
    bypass_cache: bool = Field(default=False, description="Bypass cache lookup")
    
    @validator('processing_strategy')
    def validate_strategy(cls, v):
        valid_strategies = ["auto", "docling_only", "ocr_only", "hybrid", "url_extraction", "text_analysis"]
        if v.lower() not in valid_strategies:
            raise ValueError(f"Invalid strategy. Must be one of: {valid_strategies}")
        return v.lower()
    
    @validator('quality_threshold')
    def validate_quality(cls, v):
        valid_thresholds = ["low", "medium", "high", "strict"]
        if v.lower() not in valid_thresholds:
            raise ValueError(f"Invalid quality threshold. Must be one of: {valid_thresholds}")
        return v.lower()
    
    @validator('segmentation_strategy')
    def validate_segmentation(cls, v):
        valid_strategies = ["paragraph", "sentence", "semantic", "topic", "claim_based"]
        if v.lower() not in valid_strategies:
            raise ValueError(f"Invalid segmentation strategy. Must be one of: {valid_strategies}")
        return v.lower()


class URLProcessingRequest(BaseModel):
    """Request model for URL processing."""
    
    url: str = Field(..., description="URL to process")
    processing_strategy: str = Field(default="url_extraction", description="Processing strategy")
    quality_threshold: str = Field(default="medium", description="Quality threshold")
    include_metadata: bool = Field(default=True, description="Include metadata extraction")
    detect_claims: bool = Field(default=True, description="Detect potential claims")
    segmentation_strategy: str = Field(default="paragraph", description="Text segmentation strategy")
    claim_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Claim confidence threshold")
    timeout_seconds: float = Field(default=60.0, ge=1.0, le=300.0, description="Processing timeout")
    bypass_cache: bool = Field(default=False, description="Bypass cache lookup")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


class TextProcessingRequest(BaseModel):
    """Request model for text processing."""
    
    text: str = Field(..., description="Text content to process")
    processing_strategy: str = Field(default="text_analysis", description="Processing strategy")
    quality_threshold: str = Field(default="medium", description="Quality threshold")
    detect_claims: bool = Field(default=True, description="Detect potential claims")
    segmentation_strategy: str = Field(default="paragraph", description="Text segmentation strategy")
    claim_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Claim confidence threshold")
    timeout_seconds: float = Field(default=30.0, ge=1.0, le=120.0, description="Processing timeout")
    bypass_cache: bool = Field(default=False, description="Bypass cache lookup")
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text content cannot be empty")
        if len(v) > 1000000:  # 1MB limit for text
            raise ValueError("Text content too large (max 1MB)")
        return v


@router.post("/process-file", response_model=Dict[str, Any])
async def process_file(
    file: UploadFile = File(...),
    processing_strategy: str = Form(default="auto"),
    quality_threshold: str = Form(default="medium"),
    force_ocr: bool = Form(default=False),
    include_images: bool = Form(default=False),
    include_tables: bool = Form(default=True),
    include_metadata: bool = Form(default=True),
    detect_claims: bool = Form(default=True),
    segmentation_strategy: str = Form(default="paragraph"),
    claim_confidence_threshold: float = Form(default=0.5),
    timeout_seconds: float = Form(default=120.0),
    bypass_cache: bool = Form(default=False)
):
    """
    Process uploaded file using the focused document processing pipeline.
    
    Supports: PDF, DOC, DOCX, TXT, and image files.
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Determine document type from filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        file_extension = file.filename.split('.')[-1].lower()
        
        # Map file extensions to document types
        extension_map = {
            'pdf': 'pdf',
            'doc': 'doc',
            'docx': 'docx',
            'txt': 'txt',
            'png': 'image',
            'jpg': 'image',
            'jpeg': 'image',
            'gif': 'image',
            'bmp': 'image',
            'tiff': 'image',
            'webp': 'image'
        }
        
        document_type = extension_map.get(file_extension)
        if not document_type:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}"
            )
        
        # Process document
        result = await focused_service.process_document(
            document_data=file_content,
            document_type=document_type,
            filename=file.filename,
            processing_strategy=processing_strategy,
            quality_threshold=quality_threshold,
            force_ocr=force_ocr,
            include_images=include_images,
            include_tables=include_tables,
            include_metadata=include_metadata,
            detect_claims=detect_claims,
            segmentation_strategy=segmentation_strategy,
            claim_confidence_threshold=claim_confidence_threshold,
            timeout_seconds=timeout_seconds,
            bypass_cache=bypass_cache
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/process-url", response_model=Dict[str, Any])
async def process_url(request: URLProcessingRequest):
    """
    Process URL content using the focused document processing pipeline.
    
    Extracts content from web pages and processes it for fact-checking.
    """
    try:
        result = await focused_service.process_url(
            url=request.url,
            processing_strategy=request.processing_strategy,
            quality_threshold=request.quality_threshold,
            include_metadata=request.include_metadata,
            detect_claims=request.detect_claims,
            segmentation_strategy=request.segmentation_strategy,
            claim_confidence_threshold=request.claim_confidence_threshold,
            timeout_seconds=request.timeout_seconds,
            bypass_cache=request.bypass_cache
        )
        
        return result
        
    except Exception as e:
        logger.error(f"URL processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"URL processing failed: {str(e)}")


@router.post("/process-text", response_model=Dict[str, Any])
async def process_text(request: TextProcessingRequest):
    """
    Process text content using the focused document processing pipeline.
    
    Analyzes text for structure, claims, and other fact-checking relevant information.
    """
    try:
        result = await focused_service.process_text(
            text=request.text,
            processing_strategy=request.processing_strategy,
            quality_threshold=request.quality_threshold,
            detect_claims=request.detect_claims,
            segmentation_strategy=request.segmentation_strategy,
            claim_confidence_threshold=request.claim_confidence_threshold,
            timeout_seconds=request.timeout_seconds,
            bypass_cache=request.bypass_cache
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Text processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Text processing failed: {str(e)}")


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_capabilities():
    """
    Get information about the focused document processing capabilities.
    
    Returns supported formats, strategies, and current system status.
    """
    try:
        capabilities = await focused_service.get_processing_capabilities()
        return capabilities
        
    except Exception as e:
        logger.error(f"Failed to get capabilities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


@router.post("/process-url-form", response_model=Dict[str, Any])
async def process_url_form(
    url: str = Form(...),
    processing_strategy: str = Form(default="url_extraction"),
    quality_threshold: str = Form(default="medium"),
    include_metadata: bool = Form(default=True),
    detect_claims: bool = Form(default=True),
    segmentation_strategy: str = Form(default="paragraph"),
    claim_confidence_threshold: float = Form(default=0.5),
    timeout_seconds: float = Form(default=60.0),
    bypass_cache: bool = Form(default=False)
):
    """
    Process URL using form data (alternative to JSON endpoint).
    """
    try:
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
        
        result = await focused_service.process_url(
            url=url,
            processing_strategy=processing_strategy,
            quality_threshold=quality_threshold,
            include_metadata=include_metadata,
            detect_claims=detect_claims,
            segmentation_strategy=segmentation_strategy,
            claim_confidence_threshold=claim_confidence_threshold,
            timeout_seconds=timeout_seconds,
            bypass_cache=bypass_cache
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL form processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"URL processing failed: {str(e)}")


@router.post("/process-text-form", response_model=Dict[str, Any])
async def process_text_form(
    text: str = Form(...),
    processing_strategy: str = Form(default="text_analysis"),
    quality_threshold: str = Form(default="medium"),
    detect_claims: bool = Form(default=True),
    segmentation_strategy: str = Form(default="paragraph"),
    claim_confidence_threshold: float = Form(default=0.5),
    timeout_seconds: float = Form(default=30.0),
    bypass_cache: bool = Form(default=False)
):
    """
    Process text using form data (alternative to JSON endpoint).
    """
    try:
        # Validate text
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text content cannot be empty")
        if len(text) > 1000000:  # 1MB limit
            raise HTTPException(status_code=400, detail="Text content too large (max 1MB)")
        
        result = await focused_service.process_text(
            text=text,
            processing_strategy=processing_strategy,
            quality_threshold=quality_threshold,
            detect_claims=detect_claims,
            segmentation_strategy=segmentation_strategy,
            claim_confidence_threshold=claim_confidence_threshold,
            timeout_seconds=timeout_seconds,
            bypass_cache=bypass_cache
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text form processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Text processing failed: {str(e)}")
