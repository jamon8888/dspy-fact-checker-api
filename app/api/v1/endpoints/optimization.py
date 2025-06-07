"""
Optimization API Endpoints

API endpoints for multi-model optimization system providing intelligent
model routing, performance tracking, and cost optimization.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator

from app.services.optimization_service import OptimizationService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
optimization_service = OptimizationService()


class DocumentOptimizationRequest(BaseModel):
    """Request model for document processing optimization."""
    
    document_content: str = Field(..., description="Document content to optimize processing for")
    document_metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    processing_preferences: Optional[Dict[str, Any]] = Field(None, description="Processing preferences")
    user_constraints: Optional[Dict[str, Any]] = Field(None, description="User constraints")
    user_id: Optional[str] = Field(None, description="User identifier")
    
    @validator('document_content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("Document content cannot be empty")
        return v


class ModelRecommendationRequest(BaseModel):
    """Request model for model recommendation."""
    
    document_type: str = Field(..., description="Type of document")
    estimated_tokens: int = Field(..., ge=1, description="Estimated token count")
    complexity_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Document complexity score")
    prefer_speed: bool = Field(default=False, description="Prioritize processing speed")
    prefer_cost: bool = Field(default=False, description="Prioritize cost efficiency")
    max_cost: Optional[float] = Field(None, ge=0.0, description="Maximum acceptable cost")
    max_latency: Optional[float] = Field(None, ge=0.0, description="Maximum acceptable latency")
    
    @validator('complexity_score')
    def validate_complexity(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Complexity score must be between 0.0 and 1.0')
        return v


class PerformanceTrackingRequest(BaseModel):
    """Request model for performance tracking."""
    
    optimization_id: str = Field(..., description="Optimization ID to track")
    actual_performance: Dict[str, Any] = Field(..., description="Actual performance metrics")
    
    @validator('actual_performance')
    def validate_performance(cls, v):
        if not v:
            raise ValueError("Performance metrics cannot be empty")
        return v


class CostAnalysisRequest(BaseModel):
    """Request model for cost analysis."""
    
    model_name: str = Field(..., description="Model name to analyze")
    estimated_tokens: int = Field(..., ge=1, description="Estimated token count")
    user_budget: Optional[float] = Field(None, ge=0.0, description="User budget for comparison")
    
    @validator('model_name')
    def validate_model(cls, v):
        if not v.strip():
            raise ValueError("Model name cannot be empty")
        return v


@router.post("/optimize-document-processing", response_model=Dict[str, Any])
async def optimize_document_processing(request: DocumentOptimizationRequest):
    """
    Optimize document processing configuration using intelligent routing and cost optimization.
    
    This endpoint analyzes document characteristics, user preferences, and constraints
    to recommend the optimal processing configuration including model selection,
    cost estimates, and performance predictions.
    """
    try:
        result = await optimization_service.optimize_document_processing(
            document_content=request.document_content,
            document_metadata=request.document_metadata,
            processing_preferences=request.processing_preferences,
            user_constraints=request.user_constraints,
            user_id=request.user_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Document processing optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/recommend-model", response_model=Dict[str, Any])
async def recommend_model(request: ModelRecommendationRequest):
    """
    Get intelligent model recommendation based on document characteristics and requirements.
    
    This endpoint provides model recommendations using intelligent routing that considers
    document complexity, performance requirements, cost constraints, and user preferences.
    """
    try:
        result = await optimization_service.get_model_recommendation(
            document_type=request.document_type,
            estimated_tokens=request.estimated_tokens,
            complexity_score=request.complexity_score,
            prefer_speed=request.prefer_speed,
            prefer_cost=request.prefer_cost,
            max_cost=request.max_cost,
            max_latency=request.max_latency
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Model recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model recommendation failed: {str(e)}")


@router.post("/track-performance", response_model=Dict[str, Any])
async def track_performance(request: PerformanceTrackingRequest):
    """
    Track actual performance metrics for continuous optimization.
    
    This endpoint allows tracking of actual performance metrics to improve
    future optimization decisions and model recommendations.
    """
    try:
        result = await optimization_service.track_performance(
            optimization_id=request.optimization_id,
            actual_performance=request.actual_performance
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Performance tracking failed: {e}")
        raise HTTPException(status_code=500, detail=f"Performance tracking failed: {str(e)}")


@router.get("/optimization-insights", response_model=Dict[str, Any])
async def get_optimization_insights():
    """
    Get optimization insights and recommendations.
    
    This endpoint provides insights from the optimization system including
    performance trends, bottlenecks, and optimization opportunities.
    """
    try:
        insights = await optimization_service.get_optimization_insights()
        return insights
        
    except Exception as e:
        logger.error(f"Failed to get optimization insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")


@router.post("/analyze-cost", response_model=Dict[str, Any])
async def analyze_cost(request: CostAnalysisRequest):
    """
    Analyze cost for a specific model and usage pattern.
    
    This endpoint provides detailed cost analysis including cost breakdown,
    budget utilization, and cost optimization recommendations.
    """
    try:
        result = await optimization_service.get_cost_analysis(
            model_name=request.model_name,
            estimated_tokens=request.estimated_tokens,
            user_budget=request.user_budget
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Cost analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cost analysis failed: {str(e)}")


@router.get("/service-status", response_model=Dict[str, Any])
async def get_service_status():
    """
    Get optimization service status and capabilities.
    
    Returns information about service availability, supported features,
    and system health.
    """
    try:
        # Check service initialization
        if not optimization_service.initialized:
            await optimization_service.initialize()
        
        from app.core.optimization import (
            OPTIMIZER_AVAILABLE, DATA_MODELS_AVAILABLE, MODEL_ROUTER_AVAILABLE,
            STRATEGIES_AVAILABLE, PERFORMANCE_TRACKER_AVAILABLE, COST_OPTIMIZER_AVAILABLE
        )
        
        return {
            "success": True,
            "service_status": {
                "initialized": optimization_service.initialized,
                "optimization_cache_size": len(optimization_service.optimization_cache),
                "performance_history_size": len(optimization_service.performance_history)
            },
            "module_availability": {
                "optimizer": OPTIMIZER_AVAILABLE,
                "data_models": DATA_MODELS_AVAILABLE,
                "model_router": MODEL_ROUTER_AVAILABLE,
                "strategies": STRATEGIES_AVAILABLE,
                "performance_tracker": PERFORMANCE_TRACKER_AVAILABLE,
                "cost_optimizer": COST_OPTIMIZER_AVAILABLE
            },
            "capabilities": {
                "document_optimization": OPTIMIZER_AVAILABLE and DATA_MODELS_AVAILABLE,
                "model_recommendation": MODEL_ROUTER_AVAILABLE,
                "performance_tracking": PERFORMANCE_TRACKER_AVAILABLE,
                "cost_optimization": COST_OPTIMIZER_AVAILABLE,
                "intelligent_routing": MODEL_ROUTER_AVAILABLE,
                "multi_strategy_optimization": STRATEGIES_AVAILABLE
            },
            "supported_features": [
                "Document processing optimization",
                "Intelligent model routing",
                "Cost analysis and optimization",
                "Performance tracking and insights",
                "Multi-strategy optimization (MIPROv2, Bootstrap RS, Ensemble, Adaptive)",
                "Budget management and constraints",
                "Real-time performance monitoring"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        return {
            "success": False,
            "error": str(e),
            "service_status": "error"
        }


@router.get("/supported-models", response_model=Dict[str, Any])
async def get_supported_models():
    """
    Get list of supported models and their characteristics.
    
    Returns information about available models, their capabilities,
    pricing, and performance characteristics.
    """
    try:
        # Model information (would typically come from configuration)
        supported_models = {
            "gpt-4o": {
                "capabilities": ["complex_reasoning", "multilingual", "large_context"],
                "max_context": 128000,
                "cost_per_1k_tokens": {"input": 0.0025, "output": 0.01},
                "avg_latency": 2.5,
                "accuracy_score": 0.92,
                "use_cases": ["Complex analysis", "Academic documents", "Legal documents"]
            },
            "gpt-4o-mini": {
                "capabilities": ["fast_processing", "cost_effective"],
                "max_context": 128000,
                "cost_per_1k_tokens": {"input": 0.00015, "output": 0.0006},
                "avg_latency": 1.2,
                "accuracy_score": 0.85,
                "use_cases": ["General documents", "Quick processing", "Cost-sensitive tasks"]
            },
            "claude-3-opus": {
                "capabilities": ["analytical_reasoning", "long_documents", "complex_reasoning"],
                "max_context": 200000,
                "cost_per_1k_tokens": {"input": 0.015, "output": 0.075},
                "avg_latency": 3.0,
                "accuracy_score": 0.94,
                "use_cases": ["Research papers", "Complex analysis", "Long documents"]
            },
            "claude-3-sonnet": {
                "capabilities": ["balanced_performance", "multilingual"],
                "max_context": 200000,
                "cost_per_1k_tokens": {"input": 0.003, "output": 0.015},
                "avg_latency": 2.0,
                "accuracy_score": 0.88,
                "use_cases": ["General purpose", "Balanced cost/performance"]
            },
            "claude-3-haiku": {
                "capabilities": ["fast_processing", "cost_effective"],
                "max_context": 200000,
                "cost_per_1k_tokens": {"input": 0.00025, "output": 0.00125},
                "avg_latency": 0.8,
                "accuracy_score": 0.82,
                "use_cases": ["Fast processing", "High volume", "Cost optimization"]
            }
        }
        
        return {
            "success": True,
            "supported_models": supported_models,
            "total_models": len(supported_models),
            "model_selection_criteria": [
                "Document complexity",
                "Processing speed requirements",
                "Cost constraints",
                "Accuracy requirements",
                "Context length needs",
                "Language support"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get supported models: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/optimization-strategies", response_model=Dict[str, Any])
async def get_optimization_strategies():
    """
    Get information about available optimization strategies.
    
    Returns details about different optimization strategies and their
    characteristics, use cases, and performance.
    """
    try:
        strategies = {
            "mipro_v2": {
                "name": "Multi-Prompt Instruction Optimization v2",
                "description": "Advanced optimization using multiple prompts and instructions",
                "best_for": ["Complex reasoning tasks", "High accuracy requirements"],
                "typical_iterations": 50,
                "convergence_time": "Medium",
                "improvement_potential": "High"
            },
            "bootstrap_rs": {
                "name": "Bootstrap Random Search",
                "description": "Bootstrap sampling with random parameter search",
                "best_for": ["Small datasets", "Quick optimization"],
                "typical_iterations": 30,
                "convergence_time": "Fast",
                "improvement_potential": "Medium"
            },
            "ensemble": {
                "name": "Ensemble Optimization",
                "description": "Creates ensemble of optimized modules",
                "best_for": ["Maximum accuracy", "Large datasets"],
                "typical_iterations": 20,
                "convergence_time": "Slow",
                "improvement_potential": "Very High"
            },
            "adaptive": {
                "name": "Adaptive Strategy Selection",
                "description": "Automatically selects best strategy based on data",
                "best_for": ["General purpose", "Unknown data characteristics"],
                "typical_iterations": "Variable",
                "convergence_time": "Variable",
                "improvement_potential": "High"
            }
        }
        
        return {
            "success": True,
            "optimization_strategies": strategies,
            "total_strategies": len(strategies),
            "selection_criteria": [
                "Dataset size",
                "Data complexity",
                "Time constraints",
                "Accuracy requirements",
                "Resource availability"
            ],
            "recommendation": "Use 'adaptive' strategy for automatic selection based on your data characteristics"
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization strategies: {e}")
        return {
            "success": False,
            "error": str(e)
        }
