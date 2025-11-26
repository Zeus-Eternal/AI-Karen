"""
Configuration management for the KARI extension system.

This module handles extension configuration, including loading, validation,
and environment-specific settings.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ValidationError

from .base import ExtensionManifest, ExtensionPermissions, ExtensionRBAC
from .errors import ExtensionConfigurationError


class ExtensionHostConfig(BaseModel):
    """Configuration for the extension host."""
    
    extensions_dir: str = "src/extensions"
    timeout_seconds: float = 30.0
    max_concurrent_extensions: int = 10
    enable_metrics: bool = True
    enable_observation: bool = True
    log_level: str = "INFO"
    strict_validation: bool = True
    auto_reload: bool = False
    allowed_file_extensions: List[str] = Field(default_factory=lambda: [".py", ".json", ".txt"])
    
    class Config:
        env_prefix = "KARI_EXTENSION_"
        case_sensitive = False


class ExtensionEnvironmentConfig(BaseModel):
    """Environment-specific configuration for extensions."""
    
    development: ExtensionHostConfig = Field(default_factory=ExtensionHostConfig)
    staging: ExtensionHostConfig = Field(default_factory=lambda: ExtensionHostConfig(
        log_level="WARNING",
        strict_validation=True,
        auto_reload=False
    ))
    production: ExtensionHostConfig = Field(default_factory=lambda: ExtensionHostConfig(
        log_level="ERROR",
        strict_validation=True,
        auto_reload=False,
        timeout_seconds=15.0
    ))


class ExtensionConfigManager:
    """Manager for extension configuration."""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = Path(config_file) if config_file else None
        self._config: Optional[ExtensionHostConfig] = None
        self._environment = os.environ.get("KARI_ENVIRONMENT", "development")
        self._extension_configs: Dict[str, Dict[str, Any]] = {}
    
    def load_config(self) -> ExtensionHostConfig:
        """
        Load the extension host configuration.
        
        Returns:
            The loaded configuration
            
        Raises:
            ExtensionConfigurationError: If configuration cannot be loaded
        """
        if self._config is not None:
            return self._config
        
        try:
            # Try to load from file first
            if self.config_file and self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                env_config = ExtensionEnvironmentConfig(**config_data)
                self._config = getattr(env_config, self._environment, env_config.development)
            else:
                # Use default configuration
                env_config = ExtensionEnvironmentConfig()
                self._config = getattr(env_config, self._environment, env_config.development)
            
            # Override with environment variables
            if self._config is not None:
                self._apply_env_overrides(self._config)
            
            # Ensure we always return a valid config
            if self._config is None:
                raise ExtensionConfigurationError("Configuration was not properly loaded")
            
            return self._config
        except (json.JSONDecodeError, ValidationError) as e:
            raise ExtensionConfigurationError(f"Failed to load configuration: {e}") from e
        except Exception as e:
            raise ExtensionConfigurationError(f"Unexpected error loading configuration: {e}") from e
    
    def _apply_env_overrides(self, config: ExtensionHostConfig) -> None:
        """
        Apply environment variable overrides to configuration.
        
        Args:
            config: The configuration to update
        """
        env_mapping = {
            "KARI_EXTENSION_EXTENSIONS_DIR": ("extensions_dir", str),
            "KARI_EXTENSION_TIMEOUT_SECONDS": ("timeout_seconds", float),
            "KARI_EXTENSION_MAX_CONCURRENT_EXTENSIONS": ("max_concurrent_extensions", int),
            "KARI_EXTENSION_ENABLE_METRICS": ("enable_metrics", lambda x: x.lower() == "true"),
            "KARI_EXTENSION_ENABLE_OBSERVATION": ("enable_observation", lambda x: x.lower() == "true"),
            "KARI_EXTENSION_LOG_LEVEL": ("log_level", str),
            "KARI_EXTENSION_STRICT_VALIDATION": ("strict_validation", lambda x: x.lower() == "true"),
            "KARI_EXTENSION_AUTO_RELOAD": ("auto_reload", lambda x: x.lower() == "true"),
        }
        
        for env_var, (field, converter) in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    setattr(config, field, converter(value))
                except (ValueError, TypeError) as e:
                    # Log warning but continue with default
                    print(f"Warning: Invalid value for {env_var}: {value} ({e})")
    
    def get_config(self) -> ExtensionHostConfig:
        """
        Get the current configuration.
        
        Returns:
            The current configuration
        """
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def get_extensions_dir(self) -> Path:
        """
        Get the extensions directory path.
        
        Returns:
            Path to the extensions directory
        """
        config = self.get_config()
        return Path(config.extensions_dir)
    
    def load_extension_config(self, extension_id: str, config_file: Path) -> Dict[str, Any]:
        """
        Load configuration for a specific extension.
        
        Args:
            extension_id: ID of the extension
            config_file: Path to the extension configuration file
            
        Returns:
            The extension configuration
            
        Raises:
            ExtensionConfigurationError: If configuration cannot be loaded
        """
        try:
            if not config_file.exists():
                return {}
            
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Validate against manifest schema if available
            extension_dir = config_file.parent
            manifest_file = extension_dir / "extension_manifest.json"
            
            if manifest_file.exists():
                manifest = ExtensionManifest.from_file(manifest_file)
                if manifest.config_schema:
                    # Validate config against schema
                    self._validate_config_against_schema(config_data, manifest.config_schema)
            
            self._extension_configs[extension_id] = config_data
            return config_data
        except (json.JSONDecodeError, ValidationError) as e:
            raise ExtensionConfigurationError(f"Failed to load extension config: {e}") from e
        except Exception as e:
            raise ExtensionConfigurationError(f"Unexpected error loading extension config: {e}") from e
    
    def _validate_config_against_schema(self, config_data: Dict[str, Any], schema: Any) -> None:
        """
        Validate configuration data against a schema.
        
        Args:
            config_data: The configuration data to validate
            schema: The schema to validate against
            
        Raises:
            ExtensionConfigurationError: If validation fails
        """
        try:
            # Use Pydantic for validation if available
            if hasattr(schema, 'parse_obj'):
                schema.parse_obj(config_data)
            else:
                # Basic validation - check required fields
                if hasattr(schema, 'properties') and hasattr(schema, 'required'):
                    for field in schema.required:
                        if field not in config_data:
                            raise ExtensionConfigurationError(f"Missing required configuration field: {field}")
        except ValidationError as e:
            errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            raise ExtensionConfigurationError(f"Configuration validation failed: {'; '.join(errors)}")
        except Exception as e:
            if isinstance(e, ExtensionConfigurationError):
                raise
            raise ExtensionConfigurationError(f"Unexpected error during validation: {e}")
    
    def get_extension_config(self, extension_id: str) -> Dict[str, Any]:
        """
        Get configuration for a specific extension.
        
        Args:
            extension_id: ID of the extension
            
        Returns:
            The extension configuration
        """
        return self._extension_configs.get(extension_id, {})
    
    def save_config(self, config_file: Optional[Union[str, Path]] = None) -> None:
        """
        Save the current configuration to a file.
        
        Args:
            config_file: Path to save the configuration to
        """
        if config_file:
            self.config_file = Path(config_file)
        
        if not self.config_file:
            raise ExtensionConfigurationError("No configuration file specified")
        
        try:
            config = self.get_config()
            config_data = config.dict()
            
            # Create directory if it doesn't exist
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            raise ExtensionConfigurationError(f"Failed to save configuration: {e}") from e
    
    def reload_config(self) -> ExtensionHostConfig:
        """
        Reload the configuration from file.
        
        Returns:
            The reloaded configuration
        """
        self._config = None
        return self.load_config()
    
    def create_default_config(self, config_file: Union[str, Path]) -> None:
        """
        Create a default configuration file.
        
        Args:
            config_file: Path to create the configuration file at
        """
        config_file = Path(config_file)
        
        try:
            env_config = ExtensionEnvironmentConfig()
            config_data = env_config.dict()
            
            # Create directory if it doesn't exist
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            raise ExtensionConfigurationError(f"Failed to create default configuration: {e}") from e
    
    def get_environment(self) -> str:
        """
        Get the current environment.
        
        Returns:
            The current environment name
        """
        return self._environment
    
    def set_environment(self, environment: str) -> None:
        """
        Set the current environment.
        
        Args:
            environment: The environment name (development, staging, production)
        """
        if environment not in ["development", "staging", "production"]:
            raise ExtensionConfigurationError(f"Invalid environment: {environment}")
        
        self._environment = environment
        # Force reload of configuration with new environment
        self._config = None