"""
Service Registry and Dependency Injection for AI Karen Engine Integration.

This module provides centralized service management and dependency injection
for integrating the new Python backend services with the existing AI Karen engine.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Type, TypeVar, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum

from ..services.ai_orchestrator import AIOrchestrator
from ..services.memory_service import WebUIMemoryService
from ..services.conversation_service import WebUIConversationService
from ..services.plugin_service import PluginService
from ..services.tool_service import ToolService
from ..services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceStatus(str, Enum):
    """Service status enumeration."""
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class ServiceInfo:
    """Information about a registered service."""
    name: str
    service_type: Type
    instance: Optional[Any] = None
    status: ServiceStatus = ServiceStatus.INITIALIZING
    dependencies: list[str] = field(default_factory=list)
    health_check: Optional[Callable] = None
    error_message: Optional[str] = None
    initialization_time: Optional[float] = None


class ServiceRegistry:
    """
    Central service registry for AI Karen engine integration.
    
    Manages service lifecycle, dependency injection, and health monitoring
    for all backend services.
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}
        self._instances: Dict[str, Any] = {}
        self._initialization_lock = asyncio.Lock()
        self._health_check_interval = 30  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics = {
            "services_registered": 0,
            "services_ready": 0,
            "services_error": 0,
            "health_checks_performed": 0,
            "health_check_failures": 0
        }
    
    def register_service(
        self,
        name: str,
        service_type: Type[T],
        dependencies: Optional[list[str]] = None,
        health_check: Optional[Callable] = None
    ) -> None:
        """Register a service with the registry."""
        if name in self._services:
            logger.warning(f"Service {name} already registered, overwriting")
        
        self._services[name] = ServiceInfo(
            name=name,
            service_type=service_type,
            dependencies=dependencies or [],
            health_check=health_check
        )
        self._metrics["services_registered"] += 1
        logger.info(f"Registered service: {name}")
    
    async def get_service(self, name: str) -> Any:
        """Get a service instance, initializing if necessary."""
        if name not in self._services:
            raise ValueError(f"Service {name} not registered")
        
        # Return cached instance if available and ready
        if name in self._instances:
            service_info = self._services[name]
            if service_info.status == ServiceStatus.READY:
                return self._instances[name]
        
        # Initialize service if not ready
        async with self._initialization_lock:
            if name not in self._instances or self._services[name].status != ServiceStatus.READY:
                await self._initialize_service(name)
        
        return self._instances[name]
    
    async def _initialize_service(self, name: str) -> None:
        """Initialize a service and its dependencies."""
        service_info = self._services[name]
        
        if service_info.status == ServiceStatus.READY:
            return
        
        logger.info(f"Initializing service: {name}")
        service_info.status = ServiceStatus.INITIALIZING
        
        try:
            # Initialize dependencies first
            dependency_instances = {}
            for dep_name in service_info.dependencies:
                if dep_name not in self._services:
                    raise ValueError(f"Dependency {dep_name} not registered for service {name}")
                dependency_instances[dep_name] = await self.get_service(dep_name)
            
            # Initialize the service
            import time
            start_time = time.time()
            
            # Create service config
            from .services.base import ServiceConfig
            service_config = ServiceConfig(
                name=name,
                enabled=True,
                dependencies=service_info.dependencies,
                config={}
            )
            
            # Initialize service with proper constructor arguments
            if service_info.service_type == AIOrchestrator:
                instance = AIOrchestrator(service_config)
            elif service_info.service_type == WebUIMemoryService:
                # WebUIMemoryService needs base_memory_manager
                # Create a proper MemoryManager instance
                from ai_karen_engine.database.memory_manager import MemoryManager
                from ai_karen_engine.database.client import MultiTenantPostgresClient
                from ai_karen_engine.core.milvus_client import MilvusClient
                from ai_karen_engine.core.embedding_manager import EmbeddingManager
                
                # Initialize required components
                db_client = MultiTenantPostgresClient()
                milvus_client = MilvusClient()
                embedding_manager = EmbeddingManager()
                
                # Create memory manager instance
                memory_manager = MemoryManager(
                    db_client=db_client,
                    milvus_client=milvus_client,
                    embedding_manager=embedding_manager
                )
                
                instance = WebUIMemoryService(memory_manager)
            elif service_info.service_type == WebUIConversationService:
                # WebUIConversationService needs memory_service dependency
                memory_service = dependency_instances.get('memory_service')
                if not memory_service:
                    raise ValueError("WebUIConversationService requires memory_service dependency")

                # Build ConversationManager using the same components as memory_service
                from ai_karen_engine.database.conversation_manager import ConversationManager

                memory_manager = memory_service.base_manager
                conversation_manager = ConversationManager(
                    db_client=memory_manager.db_client,
                    memory_manager=memory_manager,
                    embedding_manager=memory_manager.embedding_manager,
                )

                instance = WebUIConversationService(conversation_manager, memory_service)
            elif service_info.service_type == PluginService:
                from pathlib import Path
                marketplace_path = Path("plugin_marketplace")
                core_plugins_path = Path("src/ai_karen_engine/plugins")
                instance = PluginService(
                    marketplace_path=marketplace_path,
                    core_plugins_path=core_plugins_path
                )
            elif service_info.service_type == ToolService:
                instance = ToolService(service_config)
            elif service_info.service_type == AnalyticsService:
                # AnalyticsService needs memory and conversation service dependencies
                memory_service = dependency_instances.get('memory_service')
                conversation_service = dependency_instances.get('conversation_service')
                if not memory_service or not conversation_service:
                    raise ValueError("AnalyticsService requires memory_service and conversation_service dependencies")
                instance = AnalyticsService(memory_service, conversation_service)
            else:
                # Try to instantiate with dependency injection
                instance = service_info.service_type(service_config, **dependency_instances)
            
            # Initialize the service if it has an async init method
            if hasattr(instance, 'initialize'):
                await instance.initialize()
            
            service_info.initialization_time = time.time() - start_time
            service_info.status = ServiceStatus.READY
            service_info.error_message = None
            
            self._instances[name] = instance
            self._metrics["services_ready"] += 1
            
            logger.info(f"Service {name} initialized successfully in {service_info.initialization_time:.2f}s")
            
        except Exception as e:
            service_info.status = ServiceStatus.ERROR
            service_info.error_message = str(e)
            self._metrics["services_error"] += 1
            logger.error(f"Failed to initialize service {name}: {e}", exc_info=True)
            raise
    
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
        """Perform health checks on services."""
        results = {}
        services_to_check = [service_name] if service_name else list(self._services.keys())
        
        for name in services_to_check:
            service_info = self._services[name]
            result = {
                "status": service_info.status.value,
                "error_message": service_info.error_message,
                "initialization_time": service_info.initialization_time
            }
            
            # Perform custom health check if available
            if service_info.health_check and name in self._instances:
                try:
                    health_result = await service_info.health_check(self._instances[name])
                    result["health_check"] = health_result
                    self._metrics["health_checks_performed"] += 1
                except Exception as e:
                    result["health_check"] = {"error": str(e)}
                    self._metrics["health_check_failures"] += 1
                    logger.warning(f"Health check failed for service {name}: {e}")
            
            results[name] = result
        
        return results
    
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
    
    # Register core services
    registry.register_service("ai_orchestrator", AIOrchestrator)
    registry.register_service("memory_service", WebUIMemoryService)
    registry.register_service("conversation_service", WebUIConversationService, ["memory_service"])
    registry.register_service("plugin_service", PluginService)
    registry.register_service("tool_service", ToolService)
    # Temporarily disable analytics service to fix startup issues
    # registry.register_service("analytics_service", AnalyticsService, ["memory_service", "conversation_service"])
    
    # Initialize all services
    await registry.initialize_all_services()
    
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


async def get_memory_service() -> WebUIMemoryService:
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