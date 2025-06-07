#!/usr/bin/env python3
"""
OCR Engine Interface and Base Classes
Defines the common interface for all OCR engines (cloud and local)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import time


class OCREngineType(Enum):
    """Types of OCR engines."""
    CLOUD = "cloud"
    LOCAL = "local"
    HYBRID = "hybrid"


@dataclass
class OCRQualityMetrics:
    """OCR quality assessment metrics."""
    overall_confidence: float
    text_confidence: float
    language_confidence: float
    structure_preservation: float
    word_count: int
    character_count: int
    detected_language: str
    processing_time: float


@dataclass
class OCRResult:
    """Result from OCR processing."""
    text: str
    confidence: float
    language: str
    processing_time: float
    engine_used: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    bbox_annotations: Optional[List[Dict]] = None
    word_confidences: Optional[List[float]] = None
    quality_metrics: Optional[OCRQualityMetrics] = None
    cost_estimate: Optional[float] = None
    
    def __post_init__(self):
        """Calculate quality metrics if not provided."""
        if self.quality_metrics is None:
            self.quality_metrics = self._calculate_quality_metrics()
    
    def _calculate_quality_metrics(self) -> OCRQualityMetrics:
        """Calculate basic quality metrics from OCR result."""
        word_count = len(self.text.split()) if self.text else 0
        character_count = len(self.text) if self.text else 0
        
        # Calculate average word confidence if available
        avg_word_confidence = (
            sum(self.word_confidences) / len(self.word_confidences)
            if self.word_confidences else self.confidence
        )
        
        return OCRQualityMetrics(
            overall_confidence=self.confidence,
            text_confidence=avg_word_confidence,
            language_confidence=0.9,  # Default, should be calculated by engine
            structure_preservation=0.8,  # Default, should be assessed
            word_count=word_count,
            character_count=character_count,
            detected_language=self.language,
            processing_time=self.processing_time
        )


@dataclass
class OCREngineInfo:
    """Information about an OCR engine."""
    name: str
    type: OCREngineType
    supported_languages: List[str]
    max_file_size: int
    cost_per_page: Optional[float]
    requires_api_key: bool
    offline_capable: bool
    supports_bbox: bool = False
    supports_tables: bool = False
    supports_handwriting: bool = False
    quality_rating: float = 0.8  # 0.0 to 1.0


class OCREngineInterface(ABC):
    """Abstract interface for all OCR engines."""
    
    @abstractmethod
    async def process_image(
        self, 
        image_data: bytes, 
        language: str = "en",
        **kwargs
    ) -> OCRResult:
        """
        Process an image with OCR.
        
        Args:
            image_data: Image data as bytes
            language: Language code for OCR
            **kwargs: Additional engine-specific options
            
        Returns:
            OCRResult with extracted text and metadata
        """
        pass
    
    @abstractmethod
    async def process_pdf_page(
        self, 
        pdf_page: bytes, 
        page_number: int = 1,
        language: str = "en",
        **kwargs
    ) -> OCRResult:
        """
        Process a single PDF page with OCR.
        
        Args:
            pdf_page: PDF page data as bytes
            page_number: Page number for reference
            language: Language code for OCR
            **kwargs: Additional engine-specific options
            
        Returns:
            OCRResult with extracted text and metadata
        """
        pass
    
    @abstractmethod
    def supports_language(self, language: str) -> bool:
        """
        Check if the engine supports a specific language.
        
        Args:
            language: Language code to check
            
        Returns:
            True if language is supported
        """
        pass
    
    @abstractmethod
    def get_engine_info(self) -> OCREngineInfo:
        """
        Get information about this OCR engine.
        
        Returns:
            OCREngineInfo with engine capabilities and metadata
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the OCR engine is available and properly configured.
        
        Returns:
            True if engine is ready to use
        """
        pass
    
    def estimate_cost(self, data_size: int, pages: int = 1) -> Optional[float]:
        """
        Estimate the cost of processing with this engine.
        
        Args:
            data_size: Size of data in bytes
            pages: Number of pages to process
            
        Returns:
            Estimated cost in USD, or None if free/unknown
        """
        engine_info = self.get_engine_info()
        if engine_info.cost_per_page:
            return engine_info.cost_per_page * pages
        return None
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats.
        
        Returns:
            List of supported format extensions
        """
        return ["jpg", "jpeg", "png", "pdf", "tiff", "bmp"]


class OCRQualityAssessor:
    """Assesses the quality of OCR results."""
    
    def assess_result(self, result: OCRResult) -> float:
        """
        Assess the overall quality of an OCR result.
        
        Args:
            result: OCR result to assess
            
        Returns:
            Quality score from 0.0 to 1.0
        """
        if not result.quality_metrics:
            return result.confidence
        
        metrics = result.quality_metrics
        
        # Weighted quality score
        quality_score = (
            metrics.overall_confidence * 0.4 +
            metrics.text_confidence * 0.3 +
            metrics.language_confidence * 0.2 +
            metrics.structure_preservation * 0.1
        )
        
        # Penalize very short text (likely poor OCR)
        if metrics.word_count < 5:
            quality_score *= 0.7
        
        # Penalize very long processing time
        if metrics.processing_time > 30:
            quality_score *= 0.9
        
        return min(1.0, max(0.0, quality_score))
    
    def compare_results(self, results: List[OCRResult]) -> OCRResult:
        """
        Compare multiple OCR results and return the best one.
        
        Args:
            results: List of OCR results to compare
            
        Returns:
            Best OCR result based on quality assessment
        """
        if not results:
            raise ValueError("No results to compare")
        
        if len(results) == 1:
            return results[0]
        
        best_result = results[0]
        best_score = self.assess_result(best_result)
        
        for result in results[1:]:
            score = self.assess_result(result)
            if score > best_score:
                best_score = score
                best_result = result
        
        return best_result


class CostOptimizer:
    """Optimizes OCR engine selection based on cost and quality."""
    
    def __init__(self, budget_per_document: float = 1.0):
        """
        Initialize cost optimizer.
        
        Args:
            budget_per_document: Maximum budget per document in USD
        """
        self.budget_per_document = budget_per_document
    
    def select_cost_effective_engine(
        self,
        engines: Dict[str, OCREngineInterface],
        data_size: int,
        pages: int = 1,
        quality_threshold: float = 0.7,
        **kwargs
    ) -> OCREngineInterface:
        """
        Select the most cost-effective engine that meets quality requirements.
        
        Args:
            engines: Available OCR engines
            data_size: Size of data to process
            pages: Number of pages
            quality_threshold: Minimum quality requirement
            **kwargs: Additional selection criteria
            
        Returns:
            Selected OCR engine
        """
        candidates = []
        
        for name, engine in engines.items():
            if not engine.is_available():
                continue
            
            engine_info = engine.get_engine_info()
            
            # Skip if quality rating is below threshold
            if engine_info.quality_rating < quality_threshold:
                continue
            
            cost = engine.estimate_cost(data_size, pages) or 0.0
            
            # Skip if cost exceeds budget
            if cost > self.budget_per_document:
                continue
            
            candidates.append({
                "engine": engine,
                "cost": cost,
                "quality": engine_info.quality_rating,
                "name": name
            })
        
        if not candidates:
            # Fallback to any available engine
            for engine in engines.values():
                if engine.is_available():
                    return engine
            raise RuntimeError("No available OCR engines")
        
        # Sort by cost-effectiveness (quality/cost ratio)
        candidates.sort(
            key=lambda x: x["quality"] / max(x["cost"], 0.001),
            reverse=True
        )
        
        return candidates[0]["engine"]
