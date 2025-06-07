#!/usr/bin/env python3
"""
Enhanced Fact-Checking API Endpoints
Integrates enhanced Docling processing with DSPy fact-checking pipeline
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from pydantic import BaseModel, Field

# from app.core.auth import get_current_user  # Optional auth
from app.core.rate_limiting import check_rate_limit
from app.core.request_id import get_request_id
from app.services.enhanced_fact_checking_service import enhanced_fact_checking_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-fact-check", tags=["Enhanced Fact-Checking"])


class EnhancedTextFactCheckRequest(BaseModel):
    """Request model for enhanced text fact-checking."""
    text: str = Field(..., description="Text content to fact-check")
    document_type: str = Field("general", description="Type of document for specialized analysis")
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")
    max_claims_per_document: int = Field(50, ge=1, le=200, description="Maximum claims to extract")
    enable_uncertainty_quantification: bool = Field(True, description="Enable uncertainty analysis")
    preserve_context: bool = Field(True, description="Preserve document context")
    extract_citations: bool = Field(True, description="Extract citations and references")
    verification_depth: str = Field("standard", description="Verification depth")
    require_multiple_sources: bool = Field(True, description="Require multiple sources")
    context_metadata: Optional[Dict[str, Any]] = Field(None, description="Optional context metadata")


class EnhancedDocumentFactCheckRequest(BaseModel):
    """Request model for enhanced document fact-checking."""
    document_type: str = Field("general", description="Type of document for specialized analysis")
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")
    max_claims_per_document: int = Field(50, ge=1, le=200, description="Maximum claims to extract")
    enable_uncertainty_quantification: bool = Field(True, description="Enable uncertainty analysis")
    preserve_context: bool = Field(True, description="Preserve document context")
    extract_citations: bool = Field(True, description="Extract citations and references")
    verification_depth: str = Field("standard", description="Verification depth")
    require_multiple_sources: bool = Field(True, description="Require multiple sources")
    enable_advanced_processing: bool = Field(True, description="Enable advanced document processing")
    extract_tables: bool = Field(True, description="Extract and analyze tables")
    extract_images: bool = Field(True, description="Extract and analyze images")
    enable_chunking: bool = Field(True, description="Enable document chunking for RAG")


@router.post("/text", response_model=Dict[str, Any])
async def enhanced_text_fact_check(
    request: EnhancedTextFactCheckRequest,
    _: None = Depends(check_rate_limit),
    request_id: str = Depends(get_request_id)
) -> Dict[str, Any]:
    """
    Enhanced text fact-checking with advanced context analysis.
    
    This endpoint provides comprehensive fact-checking with enhanced context
    understanding and advanced DSPy processing capabilities.
    """
    try:
        logger.info(f"Enhanced text fact-checking request: {len(request.text)} characters")
        
        result = await enhanced_fact_checking_service.fact_check_text_with_context(
            text=request.text,
            context_metadata=request.context_metadata,
            document_type=request.document_type,
            confidence_threshold=request.confidence_threshold,
            max_claims_per_document=request.max_claims_per_document,
            enable_uncertainty_quantification=request.enable_uncertainty_quantification,
            preserve_context=request.preserve_context,
            extract_citations=request.extract_citations,
            verification_depth=request.verification_depth,
            require_multiple_sources=request.require_multiple_sources
        )
        
        logger.info(f"Enhanced text fact-checking completed successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced text fact-checking failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Enhanced text fact-checking failed: {str(e)}"
        )


@router.post("/document", response_model=Dict[str, Any])
async def enhanced_document_fact_check(
    file: UploadFile = File(..., description="Document file to fact-check"),
    document_type: str = Form("general", description="Type of document"),
    confidence_threshold: float = Form(0.5, description="Minimum confidence threshold"),
    max_claims_per_document: int = Form(50, description="Maximum claims to extract"),
    enable_uncertainty_quantification: bool = Form(True, description="Enable uncertainty analysis"),
    preserve_context: bool = Form(True, description="Preserve document context"),
    extract_citations: bool = Form(True, description="Extract citations"),
    verification_depth: str = Form("standard", description="Verification depth"),
    require_multiple_sources: bool = Form(True, description="Require multiple sources"),
    enable_advanced_processing: bool = Form(True, description="Enable advanced processing"),
    extract_tables: bool = Form(True, description="Extract tables"),
    extract_images: bool = Form(True, description="Extract images"),
    enable_chunking: bool = Form(True, description="Enable chunking"),
    _: None = Depends(check_rate_limit),
    request_id: str = Depends(get_request_id)
) -> Dict[str, Any]:
    """
    Enhanced document fact-checking with advanced document processing.
    
    This endpoint combines enhanced Docling document processing with DSPy
    fact-checking for comprehensive document analysis including:
    - Advanced OCR and text extraction
    - Table structure recognition
    - Image classification and analysis
    - Formula and code detection
    - Document chunking for RAG
    - Context-aware fact-checking
    """
    try:
        logger.info(f"Enhanced document fact-checking: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        
        result = await enhanced_fact_checking_service.fact_check_document(
            file_data=file_content,
            filename=file.filename or "unknown",
            document_type=document_type,
            confidence_threshold=confidence_threshold,
            max_claims_per_document=max_claims_per_document,
            enable_uncertainty_quantification=enable_uncertainty_quantification,
            preserve_context=preserve_context,
            extract_citations=extract_citations,
            verification_depth=verification_depth,
            require_multiple_sources=require_multiple_sources,
            extract_tables=extract_tables,
            extract_images=extract_images,
            enable_chunking=enable_chunking
        )
        
        logger.info(f"Enhanced document fact-checking completed: {file.filename}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced document fact-checking failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced document fact-checking failed: {str(e)}"
        )


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_enhanced_capabilities() -> Dict[str, Any]:
    """
    Get enhanced fact-checking capabilities and features.
    
    Returns information about available advanced processing features,
    supported document types, and processing capabilities.
    """
    try:
        # Check service initialization status
        if not enhanced_fact_checking_service.initialized:
            await enhanced_fact_checking_service.initialize()
        
        capabilities = {
            "service_status": {
                "initialized": enhanced_fact_checking_service.initialized,
                "enhanced_processor_available": enhanced_fact_checking_service.enhanced_processor is not None,
                "dspy_service_available": enhanced_fact_checking_service.dspy_service.initialized
            },
            "document_processing": {
                "supported_formats": ["PDF", "DOCX", "HTML", "TXT", "RTF", "ODT"],
                "advanced_features": {
                    "ocr_processing": True,
                    "table_structure_recognition": True,
                    "image_classification": True,
                    "formula_detection": True,
                    "code_recognition": True,
                    "document_chunking": True,
                    "multi_language_support": True
                },
                "processing_limits": {
                    "max_file_size": "100MB",
                    "max_pages": 1000,
                    "timeout_seconds": 300
                }
            },
            "fact_checking": {
                "document_types": ["general", "academic", "news", "legal", "medical", "financial", "technical"],
                "verification_depths": ["standard", "deep", "comprehensive"],
                "features": {
                    "claim_extraction": True,
                    "claim_verification": True,
                    "uncertainty_quantification": True,
                    "citation_extraction": True,
                    "context_preservation": True,
                    "multi_source_verification": True
                }
            },
            "integration_features": {
                "enhanced_document_processing": True,
                "context_aware_fact_checking": True,
                "structured_content_analysis": True,
                "multi_modal_processing": True,
                "rag_ready_chunking": True
            }
        }
        
        return capabilities
        
    except Exception as e:
        logger.error(f"Failed to get enhanced capabilities: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get capabilities: {str(e)}"
        )


@router.get("/status", response_model=Dict[str, Any])
async def get_enhanced_service_status() -> Dict[str, Any]:
    """
    Get enhanced fact-checking service status and health information.
    
    Returns detailed status information about all service components
    and their operational status.
    """
    try:
        status = {
            "service_name": "Enhanced Fact-Checking Service",
            "version": "1.0.0",
            "status": "operational" if enhanced_fact_checking_service.initialized else "initializing",
            "components": {
                "enhanced_fact_checking_service": {
                    "status": "operational" if enhanced_fact_checking_service.initialized else "initializing",
                    "initialized": enhanced_fact_checking_service.initialized
                },
                "enhanced_docling_processor": {
                    "status": "operational" if enhanced_fact_checking_service.enhanced_processor else "unavailable",
                    "available": enhanced_fact_checking_service.enhanced_processor is not None
                },
                "dspy_fact_checking": {
                    "status": "operational" if enhanced_fact_checking_service.dspy_service.initialized else "initializing",
                    "initialized": enhanced_fact_checking_service.dspy_service.initialized
                },
                "document_processing": {
                    "status": "operational",
                    "service_available": True
                }
            },
            "features": {
                "advanced_document_processing": enhanced_fact_checking_service.enhanced_processor is not None,
                "context_aware_fact_checking": enhanced_fact_checking_service.initialized,
                "multi_modal_analysis": True,
                "rag_integration": True
            },
            "last_checked": "2024-01-01T00:00:00Z"
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get service status: {str(e)}"
        )
