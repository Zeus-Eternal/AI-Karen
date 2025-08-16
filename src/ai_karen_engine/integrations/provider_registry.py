"""
Generic provider registry for hierarchical extension management.

Goals:
- Single, DRY implementation (no duplicate classes/functions).
- Thread-safe registration and instance caching.
- Cache instances per (provider_name, init_kwargs) to support different configs.
- Graceful auto-registration of core providers (CopilotKit) if available.
- Safe shutdown on unregister (sync or async).
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)

# -----------------------------
# Data models
# -----------------------------

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
    category: str = "LLM"


# -----------------------------
# Registry
# -----------------------------

class ProviderRegistry:
    """Simple registry for extension providers."""

    def __init__(self) -> None:
        self._registrations: Dict[str, ProviderRegistration] = {}
        # Cache of instances per provider and per-kwargs hash
        self._instances: Dict[str, Dict[int, Any]] = {}
        self._lock = threading.RLock()

        # Attempt to auto-register core providers (best-effort)
        self._register_core_providers()

    # ---------- Registration API ----------

    def register_provider(
        self,
        name: str,
        provider_class: Type[Any],
        *,
        description: str = "",
        models: Optional[List[ModelInfo]] = None,
        requires_api_key: bool = False,
        default_model: Optional[str] = None,
        category: str = "LLM",
    ) -> None:
        """Register (or overwrite) a provider with optional models."""
        with self._lock:
            self._registrations[name] = ProviderRegistration(
                name=name,
                provider_class=provider_class,
                description=description,
                models=models or [],
                requires_api_key=requires_api_key,
                default_model=default_model,
                category=category,
            )
            # Ensure an instance bucket exists
            self._instances.setdefault(name, {})

    def unregister_provider(self, name: str) -> bool:
        """Unregister a provider and clean up all its cached instances."""
        with self._lock:
            if name not in self._registrations:
                return False

            # Clean up instances if present
            instances = self._instances.pop(name, {})
            for cache_key, instance in list(instances.items()):
                self._shutdown_instance(name, instance, cache_key)

            # Remove registration
            del self._registrations[name]
            return True

    def is_provider_registered(self, name: str) -> bool:
        with self._lock:
            return name in self._registrations

    def get_provider_info(self, name: str) -> Optional[ProviderRegistration]:
        with self._lock:
            return self._registrations.get(name)

    def list_providers(self, category: Optional[str] = None) -> List[str]:
        with self._lock:
            if category:
                return [
                    name
                    for name, reg in self._registrations.items()
                    if reg.category == category
                ]
            return list(self._registrations.keys())

    def list_models(self, provider_name: str) -> List[str]:
        with self._lock:
            reg = self._registrations.get(provider_name)
            if not reg:
                return []
            return [m.name for m in reg.models]

    def get_all_capabilities(self) -> Dict[str, List[str]]:
        with self._lock:
            out: Dict[str, List[str]] = {}
            for name, reg in self._registrations.items():
                caps: List[str] = []
                for m in reg.models:
                    caps.extend(m.capabilities)
                # Deduplicate while preserving order
                seen = set()
                deduped = [c for c in caps if not (c in seen or seen.add(c))]
                out[name] = deduped
            return out

    # ---------- Instance API ----------

    def get_provider(self, name: str, **init_kwargs: Any) -> Optional[Any]:
        """
        Get or create an instance of a provider.

        Instances are cached per provider + init_kwargs combo:
        cache_key = hash(frozenset(init_kwargs.items()))
        """
        with self._lock:
            reg = self._registrations.get(name)
            if not reg:
                logger.debug("Provider '%s' not registered", name)
                return None

            # Inject default model if not provided
            if reg.default_model and "model" not in init_kwargs:
                init_kwargs["model"] = reg.default_model

            bucket = self._instances.setdefault(name, {})
            try:
                cache_key = hash(frozenset(init_kwargs.items()))
            except TypeError:
                # Fallback if kwargs contain unhashables: use repr
                cache_key = hash(repr(sorted(init_kwargs.items(), key=lambda kv: kv[0])))

            if cache_key not in bucket:
                logger.debug("Creating provider instance '%s' with kwargs=%s", name, init_kwargs)
                bucket[cache_key] = reg.provider_class(**init_kwargs)
            return bucket[cache_key]

    # ---------- Internals ----------

    def _register_core_providers(self) -> None:
        """Best-effort auto-registration of core system providers."""

        try:
            from ai_karen_engine.integrations.providers import (
                DeepseekProvider,
                GeminiProvider,
                HuggingFaceProvider,
                OllamaProvider,
                OpenAIProvider,
            )

            providers: List[Dict[str, Any]] = [
                {
                    "name": "ollama",
                    "cls": OllamaProvider,
                    "description": "Local Ollama server for running open-source models",
                    "default_model": "llama3.2:latest",
                    "requires_api_key": False,
                    "capabilities": ["text", "embeddings"],
                },
                {
                    "name": "openai",
                    "cls": OpenAIProvider,
                    "description": "OpenAI GPT models via API",
                    "default_model": "gpt-3.5-turbo",
                    "requires_api_key": True,
                    "capabilities": ["text", "embeddings"],
                },
                {
                    "name": "gemini",
                    "cls": GeminiProvider,
                    "description": "Google Gemini models via API",
                    "default_model": "gemini-1.5-flash",
                    "requires_api_key": True,
                    "capabilities": ["text", "embeddings"],
                },
                {
                    "name": "deepseek",
                    "cls": DeepseekProvider,
                    "description": "Deepseek models optimized for coding and reasoning",
                    "default_model": "deepseek-chat",
                    "requires_api_key": True,
                    "capabilities": ["text"],
                },
                {
                    "name": "huggingface",
                    "cls": HuggingFaceProvider,
                    "description": "HuggingFace models via Inference API or local execution",
                    "default_model": "microsoft/DialoGPT-large",
                    "requires_api_key": True,
                    "capabilities": ["text", "embeddings"],
                },
            ]

            for info in providers:
                models = [ModelInfo(name=info["default_model"], capabilities=info["capabilities"])]
                self.register_provider(
                    name=info["name"],
                    provider_class=info["cls"],
                    description=info["description"],
                    models=models,
                    requires_api_key=info["requires_api_key"],
                    default_model=info["default_model"],
                )
                logger.info("Auto-registered core provider: %s", info["name"])

        except Exception as e:  # pragma: no cover - best effort
            logger.warning("Failed to register core providers: %s", e)

    def _shutdown_instance(self, provider_name: str, instance: Any, cache_key: int) -> None:
        """Attempt graceful shutdown of a provider instance (sync or async)."""
        try:
            if hasattr(instance, "shutdown"):
                if inspect.iscoroutinefunction(instance.shutdown):
                    # Fire-and-forget; do not block the unregister path
                    try:
                        asyncio.get_running_loop().create_task(instance.shutdown())  # type: ignore
                        logger.info(
                            "Provider %s instance (%s) scheduled async shutdown",
                            provider_name, cache_key
                        )
                    except RuntimeError:
                        # No running loop; run synchronously
                        asyncio.run(instance.shutdown())  # type: ignore
                else:
                    instance.shutdown()  # type: ignore
        except Exception as exc:  # pragma: no cover
            logger.warning("Error during provider %s shutdown: %s", provider_name, exc)


# -----------------------------
# Global accessors (singleton-ish)
# -----------------------------

_global_registry: Optional[ProviderRegistry] = None
_global_lock = threading.RLock()

def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry instance (create on first use)."""
    global _global_registry
    if _global_registry is None:
        with _global_lock:
            if _global_registry is None:
                _global_registry = ProviderRegistry()
    return _global_registry

def initialize_provider_registry() -> ProviderRegistry:
    """Reinitialize and return a fresh global provider registry."""
    global _global_registry
    with _global_lock:
        _global_registry = ProviderRegistry()
    return _global_registry


__all__ = [
    "ModelInfo",
    "ProviderRegistration",
    "ProviderRegistry",
    "get_provider_registry",
    "initialize_provider_registry",
]
