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
        
        # Auto-register core providers
        self._register_core_providers()

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
        
        # Create a cache key based on the provider name and init kwargs
        cache_key = f"{name}_{hash(frozenset(init_kwargs.items()))}"
        
        if cache_key not in self._instances:
            if reg.default_model and "model" not in init_kwargs:
                init_kwargs["model"] = reg.default_model
            self._instances[cache_key] = reg.provider_class(**init_kwargs)
        return self._instances[cache_key]

    def list_providers(self) -> List[str]:
        """Return the list of registered provider names."""
        return list(self._registrations.keys())

    def list_models(self, provider_name: str) -> List[str]:
        """List available models for a provider."""
        reg = self._registrations.get(provider_name)
        if not reg:
            return []
        return [m.name for m in reg.models]

    def _register_core_providers(self) -> None:
        """Register core system providers automatically."""
        try:
            # Register CopilotKit provider
            from ai_karen_engine.integrations.copilotkit_provider import (
                CopilotKitProvider,
                COPILOTKIT_MODELS
            )
            
            self.register_provider(
                name="copilotkit",
                provider_class=CopilotKitProvider,
                description="AI-powered development assistance with memory integration and action suggestions",
                models=COPILOTKIT_MODELS,
                requires_api_key=False,
                default_model="copilot-assist"
            )
            
        except ImportError as e:
            # CopilotKit provider not available - this is acceptable in some environments
            pass
        except Exception as e:
            # Log error but don't fail registry initialization
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to register core providers: {e}")

    def get_provider_info(self, name: str) -> Optional[ProviderRegistration]:
        """Get provider registration information."""
        return self._registrations.get(name)

    def is_provider_registered(self, name: str) -> bool:
        """Check if a provider is registered."""
        return name in self._registrations

    def unregister_provider(self, name: str) -> bool:
        """Unregister a provider and clean up its instance."""
        if name not in self._registrations:
            return False
        
        # Clean up instance if it exists
        if name in self._instances:
            instance = self._instances[name]
            # Try to shutdown gracefully if the provider supports it
            if hasattr(instance, 'shutdown'):
                try:
                    if hasattr(instance.shutdown, '__call__'):
                        # Check if it's async
                        import asyncio
                        import inspect
                        if inspect.iscoroutinefunction(instance.shutdown):
                            # For async shutdown, we can't wait here, just log
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.info(f"Provider {name} has async shutdown - manual cleanup required")
                        else:
                            instance.shutdown()
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Error during provider {name} shutdown: {e}")
            
            del self._instances[name]
        
        # Remove registration
        del self._registrations[name]
        return True

    def get_all_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities for all registered providers."""
        capabilities = {}
        for name, reg in self._registrations.items():
            provider_caps = []
            for model in reg.models:
                provider_caps.extend(model.capabilities)
            capabilities[name] = list(set(provider_caps))  # Remove duplicates
        return capabilities


# Global provider registry instance
_global_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ProviderRegistry()
    return _global_registry


def initialize_provider_registry() -> ProviderRegistry:
    """Initialize and return the global provider registry."""
    global _global_registry
    _global_registry = ProviderRegistry()
    return _global_registry


__all__ = [
    "ModelInfo",
    "ProviderRegistration", 
    "ProviderRegistry",
    "get_provider_registry",
    "initialize_provider_registry"
]