#!/usr/bin/env python3
"""
OCR Engine Factory
Creates and manages OCR engine instances with configuration validation
"""

import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field

from app.core.document_processing.ocr.base import (
    OCREngineInterface, OCRQualityAssessor, CostOptimizer
)

logger = logging.getLogger(__name__)


@dataclass
class OCREngineConfiguration:
    """Configuration for OCR engine selection and management."""
    primary_ocr_engine: str = "easyocr"
    fallback_ocr_engines: List[str] = field(default_factory=lambda: ["tesseract"])
    enable_ocr_fallback: bool = True
    ocr_quality_threshold: float = 0.7
    cost_optimization: bool = False
    local_ocr_priority: bool = True
    budget_per_document: float = 1.0
    
    # Engine-specific configurations
    mistral_api_key: Optional[str] = None
    mistral_model: str = "mistral-ocr-latest"
    mistral_timeout: int = 300
    
    easyocr_languages: List[str] = field(default_factory=lambda: ["en"])
    tesseract_config: str = "--psm 6"
    
    # Performance settings
    max_concurrent_requests: int = 5
    cache_results: bool = True
    cache_ttl_seconds: int = 3600


class OCREngineFactory:
    """Factory for creating and managing OCR engines."""
    
    def __init__(self, config: OCREngineConfiguration):
        """
        Initialize OCR engine factory.
        
        Args:
            config: OCR engine configuration
        """
        self.config = config
        self.engines: Dict[str, OCREngineInterface] = {}
        self.quality_assessor = OCRQualityAssessor()
        self.cost_optimizer = CostOptimizer(config.budget_per_document)
        
        logger.info("OCR Engine Factory initialized")
    
    async def initialize_engines(self) -> Dict[str, OCREngineInterface]:
        """
        Initialize all configured OCR engines.
        
        Returns:
            Dictionary of initialized engines
        """
        try:
            # Initialize Mistral OCR if configured
            if self.config.mistral_api_key:
                await self._initialize_mistral_engine()
            
            # Initialize local OCR engines
            await self._initialize_local_engines()
            
            logger.info(f"Initialized {len(self.engines)} OCR engines: {list(self.engines.keys())}")
            return self.engines
            
        except Exception as e:
            logger.error(f"Failed to initialize OCR engines: {e}")
            raise
    
    async def _initialize_mistral_engine(self):
        """Initialize Mistral OCR engine."""
        try:
            from app.core.document_processing.ocr.mistral_engine import MistralOCREngine
            
            engine = MistralOCREngine(
                api_key=self.config.mistral_api_key,
                model=self.config.mistral_model,
                timeout_seconds=self.config.mistral_timeout
            )
            
            if engine.is_available():
                self.engines["mistral"] = engine
                logger.info("Mistral OCR engine initialized successfully")
            else:
                logger.warning("Mistral OCR engine not available")
                
        except ImportError:
            logger.warning("Mistral OCR engine not available - missing dependencies")
        except Exception as e:
            logger.error(f"Failed to initialize Mistral OCR engine: {e}")
    
    async def _initialize_local_engines(self):
        """Initialize local OCR engines."""
        try:
            from app.core.document_processing.ocr.local_engines import (
                EasyOCREngine, TesseractOCREngine, RapidOCREngine
            )
            
            # Initialize EasyOCR
            try:
                easyocr_engine = EasyOCREngine(languages=self.config.easyocr_languages)
                if easyocr_engine.is_available():
                    self.engines["easyocr"] = easyocr_engine
                    logger.info("EasyOCR engine initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize EasyOCR: {e}")
            
            # Initialize Tesseract
            try:
                tesseract_engine = TesseractOCREngine(config=self.config.tesseract_config)
                if tesseract_engine.is_available():
                    self.engines["tesseract"] = tesseract_engine
                    logger.info("Tesseract OCR engine initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Tesseract: {e}")
            
            # Initialize RapidOCR
            try:
                rapidocr_engine = RapidOCREngine()
                if rapidocr_engine.is_available():
                    self.engines["rapidocr"] = rapidocr_engine
                    logger.info("RapidOCR engine initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize RapidOCR: {e}")
                
        except ImportError:
            logger.warning("Local OCR engines not available - missing dependencies")
        except Exception as e:
            logger.error(f"Failed to initialize local OCR engines: {e}")
    
    def get_engine(self, engine_name: str) -> Optional[OCREngineInterface]:
        """
        Get a specific OCR engine by name.
        
        Args:
            engine_name: Name of the engine to retrieve
            
        Returns:
            OCR engine instance or None if not available
        """
        return self.engines.get(engine_name)
    
    def get_available_engines(self) -> List[str]:
        """
        Get list of available engine names.
        
        Returns:
            List of available engine names
        """
        return [name for name, engine in self.engines.items() if engine.is_available()]
    
    def select_optimal_engine(
        self,
        data_size: int,
        pages: int = 1,
        language: str = "en",
        quality_requirement: float = None,
        **kwargs
    ) -> OCREngineInterface:
        """
        Select the optimal OCR engine based on configuration and requirements.
        
        Args:
            data_size: Size of data to process
            pages: Number of pages
            language: Language code
            quality_requirement: Minimum quality requirement
            **kwargs: Additional selection criteria
            
        Returns:
            Selected OCR engine
        """
        quality_threshold = quality_requirement or self.config.ocr_quality_threshold
        
        # Filter engines by language support
        compatible_engines = {
            name: engine for name, engine in self.engines.items()
            if engine.is_available() and engine.supports_language(language)
        }
        
        if not compatible_engines:
            # Fallback to any available engine
            compatible_engines = {
                name: engine for name, engine in self.engines.items()
                if engine.is_available()
            }
        
        if not compatible_engines:
            raise RuntimeError("No available OCR engines")
        
        # Cost optimization
        if self.config.cost_optimization:
            return self.cost_optimizer.select_cost_effective_engine(
                compatible_engines, data_size, pages, quality_threshold
            )
        
        # Local priority
        if self.config.local_ocr_priority:
            local_engines = [
                "easyocr", "tesseract", "rapidocr"
            ]
            for engine_name in local_engines:
                if engine_name in compatible_engines:
                    return compatible_engines[engine_name]
        
        # Primary engine preference
        if self.config.primary_ocr_engine in compatible_engines:
            return compatible_engines[self.config.primary_ocr_engine]
        
        # Fallback to first available
        return next(iter(compatible_engines.values()))
    
    async def process_with_fallback(
        self,
        data: bytes,
        data_type: str,
        language: str = "en",
        **kwargs
    ) -> 'OCRResult':
        """
        Process data with automatic fallback between engines.
        
        Args:
            data: Data to process
            data_type: Type of data ("image" or "pdf_page")
            language: Language code
            **kwargs: Additional processing options
            
        Returns:
            OCR result from the best available engine
        """
        # Select primary engine
        primary_engine = self.select_optimal_engine(
            data_size=len(data),
            language=language,
            **kwargs
        )
        
        # Try primary engine
        try:
            if data_type == "image":
                result = await primary_engine.process_image(data, language, **kwargs)
            else:
                page_number = kwargs.get("page_number", 1)
                result = await primary_engine.process_pdf_page(data, page_number, language, **kwargs)
            
            # Check quality
            quality_score = self.quality_assessor.assess_result(result)
            
            if quality_score >= self.config.ocr_quality_threshold:
                return result
            
            logger.info(f"Primary engine quality ({quality_score:.2f}) below threshold, trying fallback")
            
        except Exception as e:
            logger.warning(f"Primary OCR engine failed: {e}")
        
        # Try fallback engines if enabled
        if self.config.enable_ocr_fallback:
            return await self._try_fallback_engines(data, data_type, language, **kwargs)
        
        # Return primary result even if quality is low
        return result
    
    async def _try_fallback_engines(
        self,
        data: bytes,
        data_type: str,
        language: str,
        **kwargs
    ) -> 'OCRResult':
        """Try fallback engines in order."""
        results = []
        
        for engine_name in self.config.fallback_ocr_engines:
            engine = self.engines.get(engine_name)
            if not engine or not engine.is_available():
                continue
            
            try:
                if data_type == "image":
                    result = await engine.process_image(data, language, **kwargs)
                else:
                    page_number = kwargs.get("page_number", 1)
                    result = await engine.process_pdf_page(data, page_number, language, **kwargs)
                
                results.append(result)
                
                # Check if this result meets quality threshold
                quality_score = self.quality_assessor.assess_result(result)
                if quality_score >= self.config.ocr_quality_threshold:
                    logger.info(f"Fallback engine {engine_name} met quality threshold")
                    return result
                
            except Exception as e:
                logger.warning(f"Fallback engine {engine_name} failed: {e}")
                continue
        
        # Return best result if we have any
        if results:
            best_result = self.quality_assessor.compare_results(results)
            logger.info(f"Returning best result from {best_result.engine_used}")
            return best_result
        
        # Last resort - raise error
        raise RuntimeError("All OCR engines failed")
    
    def get_engine_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all engines.
        
        Returns:
            Dictionary with engine status information
        """
        status = {}
        
        for name, engine in self.engines.items():
            engine_info = engine.get_engine_info()
            status[name] = {
                "available": engine.is_available(),
                "type": engine_info.type.value,
                "supported_languages": engine_info.supported_languages,
                "quality_rating": engine_info.quality_rating,
                "cost_per_page": engine_info.cost_per_page,
                "offline_capable": engine_info.offline_capable
            }
        
        return status
