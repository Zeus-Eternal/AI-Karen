"""
Intelligent Model Router

This service provides intelligent routing for model calls using
telemetry and optimization logic.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import time
import statistics

from .llm_router import LLMRouter, RoutingStrategy, RouteRequest, RouteDecision


class ModelCapability(Enum):
    """Model capabilities."""
    SPEED = "speed"
    QUALITY = "quality"
    COST = "cost"
    RELIABILITY = "reliability"


@dataclass
class ModelMetrics:
    """Metrics for a model."""
    model_id: str
    provider_id: str
    avg_latency_ms: float
    error_rate: float
    cost_per_token: float
    quality_score: float
    availability: float
    last_updated: float


@dataclass
class RoutingContext:
    """Context for routing decisions."""
    user_id: str
    session_id: str
    request_type: str
    priority: str
    budget_limit: Optional[float] = None
    latency_limit_ms: Optional[int] = None
    quality_threshold: Optional[float] = None


class IntelligentModelRouter:
    """
    Intelligent Model Router provides intelligent routing for model calls
    using telemetry and optimization logic.
    
    This service extends the basic LLM router with intelligent
    decision-making based on historical performance metrics and
    contextual requirements.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Intelligent Model Router.
        
        Args:
            config: Configuration for the intelligent model router
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize base router
        self.base_router = LLMRouter(config.get("base_router", {}))
        
        # Model metrics storage
        self.model_metrics: Dict[str, ModelMetrics] = {}
        
        # Routing history
        self.routing_history: List[Dict[str, Any]] = []
        
        # Configuration
        self.telemetry_weight = config.get("telemetry_weight", 0.7)
        self.context_weight = config.get("context_weight", 0.3)
        self.learning_rate = config.get("learning_rate", 0.1)
    
    def route_intelligent(
        self, 
        request: RouteRequest, 
        context: RoutingContext
    ) -> RouteDecision:
        """
        Route a request using intelligent routing.
        
        Args:
            request: The routing request
            context: The routing context
            
        Returns:
            The routing decision
        """
        # Get available models
        available_models = self._get_available_models(request.model_type)
        if not available_models:
            raise ValueError("No available models for request")
        
        # Score each model
        model_scores = []
        for model_id in available_models:
            score = self._score_model(model_id, request, context)
            model_scores.append((model_id, score))
        
        # Sort by score
        model_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select best model
        best_model_id, best_score = model_scores[0]
        
        # Get provider for model
        provider_id = self._get_provider_for_model(best_model_id)
        
        # Create decision
        decision = RouteDecision(
            provider_id=provider_id,
            model_id=best_model_id,
            strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED,
            confidence=best_score,
            reason=f"Intelligent routing with score: {best_score:.2f}"
        )
        
        # Record routing decision
        self._record_routing_decision(request, context, decision)
        
        return decision
    
    def _score_model(
        self, 
        model_id: str, 
        request: RouteRequest, 
        context: RoutingContext
    ) -> float:
        """
        Score a model for the given request and context.
        
        Args:
            model_id: The model ID
            request: The routing request
            context: The routing context
            
        Returns:
            The model score (0.0 to 1.0)
        """
        # Get model metrics
        metrics = self.model_metrics.get(model_id)
        if not metrics:
            # No metrics available, use default score
            return 0.5
        
        # Calculate telemetry score
        telemetry_score = self._calculate_telemetry_score(metrics)
        
        # Calculate context score
        context_score = self._calculate_context_score(metrics, context)
        
        # Combine scores
        total_score = (
            telemetry_score * self.telemetry_weight + 
            context_score * self.context_weight
        )
        
        return min(max(total_score, 0.0), 1.0)
    
    def _calculate_telemetry_score(self, metrics: ModelMetrics) -> float:
        """Calculate score based on telemetry metrics."""
        # Normalize metrics
        latency_score = 1.0 - min(metrics.avg_latency_ms / 10000, 1.0)  # 10s max
        reliability_score = metrics.availability
        quality_score = metrics.quality_score
        cost_score = 1.0 - min(metrics.cost_per_token * 1000, 1.0)  # $0.001 per token max
        
        # Weighted average
        weights = self.config.get("telemetry_weights", {
            "latency": 0.3,
            "reliability": 0.3,
            "quality": 0.3,
            "cost": 0.1
        })
        
        telemetry_score = (
            latency_score * weights["latency"] +
            reliability_score * weights["reliability"] +
            quality_score * weights["quality"] +
            cost_score * weights["cost"]
        )
        
        return telemetry_score
    
    def _calculate_context_score(
        self, 
        metrics: ModelMetrics, 
        context: RoutingContext
    ) -> float:
        """Calculate score based on routing context."""
        context_score = 1.0  # Default score
        
        # Check latency limit
        if context.latency_limit_ms:
            if metrics.avg_latency_ms > context.latency_limit_ms:
                context_score *= 0.5  # Penalty for exceeding limit
        
        # Check quality threshold
        if context.quality_threshold:
            if metrics.quality_score < context.quality_threshold:
                context_score *= 0.5  # Penalty for not meeting threshold
        
        # Check budget limit
        if context.budget_limit:
            # Estimate cost for this request
            estimated_cost = metrics.cost_per_token * 1000  # Assume 1K tokens
            if estimated_cost > context.budget_limit:
                context_score *= 0.5  # Penalty for exceeding budget
        
        # Adjust for priority
        if context.priority == "high":
            # Prioritize speed and reliability
            context_score *= (metrics.availability * 0.7 + (1.0 - metrics.avg_latency_ms / 10000) * 0.3)
        elif context.priority == "low":
            # Prioritize cost
            context_score *= (1.0 - min(metrics.cost_per_token * 1000, 1.0))
        
        return min(max(context_score, 0.0), 1.0)
    
    def _get_available_models(self, model_type: str) -> List[str]:
        """Get available models for a model type."""
        # Implementation would query model registry
        # For now, return mock models
        return [
            "provider1_gpt4_model",
            "provider2_claude_model",
            "provider3_llama_model"
        ]
    
    def _get_provider_for_model(self, model_id: str) -> str:
        """Get the provider for a model."""
        # Extract provider from model ID
        return model_id.split("_")[0]
    
    def _record_routing_decision(
        self, 
        request: RouteRequest, 
        context: RoutingContext, 
        decision: RouteDecision
    ):
        """Record a routing decision for learning."""
        record = {
            "timestamp": time.time(),
            "request": {
                "model_type": request.model_type,
                "prompt_length": len(request.prompt)
            },
            "context": {
                "user_id": context.user_id,
                "session_id": context.session_id,
                "priority": context.priority
            },
            "decision": {
                "provider_id": decision.provider_id,
                "model_id": decision.model_id,
                "strategy": decision.strategy.value,
                "confidence": decision.confidence
            }
        }
        
        self.routing_history.append(record)
        
        # Keep only recent history
        max_history = self.config.get("max_history", 1000)
        if len(self.routing_history) > max_history:
            self.routing_history = self.routing_history[-max_history:]
    
    def update_model_metrics(self, metrics: ModelMetrics):
        """
        Update metrics for a model.
        
        Args:
            metrics: The model metrics to update
        """
        self.model_metrics[metrics.model_id] = metrics
    
    def get_model_recommendations(
        self, 
        model_type: str, 
        context: RoutingContext
    ) -> List[Dict[str, Any]]:
        """
        Get model recommendations for a request.
        
        Args:
            model_type: The model type
            context: The routing context
            
        Returns:
            List of model recommendations
        """
        # Get available models
        available_models = self._get_available_models(model_type)
        
        # Score each model
        recommendations = []
        for model_id in available_models:
            metrics = self.model_metrics.get(model_id)
            if metrics:
                score = self._score_model(
                    model_id, 
                    RouteRequest(prompt="", model_type=model_type), 
                    context
                )
                
                recommendations.append({
                    "model_id": model_id,
                    "provider_id": metrics.provider_id,
                    "score": score,
                    "metrics": {
                        "avg_latency_ms": metrics.avg_latency_ms,
                        "error_rate": metrics.error_rate,
                        "cost_per_token": metrics.cost_per_token,
                        "quality_score": metrics.quality_score,
                        "availability": metrics.availability
                    }
                })
        
        # Sort by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        return recommendations
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get routing statistics.
        
        Returns:
            Dictionary of statistics
        """
        # Calculate model usage statistics
        model_usage = {}
        for record in self.routing_history:
            model_id = record["decision"]["model_id"]
            if model_id not in model_usage:
                model_usage[model_id] = 0
            model_usage[model_id] += 1
        
        # Calculate provider usage statistics
        provider_usage = {}
        for record in self.routing_history:
            provider_id = record["decision"]["provider_id"]
            if provider_id not in provider_usage:
                provider_usage[provider_id] = 0
            provider_usage[provider_id] += 1
        
        return {
            "total_routings": len(self.routing_history),
            "model_usage": model_usage,
            "provider_usage": provider_usage,
            "model_metrics_count": len(self.model_metrics),
            "config": {
                "telemetry_weight": self.telemetry_weight,
                "context_weight": self.context_weight,
                "learning_rate": self.learning_rate
            }
        }
