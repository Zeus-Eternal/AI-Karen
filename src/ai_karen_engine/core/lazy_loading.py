"""
Lazy Loading and Resource Management System for AI-Karen.
Implements on-demand service initialization and resource cleanup.
"""

import asyncio
import logging
import os
import threading
import time
import weakref
from typing import Dict, Any, Optional, Set, TypeVar, Generic, Callable
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

ServiceType = TypeVar('ServiceType')


class ServiceState(Enum):
    """Service lifecycle states."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    IDLE = "idle"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"
    ERROR = "error"


@dataclass
class ServiceMetrics:
    """Metrics for service usage and performance."""
    last_used: datetime
    usage_count: int
    initialization_time: float
    total_runtime: float
    memory_usage_mb: float
    cpu_usage_percent: float


class LazyService(Generic[ServiceType]):
    """
    Lazy wrapper for services that initializes only when needed.
    Includes automatic cleanup and resource monitoring.
    """
    
    def __init__(
        self,
        name: str,
        factory: Callable[[], ServiceType],
        idle_timeout: float = 300.0,  # 5 minutes
        cleanup_callback: Optional[Callable[[ServiceType], None]] = None,
        max_memory_mb: Optional[float] = None,
        priority: int = 1  # 1=low, 5=critical
    ):
        self.name = name
        self.factory = factory
        self.idle_timeout = idle_timeout
        self.cleanup_callback = cleanup_callback
        self.max_memory_mb = max_memory_mb
        self.priority = priority
        
        self._service: Optional[ServiceType] = None
        self._state = ServiceState.UNINITIALIZED
        self._lock = threading.RLock()
        self._metrics = ServiceMetrics(
            last_used=datetime.now(),
            usage_count=0,
            initialization_time=0.0,
            total_runtime=0.0,
            memory_usage_mb=0.0,
            cpu_usage_percent=0.0
        )
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def get(self) -> ServiceType:
        """Get the service, initializing if necessary."""
        async with self._get_lock():
            if self._service is None and self._state != ServiceState.ERROR:
                await self._initialize()
            
            if self._service is not None:
                self._metrics.last_used = datetime.now()
                self._metrics.usage_count += 1
                self._schedule_cleanup()
                return self._service
            else:
                raise RuntimeError(f"Service {self.name} failed to initialize")
    
    async def _initialize(self) -> None:
        """Initialize the service."""
        if self._state == ServiceState.INITIALIZING:
            return  # Already initializing
            
        self._state = ServiceState.INITIALIZING
        start_time = time.time()
        
        try:
            logger.info(f"🔧 Initializing lazy service: {self.name}")
            self._service = self.factory()
            
            # If service has async initialization
            if hasattr(self._service, 'initialize') and callable(getattr(self._service, 'initialize')):
                await self._service.initialize()
            
            self._metrics.initialization_time = time.time() - start_time
            self._state = ServiceState.READY
            
            logger.info(f"✅ Service {self.name} initialized in {self._metrics.initialization_time:.2f}s")
            
        except Exception as e:
            self._state = ServiceState.ERROR
            logger.error(f"❌ Failed to initialize service {self.name}: {e}")
            raise
    
    def _schedule_cleanup(self) -> None:
        """Schedule cleanup after idle timeout."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        self._cleanup_task = asyncio.create_task(self._auto_cleanup())
    
    async def _auto_cleanup(self) -> None:
        """Automatically cleanup service after idle timeout."""
        try:
            await asyncio.sleep(self.idle_timeout)
            
            # Check if still idle
            time_since_use = (datetime.now() - self._metrics.last_used).total_seconds()
            if time_since_use >= self.idle_timeout and self._state == ServiceState.READY:
                await self.cleanup()
                
        except asyncio.CancelledError:
            pass  # Normal cancellation
    
    async def cleanup(self) -> None:
        """Cleanup the service."""
        async with self._get_lock():
            if self._service is not None and self._state != ServiceState.SHUTDOWN:
                self._state = ServiceState.SHUTTING_DOWN
                
                try:
                    logger.info(f"🧹 Cleaning up service: {self.name}")
                    
                    # Call custom cleanup if provided
                    if self.cleanup_callback:
                        self.cleanup_callback(self._service)
                    
                    # Call service cleanup if available
                    if hasattr(self._service, 'cleanup') and callable(getattr(self._service, 'cleanup')):
                        await self._service.cleanup()
                    
                    self._service = None
                    self._state = ServiceState.SHUTDOWN
                    
                    logger.info(f"✅ Service {self.name} cleaned up")
                    
                except Exception as e:
                    logger.error(f"❌ Error cleaning up service {self.name}: {e}")
    
    @asynccontextmanager
    async def _get_lock(self):
        """Async context manager for thread-safe operations."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._lock.acquire)
        try:
            yield
        finally:
            try:
                self._lock.release()
            except RuntimeError:
                # Lock may already be released if initialization raised.
                pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._service is not None and self._state == ServiceState.READY
    
    @property
    def state(self) -> ServiceState:
        """Get current service state."""
        return self._state
    
    @property
    def metrics(self) -> ServiceMetrics:
        """Get service metrics."""
        return self._metrics


class ResourceManager:
    """
    Manages system resources and automatically cleans up services
    when resource limits are exceeded.
    """
    
    def __init__(
        self,
        max_memory_mb: float = 2048,
        max_cpu_percent: float = 80.0,
        check_interval: float = 30.0
    ):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.check_interval = check_interval
        
        self._services: Dict[str, LazyService] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._enabled = True
    
    def register_service(self, service: LazyService) -> None:
        """Register a service for resource monitoring."""
        self._services[service.name] = service
        logger.debug(f"Registered service for resource monitoring: {service.name}")
    
    def unregister_service(self, name: str) -> None:
        """Unregister a service."""
        if name in self._services:
            del self._services[name]
            logger.debug(f"Unregistered service: {name}")
    
    async def start_monitoring(self) -> None:
        """Start resource monitoring."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitor_resources())
            logger.info("🔍 Resource monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None
            logger.info("🛑 Resource monitoring stopped")
    
    async def _monitor_resources(self) -> None:
        """Monitor system resources and cleanup if needed."""
        while self._enabled:
            try:
                await asyncio.sleep(self.check_interval)
                
                # Get current resource usage
                memory_usage = await self._get_memory_usage()
                cpu_usage = await self._get_cpu_usage()
                
                # Check if cleanup is needed
                if memory_usage > self.max_memory_mb or cpu_usage > self.max_cpu_percent:
                    logger.warning(f"🚨 Resource limits exceeded - Memory: {memory_usage:.1f}MB, CPU: {cpu_usage:.1f}%")
                    await self._cleanup_idle_services()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
    
    async def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    async def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 0.0
    
    async def _cleanup_idle_services(self) -> None:
        """Cleanup idle services based on priority and usage."""
        # Sort services by priority (low priority first) and last used time
        services_to_cleanup = []
        
        for service in self._services.values():
            if service.is_initialized:
                idle_time = (datetime.now() - service.metrics.last_used).total_seconds()
                services_to_cleanup.append((service, idle_time))
        
        # Sort by priority (ascending) then by idle time (descending)
        services_to_cleanup.sort(key=lambda x: (x[0].priority, -x[1]))
        
        # Cleanup services until resources are under limits
        cleaned_count = 0
        for service, idle_time in services_to_cleanup:
            if idle_time > 60:  # Only cleanup services idle for more than 1 minute - balanced approach
                await service.cleanup()
                cleaned_count += 1
                
                # Check if we're under limits now
                memory_usage = await self._get_memory_usage()
                cpu_usage = await self._get_cpu_usage()
                
                if memory_usage <= self.max_memory_mb * 0.8 and cpu_usage <= self.max_cpu_percent * 0.8:
                    break
        
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned up {cleaned_count} idle services to free resources")


class LazyServiceRegistry:
    """
    Registry for lazy services with automatic resource management.
    """
    
    def __init__(self):
        self._services: Dict[str, LazyService] = {}
        # Configure resource manager with balanced limits
        max_memory = float(os.getenv("KAREN_MAX_MEMORY_MB", "1536"))  # Default 1.5GB - balanced approach
        max_cpu = float(os.getenv("KAREN_MAX_CPU_PERCENT", "60.0"))   # Default 60% - less aggressive
        check_interval = float(os.getenv("KAREN_RESOURCE_CHECK_INTERVAL", "30.0"))  # Check every 30s - less frequent
        
        self._resource_manager = ResourceManager(
            max_memory_mb=max_memory,
            max_cpu_percent=max_cpu,
            check_interval=check_interval
        )
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the service registry."""
        if not self._initialized:
            await self._resource_manager.start_monitoring()
            self._initialized = True
            logger.info("🚀 Lazy service registry initialized")
    
    async def shutdown(self) -> None:
        """Shutdown all services and resource monitoring."""
        await self._resource_manager.stop_monitoring()
        
        # Cleanup all services
        cleanup_tasks = []
        for service in self._services.values():
            if service.is_initialized:
                cleanup_tasks.append(service.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self._services.clear()
        self._initialized = False
        logger.info("🛑 Lazy service registry shutdown complete")
    
    def register(
        self,
        name: str,
        factory: Callable[[], ServiceType],
        idle_timeout: float = 300.0,
        cleanup_callback: Optional[Callable[[ServiceType], None]] = None,
        max_memory_mb: Optional[float] = None,
        priority: int = 1
    ) -> LazyService[ServiceType]:
        """Register a new lazy service."""
        service = LazyService(
            name=name,
            factory=factory,
            idle_timeout=idle_timeout,
            cleanup_callback=cleanup_callback,
            max_memory_mb=max_memory_mb,
            priority=priority
        )
        
        self._services[name] = service
        self._resource_manager.register_service(service)
        
        logger.debug(f"Registered lazy service: {name}")
        return service
    
    def get_service(self, name: str) -> Optional[LazyService]:
        """Get a registered service."""
        return self._services.get(name)
    
    async def get_service_instance(self, name: str) -> Any:
        """Get an instance of a service, initializing if needed."""
        service = self.get_service(name)
        if service:
            return await service.get()
        else:
            raise KeyError(f"Service not registered: {name}")
    
    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """List all registered services and their status."""
        result = {}
        for name, service in self._services.items():
            result[name] = {
                "state": service.state.value,
                "is_initialized": service.is_initialized,
                "usage_count": service.metrics.usage_count,
                "last_used": service.metrics.last_used.isoformat(),
                "priority": service.priority
            }
        return result


# Global lazy service registry
lazy_registry = LazyServiceRegistry()


# Convenience functions for common services
def create_nlp_service_factory():
    """Factory for NLP service manager."""
    def factory():
        from ai_karen_engine.services.nlp_service_manager import NLPServiceManager
        return NLPServiceManager()
    return factory


def create_ai_orchestrator_factory():
    """Factory for AI orchestrator service."""

    def factory():
        from ai_karen_engine.core.services.base import ServiceConfig
        from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import (
            AIOrchestrator,
        )

        service = AIOrchestrator(
            ServiceConfig(name="ai_orchestrator", dependencies=[], config={})
        )
        return service

    return factory


def create_analytics_service_factory():
    """Factory for analytics service."""
    def factory():
        from ai_karen_engine.services.analytics_service import AnalyticsService
        return AnalyticsService()
    return factory


async def setup_lazy_services():
    """Setup all lazy services with appropriate configurations."""
    await lazy_registry.initialize()
    
    # Get timeout configurations from environment - balanced cleanup
    nlp_timeout = float(os.getenv("KAREN_NLP_IDLE_TIMEOUT", "120.0"))  # 2 minutes - balanced
    orchestrator_timeout = float(os.getenv("KAREN_ORCHESTRATOR_IDLE_TIMEOUT", "60.0"))  # 1 minute - balanced
    analytics_timeout = float(os.getenv("KAREN_ANALYTICS_IDLE_TIMEOUT", "30.0"))  # 30 seconds - balanced
    
    # Register NLP services (low priority, shorter timeout for memory efficiency)
    lazy_registry.register(
        name="nlp_service",
        factory=create_nlp_service_factory(),
        idle_timeout=nlp_timeout,
        priority=2,
        max_memory_mb=256  # Reduced from 512MB
    )
    
    # Register AI orchestrator (medium priority, aggressive cleanup)
    lazy_registry.register(
        name="ai_orchestrator",
        factory=create_ai_orchestrator_factory(),
        idle_timeout=orchestrator_timeout,
        priority=3
    )
    
    # Register analytics service (low priority, very aggressive cleanup)
    lazy_registry.register(
        name="analytics_service",
        factory=create_analytics_service_factory(),
        idle_timeout=analytics_timeout,
        priority=1
    )
    
    logger.info("✅ Lazy services configured")


async def cleanup_lazy_services():
    """Cleanup all lazy services."""
    await lazy_registry.shutdown()


class LazyServiceManager:
    """
    Main manager for lazy loading services and resource optimization.
    """
    
    def __init__(self):
        self.services: Dict[str, LazyService] = {}
        self.enabled = os.getenv("KARI_LAZY_LOADING", "false").lower() == "true"
        self.minimal_mode = os.getenv("KARI_MINIMAL_STARTUP", "false").lower() == "true"
        self.ultra_minimal = os.getenv("KARI_ULTRA_MINIMAL", "false").lower() == "true"
        self._initialized = False
        
    async def initialize(self):
        """Initialize the lazy service manager."""
        if self._initialized:
            return
            
        if self.enabled:
            await setup_lazy_services()
            logger.info("🚀 Lazy Service Manager initialized")
        else:
            logger.info("⚡ Lazy loading disabled, using eager initialization")
            
        self._initialized = True
    
    def get_service(self, name: str) -> Any:
        """Get a service, initializing it lazily if needed."""
        if not self.enabled:
            # Fall back to eager loading
            return self._get_eager_service(name)
            
        if name not in self.services:
            logger.warning(f"Service '{name}' not registered in lazy manager")
            return None
            
        return self.services[name].get()
    
    def _get_eager_service(self, name: str) -> Any:
        """Get service using eager initialization (fallback)."""
        # Import and create services directly for non-lazy mode
        if name == "nlp_service":
            from ai_karen_engine.services.nlp_service_manager import NLPServiceManager
            return NLPServiceManager()
        elif name == "ai_orchestrator":
            from ai_karen_engine.core.services.base import ServiceConfig
            from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import (
                AIOrchestrator,
            )

            return AIOrchestrator(
                ServiceConfig(name="ai_orchestrator", dependencies=[], config={})
            )
        elif name == "analytics_service":
            from ai_karen_engine.services.analytics_service import AnalyticsService
            return AnalyticsService()
        else:
            logger.warning(f"Unknown service: {name}")
            return None
    
    async def shutdown(self):
        """Shutdown all managed services."""
        await cleanup_lazy_services()
        logger.info("🛑 Lazy Service Manager shutdown complete")
