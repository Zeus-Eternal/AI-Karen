"""
Dependency injection container for AI Karen services.
"""

from typing import Any, Dict, Type, TypeVar, Callable, Optional, List
from functools import wraps
import inspect
import logging
from ai_karen_engine.core.services.base import BaseService, ServiceConfig

T = TypeVar('T')
logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Dependency injection container for managing service instances and dependencies.
    """
    
    def __init__(self):
        self._services: Dict[str, BaseService] = {}
        self._factories: Dict[str, Callable[[], BaseService]] = {}
        self._singletons: Dict[str, BaseService] = {}
        self._configs: Dict[str, ServiceConfig] = {}
        self._dependency_graph: Dict[str, List[str]] = {}
    
    def register_service(
        self, 
        name: str, 
        service_class: Type[BaseService], 
        config: ServiceConfig,
        singleton: bool = True
    ) -> None:
        """
        Register a service class with the container.
        
        Args:
            name: Service name
            service_class: Service class to instantiate
            config: Service configuration
            singleton: Whether to create a singleton instance
        """
        self._configs[name] = config
        self._dependency_graph[name] = config.dependencies
        
        def factory():
            return service_class(config)
        
        self._factories[name] = factory
        
        if singleton:
            logger.info(f"Registered singleton service: {name}")
        else:
            logger.info(f"Registered transient service: {name}")
    
    def register_instance(self, name: str, instance: BaseService) -> None:
        """
        Register a service instance directly.
        
        Args:
            name: Service name
            instance: Service instance
        """
        self._singletons[name] = instance
        self._configs[name] = instance.config
        self._dependency_graph[name] = instance.config.dependencies
        logger.info(f"Registered service instance: {name}")
    
    def get_service(self, name: str) -> BaseService:
        """
        Get a service instance by name.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service is not registered
        """
        # Check if singleton instance exists
        if name in self._singletons:
            return self._singletons[name]
        
        # Check if factory exists
        if name in self._factories:
            instance = self._factories[name]()
            self._singletons[name] = instance
            return instance
        
        raise ValueError(f"Service not registered: {name}")
    
    def resolve_dependencies(self, service_name: str) -> List[BaseService]:
        """
        Resolve all dependencies for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            List of dependency service instances
        """
        dependencies = []
        for dep_name in self._dependency_graph.get(service_name, []):
            dependencies.append(self.get_service(dep_name))
        return dependencies
    
    def get_startup_order(self) -> List[str]:
        """
        Get the correct startup order for services based on dependencies.
        
        Returns:
            List of service names in startup order
        """
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(service_name: str):
            if service_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving: {service_name}")
            
            if service_name not in visited:
                temp_visited.add(service_name)
                
                # Visit dependencies first
                for dep in self._dependency_graph.get(service_name, []):
                    visit(dep)
                
                temp_visited.remove(service_name)
                visited.add(service_name)
                order.append(service_name)
        
        # Visit all services
        for service_name in self._dependency_graph.keys():
            if service_name not in visited:
                visit(service_name)
        
        return order
    
    async def start_all_services(self) -> None:
        """
        Start all registered services in dependency order.
        """
        startup_order = self.get_startup_order()
        logger.info(f"Starting services in order: {startup_order}")
        
        for service_name in startup_order:
            try:
                service = self.get_service(service_name)
                await service.startup()
                logger.info(f"Successfully started service: {service_name}")
            except Exception as e:
                logger.error(f"Failed to start service {service_name}: {e}")
                raise
    
    async def stop_all_services(self) -> None:
        """
        Stop all services in reverse dependency order.
        """
        startup_order = self.get_startup_order()
        shutdown_order = list(reversed(startup_order))
        logger.info(f"Stopping services in order: {shutdown_order}")
        
        for service_name in shutdown_order:
            try:
                if service_name in self._singletons:
                    service = self._singletons[service_name]
                    await service.shutdown()
                    logger.info(f"Successfully stopped service: {service_name}")
            except Exception as e:
                logger.error(f"Failed to stop service {service_name}: {e}")
    
    def get_all_services(self) -> Dict[str, BaseService]:
        """
        Get all instantiated service instances.
        
        Returns:
            Dictionary of service name to instance
        """
        return self._singletons.copy()
    
    def get_service_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health status of all services.
        
        Returns:
            Dictionary of service health information
        """
        health_info = {}
        for name, service in self._singletons.items():
            health_info[name] = {
                "status": service.status.value,
                "health": service.health.dict(),
                "metrics": service.get_metrics()
            }
        return health_info


# Global service container instance
_container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Get the global service container instance."""
    return _container


def service(
    name: str, 
    config: Optional[ServiceConfig] = None,
    singleton: bool = True
) -> Callable[[Type[BaseService]], Type[BaseService]]:
    """
    Decorator to register a service class with the container.
    
    Args:
        name: Service name
        config: Service configuration (optional)
        singleton: Whether to create singleton instance
    """
    def decorator(cls: Type[BaseService]) -> Type[BaseService]:
        service_config = config or ServiceConfig(name=name)
        _container.register_service(name, cls, service_config, singleton)
        return cls
    return decorator


def inject(service_name: str) -> Callable:
    """
    Decorator to inject a service dependency into a function or method.
    
    Args:
        service_name: Name of the service to inject
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            service_instance = _container.get_service(service_name)
            return func(service_instance, *args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            service_instance = _container.get_service(service_name)
            return await func(service_instance, *args, **kwargs)
        
        return async_wrapper if inspect.iscoroutinefunction(func) else wrapper
    return decorator