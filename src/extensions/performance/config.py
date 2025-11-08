"""
Performance Configuration

Configuration settings for extension performance optimization.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class CacheConfig:
    """Configuration for extension caching."""
    max_size_mb: int = 256
    max_entries: int = 1000
    default_ttl: Optional[float] = 3600  # 1 hour
    cleanup_interval: float = 300  # 5 minutes
    enable_manifest_cache: bool = True
    enable_class_cache: bool = True


@dataclass
class LazyLoadingConfig:
    """Configuration for lazy loading."""
    max_concurrent_loads: int = 5
    default_strategy: str = "lazy"  # eager, lazy, on_demand, background
    background_load_delay: float = 1.0
    loading_timeout: float = 300.0  # 5 minutes


@dataclass
class ResourceOptimizationConfig:
    """Configuration for resource optimization."""
    monitoring_interval: float = 30.0
    optimization_interval: float = 300.0  # 5 minutes
    memory_threshold: float = 0.8  # 80% of system memory
    cpu_threshold: float = 0.7  # 70% of system CPU
    enable_auto_optimization: bool = True
    enable_garbage_collection: bool = True


@dataclass
class ScalingConfig:
    """Configuration for horizontal scaling."""
    enable_scaling: bool = False
    metrics_collection_interval: float = 30.0
    scaling_evaluation_interval: float = 60.0
    health_check_interval: float = 30.0
    default_min_instances: int = 1
    default_max_instances: int = 5
    default_cooldown_seconds: float = 300.0


@dataclass
class MonitoringConfig:
    """Configuration for performance monitoring."""
    enable_monitoring: bool = True
    monitoring_interval: float = 30.0
    alert_check_interval: float = 60.0
    metrics_retention_hours: float = 168.0  # 1 week
    enable_alerting: bool = True
    export_metrics: bool = False
    metrics_export_path: Optional[Path] = None


@dataclass
class ExtensionPerformanceConfig:
    """Performance configuration for a specific extension."""
    extension_name: str
    loading_strategy: str = "lazy"
    loading_priority: int = 100
    loading_dependencies: List[str] = field(default_factory=list)
    loading_conditions: List[str] = field(default_factory=list)
    
    # Resource limits
    max_memory_mb: Optional[float] = None
    max_cpu_percent: Optional[float] = None
    max_disk_io_mb_per_sec: Optional[float] = None
    max_network_io_mb_per_sec: Optional[float] = None
    max_file_handles: Optional[int] = None
    max_threads: Optional[int] = None
    
    # Scaling configuration
    enable_scaling: bool = False
    scaling_strategy: str = "none"  # none, horizontal, vertical, auto
    min_instances: int = 1
    max_instances: int = 5
    scaling_rules: List[Dict[str, Any]] = field(default_factory=list)
    
    # Monitoring thresholds
    performance_thresholds: Dict[str, float] = field(default_factory=dict)
    enable_custom_metrics: bool = False


@dataclass
class PerformanceConfig:
    """Main performance configuration."""
    cache: CacheConfig = field(default_factory=CacheConfig)
    lazy_loading: LazyLoadingConfig = field(default_factory=LazyLoadingConfig)
    resource_optimization: ResourceOptimizationConfig = field(default_factory=ResourceOptimizationConfig)
    scaling: ScalingConfig = field(default_factory=ScalingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Extension-specific configurations
    extension_configs: Dict[str, ExtensionPerformanceConfig] = field(default_factory=dict)
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'PerformanceConfig':
        """Load configuration from a JSON file."""
        if not config_path.exists():
            return cls()
        
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceConfig':
        """Create configuration from a dictionary."""
        config = cls()
        
        # Load main configuration sections
        if 'cache' in data:
            config.cache = CacheConfig(**data['cache'])
        
        if 'lazy_loading' in data:
            config.lazy_loading = LazyLoadingConfig(**data['lazy_loading'])
        
        if 'resource_optimization' in data:
            config.resource_optimization = ResourceOptimizationConfig(**data['resource_optimization'])
        
        if 'scaling' in data:
            config.scaling = ScalingConfig(**data['scaling'])
        
        if 'monitoring' in data:
            monitoring_data = data['monitoring'].copy()
            if 'metrics_export_path' in monitoring_data and monitoring_data['metrics_export_path']:
                monitoring_data['metrics_export_path'] = Path(monitoring_data['metrics_export_path'])
            config.monitoring = MonitoringConfig(**monitoring_data)
        
        # Load extension-specific configurations
        if 'extensions' in data:
            for ext_name, ext_data in data['extensions'].items():
                config.extension_configs[ext_name] = ExtensionPerformanceConfig(
                    extension_name=ext_name,
                    **ext_data
                )
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        result = {
            'cache': self.cache.__dict__,
            'lazy_loading': self.lazy_loading.__dict__,
            'resource_optimization': self.resource_optimization.__dict__,
            'scaling': self.scaling.__dict__,
            'monitoring': self.monitoring.__dict__.copy()
        }
        
        # Convert Path objects to strings
        if result['monitoring']['metrics_export_path']:
            result['monitoring']['metrics_export_path'] = str(result['monitoring']['metrics_export_path'])
        
        # Add extension configurations
        if self.extension_configs:
            result['extensions'] = {}
            for ext_name, ext_config in self.extension_configs.items():
                result['extensions'][ext_name] = ext_config.__dict__.copy()
                # Remove extension_name from the dict as it's the key
                result['extensions'][ext_name].pop('extension_name', None)
        
        return result
    
    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to a JSON file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def get_extension_config(self, extension_name: str) -> ExtensionPerformanceConfig:
        """Get configuration for a specific extension."""
        if extension_name not in self.extension_configs:
            self.extension_configs[extension_name] = ExtensionPerformanceConfig(
                extension_name=extension_name
            )
        
        return self.extension_configs[extension_name]
    
    def set_extension_config(
        self,
        extension_name: str,
        config: ExtensionPerformanceConfig
    ) -> None:
        """Set configuration for a specific extension."""
        config.extension_name = extension_name
        self.extension_configs[extension_name] = config


# Default performance configurations for different extension types
DEFAULT_EXTENSION_CONFIGS = {
    'security': ExtensionPerformanceConfig(
        extension_name='security',
        loading_strategy='eager',
        loading_priority=10,
        max_memory_mb=512,
        max_cpu_percent=50,
        performance_thresholds={
            'cpu_usage_percent': 60,
            'memory_usage_mb': 400,
            'average_response_time_ms': 500
        }
    ),
    'auth': ExtensionPerformanceConfig(
        extension_name='auth',
        loading_strategy='eager',
        loading_priority=20,
        max_memory_mb=256,
        max_cpu_percent=30,
        performance_thresholds={
            'cpu_usage_percent': 40,
            'memory_usage_mb': 200,
            'average_response_time_ms': 200
        }
    ),
    'analytics': ExtensionPerformanceConfig(
        extension_name='analytics',
        loading_strategy='lazy',
        loading_priority=100,
        max_memory_mb=1024,
        max_cpu_percent=70,
        enable_scaling=True,
        scaling_strategy='auto',
        min_instances=1,
        max_instances=3,
        scaling_rules=[
            {
                'trigger': 'cpu_usage',
                'threshold_up': 70,
                'threshold_down': 30,
                'cooldown_seconds': 300,
                'min_instances': 1,
                'max_instances': 3,
                'scale_up_step': 1,
                'scale_down_step': 1
            }
        ],
        performance_thresholds={
            'cpu_usage_percent': 80,
            'memory_usage_mb': 800,
            'average_response_time_ms': 2000
        }
    ),
    'automation': ExtensionPerformanceConfig(
        extension_name='automation',
        loading_strategy='background',
        loading_priority=150,
        max_memory_mb=512,
        max_cpu_percent=60,
        enable_scaling=True,
        scaling_strategy='auto',
        min_instances=1,
        max_instances=5,
        scaling_rules=[
            {
                'trigger': 'queue_length',
                'threshold_up': 10,
                'threshold_down': 2,
                'cooldown_seconds': 180,
                'min_instances': 1,
                'max_instances': 5,
                'scale_up_step': 1,
                'scale_down_step': 1
            }
        ],
        performance_thresholds={
            'cpu_usage_percent': 70,
            'memory_usage_mb': 400,
            'queue_length': 20
        }
    )
}


def create_default_config() -> PerformanceConfig:
    """Create a default performance configuration."""
    config = PerformanceConfig()
    
    # Add default extension configurations
    for ext_name, ext_config in DEFAULT_EXTENSION_CONFIGS.items():
        config.extension_configs[ext_name] = ext_config
    
    return config


def load_config_from_environment() -> PerformanceConfig:
    """Load configuration from environment variables."""
    import os
    
    config = PerformanceConfig()
    
    # Cache configuration
    if os.getenv('EXTENSION_CACHE_SIZE_MB'):
        config.cache.max_size_mb = int(os.getenv('EXTENSION_CACHE_SIZE_MB'))
    
    if os.getenv('EXTENSION_CACHE_TTL'):
        config.cache.default_ttl = float(os.getenv('EXTENSION_CACHE_TTL'))
    
    # Resource optimization configuration
    if os.getenv('EXTENSION_MEMORY_THRESHOLD'):
        config.resource_optimization.memory_threshold = float(os.getenv('EXTENSION_MEMORY_THRESHOLD'))
    
    if os.getenv('EXTENSION_CPU_THRESHOLD'):
        config.resource_optimization.cpu_threshold = float(os.getenv('EXTENSION_CPU_THRESHOLD'))
    
    # Scaling configuration
    if os.getenv('EXTENSION_ENABLE_SCALING'):
        config.scaling.enable_scaling = os.getenv('EXTENSION_ENABLE_SCALING').lower() == 'true'
    
    # Monitoring configuration
    if os.getenv('EXTENSION_ENABLE_MONITORING'):
        config.monitoring.enable_monitoring = os.getenv('EXTENSION_ENABLE_MONITORING').lower() == 'true'
    
    if os.getenv('EXTENSION_METRICS_RETENTION_HOURS'):
        config.monitoring.metrics_retention_hours = float(os.getenv('EXTENSION_METRICS_RETENTION_HOURS'))
    
    return config