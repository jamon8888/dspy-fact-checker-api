"""
Data models for the multi-model optimization system.

This module contains Pydantic models that define the data structures
used throughout the optimization pipeline.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator


class DocumentComplexity(str, Enum):
    """Document complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class OptimizationStrategy(str, Enum):
    """Available optimization strategies."""
    MIPRO_V2 = "mipro_v2"
    BOOTSTRAP_RS = "bootstrap_rs"
    ENSEMBLE = "ensemble"
    ADAPTIVE = "adaptive"


class ModelCapability(str, Enum):
    """Model capabilities."""
    COMPLEX_REASONING = "complex_reasoning"
    MULTILINGUAL = "multilingual"
    LARGE_CONTEXT = "large_context"
    FAST_PROCESSING = "fast_processing"
    COST_EFFECTIVE = "cost_effective"
    ANALYTICAL_REASONING = "analytical_reasoning"
    LONG_DOCUMENTS = "long_documents"


class DocumentCharacteristics(BaseModel):
    """Characteristics of a document for optimization."""
    
    document_type: str = Field(..., description="Type of document")
    estimated_tokens: int = Field(..., description="Estimated token count")
    complexity_score: float = Field(..., ge=0.0, le=1.0, description="Document complexity score")
    language: str = Field(default="en", description="Document language")
    domain: Optional[str] = Field(None, description="Document domain (academic, news, legal, etc.)")
    
    # Content characteristics
    has_tables: bool = Field(default=False, description="Contains tables")
    has_images: bool = Field(default=False, description="Contains images")
    has_citations: bool = Field(default=False, description="Contains citations")
    has_formulas: bool = Field(default=False, description="Contains mathematical formulas")
    
    # Processing requirements
    requires_ocr: bool = Field(default=False, description="Requires OCR processing")
    requires_translation: bool = Field(default=False, description="Requires translation")
    requires_specialized_knowledge: bool = Field(default=False, description="Requires domain expertise")
    
    @validator('complexity_score')
    def validate_complexity(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Complexity score must be between 0.0 and 1.0')
        return v


class ProcessingRequirements(BaseModel):
    """Requirements for document processing."""
    
    max_latency: Optional[float] = Field(None, description="Maximum acceptable latency in seconds")
    max_cost: Optional[float] = Field(None, description="Maximum acceptable cost")
    accuracy_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="Minimum accuracy required")
    
    # Quality requirements
    require_citations: bool = Field(default=True, description="Require citation verification")
    require_uncertainty_quantification: bool = Field(default=True, description="Require uncertainty metrics")
    require_specialized_analysis: bool = Field(default=False, description="Require specialized modules")
    
    # Processing preferences
    prefer_speed: bool = Field(default=False, description="Prioritize speed over accuracy")
    prefer_accuracy: bool = Field(default=True, description="Prioritize accuracy over speed")
    prefer_cost_efficiency: bool = Field(default=False, description="Prioritize cost efficiency")
    
    @validator('accuracy_threshold')
    def validate_accuracy(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Accuracy threshold must be between 0.0 and 1.0')
        return v


class UserConstraints(BaseModel):
    """User-specific constraints for optimization."""
    
    user_tier: str = Field(default="free", description="User subscription tier")
    monthly_quota: Optional[int] = Field(None, description="Monthly processing quota")
    remaining_quota: Optional[int] = Field(None, description="Remaining quota this month")
    
    # Cost constraints
    max_cost_per_request: Optional[float] = Field(None, description="Maximum cost per request")
    monthly_budget: Optional[float] = Field(None, description="Monthly budget limit")
    remaining_budget: Optional[float] = Field(None, description="Remaining budget this month")
    
    # Performance constraints
    max_processing_time: Optional[float] = Field(None, description="Maximum processing time")
    priority_level: str = Field(default="normal", description="Processing priority level")
    
    # Feature access
    has_premium_features: bool = Field(default=False, description="Access to premium features")
    has_api_access: bool = Field(default=True, description="API access enabled")
    has_bulk_processing: bool = Field(default=False, description="Bulk processing access")


class ModelConfiguration(BaseModel):
    """Configuration for a specific model."""
    
    model_name: str = Field(..., description="Model identifier")
    capabilities: List[ModelCapability] = Field(..., description="Model capabilities")
    cost_per_token: float = Field(..., description="Cost per token")
    avg_latency: float = Field(..., description="Average latency in seconds")
    max_context: int = Field(..., description="Maximum context length")
    
    # Performance metrics
    accuracy_score: Optional[float] = Field(None, description="Historical accuracy score")
    reliability_score: Optional[float] = Field(None, description="Reliability score")
    
    # Availability
    is_available: bool = Field(default=True, description="Model availability")
    rate_limit: Optional[int] = Field(None, description="Rate limit per minute")


class ModelRoutingDecision(BaseModel):
    """Decision made by the model router."""
    
    selected_model: str = Field(..., description="Selected model name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in selection")
    reasoning: str = Field(..., description="Reasoning for selection")
    
    # Alternatives
    alternatives: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative models")
    
    # Estimates
    estimated_cost: float = Field(..., description="Estimated processing cost")
    estimated_latency: float = Field(..., description="Estimated processing time")
    estimated_accuracy: Optional[float] = Field(None, description="Estimated accuracy")
    
    # Metadata
    routing_timestamp: datetime = Field(default_factory=datetime.now)
    routing_version: str = Field(default="1.0", description="Router version")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class OptimizationConfig(BaseModel):
    """Configuration for optimization process."""
    
    strategy: OptimizationStrategy = Field(..., description="Optimization strategy to use")
    target_metrics: List[str] = Field(..., description="Metrics to optimize for")
    
    # Optimization parameters
    max_iterations: int = Field(default=100, description="Maximum optimization iterations")
    convergence_threshold: float = Field(default=0.001, description="Convergence threshold")
    early_stopping: bool = Field(default=True, description="Enable early stopping")
    
    # Cost constraints
    cost_constraints: Optional[Dict[str, float]] = Field(None, description="Cost constraints")
    time_constraints: Optional[Dict[str, float]] = Field(None, description="Time constraints")
    
    # Advanced options
    use_ensemble: bool = Field(default=False, description="Use ensemble methods")
    cross_validation_folds: int = Field(default=5, description="Cross-validation folds")
    random_seed: Optional[int] = Field(None, description="Random seed for reproducibility")


class OptimizedComponent(BaseModel):
    """An optimized component of the processing pipeline."""
    
    component_type: str = Field(..., description="Type of component")
    optimized_parameters: Dict[str, Any] = Field(..., description="Optimized parameters")
    performance_metrics: Dict[str, float] = Field(..., description="Performance metrics")
    
    # Optimization details
    optimization_strategy: str = Field(..., description="Strategy used for optimization")
    optimization_time: float = Field(..., description="Time taken for optimization")
    iterations_completed: int = Field(..., description="Optimization iterations completed")
    
    # Validation results
    validation_score: Optional[float] = Field(None, description="Validation score")
    cross_validation_scores: Optional[List[float]] = Field(None, description="CV scores")


class OptimizedPipeline(BaseModel):
    """Complete optimized processing pipeline."""
    
    pipeline_id: str = Field(..., description="Unique pipeline identifier")
    document_type: str = Field(..., description="Document type this pipeline is optimized for")
    
    # Components
    components: Dict[str, OptimizedComponent] = Field(..., description="Optimized components")
    routing_strategy: ModelRoutingDecision = Field(..., description="Model routing strategy")
    
    # Performance
    overall_performance: Dict[str, float] = Field(..., description="Overall pipeline performance")
    estimated_improvement: Optional[float] = Field(None, description="Estimated improvement over baseline")
    
    # Metadata
    optimization_metadata: Dict[str, Any] = Field(..., description="Optimization metadata")
    creation_timestamp: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0", description="Pipeline version")
    
    # Usage tracking
    usage_count: int = Field(default=0, description="Number of times used")
    success_rate: Optional[float] = Field(None, description="Success rate in production")


class PerformanceMetrics(BaseModel):
    """Performance metrics for tracking."""
    
    accuracy: Optional[float] = Field(None, description="Accuracy score")
    precision: Optional[float] = Field(None, description="Precision score")
    recall: Optional[float] = Field(None, description="Recall score")
    f1_score: Optional[float] = Field(None, description="F1 score")
    
    # Processing metrics
    processing_time: float = Field(..., description="Processing time in seconds")
    cost: float = Field(..., description="Processing cost")
    tokens_processed: int = Field(..., description="Number of tokens processed")
    
    # Quality metrics
    confidence_score: Optional[float] = Field(None, description="Confidence in results")
    uncertainty_score: Optional[float] = Field(None, description="Uncertainty score")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    model_used: str = Field(..., description="Model used for processing")
    document_type: str = Field(..., description="Document type processed")


class OptimizationResult(BaseModel):
    """Result of an optimization process."""
    
    optimization_id: str = Field(..., description="Unique optimization identifier")
    strategy_used: OptimizationStrategy = Field(..., description="Strategy used")
    
    # Results
    optimized_pipeline: OptimizedPipeline = Field(..., description="Optimized pipeline")
    baseline_performance: Dict[str, float] = Field(..., description="Baseline performance")
    optimized_performance: Dict[str, float] = Field(..., description="Optimized performance")
    improvement_metrics: Dict[str, float] = Field(..., description="Improvement metrics")
    
    # Process details
    optimization_time: float = Field(..., description="Total optimization time")
    iterations_completed: int = Field(..., description="Iterations completed")
    convergence_achieved: bool = Field(..., description="Whether convergence was achieved")
    
    # Validation
    validation_results: Optional[Dict[str, Any]] = Field(None, description="Validation results")
    cross_validation_score: Optional[float] = Field(None, description="Cross-validation score")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    configuration: OptimizationConfig = Field(..., description="Configuration used")
    notes: Optional[str] = Field(None, description="Additional notes")
