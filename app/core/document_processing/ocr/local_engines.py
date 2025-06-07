#!/usr/bin/env python3
"""
Local OCR Engines Implementation
Implements EasyOCR, Tesseract, and RapidOCR engines for offline processing
"""

import logging
import time
import tempfile
import os
from typing import Dict, Any, List, Optional
from PIL import Image
import io

from app.core.document_processing.ocr.base import (
    OCREngineInterface, OCRResult, OCREngineInfo, OCREngineType, OCRQualityMetrics
)

logger = logging.getLogger(__name__)


class LocalOCREngineError(Exception):
    """Base exception for local OCR engine errors."""
    pass


class EasyOCREngine(OCREngineInterface):
    """EasyOCR engine implementation."""
    
    def __init__(self, languages: List[str] = None):
        """
        Initialize EasyOCR engine.
        
        Args:
            languages: List of language codes (default: ["en"])
        """
        self.languages = languages or ["en"]
        self.reader = None
        self._initialize_reader()
    
    def _initialize_reader(self):
        """Initialize EasyOCR reader."""
        try:
            import easyocr
            self.reader = easyocr.Reader(self.languages, gpu=False)
            logger.info(f"EasyOCR initialized with languages: {self.languages}")
        except ImportError:
            logger.warning("EasyOCR not available - install easyocr package")
            self.reader = None
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            self.reader = None
    
    async def process_image(self, image_data: bytes, language: str = "en", **kwargs) -> OCRResult:
        """Process image with EasyOCR."""
        start_time = time.time()
        
        try:
            if not self.reader:
                raise LocalOCREngineError("EasyOCR reader not initialized")
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Process with EasyOCR
            results = self.reader.readtext(image, detail=1)
            
            # Extract text and confidence
            text_parts = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                text_parts.append(text)
                confidences.append(confidence)
            
            full_text = " ".join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            processing_time = time.time() - start_time
            
            # Create quality metrics
            quality_metrics = OCRQualityMetrics(
                overall_confidence=avg_confidence,
                text_confidence=avg_confidence,
                language_confidence=0.8,  # EasyOCR has good language detection
                structure_preservation=0.7,  # Moderate structure preservation
                word_count=len(full_text.split()) if full_text else 0,
                character_count=len(full_text) if full_text else 0,
                detected_language=language,
                processing_time=processing_time
            )
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                language=language,
                processing_time=processing_time,
                engine_used="easyocr",
                metadata={
                    "num_detections": len(results),
                    "languages_used": self.languages
                },
                word_confidences=confidences,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            logger.error(f"EasyOCR processing failed: {e}")
            raise LocalOCREngineError(f"EasyOCR processing failed: {str(e)}")
    
    async def process_pdf_page(self, pdf_page: bytes, page_number: int = 1, language: str = "en", **kwargs) -> OCRResult:
        """Process PDF page with EasyOCR (converts to image first)."""
        try:
            # Convert PDF page to image
            import fitz  # PyMuPDF
            
            doc = fitz.open(stream=pdf_page, filetype="pdf")
            page = doc[0]  # First page
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            doc.close()
            
            # Process as image
            result = await self.process_image(img_data, language, **kwargs)
            result.metadata["page_number"] = page_number
            result.metadata["converted_from_pdf"] = True
            
            return result
            
        except ImportError:
            raise LocalOCREngineError("PyMuPDF not available for PDF processing")
        except Exception as e:
            logger.error(f"EasyOCR PDF processing failed: {e}")
            raise LocalOCREngineError(f"PDF processing failed: {str(e)}")
    
    def supports_language(self, language: str) -> bool:
        """Check if EasyOCR supports the language."""
        # EasyOCR supports many languages
        supported = [
            "en", "fr", "de", "es", "it", "pt", "nl", "ru", "zh", "ja", "ko", "ar",
            "th", "vi", "hi", "bn", "ta", "te", "kn", "ml", "gu", "pa", "or", "as"
        ]
        return language.lower() in supported
    
    def get_engine_info(self) -> OCREngineInfo:
        """Get EasyOCR engine information."""
        return OCREngineInfo(
            name="EasyOCR",
            type=OCREngineType.LOCAL,
            supported_languages=[
                "en", "fr", "de", "es", "it", "pt", "nl", "ru", "zh", "ja", "ko", "ar",
                "th", "vi", "hi", "bn", "ta", "te", "kn", "ml", "gu", "pa", "or", "as"
            ],
            max_file_size=50 * 1024 * 1024,  # 50MB
            cost_per_page=None,  # Free
            requires_api_key=False,
            offline_capable=True,
            supports_bbox=True,
            supports_tables=False,
            supports_handwriting=True,
            quality_rating=0.85
        )
    
    def is_available(self) -> bool:
        """Check if EasyOCR is available."""
        return self.reader is not None


class TesseractOCREngine(OCREngineInterface):
    """Tesseract OCR engine implementation."""
    
    def __init__(self, config: str = "--psm 6"):
        """
        Initialize Tesseract OCR engine.
        
        Args:
            config: Tesseract configuration string
        """
        self.config = config
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Tesseract is available."""
        try:
            import pytesseract

            # Set Tesseract path for Windows if not in PATH
            if os.name == 'nt':  # Windows
                tesseract_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    r"C:\Tesseract-OCR\tesseract.exe"
                ]

                for path in tesseract_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        logger.info(f"Set Tesseract binary path to: {path}")
                        break

                # Set TESSDATA_PREFIX - use backslashes for Windows
                tessdata_paths = [
                    r"C:\Program Files\Tesseract-OCR\tessdata",
                    r"C:\Program Files (x86)\Tesseract-OCR\tessdata",
                    r"C:\Tesseract-OCR\tessdata"
                ]

                for path in tessdata_paths:
                    if os.path.exists(path):
                        # Use Windows path format
                        os.environ['TESSDATA_PREFIX'] = path.replace('/', '\\')
                        logger.info(f"Set TESSDATA_PREFIX to: {path}")

                        # Also try setting it without trailing slash
                        if path.endswith('\\'):
                            os.environ['TESSDATA_PREFIX'] = path[:-1]
                        break

            # Try to get version to check if Tesseract binary is available
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR is available and configured")
            return True
        except ImportError:
            logger.warning("pytesseract not available")
            return False
        except Exception as e:
            logger.warning(f"Tesseract binary not available: {e}")
            return False
    
    async def process_image(self, image_data: bytes, language: str = "en", **kwargs) -> OCRResult:
        """Process image with Tesseract."""
        start_time = time.time()
        
        try:
            if not self.available:
                raise LocalOCREngineError("Tesseract not available")
            
            import pytesseract
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Process with Tesseract
            text = pytesseract.image_to_string(image, lang=language, config=self.config)
            
            # Get confidence data
            try:
                data = pytesseract.image_to_data(image, lang=language, config=self.config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.5
            except:
                avg_confidence = 0.7  # Default confidence
            
            processing_time = time.time() - start_time
            
            # Create quality metrics
            quality_metrics = OCRQualityMetrics(
                overall_confidence=avg_confidence,
                text_confidence=avg_confidence,
                language_confidence=0.9,  # Tesseract has excellent language support
                structure_preservation=0.8,  # Good structure preservation
                word_count=len(text.split()) if text else 0,
                character_count=len(text) if text else 0,
                detected_language=language,
                processing_time=processing_time
            )
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                language=language,
                processing_time=processing_time,
                engine_used="tesseract",
                metadata={
                    "config": self.config,
                    "tesseract_version": pytesseract.get_tesseract_version()
                },
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            logger.error(f"Tesseract processing failed: {e}")
            raise LocalOCREngineError(f"Tesseract processing failed: {str(e)}")
    
    async def process_pdf_page(self, pdf_page: bytes, page_number: int = 1, language: str = "en", **kwargs) -> OCRResult:
        """Process PDF page with Tesseract (converts to image first)."""
        try:
            # Convert PDF page to image
            import fitz  # PyMuPDF
            
            doc = fitz.open(stream=pdf_page, filetype="pdf")
            page = doc[0]  # First page
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            doc.close()
            
            # Process as image
            result = await self.process_image(img_data, language, **kwargs)
            result.metadata["page_number"] = page_number
            result.metadata["converted_from_pdf"] = True
            
            return result
            
        except ImportError:
            raise LocalOCREngineError("PyMuPDF not available for PDF processing")
        except Exception as e:
            logger.error(f"Tesseract PDF processing failed: {e}")
            raise LocalOCREngineError(f"PDF processing failed: {str(e)}")
    
    def supports_language(self, language: str) -> bool:
        """Check if Tesseract supports the language."""
        # Tesseract supports many languages
        supported = [
            "en", "fr", "de", "es", "it", "pt", "nl", "ru", "zh", "ja", "ko", "ar",
            "hi", "bn", "ta", "te", "kn", "ml", "gu", "pa", "or", "as", "th", "vi"
        ]
        return language.lower() in supported
    
    def get_engine_info(self) -> OCREngineInfo:
        """Get Tesseract engine information."""
        return OCREngineInfo(
            name="Tesseract OCR",
            type=OCREngineType.LOCAL,
            supported_languages=[
                "en", "fr", "de", "es", "it", "pt", "nl", "ru", "zh", "ja", "ko", "ar",
                "hi", "bn", "ta", "te", "kn", "ml", "gu", "pa", "or", "as", "th", "vi"
            ],
            max_file_size=100 * 1024 * 1024,  # 100MB
            cost_per_page=None,  # Free
            requires_api_key=False,
            offline_capable=True,
            supports_bbox=True,
            supports_tables=False,
            supports_handwriting=False,
            quality_rating=0.80
        )
    
    def is_available(self) -> bool:
        """Check if Tesseract is available."""
        return self.available


class RapidOCREngine(OCREngineInterface):
    """RapidOCR engine implementation."""
    
    def __init__(self):
        """Initialize RapidOCR engine."""
        self.ocr = None
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Initialize RapidOCR."""
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr = RapidOCR()
            logger.info("RapidOCR initialized successfully")
        except ImportError:
            logger.warning("RapidOCR not available - install rapidocr-onnxruntime package")
            self.ocr = None
        except Exception as e:
            logger.error(f"Failed to initialize RapidOCR: {e}")
            self.ocr = None
    
    async def process_image(self, image_data: bytes, language: str = "en", **kwargs) -> OCRResult:
        """Process image with RapidOCR."""
        start_time = time.time()
        
        try:
            if not self.ocr:
                raise LocalOCREngineError("RapidOCR not initialized")
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Process with RapidOCR
            result, elapse = self.ocr(image)
            
            # Extract text and confidence
            if result:
                text_parts = []
                confidences = []
                
                for line in result:
                    text_parts.append(line[1])
                    confidences.append(line[2])
                
                full_text = " ".join(text_parts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            else:
                full_text = ""
                avg_confidence = 0.0
                confidences = []
            
            processing_time = time.time() - start_time
            
            # Create quality metrics
            quality_metrics = OCRQualityMetrics(
                overall_confidence=avg_confidence,
                text_confidence=avg_confidence,
                language_confidence=0.7,  # RapidOCR has moderate language detection
                structure_preservation=0.75,  # Good structure preservation
                word_count=len(full_text.split()) if full_text else 0,
                character_count=len(full_text) if full_text else 0,
                detected_language=language,
                processing_time=processing_time
            )
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                language=language,
                processing_time=processing_time,
                engine_used="rapidocr",
                metadata={
                    "num_detections": len(result) if result else 0,
                    "rapidocr_elapse": elapse
                },
                word_confidences=confidences,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            logger.error(f"RapidOCR processing failed: {e}")
            raise LocalOCREngineError(f"RapidOCR processing failed: {str(e)}")
    
    async def process_pdf_page(self, pdf_page: bytes, page_number: int = 1, language: str = "en", **kwargs) -> OCRResult:
        """Process PDF page with RapidOCR (converts to image first)."""
        try:
            # Convert PDF page to image
            import fitz  # PyMuPDF
            
            doc = fitz.open(stream=pdf_page, filetype="pdf")
            page = doc[0]  # First page
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            doc.close()
            
            # Process as image
            result = await self.process_image(img_data, language, **kwargs)
            result.metadata["page_number"] = page_number
            result.metadata["converted_from_pdf"] = True
            
            return result
            
        except ImportError:
            raise LocalOCREngineError("PyMuPDF not available for PDF processing")
        except Exception as e:
            logger.error(f"RapidOCR PDF processing failed: {e}")
            raise LocalOCREngineError(f"PDF processing failed: {str(e)}")
    
    def supports_language(self, language: str) -> bool:
        """Check if RapidOCR supports the language."""
        # RapidOCR primarily supports Chinese and English
        supported = ["en", "zh", "ch"]
        return language.lower() in supported
    
    def get_engine_info(self) -> OCREngineInfo:
        """Get RapidOCR engine information."""
        return OCREngineInfo(
            name="RapidOCR",
            type=OCREngineType.LOCAL,
            supported_languages=["en", "zh", "ch"],
            max_file_size=50 * 1024 * 1024,  # 50MB
            cost_per_page=None,  # Free
            requires_api_key=False,
            offline_capable=True,
            supports_bbox=True,
            supports_tables=False,
            supports_handwriting=True,
            quality_rating=0.75
        )
    
    def is_available(self) -> bool:
        """Check if RapidOCR is available."""
        return self.ocr is not None
