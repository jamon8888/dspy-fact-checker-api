"""
Intelligent Model Router

This module provides intelligent routing of requests to optimal models
based on document characteristics, performance requirements, and user constraints.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from .data_models import (
    DocumentCharacteristics, ProcessingRequirements, UserConstraints,
    ModelRoutingDecision, ModelConfiguration, ModelCapability
)

logger = logging.getLogger(__name__)


class ModelPerformanceDatabase:
    """Database for tracking model performance metrics."""
    
    def __init__(self):
        """Initialize the performance database."""
        self.performance_data = {}
        self.logger = logging.getLogger(__name__ + ".ModelPerformanceDatabase")
    
    async def get_performance_data(self, model_name: str, document_type: str) -> Dict[str, float]:
        """Get performance data for a specific model and document type."""
        key = f"{model_name}_{document_type}"
        return self.performance_data.get(key, {
            "accuracy": 0.8,
            "avg_latency": 2.0,
            "reliability": 0.9,
            "cost_efficiency": 0.7
        })
    
    async def update_performance_data(
        self, 
        model_name: str, 
        document_type: str, 
        metrics: Dict[str, float]
    ):
        """Update performance data for a model."""
        key = f"{model_name}_{document_type}"
        if key not in self.performance_data:
            self.performance_data[key] = {}
        self.performance_data[key].update(metrics)


class CostCalculator:
    """Calculator for estimating processing costs."""
    
    def __init__(self):
        """Initialize the cost calculator."""
        self.logger = logging.getLogger(__name__ + ".CostCalculator")
    
    async def estimate_cost(self, model_name: str, estimated_tokens: int) -> float:
        """Estimate the cost for processing with a specific model."""
        # Model pricing (cost per 1K tokens)
        model_pricing = {
            "gpt-4o": 0.03,
            "gpt-4o-mini": 0.015,
            "claude-3-opus": 0.075,
            "claude-3-haiku": 0.00025,
            "claude-3-sonnet": 0.015,
            "gemini-pro": 0.01,
            "gemini-flash": 0.005
        }
        
        cost_per_1k = model_pricing.get(model_name, 0.02)  # Default cost
        return (estimated_tokens / 1000) * cost_per_1k


class LatencyPredictor:
    """Predictor for estimating processing latency."""
    
    def __init__(self):
        """Initialize the latency predictor."""
        self.logger = logging.getLogger(__name__ + ".LatencyPredictor")
    
    async def predict(
        self, 
        model_name: str, 
        document_characteristics: DocumentCharacteristics
    ) -> float:
        """Predict processing latency for a model and document."""
        # Base latency for models (seconds)
        base_latency = {
            "gpt-4o": 2.5,
            "gpt-4o-mini": 1.2,
            "claude-3-opus": 3.0,
            "claude-3-haiku": 0.8,
            "claude-3-sonnet": 2.0,
            "gemini-pro": 2.2,
            "gemini-flash": 1.0
        }
        
        base = base_latency.get(model_name, 2.0)
        
        # Adjust for document complexity
        complexity_multiplier = 1.0 + document_characteristics.complexity_score
        
        # Adjust for document size
        size_multiplier = 1.0 + (document_characteristics.estimated_tokens / 10000)
        
        # Adjust for special requirements
        special_multiplier = 1.0
        if document_characteristics.requires_ocr:
            special_multiplier += 0.5
        if document_characteristics.requires_translation:
            special_multiplier += 0.3
        if document_characteristics.requires_specialized_knowledge:
            special_multiplier += 0.2
        
        return base * complexity_multiplier * size_multiplier * special_multiplier


class IntelligentModelRouter:
    """Route requests to optimal models based on document characteristics."""
    
    def __init__(self):
        """Initialize the intelligent model router."""
        self.logger = logging.getLogger(__name__ + ".IntelligentModelRouter")
        self.model_performance_db = ModelPerformanceDatabase()
        self.cost_calculator = CostCalculator()
        self.latency_predictor = LatencyPredictor()
        
        # Available models with capabilities
        self.available_models = {
            "gpt-4o": ModelConfiguration(
                model_name="gpt-4o",
                capabilities=[
                    ModelCapability.COMPLEX_REASONING,
                    ModelCapability.MULTILINGUAL,
                    ModelCapability.LARGE_CONTEXT
                ],
                cost_per_token=0.00003,
                avg_latency=2.5,
                max_context=128000,
                accuracy_score=0.92,
                reliability_score=0.95
            ),
            "gpt-4o-mini": ModelConfiguration(
                model_name="gpt-4o-mini",
                capabilities=[
                    ModelCapability.FAST_PROCESSING,
                    ModelCapability.COST_EFFECTIVE
                ],
                cost_per_token=0.000015,
                avg_latency=1.2,
                max_context=128000,
                accuracy_score=0.85,
                reliability_score=0.90
            ),
            "claude-3-opus": ModelConfiguration(
                model_name="claude-3-opus",
                capabilities=[
                    ModelCapability.ANALYTICAL_REASONING,
                    ModelCapability.LONG_DOCUMENTS,
                    ModelCapability.COMPLEX_REASONING
                ],
                cost_per_token=0.000075,
                avg_latency=3.0,
                max_context=200000,
                accuracy_score=0.94,
                reliability_score=0.93
            ),
            "claude-3-haiku": ModelConfiguration(
                model_name="claude-3-haiku",
                capabilities=[
                    ModelCapability.FAST_PROCESSING,
                    ModelCapability.COST_EFFECTIVE
                ],
                cost_per_token=0.00000025,
                avg_latency=0.8,
                max_context=200000,
                accuracy_score=0.82,
                reliability_score=0.88
            )
        }
    
    async def route_request(
        self,
        document_characteristics: DocumentCharacteristics,
        processing_requirements: ProcessingRequirements,
        user_constraints: UserConstraints
    ) -> ModelRoutingDecision:
        """Determine optimal model for document processing request."""
        try:
            # Analyze document complexity
            complexity_score = await self._analyze_document_complexity(document_characteristics)
            
            # Determine required capabilities
            required_capabilities = await self._determine_required_capabilities(
                document_characteristics, processing_requirements
            )
            
            # Filter compatible models
            compatible_models = self._filter_compatible_models(
                required_capabilities, document_characteristics.estimated_tokens
            )
            
            if not compatible_models:
                # Fallback to default model
                return await self._create_fallback_decision(document_characteristics)
            
            # Score models based on multiple criteria
            model_scores = await self._score_models(
                compatible_models, document_characteristics, 
                processing_requirements, user_constraints
            )
            
            # Select best model
            best_model = max(model_scores.items(), key=lambda x: x[1]['final_score'])
            
            # Generate alternatives
            alternatives = sorted(
                model_scores.items(),
                key=lambda x: x[1]['final_score'],
                reverse=True
            )[1:3]  # Top 2 alternatives
            
            return ModelRoutingDecision(
                selected_model=best_model[0],
                confidence=best_model[1]['final_score'],
                reasoning=self._generate_routing_reasoning(model_scores, best_model[0]),
                alternatives=[
                    {
                        "model": alt[0],
                        "score": alt[1]['final_score'],
                        "estimated_cost": alt[1]['estimated_cost'],
                        "estimated_latency": alt[1]['estimated_latency']
                    }
                    for alt in alternatives
                ],
                estimated_cost=best_model[1]['estimated_cost'],
                estimated_latency=best_model[1]['estimated_latency'],
                estimated_accuracy=best_model[1].get('performance_score', 0.8)
            )
            
        except Exception as e:
            self.logger.error(f"Error in model routing: {e}")
            return await self._create_fallback_decision(document_characteristics)
    
    async def _analyze_document_complexity(
        self, 
        document_characteristics: DocumentCharacteristics
    ) -> float:
        """Analyze document complexity."""
        complexity = document_characteristics.complexity_score
        
        # Adjust based on document features
        if document_characteristics.has_tables:
            complexity += 0.1
        if document_characteristics.has_formulas:
            complexity += 0.15
        if document_characteristics.requires_specialized_knowledge:
            complexity += 0.2
        if document_characteristics.estimated_tokens > 50000:
            complexity += 0.1
        
        return min(1.0, complexity)
    
    async def _determine_required_capabilities(
        self,
        document_characteristics: DocumentCharacteristics,
        processing_requirements: ProcessingRequirements
    ) -> List[ModelCapability]:
        """Determine required model capabilities."""
        capabilities = []
        
        # Based on document characteristics
        if document_characteristics.complexity_score > 0.7:
            capabilities.append(ModelCapability.COMPLEX_REASONING)
        
        if document_characteristics.language != "en":
            capabilities.append(ModelCapability.MULTILINGUAL)
        
        if document_characteristics.estimated_tokens > 50000:
            capabilities.append(ModelCapability.LARGE_CONTEXT)
        
        if document_characteristics.domain in ["academic", "legal", "medical"]:
            capabilities.append(ModelCapability.ANALYTICAL_REASONING)
        
        # Based on processing requirements
        if processing_requirements.prefer_speed:
            capabilities.append(ModelCapability.FAST_PROCESSING)
        
        if processing_requirements.prefer_cost_efficiency:
            capabilities.append(ModelCapability.COST_EFFECTIVE)
        
        return capabilities
    
    def _filter_compatible_models(
        self,
        required_capabilities: List[ModelCapability],
        estimated_tokens: int
    ) -> Dict[str, ModelConfiguration]:
        """Filter models that meet the requirements."""
        compatible = {}
        
        for model_name, config in self.available_models.items():
            # Check if model is available
            if not config.is_available:
                continue
            
            # Check context length
            if estimated_tokens > config.max_context:
                continue
            
            # Check capabilities (at least 50% match for flexibility)
            if required_capabilities:
                matching_capabilities = sum(
                    1 for cap in required_capabilities 
                    if cap in config.capabilities
                )
                capability_match_ratio = matching_capabilities / len(required_capabilities)
                if capability_match_ratio < 0.5:
                    continue
            
            compatible[model_name] = config
        
        return compatible
    
    async def _score_models(
        self,
        compatible_models: Dict[str, ModelConfiguration],
        document_characteristics: DocumentCharacteristics,
        processing_requirements: ProcessingRequirements,
        user_constraints: UserConstraints
    ) -> Dict[str, Dict[str, float]]:
        """Score models based on multiple criteria."""
        model_scores = {}
        
        for model_name, model_config in compatible_models.items():
            # Performance score
            performance_score = await self._calculate_performance_score(
                model_name, model_config, document_characteristics
            )
            
            # Cost score
            cost_score = await self._calculate_cost_score(
                model_name, model_config, document_characteristics, user_constraints
            )
            
            # Latency score
            latency_score = await self._calculate_latency_score(
                model_name, model_config, document_characteristics, processing_requirements
            )
            
            # Capability score
            capability_score = self._calculate_capability_score(
                model_config, document_characteristics, processing_requirements
            )
            
            # Weighted final score
            weights = self._get_scoring_weights(processing_requirements)
            final_score = (
                weights['performance'] * performance_score +
                weights['cost'] * cost_score +
                weights['latency'] * latency_score +
                weights['capability'] * capability_score
            )
            
            model_scores[model_name] = {
                'final_score': final_score,
                'performance_score': performance_score,
                'cost_score': cost_score,
                'latency_score': latency_score,
                'capability_score': capability_score,
                'estimated_cost': await self.cost_calculator.estimate_cost(
                    model_name, document_characteristics.estimated_tokens
                ),
                'estimated_latency': await self.latency_predictor.predict(
                    model_name, document_characteristics
                )
            }
        
        return model_scores
    
    async def _calculate_performance_score(
        self,
        model_name: str,
        model_config: ModelConfiguration,
        document_characteristics: DocumentCharacteristics
    ) -> float:
        """Calculate performance score for a model."""
        # Get historical performance data
        performance_data = await self.model_performance_db.get_performance_data(
            model_name, document_characteristics.document_type
        )
        
        # Combine historical and configuration data
        accuracy = performance_data.get('accuracy', model_config.accuracy_score or 0.8)
        reliability = performance_data.get('reliability', model_config.reliability_score or 0.9)
        
        return (accuracy + reliability) / 2
    
    async def _calculate_cost_score(
        self,
        model_name: str,
        model_config: ModelConfiguration,
        document_characteristics: DocumentCharacteristics,
        user_constraints: UserConstraints
    ) -> float:
        """Calculate cost score for a model."""
        estimated_cost = await self.cost_calculator.estimate_cost(
            model_name, document_characteristics.estimated_tokens
        )
        
        # Check against user constraints
        if user_constraints.max_cost_per_request:
            if estimated_cost > user_constraints.max_cost_per_request:
                return 0.0  # Exceeds budget
        
        # Normalize cost score (lower cost = higher score)
        max_cost = 1.0  # Maximum reasonable cost
        cost_score = max(0.0, 1.0 - (estimated_cost / max_cost))
        
        return cost_score
    
    async def _calculate_latency_score(
        self,
        model_name: str,
        model_config: ModelConfiguration,
        document_characteristics: DocumentCharacteristics,
        processing_requirements: ProcessingRequirements
    ) -> float:
        """Calculate latency score for a model."""
        estimated_latency = await self.latency_predictor.predict(
            model_name, document_characteristics
        )
        
        # Check against requirements
        if processing_requirements.max_latency:
            if estimated_latency > processing_requirements.max_latency:
                return 0.0  # Exceeds latency requirement
        
        # Normalize latency score (lower latency = higher score)
        max_latency = 10.0  # Maximum reasonable latency
        latency_score = max(0.0, 1.0 - (estimated_latency / max_latency))
        
        return latency_score
    
    def _calculate_capability_score(
        self,
        model_config: ModelConfiguration,
        document_characteristics: DocumentCharacteristics,
        processing_requirements: ProcessingRequirements
    ) -> float:
        """Calculate capability match score."""
        required_capabilities = []
        
        # Determine what capabilities are needed
        if document_characteristics.complexity_score > 0.7:
            required_capabilities.append(ModelCapability.COMPLEX_REASONING)
        
        if document_characteristics.estimated_tokens > 50000:
            required_capabilities.append(ModelCapability.LARGE_CONTEXT)
        
        if processing_requirements.prefer_speed:
            required_capabilities.append(ModelCapability.FAST_PROCESSING)
        
        if not required_capabilities:
            return 1.0  # No specific requirements
        
        # Calculate match ratio
        matching_capabilities = sum(
            1 for cap in required_capabilities 
            if cap in model_config.capabilities
        )
        
        return matching_capabilities / len(required_capabilities)
    
    def _get_scoring_weights(self, processing_requirements: ProcessingRequirements) -> Dict[str, float]:
        """Get scoring weights based on processing requirements."""
        if processing_requirements.prefer_speed:
            return {
                'performance': 0.3,
                'cost': 0.2,
                'latency': 0.4,
                'capability': 0.1
            }
        elif processing_requirements.prefer_cost_efficiency:
            return {
                'performance': 0.3,
                'cost': 0.5,
                'latency': 0.1,
                'capability': 0.1
            }
        else:  # Prefer accuracy
            return {
                'performance': 0.5,
                'cost': 0.2,
                'latency': 0.2,
                'capability': 0.1
            }
    
    def _generate_routing_reasoning(
        self, 
        model_scores: Dict[str, Dict[str, float]], 
        selected_model: str
    ) -> str:
        """Generate reasoning for model selection."""
        selected_scores = model_scores[selected_model]
        
        reasoning_parts = []
        
        if selected_scores['performance_score'] > 0.8:
            reasoning_parts.append("high performance score")
        
        if selected_scores['cost_score'] > 0.7:
            reasoning_parts.append("cost-effective")
        
        if selected_scores['latency_score'] > 0.7:
            reasoning_parts.append("low latency")
        
        if selected_scores['capability_score'] > 0.8:
            reasoning_parts.append("excellent capability match")
        
        if not reasoning_parts:
            reasoning_parts.append("best overall balance of factors")
        
        return f"Selected {selected_model} due to: {', '.join(reasoning_parts)}"
    
    async def _create_fallback_decision(
        self, 
        document_characteristics: DocumentCharacteristics
    ) -> ModelRoutingDecision:
        """Create a fallback decision when routing fails."""
        fallback_model = "gpt-4o-mini"  # Safe default
        
        return ModelRoutingDecision(
            selected_model=fallback_model,
            confidence=0.5,
            reasoning="Fallback to default model due to routing constraints",
            alternatives=[],
            estimated_cost=await self.cost_calculator.estimate_cost(
                fallback_model, document_characteristics.estimated_tokens
            ),
            estimated_latency=await self.latency_predictor.predict(
                fallback_model, document_characteristics
            )
        )
