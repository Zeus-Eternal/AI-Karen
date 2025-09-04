"""
LLM Provider Configuration Management

This module provides comprehensive configuration management for LLM providers with:
- Per-provider settings (API keys, models, endpoints)
- Environment variable support for all provider settings
- Configuration validation and error handling
- Runtime provider switching capabilities
- Secure API key management
"""

import os
import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, Callable
from datetime import datetime

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """LLM provider types"""
    LOCAL = "local"
    REMOTE = "remote"
    HYBRID = "hybrid"


class AuthenticationType(str, Enum):
    """Authentication types for providers"""
    NONE = "none"
    API_KEY = "api_key"
    OAUTH = "oauth"
    CUSTOM = "custom"


@dataclass
class ProviderEndpoint:
    """Provider endpoint configuration"""
    base_url: str
    chat_endpoint: str = "/chat/completions"
    models_endpoint: str = "/models"
    embeddings_endpoint: str = "/embeddings"
    health_endpoint: str = "/health"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class ProviderAuthentication:
    """Provider authentication configuration"""
    type: AuthenticationType = AuthenticationType.NONE
    api_key_env_var: Optional[str] = None
    api_key_header: str = "Authorization"
    api_key_prefix: str = "Bearer"
    custom_headers: Dict[str, str] = field(default_factory=dict)
    validation_endpoint: Optional[str] = None
    validation_timeout: int = 10


@dataclass
class ProviderModel:
    """Individual model configuration"""
    id: str
    name: str
    family: str = "unknown"
    capabilities: Set[str] = field(default_factory=set)
    context_length: int = 4096
    max_tokens: int = 2048
    temperature_range: tuple = (0.0, 2.0)
    supports_streaming: bool = True
    supports_functions: bool = False
    supports_vision: bool = False
    cost_per_1k_tokens: Optional[float] = None
    parameters: Optional[str] = None
    quantization: Optional[str] = None
    local_path: Optional[str] = None


@dataclass
class ProviderLimits:
    """Provider rate limits and quotas"""
    requests_per_minute: Optional[int] = None
    tokens_per_minute: Optional[int] = None
    concurrent_requests: int = 5
    max_context_length: int = 32768
    max_output_tokens: int = 4096
    daily_quota: Optional[int] = None
    monthly_quota: Optional[int] = None


@dataclass
class ProviderConfig:
    """Complete provider configuration"""
    
    # Basic information
    name: str
    display_name: str
    description: str = ""
    provider_type: ProviderType = ProviderType.REMOTE
    enabled: bool = True
    priority: int = 50
    
    # Connection and authentication
    endpoint: Optional[ProviderEndpoint] = None
    authentication: ProviderAuthentication = field(default_factory=ProviderAuthentication)
    
    # Models and capabilities
    models: List[ProviderModel] = field(default_factory=list)
    default_model: Optional[str] = None
    capabilities: Set[str] = field(default_factory=set)
    
    # Limits and quotas
    limits: ProviderLimits = field(default_factory=ProviderLimits)
    
    # Configuration metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    
    # Validation status
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        
        # Convert enums to strings
        data["provider_type"] = self.provider_type.value
        data["authentication"]["type"] = self.authentication.type.value
        
        # Convert sets to lists
        data["capabilities"] = list(self.capabilities)
        for model in data["models"]:
            model["capabilities"] = list(model["capabilities"])
        
        # Convert datetime objects
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.last_health_check:
            data["last_health_check"] = self.last_health_check.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProviderConfig':
        """Create from dictionary"""
        # Convert string enums back to enum objects
        if "provider_type" in data:
            data["provider_type"] = ProviderType(data["provider_type"])
        
        if "authentication" in data and "type" in data["authentication"]:
            data["authentication"]["type"] = AuthenticationType(data["authentication"]["type"])
        
        # Convert lists back to sets
        if "capabilities" in data:
            data["capabilities"] = set(data["capabilities"])
        
        if "models" in data:
            for model in data["models"]:
                if "capabilities" in model:
                    model["capabilities"] = set(model["capabilities"])
        
        # Convert datetime strings
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if "last_health_check" in data and isinstance(data["last_health_check"], str):
            data["last_health_check"] = datetime.fromisoformat(data["last_health_check"])
        
        # Create nested objects
        if "endpoint" in data and data["endpoint"]:
            data["endpoint"] = ProviderEndpoint(**data["endpoint"])
        
        if "authentication" in data:
            data["authentication"] = ProviderAuthentication(**data["authentication"])
        
        if "limits" in data:
            data["limits"] = ProviderLimits(**data["limits"])
        
        if "models" in data:
            models = []
            for model_data in data["models"]:
                models.append(ProviderModel(**model_data))
            data["models"] = models
        
        return cls(**data)


class LLMProviderConfigManager:
    """
    Manager for LLM provider configurations with comprehensive features:
    - Per-provider settings management
    - Environment variable support
    - Configuration validation
    - Runtime provider switching
    - Secure API key management
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".kari" / "providers"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._providers: Dict[str, ProviderConfig] = {}
        self._config_lock = threading.RLock()
        self._change_listeners: List[Callable[[str, ProviderConfig], None]] = []
        
        # Load existing configurations
        self._load_configurations()
        
        # Create default configurations if none exist
        if not self._providers:
            self._create_default_configurations()
    
    # ---------- Configuration Management ----------
    
    def add_provider(self, config: ProviderConfig) -> None:
        """Add a new provider configuration"""
        with self._config_lock:
            # Validate configuration
            self._validate_provider_config(config)
            
            # Apply environment variable overrides
            self._apply_env_overrides(config)
            
            # Store configuration
            self._providers[config.name] = config
            
            # Save to disk
            self._save_provider_config(config)
            
            # Notify listeners
            self._notify_change_listeners(config.name, config)
            
            logger.info(f"Added LLM provider configuration: {config.name}")
    
    def update_provider(self, name: str, updates: Dict[str, Any]) -> ProviderConfig:
        """Update an existing provider configuration"""
        with self._config_lock:
            if name not in self._providers:
                raise ValueError(f"Provider {name} not found")
            
            config = self._providers[name]
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            config.updated_at = datetime.now()
            
            # Re-validate configuration
            self._validate_provider_config(config)
            
            # Apply environment variable overrides
            self._apply_env_overrides(config)
            
            # Save to disk
            self._save_provider_config(config)
            
            # Notify listeners
            self._notify_change_listeners(name, config)
            
            logger.info(f"Updated LLM provider configuration: {name}")
            return config
    
    def remove_provider(self, name: str) -> bool:
        """Remove a provider configuration"""
        with self._config_lock:
            if name not in self._providers:
                return False
            
            config = self._providers[name]
            
            # Remove from memory
            del self._providers[name]
            
            # Remove from disk
            config_file = self.config_dir / f"{name}.json"
            if config_file.exists():
                config_file.unlink()
            
            logger.info(f"Removed LLM provider configuration: {name}")
            return True
    
    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Get a provider configuration"""
        return self._providers.get(name)
    
    def list_providers(self, enabled_only: bool = False) -> List[ProviderConfig]:
        """List all provider configurations"""
        providers = list(self._providers.values())
        if enabled_only:
            providers = [p for p in providers if p.enabled]
        return sorted(providers, key=lambda p: p.priority, reverse=True)
    
    def get_provider_names(self, enabled_only: bool = False) -> List[str]:
        """Get list of provider names"""
        providers = self.list_providers(enabled_only)
        return [p.name for p in providers]
    
    # ---------- Environment Variable Support ----------
    
    def _apply_env_overrides(self, config: ProviderConfig) -> None:
        """Apply environment variable overrides to configuration"""
        
        # API key override
        if config.authentication.api_key_env_var:
            api_key = os.getenv(config.authentication.api_key_env_var)
            if api_key:
                # Store API key securely (not in the config object)
                self._store_api_key(config.name, api_key)
        
        # Provider-specific environment variables
        env_prefix = f"KARI_{config.name.upper()}"
        
        # Endpoint overrides
        if config.endpoint:
            base_url = os.getenv(f"{env_prefix}_BASE_URL")
            if base_url:
                config.endpoint.base_url = base_url
            
            timeout = os.getenv(f"{env_prefix}_TIMEOUT")
            if timeout:
                try:
                    config.endpoint.timeout = int(timeout)
                except ValueError:
                    logger.warning(f"Invalid timeout value for {config.name}: {timeout}")
        
        # Enable/disable override
        enabled = os.getenv(f"{env_prefix}_ENABLED")
        if enabled is not None:
            config.enabled = enabled.lower() in ("true", "1", "yes", "on")
        
        # Priority override
        priority = os.getenv(f"{env_prefix}_PRIORITY")
        if priority:
            try:
                config.priority = int(priority)
            except ValueError:
                logger.warning(f"Invalid priority value for {config.name}: {priority}")
        
        # Default model override
        default_model = os.getenv(f"{env_prefix}_DEFAULT_MODEL")
        if default_model:
            config.default_model = default_model
    
    def _store_api_key(self, provider_name: str, api_key: str) -> None:
        """Store API key securely (placeholder for secure storage)"""
        # In a production system, this would use a secure key store
        # For now, we'll store in memory with basic obfuscation
        if not hasattr(self, '_api_keys'):
            self._api_keys = {}
        self._api_keys[provider_name] = api_key
    
    def get_api_key(self, provider_name: str) -> Optional[str]:
        """Get API key for a provider"""
        if hasattr(self, '_api_keys'):
            return self._api_keys.get(provider_name)
        
        # Fallback to environment variable
        config = self.get_provider(provider_name)
        if config and config.authentication.api_key_env_var:
            return os.getenv(config.authentication.api_key_env_var)
        
        return None
    
    # ---------- Configuration Validation ----------
    
    def _validate_provider_config(self, config: ProviderConfig) -> None:
        """Validate a provider configuration"""
        errors = []
        
        # Basic validation
        if not config.name:
            errors.append("Provider name is required")
        
        if not config.display_name:
            errors.append("Provider display name is required")
        
        # Endpoint validation for remote providers
        if config.provider_type in [ProviderType.REMOTE, ProviderType.HYBRID]:
            if not config.endpoint:
                errors.append("Endpoint configuration is required for remote providers")
            elif not config.endpoint.base_url:
                errors.append("Base URL is required for remote providers")
        
        # Authentication validation
        if config.authentication.type == AuthenticationType.API_KEY:
            if not config.authentication.api_key_env_var:
                errors.append("API key environment variable is required for API key authentication")
        
        # Model validation
        if config.models:
            model_ids = [m.id for m in config.models]
            if len(model_ids) != len(set(model_ids)):
                errors.append("Duplicate model IDs found")
            
            if config.default_model and config.default_model not in model_ids:
                errors.append(f"Default model '{config.default_model}' not found in model list")
        
        # Update validation status
        config.is_valid = len(errors) == 0
        config.validation_errors = errors
        
        if errors:
            logger.warning(f"Provider {config.name} has validation errors: {errors}")
    
    def validate_all_providers(self) -> Dict[str, List[str]]:
        """Validate all provider configurations"""
        validation_results = {}
        
        for name, config in self._providers.items():
            self._validate_provider_config(config)
            if config.validation_errors:
                validation_results[name] = config.validation_errors
        
        return validation_results
    
    # ---------- Runtime Provider Switching ----------
    
    def enable_provider(self, name: str) -> bool:
        """Enable a provider at runtime"""
        return self.update_provider(name, {"enabled": True}) is not None
    
    def disable_provider(self, name: str) -> bool:
        """Disable a provider at runtime"""
        return self.update_provider(name, {"enabled": False}) is not None
    
    def set_provider_priority(self, name: str, priority: int) -> bool:
        """Set provider priority at runtime"""
        return self.update_provider(name, {"priority": priority}) is not None
    
    def reload_provider_config(self, name: str) -> bool:
        """Reload a provider configuration from disk"""
        with self._config_lock:
            config_file = self.config_dir / f"{name}.json"
            if not config_file.exists():
                return False
            
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                
                config = ProviderConfig.from_dict(data)
                
                # Validate and apply environment overrides
                self._validate_provider_config(config)
                self._apply_env_overrides(config)
                
                # Update in memory
                self._providers[name] = config
                
                # Notify listeners
                self._notify_change_listeners(name, config)
                
                logger.info(f"Reloaded provider configuration: {name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to reload provider config {name}: {e}")
                return False
    
    def reload_all_configs(self) -> int:
        """Reload all provider configurations from disk"""
        reloaded_count = 0
        
        for config_file in self.config_dir.glob("*.json"):
            provider_name = config_file.stem
            if self.reload_provider_config(provider_name):
                reloaded_count += 1
        
        logger.info(f"Reloaded {reloaded_count} provider configurations")
        return reloaded_count
    
    # ---------- Change Listeners ----------
    
    def add_change_listener(self, listener: Callable[[str, ProviderConfig], None]) -> None:
        """Add a configuration change listener"""
        self._change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[str, ProviderConfig], None]) -> None:
        """Remove a configuration change listener"""
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)
    
    def _notify_change_listeners(self, provider_name: str, config: ProviderConfig) -> None:
        """Notify all change listeners"""
        for listener in self._change_listeners:
            try:
                listener(provider_name, config)
            except Exception as e:
                logger.warning(f"Configuration change listener failed: {e}")
    
    # ---------- Persistence ----------
    
    def _load_configurations(self) -> None:
        """Load all provider configurations from disk"""
        if not self.config_dir.exists():
            return
        
        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                
                config = ProviderConfig.from_dict(data)
                
                # Validate and apply environment overrides
                self._validate_provider_config(config)
                self._apply_env_overrides(config)
                
                self._providers[config.name] = config
                
            except Exception as e:
                logger.warning(f"Failed to load provider config from {config_file}: {e}")
        
        logger.info(f"Loaded {len(self._providers)} provider configurations")
    
    def _save_provider_config(self, config: ProviderConfig) -> None:
        """Save a provider configuration to disk"""
        config_file = self.config_dir / f"{config.name}.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save provider config {config.name}: {e}")
    
    def save_all_configs(self) -> int:
        """Save all provider configurations to disk"""
        saved_count = 0
        
        for config in self._providers.values():
            try:
                self._save_provider_config(config)
                saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save config for {config.name}: {e}")
        
        logger.info(f"Saved {saved_count} provider configurations")
        return saved_count 
   
    # ---------- Default Configurations ----------
    
    def _create_default_configurations(self) -> None:
        """Create default provider configurations"""
        
        # OpenAI Provider
        openai_config = ProviderConfig(
            name="openai",
            display_name="OpenAI",
            description="OpenAI GPT models via API",
            provider_type=ProviderType.REMOTE,
            priority=80,
            endpoint=ProviderEndpoint(
                base_url="https://api.openai.com/v1",
                chat_endpoint="/chat/completions",
                models_endpoint="/models",
                embeddings_endpoint="/embeddings"
            ),
            authentication=ProviderAuthentication(
                type=AuthenticationType.API_KEY,
                api_key_env_var="OPENAI_API_KEY",
                api_key_header="Authorization",
                api_key_prefix="Bearer",
                validation_endpoint="/models"
            ),
            models=[
                ProviderModel(
                    id="gpt-4o",
                    name="GPT-4o",
                    family="gpt",
                    capabilities={"text", "vision", "function_calling"},
                    context_length=128000,
                    max_tokens=4096,
                    supports_streaming=True,
                    supports_functions=True,
                    supports_vision=True,
                    cost_per_1k_tokens=0.03
                ),
                ProviderModel(
                    id="gpt-4o-mini",
                    name="GPT-4o Mini",
                    family="gpt",
                    capabilities={"text", "function_calling"},
                    context_length=128000,
                    max_tokens=16384,
                    supports_streaming=True,
                    supports_functions=True,
                    cost_per_1k_tokens=0.0015
                ),
                ProviderModel(
                    id="gpt-3.5-turbo",
                    name="GPT-3.5 Turbo",
                    family="gpt",
                    capabilities={"text", "function_calling"},
                    context_length=16385,
                    max_tokens=4096,
                    supports_streaming=True,
                    supports_functions=True,
                    cost_per_1k_tokens=0.001
                )
            ],
            default_model="gpt-4o-mini",
            capabilities={"streaming", "embeddings", "function_calling", "vision"},
            limits=ProviderLimits(
                requests_per_minute=3500,
                tokens_per_minute=90000,
                concurrent_requests=10,
                max_context_length=128000,
                max_output_tokens=16384
            )
        )
        self.add_provider(openai_config)
        
        # Gemini Provider
        gemini_config = ProviderConfig(
            name="gemini",
            display_name="Google Gemini",
            description="Google Gemini models via API",
            provider_type=ProviderType.REMOTE,
            priority=75,
            endpoint=ProviderEndpoint(
                base_url="https://generativelanguage.googleapis.com/v1beta",
                chat_endpoint="/models/{model}:generateContent",
                models_endpoint="/models"
            ),
            authentication=ProviderAuthentication(
                type=AuthenticationType.API_KEY,
                api_key_env_var="GEMINI_API_KEY",
                validation_endpoint="/models"
            ),
            models=[
                ProviderModel(
                    id="gemini-1.5-pro",
                    name="Gemini 1.5 Pro",
                    family="gemini",
                    capabilities={"text", "vision", "code"},
                    context_length=2097152,
                    max_tokens=8192,
                    supports_streaming=True,
                    supports_vision=True,
                    cost_per_1k_tokens=0.0035
                ),
                ProviderModel(
                    id="gemini-1.5-flash",
                    name="Gemini 1.5 Flash",
                    family="gemini",
                    capabilities={"text", "vision", "code"},
                    context_length=1048576,
                    max_tokens=8192,
                    supports_streaming=True,
                    supports_vision=True,
                    cost_per_1k_tokens=0.00075
                )
            ],
            default_model="gemini-1.5-flash",
            capabilities={"streaming", "vision", "code"},
            limits=ProviderLimits(
                requests_per_minute=1500,
                concurrent_requests=5,
                max_context_length=2097152,
                max_output_tokens=8192
            )
        )
        self.add_provider(gemini_config)
        
        # DeepSeek Provider
        deepseek_config = ProviderConfig(
            name="deepseek",
            display_name="DeepSeek",
            description="DeepSeek models optimized for coding and reasoning",
            provider_type=ProviderType.REMOTE,
            priority=70,
            endpoint=ProviderEndpoint(
                base_url="https://api.deepseek.com",
                chat_endpoint="/chat/completions",
                models_endpoint="/models"
            ),
            authentication=ProviderAuthentication(
                type=AuthenticationType.API_KEY,
                api_key_env_var="DEEPSEEK_API_KEY",
                api_key_header="Authorization",
                api_key_prefix="Bearer",
                validation_endpoint="/models"
            ),
            models=[
                ProviderModel(
                    id="deepseek-chat",
                    name="DeepSeek Chat",
                    family="deepseek",
                    capabilities={"text", "reasoning"},
                    context_length=32768,
                    max_tokens=4096,
                    supports_streaming=True,
                    cost_per_1k_tokens=0.0014
                ),
                ProviderModel(
                    id="deepseek-coder",
                    name="DeepSeek Coder",
                    family="deepseek",
                    capabilities={"code", "text"},
                    context_length=16384,
                    max_tokens=4096,
                    supports_streaming=True,
                    cost_per_1k_tokens=0.0014
                )
            ],
            default_model="deepseek-chat",
            capabilities={"streaming", "code", "reasoning"},
            limits=ProviderLimits(
                requests_per_minute=1000,
                concurrent_requests=5,
                max_context_length=32768,
                max_output_tokens=4096
            )
        )
        self.add_provider(deepseek_config)
        
        # HuggingFace Provider
        huggingface_config = ProviderConfig(
            name="huggingface",
            display_name="HuggingFace",
            description="HuggingFace Hub models and local execution",
            provider_type=ProviderType.HYBRID,
            priority=65,
            endpoint=ProviderEndpoint(
                base_url="https://api-inference.huggingface.co",
                chat_endpoint="/models/{model}",
                models_endpoint="/api/models"
            ),
            authentication=ProviderAuthentication(
                type=AuthenticationType.API_KEY,
                api_key_env_var="HUGGINGFACE_API_KEY",
                api_key_header="Authorization",
                api_key_prefix="Bearer",
                validation_endpoint="/api/whoami"
            ),
            models=[
                ProviderModel(
                    id="microsoft/DialoGPT-large",
                    name="DialoGPT Large",
                    family="gpt",
                    capabilities={"text", "conversation"},
                    context_length=1024,
                    max_tokens=1024,
                    parameters="345M"
                ),
                ProviderModel(
                    id="microsoft/DialoGPT-medium",
                    name="DialoGPT Medium",
                    family="gpt",
                    capabilities={"text", "conversation"},
                    context_length=1024,
                    max_tokens=1024,
                    parameters="117M"
                )
            ],
            default_model="microsoft/DialoGPT-large",
            capabilities={"local_execution", "model_download", "embeddings"},
            limits=ProviderLimits(
                requests_per_minute=1000,
                concurrent_requests=3,
                max_context_length=4096,
                max_output_tokens=2048
            )
        )
        self.add_provider(huggingface_config)
        
        # Note: Ollama provider removed; use llama.cpp local provider instead.
        
        logger.info("Created default LLM provider configurations")
    
    # ---------- Utility Methods ----------
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of all provider configurations"""
        summary = {
            "total_providers": len(self._providers),
            "enabled_providers": len([p for p in self._providers.values() if p.enabled]),
            "provider_types": {},
            "authentication_types": {},
            "validation_status": {"valid": 0, "invalid": 0},
            "providers": []
        }
        
        for config in self._providers.values():
            # Count by provider type
            provider_type = config.provider_type.value
            summary["provider_types"][provider_type] = summary["provider_types"].get(provider_type, 0) + 1
            
            # Count by authentication type
            auth_type = config.authentication.type.value
            summary["authentication_types"][auth_type] = summary["authentication_types"].get(auth_type, 0) + 1
            
            # Count validation status
            if config.is_valid:
                summary["validation_status"]["valid"] += 1
            else:
                summary["validation_status"]["invalid"] += 1
            
            # Add provider summary
            summary["providers"].append({
                "name": config.name,
                "display_name": config.display_name,
                "type": config.provider_type.value,
                "enabled": config.enabled,
                "priority": config.priority,
                "model_count": len(config.models),
                "default_model": config.default_model,
                "is_valid": config.is_valid,
                "health_status": config.health_status
            })
        
        return summary
    
    def export_configurations(self, file_path: Path) -> bool:
        """Export all configurations to a file"""
        try:
            export_data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "providers": {name: config.to_dict() for name, config in self._providers.items()}
            }
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported {len(self._providers)} provider configurations to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configurations: {e}")
            return False
    
    def import_configurations(self, file_path: Path, overwrite: bool = False) -> int:
        """Import configurations from a file"""
        try:
            with open(file_path, 'r') as f:
                import_data = json.load(f)
            
            imported_count = 0
            providers_data = import_data.get("providers", {})
            
            for name, config_data in providers_data.items():
                if name in self._providers and not overwrite:
                    logger.warning(f"Provider {name} already exists, skipping (use overwrite=True to replace)")
                    continue
                
                try:
                    config = ProviderConfig.from_dict(config_data)
                    self.add_provider(config)
                    imported_count += 1
                except Exception as e:
                    logger.error(f"Failed to import provider {name}: {e}")
            
            logger.info(f"Imported {imported_count} provider configurations from {file_path}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import configurations: {e}")
            return 0


# Global instance
_provider_config_manager: Optional[LLMProviderConfigManager] = None


def get_provider_config_manager() -> LLMProviderConfigManager:
    """Get the global provider configuration manager instance"""
    global _provider_config_manager
    if _provider_config_manager is None:
        _provider_config_manager = LLMProviderConfigManager()
    return _provider_config_manager


def reset_provider_config_manager() -> None:
    """Reset the global provider configuration manager (for testing)"""
    global _provider_config_manager
    _provider_config_manager = None
