"""
Enhanced Configuration Manager for System Warnings and Errors Fix

This module provides comprehensive configuration management with validation,
migration support, environment variable handling, and health checks to address
requirements 9.1-9.5 from the system-warnings-errors-fix specification.
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

from ai_karen_engine.utils.pydantic_migration import PydanticMigrationUtility

logger = logging.getLogger(__name__)


class ConfigValidationSeverity(str, Enum):
    """Configuration validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ConfigSource(str, Enum):
    """Configuration sources"""
    DEFAULT = "default"
    FILE = "file"
    ENVIRONMENT = "environment"
    RUNTIME = "runtime"


@dataclass
class ConfigIssue:
    """Represents a configuration issue"""
    key: str
    issue_type: str  # 'missing', 'deprecated', 'invalid', 'migration_needed'
    message: str
    suggested_fix: str
    severity: ConfigValidationSeverity
    source: ConfigSource
    line_number: Optional[int] = None


@dataclass
class ConfigValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    issues: List[ConfigIssue] = field(default_factory=list)
    missing_required: List[str] = field(default_factory=list)
    deprecated_configs: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    migration_needed: bool = False
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any error-level issues"""
        return any(issue.severity in [ConfigValidationSeverity.ERROR, ConfigValidationSeverity.CRITICAL] 
                  for issue in self.issues)
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warning-level issues"""
        return any(issue.severity == ConfigValidationSeverity.WARNING for issue in self.issues)


class EnvironmentVariableConfig(BaseModel):
    """Configuration for environment variable mapping"""
    model_config = ConfigDict(extra="forbid")
    
    env_var: str = Field(..., description="Environment variable name")
    config_path: str = Field(..., description="Dot-notation path in config")
    required: bool = Field(default=False, description="Whether this env var is required")
    default_value: Optional[Any] = Field(default=None, description="Default value if not set")
    value_type: str = Field(default="str", description="Expected value type")
    description: str = Field(default="", description="Description of the configuration")
    validation_pattern: Optional[str] = Field(default=None, description="Regex pattern for validation")


class ConfigurationManager:
    """
    Enhanced configuration manager with validation, migration, and health monitoring.
    
    Features:
    - Automatic Pydantic V2 migration
    - Environment variable validation with clear error messages
    - Configuration health checks during startup
    - Default value management with appropriate warnings
    - Comprehensive validation and error reporting
    """
    
    # Default environment variable mappings
    DEFAULT_ENV_MAPPINGS = [
        EnvironmentVariableConfig(
            env_var="KARI_ENV",
            config_path="environment",
            required=False,
            default_value="development",
            description="Application environment (development, staging, production)"
        ),
        EnvironmentVariableConfig(
            env_var="KARI_DEBUG",
            config_path="debug",
            required=False,
            default_value=False,
            value_type="bool",
            description="Enable debug mode"
        ),
        EnvironmentVariableConfig(
            env_var="DB_HOST",
            config_path="database.host",
            required=False,
            default_value="localhost",
            description="Database host"
        ),
        EnvironmentVariableConfig(
            env_var="DB_PORT",
            config_path="database.port",
            required=False,
            default_value=5432,
            value_type="int",
            description="Database port"
        ),
        EnvironmentVariableConfig(
            env_var="DB_NAME",
            config_path="database.name",
            required=False,
            default_value="ai_karen",
            description="Database name"
        ),
        EnvironmentVariableConfig(
            env_var="DB_USER",
            config_path="database.username",
            required=False,
            default_value="postgres",
            description="Database username"
        ),
        EnvironmentVariableConfig(
            env_var="DB_PASSWORD",
            config_path="database.password",
            required=False,
            default_value="",
            description="Database password"
        ),
        EnvironmentVariableConfig(
            env_var="REDIS_HOST",
            config_path="redis.host",
            required=False,
            default_value="localhost",
            description="Redis host"
        ),
        EnvironmentVariableConfig(
            env_var="REDIS_PORT",
            config_path="redis.port",
            required=False,
            default_value=6379,
            value_type="int",
            description="Redis port"
        ),
        EnvironmentVariableConfig(
            env_var="REDIS_PASSWORD",
            config_path="redis.password",
            required=False,
            default_value=None,
            description="Redis password"
        ),
        EnvironmentVariableConfig(
            env_var="OPENAI_API_KEY",
            config_path="llm.openai_api_key",
            required=False,
            default_value=None,
            description="OpenAI API key for LLM services"
        ),
        EnvironmentVariableConfig(
            env_var="LLM_PROVIDER",
            config_path="llm.provider",
            required=False,
            default_value="local",
            description="Default LLM provider (openai, anthropic, local)"
        ),
        EnvironmentVariableConfig(
            env_var="LLM_MODEL",
            config_path="llm.model",
            required=False,
            default_value="llama3.2:latest",
            description="Default LLM model"
        ),
        EnvironmentVariableConfig(
            env_var="JWT_SECRET",
            config_path="security.jwt_secret",
            required=True,
            description="JWT secret key for authentication"
        ),
        EnvironmentVariableConfig(
            env_var="CORS_ORIGINS",
            config_path="security.cors_origins",
            required=False,
            default_value="*",
            description="CORS allowed origins (comma-separated)"
        ),
    ]
    
    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        env_mappings: Optional[List[EnvironmentVariableConfig]] = None,
        enable_migration: bool = True,
        enable_health_checks: bool = True
    ):
        """
        Initialize the enhanced configuration manager.
        
        Args:
            config_path: Path to configuration file
            env_mappings: Custom environment variable mappings
            enable_migration: Enable automatic Pydantic V2 migration
            enable_health_checks: Enable configuration health checks
        """
        self.config_path = Path(config_path) if config_path else Path("config.json")
        self.env_mappings = env_mappings or self.DEFAULT_ENV_MAPPINGS
        self.enable_migration = enable_migration
        self.enable_health_checks = enable_health_checks
        
        # Internal state
        self._config: Optional[Dict[str, Any]] = None
        self._config_lock = threading.RLock()
        self._validation_result: Optional[ConfigValidationResult] = None
        self._last_health_check: Optional[datetime] = None
        self._change_listeners: List[Callable[[Dict[str, Any]], None]] = []
        
        # Migration utility
        self._migration_utility = PydanticMigrationUtility() if enable_migration else None
        
        logger.info(f"Enhanced configuration manager initialized with config path: {self.config_path}")
    
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file with validation and migration.
        
        Args:
            config_path: Optional path to config file
            
        Returns:
            Dict containing the loaded configuration
            
        Raises:
            ConfigurationError: If configuration loading fails
        """
        with self._config_lock:
            file_path = Path(config_path) if config_path else self.config_path
            
            logger.info(f"Loading configuration from {file_path}")
            
            # Initialize with defaults
            config = self._get_default_config()
            
            # Load from file if it exists
            if file_path.exists():
                try:
                    file_config = self._load_config_file(file_path)
                    config = self._merge_configs(config, file_config)
                    logger.info(f"Loaded configuration from file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to load config file {file_path}: {e}")
                    # Continue with defaults and environment overrides
            else:
                logger.info(f"Config file {file_path} not found, using defaults")
            
            # Apply environment variable overrides (only for explicitly set env vars)
            env_config = self._load_from_environment()
            if env_config:  # Only merge if there are actual environment overrides
                config = self._merge_configs(config, env_config)
            
            # Perform Pydantic V2 migration if enabled
            if self.enable_migration:
                config = self._migrate_pydantic_config(config)
            
            # Validate configuration
            validation_result = self._validate_config(config)
            self._validation_result = validation_result
            
            # Log validation results
            self._log_validation_results(validation_result)
            
            # Store configuration
            self._config = config
            
            # Perform health checks if enabled
            if self.enable_health_checks:
                self._perform_health_checks()
            
            # Notify change listeners
            self._notify_change_listeners(config)
            
            return config
    
    def validate_environment(self) -> ConfigValidationResult:
        """
        Validate environment variables with clear error messages.
        
        Returns:
            ConfigValidationResult with validation details
        """
        logger.info("Validating environment variables")
        
        issues = []
        missing_required = []
        warnings = []
        
        for env_config in self.env_mappings:
            env_value = os.getenv(env_config.env_var)
            
            if env_value is None:
                if env_config.required:
                    missing_required.append(env_config.env_var)
                    issues.append(ConfigIssue(
                        key=env_config.env_var,
                        issue_type="missing",
                        message=f"Required environment variable {env_config.env_var} is not set",
                        suggested_fix=f"Set {env_config.env_var}={env_config.default_value or '<value>'} in your environment",
                        severity=ConfigValidationSeverity.ERROR,
                        source=ConfigSource.ENVIRONMENT
                    ))
                elif env_config.default_value is not None:
                    warnings.append(f"Using default value for {env_config.env_var}: {env_config.default_value}")
                    issues.append(ConfigIssue(
                        key=env_config.env_var,
                        issue_type="missing",
                        message=f"Environment variable {env_config.env_var} not set, using default: {env_config.default_value}",
                        suggested_fix=f"Set {env_config.env_var}=<value> to override default",
                        severity=ConfigValidationSeverity.WARNING,
                        source=ConfigSource.ENVIRONMENT
                    ))
            else:
                # Validate value type
                try:
                    converted_value = self._convert_env_value(env_value, env_config.value_type)
                    
                    # Validate pattern if specified
                    if env_config.validation_pattern:
                        import re
                        if not re.match(env_config.validation_pattern, str(converted_value)):
                            issues.append(ConfigIssue(
                                key=env_config.env_var,
                                issue_type="invalid",
                                message=f"Environment variable {env_config.env_var} does not match expected pattern",
                                suggested_fix=f"Ensure {env_config.env_var} matches pattern: {env_config.validation_pattern}",
                                severity=ConfigValidationSeverity.ERROR,
                                source=ConfigSource.ENVIRONMENT
                            ))
                            
                except ValueError as e:
                    issues.append(ConfigIssue(
                        key=env_config.env_var,
                        issue_type="invalid",
                        message=f"Environment variable {env_config.env_var} has invalid value type: {e}",
                        suggested_fix=f"Set {env_config.env_var} to a valid {env_config.value_type} value",
                        severity=ConfigValidationSeverity.ERROR,
                        source=ConfigSource.ENVIRONMENT
                    ))
        
        result = ConfigValidationResult(
            is_valid=len(missing_required) == 0 and not any(issue.severity == ConfigValidationSeverity.ERROR for issue in issues),
            issues=issues,
            missing_required=missing_required,
            warnings=warnings
        )
        
        logger.info(f"Environment validation complete: {len(issues)} issues found")
        return result
    
    def migrate_pydantic_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate Pydantic V1 configuration patterns to V2.
        
        Args:
            config: Configuration dictionary to migrate
            
        Returns:
            Migrated configuration dictionary
        """
        if not self._migration_utility:
            logger.warning("Pydantic migration disabled")
            return config
        
        logger.info("Migrating Pydantic V1 patterns to V2")
        
        # Check if migration is needed
        migration_needed = False
        
        # Look for deprecated patterns in config
        config_str = json.dumps(config, indent=2)
        
        # Check for schema_extra patterns
        if 'schema_extra' in config_str:
            migration_needed = True
            # Replace schema_extra with json_schema_extra
            config_str = config_str.replace('"schema_extra"', '"json_schema_extra"')
            config = json.loads(config_str)
            logger.info("Migrated schema_extra to json_schema_extra")
        
        # Check for other deprecated patterns
        deprecated_patterns = [
            'allow_population_by_field_name',
            'allow_reuse',
            'validate_all'
        ]
        
        for pattern in deprecated_patterns:
            if pattern in config_str:
                migration_needed = True
                logger.warning(f"Found deprecated Pydantic pattern: {pattern}")
        
        if migration_needed:
            logger.info("Pydantic V2 migration completed")
        
        return config
    
    def get_with_fallback(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with fallback to default.
        
        Args:
            key: Dot-notation key path (e.g., 'database.host')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if not self._config:
            self.load_config()
        
        return self._get_nested_value(self._config, key, default)
    
    def report_missing_configs(self) -> List[ConfigIssue]:
        """
        Report missing configuration values.
        
        Returns:
            List of ConfigIssue objects for missing configurations
        """
        if not self._validation_result:
            validation_result = self.validate_environment()
            self._validation_result = validation_result
        
        return [issue for issue in self._validation_result.issues 
                if issue.issue_type == "missing"]
    
    def perform_health_checks(self) -> Dict[str, Any]:
        """
        Perform configuration health checks.
        
        Returns:
            Dictionary with health check results
        """
        logger.info("Performing configuration health checks")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # Check configuration file accessibility
        health_status['checks']['config_file'] = {
            'status': 'healthy' if self.config_path.exists() else 'warning',
            'message': f"Config file {'exists' if self.config_path.exists() else 'missing'}: {self.config_path}"
        }
        
        # Check environment variables
        env_validation = self.validate_environment()
        health_status['checks']['environment'] = {
            'status': 'healthy' if env_validation.is_valid else ('warning' if not env_validation.has_errors else 'error'),
            'message': f"Environment validation: {len(env_validation.issues)} issues found",
            'issues': len(env_validation.issues)
        }
        
        # Check for deprecated patterns
        if self._migration_utility:
            try:
                issues = self._migration_utility.scan_for_deprecated_patterns()
                health_status['checks']['pydantic_migration'] = {
                    'status': 'healthy' if len(issues) == 0 else 'warning',
                    'message': f"Pydantic patterns: {len(issues)} deprecated patterns found",
                    'deprecated_patterns': len(issues)
                }
            except Exception as e:
                health_status['checks']['pydantic_migration'] = {
                    'status': 'error',
                    'message': f"Migration check failed: {e}"
                }
        
        # Check critical configuration values
        critical_configs = [
            'database.host',
            'security.jwt_secret'
        ]
        
        missing_critical = []
        for config_key in critical_configs:
            value = self.get_with_fallback(config_key)
            if not value or (isinstance(value, str) and value.strip() == ""):
                missing_critical.append(config_key)
        
        health_status['checks']['critical_configs'] = {
            'status': 'healthy' if len(missing_critical) == 0 else 'error',
            'message': f"Critical configs: {len(missing_critical)} missing",
            'missing': missing_critical
        }
        
        # Determine overall status
        check_statuses = [check['status'] for check in health_status['checks'].values()]
        if 'error' in check_statuses:
            health_status['overall_status'] = 'error'
        elif 'warning' in check_statuses:
            health_status['overall_status'] = 'warning'
        
        self._last_health_check = datetime.now()
        
        logger.info(f"Health check completed with status: {health_status['overall_status']}")
        return health_status
    
    def add_change_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        """Add a configuration change listener."""
        self._change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        """Remove a configuration change listener."""
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration state."""
        return {
            'config_loaded': self._config is not None,
            'config_path': str(self.config_path),
            'config_exists': self.config_path.exists(),
            'last_health_check': self._last_health_check.isoformat() if self._last_health_check else None,
            'validation_status': {
                'is_valid': self._validation_result.is_valid if self._validation_result else None,
                'issues_count': len(self._validation_result.issues) if self._validation_result else 0,
                'has_errors': self._validation_result.has_errors if self._validation_result else False,
                'has_warnings': self._validation_result.has_warnings if self._validation_result else False
            },
            'env_mappings_count': len(self.env_mappings),
            'change_listeners_count': len(self._change_listeners),
            'migration_enabled': self.enable_migration,
            'health_checks_enabled': self.enable_health_checks
        }
    
    # Private methods
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'environment': 'development',
            'debug': False,
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'ai_karen',
                'username': 'postgres',
                'password': ''
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'password': None
            },
            'llm': {
                'provider': 'local',
                'model': 'llama3.2:latest',
                'openai_api_key': None
            },
            'security': {
                'jwt_secret': 'change-me-in-production',
                'cors_origins': ['*']
            },
            'memory': {
                'enabled': True,
                'provider': 'local',
                'embedding_dim': 768,
                'decay_lambda': 0.1
            },
            'ui': {
                'show_debug_info': False
            }
        }
    
    def _load_config_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        suffix = file_path.suffix.lower()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            if suffix == '.json':
                return json.load(f)
            elif suffix in ['.yaml', '.yml']:
                if not YAML_AVAILABLE:
                    raise ImportError("PyYAML is required for YAML configuration files")
                return yaml.safe_load(f)
            else:
                # Try JSON as default
                return json.load(f)
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}
        
        for env_mapping in self.env_mappings:
            env_value = os.getenv(env_mapping.env_var)
            
            if env_value is not None:
                try:
                    converted_value = self._convert_env_value(env_value, env_mapping.value_type)
                    self._set_nested_value(env_config, env_mapping.config_path, converted_value)
                except ValueError as e:
                    logger.error(f"Failed to convert environment variable {env_mapping.env_var}: {e}")
            # Don't set default values here - they should be in the default config
        
        return env_config
    
    def _convert_env_value(self, value: str, value_type: str = "str") -> Any:
        """Convert environment variable value to appropriate type."""
        if value_type == "bool":
            return value.lower() in ("true", "1", "yes", "on")
        elif value_type == "int":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "list":
            return [item.strip() for item in value.split(",")]
        else:
            return value
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set a nested value in a dictionary using dot notation."""
        keys = path.split(".")
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _get_nested_value(self, data: Dict[str, Any], path: str, default: Any = None) -> Any:
        """Get a nested value from a dictionary using dot notation."""
        keys = path.split(".")
        current = data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration dictionaries recursively."""
        result = base.copy()
        
        for key, value in override.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _migrate_pydantic_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate Pydantic V1 patterns in configuration."""
        if not self.enable_migration:
            return config
        
        return self.migrate_pydantic_config(config)
    
    def _validate_config(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """Validate configuration and return validation result."""
        issues = []
        
        # Validate required fields
        required_fields = [
            'database.host',
            'security.jwt_secret'
        ]
        
        for field in required_fields:
            value = self._get_nested_value(config, field)
            if not value or (isinstance(value, str) and value.strip() == ""):
                issues.append(ConfigIssue(
                    key=field,
                    issue_type="missing",
                    message=f"Required configuration field {field} is missing or empty",
                    suggested_fix=f"Set {field} in configuration file or environment variable",
                    severity=ConfigValidationSeverity.ERROR,
                    source=ConfigSource.FILE
                ))
        
        # Validate production-specific requirements
        environment = self._get_nested_value(config, 'environment', 'development')
        if environment == 'production':
            jwt_secret = self._get_nested_value(config, 'security.jwt_secret')
            if jwt_secret == 'change-me-in-production':
                issues.append(ConfigIssue(
                    key='security.jwt_secret',
                    issue_type="invalid",
                    message="Default JWT secret should not be used in production",
                    suggested_fix="Set a secure JWT secret via JWT_SECRET environment variable",
                    severity=ConfigValidationSeverity.CRITICAL,
                    source=ConfigSource.FILE
                ))
        
        # Check for deprecated patterns
        config_str = json.dumps(config, indent=2)
        if 'schema_extra' in config_str:
            issues.append(ConfigIssue(
                key="pydantic_config",
                issue_type="deprecated",
                message="Deprecated Pydantic V1 pattern 'schema_extra' found",
                suggested_fix="Use 'json_schema_extra' instead of 'schema_extra'",
                severity=ConfigValidationSeverity.WARNING,
                source=ConfigSource.FILE
            ))
        
        return ConfigValidationResult(
            is_valid=not any(issue.severity in [ConfigValidationSeverity.ERROR, ConfigValidationSeverity.CRITICAL] 
                           for issue in issues),
            issues=issues,
            migration_needed='schema_extra' in config_str
        )
    
    def _log_validation_results(self, validation_result: ConfigValidationResult) -> None:
        """Log validation results with appropriate levels."""
        if validation_result.is_valid:
            logger.info("Configuration validation passed")
        else:
            logger.error("Configuration validation failed")
        
        for issue in validation_result.issues:
            if issue.severity == ConfigValidationSeverity.CRITICAL:
                logger.critical(f"{issue.key}: {issue.message} - {issue.suggested_fix}")
            elif issue.severity == ConfigValidationSeverity.ERROR:
                logger.error(f"{issue.key}: {issue.message} - {issue.suggested_fix}")
            elif issue.severity == ConfigValidationSeverity.WARNING:
                logger.warning(f"{issue.key}: {issue.message} - {issue.suggested_fix}")
            else:
                logger.info(f"{issue.key}: {issue.message} - {issue.suggested_fix}")
    
    def _perform_health_checks(self) -> None:
        """Perform internal health checks."""
        try:
            health_result = self.perform_health_checks()
            if health_result['overall_status'] != 'healthy':
                logger.warning(f"Configuration health check status: {health_result['overall_status']}")
        except Exception as e:
            logger.error(f"Configuration health check failed: {e}")
    
    def _notify_change_listeners(self, config: Dict[str, Any]) -> None:
        """Notify all change listeners of configuration changes."""
        for listener in self._change_listeners:
            try:
                listener(config)
            except Exception as e:
                logger.error(f"Configuration change listener error: {e}")


class ConfigurationError(Exception):
    """Configuration-related error"""
    pass


# Global configuration manager instance
_enhanced_config_manager: Optional[ConfigurationManager] = None


def get_enhanced_config_manager() -> ConfigurationManager:
    """Get the global enhanced configuration manager instance."""
    global _enhanced_config_manager
    if _enhanced_config_manager is None:
        _enhanced_config_manager = ConfigurationManager()
    return _enhanced_config_manager


def initialize_enhanced_config_manager(
    config_path: Optional[str] = None,
    env_mappings: Optional[List[EnvironmentVariableConfig]] = None
) -> ConfigurationManager:
    """Initialize the global enhanced configuration manager."""
    global _enhanced_config_manager
    _enhanced_config_manager = ConfigurationManager(
        config_path=config_path,
        env_mappings=env_mappings
    )
    return _enhanced_config_manager