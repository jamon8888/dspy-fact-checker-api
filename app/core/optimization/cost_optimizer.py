"""
Cost Optimizer

This module provides cost optimization capabilities for document processing
pipelines, including budget management and cost-aware model selection.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .data_models import UserConstraints, ModelConfiguration

logger = logging.getLogger(__name__)


@dataclass
class CostEstimate:
    """Cost estimate for a processing request."""
    estimated_cost: float
    breakdown: Dict[str, float]
    confidence: float
    factors: List[str]


@dataclass
class BudgetStatus:
    """Current budget status for a user."""
    monthly_budget: Optional[float]
    remaining_budget: Optional[float]
    monthly_usage: float
    daily_usage: float
    projected_monthly_usage: float
    budget_utilization: float


class CostCalculator:
    """Calculates processing costs for different models and configurations."""
    
    def __init__(self):
        """Initialize the cost calculator."""
        self.logger = logging.getLogger(__name__ + ".CostCalculator")
        
        # Model pricing (cost per 1K tokens)
        self.model_pricing = {
            "gpt-4o": {"input": 0.0025, "output": 0.01},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
            "gemini-flash": {"input": 0.000075, "output": 0.0003}
        }
        
        # Additional service costs
        self.service_costs = {
            "ocr_processing": 0.001,  # per page
            "translation": 0.0002,   # per 100 characters
            "specialized_analysis": 0.005  # per request
        }
    
    async def estimate_cost(
        self,
        model_name: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int,
        additional_services: Optional[List[str]] = None
    ) -> CostEstimate:
        """Estimate cost for a processing request."""
        try:
            breakdown = {}
            factors = []
            
            # Model costs
            if model_name in self.model_pricing:
                pricing = self.model_pricing[model_name]
                input_cost = (estimated_input_tokens / 1000) * pricing["input"]
                output_cost = (estimated_output_tokens / 1000) * pricing["output"]
                
                breakdown["model_input"] = input_cost
                breakdown["model_output"] = output_cost
                factors.append(f"Model: {model_name}")
            else:
                # Default pricing for unknown models
                input_cost = (estimated_input_tokens / 1000) * 0.002
                output_cost = (estimated_output_tokens / 1000) * 0.006
                breakdown["model_input"] = input_cost
                breakdown["model_output"] = output_cost
                factors.append(f"Model: {model_name} (default pricing)")
            
            # Additional service costs
            if additional_services:
                for service in additional_services:
                    if service in self.service_costs:
                        service_cost = self.service_costs[service]
                        breakdown[f"service_{service}"] = service_cost
                        factors.append(f"Service: {service}")
            
            total_cost = sum(breakdown.values())
            
            # Confidence based on known vs unknown models
            confidence = 0.9 if model_name in self.model_pricing else 0.7
            
            return CostEstimate(
                estimated_cost=total_cost,
                breakdown=breakdown,
                confidence=confidence,
                factors=factors
            )
            
        except Exception as e:
            self.logger.error(f"Error estimating cost: {e}")
            return CostEstimate(
                estimated_cost=0.01,  # Default estimate
                breakdown={"error": 0.01},
                confidence=0.1,
                factors=["Error in cost calculation"]
            )
    
    async def compare_model_costs(
        self,
        models: List[str],
        estimated_input_tokens: int,
        estimated_output_tokens: int
    ) -> Dict[str, CostEstimate]:
        """Compare costs across multiple models."""
        cost_comparisons = {}
        
        for model in models:
            cost_estimate = await self.estimate_cost(
                model, estimated_input_tokens, estimated_output_tokens
            )
            cost_comparisons[model] = cost_estimate
        
        return cost_comparisons


class BudgetManager:
    """Manages user budgets and spending tracking."""
    
    def __init__(self):
        """Initialize the budget manager."""
        self.logger = logging.getLogger(__name__ + ".BudgetManager")
        self.user_spending = {}  # In practice, this would be a database
    
    async def get_budget_status(self, user_id: str, user_constraints: UserConstraints) -> BudgetStatus:
        """Get current budget status for a user."""
        try:
            # Get spending history
            monthly_usage = self._get_monthly_usage(user_id)
            daily_usage = self._get_daily_usage(user_id)
            
            # Calculate projections
            days_in_month = 30  # Simplified
            days_elapsed = datetime.now().day
            projected_monthly_usage = (daily_usage * days_in_month) if daily_usage > 0 else monthly_usage
            
            # Calculate budget utilization
            budget_utilization = 0.0
            if user_constraints.monthly_budget:
                budget_utilization = monthly_usage / user_constraints.monthly_budget
            
            return BudgetStatus(
                monthly_budget=user_constraints.monthly_budget,
                remaining_budget=user_constraints.remaining_budget,
                monthly_usage=monthly_usage,
                daily_usage=daily_usage,
                projected_monthly_usage=projected_monthly_usage,
                budget_utilization=budget_utilization
            )
            
        except Exception as e:
            self.logger.error(f"Error getting budget status: {e}")
            return BudgetStatus(
                monthly_budget=None,
                remaining_budget=None,
                monthly_usage=0.0,
                daily_usage=0.0,
                projected_monthly_usage=0.0,
                budget_utilization=0.0
            )
    
    async def check_budget_constraints(
        self,
        user_id: str,
        user_constraints: UserConstraints,
        estimated_cost: float
    ) -> Dict[str, Any]:
        """Check if request fits within budget constraints."""
        try:
            budget_status = await self.get_budget_status(user_id, user_constraints)
            
            constraints_check = {
                "within_budget": True,
                "warnings": [],
                "blocking_issues": []
            }
            
            # Check per-request limit
            if user_constraints.max_cost_per_request:
                if estimated_cost > user_constraints.max_cost_per_request:
                    constraints_check["within_budget"] = False
                    constraints_check["blocking_issues"].append(
                        f"Cost ${estimated_cost:.4f} exceeds per-request limit ${user_constraints.max_cost_per_request:.4f}"
                    )
            
            # Check remaining budget
            if user_constraints.remaining_budget is not None:
                if estimated_cost > user_constraints.remaining_budget:
                    constraints_check["within_budget"] = False
                    constraints_check["blocking_issues"].append(
                        f"Cost ${estimated_cost:.4f} exceeds remaining budget ${user_constraints.remaining_budget:.4f}"
                    )
                elif estimated_cost > user_constraints.remaining_budget * 0.8:
                    constraints_check["warnings"].append(
                        f"Cost ${estimated_cost:.4f} uses significant portion of remaining budget"
                    )
            
            # Check monthly budget projection
            if budget_status.monthly_budget:
                projected_total = budget_status.monthly_usage + estimated_cost
                if projected_total > budget_status.monthly_budget:
                    constraints_check["warnings"].append(
                        f"Request may contribute to monthly budget overrun"
                    )
            
            return constraints_check
            
        except Exception as e:
            self.logger.error(f"Error checking budget constraints: {e}")
            return {
                "within_budget": True,
                "warnings": [f"Error checking budget: {str(e)}"],
                "blocking_issues": []
            }
    
    async def record_spending(self, user_id: str, cost: float, details: Dict[str, Any]):
        """Record spending for a user."""
        try:
            if user_id not in self.user_spending:
                self.user_spending[user_id] = []
            
            spending_record = {
                "cost": cost,
                "timestamp": datetime.now(),
                "details": details
            }
            
            self.user_spending[user_id].append(spending_record)
            self.logger.debug(f"Recorded spending of ${cost:.4f} for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error recording spending: {e}")
    
    def _get_monthly_usage(self, user_id: str) -> float:
        """Get monthly usage for a user."""
        if user_id not in self.user_spending:
            return 0.0
        
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_spending = [
            record["cost"] for record in self.user_spending[user_id]
            if record["timestamp"] >= current_month
        ]
        
        return sum(monthly_spending)
    
    def _get_daily_usage(self, user_id: str) -> float:
        """Get daily usage for a user."""
        if user_id not in self.user_spending:
            return 0.0
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_spending = [
            record["cost"] for record in self.user_spending[user_id]
            if record["timestamp"] >= today
        ]
        
        return sum(daily_spending)


class CostOptimizer:
    """Main cost optimization system."""
    
    def __init__(self):
        """Initialize the cost optimizer."""
        self.cost_calculator = CostCalculator()
        self.budget_manager = BudgetManager()
        self.logger = logging.getLogger(__name__ + ".CostOptimizer")
    
    async def optimize_for_cost(
        self,
        available_models: List[str],
        estimated_input_tokens: int,
        estimated_output_tokens: int,
        user_constraints: UserConstraints,
        quality_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Find the most cost-effective model that meets quality requirements."""
        try:
            # Get cost estimates for all models
            cost_comparisons = await self.cost_calculator.compare_model_costs(
                available_models, estimated_input_tokens, estimated_output_tokens
            )
            
            # Filter models by budget constraints
            affordable_models = []
            for model, cost_estimate in cost_comparisons.items():
                if user_constraints.max_cost_per_request:
                    if cost_estimate.estimated_cost <= user_constraints.max_cost_per_request:
                        affordable_models.append((model, cost_estimate))
                else:
                    affordable_models.append((model, cost_estimate))
            
            if not affordable_models:
                return {
                    "success": False,
                    "error": "No models within budget constraints",
                    "cost_comparisons": cost_comparisons
                }
            
            # Sort by cost (ascending)
            affordable_models.sort(key=lambda x: x[1].estimated_cost)
            
            # Select most cost-effective model
            selected_model, selected_cost = affordable_models[0]
            
            # Calculate potential savings
            most_expensive = max(cost_comparisons.values(), key=lambda x: x.estimated_cost)
            potential_savings = most_expensive.estimated_cost - selected_cost.estimated_cost
            
            return {
                "success": True,
                "selected_model": selected_model,
                "estimated_cost": selected_cost.estimated_cost,
                "cost_breakdown": selected_cost.breakdown,
                "potential_savings": potential_savings,
                "alternatives": [
                    {
                        "model": model,
                        "cost": cost.estimated_cost,
                        "savings": cost.estimated_cost - selected_cost.estimated_cost
                    }
                    for model, cost in affordable_models[1:3]  # Top 2 alternatives
                ],
                "cost_comparisons": cost_comparisons
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing for cost: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_cost_optimization_recommendations(
        self,
        user_id: str,
        user_constraints: UserConstraints,
        usage_patterns: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get cost optimization recommendations for a user."""
        try:
            recommendations = []
            
            # Get budget status
            budget_status = await self.budget_manager.get_budget_status(user_id, user_constraints)
            
            # Budget utilization recommendations
            if budget_status.budget_utilization > 0.8:
                recommendations.append({
                    "type": "budget_warning",
                    "priority": "high",
                    "title": "High Budget Utilization",
                    "description": f"You've used {budget_status.budget_utilization:.1%} of your monthly budget",
                    "action": "Consider using more cost-effective models or reducing processing frequency"
                })
            
            # Model selection recommendations
            if usage_patterns and usage_patterns.get("preferred_models"):
                expensive_models = ["gpt-4o", "claude-3-opus"]
                if any(model in expensive_models for model in usage_patterns["preferred_models"]):
                    recommendations.append({
                        "type": "model_optimization",
                        "priority": "medium",
                        "title": "Consider Cost-Effective Alternatives",
                        "description": "You're using premium models that may be more expensive",
                        "action": "Try gpt-4o-mini or claude-3-haiku for simpler tasks"
                    })
            
            # Batch processing recommendations
            if usage_patterns and usage_patterns.get("request_frequency", 0) > 10:
                recommendations.append({
                    "type": "efficiency",
                    "priority": "medium",
                    "title": "Batch Processing Opportunity",
                    "description": "High request frequency detected",
                    "action": "Consider batching multiple documents to reduce per-request overhead"
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting cost optimization recommendations: {e}")
            return []
    
    async def estimate_monthly_costs(
        self,
        user_id: str,
        user_constraints: UserConstraints,
        projected_usage: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate monthly costs based on projected usage."""
        try:
            # Get current usage patterns
            budget_status = await self.budget_manager.get_budget_status(user_id, user_constraints)
            
            # Calculate projections
            daily_requests = projected_usage.get("daily_requests", 10)
            avg_tokens_per_request = projected_usage.get("avg_tokens_per_request", 5000)
            preferred_model = projected_usage.get("preferred_model", "gpt-4o-mini")
            
            # Estimate daily cost
            daily_cost_estimate = await self.cost_calculator.estimate_cost(
                preferred_model,
                avg_tokens_per_request,
                avg_tokens_per_request // 4,  # Assume 4:1 input:output ratio
            )
            
            daily_cost = daily_cost_estimate.estimated_cost * daily_requests
            monthly_cost = daily_cost * 30
            
            # Compare with budget
            budget_fit = "within_budget"
            if user_constraints.monthly_budget:
                if monthly_cost > user_constraints.monthly_budget:
                    budget_fit = "over_budget"
                elif monthly_cost > user_constraints.monthly_budget * 0.8:
                    budget_fit = "tight_budget"
            
            return {
                "projected_monthly_cost": monthly_cost,
                "projected_daily_cost": daily_cost,
                "current_monthly_usage": budget_status.monthly_usage,
                "budget_fit": budget_fit,
                "cost_breakdown": daily_cost_estimate.breakdown,
                "assumptions": {
                    "daily_requests": daily_requests,
                    "avg_tokens_per_request": avg_tokens_per_request,
                    "preferred_model": preferred_model
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error estimating monthly costs: {e}")
            return {"error": str(e)}
