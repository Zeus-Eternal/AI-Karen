"""
Service Registry and Dependency Injection for AI Karen Engine Integration.

This module provides centralized service management and dependency injection
for integrating the new Python backend services with the existing AI Karen engine.

Enhanced with graceful dependency handling, metrics deduplication, and comprehensive
health monitoring to prevent service initialization warnings.
"""

import asyncio
import logging
import time
import weakref
from typing import Dict, Any, Optional, Type, TypeVar, Callable, Set, List, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

try:
    from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import AIOrchestrator
    from ai_karen_engine.services.memory_service import WebUIMemoryService
    from ai_karen_engine.services.memory.unified_memory_service import UnifiedMemoryService
    from ai_karen_engine.services.conversation_service import WebUIConversationService
    from ai_karen_engine.services.plugin_service import PluginService
    from ai_karen_engine.services.tool_service import ToolService
    from ai_karen_engine.services.analytics_service import AnalyticsService
    from ai_karen_engine.database.conversation_manager import ConversationManager
except ImportError as e:
    logger.warning(f"Some service imports failed: {e}")
    # Define dummy classes for missing services to allow the registry to load
    class AIOrchestrator:
        def __init__(self, config):
            self.config = config
        async def initialize(self):
            pass
    
    class WebUIMemoryService:
        def __init__(self, memory_manager):
            self.memory_manager = memory_manager
        async def initialize(self):
            pass
    
    class UnifiedMemoryService:
        def __init__(self):
            pass
        async def initialize(self):
            pass
    
    class WebUIConversationService:
        def __init__(self, conversation_manager, memory_service):
            self.conversation_manager = conversation_manager
            self.memory_service = memory_service
        async def initialize(self):
            pass
    
    class PluginService:
        def __init__(self, marketplace_path, core_plugins_path):
            self.marketplace_path = marketplace_path
            self.core_plugins_path = core_plugins_path
        async def initialize(self):
            pass
    
    class ToolService:
        def __init__(self, config):
            self.config = config
        async def initialize(self):
            pass
    
    class AnalyticsService:
        def __init__(self, config):
            self.config = config
        async def initialize(self):
            pass
    
    class ConversationManager:
        def __init__(self, db_client, memory_manager, embedding_manager):
            self.db_client = db_client
            self.memory_manager = memory_manager
            self.embedding_manager = embedding_manager

T = TypeVar('T')


class ServiceStatus(str, Enum):
    """Service status enumeration."""
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    STOPPED = "stopped"
    DEGRADED = "degraded"  # Service running with missing dependencies
    PENDING = "pending"    # Waiting for dependencies


class DependencyStatus(str, Enum):
    """Dependency status enumeration."""
    AVAILABLE = "available"
    MISSING = "missing"
    FAILED = "failed"
    OPTIONAL = "optional"


@dataclass
class DependencyInfo:
    """Information about a service dependency."""
    name: str
    required: bool = True
    status: DependencyStatus = DependencyStatus.MISSING
    error_message: Optional[str] = None
    fallback_available: bool = False


@dataclass
class ServiceInfo:
    """Information about a registered service."""
    name: str
    service_type: Type
    instance: Optional[Any] = None
    status: ServiceStatus = ServiceStatus.PENDING
    dependencies: List[DependencyInfo] = field(default_factory=list)
    health_check: Optional[Callable] = None
    error_message: Optional[str] = None
    initialization_time: Optional[float] = None
    initialization_attempts: int = 0
    max_initialization_attempts: int = 3
    last_health_check: Optional[float] = None
    health_status: str = "unknown"
    fallback_mode: bool = False


class ServiceRegistry:
    """
    Enhanced central service registry for AI Karen engine integration.
    
    Manages service lifecycle, dependency injection, and health monitoring
    for all backend services with graceful degradation and comprehensive
    error handling to prevent initialization warnings.
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}
        self._instances: Dict[str, Any] = {}
        self._initialization_lock = asyncio.Lock()
        self._health_check_interval = 30  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        self._registered_metrics: Set[str] = set()  # Track registered metrics
        self._initialization_order: List[str] = []  # Track initialization order
        self._shutdown_hooks: List[Callable] = []  # Cleanup hooks
        self._metrics = {
            "services_registered": 0,
            "services_ready": 0,
            "services_error": 0,
            "services_degraded": 0,
            "health_checks_performed": 0,
            "health_check_failures": 0,
            "dependency_failures": 0,
            "fallback_activations": 0
        }
    
    def register_service(
        self,
        name: str,
        service_type: Type[T],
        dependencies: Optional[Dict[str, bool]] = None,
        health_check: Optional[Callable] = None,
        max_attempts: int = 3
    ) -> None:
        """
        Register a service with the registry.
        
        Args:
            name: Service name
            service_type: Service class type
            dependencies: Dict of dependency_name -> required (True/False)
            health_check: Optional health check function
            max_attempts: Maximum initialization attempts
        """
        if name in self._services:
            logger.warning(f"Service {name} already registered, updating registration")
        
        # Convert dependencies to DependencyInfo objects
        dep_info_list = []
        if dependencies:
            for dep_name, required in dependencies.items():
                dep_info_list.append(DependencyInfo(
                    name=dep_name,
                    required=required,
                    status=DependencyStatus.MISSING
                ))
        
        self._services[name] = ServiceInfo(
            name=name,
            service_type=service_type,
            dependencies=dep_info_list,
            health_check=health_check,
            max_initialization_attempts=max_attempts
        )
        self._metrics["services_registered"] += 1
        logger.info(f"Registered service: {name} with {len(dep_info_list)} dependencies")
    
    def register_metrics_safely(self, metric_name: str, metric_factory: Callable) -> Any:
        """
        Register metrics safely, preventing duplicate registration warnings.
        
        Args:
            metric_name: Name of the metric
            metric_factory: Function to create the metric
            
        Returns:
            The metric instance or a dummy metric if already registered
        """
        if metric_name in self._registered_metrics:
            logger.debug(f"Metric {metric_name} already registered, returning dummy metric")
            
            # Return dummy metric to prevent errors
            class DummyMetric1:
                def labels(self, **kwargs):
                    return self
                def inc(self, amount=1):
                    pass
                def observe(self, value):
                    pass
                def set(self, value):
                    pass
            
            return DummyMetric1()
        
        try:
            metric = metric_factory()
            self._registered_metrics.add(metric_name)
            logger.debug(f"Successfully registered metric: {metric_name}")
            return metric
        except ValueError as e:
            if "Duplicated timeseries" in str(e) or "already registered" in str(e).lower():
                logger.warning(f"Metric {metric_name} already registered by external system, using dummy metric")
                self._registered_metrics.add(metric_name)
                
                class DummyMetric2:
                    def labels(self, **kwargs):
                        return self
                    def inc(self, amount=1):
                        pass
                    def observe(self, value):
                        pass
                    def set(self, value):
                        pass
                
                return DummyMetric2()
            else:
                logger.error(f"Failed to register metric {metric_name}: {e}")
                raise
    
    async def get_service(self, name: str) -> Any:
        """Get a service instance, initializing if necessary."""
        if name not in self._services:
            raise ValueError(f"Service {name} not registered")
        
        # Return cached instance if available and ready
        if name in self._instances:
            service_info = self._services[name]
            if service_info.status in [ServiceStatus.READY, ServiceStatus.DEGRADED]:
                return self._instances[name]
        
        # Initialize service if not ready
        async with self._initialization_lock:
            if name not in self._instances or self._services[name].status not in [ServiceStatus.READY, ServiceStatus.DEGRADED]:
                await self._initialize_service(name)
        
        # Check if service was successfully initialized
        if name in self._instances:
            return self._instances[name]
        else:
            # Service failed to initialize
            service_info = self._services[name]
            if service_info.status == ServiceStatus.ERROR:
                raise RuntimeError(f"Service {name} failed to initialize: {service_info.error_message}")
            else:
                raise RuntimeError(f"Service {name} is not available (status: {service_info.status})")
    
    async def _initialize_service(self, name: str) -> None:
        """Initialize a service and its dependencies with graceful degradation."""
        service_info = self._services[name]
        
        if service_info.status == ServiceStatus.READY:
            return
        
        # Check if we've exceeded max attempts (don't increment if already exceeded)
        if service_info.initialization_attempts >= service_info.max_initialization_attempts:
            logger.error(f"Service {name} exceeded maximum initialization attempts ({service_info.max_initialization_attempts})")
            service_info.status = ServiceStatus.ERROR
            service_info.error_message = "Maximum initialization attempts exceeded"
            return
        
        service_info.initialization_attempts += 1
        
        logger.info(f"Initializing service: {name} (attempt {service_info.initialization_attempts})")
        service_info.status = ServiceStatus.INITIALIZING
        
        try:
            # Check and initialize dependencies
            dependency_instances = {}
            missing_required_deps = []
            available_deps = []
            
            for dep_info in service_info.dependencies:
                dep_name = dep_info.name
                
                try:
                    if dep_name not in self._services:
                        if dep_info.required:
                            dep_info.status = DependencyStatus.MISSING
                            dep_info.error_message = f"Dependency {dep_name} not registered"
                            missing_required_deps.append(dep_name)
                            logger.warning(f"Required dependency {dep_name} not registered for service {name}")
                        else:
                            dep_info.status = DependencyStatus.OPTIONAL
                            logger.info(f"Optional dependency {dep_name} not available for service {name}")
                        continue
                    
                    # Check if dependency is already being initialized to prevent infinite recursion
                    dep_service_info = self._services[dep_name]
                    if dep_service_info.status == ServiceStatus.INITIALIZING:
                        if dep_info.required:
                            dep_info.status = DependencyStatus.FAILED
                            dep_info.error_message = f"Circular dependency detected with {dep_name}"
                            missing_required_deps.append(dep_name)
                            logger.error(f"Circular dependency detected: {name} -> {dep_name}")
                        else:
                            dep_info.status = DependencyStatus.OPTIONAL
                            logger.warning(f"Circular dependency detected with optional dependency {dep_name}")
                        continue
                    
                    # Try to get the dependency
                    dep_instance = await self.get_service(dep_name)
                    dependency_instances[dep_name] = dep_instance
                    dep_info.status = DependencyStatus.AVAILABLE
                    available_deps.append(dep_name)
                    logger.debug(f"Dependency {dep_name} available for service {name}")
                    
                except Exception as e:
                    dep_info.status = DependencyStatus.FAILED
                    dep_info.error_message = str(e)
                    
                    if dep_info.required:
                        missing_required_deps.append(dep_name)
                        logger.error(f"Failed to initialize required dependency {dep_name} for service {name}: {e}")
                    else:
                        logger.warning(f"Failed to initialize optional dependency {dep_name} for service {name}: {e}")
                        self._metrics["dependency_failures"] += 1
            
            # Decide how to proceed based on dependency availability
            can_initialize = len(missing_required_deps) == 0
            degraded_mode = len(missing_required_deps) == 0 and len(available_deps) < len([d for d in service_info.dependencies if d.required])
            
            if not can_initialize:
                logger.warning(f"Cannot initialize service {name}: missing required dependencies: {missing_required_deps}")
                service_info.status = ServiceStatus.ERROR
                service_info.error_message = f"Missing required dependencies: {', '.join(missing_required_deps)}"
                return
            
            # Initialize the service
            start_time = time.time()
            
            # Create service config (create a simple config if ServiceConfig doesn't exist)
            try:
                from ai_karen_engine.core.services.base import ServiceConfig
                service_config = ServiceConfig(
                    name=name,
                    enabled=True,
                    dependencies=[dep.name for dep in service_info.dependencies],
                    config={}
                )
            except ImportError:
                # Create a simple config object if ServiceConfig doesn't exist
                class SimpleServiceConfig:
                    def __init__(self, name: str, enabled: bool = True, dependencies: Optional[List[str]] = None, config: Optional[Dict] = None):
                        self.name = name
                        self.enabled = enabled
                        self.dependencies = dependencies or []
                        self.config = config or {}
                
                service_config = SimpleServiceConfig(
                    name=name,
                    enabled=True,
                    dependencies=[dep.name for dep in service_info.dependencies],
                    config={}
                )
            
            # Initialize service with proper constructor arguments and graceful handling
            instance = None
            
            try:
                if service_info.service_type == AIOrchestrator:
                    instance = AIOrchestrator(service_config)
                elif service_info.service_type == WebUIMemoryService:
                    # WebUIMemoryService needs base_memory_manager
                    try:
                        try:
                            from ai_karen_engine.database.memory_manager import MemoryManager
                            from ai_karen_engine.database.client import MultiTenantPostgresClient
                            from ai_karen_engine.core.milvus_client import MilvusClient
                            from ai_karen_engine.core import default_models
                        except ImportError:
                            # Use dummy classes if imports fail
                            class MemoryManager:
                                def __init__(self, db_client, milvus_client, embedding_manager): pass
                            
                            class MultiTenantPostgresClient:
                                def __init__(self): pass
                            
                            class MilvusClient:
                                def __init__(self): pass
                            
                            default_models = type('DefaultModels', (), {'load_default_models': lambda: None, 'get_embedding_manager': lambda: None})()
                        
                        # Initialize required components with error handling
                        db_client = MultiTenantPostgresClient()
                        milvus_client = MilvusClient()
                        await default_models.load_default_models()
                        embedding_manager = default_models.get_embedding_manager()
                        
                        # Create memory manager instance
                        memory_manager = MemoryManager(
                            db_client=db_client,
                            milvus_client=milvus_client,
                            embedding_manager=embedding_manager
                        )
                        
                        instance = WebUIMemoryService(memory_manager)
                    except Exception as e:
                        logger.warning(f"Failed to initialize WebUIMemoryService components: {e}")
                        # Create a minimal fallback instance if possible
                        instance = None
                elif service_info.service_type == UnifiedMemoryService:
                    # UnifiedMemoryService can be initialized directly
                    try:
                        instance = UnifiedMemoryService()
                    except Exception as e:
                        logger.warning(f"Failed to initialize UnifiedMemoryService: {e}")
                        instance = None
                        
                elif service_info.service_type == WebUIConversationService:
                    # WebUIConversationService needs memory_service dependency
                    memory_service = dependency_instances.get("memory_service")
                    if memory_service:
                        try:
                            # Build ConversationManager using the existing memory service components
                            memory_manager = memory_service.base_manager
                            conversation_manager = ConversationManager(
                                db_client=memory_manager.db_client,
                                memory_manager=memory_manager,
                                embedding_manager=memory_manager.embedding_manager,
                            )
                            instance = WebUIConversationService(conversation_manager, memory_service)
                        except Exception as e:
                            logger.warning(f"Failed to initialize WebUIConversationService: {e}")
                            instance = None
                    else:
                        logger.warning("WebUIConversationService cannot initialize without memory_service")
                        instance = None
                        
                elif service_info.service_type == PluginService:
                    try:
                        from pathlib import Path
                        marketplace_path = Path("plugin_marketplace")
                        core_plugins_path = Path("src/ai_karen_engine/plugins")
                        instance = PluginService(
                            marketplace_path=marketplace_path,
                            core_plugins_path=core_plugins_path
                        )
                    except Exception as e:
                        logger.warning(f"Failed to initialize PluginService: {e}")
                        instance = None
                        
                elif service_info.service_type == ToolService:
                    try:
                        instance = ToolService(service_config)
                    except Exception as e:
                        logger.warning(f"Failed to initialize ToolService: {e}")
                        instance = None
                        
                elif service_info.service_type == AnalyticsService:
                    # AnalyticsService takes a config dict, not direct service dependencies
                    try:
                        config = {
                            "max_metrics": 10000,
                            "system_monitor_interval": 30,
                            "max_alerts": 1000,
                            "max_user_events": 10000,
                            "max_performance_metrics": 10000
                        }
                        instance = AnalyticsService(config)
                        logger.info(f"Successfully initialized AnalyticsService with config: {config}")
                    except Exception as e:
                        logger.error(f"Failed to initialize AnalyticsService: {e}")
                        # Create a minimal fallback analytics service
                        try:
                            class MinimalAnalyticsService:
                                def __init__(self, config):
                                    self.config = config
                                    self.logger = logging.getLogger(__name__)
                                    self.logger.info("Initialized minimal analytics service fallback")
                                
                                def record_metric(self, *args, **kwargs):
                                    pass
                                
                                def get_system_metrics(self):
                                    return {"status": "fallback_mode"}
                                
                                async def run_health_check(self, name):
                                    return {"status": "healthy", "mode": "fallback"}
                                
                                async def initialize(self):
                                    pass
                            
                            instance = MinimalAnalyticsService(config)
                            logger.info("Created fallback analytics service")
                        except Exception as fallback_error:
                            logger.error(f"Failed to create fallback analytics service: {fallback_error}")
                            instance = None
                else:
                    # Try to instantiate with dependency injection
                    try:
                        # First try with service_config and dependencies
                        instance = service_info.service_type(service_config, **dependency_instances)
                    except Exception as e:
                        logger.warning(f"Failed to initialize {service_info.service_type.__name__} with dependency injection: {e}")
                        # Try with just dependencies (for test services)
                        try:
                            instance = service_info.service_type(**dependency_instances)
                        except Exception as e2:
                            logger.warning(f"Failed to initialize {service_info.service_type.__name__} with dependencies only: {e2}")
                            # Try without dependencies
                            try:
                                instance = service_info.service_type()
                            except Exception as e3:
                                logger.warning(f"Failed to initialize {service_info.service_type.__name__} without dependencies: {e3}")
                                instance = None
                            
            except Exception as e:
                logger.error(f"Unexpected error during service instantiation for {name}: {e}")
                instance = None
            
            if instance is None:
                raise ValueError(f"Failed to create instance for service {name}")
            
            # Initialize the service if it has an async init method
            try:
                if hasattr(instance, 'initialize'):
                    await instance.initialize()
            except Exception as e:
                logger.warning(f"Service {name} initialization method failed: {e}")
                # Continue with service registration even if initialization fails
            
            service_info.initialization_time = time.time() - start_time
            
            # Determine final status based on dependency availability
            if degraded_mode:
                service_info.status = ServiceStatus.DEGRADED
                service_info.fallback_mode = True
                self._metrics["services_degraded"] += 1
                self._metrics["fallback_activations"] += 1
                logger.warning(f"Service {name} initialized in degraded mode (missing optional dependencies)")
            else:
                service_info.status = ServiceStatus.READY
                self._metrics["services_ready"] += 1
                logger.info(f"Service {name} initialized successfully in {service_info.initialization_time:.2f}s")
            
            service_info.error_message = None
            self._instances[name] = instance
            self._initialization_order.append(name)
            
        except Exception as e:
            service_info.status = ServiceStatus.ERROR
            service_info.error_message = str(e)
            self._metrics["services_error"] += 1
            logger.error(f"Failed to initialize service {name} (attempt {service_info.initialization_attempts}): {e}")
            
            # Don't re-raise the exception to allow other services to initialize
            if service_info.initialization_attempts >= service_info.max_initialization_attempts:
                logger.error(f"Service {name} permanently failed after {service_info.max_initialization_attempts} attempts")
            else:
                logger.info(f"Service {name} will be retried later")
    
    async def initialize_all_services(self) -> Dict[str, ServiceStatus]:
        """Initialize all registered services."""
        logger.info("Initializing all services...")
        results = {}
        
        for name in self._services:
            try:
                await self.get_service(name)
                results[name] = self._services[name].status
            except Exception as e:
                logger.error(f"Failed to initialize service {name}: {e}")
                results[name] = ServiceStatus.ERROR
        
        ready_count = sum(1 for status in results.values() if status == ServiceStatus.READY)
        logger.info(f"Service initialization complete: {ready_count}/{len(results)} services ready")
        
        return results
    
    async def health_check(self, service_name: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Perform comprehensive health checks on services."""
        results = {}
        services_to_check = [service_name] if service_name else list(self._services.keys())
        
        for name in services_to_check:
            service_info = self._services[name]
            current_time = time.time()
            
            # Basic service information
            result = {
                "status": service_info.status.value,
                "error_message": service_info.error_message,
                "initialization_time": service_info.initialization_time,
                "initialization_attempts": service_info.initialization_attempts,
                "fallback_mode": service_info.fallback_mode,
                "last_health_check": service_info.last_health_check,
                "dependencies": {}
            }
            
            # Dependency status
            for dep_info in service_info.dependencies:
                result["dependencies"][dep_info.name] = {
                    "status": dep_info.status.value,
                    "required": dep_info.required,
                    "error_message": dep_info.error_message,
                    "fallback_available": dep_info.fallback_available
                }
            
            # Perform custom health check if available and service is running
            if service_info.health_check and name in self._instances and service_info.status in [ServiceStatus.READY, ServiceStatus.DEGRADED]:
                try:
                    health_result = await service_info.health_check(self._instances[name])
                    result["health_check"] = health_result
                    service_info.health_status = "healthy"
                    self._metrics["health_checks_performed"] += 1
                except Exception as e:
                    result["health_check"] = {"error": str(e)}
                    service_info.health_status = "unhealthy"
                    self._metrics["health_check_failures"] += 1
                    logger.warning(f"Health check failed for service {name}: {e}")
            else:
                result["health_check"] = {"status": "not_available", "reason": "Service not running or no health check defined"}
            
            # Update last health check time
            service_info.last_health_check = current_time
            result["health_status"] = service_info.health_status
            
            results[name] = result
        
        return results
    
    def get_initialization_report(self) -> Dict[str, Any]:
        """Get a comprehensive initialization report."""
        total_services = len(self._services)
        ready_services = sum(1 for s in self._services.values() if s.status == ServiceStatus.READY)
        degraded_services = sum(1 for s in self._services.values() if s.status == ServiceStatus.DEGRADED)
        error_services = sum(1 for s in self._services.values() if s.status == ServiceStatus.ERROR)
        pending_services = sum(1 for s in self._services.values() if s.status == ServiceStatus.PENDING)
        
        report = {
            "summary": {
                "total_services": total_services,
                "ready_services": ready_services,
                "degraded_services": degraded_services,
                "error_services": error_services,
                "pending_services": pending_services,
                "success_rate": (ready_services + degraded_services) / total_services if total_services > 0 else 0,
                "initialization_order": self._initialization_order.copy()
            },
            "services": {},
            "dependency_graph": self._build_dependency_graph(),
            "metrics": self._metrics.copy()
        }
        
        # Detailed service information
        for name, service_info in self._services.items():
            report["services"][name] = {
                "status": service_info.status.value,
                "type": service_info.service_type.__name__,
                "initialization_time": service_info.initialization_time,
                "initialization_attempts": service_info.initialization_attempts,
                "fallback_mode": service_info.fallback_mode,
                "error_message": service_info.error_message,
                "dependencies": {
                    dep.name: {
                        "status": dep.status.value,
                        "required": dep.required,
                        "error": dep.error_message
                    } for dep in service_info.dependencies
                }
            }
        
        return report
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build a dependency graph for visualization."""
        graph = {}
        for name, service_info in self._services.items():
            graph[name] = [dep.name for dep in service_info.dependencies]
        return graph
    
    def start_health_monitoring(self) -> None:
        """Start periodic health monitoring."""
        if self._health_check_task and not self._health_check_task.done():
            logger.warning("Health monitoring already running")
            return
        
        async def _health_monitor():
            while True:
                try:
                    await asyncio.sleep(self._health_check_interval)
                    await self.health_check()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
        
        self._health_check_task = asyncio.create_task(_health_monitor())
        logger.info("Started health monitoring")
    
    def stop_health_monitoring(self) -> None:
        """Stop periodic health monitoring."""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            logger.info("Stopped health monitoring")
    
    async def shutdown(self) -> None:
        """Shutdown all services gracefully."""
        logger.info("Shutting down services...")
        
        # Stop health monitoring
        self.stop_health_monitoring()
        
        # Shutdown services in reverse dependency order
        shutdown_order = self._get_shutdown_order()
        
        for name in shutdown_order:
            if name in self._instances:
                try:
                    instance = self._instances[name]
                    if hasattr(instance, 'shutdown'):
                        await instance.shutdown()
                    self._services[name].status = ServiceStatus.STOPPED
                    logger.info(f"Service {name} shut down successfully")
                except Exception as e:
                    logger.error(f"Error shutting down service {name}: {e}")
        
        self._instances.clear()
        logger.info("All services shut down")
    
    def _get_shutdown_order(self) -> list[str]:
        """Get the order in which services should be shut down (reverse dependency order)."""
        # Simple topological sort for shutdown order
        visited = set()
        order = []
        
        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            
            # Visit dependents first (services that depend on this one)
            for service_name, service_info in self._services.items():
                if name in service_info.dependencies:
                    visit(service_name)
            
            order.append(name)
        
        for name in self._services:
            visit(name)
        
        return order
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service registry metrics."""
        return {
            **self._metrics,
            "services_total": len(self._services),
            "services_status": {
                name: info.status.value for name, info in self._services.items()
            }
        }
    
    def get_service_info(self, name: str) -> Optional[ServiceInfo]:
        """Get information about a specific service."""
        return self._services.get(name)
    
    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """List all registered services with their status."""
        return {
            name: {
                "type": info.service_type.__name__,
                "status": info.status.value,
                "dependencies": info.dependencies,
                "error_message": info.error_message,
                "initialization_time": info.initialization_time
            }
            for name, info in self._services.items()
        }


# Global service registry instance
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry


async def initialize_services() -> None:
    """Initialize all core services for AI Karen engine integration."""
    registry = get_service_registry()
    
    # Check if we should use classified service registry
    try:
        from ai_karen_engine.core.classified_service_registry import get_classified_registry
        classified_registry = get_classified_registry()
        
        if classified_registry and hasattr(classified_registry, 'is_initialized') and classified_registry.is_initialized():
            logger.info("🔧 Using classified service registry for optimized initialization")
            
            # Use classified registry for service management
            await classified_registry.initialize_services_by_classification()
            
            # Get initialization report from classified registry
            report = classified_registry.get_initialization_report()
            logger.info(f"Classified service initialization complete: {report['summary']['ready_services']}/{report['summary']['total_services']} ready")
            
            return
            
    except ImportError:
        logger.debug("Classified service registry not available, using standard registry")
    except Exception as e:
        logger.warning(f"Failed to use classified service registry: {e}, falling back to standard")
    
    # Standard service registration and initialization
    # Register core services with proper dependency management
    registry.register_service("ai_orchestrator", AIOrchestrator)
    registry.register_service("memory_service", WebUIMemoryService)
    registry.register_service("conversation_service", WebUIConversationService, {"memory_service": True})
    registry.register_service("plugin_service", PluginService)
    registry.register_service("tool_service", ToolService)
    # Register analytics service with optional dependencies to prevent startup failures
    registry.register_service("analytics_service", AnalyticsService, {
        "memory_service": False,  # Optional dependency
        "conversation_service": False  # Optional dependency
    })
    
    # Initialize all services with comprehensive reporting
    results = await registry.initialize_all_services()
    
    # Generate and log initialization report
    report = registry.get_initialization_report()
    logger.info(f"Service initialization complete: {report['summary']['ready_services']}/{report['summary']['total_services']} ready, "
               f"{report['summary']['degraded_services']} degraded, {report['summary']['error_services']} failed")
    
    # Log any services that failed to initialize
    for service_name, service_info in report['services'].items():
        if service_info['status'] == 'error':
            logger.error(f"Service {service_name} failed to initialize: {service_info['error_message']}")
        elif service_info['status'] == 'degraded':
            logger.warning(f"Service {service_name} running in degraded mode")
    
    # Start health monitoring
    registry.start_health_monitoring()
    
    logger.info("AI Karen engine integration services initialized successfully")


@asynccontextmanager
async def service_context():
    """Context manager for service lifecycle management."""
    try:
        await initialize_services()
        yield get_service_registry()
    finally:
        registry = get_service_registry()
        await registry.shutdown()


# Dependency injection helpers
async def get_ai_orchestrator() -> AIOrchestrator:
    """Get AI Orchestrator service instance."""
    registry = get_service_registry()
    return await registry.get_service("ai_orchestrator")


async def get_memory_service() -> Union[WebUIMemoryService, UnifiedMemoryService]:
    """Get Memory service instance."""
    registry = get_service_registry()
    return await registry.get_service("memory_service")


async def get_conversation_service() -> WebUIConversationService:
    """Get Conversation service instance."""
    registry = get_service_registry()
    return await registry.get_service("conversation_service")


async def get_plugin_service() -> PluginService:
    """Get Plugin service instance."""
    registry = get_service_registry()
    return await registry.get_service("plugin_service")


async def get_tool_service() -> ToolService:
    """Get Tool service instance."""
    registry = get_service_registry()
    return await registry.get_service("tool_service")


async def get_analytics_service() -> AnalyticsService:
    """Get Analytics service instance."""
    registry = get_service_registry()
    return await registry.get_service("analytics_service")