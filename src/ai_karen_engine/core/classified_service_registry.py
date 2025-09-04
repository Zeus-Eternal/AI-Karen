"""
Classification-based Service Registry Integration.

This module extends the existing service registry with classification-based management,
enabling performance optimization through service lifecycle control.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .service_registry import ServiceRegistry, ServiceStatus
from .service_classification import (
    ServiceConfig, ServiceClassification, DeploymentMode,
    ServiceConfigurationLoader, DependencyGraphAnalyzer,
    ServiceConfigurationValidator
)

logger = logging.getLogger(__name__)


class ServiceLifecycleState(str, Enum):
    """Extended service lifecycle states for classification-based management."""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    ACTIVE = "active"
    IDLE = "idle"
    SUSPENDED = "suspended"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


@dataclass
class ClassifiedServiceInfo:
    """Extended service information with classification data."""
    config: ServiceConfig
    lifecycle_state: ServiceLifecycleState = ServiceLifecycleState.NOT_LOADED
    last_accessed: Optional[float] = None
    idle_since: Optional[float] = None
    suspension_count: int = 0
    total_active_time: float = 0.0
    resource_usage: Dict[str, float] = None
    
    def __post_init__(self):
        if self.resource_usage is None:
            self.resource_usage = {}


class ClassifiedServiceRegistry(ServiceRegistry):
    """
    Enhanced service registry with classification-based lifecycle management.
    
    Extends the base ServiceRegistry to support service classification,
    lazy loading, and performance optimization features.
    """
    
    def __init__(self, config_paths: Optional[List[str]] = None):
        """
        Initialize the classified service registry.
        
        Args:
            config_paths: Paths to service configuration files
        """
        super().__init__()
        
        # Classification system components
        self.config_loader = ServiceConfigurationLoader(config_paths)
        self.config_loader.load_configurations()
        self.dependency_analyzer = DependencyGraphAnalyzer(self.config_loader.services)
        self.validator = ServiceConfigurationValidator(self.config_loader)
        
        # Classification-specific state
        self.classified_services: Dict[str, ClassifiedServiceInfo] = {}
        self.deployment_mode = DeploymentMode.DEVELOPMENT
        self.startup_order: List[str] = []
        self.shutdown_order: List[str] = []
        
        # Lifecycle management
        self.idle_check_interval = 60  # seconds
        self.idle_check_task: Optional[asyncio.Task] = None
        self.auto_suspend_enabled = True
        
        # Performance tracking
        self.performance_metrics = {
            "services_suspended": 0,
            "services_resumed": 0,
            "memory_saved_mb": 0,
            "startup_time_saved_seconds": 0.0,
        }
        
        self._initialize_classified_services()
    
    def _initialize_classified_services(self) -> None:
        """Initialize classified service information."""
        for service_name, config in self.config_loader.services.items():
            self.classified_services[service_name] = ClassifiedServiceInfo(config=config)
        
        # Calculate startup and shutdown orders
        self.startup_order = self.dependency_analyzer.get_startup_order()
        self.shutdown_order = self.dependency_analyzer.get_shutdown_order()
        
        logger.info(f"Initialized {len(self.classified_services)} classified services")
        logger.info(f"Startup order: {self.startup_order}")
    
    def set_deployment_mode(self, mode: DeploymentMode) -> None:
        """
        Set the deployment mode and update service configurations.
        
        Args:
            mode: Deployment mode to set
        """
        self.deployment_mode = mode
        logger.info(f"Set deployment mode to: {mode.value}")
        
        # Update service enabled status based on deployment mode
        enabled_services = set(
            config.name for config in 
            self.config_loader.get_services_for_deployment_mode(mode)
        )
        
        for service_name, classified_info in self.classified_services.items():
            was_enabled = classified_info.config.enabled
            classified_info.config.enabled = service_name in enabled_services
            
            if was_enabled and not classified_info.config.enabled:
                logger.info(f"Service {service_name} disabled for deployment mode {mode.value}")
            elif not was_enabled and classified_info.config.enabled:
                logger.info(f"Service {service_name} enabled for deployment mode {mode.value}")
    
    def register_classified_service(
        self,
        service_name: str,
        service_type: type,
        config: Optional[ServiceConfig] = None,
        health_check: Optional[Callable] = None
    ) -> None:
        """
        Register a service with classification support.
        
        Args:
            service_name: Name of the service
            service_type: Service class type
            config: Service configuration (uses default if not provided)
            health_check: Optional health check function
        """
        # Use provided config or get from loader
        if config is None:
            config = self.config_loader.get_service_config(service_name)
            if config is None:
                # Create default config for unknown services
                config = ServiceConfig(
                    name=service_name,
                    classification=ServiceClassification.OPTIONAL,
                    startup_priority=100,
                )
                self.config_loader.add_service_config(config)
        
        # Register with base registry
        dependencies = {dep: True for dep in config.dependencies}
        super().register_service(
            name=service_name,
            service_type=service_type,
            dependencies=dependencies,
            health_check=health_check,
            max_attempts=config.max_restart_attempts
        )
        
        # Add classification info
        self.classified_services[service_name] = ClassifiedServiceInfo(config=config)
        
        logger.info(f"Registered classified service: {service_name} ({config.classification.value})")
    
    async def start_essential_services(self) -> Dict[str, ServiceStatus]:
        """
        Start only essential services for fast startup.
        
        Returns:
            Dictionary of service names to their status
        """
        logger.info("Starting essential services only...")
        
        essential_services = [
            name for name, info in self.classified_services.items()
            if (info.config.classification == ServiceClassification.ESSENTIAL and 
                info.config.enabled)
        ]
        
        # Filter startup order to only include essential services
        essential_startup_order = [
            name for name in self.startup_order 
            if name in essential_services
        ]
        
        results = {}
        start_time = time.time()
        
        for service_name in essential_startup_order:
            try:
                await self.get_service(service_name)
                results[service_name] = self._services[service_name].status
                
                # Update lifecycle state
                classified_info = self.classified_services[service_name]
                classified_info.lifecycle_state = ServiceLifecycleState.ACTIVE
                classified_info.last_accessed = time.time()
                
            except Exception as e:
                logger.error(f"Failed to start essential service {service_name}: {e}")
                results[service_name] = ServiceStatus.ERROR
        
        startup_time = time.time() - start_time
        logger.info(f"Essential services startup completed in {startup_time:.2f}s")
        
        # Start idle monitoring if not already running
        if self.idle_check_task is None and self.auto_suspend_enabled:
            self.idle_check_task = asyncio.create_task(self._idle_monitoring_loop())
        
        return results
    
    async def load_service_on_demand(self, service_name: str) -> Any:
        """
        Load a service on-demand with lazy loading.
        
        Args:
            service_name: Name of the service to load
            
        Returns:
            Service instance
        """
        if service_name not in self.classified_services:
            raise ValueError(f"Service {service_name} not registered")
        
        classified_info = self.classified_services[service_name]
        
        # Check if service is enabled for current deployment mode
        if not classified_info.config.enabled:
            raise RuntimeError(f"Service {service_name} is disabled for deployment mode {self.deployment_mode.value}")
        
        # Update access time
        classified_info.last_accessed = time.time()
        
        # Resume if suspended
        if classified_info.lifecycle_state == ServiceLifecycleState.SUSPENDED:
            await self._resume_service(service_name)
        
        # Load if not already loaded
        if classified_info.lifecycle_state in [ServiceLifecycleState.NOT_LOADED, ServiceLifecycleState.FAILED]:
            classified_info.lifecycle_state = ServiceLifecycleState.LOADING
            
            try:
                service_instance = await self.get_service(service_name)
                classified_info.lifecycle_state = ServiceLifecycleState.ACTIVE
                classified_info.idle_since = None
                
                logger.info(f"Loaded service on-demand: {service_name}")
                return service_instance
                
            except Exception as e:
                classified_info.lifecycle_state = ServiceLifecycleState.FAILED
                logger.error(f"Failed to load service on-demand {service_name}: {e}")
                raise
        
        # Return existing instance
        return await self.get_service(service_name)
    
    async def suspend_idle_services(self) -> List[str]:
        """
        Suspend services that have been idle for too long.
        
        Returns:
            List of suspended service names
        """
        suspended_services = []
        current_time = time.time()
        
        for service_name, classified_info in self.classified_services.items():
            config = classified_info.config
            
            # Skip essential services and services without idle timeout
            if (config.classification == ServiceClassification.ESSENTIAL or 
                config.idle_timeout is None or
                classified_info.lifecycle_state != ServiceLifecycleState.ACTIVE):
                continue
            
            # Check if service has been idle long enough
            if classified_info.last_accessed is not None:
                idle_time = current_time - classified_info.last_accessed
                if idle_time >= config.idle_timeout:
                    try:
                        await self._suspend_service(service_name)
                        suspended_services.append(service_name)
                    except Exception as e:
                        logger.error(f"Failed to suspend idle service {service_name}: {e}")
        
        if suspended_services:
            logger.info(f"Suspended {len(suspended_services)} idle services: {suspended_services}")
        
        return suspended_services
    
    async def _suspend_service(self, service_name: str) -> None:
        """Suspend a service to free up resources."""
        classified_info = self.classified_services[service_name]
        
        if service_name in self._instances:
            # Call shutdown method if available
            instance = self._instances[service_name]
            if hasattr(instance, 'shutdown'):
                try:
                    if asyncio.iscoroutinefunction(instance.shutdown):
                        await instance.shutdown()
                    else:
                        instance.shutdown()
                except Exception as e:
                    logger.warning(f"Error during service shutdown for {service_name}: {e}")
            
            # Remove from instances but keep registration
            del self._instances[service_name]
        
        # Update state
        classified_info.lifecycle_state = ServiceLifecycleState.SUSPENDED
        classified_info.suspension_count += 1
        classified_info.idle_since = time.time()
        
        # Update metrics
        self.performance_metrics["services_suspended"] += 1
        if classified_info.config.resource_requirements.memory_mb:
            self.performance_metrics["memory_saved_mb"] += classified_info.config.resource_requirements.memory_mb
        
        logger.info(f"Suspended service: {service_name}")
    
    async def _resume_service(self, service_name: str) -> None:
        """Resume a suspended service."""
        classified_info = self.classified_services[service_name]
        
        if classified_info.lifecycle_state == ServiceLifecycleState.SUSPENDED:
            classified_info.lifecycle_state = ServiceLifecycleState.LOADING
            
            # Service will be reloaded on next access
            self.performance_metrics["services_resumed"] += 1
            
            logger.info(f"Resuming service: {service_name}")
    
    async def _idle_monitoring_loop(self) -> None:
        """Background task to monitor and suspend idle services."""
        logger.info("Started idle service monitoring")
        
        try:
            while True:
                await asyncio.sleep(self.idle_check_interval)
                
                if self.auto_suspend_enabled:
                    await self.suspend_idle_services()
                
        except asyncio.CancelledError:
            logger.info("Idle monitoring stopped")
        except Exception as e:
            logger.error(f"Error in idle monitoring loop: {e}")
    
    def get_service_classification_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive report on service classifications and states.
        
        Returns:
            Dictionary with classification report
        """
        report = {
            "deployment_mode": self.deployment_mode.value,
            "total_services": len(self.classified_services),
            "by_classification": {},
            "by_lifecycle_state": {},
            "performance_metrics": self.performance_metrics.copy(),
            "startup_order": self.startup_order,
            "shutdown_order": self.shutdown_order,
            "services": {}
        }
        
        # Count by classification
        for classification in ServiceClassification:
            services = [
                info for info in self.classified_services.values()
                if info.config.classification == classification
            ]
            report["by_classification"][classification.value] = {
                "count": len(services),
                "enabled": len([s for s in services if s.config.enabled]),
                "services": [s.config.name for s in services]
            }
        
        # Count by lifecycle state
        for state in ServiceLifecycleState:
            services = [
                info for info in self.classified_services.values()
                if info.lifecycle_state == state
            ]
            report["by_lifecycle_state"][state.value] = {
                "count": len(services),
                "services": [s.config.name for s in services]
            }
        
        # Detailed service information
        for service_name, classified_info in self.classified_services.items():
            config = classified_info.config
            report["services"][service_name] = {
                "classification": config.classification.value,
                "lifecycle_state": classified_info.lifecycle_state.value,
                "enabled": config.enabled,
                "startup_priority": config.startup_priority,
                "idle_timeout": config.idle_timeout,
                "dependencies": config.dependencies,
                "last_accessed": classified_info.last_accessed,
                "suspension_count": classified_info.suspension_count,
                "resource_requirements": {
                    "memory_mb": config.resource_requirements.memory_mb,
                    "cpu_cores": config.resource_requirements.cpu_cores,
                    "gpu_memory_mb": config.resource_requirements.gpu_memory_mb,
                }
            }
        
        return report
    
    def validate_configuration(self) -> Dict[str, List[str]]:
        """
        Validate the current service configuration.
        
        Returns:
            Validation results with errors, warnings, and recommendations
        """
        return self.validator.validate_all()
    
    def get_consolidation_opportunities(self) -> Dict[str, List[str]]:
        """
        Get service consolidation opportunities.
        
        Returns:
            Dictionary mapping consolidation groups to service lists
        """
        return self.dependency_analyzer.get_consolidation_groups()
    
    def get_resource_analysis(self) -> Dict[str, Any]:
        """
        Get resource usage analysis by classification.
        
        Returns:
            Resource analysis report
        """
        return self.dependency_analyzer.analyze_resource_requirements()
    
    async def shutdown_all_services(self) -> None:
        """Shutdown all services in proper order."""
        logger.info("Shutting down all services...")
        
        # Stop idle monitoring
        if self.idle_check_task:
            self.idle_check_task.cancel()
            try:
                await self.idle_check_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown services in reverse dependency order
        for service_name in self.shutdown_order:
            if service_name in self._instances:
                try:
                    classified_info = self.classified_services[service_name]
                    
                    # Call graceful shutdown
                    instance = self._instances[service_name]
                    if hasattr(instance, 'shutdown'):
                        shutdown_timeout = classified_info.config.graceful_shutdown_timeout
                        
                        try:
                            if asyncio.iscoroutinefunction(instance.shutdown):
                                await asyncio.wait_for(instance.shutdown(), timeout=shutdown_timeout)
                            else:
                                instance.shutdown()
                        except asyncio.TimeoutError:
                            logger.warning(f"Service {service_name} shutdown timed out after {shutdown_timeout}s")
                        except Exception as e:
                            logger.error(f"Error during graceful shutdown of {service_name}: {e}")
                    
                    # Update state
                    classified_info.lifecycle_state = ServiceLifecycleState.SHUTDOWN
                    
                    logger.info(f"Shutdown service: {service_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to shutdown service {service_name}: {e}")
        
        # Clear instances
        self._instances.clear()
        
        logger.info("All services shutdown complete")
    
    def enable_auto_suspend(self, enabled: bool = True) -> None:
        """Enable or disable automatic service suspension."""
        self.auto_suspend_enabled = enabled
        logger.info(f"Auto-suspend {'enabled' if enabled else 'disabled'}")
    
    def set_idle_check_interval(self, interval_seconds: int) -> None:
        """Set the interval for idle service checks."""
        self.idle_check_interval = interval_seconds
        logger.info(f"Idle check interval set to {interval_seconds}s")