"""
Document processing module for the DSPy-Enhanced Fact-Checker API Platform.
"""

from app.core.document_processing.base import (
    DocumentProcessor, ProcessingResult, DocumentType, ProcessingMethod,
    DocumentMetadata, TableData, ImageData, StructuredContent
)
from app.core.document_processing.exceptions import (
    ProcessingError, UnsupportedFormatError, DocumentTooLargeError,
    CorruptedDocumentError, ProcessingTimeoutError, ExtractionError,
    ProcessingQualityError
)

# Import DoclingProcessor conditionally to handle missing dependencies
try:
    from app.core.document_processing.docling_processor import DoclingProcessor
    DOCLING_AVAILABLE = True
except ImportError:
    DoclingProcessor = None
    DOCLING_AVAILABLE = False

# Import FocusedDocumentProcessor
try:
    from app.core.document_processing.focused_processor import (
        FocusedDocumentProcessor, InputData, ProcessingOptions,
        ProcessingResult as FocusedProcessingResult, InputType,
        ProcessingStrategy, QualityThreshold, ProcessingStats, ProcessingCache
    )
    FOCUSED_PROCESSOR_AVAILABLE = True
except ImportError as e:
    FocusedDocumentProcessor = None
    InputData = None
    ProcessingOptions = None
    FocusedProcessingResult = None
    InputType = None
    ProcessingStrategy = None
    QualityThreshold = None
    ProcessingStats = None
    ProcessingCache = None
    FOCUSED_PROCESSOR_AVAILABLE = False

__all__ = [
    "DocumentProcessor",
    "ProcessingResult",
    "DocumentType",
    "ProcessingMethod",
    "DocumentMetadata",
    "TableData",
    "ImageData",
    "StructuredContent",
    "ProcessingError",
    "UnsupportedFormatError",
    "DocumentTooLargeError",
    "CorruptedDocumentError",
    "ProcessingTimeoutError",
    "ExtractionError",
    "ProcessingQualityError",
    "DoclingProcessor",
    "DOCLING_AVAILABLE",
    "FocusedDocumentProcessor",
    "InputData",
    "ProcessingOptions",
    "FocusedProcessingResult",
    "InputType",
    "ProcessingStrategy",
    "QualityThreshold",
    "ProcessingStats",
    "ProcessingCache",
    "FOCUSED_PROCESSOR_AVAILABLE"
]