"""
Configuration Management System for Intelligent Authentication.

This module provides comprehensive configuration management capabilities including
dynamic configuration updates, environment-based loading, hot-reloading,
versioning, and rollback mechanisms for the intelligent authentication system.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union, Type
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

from ai_karen_engine.security.models import IntelligentAuthConfig
from ai_karen_engine.security.intelligent_auth_base import Configurable

logger = logging.getLogger(__name__)


class ConfigFormat(Enum):
    """Configuration file formats."""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"


class ConfigSource(Enum):
    """Configuration sources."""
    FILE = "file"
    ENVIRONMENT = "environment"
    DATABASE = "database"
    REMOTE = "remote"


@dataclass
class ConfigVersion:
    """Configuration version information."""
    version_id: str
    timestamp: datetime
    source: ConfigSource
    config_data: Dict[str, Any]
    description: str = ""
    is_active: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'version_id': self.version_id,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source.value,
            'config_data': self.config_data,
            'description': self.description,
            'is_active': self.is_active
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConfigVersion:
        """Create instance from dictionary."""
        return cls(
            version_id=data['version_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            source=ConfigSource(data['source']),
            config_data=data['config_data'],
            description=data.get('description', ''),
            is_active=data.get('is_active', False)
        )


@dataclass
class ConfigChangeEvent:
    """Configuration change event."""
    timestamp: datetime
    old_config: Optional[IntelligentAuthConfig]
    new_config: IntelligentAuthConfig
    source: ConfigSource
    changed_keys: List[str]
    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'old_config': self.old_config.to_dict() if self.old_config else None,
            'new_config': self.new_config.to_dict(),
            'source': self.source.value,
            'changed_keys': self.changed_keys,
            'success': self.success,
            'error_message': self.error_message
        }


if WATCHDOG_AVAILABLE:
    class ConfigFileWatcher(FileSystemEventHandler):
        """File system watcher for configuration files."""

        def __init__(self, config_manager: ConfigurationManager):
            self.config_manager = config_manager
            self.logger = logging.getLogger(f"{__name__}.ConfigFileWatcher")

        def on_modified(self, event):
            """Handle file modification events."""
            if event.is_directory:
                return

            file_path = Path(event.src_path)
            
            # Check if this is a config file we're watching
            if file_path in self.config_manager._watched_files:
                self.logger.info(f"Configuration file modified: {file_path}")
                asyncio.create_task(self.config_manager._reload_from_file(file_path))
else:
    class ConfigFileWatcher:
        """Fallback file watcher when watchdog is not available."""
        
        def __init__(self, config_manager: ConfigurationManager):
            self.config_manager = config_manager
            self.logger = logging.getLogger(f"{__name__}.ConfigFileWatcher")
            self.logger.warning("Watchdog not available, file watching disabled")


class ConfigurationManager:
    """
    Comprehensive configuration management system.
    
    Features:
    - Dynamic configuration updates with validation
    - Environment-based configuration loading
    - Hot-reloading from file changes
    - Configuration versioning and rollback
    - Multiple configuration sources (file, env, database)
    - Configuration change notifications
    - Validation and error handling
    """

    def __init__(self, 
                 config_class: Type[IntelligentAuthConfig] = IntelligentAuthConfig,
                 enable_hot_reload: bool = True,
                 enable_versioning: bool = True,
                 max_versions: int = 50):
        """
        Initialize configuration manager.
        
        Args:
            config_class: Configuration class to manage
            enable_hot_reload: Enable hot-reloading from file changes
            enable_versioning: Enable configuration versioning
            max_versions: Maximum number of versions to keep
        """
        self.config_class = config_class
        self.enable_hot_reload = enable_hot_reload
        self.enable_versioning = enable_versioning
        self.max_versions = max_versions
        self.logger = logging.getLogger(f"{__name__}.ConfigurationManager")
        
        # Current configuration
        self._current_config: Optional[IntelligentAuthConfig] = None
        self._config_lock = threading.RLock()
        
        # Versioning
        self._versions: List[ConfigVersion] = []
        self._version_counter = 0
        
        # File watching
        self._file_observer: Optional[Observer] = None if not WATCHDOG_AVAILABLE else None
        self._watched_files: set[Path] = set()
        self._file_watcher = ConfigFileWatcher(self)
        
        # Change tracking
        self._change_history: List[ConfigChangeEvent] = []
        self._change_listeners: List[Callable[[ConfigChangeEvent], None]] = []
        
        # Configurable services
        self._configurable_services: List[Configurable] = []
        
        # Environment mapping
        self._env_mapping = {
            'INTELLIGENT_AUTH_ENABLE_NLP': 'enable_nlp_analysis',
            'INTELLIGENT_AUTH_ENABLE_EMBEDDING': 'enable_embedding_analysis',
            'INTELLIGENT_AUTH_ENABLE_BEHAVIORAL': 'enable_behavioral_analysis',
            'INTELLIGENT_AUTH_ENABLE_THREAT_INTEL': 'enable_threat_intelligence',
            'INTELLIGENT_AUTH_MAX_PROCESSING_TIME': 'max_processing_time',
            'INTELLIGENT_AUTH_CACHE_SIZE': 'cache_size',
            'INTELLIGENT_AUTH_CACHE_TTL': 'cache_ttl',
            'INTELLIGENT_AUTH_BATCH_SIZE': 'batch_size',
            'INTELLIGENT_AUTH_LOW_RISK_THRESHOLD': 'risk_thresholds.low_risk_threshold',
            'INTELLIGENT_AUTH_MEDIUM_RISK_THRESHOLD': 'risk_thresholds.medium_risk_threshold',
            'INTELLIGENT_AUTH_HIGH_RISK_THRESHOLD': 'risk_thresholds.high_risk_threshold',
            'INTELLIGENT_AUTH_CRITICAL_RISK_THRESHOLD': 'risk_thresholds.critical_risk_threshold',
        }

    async def initialize(self, initial_config: Optional[IntelligentAuthConfig] = None) -> bool:
        """
        Initialize the configuration manager.
        
        Args:
            initial_config: Initial configuration to use
            
        Returns:
            bool: True if initialization successful
        """
        try:
            # Set initial configuration
            if initial_config:
                await self.update_config(initial_config, ConfigSource.ENVIRONMENT)
            else:
                # Load from environment or create default
                config = await self.load_from_environment()
                await self.update_config(config, ConfigSource.ENVIRONMENT)
            
            # Start file watching if enabled
            if self.enable_hot_reload:
                await self._start_file_watching()
            
            self.logger.info("Configuration manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize configuration manager: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown the configuration manager."""
        try:
            # Stop file watching
            if self._file_observer:
                self._file_observer.stop()
                self._file_observer.join()
                self._file_observer = None
            
            # Clear data
            with self._config_lock:
                self._versions.clear()
                self._change_history.clear()
                self._change_listeners.clear()
                self._configurable_services.clear()
                self._watched_files.clear()
            
            self.logger.info("Configuration manager shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during configuration manager shutdown: {e}")

    def get_current_config(self) -> Optional[IntelligentAuthConfig]:
        """Get the current configuration."""
        with self._config_lock:
            return self._current_config

    async def update_config(self, 
                          new_config: IntelligentAuthConfig, 
                          source: ConfigSource = ConfigSource.ENVIRONMENT,
                          description: str = "") -> bool:
        """
        Update the current configuration.
        
        Args:
            new_config: New configuration to apply
            source: Source of the configuration change
            description: Description of the change
            
        Returns:
            bool: True if update successful
        """
        start_time = time.time()
        
        try:
            # Validate new configuration
            if not new_config.validate():
                raise ValueError("Invalid configuration provided")
            
            with self._config_lock:
                old_config = self._current_config
                
                # Determine changed keys
                changed_keys = self._get_changed_keys(old_config, new_config)
                
                # Create version if versioning enabled
                if self.enable_versioning:
                    version = ConfigVersion(
                        version_id=f"v{self._version_counter}",
                        timestamp=datetime.now(),
                        source=source,
                        config_data=new_config.to_dict(),
                        description=description,
                        is_active=True
                    )
                    
                    # Mark previous version as inactive
                    for v in self._versions:
                        v.is_active = False
                    
                    self._versions.append(version)
                    self._version_counter += 1
                    
                    # Limit version history
                    if len(self._versions) > self.max_versions:
                        self._versions = self._versions[-self.max_versions:]
                
                # Update current configuration
                self._current_config = new_config
            
            # Notify configurable services
            await self._notify_configurable_services(new_config)
            
            # Create change event
            change_event = ConfigChangeEvent(
                timestamp=datetime.now(),
                old_config=old_config,
                new_config=new_config,
                source=source,
                changed_keys=changed_keys,
                success=True
            )
            
            # Record change
            self._record_change_event(change_event)
            
            # Notify listeners
            await self._notify_change_listeners(change_event)
            
            processing_time = time.time() - start_time
            self.logger.info(
                f"Configuration updated successfully from {source.value} "
                f"(changed keys: {changed_keys}, processing time: {processing_time:.3f}s)"
            )
            
            return True
            
        except Exception as e:
            # Create error change event
            change_event = ConfigChangeEvent(
                timestamp=datetime.now(),
                old_config=self._current_config,
                new_config=new_config,
                source=source,
                changed_keys=[],
                success=False,
                error_message=str(e)
            )
            
            self._record_change_event(change_event)
            await self._notify_change_listeners(change_event)
            
            self.logger.error(f"Failed to update configuration: {e}")
            return False

    async def load_from_file(self, 
                           file_path: Union[str, Path], 
                           format: Optional[ConfigFormat] = None,
                           watch: bool = True) -> IntelligentAuthConfig:
        """
        Load configuration from file.
        
        Args:
            file_path: Path to configuration file
            format: File format (auto-detected if None)
            watch: Whether to watch file for changes
            
        Returns:
            IntelligentAuthConfig: Loaded configuration
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Auto-detect format if not specified
        if format is None:
            format = self._detect_file_format(file_path)
        
        # Load configuration data
        with open(file_path, 'r') as f:
            if format == ConfigFormat.JSON:
                config_data = json.load(f)
            elif format == ConfigFormat.YAML:
                if not YAML_AVAILABLE:
                    raise ValueError("YAML format requested but PyYAML not available")
                config_data = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported file format: {format}")
        
        # Create configuration object
        config = self.config_class.from_dict(config_data)
        
        # Add to watched files if requested
        if watch and self.enable_hot_reload:
            self._watched_files.add(file_path)
            if self._file_observer:
                self._file_observer.schedule(
                    self._file_watcher, 
                    str(file_path.parent), 
                    recursive=False
                )
        
        self.logger.info(f"Loaded configuration from file: {file_path}")
        return config

    async def save_to_file(self, 
                         file_path: Union[str, Path], 
                         config: Optional[IntelligentAuthConfig] = None,
                         format: Optional[ConfigFormat] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            file_path: Path to save configuration
            config: Configuration to save (current if None)
            format: File format (auto-detected if None)
        """
        file_path = Path(file_path)
        config = config or self.get_current_config()
        
        if not config:
            raise ValueError("No configuration to save")
        
        # Auto-detect format if not specified
        if format is None:
            format = self._detect_file_format(file_path)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        config_data = config.to_dict()
        
        with open(file_path, 'w') as f:
            if format == ConfigFormat.JSON:
                json.dump(config_data, f, indent=2)
            elif format == ConfigFormat.YAML:
                if not YAML_AVAILABLE:
                    raise ValueError("YAML format requested but PyYAML not available")
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            else:
                raise ValueError(f"Unsupported file format: {format}")
        
        self.logger.info(f"Saved configuration to file: {file_path}")

    async def load_from_environment(self) -> IntelligentAuthConfig:
        """
        Load configuration from environment variables.
        
        Returns:
            IntelligentAuthConfig: Configuration loaded from environment
        """
        config_data = {}
        
        # Load mapped environment variables
        for env_var, config_path in self._env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert value to appropriate type
                converted_value = self._convert_env_value(value)
                
                # Set nested value
                self._set_nested_value(config_data, config_path, converted_value)
        
        # Create configuration with environment overrides
        if config_data:
            config = self.config_class.from_dict(config_data)
        else:
            config = self.config_class()  # Use defaults
        
        self.logger.info("Loaded configuration from environment variables")
        return config

    async def rollback_to_version(self, version_id: str) -> bool:
        """
        Rollback to a specific configuration version.
        
        Args:
            version_id: Version ID to rollback to
            
        Returns:
            bool: True if rollback successful
        """
        with self._config_lock:
            # Find the version
            target_version = None
            for version in self._versions:
                if version.version_id == version_id:
                    target_version = version
                    break
            
            if not target_version:
                self.logger.error(f"Version not found: {version_id}")
                return False
            
            # Create configuration from version data
            config = self.config_class.from_dict(target_version.config_data)
            
            # Update configuration
            success = await self.update_config(
                config, 
                target_version.source, 
                f"Rollback to version {version_id}"
            )
            
            if success:
                self.logger.info(f"Successfully rolled back to version: {version_id}")
            
            return success

    def get_version_history(self, limit: int = 20) -> List[ConfigVersion]:
        """
        Get configuration version history.
        
        Args:
            limit: Maximum number of versions to return
            
        Returns:
            List[ConfigVersion]: Version history
        """
        with self._config_lock:
            return self._versions[-limit:] if limit > 0 else self._versions.copy()

    def get_change_history(self, limit: int = 50) -> List[ConfigChangeEvent]:
        """
        Get configuration change history.
        
        Args:
            limit: Maximum number of changes to return
            
        Returns:
            List[ConfigChangeEvent]: Change history
        """
        with self._config_lock:
            return self._change_history[-limit:] if limit > 0 else self._change_history.copy()

    def add_change_listener(self, listener: Callable[[ConfigChangeEvent], None]) -> None:
        """Add a configuration change listener."""
        self._change_listeners.append(listener)

    def remove_change_listener(self, listener: Callable[[ConfigChangeEvent], None]) -> None:
        """Remove a configuration change listener."""
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)

    def register_configurable_service(self, service: Configurable) -> None:
        """Register a configurable service for automatic updates."""
        self._configurable_services.append(service)

    def unregister_configurable_service(self, service: Configurable) -> None:
        """Unregister a configurable service."""
        if service in self._configurable_services:
            self._configurable_services.remove(service)

    async def validate_config(self, config: IntelligentAuthConfig) -> tuple[bool, List[str]]:
        """
        Validate a configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Basic validation
            if not config.validate():
                errors.append("Configuration validation failed")
            
            # Additional custom validations
            if config.max_processing_time <= 0:
                errors.append("max_processing_time must be positive")
            
            if config.cache_size <= 0:
                errors.append("cache_size must be positive")
            
            if config.cache_ttl <= 0:
                errors.append("cache_ttl must be positive")
            
            # Validate risk thresholds
            thresholds = config.risk_thresholds
            if not (0 <= thresholds.low_risk_threshold <= thresholds.medium_risk_threshold <= 
                   thresholds.high_risk_threshold <= thresholds.critical_risk_threshold <= 1.0):
                errors.append("Risk thresholds must be in ascending order between 0 and 1")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return False, errors

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration state."""
        with self._config_lock:
            current_config = self._current_config
            
            return {
                'has_current_config': current_config is not None,
                'current_config_valid': current_config.validate() if current_config else False,
                'total_versions': len(self._versions),
                'total_changes': len(self._change_history),
                'watched_files': [str(f) for f in self._watched_files],
                'configurable_services': len(self._configurable_services),
                'change_listeners': len(self._change_listeners),
                'hot_reload_enabled': self.enable_hot_reload,
                'versioning_enabled': self.enable_versioning,
                'file_watching_active': self._file_observer is not None and self._file_observer.is_alive()
            }

    # Private methods

    async def _start_file_watching(self) -> None:
        """Start file system watching for configuration files."""
        if not WATCHDOG_AVAILABLE:
            self.logger.warning("File watching disabled - watchdog not available")
            return
            
        if self._file_observer:
            return
        
        self._file_observer = Observer()
        
        # Watch existing files
        for file_path in self._watched_files:
            if file_path.exists():
                self._file_observer.schedule(
                    self._file_watcher,
                    str(file_path.parent),
                    recursive=False
                )
        
        self._file_observer.start()
        self.logger.info("Started configuration file watching")

    async def _reload_from_file(self, file_path: Path) -> None:
        """Reload configuration from a file."""
        try:
            config = await self.load_from_file(file_path, watch=False)
            await self.update_config(
                config, 
                ConfigSource.FILE, 
                f"Hot-reload from {file_path}"
            )
        except Exception as e:
            self.logger.error(f"Failed to reload configuration from {file_path}: {e}")

    def _detect_file_format(self, file_path: Path) -> ConfigFormat:
        """Detect file format from extension."""
        suffix = file_path.suffix.lower()
        
        if suffix in ['.json']:
            return ConfigFormat.JSON
        elif suffix in ['.yaml', '.yml']:
            return ConfigFormat.YAML
        else:
            # Default to JSON
            return ConfigFormat.JSON

    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable value to appropriate type."""
        # Try boolean
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value

    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set a nested value in a dictionary using dot notation."""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value

    def _get_changed_keys(self, 
                         old_config: Optional[IntelligentAuthConfig], 
                         new_config: IntelligentAuthConfig) -> List[str]:
        """Get list of changed configuration keys."""
        if not old_config:
            return ['*']  # All keys changed (new configuration)
        
        changed_keys = []
        old_dict = old_config.to_dict()
        new_dict = new_config.to_dict()
        
        def compare_dicts(old_d: Dict, new_d: Dict, prefix: str = '') -> None:
            all_keys = set(old_d.keys()) | set(new_d.keys())
            
            for key in all_keys:
                full_key = f"{prefix}.{key}" if prefix else key
                
                if key not in old_d:
                    changed_keys.append(f"+{full_key}")  # Added
                elif key not in new_d:
                    changed_keys.append(f"-{full_key}")  # Removed
                elif isinstance(old_d[key], dict) and isinstance(new_d[key], dict):
                    compare_dicts(old_d[key], new_d[key], full_key)
                elif old_d[key] != new_d[key]:
                    changed_keys.append(full_key)  # Modified
        
        compare_dicts(old_dict, new_dict)
        return changed_keys

    async def _notify_configurable_services(self, new_config: IntelligentAuthConfig) -> None:
        """Notify all registered configurable services of configuration change."""
        for service in self._configurable_services:
            try:
                await service.update_config(new_config)
            except Exception as e:
                self.logger.error(f"Failed to update service configuration: {e}")

    def _record_change_event(self, event: ConfigChangeEvent) -> None:
        """Record a configuration change event."""
        with self._config_lock:
            self._change_history.append(event)
            
            # Limit history size
            if len(self._change_history) > 1000:
                self._change_history = self._change_history[-1000:]

    async def _notify_change_listeners(self, event: ConfigChangeEvent) -> None:
        """Notify all change listeners of a configuration change."""
        for listener in self._change_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                self.logger.error(f"Error in configuration change listener: {e}")


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> Optional[ConfigurationManager]:
    """Get the global configuration manager instance."""
    return _config_manager


def initialize_config_manager(config_manager: ConfigurationManager) -> None:
    """Initialize the global configuration manager."""
    global _config_manager
    _config_manager = config_manager


# Utility functions

async def load_config_from_file(file_path: Union[str, Path]) -> IntelligentAuthConfig:
    """Utility function to load configuration from file."""
    manager = ConfigurationManager()
    return await manager.load_from_file(file_path)


async def save_config_to_file(config: IntelligentAuthConfig, 
                            file_path: Union[str, Path]) -> None:
    """Utility function to save configuration to file."""
    manager = ConfigurationManager()
    await manager.save_config_to_file(file_path, config)


def create_default_config() -> IntelligentAuthConfig:
    """Create a default configuration."""
    return IntelligentAuthConfig()