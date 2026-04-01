"""
Legacy provider registry compatibility layer.

This module preserves the historical ``ai_karen_engine.integrations.provider_registry``
API while delegating the live LLM provider state to the refactored registry modules.
It keeps the app DRY by reusing ``llm_registry`` for real providers and exposes a small
in-memory registry class for voice/video registries and older integration code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from ai_karen_engine.integrations.llm_registry import get_registry


@dataclass
class ModelInfo:
    """Legacy model metadata shape expected across older integrations."""

    name: str
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    default_settings: Dict[str, Any] = field(default_factory=dict)
    context_length: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderRegistration:
    """Legacy provider registration shape expected by older integrations."""

    name: str
    provider_class: Any
    description: str
    models: List[ModelInfo] = field(default_factory=list)
    requires_api_key: bool = False
    default_model: Optional[str] = None
    category: str = "LLM"
    supports_streaming: bool = False
    supports_embeddings: bool = False
    health_status: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProviderRegistry:
    """Small compatibility registry used by voice/video and legacy integrations."""

    def __init__(self) -> None:
        self._registrations: Dict[str, ProviderRegistration] = {}
        self._instances: Dict[str, Dict[str, Any]] = {}

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
        supports_streaming: bool = False,
        supports_embeddings: bool = False,
        **kwargs: Any,
    ) -> None:
        self._registrations[name] = ProviderRegistration(
            name=name,
            provider_class=provider_class,
            description=description,
            models=models or [],
            requires_api_key=requires_api_key,
            default_model=default_model,
            category=category,
            supports_streaming=supports_streaming,
            supports_embeddings=supports_embeddings,
            metadata=dict(kwargs),
        )

    def list_providers(
        self, category: Optional[str] = None, healthy_only: bool = False
    ) -> List[str]:
        providers = []
        for name, registration in self._registrations.items():
            if category and registration.category != category:
                continue
            if healthy_only and registration.health_status not in {"healthy", "unknown"}:
                continue
            providers.append(name)
        return providers

    def get_provider_info(self, name: str) -> Optional[ProviderRegistration]:
        return self._registrations.get(name)

    def get_provider(self, name: str, **init_kwargs: Any) -> Optional[Any]:
        registration = self._registrations.get(name)
        if not registration:
            return None
        model_name = init_kwargs.get("model") or registration.default_model or ""
        bucket = self._instances.setdefault(name, {})
        cache_key = repr(sorted(init_kwargs.items()))
        if cache_key not in bucket:
            if model_name and "model" not in init_kwargs:
                init_kwargs["model"] = model_name
            bucket[cache_key] = registration.provider_class(**init_kwargs)
        return bucket[cache_key]


class _LegacyLLMProviderRegistry(ProviderRegistry):
    """Adapter that exposes the old provider_registry API over llm_registry."""

    @staticmethod
    def _to_models(info: Dict[str, Any]) -> List[ModelInfo]:
        models: List[ModelInfo] = []
        raw_models = info.get("models")
        if isinstance(raw_models, list):
            for raw in raw_models:
                if isinstance(raw, ModelInfo):
                    models.append(raw)
                elif isinstance(raw, dict):
                    models.append(
                        ModelInfo(
                            name=str(raw.get("name") or raw.get("model") or raw.get("id") or ""),
                            description=str(raw.get("description") or ""),
                            capabilities=list(raw.get("capabilities") or []),
                            default_settings=dict(raw.get("default_settings") or {}),
                            context_length=raw.get("context_length"),
                            metadata=dict(raw.get("metadata") or {}),
                        )
                    )
                elif raw:
                    models.append(ModelInfo(name=str(raw)))

        if not models:
            for raw in info.get("available_models") or []:
                if raw:
                    models.append(ModelInfo(name=str(raw)))

        default_model = info.get("default_model")
        if default_model and not any(model.name == default_model for model in models):
            models.insert(0, ModelInfo(name=str(default_model)))

        return [model for model in models if model.name]

    @staticmethod
    def _coerce_provider_class(raw: Any) -> Any:
        return raw if raw else "unknown"

    def register_provider(self, name: str, provider_class: Type[Any], **kwargs: Any) -> None:
        registry = get_registry()
        registration_kwargs = dict(kwargs)
        registration_kwargs.pop("models", None)
        registration_kwargs.pop("category", None)
        registry.register_provider(name, provider_class, **registration_kwargs)

    def list_providers(
        self, category: Optional[str] = None, healthy_only: bool = False
    ) -> List[str]:
        registry = get_registry()
        providers = registry.list_providers()
        if category is None and not healthy_only:
            return providers

        filtered: List[str] = []
        for name in providers:
            info = registry.get_provider_info(name) or {}
            if category and str(info.get("category") or "LLM") != category:
                continue
            if healthy_only and str(info.get("health_status") or "unknown") not in {"healthy", "unknown"}:
                continue
            filtered.append(name)
        return filtered

    def get_provider_info(self, name: str) -> Optional[ProviderRegistration]:
        info = get_registry().get_provider_info(name)
        if not info:
            return None
        return ProviderRegistration(
            name=name,
            provider_class=self._coerce_provider_class(info.get("provider_class")),
            description=str(info.get("description") or ""),
            models=self._to_models(info),
            requires_api_key=bool(info.get("requires_api_key", False)),
            default_model=info.get("default_model"),
            category=str(info.get("category") or "LLM"),
            supports_streaming=bool(info.get("supports_streaming", False)),
            supports_embeddings=bool(info.get("supports_embeddings", False)),
            health_status=str(info.get("health_status") or "unknown"),
            metadata=dict(info),
        )

    def get_provider(self, name: str, **init_kwargs: Any) -> Optional[Any]:
        return get_registry().get_provider(name, **init_kwargs)


_legacy_provider_registry: Optional[_LegacyLLMProviderRegistry] = None


def get_provider_registry() -> _LegacyLLMProviderRegistry:
    """Return the legacy provider registry facade backed by llm_registry."""
    global _legacy_provider_registry
    if _legacy_provider_registry is None:
        _legacy_provider_registry = _LegacyLLMProviderRegistry()
    return _legacy_provider_registry


__all__ = [
    "ModelInfo",
    "ProviderRegistration",
    "ProviderRegistry",
    "get_provider_registry",
]
