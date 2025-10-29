"""
Development-Specific Configuration Management for Extensions

Provides environment-aware configuration management that adapts automatically
between development, staging, and production environments.

Requirements addressed:
- 6.4: Detailed logging for debugging extension issues
- 6.5: Environment-specific configuration adaptation
- 8.1: Environment-specific configuration (dev/staging/prod)
- 8.2: Secure credential storage and management
- 8.3: Configuration validation and health checks
- 8.4: Configuration hot-reload without service restart
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import yaml

logger = logging.getLogger(__name__)

@dataclass
class DevelopmentAuthConfig:
    """Development authentication configuration."""
    enabled: bool = True
    bypass_auth: bool = True
    mock_auth_enabled: bool = True
    hot_reload_support: bool = True
    debug_logging: bool = True
    auto_token_refresh: bool = True
    token_expiry_hours: int = 24
    mock_users_file: Optional[str] = None
    dev_api_key: str = "dev-extension-api-key"
    dev_secret_key: str = "dev-extension-secret-key"

@dataclass
class DevelopmentServerConfig:
    """Development server configuration."""
    host: str = "localhost"
    port: int = 8000
    reload: bool = True
    debug: bool = True
    log_level: str = "DEBUG"
    cors_origins: List[str] = None
    allow_credentials: bool = True
    hot_reload_paths: List[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = [
                "http://localhost:3000",
                "http://localhost:3001", 
                "http://localhost:8010",
                "http://localhost:8020",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
                "http://127.0.0.1:8010",
                "http://127.0.0.1:8020"
            ]
        
        if self.hot_reload_paths is None:
            self.hot_reload_paths = [
                "server/",
                "ui_launchers/web_ui/src/",
                "extensions/",
                "config/"
            ]

@dataclass
class DevelopmentDatabaseConfig:
    """Development database configuration."""
    url: str = "postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen_dev"
    echo: bool = True
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    auto_create_tables: bool = True
    seed_test_data: bool = True

@dataclass
class DevelopmentExtensionConfig:
    """Development extension configuration."""
    auto_load: bool = True
    auto_reload: bool = True
    development_extensions_path: str = "extensions/development/"
    test_extensions_path: str = "extensions/test/"
    mock_external_services: bool = True
    enable_extension_debugging: bool = True
    extension_timeout_seconds: int = 30
    max_extension_memory_mb: int = 512

class DevelopmentConfigManager:
    """Manages development-specific configuration with hot reload support."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize development configuration manager."""
        self.config_dir = Path(config_dir or "config/development/")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_files = {
            "auth": self.config_dir / "auth.yaml",
            "server": self.config_dir / "server.yaml", 
            "database": self.config_dir / "database.yaml",
            "extensions": self.config_dir / "extensions.yaml",
            "logging": self.config_dir / "logging.yaml"
        }
        
        self.configs = {}
        self.file_watchers = {}
        self.last_modified = {}
        
        # Initialize configurations
        self._initialize_default_configs()
        self._load_all_configs()
        
        logger.info(f"Development configuration manager initialized with config dir: {self.config_dir}")
    
    def _initialize_default_configs(self):
        """Initialize default configuration files if they don't exist."""
        default_configs = {
            "auth": {
                "development_auth": asdict(DevelopmentAuthConfig()),
                "jwt_settings": {
                    "secret_key": "${EXTENSION_SECRET_KEY:-dev-extension-secret-key}",
                    "algorithm": "HS256",
                    "access_token_expire_minutes": 1440,  # 24 hours
                    "refresh_token_expire_days": 7
                },
                "api_keys": {
                    "extension_api_key": "${EXTENSION_API_KEY:-dev-extension-api-key}",
                    "admin_api_key": "${ADMIN_API_KEY:-dev-admin-api-key}"
                },
                "rate_limiting": {
                    "enabled": False,  # Disabled in development
                    "requests_per_minute": 1000,
                    "burst_limit": 100
                }
            },
            "server": asdict(DevelopmentServerConfig()),
            "database": asdict(DevelopmentDatabaseConfig()),
            "extensions": asdict(DevelopmentExtensionConfig()),
            "logging": {
                "level": "DEBUG",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "formatter": "detailed"
                    },
                    "file": {
                        "class": "logging.FileHandler",
                        "filename": "logs/development.log",
                        "level": "DEBUG",
                        "formatter": "detailed"
                    }
                },
                "loggers": {
                    "server.extension_dev_auth": {"level": "DEBUG"},
                    "server.extension_dev_config": {"level": "DEBUG"},
                    "extensions": {"level": "DEBUG"},
                    "uvicorn": {"level": "INFO"}
                }
            }
        }
        
        for config_name, config_data in default_configs.items():
            config_file = self.config_files[config_name]
            if not config_file.exists():
                self._write_config_file(config_file, config_data)
                logger.info(f"Created default {config_name} configuration: {config_file}")
    
    def _write_config_file(self, file_path: Path, config_data: Dict[str, Any]):
        """Write configuration data to YAML file."""
        try:
            with open(file_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to write config file {file_path}: {e}")
    
    def _load_all_configs(self):
        """Load all configuration files."""
        for config_name, config_file in self.config_files.items():
            self._load_config(config_name, config_file)
    
    def _load_config(self, config_name: str, config_file: Path):
        """Load a single configuration file."""
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Expand environment variables
                config_data = self._expand_environment_variables(config_data)
                
                self.configs[config_name] = config_data
                self.last_modified[config_name] = config_file.stat().st_mtime
                
                logger.debug(f"Loaded {config_name} configuration from {config_file}")
            else:
                logger.warning(f"Configuration file not found: {config_file}")
                self.configs[config_name] = {}
        
        except Exception as e:
            logger.error(f"Failed to load {config_name} configuration from {config_file}: {e}")
            self.configs[config_name] = {}
    
    def _expand_environment_variables(self, config_data: Any) -> Any:
        """Recursively expand environment variables in configuration."""
        if isinstance(config_data, dict):
            return {key: self._expand_environment_variables(value) for key, value in config_data.items()}
        elif isinstance(config_data, list):
            return [self._expand_environment_variables(item) for item in config_data]
        elif isinstance(config_data, str) and config_data.startswith("${") and config_data.endswith("}"):
            # Parse environment variable with optional default
            env_expr = config_data[2:-1]  # Remove ${ and }
            if ":-" in env_expr:
                env_var, default_value = env_expr.split(":-", 1)
                return os.getenv(env_var, default_value)
            else:
                return os.getenv(env_expr, config_data)
        else:
            return config_data
    
    def get_auth_config(self) -> DevelopmentAuthConfig:
        """Get development authentication configuration."""
        auth_config = self.configs.get("auth", {}).get("development_auth", {})
        return DevelopmentAuthConfig(**auth_config)
    
    def get_server_config(self) -> DevelopmentServerConfig:
        """Get development server configuration."""
        server_config = self.configs.get("server", {})
        return DevelopmentServerConfig(**server_config)
    
    def get_database_config(self) -> DevelopmentDatabaseConfig:
        """Get development database configuration."""
        db_config = self.configs.get("database", {})
        return DevelopmentDatabaseConfig(**db_config)
    
    def get_extension_config(self) -> DevelopmentExtensionConfig:
        """Get development extension configuration."""
        ext_config = self.configs.get("extensions", {})
        return DevelopmentExtensionConfig(**ext_config)
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get development logging configuration."""
        return self.configs.get("logging", {})
    
    def get_jwt_settings(self) -> Dict[str, Any]:
        """Get JWT settings for development."""
        return self.configs.get("auth", {}).get("jwt_settings", {})
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get API keys for development."""
        return self.configs.get("auth", {}).get("api_keys", {})
    
    def get_rate_limiting_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration."""
        return self.configs.get("auth", {}).get("rate_limiting", {})
    
    def check_for_config_changes(self) -> List[str]:
        """Check for configuration file changes and reload if necessary."""
        changed_configs = []
        
        for config_name, config_file in self.config_files.items():
            if config_file.exists():
                current_mtime = config_file.stat().st_mtime
                last_mtime = self.last_modified.get(config_name, 0)
                
                if current_mtime > last_mtime:
                    logger.info(f"Configuration file changed: {config_file}")
                    self._load_config(config_name, config_file)
                    changed_configs.append(config_name)
        
        return changed_configs
    
    def reload_config(self, config_name: Optional[str] = None):
        """Reload specific configuration or all configurations."""
        if config_name:
            if config_name in self.config_files:
                self._load_config(config_name, self.config_files[config_name])
                logger.info(f"Reloaded {config_name} configuration")
            else:
                logger.warning(f"Unknown configuration: {config_name}")
        else:
            self._load_all_configs()
            logger.info("Reloaded all configurations")
    
    def validate_configuration(self) -> Dict[str, List[str]]:
        """Validate all configurations and return any errors."""
        errors = {}
        
        # Validate auth configuration
        auth_errors = []
        auth_config = self.get_auth_config()
        
        if auth_config.enabled and not auth_config.dev_secret_key:
            auth_errors.append("dev_secret_key is required when auth is enabled")
        
        if auth_config.token_expiry_hours <= 0:
            auth_errors.append("token_expiry_hours must be positive")
        
        if auth_errors:
            errors["auth"] = auth_errors
        
        # Validate server configuration
        server_errors = []
        server_config = self.get_server_config()
        
        if server_config.port <= 0 or server_config.port > 65535:
            server_errors.append("port must be between 1 and 65535")
        
        if server_errors:
            errors["server"] = server_errors
        
        # Validate database configuration
        db_errors = []
        db_config = self.get_database_config()
        
        if not db_config.url:
            db_errors.append("database URL is required")
        
        if db_config.pool_size <= 0:
            db_errors.append("pool_size must be positive")
        
        if db_errors:
            errors["database"] = db_errors
        
        # Validate extension configuration
        ext_errors = []
        ext_config = self.get_extension_config()
        
        if ext_config.extension_timeout_seconds <= 0:
            ext_errors.append("extension_timeout_seconds must be positive")
        
        if ext_config.max_extension_memory_mb <= 0:
            ext_errors.append("max_extension_memory_mb must be positive")
        
        if ext_errors:
            errors["extensions"] = ext_errors
        
        return errors
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get current environment information."""
        return {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "node_env": os.getenv("NODE_ENV", "development"),
            "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
            "config_dir": str(self.config_dir),
            "config_files": {name: str(path) for name, path in self.config_files.items()},
            "last_reload": max(self.last_modified.values()) if self.last_modified else None,
            "python_version": os.sys.version,
            "working_directory": os.getcwd()
        }
    
    def export_config(self, config_name: Optional[str] = None) -> Dict[str, Any]:
        """Export configuration for debugging or backup."""
        if config_name:
            return {config_name: self.configs.get(config_name, {})}
        else:
            return dict(self.configs)
    
    def update_config(self, config_name: str, updates: Dict[str, Any], persist: bool = True):
        """Update configuration values."""
        if config_name not in self.configs:
            logger.warning(f"Unknown configuration: {config_name}")
            return
        
        # Deep merge updates
        self._deep_merge(self.configs[config_name], updates)
        
        if persist:
            # Write updated configuration to file
            config_file = self.config_files[config_name]
            self._write_config_file(config_file, self.configs[config_name])
            logger.info(f"Updated and persisted {config_name} configuration")
        else:
            logger.info(f"Updated {config_name} configuration (in-memory only)")
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge source dictionary into target dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def create_development_environment_file(self) -> str:
        """Create a .env file for development environment."""
        env_file_path = self.config_dir.parent / ".env.development"
        
        auth_config = self.get_auth_config()
        server_config = self.get_server_config()
        db_config = self.get_database_config()
        
        env_content = f"""# Development Environment Configuration
# Generated on {datetime.now().isoformat()}

# Environment
ENVIRONMENT=development
NODE_ENV=development
DEBUG=true

# Extension Authentication
EXTENSION_SECRET_KEY={auth_config.dev_secret_key}
EXTENSION_API_KEY={auth_config.dev_api_key}
EXTENSION_AUTH_ENABLED={str(auth_config.enabled).lower()}
EXTENSION_DEV_BYPASS_ENABLED={str(auth_config.bypass_auth).lower()}
EXTENSION_DEVELOPMENT_MODE=true

# Server Configuration
HOST={server_config.host}
PORT={server_config.port}
LOG_LEVEL={server_config.log_level}

# Database Configuration
DATABASE_URL={db_config.url}
DB_ECHO={str(db_config.echo).lower()}
DB_POOL_SIZE={db_config.pool_size}

# CORS Origins
CORS_ORIGINS={','.join(server_config.cors_origins)}

# Hot Reload
ENABLE_HOT_RELOAD=true
HOT_RELOAD_PATHS={','.join(server_config.hot_reload_paths)}
"""
        
        try:
            with open(env_file_path, 'w') as f:
                f.write(env_content)
            
            logger.info(f"Created development environment file: {env_file_path}")
            return str(env_file_path)
        
        except Exception as e:
            logger.error(f"Failed to create development environment file: {e}")
            return ""


# Global development config manager instance
_dev_config_manager: Optional[DevelopmentConfigManager] = None

def get_development_config_manager() -> DevelopmentConfigManager:
    """Get or create the global development configuration manager."""
    global _dev_config_manager
    if _dev_config_manager is None:
        _dev_config_manager = DevelopmentConfigManager()
    return _dev_config_manager

def reset_development_config_manager():
    """Reset the global development configuration manager (useful for testing)."""
    global _dev_config_manager
    _dev_config_manager = None