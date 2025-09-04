"""
Performance Optimization Configuration Integration.

This module integrates performance optimization settings with the existing
configuration management system.
"""

import logging
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PerformanceConfig:
    """Performance optimization configuration."""
    
    # Core optimization settings
    enable_performance_optimization: bool = True
    deployment_mode: str = "development"
    enable_lazy_loading: bool = True
    enable_gpu_offloading: bool = True
    enable_service_consolidation: bool = True
    
    # Resource thresholds
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    response_time_threshold: float = 2.0
    
    # Startup optimization
    max_startup_time: float = 30.0
    essential_services_only: bool = False
    
    # Service lifecycle settings
    idle_timeout_seconds: int = 300
    health_check_interval: int = 60
    max_restart_attempts: int = 3
    
    # Async processing settings
    max_worker_threads: int = 4
    task_queue_size: int = 1000
    enable_parallel_processing: bool = True
    
    # GPU settings
    gpu_memory_limit_mb: Optional[int] = None
    enable_gpu_memory_optimization: bool = True
    
    # Monitoring settings
    enable_performance_monitoring: bool = True
    metrics_collection_interval: int = 30
    enable_performance_alerts: bool = True
    
    # Logging settings
    log_level: str = "INFO"
    enable_performance_logging: bool = True
    performance_log_file: str = "logs/performance.log"
    
    # Advanced settings
    enable_service_mesh: bool = False
    enable_distributed_processing: bool = False
    cache_size_mb: int = 256
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceConfig':
        """Create configuration from dictionary."""
        # Filter out unknown fields
        valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
    @classmethod
    def from_environment(cls) -> 'PerformanceConfig':
        """Create configuration from environment variables."""
        config = cls()
        
        # Map environment variables to configuration fields
        env_mapping = {
            'ENABLE_PERFORMANCE_OPTIMIZATION': ('enable_performance_optimization', bool),
            'DEPLOYMENT_MODE': ('deployment_mode', str),
            'ENABLE_LAZY_LOADING': ('enable_lazy_loading', bool),
            'ENABLE_GPU_OFFLOADING': ('enable_gpu_offloading', bool),
            'ENABLE_SERVICE_CONSOLIDATION': ('enable_service_consolidation', bool),
            'CPU_THRESHOLD': ('cpu_threshold', float),
            'MEMORY_THRESHOLD': ('memory_threshold', float),
            'RESPONSE_TIME_THRESHOLD': ('response_time_threshold', float),
            'MAX_STARTUP_TIME': ('max_startup_time', float),
            'ESSENTIAL_SERVICES_ONLY': ('essential_services_only', bool),
            'IDLE_TIMEOUT_SECONDS': ('idle_timeout_seconds', int),
            'HEALTH_CHECK_INTERVAL': ('health_check_interval', int),
            'MAX_RESTART_ATTEMPTS': ('max_restart_attempts', int),
            'MAX_WORKER_THREADS': ('max_worker_threads', int),
            'TASK_QUEUE_SIZE': ('task_queue_size', int),
            'ENABLE_PARALLEL_PROCESSING': ('enable_parallel_processing', bool),
            'GPU_MEMORY_LIMIT_MB': ('gpu_memory_limit_mb', int),
            'ENABLE_GPU_MEMORY_OPTIMIZATION': ('enable_gpu_memory_optimization', bool),
            'ENABLE_PERFORMANCE_MONITORING': ('enable_performance_monitoring', bool),
            'METRICS_COLLECTION_INTERVAL': ('metrics_collection_interval', int),
            'ENABLE_PERFORMANCE_ALERTS': ('enable_performance_alerts', bool),
            'LOG_LEVEL': ('log_level', str),
            'ENABLE_PERFORMANCE_LOGGING': ('enable_performance_logging', bool),
            'PERFORMANCE_LOG_FILE': ('performance_log_file', str),
            'ENABLE_SERVICE_MESH': ('enable_service_mesh', bool),
            'ENABLE_DISTRIBUTED_PROCESSING': ('enable_distributed_processing', bool),
            'CACHE_SIZE_MB': ('cache_size_mb', int),
        }
        
        for env_var, (field_name, field_type) in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    if field_type == bool:
                        value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif field_type == int:
                        value = int(env_value)
                    elif field_type == float:
                        value = float(env_value)
                    else:
                        value = env_value
                    
                    setattr(config, field_name, value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid value for {env_var}: {env_value}, using default. Error: {e}")
        
        return config
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        issues = []
        
        # Validate thresholds
        if not 0 < self.cpu_threshold <= 100:
            issues.append("cpu_threshold must be between 0 and 100")
        
        if not 0 < self.memory_threshold <= 100:
            issues.append("memory_threshold must be between 0 and 100")
        
        if self.response_time_threshold <= 0:
            issues.append("response_time_threshold must be positive")
        
        if self.max_startup_time <= 0:
            issues.append("max_startup_time must be positive")
        
        # Validate worker settings
        if self.max_worker_threads <= 0:
            issues.append("max_worker_threads must be positive")
        
        if self.task_queue_size <= 0:
            issues.append("task_queue_size must be positive")
        
        # Validate intervals
        if self.idle_timeout_seconds <= 0:
            issues.append("idle_timeout_seconds must be positive")
        
        if self.health_check_interval <= 0:
            issues.append("health_check_interval must be positive")
        
        if self.metrics_collection_interval <= 0:
            issues.append("metrics_collection_interval must be positive")
        
        # Validate GPU settings
        if self.gpu_memory_limit_mb is not None and self.gpu_memory_limit_mb <= 0:
            issues.append("gpu_memory_limit_mb must be positive if specified")
        
        # Validate cache size
        if self.cache_size_mb <= 0:
            issues.append("cache_size_mb must be positive")
        
        # Log validation issues
        if issues:
            logger.error("Performance configuration validation failed:")
            for issue in issues:
                logger.error(f"  • {issue}")
            return False
        
        return True
    
    def get_deployment_profile(self) -> Dict[str, Any]:
        """Get deployment-specific configuration profile."""
        profiles = {
            "minimal": {
                "essential_services_only": True,
                "enable_lazy_loading": True,
                "enable_service_consolidation": True,
                "max_worker_threads": 2,
                "cache_size_mb": 128,
                "enable_performance_monitoring": False,
                "enable_performance_alerts": False
            },
            "development": {
                "essential_services_only": False,
                "enable_lazy_loading": True,
                "enable_service_consolidation": False,
                "max_worker_threads": 4,
                "cache_size_mb": 256,
                "enable_performance_monitoring": True,
                "enable_performance_alerts": True,
                "log_level": "DEBUG"
            },
            "production": {
                "essential_services_only": False,
                "enable_lazy_loading": True,
                "enable_service_consolidation": True,
                "max_worker_threads": 8,
                "cache_size_mb": 512,
                "enable_performance_monitoring": True,
                "enable_performance_alerts": True,
                "cpu_threshold": 70.0,
                "memory_threshold": 80.0,
                "response_time_threshold": 1.0
            },
            "testing": {
                "essential_services_only": True,
                "enable_lazy_loading": False,
                "enable_service_consolidation": False,
                "max_worker_threads": 2,
                "cache_size_mb": 64,
                "enable_performance_monitoring": False,
                "enable_performance_alerts": False,
                "log_level": "WARNING"
            }
        }
        
        return profiles.get(self.deployment_mode, profiles["development"])
    
    def apply_deployment_profile(self) -> None:
        """Apply deployment-specific configuration."""
        profile = self.get_deployment_profile()
        
        for key, value in profile.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"Applied deployment profile setting: {key} = {value}")


class PerformanceConfigManager:
    """Manager for performance optimization configuration."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/performance.yml"
        self.config: Optional[PerformanceConfig] = None
        self._config_cache: Dict[str, Any] = {}
    
    async def load_config(self) -> PerformanceConfig:
        """Load performance configuration from file and environment."""
        try:
            # Start with environment-based configuration
            config = PerformanceConfig.from_environment()
            
            # Load from file if it exists
            config_path = Path(self.config_file)
            if config_path.exists():
                try:
                    import yaml
                    with open(config_path, 'r') as f:
                        file_config = yaml.safe_load(f)
                    
                    # Merge file configuration with environment configuration
                    if file_config:
                        file_based_config = PerformanceConfig.from_dict(file_config)
                        # Environment variables take precedence
                        for field in config.__dataclass_fields__:
                            if getattr(config, field) == getattr(PerformanceConfig(), field):
                                # Use file value if environment value is default
                                setattr(config, field, getattr(file_based_config, field))
                    
                    logger.info(f"Loaded performance configuration from {config_path}")
                    
                except Exception as e:
                    logger.warning(f"Failed to load configuration file {config_path}: {e}")
            
            # Apply deployment profile
            config.apply_deployment_profile()
            
            # Validate configuration
            if not config.validate():
                logger.warning("Performance configuration validation failed, using defaults")
                config = PerformanceConfig()
                config.apply_deployment_profile()
            
            self.config = config
            self._config_cache = config.to_dict()
            
            logger.info(f"Performance optimization configuration loaded:")
            logger.info(f"  • Deployment mode: {config.deployment_mode}")
            logger.info(f"  • Optimization enabled: {config.enable_performance_optimization}")
            logger.info(f"  • Lazy loading: {config.enable_lazy_loading}")
            logger.info(f"  • GPU offloading: {config.enable_gpu_offloading}")
            logger.info(f"  • Service consolidation: {config.enable_service_consolidation}")
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to load performance configuration: {e}")
            # Return default configuration
            config = PerformanceConfig()
            config.apply_deployment_profile()
            self.config = config
            return config
    
    def get_config(self) -> Optional[PerformanceConfig]:
        """Get current configuration."""
        return self.config
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific configuration setting."""
        if self.config:
            return getattr(self.config, key, default)
        return default
    
    async def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration settings."""
        if not self.config:
            await self.load_config()
        
        try:
            # Apply updates
            for key, value in updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    logger.info(f"Updated performance setting: {key} = {value}")
                else:
                    logger.warning(f"Unknown performance setting: {key}")
            
            # Validate updated configuration
            if not self.config.validate():
                logger.error("Configuration validation failed after update")
                return False
            
            # Update cache
            self._config_cache = self.config.to_dict()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update performance configuration: {e}")
            return False
    
    async def save_config(self) -> bool:
        """Save current configuration to file."""
        if not self.config:
            return False
        
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            import yaml
            with open(config_path, 'w') as f:
                yaml.dump(self.config.to_dict(), f, default_flow_style=False)
            
            logger.info(f"Saved performance configuration to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save performance configuration: {e}")
            return False


# Global configuration manager instance
_config_manager: Optional[PerformanceConfigManager] = None


def get_performance_config_manager() -> PerformanceConfigManager:
    """Get the global performance configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = PerformanceConfigManager()
    return _config_manager


async def load_performance_config() -> PerformanceConfig:
    """Load performance configuration."""
    manager = get_performance_config_manager()
    return await manager.load_config()


def get_performance_config() -> Optional[PerformanceConfig]:
    """Get current performance configuration."""
    manager = get_performance_config_manager()
    return manager.get_config()