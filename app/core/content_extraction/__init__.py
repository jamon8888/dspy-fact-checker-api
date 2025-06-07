"""
Content Extraction Module

This module provides advanced content extraction capabilities for URLs and text processing.
It includes multiple extraction strategies, content type detection, and quality assessment.
"""

from .models import (
    ExtractionOptions, ExtractedWebContent, TextProcessingOptions,
    ProcessedTextContent, ExtractionStrategy, ContentType, SegmentationStrategy,
    LanguageInfo, URLAnalysis, ContentStructure, TextSegment, PotentialClaim
)
from .url_extractor import URLContentExtractor
from .text_processor import AdvancedTextProcessor
from .exceptions import (
    ContentExtractionError,
    URLExtractionError,
    TextProcessingError,
    ContentQualityError
)

__all__ = [
    "URLContentExtractor",
    "ExtractionOptions", 
    "ExtractedWebContent",
    "AdvancedTextProcessor",
    "TextProcessingOptions",
    "ProcessedTextContent",
    "ContentExtractionError",
    "URLExtractionError", 
    "TextProcessingError",
    "ContentQualityError"
]
