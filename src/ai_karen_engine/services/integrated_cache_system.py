"""
Integrated Cache System

Connects the smart caching system with existing cache infrastructure
without disrupting FlowManager execution and other existing functionality.

Requirements addressed:
- 2.2: Efficient caching to avoid redundant computations
- 2.3: Intelligent cache invalidation based on content relevance
- 6.1-6.5: Smart caching and computation reuse capabilities
"""

import asyncio
import logging
import threading
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
import weakref

from ai_karen_engine.services.smart_cache_manager import (
    SmartCacheManager, get_smart_cache_manager, CacheEntry
)

logger = logging.getLogger("kari.integrated_cache_system")

@dataclass
class CacheIntegrationConfig:
    """Configuration for cache integration."""
    enable_flow_manager_caching: bool = True
    enable_decision_engine_caching: bool = True
    enable_small_language_model_caching: bool = True
    enable_response_caching: bool = True
    cache_ttl_seconds: float = 3600.0  # 1 hour default
    max_cache_size_mb: int = 100
    enable_distributed_cache: bool = False
    cache_warming_enabled: bool = True

@dataclass
class CacheIntegrationMetrics:
    """Metrics for cache integration performance."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_invalidations: int = 0
    cache_warmings: int = 0
    average_response_time_ms: float = 0.0
    cache_size_mb: float = 0.0
    hit_rate: float = 0.0

class IntegratedCacheSystem:
    """
    Integrated cache system that connects smart caching with existing infrastructure
    while preserving all existing functionality.
    """
    
    def __init__(self, config: Optional[CacheIntegrationConfig] = None):
        self.logger = logging.getLogger("kari.integrated_cache_system")
        self.config = config or CacheIntegrationConfig()
        
        # Core smart cache manager
        self.smart_cache_manager = get_smart_cache_manager()
        
        # Integration state
        self.integrated_components: Dict[str, Any] = {}
        self.cache_hooks: Dict[str, List[Callable]] = {}
        self.metrics = CacheIntegrationMetrics()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Cache warming
        self._warming_queue: List[Dict[str, Any]] = []
        self._warming_task: Optional[asyncio.Task] = None
        
        # Existing cache compatibility
        self.legacy_caches: Dict[str, Any] = {}
        
        self.logger.info("Integrated Cache System initialized")
    
    def register_legacy_cache(self, name: str, cache_instance: Any):
        """Register existing cache instances for integration."""
        try:
            self.legacy_caches[name] = cache_instance
            self.logger.info(f"Registered legacy cache: {name}")
        except Exception as e:
            self.logger.error(f"Failed to register legacy cache {name}: {e}")
    
    def add_cache_hook(self, component: str, hook: Callable):
        """Add cache hook for component integration."""
        if component not in self.cache_hooks:
            self.cache_hooks[component] = []
        self.cache_hooks[component].append(hook)
        self.logger.debug(f"Added cache hook for {component}")
    
    async def integrate_with_flow_manager(self, flow_manager: Any) -> Any:
        """
        Integrate caching with FlowManager without disrupting execution.
        
        This creates a transparent wrapper that adds caching to flow execution
        while preserving all existing FlowManager functionality.
        """
        if not self.config.enable_flow_manager_caching:
            return flow_manager
        
        try:
            # Create wrapper class that preserves FlowManager interface
            class CachedFlowManager:
                def __init__(self, original_flow_manager, cache_system):
                    self._original = original_flow_manager
                    self._cache_system = cache_system
                    
                    # Copy all attributes from original
                    for attr_name in dir(original_flow_manager):
                        if not attr_name.startswith('_'):
                            try:
                                attr_value = getattr(original_flow_manager, attr_name)
                                if not callable(attr_value):
                                    setattr(self, attr_name, attr_value)
                            except Exception:
                                pass
                
                def __getattr__(self, name):
                    """Delegate to original FlowManager."""
                    attr = getattr(self._original, name)
                    
                    if callable(attr) and name == 'execute_flow':
                        return self._cached_execute_flow
                    else:
                        return attr
                
                async def _cached_execute_flow(self, flow_type, input_data):
                    """Cached version of execute_flow."""
                    start_time = time.time()
                    
                    # Generate cache key
                    cache_key = self._cache_system._generate_flow_cache_key(flow_type, input_data)
                    
                    # Check cache first
                    cached_result = await self._cache_system.smart_cache_manager.get_cached_response(
                        cache_key, {"flow_type": str(flow_type)}
                    )
                    
                    if cached_result:
                        self._cache_system._update_metrics(hit=True, response_time=time.time() - start_time)
                        self._cache_system.logger.debug(f"Cache hit for flow {flow_type}")
                        return cached_result.response
                    
                    # Execute original flow
                    try:
                        result = await self._original.execute_flow(flow_type, input_data)
                        
                        # Cache the result
                        await self._cache_system.smart_cache_manager.cache_response(
                            cache_key,
                            result,
                            {"flow_type": str(flow_type)},
                            ttl_seconds=self._cache_system.config.cache_ttl_seconds
                        )
                        
                        self._cache_system._update_metrics(hit=False, response_time=time.time() - start_time)
                        self._cache_system.logger.debug(f"Cached result for flow {flow_type}")
                        
                        return result
                        
                    except Exception as e:
                        self._cache_system._update_metrics(hit=False, response_time=time.time() - start_time)
                        raise
            
            wrapped_flow_manager = CachedFlowManager(flow_manager, self)
            self.integrated_components["flow_manager"] = wrapped_flow_manager
            
            self.logger.info("FlowManager integrated with caching system")
            return wrapped_flow_manager
            
        except Exception as e:
            self.logger.error(f"Failed to integrate FlowManager with caching: {e}")
            return flow_manager
    
    async def integrate_with_decision_engine(self, decision_engine: Any) -> Any:
        """
        Integrate caching with DecisionEngine while preserving reasoning logic.
        """
        if not self.config.enable_decision_engine_caching:
            return decision_engine
        
        try:
            class CachedDecisionEngine:
                def __init__(self, original_decision_engine, cache_system):
                    self._original = original_decision_engine
                    self._cache_system = cache_system
                    
                    # Copy all attributes from original
                    for attr_name in dir(original_decision_engine):
                        if not attr_name.startswith('_'):
                            try:
                                attr_value = getattr(original_decision_engine, attr_name)
                                if not callable(attr_value):
                                    setattr(self, attr_name, attr_value)
                            except Exception:
                                pass
                
                def __getattr__(self, name):
                    """Delegate to original DecisionEngine."""
                    attr = getattr(self._original, name)
                    
                    if callable(attr) and name in ['decide_action', 'analyze_intent']:
                        return self._create_cached_method(name, attr)
                    else:
                        return attr
                
                def _create_cached_method(self, method_name: str, original_method: Callable):
                    """Create cached version of a method."""
                    async def cached_method(*args, **kwargs):
                        start_time = time.time()
                        
                        # Generate cache key
                        cache_key = self._cache_system._generate_decision_cache_key(
                            method_name, args, kwargs
                        )
                        
                        # Check cache
                        cached_result = await self._cache_system.smart_cache_manager.get_cached_response(
                            cache_key, {"method": method_name}
                        )
                        
                        if cached_result:
                            self._cache_system._update_metrics(hit=True, response_time=time.time() - start_time)
                            return cached_result.response
                        
                        # Execute original method
                        try:
                            result = await original_method(*args, **kwargs)
                            
                            # Cache the result
                            await self._cache_system.smart_cache_manager.cache_response(
                                cache_key,
                                result,
                                {"method": method_name},
                                ttl_seconds=self._cache_system.config.cache_ttl_seconds
                            )
                            
                            self._cache_system._update_metrics(hit=False, response_time=time.time() - start_time)
                            return result
                            
                        except Exception as e:
                            self._cache_system._update_metrics(hit=False, response_time=time.time() - start_time)
                            raise
                    
                    return cached_method
            
            wrapped_decision_engine = CachedDecisionEngine(decision_engine, self)
            self.integrated_components["decision_engine"] = wrapped_decision_engine
            
            self.logger.info("DecisionEngine integrated with caching system")
            return wrapped_decision_engine
            
        except Exception as e:
            self.logger.error(f"Failed to integrate DecisionEngine with caching: {e}")
            return decision_engine
    
    async def integrate_with_small_language_model_service(self, small_language_model_service: Any) -> Any:
        """
        Integrate caching with SmallLanguageModel service while preserving scaffolding functionality.
        """
        if not self.config.enable_small_language_model_caching:
            return small_language_model_service
        
        try:
            class CachedSmallLanguageModelService:
                def __init__(self, original_service, cache_system):
                    self._original = original_service
                    self._cache_system = cache_system
                    
                    # Copy all attributes from original
                    for attr_name in dir(original_service):
                        if not attr_name.startswith('_'):
                            try:
                                attr_value = getattr(original_service, attr_name)
                                if not callable(attr_value):
                                    setattr(self, attr_name, attr_value)
                            except Exception:
                                pass
                
                def __getattr__(self, name):
                    """Delegate to original SmallLanguageModel service."""
                    attr = getattr(self._original, name)
                    
                    if callable(attr) and name in [
                        'generate_scaffold', 'generate_outline', 'generate_short_fill', 'summarize_context'
                    ]:
                        return self._create_cached_method(name, attr)
                    else:
                        return attr
                
                def _create_cached_method(self, method_name: str, original_method: Callable):
                    """Create cached version of a method."""
                    async def cached_method(*args, **kwargs):
                        start_time = time.time()
                        
                        # Generate cache key
                        cache_key = self._cache_system._generate_small_language_model_cache_key(
                            method_name, args, kwargs
                        )
                        
                        # Check cache
                        cached_result = await self._cache_system.smart_cache_manager.get_cached_response(
                            cache_key, {"method": method_name, "service": "small_language_model"}
                        )
                        
                        if cached_result:
                            self._cache_system._update_metrics(hit=True, response_time=time.time() - start_time)
                            return cached_result.response
                        
                        # Execute original method
                        try:
                            result = await original_method(*args, **kwargs)
                            
                            # Cache the result
                            await self._cache_system.smart_cache_manager.cache_response(
                                cache_key,
                                result,
                                {"method": method_name, "service": "small_language_model"},
                                ttl_seconds=self._cache_system.config.cache_ttl_seconds
                            )
                            
                            self._cache_system._update_metrics(hit=False, response_time=time.time() - start_time)
                            return result
                            
                        except Exception as e:
                            self._cache_system._update_metrics(hit=False, response_time=time.time() - start_time)
                            raise
                    
                    return cached_method
            
            wrapped_service = CachedSmallLanguageModelService(small_language_model_service, self)
            self.integrated_components["small_language_model_service"] = wrapped_service
            
            self.logger.info("SmallLanguageModel service integrated with caching system")
            return wrapped_service
            
        except Exception as e:
            self.logger.error(f"Failed to integrate SmallLanguageModel service with caching: {e}")
            return small_language_model_service
    
    def _generate_flow_cache_key(self, flow_type: Any, input_data: Any) -> str:
        """Generate cache key for flow execution."""
        try:
            key_data = f"flow:{flow_type}:{hash(str(input_data))}"
            return hashlib.md5(key_data.encode()).hexdigest()
        except Exception:
            return f"flow:{flow_type}:{int(time.time())}"
    
    def _generate_decision_cache_key(self, method_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key for decision engine methods."""
        try:
            key_data = f"decision:{method_name}:{hash(str(args))}:{hash(str(kwargs))}"
            return hashlib.md5(key_data.encode()).hexdigest()
        except Exception:
            return f"decision:{method_name}:{int(time.time())}"
    
    def _generate_small_language_model_cache_key(self, method_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key for SmallLanguageModel methods."""
        try:
            # For SmallLanguageModel, include the text content in the key for better cache hits
            text_content = ""
            if args and len(args) > 0:
                text_content = str(args[0])[:100]  # First 100 chars of text
            
            key_data = f"small_language_model:{method_name}:{text_content}:{hash(str(kwargs))}"
            return hashlib.md5(key_data.encode()).hexdigest()
        except Exception:
            return f"small_language_model:{method_name}:{int(time.time())}"
    
    def _update_metrics(self, hit: bool, response_time: float):
        """Update cache integration metrics."""
        with self._lock:
            self.metrics.total_requests += 1
            
            if hit:
                self.metrics.cache_hits += 1
            else:
                self.metrics.cache_misses += 1
            
            # Update hit rate
            self.metrics.hit_rate = self.metrics.cache_hits / self.metrics.total_requests
            
            # Update average response time
            if self.metrics.average_response_time_ms == 0:
                self.metrics.average_response_time_ms = response_time * 1000
            else:
                self.metrics.average_response_time_ms = (
                    self.metrics.average_response_time_ms + (response_time * 1000)
                ) / 2
    
    async def warm_cache_for_common_operations(self):
        """Warm cache with common operations."""
        if not self.config.cache_warming_enabled:
            return
        
        try:
            # Common decision engine operations
            common_intents = [
                "What's the weather?",
                "What time is it?",
                "Check my email",
                "Hello",
                "How are you?"
            ]
            
            # Warm cache with common queries (if decision engine is integrated)
            if "decision_engine" in self.integrated_components:
                decision_engine = self.integrated_components["decision_engine"]
                
                for intent in common_intents:
                    try:
                        # This will cache the intent analysis
                        await decision_engine.analyze_intent(intent, {})
                        self.metrics.cache_warmings += 1
                    except Exception as e:
                        self.logger.debug(f"Cache warming failed for intent '{intent}': {e}")
            
            self.logger.info(f"Cache warming completed: {self.metrics.cache_warmings} operations")
            
        except Exception as e:
            self.logger.error(f"Cache warming failed: {e}")
    
    async def invalidate_related_cache(self, context: Dict[str, Any]):
        """Invalidate cache entries related to specific context."""
        try:
            # Use smart cache manager's intelligent invalidation
            invalidated_count = await self.smart_cache_manager.invalidate_by_context(context)
            
            with self._lock:
                self.metrics.cache_invalidations += invalidated_count
            
            self.logger.debug(f"Invalidated {invalidated_count} cache entries for context: {context}")
            
        except Exception as e:
            self.logger.error(f"Cache invalidation failed: {e}")
    
    def get_integration_metrics(self) -> Dict[str, Any]:
        """Get comprehensive integration metrics."""
        with self._lock:
            return {
                "total_requests": self.metrics.total_requests,
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "hit_rate": self.metrics.hit_rate,
                "cache_invalidations": self.metrics.cache_invalidations,
                "cache_warmings": self.metrics.cache_warmings,
                "average_response_time_ms": self.metrics.average_response_time_ms,
                "integrated_components": list(self.integrated_components.keys()),
                "legacy_caches": list(self.legacy_caches.keys()),
                "cache_hooks": {comp: len(hooks) for comp, hooks in self.cache_hooks.items()},
                "config": {
                    "flow_manager_caching": self.config.enable_flow_manager_caching,
                    "decision_engine_caching": self.config.enable_decision_engine_caching,
                    "small_language_model_caching": self.config.enable_small_language_model_caching,
                    "cache_ttl_seconds": self.config.cache_ttl_seconds,
                    "cache_warming_enabled": self.config.cache_warming_enabled
                }
            }
    
    async def optimize_cache_performance(self):
        """Optimize cache performance based on usage patterns."""
        try:
            # Get cache statistics from smart cache manager
            cache_stats = await self.smart_cache_manager.get_cache_statistics()
            
            # Adjust TTL based on hit rates
            if cache_stats.hit_rate > 0.8:
                # High hit rate, increase TTL
                self.config.cache_ttl_seconds = min(self.config.cache_ttl_seconds * 1.2, 7200.0)
            elif cache_stats.hit_rate < 0.3:
                # Low hit rate, decrease TTL
                self.config.cache_ttl_seconds = max(self.config.cache_ttl_seconds * 0.8, 300.0)
            
            # Trigger cache cleanup if needed
            if cache_stats.cache_size_mb > self.config.max_cache_size_mb:
                await self.smart_cache_manager.cleanup_expired_entries()
            
            self.logger.debug(f"Cache performance optimized: TTL={self.config.cache_ttl_seconds}s")
            
        except Exception as e:
            self.logger.error(f"Cache performance optimization failed: {e}")

# Global instance
_integrated_cache_system: Optional[IntegratedCacheSystem] = None
_cache_lock = threading.RLock()

def get_integrated_cache_system(config: Optional[CacheIntegrationConfig] = None) -> IntegratedCacheSystem:
    """Get the global integrated cache system instance."""
    global _integrated_cache_system
    if _integrated_cache_system is None:
        with _cache_lock:
            if _integrated_cache_system is None:
                _integrated_cache_system = IntegratedCacheSystem(config)
    return _integrated_cache_system

async def initialize_integrated_cache_system(config: Optional[CacheIntegrationConfig] = None):
    """Initialize the integrated cache system."""
    cache_system = get_integrated_cache_system(config)
    await cache_system.warm_cache_for_common_operations()
    return cache_system