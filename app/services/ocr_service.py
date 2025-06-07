"""
OCR service for the DSPy-Enhanced Fact-Checker API Platform.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime
import uuid
import base64
from pathlib import Path

from app.core.ocr import (
    MistralOCRProcessor, MistralOCRError, MistralOCRConfigurationError,
    MistralOCRProcessingError, MistralOCRRateLimitError, MISTRAL_AVAILABLE
)
from app.core.config import get_settings
from app.core.redis import cache

logger = logging.getLogger(__name__)


class OCRService:
    """Service for optical character recognition using Mistral OCR."""
    
    def __init__(self):
        """Initialize OCR service."""
        self.settings = get_settings()
        self._initialize_processors()
    
    def _initialize_processors(self):
        """Initialize OCR processors."""
        try:
            if MISTRAL_AVAILABLE and self.settings.MISTRAL_API_KEY:
                self.mistral_processor = MistralOCRProcessor(
                    api_key=self.settings.MISTRAL_API_KEY
                )
                logger.info("Mistral OCR processor initialized successfully")
            else:
                self.mistral_processor = None
                if not MISTRAL_AVAILABLE:
                    logger.warning("Mistral OCR not available - missing mistralai package")
                else:
                    logger.warning("Mistral OCR not configured - missing API key")
                    
        except Exception as e:
            logger.error(f"Failed to initialize OCR processors: {e}")
            self.mistral_processor = None
    
    async def process_image_ocr(
        self,
        image_data: Union[bytes, BinaryIO],
        filename: str,
        image_format: Optional[str] = None,
        include_image_base64: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process an image using OCR.
        
        Args:
            image_data: Image data as bytes or file-like object
            filename: Original filename
            image_format: Image format (auto-detected if not provided)
            include_image_base64: Whether to include image base64 in response
            **kwargs: Additional processing options
            
        Returns:
            OCR results with extracted text and metadata
        """
        processing_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Check if OCR is available
            if not self.mistral_processor:
                raise MistralOCRConfigurationError(
                    "Mistral OCR is not available. Please configure MISTRAL_API_KEY."
                )
            
            # Convert file data to bytes if needed
            if isinstance(image_data, bytes):
                data_bytes = image_data
            else:
                data_bytes = image_data.read()
            
            # Auto-detect image format if not provided
            if not image_format:
                image_format = self._detect_image_format(filename, data_bytes)
            
            # Update processing status
            await self._update_processing_status(
                processing_id,
                "processing",
                f"Processing image OCR for {filename}"
            )
            
            # Process with Mistral OCR
            ocr_result = await self.mistral_processor.process_image(
                image_data=data_bytes,
                image_format=image_format,
                include_image_base64=include_image_base64,
                **kwargs
            )
            
            # Prepare response
            response = {
                "processing_id": processing_id,
                "filename": filename,
                "file_type": "image",
                "image_format": image_format,
                "processor_used": "mistral-ocr",
                "success": ocr_result["success"],
                "processing_time": ocr_result["metadata"]["processing_time"],
                "confidence_score": ocr_result["metadata"]["confidence_score"],
                "processed_at": datetime.now().isoformat(),
                "ocr_results": {
                    "text": ocr_result["text"],
                    "markdown": ocr_result["markdown"],
                    "metadata": ocr_result["metadata"],
                    "images": ocr_result["images"],
                    "tables": ocr_result["tables"],
                    "structure": ocr_result["structure"]
                },
                "statistics": {
                    "character_count": ocr_result["metadata"]["character_count"],
                    "word_count": ocr_result["metadata"]["word_count"],
                    "language": ocr_result["metadata"]["language"],
                    "total_tables": len(ocr_result["tables"]),
                    "total_images": len(ocr_result["images"])
                }
            }
            
            # Update success status
            await self._update_processing_status(
                processing_id,
                "completed",
                "Image OCR processing completed successfully"
            )
            
            # Cache the result
            await cache.set(f"ocr_processing:{processing_id}", response, ttl=3600)
            
            return response
            
        except MistralOCRRateLimitError as e:
            logger.warning(f"OCR rate limit exceeded for {filename}: {e}")
            error_response = self._create_error_response(
                processing_id, filename, "rate_limit_exceeded", str(e), start_time
            )
            await self._update_processing_status(processing_id, "failed", str(e))
            return error_response
            
        except MistralOCRConfigurationError as e:
            logger.error(f"OCR configuration error for {filename}: {e}")
            error_response = self._create_error_response(
                processing_id, filename, "configuration_error", str(e), start_time
            )
            await self._update_processing_status(processing_id, "failed", str(e))
            return error_response
            
        except Exception as e:
            logger.error(f"Image OCR processing failed for {filename}: {e}")
            error_response = self._create_error_response(
                processing_id, filename, "processing_error", str(e), start_time
            )
            await self._update_processing_status(processing_id, "failed", str(e))
            return error_response
    
    async def process_pdf_ocr(
        self,
        pdf_data: Union[bytes, BinaryIO],
        filename: str,
        include_image_base64: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a PDF using OCR.
        
        Args:
            pdf_data: PDF data as bytes or file-like object
            filename: Original filename
            include_image_base64: Whether to include image base64 in response
            **kwargs: Additional processing options
            
        Returns:
            OCR results with extracted text and metadata
        """
        processing_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Check if OCR is available
            if not self.mistral_processor:
                raise MistralOCRConfigurationError(
                    "Mistral OCR is not available. Please configure MISTRAL_API_KEY."
                )
            
            # Convert file data to bytes if needed
            if isinstance(pdf_data, bytes):
                data_bytes = pdf_data
            else:
                data_bytes = pdf_data.read()
            
            # Update processing status
            await self._update_processing_status(
                processing_id,
                "processing",
                f"Processing PDF OCR for {filename}"
            )
            
            # Process with Mistral OCR
            ocr_result = await self.mistral_processor.process_pdf(
                pdf_data=data_bytes,
                include_image_base64=include_image_base64,
                **kwargs
            )
            
            # Prepare response
            response = {
                "processing_id": processing_id,
                "filename": filename,
                "file_type": "pdf",
                "processor_used": "mistral-ocr",
                "success": ocr_result["success"],
                "processing_time": ocr_result["metadata"]["processing_time"],
                "confidence_score": ocr_result["metadata"]["confidence_score"],
                "processed_at": datetime.now().isoformat(),
                "ocr_results": {
                    "text": ocr_result["text"],
                    "markdown": ocr_result["markdown"],
                    "metadata": ocr_result["metadata"],
                    "images": ocr_result["images"],
                    "tables": ocr_result["tables"],
                    "structure": ocr_result["structure"]
                },
                "statistics": {
                    "character_count": ocr_result["metadata"]["character_count"],
                    "word_count": ocr_result["metadata"]["word_count"],
                    "language": ocr_result["metadata"]["language"],
                    "estimated_pages": ocr_result["metadata"]["estimated_pages"],
                    "total_tables": len(ocr_result["tables"]),
                    "total_images": len(ocr_result["images"])
                }
            }
            
            # Update success status
            await self._update_processing_status(
                processing_id,
                "completed",
                "PDF OCR processing completed successfully"
            )
            
            # Cache the result
            await cache.set(f"ocr_processing:{processing_id}", response, ttl=3600)
            
            return response
            
        except Exception as e:
            logger.error(f"PDF OCR processing failed for {filename}: {e}")
            error_response = self._create_error_response(
                processing_id, filename, "processing_error", str(e), start_time
            )
            await self._update_processing_status(processing_id, "failed", str(e))
            return error_response
    
    async def process_url_ocr(
        self,
        document_url: str,
        include_image_base64: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a document from URL using OCR.
        
        Args:
            document_url: URL of the document to process
            include_image_base64: Whether to include image base64 in response
            **kwargs: Additional processing options
            
        Returns:
            OCR results with extracted text and metadata
        """
        processing_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Check if OCR is available
            if not self.mistral_processor:
                raise MistralOCRConfigurationError(
                    "Mistral OCR is not available. Please configure MISTRAL_API_KEY."
                )
            
            # Update processing status
            await self._update_processing_status(
                processing_id,
                "processing",
                f"Processing URL OCR for {document_url}"
            )
            
            # Process with Mistral OCR
            ocr_result = await self.mistral_processor.process_url(
                document_url=document_url,
                include_image_base64=include_image_base64,
                **kwargs
            )
            
            # Prepare response
            response = {
                "processing_id": processing_id,
                "source_url": document_url,
                "file_type": ocr_result["metadata"]["document_type"],
                "processor_used": "mistral-ocr",
                "success": ocr_result["success"],
                "processing_time": ocr_result["metadata"]["processing_time"],
                "confidence_score": ocr_result["metadata"]["confidence_score"],
                "processed_at": datetime.now().isoformat(),
                "ocr_results": {
                    "text": ocr_result["text"],
                    "markdown": ocr_result["markdown"],
                    "metadata": ocr_result["metadata"],
                    "images": ocr_result["images"],
                    "tables": ocr_result["tables"],
                    "structure": ocr_result["structure"]
                },
                "statistics": {
                    "character_count": ocr_result["metadata"]["character_count"],
                    "word_count": ocr_result["metadata"]["word_count"],
                    "language": ocr_result["metadata"]["language"],
                    "total_tables": len(ocr_result["tables"]),
                    "total_images": len(ocr_result["images"])
                }
            }
            
            # Update success status
            await self._update_processing_status(
                processing_id,
                "completed",
                "URL OCR processing completed successfully"
            )
            
            # Cache the result
            await cache.set(f"ocr_processing:{processing_id}", response, ttl=3600)
            
            return response
            
        except Exception as e:
            logger.error(f"URL OCR processing failed for {document_url}: {e}")
            error_response = self._create_error_response(
                processing_id, document_url, "processing_error", str(e), start_time
            )
            await self._update_processing_status(processing_id, "failed", str(e))
            return error_response

    async def process_with_structured_annotations(
        self,
        document_data: Union[bytes, BinaryIO],
        filename: str,
        document_type: str = "pdf",
        pages: Optional[List[int]] = None,
        bbox_annotation_schema: Optional[Dict[str, Any]] = None,
        document_annotation_schema: Optional[Dict[str, Any]] = None,
        include_image_base64: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process document with structured annotations using Mistral Document AI.

        Args:
            document_data: Document data as bytes or file-like object
            filename: Original filename
            document_type: Type of document (pdf, image, docx, pptx)
            pages: List of page numbers to process (max 8 for document annotations)
            bbox_annotation_schema: JSON schema for bbox annotations
            document_annotation_schema: JSON schema for document annotations
            include_image_base64: Whether to include image base64 in response
            **kwargs: Additional processing options

        Returns:
            OCR results with structured annotations
        """
        processing_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # Check if OCR is available
            if not self.mistral_processor:
                raise MistralOCRConfigurationError(
                    "Mistral OCR is not available. Please configure MISTRAL_API_KEY."
                )

            # Convert file data to bytes if needed
            if isinstance(document_data, bytes):
                data_bytes = document_data
            else:
                data_bytes = document_data.read()

            # Update processing status
            await self._update_processing_status(
                processing_id,
                "processing",
                f"Processing {filename} with structured annotations"
            )

            # Process with Mistral OCR annotations
            ocr_result = await self.mistral_processor.process_with_annotations(
                document_data=data_bytes,
                document_type=document_type,
                pages=pages,
                bbox_annotation_schema=bbox_annotation_schema,
                document_annotation_schema=document_annotation_schema,
                include_image_base64=include_image_base64,
                **kwargs
            )

            # Prepare response
            response = {
                "processing_id": processing_id,
                "filename": filename,
                "file_type": document_type,
                "processor_used": "mistral-ocr-annotations",
                "success": ocr_result["success"],
                "processing_time": ocr_result["metadata"]["processing_time"],
                "confidence_score": ocr_result["metadata"]["confidence_score"],
                "processed_at": datetime.now().isoformat(),
                "ocr_results": {
                    "text": ocr_result["text"],
                    "markdown": ocr_result["markdown"],
                    "metadata": ocr_result["metadata"],
                    "images": ocr_result["images"],
                    "bbox_annotations": ocr_result["bbox_annotations"],
                    "document_annotation": ocr_result["document_annotation"],
                    "tables": ocr_result["tables"],
                    "structure": ocr_result["structure"]
                },
                "statistics": {
                    "character_count": ocr_result["metadata"]["character_count"],
                    "word_count": ocr_result["metadata"]["word_count"],
                    "language": ocr_result["metadata"]["language"],
                    "pages_processed": ocr_result["metadata"]["pages_processed"],
                    "total_tables": len(ocr_result["tables"]),
                    "total_images": len(ocr_result["images"]),
                    "total_bbox_annotations": len(ocr_result["bbox_annotations"]),
                    "has_document_annotation": bool(ocr_result["document_annotation"])
                },
                "annotation_schemas": {
                    "bbox_schema_provided": bbox_annotation_schema is not None,
                    "document_schema_provided": document_annotation_schema is not None
                }
            }

            # Update success status
            await self._update_processing_status(
                processing_id,
                "completed",
                "Structured annotation processing completed successfully"
            )

            # Cache the result
            await cache.set(f"ocr_processing:{processing_id}", response, ttl=3600)

            return response

        except Exception as e:
            logger.error(f"Structured annotation processing failed for {filename}: {e}")
            error_response = self._create_error_response(
                processing_id, filename, "processing_error", str(e), start_time
            )
            await self._update_processing_status(processing_id, "failed", str(e))
            return error_response

    async def get_processing_status(self, processing_id: str) -> Optional[Dict[str, Any]]:
        """Get OCR processing status."""
        return await cache.get(f"ocr_status:{processing_id}")
    
    async def get_processing_result(self, processing_id: str) -> Optional[Dict[str, Any]]:
        """Get OCR processing result."""
        return await cache.get(f"ocr_processing:{processing_id}")
    
    def is_available(self) -> bool:
        """Check if OCR service is available."""
        return self.mistral_processor is not None
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get OCR service capabilities."""
        return {
            "available": self.is_available(),
            "processors": {
                "mistral-ocr": {
                    "available": self.mistral_processor is not None,
                    "supported_formats": ["pdf", "png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp", "avif"],
                    "max_file_size": self.settings.MISTRAL_OCR_MAX_FILE_SIZE,
                    "timeout": self.settings.MISTRAL_OCR_TIMEOUT,
                    "features": [
                        "high_accuracy_text_extraction",
                        "multi_language_support",
                        "complex_layout_understanding",
                        "table_extraction",
                        "image_classification",
                        "structure_preservation",
                        "bbox_annotations",
                        "document_annotations",
                        "structured_data_extraction",
                        "custom_annotation_schemas"
                    ]
                }
            }
        }
    
    def _detect_image_format(self, filename: str, data_bytes: bytes) -> str:
        """Detect image format from filename and data."""
        # Try filename extension first
        file_extension = Path(filename).suffix.lower().lstrip('.')
        if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'avif']:
            return file_extension if file_extension != 'jpg' else 'jpeg'
        
        # Try to detect from file header
        if data_bytes.startswith(b'\xff\xd8\xff'):
            return 'jpeg'
        elif data_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
        elif data_bytes.startswith(b'GIF87a') or data_bytes.startswith(b'GIF89a'):
            return 'gif'
        elif data_bytes.startswith(b'BM'):
            return 'bmp'
        elif data_bytes.startswith(b'II*\x00') or data_bytes.startswith(b'MM\x00*'):
            return 'tiff'
        
        # Default to jpeg
        return 'jpeg'
    
    def _create_error_response(
        self, 
        processing_id: str, 
        filename: str, 
        error_type: str, 
        error_message: str,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Create error response."""
        return {
            "processing_id": processing_id,
            "filename": filename,
            "success": False,
            "error": error_message,
            "error_type": error_type,
            "processing_time": (datetime.now() - start_time).total_seconds(),
            "processed_at": datetime.now().isoformat()
        }
    
    async def _update_processing_status(
        self, 
        processing_id: str, 
        status: str, 
        message: str
    ):
        """Update processing status in cache."""
        try:
            status_info = {
                "processing_id": processing_id,
                "status": status,
                "message": message,
                "updated_at": datetime.now().isoformat()
            }
            
            await cache.set(f"ocr_status:{processing_id}", status_info, ttl=3600)
            
        except Exception as e:
            logger.error(f"Failed to update OCR processing status: {e}")


# Global service instance
ocr_service = OCRService()


# FastAPI dependency
def get_ocr_service() -> OCRService:
    """FastAPI dependency for OCR service."""
    return ocr_service
