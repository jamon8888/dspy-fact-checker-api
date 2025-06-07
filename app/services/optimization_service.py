"""
Optimization Service

Service layer for multi-model optimization system providing intelligent
model routing, performance tracking, and cost optimization.
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.optimization import (
    DocumentProcessingOptimizer, DocumentCharacteristics, ProcessingRequirements,
    UserConstraints, OptimizationConfig,
    OPTIMIZER_AVAILABLE, DATA_MODELS_AVAILABLE
)

logger = logging.getLogger(__name__)


class OptimizationService:
    """Service for document processing optimization."""
    
    def __init__(self):
        """Initialize the optimization service."""
        self.optimizer = None
        self.initialized = False
        self.logger = logging.getLogger(__name__ + ".OptimizationService")
        
        # Service state
        self.optimization_cache = {}
        self.performance_history = []
        
        self.logger.info("OptimizationService initialized")
    
    async def initialize(self):
        """Initialize the optimization service."""
        try:
            if not OPTIMIZER_AVAILABLE or not DATA_MODELS_AVAILABLE:
                self.logger.warning("Optimization modules not fully available - service will be limited")
                return False
            
            # Initialize the main optimizer
            self.optimizer = DocumentProcessingOptimizer()
            
            self.initialized = True
            self.logger.info("Optimization service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize optimization service: {e}")
            return False
    
    async def optimize_document_processing(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        processing_preferences: Optional[Dict[str, Any]] = None,
        user_constraints: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize document processing configuration.
        
        Args:
            document_content: Content of the document to process
            document_metadata: Metadata about the document
            processing_preferences: User preferences for processing
            user_constraints: User constraints (budget, performance, etc.)
            user_id: Optional user identifier
            
        Returns:
            Optimization result with recommended configuration
        """
        optimization_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Initialize if not already done
            if not self.initialized:
                await self.initialize()
            
            if not self.initialized:
                return self._create_fallback_optimization(optimization_id, start_time)
            
            # Analyze document characteristics
            document_characteristics = await self._analyze_document_characteristics(
                document_content, document_metadata
            )
            
            # Parse processing requirements
            processing_requirements = self._parse_processing_requirements(
                processing_preferences or {}
            )
            
            # Parse user constraints
            user_constraints_obj = self._parse_user_constraints(
                user_constraints or {}, user_id
            )
            
            # Perform optimization
            optimization_result = await self.optimizer.optimize_for_request(
                document_characteristics,
                processing_requirements,
                user_constraints_obj,
                user_id
            )
            
            # Cache result
            self.optimization_cache[optimization_id] = optimization_result
            
            # Convert to API response format
            response = self._convert_to_api_response(optimization_result, optimization_id, start_time)
            
            self.logger.info(f"Document processing optimization completed for {optimization_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Document processing optimization failed for {optimization_id}: {e}")
            return self._create_error_response(optimization_id, str(e), start_time)
    
    async def get_model_recommendation(
        self,
        document_type: str,
        estimated_tokens: int,
        complexity_score: float = 0.5,
        prefer_speed: bool = False,
        prefer_cost: bool = False,
        max_cost: Optional[float] = None,
        max_latency: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get model recommendation for specific requirements.
        
        Args:
            document_type: Type of document
            estimated_tokens: Estimated token count
            complexity_score: Document complexity (0.0-1.0)
            prefer_speed: Prioritize processing speed
            prefer_cost: Prioritize cost efficiency
            max_cost: Maximum acceptable cost
            max_latency: Maximum acceptable latency
            
        Returns:
            Model recommendation with reasoning
        """
        try:
            # Initialize if not already done
            if not self.initialized:
                await self.initialize()
            
            if not self.initialized:
                return self._create_fallback_model_recommendation()
            
            # Create document characteristics
            document_characteristics = DocumentCharacteristics(
                document_type=document_type,
                estimated_tokens=estimated_tokens,
                complexity_score=complexity_score,
                language="en"
            )
            
            # Create processing requirements
            processing_requirements = ProcessingRequirements(
                max_latency=max_latency,
                max_cost=max_cost,
                prefer_speed=prefer_speed,
                prefer_cost_efficiency=prefer_cost
            )
            
            # Create user constraints
            user_constraints = UserConstraints(
                max_cost_per_request=max_cost
            )
            
            # Get routing decision
            routing_decision = await self.optimizer.model_router.route_request(
                document_characteristics, processing_requirements, user_constraints
            )
            
            return {
                "success": True,
                "recommended_model": routing_decision.selected_model,
                "confidence": routing_decision.confidence,
                "reasoning": routing_decision.reasoning,
                "estimated_cost": routing_decision.estimated_cost,
                "estimated_latency": routing_decision.estimated_latency,
                "alternatives": routing_decision.alternatives
            }
            
        except Exception as e:
            self.logger.error(f"Model recommendation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_model": "gpt-4o-mini"
            }
    
    async def track_performance(
        self,
        optimization_id: str,
        actual_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track actual performance metrics for continuous optimization.
        
        Args:
            optimization_id: ID of the optimization to track
            actual_performance: Actual performance metrics
            
        Returns:
            Tracking result
        """
        try:
            if not self.initialized:
                return {"success": False, "error": "Service not initialized"}
            
            # Convert to PerformanceMetrics object
            try:
                from app.core.optimization.data_models import PerformanceMetrics
                performance_metrics = PerformanceMetrics(
                    accuracy=actual_performance.get("accuracy"),
                    precision=actual_performance.get("precision"),
                    recall=actual_performance.get("recall"),
                    f1_score=actual_performance.get("f1_score"),
                    processing_time=actual_performance.get("processing_time", 0.0),
                    cost=actual_performance.get("cost", 0.0),
                    tokens_processed=actual_performance.get("tokens_processed", 0),
                    confidence_score=actual_performance.get("confidence_score"),
                    uncertainty_score=actual_performance.get("uncertainty_score"),
                    model_used=actual_performance.get("model_used", "unknown"),
                    document_type=actual_performance.get("document_type", "unknown")
                )
            except ImportError:
                # Fallback if PerformanceMetrics not available
                performance_metrics = actual_performance
            
            # Track performance
            await self.optimizer.track_performance(optimization_id, performance_metrics)
            
            # Store in history
            self.performance_history.append({
                "optimization_id": optimization_id,
                "metrics": actual_performance,
                "timestamp": datetime.now()
            })
            
            return {
                "success": True,
                "message": "Performance tracked successfully",
                "optimization_id": optimization_id
            }
            
        except Exception as e:
            self.logger.error(f"Performance tracking failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_optimization_insights(self) -> Dict[str, Any]:
        """Get optimization insights and recommendations."""
        try:
            if not self.initialized:
                return {"success": False, "error": "Service not initialized"}
            
            # Get insights from optimizer
            insights = await self.optimizer.get_optimization_insights()
            
            # Add service-level insights
            service_insights = {
                "total_optimizations": len(self.optimization_cache),
                "performance_history_size": len(self.performance_history),
                "service_status": "active" if self.initialized else "inactive"
            }
            
            return {
                "success": True,
                "optimizer_insights": insights,
                "service_insights": service_insights
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get optimization insights: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_cost_analysis(
        self,
        model_name: str,
        estimated_tokens: int,
        user_budget: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get cost analysis for a specific model and usage."""
        try:
            if not self.initialized:
                return {"success": False, "error": "Service not initialized"}
            
            # Get cost estimate
            cost_estimate = await self.optimizer.cost_optimizer.cost_calculator.estimate_cost(
                model_name,
                estimated_tokens,
                estimated_tokens // 4  # Assume 4:1 input:output ratio
            )
            
            # Budget analysis
            budget_analysis = {}
            if user_budget:
                budget_analysis = {
                    "within_budget": cost_estimate.estimated_cost <= user_budget,
                    "budget_utilization": cost_estimate.estimated_cost / user_budget,
                    "remaining_budget": user_budget - cost_estimate.estimated_cost
                }
            
            return {
                "success": True,
                "model": model_name,
                "estimated_tokens": estimated_tokens,
                "cost_estimate": cost_estimate.dict(),
                "budget_analysis": budget_analysis
            }
            
        except Exception as e:
            self.logger.error(f"Cost analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_document_characteristics(
        self,
        document_content: str,
        document_metadata: Dict[str, Any]
    ) -> DocumentCharacteristics:
        """Analyze document characteristics for optimization."""
        # Estimate token count (rough approximation)
        estimated_tokens = len(document_content.split()) * 1.3  # Rough token estimation
        
        # Analyze complexity
        complexity_indicators = [
            len(document_content) > 10000,  # Long document
            "table" in document_content.lower(),  # Has tables
            "figure" in document_content.lower(),  # Has figures
            "citation" in document_content.lower(),  # Has citations
            document_metadata.get("has_formulas", False)  # Has formulas
        ]
        complexity_score = sum(complexity_indicators) / len(complexity_indicators)
        
        return DocumentCharacteristics(
            document_type=document_metadata.get("document_type", "general"),
            estimated_tokens=int(estimated_tokens),
            complexity_score=complexity_score,
            language=document_metadata.get("language", "en"),
            domain=document_metadata.get("domain"),
            has_tables="table" in document_content.lower(),
            has_citations="citation" in document_content.lower(),
            has_formulas=document_metadata.get("has_formulas", False),
            requires_specialized_knowledge=document_metadata.get("requires_expertise", False)
        )
    
    def _parse_processing_requirements(
        self,
        preferences: Dict[str, Any]
    ) -> ProcessingRequirements:
        """Parse processing requirements from preferences."""
        return ProcessingRequirements(
            max_latency=preferences.get("max_latency"),
            max_cost=preferences.get("max_cost"),
            accuracy_threshold=preferences.get("accuracy_threshold", 0.8),
            require_citations=preferences.get("require_citations", True),
            require_uncertainty_quantification=preferences.get("require_uncertainty", True),
            prefer_speed=preferences.get("prefer_speed", False),
            prefer_accuracy=preferences.get("prefer_accuracy", True),
            prefer_cost_efficiency=preferences.get("prefer_cost", False)
        )
    
    def _parse_user_constraints(
        self,
        constraints: Dict[str, Any],
        user_id: Optional[str]
    ) -> UserConstraints:
        """Parse user constraints."""
        return UserConstraints(
            user_tier=constraints.get("user_tier", "free"),
            monthly_quota=constraints.get("monthly_quota"),
            remaining_quota=constraints.get("remaining_quota"),
            max_cost_per_request=constraints.get("max_cost_per_request"),
            monthly_budget=constraints.get("monthly_budget"),
            remaining_budget=constraints.get("remaining_budget"),
            max_processing_time=constraints.get("max_processing_time"),
            priority_level=constraints.get("priority_level", "normal"),
            has_premium_features=constraints.get("has_premium_features", False)
        )
    
    def _convert_to_api_response(
        self,
        optimization_result: Dict[str, Any],
        optimization_id: str,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Convert optimization result to API response format."""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": optimization_result.get("success", True),
            "optimization_id": optimization_id,
            "processing_time": processing_time,
            "routing_decision": optimization_result.get("routing_decision", {}),
            "cost_analysis": optimization_result.get("cost_analysis", {}),
            "performance_prediction": optimization_result.get("performance_prediction", {}),
            "recommendations": optimization_result.get("recommendations", []),
            "optimized_pipeline": optimization_result.get("optimized_pipeline")
        }
    
    def _create_fallback_optimization(
        self,
        optimization_id: str,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Create fallback optimization when service is not available."""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": True,
            "optimization_id": optimization_id,
            "processing_time": processing_time,
            "routing_decision": {
                "selected_model": "gpt-4o-mini",
                "confidence": 0.5,
                "reasoning": "Fallback model selection - optimization service unavailable",
                "estimated_cost": 0.01,
                "estimated_latency": 2.0
            },
            "cost_analysis": {
                "cost_estimate": {"estimated_cost": 0.01},
                "budget_check": {"within_budget": True}
            },
            "performance_prediction": {
                "predicted_accuracy": 0.8,
                "predicted_latency": 2.0,
                "predicted_cost": 0.01,
                "confidence": 0.5
            },
            "recommendations": [
                {
                    "type": "service",
                    "priority": "low",
                    "title": "Optimization Service Unavailable",
                    "description": "Using fallback configuration",
                    "action": "Enable optimization modules for better performance"
                }
            ],
            "fallback": True
        }
    
    def _create_fallback_model_recommendation(self) -> Dict[str, Any]:
        """Create fallback model recommendation."""
        return {
            "success": True,
            "recommended_model": "gpt-4o-mini",
            "confidence": 0.5,
            "reasoning": "Fallback recommendation - optimization service unavailable",
            "estimated_cost": 0.01,
            "estimated_latency": 2.0,
            "alternatives": [],
            "fallback": True
        }
    
    def _create_error_response(
        self,
        optimization_id: str,
        error_message: str,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Create error response."""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": False,
            "optimization_id": optimization_id,
            "error": error_message,
            "processing_time": processing_time,
            "fallback_model": "gpt-4o-mini"
        }
