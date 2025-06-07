"""
OCR (Optical Character Recognition) module for the DSPy-Enhanced Fact-Checker API Platform.
"""

from app.core.ocr.mistral_ocr import (
    MistralOCRProcessor,
    MistralOCRError,
    MistralOCRConfigurationError,
    MistralOCRProcessingError,
    MistralOCRRateLimitError,
    MISTRAL_AVAILABLE
)

__all__ = [
    "MistralOCRProcessor",
    "MistralOCRError",
    "MistralOCRConfigurationError", 
    "MistralOCRProcessingError",
    "MistralOCRRateLimitError",
    "MISTRAL_AVAILABLE"
]
