"""
LLM Provider Registry

Manages registration, discovery, and health monitoring of LLM providers.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .llm_utils import LLMProviderBase
from .providers import (DeepseekProvider, GeminiProvider, HuggingFaceProvider,
                        OllamaProvider, OpenAIProvider)

logger = logging.getLogger("kari.llm_registry")


@dataclass
class ProviderRegistration:
    """Provider registration information."""

    name: str
    provider_class: str
    description: str
    supports_streaming: bool = False
    supports_embeddings: bool = False
    requires_api_key: bool = False
    default_model: str = ""
    health_status: str = "unknown"  # unknown, healthy, unhealthy
    last_health_check: Optional[float] = None
    error_message: Optional[str] = None


class LLMRegistry:
    """Registry for managing LLM providers."""

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize LLM registry.

        Args:
            registry_path: Path to registry JSON file (defaults to models/llm_registry.json)
        """
        self.registry_path = registry_path or Path("models/llm_registry.json")
        self._providers: Dict[str, LLMProviderBase] = {}
        self._registrations: Dict[str, ProviderRegistration] = {}

        # Register built-in providers
        self._register_builtin_providers()

        # Load existing registry
        self._load_registry()

    def _register_builtin_providers(self):
        """Register all built-in LLM providers."""
        builtin_providers = [
            {
                "name": "ollama",
                "provider_class": "OllamaProvider",
                "description": "Local Ollama server for running open-source models",
                "supports_streaming": True,
                "supports_embeddings": True,
                "requires_api_key": False,
                "default_model": "llama3.2:latest",
            },
            {
                "name": "openai",
                "provider_class": "OpenAIProvider",
                "description": "OpenAI GPT models via API",
                "supports_streaming": True,
                "supports_embeddings": True,
                "requires_api_key": True,
                "default_model": "gpt-3.5-turbo",
            },
            {
                "name": "gemini",
                "provider_class": "GeminiProvider",
                "description": "Google Gemini models via API",
                "supports_streaming": True,
                "supports_embeddings": True,
                "requires_api_key": True,
                "default_model": "gemini-1.5-flash",
            },
            {
                "name": "deepseek",
                "provider_class": "DeepseekProvider",
                "description": "Deepseek models optimized for coding and reasoning",
                "supports_streaming": True,
                "supports_embeddings": False,
                "requires_api_key": True,
                "default_model": "deepseek-chat",
            },
            {
                "name": "huggingface",
                "provider_class": "HuggingFaceProvider",
                "description": "HuggingFace models via Inference API or local execution",
                "supports_streaming": False,
                "supports_embeddings": True,
                "requires_api_key": True,
                "default_model": "microsoft/DialoGPT-large",
            },
        ]

        for provider_info in builtin_providers:
            registration = ProviderRegistration(**provider_info)
            self._registrations[provider_info["name"]] = registration

    def _load_registry(self):
        """Load registry from JSON file."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r") as f:
                    data = json.load(f)

                # Load custom registrations (if any)
                for item in data:
                    if isinstance(item, dict) and "name" in item:
                        # Update existing registration or create new one
                        name = item["name"]
                        if name in self._registrations:
                            # Update existing registration with saved data
                            registration = self._registrations[name]
                            registration.health_status = item.get(
                                "health_status", "unknown"
                            )
                            registration.last_health_check = item.get(
                                "last_health_check"
                            )
                            registration.error_message = item.get("error_message")
                        else:
                            # Create new registration from saved data
                            self._registrations[name] = ProviderRegistration(**item)

                logger.info(f"Loaded registry from {self.registry_path}")

            except Exception as ex:
                logger.warning(
                    f"Could not load registry from {self.registry_path}: {ex}"
                )

    def _save_registry(self):
        """Save registry to JSON file."""
        try:
            # Ensure directory exists
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert registrations to list of dicts
            data = [asdict(reg) for reg in self._registrations.values()]

            with open(self.registry_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved registry to {self.registry_path}")

        except Exception as ex:
            logger.error(f"Could not save registry to {self.registry_path}: {ex}")

    def register_provider(
        self,
        name: str,
        provider_class: Type[LLMProviderBase],
        description: str = "",
        **kwargs,
    ):
        """
        Register a custom LLM provider.

        Args:
            name: Provider name
            provider_class: Provider class
            description: Provider description
            **kwargs: Additional registration parameters
        """
        registration = ProviderRegistration(
            name=name,
            provider_class=provider_class.__name__,
            description=description,
            **kwargs,
        )

        self._registrations[name] = registration
        logger.info(f"Registered provider: {name}")

        # Save updated registry
        self._save_registry()

    def get_provider(self, name: str, **init_kwargs) -> Optional[LLMProviderBase]:
        """
        Get provider instance by name.

        Args:
            name: Provider name
            **init_kwargs: Provider initialization arguments

        Returns:
            Provider instance or None if not found
        """
        if name not in self._registrations:
            logger.error(f"Provider '{name}' not registered")
            return None

        # Return cached instance if available
        if name in self._providers:
            return self._providers[name]

        # Create new instance
        try:
            registration = self._registrations[name]
            provider_class = self._get_provider_class(registration.provider_class)

            if provider_class:
                # Use default model if not specified
                if "model" not in init_kwargs and registration.default_model:
                    init_kwargs["model"] = registration.default_model

                provider = provider_class(**init_kwargs)
                self._providers[name] = provider

                logger.info(f"Created provider instance: {name}")
                return provider

        except Exception as ex:
            logger.error(f"Failed to create provider '{name}': {ex}")

        return None

    def _get_provider_class(self, class_name: str) -> Optional[Type[LLMProviderBase]]:
        """Get provider class by name."""
        class_map = {
            "OllamaProvider": OllamaProvider,
            "OpenAIProvider": OpenAIProvider,
            "GeminiProvider": GeminiProvider,
            "DeepseekProvider": DeepseekProvider,
            "HuggingFaceProvider": HuggingFaceProvider,
        }

        return class_map.get(class_name)

    def list_providers(self) -> List[str]:
        """Get list of registered provider names."""
        return list(self._registrations.keys())

    def get_provider_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get provider registration information."""
        if name not in self._registrations:
            return None

        registration = self._registrations[name]
        info = asdict(registration)

        # Add runtime info if provider is instantiated
        if name in self._providers:
            try:
                provider_info = self._providers[name].get_provider_info()
                info.update(provider_info)
            except Exception as ex:
                logger.warning(f"Could not get provider info for {name}: {ex}")

        return info

    def health_check(self, name: str) -> Dict[str, Any]:
        """Perform health check on a provider."""
        if name not in self._registrations:
            return {
                "status": "not_registered",
                "error": f"Provider '{name}' not registered",
            }

        try:
            provider = self.get_provider(name)
            if not provider:
                return {
                    "status": "failed_to_create",
                    "error": "Could not create provider instance",
                }

            # Perform health check if provider supports it
            if hasattr(provider, "health_check"):
                result = provider.health_check()
            else:
                # Basic health check - try to get provider info
                provider.get_provider_info()
                result = {"status": "healthy", "message": "Basic health check passed"}

            # Update registration
            registration = self._registrations[name]
            registration.health_status = result.get("status", "unknown")
            registration.last_health_check = time.time()
            registration.error_message = result.get("error")

            # Save updated registry
            self._save_registry()

            return result

        except Exception as ex:
            # Update registration with error
            registration = self._registrations[name]
            registration.health_status = "unhealthy"
            registration.last_health_check = time.time()
            registration.error_message = str(ex)

            # Save updated registry
            self._save_registry()

            return {"status": "unhealthy", "error": str(ex)}

    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all registered providers."""
        results = {}

        for name in self._registrations.keys():
            results[name] = self.health_check(name)

        return results

    def get_available_providers(self) -> List[str]:
        """Get list of providers that are currently healthy or unknown status."""
        available = []

        for name, registration in self._registrations.items():
            if registration.health_status in ["healthy", "unknown"]:
                available.append(name)

        return available

    def auto_select_provider(
        self, requirements: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Automatically select the best available provider based on requirements.

        Args:
            requirements: Dict with keys like 'streaming', 'embeddings', 'api_key_available'

        Returns:
            Provider name or None if no suitable provider found
        """
        requirements = requirements or {}

        # Get available providers
        available = self.get_available_providers()

        # Filter by requirements
        suitable = []
        for name in available:
            registration = self._registrations[name]

            # Check streaming requirement
            if requirements.get("streaming") and not registration.supports_streaming:
                continue

            # Check embeddings requirement
            if requirements.get("embeddings") and not registration.supports_embeddings:
                continue

            # Check API key requirement
            if registration.requires_api_key and not requirements.get(
                "api_key_available", True
            ):
                continue

            suitable.append(name)

        # Return first suitable provider (could be enhanced with priority logic)
        return suitable[0] if suitable else None


# Global registry instance
_registry = None


def get_registry() -> LLMRegistry:
    """Get global LLM registry instance."""
    global _registry
    if _registry is None:
        _registry = LLMRegistry()
    return _registry


def register_provider(name: str, provider_class: Type[LLMProviderBase], **kwargs):
    """Register a provider in the global registry."""
    registry = get_registry()
    registry.register_provider(name, provider_class, **kwargs)


def get_provider(name: str, **init_kwargs) -> Optional[LLMProviderBase]:
    """Get provider from global registry."""
    registry = get_registry()
    return registry.get_provider(name, **init_kwargs)


def list_providers() -> List[str]:
    """List all registered providers."""
    registry = get_registry()
    return registry.list_providers()


def health_check_all() -> Dict[str, Dict[str, Any]]:
    """Health check all providers."""
    registry = get_registry()
    return registry.health_check_all()


# Expose a module-level registry instance for plugin consumers
registry = get_registry()

__all__ = [
    "LLMRegistry",
    "get_registry",
    "register_provider",
    "get_provider",
    "list_providers",
    "health_check_all",
    "registry",
]
