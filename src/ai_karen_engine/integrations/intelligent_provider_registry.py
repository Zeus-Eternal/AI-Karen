"""
Intelligent Provider Registry with Fallback Routing
- Local-first provider priority system
- Network-aware provider selection
- Capability-based routing with fallback chains
- Health monitoring and automatic switching
- Cost optimization through smart selection
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Type, Set, Tuple, Callable
from collections import defaultdict

from .provider_registry import ModelInfo, ProviderRegistration
from ..monitoring.network_connectivity import NetworkStatus, get_network_monitor

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Provider classification for intelligent routing"""
    LOCAL = auto()
    CLOUD = auto()
    HYBRID = auto()
    FALLBACK = auto()


class ProviderPriority(Enum):
    """Provider priority levels for local-first routing"""
    CRITICAL = 0  # Always available (fallback providers)
    LOCAL = 1     # Local models and services
    PREFERRED = 2  # Preferred cloud providers
    STANDARD = 3   # Standard cloud providers
    EXPERIMENTAL = 4  # Experimental or less reliable providers


@dataclass
class ProviderMetrics:
    """Performance and reliability metrics for providers"""
    success_rate: float = 1.0
    average_latency: float = 0.0
    last_success: float = 0.0
    last_failure: float = 0.0
    consecutive_failures: int = 0
    total_requests: int = 0
    failure_count: int = 0
    circuit_breaker_until: float = 0.0
    rate_limit_until: float = 0.0
    cost_per_request: float = 0.0
    capabilities_score: Dict[str, float] = field(default_factory=dict)


@dataclass
class IntelligentProviderRegistration:
    """Enhanced provider registration with intelligent routing metadata"""
    base_registration: ProviderRegistration
    provider_type: ProviderType
    priority: ProviderPriority
    network_dependent: bool = True
    offline_capable: bool = False
    cost_tier: str = "standard"  # free, standard, premium
    reliability_score: float = 1.0
    max_concurrent_requests: int = 10
    warmup_time: float = 0.0
    capabilities_weight: Dict[str, float] = field(default_factory=dict)
    fallback_chain: List[str] = field(default_factory=list)
    auto_failover: bool = True
    metrics: ProviderMetrics = field(default_factory=ProviderMetrics)


class CapabilityMatcher:
    """Intelligent capability matching for provider selection"""
    
    @staticmethod
    def calculate_capability_score(
        required_capabilities: Set[str],
        provider_capabilities: Set[str],
        capability_weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate how well a provider matches required capabilities"""
        if not required_capabilities:
            return 1.0
            
        capability_weights = capability_weights or {}
        total_score = 0.0
        total_weight = 0.0
        
        for cap in required_capabilities:
            weight = capability_weights.get(cap, 1.0)
            total_weight += weight
            
            if cap in provider_capabilities:
                # Exact match gets full weight
                total_score += weight
            elif CapabilityMatcher._find_similar_capability(cap, provider_capabilities):
                # Similar capability gets partial weight
                total_score += weight * 0.7
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    @staticmethod
    def _find_similar_capability(target: str, capabilities: Set[str]) -> bool:
        """Find if there's a similar capability available"""
        similarity_map = {
            'text': ['conversation', 'chat', 'generation'],
            'code': ['coding', 'programming', 'development'],
            'embeddings': ['embedding', 'vector', 'semantic'],
            'analysis': ['reasoning', 'inference', 'processing'],
            'creative': ['generation', 'writing', 'composition'],
        }
        
        similar_caps = similarity_map.get(target.lower(), [])
        return any(sim in capabilities for sim in similar_caps)


class IntelligentProviderRegistry:
    """Enhanced provider registry with intelligent fallback routing"""
    
    def __init__(self) -> None:
        self._registrations: Dict[str, IntelligentProviderRegistration] = {}
        self._instances: Dict[str, Dict[int, Any]] = {}
        self._lock = threading.RLock()
        self._network_monitor = get_network_monitor()
        self._capability_matcher = CapabilityMatcher()
        
        # Performance tracking
        self._request_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000
        
        # Background monitoring
        self._monitoring_active = False
        self._start_health_monitoring()
    
    def register_intelligent_provider(
        self,
        base_registration: ProviderRegistration,
        provider_type: ProviderType,
        priority: ProviderPriority,
        **kwargs
    ) -> None:
        """Register a provider with intelligent routing metadata"""
        with self._lock:
            intelligent_reg = IntelligentProviderRegistration(
                base_registration=base_registration,
                provider_type=provider_type,
                priority=priority,
                **kwargs
            )
            
            self._registrations[base_registration.name] = intelligent_reg
            self._instances.setdefault(base_registration.name, {})
            
            logger.info(
                f"Registered intelligent provider: {base_registration.name} "
                f"(type: {provider_type.name}, priority: {priority.name})"
            )
    
    def get_optimal_provider(
        self,
        required_capabilities: Optional[Set[str]] = None,
        preference: str = "balanced",  # cost, speed, reliability, local_first
        exclude_providers: Optional[Set[str]] = None
    ) -> Tuple[Optional[str], Optional[IntelligentProviderRegistration]]:
        """Get optimal provider based on current conditions and requirements"""
        with self._lock:
            current_time = time.time()
            network_status = self._network_monitor.get_current_status()
            exclude_providers = exclude_providers or set()
            
            # Filter available providers
            candidates = []
            for name, reg in self._registrations.items():
                if name in exclude_providers:
                    continue
                    
                # Check network dependency
                if reg.network_dependent and network_status == NetworkStatus.OFFLINE:
                    if not reg.offline_capable:
                        continue
                
                # Check circuit breaker
                if current_time < reg.metrics.circuit_breaker_until:
                    continue
                
                # Check rate limiting
                if current_time < reg.metrics.rate_limit_until:
                    continue
                
                # Check capability match
                provider_caps = set()
                for model in reg.base_registration.models:
                    provider_caps.update(model.capabilities)
                
                if required_capabilities:
                    capability_score = self._capability_matcher.calculate_capability_score(
                        required_capabilities, provider_caps, reg.capabilities_weight
                    )
                    if capability_score < 0.3:  # Minimum capability threshold
                        continue
                else:
                    capability_score = 1.0
                
                candidates.append((name, reg, capability_score))
            
            if not candidates:
                return None, None
            
            # Sort candidates based on preference
            sorted_candidates = self._sort_candidates(candidates, preference, network_status)
            
            # Return best candidate
            best_name, best_reg, _ = sorted_candidates[0]
            return best_name, best_reg
    
    def _sort_candidates(
        self,
        candidates: List[Tuple[str, IntelligentProviderRegistration, float]],
        preference: str,
        network_status: NetworkStatus
    ) -> List[Tuple[str, IntelligentProviderRegistration, float]]:
        """Sort candidates based on preference and current conditions"""
        
        def sort_key(candidate):
            name, reg, capability_score = candidate
            
            # Base priority score (lower is better)
            priority_score = reg.priority.value
            
            # Network status adjustments
            if network_status == NetworkStatus.OFFLINE:
                if reg.provider_type == ProviderType.LOCAL:
                    priority_score -= 10  # Heavily prefer local when offline
                elif reg.offline_capable:
                    priority_score -= 5
                else:
                    priority_score += 20  # Deprioritize network-dependent providers
            elif network_status == NetworkStatus.DEGRADED:
                if reg.provider_type == ProviderType.LOCAL:
                    priority_score -= 5
                elif reg.reliability_score > 0.8:
                    priority_score -= 2
            
            # Preference-based adjustments
            if preference == "local_first":
                if reg.provider_type == ProviderType.LOCAL:
                    priority_score -= 15
                elif reg.provider_type == ProviderType.HYBRID:
                    priority_score -= 5
            elif preference == "cost":
                if reg.cost_tier == "free":
                    priority_score -= 10
                elif reg.cost_tier == "standard":
                    priority_score -= 5
            elif preference == "speed":
                if reg.metrics.average_latency > 0:
                    priority_score += reg.metrics.average_latency * 10
            elif preference == "reliability":
                priority_score += (1.0 - reg.reliability_score) * 20
            
            # Performance-based adjustments
            if reg.metrics.success_rate < 0.5:
                priority_score += 15
            elif reg.metrics.success_rate < 0.8:
                priority_score += 5
            
            # Capability score (higher is better, so we subtract)
            priority_score -= capability_score * 5
            
            return priority_score
        
        return sorted(candidates, key=sort_key)
    
    def get_fallback_chain(
        self,
        primary_provider: str,
        required_capabilities: Optional[Set[str]] = None
    ) -> List[str]:
        """Get fallback chain for a provider"""
        with self._lock:
            primary_reg = self._registrations.get(primary_provider)
            if not primary_reg:
                return []
            
            # Start with configured fallback chain
            fallback_chain = list(primary_reg.fallback_chain)
            
            # Add intelligent fallbacks based on capabilities
            if required_capabilities:
                for name, reg in self._registrations.items():
                    if name == primary_provider or name in fallback_chain:
                        continue
                    
                    provider_caps = set()
                    for model in reg.base_registration.models:
                        provider_caps.update(model.capabilities)
                    
                    capability_score = self._capability_matcher.calculate_capability_score(
                        required_capabilities, provider_caps, reg.capabilities_weight
                    )
                    
                    if capability_score >= 0.5 and reg.auto_failover:
                        fallback_chain.append(name)
            
            return fallback_chain
    
    def record_provider_performance(
        self,
        provider_name: str,
        success: bool,
        latency: float = 0.0,
        error: Optional[str] = None
    ) -> None:
        """Record performance metrics for a provider"""
        with self._lock:
            reg = self._registrations.get(provider_name)
            if not reg:
                return
            
            current_time = time.time()
            metrics = reg.metrics
            
            # Update basic metrics
            metrics.total_requests += 1
            if success:
                metrics.last_success = current_time
                metrics.consecutive_failures = 0
                if latency > 0:
                    # Update moving average
                    alpha = 0.1  # Smoothing factor
                    if metrics.average_latency == 0:
                        metrics.average_latency = latency
                    else:
                        metrics.average_latency = (
                            alpha * latency + 
                            (1 - alpha) * metrics.average_latency
                        )
            else:
                metrics.last_failure = current_time
                metrics.consecutive_failures += 1
                metrics.failure_count += 1
                
                # Circuit breaker logic
                if metrics.consecutive_failures >= 3:
                    backoff_time = min(300, 2 ** metrics.consecutive_failures)  # Max 5 minutes
                    metrics.circuit_breaker_until = current_time + backoff_time
                    logger.warning(
                        f"Circuit breaker opened for {provider_name} for {backoff_time}s"
                    )
            
            # Update success rate
            metrics.success_rate = (
                (metrics.total_requests - metrics.failure_count) / metrics.total_requests
            )
            
            # Record in history
            self._record_request_history(provider_name, success, latency, error)
    
    def _record_request_history(
        self,
        provider_name: str,
        success: bool,
        latency: float,
        error: Optional[str] = None
    ) -> None:
        """Record request in history for analysis"""
        record = {
            "provider": provider_name,
            "timestamp": time.time(),
            "success": success,
            "latency": latency,
            "error": error
        }
        
        self._request_history.append(record)
        
        # Trim history if too large
        if len(self._request_history) > self._max_history_size:
            self._request_history = self._request_history[-self._max_history_size:]
    
    def get_provider_metrics(self, provider_name: str) -> Optional[ProviderMetrics]:
        """Get performance metrics for a provider"""
        with self._lock:
            reg = self._registrations.get(provider_name)
            return reg.metrics if reg else None
    
    def get_all_provider_metrics(self) -> Dict[str, ProviderMetrics]:
        """Get metrics for all providers"""
        with self._lock:
            return {name: reg.metrics for name, reg in self._registrations.items()}
    
    def reset_provider_metrics(self, provider_name: str) -> bool:
        """Reset metrics for a provider"""
        with self._lock:
            reg = self._registrations.get(provider_name)
            if reg:
                reg.metrics = ProviderMetrics()
                return True
            return False
    
    def _start_health_monitoring(self) -> None:
        """Start background health monitoring"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        
        def monitor_loop():
            while self._monitoring_active:
                try:
                    self._perform_health_check()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    time.sleep(30)
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        logger.info("Started intelligent provider health monitoring")
    
    def _perform_health_check(self) -> None:
        """Perform health check on all providers"""
        with self._lock:
            current_time = time.time()
            network_status = self._network_monitor.get_current_status()
            
            for name, reg in self._registrations.items():
                # Check if circuit breaker can be reset
                if current_time >= reg.metrics.circuit_breaker_until:
                    if reg.metrics.consecutive_failures > 0:
                        logger.info(f"Circuit breaker reset for {name}")
                        reg.metrics.consecutive_failures = 0
                
                # Network-dependent provider health
                if reg.network_dependent:
                    if network_status == NetworkStatus.OFFLINE and not reg.offline_capable:
                        reg.metrics.success_rate *= 0.9  # Degrade success rate
                    elif network_status == NetworkStatus.ONLINE:
                        reg.metrics.success_rate = min(1.0, reg.metrics.success_rate * 1.05)
    
    def shutdown(self) -> None:
        """Shutdown registry and cleanup resources"""
        self._monitoring_active = False
        
        with self._lock:
            # Shutdown all provider instances
            for provider_name, instances in self._instances.items():
                for cache_key, instance in instances.items():
                    try:
                        if hasattr(instance, "shutdown"):
                            if inspect.iscoroutinefunction(instance.shutdown):
                                asyncio.create_task(instance.shutdown())
                            else:
                                instance.shutdown()
                    except Exception as e:
                        logger.warning(f"Error shutting down {provider_name}: {e}")
        
        logger.info("Intelligent provider registry shutdown complete")
    
    # Compatibility methods with existing provider registry
    def register_provider(
        self,
        name: str,
        provider_class: Type[Any],
        *,
        description: str = "",
        models: Optional[List[ModelInfo]] = None,
        requires_api_key: bool = False,
        default_model: Optional[str] = None,
        category: str = "LLM",
        provider_type: ProviderType = ProviderType.CLOUD,
        priority: ProviderPriority = ProviderPriority.STANDARD,
        **kwargs
    ) -> None:
        """Register provider with intelligent routing (compatibility method)"""
        base_reg = ProviderRegistration(
            name=name,
            provider_class=provider_class,
            description=description,
            models=models or [],
            requires_api_key=requires_api_key,
            default_model=default_model,
            category=category
        )
        
        self.register_intelligent_provider(
            base_reg, provider_type, priority, **kwargs
        )
    
    def get_provider(self, name: str, **init_kwargs: Any) -> Optional[Any]:
        """Get provider instance (compatibility method)"""
        with self._lock:
            reg = self._registrations.get(name)
            if not reg:
                return None
            
            base_reg = reg.base_registration
            
            # Inject default model if not provided
            if base_reg.default_model and "model" not in init_kwargs:
                init_kwargs["model"] = base_reg.default_model
            
            bucket = self._instances.setdefault(name, {})
            try:
                cache_key = hash(frozenset(init_kwargs.items()))
            except TypeError:
                cache_key = hash(repr(sorted(init_kwargs.items(), key=lambda kv: kv[0])))
            
            if cache_key not in bucket:
                logger.debug(f"Creating intelligent provider instance '{name}' with kwargs={init_kwargs}")
                bucket[cache_key] = base_reg.provider_class(**init_kwargs)
            return bucket[cache_key]
    
    def list_providers(self, provider_type: Optional[ProviderType] = None) -> List[str]:
        """List providers by type"""
        with self._lock:
            if provider_type:
                return [
                    name for name, reg in self._registrations.items()
                    if reg.provider_type == provider_type
                ]
            return list(self._registrations.keys())
    
    def get_provider_info(self, name: str) -> Optional[IntelligentProviderRegistration]:
        """Get intelligent provider registration info"""
        with self._lock:
            return self._registrations.get(name)


# Global instance
_intelligent_registry: Optional[IntelligentProviderRegistry] = None
_registry_lock = threading.RLock()


def get_intelligent_provider_registry() -> IntelligentProviderRegistry:
    """Get the global intelligent provider registry instance"""
    global _intelligent_registry
    if _intelligent_registry is None:
        with _registry_lock:
            if _intelligent_registry is None:
                _intelligent_registry = IntelligentProviderRegistry()
    return _intelligent_registry


def initialize_intelligent_provider_registry() -> IntelligentProviderRegistry:
    """Reinitialize and return a fresh intelligent provider registry"""
    global _intelligent_registry
    with _registry_lock:
        _intelligent_registry = IntelligentProviderRegistry()
    return _intelligent_registry


__all__ = [
    "ProviderType",
    "ProviderPriority",
    "ProviderMetrics",
    "IntelligentProviderRegistration",
    "CapabilityMatcher",
    "IntelligentProviderRegistry",
    "get_intelligent_provider_registry",
    "initialize_intelligent_provider_registry",
]