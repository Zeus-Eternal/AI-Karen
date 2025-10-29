"""
Environment-aware configuration management for extension authentication.
Handles environment-specific settings, secure credential storage, and hot-reload capabilities.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import os
import json
import yaml
import logging
import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Supported deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class ConfigFormat(str, Enum):
    """Supported configuration file formats."""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"


@dataclass
class CredentialConfig:
    """Configuration for a single credential."""
    name: str
    value: str
    encrypted: bool = False
    expires_at: Optional[datetime] = None
    rotation_interval_days: Optional[int] = None
    environment: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class ExtensionEnvironmentConfig:
    """Environment-specific extension configuration."""
    environment: Environment
    
    # Authentication settings
    auth_enabled: bool = True
    secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    service_token_expire_minutes: int = 30
    api_key: str = ""
    
    # Security settings
    auth_mode: str = "hybrid"  # development, hybrid, strict
    dev_bypass_enabled: bool = False
    require_https: bool = True
    token_blacklist_enabled: bool = True
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 15
    audit_logging_enabled: bool = True
    
    # Rate limiting
    rate_limit_per_minute: int = 100
    burst_limit: int = 20
    enable_rate_limiting: bool = True
    
    # Permissions
    default_permissions: List[str] = None
    admin_permissions: List[str] = None
    service_permissions: List[str] = None
    
    # Health monitoring
    health_check_enabled: bool = True
    health_check_interval_seconds: int = 30
    health_check_timeout_seconds: int = 5
    
    # Logging
    log_level: str = "INFO"
    enable_debug_logging: bool = False
    log_sensitive_data: bool = False
    
    def __post_init__(self):
        if self.default_permissions is None:
            self.default_permissions = ["extension:read", "extension:write"]
        if self.admin_permissions is None:
            self.admin_permissions = ["extension:*"]
        if self.service_permissions is None:
            self.service_permissions = ["extension:background_tasks", "extension:health"]


class SecureCredentialManager:
    """Manages secure storage and rotation of credentials."""
    
    def __init__(self, storage_path: str, master_key: Optional[str] = None):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.credentials_file = self.storage_path / "credentials.enc"
        self.rotation_log_file = self.storage_path / "rotation.log"
        
        # Initialize encryption
        if master_key:
            self.master_key = master_key.encode()
        else:
            self.master_key = os.environ.get("EXTENSION_MASTER_KEY", "").encode()
            if not self.master_key:
                # Generate a new master key for development
                self.master_key = Fernet.generate_key()
                logger.warning("Generated new master key for credential encryption")
        
        self._setup_encryption()
        self.credentials: Dict[str, CredentialConfig] = {}
        self._load_credentials()
        
        # Rotation tracking
        self._rotation_lock = threading.Lock()
        self._rotation_tasks: Dict[str, asyncio.Task] = {}
    
    def _setup_encryption(self):
        """Setup encryption for credential storage."""
        try:
            # Derive key from master key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'extension_auth_salt',  # In production, use random salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
            self.cipher = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to setup encryption: {e}")
            raise
    
    def _load_credentials(self):
        """Load credentials from encrypted storage."""
        try:
            if not self.credentials_file.exists():
                logger.info("No existing credentials file found")
                return
            
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            credentials_data = json.loads(decrypted_data.decode())
            
            for name, data in credentials_data.items():
                # Convert datetime strings back to datetime objects
                if data.get('created_at'):
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if data.get('updated_at'):
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                if data.get('expires_at'):
                    data['expires_at'] = datetime.fromisoformat(data['expires_at'])
                
                self.credentials[name] = CredentialConfig(**data)
            
            logger.info(f"Loaded {len(self.credentials)} credentials from storage")
            
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            self.credentials = {}
    
    def _save_credentials(self):
        """Save credentials to encrypted storage."""
        try:
            # Convert credentials to serializable format
            credentials_data = {}
            for name, cred in self.credentials.items():
                data = asdict(cred)
                # Convert datetime objects to strings
                if data.get('created_at'):
                    data['created_at'] = data['created_at'].isoformat()
                if data.get('updated_at'):
                    data['updated_at'] = data['updated_at'].isoformat()
                if data.get('expires_at'):
                    data['expires_at'] = data['expires_at'].isoformat()
                credentials_data[name] = data
            
            # Encrypt and save
            json_data = json.dumps(credentials_data, indent=2)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
            
            logger.debug(f"Saved {len(self.credentials)} credentials to storage")
            
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            raise
    
    def store_credential(
        self,
        name: str,
        value: str,
        environment: Optional[str] = None,
        rotation_interval_days: Optional[int] = None,
        description: Optional[str] = None
    ) -> bool:
        """Store a credential securely."""
        try:
            # Calculate expiration if rotation is enabled
            expires_at = None
            if rotation_interval_days:
                expires_at = datetime.utcnow() + timedelta(days=rotation_interval_days)
            
            credential = CredentialConfig(
                name=name,
                value=value,
                encrypted=True,
                expires_at=expires_at,
                rotation_interval_days=rotation_interval_days,
                environment=environment,
                description=description,
                updated_at=datetime.utcnow()
            )
            
            self.credentials[name] = credential
            self._save_credentials()
            
            # Log rotation event
            self._log_rotation_event(name, "stored", environment)
            
            logger.info(f"Stored credential '{name}' for environment '{environment}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credential '{name}': {e}")
            return False
    
    def get_credential(self, name: str, environment: Optional[str] = None) -> Optional[str]:
        """Retrieve a credential value."""
        try:
            credential = self.credentials.get(name)
            if not credential:
                return None
            
            # Check environment match
            if environment and credential.environment and credential.environment != environment:
                return None
            
            # Check expiration
            if credential.expires_at and datetime.utcnow() > credential.expires_at:
                logger.warning(f"Credential '{name}' has expired")
                return None
            
            return credential.value
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential '{name}': {e}")
            return None
    
    def rotate_credential(self, name: str, new_value: Optional[str] = None) -> bool:
        """Rotate a credential to a new value."""
        try:
            credential = self.credentials.get(name)
            if not credential:
                logger.error(f"Credential '{name}' not found for rotation")
                return False
            
            # Generate new value if not provided
            if new_value is None:
                if name.endswith('_key') or name.endswith('_secret'):
                    # Generate secure random key
                    new_value = secrets.token_urlsafe(32)
                elif name.endswith('_api_key'):
                    # Generate API key format
                    new_value = f"ext_{secrets.token_urlsafe(24)}"
                else:
                    # Generate generic secure token
                    new_value = secrets.token_urlsafe(32)
            
            # Update credential
            old_value = credential.value
            credential.value = new_value
            credential.updated_at = datetime.utcnow()
            
            # Update expiration if rotation interval is set
            if credential.rotation_interval_days:
                credential.expires_at = datetime.utcnow() + timedelta(days=credential.rotation_interval_days)
            
            self._save_credentials()
            
            # Log rotation event
            self._log_rotation_event(name, "rotated", credential.environment)
            
            logger.info(f"Rotated credential '{name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate credential '{name}': {e}")
            return False
    
    def list_credentials(self, environment: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all credentials (without values)."""
        try:
            result = []
            for name, credential in self.credentials.items():
                if environment and credential.environment and credential.environment != environment:
                    continue
                
                result.append({
                    'name': name,
                    'environment': credential.environment,
                    'expires_at': credential.expires_at.isoformat() if credential.expires_at else None,
                    'rotation_interval_days': credential.rotation_interval_days,
                    'description': credential.description,
                    'created_at': credential.created_at.isoformat() if credential.created_at else None,
                    'updated_at': credential.updated_at.isoformat() if credential.updated_at else None,
                    'expired': credential.expires_at and datetime.utcnow() > credential.expires_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list credentials: {e}")
            return []
    
    def _log_rotation_event(self, credential_name: str, action: str, environment: Optional[str]):
        """Log credential rotation events."""
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'credential_name': credential_name,
                'action': action,
                'environment': environment,
                'user': os.environ.get('USER', 'system')
            }
            
            with open(self.rotation_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to log rotation event: {e}")
    
    async def start_auto_rotation(self):
        """Start automatic credential rotation for credentials with rotation intervals."""
        try:
            for name, credential in self.credentials.items():
                if credential.rotation_interval_days and credential.expires_at:
                    # Calculate time until rotation
                    time_until_rotation = credential.expires_at - datetime.utcnow()
                    
                    if time_until_rotation.total_seconds() > 0:
                        # Schedule rotation
                        task = asyncio.create_task(
                            self._schedule_rotation(name, time_until_rotation.total_seconds())
                        )
                        self._rotation_tasks[name] = task
                        logger.info(f"Scheduled rotation for credential '{name}' in {time_until_rotation}")
            
        except Exception as e:
            logger.error(f"Failed to start auto rotation: {e}")
    
    async def _schedule_rotation(self, credential_name: str, delay_seconds: float):
        """Schedule a credential rotation."""
        try:
            await asyncio.sleep(delay_seconds)
            
            with self._rotation_lock:
                success = self.rotate_credential(credential_name)
                if success:
                    logger.info(f"Auto-rotated credential '{credential_name}'")
                else:
                    logger.error(f"Failed to auto-rotate credential '{credential_name}'")
            
            # Remove from rotation tasks
            self._rotation_tasks.pop(credential_name, None)
            
        except asyncio.CancelledError:
            logger.info(f"Rotation cancelled for credential '{credential_name}'")
        except Exception as e:
            logger.error(f"Error in scheduled rotation for '{credential_name}': {e}")
    
    def stop_auto_rotation(self):
        """Stop all automatic rotation tasks."""
        for task in self._rotation_tasks.values():
            task.cancel()
        self._rotation_tasks.clear()
        logger.info("Stopped all auto-rotation tasks")


class ConfigFileWatcher(FileSystemEventHandler):
    """Watches configuration files for changes and triggers hot-reload."""
    
    def __init__(self, config_manager: 'ExtensionEnvironmentConfigManager'):
        self.config_manager = config_manager
        self.debounce_delay = 1.0  # seconds
        self._reload_timer: Optional[threading.Timer] = None
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Check if it's a config file we care about
        if file_path.suffix.lower() in ['.json', '.yaml', '.yml', '.env']:
            logger.debug(f"Config file modified: {file_path}")
            self._debounced_reload()
    
    def _debounced_reload(self):
        """Debounced configuration reload to avoid multiple rapid reloads."""
        if self._reload_timer:
            self._reload_timer.cancel()
        
        self._reload_timer = threading.Timer(
            self.debounce_delay,
            self._trigger_reload
        )
        self._reload_timer.start()
    
    def _trigger_reload(self):
        """Trigger configuration reload."""
        try:
            asyncio.create_task(self.config_manager.reload_configuration())
        except Exception as e:
            logger.error(f"Failed to trigger config reload: {e}")


class ExtensionEnvironmentConfigManager:
    """Manages environment-aware configuration for extension authentication."""
    
    def __init__(
        self,
        config_dir: str = "config/extensions",
        credentials_dir: str = "config/extensions/credentials",
        enable_hot_reload: bool = True
    ):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.credentials_manager = SecureCredentialManager(credentials_dir)
        self.enable_hot_reload = enable_hot_reload
        
        # Configuration storage
        self.configurations: Dict[Environment, ExtensionEnvironmentConfig] = {}
        self.current_environment = self._detect_environment()
        self.config_validators: List[Callable[[ExtensionEnvironmentConfig], List[str]]] = []
        self.reload_callbacks: List[Callable[[ExtensionEnvironmentConfig], None]] = []
        
        # File watching
        self.file_observer: Optional[Observer] = None
        self.file_watcher: Optional[ConfigFileWatcher] = None
        
        # Load initial configuration
        self._load_all_configurations()
        
        # Start file watching if enabled
        if self.enable_hot_reload:
            self._start_file_watching()
    
    def _detect_environment(self) -> Environment:
        """Detect the current environment from environment variables."""
        env_var = (
            os.getenv("EXTENSION_ENVIRONMENT") or
            os.getenv("ENVIRONMENT") or
            os.getenv("KARI_ENV") or
            os.getenv("ENV") or
            "development"
        ).lower()
        
        try:
            return Environment(env_var)
        except ValueError:
            logger.warning(f"Unknown environment '{env_var}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _load_all_configurations(self):
        """Load configurations for all environments."""
        try:
            for environment in Environment:
                config = self._load_environment_config(environment)
                self.configurations[environment] = config
            
            logger.info(f"Loaded configurations for {len(self.configurations)} environments")
            
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            # Create default configurations
            self._create_default_configurations()
    
    def _load_environment_config(self, environment: Environment) -> ExtensionEnvironmentConfig:
        """Load configuration for a specific environment."""
        config_file = self.config_dir / f"{environment.value}.yaml"
        
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f) or {}
                
                # Apply environment-specific defaults
                config_data = self._apply_environment_defaults(environment, config_data)
                
                # Load credentials
                config_data = self._load_credentials_for_config(environment, config_data)
                
                return ExtensionEnvironmentConfig(environment=environment, **config_data)
            else:
                logger.info(f"No config file found for {environment.value}, using defaults")
                return self._create_default_config(environment)
                
        except Exception as e:
            logger.error(f"Failed to load config for {environment.value}: {e}")
            return self._create_default_config(environment)
    
    def _apply_environment_defaults(self, environment: Environment, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment-specific defaults."""
        defaults = {
            Environment.DEVELOPMENT: {
                'auth_mode': 'development',
                'dev_bypass_enabled': True,
                'require_https': False,
                'rate_limit_per_minute': 1000,
                'burst_limit': 100,
                'max_failed_attempts': 10,
                'lockout_duration_minutes': 1,
                'enable_debug_logging': True,
                'log_sensitive_data': True,
                'health_check_interval_seconds': 60,
            },
            Environment.STAGING: {
                'auth_mode': 'hybrid',
                'dev_bypass_enabled': False,
                'require_https': True,
                'rate_limit_per_minute': 200,
                'burst_limit': 30,
                'max_failed_attempts': 5,
                'lockout_duration_minutes': 10,
                'enable_debug_logging': True,
                'log_sensitive_data': False,
                'health_check_interval_seconds': 30,
            },
            Environment.PRODUCTION: {
                'auth_mode': 'strict',
                'dev_bypass_enabled': False,
                'require_https': True,
                'rate_limit_per_minute': 100,
                'burst_limit': 20,
                'max_failed_attempts': 3,
                'lockout_duration_minutes': 30,
                'enable_debug_logging': False,
                'log_sensitive_data': False,
                'health_check_interval_seconds': 30,
            },
            Environment.TEST: {
                'auth_mode': 'development',
                'dev_bypass_enabled': True,
                'require_https': False,
                'rate_limit_per_minute': 10000,
                'burst_limit': 1000,
                'max_failed_attempts': 100,
                'lockout_duration_minutes': 0,
                'enable_debug_logging': True,
                'log_sensitive_data': True,
                'health_check_interval_seconds': 120,
            }
        }
        
        env_defaults = defaults.get(environment, {})
        
        # Merge defaults with provided config
        for key, value in env_defaults.items():
            if key not in config_data:
                config_data[key] = value
        
        return config_data
    
    def _load_credentials_for_config(self, environment: Environment, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load credentials from secure storage for configuration."""
        try:
            # Load secret key
            secret_key = self.credentials_manager.get_credential(
                f"extension_secret_key_{environment.value}",
                environment.value
            )
            if secret_key:
                config_data['secret_key'] = secret_key
            elif not config_data.get('secret_key'):
                # Generate and store new secret key
                new_secret_key = secrets.token_urlsafe(32)
                self.credentials_manager.store_credential(
                    f"extension_secret_key_{environment.value}",
                    new_secret_key,
                    environment.value,
                    rotation_interval_days=90 if environment == Environment.PRODUCTION else None,
                    description=f"Extension authentication secret key for {environment.value}"
                )
                config_data['secret_key'] = new_secret_key
            
            # Load API key
            api_key = self.credentials_manager.get_credential(
                f"extension_api_key_{environment.value}",
                environment.value
            )
            if api_key:
                config_data['api_key'] = api_key
            elif not config_data.get('api_key'):
                # Generate and store new API key
                new_api_key = f"ext_{environment.value}_{secrets.token_urlsafe(24)}"
                self.credentials_manager.store_credential(
                    f"extension_api_key_{environment.value}",
                    new_api_key,
                    environment.value,
                    rotation_interval_days=30 if environment == Environment.PRODUCTION else None,
                    description=f"Extension API key for {environment.value}"
                )
                config_data['api_key'] = new_api_key
            
            return config_data
            
        except Exception as e:
            logger.error(f"Failed to load credentials for {environment.value}: {e}")
            return config_data
    
    def _create_default_config(self, environment: Environment) -> ExtensionEnvironmentConfig:
        """Create default configuration for an environment."""
        config_data = self._apply_environment_defaults(environment, {})
        config_data = self._load_credentials_for_config(environment, config_data)
        return ExtensionEnvironmentConfig(environment=environment, **config_data)
    
    def _create_default_configurations(self):
        """Create default configurations for all environments."""
        for environment in Environment:
            self.configurations[environment] = self._create_default_config(environment)
    
    def get_current_config(self) -> ExtensionEnvironmentConfig:
        """Get configuration for the current environment."""
        return self.configurations.get(self.current_environment, self._create_default_config(self.current_environment))
    
    def get_config(self, environment: Environment) -> ExtensionEnvironmentConfig:
        """Get configuration for a specific environment."""
        return self.configurations.get(environment, self._create_default_config(environment))
    
    def update_config(
        self,
        environment: Environment,
        updates: Dict[str, Any],
        save_to_file: bool = True
    ) -> bool:
        """Update configuration for an environment."""
        try:
            config = self.configurations.get(environment)
            if not config:
                config = self._create_default_config(environment)
                self.configurations[environment] = config
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    logger.warning(f"Unknown config key '{key}' for environment {environment.value}")
            
            # Validate configuration
            validation_errors = self.validate_config(config)
            if validation_errors:
                logger.error(f"Configuration validation failed for {environment.value}:")
                for error in validation_errors:
                    logger.error(f"  - {error}")
                return False
            
            # Save to file if requested
            if save_to_file:
                self._save_environment_config(environment, config)
            
            # Trigger reload callbacks
            self._trigger_reload_callbacks(config)
            
            logger.info(f"Updated configuration for {environment.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update config for {environment.value}: {e}")
            return False
    
    def _save_environment_config(self, environment: Environment, config: ExtensionEnvironmentConfig):
        """Save configuration to file."""
        try:
            config_file = self.config_dir / f"{environment.value}.yaml"
            
            # Convert config to dict, excluding sensitive data
            config_dict = asdict(config)
            config_dict.pop('environment', None)  # Don't save environment in file
            
            # Remove credentials from config dict (they're stored securely)
            sensitive_keys = ['secret_key', 'api_key']
            for key in sensitive_keys:
                config_dict.pop(key, None)
            
            with open(config_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            logger.debug(f"Saved configuration for {environment.value} to {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save config for {environment.value}: {e}")
            raise
    
    def validate_config(self, config: ExtensionEnvironmentConfig) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        try:
            # Basic validation
            if not config.secret_key:
                errors.append("secret_key is required")
            elif len(config.secret_key) < 32:
                errors.append("secret_key must be at least 32 characters")
            
            if not config.api_key:
                errors.append("api_key is required")
            
            if config.access_token_expire_minutes <= 0:
                errors.append("access_token_expire_minutes must be positive")
            
            if config.service_token_expire_minutes <= 0:
                errors.append("service_token_expire_minutes must be positive")
            
            if config.auth_mode not in ['development', 'hybrid', 'strict']:
                errors.append("auth_mode must be one of: development, hybrid, strict")
            
            if config.jwt_algorithm not in ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']:
                errors.append("jwt_algorithm must be a valid JWT algorithm")
            
            if config.rate_limit_per_minute <= 0:
                errors.append("rate_limit_per_minute must be positive")
            
            if config.burst_limit <= 0:
                errors.append("burst_limit must be positive")
            
            if config.max_failed_attempts < 0:
                errors.append("max_failed_attempts must be non-negative")
            
            if config.lockout_duration_minutes < 0:
                errors.append("lockout_duration_minutes must be non-negative")
            
            if config.health_check_interval_seconds <= 0:
                errors.append("health_check_interval_seconds must be positive")
            
            if config.health_check_timeout_seconds <= 0:
                errors.append("health_check_timeout_seconds must be positive")
            
            # Environment-specific validation
            if config.environment == Environment.PRODUCTION:
                if config.dev_bypass_enabled:
                    errors.append("dev_bypass_enabled should be False in production")
                
                if not config.require_https:
                    errors.append("require_https should be True in production")
                
                if config.auth_mode == 'development':
                    errors.append("auth_mode should not be 'development' in production")
                
                if config.log_sensitive_data:
                    errors.append("log_sensitive_data should be False in production")
            
            # Run custom validators
            for validator in self.config_validators:
                try:
                    validator_errors = validator(config)
                    if validator_errors:
                        errors.extend(validator_errors)
                except Exception as e:
                    errors.append(f"Validator error: {e}")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    def add_config_validator(self, validator: Callable[[ExtensionEnvironmentConfig], List[str]]):
        """Add a custom configuration validator."""
        self.config_validators.append(validator)
    
    def add_reload_callback(self, callback: Callable[[ExtensionEnvironmentConfig], None]):
        """Add a callback to be called when configuration is reloaded."""
        self.reload_callbacks.append(callback)
    
    def _trigger_reload_callbacks(self, config: ExtensionEnvironmentConfig):
        """Trigger all reload callbacks."""
        for callback in self.reload_callbacks:
            try:
                callback(config)
            except Exception as e:
                logger.error(f"Error in reload callback: {e}")
    
    async def reload_configuration(self):
        """Reload configuration from files."""
        try:
            logger.info("Reloading extension configuration...")
            
            old_configs = self.configurations.copy()
            self._load_all_configurations()
            
            # Check for changes and trigger callbacks
            current_config = self.get_current_config()
            old_current_config = old_configs.get(self.current_environment)
            
            if not old_current_config or asdict(current_config) != asdict(old_current_config):
                logger.info(f"Configuration changed for {self.current_environment.value}")
                self._trigger_reload_callbacks(current_config)
            
            logger.info("Configuration reload completed")
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
    
    def _start_file_watching(self):
        """Start watching configuration files for changes."""
        try:
            if self.file_observer:
                return  # Already watching
            
            self.file_watcher = ConfigFileWatcher(self)
            self.file_observer = Observer()
            self.file_observer.schedule(
                self.file_watcher,
                str(self.config_dir),
                recursive=True
            )
            self.file_observer.start()
            
            logger.info(f"Started watching configuration files in {self.config_dir}")
            
        except Exception as e:
            logger.error(f"Failed to start file watching: {e}")
    
    def stop_file_watching(self):
        """Stop watching configuration files."""
        try:
            if self.file_observer:
                self.file_observer.stop()
                self.file_observer.join()
                self.file_observer = None
                self.file_watcher = None
                logger.info("Stopped watching configuration files")
        except Exception as e:
            logger.error(f"Failed to stop file watching: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the configuration system."""
        try:
            current_config = self.get_current_config()
            validation_errors = self.validate_config(current_config)
            
            credentials_list = self.credentials_manager.list_credentials()
            expired_credentials = [c for c in credentials_list if c.get('expired')]
            
            return {
                'status': 'healthy' if not validation_errors and not expired_credentials else 'degraded',
                'environment': self.current_environment.value,
                'config_valid': len(validation_errors) == 0,
                'validation_errors': validation_errors,
                'credentials_count': len(credentials_list),
                'expired_credentials_count': len(expired_credentials),
                'expired_credentials': [c['name'] for c in expired_credentials],
                'file_watching_enabled': self.enable_hot_reload,
                'file_watching_active': self.file_observer is not None and self.file_observer.is_alive(),
                'last_reload': datetime.utcnow().isoformat(),
                'config_dir': str(self.config_dir),
                'credentials_dir': str(self.credentials_manager.storage_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    async def start_services(self):
        """Start configuration management services."""
        try:
            # Start credential auto-rotation
            await self.credentials_manager.start_auto_rotation()
            
            # Start file watching if not already started
            if self.enable_hot_reload and not self.file_observer:
                self._start_file_watching()
            
            logger.info("Started extension configuration management services")
            
        except Exception as e:
            logger.error(f"Failed to start configuration services: {e}")
            raise
    
    def stop_services(self):
        """Stop configuration management services."""
        try:
            # Stop credential auto-rotation
            self.credentials_manager.stop_auto_rotation()
            
            # Stop file watching
            self.stop_file_watching()
            
            logger.info("Stopped extension configuration management services")
            
        except Exception as e:
            logger.error(f"Failed to stop configuration services: {e}")
    
    def export_config(self, environment: Environment, format: ConfigFormat = ConfigFormat.YAML) -> str:
        """Export configuration in specified format."""
        try:
            config = self.get_config(environment)
            config_dict = asdict(config)
            
            # Remove sensitive data
            sensitive_keys = ['secret_key', 'api_key']
            for key in sensitive_keys:
                if key in config_dict:
                    config_dict[key] = "***REDACTED***"
            
            if format == ConfigFormat.JSON:
                return json.dumps(config_dict, indent=2, default=str)
            elif format == ConfigFormat.YAML:
                return yaml.dump(config_dict, default_flow_style=False, indent=2)
            elif format == ConfigFormat.ENV:
                env_lines = []
                for key, value in config_dict.items():
                    env_key = f"EXTENSION_{key.upper()}"
                    if isinstance(value, list):
                        value = ",".join(str(v) for v in value)
                    env_lines.append(f"{env_key}={value}")
                return "\n".join(env_lines)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export config for {environment.value}: {e}")
            raise


# Global configuration manager instance
config_manager: Optional[ExtensionEnvironmentConfigManager] = None


def get_config_manager() -> ExtensionEnvironmentConfigManager:
    """Get the global configuration manager instance."""
    global config_manager
    if config_manager is None:
        config_manager = ExtensionEnvironmentConfigManager()
    return config_manager


def get_current_extension_config() -> ExtensionEnvironmentConfig:
    """Get the current extension configuration."""
    return get_config_manager().get_current_config()


async def initialize_extension_config():
    """Initialize the extension configuration system."""
    try:
        manager = get_config_manager()
        await manager.start_services()
        logger.info("Extension configuration system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize extension configuration: {e}")
        raise


def shutdown_extension_config():
    """Shutdown the extension configuration system."""
    try:
        global config_manager
        if config_manager:
            config_manager.stop_services()
            config_manager = None
        logger.info("Extension configuration system shutdown")
    except Exception as e:
        logger.error(f"Failed to shutdown extension configuration: {e}")