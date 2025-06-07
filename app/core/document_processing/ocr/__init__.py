"""
OCR Engine Abstraction Layer for Enhanced Document Processing
Provides unified interface for multiple OCR engines including Mistral API and local engines
"""

from app.core.document_processing.ocr.base import (
    OCREngineInterface,
    OCRResult,
    OCREngineInfo,
    OCREngineType,
    OCRQualityMetrics
)

try:
    from app.core.document_processing.ocr.mistral_engine import MistralOCREngine
    MISTRAL_OCR_ENGINE_AVAILABLE = True
except ImportError:
    MistralOCREngine = None
    MISTRAL_OCR_ENGINE_AVAILABLE = False

try:
    from app.core.document_processing.ocr.local_engines import (
        EasyOCREngine,
        TesseractOCREngine,
        RapidOCREngine
    )
    LOCAL_OCR_ENGINES_AVAILABLE = True
except ImportError:
    EasyOCREngine = None
    TesseractOCREngine = None
    RapidOCREngine = None
    LOCAL_OCR_ENGINES_AVAILABLE = False

from app.core.document_processing.ocr.factory import OCREngineFactory

__all__ = [
    "OCREngineInterface",
    "OCRResult", 
    "OCREngineInfo",
    "OCREngineType",
    "OCRQualityMetrics",
    "MistralOCREngine",
    "EasyOCREngine",
    "TesseractOCREngine", 
    "RapidOCREngine",
    "OCREngineFactory",
    "MISTRAL_OCR_ENGINE_AVAILABLE",
    "LOCAL_OCR_ENGINES_AVAILABLE"
]
