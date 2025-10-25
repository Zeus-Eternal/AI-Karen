"""
Fallback Manager for Intelligent LLM Routing

This module implements intelligent fallback handling with local provider prioritization,
degraded mode activation, and recovery monitoring for the LLM routing system.

Key Features:
- Intelligent fallback chain construction based on provider health and capabilities
- Local provider prioritization when cloud providers fail
- Degraded mode activation with core helpers (TinyLLaMA, DistilBERT, spaCy)
- Recovery monitoring and automatic switching back to preferred providers
- Comprehensive logging and failure pattern analysis
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from ai_karen_engine.integrations.registry import get_registry, ModelMetadata
from ai_karen_engine.integrations.llm_router import RoutingRequest, RouteDecision, PrivacyLevel, TaskType
from ai_karen_engine.core.degraded_mode import get_degraded_mode_manager, DegradedModeReason


class FallbackReason(Enum):
    """Reasons for fallback activation."""
    PROVIDER_UNHEALTHY = "provider_unhealthy"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    AUTHENTICATION_FAILED = "authentication_failed"
    RATE_LIMITED = "rate_limited"
    NETWORK_ERROR = "network_error"
    MODEL_UNAVAILABLE = "model_unavailable"
    CAPABILITY_MISSING = "capability_missing"
    PRIVACY_VIOLATION = "privacy_violation"
    TIMEOUT = "timeout"
    UNKNOWN_ERROR = "unknown_error"


class FallbackStrategy(Enum):
    """Fallback strategies for different scenarios."""
    CLOUD_TO_LOCAL = "cloud_to_local"
    LOCAL_TO_DEGRADED = "local_to_degraded"
    CAPABILITY_DOWNGRADE = "capability_downgrade"
    MODEL_DOWNGRADE = "model_downgrade"
    RUNTIME_SWITCH = "runtime_switch"
    EMERGENCY_DEGRADED = "emergency_degraded"


@dataclass
class FallbackEvent:
    """Record of a fallback event."""
    timestamp: datetime
    original_provider: str
    fallback_provider: str
    original_model: Optional[str]
    fallback_model: Optional[str]
    reason: FallbackReason
    strategy: FallbackStrategy
    success: bool
    request_type: str
    recovery_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FallbackAttempt:
    """Record of a single fallback attempt."""
    provider: str
    runtime: str
    model: str
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    latency: Optional[float] = None
    confidence: Optional[float] = None


@dataclass
class FallbackResult:
    """Result of fallback execution."""
    success: bool
    used_provider: Optional[str]
    used_runtime: Optional[str]
    used_model: Optional[str]
    attempts: List[FallbackAttempt]
    final_error: Optional[str]
    degraded_mode_activated: bool
    total_time: float
    strategy_used: Optional[FallbackStrategy] = None
    recovery_suggestions: List[str] = field(default_factory=list)


@dataclass
class RecoveryStatus:
    """Status of provider recovery monitoring."""
    recovered_providers: List[str]
    still_failing_providers: List[str]
    recovery_recommendations: List[str]
    next_check_time: datetime
    monitoring_active: bool


class FallbackManager:
    """
    Intelligent fallback manager for LLM routing.
    
    This manager handles fallback scenarios when primary providers fail,
    implements intelligent fallback chain construction, and monitors
    provider recovery to automatically switch back to preferred providers.
    """
    
    def __init__(self, registry=None, router=None):
        self.registry = registry or get_registry()
        self.router = router  # Will be set by router
        self.logger = logging.getLogger("kari.fallback_manager")
        self.degraded_mode_manager = get_degraded_mode_manager()
        
        # Fallback history and statistics
        self.fallback_history: List[FallbackEvent] = []
        self.recovery_monitoring_active = False
        self.recovery_check_interval = 300  # 5 minutes
        self.last_recovery_check = datetime.now()
        
        # Provider failure tracking
        self.provider_failure_counts: Dict[str, int] = {}
        self.provider_last_failure: Dict[str, datetime] = {}
        self.provider_recovery_attempts: Dict[str, int] = {}
        
        # Configuration
        self.max_fallback_attempts = 5
        self.recovery_threshold_minutes = 10
        self.failure_threshold_count = 3
        
        self.logger.info("Fallback manager initialized")
    
    def construct_fallback_chain(self, request: RoutingRequest, failed_providers: List[str]) -> List[str]:
        """
        Construct intelligent fallback chain based on request and failures.
        
        Args:
            request: The routing request with requirements
            failed_providers: List of providers that have already failed
            
        Returns:
            Ordered list of provider names to try as fallbacks
        """
        fallback_chain = []
        
        self.logger.debug(f"Constructing fallback chain for {request.task_type.value} task, failed: {failed_providers}")
        
        # Strategy 1: Cloud to local fallback
        if self._should_use_cloud_to_local_strategy(request, failed_providers):
            local_providers = self._get_local_providers(request, failed_providers)
            fallback_chain.extend(local_providers)
            self.logger.debug(f"Added local providers to fallback chain: {local_providers}")
        
        # Strategy 2: Capability-based fallback
        capability_providers = self._get_capability_compatible_providers(request, failed_providers + fallback_chain)
        fallback_chain.extend(capability_providers)
        self.logger.debug(f"Added capability-compatible providers: {capability_providers}")
        
        # Strategy 3: Privacy-compliant alternatives
        privacy_providers = self._get_privacy_compliant_providers(request, failed_providers + fallback_chain)
        fallback_chain.extend(privacy_providers)
        self.logger.debug(f"Added privacy-compliant providers: {privacy_providers}")
        
        # Strategy 4: Emergency fallbacks (any healthy provider)
        if not fallback_chain:
            emergency_providers = self._get_emergency_fallback_providers(request, failed_providers)
            fallback_chain.extend(emergency_providers)
            self.logger.debug(f"Added emergency fallback providers: {emergency_providers}")
        
        # Remove duplicates while preserving order
        unique_chain = []
        for provider in fallback_chain:
            if provider not in unique_chain:
                unique_chain.append(provider)
        
        self.logger.info(f"Constructed fallback chain: {unique_chain}")
        return unique_chain
    
    def execute_fallback(self, request: RoutingRequest, fallback_chain: List[str]) -> FallbackResult:
        """
        Execute fallback chain until successful or exhausted.
        
        Args:
            request: The routing request
            fallback_chain: Ordered list of providers to try
            
        Returns:
            FallbackResult with execution details
        """
        start_time = time.time()
        attempts = []
        
        self.logger.info(f"Executing fallback chain: {fallback_chain}")
        
        for i, provider in enumerate(fallback_chain):
            if i >= self.max_fallback_attempts:
                self.logger.warning(f"Reached maximum fallback attempts ({self.max_fallback_attempts})")
                break
            
            attempt_start = time.time()
            attempt = FallbackAttempt(
                provider=provider,
                runtime="",  # Will be filled in
                model="",    # Will be filled in
                timestamp=datetime.now(),
                success=False
            )
            
            try:
                self.logger.debug(f"Attempting fallback to provider: {provider}")
                
                # Check provider health
                if not self._is_provider_healthy(provider):
                    attempt.error_message = "Provider unhealthy"
                    self.logger.debug(f"Provider {provider} is unhealthy, skipping")
                    attempts.append(attempt)
                    continue
                
                # Check privacy compliance
                if not self._check_privacy_compliance(request, provider):
                    attempt.error_message = "Privacy compliance failed"
                    self.logger.debug(f"Provider {provider} fails privacy compliance")
                    attempts.append(attempt)
                    continue
                
                # Try to create a route decision for this provider
                decision = self._create_fallback_decision(request, provider)
                if decision:
                    attempt.runtime = decision["runtime"]
                    attempt.model = decision["model_id"]
                    attempt.success = True
                    attempt.latency = time.time() - attempt_start
                    attempt.confidence = decision["confidence"]
                    attempts.append(attempt)
                    
                    # Record successful fallback event
                    self._record_fallback_event(
                        original_provider=request.preferred_provider or "unknown",
                        fallback_provider=provider,
                        original_model=request.preferred_model,
                        fallback_model=decision["model_id"],
                        reason=FallbackReason.PROVIDER_UNAVAILABLE,
                        strategy=self._determine_strategy(request, provider),
                        success=True,
                        request_type=request.task_type.value
                    )
                    
                    total_time = time.time() - start_time
                    self.logger.info(f"Fallback successful to {provider}/{decision['model_id']} in {total_time:.2f}s")
                    
                    return FallbackResult(
                        success=True,
                        used_provider=provider,
                        used_runtime=decision["runtime"],
                        used_model=decision["model_id"],
                        attempts=attempts,
                        final_error=None,
                        degraded_mode_activated=False,
                        total_time=total_time,
                        strategy_used=self._determine_strategy(request, provider)
                    )
                else:
                    attempt.error_message = "Could not create viable route decision"
                    
            except Exception as e:
                attempt.error_message = str(e)
                self.logger.warning(f"Fallback attempt to {provider} failed: {e}")
            
            attempts.append(attempt)
        
        # All fallback attempts failed - try degraded mode
        degraded_result = self._try_degraded_mode_fallback(request, attempts)
        if degraded_result:
            return degraded_result
        
        # Complete failure
        total_time = time.time() - start_time
        self.logger.error(f"All fallback attempts failed in {total_time:.2f}s")
        
        return FallbackResult(
            success=False,
            used_provider=None,
            used_runtime=None,
            used_model=None,
            attempts=attempts,
            final_error="All fallback providers failed",
            degraded_mode_activated=False,
            total_time=total_time,
            recovery_suggestions=self._generate_recovery_suggestions(attempts)
        )
    
    def activate_degraded_mode(self, request: RoutingRequest) -> Optional[RouteDecision]:
        """
        Activate degraded mode with core helpers.
        
        Args:
            request: The routing request
            
        Returns:
            RouteDecision for degraded mode or None if unavailable
        """
        self.logger.warning("Activating degraded mode with core helpers")
        
        if not self.degraded_mode_manager:
            self.logger.error("Degraded mode manager not available")
            return None
        
        try:
            # Activate degraded mode
            degraded_status = self.degraded_mode_manager.activate_degraded_mode(
                reason=DegradedModeReason.ALL_PROVIDERS_FAILED,
                context={
                    "task_type": request.task_type.value,
                    "privacy_level": request.privacy_level.value,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            if not degraded_status.is_active:
                self.logger.error("Failed to activate degraded mode")
                return None
            
            # Create degraded mode decision
            decision = RouteDecision(
                provider="core_helpers",
                runtime="core_helpers",
                model_id="tinyllama+distilbert+spacy",
                reason="Degraded mode activated - all providers failed",
                confidence=0.3,  # Low confidence for degraded mode
                fallback_chain=[],
                estimated_cost=0.0,  # Core helpers are free
                estimated_latency=0.5,  # Fast but limited
                privacy_compliant=True,  # Core helpers are always privacy compliant
                capabilities=["basic_text", "simple_analysis"]
            )
            
            # Record degraded mode activation
            self._record_fallback_event(
                original_provider="unknown",
                fallback_provider="core_helpers",
                original_model=None,
                fallback_model="tinyllama+distilbert+spacy",
                reason=FallbackReason.PROVIDER_UNAVAILABLE,
                strategy=FallbackStrategy.EMERGENCY_DEGRADED,
                success=True,
                request_type=request.task_type.value
            )
            
            self.logger.info("Degraded mode activated successfully")
            return decision
            
        except Exception as e:
            self.logger.error(f"Failed to activate degraded mode: {e}")
            return None
    
    def monitor_recovery(self) -> RecoveryStatus:
        """
        Monitor provider recovery and suggest switching back.
        
        Returns:
            RecoveryStatus with recovery information
        """
        now = datetime.now()
        
        # Check if it's time for recovery monitoring
        if (now - self.last_recovery_check).total_seconds() < self.recovery_check_interval:
            return RecoveryStatus(
                recovered_providers=[],
                still_failing_providers=[],
                recovery_recommendations=[],
                next_check_time=self.last_recovery_check + timedelta(seconds=self.recovery_check_interval),
                monitoring_active=self.recovery_monitoring_active
            )
        
        self.last_recovery_check = now
        recovered_providers = []
        still_failing_providers = []
        recovery_recommendations = []
        
        self.logger.debug("Checking provider recovery status")
        
        # Check each provider that has failed recently
        for provider, last_failure in self.provider_last_failure.items():
            # Only check providers that failed within the recovery threshold
            if (now - last_failure).total_seconds() < (self.recovery_threshold_minutes * 60):
                continue
            
            try:
                # Test provider health
                if self._is_provider_healthy(provider):
                    recovered_providers.append(provider)
                    self.logger.info(f"Provider {provider} has recovered")
                    
                    # Reset failure tracking
                    self.provider_failure_counts.pop(provider, None)
                    self.provider_last_failure.pop(provider, None)
                    self.provider_recovery_attempts.pop(provider, None)
                    
                    recovery_recommendations.append(
                        f"Provider {provider} is now healthy and can be used again"
                    )
                else:
                    still_failing_providers.append(provider)
                    self.provider_recovery_attempts[provider] = self.provider_recovery_attempts.get(provider, 0) + 1
                    
                    if self.provider_recovery_attempts[provider] > 5:
                        recovery_recommendations.append(
                            f"Provider {provider} has failed recovery {self.provider_recovery_attempts[provider]} times - consider manual intervention"
                        )
                    
            except Exception as e:
                self.logger.warning(f"Error checking recovery for provider {provider}: {e}")
                still_failing_providers.append(provider)
        
        return RecoveryStatus(
            recovered_providers=recovered_providers,
            still_failing_providers=still_failing_providers,
            recovery_recommendations=recovery_recommendations,
            next_check_time=now + timedelta(seconds=self.recovery_check_interval),
            monitoring_active=self.recovery_monitoring_active
        )
    
    def start_recovery_monitoring(self) -> None:
        """Start automatic recovery monitoring."""
        self.recovery_monitoring_active = True
        self.logger.info("Recovery monitoring started")
    
    def stop_recovery_monitoring(self) -> None:
        """Stop automatic recovery monitoring."""
        self.recovery_monitoring_active = False
        self.logger.info("Recovery monitoring stopped")
    
    def get_fallback_statistics(self) -> Dict[str, Any]:
        """Get comprehensive fallback statistics."""
        now = datetime.now()
        recent_events = [
            event for event in self.fallback_history
            if (now - event.timestamp).total_seconds() < 3600  # Last hour
        ]
        
        return {
            "total_fallback_events": len(self.fallback_history),
            "recent_fallback_events": len(recent_events),
            "provider_failure_counts": self.provider_failure_counts.copy(),
            "provider_recovery_attempts": self.provider_recovery_attempts.copy(),
            "most_common_failure_reasons": self._get_most_common_failure_reasons(),
            "most_used_fallback_providers": self._get_most_used_fallback_providers(),
            "average_fallback_success_rate": self._calculate_fallback_success_rate(),
            "recovery_monitoring_active": self.recovery_monitoring_active,
            "last_recovery_check": self.last_recovery_check.isoformat(),
        }
    
    def clear_fallback_history(self, older_than_hours: int = 24) -> int:
        """Clear old fallback history entries."""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        original_count = len(self.fallback_history)
        
        self.fallback_history = [
            event for event in self.fallback_history
            if event.timestamp > cutoff_time
        ]
        
        cleared_count = original_count - len(self.fallback_history)
        self.logger.info(f"Cleared {cleared_count} fallback history entries older than {older_than_hours} hours")
        return cleared_count
    
    # Private helper methods
    
    def _should_use_cloud_to_local_strategy(self, request: RoutingRequest, failed_providers: List[str]) -> bool:
        """Determine if cloud-to-local fallback strategy should be used."""
        # Use cloud-to-local if privacy allows and cloud providers have failed
        if request.privacy_level in [PrivacyLevel.CONFIDENTIAL, PrivacyLevel.RESTRICTED]:
            return False  # Already restricted to local
        
        cloud_providers = ["openai", "gemini", "deepseek"]
        failed_cloud_providers = [p for p in failed_providers if p in cloud_providers]
        
        return len(failed_cloud_providers) > 0
    
    def _get_local_providers(self, request: RoutingRequest, exclude: List[str]) -> List[str]:
        """Get local providers that meet privacy requirements."""
        local_providers = ["local", "huggingface"]
        viable_locals = []
        
        for provider in local_providers:
            if (provider not in exclude and 
                self._is_provider_healthy(provider) and
                self._check_privacy_compliance(request, provider)):
                viable_locals.append(provider)
        
        return viable_locals
    
    def _get_capability_compatible_providers(self, request: RoutingRequest, exclude: List[str]) -> List[str]:
        """Get providers that support required capabilities."""
        compatible_providers = []
        all_providers = self.registry.list_providers(healthy_only=True)
        
        for provider in all_providers:
            if provider in exclude:
                continue
            
            provider_spec = self.registry.get_provider_spec(provider)
            if not provider_spec:
                continue
            
            # Check capability requirements
            if request.requires_streaming and "streaming" not in provider_spec.capabilities:
                continue
            if request.requires_function_calling and "function_calling" not in provider_spec.capabilities:
                continue
            if request.requires_vision and "vision" not in provider_spec.capabilities:
                continue
            
            if self._check_privacy_compliance(request, provider):
                compatible_providers.append(provider)
        
        return compatible_providers
    
    def _get_privacy_compliant_providers(self, request: RoutingRequest, exclude: List[str]) -> List[str]:
        """Get providers that meet privacy requirements."""
        compliant_providers = []
        all_providers = self.registry.list_providers(healthy_only=True)
        
        for provider in all_providers:
            if (provider not in exclude and 
                self._check_privacy_compliance(request, provider)):
                compliant_providers.append(provider)
        
        return compliant_providers
    
    def _get_emergency_fallback_providers(self, request: RoutingRequest, exclude: List[str]) -> List[str]:
        """Get any healthy providers as emergency fallbacks."""
        emergency_providers = []
        all_providers = self.registry.list_providers(healthy_only=True)
        
        for provider in all_providers:
            if provider not in exclude:
                emergency_providers.append(provider)
        
        return emergency_providers
    
    def _is_provider_healthy(self, provider: str) -> bool:
        """Check if a provider is healthy."""
        health = self.registry.get_health_status(f"provider:{provider}")
        return health is None or health.status in ["healthy", "unknown"]
    
    def _check_privacy_compliance(self, request: RoutingRequest, provider: str) -> bool:
        """Check if provider meets privacy requirements."""
        if not self.router:
            return True  # Default to allowing if no router available
        
        return self.router._check_privacy_compliance(request, provider, None)
    
    def _create_fallback_decision(self, request: RoutingRequest, provider: str) -> Optional[RouteDecision]:
        """Create a route decision for fallback provider."""
        try:
            provider_spec = self.registry.get_provider_spec(provider)
            if not provider_spec:
                return None
            
            # Select model for provider
            model_id = self._select_model_for_provider(provider, request)
            if not model_id:
                return None
            
            # Find compatible runtime
            model_meta = ModelMetadata(id=model_id, name=model_id, provider=provider)
            compatible_runtimes = self.registry.compatible_runtimes(model_meta)
            
            viable_runtime = None
            for runtime in compatible_runtimes:
                if self._is_runtime_healthy(runtime):
                    viable_runtime = runtime
                    break
            
            if not viable_runtime:
                return None
            
            return RouteDecision(
                provider=provider,
                runtime=viable_runtime,
                model_id=model_id,
                reason=f"Fallback to {provider}",
                confidence=0.6,  # Medium confidence for fallback
                fallback_chain=[],
                estimated_cost=self._estimate_cost(provider, model_id),
                estimated_latency=self._estimate_latency(provider, viable_runtime),
                privacy_compliant=self._check_privacy_compliance(request, provider),
                capabilities=list(provider_spec.capabilities)
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to create fallback decision for {provider}: {e}")
            return None
    
    def _select_model_for_provider(self, provider: str, request: RoutingRequest) -> Optional[str]:
        """Select appropriate model for provider."""
        # Simplified model selection - would be enhanced with actual model discovery
        if provider == "openai":
            if request.requires_vision:
                return "gpt-4o"
            elif request.task_type == TaskType.CODE:
                return "gpt-4o-mini"
            else:
                return "gpt-4o-mini"
        elif provider == "gemini":
            return "gemini-1.5-flash"
        elif provider == "deepseek":
            return "deepseek-chat"
        elif provider == "local":
            return "llama3.2:latest"
        elif provider == "huggingface":
            return "microsoft/DialoGPT-medium"
        else:
            return "default-model"
    
    def _is_runtime_healthy(self, runtime: str) -> bool:
        """Check if runtime is healthy."""
        health = self.registry.get_health_status(f"runtime:{runtime}")
        return health is None or health.status in ["healthy", "unknown"]
    
    def _estimate_cost(self, provider: str, model_id: str) -> Optional[float]:
        """Estimate cost for provider/model."""
        if provider in ["local", "huggingface", "core_helpers"]:
            return 0.0
        elif provider == "openai":
            return 0.002 if "mini" in model_id else 0.03
        elif provider == "gemini":
            return 0.001
        elif provider == "deepseek":
            return 0.0002
        return None
    
    def _estimate_latency(self, provider: str, runtime: str) -> Optional[float]:
        """Estimate latency for provider/runtime."""
        if provider in ["openai", "gemini", "deepseek"]:
            return 1.5
        elif runtime == "vllm":
            return 0.5
        elif runtime == "transformers":
            return 2.0
        elif runtime == "llama.cpp":
            return 1.0
        elif runtime == "core_helpers":
            return 0.3
        return None
    
    def _determine_strategy(self, request: RoutingRequest, provider: str) -> FallbackStrategy:
        """Determine the fallback strategy used."""
        if provider in ["local", "huggingface"]:
            return FallbackStrategy.CLOUD_TO_LOCAL
        elif provider == "core_helpers":
            return FallbackStrategy.EMERGENCY_DEGRADED
        else:
            return FallbackStrategy.RUNTIME_SWITCH
    
    def _try_degraded_mode_fallback(self, request: RoutingRequest, attempts: List[FallbackAttempt]) -> Optional[FallbackResult]:
        """Try degraded mode as final fallback."""
        if not self.degraded_mode_manager:
            return None
        
        try:
            decision = self.activate_degraded_mode(request)
            if decision:
                degraded_attempt = FallbackAttempt(
                    provider="core_helpers",
                    runtime="core_helpers",
                    model="tinyllama+distilbert+spacy",
                    timestamp=datetime.now(),
                    success=True,
                    confidence=0.3
                )
                attempts.append(degraded_attempt)
                
                return FallbackResult(
                    success=True,
                    used_provider="core_helpers",
                    used_runtime="core_helpers",
                    used_model="tinyllama+distilbert+spacy",
                    attempts=attempts,
                    final_error=None,
                    degraded_mode_activated=True,
                    total_time=0.0,  # Will be calculated by caller
                    strategy_used=FallbackStrategy.EMERGENCY_DEGRADED
                )
        except Exception as e:
            self.logger.error(f"Degraded mode fallback failed: {e}")
        
        return None
    
    def _record_fallback_event(self, original_provider: str, fallback_provider: str, 
                              original_model: Optional[str], fallback_model: Optional[str],
                              reason: FallbackReason, strategy: FallbackStrategy,
                              success: bool, request_type: str) -> None:
        """Record a fallback event for statistics."""
        event = FallbackEvent(
            timestamp=datetime.now(),
            original_provider=original_provider,
            fallback_provider=fallback_provider,
            original_model=original_model,
            fallback_model=fallback_model,
            reason=reason,
            strategy=strategy,
            success=success,
            request_type=request_type
        )
        
        self.fallback_history.append(event)
        
        # Update failure tracking
        if not success:
            self.provider_failure_counts[original_provider] = self.provider_failure_counts.get(original_provider, 0) + 1
            self.provider_last_failure[original_provider] = datetime.now()
    
    def _generate_recovery_suggestions(self, attempts: List[FallbackAttempt]) -> List[str]:
        """Generate recovery suggestions based on failed attempts."""
        suggestions = []
        
        failed_providers = [attempt.provider for attempt in attempts if not attempt.success]
        
        if "openai" in failed_providers:
            suggestions.append("Check OpenAI API key and account status")
        if "gemini" in failed_providers:
            suggestions.append("Verify Google AI API key and quota limits")
        if "local" in failed_providers:
            suggestions.append("Check local model availability and Ollama service status")
        
        if len(failed_providers) > 2:
            suggestions.append("Consider checking network connectivity and firewall settings")
        
        return suggestions
    
    def _get_most_common_failure_reasons(self) -> List[Tuple[str, int]]:
        """Get most common failure reasons from history."""
        reason_counts = {}
        for event in self.fallback_history:
            if not event.success:
                reason = event.reason.value
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        return sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _get_most_used_fallback_providers(self) -> List[Tuple[str, int]]:
        """Get most used fallback providers from history."""
        provider_counts = {}
        for event in self.fallback_history:
            if event.success:
                provider = event.fallback_provider
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
        
        return sorted(provider_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _calculate_fallback_success_rate(self) -> float:
        """Calculate overall fallback success rate."""
        if not self.fallback_history:
            return 0.0
        
        successful_events = sum(1 for event in self.fallback_history if event.success)
        return successful_events / len(self.fallback_history)


# Convenience functions
def get_fallback_manager(registry=None, router=None) -> FallbackManager:
    """Get a fallback manager instance."""
    return FallbackManager(registry=registry, router=router)


# Export classes and functions
__all__ = [
    "FallbackReason",
    "FallbackStrategy", 
    "FallbackEvent",
    "FallbackAttempt",
    "FallbackResult",
    "RecoveryStatus",
    "FallbackManager",
    "get_fallback_manager",
]