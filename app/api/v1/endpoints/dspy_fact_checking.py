"""
DSPy Fact-Checking API Endpoints

API endpoints for document-aware fact-checking using DSPy modules.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from app.services.dspy_fact_checking_service import DSPyFactCheckingService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
dspy_service = DSPyFactCheckingService()


class FactCheckRequest(BaseModel):
    """Request model for document fact-checking."""
    
    document_content: str = Field(..., description="Document content to fact-check")
    document_metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    document_type: str = Field(default="general", description="Type of document")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence threshold")
    max_claims_per_document: int = Field(default=50, ge=1, le=100, description="Maximum claims to process")
    enable_uncertainty_quantification: bool = Field(default=True, description="Enable uncertainty analysis")
    preserve_context: bool = Field(default=True, description="Preserve document context")
    extract_citations: bool = Field(default=True, description="Extract and verify citations")
    evidence_sources: Optional[List[str]] = Field(None, description="Preferred evidence sources")
    verification_depth: str = Field(default="standard", description="Verification depth")
    require_multiple_sources: bool = Field(default=True, description="Require multiple sources")
    timeout_seconds: float = Field(default=300.0, ge=1.0, le=600.0, description="Processing timeout")
    parallel_processing: bool = Field(default=True, description="Enable parallel processing")
    cache_results: bool = Field(default=True, description="Cache results")
    
    @validator('document_type')
    def validate_document_type(cls, v):
        valid_types = ["general", "academic", "news", "legal", "medical", "financial", "technical"]
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid document type. Must be one of: {valid_types}")
        return v.lower()
    
    @validator('verification_depth')
    def validate_verification_depth(cls, v):
        valid_depths = ["quick", "standard", "thorough"]
        if v.lower() not in valid_depths:
            raise ValueError(f"Invalid verification depth. Must be one of: {valid_depths}")
        return v.lower()
    
    @validator('document_content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("Document content cannot be empty")
        if len(v) > 1000000:  # 1MB limit
            raise ValueError("Document content too large (max 1MB)")
        return v


class ClaimExtractionRequest(BaseModel):
    """Request model for claim extraction only."""
    
    document_content: str = Field(..., description="Document content")
    document_metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    document_type: str = Field(default="general", description="Type of document")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence threshold")
    max_claims: int = Field(default=50, ge=1, le=100, description="Maximum claims to extract")
    
    @validator('document_content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("Document content cannot be empty")
        return v


class SingleClaimVerificationRequest(BaseModel):
    """Request model for single claim verification."""
    
    claim_text: str = Field(..., description="Claim to verify")
    document_context: str = Field(..., description="Document context")
    document_metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    document_type: str = Field(default="general", description="Type of document")
    evidence_sources: Optional[List[str]] = Field(None, description="Evidence sources")
    
    @validator('claim_text')
    def validate_claim(cls, v):
        if not v.strip():
            raise ValueError("Claim text cannot be empty")
        return v


@router.post("/fact-check-document", response_model=Dict[str, Any])
async def fact_check_document(request: FactCheckRequest):
    """
    Perform comprehensive fact-checking on a document using DSPy modules.
    
    This endpoint processes the entire document through the DSPy fact-checking
    pipeline including claim extraction, verification, and synthesis.
    """
    try:
        result = await dspy_service.fact_check_document(
            document_content=request.document_content,
            document_metadata=request.document_metadata,
            document_type=request.document_type,
            confidence_threshold=request.confidence_threshold,
            max_claims_per_document=request.max_claims_per_document,
            enable_uncertainty_quantification=request.enable_uncertainty_quantification,
            preserve_context=request.preserve_context,
            extract_citations=request.extract_citations,
            evidence_sources=request.evidence_sources,
            verification_depth=request.verification_depth,
            require_multiple_sources=request.require_multiple_sources,
            timeout_seconds=request.timeout_seconds,
            parallel_processing=request.parallel_processing,
            cache_results=request.cache_results
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Document fact-checking failed: {e}")
        raise HTTPException(status_code=500, detail=f"Fact-checking failed: {str(e)}")


@router.post("/fact-check-file", response_model=Dict[str, Any])
async def fact_check_file(
    file: UploadFile = File(...),
    document_type: str = Form(default="general"),
    confidence_threshold: float = Form(default=0.5),
    max_claims_per_document: int = Form(default=50),
    enable_uncertainty_quantification: bool = Form(default=True),
    preserve_context: bool = Form(default=True),
    extract_citations: bool = Form(default=True),
    verification_depth: str = Form(default="standard"),
    require_multiple_sources: bool = Form(default=True),
    timeout_seconds: float = Form(default=300.0),
    parallel_processing: bool = Form(default=True),
    cache_results: bool = Form(default=True)
):
    """
    Fact-check an uploaded file using DSPy modules.
    
    Supports text files and will extract text content for fact-checking.
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Convert to text (assuming UTF-8 encoding for text files)
        try:
            document_content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File must be a text file (UTF-8 encoded)")
        
        # Create document metadata
        document_metadata = {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": len(file_content)
        }
        
        result = await dspy_service.fact_check_document(
            document_content=document_content,
            document_metadata=document_metadata,
            document_type=document_type,
            confidence_threshold=confidence_threshold,
            max_claims_per_document=max_claims_per_document,
            enable_uncertainty_quantification=enable_uncertainty_quantification,
            preserve_context=preserve_context,
            extract_citations=extract_citations,
            verification_depth=verification_depth,
            require_multiple_sources=require_multiple_sources,
            timeout_seconds=timeout_seconds,
            parallel_processing=parallel_processing,
            cache_results=cache_results
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File fact-checking failed: {e}")
        raise HTTPException(status_code=500, detail=f"File fact-checking failed: {str(e)}")


@router.post("/extract-claims", response_model=Dict[str, Any])
async def extract_claims(request: ClaimExtractionRequest):
    """
    Extract claims from document content without full verification.
    
    This endpoint only performs claim extraction using DSPy modules,
    which is faster than full fact-checking.
    """
    try:
        result = await dspy_service.extract_claims_only(
            document_content=request.document_content,
            document_metadata=request.document_metadata,
            document_type=request.document_type,
            confidence_threshold=request.confidence_threshold,
            max_claims=request.max_claims
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Claim extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Claim extraction failed: {str(e)}")


@router.post("/verify-claim", response_model=Dict[str, Any])
async def verify_single_claim(request: SingleClaimVerificationRequest):
    """
    Verify a single claim with document context using DSPy modules.
    
    This endpoint verifies one specific claim rather than processing
    an entire document.
    """
    try:
        result = await dspy_service.verify_single_claim(
            claim_text=request.claim_text,
            document_context=request.document_context,
            document_metadata=request.document_metadata,
            document_type=request.document_type,
            evidence_sources=request.evidence_sources
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Single claim verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Claim verification failed: {str(e)}")


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_dspy_capabilities():
    """
    Get information about DSPy fact-checking service capabilities.
    
    Returns supported document types, verification depths, and system status.
    """
    try:
        capabilities = await dspy_service.get_service_capabilities()
        return capabilities
        
    except Exception as e:
        logger.error(f"Failed to get DSPy capabilities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


@router.post("/fact-check-text-form", response_model=Dict[str, Any])
async def fact_check_text_form(
    document_content: str = Form(...),
    document_type: str = Form(default="general"),
    confidence_threshold: float = Form(default=0.5),
    max_claims_per_document: int = Form(default=50),
    enable_uncertainty_quantification: bool = Form(default=True),
    preserve_context: bool = Form(default=True),
    extract_citations: bool = Form(default=True),
    verification_depth: str = Form(default="standard"),
    require_multiple_sources: bool = Form(default=True),
    timeout_seconds: float = Form(default=300.0),
    parallel_processing: bool = Form(default=True),
    cache_results: bool = Form(default=True)
):
    """
    Fact-check text content using form data (alternative to JSON endpoint).
    """
    try:
        # Validate input
        if not document_content.strip():
            raise HTTPException(status_code=400, detail="Document content cannot be empty")
        if len(document_content) > 1000000:  # 1MB limit
            raise HTTPException(status_code=400, detail="Document content too large (max 1MB)")
        
        result = await dspy_service.fact_check_document(
            document_content=document_content,
            document_metadata={},
            document_type=document_type,
            confidence_threshold=confidence_threshold,
            max_claims_per_document=max_claims_per_document,
            enable_uncertainty_quantification=enable_uncertainty_quantification,
            preserve_context=preserve_context,
            extract_citations=extract_citations,
            verification_depth=verification_depth,
            require_multiple_sources=require_multiple_sources,
            timeout_seconds=timeout_seconds,
            parallel_processing=parallel_processing,
            cache_results=cache_results
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text form fact-checking failed: {e}")
        raise HTTPException(status_code=500, detail=f"Text fact-checking failed: {str(e)}")


@router.post("/extract-claims-form", response_model=Dict[str, Any])
async def extract_claims_form(
    document_content: str = Form(...),
    document_type: str = Form(default="general"),
    confidence_threshold: float = Form(default=0.5),
    max_claims: int = Form(default=50)
):
    """
    Extract claims using form data (alternative to JSON endpoint).
    """
    try:
        # Validate input
        if not document_content.strip():
            raise HTTPException(status_code=400, detail="Document content cannot be empty")
        
        result = await dspy_service.extract_claims_only(
            document_content=document_content,
            document_metadata={},
            document_type=document_type,
            confidence_threshold=confidence_threshold,
            max_claims=max_claims
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Claims extraction form failed: {e}")
        raise HTTPException(status_code=500, detail=f"Claim extraction failed: {str(e)}")


@router.post("/verify-claim-form", response_model=Dict[str, Any])
async def verify_claim_form(
    claim_text: str = Form(...),
    document_context: str = Form(...),
    document_type: str = Form(default="general")
):
    """
    Verify a single claim using form data (alternative to JSON endpoint).
    """
    try:
        # Validate input
        if not claim_text.strip():
            raise HTTPException(status_code=400, detail="Claim text cannot be empty")
        if not document_context.strip():
            raise HTTPException(status_code=400, detail="Document context cannot be empty")
        
        result = await dspy_service.verify_single_claim(
            claim_text=claim_text,
            document_context=document_context,
            document_metadata={},
            document_type=document_type,
            evidence_sources=None
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Claim verification form failed: {e}")
        raise HTTPException(status_code=500, detail=f"Claim verification failed: {str(e)}")
