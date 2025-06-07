"""
Content Extraction Exceptions

Custom exception classes for content extraction and text processing operations.
"""

from typing import Optional, Dict, Any


class ContentExtractionError(Exception):
    """Base exception for content extraction operations."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class URLExtractionError(ContentExtractionError):
    """Exception raised when URL content extraction fails."""
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.url = url
        self.status_code = status_code


class TextProcessingError(ContentExtractionError):
    """Exception raised when text processing fails."""
    
    def __init__(
        self, 
        message: str, 
        text_length: Optional[int] = None,
        processing_stage: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.text_length = text_length
        self.processing_stage = processing_stage


class ContentQualityError(ContentExtractionError):
    """Exception raised when content quality is below acceptable threshold."""
    
    def __init__(
        self, 
        message: str, 
        quality_score: Optional[float] = None,
        min_threshold: Optional[float] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.quality_score = quality_score
        self.min_threshold = min_threshold


class ExtractionTimeoutError(URLExtractionError):
    """Exception raised when content extraction times out."""
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(message, url, None, error_code)
        self.timeout_seconds = timeout_seconds


class UnsupportedContentTypeError(URLExtractionError):
    """Exception raised when content type is not supported."""
    
    def __init__(
        self, 
        message: str, 
        content_type: Optional[str] = None,
        url: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(message, url, None, error_code)
        self.content_type = content_type


class LanguageDetectionError(TextProcessingError):
    """Exception raised when language detection fails."""
    
    def __init__(
        self, 
        message: str, 
        text_sample: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(message, None, "language_detection", error_code)
        self.text_sample = text_sample[:100] if text_sample else None


class ClaimDetectionError(TextProcessingError):
    """Exception raised when claim detection fails."""
    
    def __init__(
        self, 
        message: str, 
        text_segment: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(message, None, "claim_detection", error_code)
        self.text_segment = text_segment[:200] if text_segment else None
