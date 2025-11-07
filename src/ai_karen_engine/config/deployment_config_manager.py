"""
Deployment Configuration Manager for Runtime Performance Optimization

This module provides comprehensive deployment mode configuration management with
dynamic service configuration, hot-reloading, and environment-specific profiles.
Implements task 10 requirements from the runtime-performance-optimization spec.
"""

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, Callable
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

try:
    from pydantic import BaseModel, ConfigDict, Field, ValidationError
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, ConfigDict, Field, ValidationError

logger = logging.getLogger(__name__)


class DeploymentMode(str, Enum):
    """Deployment mode types"""
    MINIMAL = "minimal"
    DEVELOPMENT = "development" 
    PRODUCTION = "production"
    TESTING = "testing"
    CUSTOM = "custom"


class ServiceClassification(str, Enum):
    """Service classification levels"""
    ESSENTIAL = "essential"
    OPTIONAL = "optional"
    BACKGROUND = "background"


class ConfigChangeType(str, Enum):
    """Configuration change types"""
    SERVICE_ADDED = "service_added"
    SERVICE_REMOVED = "service_removed"
    SERVICE_MODIFIED = "service_modified"
    DEPLOYMENT_MODE_CHANGED = "deployment_mode_changed"
    RESOURCE_LIMITS_CHANGED = "resource_limits_changed"
    PROFILE_UPDATED = "profile_updated"


@dataclass
class ResourceRequirements:
    """Resource requirements for services"""
    memory_mb: int = 64
    cpu_cores: float = 0.1
    gpu_memory_mb: Optional[int] = None
    disk_mb: Optional[int] = None
    network_bandwidth_mbps: Optional[float] = None


@dataclass
class ServiceConfig:
    """Service configuration model"""
    name: str
    classification: ServiceClassification
    startup_priority: int = 100
    dependencies: List[str] = field(default_factory=list)
    resource_requirements: ResourceRequirements = field(default_factory=ResourceRequirements)
    idle_timeout: Optional[int] = None
    health_check_interval: int = 60
    max_restart_attempts: int = 3
    graceful_shutdown_timeout: int = 10
    gpu_compatible: bool = False
    consolidation_group: Optional[str] = None
    enabled: bool = True
    auto_start: bool = True


@dataclass
class DeploymentProfile:
    """Deployment profile configuration"""
    name: str
    enabled_classifications: List[ServiceClassification]
    max_memory_mb: int = 4096
    max_services: int = 100
    max_cpu_cores: float = 8.0
    aggressive_idle_timeout: bool = False
    debug_services: bool = False
    performance_optimized: bool = False
    fast_startup: bool = False
    description: str = ""
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigChange:
    """Configuration change event"""
    change_type: ConfigChangeType
    timestamp: datetime
    affected_services: List[str]
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    description: str = ""


class ConfigValidationError(Exception):
    """Configuration validation error"""
    pass


class DeploymentConfigManager:
    """
    Deployment configuration manager with dynamic service management and hot-reloading.
    
    Features:
    - Multiple deployment modes (minimal, development, production, testing)
    - Dynamic service start/stop without restart
    - Environment-specific service profiles
    - Configuration validation and safety checks
    - Hot-reloading capability for runtime adjustments
    - Resource allocation management
    """
    
    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        enable_hot_reload: bool = True,
        reload_interval: float = 5.0,
        enable_validation: bool = True
    ):
        """
        Initialize deployment configuration manager.
        
        Args:
            config_path: Path to services configuration file
            enable_hot_reload: Enable automatic configuration reloading
            reload_interval: Hot reload check interval in seconds
            enable_validation: Enable configuration validation
        """
        self.config_path = Path(config_path) if config_path else Path("config/services.yml")
        self.enable_hot_reload = enable_hot_reload
        self.reload_interval = reload_interval
        self.enable_validation = enable_validation
        
        # Internal state
        self._config_lock = threading.RLock()
        self._services: Dict[str, ServiceConfig] = {}
        self._deployment_profiles: Dict[str, DeploymentProfile] = {}
        self._current_mode: DeploymentMode = DeploymentMode.DEVELOPMENT
        self._current_profile: Optional[DeploymentProfile] = None
        self._last_modified: Optional[float] = None
        self._change_listeners: List[Callable[[ConfigChange], None]] = []
        self._service_listeners: List[Callable[[str, str], None]] = []  # service_name, action
        self._hot_reload_task: Optional[asyncio.Task] = None
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="config-mgr")
        
        # Change history
        self._change_history: List[ConfigChange] = []
        self._max_history_size = 100
        
        logger.info(f"Deployment configuration manager initialized with config: {self.config_path}")
    
    async def initialize(self) -> None:
        """Initialize the configuration manager"""
        try:
            await self.load_configuration()
            
            if self.enable_hot_reload:
                self._hot_reload_task = asyncio.create_task(self._hot_reload_worker())
                logger.info("Hot reload monitoring started")
            
            logger.info("Deployment configuration manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize deployment configuration manager: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the configuration manager"""
        if self._hot_reload_task:
            self._hot_reload_task.cancel()
            try:
                await self._hot_reload_task
            except asyncio.CancelledError:
                pass
        
        self._executor.shutdown(wait=True)
        logger.info("Deployment configuration manager shutdown complete")
    
    async def load_configuration(self) -> None:
        """Load configuration from file"""
        with self._config_lock:
            try:
                if not self.config_path.exists():
                    logger.warning(f"Configuration file not found: {self.config_path}")
                    self._create_default_configuration()
                    return
                
                # Load configuration file
                config_data = await self._load_config_file()
                
                # Parse services
                services_data = config_data.get('services', {})
                self._services = {}
                
                for service_name, service_data in services_data.items():
                    service_config = self._parse_service_config(service_name, service_data)
                    self._services[service_name] = service_config
                
                # Parse deployment profiles
                profiles_data = config_data.get('deployment_profiles', {})
                self._deployment_profiles = {}
                
                for profile_name, profile_data in profiles_data.items():
                    profile = self._parse_deployment_profile(profile_name, profile_data)
                    self._deployment_profiles[profile_name] = profile
                
                # Set current deployment mode from environment or config
                mode_name = os.getenv('DEPLOYMENT_MODE', 'development')
                try:
                    self._current_mode = DeploymentMode(mode_name)
                except ValueError:
                    logger.warning(f"Invalid deployment mode: {mode_name}, using development")
                    self._current_mode = DeploymentMode.DEVELOPMENT
                
                # Set current profile
                self._current_profile = self._deployment_profiles.get(self._current_mode.value)
                
                # Update last modified time
                self._last_modified = self.config_path.stat().st_mtime
                
                # Validate configuration
                if self.enable_validation:
                    await self._validate_configuration()
                
                logger.info(f"Configuration loaded: {len(self._services)} services, "
                          f"{len(self._deployment_profiles)} profiles, mode: {self._current_mode}")
                
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                raise ConfigValidationError(f"Configuration loading failed: {e}")
    
    async def set_deployment_mode(self, mode: Union[DeploymentMode, str]) -> None:
        """
        Set deployment mode and apply corresponding profile.
        
        Args:
            mode: Deployment mode to set
        """
        if isinstance(mode, str):
            try:
                mode = DeploymentMode(mode)
            except ValueError:
                raise ConfigValidationError(f"Invalid deployment mode: {mode}")
        
        with self._config_lock:
            old_mode = self._current_mode
            self._current_mode = mode
            
            # Get corresponding profile
            profile = self._deployment_profiles.get(mode.value)
            if not profile:
                logger.warning(f"No profile found for deployment mode: {mode}")
                return
            
            old_profile = self._current_profile
            self._current_profile = profile
            
            # Record change
            change = ConfigChange(
                change_type=ConfigChangeType.DEPLOYMENT_MODE_CHANGED,
                timestamp=datetime.now(),
                affected_services=list(self._services.keys()),
                old_value=old_mode.value if old_mode else None,
                new_value=mode.value,
                description=f"Deployment mode changed from {old_mode} to {mode}"
            )
            
            self._add_change_to_history(change)
            await self._notify_change_listeners(change)
            
            logger.info(f"Deployment mode changed to: {mode}")
    
    async def get_services_for_current_mode(self) -> Dict[str, ServiceConfig]:
        """Get services that should be running for current deployment mode"""
        if not self._current_profile:
            return self._services
        
        enabled_classifications = set(self._current_profile.enabled_classifications)
        filtered_services = {}
        
        for name, service in self._services.items():
            if (service.classification in enabled_classifications and 
                service.enabled):
                filtered_services[name] = service
        
        return filtered_services
    
    async def start_service(self, service_name: str) -> bool:
        """
        Start a service dynamically.
        
        Args:
            service_name: Name of service to start
            
        Returns:
            True if service was started successfully
        """
        with self._config_lock:
            if service_name not in self._services:
                logger.error(f"Service not found: {service_name}")
                return False
            
            service = self._services[service_name]
            if not service.enabled:
                service.enabled = True
                
                # Record change
                change = ConfigChange(
                    change_type=ConfigChangeType.SERVICE_ADDED,
                    timestamp=datetime.now(),
                    affected_services=[service_name],
                    description=f"Service {service_name} started dynamically"
                )
                
                self._add_change_to_history(change)
                await self._notify_change_listeners(change)
                await self._notify_service_listeners(service_name, "start")
                
                logger.info(f"Service started: {service_name}")
                return True
            
            logger.warning(f"Service already running: {service_name}")
            return False
    
    async def stop_service(self, service_name: str) -> bool:
        """
        Stop a service dynamically.
        
        Args:
            service_name: Name of service to stop
            
        Returns:
            True if service was stopped successfully
        """
        with self._config_lock:
            if service_name not in self._services:
                logger.error(f"Service not found: {service_name}")
                return False
            
            service = self._services[service_name]
            if service.enabled:
                # Check if service is essential in current mode
                if (self._current_profile and 
                    service.classification == ServiceClassification.ESSENTIAL and
                    ServiceClassification.ESSENTIAL in self._current_profile.enabled_classifications):
                    logger.warning(f"Cannot stop essential service in current mode: {service_name}")
                    return False
                
                service.enabled = False
                
                # Record change
                change = ConfigChange(
                    change_type=ConfigChangeType.SERVICE_REMOVED,
                    timestamp=datetime.now(),
                    affected_services=[service_name],
                    description=f"Service {service_name} stopped dynamically"
                )
                
                self._add_change_to_history(change)
                await self._notify_change_listeners(change)
                await self._notify_service_listeners(service_name, "stop")
                
                logger.info(f"Service stopped: {service_name}")
                return True
            
            logger.warning(f"Service already stopped: {service_name}")
            return False
    
    async def update_service_config(self, service_name: str, updates: Dict[str, Any]) -> bool:
        """
        Update service configuration dynamically.
        
        Args:
            service_name: Name of service to update
            updates: Dictionary of configuration updates
            
        Returns:
            True if service was updated successfully
        """
        with self._config_lock:
            if service_name not in self._services:
                logger.error(f"Service not found: {service_name}")
                return False
            
            service = self._services[service_name]
            old_config = {
                'idle_timeout': service.idle_timeout,
                'resource_requirements': service.resource_requirements,
                'health_check_interval': service.health_check_interval
            }
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(service, key):
                    if key == 'resource_requirements' and isinstance(value, dict):
                        # Update resource requirements
                        for res_key, res_value in value.items():
                            if hasattr(service.resource_requirements, res_key):
                                setattr(service.resource_requirements, res_key, res_value)
                    else:
                        setattr(service, key, value)
                else:
                    logger.warning(f"Unknown service configuration key: {key}")
            
            # Validate updated configuration
            if self.enable_validation:
                try:
                    await self._validate_service_config(service)
                except ConfigValidationError as e:
                    logger.error(f"Service configuration validation failed: {e}")
                    return False
            
            # Record change
            change = ConfigChange(
                change_type=ConfigChangeType.SERVICE_MODIFIED,
                timestamp=datetime.now(),
                affected_services=[service_name],
                old_value=old_config,
                new_value=updates,
                description=f"Service {service_name} configuration updated"
            )
            
            self._add_change_to_history(change)
            await self._notify_change_listeners(change)
            await self._notify_service_listeners(service_name, "update")
            
            logger.info(f"Service configuration updated: {service_name}")
            return True
    
    async def get_resource_allocation(self) -> Dict[str, Any]:
        """Get current resource allocation summary"""
        services = await self.get_services_for_current_mode()
        
        total_memory = 0
        total_cpu = 0.0
        total_gpu_memory = 0
        service_count = len(services)
        
        for service in services.values():
            if service.enabled:
                total_memory += service.resource_requirements.memory_mb
                total_cpu += service.resource_requirements.cpu_cores
                if service.resource_requirements.gpu_memory_mb:
                    total_gpu_memory += service.resource_requirements.gpu_memory_mb
        
        profile_limits = {}
        if self._current_profile:
            profile_limits = {
                'max_memory_mb': self._current_profile.max_memory_mb,
                'max_services': self._current_profile.max_services,
                'max_cpu_cores': self._current_profile.max_cpu_cores
            }
        
        return {
            'current_allocation': {
                'memory_mb': total_memory,
                'cpu_cores': total_cpu,
                'gpu_memory_mb': total_gpu_memory,
                'service_count': service_count
            },
            'profile_limits': profile_limits,
            'utilization': {
                'memory_percent': (total_memory / self._current_profile.max_memory_mb * 100) if self._current_profile else 0,
                'cpu_percent': (total_cpu / self._current_profile.max_cpu_cores * 100) if self._current_profile else 0,
                'service_percent': (service_count / self._current_profile.max_services * 100) if self._current_profile else 0
            }
        }
    
    def get_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Get configuration for a specific service"""
        return self._services.get(service_name)
    
    def get_all_services(self) -> Dict[str, ServiceConfig]:
        """Get all service configurations"""
        return self._services.copy()
    
    def get_deployment_profiles(self) -> Dict[str, DeploymentProfile]:
        """Get all deployment profiles"""
        return self._deployment_profiles.copy()
    
    def get_current_mode(self) -> DeploymentMode:
        """Get current deployment mode"""
        return self._current_mode
    
    def get_current_profile(self) -> Optional[DeploymentProfile]:
        """Get current deployment profile"""
        return self._current_profile
    
    def get_change_history(self, limit: int = 50) -> List[ConfigChange]:
        """Get configuration change history"""
        return self._change_history[-limit:]
    
    def add_change_listener(self, listener: Callable[[ConfigChange], None]) -> None:
        """Add configuration change listener"""
        self._change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[ConfigChange], None]) -> None:
        """Remove configuration change listener"""
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)
    
    def add_service_listener(self, listener: Callable[[str, str], None]) -> None:
        """Add service state change listener"""
        self._service_listeners.append(listener)
    
    def remove_service_listener(self, listener: Callable[[str, str], None]) -> None:
        """Remove service state change listener"""
        if listener in self._service_listeners:
            self._service_listeners.remove(listener)
    
    async def save_configuration(self) -> None:
        """Save current configuration to file"""
        with self._config_lock:
            try:
                config_data = {
                    'services': {},
                    'deployment_profiles': {}
                }
                
                # Serialize services
                for name, service in self._services.items():
                    config_data['services'][name] = {
                        'classification': service.classification.value,
                        'startup_priority': service.startup_priority,
                        'dependencies': service.dependencies,
                        'resource_requirements': {
                            'memory_mb': service.resource_requirements.memory_mb,
                            'cpu_cores': service.resource_requirements.cpu_cores,
                            'gpu_memory_mb': service.resource_requirements.gpu_memory_mb,
                            'disk_mb': service.resource_requirements.disk_mb,
                            'network_bandwidth_mbps': service.resource_requirements.network_bandwidth_mbps
                        },
                        'idle_timeout': service.idle_timeout,
                        'health_check_interval': service.health_check_interval,
                        'max_restart_attempts': service.max_restart_attempts,
                        'graceful_shutdown_timeout': service.graceful_shutdown_timeout,
                        'gpu_compatible': service.gpu_compatible,
                        'consolidation_group': service.consolidation_group,
                        'enabled': service.enabled,
                        'auto_start': service.auto_start
                    }
                
                # Serialize deployment profiles
                for name, profile in self._deployment_profiles.items():
                    config_data['deployment_profiles'][name] = {
                        'enabled_classifications': [cls.value for cls in profile.enabled_classifications],
                        'max_memory_mb': profile.max_memory_mb,
                        'max_services': profile.max_services,
                        'max_cpu_cores': profile.max_cpu_cores,
                        'aggressive_idle_timeout': profile.aggressive_idle_timeout,
                        'debug_services': profile.debug_services,
                        'performance_optimized': profile.performance_optimized,
                        'fast_startup': profile.fast_startup,
                        'description': profile.description,
                        'custom_settings': profile.custom_settings
                    }
                
                # Write to file
                await self._save_config_file(config_data)
                
                logger.info(f"Configuration saved to: {self.config_path}")
                
            except Exception as e:
                logger.error(f"Failed to save configuration: {e}")
                raise
    
    # Private methods
    
    async def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration file"""
        def _load():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    if not YAML_AVAILABLE:
                        raise ImportError("PyYAML is required for YAML configuration files")
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, _load)
    
    async def _save_config_file(self, config_data: Dict[str, Any]) -> None:
        """Save configuration file"""
        def _save():
            # Create backup
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix(f'.backup.{int(time.time())}')
                backup_path.write_bytes(self.config_path.read_bytes())
            
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    if not YAML_AVAILABLE:
                        raise ImportError("PyYAML is required for YAML configuration files")
                    yaml.safe_dump(config_data, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_data, f, indent=2)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, _save)
    
    def _parse_service_config(self, name: str, data: Dict[str, Any]) -> ServiceConfig:
        """Parse service configuration from data"""
        resource_data = data.get('resource_requirements', {})
        resource_requirements = ResourceRequirements(
            memory_mb=resource_data.get('memory_mb', 64),
            cpu_cores=resource_data.get('cpu_cores', 0.1),
            gpu_memory_mb=resource_data.get('gpu_memory_mb'),
            disk_mb=resource_data.get('disk_mb'),
            network_bandwidth_mbps=resource_data.get('network_bandwidth_mbps')
        )
        
        return ServiceConfig(
            name=name,
            classification=ServiceClassification(data.get('classification', 'optional')),
            startup_priority=data.get('startup_priority', 100),
            dependencies=data.get('dependencies', []),
            resource_requirements=resource_requirements,
            idle_timeout=data.get('idle_timeout'),
            health_check_interval=data.get('health_check_interval', 60),
            max_restart_attempts=data.get('max_restart_attempts', 3),
            graceful_shutdown_timeout=data.get('graceful_shutdown_timeout', 10),
            gpu_compatible=data.get('gpu_compatible', False),
            consolidation_group=data.get('consolidation_group'),
            enabled=data.get('enabled', True),
            auto_start=data.get('auto_start', True)
        )
    
    def _parse_deployment_profile(self, name: str, data: Dict[str, Any]) -> DeploymentProfile:
        """Parse deployment profile from data"""
        enabled_classifications = [
            ServiceClassification(cls) for cls in data.get('enabled_classifications', ['essential'])
        ]
        
        return DeploymentProfile(
            name=name,
            enabled_classifications=enabled_classifications,
            max_memory_mb=data.get('max_memory_mb', 4096),
            max_services=data.get('max_services', 100),
            max_cpu_cores=data.get('max_cpu_cores', 8.0),
            aggressive_idle_timeout=data.get('aggressive_idle_timeout', False),
            debug_services=data.get('debug_services', False),
            performance_optimized=data.get('performance_optimized', False),
            fast_startup=data.get('fast_startup', False),
            description=data.get('description', ''),
            custom_settings=data.get('custom_settings', {})
        )
    
    async def _validate_configuration(self) -> None:
        """Validate entire configuration"""
        # Validate services
        for service in self._services.values():
            await self._validate_service_config(service)
        
        # Validate deployment profiles
        for profile in self._deployment_profiles.values():
            await self._validate_deployment_profile(profile)
        
        # Validate service dependencies
        await self._validate_service_dependencies()
        
        logger.info("Configuration validation completed successfully")
    
    async def _validate_service_config(self, service: ServiceConfig) -> None:
        """Validate individual service configuration"""
        # Check resource requirements
        if service.resource_requirements.memory_mb <= 0:
            raise ConfigValidationError(f"Service {service.name}: memory_mb must be positive")
        
        if service.resource_requirements.cpu_cores <= 0:
            raise ConfigValidationError(f"Service {service.name}: cpu_cores must be positive")
        
        # Check timeouts
        if service.idle_timeout is not None and service.idle_timeout <= 0:
            raise ConfigValidationError(f"Service {service.name}: idle_timeout must be positive")
        
        if service.health_check_interval <= 0:
            raise ConfigValidationError(f"Service {service.name}: health_check_interval must be positive")
        
        if service.graceful_shutdown_timeout <= 0:
            raise ConfigValidationError(f"Service {service.name}: graceful_shutdown_timeout must be positive")
    
    async def _validate_deployment_profile(self, profile: DeploymentProfile) -> None:
        """Validate deployment profile"""
        if profile.max_memory_mb <= 0:
            raise ConfigValidationError(f"Profile {profile.name}: max_memory_mb must be positive")
        
        if profile.max_services <= 0:
            raise ConfigValidationError(f"Profile {profile.name}: max_services must be positive")
        
        if profile.max_cpu_cores <= 0:
            raise ConfigValidationError(f"Profile {profile.name}: max_cpu_cores must be positive")
    
    async def _validate_service_dependencies(self) -> None:
        """Validate service dependency graph"""
        # Check for circular dependencies
        def has_circular_dependency(service_name: str, visited: Set[str], path: Set[str]) -> bool:
            if service_name in path:
                return True
            if service_name in visited:
                return False
            
            visited.add(service_name)
            path.add(service_name)
            
            service = self._services.get(service_name)
            if service:
                for dep in service.dependencies:
                    if has_circular_dependency(dep, visited, path):
                        return True
            
            path.remove(service_name)
            return False
        
        visited = set()
        for service_name in self._services:
            if has_circular_dependency(service_name, visited, set()):
                raise ConfigValidationError(f"Circular dependency detected involving service: {service_name}")
        
        # Check for missing dependencies
        for service_name, service in self._services.items():
            for dep in service.dependencies:
                if dep not in self._services:
                    raise ConfigValidationError(f"Service {service_name} depends on non-existent service: {dep}")
    
    def _create_default_configuration(self) -> None:
        """Create default configuration"""
        # Create minimal default services
        self._services = {
            'logging_service': ServiceConfig(
                name='logging_service',
                classification=ServiceClassification.ESSENTIAL,
                startup_priority=1,
                resource_requirements=ResourceRequirements(memory_mb=32, cpu_cores=0.1)
            ),
            'config_manager': ServiceConfig(
                name='config_manager',
                classification=ServiceClassification.ESSENTIAL,
                startup_priority=5,
                resource_requirements=ResourceRequirements(memory_mb=32, cpu_cores=0.1)
            )
        }
        
        # Create default deployment profiles
        self._deployment_profiles = {
            'minimal': DeploymentProfile(
                name='minimal',
                enabled_classifications=[ServiceClassification.ESSENTIAL],
                max_memory_mb=512,
                max_services=10,
                description="Minimal deployment with only essential services"
            ),
            'development': DeploymentProfile(
                name='development',
                enabled_classifications=[ServiceClassification.ESSENTIAL, ServiceClassification.OPTIONAL],
                max_memory_mb=2048,
                max_services=50,
                debug_services=True,
                description="Development mode with debugging capabilities"
            ),
            'production': DeploymentProfile(
                name='production',
                enabled_classifications=[ServiceClassification.ESSENTIAL, ServiceClassification.OPTIONAL, ServiceClassification.BACKGROUND],
                max_memory_mb=4096,
                max_services=100,
                performance_optimized=True,
                description="Full production deployment with all optimizations"
            )
        }
        
        logger.info("Created default configuration")
    
    async def _hot_reload_worker(self) -> None:
        """Hot reload worker task"""
        while True:
            try:
                await asyncio.sleep(self.reload_interval)
                
                if not self.config_path.exists():
                    continue
                
                current_mtime = self.config_path.stat().st_mtime
                if self._last_modified and current_mtime > self._last_modified:
                    logger.info("Configuration file changed, reloading...")
                    await self.load_configuration()
                    
                    # Notify listeners of reload
                    change = ConfigChange(
                        change_type=ConfigChangeType.PROFILE_UPDATED,
                        timestamp=datetime.now(),
                        affected_services=list(self._services.keys()),
                        description="Configuration reloaded from file"
                    )
                    
                    self._add_change_to_history(change)
                    await self._notify_change_listeners(change)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Hot reload error: {e}")
    
    def _add_change_to_history(self, change: ConfigChange) -> None:
        """Add change to history"""
        self._change_history.append(change)
        if len(self._change_history) > self._max_history_size:
            self._change_history = self._change_history[-self._max_history_size:]
    
    async def _notify_change_listeners(self, change: ConfigChange) -> None:
        """Notify configuration change listeners"""
        for listener in self._change_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(change)
                else:
                    listener(change)
            except Exception as e:
                logger.error(f"Error notifying change listener: {e}")
    
    async def _notify_service_listeners(self, service_name: str, action: str) -> None:
        """Notify service state change listeners"""
        for listener in self._service_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(service_name, action)
                else:
                    listener(service_name, action)
            except Exception as e:
                logger.error(f"Error notifying service listener: {e}")