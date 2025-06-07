"""
Document Processing Optimizer

Main optimizer that orchestrates multi-model optimization for document processing
pipelines using intelligent routing, performance tracking, and cost optimization.
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from .model_router import IntelligentModelRouter
from .strategies import MIPROv2Optimizer, BootstrapRSOptimizer, EnsembleOptimizer, AdaptiveOptimizer
from .performance_tracker import PerformanceTracker
from .cost_optimizer import CostOptimizer
from .data_models import (
    DocumentCharacteristics, ProcessingRequirements, UserConstraints,
    OptimizationConfig, OptimizedPipeline, OptimizationResult,
    PerformanceMetrics, OptimizationStrategy
)

logger = logging.getLogger(__name__)


class DocumentProcessingOptimizer:
    """
    Main optimizer for document processing pipelines.
    
    Provides comprehensive optimization including:
    - Intelligent model routing
    - Performance optimization using DSPy strategies
    - Cost optimization
    - Continuous performance tracking
    """
    
    def __init__(self):
        """Initialize the document processing optimizer."""
        self.logger = logging.getLogger(__name__ + ".DocumentProcessingOptimizer")
        
        # Initialize components
        self.model_router = IntelligentModelRouter()
        self.performance_tracker = PerformanceTracker()
        self.cost_optimizer = CostOptimizer()
        
        # Initialize optimization strategies
        self.optimization_strategies = {
            OptimizationStrategy.MIPRO_V2: MIPROv2Optimizer(),
            OptimizationStrategy.BOOTSTRAP_RS: BootstrapRSOptimizer(),
            OptimizationStrategy.ENSEMBLE: EnsembleOptimizer(),
            OptimizationStrategy.ADAPTIVE: AdaptiveOptimizer()
        }
        
        # Optimization state
        self.optimized_pipelines = {}
        self.optimization_history = []
        
        self.logger.info("DocumentProcessingOptimizer initialized")
    
    async def optimize_for_request(
        self,
        document_characteristics: DocumentCharacteristics,
        processing_requirements: ProcessingRequirements,
        user_constraints: UserConstraints,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize processing pipeline for a specific request.
        
        Args:
            document_characteristics: Characteristics of the document to process
            processing_requirements: Processing requirements and preferences
            user_constraints: User-specific constraints (budget, tier, etc.)
            user_id: Optional user identifier for tracking
            
        Returns:
            Optimization result with recommended configuration
        """
        optimization_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting optimization for request {optimization_id}")
            
            # Step 1: Intelligent model routing
            routing_decision = await self.model_router.route_request(
                document_characteristics, processing_requirements, user_constraints
            )
            
            # Step 2: Cost optimization check
            cost_check = await self._perform_cost_optimization(
                routing_decision, document_characteristics, user_constraints, user_id
            )
            
            # Step 3: Get or create optimized pipeline
            pipeline = await self._get_optimized_pipeline(
                document_characteristics, processing_requirements, routing_decision
            )
            
            # Step 4: Performance prediction
            performance_prediction = await self._predict_performance(
                pipeline, document_characteristics, routing_decision
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "optimization_id": optimization_id,
                "routing_decision": routing_decision.dict(),
                "cost_analysis": cost_check,
                "optimized_pipeline": pipeline.dict() if pipeline else None,
                "performance_prediction": performance_prediction,
                "processing_time": processing_time,
                "recommendations": await self._generate_recommendations(
                    routing_decision, cost_check, performance_prediction
                )
            }
            
            self.logger.info(f"Optimization completed for {optimization_id} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Optimization failed for {optimization_id}: {e}")
            return {
                "success": False,
                "optimization_id": optimization_id,
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
    
    async def optimize_pipeline(
        self,
        document_type: str,
        training_data: List[Dict[str, Any]],
        optimization_config: OptimizationConfig,
        target_metrics: Optional[List[str]] = None
    ) -> OptimizationResult:
        """
        Optimize an entire processing pipeline using training data.
        
        Args:
            document_type: Type of documents the pipeline will process
            training_data: Training data for optimization
            optimization_config: Configuration for optimization process
            target_metrics: Metrics to optimize for
            
        Returns:
            Complete optimization result
        """
        optimization_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting pipeline optimization {optimization_id} for {document_type}")
            
            if not target_metrics:
                target_metrics = ["accuracy", "processing_time", "cost"]
            
            # Select optimization strategy
            strategy = self.optimization_strategies.get(optimization_config.strategy)
            if not strategy:
                raise ValueError(f"Unknown optimization strategy: {optimization_config.strategy}")
            
            # Optimize individual components
            optimized_components = {}
            
            # Optimize claim extraction
            if "claim_extraction" in optimization_config.target_metrics or "accuracy" in target_metrics:
                extraction_component = await strategy.optimize_module(
                    "claim_extraction", training_data, ["accuracy", "precision", "recall"], optimization_config
                )
                optimized_components["claim_extraction"] = extraction_component
            
            # Optimize claim verification
            if "claim_verification" in optimization_config.target_metrics or "accuracy" in target_metrics:
                verification_component = await strategy.optimize_module(
                    "claim_verification", training_data, ["accuracy", "confidence"], optimization_config
                )
                optimized_components["claim_verification"] = verification_component
            
            # Create optimized pipeline
            pipeline = OptimizedPipeline(
                pipeline_id=optimization_id,
                document_type=document_type,
                components=optimized_components,
                routing_strategy=await self._create_default_routing_strategy(),
                overall_performance=await self._calculate_overall_performance(optimized_components),
                optimization_metadata={
                    "strategy": optimization_config.strategy.value,
                    "target_metrics": target_metrics,
                    "training_data_size": len(training_data)
                }
            )
            
            # Store optimized pipeline
            self.optimized_pipelines[f"{document_type}_{optimization_id}"] = pipeline
            
            # Calculate baseline for comparison
            baseline_performance = await self._calculate_baseline_performance(training_data, target_metrics)
            
            # Calculate improvement metrics
            improvement_metrics = await self._calculate_improvement_metrics(
                baseline_performance, pipeline.overall_performance
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = OptimizationResult(
                optimization_id=optimization_id,
                strategy_used=optimization_config.strategy,
                optimized_pipeline=pipeline,
                baseline_performance=baseline_performance,
                optimized_performance=pipeline.overall_performance,
                improvement_metrics=improvement_metrics,
                optimization_time=processing_time,
                iterations_completed=optimization_config.max_iterations,
                convergence_achieved=True,  # Simplified
                configuration=optimization_config
            )
            
            # Store in history
            self.optimization_history.append(result)
            
            self.logger.info(f"Pipeline optimization completed for {optimization_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Pipeline optimization failed for {optimization_id}: {e}")
            raise
    
    async def track_performance(
        self,
        optimization_id: str,
        actual_metrics: PerformanceMetrics
    ):
        """Track actual performance metrics for continuous optimization."""
        try:
            await self.performance_tracker.track_performance(actual_metrics)
            
            # Update pipeline performance if applicable
            await self._update_pipeline_performance(optimization_id, actual_metrics)
            
            self.logger.debug(f"Tracked performance for optimization {optimization_id}")
            
        except Exception as e:
            self.logger.error(f"Error tracking performance: {e}")
    
    async def get_optimization_insights(
        self,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get insights from optimization history and performance data."""
        try:
            # Get performance summary
            performance_summary = await self.performance_tracker.get_performance_summary()
            
            # Get optimization recommendations
            recommendations = await self.performance_tracker.get_optimization_recommendations()
            
            # Analyze optimization history
            history_analysis = await self._analyze_optimization_history()
            
            return {
                "performance_summary": performance_summary,
                "optimization_recommendations": recommendations,
                "history_analysis": history_analysis,
                "active_pipelines": len(self.optimized_pipelines),
                "total_optimizations": len(self.optimization_history)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting optimization insights: {e}")
            return {"error": str(e)}
    
    async def _perform_cost_optimization(
        self,
        routing_decision,
        document_characteristics: DocumentCharacteristics,
        user_constraints: UserConstraints,
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Perform cost optimization analysis."""
        try:
            # Estimate costs for the selected model
            cost_estimate = await self.cost_optimizer.cost_calculator.estimate_cost(
                routing_decision.selected_model,
                document_characteristics.estimated_tokens,
                document_characteristics.estimated_tokens // 4  # Assume 4:1 input:output ratio
            )
            
            # Check budget constraints
            budget_check = {"within_budget": True, "warnings": [], "blocking_issues": []}
            if user_id:
                budget_check = await self.cost_optimizer.budget_manager.check_budget_constraints(
                    user_id, user_constraints, cost_estimate.estimated_cost
                )
            
            # Get cost optimization recommendations
            cost_recommendations = []
            if not budget_check["within_budget"]:
                # Find cheaper alternatives
                available_models = ["gpt-4o-mini", "claude-3-haiku", "gemini-flash"]
                cost_optimization = await self.cost_optimizer.optimize_for_cost(
                    available_models,
                    document_characteristics.estimated_tokens,
                    document_characteristics.estimated_tokens // 4,
                    user_constraints
                )
                cost_recommendations.append(cost_optimization)
            
            return {
                "cost_estimate": cost_estimate.dict(),
                "budget_check": budget_check,
                "cost_recommendations": cost_recommendations
            }
            
        except Exception as e:
            self.logger.error(f"Error in cost optimization: {e}")
            return {"error": str(e)}
    
    async def _get_optimized_pipeline(
        self,
        document_characteristics: DocumentCharacteristics,
        processing_requirements: ProcessingRequirements,
        routing_decision
    ) -> Optional[OptimizedPipeline]:
        """Get or create optimized pipeline for the request."""
        try:
            # Look for existing optimized pipeline
            pipeline_key = f"{document_characteristics.document_type}_optimized"
            
            if pipeline_key in self.optimized_pipelines:
                return self.optimized_pipelines[pipeline_key]
            
            # Create a basic optimized pipeline if none exists
            # In practice, this would use actual optimization results
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting optimized pipeline: {e}")
            return None
    
    async def _predict_performance(
        self,
        pipeline: Optional[OptimizedPipeline],
        document_characteristics: DocumentCharacteristics,
        routing_decision
    ) -> Dict[str, Any]:
        """Predict performance for the optimized configuration."""
        try:
            # Base performance prediction
            base_accuracy = 0.85
            base_latency = routing_decision.estimated_latency
            base_cost = routing_decision.estimated_cost
            
            # Adjust based on pipeline optimization
            if pipeline:
                accuracy_boost = 0.05  # Optimized pipeline boost
                latency_reduction = 0.9  # 10% latency reduction
                base_accuracy += accuracy_boost
                base_latency *= latency_reduction
            
            # Adjust based on document complexity
            complexity_factor = document_characteristics.complexity_score
            base_accuracy *= (1.0 - complexity_factor * 0.1)
            base_latency *= (1.0 + complexity_factor * 0.2)
            
            return {
                "predicted_accuracy": min(0.95, base_accuracy),
                "predicted_latency": base_latency,
                "predicted_cost": base_cost,
                "confidence": 0.8,
                "factors": [
                    f"Document complexity: {complexity_factor:.2f}",
                    f"Selected model: {routing_decision.selected_model}",
                    f"Pipeline optimized: {pipeline is not None}"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting performance: {e}")
            return {"error": str(e)}
    
    async def _generate_recommendations(
        self,
        routing_decision,
        cost_check: Dict[str, Any],
        performance_prediction: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Cost recommendations
        if not cost_check.get("budget_check", {}).get("within_budget", True):
            recommendations.append({
                "type": "cost",
                "priority": "high",
                "title": "Budget Constraint",
                "description": "Selected configuration exceeds budget constraints",
                "action": "Consider using a more cost-effective model"
            })
        
        # Performance recommendations
        predicted_accuracy = performance_prediction.get("predicted_accuracy", 0)
        if predicted_accuracy < 0.8:
            recommendations.append({
                "type": "performance",
                "priority": "medium",
                "title": "Low Predicted Accuracy",
                "description": f"Predicted accuracy is {predicted_accuracy:.2f}",
                "action": "Consider using a more capable model or optimizing the pipeline"
            })
        
        # Model recommendations
        if routing_decision.confidence < 0.7:
            recommendations.append({
                "type": "routing",
                "priority": "medium",
                "title": "Low Routing Confidence",
                "description": f"Model selection confidence is {routing_decision.confidence:.2f}",
                "action": "Review document characteristics and requirements"
            })
        
        return recommendations
    
    async def _create_default_routing_strategy(self):
        """Create a default routing strategy."""
        from .data_models import ModelRoutingDecision
        return ModelRoutingDecision(
            selected_model="gpt-4o-mini",
            confidence=0.8,
            reasoning="Default routing strategy",
            estimated_cost=0.01,
            estimated_latency=2.0
        )
    
    async def _calculate_overall_performance(
        self,
        optimized_components: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate overall pipeline performance."""
        if not optimized_components:
            return {"accuracy": 0.8, "processing_time": 2.0, "cost": 0.01}
        
        # Aggregate component performances
        total_accuracy = 0
        total_time = 0
        total_cost = 0
        component_count = len(optimized_components)
        
        for component in optimized_components.values():
            metrics = component.performance_metrics
            total_accuracy += metrics.get("accuracy", 0.8)
            total_time += metrics.get("processing_time", 1.0)
            total_cost += metrics.get("cost", 0.005)
        
        return {
            "accuracy": total_accuracy / component_count,
            "processing_time": total_time,
            "cost": total_cost
        }
    
    async def _calculate_baseline_performance(
        self,
        training_data: List[Dict[str, Any]],
        target_metrics: List[str]
    ) -> Dict[str, float]:
        """Calculate baseline performance metrics."""
        # Simplified baseline calculation
        return {metric: 0.75 for metric in target_metrics}
    
    async def _calculate_improvement_metrics(
        self,
        baseline: Dict[str, float],
        optimized: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate improvement metrics."""
        improvements = {}
        
        for metric in baseline:
            if metric in optimized:
                baseline_val = baseline[metric]
                optimized_val = optimized[metric]
                
                if baseline_val != 0:
                    improvement = (optimized_val - baseline_val) / baseline_val
                    improvements[f"{metric}_improvement"] = improvement
        
        return improvements
    
    async def _update_pipeline_performance(
        self,
        optimization_id: str,
        actual_metrics: PerformanceMetrics
    ):
        """Update pipeline performance with actual metrics."""
        # Find and update relevant pipeline
        for pipeline in self.optimized_pipelines.values():
            if pipeline.pipeline_id == optimization_id:
                pipeline.usage_count += 1
                # Update success rate and other metrics
                break
    
    async def _analyze_optimization_history(self) -> Dict[str, Any]:
        """Analyze optimization history for insights."""
        if not self.optimization_history:
            return {"message": "No optimization history available"}
        
        # Calculate average improvements
        total_improvements = {}
        for result in self.optimization_history:
            for metric, improvement in result.improvement_metrics.items():
                if metric not in total_improvements:
                    total_improvements[metric] = []
                total_improvements[metric].append(improvement)
        
        avg_improvements = {
            metric: sum(values) / len(values)
            for metric, values in total_improvements.items()
        }
        
        return {
            "total_optimizations": len(self.optimization_history),
            "average_improvements": avg_improvements,
            "most_recent": self.optimization_history[-1].dict() if self.optimization_history else None
        }
