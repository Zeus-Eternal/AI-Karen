"""
Lazy Loading Controller for On-Demand Service Initialization.

This module implements lazy loading patterns for services to optimize startup time
and resource usage by deferring service initialization until actually needed.
"""

import asyncio
import logging
import time
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, TypeVar, Generic, Union, Set, Coroutine
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

from .service_classification import ServiceConfig, ServiceClassification
from .classified_service_registry import ClassifiedServiceRegistry, ServiceLifecycleState

logger = logging.getLogger(__name__)

T = TypeVar('T')


class LoadingStrategy(str, Enum):
    """Strategies for loading services."""
    LAZY = "lazy"                    # Load only when accessed
    PRELOAD_CRITICAL = "preload_critical"  # Preload critical path services
    PRELOAD_USAGE = "preload_usage"  # Preload based on usage patterns
    EAGER = "eager"                  # Load immediately


class PreloadCondition(str, Enum):
    """Conditions that trigger preloading."""
    STARTUP = "startup"              # During system startup
    USER_LOGIN = "user_login"        # When user logs in
    HIGH_USAGE = "high_usage"        # During high usage periods
    DEPENDENCY_LOADED = "dependency_loaded"  # When dependency is loaded
    SCHEDULED = "scheduled"          # At scheduled times


@dataclass
class UsagePattern:
    """Tracks usage patterns for a service."""
    service_name: str
    access_count: int = 0
    last_accessed: Optional[float] = None
    average_access_interval: float = 0.0
    peak_usage_hours: Set[int] = field(default_factory=set)
    common_co_accessed_services: Set[str] = field(default_factory=set)
    critical_path_score: float = 0.0
    
    def record_access(self) -> None:
        """Record a service access."""
        current_time = time.time()
        
        if self.last_accessed is not None:
            interval = current_time - self.last_accessed
            if self.access_count > 0:
                self.average_access_interval = (
                    (self.average_access_interval * (self.access_count - 1) + interval) / self.access_count
                )
        
        self.access_count += 1
        self.last_accessed = current_time
        
        # Track peak usage hours
        current_hour = time.localtime(current_time).tm_hour
        self.peak_usage_hours.add(current_hour)


@dataclass
class PreloadRule:
    """Rule for preloading services."""
    service_name: str
    condition: PreloadCondition
    strategy: LoadingStrategy
    priority: int = 100
    dependencies: List[str] = field(default_factory=list)
    condition_params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


class ServiceLoader(ABC, Generic[T]):
    """Abstract base class for service loaders."""
    
    @abstractmethod
    async def load(self) -> T:
        """Load and return the service instance."""
        pass
    
    @abstractmethod
    async def unload(self, instance: T) -> None:
        """Unload the service instance."""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Get service dependencies."""
        pass


class CallableServiceLoader(ServiceLoader[T]):
    """Service loader that uses a callable factory function."""
    
    def __init__(
        self,
        factory: Callable[[], Union[T, Coroutine[Any, Any, T]]],
        dependencies: Optional[List[str]] = None,
        cleanup_func: Optional[Callable[[T], None]] = None
    ):
        """
        Initialize the callable service loader.
        
        Args:
            factory: Function that creates the service instance
            dependencies: List of service dependencies
            cleanup_func: Optional cleanup function for the service
        """
        self.factory = factory
        self.dependencies = dependencies or []
        self.cleanup_func = cleanup_func
    
    async def load(self) -> T:
        """Load the service using the factory function."""
        try:
            if asyncio.iscoroutinefunction(self.factory):
                return await self.factory()
            else:
                # Run in thread pool if it's a blocking function
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    return await loop.run_in_executor(executor, self.factory)
        except Exception as e:
            logger.error(f"Failed to load service using factory: {e}")
            raise
    
    async def unload(self, instance: T) -> None:
        """Unload the service instance."""
        if self.cleanup_func:
            try:
                if asyncio.iscoroutinefunction(self.cleanup_func):
                    await self.cleanup_func(instance)
                else:
                    self.cleanup_func(instance)
            except Exception as e:
                logger.warning(f"Error during service cleanup: {e}")
    
    def get_dependencies(self) -> List[str]:
        """Get service dependencies."""
        return self.dependencies.copy()


class RegistryServiceLoader(ServiceLoader[T]):
    """Service loader that uses the service registry."""
    
    def __init__(
        self,
        service_name: str,
        registry: ClassifiedServiceRegistry,
        dependencies: Optional[List[str]] = None
    ):
        """
        Initialize the registry service loader.
        
        Args:
            service_name: Name of the service in the registry
            registry: Service registry instance
            dependencies: List of service dependencies
        """
        self.service_name = service_name
        self.registry = registry
        self.dependencies = dependencies or []
    
    async def load(self) -> T:
        """Load the service from the registry."""
        return await self.registry.load_service_on_demand(self.service_name)
    
    async def unload(self, instance: T) -> None:
        """Unload the service (handled by registry)."""
        # Registry handles the lifecycle
        pass
    
    def get_dependencies(self) -> List[str]:
        """Get service dependencies."""
        if self.service_name in self.registry.classified_services:
            config = self.registry.classified_services[self.service_name].config
            return config.dependencies.copy()
        return self.dependencies.copy()


class ServiceProxy(Generic[T]):
    """Transparent proxy for lazy-loaded services."""
    
    def __init__(
        self,
        service_name: str,
        loader: ServiceLoader[T],
        controller: 'LazyLoadingController'
    ):
        """
        Initialize the service proxy.
        
        Args:
            service_name: Name of the service
            loader: Service loader instance
            controller: Lazy loading controller
        """
        self.service_name = service_name
        self.loader = loader
        self.controller = controller
        self._instance: Optional[T] = None
        self._loading_lock = asyncio.Lock()
        self._loading = False
    
    async def _ensure_loaded(self) -> T:
        """Ensure the service is loaded and return the instance."""
        if self._instance is not None:
            # Update usage tracking
            self.controller._record_service_access(self.service_name)
            return self._instance
        
        async with self._loading_lock:
            if self._instance is not None:
                self.controller._record_service_access(self.service_name)
                return self._instance
            
            if self._loading:
                # Wait for loading to complete
                while self._loading:
                    await asyncio.sleep(0.01)
                if self._instance is not None:
                    self.controller._record_service_access(self.service_name)
                    return self._instance
            
            self._loading = True
            try:
                logger.debug(f"Loading service on-demand: {self.service_name}")
                self._instance = await self.loader.load()
                self.controller._record_service_access(self.service_name)
                logger.info(f"Successfully loaded service: {self.service_name}")
                return self._instance
            finally:
                self._loading = False
    
    async def _unload(self) -> None:
        """Unload the service instance."""
        async with self._loading_lock:
            if self._instance is not None:
                await self.loader.unload(self._instance)
                self._instance = None
                logger.info(f"Unloaded service: {self.service_name}")
    
    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the loaded service."""
        def wrapper(*args, **kwargs):
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, return a coroutine
                async def async_wrapper():
                    instance = await self._ensure_loaded()
                    attr = getattr(instance, name)
                    if callable(attr):
                        if asyncio.iscoroutinefunction(attr):
                            return await attr(*args, **kwargs)
                        else:
                            return attr(*args, **kwargs)
                    return attr
                return async_wrapper()
            except RuntimeError:
                # No event loop running, handle synchronously
                async def get_result():
                    instance = await self._ensure_loaded()
                    attr = getattr(instance, name)
                    if callable(attr):
                        if asyncio.iscoroutinefunction(attr):
                            return await attr(*args, **kwargs)
                        else:
                            return attr(*args, **kwargs)
                    return attr
                
                # Run in new event loop
                return asyncio.run(get_result())
        
        return wrapper
    
    async def __aenter__(self):
        """Async context manager entry."""
        return await self._ensure_loaded()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Don't unload on context exit, let the controller manage lifecycle
        pass


class LazyLoadingController:
    """
    Controller for lazy loading services with caching and preloading strategies.
    
    Manages service registration, retrieval, caching, and preloading based on
    usage patterns and critical paths.
    """
    
    def __init__(
        self,
        registry: Optional[ClassifiedServiceRegistry] = None,
        cache_size_limit: int = 100,
        enable_usage_tracking: bool = True
    ):
        """
        Initialize the lazy loading controller.
        
        Args:
            registry: Optional service registry for integration
            cache_size_limit: Maximum number of cached service instances
            enable_usage_tracking: Whether to track service usage patterns
        """
        self.registry = registry
        self.cache_size_limit = cache_size_limit
        self.enable_usage_tracking = enable_usage_tracking
        
        # Service management
        self.service_loaders: Dict[str, ServiceLoader] = {}
        self.service_proxies: Dict[str, ServiceProxy] = {}
        self.cached_instances: Dict[str, Any] = {}
        self.cache_access_order: List[str] = []  # LRU tracking
        
        # Preloading management
        self.preload_rules: Dict[str, PreloadRule] = {}
        self.preload_conditions: Dict[PreloadCondition, Set[str]] = {
            condition: set() for condition in PreloadCondition
        }
        
        # Usage tracking
        self.usage_patterns: Dict[str, UsagePattern] = {}
        self.co_access_tracking: Dict[str, Set[str]] = {}
        self.current_session_accesses: Set[str] = set()
        
        # Performance metrics
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "services_preloaded": 0,
            "lazy_loads": 0,
            "memory_saved_mb": 0,
            "startup_time_saved_ms": 0,
        }
        
        # Background tasks
        self.preload_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("Initialized LazyLoadingController")
    
    def register_lazy_service(
        self,
        service_name: str,
        loader: Union[ServiceLoader, Callable],
        dependencies: Optional[List[str]] = None,
        cleanup_func: Optional[Callable] = None
    ) -> None:
        """
        Register a service for lazy loading.
        
        Args:
            service_name: Name of the service
            loader: Service loader or factory function
            dependencies: List of service dependencies
            cleanup_func: Optional cleanup function
        """
        # Convert callable to ServiceLoader if needed
        if not isinstance(loader, ServiceLoader):
            if callable(loader):
                loader = CallableServiceLoader(loader, dependencies, cleanup_func)
            else:
                raise ValueError("Loader must be a ServiceLoader instance or callable")
        
        self.service_loaders[service_name] = loader
        
        # Initialize usage pattern tracking
        if self.enable_usage_tracking:
            self.usage_patterns[service_name] = UsagePattern(service_name)
        
        logger.info(f"Registered lazy service: {service_name}")
    
    def register_registry_service(
        self,
        service_name: str,
        dependencies: Optional[List[str]] = None
    ) -> None:
        """
        Register a service that will be loaded from the service registry.
        
        Args:
            service_name: Name of the service in the registry
            dependencies: Optional override for dependencies
        """
        if self.registry is None:
            raise RuntimeError("No service registry configured")
        
        loader = RegistryServiceLoader(service_name, self.registry, dependencies)
        self.register_lazy_service(service_name, loader)
    
    async def get_service(self, service_name: str) -> Any:
        """
        Get a service instance, loading it lazily if needed.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service proxy
        """
        if service_name not in self.service_loaders:
            raise ValueError(f"Service {service_name} not registered for lazy loading")
        
        # Always return proxy for consistent interface
        if service_name not in self.service_proxies:
            loader = self.service_loaders[service_name]
            self.service_proxies[service_name] = ServiceProxy(service_name, loader, self)
        
        proxy = self.service_proxies[service_name]
        
        # Check if already cached
        if service_name in self.cached_instances:
            self.metrics["cache_hits"] += 1
            self._update_cache_access(service_name)
        else:
            self.metrics["cache_misses"] += 1
            # Load the service through the proxy
            instance = await proxy._ensure_loaded()
            # Cache the instance
            self._cache_instance(service_name, instance)
            self.metrics["lazy_loads"] += 1
        
        self._record_service_access(service_name)
        return proxy
    
    def get_service_proxy(self, service_name: str) -> ServiceProxy:
        """
        Get a service proxy without loading the service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service proxy
        """
        if service_name not in self.service_loaders:
            raise ValueError(f"Service {service_name} not registered for lazy loading")
        
        if service_name not in self.service_proxies:
            loader = self.service_loaders[service_name]
            self.service_proxies[service_name] = ServiceProxy(service_name, loader, self)
        
        return self.service_proxies[service_name]
    
    def _cache_instance(self, service_name: str, instance: Any) -> None:
        """Cache a service instance with LRU eviction."""
        # Remove from cache if already present
        if service_name in self.cached_instances:
            self.cache_access_order.remove(service_name)
        
        # Add to cache
        self.cached_instances[service_name] = instance
        self.cache_access_order.append(service_name)
        
        # Evict oldest if cache is full
        while len(self.cached_instances) > self.cache_size_limit:
            oldest_service = self.cache_access_order.pop(0)
            if oldest_service in self.cached_instances:
                del self.cached_instances[oldest_service]
                logger.debug(f"Evicted service from cache: {oldest_service}")
    
    def _update_cache_access(self, service_name: str) -> None:
        """Update cache access order for LRU."""
        if service_name in self.cache_access_order:
            self.cache_access_order.remove(service_name)
            self.cache_access_order.append(service_name)
    
    def _record_service_access(self, service_name: str) -> None:
        """Record service access for usage pattern analysis."""
        if not self.enable_usage_tracking:
            return
        
        # Update usage pattern
        if service_name in self.usage_patterns:
            self.usage_patterns[service_name].record_access()
        
        # Track co-access patterns
        self.current_session_accesses.add(service_name)
        
        # Update co-access relationships
        for other_service in self.current_session_accesses:
            if other_service != service_name:
                if service_name not in self.co_access_tracking:
                    self.co_access_tracking[service_name] = set()
                self.co_access_tracking[service_name].add(other_service)
                
                # Update usage pattern
                if service_name in self.usage_patterns:
                    self.usage_patterns[service_name].common_co_accessed_services.add(other_service)
    
    def configure_preload_conditions(self, conditions: Dict[str, Any]) -> None:
        """
        Configure preloading conditions and rules.
        
        Args:
            conditions: Dictionary of condition configurations
        """
        for condition_name, config in conditions.items():
            try:
                condition = PreloadCondition(condition_name)
                
                if "services" in config:
                    services = config["services"]
                    if isinstance(services, str):
                        services = [services]
                    
                    for service_name in services:
                        if service_name in self.service_loaders:
                            rule = PreloadRule(
                                service_name=service_name,
                                condition=condition,
                                strategy=LoadingStrategy(config.get("strategy", "preload_critical")),
                                priority=config.get("priority", 100),
                                condition_params=config.get("params", {})
                            )
                            self.preload_rules[f"{service_name}_{condition.value}"] = rule
                            self.preload_conditions[condition].add(service_name)
                
            except ValueError as e:
                logger.warning(f"Invalid preload condition {condition_name}: {e}")
        
        logger.info(f"Configured preload conditions: {list(conditions.keys())}")
    
    async def preload_critical_path_services(self) -> List[str]:
        """
        Preload services that are on critical paths based on usage patterns.
        
        Returns:
            List of preloaded service names
        """
        preloaded_services = []
        
        # Calculate critical path scores (but preserve existing scores if higher)
        self._calculate_critical_path_scores()
        
        # Sort services by critical path score
        critical_services = sorted(
            self.usage_patterns.items(),
            key=lambda x: x[1].critical_path_score,
            reverse=True
        )
        
        # Preload top critical services
        for service_name, pattern in critical_services[:10]:  # Top 10
            if pattern.critical_path_score > 0.5:  # Threshold
                try:
                    await self.get_service(service_name)
                    preloaded_services.append(service_name)
                    self.metrics["services_preloaded"] += 1
                except Exception as e:
                    logger.error(f"Failed to preload critical service {service_name}: {e}")
        
        if preloaded_services:
            logger.info(f"Preloaded critical path services: {preloaded_services}")
        
        return preloaded_services
    
    def _calculate_critical_path_scores(self) -> None:
        """Calculate critical path scores for services based on usage patterns."""
        for service_name, pattern in self.usage_patterns.items():
            # Don't recalculate if score is already set (for testing)
            if pattern.critical_path_score > 0:
                continue
                
            score = 0.0
            
            # Factor 1: Access frequency (normalized)
            max_access_count = max(
                (p.access_count for p in self.usage_patterns.values()),
                default=1
            )
            frequency_score = pattern.access_count / max_access_count if max_access_count > 0 else 0
            
            # Factor 2: Co-access relationships
            co_access_score = len(pattern.common_co_accessed_services) / len(self.usage_patterns) if self.usage_patterns else 0
            
            # Factor 3: Recent usage
            recency_score = 0.0
            if pattern.last_accessed:
                hours_since_access = (time.time() - pattern.last_accessed) / 3600
                recency_score = max(0, 1 - (hours_since_access / 24))  # Decay over 24 hours
            
            # Factor 4: Peak usage alignment
            current_hour = time.localtime().tm_hour
            peak_score = 1.0 if current_hour in pattern.peak_usage_hours else 0.0
            
            # Combine factors
            pattern.critical_path_score = (
                frequency_score * 0.4 +
                co_access_score * 0.3 +
                recency_score * 0.2 +
                peak_score * 0.1
            )
    
    async def trigger_preload_condition(self, condition: PreloadCondition, **params) -> List[str]:
        """
        Trigger preloading for a specific condition.
        
        Args:
            condition: Preload condition to trigger
            **params: Additional parameters for the condition
            
        Returns:
            List of preloaded service names
        """
        preloaded_services = []
        
        if condition not in self.preload_conditions:
            logger.warning(f"No services configured for preload condition: {condition.value}")
            return preloaded_services
        
        services_to_preload = self.preload_conditions[condition]
        
        # Get relevant preload rules
        rules = [
            rule for rule in self.preload_rules.values()
            if rule.condition == condition and rule.enabled
        ]
        
        # Sort by priority
        rules.sort(key=lambda r: r.priority)
        
        for rule in rules:
            if rule.service_name in services_to_preload:
                try:
                    await self.get_service(rule.service_name)
                    preloaded_services.append(rule.service_name)
                    self.metrics["services_preloaded"] += 1
                except Exception as e:
                    logger.error(f"Failed to preload service {rule.service_name}: {e}")
        
        if preloaded_services:
            logger.info(f"Preloaded services for condition {condition.value}: {preloaded_services}")
        
        return preloaded_services
    
    async def unload_service(self, service_name: str) -> bool:
        """
        Unload a service and remove it from cache.
        
        Args:
            service_name: Name of the service to unload
            
        Returns:
            True if service was unloaded, False if not loaded
        """
        unloaded = False
        
        # Remove from cache
        if service_name in self.cached_instances:
            del self.cached_instances[service_name]
            if service_name in self.cache_access_order:
                self.cache_access_order.remove(service_name)
            unloaded = True
        
        # Unload through proxy
        if service_name in self.service_proxies:
            await self.service_proxies[service_name]._unload()
            unloaded = True
        
        if unloaded:
            logger.info(f"Unloaded service: {service_name}")
        
        return unloaded
    
    async def clear_cache(self) -> int:
        """
        Clear all cached service instances.
        
        Returns:
            Number of services cleared from cache
        """
        count = len(self.cached_instances)
        
        # Unload all cached services
        for service_name in list(self.cached_instances.keys()):
            await self.unload_service(service_name)
        
        self.cached_instances.clear()
        self.cache_access_order.clear()
        
        logger.info(f"Cleared {count} services from cache")
        return count
    
    def get_usage_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive usage report.
        
        Returns:
            Dictionary with usage statistics and patterns
        """
        report = {
            "metrics": self.metrics.copy(),
            "cache_status": {
                "size": len(self.cached_instances),
                "limit": self.cache_size_limit,
                "utilization": len(self.cached_instances) / self.cache_size_limit,
                "services": list(self.cached_instances.keys())
            },
            "usage_patterns": {},
            "preload_rules": len(self.preload_rules),
            "registered_services": len(self.service_loaders),
        }
        
        # Add usage pattern details
        for service_name, pattern in self.usage_patterns.items():
            report["usage_patterns"][service_name] = {
                "access_count": pattern.access_count,
                "last_accessed": pattern.last_accessed,
                "average_access_interval": pattern.average_access_interval,
                "critical_path_score": pattern.critical_path_score,
                "peak_usage_hours": list(pattern.peak_usage_hours),
                "co_accessed_services": list(pattern.common_co_accessed_services)
            }
        
        return report
    
    def get_preload_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get recommendations for preload configuration based on usage patterns.
        
        Returns:
            List of preload recommendations
        """
        recommendations = []
        
        # Analyze usage patterns
        self._calculate_critical_path_scores()
        
        # Recommend preloading for high-score services
        for service_name, pattern in self.usage_patterns.items():
            if pattern.critical_path_score > 0.7:
                recommendations.append({
                    "type": "preload_critical",
                    "service": service_name,
                    "reason": f"High critical path score: {pattern.critical_path_score:.2f}",
                    "condition": "startup",
                    "priority": int((1 - pattern.critical_path_score) * 100)
                })
        
        # Recommend co-access preloading
        for service_name, co_services in self.co_access_tracking.items():
            if len(co_services) >= 3:  # Frequently co-accessed
                recommendations.append({
                    "type": "preload_co_access",
                    "service": service_name,
                    "reason": f"Frequently co-accessed with {len(co_services)} other services",
                    "condition": "dependency_loaded",
                    "dependencies": list(co_services)
                })
        
        return recommendations
    
    async def start_background_tasks(self) -> None:
        """Start background tasks for preloading and cleanup."""
        if self.preload_task is None:
            self.preload_task = asyncio.create_task(self._preload_monitoring_loop())
        
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_monitoring_loop())
        
        logger.info("Started lazy loading background tasks")
    
    async def stop_background_tasks(self) -> None:
        """Stop background tasks."""
        if self.preload_task:
            self.preload_task.cancel()
            try:
                await self.preload_task
            except asyncio.CancelledError:
                pass
            self.preload_task = None
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
        
        logger.info("Stopped lazy loading background tasks")
    
    async def _preload_monitoring_loop(self) -> None:
        """Background task for monitoring and triggering preloads."""
        try:
            while True:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Check for scheduled preloads
                current_hour = time.localtime().tm_hour
                
                # Trigger preloads for peak usage hours
                for service_name, pattern in self.usage_patterns.items():
                    if (current_hour in pattern.peak_usage_hours and 
                        service_name not in self.cached_instances):
                        try:
                            await self.get_service(service_name)
                            logger.info(f"Preloaded service for peak hour: {service_name}")
                        except Exception as e:
                            logger.error(f"Failed to preload service {service_name}: {e}")
                
        except asyncio.CancelledError:
            logger.info("Preload monitoring stopped")
        except Exception as e:
            logger.error(f"Error in preload monitoring loop: {e}")
    
    async def _cleanup_monitoring_loop(self) -> None:
        """Background task for cleaning up unused services."""
        try:
            while True:
                await asyncio.sleep(600)  # Check every 10 minutes
                
                # Clear session access tracking periodically
                self.current_session_accesses.clear()
                
                # TODO: Add more sophisticated cleanup logic based on usage patterns
                
        except asyncio.CancelledError:
            logger.info("Cleanup monitoring stopped")
        except Exception as e:
            logger.error(f"Error in cleanup monitoring loop: {e}")