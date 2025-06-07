"""
Content Extraction Service

Service layer for URL content extraction and text processing operations.
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from app.core.content_extraction import (
    URLContentExtractor, AdvancedTextProcessor,
    ExtractionOptions, TextProcessingOptions,
    ExtractedWebContent, ProcessedTextContent,
    ExtractionStrategy, SegmentationStrategy,
    ContentExtractionError, URLExtractionError, TextProcessingError
)
from app.core.redis import cache

logger = logging.getLogger(__name__)


class ContentExtractionService:
    """Service for URL content extraction and text processing."""
    
    def __init__(self):
        self.url_extractor = URLContentExtractor()
        self.text_processor = AdvancedTextProcessor()
        logger.info("ContentExtractionService initialized")
    
    async def extract_url_content(
        self,
        url: str,
        extraction_strategy: str = "auto",
        timeout_seconds: float = 30.0,
        quality_threshold: float = 0.3,
        include_metadata: bool = True,
        include_images: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract content from a URL.
        
        Args:
            url: URL to extract content from
            extraction_strategy: Strategy to use (auto, newspaper, readability, trafilatura, custom)
            timeout_seconds: Timeout for extraction
            quality_threshold: Minimum quality threshold
            include_metadata: Whether to include metadata
            include_images: Whether to include images
            **kwargs: Additional options
            
        Returns:
            Dictionary with extraction results
        """
        extraction_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Validate strategy
            try:
                strategy = ExtractionStrategy(extraction_strategy)
            except ValueError:
                strategy = ExtractionStrategy.AUTO
                logger.warning(f"Invalid strategy '{extraction_strategy}', using auto")
            
            # Create extraction options
            options = ExtractionOptions(
                strategy=strategy,
                timeout_seconds=timeout_seconds,
                quality_threshold=quality_threshold,
                include_metadata=include_metadata,
                include_images=include_images,
                **kwargs
            )
            
            # Check cache first
            cache_key = f"url_extraction:{hash(url + str(options.dict()))}"
            cached_result = await cache.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached result for URL: {url}")
                return cached_result
            
            # Extract content
            extracted_content = await self.url_extractor.extract_content(url, options)
            
            # Prepare response
            response = {
                "extraction_id": extraction_id,
                "url": url,
                "success": True,
                "extraction_method": extracted_content.extraction_method.value,
                "content_type": extracted_content.content_type.value,
                "quality_score": extracted_content.quality_score,
                "processing_time": extracted_content.processing_time,
                "extracted_at": extracted_content.extraction_timestamp.isoformat(),
                "content": {
                    "title": extracted_content.title,
                    "text": extracted_content.content,
                    "author": extracted_content.author,
                    "publish_date": extracted_content.publish_date.isoformat() if extracted_content.publish_date else None,
                    "language": extracted_content.language.dict() if extracted_content.language else None,
                    "word_count": len(extracted_content.content.split()),
                    "character_count": len(extracted_content.content)
                },
                "metadata": extracted_content.metadata,
                "images": extracted_content.images if include_images else [],
                "links": extracted_content.links
            }
            
            # Cache the result
            await cache.set(cache_key, response, ttl=3600)  # Cache for 1 hour
            
            logger.info(f"Successfully extracted content from {url} "
                       f"(quality: {extracted_content.quality_score:.2f}, "
                       f"method: {extracted_content.extraction_method.value})")
            
            return response
            
        except URLExtractionError as e:
            logger.error(f"URL extraction failed for {url}: {e}")
            return self._create_error_response(
                extraction_id, url, "url_extraction_error", str(e), start_time
            )
        except Exception as e:
            logger.error(f"Unexpected error extracting content from {url}: {e}")
            return self._create_error_response(
                extraction_id, url, "unexpected_error", str(e), start_time
            )
    
    async def process_text_content(
        self,
        text: str,
        segmentation_strategy: str = "paragraph",
        detect_language: bool = True,
        detect_claims: bool = True,
        analyze_structure: bool = True,
        claim_confidence_threshold: float = 0.5,
        min_segment_length: int = 50,
        max_segment_length: int = 5000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process text content with comprehensive analysis.
        
        Args:
            text: Text content to process
            segmentation_strategy: Strategy for text segmentation
            detect_language: Whether to detect language
            detect_claims: Whether to detect potential claims
            analyze_structure: Whether to analyze text structure
            claim_confidence_threshold: Minimum confidence for claims
            min_segment_length: Minimum segment length
            max_segment_length: Maximum segment length
            **kwargs: Additional options
            
        Returns:
            Dictionary with processing results
        """
        processing_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Validate segmentation strategy
            try:
                strategy = SegmentationStrategy(segmentation_strategy)
            except ValueError:
                strategy = SegmentationStrategy.PARAGRAPH
                logger.warning(f"Invalid segmentation strategy '{segmentation_strategy}', using paragraph")
            
            # Create processing options
            options = TextProcessingOptions(
                segmentation_strategy=strategy,
                detect_language=detect_language,
                detect_claims=detect_claims,
                analyze_structure=analyze_structure,
                claim_confidence_threshold=claim_confidence_threshold,
                min_segment_length=min_segment_length,
                max_segment_length=max_segment_length,
                **kwargs
            )
            
            # Check cache first
            cache_key = f"text_processing:{hash(text[:1000] + str(options.dict()))}"
            cached_result = await cache.get(cache_key)
            if cached_result:
                logger.info("Returning cached text processing result")
                return cached_result
            
            # Process text
            processed_content = await self.text_processor.process_text(text, options)
            
            # Prepare response
            response = {
                "processing_id": processing_id,
                "success": True,
                "processing_time": processed_content.processing_time,
                "processed_at": processed_content.processing_timestamp.isoformat(),
                "content": {
                    "original_text": processed_content.original_text,
                    "cleaned_text": processed_content.cleaned_text,
                    "language": processed_content.language.dict() if processed_content.language else None,
                    "structure": processed_content.structure.dict(),
                    "segments": [segment.dict() for segment in processed_content.segments],
                    "potential_claims": [claim.dict() for claim in processed_content.potential_claims],
                    "statistics": {
                        "total_segments": len(processed_content.segments),
                        "total_claims": len(processed_content.potential_claims),
                        "high_confidence_claims": len([
                            c for c in processed_content.potential_claims 
                            if c.confidence >= 0.7
                        ]),
                        "original_length": len(processed_content.original_text),
                        "cleaned_length": len(processed_content.cleaned_text),
                        "reduction_ratio": processed_content.processing_metadata.get("reduction_ratio", 0)
                    }
                },
                "processing_metadata": processed_content.processing_metadata
            }
            
            # Cache the result
            await cache.set(cache_key, response, ttl=1800)  # Cache for 30 minutes
            
            logger.info(f"Successfully processed text content "
                       f"({len(processed_content.segments)} segments, "
                       f"{len(processed_content.potential_claims)} claims)")
            
            return response
            
        except TextProcessingError as e:
            logger.error(f"Text processing failed: {e}")
            return self._create_error_response(
                processing_id, "text_content", "text_processing_error", str(e), start_time
            )
        except Exception as e:
            logger.error(f"Unexpected error processing text: {e}")
            return self._create_error_response(
                processing_id, "text_content", "unexpected_error", str(e), start_time
            )
    
    async def extract_key_information(self, text: str) -> Dict[str, Any]:
        """
        Extract key information from text for fact-checking.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with key information
        """
        try:
            key_info = await self.text_processor.extract_key_information(text)
            return {
                "success": True,
                "key_information": key_info,
                "extracted_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Key information extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "key_information_extraction_error"
            }
    
    async def get_extraction_capabilities(self) -> Dict[str, Any]:
        """Get information about extraction capabilities."""
        return {
            "url_extraction": {
                "available_strategies": [strategy.value for strategy in self.url_extractor.get_available_strategies()],
                "supported_content_types": [
                    "news_article", "blog_post", "academic_paper", "wikipedia",
                    "social_media", "forum_post", "documentation", "general"
                ],
                "max_timeout": 300.0,
                "quality_assessment": True,
                "language_detection": True,
                "metadata_extraction": True
            },
            "text_processing": self.text_processor.get_processing_capabilities(),
            "caching": {
                "url_extraction_ttl": 3600,
                "text_processing_ttl": 1800
            }
        }
    
    def _create_error_response(
        self, 
        operation_id: str, 
        target: str, 
        error_type: str, 
        error_message: str, 
        start_time: datetime
    ) -> Dict[str, Any]:
        """Create standardized error response."""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "operation_id": operation_id,
            "target": target,
            "success": False,
            "error": error_message,
            "error_type": error_type,
            "processing_time": processing_time,
            "processed_at": datetime.now().isoformat()
        }
