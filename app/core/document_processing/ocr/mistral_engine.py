#!/usr/bin/env python3
"""
Mistral OCR Engine Implementation
Integrates Mistral Document AI API as an OCR engine for the enhanced Docling processor
"""

import logging
import asyncio
import base64
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.document_processing.ocr.base import (
    OCREngineInterface, OCRResult, OCREngineInfo, OCREngineType, OCRQualityMetrics
)

logger = logging.getLogger(__name__)

# Import Mistral AI components
try:
    from mistralai import Mistral
    from mistralai.models import ImageURLChunk, DocumentURLChunk
    MISTRAL_AVAILABLE = True
except ImportError:
    logger.warning("Mistral AI not available - install mistralai>=1.0.0")
    Mistral = None
    ImageURLChunk = None
    DocumentURLChunk = None
    MISTRAL_AVAILABLE = False


class MistralOCREngineError(Exception):
    """Base exception for Mistral OCR engine errors."""
    pass


class MistralOCRConfigurationError(MistralOCREngineError):
    """Configuration error for Mistral OCR engine."""
    pass


class MistralOCRProcessingError(MistralOCREngineError):
    """Processing error for Mistral OCR engine."""
    pass


class MistralOCREngine(OCREngineInterface):
    """Mistral OCR engine implementation using Mistral Document AI API."""
    
    def __init__(
        self, 
        api_key: str,
        model: str = "mistral-ocr-latest",
        timeout_seconds: int = 300,
        max_file_size: int = 50 * 1024 * 1024  # 50MB
    ):
        """
        Initialize Mistral OCR engine.
        
        Args:
            api_key: Mistral API key
            model: Mistral OCR model to use
            timeout_seconds: Processing timeout
            max_file_size: Maximum file size in bytes
        """
        if not MISTRAL_AVAILABLE:
            raise MistralOCRConfigurationError(
                "Mistral AI is not available. Please install mistralai>=1.0.0"
            )
        
        if not api_key:
            raise MistralOCRConfigurationError(
                "Mistral API key is required"
            )
        
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_file_size = max_file_size
        
        # Initialize Mistral client
        self.client = Mistral(api_key=api_key)
        
        # Cost estimation (example values - adjust based on actual Mistral pricing)
        self.cost_per_page = 0.01  # $0.01 per page
        
        logger.info(f"Mistral OCR engine initialized with model: {model}")
    
    async def process_image(
        self, 
        image_data: bytes, 
        language: str = "en",
        **kwargs
    ) -> OCRResult:
        """
        Process an image with Mistral OCR.
        
        Args:
            image_data: Image data as bytes
            language: Language code for OCR
            **kwargs: Additional options
            
        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = time.time()
        
        try:
            # Validate input
            if len(image_data) > self.max_file_size:
                raise MistralOCRProcessingError(
                    f"Image size ({len(image_data)} bytes) exceeds maximum ({self.max_file_size} bytes)"
                )
            
            # Convert to base64 for Mistral API
            base64_image = base64.b64encode(image_data).decode('utf-8')
            image_url = f"data:image/jpeg;base64,{base64_image}"
            
            # Process with Mistral OCR
            response = await asyncio.wait_for(
                self._call_mistral_ocr(
                    document_type="image_url",
                    document_url=image_url,
                    language=language,
                    **kwargs
                ),
                timeout=self.timeout_seconds
            )
            
            processing_time = time.time() - start_time
            
            # Extract text and metadata
            text = response.get("markdown", "")
            confidence = self._calculate_confidence(response)
            
            # Create quality metrics
            quality_metrics = OCRQualityMetrics(
                overall_confidence=confidence,
                text_confidence=confidence,
                language_confidence=0.95,  # Mistral has good language detection
                structure_preservation=0.9,  # Mistral preserves structure well
                word_count=len(text.split()) if text else 0,
                character_count=len(text) if text else 0,
                detected_language=language,
                processing_time=processing_time
            )
            
            return OCRResult(
                text=text,
                confidence=confidence,
                language=language,
                processing_time=processing_time,
                engine_used="mistral",
                metadata={
                    "model": self.model,
                    "api_response_size": len(str(response)),
                    "has_bbox_annotations": bool(response.get("bbox_annotations")),
                    "has_images": bool(response.get("images"))
                },
                bbox_annotations=response.get("bbox_annotations", []),
                quality_metrics=quality_metrics,
                cost_estimate=self.cost_per_page
            )
            
        except asyncio.TimeoutError:
            raise MistralOCRProcessingError(
                f"OCR processing timed out after {self.timeout_seconds}s"
            )
        except Exception as e:
            logger.error(f"Mistral image OCR failed: {e}")
            raise MistralOCRProcessingError(f"Failed to process image: {str(e)}")
    
    async def process_pdf_page(
        self, 
        pdf_page: bytes, 
        page_number: int = 1,
        language: str = "en",
        **kwargs
    ) -> OCRResult:
        """
        Process a PDF page with Mistral OCR.
        
        Args:
            pdf_page: PDF page data as bytes
            page_number: Page number for reference
            language: Language code for OCR
            **kwargs: Additional options
            
        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = time.time()
        
        try:
            # Validate input
            if len(pdf_page) > self.max_file_size:
                raise MistralOCRProcessingError(
                    f"PDF page size ({len(pdf_page)} bytes) exceeds maximum ({self.max_file_size} bytes)"
                )
            
            # Convert to base64 for Mistral API
            base64_pdf = base64.b64encode(pdf_page).decode('utf-8')
            document_url = f"data:application/pdf;base64,{base64_pdf}"
            
            # Process with Mistral OCR
            response = await asyncio.wait_for(
                self._call_mistral_ocr(
                    document_type="document_url",
                    document_url=document_url,
                    language=language,
                    pages=[page_number] if page_number else None,
                    **kwargs
                ),
                timeout=self.timeout_seconds
            )
            
            processing_time = time.time() - start_time
            
            # Extract text and metadata
            text = response.get("markdown", "")
            confidence = self._calculate_confidence(response)
            
            # Create quality metrics
            quality_metrics = OCRQualityMetrics(
                overall_confidence=confidence,
                text_confidence=confidence,
                language_confidence=0.95,
                structure_preservation=0.9,
                word_count=len(text.split()) if text else 0,
                character_count=len(text) if text else 0,
                detected_language=language,
                processing_time=processing_time
            )
            
            return OCRResult(
                text=text,
                confidence=confidence,
                language=language,
                processing_time=processing_time,
                engine_used="mistral",
                metadata={
                    "model": self.model,
                    "page_number": page_number,
                    "api_response_size": len(str(response)),
                    "has_bbox_annotations": bool(response.get("bbox_annotations")),
                    "has_tables": bool(response.get("tables"))
                },
                bbox_annotations=response.get("bbox_annotations", []),
                quality_metrics=quality_metrics,
                cost_estimate=self.cost_per_page
            )
            
        except asyncio.TimeoutError:
            raise MistralOCRProcessingError(
                f"OCR processing timed out after {self.timeout_seconds}s"
            )
        except Exception as e:
            logger.error(f"Mistral PDF OCR failed: {e}")
            raise MistralOCRProcessingError(f"Failed to process PDF page: {str(e)}")
    
    def supports_language(self, language: str) -> bool:
        """Check if Mistral OCR supports a specific language."""
        # Mistral OCR supports many languages
        supported_languages = [
            "en", "fr", "de", "es", "it", "pt", "nl", "ru", "zh", "ja", "ko", "ar"
        ]
        return language.lower() in supported_languages
    
    def get_engine_info(self) -> OCREngineInfo:
        """Get information about the Mistral OCR engine."""
        return OCREngineInfo(
            name="Mistral OCR",
            type=OCREngineType.CLOUD,
            supported_languages=[
                "en", "fr", "de", "es", "it", "pt", "nl", "ru", "zh", "ja", "ko", "ar"
            ],
            max_file_size=self.max_file_size,
            cost_per_page=self.cost_per_page,
            requires_api_key=True,
            offline_capable=False,
            supports_bbox=True,
            supports_tables=True,
            supports_handwriting=True,
            quality_rating=0.95  # High quality rating for Mistral
        )
    
    def is_available(self) -> bool:
        """Check if Mistral OCR engine is available."""
        return MISTRAL_AVAILABLE and self.client is not None
    
    async def _call_mistral_ocr(
        self,
        document_type: str,
        document_url: str,
        language: str = "en",
        pages: Optional[List[int]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call Mistral OCR API.
        
        Args:
            document_type: Type of document ("image_url" or "document_url")
            document_url: Base64 encoded document URL
            language: Language code
            pages: Specific pages to process
            **kwargs: Additional API parameters
            
        Returns:
            API response as dictionary
        """
        try:
            # Prepare document chunk
            if document_type == "image_url":
                if ImageURLChunk:
                    document_chunk = ImageURLChunk(image_url=document_url)
                else:
                    document_chunk = {"type": "image_url", "image_url": document_url}
            else:
                if DocumentURLChunk:
                    document_chunk = DocumentURLChunk(document_url=document_url)
                else:
                    document_chunk = {"type": "document_url", "document_url": document_url}
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "document": document_chunk,
                "include_image_base64": kwargs.get("include_image_base64", False)
            }
            
            # Add optional parameters
            if pages is not None:
                request_params["pages"] = pages
            
            if kwargs.get("bbox_annotation_format"):
                request_params["bbox_annotation_format"] = kwargs["bbox_annotation_format"]
            
            if kwargs.get("document_annotation_format"):
                request_params["document_annotation_format"] = kwargs["document_annotation_format"]
            
            # Make the API call
            response = await asyncio.to_thread(
                self.client.ocr.process,
                **request_params
            )
            
            # Convert response to dictionary
            if hasattr(response, 'model_dump'):
                return response.model_dump()
            elif hasattr(response, 'dict'):
                return response.dict()
            else:
                return dict(response)
                
        except Exception as e:
            logger.error(f"Mistral OCR API call failed: {e}")
            raise MistralOCRProcessingError(f"API call failed: {str(e)}")
    
    def _calculate_confidence(self, response: Dict[str, Any]) -> float:
        """
        Calculate confidence score from Mistral OCR response.
        
        Args:
            response: Mistral OCR API response
            
        Returns:
            Confidence score from 0.0 to 1.0
        """
        # Mistral doesn't provide explicit confidence scores
        # We estimate based on response quality indicators
        
        text = response.get("markdown", "")
        bbox_annotations = response.get("bbox_annotations", [])
        
        # Base confidence
        confidence = 0.8
        
        # Increase confidence if we have bbox annotations
        if bbox_annotations:
            confidence += 0.1
        
        # Increase confidence based on text length (more text usually means better OCR)
        if len(text) > 100:
            confidence += 0.05
        elif len(text) < 10:
            confidence -= 0.2
        
        # Decrease confidence if text has many special characters (OCR artifacts)
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1)
        if special_char_ratio > 0.3:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
