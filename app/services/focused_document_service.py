"""
Focused Document Processing Service

Service layer for the unified document processing pipeline.
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime

from app.core.document_processing.focused_processor import (
    FocusedDocumentProcessor, InputData, ProcessingOptions, ProcessingResult,
    InputType, ProcessingStrategy, QualityThreshold
)

logger = logging.getLogger(__name__)


class FocusedDocumentService:
    """Service for unified document processing."""
    
    def __init__(self):
        self.processor = FocusedDocumentProcessor()
        logger.info("FocusedDocumentService initialized")
    
    async def process_document(
        self,
        document_data: Union[bytes, str],
        document_type: str,
        filename: Optional[str] = None,
        processing_strategy: str = "auto",
        quality_threshold: str = "medium",
        force_ocr: bool = False,
        include_images: bool = False,
        include_tables: bool = True,
        include_metadata: bool = True,
        detect_claims: bool = True,
        segmentation_strategy: str = "paragraph",
        claim_confidence_threshold: float = 0.5,
        timeout_seconds: float = 120.0,
        bypass_cache: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a document using the unified processing pipeline.
        
        Args:
            document_data: Document data (bytes for files, string for text/URLs)
            document_type: Type of document (pdf, doc, docx, txt, url, text, image)
            filename: Original filename (optional)
            processing_strategy: Strategy to use (auto, docling_only, ocr_only, hybrid, url_extraction, text_analysis)
            quality_threshold: Quality threshold (low, medium, high, strict)
            force_ocr: Force OCR processing even for text-based documents
            include_images: Include image extraction
            include_tables: Include table extraction
            include_metadata: Include metadata extraction
            detect_claims: Detect potential factual claims
            segmentation_strategy: Text segmentation strategy
            claim_confidence_threshold: Minimum confidence for claims
            timeout_seconds: Processing timeout
            bypass_cache: Bypass cache lookup
            **kwargs: Additional options
            
        Returns:
            Dictionary with processing results
        """
        processing_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Validate and convert input type
            try:
                input_type = InputType(document_type.lower())
            except ValueError:
                raise ValueError(f"Unsupported document type: {document_type}")
            
            # Validate and convert processing strategy
            try:
                strategy = ProcessingStrategy(processing_strategy.lower())
            except ValueError:
                strategy = ProcessingStrategy.AUTO
                logger.warning(f"Invalid strategy '{processing_strategy}', using auto")
            
            # Validate and convert quality threshold
            try:
                quality = QualityThreshold(quality_threshold.lower())
            except ValueError:
                quality = QualityThreshold.MEDIUM
                logger.warning(f"Invalid quality threshold '{quality_threshold}', using medium")
            
            # Create input data
            input_data = InputData(
                type=input_type,
                data=document_data,
                filename=filename,
                metadata=kwargs.get('metadata', {})
            )
            
            # Create processing options
            options = ProcessingOptions(
                strategy=strategy,
                quality_threshold=quality,
                force_ocr=force_ocr,
                include_images=include_images,
                include_tables=include_tables,
                include_metadata=include_metadata,
                bypass_cache=bypass_cache,
                timeout_seconds=timeout_seconds,
                detect_claims=detect_claims,
                segmentation_strategy=segmentation_strategy,
                claim_confidence_threshold=claim_confidence_threshold,
                **{k: v for k, v in kwargs.items() if k not in ['metadata']}
            )
            
            # Process document
            result = await asyncio.wait_for(
                self.processor.process_input(input_data, options),
                timeout=timeout_seconds
            )
            
            # Convert to API response format
            response = self._convert_to_api_response(result, processing_id, start_time)
            
            logger.info(f"Document processing completed successfully for {processing_id}")
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Document processing timed out for {processing_id}")
            return self._create_error_response(
                processing_id, "timeout_error", 
                f"Processing timed out after {timeout_seconds}s", start_time
            )
        except Exception as e:
            logger.error(f"Document processing failed for {processing_id}: {e}")
            return self._create_error_response(
                processing_id, "processing_error", str(e), start_time
            )
    
    async def process_url(
        self,
        url: str,
        processing_strategy: str = "url_extraction",
        quality_threshold: str = "medium",
        include_metadata: bool = True,
        detect_claims: bool = True,
        timeout_seconds: float = 60.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a URL using content extraction.
        
        Args:
            url: URL to process
            processing_strategy: Strategy to use
            quality_threshold: Quality threshold
            include_metadata: Include metadata extraction
            detect_claims: Detect potential claims
            timeout_seconds: Processing timeout
            **kwargs: Additional options
            
        Returns:
            Dictionary with processing results
        """
        return await self.process_document(
            document_data=url,
            document_type="url",
            filename=None,
            processing_strategy=processing_strategy,
            quality_threshold=quality_threshold,
            include_metadata=include_metadata,
            detect_claims=detect_claims,
            timeout_seconds=timeout_seconds,
            **kwargs
        )
    
    async def process_text(
        self,
        text: str,
        processing_strategy: str = "text_analysis",
        quality_threshold: str = "medium",
        detect_claims: bool = True,
        segmentation_strategy: str = "paragraph",
        claim_confidence_threshold: float = 0.5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process direct text input.
        
        Args:
            text: Text content to process
            processing_strategy: Strategy to use
            quality_threshold: Quality threshold
            detect_claims: Detect potential claims
            segmentation_strategy: Text segmentation strategy
            claim_confidence_threshold: Minimum confidence for claims
            **kwargs: Additional options
            
        Returns:
            Dictionary with processing results
        """
        return await self.process_document(
            document_data=text,
            document_type="text",
            filename=None,
            processing_strategy=processing_strategy,
            quality_threshold=quality_threshold,
            detect_claims=detect_claims,
            segmentation_strategy=segmentation_strategy,
            claim_confidence_threshold=claim_confidence_threshold,
            **kwargs
        )
    
    async def get_processing_capabilities(self) -> Dict[str, Any]:
        """Get information about processing capabilities."""
        try:
            # Initialize processors to get accurate capability info
            await self.processor.initialize_processors()
            
            stats = self.processor.get_processing_statistics()
            
            return {
                "success": True,
                "capabilities": {
                    "supported_input_types": [t.value for t in InputType],
                    "supported_strategies": [s.value for s in ProcessingStrategy],
                    "quality_thresholds": [q.value for q in QualityThreshold],
                    "available_processors": stats["available_processors"],
                    "features": {
                        "hybrid_processing": True,
                        "claim_detection": True,
                        "text_segmentation": True,
                        "quality_assessment": True,
                        "caching": True,
                        "metadata_extraction": True,
                        "table_extraction": True,
                        "image_extraction": True,
                        "language_detection": True,
                        "structure_analysis": True
                    },
                    "limits": {
                        "max_file_size": "50MB",
                        "max_timeout": "600s",
                        "supported_formats": [
                            "PDF", "DOC", "DOCX", "TXT", "URLs", "Plain Text", "Images"
                        ]
                    }
                },
                "statistics": stats,
                "service_info": {
                    "name": "Focused Document Processing Service",
                    "version": "1.0.0",
                    "description": "Unified document processing pipeline with intelligent routing"
                }
            }
        except Exception as e:
            logger.error(f"Failed to get capabilities: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "capability_error"
            }
    
    def _convert_to_api_response(
        self, 
        result: ProcessingResult, 
        processing_id: str, 
        start_time: datetime
    ) -> Dict[str, Any]:
        """Convert ProcessingResult to API response format."""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": result.success,
            "processing_id": processing_id,
            "input_type": result.input_type.value,
            "processing_strategy": result.processing_strategy.value,
            "processing_time": processing_time,
            "processed_at": result.processed_at.isoformat(),
            "cache_hit": result.cache_hit,
            "content": {
                "text": result.text,
                "markdown": result.markdown,
                "structured_content": result.structured_content,
                "language": result.language,
                "word_count": result.processing_stats.word_count,
                "character_count": result.processing_stats.character_count
            },
            "extracted_elements": {
                "tables": result.tables,
                "images": result.images,
                "links": result.links
            },
            "analysis": {
                "segments": result.segments,
                "potential_claims": result.potential_claims,
                "claim_count": result.processing_stats.claim_count
            },
            "metadata": result.metadata,
            "processing_stats": result.processing_stats.dict(),
            "warnings": result.warnings,
            "errors": result.errors
        }
    
    def _create_error_response(
        self, 
        processing_id: str, 
        error_type: str, 
        error_message: str, 
        start_time: datetime
    ) -> Dict[str, Any]:
        """Create standardized error response."""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": False,
            "processing_id": processing_id,
            "error": error_message,
            "error_type": error_type,
            "processing_time": processing_time,
            "processed_at": datetime.now().isoformat()
        }
