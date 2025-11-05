"""
Configuration Management for AI Karen Engine Integration.

This module provides centralized configuration management for integrating
the new Python backend services with the existing AI Karen engine.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Environment enumeration."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"


@dataclass
class DatabaseConfig:
    """Database configuration."""

    host: str = "localhost"
    port: int = 5432
    database: str = "ai_karen"
    username: str = "postgres"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    ssl_mode: str = "prefer"


@dataclass
class RedisConfig:
    """Redis configuration."""

    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True


@dataclass
class VectorDBConfig:
    """Vector database configuration."""

    provider: str = "milvus"  # milvus, pinecone, weaviate
    host: str = "localhost"
    port: int = 19530
    collection_name: str = "ai_karen_memories"
    dimension: int = 1536
    metric_type: str = "COSINE"
    index_type: str = "IVF_FLAT"
    nlist: int = 1024


@dataclass
class LLMConfig:
    """LLM configuration."""

    provider: str = "llamacpp"  # llamacpp, openai, anthropic, gemini
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 30
    max_retries: int = 3


@dataclass
class ServiceConfig:
    """Service-specific configuration."""

    ai_orchestrator: Dict[str, Any] = field(default_factory=dict)
    memory_service: Dict[str, Any] = field(default_factory=dict)
    conversation_service: Dict[str, Any] = field(default_factory=dict)
    plugin_service: Dict[str, Any] = field(default_factory=dict)
    tool_service: Dict[str, Any] = field(default_factory=dict)
    analytics_service: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityConfig:
    """Security configuration."""

    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # seconds
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    enable_auth: bool = True
    enable_rate_limiting: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""

    enable_metrics: bool = True
    enable_tracing: bool = False
    enable_logging: bool = True
    log_level: str = "INFO"
    metrics_port: int = 8080
    health_check_interval: int = 30
    prometheus_enabled: bool = True


@dataclass
class WebUIConfig:
    """Web UI integration configuration."""

    enable_web_ui_features: bool = True
    session_timeout: int = 3600  # seconds
    max_conversation_history: int = 1000
    enable_proactive_suggestions: bool = True
    enable_memory_integration: bool = True
    ui_sources: List[str] = field(
        default_factory=lambda: ["web", "desktop", "api"]
    )


@dataclass
class AIKarenConfig:
    """Main AI Karen configuration."""

    environment: Environment = Environment.LOCAL
    debug: bool = False
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    vector_db: VectorDBConfig = field(default_factory=VectorDBConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    services: ServiceConfig = field(default_factory=ServiceConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    web_ui: WebUIConfig = field(default_factory=WebUIConfig)

    # NLP and Embedding Models
    default_embedding_model: str = (
        "sentence-transformers/distilbert-base-nli-stsb-mean-tokens"
    )
    spacy_model: str = "en_core_web_sm"

    # Legacy compatibility
    active_user: str = "default"
    theme: str = "dark"
    llm_model: str = "llama3.2:latest"
    memory: Dict[str, Any] = field(
        default_factory=lambda: {
            "enabled": True,
            "provider": "local",
            "embedding_dim": 768,
            "decay_lambda": 0.1,
            "query_limit": 100,
        }
    )
    event_bus: str = "memory"
    ui: Dict[str, Any] = field(default_factory=lambda: {"show_debug_info": False})

    # User profiles (routing/model selections) stored in config.json
    # Structure example:
    # {
    #   "profiles": [
    #       {
    #         "id": "default",
    #         "name": "Default",
    #         "assignments": {"chat": {"provider": "openai", "model": "gpt-4o-mini"}},
    #         "fallback_chain": ["openai", "deepseek", "llamacpp"],
    #         "is_active": true
    #       }
    #   ],
    #   "active_profile": "default"
    # }
    user_profiles: Dict[str, Any] = field(default_factory=dict)
    active_profile: Optional[str] = None


class ConfigManager:
    """
    Configuration manager for AI Karen engine integration.

    Handles loading, validation, and management of configuration from
    multiple sources including environment variables, config files,
    and runtime updates.
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = Path(config_path) if config_path else Path("config.json")
        self._config: Optional[AIKarenConfig] = None
        self._watchers: List[callable] = []

    def load_config(self) -> AIKarenConfig:
        """Load configuration from all sources."""
        if self._config is not None:
            return self._config

        # Start with default configuration
        config_dict = {}

        # Load from config file if it exists
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    file_config = json.load(f)
                config_dict.update(file_config)
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_path}: {e}")

        # Override with environment variables
        env_config = self._load_from_environment()
        config_dict = self._merge_configs(config_dict, env_config)

        # Create configuration object
        self._config = self._create_config_object(config_dict)

        # Validate configuration
        self._validate_config(self._config)

        logger.info(f"Configuration loaded for environment: {self._config.environment}")
        return self._config

    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}

        # Environment
        if env := os.getenv("KARI_ENV"):
            env_config["environment"] = env

        # Debug
        if debug := os.getenv("KARI_DEBUG"):
            env_config["debug"] = debug.lower() in ("true", "1", "yes")

        # Database
        db_config = {}
        if host := os.getenv("DB_HOST"):
            db_config["host"] = host
        if port := os.getenv("DB_PORT"):
            db_config["port"] = int(port)
        if database := os.getenv("DB_NAME"):
            db_config["database"] = database
        if username := os.getenv("DB_USER"):
            db_config["username"] = username
        if password := os.getenv("DB_PASSWORD"):
            db_config["password"] = password
        if db_config:
            env_config["database"] = db_config

        # Redis
        redis_config = {}
        if host := os.getenv("REDIS_HOST"):
            redis_config["host"] = host
        if port := os.getenv("REDIS_PORT"):
            redis_config["port"] = int(port)
        if password := os.getenv("REDIS_PASSWORD"):
            redis_config["password"] = password
        if redis_config:
            env_config["redis"] = redis_config

        # Vector DB
        vector_config = {}
        if provider := os.getenv("VECTOR_DB_PROVIDER"):
            vector_config["provider"] = provider
        if host := os.getenv("VECTOR_DB_HOST"):
            vector_config["host"] = host
        if port := os.getenv("VECTOR_DB_PORT"):
            vector_config["port"] = int(port)
        if vector_config:
            env_config["vector_db"] = vector_config

        # LLM
        llm_config = {}
        if provider := os.getenv("LLM_PROVIDER"):
            llm_config["provider"] = provider
        if model := os.getenv("LLM_MODEL"):
            llm_config["model"] = model
        if api_key := os.getenv("LLM_API_KEY"):
            llm_config["api_key"] = api_key
        if base_url := os.getenv("LLM_BASE_URL"):
            llm_config["base_url"] = base_url
        if llm_config:
            env_config["llm"] = llm_config

        # Security
        security_config = {}
        if secret := os.getenv("JWT_SECRET"):
            security_config["jwt_secret"] = secret
        if origins := os.getenv("CORS_ORIGINS"):
            security_config["cors_origins"] = origins.split(",")
        if security_config:
            env_config["security"] = security_config

        # NLP and Embedding Models
        if embedding_model := os.getenv("KARI_EMBED_MODEL"):
            env_config["default_embedding_model"] = embedding_model
        if spacy_model := os.getenv("KARI_SPACY_MODEL"):
            env_config["spacy_model"] = spacy_model

        return env_config

    def _merge_configs(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge configuration dictionaries recursively."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _create_config_object(self, config_dict: Dict[str, Any]) -> AIKarenConfig:
        """Create configuration object from dictionary."""
        # Handle nested configurations
        if "database" in config_dict:
            config_dict["database"] = DatabaseConfig(**config_dict["database"])

        if "redis" in config_dict:
            config_dict["redis"] = RedisConfig(**config_dict["redis"])

        if "vector_db" in config_dict:
            config_dict["vector_db"] = VectorDBConfig(**config_dict["vector_db"])

        if "llm" in config_dict:
            config_dict["llm"] = LLMConfig(**config_dict["llm"])

        if "services" in config_dict:
            config_dict["services"] = ServiceConfig(**config_dict["services"])

        if "security" in config_dict:
            config_dict["security"] = SecurityConfig(**config_dict["security"])

        if "monitoring" in config_dict:
            config_dict["monitoring"] = MonitoringConfig(**config_dict["monitoring"])

        if "web_ui" in config_dict:
            config_dict["web_ui"] = WebUIConfig(**config_dict["web_ui"])

        # Convert environment string to enum
        if "environment" in config_dict and isinstance(config_dict["environment"], str):
            config_dict["environment"] = Environment(config_dict["environment"])

        return AIKarenConfig(**config_dict)

    def _validate_config(self, config: AIKarenConfig) -> None:
        """Validate configuration."""
        # Validate required fields based on environment
        if config.environment == Environment.PRODUCTION:
            if (
                not config.security.jwt_secret
                or config.security.jwt_secret == "your-secret-key"
            ):
                raise ValueError("JWT secret must be set in production")

            if not config.llm.api_key and config.llm.provider in [
                "openai",
                "anthropic",
            ]:
                raise ValueError(
                    f"API key required for {config.llm.provider} in production"
                )

        # Validate database configuration
        if not config.database.host:
            raise ValueError("Database host is required")

        # Validate vector database configuration
        if config.vector_db.dimension <= 0:
            raise ValueError("Vector database dimension must be positive")

        logger.info("Configuration validation passed")

    def get_config(self) -> AIKarenConfig:
        """Get the current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config

    def reload_config(self) -> AIKarenConfig:
        """Reload configuration from sources."""
        self._config = None
        config = self.load_config()

        # Notify watchers
        for watcher in self._watchers:
            try:
                watcher(config)
            except Exception as e:
                logger.error(f"Configuration watcher error: {e}")

        return config

    def add_config_watcher(self, callback: callable) -> None:
        """Add a configuration change watcher."""
        self._watchers.append(callback)

    def remove_config_watcher(self, callback: callable) -> None:
        """Remove a configuration change watcher."""
        if callback in self._watchers:
            self._watchers.remove(callback)

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration at runtime."""
        if self._config is None:
            self.load_config()

        # Apply updates
        config_dict = self._config_to_dict(self._config)
        updated_dict = self._merge_configs(config_dict, updates)
        self._config = self._create_config_object(updated_dict)

        # Validate updated configuration
        self._validate_config(self._config)

        # Notify watchers
        for watcher in self._watchers:
            try:
                watcher(self._config)
            except Exception as e:
                logger.error(f"Configuration watcher error: {e}")

        logger.info("Configuration updated at runtime")

    def _config_to_dict(self, config: AIKarenConfig) -> Dict[str, Any]:
        """Convert configuration object to dictionary."""
        # This is a simplified implementation
        # In practice, you might want to use a more sophisticated serialization
        result = {}
        for field_name in config.__dataclass_fields__:
            value = getattr(config, field_name)
            if hasattr(value, "__dataclass_fields__"):
                result[field_name] = self._config_to_dict(value)
            else:
                result[field_name] = value
        return result

    def save_config(self, path: Optional[Union[str, Path]] = None) -> None:
        """Save current configuration to file."""
        if self._config is None:
            raise ValueError("No configuration loaded")

        save_path = Path(path) if path else self.config_path
        config_dict = self._config_to_dict(self._config)

        try:
            with open(save_path, "w") as f:
                json.dump(config_dict, f, indent=2, default=str)
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    def save_llm_settings(
        self, settings: Any, path: Optional[Union[str, Path]] = None
    ) -> None:
        """Persist LLM settings to a dedicated configuration file."""
        save_path = Path(path) if path else Path("config/llm_settings.json")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        data = settings.dict() if hasattr(settings, "dict") else settings
        try:
            with open(save_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"LLM settings saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save LLM settings: {e}")
            raise


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AIKarenConfig:
    """Get the current configuration."""
    return get_config_manager().get_config()


def reload_config() -> AIKarenConfig:
    """Reload configuration from sources."""
    return get_config_manager().reload_config()
