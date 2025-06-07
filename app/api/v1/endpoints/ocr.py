"""
OCR (Optical Character Recognition) API endpoints.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.ocr_service import OCRService, get_ocr_service
from app.core.ocr import (
    MistralOCRError, MistralOCRConfigurationError, 
    MistralOCRProcessingError, MistralOCRRateLimitError
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


class OCRProcessingResponse(BaseModel):
    """Response model for OCR processing."""
    processing_id: str = Field(..., description="Unique processing identifier")
    filename: Optional[str] = Field(None, description="Original filename")
    source_url: Optional[str] = Field(None, description="Source URL if processed from URL")
    file_type: str = Field(..., description="File type")
    processor_used: str = Field(..., description="OCR processor used")
    success: bool = Field(..., description="Processing success status")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    confidence_score: Optional[float] = Field(None, description="OCR confidence score")
    processed_at: str = Field(..., description="Processing timestamp")


class OCRResults(BaseModel):
    """OCR results model."""
    text: str = Field(..., description="Extracted text content")
    markdown: str = Field(..., description="Extracted content in markdown format")
    metadata: Dict[str, Any] = Field(..., description="OCR metadata")
    images: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted images")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted tables")
    structure: Dict[str, Any] = Field(..., description="Document structure analysis")


class OCRStatusResponse(BaseModel):
    """OCR processing status response model."""
    processing_id: str = Field(..., description="Processing identifier")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    updated_at: str = Field(..., description="Last update timestamp")


class OCRCapabilitiesResponse(BaseModel):
    """OCR capabilities response model."""
    available: bool = Field(..., description="Whether OCR is available")
    processors: Dict[str, Any] = Field(..., description="Available OCR processors")


@router.post("/image", response_model=OCRProcessingResponse)
async def process_image_ocr(
    file: UploadFile = File(..., description="Image file to process with OCR"),
    include_image_base64: bool = Form(False, description="Include image base64 in response"),
    image_format: Optional[str] = Form(None, description="Image format (auto-detected if not provided)"),
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """
    Process an image using Mistral OCR for text extraction.
    
    Supported formats: PNG, JPEG, GIF, BMP, TIFF, WebP, AVIF
    Max file size: 50MB
    
    Features:
    - High-accuracy text extraction
    - Multi-language support
    - Complex layout understanding
    - Table extraction and structure preservation
    - Image classification and metadata
    """
    settings = get_settings()
    
    try:
        # Check if OCR is available
        if not ocr_service.is_available():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "OCR service is not available. Please configure MISTRAL_API_KEY.",
                    "error_code": "OCR_UNAVAILABLE"
                }
            )
        
        # Validate file size
        if file.size and file.size > settings.MISTRAL_OCR_MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": f"File size ({file.size} bytes) exceeds maximum allowed size ({settings.MISTRAL_OCR_MAX_FILE_SIZE} bytes)",
                    "error_code": "FILE_TOO_LARGE"
                }
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size after reading
        if len(file_content) > settings.MISTRAL_OCR_MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": f"File size ({len(file_content)} bytes) exceeds maximum allowed size ({settings.MISTRAL_OCR_MAX_FILE_SIZE} bytes)",
                    "error_code": "FILE_TOO_LARGE"
                }
            )
        
        # Process image with OCR
        result = await ocr_service.process_image_ocr(
            image_data=file_content,
            filename=file.filename or "unknown",
            image_format=image_format,
            include_image_base64=include_image_base64
        )
        
        if result["success"]:
            return OCRProcessingResponse(**result)
        else:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": result.get("error", "OCR processing failed"),
                    "error_type": result.get("error_type", "ProcessingError")
                }
            )
    
    except MistralOCRRateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail={
                "error": str(e),
                "error_code": "RATE_LIMIT_EXCEEDED",
                "retry_after": 60  # Suggest retry after 60 seconds
            }
        )
    
    except MistralOCRConfigurationError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": str(e),
                "error_code": "CONFIGURATION_ERROR"
            }
        )
    
    except MistralOCRProcessingError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": str(e),
                "error_code": "PROCESSING_ERROR"
            }
        )
    
    except Exception as e:
        logger.error(f"Image OCR processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during OCR processing",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.post("/pdf", response_model=OCRProcessingResponse)
async def process_pdf_ocr(
    file: UploadFile = File(..., description="PDF file to process with OCR"),
    include_image_base64: bool = Form(False, description="Include image base64 in response"),
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """
    Process a PDF using Mistral OCR for text extraction.
    
    Max file size: 50MB
    Max pages: 1000
    
    Features:
    - Advanced PDF layout understanding
    - Text extraction from scanned PDFs
    - Table structure preservation
    - Image extraction and classification
    - Multi-language support
    """
    settings = get_settings()
    
    try:
        # Check if OCR is available
        if not ocr_service.is_available():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "OCR service is not available. Please configure MISTRAL_API_KEY.",
                    "error_code": "OCR_UNAVAILABLE"
                }
            )
        
        # Validate file size
        if file.size and file.size > settings.MISTRAL_OCR_MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": f"File size ({file.size} bytes) exceeds maximum allowed size ({settings.MISTRAL_OCR_MAX_FILE_SIZE} bytes)",
                    "error_code": "FILE_TOO_LARGE"
                }
            )
        
        # Read file content
        file_content = await file.read()
        
        # Process PDF with OCR
        result = await ocr_service.process_pdf_ocr(
            pdf_data=file_content,
            filename=file.filename or "unknown",
            include_image_base64=include_image_base64
        )
        
        if result["success"]:
            return OCRProcessingResponse(**result)
        else:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": result.get("error", "OCR processing failed"),
                    "error_type": result.get("error_type", "ProcessingError")
                }
            )
    
    except Exception as e:
        logger.error(f"PDF OCR processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during OCR processing",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.post("/url", response_model=OCRProcessingResponse)
async def process_url_ocr(
    document_url: str = Form(..., description="URL of document to process with OCR"),
    include_image_base64: bool = Form(False, description="Include image base64 in response"),
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """
    Process a document from URL using Mistral OCR.
    
    Supports both image URLs and document URLs.
    Automatically detects document type from URL.
    """
    try:
        # Check if OCR is available
        if not ocr_service.is_available():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "OCR service is not available. Please configure MISTRAL_API_KEY.",
                    "error_code": "OCR_UNAVAILABLE"
                }
            )
        
        # Process URL with OCR
        result = await ocr_service.process_url_ocr(
            document_url=document_url,
            include_image_base64=include_image_base64
        )
        
        if result["success"]:
            return OCRProcessingResponse(**result)
        else:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": result.get("error", "OCR processing failed"),
                    "error_type": result.get("error_type", "ProcessingError")
                }
            )
    
    except Exception as e:
        logger.error(f"URL OCR processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during OCR processing",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.get("/status/{processing_id}", response_model=OCRStatusResponse)
async def get_ocr_processing_status(
    processing_id: str,
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """
    Get the processing status of an OCR operation.
    
    Returns the current status of OCR processing including
    progress updates and completion status.
    """
    try:
        status = await ocr_service.get_processing_status(processing_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"OCR processing status not found for ID: {processing_id}",
                    "error_code": "STATUS_NOT_FOUND"
                }
            )
        
        return OCRStatusResponse(**status)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get OCR processing status: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve OCR processing status",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.post("/annotations", response_model=OCRProcessingResponse)
async def process_document_with_annotations(
    file: UploadFile = File(..., description="Document file to process with structured annotations"),
    document_type: str = Form("pdf", description="Document type (pdf, image, docx, pptx)"),
    pages: Optional[str] = Form(None, description="Comma-separated page numbers (max 8 for document annotations)"),
    bbox_annotation_schema: Optional[str] = Form(None, description="JSON schema for bbox annotations"),
    document_annotation_schema: Optional[str] = Form(None, description="JSON schema for document annotations"),
    include_image_base64: bool = Form(False, description="Include image base64 in response"),
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """
    Process a document with structured annotations using Mistral Document AI.

    This endpoint supports the full Mistral Document AI annotation capabilities:
    - BBox annotations: Extract structured data from images/figures within documents
    - Document annotations: Extract structured data from entire documents

    Features:
    - Custom JSON schemas for structured data extraction
    - Support for multiple document types (PDF, DOCX, PPTX, images)
    - Page-specific processing (max 8 pages for document annotations)
    - High-accuracy OCR with structured output

    Example bbox annotation schema:
    {
        "properties": {
            "image_type": {"type": "string", "description": "Type of image"},
            "description": {"type": "string", "description": "Image description"},
            "data_points": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["image_type", "description"]
    }

    Example document annotation schema:
    {
        "properties": {
            "language": {"type": "string"},
            "title": {"type": "string"},
            "key_points": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"}
        },
        "required": ["language", "title"]
    }
    """
    settings = get_settings()

    try:
        # Check if OCR is available
        if not ocr_service.is_available():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "OCR service is not available. Please configure MISTRAL_API_KEY.",
                    "error_code": "OCR_UNAVAILABLE"
                }
            )

        # Validate file size
        if file.size and file.size > settings.MISTRAL_OCR_MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": f"File size ({file.size} bytes) exceeds maximum allowed size ({settings.MISTRAL_OCR_MAX_FILE_SIZE} bytes)",
                    "error_code": "FILE_TOO_LARGE"
                }
            )

        # Parse pages parameter
        pages_list = None
        if pages:
            try:
                pages_list = [int(p.strip()) for p in pages.split(",")]
                if len(pages_list) > 8 and document_annotation_schema:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "Document annotations are limited to 8 pages maximum",
                            "error_code": "TOO_MANY_PAGES"
                        }
                    )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Invalid pages format. Use comma-separated integers (e.g., '0,1,2')",
                        "error_code": "INVALID_PAGES_FORMAT"
                    }
                )

        # Parse annotation schemas
        bbox_schema = None
        document_schema = None

        if bbox_annotation_schema:
            try:
                import json
                bbox_schema_data = json.loads(bbox_annotation_schema)
                # Create proper schema format for Mistral API
                bbox_schema = {
                    "type": "json_schema",
                    "json_schema": {
                        "schema": {
                            "properties": bbox_schema_data.get("properties", {}),
                            "required": bbox_schema_data.get("required", []),
                            "title": bbox_schema_data.get("title", "BBoxAnnotation"),
                            "type": "object",
                            "additionalProperties": False
                        },
                        "name": "bbox_annotation",
                        "strict": True
                    }
                }
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Invalid JSON format for bbox annotation schema",
                        "error_code": "INVALID_BBOX_SCHEMA"
                    }
                )

        if document_annotation_schema:
            try:
                import json
                doc_schema_data = json.loads(document_annotation_schema)
                # Create proper schema format for Mistral API
                document_schema = {
                    "type": "json_schema",
                    "json_schema": {
                        "schema": {
                            "properties": doc_schema_data.get("properties", {}),
                            "required": doc_schema_data.get("required", []),
                            "title": doc_schema_data.get("title", "DocumentAnnotation"),
                            "type": "object",
                            "additionalProperties": False
                        },
                        "name": "document_annotation",
                        "strict": True
                    }
                }
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Invalid JSON format for document annotation schema",
                        "error_code": "INVALID_DOCUMENT_SCHEMA"
                    }
                )

        # Validate that at least one annotation schema is provided
        if not bbox_schema and not document_schema:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "At least one annotation schema (bbox or document) must be provided",
                    "error_code": "NO_ANNOTATION_SCHEMA"
                }
            )

        # Read file content
        file_content = await file.read()

        # Process document with structured annotations
        result = await ocr_service.process_with_structured_annotations(
            document_data=file_content,
            filename=file.filename or "unknown",
            document_type=document_type,
            pages=pages_list,
            bbox_annotation_schema=bbox_schema,
            document_annotation_schema=document_schema,
            include_image_base64=include_image_base64
        )

        if result["success"]:
            return OCRProcessingResponse(**result)
        else:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": result.get("error", "Annotation processing failed"),
                    "error_type": result.get("error_type", "ProcessingError")
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document annotation processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during annotation processing",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.get("/result/{processing_id}")
async def get_ocr_processing_result(
    processing_id: str,
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """
    Get the complete OCR processing result.
    
    Returns the full OCR result including extracted text,
    markdown, metadata, tables, images, and structure analysis.
    """
    try:
        result = await ocr_service.get_processing_result(processing_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"OCR processing result not found for ID: {processing_id}",
                    "error_code": "RESULT_NOT_FOUND"
                }
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get OCR processing result: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve OCR processing result",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.get("/capabilities", response_model=OCRCapabilitiesResponse)
async def get_ocr_capabilities(
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """
    Get OCR service capabilities and supported features.
    
    Returns information about available OCR processors,
    supported formats, and feature capabilities.
    """
    try:
        capabilities = ocr_service.get_capabilities()
        return OCRCapabilitiesResponse(**capabilities)
    
    except Exception as e:
        logger.error(f"Failed to get OCR capabilities: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve OCR capabilities",
                "error_code": "INTERNAL_ERROR"
            }
        )
