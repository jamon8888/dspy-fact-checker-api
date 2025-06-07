"""
Document processing exceptions for the DSPy-Enhanced Fact-Checker API Platform.
"""

from typing import Optional, Any


class ProcessingError(Exception):
    """Base exception for document processing errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[dict] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "PROCESSING_ERROR"
        self.details = details or {}


class UnsupportedFormatError(ProcessingError):
    """Exception raised when document format is not supported."""
    
    def __init__(
        self, 
        format_type: str, 
        supported_formats: Optional[list] = None
    ):
        message = f"Unsupported document format: {format_type}"
        if supported_formats:
            message += f". Supported formats: {', '.join(supported_formats)}"
        
        super().__init__(
            message=message,
            error_code="UNSUPPORTED_FORMAT",
            details={
                "format_type": format_type,
                "supported_formats": supported_formats or []
            }
        )


class DocumentTooLargeError(ProcessingError):
    """Exception raised when document exceeds size limits."""
    
    def __init__(self, file_size: int, max_size: int):
        message = f"Document size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)"
        
        super().__init__(
            message=message,
            error_code="DOCUMENT_TOO_LARGE",
            details={
                "file_size": file_size,
                "max_size": max_size
            }
        )


class CorruptedDocumentError(ProcessingError):
    """Exception raised when document is corrupted or unreadable."""
    
    def __init__(self, reason: Optional[str] = None):
        message = "Document appears to be corrupted or unreadable"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message=message,
            error_code="CORRUPTED_DOCUMENT",
            details={"reason": reason}
        )


class ProcessingTimeoutError(ProcessingError):
    """Exception raised when document processing times out."""
    
    def __init__(self, timeout_seconds: int):
        message = f"Document processing timed out after {timeout_seconds} seconds"
        
        super().__init__(
            message=message,
            error_code="PROCESSING_TIMEOUT",
            details={"timeout_seconds": timeout_seconds}
        )


class ExtractionError(ProcessingError):
    """Exception raised when content extraction fails."""
    
    def __init__(self, extraction_type: str, reason: Optional[str] = None):
        message = f"Failed to extract {extraction_type}"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message=message,
            error_code="EXTRACTION_ERROR",
            details={
                "extraction_type": extraction_type,
                "reason": reason
            }
        )


class ConfigurationError(ProcessingError):
    """Exception raised when processor configuration is invalid."""

    def __init__(self, config_issue: str):
        message = f"Invalid processor configuration: {config_issue}"

        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={"config_issue": config_issue}
        )


class ProcessingQualityError(ProcessingError):
    """Exception raised when processing quality is below threshold."""

    def __init__(self, quality_score: float, threshold: float):
        message = f"Processing quality ({quality_score:.2f}) below threshold ({threshold:.2f})"

        super().__init__(
            message=message,
            error_code="QUALITY_ERROR",
            details={
                "quality_score": quality_score,
                "threshold": threshold
            }
        )
