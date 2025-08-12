"""Generic provider registry for hierarchical extension management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type


@dataclass
class ModelInfo:
    """Information about a specific model or service offered by a provider."""

    name: str
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    default_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderRegistration:
    """Registration record for a provider."""

    name: str
    provider_class: Type[Any]
    description: str = ""
    models: List[ModelInfo] = field(default_factory=list)
    requires_api_key: bool = False
    default_model: Optional[str] = None


class ProviderRegistry:
    """Simple registry for extension providers."""

    def __init__(self) -> None:
        self._registrations: Dict[str, ProviderRegistration] = {}
        self._instances: Dict[str, Any] = {}

    def register_default_providers(self) -> None:
        """Register built-in providers."""
        from ai_karen_engine.integrations.providers.copilotkit_provider import (
            CopilotKitProvider,
        )

        self.register_provider(
            "copilotkit",
            CopilotKitProvider,
            description="CopilotKit AI-powered code assistance and contextual suggestions",
            models=[ModelInfo(name="gpt-4", description="Default CopilotKit model")],
            requires_api_key=True,
            default_model="gpt-4",
        )

    def register_provider(
        self,
        name: str,
        provider_class: Type[Any],
        *,
        description: str = "",
        models: Optional[List[ModelInfo]] = None,
        requires_api_key: bool = False,
        default_model: Optional[str] = None,
    ) -> None:
        """Register a provider with optional models."""
        self._registrations[name] = ProviderRegistration(
            name=name,
            provider_class=provider_class,
            description=description,
            models=models or [],
            requires_api_key=requires_api_key,
            default_model=default_model,
        )

    def get_provider(self, name: str, **init_kwargs: Any) -> Optional[Any]:
        """Get or create an instance of a provider."""
        reg = self._registrations.get(name)
        if not reg:
            return None
        if name not in self._instances:
            if reg.default_model and "model" not in init_kwargs:
                init_kwargs["model"] = reg.default_model
            self._instances[name] = reg.provider_class(**init_kwargs)
        return self._instances[name]

    def list_providers(self) -> List[str]:
        """Return the list of registered provider names."""
        return list(self._registrations.keys())

    def list_models(self, provider_name: str) -> List[str]:
        """List available models for a provider."""
        reg = self._registrations.get(provider_name)
        if not reg:
            return []
        return [m.name for m in reg.models]


# Global registry instance
_provider_registry: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    """Get or create the global provider registry."""
    global _provider_registry
    if _provider_registry is None:
        _provider_registry = ProviderRegistry()
        _provider_registry.register_default_providers()
    return _provider_registry


__all__ = [
    "ModelInfo",
    "ProviderRegistration",
    "ProviderRegistry",
    "get_provider_registry",
]

