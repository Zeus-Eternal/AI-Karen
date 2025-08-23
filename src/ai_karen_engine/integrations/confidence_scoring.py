"""
Advanced Confidence Scoring System for LLM Router

This module provides sophisticated confidence scoring for routing decisions,
taking into account multiple factors including policy alignment, health status,
performance history, and capability matching.

Key Features:
- Multi-factor confidence scoring
- Historical performance weighting
- Capability matching assessment
- Policy alignment scoring
- Health-based adjustments
- Meta information for explainability
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ai_karen_engine.integrations.llm_router import RoutingRequest, RoutingPolicy
from ai_karen_engine.integrations.registry import ModelMetadata, ProviderSpec, RuntimeSpec

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceFactors:
    """Breakdown of confidence scoring factors."""
    policy_alignment: float = 0.0
    health_status: float = 0.0
    capability_match: float = 0.0
    performance_history: float = 0.0
    availability: float = 0.0
    cost_efficiency: float = 0.0
    privacy_compliance: float = 0.0
    user_preference: float = 0.0
    
    # Weights for each factor
    policy_weight: float = 0.25
    health_weight: float = 0.20
    capability_weight: float = 0.15
    performance_weight: float = 0.15
    availability_weight: float = 0.10
    cost_weight: float = 0.05
    privacy_weight: float = 0.05
    preference_weight: float = 0.05
    
    def calculate_weighted_score(self) -> float:
        """Calculate the final weighted confidence score."""
        return (
            self.policy_alignment * self.policy_weight +
            self.health_status * self.health_weight +
            self.capability_match * self.capability_weight +
            self.performance_history * self.performance_weight +
            self.availability * self.availability_weight +
            self.cost_efficiency * self.cost_weight +
            self.privacy_compliance * self.privacy_weight +
            self.user_preference * self.preference_weight
        )


@dataclass
class ConfidenceMetadata:
    """Metadata about confidence scoring for explainability."""
    factors: ConfidenceFactors
    reasoning: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    alternatives_considered: int = 0
    scoring_time: float = 0.0


class AdvancedConfidenceScorer:
    """
    Advanced confidence scoring system for routing decisions.
    
    This scorer evaluates routing decisions across multiple dimensions
    to provide accurate confidence scores and detailed explanations.
    """
    
    def __init__(self, registry=None, health_monitor=None):
        self.registry = registry
        self.health_monitor = health_monitor
        
        # Performance history tracking
        self.performance_history: Dict[str, List[float]] = {}
        self.response_times: Dict[str, List[float]] = {}
        self.success_rates: Dict[str, float] = {}
        
        # Cost tracking
        self.cost_history: Dict[str, List[float]] = {}
        
        logger.info("Advanced confidence scorer initialized")
    
    def score_routing_decision(
        self,
        request: RoutingRequest,
        provider: str,
        runtime: str,
        model_id: str,
        policy: RoutingPolicy,
        provider_spec: Optional[ProviderSpec] = None,
        runtime_spec: Optional[RuntimeSpec] = None,
    ) -> Tuple[float, ConfidenceMetadata]:
        """
        Score a routing decision and provide detailed metadata.
        
        Args:
            request: The routing request
            provider: Selected provider
            runtime: Selected runtime
            model_id: Selected model
            policy: Active routing policy
            provider_spec: Provider specification (optional)
            runtime_spec: Runtime specification (optional)
            
        Returns:
            Tuple of (confidence_score, metadata)
        """
        start_time = time.time()
        
        factors = ConfidenceFactors()
        reasoning = []
        warnings = []
        
        # Get specs if not provided
        if not provider_spec and self.registry:
            provider_spec = self.registry.get_provider_spec(provider)
        if not runtime_spec and self.registry:
            runtime_spec = self.registry.get_runtime_spec(runtime)
        
        # 1. Policy Alignment Scoring
        factors.policy_alignment = self._score_policy_alignment(
            request, provider, runtime, policy, reasoning
        )
        
        # 2. Health Status Scoring
        factors.health_status = self._score_health_status(
            provider, runtime, reasoning, warnings
        )
        
        # 3. Capability Matching Scoring
        factors.capability_match = self._score_capability_match(
            request, provider_spec, runtime_spec, reasoning, warnings
        )
        
        # 4. Performance History Scoring
        factors.performance_history = self._score_performance_history(
            provider, runtime, reasoning
        )
        
        # 5. Availability Scoring
        factors.availability = self._score_availability(
            provider, runtime, reasoning
        )
        
        # 6. Cost Efficiency Scoring
        factors.cost_efficiency = self._score_cost_efficiency(
            provider, model_id, reasoning
        )
        
        # 7. Privacy Compliance Scoring
        factors.privacy_compliance = self._score_privacy_compliance(
            request, provider, runtime, policy, reasoning
        )
        
        # 8. User Preference Scoring
        factors.user_preference = self._score_user_preference(
            request, provider, runtime, model_id, reasoning
        )
        
        # Apply policy weights
        factors.policy_weight = policy.privacy_weight if hasattr(policy, 'privacy_weight') else 0.25
        factors.health_weight = policy.availability_weight if hasattr(policy, 'availability_weight') else 0.20
        factors.performance_weight = policy.performance_weight if hasattr(policy, 'performance_weight') else 0.15
        factors.cost_weight = policy.cost_weight if hasattr(policy, 'cost_weight') else 0.05
        
        # Calculate final score
        final_score = factors.calculate_weighted_score()
        
        # Create metadata
        metadata = ConfidenceMetadata(
            factors=factors,
            reasoning=reasoning,
            warnings=warnings,
            alternatives_considered=0,  # Would be set by caller
            scoring_time=time.time() - start_time,
        )
        
        return final_score, metadata
    
    def _score_policy_alignment(
        self,
        request: RoutingRequest,
        provider: str,
        runtime: str,
        policy: RoutingPolicy,
        reasoning: List[str],
    ) -> float:
        """Score how well the selection aligns with policy preferences."""
        score = 0.0
        
        # Task-based alignment
        preferred_provider = policy.task_provider_map.get(request.task_type)
        preferred_runtime = policy.task_runtime_map.get(request.task_type)
        
        if provider == preferred_provider:
            score += 0.4
            reasoning.append(f"Provider {provider} matches task preference for {request.task_type.value}")
        elif preferred_provider:
            score += 0.1
            reasoning.append(f"Provider {provider} differs from task preference {preferred_provider}")
        
        if runtime == preferred_runtime:
            score += 0.4
            reasoning.append(f"Runtime {runtime} matches task preference for {request.task_type.value}")
        elif preferred_runtime:
            score += 0.1
            reasoning.append(f"Runtime {runtime} differs from task preference {preferred_runtime}")
        
        # Performance requirement alignment
        perf_provider = policy.performance_provider_map.get(request.performance_req)
        perf_runtime = policy.performance_runtime_map.get(request.performance_req)
        
        if provider == perf_provider:
            score += 0.1
            reasoning.append(f"Provider aligns with performance requirement {request.performance_req.value}")
        
        if runtime == perf_runtime:
            score += 0.1
            reasoning.append(f"Runtime aligns with performance requirement {request.performance_req.value}")
        
        return min(score, 1.0)
    
    def _score_health_status(
        self,
        provider: str,
        runtime: str,
        reasoning: List[str],
        warnings: List[str],
    ) -> float:
        """Score based on current health status."""
        score = 0.0
        
        if self.registry:
            # Provider health
            provider_health = self.registry.get_health_status(f"provider:{provider}")
            if provider_health:
                if provider_health.status == "healthy":
                    score += 0.5
                    reasoning.append(f"Provider {provider} is healthy")
                elif provider_health.status == "degraded":
                    score += 0.3
                    warnings.append(f"Provider {provider} is in degraded state")
                else:
                    score += 0.1
                    warnings.append(f"Provider {provider} is unhealthy: {provider_health.error_message}")
            else:
                score += 0.4  # Unknown status, assume reasonable health
                reasoning.append(f"Provider {provider} health status unknown")
            
            # Runtime health
            runtime_health = self.registry.get_health_status(f"runtime:{runtime}")
            if runtime_health:
                if runtime_health.status == "healthy":
                    score += 0.5
                    reasoning.append(f"Runtime {runtime} is healthy")
                elif runtime_health.status == "degraded":
                    score += 0.3
                    warnings.append(f"Runtime {runtime} is in degraded state")
                else:
                    score += 0.1
                    warnings.append(f"Runtime {runtime} is unhealthy: {runtime_health.error_message}")
            else:
                score += 0.4  # Unknown status, assume reasonable health
                reasoning.append(f"Runtime {runtime} health status unknown")
        else:
            score = 0.8  # No health monitoring, assume good health
            reasoning.append("Health monitoring not available, assuming good health")
        
        return min(score, 1.0)
    
    def _score_capability_match(
        self,
        request: RoutingRequest,
        provider_spec: Optional[ProviderSpec],
        runtime_spec: Optional[RuntimeSpec],
        reasoning: List[str],
        warnings: List[str],
    ) -> float:
        """Score based on capability matching."""
        score = 0.5  # Base score
        
        if provider_spec:
            capabilities = provider_spec.capabilities
            
            # Check required capabilities
            if request.requires_streaming:
                if "streaming" in capabilities:
                    score += 0.15
                    reasoning.append("Provider supports required streaming")
                else:
                    score -= 0.2
                    warnings.append("Provider does not support required streaming")
            
            if request.requires_function_calling:
                if "function_calling" in capabilities:
                    score += 0.15
                    reasoning.append("Provider supports required function calling")
                else:
                    score -= 0.2
                    warnings.append("Provider does not support required function calling")
            
            if request.requires_vision:
                if "vision" in capabilities:
                    score += 0.15
                    reasoning.append("Provider supports required vision capabilities")
                else:
                    score -= 0.2
                    warnings.append("Provider does not support required vision capabilities")
        else:
            reasoning.append("Provider capabilities unknown")
        
        if runtime_spec:
            # Check runtime capabilities
            if request.requires_streaming and runtime_spec.supports_streaming:
                score += 0.1
                reasoning.append("Runtime supports streaming")
            elif request.requires_streaming and not runtime_spec.supports_streaming:
                score -= 0.1
                warnings.append("Runtime does not support streaming")
        else:
            reasoning.append("Runtime capabilities unknown")
        
        return max(min(score, 1.0), 0.0)
    
    def _score_performance_history(
        self,
        provider: str,
        runtime: str,
        reasoning: List[str],
    ) -> float:
        """Score based on historical performance."""
        component_key = f"{provider}:{runtime}"
        
        # Check success rate
        success_rate = self.success_rates.get(component_key, 0.8)  # Default to 80%
        
        # Check response times
        response_times = self.response_times.get(component_key, [])
        avg_response_time = sum(response_times) / len(response_times) if response_times else 2.0
        
        # Score based on success rate (0.6 weight)
        success_score = success_rate * 0.6
        
        # Score based on response time (0.4 weight)
        # Assume good response time is < 1s, poor is > 5s
        if avg_response_time < 1.0:
            time_score = 0.4
        elif avg_response_time < 3.0:
            time_score = 0.3
        elif avg_response_time < 5.0:
            time_score = 0.2
        else:
            time_score = 0.1
        
        total_score = success_score + time_score
        
        if response_times:
            reasoning.append(f"Historical performance: {success_rate:.1%} success, {avg_response_time:.1f}s avg response")
        else:
            reasoning.append("No historical performance data available")
        
        return total_score
    
    def _score_availability(
        self,
        provider: str,
        runtime: str,
        reasoning: List[str],
    ) -> float:
        """Score based on availability and uptime."""
        # This would be enhanced with actual uptime tracking
        # For now, use a simple heuristic based on provider type
        
        if provider in ["local", "huggingface"]:
            score = 0.9  # Local providers are highly available
            reasoning.append("Local provider has high availability")
        elif provider in ["openai", "gemini", "deepseek"]:
            score = 0.8  # Cloud providers have good but not perfect availability
            reasoning.append("Cloud provider has good availability")
        else:
            score = 0.7  # Unknown providers get moderate score
            reasoning.append("Provider availability unknown")
        
        # Runtime availability
        if runtime == "core_helpers":
            score = min(score + 0.1, 1.0)  # Core helpers are always available
            reasoning.append("Core helpers runtime is always available")
        
        return score
    
    def _score_cost_efficiency(
        self,
        provider: str,
        model_id: str,
        reasoning: List[str],
    ) -> float:
        """Score based on cost efficiency."""
        # Simple cost scoring based on provider type
        if provider in ["local", "huggingface", "core_helpers"]:
            score = 1.0  # Free
            reasoning.append("Provider is cost-free")
        elif provider == "deepseek":
            score = 0.9  # Very cheap
            reasoning.append("Provider is very cost-effective")
        elif provider == "gemini":
            score = 0.7  # Moderate cost
            reasoning.append("Provider has moderate cost")
        elif provider == "openai":
            if "gpt-4" in model_id:
                score = 0.4  # Expensive
                reasoning.append("Provider/model combination is expensive")
            else:
                score = 0.6  # Moderate cost
                reasoning.append("Provider/model combination has moderate cost")
        else:
            score = 0.5  # Unknown cost
            reasoning.append("Provider cost unknown")
        
        return score
    
    def _score_privacy_compliance(
        self,
        request: RoutingRequest,
        provider: str,
        runtime: str,
        policy: RoutingPolicy,
        reasoning: List[str],
    ) -> float:
        """Score based on privacy compliance."""
        allowed_providers = policy.privacy_provider_map.get(request.privacy_level, [])
        allowed_runtimes = policy.privacy_runtime_map.get(request.privacy_level, [])
        
        if provider in allowed_providers and runtime in allowed_runtimes:
            score = 1.0
            reasoning.append(f"Selection meets {request.privacy_level.value} privacy requirements")
        elif provider in allowed_providers:
            score = 0.7
            reasoning.append(f"Provider meets privacy requirements, runtime may not")
        elif runtime in allowed_runtimes:
            score = 0.7
            reasoning.append(f"Runtime meets privacy requirements, provider may not")
        else:
            score = 0.0
            reasoning.append(f"Selection does not meet {request.privacy_level.value} privacy requirements")
        
        return score
    
    def _score_user_preference(
        self,
        request: RoutingRequest,
        provider: str,
        runtime: str,
        model_id: str,
        reasoning: List[str],
    ) -> float:
        """Score based on user preferences."""
        score = 0.0
        
        if request.preferred_provider == provider:
            score += 0.4
            reasoning.append("Matches user's preferred provider")
        
        if request.preferred_runtime == runtime:
            score += 0.3
            reasoning.append("Matches user's preferred runtime")
        
        if request.preferred_model == model_id:
            score += 0.3
            reasoning.append("Matches user's preferred model")
        
        if score == 0.0:
            score = 0.5  # Neutral score when no preferences specified
            reasoning.append("No specific user preferences to match")
        
        return min(score, 1.0)
    
    def record_performance(
        self,
        provider: str,
        runtime: str,
        response_time: float,
        success: bool,
    ) -> None:
        """Record performance data for future scoring."""
        component_key = f"{provider}:{runtime}"
        
        # Record response time
        if component_key not in self.response_times:
            self.response_times[component_key] = []
        
        self.response_times[component_key].append(response_time)
        
        # Keep only last 100 response times
        if len(self.response_times[component_key]) > 100:
            self.response_times[component_key].pop(0)
        
        # Update success rate (exponential moving average)
        current_rate = self.success_rates.get(component_key, 0.8)
        new_rate = current_rate * 0.9 + (1.0 if success else 0.0) * 0.1
        self.success_rates[component_key] = new_rate
    
    def record_cost(self, provider: str, model_id: str, cost: float) -> None:
        """Record cost data for future scoring."""
        cost_key = f"{provider}:{model_id}"
        
        if cost_key not in self.cost_history:
            self.cost_history[cost_key] = []
        
        self.cost_history[cost_key].append(cost)
        
        # Keep only last 50 cost records
        if len(self.cost_history[cost_key]) > 50:
            self.cost_history[cost_key].pop(0)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all components."""
        stats = {}
        
        for component, times in self.response_times.items():
            if times:
                stats[component] = {
                    "avg_response_time": sum(times) / len(times),
                    "min_response_time": min(times),
                    "max_response_time": max(times),
                    "success_rate": self.success_rates.get(component, 0.0),
                    "sample_count": len(times),
                }
        
        return stats


# Global confidence scorer instance
_global_confidence_scorer: Optional[AdvancedConfidenceScorer] = None


def get_confidence_scorer() -> AdvancedConfidenceScorer:
    """Get the global confidence scorer instance."""
    global _global_confidence_scorer
    if _global_confidence_scorer is None:
        from ai_karen_engine.integrations.registry import get_registry
        from ai_karen_engine.integrations.health_monitor import get_health_monitor
        
        try:
            health_monitor = get_health_monitor()
        except Exception:
            health_monitor = None
        
        _global_confidence_scorer = AdvancedConfidenceScorer(
            registry=get_registry(),
            health_monitor=health_monitor,
        )
    
    return _global_confidence_scorer


__all__ = [
    "ConfidenceFactors",
    "ConfidenceMetadata",
    "AdvancedConfidenceScorer",
    "get_confidence_scorer",
]