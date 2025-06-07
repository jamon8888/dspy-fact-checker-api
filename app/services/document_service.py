"""
Document processing service for the DSPy-Enhanced Fact-Checker API Platform.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime
import uuid
import os
from pathlib import Path

from app.core.document_processing import (
    DocumentProcessor, ProcessingResult, DocumentType,
    ProcessingError, UnsupportedFormatError, DOCLING_AVAILABLE
)

# Import DoclingProcessor conditionally
if DOCLING_AVAILABLE:
    from app.core.document_processing import DoclingProcessor
    # Import Enhanced Docling Processor
    try:
        from app.core.document_processing.enhanced_docling_processor import EnhancedDoclingProcessor
        ENHANCED_DOCLING_AVAILABLE = True
    except ImportError:
        EnhancedDoclingProcessor = None
        ENHANCED_DOCLING_AVAILABLE = False
else:
    DoclingProcessor = None
    EnhancedDoclingProcessor = None
    ENHANCED_DOCLING_AVAILABLE = False
from app.core.document_processing.base import processor_registry
from app.core.document_processing.fallback_processor import FallbackProcessor
from app.core.config import get_settings
from app.core.redis import cache
from app.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """Service for processing documents with multiple processors."""
    
    def __init__(self):
        """Initialize document processing service."""
        self.settings = get_settings()
        self._initialize_processors()
    
    def _initialize_processors(self):
        """Initialize and register document processors."""
        try:
            # Try to use Enhanced Docling Processor first
            if ENHANCED_DOCLING_AVAILABLE and EnhancedDoclingProcessor:
                # Enhanced Docling configuration with advanced features and OCR integration
                enhanced_config = {
                    "max_file_size": self.settings.MAX_FILE_SIZE,
                    "timeout_seconds": self.settings.PROCESSING_TIMEOUT,
                    "max_pages": self.settings.DOCLING_MAX_PAGES,
                    # Advanced features
                    "enable_ocr": True,
                    "enable_table_structure": True,
                    "enable_picture_extraction": True,
                    "enable_formula_detection": True,
                    "enable_code_detection": True,
                    "enable_chunking": True,
                    "table_mode": "accurate",
                    "ocr_language": ["en"],
                    "chunk_max_tokens": 512,
                    "cpu_threads": 4,
                    # OCR Engine Configuration - Mistral API Primary with Local Fallback
                    "primary_ocr_engine": "mistral",
                    "fallback_ocr_engines": ["tesseract", "rapidocr"],
                    "enable_ocr_fallback": True,
                    "ocr_quality_threshold": 0.7,
                    "local_ocr_priority": False,  # Prefer cloud API first
                    "cost_optimization": True,
                    "budget_per_document": 0.10,  # 10 cents per document
                    "mistral_api_key": os.getenv("MISTRAL_API_KEY"),
                    "mistral_model": "mistral-ocr-latest",  # Correct Mistral OCR model (working)
                    "mistral_api_endpoint": "https://api.mistral.ai/v1/ocr"  # Correct OCR endpoint
                }

                enhanced_processor = EnhancedDoclingProcessor(enhanced_config)
                processor_registry.register("enhanced_docling", enhanced_processor)
                processor_registry.register("docling", enhanced_processor)  # Default to enhanced
                logger.info("Enhanced Docling processor initialized successfully with advanced features")

            elif DOCLING_AVAILABLE and DoclingProcessor:
                # Fallback to basic Docling processor
                docling_config = {
                    "max_file_size": self.settings.MAX_FILE_SIZE,
                    "timeout_seconds": self.settings.PROCESSING_TIMEOUT,
                    "extract_images": self.settings.DOCLING_EXTRACT_IMAGES,
                    "extract_tables": self.settings.DOCLING_EXTRACT_TABLES,
                    "max_pages": self.settings.DOCLING_MAX_PAGES,
                    "do_ocr": False  # We'll use Mistral OCR separately
                }

                docling_processor = DoclingProcessor(docling_config)
                processor_registry.register("docling", docling_processor)
                logger.info("Basic Docling processor initialized successfully")
            else:
                logger.warning("Docling processors not available - using fallback processors")

            # Always register fallback processor as last resort
            fallback_config = {
                "max_file_size": self.settings.MAX_FILE_SIZE,
                "timeout_seconds": self.settings.PROCESSING_TIMEOUT
            }

            fallback_processor = FallbackProcessor(fallback_config)
            processor_registry.register("fallback", fallback_processor)
            logger.info("Fallback processor registered for unsupported formats")

            logger.info("Document processors initialization completed")

        except Exception as e:
            logger.error(f"Failed to initialize document processors: {e}")
    
    async def process_document(
        self,
        file_data: Union[bytes, BinaryIO],
        filename: str,
        processor_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a document and return structured results.
        
        Args:
            file_data: Document data
            filename: Original filename
            processor_name: Specific processor to use (optional)
            **kwargs: Additional processing options
            
        Returns:
            Processing results with content, metadata, and extracted elements
        """
        processing_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Determine document type from filename
            file_type = self._get_document_type(filename)
            
            # Get processor
            if processor_name:
                processor = processor_registry.get_processor(processor_name)
                if not processor:
                    raise ProcessingError(f"Processor '{processor_name}' not found")
            else:
                processor = processor_registry.get_best_processor(file_type)
                if not processor:
                    # Try OCR as fallback for images and PDFs
                    if file_type in [DocumentType.PDF] and ocr_service.is_available():
                        return await self._process_with_ocr_fallback(
                            file_data, filename, file_type, **kwargs
                        )
                    else:
                        # Use fallback processor as last resort
                        processor = processor_registry.get_processor("fallback")
                        if not processor:
                            raise UnsupportedFormatError(
                                file_type.value,
                                [fmt.value for fmt in DocumentType]
                            )
            
            # Update processing status
            await self._update_processing_status(
                processing_id, 
                "processing", 
                f"Processing {filename} with {processor.__class__.__name__}"
            )
            
            # Process document
            result = await processor.process_document(
                file_data=file_data,
                file_type=file_type,
                filename=filename,
                **kwargs
            )
            
            # Prepare response
            response = {
                "processing_id": processing_id,
                "filename": filename,
                "file_type": file_type.value,
                "processor_used": processor.__class__.__name__,
                "success": result.success,
                "processing_time": result.processing_time,
                "confidence_score": result.confidence_score,
                "processed_at": datetime.now().isoformat()
            }
            
            if result.success:
                response.update({
                    "content": {
                        "text": result.content.text if result.content else "",
                        "paragraphs": result.content.paragraphs if result.content else [],
                        "headings": result.content.headings if result.content else [],
                        "lists": result.content.lists if result.content else [],
                        "reading_order": result.content.reading_order if result.content else []
                    },
                    "metadata": {
                        "title": result.metadata.title if result.metadata else None,
                        "author": result.metadata.author if result.metadata else None,
                        "creation_date": result.metadata.creation_date.isoformat() if result.metadata and result.metadata.creation_date else None,
                        "page_count": result.metadata.page_count if result.metadata else None,
                        "word_count": result.metadata.word_count if result.metadata else None,
                        "character_count": result.metadata.character_count if result.metadata else None,
                        "language": result.metadata.language if result.metadata else None
                    },
                    "tables": [
                        {
                            "table_id": table.table_id,
                            "caption": table.caption,
                            "headers": table.headers,
                            "rows": table.rows,
                            "confidence": table.confidence
                        }
                        for table in result.tables
                    ],
                    "images": [
                        {
                            "image_id": image.image_id,
                            "caption": image.caption,
                            "alt_text": image.alt_text,
                            "dimensions": image.dimensions,
                            "classification": image.classification,
                            "confidence": image.confidence
                        }
                        for image in result.images
                    ],
                    "warnings": result.warnings,
                    "statistics": {
                        "total_tables": len(result.tables),
                        "total_images": len(result.images),
                        "total_paragraphs": len(result.content.paragraphs) if result.content else 0,
                        "total_headings": len(result.content.headings) if result.content else 0
                    }
                })
                
                # Update success status
                await self._update_processing_status(
                    processing_id, 
                    "completed", 
                    "Document processing completed successfully"
                )
            else:
                response.update({
                    "errors": result.errors,
                    "warnings": result.warnings
                })
                
                # Update error status
                await self._update_processing_status(
                    processing_id, 
                    "failed", 
                    f"Document processing failed: {'; '.join(result.errors)}"
                )
            
            # Cache the result
            await cache.set(f"document_processing:{processing_id}", response, ttl=3600)
            
            return response
            
        except Exception as e:
            logger.error(f"Document processing failed for {filename}: {e}")
            
            error_response = {
                "processing_id": processing_id,
                "filename": filename,
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "processed_at": datetime.now().isoformat()
            }
            
            # Update error status
            await self._update_processing_status(
                processing_id, 
                "failed", 
                f"Processing failed: {str(e)}"
            )
            
            return error_response
    
    async def get_processing_status(self, processing_id: str) -> Optional[Dict[str, Any]]:
        """Get processing status for a document."""
        return await cache.get(f"processing_status:{processing_id}")
    
    async def get_processing_result(self, processing_id: str) -> Optional[Dict[str, Any]]:
        """Get processing result for a document."""
        return await cache.get(f"document_processing:{processing_id}")
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported document formats."""
        formats = set()
        for processor_name in processor_registry.list_processors():
            processor = processor_registry.get_processor(processor_name)
            if processor:
                formats.update(fmt.value for fmt in processor.get_supported_formats())
        return sorted(list(formats))
    
    def get_available_processors(self) -> List[Dict[str, Any]]:
        """Get list of available processors and their capabilities."""
        processors = []
        for processor_name in processor_registry.list_processors():
            processor = processor_registry.get_processor(processor_name)
            if processor:
                processors.append({
                    "name": processor_name,
                    "class": processor.__class__.__name__,
                    "supported_formats": [fmt.value for fmt in processor.get_supported_formats()],
                    "description": processor.__class__.__doc__ or "No description available"
                })
        return processors
    
    def _get_document_type(self, filename: str) -> DocumentType:
        """Determine document type from filename."""
        file_extension = Path(filename).suffix.lower().lstrip('.')
        
        type_mapping = {
            'pdf': DocumentType.PDF,
            'docx': DocumentType.DOCX,
            'doc': DocumentType.DOC,
            'txt': DocumentType.TXT,
            'html': DocumentType.HTML,
            'htm': DocumentType.HTML,
            'rtf': DocumentType.RTF,
            'odt': DocumentType.ODT,
            # Image formats for OCR processing
            'png': DocumentType.IMAGE,
            'jpg': DocumentType.IMAGE,
            'jpeg': DocumentType.IMAGE,
            'gif': DocumentType.IMAGE,
            'bmp': DocumentType.IMAGE,
            'tiff': DocumentType.IMAGE,
            'tif': DocumentType.IMAGE,
            'webp': DocumentType.IMAGE
        }
        
        if file_extension not in type_mapping:
            raise UnsupportedFormatError(
                file_extension,
                list(type_mapping.keys())
            )
        
        return type_mapping[file_extension]
    
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
            
            await cache.set(f"processing_status:{processing_id}", status_info, ttl=3600)
            
        except Exception as e:
            logger.error(f"Failed to update processing status: {e}")

    async def _process_with_ocr_fallback(
        self,
        file_data: Union[bytes, BinaryIO],
        filename: str,
        file_type: DocumentType,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process document using OCR as fallback when no document processor is available.

        Args:
            file_data: Document data
            filename: Original filename
            file_type: Document type
            **kwargs: Additional processing options

        Returns:
            Processing results using OCR
        """
        processing_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            logger.info(f"Using OCR fallback for {filename} (type: {file_type.value})")

            # Convert file data to bytes if needed
            if isinstance(file_data, bytes):
                data_bytes = file_data
            else:
                data_bytes = file_data.read()

            # Update processing status
            await self._update_processing_status(
                processing_id,
                "processing",
                f"Processing {filename} with OCR fallback"
            )

            # Process with OCR based on file type
            if file_type == DocumentType.PDF:
                ocr_result = await ocr_service.process_pdf_ocr(
                    pdf_data=data_bytes,
                    filename=filename,
                    **kwargs
                )
            else:
                # For other types, try as image
                ocr_result = await ocr_service.process_image_ocr(
                    image_data=data_bytes,
                    filename=filename,
                    **kwargs
                )

            if ocr_result["success"]:
                # Convert OCR result to document processing format
                response = {
                    "processing_id": processing_id,
                    "filename": filename,
                    "file_type": file_type.value,
                    "processor_used": "mistral-ocr-fallback",
                    "success": True,
                    "processing_time": ocr_result["processing_time"],
                    "confidence_score": ocr_result["confidence_score"],
                    "processed_at": datetime.now().isoformat(),
                    "content": {
                        "text": ocr_result["ocr_results"]["text"],
                        "paragraphs": [],  # OCR doesn't provide paragraph structure
                        "headings": [],    # OCR doesn't provide heading structure
                        "lists": [],       # OCR doesn't provide list structure
                        "reading_order": []
                    },
                    "metadata": {
                        "title": None,
                        "author": None,
                        "creation_date": None,
                        "page_count": ocr_result["statistics"].get("estimated_pages"),
                        "word_count": ocr_result["statistics"]["word_count"],
                        "character_count": ocr_result["statistics"]["character_count"],
                        "language": ocr_result["statistics"]["language"]
                    },
                    "tables": ocr_result["ocr_results"]["tables"],
                    "images": ocr_result["ocr_results"]["images"],
                    "warnings": ["Processed using OCR fallback - structure may be limited"],
                    "statistics": {
                        "total_tables": ocr_result["statistics"]["total_tables"],
                        "total_images": ocr_result["statistics"]["total_images"],
                        "total_paragraphs": 0,
                        "total_headings": 0
                    }
                }

                # Update success status
                await self._update_processing_status(
                    processing_id,
                    "completed",
                    "OCR fallback processing completed successfully"
                )

                # Cache the result
                await cache.set(f"document_processing:{processing_id}", response, ttl=3600)

                return response
            else:
                raise ProcessingError(f"OCR fallback failed: {ocr_result.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"OCR fallback processing failed for {filename}: {e}")

            error_response = {
                "processing_id": processing_id,
                "filename": filename,
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "processed_at": datetime.now().isoformat()
            }

            # Update error status
            await self._update_processing_status(
                processing_id,
                "failed",
                f"OCR fallback processing failed: {str(e)}"
            )

            return error_response


# Global service instance
document_service = DocumentProcessingService()


# FastAPI dependency
def get_document_service() -> DocumentProcessingService:
    """FastAPI dependency for document service."""
    return document_service
