"""
Extension Lifecycle Management Configuration
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class HealthCheckConfig(BaseModel):
    """Health check configuration."""
    enabled: bool = True
    check_interval_seconds: int = 60
    timeout_seconds: int = 30
    failure_threshold: int = 3
    success_threshold: int = 1
    
    # Metric thresholds
    cpu_warning_threshold: float = 70.0
    cpu_critical_threshold: float = 90.0
    memory_warning_mb: float = 400.0
    memory_critical_mb: float = 512.0
    error_rate_warning: float = 5.0
    error_rate_critical: float = 10.0
    response_time_warning_ms: float = 2000.0
    response_time_critical_ms: float = 5000.0
    
    # Custom checks
    custom_checks: List[Dict[str, Any]] = Field(default_factory=list)


class BackupConfig(BaseModel):
    """Backup configuration."""
    enabled: bool = True
    backup_root: str = "data/backups/extensions"
    auto_backup_enabled: bool = True
    auto_backup_interval_hours: int = 24
    max_backups_per_extension: int = 10
    backup_retention_days: int = 30
    
    # Backup types
    default_backup_type: str = "full"
    include_data_by_default: bool = True
    include_config_by_default: bool = True
    include_code_by_default: bool = False
    
    # Compression
    compression_enabled: bool = True
    compression_level: int = 6


class MigrationConfig(BaseModel):
    """Migration configuration."""
    enabled: bool = True
    auto_backup_before_migration: bool = True
    auto_rollback_on_failure: bool = True
    migration_timeout_seconds: int = 3600
    
    # Verification
    verify_migration: bool = True
    verification_timeout_seconds: int = 300
    
    # Rollback
    rollback_timeout_seconds: int = 1800


class RecoveryConfig(BaseModel):
    """Recovery configuration."""
    enabled: bool = True
    auto_recovery_enabled: bool = True
    default_strategy: str = "auto"  # auto, conservative, aggressive
    
    # Recovery timeouts
    restart_timeout_seconds: int = 300
    recovery_cooldown_seconds: int = 300
    max_recovery_attempts: int = 3
    
    # Recovery actions
    enable_restart: bool = True
    enable_cache_clear: bool = True
    enable_backup_restore: bool = True
    enable_version_rollback: bool = True
    enable_reinstall: bool = False
    enable_disable: bool = True


class LifecycleConfig(BaseModel):
    """Main lifecycle management configuration."""
    enabled: bool = True
    
    # Component configurations
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)
    migration: MigrationConfig = Field(default_factory=MigrationConfig)
    recovery: RecoveryConfig = Field(default_factory=RecoveryConfig)
    
    # Logging
    log_level: str = "INFO"
    log_lifecycle_events: bool = True
    event_retention_days: int = 90
    
    # Performance
    max_concurrent_operations: int = 5
    operation_timeout_seconds: int = 3600
    
    # Security
    require_confirmation_for_destructive_ops: bool = True
    allowed_recovery_strategies: List[str] = Field(
        default_factory=lambda: ["auto", "conservative", "aggressive"]
    )


class ExtensionSpecificConfig(BaseModel):
    """Extension-specific lifecycle configuration."""
    extension_name: str
    
    # Override global settings
    health_check: Optional[HealthCheckConfig] = None
    backup: Optional[BackupConfig] = None
    migration: Optional[MigrationConfig] = None
    recovery: Optional[RecoveryConfig] = None
    
    # Extension-specific settings
    critical_extension: bool = False  # Higher priority for recovery
    maintenance_window: Optional[Dict[str, str]] = None  # {"start": "02:00", "end": "04:00"}
    custom_recovery_actions: List[Dict[str, Any]] = Field(default_factory=list)


def load_lifecycle_config(config_path: Optional[Path] = None) -> LifecycleConfig:
    """Load lifecycle configuration from file."""
    if config_path and config_path.exists():
        import json
        with open(config_path) as f:
            config_data = json.load(f)
        return LifecycleConfig(**config_data)
    else:
        # Return default configuration
        return LifecycleConfig()


def save_lifecycle_config(config: LifecycleConfig, config_path: Path) -> None:
    """Save lifecycle configuration to file."""
    import json
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config.dict(), f, indent=2)


def get_extension_config(
    extension_name: str,
    global_config: LifecycleConfig,
    extension_configs: Dict[str, ExtensionSpecificConfig]
) -> LifecycleConfig:
    """Get effective configuration for a specific extension."""
    if extension_name not in extension_configs:
        return global_config
    
    ext_config = extension_configs[extension_name]
    
    # Create merged configuration
    merged_config = global_config.copy(deep=True)
    
    # Override with extension-specific settings
    if ext_config.health_check:
        merged_config.health_check = ext_config.health_check
    
    if ext_config.backup:
        merged_config.backup = ext_config.backup
    
    if ext_config.migration:
        merged_config.migration = ext_config.migration
    
    if ext_config.recovery:
        merged_config.recovery = ext_config.recovery
    
    return merged_config


# Default configuration templates
DEFAULT_HEALTH_THRESHOLDS = {
    "cpu_warning": 70.0,
    "cpu_critical": 90.0,
    "memory_warning_mb": 400.0,
    "memory_critical_mb": 512.0,
    "error_rate_warning": 5.0,
    "error_rate_critical": 10.0,
    "response_time_warning_ms": 2000.0,
    "response_time_critical_ms": 5000.0
}

DEFAULT_RECOVERY_ACTIONS = [
    {
        "type": "restart",
        "priority": 1,
        "max_attempts": 3,
        "cooldown_seconds": 300
    },
    {
        "type": "clear_cache",
        "priority": 2,
        "max_attempts": 1,
        "cooldown_seconds": 60
    },
    {
        "type": "restore_backup",
        "priority": 3,
        "max_attempts": 1,
        "cooldown_seconds": 600
    },
    {
        "type": "rollback_version",
        "priority": 4,
        "max_attempts": 1,
        "cooldown_seconds": 1800
    },
    {
        "type": "disable",
        "priority": 5,
        "max_attempts": 1,
        "cooldown_seconds": 0
    }
]

CRITICAL_EXTENSION_CONFIG = ExtensionSpecificConfig(
    extension_name="critical_extension",
    critical_extension=True,
    health_check=HealthCheckConfig(
        check_interval_seconds=30,  # More frequent checks
        failure_threshold=2,  # Lower threshold
        cpu_critical_threshold=80.0,  # Lower CPU threshold
        memory_critical_mb=400.0  # Lower memory threshold
    ),
    recovery=RecoveryConfig(
        max_recovery_attempts=5,  # More attempts
        recovery_cooldown_seconds=60  # Shorter cooldown
    )
)