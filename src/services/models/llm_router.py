"""
LLM Router

This service provides routing logic for LLM calls.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import random


class RoutingStrategy(Enum):
    """Routing strategies for LLM calls."""
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    FAILOVER = "failover"


@dataclass
class RouteRequest:
    """A request for routing."""
    prompt: str
    model_type: str
    requirements: Dict[str, Any] = None
    context: Dict[str, Any] = None


@dataclass
class RouteDecision:
    """A routing decision."""
    provider_id: str
    model_id: str
    strategy: RoutingStrategy
    confidence: float
    reason: str = ""


class LLMRouter:
    """
    LLM Router provides routing logic for LLM calls.
    
    This service implements various routing strategies to select the
    best provider and model for each request.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM Router.
        
        Args:
            config: Configuration for the LLM router
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Routing state
        self.round_robin_index = 0
        self.provider_stats: Dict[str, Dict[str, Any]] = {}
        
        # Default strategy
        self.default_strategy = RoutingStrategy(
            config.get("default_strategy", "round_robin")
        )
    
    def route_request(self, request: RouteRequest) -> RouteDecision:
        """
        Route a request to the best provider and model.
        
        Args:
            request: The routing request
            
        Returns:
            The routing decision
        """
        # Determine strategy
        strategy = self._determine_strategy(request)
        
        # Apply strategy
        if strategy == RoutingStrategy.ROUND_ROBIN:
            decision = self._route_round_robin(request)
        elif strategy == RoutingStrategy.LOAD_BALANCED:
            decision = self._route_load_balanced(request)
        elif strategy == RoutingStrategy.COST_OPTIMIZED:
            decision = self._route_cost_optimized(request)
        elif strategy == RoutingStrategy.PERFORMANCE_OPTIMIZED:
            decision = self._route_performance_optimized(request)
        elif strategy == RoutingStrategy.FAILOVER:
            decision = self._route_failover(request)
        else:
            decision = self._route_default(request)
        
        self.logger.info(
            f"Routed request to {decision.provider_id}/{decision.model_id} "
            f"using {strategy.value} strategy"
        )
        
        return decision
    
    def _determine_strategy(self, request: RouteRequest) -> RoutingStrategy:
        """Determine the routing strategy for a request."""
        # Check if request specifies a strategy
        if request.requirements and "routing_strategy" in request.requirements:
            strategy = request.requirements["routing_strategy"]
            try:
                return RoutingStrategy(strategy)
            except ValueError:
                self.logger.warning(f"Invalid routing strategy: {strategy}")
        
        # Use default strategy
        return self.default_strategy
    
    def _route_round_robin(self, request: RouteRequest) -> RouteDecision:
        """Route using round-robin strategy."""
        # Get available providers
        providers = self._get_available_providers(request.model_type)
        if not providers:
            raise ValueError("No available providers for model type")
        
        # Select provider using round-robin
        provider_id = providers[self.round_robin_index % len(providers)]
        self.round_robin_index += 1
        
        # Get model for provider
        model_id = self._get_model_for_provider(provider_id, request.model_type)
        
        return RouteDecision(
            provider_id=provider_id,
            model_id=model_id,
            strategy=RoutingStrategy.ROUND_ROBIN,
            confidence=0.8,
            reason="Round-robin selection"
        )
    
    def _route_load_balanced(self, request: RouteRequest) -> RouteDecision:
        """Route using load-balanced strategy."""
        # Get available providers
        providers = self._get_available_providers(request.model_type)
        if not providers:
            raise ValueError("No available providers for model type")
        
        # Select provider with lowest load
        best_provider = None
        lowest_load = float('inf')
        
        for provider_id in providers:
            load = self._get_provider_load(provider_id)
            if load < lowest_load:
                lowest_load = load
                best_provider = provider_id
        
        # Get model for provider
        model_id = self._get_model_for_provider(best_provider, request.model_type)
        
        return RouteDecision(
            provider_id=best_provider,
            model_id=model_id,
            strategy=RoutingStrategy.LOAD_BALANCED,
            confidence=0.9,
            reason=f"Lowest load: {lowest_load}"
        )
    
    def _route_cost_optimized(self, request: RouteRequest) -> RouteDecision:
        """Route using cost-optimized strategy."""
        # Get available providers
        providers = self._get_available_providers(request.model_type)
        if not providers:
            raise ValueError("No available providers for model type")
        
        # Select provider with lowest cost
        best_provider = None
        lowest_cost = float('inf')
        
        for provider_id in providers:
            cost = self._get_provider_cost(provider_id, request.model_type)
            if cost < lowest_cost:
                lowest_cost = cost
                best_provider = provider_id
        
        # Get model for provider
        model_id = self._get_model_for_provider(best_provider, request.model_type)
        
        return RouteDecision(
            provider_id=best_provider,
            model_id=model_id,
            strategy=RoutingStrategy.COST_OPTIMIZED,
            confidence=0.7,
            reason=f"Lowest cost: {lowest_cost}"
        )
    
    def _route_performance_optimized(self, request: RouteRequest) -> RouteDecision:
        """Route using performance-optimized strategy."""
        # Get available providers
        providers = self._get_available_providers(request.model_type)
        if not providers:
            raise ValueError("No available providers for model type")
        
        # Select provider with best performance
        best_provider = None
        best_performance = 0
        
        for provider_id in providers:
            performance = self._get_provider_performance(provider_id, request.model_type)
            if performance > best_performance:
                best_performance = performance
                best_provider = provider_id
        
        # Get model for provider
        model_id = self._get_model_for_provider(best_provider, request.model_type)
        
        return RouteDecision(
            provider_id=best_provider,
            model_id=model_id,
            strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED,
            confidence=0.9,
            reason=f"Best performance: {best_performance}"
        )
    
    def _route_failover(self, request: RouteRequest) -> RouteDecision:
        """Route using failover strategy."""
        # Get available providers
        providers = self._get_available_providers(request.model_type)
        if not providers:
            raise ValueError("No available providers for model type")
        
        # Try primary provider first
        primary_provider = self.config.get("primary_provider")
        if primary_provider and primary_provider in providers:
            model_id = self._get_model_for_provider(primary_provider, request.model_type)
            if self._is_provider_available(primary_provider):
                return RouteDecision(
                    provider_id=primary_provider,
                    model_id=model_id,
                    strategy=RoutingStrategy.FAILOVER,
                    confidence=1.0,
                    reason="Primary provider"
                )
        
        # Fallback to any available provider
        for provider_id in providers:
            if self._is_provider_available(provider_id):
                model_id = self._get_model_for_provider(provider_id, request.model_type)
                return RouteDecision(
                    provider_id=provider_id,
                    model_id=model_id,
                    strategy=RoutingStrategy.FAILOVER,
                    confidence=0.8,
                    reason="Failover provider"
                )
        
        # No available providers
        raise ValueError("No available providers for failover")
    
    def _route_default(self, request: RouteRequest) -> RouteDecision:
        """Route using default strategy."""
        return self._route_round_robin(request)
    
    def _get_available_providers(self, model_type: str) -> List[str]:
        """Get available providers for a model type."""
        # Implementation would query provider registry
        # For now, return mock providers
        return ["provider1", "provider2", "provider3"]
    
    def _get_model_for_provider(self, provider_id: str, model_type: str) -> str:
        """Get a model for a provider and model type."""
        # Implementation would query model registry
        # For now, return a mock model ID
        return f"{provider_id}_{model_type}_model"
    
    def _get_provider_load(self, provider_id: str) -> float:
        """Get the current load for a provider."""
        stats = self.provider_stats.get(provider_id, {})
        return stats.get("current_load", 0.5)
    
    def _get_provider_cost(self, provider_id: str, model_type: str) -> float:
        """Get the cost for a provider and model type."""
        # Implementation would query pricing information
        # For now, return mock costs
        return random.uniform(0.001, 0.01)
    
    def _get_provider_performance(self, provider_id: str, model_type: str) -> float:
        """Get the performance score for a provider and model type."""
        stats = self.provider_stats.get(provider_id, {})
        return stats.get("performance_score", 0.8)
    
    def _is_provider_available(self, provider_id: str) -> bool:
        """Check if a provider is available."""
        stats = self.provider_stats.get(provider_id, {})
        return stats.get("is_available", True)
    
    def update_provider_stats(self, provider_id: str, stats: Dict[str, Any]):
        """
        Update statistics for a provider.
        
        Args:
            provider_id: The provider ID
            stats: The statistics to update
        """
        if provider_id not in self.provider_stats:
            self.provider_stats[provider_id] = {}
        
        self.provider_stats[provider_id].update(stats)
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get routing statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "round_robin_index": self.round_robin_index,
            "provider_stats": self.provider_stats,
            "default_strategy": self.default_strategy.value
        }
