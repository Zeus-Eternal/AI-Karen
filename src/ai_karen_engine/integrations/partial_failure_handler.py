"""
Partial Failure Handler for LLM Provider System

This module implements comprehensive partial failure handling to ensure provider isolation,
graceful degradation of features, and model-level fallbacks within providers.

Key Features:
- Provider isolation to prevent cascading failures
- Model-level fallbacks within providers when specific models are unavailable
- Capability-based routing that routes requests to providers with required features
- Graceful degradation of features (streaming → non-streaming, function calling → text-only)
- Intelligent failure recovery and retry mechanisms
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of failures that can occur in the provider system."""
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    MODEL_UNAVAILABLE = "model_unavailable"
    CAPABILITY_MISSING = "capability_missing"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    RESOURCE_ERROR = "resource_error"
    CONFIGURATION_ERROR = "configuration_error"


class CapabilityType(Enum):
    """Types of capabilities that providers can support."""
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    EMBEDDINGS = "embeddings"
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    MULTIMODAL = "multimodal"
    BATCH_PROCESSING = "batch_processing"


@dataclass
class FailureEvent:
    """Record of a failure event for analysis and recovery."""
    timestamp: datetime
    provider: str
    model: Optional[str]
    failure_type: FailureType
    error_message: str
    request_type: str
    recovery_attempted: bool = False
    recovery_successful: bool = False
    isolation_triggered: bool = False


@dataclass
class CapabilityRequirement:
    """Requirement for specific capabilities in a request."""
    required: Set[CapabilityType] = field(default_factory=set)
    preferred: Set[CapabilityType] = field(default_factory=set)
    fallback_acceptable: Set[CapabilityType] = field(default_factory=set)


@dataclass
class ModelFallbackChain:
    """Fallback chain for models within a provider."""
    provider: str
    primary_model: str
    fallback_models: List[str] = field(default_factory=list)
    last_successful_model: Optional[str] = None
    failure_counts: Dict[str, int] = field(default_factory=dict)


@dataclass
class ProviderIsolationStatus:
    """Isolation status for a provider to prevent cascading failures."""
    provider: str
    isolated: bool = False
    isolation_reason: Optional[str] = None
    isolation_timestamp: Optional[datetime] = None
    failure_count: int = 0
    last_failure: Optional[datetime] = None
    recovery_attempts: int = 0
    next_recovery_check: Optional[datetime] = None


@dataclass
class CapabilityFallbackResult:
    """Result of capability-based fallback."""
    success: bool
    original_capabilities: Set[CapabilityType]
    achieved_capabilities: Set[CapabilityType]
    degraded_capabilities: Set[CapabilityType]
    provider: Optional[str] = None
    model: Optional[str] = None
    fallback_reason: Optional[str] = None


class PartialFailureHandler:
    """
    Handles partial failures in the LLM provider system with intelligent isolation,
    capability-based routing, and graceful degradation.
    """
    
    def __init__(self, registry=None, max_failure_threshold: int = 5, 
                 isolation_duration: int = 300, recovery_check_interval: int = 60):
        """
        Initialize the partial failure handler.
        
        Args:
            registry: LLM registry instance
            max_failure_threshold: Maximum failures before isolating a provider
            isolation_duration: Duration in seconds to isolate a failed provider
            recovery_check_interval: Interval in seconds to check for recovery
        """
        from ai_karen_engine.integrations.registry import get_registry
        self.registry = registry or get_registry()
        self.max_failure_threshold = max_failure_threshold
        self.isolation_duration = isolation_duration
        self.recovery_check_interval = recovery_check_interval
        
        # Failure tracking
        self.failure_history: List[FailureEvent] = []
        self.provider_isolation: Dict[str, ProviderIsolationStatus] = {}
        self.model_fallback_chains: Dict[str, ModelFallbackChain] = {}
        
        # Capability mappings
        self.provider_capabilities: Dict[str, Set[CapabilityType]] = {}
        self.model_capabilities: Dict[str, Set[CapabilityType]] = {}
        
        # Performance tracking
        self.provider_performance: Dict[str, Dict[str, float]] = {}
        
        logger.info("Partial failure handler initialized")
    
    def record_failure(self, provider: str, model: Optional[str], failure_type: FailureType,
                      error_message: str, request_type: str) -> None:
        """
        Record a failure event and update isolation status if necessary.
        
        Args:
            provider: Name of the failed provider
            model: Name of the failed model (if applicable)
            failure_type: Type of failure that occurred
            error_message: Detailed error message
            request_type: Type of request that failed
        """
        failure_event = FailureEvent(
            timestamp=datetime.now(),
            provider=provider,
            model=model,
            failure_type=failure_type,
            error_message=error_message,
            request_type=request_type
        )
        
        self.failure_history.append(failure_event)
        logger.warning(f"Recorded failure for {provider}/{model}: {failure_type.value} - {error_message}")
        
        # Update provider isolation status
        self._update_provider_isolation(provider, failure_event)
        
        # Update model fallback chains
        if model:
            self._update_model_fallback_chain(provider, model, failure_type)
        
        # Clean up old failure history (keep last 1000 events)
        if len(self.failure_history) > 1000:
            self.failure_history = self.failure_history[-1000:]
    
    def is_provider_isolated(self, provider: str) -> bool:
        """
        Check if a provider is currently isolated due to failures.
        
        Args:
            provider: Name of the provider to check
            
        Returns:
            True if the provider is isolated, False otherwise
        """
        if provider not in self.provider_isolation:
            return False
        
        isolation_status = self.provider_isolation[provider]
        if not isolation_status.isolated:
            return False
        
        # Check if isolation period has expired
        if isolation_status.isolation_timestamp:
            isolation_end = isolation_status.isolation_timestamp + timedelta(seconds=self.isolation_duration)
            if datetime.now() > isolation_end:
                # Isolation period expired, check for recovery
                self._check_provider_recovery(provider)
                return self.provider_isolation[provider].isolated
        
        return True
    
    def get_available_providers(self, capability_requirements: Optional[CapabilityRequirement] = None,
                              exclude_isolated: bool = True) -> List[str]:
        """
        Get list of available providers, optionally filtered by capabilities and isolation status.
        
        Args:
            capability_requirements: Required capabilities for the providers
            exclude_isolated: Whether to exclude isolated providers
            
        Returns:
            List of available provider names
        """
        providers = self.registry.list_providers(healthy_only=True)
        available_providers = []
        
        for provider in providers:
            # Skip isolated providers if requested
            if exclude_isolated and self.is_provider_isolated(provider):
                logger.debug(f"Skipping isolated provider: {provider}")
                continue
            
            # Check capability requirements
            if capability_requirements and capability_requirements.required:
                provider_caps = self._get_provider_capabilities(provider)
                if not capability_requirements.required.issubset(provider_caps):
                    logger.debug(f"Provider {provider} missing required capabilities: "
                               f"{capability_requirements.required - provider_caps}")
                    continue
            
            available_providers.append(provider)
        
        return available_providers
    
    def get_model_fallback_chain(self, provider: str, primary_model: str) -> List[str]:
        """
        Get the fallback chain for a specific model within a provider.
        
        Args:
            provider: Name of the provider
            primary_model: Primary model to get fallbacks for
            
        Returns:
            List of model names in fallback order
        """
        chain_key = f"{provider}:{primary_model}"
        
        if chain_key not in self.model_fallback_chains:
            # Create default fallback chain based on provider models
            self._create_default_fallback_chain(provider, primary_model)
        
        fallback_chain = self.model_fallback_chains[chain_key]
        
        # Filter out models that have failed too many times recently
        viable_models = [primary_model]
        current_time = datetime.now()
        
        for model in fallback_chain.fallback_models:
            failure_count = fallback_chain.failure_counts.get(model, 0)
            if failure_count < self.max_failure_threshold:
                viable_models.append(model)
            else:
                logger.debug(f"Skipping model {model} due to high failure count: {failure_count}")
        
        return viable_models
    
    def attempt_capability_fallback(self, original_requirements: CapabilityRequirement,
                                  failed_provider: Optional[str] = None) -> CapabilityFallbackResult:
        """
        Attempt to find alternative providers/models with degraded capabilities.
        
        Args:
            original_requirements: Original capability requirements
            failed_provider: Provider that failed (to exclude from fallback)
            
        Returns:
            CapabilityFallbackResult with fallback information
        """
        logger.info(f"Attempting capability fallback for requirements: {original_requirements.required}")
        
        # Try to find providers with all required capabilities first
        available_providers = self.get_available_providers(original_requirements, exclude_isolated=True)
        if failed_provider and failed_provider in available_providers:
            available_providers.remove(failed_provider)
        
        if available_providers:
            # Found providers with full capabilities
            best_provider = self._select_best_provider(available_providers, original_requirements)
            return CapabilityFallbackResult(
                success=True,
                original_capabilities=original_requirements.required,
                achieved_capabilities=original_requirements.required,
                degraded_capabilities=set(),
                provider=best_provider,
                fallback_reason="Found provider with full capabilities"
            )
        
        # Try graceful degradation of capabilities
        degradation_strategies = [
            # Strategy 1: Remove streaming requirement
            (CapabilityType.STREAMING, "Fallback to non-streaming response"),
            # Strategy 2: Remove function calling requirement
            (CapabilityType.FUNCTION_CALLING, "Fallback to text-only response"),
            # Strategy 3: Remove vision requirement
            (CapabilityType.VISION, "Fallback to text-only processing"),
            # Strategy 4: Remove multimodal requirement
            (CapabilityType.MULTIMODAL, "Fallback to single-modal processing"),
        ]
        
        for capability_to_remove, reason in degradation_strategies:
            if capability_to_remove in original_requirements.required:
                degraded_requirements = CapabilityRequirement(
                    required=original_requirements.required - {capability_to_remove},
                    preferred=original_requirements.preferred,
                    fallback_acceptable=original_requirements.fallback_acceptable | {capability_to_remove}
                )
                
                available_providers = self.get_available_providers(degraded_requirements, exclude_isolated=True)
                if failed_provider and failed_provider in available_providers:
                    available_providers.remove(failed_provider)
                
                if available_providers:
                    best_provider = self._select_best_provider(available_providers, degraded_requirements)
                    logger.info(f"Capability fallback successful: {reason}")
                    return CapabilityFallbackResult(
                        success=True,
                        original_capabilities=original_requirements.required,
                        achieved_capabilities=degraded_requirements.required,
                        degraded_capabilities={capability_to_remove},
                        provider=best_provider,
                        fallback_reason=reason
                    )
        
        # No viable fallback found
        logger.warning("No viable capability fallback found")
        return CapabilityFallbackResult(
            success=False,
            original_capabilities=original_requirements.required,
            achieved_capabilities=set(),
            degraded_capabilities=original_requirements.required,
            fallback_reason="No providers available with required or degraded capabilities"
        )
    
    def isolate_provider(self, provider: str, reason: str) -> None:
        """
        Manually isolate a provider to prevent further requests.
        
        Args:
            provider: Name of the provider to isolate
            reason: Reason for isolation
        """
        if provider not in self.provider_isolation:
            self.provider_isolation[provider] = ProviderIsolationStatus(provider=provider)
        
        isolation_status = self.provider_isolation[provider]
        isolation_status.isolated = True
        isolation_status.isolation_reason = reason
        isolation_status.isolation_timestamp = datetime.now()
        isolation_status.next_recovery_check = datetime.now() + timedelta(seconds=self.recovery_check_interval)
        
        logger.warning(f"Provider {provider} isolated: {reason}")
    
    def recover_provider(self, provider: str) -> bool:
        """
        Attempt to recover an isolated provider.
        
        Args:
            provider: Name of the provider to recover
            
        Returns:
            True if recovery was successful, False otherwise
        """
        if provider not in self.provider_isolation:
            return True  # Provider was never isolated
        
        isolation_status = self.provider_isolation[provider]
        if not isolation_status.isolated:
            return True  # Provider is not isolated
        
        logger.info(f"Attempting to recover provider: {provider}")
        
        # Check provider health
        try:
            health_status = self.registry.get_health_status(f"provider:{provider}")
            if health_status and health_status.status == "healthy":
                # Provider is healthy, remove isolation
                isolation_status.isolated = False
                isolation_status.isolation_reason = None
                isolation_status.isolation_timestamp = None
                isolation_status.recovery_attempts += 1
                
                logger.info(f"Provider {provider} successfully recovered")
                return True
            else:
                logger.debug(f"Provider {provider} still unhealthy, keeping isolated")
                isolation_status.recovery_attempts += 1
                isolation_status.next_recovery_check = datetime.now() + timedelta(seconds=self.recovery_check_interval)
                return False
        except Exception as e:
            logger.error(f"Error checking provider {provider} health during recovery: {e}")
            isolation_status.recovery_attempts += 1
            isolation_status.next_recovery_check = datetime.now() + timedelta(seconds=self.recovery_check_interval)
            return False
    
    def get_failure_statistics(self, provider: Optional[str] = None, 
                             time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get failure statistics for analysis.
        
        Args:
            provider: Specific provider to get stats for (None for all)
            time_window: Time window to analyze (None for all time)
            
        Returns:
            Dictionary with failure statistics
        """
        current_time = datetime.now()
        cutoff_time = current_time - time_window if time_window else datetime.min
        
        # Filter failures by time window and provider
        relevant_failures = [
            f for f in self.failure_history
            if f.timestamp >= cutoff_time and (provider is None or f.provider == provider)
        ]
        
        if not relevant_failures:
            return {"total_failures": 0, "failure_types": {}, "providers": {}, "models": {}}
        
        # Analyze failure types
        failure_types = {}
        for failure in relevant_failures:
            failure_type = failure.failure_type.value
            failure_types[failure_type] = failure_types.get(failure_type, 0) + 1
        
        # Analyze by provider
        provider_stats = {}
        for failure in relevant_failures:
            prov = failure.provider
            if prov not in provider_stats:
                provider_stats[prov] = {"count": 0, "failure_types": {}}
            provider_stats[prov]["count"] += 1
            ft = failure.failure_type.value
            provider_stats[prov]["failure_types"][ft] = provider_stats[prov]["failure_types"].get(ft, 0) + 1
        
        # Analyze by model
        model_stats = {}
        for failure in relevant_failures:
            if failure.model:
                model_key = f"{failure.provider}:{failure.model}"
                model_stats[model_key] = model_stats.get(model_key, 0) + 1
        
        return {
            "total_failures": len(relevant_failures),
            "failure_types": failure_types,
            "providers": provider_stats,
            "models": model_stats,
            "time_window": str(time_window) if time_window else "all_time",
            "isolated_providers": [p for p, status in self.provider_isolation.items() if status.isolated]
        }
    
    def _update_provider_isolation(self, provider: str, failure_event: FailureEvent) -> None:
        """Update provider isolation status based on failure event."""
        if provider not in self.provider_isolation:
            self.provider_isolation[provider] = ProviderIsolationStatus(provider=provider)
        
        isolation_status = self.provider_isolation[provider]
        isolation_status.failure_count += 1
        isolation_status.last_failure = failure_event.timestamp
        
        # Check if provider should be isolated
        if (isolation_status.failure_count >= self.max_failure_threshold and 
            not isolation_status.isolated):
            
            # Check if failures are recent (within last 5 minutes)
            recent_failures = [
                f for f in self.failure_history[-20:]  # Check last 20 failures
                if (f.provider == provider and 
                    f.timestamp >= datetime.now() - timedelta(minutes=5))
            ]
            
            if len(recent_failures) >= self.max_failure_threshold:
                self.isolate_provider(provider, f"Too many recent failures: {len(recent_failures)}")
                failure_event.isolation_triggered = True
    
    def _update_model_fallback_chain(self, provider: str, model: str, failure_type: FailureType) -> None:
        """Update model fallback chain based on failure."""
        chain_key = f"{provider}:{model}"
        
        if chain_key not in self.model_fallback_chains:
            self._create_default_fallback_chain(provider, model)
        
        fallback_chain = self.model_fallback_chains[chain_key]
        fallback_chain.failure_counts[model] = fallback_chain.failure_counts.get(model, 0) + 1
        
        # If this was the last successful model, clear it
        if fallback_chain.last_successful_model == model:
            fallback_chain.last_successful_model = None
    
    def _create_default_fallback_chain(self, provider: str, primary_model: str) -> None:
        """Create a default fallback chain for a model."""
        chain_key = f"{provider}:{primary_model}"
        
        # Get available models from the provider
        try:
            provider_models = self.registry.list_models(provider=provider)
            fallback_models = [m.id for m in provider_models if m.id != primary_model]
            
            # Sort by preference (smaller models first for fallback)
            fallback_models.sort(key=lambda m: self._get_model_priority(m))
            
        except Exception as e:
            logger.warning(f"Could not get models for provider {provider}: {e}")
            fallback_models = []
        
        self.model_fallback_chains[chain_key] = ModelFallbackChain(
            provider=provider,
            primary_model=primary_model,
            fallback_models=fallback_models
        )
        
        logger.debug(f"Created fallback chain for {chain_key}: {fallback_models}")
    
    def _get_provider_capabilities(self, provider: str) -> Set[CapabilityType]:
        """Get capabilities for a provider."""
        if provider in self.provider_capabilities:
            return self.provider_capabilities[provider]
        
        # Query provider capabilities from registry
        try:
            provider_spec = self.registry.get_provider_spec(provider)
            if provider_spec and provider_spec.capabilities:
                # Map string capabilities to CapabilityType enum
                capabilities = set()
                for cap in provider_spec.capabilities:
                    try:
                        capabilities.add(CapabilityType(cap))
                    except ValueError:
                        logger.debug(f"Unknown capability type: {cap}")
                
                self.provider_capabilities[provider] = capabilities
                return capabilities
        except Exception as e:
            logger.warning(f"Could not get capabilities for provider {provider}: {e}")
        
        # Default capabilities if none specified
        default_caps = {CapabilityType.STREAMING}
        self.provider_capabilities[provider] = default_caps
        return default_caps
    
    def _select_best_provider(self, providers: List[str], requirements: CapabilityRequirement) -> str:
        """Select the best provider from available options."""
        if not providers:
            raise ValueError("No providers available for selection")
        
        if len(providers) == 1:
            return providers[0]
        
        # Score providers based on various factors
        provider_scores = {}
        
        for provider in providers:
            score = 0.0
            
            # Health score (higher is better)
            try:
                health = self.registry.get_health_status(f"provider:{provider}")
                if health and health.status == "healthy":
                    score += 10.0
                elif health and health.status == "degraded":
                    score += 5.0
            except Exception:
                pass
            
            # Capability match score
            provider_caps = self._get_provider_capabilities(provider)
            required_match = len(requirements.required.intersection(provider_caps))
            preferred_match = len(requirements.preferred.intersection(provider_caps))
            score += required_match * 5.0 + preferred_match * 2.0
            
            # Failure history penalty
            isolation_status = self.provider_isolation.get(provider)
            if isolation_status:
                score -= isolation_status.failure_count * 0.5
            
            # Performance bonus (if available)
            if provider in self.provider_performance:
                avg_response_time = self.provider_performance[provider].get("avg_response_time", 1.0)
                score += max(0, 5.0 - avg_response_time)  # Bonus for faster response times
            
            provider_scores[provider] = score
        
        # Return provider with highest score
        best_provider = max(provider_scores.items(), key=lambda x: x[1])[0]
        logger.debug(f"Selected best provider {best_provider} with score {provider_scores[best_provider]}")
        return best_provider
    
    def _get_model_priority(self, model_id: str) -> int:
        """Get priority for model ordering (lower number = higher priority)."""
        # Prefer smaller, faster models for fallback
        if "7b" in model_id.lower() or "small" in model_id.lower():
            return 1
        elif "13b" in model_id.lower() or "medium" in model_id.lower():
            return 2
        elif "70b" in model_id.lower() or "large" in model_id.lower():
            return 3
        else:
            return 4
    
    def _check_provider_recovery(self, provider: str) -> None:
        """Check if an isolated provider has recovered."""
        if provider not in self.provider_isolation:
            return
        
        isolation_status = self.provider_isolation[provider]
        current_time = datetime.now()
        
        # Check if it's time for a recovery check
        if (isolation_status.next_recovery_check and 
            current_time >= isolation_status.next_recovery_check):
            self.recover_provider(provider)


# Global instance
_partial_failure_handler = None


def get_partial_failure_handler(registry=None) -> PartialFailureHandler:
    """Get the global partial failure handler instance."""
    global _partial_failure_handler
    if _partial_failure_handler is None:
        _partial_failure_handler = PartialFailureHandler(registry=registry)
    return _partial_failure_handler