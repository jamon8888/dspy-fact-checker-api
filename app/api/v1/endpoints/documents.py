"""
Document processing endpoints for the DSPy-Enhanced Fact-Checker API Platform.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Request, Form
from typing import Dict, Any, List, Optional
import uuid
import logging

from app.core.config import get_settings, Settings
from app.services.document_service import DocumentProcessingService, get_document_service
from app.core.document_processing.exceptions import (
    ProcessingError, UnsupportedFormatError, DocumentTooLargeError
)
from app.api.v1.models.documents import (
    DocumentUploadResponse, DocumentProcessingStatus, DocumentFactCheckResult,
    BatchDocumentResponse, DocumentSearchRequest, DocumentSearchResponse,
    DocumentProcessingOptions, ProcessingStatus
)
from app.api.v1.models.base import ResponseStatus
from app.api.v1.dependencies.common import (
    get_request_id, check_rate_limit, validate_file_upload,
    estimate_processing_cost, estimate_processing_time, log_request
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    processor: Optional[str] = Form(None, description="Specific processor to use (default: docling)"),
    extract_images: bool = Form(True, description="Extract images from document"),
    extract_tables: bool = Form(True, description="Extract tables from document"),
    settings: Settings = Depends(get_settings),
    document_service: DocumentProcessingService = Depends(get_document_service),
    _: None = Depends(check_rate_limit),
    request_id: str = Depends(get_request_id)
) -> DocumentUploadResponse:
    """
    Upload and process a document using Enhanced Docling with OCR integration.

    Supported formats: PDF, DOC, DOCX, TXT, RTF, ODT, PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP
    Max file size: 50MB
    Processing time: 30 seconds - 5 minutes depending on document complexity

    Features:
    - Advanced PDF layout understanding with Enhanced Docling
    - OCR processing for image documents (PNG, JPG, etc.)
    - Table structure preservation and extraction
    - Image extraction and classification
    - Multi-language support
    - Structured content extraction (headings, paragraphs, lists)
    - Reading order detection
    - Intelligent processing engine selection
    - Local OCR with RapidOCR for cost-effective processing
    """

    try:
        # Validate file upload
        file_validation = await validate_file_upload(
            filename=file.filename or "unknown",
            file_size=file.size or 0,
            settings=settings
        )

        # Read file content
        file_content = await file.read()

        # Process document with Docling
        processing_result = await document_service.process_document(
            file_data=file_content,
            filename=file.filename or "unknown",
            processor_name=processor or "docling",
            extract_images=extract_images,
            extract_tables=extract_tables
        )

        if processing_result["success"]:
            # Estimate processing cost and time (based on actual processing)
            estimated_cost = await estimate_processing_cost(
                file_size=len(file_content),
                processing_options={"extract_tables": extract_tables, "extract_images": extract_images}
            )

            estimated_time = processing_result.get("processing_time", 0)

            # Create processing options
            processing_options = DocumentProcessingOptions(
                extract_tables=extract_tables,
                extract_images=extract_images,
                processor_name=processor or "docling"
            )

            logger.info(f"Document processed successfully: {file.filename} (ID: {processing_result['processing_id']}, Request: {request_id})")

            return DocumentUploadResponse(
                status=ResponseStatus.SUCCESS,
                message="Document uploaded and processed successfully with Docling",
                request_id=request_id,
                processing_id=processing_result["processing_id"],
                filename=file.filename or "unknown",
                file_type=processing_result["file_type"],
                file_size=len(file_content),
                estimated_completion_time=estimated_time,
                estimated_cost=estimated_cost,
                queue_position=0,  # Immediate processing
                processing_options=processing_options
            )
        else:
            # Processing failed
            error_message = processing_result.get("error", "Unknown processing error")
            logger.error(f"Document processing failed: {file.filename} - {error_message}")

            raise HTTPException(
                status_code=422,
                detail={
                    "error": error_message,
                    "error_type": processing_result.get("error_type", "ProcessingError"),
                    "processing_id": processing_result.get("processing_id")
                }
            )

    except UnsupportedFormatError as e:
        raise HTTPException(
            status_code=415,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )

    except DocumentTooLargeError as e:
        raise HTTPException(
            status_code=413,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )

    except ProcessingError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )

    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during document processing",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.get("/status/{processing_id}", response_model=DocumentProcessingStatus)
async def get_processing_status(
    processing_id: str,
    document_service: DocumentProcessingService = Depends(get_document_service),
    request_id: str = Depends(get_request_id)
) -> DocumentProcessingStatus:
    """Get the processing status of a document."""

    try:
        # Get status from document service
        status = await document_service.get_processing_status(processing_id)

        if not status:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"Processing status not found for ID: {processing_id}",
                    "error_code": "STATUS_NOT_FOUND"
                }
            )

        logger.info(f"Retrieved status for processing ID: {processing_id} (Request: {request_id})")

        # Map status to ProcessingStatus enum
        status_mapping = {
            "processing": ProcessingStatus.PROCESSING,
            "completed": ProcessingStatus.COMPLETED,
            "failed": ProcessingStatus.FAILED,
            "pending": ProcessingStatus.PENDING
        }

        return DocumentProcessingStatus(
            processing_id=processing_id,
            status=status_mapping.get(status["status"], ProcessingStatus.PROCESSING),
            progress=100.0 if status["status"] == "completed" else 50.0,
            current_stage=status.get("message", "Processing document"),
            estimated_completion_time=None,
            processing_time=None  # Will be available in results
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing status: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve processing status",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.get("/results/{processing_id}")
async def get_processing_results(
    processing_id: str,
    document_service: DocumentProcessingService = Depends(get_document_service)
) -> Dict[str, Any]:
    """Get the complete processing results for a document including extracted content, metadata, tables, and images."""

    try:
        # Get results from document service
        result = await document_service.get_processing_result(processing_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"Processing result not found for ID: {processing_id}",
                    "error_code": "RESULT_NOT_FOUND"
                }
            )

        logger.info(f"Retrieved results for processing ID: {processing_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing results: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve processing results",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.get("/formats")
async def get_supported_formats(
    document_service: DocumentProcessingService = Depends(get_document_service)
) -> Dict[str, Any]:
    """
    Get list of supported document formats and available processors.

    Returns information about supported file formats and
    the capabilities of each available processor.
    """
    try:
        formats = document_service.get_supported_formats()
        processors = document_service.get_available_processors()

        return {
            "supported_formats": formats,
            "available_processors": processors,
            "default_processor": "enhanced_docling",
            "features": {
                "enhanced_docling": {
                    "advanced_pdf_layout": True,
                    "table_extraction": True,
                    "image_extraction": True,
                    "structured_content": True,
                    "reading_order_detection": True,
                    "multi_language_support": True,
                    "ocr_processing": True,
                    "image_document_support": True,
                    "local_ocr_engines": ["rapidocr"],
                    "cloud_ocr_engines": ["mistral"],
                    "intelligent_engine_selection": True,
                    "cost_optimization": True
                },
                "docling": {
                    "advanced_pdf_layout": True,
                    "table_extraction": True,
                    "image_extraction": True,
                    "structured_content": True,
                    "reading_order_detection": True,
                    "multi_language_support": True,
                    "ocr_processing": True
                }
            }
        }

    except Exception as e:
        logger.error(f"Failed to get supported formats: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve supported formats",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.post("/batch-upload")
async def batch_upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Upload and process multiple documents for fact-checking.
    
    Maximum 10 files per batch.
    """
    
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files allowed per batch"
        )
    
    batch_id = str(uuid.uuid4())
    processing_ids = []
    
    for file in files:
        if not file.filename:
            continue
            
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.SUPPORTED_FORMATS:
            continue
            
        processing_id = str(uuid.uuid4())
        processing_ids.append({
            "processing_id": processing_id,
            "filename": file.filename,
            "file_type": file_extension,
            "file_size": file.size
        })
        
        # TODO: Add actual batch processing logic
        logger.info(f"Added to batch: {file.filename} (ID: {processing_id})")
    
    return {
        "batch_id": batch_id,
        "files_accepted": len(processing_ids),
        "files_rejected": len(files) - len(processing_ids),
        "processing_ids": processing_ids,
        "status": "processing",
        "message": "Batch upload completed successfully"
    }
