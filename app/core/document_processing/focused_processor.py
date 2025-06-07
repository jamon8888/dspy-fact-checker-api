"""
Focused Document Processor

Unified document processing pipeline that integrates Docling, Mistral OCR, 
URL extraction, and text processing into a single, intelligent system.
"""

import asyncio
import logging
import time
import hashlib
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator

from .docling_processor import DoclingProcessor
from ..ocr.mistral_ocr import MistralOCRProcessor
from ..content_extraction import URLContentExtractor, AdvancedTextProcessor
from ..redis import cache
from .exceptions import (
    ProcessingError, UnsupportedFormatError, 
    ProcessingTimeoutError, ProcessingQualityError
)

logger = logging.getLogger(__name__)


class InputType(str, Enum):
    """Supported input types for document processing."""
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"
    URL = "url"
    TEXT = "text"
    IMAGE = "image"


class ProcessingStrategy(str, Enum):
    """Processing strategies for different scenarios."""
    AUTO = "auto"
    DOCLING_ONLY = "docling_only"
    OCR_ONLY = "ocr_only"
    HYBRID = "hybrid"
    URL_EXTRACTION = "url_extraction"
    TEXT_ANALYSIS = "text_analysis"


class QualityThreshold(str, Enum):
    """Quality threshold levels."""
    LOW = "low"      # 0.3
    MEDIUM = "medium"  # 0.5
    HIGH = "high"    # 0.7
    STRICT = "strict"  # 0.9


class InputData(BaseModel):
    """Standardized input data model."""
    
    type: InputType = Field(..., description="Type of input data")
    data: Union[bytes, str] = Field(..., description="Input data content")
    filename: Optional[str] = Field(None, description="Original filename")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('data')
    def validate_data(cls, v, values):
        """Validate data based on input type."""
        input_type = values.get('type')
        
        if input_type in [InputType.PDF, InputType.DOC, InputType.DOCX, InputType.IMAGE]:
            if not isinstance(v, bytes):
                raise ValueError(f"Binary data required for {input_type}")
        elif input_type in [InputType.URL, InputType.TEXT, InputType.TXT]:
            if not isinstance(v, str):
                raise ValueError(f"String data required for {input_type}")
        
        return v


class ProcessingOptions(BaseModel):
    """Configuration options for document processing."""
    
    strategy: ProcessingStrategy = Field(default=ProcessingStrategy.AUTO, description="Processing strategy")
    quality_threshold: QualityThreshold = Field(default=QualityThreshold.MEDIUM, description="Quality threshold")
    force_ocr: bool = Field(default=False, description="Force OCR processing")
    include_images: bool = Field(default=False, description="Include image extraction")
    include_tables: bool = Field(default=True, description="Include table extraction")
    include_metadata: bool = Field(default=True, description="Include metadata extraction")
    bypass_cache: bool = Field(default=False, description="Bypass cache lookup")
    timeout_seconds: float = Field(default=120.0, ge=1.0, le=600.0, description="Processing timeout")
    max_file_size: int = Field(default=50*1024*1024, description="Maximum file size in bytes")
    
    # Text processing options
    detect_claims: bool = Field(default=True, description="Detect potential claims")
    segmentation_strategy: str = Field(default="paragraph", description="Text segmentation strategy")
    claim_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Claim confidence threshold")
    
    # OCR options
    ocr_pages: Optional[List[int]] = Field(None, description="Specific pages for OCR")
    ocr_language: Optional[str] = Field(None, description="OCR language hint")
    
    def get_quality_score(self) -> float:
        """Get numeric quality threshold."""
        thresholds = {
            QualityThreshold.LOW: 0.3,
            QualityThreshold.MEDIUM: 0.5,
            QualityThreshold.HIGH: 0.7,
            QualityThreshold.STRICT: 0.9
        }
        return thresholds[self.quality_threshold]


class ProcessingStats(BaseModel):
    """Processing statistics and metrics."""
    
    processing_time: float = Field(..., description="Total processing time in seconds")
    processors_used: List[str] = Field(..., description="List of processors used")
    input_size: int = Field(..., description="Input size in bytes")
    output_size: int = Field(..., description="Output size in characters")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Content quality score")
    
    # Detailed metrics
    docling_time: Optional[float] = Field(None, description="Docling processing time")
    ocr_time: Optional[float] = Field(None, description="OCR processing time")
    text_processing_time: Optional[float] = Field(None, description="Text processing time")
    url_extraction_time: Optional[float] = Field(None, description="URL extraction time")
    
    # Content metrics
    page_count: Optional[int] = Field(None, description="Number of pages processed")
    word_count: int = Field(..., description="Total word count")
    character_count: int = Field(..., description="Total character count")
    table_count: int = Field(default=0, description="Number of tables extracted")
    image_count: int = Field(default=0, description="Number of images extracted")
    claim_count: int = Field(default=0, description="Number of potential claims detected")
    
    # Quality indicators
    text_quality: Optional[float] = Field(None, description="Text extraction quality")
    structure_quality: Optional[float] = Field(None, description="Document structure quality")
    ocr_confidence: Optional[float] = Field(None, description="OCR confidence score")


class ProcessingResult(BaseModel):
    """Unified processing result."""
    
    success: bool = Field(..., description="Processing success status")
    processing_id: str = Field(..., description="Unique processing identifier")
    input_type: InputType = Field(..., description="Type of input processed")
    processing_strategy: ProcessingStrategy = Field(..., description="Strategy used for processing")
    
    # Content results
    text: str = Field(..., description="Extracted text content")
    markdown: Optional[str] = Field(None, description="Markdown formatted content")
    structured_content: Dict[str, Any] = Field(default_factory=dict, description="Structured content")
    
    # Metadata and analysis
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    language: Optional[str] = Field(None, description="Detected language")
    
    # Extracted elements
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted tables")
    images: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted images")
    links: List[str] = Field(default_factory=list, description="Extracted links")
    
    # Text analysis
    segments: List[Dict[str, Any]] = Field(default_factory=list, description="Text segments")
    potential_claims: List[Dict[str, Any]] = Field(default_factory=list, description="Potential factual claims")
    
    # Processing information
    processing_stats: ProcessingStats = Field(..., description="Processing statistics")
    processed_at: datetime = Field(default_factory=datetime.now, description="Processing timestamp")
    cache_hit: bool = Field(default=False, description="Whether result was from cache")
    
    # Error information (if any)
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    errors: List[str] = Field(default_factory=list, description="Non-fatal errors")


class ProcessingCache:
    """Caching layer for processed documents."""
    
    def __init__(self, prefix: str = "focused_processor"):
        self.prefix = prefix
        self.default_ttl = 3600  # 1 hour
    
    def _generate_cache_key(self, input_data: InputData, options: ProcessingOptions) -> str:
        """Generate cache key for input and options."""
        # Create hash of input data
        if isinstance(input_data.data, bytes):
            data_hash = hashlib.md5(input_data.data).hexdigest()
        else:
            data_hash = hashlib.md5(input_data.data.encode('utf-8')).hexdigest()
        
        # Create hash of options
        options_str = options.json(sort_keys=True)
        options_hash = hashlib.md5(options_str.encode('utf-8')).hexdigest()
        
        return f"{self.prefix}:{input_data.type.value}:{data_hash}:{options_hash}"
    
    async def get(self, cache_key: str) -> Optional[ProcessingResult]:
        """Get cached processing result."""
        try:
            cached_data = await cache.get(cache_key)
            if cached_data:
                # Mark as cache hit
                result = ProcessingResult(**cached_data)
                result.cache_hit = True
                return result
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    async def set(self, cache_key: str, result: ProcessingResult, ttl: Optional[int] = None) -> bool:
        """Cache processing result."""
        try:
            # Don't cache the cache_hit flag
            result_data = result.dict()
            result_data['cache_hit'] = False
            
            return await cache.set(
                cache_key, 
                result_data, 
                ttl or self.default_ttl
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    async def delete(self, cache_key: str) -> bool:
        """Delete cached result."""
        try:
            return await cache.delete(cache_key)
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False


class FocusedDocumentProcessor:
    """
    Unified document processing pipeline that intelligently routes documents
    to the most appropriate processors and combines results for optimal output.
    """

    def __init__(self):
        """Initialize the focused document processor."""
        # Initialize processors
        self.docling_processor = None
        self.mistral_ocr = None
        self.url_extractor = None
        self.text_processor = None

        # Initialize cache
        self.cache = ProcessingCache()

        # Processing statistics
        self.total_processed = 0
        self.successful_processed = 0

        logger.info("FocusedDocumentProcessor initialized")

    async def initialize_processors(self):
        """Initialize all processors lazily."""
        try:
            if not self.docling_processor:
                self.docling_processor = DoclingProcessor()

            if not self.mistral_ocr:
                self.mistral_ocr = MistralOCRProcessor()

            if not self.url_extractor:
                from ..content_extraction import URLContentExtractor
                self.url_extractor = URLContentExtractor()

            if not self.text_processor:
                from ..content_extraction import AdvancedTextProcessor
                self.text_processor = AdvancedTextProcessor()

            logger.info("All processors initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize processors: {e}")
            raise ProcessingError(f"Processor initialization failed: {str(e)}")

    async def process_input(
        self,
        input_data: InputData,
        processing_options: Optional[ProcessingOptions] = None
    ) -> ProcessingResult:
        """
        Main entry point for document processing.

        Args:
            input_data: Input data to process
            processing_options: Processing configuration options

        Returns:
            ProcessingResult with extracted content and metadata
        """
        if processing_options is None:
            processing_options = ProcessingOptions()

        processing_id = f"proc_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            # Initialize processors if needed
            await self.initialize_processors()

            # Validate input
            self._validate_input(input_data, processing_options)

            # Check cache first
            cache_key = self.cache._generate_cache_key(input_data, processing_options)
            if not processing_options.bypass_cache:
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for processing ID: {processing_id}")
                    cached_result.processing_id = processing_id
                    return cached_result

            # Route to appropriate processor
            result = await self._route_processing(input_data, processing_options, processing_id)

            # Cache the result
            if result.success:
                await self.cache.set(cache_key, result)

            # Update statistics
            self.total_processed += 1
            if result.success:
                self.successful_processed += 1

            processing_time = time.time() - start_time
            logger.info(f"Processing completed for {processing_id} in {processing_time:.2f}s")

            return result

        except asyncio.TimeoutError:
            raise ProcessingTimeoutError(
                f"Processing timed out after {processing_options.timeout_seconds}s"
            )
        except Exception as e:
            logger.error(f"Processing failed for {processing_id}: {e}")

            # Create error result
            processing_time = time.time() - start_time
            error_result = ProcessingResult(
                success=False,
                processing_id=processing_id,
                input_type=input_data.type,
                processing_strategy=processing_options.strategy,
                text="",
                processing_stats=ProcessingStats(
                    processing_time=processing_time,
                    processors_used=[],
                    input_size=len(input_data.data) if isinstance(input_data.data, (str, bytes)) else 0,
                    output_size=0,
                    confidence_score=0.0,
                    quality_score=0.0,
                    word_count=0,
                    character_count=0
                ),
                errors=[str(e)]
            )

            self.total_processed += 1
            return error_result

    def _validate_input(self, input_data: InputData, options: ProcessingOptions):
        """Validate input data and options."""
        # Check file size
        if isinstance(input_data.data, (str, bytes)):
            size = len(input_data.data)
            if size > options.max_file_size:
                raise ProcessingError(
                    f"Input size ({size} bytes) exceeds maximum allowed size ({options.max_file_size} bytes)"
                )

        # Validate input type compatibility
        if input_data.type == InputType.URL and not isinstance(input_data.data, str):
            raise ProcessingError("URL input must be a string")

        if input_data.type in [InputType.PDF, InputType.DOC, InputType.DOCX] and not isinstance(input_data.data, bytes):
            raise ProcessingError(f"{input_data.type} input must be binary data")

    async def _route_processing(
        self,
        input_data: InputData,
        options: ProcessingOptions,
        processing_id: str
    ) -> ProcessingResult:
        """Route input to appropriate processing method."""

        # Determine processing strategy
        strategy = self._determine_strategy(input_data, options)

        try:
            if input_data.type == InputType.PDF:
                return await self._process_pdf(input_data, options, processing_id, strategy)
            elif input_data.type in [InputType.DOC, InputType.DOCX]:
                return await self._process_word_document(input_data, options, processing_id, strategy)
            elif input_data.type == InputType.TXT:
                return await self._process_text_file(input_data, options, processing_id, strategy)
            elif input_data.type == InputType.URL:
                return await self._process_url(input_data, options, processing_id, strategy)
            elif input_data.type == InputType.TEXT:
                return await self._process_direct_text(input_data, options, processing_id, strategy)
            elif input_data.type == InputType.IMAGE:
                return await self._process_image(input_data, options, processing_id, strategy)
            else:
                raise UnsupportedFormatError(f"Unsupported input type: {input_data.type}")

        except Exception as e:
            logger.error(f"Processing failed for {input_data.type}: {e}")
            raise ProcessingError(f"Failed to process {input_data.type}: {str(e)}")

    def _determine_strategy(self, input_data: InputData, options: ProcessingOptions) -> ProcessingStrategy:
        """Determine the best processing strategy for the input."""
        if options.strategy != ProcessingStrategy.AUTO:
            return options.strategy

        # Auto-determine strategy based on input type
        if input_data.type == InputType.PDF:
            return ProcessingStrategy.HYBRID  # Use both Docling and OCR
        elif input_data.type in [InputType.DOC, InputType.DOCX]:
            return ProcessingStrategy.DOCLING_ONLY
        elif input_data.type == InputType.IMAGE:
            return ProcessingStrategy.OCR_ONLY
        elif input_data.type == InputType.URL:
            return ProcessingStrategy.URL_EXTRACTION
        elif input_data.type in [InputType.TEXT, InputType.TXT]:
            return ProcessingStrategy.TEXT_ANALYSIS
        else:
            return ProcessingStrategy.DOCLING_ONLY

    async def _process_pdf(
        self,
        input_data: InputData,
        options: ProcessingOptions,
        processing_id: str,
        strategy: ProcessingStrategy
    ) -> ProcessingResult:
        """Process PDF documents using hybrid approach."""
        start_time = time.time()
        processors_used = []
        warnings = []

        docling_result = None
        ocr_result = None

        try:
            # Try Docling first (unless OCR-only strategy)
            if strategy != ProcessingStrategy.OCR_ONLY and self.docling_processor:
                try:
                    docling_start = time.time()
                    docling_result = await self.docling_processor.process_document(
                        input_data.data,
                        input_data.filename or "document.pdf"
                    )
                    docling_time = time.time() - docling_start
                    processors_used.append("docling")
                    logger.info(f"Docling processing completed in {docling_time:.2f}s")
                except Exception as e:
                    logger.warning(f"Docling processing failed: {e}")
                    warnings.append(f"Docling processing failed: {str(e)}")
                    docling_result = None

            # Try OCR if needed (hybrid strategy, OCR-only, or Docling failed)
            should_use_ocr = (
                strategy in [ProcessingStrategy.OCR_ONLY, ProcessingStrategy.HYBRID] or
                options.force_ocr or
                (docling_result is None and strategy == ProcessingStrategy.AUTO)
            )

            if should_use_ocr and self.mistral_ocr:
                try:
                    ocr_start = time.time()
                    ocr_result = await self.mistral_ocr.process_pdf(
                        input_data.data,
                        pages=options.ocr_pages,
                        include_image_base64=options.include_images
                    )
                    ocr_time = time.time() - ocr_start
                    processors_used.append("mistral_ocr")
                    logger.info(f"OCR processing completed in {ocr_time:.2f}s")
                except Exception as e:
                    logger.warning(f"OCR processing failed: {e}")
                    warnings.append(f"OCR processing failed: {str(e)}")
                    ocr_result = None

            # Combine results
            combined_result = await self._combine_processing_results(
                docling_result, ocr_result, input_data, options, processing_id
            )

            # Add processing statistics
            processing_time = time.time() - start_time
            combined_result.processing_stats.processing_time = processing_time
            combined_result.processing_stats.processors_used = processors_used
            combined_result.processing_stats.docling_time = docling_time if 'docling_time' in locals() else None
            combined_result.processing_stats.ocr_time = ocr_time if 'ocr_time' in locals() else None
            combined_result.warnings.extend(warnings)

            return combined_result

        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise ProcessingError(f"PDF processing failed: {str(e)}")

    async def _process_word_document(
        self,
        input_data: InputData,
        options: ProcessingOptions,
        processing_id: str,
        strategy: ProcessingStrategy
    ) -> ProcessingResult:
        """Process Word documents using Docling."""
        start_time = time.time()

        try:
            if not self.docling_processor:
                raise ProcessingError("Docling processor not available for Word documents")

            # Process with Docling
            docling_result = await self.docling_processor.process_document(
                input_data.data,
                input_data.filename or f"document.{input_data.type.value}"
            )

            # Convert to unified result
            result = await self._convert_docling_result(
                docling_result, input_data, options, processing_id
            )

            # Add processing statistics
            processing_time = time.time() - start_time
            result.processing_stats.processing_time = processing_time
            result.processing_stats.processors_used = ["docling"]
            result.processing_stats.docling_time = processing_time

            return result

        except Exception as e:
            logger.error(f"Word document processing failed: {e}")
            raise ProcessingError(f"Word document processing failed: {str(e)}")

    async def _process_image(
        self,
        input_data: InputData,
        options: ProcessingOptions,
        processing_id: str,
        strategy: ProcessingStrategy
    ) -> ProcessingResult:
        """Process images using OCR."""
        start_time = time.time()

        try:
            if not self.mistral_ocr:
                raise ProcessingError("OCR processor not available for images")

            # Determine image format from filename or default to jpeg
            image_format = "jpeg"
            if input_data.filename:
                ext = input_data.filename.split('.')[-1].lower()
                if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp']:
                    image_format = ext

            # Process with OCR
            ocr_result = await self.mistral_ocr.process_image(
                input_data.data,
                image_format=image_format,
                include_image_base64=options.include_images
            )

            # Convert to unified result
            result = await self._convert_ocr_result(
                ocr_result, input_data, options, processing_id
            )

            # Add processing statistics
            processing_time = time.time() - start_time
            result.processing_stats.processing_time = processing_time
            result.processing_stats.processors_used = ["mistral_ocr"]
            result.processing_stats.ocr_time = processing_time

            return result

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise ProcessingError(f"Image processing failed: {str(e)}")

    async def _process_url(
        self,
        input_data: InputData,
        options: ProcessingOptions,
        processing_id: str,
        strategy: ProcessingStrategy
    ) -> ProcessingResult:
        """Process URLs using content extraction."""
        start_time = time.time()

        try:
            if not self.url_extractor:
                raise ProcessingError("URL extractor not available")

            # Extract content from URL
            from ..content_extraction import ExtractionOptions
            extraction_options = ExtractionOptions(
                strategy="auto",
                timeout_seconds=min(options.timeout_seconds, 60.0),
                include_metadata=options.include_metadata,
                include_images=options.include_images
            )

            extracted_content = await self.url_extractor.extract_content(
                str(input_data.data), extraction_options
            )

            # Convert to unified result
            result = await self._convert_url_result(
                extracted_content, input_data, options, processing_id
            )

            # Add processing statistics
            processing_time = time.time() - start_time
            result.processing_stats.processing_time = processing_time
            result.processing_stats.processors_used = ["url_extractor"]
            result.processing_stats.url_extraction_time = processing_time

            return result

        except Exception as e:
            logger.error(f"URL processing failed: {e}")
            raise ProcessingError(f"URL processing failed: {str(e)}")

    async def _process_text_file(
        self,
        input_data: InputData,
        options: ProcessingOptions,
        processing_id: str,
        strategy: ProcessingStrategy
    ) -> ProcessingResult:
        """Process text files using text analysis."""
        start_time = time.time()

        try:
            # Convert bytes to string if needed
            if isinstance(input_data.data, bytes):
                text_content = input_data.data.decode('utf-8')
            else:
                text_content = input_data.data

            # Process with text processor
            result = await self._process_direct_text(
                InputData(type=InputType.TEXT, data=text_content, filename=input_data.filename),
                options, processing_id, strategy
            )

            # Update input type in result
            result.input_type = InputType.TXT

            return result

        except Exception as e:
            logger.error(f"Text file processing failed: {e}")
            raise ProcessingError(f"Text file processing failed: {str(e)}")

    async def _process_direct_text(
        self,
        input_data: InputData,
        options: ProcessingOptions,
        processing_id: str,
        strategy: ProcessingStrategy
    ) -> ProcessingResult:
        """Process direct text input using text analysis."""
        start_time = time.time()

        try:
            if not self.text_processor:
                raise ProcessingError("Text processor not available")

            # Process text
            from ..content_extraction import TextProcessingOptions, SegmentationStrategy

            # Map segmentation strategy
            try:
                seg_strategy = SegmentationStrategy(options.segmentation_strategy)
            except ValueError:
                seg_strategy = SegmentationStrategy.PARAGRAPH

            text_options = TextProcessingOptions(
                segmentation_strategy=seg_strategy,
                detect_language=True,
                detect_claims=options.detect_claims,
                analyze_structure=True,
                claim_confidence_threshold=options.claim_confidence_threshold
            )

            processed_content = await self.text_processor.process_text(
                str(input_data.data), text_options
            )

            # Convert to unified result
            result = await self._convert_text_result(
                processed_content, input_data, options, processing_id
            )

            # Add processing statistics
            processing_time = time.time() - start_time
            result.processing_stats.processing_time = processing_time
            result.processing_stats.processors_used = ["text_processor"]
            result.processing_stats.text_processing_time = processing_time

            return result

        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            raise ProcessingError(f"Text processing failed: {str(e)}")

    async def _combine_processing_results(
        self,
        docling_result: Optional[Dict[str, Any]],
        ocr_result: Optional[Dict[str, Any]],
        input_data: InputData,
        options: ProcessingOptions,
        processing_id: str
    ) -> ProcessingResult:
        """Combine results from multiple processors."""

        # Determine which result to use as primary
        primary_result = None
        secondary_result = None

        if docling_result and ocr_result:
            # Compare quality scores
            docling_quality = docling_result.get('quality_score', 0.0)
            ocr_quality = ocr_result.get('quality_score', 0.0)

            if docling_quality >= ocr_quality:
                primary_result = docling_result
                secondary_result = ocr_result
            else:
                primary_result = ocr_result
                secondary_result = docling_result
        elif docling_result:
            primary_result = docling_result
        elif ocr_result:
            primary_result = ocr_result
        else:
            raise ProcessingError("No successful processing results available")

        # Extract content
        text = primary_result.get('text', '')
        markdown = primary_result.get('markdown', '')

        # Merge metadata
        metadata = {}
        if docling_result:
            metadata.update(docling_result.get('metadata', {}))
        if ocr_result:
            metadata.update(ocr_result.get('metadata', {}))

        # Calculate combined quality score
        quality_score = primary_result.get('quality_score', 0.5)
        confidence_score = primary_result.get('confidence_score', 0.5)

        # Extract tables and images
        tables = []
        images = []

        if options.include_tables:
            tables.extend(primary_result.get('tables', []))
            if secondary_result:
                tables.extend(secondary_result.get('tables', []))

        if options.include_images:
            images.extend(primary_result.get('images', []))
            if secondary_result:
                images.extend(secondary_result.get('images', []))

        # Process text for claims if requested
        segments = []
        potential_claims = []

        if options.detect_claims and text and self.text_processor:
            try:
                from ..content_extraction import TextProcessingOptions, SegmentationStrategy

                seg_strategy = SegmentationStrategy(options.segmentation_strategy)
                text_options = TextProcessingOptions(
                    segmentation_strategy=seg_strategy,
                    detect_claims=True,
                    claim_confidence_threshold=options.claim_confidence_threshold
                )

                processed_text = await self.text_processor.process_text(text, text_options)
                segments = [seg.dict() for seg in processed_text.segments]
                potential_claims = [claim.dict() for claim in processed_text.potential_claims]

            except Exception as e:
                logger.warning(f"Text analysis failed during combination: {e}")

        # Create processing stats
        input_size = len(input_data.data) if isinstance(input_data.data, (str, bytes)) else 0
        output_size = len(text)
        word_count = len(text.split()) if text else 0

        processing_stats = ProcessingStats(
            processing_time=0.0,  # Will be set by caller
            processors_used=[],   # Will be set by caller
            input_size=input_size,
            output_size=output_size,
            confidence_score=confidence_score,
            quality_score=quality_score,
            word_count=word_count,
            character_count=len(text),
            table_count=len(tables),
            image_count=len(images),
            claim_count=len(potential_claims),
            text_quality=quality_score,
            structure_quality=primary_result.get('structure_quality', 0.5)
        )

        return ProcessingResult(
            success=True,
            processing_id=processing_id,
            input_type=input_data.type,
            processing_strategy=ProcessingStrategy.HYBRID,
            text=text,
            markdown=markdown,
            structured_content=primary_result.get('structured_content', {}),
            metadata=metadata,
            language=primary_result.get('language'),
            tables=tables,
            images=images,
            segments=segments,
            potential_claims=potential_claims,
            processing_stats=processing_stats
        )

    async def _convert_docling_result(
        self,
        docling_result: Dict[str, Any],
        input_data: InputData,
        options: ProcessingOptions,
        processing_id: str
    ) -> ProcessingResult:
        """Convert Docling result to unified format."""

        text = docling_result.get('text', '')
        markdown = docling_result.get('markdown', '')

        # Process text for claims if requested
        segments = []
        potential_claims = []

        if options.detect_claims and text and self.text_processor:
            try:
                from ..content_extraction import TextProcessingOptions, SegmentationStrategy

                seg_strategy = SegmentationStrategy(options.segmentation_strategy)
                text_options = TextProcessingOptions(
                    segmentation_strategy=seg_strategy,
                    detect_claims=True,
                    claim_confidence_threshold=options.claim_confidence_threshold
                )

                processed_text = await self.text_processor.process_text(text, text_options)
                segments = [seg.dict() for seg in processed_text.segments]
                potential_claims = [claim.dict() for claim in processed_text.potential_claims]

            except Exception as e:
                logger.warning(f"Text analysis failed for Docling result: {e}")

        # Create processing stats
        input_size = len(input_data.data) if isinstance(input_data.data, (str, bytes)) else 0
        output_size = len(text)
        word_count = len(text.split()) if text else 0

        processing_stats = ProcessingStats(
            processing_time=0.0,  # Will be set by caller
            processors_used=["docling"],
            input_size=input_size,
            output_size=output_size,
            confidence_score=docling_result.get('confidence_score', 0.8),
            quality_score=docling_result.get('quality_score', 0.8),
            word_count=word_count,
            character_count=len(text),
            table_count=len(docling_result.get('tables', [])),
            image_count=len(docling_result.get('images', [])),
            claim_count=len(potential_claims),
            text_quality=docling_result.get('quality_score', 0.8),
            structure_quality=0.9  # Docling is good at structure
        )

        return ProcessingResult(
            success=True,
            processing_id=processing_id,
            input_type=input_data.type,
            processing_strategy=ProcessingStrategy.DOCLING_ONLY,
            text=text,
            markdown=markdown,
            structured_content=docling_result.get('structured_content', {}),
            metadata=docling_result.get('metadata', {}),
            language=docling_result.get('language'),
            tables=docling_result.get('tables', []) if options.include_tables else [],
            images=docling_result.get('images', []) if options.include_images else [],
            segments=segments,
            potential_claims=potential_claims,
            processing_stats=processing_stats
        )

    async def _convert_ocr_result(
        self,
        ocr_result: Dict[str, Any],
        input_data: InputData,
        options: ProcessingOptions,
        processing_id: str
    ) -> ProcessingResult:
        """Convert OCR result to unified format."""

        text = ocr_result.get('text', '')
        markdown = ocr_result.get('markdown', '')

        # Process text for claims if requested
        segments = []
        potential_claims = []

        if options.detect_claims and text and self.text_processor:
            try:
                from ..content_extraction import TextProcessingOptions, SegmentationStrategy

                seg_strategy = SegmentationStrategy(options.segmentation_strategy)
                text_options = TextProcessingOptions(
                    segmentation_strategy=seg_strategy,
                    detect_claims=True,
                    claim_confidence_threshold=options.claim_confidence_threshold
                )

                processed_text = await self.text_processor.process_text(text, text_options)
                segments = [seg.dict() for seg in processed_text.segments]
                potential_claims = [claim.dict() for claim in processed_text.potential_claims]

            except Exception as e:
                logger.warning(f"Text analysis failed for OCR result: {e}")

        # Create processing stats
        input_size = len(input_data.data) if isinstance(input_data.data, (str, bytes)) else 0
        output_size = len(text)
        word_count = len(text.split()) if text else 0

        processing_stats = ProcessingStats(
            processing_time=0.0,  # Will be set by caller
            processors_used=["mistral_ocr"],
            input_size=input_size,
            output_size=output_size,
            confidence_score=ocr_result.get('confidence_score', 0.7),
            quality_score=ocr_result.get('quality_score', 0.7),
            word_count=word_count,
            character_count=len(text),
            table_count=len(ocr_result.get('tables', [])),
            image_count=len(ocr_result.get('images', [])),
            claim_count=len(potential_claims),
            text_quality=ocr_result.get('quality_score', 0.7),
            structure_quality=0.6,  # OCR is decent at structure
            ocr_confidence=ocr_result.get('confidence_score', 0.7)
        )

        return ProcessingResult(
            success=True,
            processing_id=processing_id,
            input_type=input_data.type,
            processing_strategy=ProcessingStrategy.OCR_ONLY,
            text=text,
            markdown=markdown,
            structured_content=ocr_result.get('structured_content', {}),
            metadata=ocr_result.get('metadata', {}),
            language=ocr_result.get('language'),
            tables=ocr_result.get('tables', []) if options.include_tables else [],
            images=ocr_result.get('images', []) if options.include_images else [],
            segments=segments,
            potential_claims=potential_claims,
            processing_stats=processing_stats
        )

    async def _convert_url_result(
        self,
        url_result: Any,  # ExtractedWebContent
        input_data: InputData,
        options: ProcessingOptions,
        processing_id: str
    ) -> ProcessingResult:
        """Convert URL extraction result to unified format."""

        text = url_result.content

        # Process text for claims if requested
        segments = []
        potential_claims = []

        if options.detect_claims and text and self.text_processor:
            try:
                from ..content_extraction import TextProcessingOptions, SegmentationStrategy

                seg_strategy = SegmentationStrategy(options.segmentation_strategy)
                text_options = TextProcessingOptions(
                    segmentation_strategy=seg_strategy,
                    detect_claims=True,
                    claim_confidence_threshold=options.claim_confidence_threshold
                )

                processed_text = await self.text_processor.process_text(text, text_options)
                segments = [seg.dict() for seg in processed_text.segments]
                potential_claims = [claim.dict() for claim in processed_text.potential_claims]

            except Exception as e:
                logger.warning(f"Text analysis failed for URL result: {e}")

        # Create processing stats
        input_size = len(str(input_data.data))
        output_size = len(text)
        word_count = len(text.split()) if text else 0

        processing_stats = ProcessingStats(
            processing_time=0.0,  # Will be set by caller
            processors_used=["url_extractor"],
            input_size=input_size,
            output_size=output_size,
            confidence_score=url_result.quality_score,
            quality_score=url_result.quality_score,
            word_count=word_count,
            character_count=len(text),
            table_count=0,  # URL extraction doesn't extract tables
            image_count=len(url_result.images) if hasattr(url_result, 'images') else 0,
            claim_count=len(potential_claims),
            text_quality=url_result.quality_score,
            structure_quality=0.7  # URL extraction is decent at structure
        )

        return ProcessingResult(
            success=True,
            processing_id=processing_id,
            input_type=input_data.type,
            processing_strategy=ProcessingStrategy.URL_EXTRACTION,
            text=text,
            markdown=None,
            structured_content={},
            metadata=url_result.metadata,
            language=url_result.language.language if url_result.language else None,
            tables=[],
            images=[{"url": img} for img in url_result.images] if options.include_images else [],
            links=url_result.links if hasattr(url_result, 'links') else [],
            segments=segments,
            potential_claims=potential_claims,
            processing_stats=processing_stats
        )

    async def _convert_text_result(
        self,
        text_result: Any,  # ProcessedTextContent
        input_data: InputData,
        options: ProcessingOptions,
        processing_id: str
    ) -> ProcessingResult:
        """Convert text processing result to unified format."""

        text = text_result.cleaned_text
        segments = [seg.dict() for seg in text_result.segments]
        potential_claims = [claim.dict() for claim in text_result.potential_claims]

        # Create processing stats
        input_size = len(str(input_data.data))
        output_size = len(text)
        word_count = len(text.split()) if text else 0

        processing_stats = ProcessingStats(
            processing_time=0.0,  # Will be set by caller
            processors_used=["text_processor"],
            input_size=input_size,
            output_size=output_size,
            confidence_score=0.9,  # Text processing is highly reliable
            quality_score=0.9,
            word_count=word_count,
            character_count=len(text),
            table_count=0,
            image_count=0,
            claim_count=len(potential_claims),
            text_quality=0.9,
            structure_quality=text_result.structure.complexity_score
        )

        return ProcessingResult(
            success=True,
            processing_id=processing_id,
            input_type=input_data.type,
            processing_strategy=ProcessingStrategy.TEXT_ANALYSIS,
            text=text,
            markdown=None,
            structured_content={},
            metadata=text_result.processing_metadata,
            language=text_result.language.language if text_result.language else None,
            tables=[],
            images=[],
            segments=segments,
            potential_claims=potential_claims,
            processing_stats=processing_stats
        )

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        success_rate = (
            self.successful_processed / self.total_processed
            if self.total_processed > 0 else 0.0
        )

        return {
            "total_processed": self.total_processed,
            "successful_processed": self.successful_processed,
            "success_rate": success_rate,
            "available_processors": {
                "docling": self.docling_processor is not None,
                "mistral_ocr": self.mistral_ocr is not None,
                "url_extractor": self.url_extractor is not None,
                "text_processor": self.text_processor is not None
            },
            "supported_input_types": [t.value for t in InputType],
            "supported_strategies": [s.value for s in ProcessingStrategy]
        }
