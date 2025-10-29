"""
Optimization Configuration Manager

Manages configuration for response optimization settings while maintaining
existing reasoning capabilities and system functionality.

Requirements addressed:
- Configuration management for all optimization components
- Integration with existing configuration systems
- Preservation of existing reasoning capabilities
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

logger = logging.getLogger("kari.optimization_configuration_manager")

@dataclass
class ModelDiscoveryConfig:
    """Configuration for model discovery engine."""
    enable_discovery: bool = True
    scan_interval_minutes: int = 30
    models_directory: str = "models"
    supported_formats: List[str] = field(default_factory=lambda: [
        "gguf", "safetensors", "bin", "pt", "pth"
    ])
    enable_metadata_extraction: bool = True
    enable_capability_detection: bool = True
    max_model_size_gb: float = 50.0
    enable_background_validation: bool = True

@dataclass
class ModelRoutingConfig:
    """Configuration for intelligent model routing."""
    enable_routing: bool = True
    enable_fallback: bool = True
    connection_timeout_seconds: int = 30
    max_retry_attempts: int = 3
    enable_load_balancing: bool = False
    routing_strategy: str = "capability_based"  # capability_based, performance_based, round_robin
    enable_model_switching: bool = True
    preserve_profile_routing: bool = True

@dataclass
class CacheConfig:
    """Configuration for smart caching system."""
    enable_caching: bool = True
    cache_size_mb: int = 500
    default_ttl_seconds: int = 3600
    enable_intelligent_invalidation: bool = True
    enable_cache_warming: bool = True
    cache_hit_threshold: float = 0.7
    enable_distributed_cache: bool = False
    compression_enabled: bool = True

@dataclass
class PerformanceConfig:
    """Configuration for performance optimization."""
    enable_optimization: bool = True
    cpu_threshold_percent: float = 5.0
    memory_threshold_mb: float = 500.0
    enable_resource_monitoring: bool = True
    enable_automatic_optimization: bool = True
    optimization_interval_seconds: int = 60
    enable_performance_alerts: bool = True
    alert_cooldown_seconds: int = 300

@dataclass
class ContentOptimizationConfig:
    """Configuration for content optimization."""
    enable_optimization: bool = True
    enable_redundancy_elimination: bool = True
    enable_relevance_analysis: bool = True
    enable_depth_adaptation: bool = True
    enable_format_optimization: bool = True
    max_response_length: int = 4000
    enable_progressive_delivery: bool = True

@dataclass
class StreamingConfig:
    """Configuration for progressive response streaming."""
    enable_streaming: bool = True
    chunk_size_bytes: int = 1024
    enable_priority_ordering: bool = True
    enable_real_time_feedback: bool = True
    streaming_timeout_seconds: int = 30
    enable_error_recovery: bool = True

@dataclass
class CudaConfig:
    """Configuration for CUDA acceleration."""
    enable_cuda: bool = True
    auto_detect_devices: bool = True
    preferred_device_id: Optional[int] = None
    memory_fraction: float = 0.8
    enable_memory_optimization: bool = True
    enable_batch_processing: bool = True
    fallback_to_cpu: bool = True

@dataclass
class MonitoringConfig:
    """Configuration for performance monitoring."""
    enable_monitoring: bool = True
    metrics_retention_hours: int = 24
    enable_real_time_alerts: bool = True
    enable_dashboard: bool = True
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "response_time_ms": 5000,
        "cpu_usage_percent": 80,
        "memory_usage_mb": 1000,
        "error_rate_percent": 10,
        "cache_hit_rate_percent": 30
    })

@dataclass
class ReasoningPreservationConfig:
    """Configuration for reasoning preservation."""
    preserve_decision_engine: bool = True
    preserve_flow_manager: bool = True
    preserve_tinyllama_scaffolding: bool = True
    preserve_profile_routing: bool = True
    preserve_memory_integration: bool = True
    preserve_personality_application: bool = True
    enable_reasoning_hooks: bool = True
    enable_performance_tracking: bool = True

@dataclass
class OptimizationConfiguration:
    """Complete optimization configuration."""
    model_discovery: ModelDiscoveryConfig = field(default_factory=ModelDiscoveryConfig)
    model_routing: ModelRoutingConfig = field(default_factory=ModelRoutingConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    content_optimization: ContentOptimizationConfig = field(default_factory=ContentOptimizationConfig)
    streaming: StreamingConfig = field(default_factory=StreamingConfig)
    cuda: CudaConfig = field(default_factory=CudaConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    reasoning_preservation: ReasoningPreservationConfig = field(default_factory=ReasoningPreservationConfig)
    
    # Global settings
    enable_optimization_system: bool = True
    optimization_level: str = "balanced"  # conservative, balanced, aggressive
    enable_experimental_features: bool = False
    config_version: str = "1.0"
    last_updated: float = field(default_factory=time.time)

class OptimizationConfigurationManager:
    """
    Manages optimization configuration while preserving existing system functionality.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.logger = logging.getLogger("kari.optimization_config_manager")
        self.config_path = config_path or Path("config/optimization_config.json")
        
        # Configuration state
        self.config = OptimizationConfiguration()
        self.config_callbacks: List[Callable] = []
        self.validation_rules: Dict[str, Callable] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Auto-save settings
        self.auto_save_enabled = True
        self.auto_save_interval = 60  # seconds
        self._last_save_time = 0.0
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing configuration
        self._load_configuration()
        
        # Set up validation rules
        self._setup_validation_rules()
        
        self.logger.info(f"Optimization Configuration Manager initialized with config: {self.config_path}")
    
    def _load_configuration(self):
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Deserialize configuration
                self.config = self._deserialize_config(config_data)
                self.logger.info(f"Loaded optimization configuration from {self.config_path}")
            else:
                # Create default configuration
                self._save_configuration()
                self.logger.info("Created default optimization configuration")
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Use default configuration on error
            self.config = OptimizationConfiguration()
    
    def _save_configuration(self):
        """Save configuration to file."""
        try:
            with self._lock:
                config_data = self._serialize_config(self.config)
                config_data["last_updated"] = time.time()
                
                # Write to temporary file first, then rename for atomicity
                temp_path = self.config_path.with_suffix('.tmp')
                with open(temp_path, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                temp_path.rename(self.config_path)
                self._last_save_time = time.time()
                
            self.logger.debug(f"Saved optimization configuration to {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def _serialize_config(self, config: OptimizationConfiguration) -> Dict[str, Any]:
        """Serialize configuration to dictionary."""
        return asdict(config)
    
    def _deserialize_config(self, config_data: Dict[str, Any]) -> OptimizationConfiguration:
        """Deserialize configuration from dictionary."""
        try:
            # Handle nested dataclass deserialization
            config = OptimizationConfiguration()
            
            # Update top-level fields
            for key, value in config_data.items():
                if hasattr(config, key) and not isinstance(getattr(config, key), (
                    ModelDiscoveryConfig, ModelRoutingConfig, CacheConfig, 
                    PerformanceConfig, ContentOptimizationConfig, StreamingConfig,
                    CudaConfig, MonitoringConfig, ReasoningPreservationConfig
                )):
                    setattr(config, key, value)
            
            # Handle nested configurations
            if "model_discovery" in config_data:
                config.model_discovery = ModelDiscoveryConfig(**config_data["model_discovery"])
            
            if "model_routing" in config_data:
                config.model_routing = ModelRoutingConfig(**config_data["model_routing"])
            
            if "cache" in config_data:
                config.cache = CacheConfig(**config_data["cache"])
            
            if "performance" in config_data:
                config.performance = PerformanceConfig(**config_data["performance"])
            
            if "content_optimization" in config_data:
                config.content_optimization = ContentOptimizationConfig(**config_data["content_optimization"])
            
            if "streaming" in config_data:
                config.streaming = StreamingConfig(**config_data["streaming"])
            
            if "cuda" in config_data:
                config.cuda = CudaConfig(**config_data["cuda"])
            
            if "monitoring" in config_data:
                monitoring_data = config_data["monitoring"]
                # Handle alert_thresholds separately
                if "alert_thresholds" not in monitoring_data:
                    monitoring_data["alert_thresholds"] = MonitoringConfig().alert_thresholds
                config.monitoring = MonitoringConfig(**monitoring_data)
            
            if "reasoning_preservation" in config_data:
                config.reasoning_preservation = ReasoningPreservationConfig(**config_data["reasoning_preservation"])
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to deserialize configuration: {e}")
            return OptimizationConfiguration()
    
    def _setup_validation_rules(self):
        """Set up configuration validation rules."""
        self.validation_rules = {
            "cpu_threshold": lambda config: 0 < config.performance.cpu_threshold_percent <= 100,
            "memory_threshold": lambda config: config.performance.memory_threshold_mb > 0,
            "cache_size": lambda config: config.cache.cache_size_mb > 0,
            "ttl_positive": lambda config: config.cache.default_ttl_seconds > 0,
            "model_size_limit": lambda config: config.model_discovery.max_model_size_gb > 0,
            "scan_interval": lambda config: config.model_discovery.scan_interval_minutes > 0,
            "timeout_positive": lambda config: config.model_routing.connection_timeout_seconds > 0,
            "retry_attempts": lambda config: config.model_routing.max_retry_attempts >= 0,
            "chunk_size": lambda config: config.streaming.chunk_size_bytes > 0,
            "cuda_memory_fraction": lambda config: 0 < config.cuda.memory_fraction <= 1.0,
            "metrics_retention": lambda config: config.monitoring.metrics_retention_hours > 0
        }
    
    def validate_configuration(self, config: Optional[OptimizationConfiguration] = None) -> Dict[str, List[str]]:
        """Validate configuration against rules."""
        config = config or self.config
        validation_errors = {}
        
        try:
            for rule_name, rule_func in self.validation_rules.items():
                try:
                    if not rule_func(config):
                        category = rule_name.split('_')[0]
                        if category not in validation_errors:
                            validation_errors[category] = []
                        validation_errors[category].append(f"Validation failed: {rule_name}")
                except Exception as e:
                    if "validation" not in validation_errors:
                        validation_errors["validation"] = []
                    validation_errors["validation"].append(f"Rule {rule_name} error: {str(e)}")
            
            # Additional logical validations
            if config.performance.cpu_threshold_percent > 50:
                if "performance" not in validation_errors:
                    validation_errors["performance"] = []
                validation_errors["performance"].append("CPU threshold above 50% may impact system performance")
            
            if config.cache.cache_size_mb > 2000:
                if "cache" not in validation_errors:
                    validation_errors["cache"] = []
                validation_errors["cache"].append("Cache size above 2GB may consume excessive memory")
            
            return validation_errors
            
        except Exception as e:
            return {"validation": [f"Validation process failed: {str(e)}"]}
    
    def get_configuration(self) -> OptimizationConfiguration:
        """Get current configuration."""
        with self._lock:
            return self.config
    
    def update_configuration(self, updates: Dict[str, Any], validate: bool = True) -> bool:
        """Update configuration with new values."""
        try:
            with self._lock:
                # Create a copy for validation
                new_config = self._deserialize_config(self._serialize_config(self.config))
                
                # Apply updates
                self._apply_updates(new_config, updates)
                
                # Validate if requested
                if validate:
                    validation_errors = self.validate_configuration(new_config)
                    if validation_errors:
                        self.logger.warning(f"Configuration validation failed: {validation_errors}")
                        return False
                
                # Apply updates to current config
                old_config = self.config
                self.config = new_config
                self.config.last_updated = time.time()
                
                # Save configuration
                if self.auto_save_enabled:
                    self._save_configuration()
                
                # Notify callbacks
                self._notify_config_change(old_config, self.config)
                
                self.logger.info("Configuration updated successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
            return False
    
    def _apply_updates(self, config: OptimizationConfiguration, updates: Dict[str, Any]):
        """Apply updates to configuration object."""
        for key, value in updates.items():
            if '.' in key:
                # Handle nested updates (e.g., "cache.enable_caching")
                parts = key.split('.')
                obj = config
                for part in parts[:-1]:
                    if hasattr(obj, part):
                        obj = getattr(obj, part)
                    else:
                        raise ValueError(f"Invalid configuration path: {key}")
                
                if hasattr(obj, parts[-1]):
                    setattr(obj, parts[-1], value)
                else:
                    raise ValueError(f"Invalid configuration field: {key}")
            else:
                # Handle top-level updates
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    raise ValueError(f"Invalid configuration field: {key}")
    
    def _notify_config_change(self, old_config: OptimizationConfiguration, new_config: OptimizationConfiguration):
        """Notify callbacks of configuration changes."""
        for callback in self.config_callbacks:
            try:
                callback(old_config, new_config)
            except Exception as e:
                self.logger.error(f"Configuration callback failed: {e}")
    
    def add_config_callback(self, callback: Callable):
        """Add callback for configuration changes."""
        self.config_callbacks.append(callback)
        self.logger.debug("Added configuration change callback")
    
    def remove_config_callback(self, callback: Callable):
        """Remove configuration change callback."""
        try:
            self.config_callbacks.remove(callback)
            self.logger.debug("Removed configuration change callback")
        except ValueError:
            pass
    
    def reset_to_defaults(self, component: Optional[str] = None) -> bool:
        """Reset configuration to defaults."""
        try:
            with self._lock:
                if component:
                    # Reset specific component
                    if component == "model_discovery":
                        self.config.model_discovery = ModelDiscoveryConfig()
                    elif component == "model_routing":
                        self.config.model_routing = ModelRoutingConfig()
                    elif component == "cache":
                        self.config.cache = CacheConfig()
                    elif component == "performance":
                        self.config.performance = PerformanceConfig()
                    elif component == "content_optimization":
                        self.config.content_optimization = ContentOptimizationConfig()
                    elif component == "streaming":
                        self.config.streaming = StreamingConfig()
                    elif component == "cuda":
                        self.config.cuda = CudaConfig()
                    elif component == "monitoring":
                        self.config.monitoring = MonitoringConfig()
                    elif component == "reasoning_preservation":
                        self.config.reasoning_preservation = ReasoningPreservationConfig()
                    else:
                        self.logger.warning(f"Unknown component: {component}")
                        return False
                else:
                    # Reset entire configuration
                    old_config = self.config
                    self.config = OptimizationConfiguration()
                    self._notify_config_change(old_config, self.config)
                
                self.config.last_updated = time.time()
                
                if self.auto_save_enabled:
                    self._save_configuration()
                
                self.logger.info(f"Reset configuration {'component ' + component if component else 'to defaults'}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to reset configuration: {e}")
            return False
    
    def export_configuration(self, export_path: Optional[Path] = None) -> bool:
        """Export configuration to file."""
        try:
            export_path = export_path or Path(f"optimization_config_export_{int(time.time())}.json")
            
            with self._lock:
                config_data = self._serialize_config(self.config)
                config_data["export_timestamp"] = datetime.now().isoformat()
                config_data["export_version"] = self.config.config_version
            
            with open(export_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Exported configuration to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_configuration(self, import_path: Path, validate: bool = True) -> bool:
        """Import configuration from file."""
        try:
            if not import_path.exists():
                self.logger.error(f"Import file does not exist: {import_path}")
                return False
            
            with open(import_path, 'r') as f:
                config_data = json.load(f)
            
            # Remove export metadata
            config_data.pop("export_timestamp", None)
            config_data.pop("export_version", None)
            
            new_config = self._deserialize_config(config_data)
            
            if validate:
                validation_errors = self.validate_configuration(new_config)
                if validation_errors:
                    self.logger.error(f"Imported configuration validation failed: {validation_errors}")
                    return False
            
            with self._lock:
                old_config = self.config
                self.config = new_config
                self.config.last_updated = time.time()
                
                if self.auto_save_enabled:
                    self._save_configuration()
                
                self._notify_config_change(old_config, self.config)
            
            self.logger.info(f"Imported configuration from {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary for display."""
        try:
            with self._lock:
                return {
                    "optimization_enabled": self.config.enable_optimization_system,
                    "optimization_level": self.config.optimization_level,
                    "config_version": self.config.config_version,
                    "last_updated": datetime.fromtimestamp(self.config.last_updated).isoformat(),
                    "components": {
                        "model_discovery": self.config.model_discovery.enable_discovery,
                        "model_routing": self.config.model_routing.enable_routing,
                        "caching": self.config.cache.enable_caching,
                        "performance_optimization": self.config.performance.enable_optimization,
                        "content_optimization": self.config.content_optimization.enable_optimization,
                        "streaming": self.config.streaming.enable_streaming,
                        "cuda_acceleration": self.config.cuda.enable_cuda,
                        "monitoring": self.config.monitoring.enable_monitoring
                    },
                    "reasoning_preservation": {
                        "decision_engine": self.config.reasoning_preservation.preserve_decision_engine,
                        "flow_manager": self.config.reasoning_preservation.preserve_flow_manager,
                        "tinyllama_scaffolding": self.config.reasoning_preservation.preserve_tinyllama_scaffolding,
                        "profile_routing": self.config.reasoning_preservation.preserve_profile_routing
                    },
                    "validation_status": len(self.validate_configuration()) == 0,
                    "auto_save_enabled": self.auto_save_enabled
                }
        except Exception as e:
            return {"error": str(e)}

# Global instance
_optimization_config_manager: Optional[OptimizationConfigurationManager] = None
_config_lock = threading.RLock()

def get_optimization_config_manager(config_path: Optional[Path] = None) -> OptimizationConfigurationManager:
    """Get the global optimization configuration manager instance."""
    global _optimization_config_manager
    if _optimization_config_manager is None:
        with _config_lock:
            if _optimization_config_manager is None:
                _optimization_config_manager = OptimizationConfigurationManager(config_path)
    return _optimization_config_manager

def get_optimization_config() -> OptimizationConfiguration:
    """Get the current optimization configuration."""
    return get_optimization_config_manager().get_configuration()