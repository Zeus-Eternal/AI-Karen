"""
Seamless Fallback Chain Manager with Capability Preservation for Karen AI Intelligent Fallback System

This module provides comprehensive fallback chain management that ensures uninterrupted service
when providers fail while maintaining required capabilities and context.

Features:
- Intelligent fallback chain creation based on capabilities and performance
- Seamless provider switching without user interruption
- Capability preservation and context bridging between providers
- Comprehensive analytics and optimization of fallback chains
- Integration with health monitoring and provider registry systems
- Support for multiple fallback strategies and preservation levels
"""

import asyncio
import logging
import os
import threading
import time
import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, Union, Awaitable
from collections import defaultdict, deque
import weakref

from .intelligent_provider_registry import (
    IntelligentProviderRegistry, ProviderType, ProviderPriority,
    get_intelligent_provider_registry
)
from .capability_aware_selector import (
    SelectionCriteria, SelectionStrategy, RequestContext, get_capability_selector
)
from .model_availability_cache import (
    ModelAvailabilityCache, AvailabilityStatus, get_model_availability_cache
)
from ..monitoring.network_connectivity import NetworkStatus, get_network_monitor
from ..monitoring.comprehensive_health_monitor import (
    HealthStatus, get_comprehensive_health_monitor
)
from ..monitoring.health_based_decision_maker import (
    DecisionStrategy, get_health_decision_maker
)

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """Fallback chain execution strategies."""
    IMMEDIATE = "immediate"      # Switch immediately on failure
    GRACEFUL = "graceful"        # Wait for current request to complete
    PREDICTIVE = "predictive"     # Switch before failure predicted
    ADAPTIVE = "adaptive"         # Adapt based on context and performance


class CapabilityPreservationLevel(Enum):
    """Levels of capability preservation during fallback."""
    FULL = "full"                # Preserve all capabilities exactly
    PARTIAL = "partial"           # Preserve core capabilities, adapt others
    MINIMAL = "minimal"           # Preserve only essential capabilities
    DEGRADED = "degraded"        # Allow capability degradation


class SwitchTrigger(Enum):
    """Triggers for provider switching."""
    PROVIDER_FAILURE = auto()     # Provider becomes unavailable
    PERFORMANCE_DEGRADATION = auto()  # Performance drops below threshold
    HEALTH_DEGRADATION = auto()   # Health score drops
    NETWORK_CHANGE = auto()        # Network status changes
    PREDICTIVE_FAILURE = auto()    # Predicted future failure
    MANUAL_OVERRIDE = auto()        # Manual intervention


@dataclass
class FallbackStep:
    """Individual step in a fallback chain."""
    provider_name: str
    model_name: Optional[str] = None
    priority: int = 0
    capabilities: Set[str] = field(default_factory=set)
    preservation_level: CapabilityPreservationLevel = CapabilityPreservationLevel.FULL
    switch_conditions: List[str] = field(default_factory=list)
    estimated_latency: float = 0.0
    reliability_score: float = 1.0
    cost_multiplier: float = 1.0
    context_bridge: Optional['ContextBridge'] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FallbackChain:
    """Complete fallback sequence for a specific context."""
    chain_id: str
    context: str
    primary_provider: str
    fallback_steps: List[FallbackStep] = field(default_factory=list)
    strategy: FallbackStrategy = FallbackStrategy.ADAPTIVE
    preservation_level: CapabilityPreservationLevel = CapabilityPreservationLevel.FULL
    required_capabilities: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    success_rate: float = 1.0
    total_executions: int = 0
    average_switch_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FallbackResult:
    """Result of a fallback execution."""
    chain_id: str
    original_provider: str
    final_provider: str
    switches_performed: int
    total_time: float
    success: bool
    preservation_level: CapabilityPreservationLevel
    switch_triggers: List[SwitchTrigger] = field(default_factory=list)
    context_preserved: bool = True
    quality_maintained: bool = True
    error_message: Optional[str] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ContextBridge:
    """Bridge for preserving context between different providers."""
    source_provider: str
    target_provider: str
    capability_mappings: Dict[str, str] = field(default_factory=dict)
    format_transformations: Dict[str, Callable] = field(default_factory=dict)
    context_filters: List[str] = field(default_factory=list)
    preservation_score: float = 1.0
    
    def bridge_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Bridge context data from source to target provider."""
        bridged_context = context_data.copy()
        
        # Apply capability mappings
        for source_cap, target_cap in self.capability_mappings.items():
            if source_cap in bridged_context:
                bridged_context[target_cap] = bridged_context.pop(source_cap)
        
        # Apply format transformations
        for field, transformer in self.format_transformations.items():
            if field in bridged_context:
                try:
                    bridged_context[field] = transformer(bridged_context[field])
                except Exception as e:
                    logger.warning(f"Context transformation failed for {field}: {e}")
        
        # Apply context filters
        for filter_field in self.context_filters:
            bridged_context.pop(filter_field, None)
        
        return bridged_context


@dataclass
class FallbackMetrics:
    """Metrics for tracking fallback performance."""
    total_fallbacks: int = 0
    successful_fallbacks: int = 0
    failed_fallbacks: int = 0
    average_switch_time: float = 0.0
    average_preservation_score: float = 1.0
    chain_usage_counts: Dict[str, int] = field(default_factory=dict)
    provider_switch_counts: Dict[str, int] = field(default_factory=dict)
    capability_gaps: Dict[str, int] = field(default_factory=dict)
    performance_degradation: Dict[str, float] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)


@dataclass
class FallbackConfig:
    """Configuration for fallback chain management."""
    enable_predictive_switching: bool = field(default_factory=lambda: 
        os.environ.get('KAREN_ENABLE_PREDICTIVE_SWITCHING', 'true').lower() == 'true')
    max_chain_length: int = field(default_factory=lambda: 
        int(os.environ.get('KAREN_MAX_FALLBACK_CHAIN_LENGTH', '5')))
    switch_timeout: float = field(default_factory=lambda: 
        float(os.environ.get('KAREN_SWITCH_TIMEOUT', '30.0')))
    preservation_threshold: float = field(default_factory=lambda: 
        float(os.environ.get('KAREN_PRESERVATION_THRESHOLD', '0.8')))
    performance_degradation_threshold: float = field(default_factory=lambda: 
        float(os.environ.get('KAREN_PERFORMANCE_DEGRADATION_THRESHOLD', '0.3')))
    health_degradation_threshold: float = field(default_factory=lambda: 
        float(os.environ.get('KAREN_HEALTH_DEGRADATION_THRESHOLD', '0.6')))
    enable_context_caching: bool = field(default_factory=lambda: 
        os.environ.get('KAREN_ENABLE_CONTEXT_CACHING', 'true').lower() == 'true')
    context_cache_ttl: float = field(default_factory=lambda: 
        float(os.environ.get('KAREN_CONTEXT_CACHE_TTL', '3600.0')))
    analytics_history_size: int = field(default_factory=lambda: 
        int(os.environ.get('KAREN_ANALYTICS_HISTORY_SIZE', '1000')))
    optimization_interval: float = field(default_factory=lambda: 
        float(os.environ.get('KAREN_OPTIMIZATION_INTERVAL', '3600.0')))
    enable_hot_switching: bool = field(default_factory=lambda: 
        os.environ.get('KAREN_ENABLE_HOT_SWITCHING', 'true').lower() == 'true')
    max_concurrent_switches: int = field(default_factory=lambda: 
        int(os.environ.get('KAREN_MAX_CONCURRENT_SWITCHES', '3')))


class FallbackChainManager:
    """
    Comprehensive fallback chain management system.
    
    Provides intelligent fallback chain creation, seamless provider switching,
    capability preservation, and comprehensive analytics.
    """
    
    def __init__(self, config: Optional[FallbackConfig] = None):
        """Initialize fallback chain manager."""
        self.config = config or FallbackConfig()
        
        # Core state
        self._fallback_chains: Dict[str, FallbackChain] = {}
        self._active_switches: Dict[str, asyncio.Task] = {}
        self._context_cache: Dict[str, Tuple[Dict[str, Any], float]] = {}
        self._lock = threading.RLock()
        
        # Component integrations
        self._provider_registry = get_intelligent_provider_registry()
        self._capability_selector = get_capability_selector()
        self._model_cache = get_model_availability_cache()
        self._network_monitor = get_network_monitor()
        self._health_monitor = get_comprehensive_health_monitor()
        self._decision_maker = get_health_decision_maker()
        
        # Analytics and optimization
        self._metrics = FallbackMetrics()
        self._execution_history: deque = deque(maxlen=self.config.analytics_history_size)
        self._optimization_task: Optional[asyncio.Task] = None
        
        # Switch management
        self._switch_semaphore = asyncio.Semaphore(self.config.max_concurrent_switches)
        self._switch_callbacks: List[Callable[[FallbackResult], None]] = []
        
        # Background tasks
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None
        
        logger.info("Fallback chain manager initialized")
    
    async def start_monitoring(self) -> None:
        """Start background monitoring and optimization."""
        if self._monitoring_active:
            logger.warning("Fallback monitoring already active")
            return
        
        self._monitoring_active = True
        
        # Start monitoring task
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        # Start optimization task
        if self.config.optimization_interval > 0:
            self._optimization_task = asyncio.create_task(self._optimization_loop())
        
        logger.info("Fallback chain monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop background monitoring and optimization."""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        
        # Cancel background tasks
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass
        
        # Cancel active switches
        for switch_task in self._active_switches.values():
            switch_task.cancel()
            try:
                await switch_task
            except asyncio.CancelledError:
                pass
        
        self._active_switches.clear()
        
        logger.info("Fallback chain monitoring stopped")
    
    def register_switch_callback(self, callback: Callable[[FallbackResult], None]) -> None:
        """Register callback for fallback switch events."""
        self._switch_callbacks.append(callback)
    
    def create_fallback_chain(
        self,
        context: str,
        primary_provider: str,
        required_capabilities: Optional[Set[str]] = None,
        strategy: Optional[FallbackStrategy] = None,
        preservation_level: Optional[CapabilityPreservationLevel] = None
    ) -> FallbackChain:
        """
        Create an intelligent fallback chain for a given context.
        
        Args:
            context: Usage context (e.g., 'chat', 'code', 'embedding')
            primary_provider: Primary provider to use
            required_capabilities: Required capabilities for the context
            strategy: Fallback strategy to use
            preservation_level: Capability preservation level
            
        Returns:
            Created fallback chain
        """
        with self._lock:
            # Generate chain ID
            chain_id = self._generate_chain_id(context, primary_provider)
            
            # Set defaults
            strategy = strategy or FallbackStrategy.ADAPTIVE
            preservation_level = preservation_level or CapabilityPreservationLevel.FULL
            required_capabilities = required_capabilities or set()
            
            # Get fallback candidates
            fallback_steps = self._create_fallback_steps(
                primary_provider, required_capabilities, preservation_level
            )
            
            # Create chain
            chain = FallbackChain(
                chain_id=chain_id,
                context=context,
                primary_provider=primary_provider,
                fallback_steps=fallback_steps,
                strategy=strategy,
                preservation_level=preservation_level,
                required_capabilities=required_capabilities,
                metadata={
                    'network_status': self._network_monitor.get_current_status().value,
                    'creation_time': time.time()
                }
            )
            
            # Store chain
            self._fallback_chains[chain_id] = chain
            
            logger.info(
                f"Created fallback chain {chain_id} for {context} with {len(fallback_steps)} steps"
            )
            
            return chain
    
    def _create_fallback_steps(
        self,
        primary_provider: str,
        required_capabilities: Set[str],
        preservation_level: CapabilityPreservationLevel
    ) -> List[FallbackStep]:
        """Create fallback steps based on capabilities and performance."""
        steps = []
        
        # Get all available providers
        all_providers = self._provider_registry._registrations
        
        # Get primary provider info
        primary_reg = all_providers.get(primary_provider)
        if not primary_reg:
            logger.warning(f"Primary provider {primary_provider} not found")
            return steps
        
        # Get network status
        network_status = self._network_monitor.get_current_status()
        
        # Create candidate providers
        candidates = []
        for provider_name, reg in all_providers.items():
            if provider_name == primary_provider:
                continue
            
            # Check network compatibility
            if reg.network_dependent and network_status == NetworkStatus.OFFLINE:
                if not reg.offline_capable:
                    continue
            
            # Get provider capabilities
            provider_caps = set()
            for model in reg.base_registration.models:
                provider_caps.update(model.capabilities)
            
            # Check capability match
            capability_score = self._capability_selector.capability_matcher.calculate_capability_score(
                required_capabilities, provider_caps
            )
            
            if capability_score < self.config.preservation_threshold:
                continue
            
            # Calculate priority
            priority = self._calculate_provider_priority(reg, capability_score, network_status)
            
            candidates.append((provider_name, reg, capability_score, priority))
        
        # Sort by priority
        candidates.sort(key=lambda x: x[3])
        
        # Create fallback steps
        for provider_name, reg, capability_score, priority in candidates[:self.config.max_chain_length]:
            # Create context bridge
            context_bridge = self._create_context_bridge(
                primary_provider, provider_name, required_capabilities
            )
            
            step = FallbackStep(
                provider_name=provider_name,
                priority=priority,
                capabilities=required_capabilities.intersection(
                    set().union(*[model.capabilities for model in reg.base_registration.models])
                ),
                preservation_level=preservation_level,
                estimated_latency=reg.metrics.average_latency,
                reliability_score=reg.reliability_score,
                cost_multiplier=self._get_cost_multiplier(reg.cost_tier),
                context_bridge=context_bridge,
                metadata={
                    'capability_score': capability_score,
                    'provider_type': reg.provider_type.name,
                    'network_dependent': reg.network_dependent
                }
            )
            
            steps.append(step)
        
        return steps
    
    def _calculate_provider_priority(
        self,
        reg: Any,
        capability_score: float,
        network_status: NetworkStatus
    ) -> int:
        """Calculate priority score for provider selection."""
        priority = reg.priority.value * 100  # Base priority
        
        # Adjust for capability score
        priority -= int(capability_score * 20)
        
        # Adjust for network status
        if network_status == NetworkStatus.OFFLINE:
            if reg.provider_type == ProviderType.LOCAL:
                priority -= 50
            elif reg.offline_capable:
                priority -= 25
        elif network_status == NetworkStatus.DEGRADED:
            if reg.provider_type == ProviderType.LOCAL:
                priority -= 20
            elif reg.reliability_score > 0.8:
                priority -= 10
        
        # Adjust for performance
        if reg.metrics.success_rate < 0.8:
            priority += 20
        elif reg.metrics.success_rate < 0.5:
            priority += 40
        
        return priority
    
    def _create_context_bridge(
        self,
        source_provider: str,
        target_provider: str,
        required_capabilities: Set[str]
    ) -> Optional[ContextBridge]:
        """Create context bridge between providers."""
        try:
            # Get provider info
            source_reg = self._provider_registry._registrations.get(source_provider)
            target_reg = self._provider_registry._registrations.get(target_provider)
            
            if not source_reg or not target_reg:
                return None
            
            # Create capability mappings
            capability_mappings = {}
            for cap in required_capabilities:
                # Check if capability needs mapping
                if cap not in target_reg.base_registration.models[0].capabilities:
                    # Find similar capability
                    similar = self._capability_selector.capability_matcher._find_similar_capability(
                        cap, set().union(*[m.capabilities for m in target_reg.base_registration.models])
                    )
                    if similar:
                        capability_mappings[cap] = similar
            
            # Calculate preservation score
            preservation_score = 1.0 - (len(capability_mappings) * 0.1)
            
            return ContextBridge(
                source_provider=source_provider,
                target_provider=target_provider,
                capability_mappings=capability_mappings,
                preservation_score=max(0.0, preservation_score)
            )
            
        except Exception as e:
            logger.error(f"Failed to create context bridge: {e}")
            return None
    
    def _get_cost_multiplier(self, cost_tier: str) -> float:
        """Get cost multiplier for cost tier."""
        multipliers = {
            'free': 0.0,
            'standard': 1.0,
            'premium': 2.0
        }
        return multipliers.get(cost_tier, 1.0)
    
    def _generate_chain_id(self, context: str, primary_provider: str) -> str:
        """Generate unique chain ID."""
        data = f"{context}:{primary_provider}:{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    async def execute_fallback_chain(
        self,
        chain_id: str,
        request_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> FallbackResult:
        """
        Execute a fallback chain for a request.
        
        Args:
            chain_id: ID of the fallback chain to execute
            request_data: Request data to process
            context: Additional context information
            
        Returns:
            Fallback execution result
        """
        start_time = time.time()
        
        with self._lock:
            chain = self._fallback_chains.get(chain_id)
            if not chain:
                raise ValueError(f"Fallback chain {chain_id} not found")
            
            # Update chain usage
            chain.last_used = start_time
            chain.total_executions += 1
        
        # Initialize result
        result = FallbackResult(
            chain_id=chain_id,
            original_provider=chain.primary_provider,
            final_provider=chain.primary_provider,
            switches_performed=0,
            total_time=0.0,
            success=False,
            preservation_level=chain.preservation_level,
            context_preserved=True,
            quality_maintained=True
        )
        
        try:
            # Execute with fallback chain
            current_provider = chain.primary_provider
            current_context = context or {}
            
            async with self._switch_semaphore:
                for step_index, step in enumerate([None] + chain.fallback_steps):
                    provider_name = step.provider_name if step else chain.primary_provider
                    
                    try:
                        # Attempt execution with current provider
                        success, response_time, error = await self._execute_with_provider(
                            provider_name, request_data, current_context
                        )
                        
                        if success:
                            # Successful execution
                            result.final_provider = provider_name
                            result.success = True
                            result.total_time = time.time() - start_time
                            result.performance_metrics['response_time'] = response_time
                            
                            # Update chain success rate
                            with self._lock:
                                chain.success_rate = (
                                    (chain.success_rate * (chain.total_executions - 1) + 1.0) /
                                    chain.total_executions
                                )
                            
                            break
                        else:
                            # Provider failed, attempt fallback
                            if step:
                                trigger = self._determine_switch_trigger(error)
                                result.switch_triggers.append(trigger)
                                
                                # Bridge context if needed
                                if step.context_bridge:
                                    current_context = step.context_bridge.bridge_context(current_context)
                                    result.context_preserved = (
                                        result.context_preserved and 
                                        step.context_bridge.preservation_score > self.config.preservation_threshold
                                    )
                                
                                current_provider = step.provider_name
                                result.switches_performed += 1
                                
                                logger.info(
                                    f"Fallback switch {step_index}: {provider_name} -> {step.provider_name} "
                                    f"(trigger: {trigger.name})"
                                )
                            else:
                                # No more fallback options
                                result.error_message = f"All providers failed: {error}"
                                break
                    
                    except Exception as e:
                        logger.error(f"Provider execution failed: {e}")
                        if step:
                            result.switch_triggers.append(SwitchTrigger.PROVIDER_FAILURE)
                        continue
            
            # Update metrics
            self._update_fallback_metrics(result)
            
            # Record execution
            self._execution_history.append(result)
            
            # Trigger callbacks
            for callback in self._switch_callbacks:
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"Fallback callback error: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Fallback chain execution failed: {e}")
            result.error_message = str(e)
            result.total_time = time.time() - start_time
            return result
    
    async def _execute_with_provider(
        self,
        provider_name: str,
        request_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, float, Optional[str]]:
        """Execute request with a specific provider."""
        start_time = time.time()
        
        try:
            # Get provider instance
            provider = self._provider_registry.get_provider(provider_name)
            if not provider:
                return False, 0.0, f"Provider {provider_name} not available"
            
            # Check provider health
            provider_health = self._health_monitor.get_component_health(provider_name)
            if provider_health and provider_health.status == HealthStatus.UNHEALTHY:
                return False, 0.0, f"Provider {provider_name} unhealthy"
            
            # Execute request (this is a simplified implementation)
            # In a real system, this would call the provider's actual API
            if hasattr(provider, 'process_request'):
                response = await provider.process_request(request_data, context)
                success = response.get('success', False)
                error = response.get('error') if not success else None
            else:
                # Simulate execution
                await asyncio.sleep(0.1)  # Simulate processing time
                success = True
                error = None
            
            response_time = time.time() - start_time
            
            # Record performance
            self._provider_registry.record_provider_performance(
                provider_name, success, response_time, error
            )
            
            return success, response_time, error
            
        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time, str(e)
    
    def _determine_switch_trigger(self, error: Optional[str]) -> SwitchTrigger:
        """Determine the trigger for a provider switch."""
        if not error:
            return SwitchTrigger.MANUAL_OVERRIDE
        
        error_lower = error.lower()
        
        if 'network' in error_lower or 'connection' in error_lower:
            return SwitchTrigger.NETWORK_CHANGE
        elif 'timeout' in error_lower or 'slow' in error_lower:
            return SwitchTrigger.PERFORMANCE_DEGRADATION
        elif 'health' in error_lower or 'unhealthy' in error_lower:
            return SwitchTrigger.HEALTH_DEGRADATION
        elif 'predicted' in error_lower:
            return SwitchTrigger.PREDICTIVE_FAILURE
        else:
            return SwitchTrigger.PROVIDER_FAILURE
    
    def _update_fallback_metrics(self, result: FallbackResult) -> None:
        """Update fallback metrics with execution result."""
        with self._lock:
            self._metrics.total_fallbacks += 1
            
            if result.success:
                self._metrics.successful_fallbacks += 1
            else:
                self._metrics.failed_fallbacks += 1
            
            # Update switch time
            if result.switches_performed > 0:
                switch_time = result.total_time / result.switches_performed
                self._metrics.average_switch_time = (
                    (self._metrics.average_switch_time * (self._metrics.total_fallbacks - 1) + switch_time) /
                    self._metrics.total_fallbacks
                )
            
            # Update chain usage
            self._metrics.chain_usage_counts[result.chain_id] = (
                self._metrics.chain_usage_counts.get(result.chain_id, 0) + 1
            )
            
            # Update provider switch counts
            if result.switches_performed > 0:
                switch_key = f"{result.original_provider}->{result.final_provider}"
                self._metrics.provider_switch_counts[switch_key] = (
                    self._metrics.provider_switch_counts.get(switch_key, 0) + 1
                )
            
            self._metrics.last_updated = time.time()
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop for predictive switching."""
        logger.info("Fallback monitoring loop started")
        
        while self._monitoring_active:
            try:
                await self._perform_predictive_checks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)
        
        logger.info("Fallback monitoring loop stopped")
    
    async def _perform_predictive_checks(self) -> None:
        """Perform predictive checks for proactive switching."""
        if not self.config.enable_predictive_switching:
            return
        
        # Get current health status
        health_summary = self._health_monitor.get_health_summary()
        overall_score = health_summary.get('overall_score', 1.0)
        
        # Check if predictive switching is needed
        if overall_score < self.config.health_degradation_threshold:
            logger.info(f"Health degradation detected (score: {overall_score:.3f}), checking for proactive switches")
            
            # Check active chains for potential issues
            with self._lock:
                for chain_id, chain in self._fallback_chains.items():
                    if await self._should_proactively_switch(chain, health_summary):
                        logger.info(f"Proactive switch recommended for chain {chain_id}")
    
    async def _should_proactively_switch(
        self,
        chain: FallbackChain,
        health_summary: Dict[str, Any]
    ) -> bool:
        """Determine if proactive switching should be triggered."""
        # Check primary provider health
        primary_health = self._health_monitor.get_component_health(chain.primary_provider)
        
        if primary_health and primary_health.status == HealthStatus.DEGRADED:
            # Check if we have better fallback options
            for step in chain.fallback_steps[:2]:  # Check top 2 fallbacks
                fallback_health = self._health_monitor.get_component_health(step.provider_name)
                if (fallback_health and 
                    fallback_health.status == HealthStatus.HEALTHY and
                    fallback_health.score > primary_health.score + 0.2):
                    return True
        
        return False
    
    async def _optimization_loop(self) -> None:
        """Background optimization loop for fallback chains."""
        logger.info("Fallback optimization loop started")
        
        while self._monitoring_active:
            try:
                await self._optimize_fallback_chains()
                await asyncio.sleep(self.config.optimization_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(60)
        
        logger.info("Fallback optimization loop stopped")
    
    async def _optimize_fallback_chains(self) -> None:
        """Optimize fallback chains based on performance data."""
        with self._lock:
            if len(self._execution_history) < 10:
                return  # Not enough data for optimization
            
            # Analyze chain performance
            chain_performance = defaultdict(list)
            for result in self._execution_history:
                chain_performance[result.chain_id].append(result)
            
            # Optimize each chain
            for chain_id, results in chain_performance.items():
                if len(results) < 5:
                    continue  # Not enough data for this chain
                
                chain = self._fallback_chains.get(chain_id)
                if not chain:
                    continue
                
                # Calculate performance metrics
                success_rate = sum(1 for r in results if r.success) / len(results)
                avg_switch_time = sum(r.total_time for r in results) / len(results)
                
                # Identify underperforming steps
                step_performance = defaultdict(list)
                for result in results:
                    if result.switches_performed > 0:
                        for i in range(min(result.switches_performed, len(chain.fallback_steps))):
                            step_key = chain.fallback_steps[i].provider_name
                            step_performance[step_key].append(result)
                
                # Reorder steps based on performance
                for step in chain.fallback_steps:
                    step_results = step_performance.get(step.provider_name, [])
                    if step_results:
                        step_success_rate = sum(1 for r in step_results if r.success) / len(step_results)
                        step.priority = int((1.0 - step_success_rate) * 100)
                
                # Sort steps by updated priority
                chain.fallback_steps.sort(key=lambda s: s.priority)
                
                logger.debug(f"Optimized fallback chain {chain_id} with {len(results)} executions")
    
    def get_fallback_chain(self, chain_id: str) -> Optional[FallbackChain]:
        """Get fallback chain by ID."""
        with self._lock:
            return self._fallback_chains.get(chain_id)
    
    def get_fallback_chains_by_context(self, context: str) -> List[FallbackChain]:
        """Get all fallback chains for a specific context."""
        with self._lock:
            return [
                chain for chain in self._fallback_chains.values()
                if chain.context == context
            ]
    
    def get_fallback_metrics(self) -> FallbackMetrics:
        """Get current fallback metrics."""
        with self._lock:
            return self._metrics
    
    def get_chain_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics about fallback chains."""
        with self._lock:
            analytics = {
                'total_chains': len(self._fallback_chains),
                'active_switches': len(self._active_switches),
                'metrics': {
                    'total_fallbacks': self._metrics.total_fallbacks,
                    'success_rate': (
                        self._metrics.successful_fallbacks / 
                        max(self._metrics.total_fallbacks, 1)
                    ),
                    'average_switch_time': self._metrics.average_switch_time,
                    'average_preservation_score': self._metrics.average_preservation_score
                },
                'chain_usage': dict(self._metrics.chain_usage_counts),
                'provider_switches': dict(self._metrics.provider_switch_counts),
                'capability_gaps': dict(self._metrics.capability_gaps),
                'performance_degradation': dict(self._metrics.performance_degradation)
            }
            
            # Context distribution
            context_counts = defaultdict(int)
            for chain in self._fallback_chains.values():
                context_counts[chain.context] += 1
            
            analytics['context_distribution'] = dict(context_counts)
            
            # Strategy distribution
            strategy_counts = defaultdict(int)
            for chain in self._fallback_chains.values():
                strategy_counts[chain.strategy.value] += 1
            
            analytics['strategy_distribution'] = dict(strategy_counts)
            
            return analytics
    
    def clear_cache(self) -> None:
        """Clear context cache and temporary data."""
        with self._lock:
            self._context_cache.clear()
            logger.info("Fallback chain cache cleared")


# Global instance
_fallback_chain_manager: Optional[FallbackChainManager] = None
_manager_lock = threading.RLock()


def get_fallback_chain_manager(config: Optional[FallbackConfig] = None) -> FallbackChainManager:
    """Get or create global fallback chain manager instance."""
    global _fallback_chain_manager
    if _fallback_chain_manager is None:
        with _manager_lock:
            if _fallback_chain_manager is None:
                _fallback_chain_manager = FallbackChainManager(config)
    return _fallback_chain_manager


async def initialize_fallback_chain_manager(config: Optional[FallbackConfig] = None) -> FallbackChainManager:
    """Initialize fallback chain manager system."""
    manager = get_fallback_chain_manager(config)
    await manager.start_monitoring()
    logger.info("Fallback chain manager system initialized")
    return manager


# Export main classes for easy import
__all__ = [
    "FallbackStrategy",
    "CapabilityPreservationLevel",
    "SwitchTrigger",
    "FallbackStep",
    "FallbackChain",
    "FallbackResult",
    "ContextBridge",
    "FallbackMetrics",
    "FallbackConfig",
    "FallbackChainManager",
    "get_fallback_chain_manager",
    "initialize_fallback_chain_manager",
]