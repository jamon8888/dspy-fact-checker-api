"""
Multi-Model Optimization System

This module provides advanced optimization capabilities for document processing
with intelligent model routing, performance tracking, and cost optimization.
"""

# Import with error handling
try:
    from .data_models import (
        DocumentCharacteristics, ProcessingRequirements, UserConstraints,
        ModelRoutingDecision, OptimizedPipeline, OptimizationConfig
    )
    DATA_MODELS_AVAILABLE = True
except ImportError as e:
    DATA_MODELS_AVAILABLE = False
    DocumentCharacteristics = None
    ProcessingRequirements = None
    UserConstraints = None
    ModelRoutingDecision = None
    OptimizedPipeline = None
    OptimizationConfig = None

try:
    from .optimizer import DocumentProcessingOptimizer
    OPTIMIZER_AVAILABLE = True
except ImportError as e:
    OPTIMIZER_AVAILABLE = False
    DocumentProcessingOptimizer = None

try:
    from .model_router import IntelligentModelRouter
    MODEL_ROUTER_AVAILABLE = True
except ImportError as e:
    MODEL_ROUTER_AVAILABLE = False
    IntelligentModelRouter = None

try:
    from .strategies import (
        MIPROv2Optimizer, BootstrapRSOptimizer,
        EnsembleOptimizer, AdaptiveOptimizer
    )
    STRATEGIES_AVAILABLE = True
except ImportError as e:
    STRATEGIES_AVAILABLE = False
    MIPROv2Optimizer = None
    BootstrapRSOptimizer = None
    EnsembleOptimizer = None
    AdaptiveOptimizer = None

try:
    from .performance_tracker import PerformanceTracker
    PERFORMANCE_TRACKER_AVAILABLE = True
except ImportError as e:
    PERFORMANCE_TRACKER_AVAILABLE = False
    PerformanceTracker = None

try:
    from .cost_optimizer import CostOptimizer
    COST_OPTIMIZER_AVAILABLE = True
except ImportError as e:
    COST_OPTIMIZER_AVAILABLE = False
    CostOptimizer = None

__all__ = [
    "DocumentProcessingOptimizer",
    "IntelligentModelRouter",
    "MIPROv2Optimizer",
    "BootstrapRSOptimizer",
    "EnsembleOptimizer",
    "AdaptiveOptimizer",
    "PerformanceTracker",
    "CostOptimizer",
    "DocumentCharacteristics",
    "ProcessingRequirements",
    "UserConstraints",
    "ModelRoutingDecision",
    "OptimizedPipeline",
    "OptimizationConfig",
    # Availability flags
    "DATA_MODELS_AVAILABLE",
    "OPTIMIZER_AVAILABLE",
    "MODEL_ROUTER_AVAILABLE",
    "STRATEGIES_AVAILABLE",
    "PERFORMANCE_TRACKER_AVAILABLE",
    "COST_OPTIMIZER_AVAILABLE"
]