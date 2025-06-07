"""
Base classes and interfaces for document processing.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, BinaryIO
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    HTML = "html"
    RTF = "rtf"
    ODT = "odt"
    IMAGE = "image"  # For OCR processing
    UNKNOWN = "unknown"


class ProcessingMethod(Enum):
    """Document processing methods."""
    DOCLING = "docling"
    PYPDF = "pypdf"
    PYMUPDF = "pymupdf"
    PYTHON_DOCX = "python_docx"
    OCR = "ocr"
    FALLBACK = "fallback"


@dataclass
class DocumentMetadata:
    """Document metadata extracted during processing."""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    keywords: List[str] = field(default_factory=list)
    language: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    file_size: Optional[int] = None
    format_version: Optional[str] = None
    security_settings: Dict[str, Any] = field(default_factory=dict)
    custom_properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TableData:
    """Extracted table data."""
    table_id: str
    caption: Optional[str] = None
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    position: Dict[str, Any] = field(default_factory=dict)  # page, bbox, etc.
    confidence: float = 1.0
    extraction_method: Optional[str] = None


@dataclass
class ImageData:
    """Extracted image data."""
    image_id: str
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    image_data: Optional[bytes] = None
    image_format: Optional[str] = None
    dimensions: Optional[Dict[str, int]] = None  # width, height
    position: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    classification: Optional[str] = None  # figure, chart, photo, etc.


@dataclass
class StructuredContent:
    """Structured document content."""
    text: str
    paragraphs: List[Dict[str, Any]] = field(default_factory=list)
    headings: List[Dict[str, Any]] = field(default_factory=list)
    lists: List[Dict[str, Any]] = field(default_factory=list)
    footnotes: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    formulas: List[Dict[str, Any]] = field(default_factory=list)
    code_blocks: List[Dict[str, Any]] = field(default_factory=list)
    reading_order: List[str] = field(default_factory=list)  # Element IDs in reading order


@dataclass
class ProcessingResult:
    """Result of document processing."""
    success: bool
    content: Optional[StructuredContent] = None
    metadata: Optional[DocumentMetadata] = None
    tables: List[TableData] = field(default_factory=list)
    images: List[ImageData] = field(default_factory=list)
    processing_method: Optional[ProcessingMethod] = None
    processing_time: Optional[float] = None
    confidence_score: float = 1.0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None  # For debugging/analysis


class DocumentProcessor(ABC):
    """Abstract base class for document processors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the processor with configuration."""
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def process_document(
        self, 
        file_data: Union[bytes, BinaryIO], 
        file_type: DocumentType,
        filename: Optional[str] = None,
        **kwargs
    ) -> ProcessingResult:
        """
        Process a document and return structured content.
        
        Args:
            file_data: Document data as bytes or file-like object
            file_type: Type of document to process
            filename: Original filename (optional)
            **kwargs: Additional processing options
            
        Returns:
            ProcessingResult with extracted content and metadata
        """
        pass
    
    @abstractmethod
    def supports_format(self, file_type: DocumentType) -> bool:
        """Check if processor supports the given format."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[DocumentType]:
        """Get list of supported document formats."""
        pass
    
    def validate_input(
        self, 
        file_data: Union[bytes, BinaryIO], 
        file_type: DocumentType,
        max_size: Optional[int] = None
    ) -> None:
        """
        Validate input data before processing.
        
        Args:
            file_data: Document data
            file_type: Document type
            max_size: Maximum allowed file size in bytes
            
        Raises:
            UnsupportedFormatError: If format is not supported
            DocumentTooLargeError: If file is too large
            ProcessingError: For other validation errors
        """
        from app.core.document_processing.exceptions import (
            UnsupportedFormatError, 
            DocumentTooLargeError
        )
        
        # Check format support
        if not self.supports_format(file_type):
            raise UnsupportedFormatError(
                file_type.value, 
                [fmt.value for fmt in self.get_supported_formats()]
            )
        
        # Check file size
        if max_size:
            if isinstance(file_data, bytes):
                file_size = len(file_data)
            else:
                # For file-like objects, try to get size
                try:
                    current_pos = file_data.tell()
                    file_data.seek(0, 2)  # Seek to end
                    file_size = file_data.tell()
                    file_data.seek(current_pos)  # Restore position
                except (AttributeError, OSError):
                    file_size = 0  # Can't determine size
            
            if file_size > max_size:
                raise DocumentTooLargeError(file_size, max_size)
    
    def _calculate_confidence_score(self, result_data: Dict[str, Any]) -> float:
        """Calculate confidence score for processing result."""
        # Base implementation - can be overridden by specific processors
        confidence = 1.0
        
        # Reduce confidence if there were warnings
        if result_data.get("warnings"):
            confidence -= 0.1 * len(result_data["warnings"])
        
        # Reduce confidence if there were errors
        if result_data.get("errors"):
            confidence -= 0.2 * len(result_data["errors"])
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def _extract_basic_metadata(
        self, 
        file_data: Union[bytes, BinaryIO],
        filename: Optional[str] = None
    ) -> DocumentMetadata:
        """Extract basic metadata that's common across formats."""
        metadata = DocumentMetadata()
        
        # Set file size
        if isinstance(file_data, bytes):
            metadata.file_size = len(file_data)
        else:
            try:
                current_pos = file_data.tell()
                file_data.seek(0, 2)
                metadata.file_size = file_data.tell()
                file_data.seek(current_pos)
            except (AttributeError, OSError):
                pass
        
        return metadata


class ProcessorRegistry:
    """Registry for document processors."""
    
    def __init__(self):
        self._processors: Dict[str, DocumentProcessor] = {}
        self._format_mapping: Dict[DocumentType, List[str]] = {}
    
    def register(self, name: str, processor: DocumentProcessor) -> None:
        """Register a document processor."""
        self._processors[name] = processor
        
        # Update format mapping
        for fmt in processor.get_supported_formats():
            if fmt not in self._format_mapping:
                self._format_mapping[fmt] = []
            if name not in self._format_mapping[fmt]:
                self._format_mapping[fmt].append(name)
    
    def get_processor(self, name: str) -> Optional[DocumentProcessor]:
        """Get processor by name."""
        return self._processors.get(name)
    
    def get_processors_for_format(self, file_type: DocumentType) -> List[DocumentProcessor]:
        """Get all processors that support a given format."""
        processor_names = self._format_mapping.get(file_type, [])
        return [self._processors[name] for name in processor_names if name in self._processors]
    
    def get_best_processor(self, file_type: DocumentType) -> Optional[DocumentProcessor]:
        """Get the best processor for a given format (first registered)."""
        processors = self.get_processors_for_format(file_type)
        return processors[0] if processors else None
    
    def list_processors(self) -> List[str]:
        """List all registered processor names."""
        return list(self._processors.keys())


# Global processor registry
processor_registry = ProcessorRegistry()
