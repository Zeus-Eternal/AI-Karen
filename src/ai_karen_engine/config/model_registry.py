import logging
from pathlib import Path
from typing import List

from ai_karen_engine.config.llm_provider_config import get_provider_config_manager

logger = logging.getLogger(__name__)

def list_local_gguf_models(models_dir=None):
    """Return local GGUF models from the core discovery service."""
    from ai_karen_engine.core.model_runtime.model_discovery_service import (
        get_model_discovery_service,
    )

    service = get_model_discovery_service()
    models = sorted({model.display_name for model in service.get_models(model_format="gguf")})
    if not models:
        logger.debug("No local GGUF models detected by the core discovery service.")
    return models or ["<no-models-found>"]


def list_transformers_models(registry_path: Path | None = None) -> List[str]:
    """Return locally available transformers models from core discovery."""
    from ai_karen_engine.core.model_runtime.model_discovery_service import (
        get_model_discovery_service,
    )

    service = get_model_discovery_service()
    models = sorted({model.display_name for model in service.get_models(model_format="transformers")})
    if not models:
        logger.debug("No transformers models detected by the core discovery service.")
    return models


def list_ollama_models():
    """Compatibility alias for local GGUF discovery."""
    return list_local_gguf_models()


def list_gemini_models() -> List[str]:
    """Return configured Gemini models without invoking the provider."""
    provider = get_provider_config_manager().get_provider("gemini")
    if not provider:
        return []
    models = [model.name for model in provider.models if getattr(model, "name", None)]
    return sorted(set(models or ([provider.default_model] if provider.default_model else [])))


def list_lmstudio_models(endpoint: str | None = None, registry_path: Path | None = None) -> List[str]:
    """Return configured LM Studio models without probing the network."""
    provider = get_provider_config_manager().get_provider("lmstudio")
    if not provider:
        return []
    models = [model.name for model in provider.models if getattr(model, "name", None)]
    return sorted(set(models or ([provider.default_model] if provider.default_model else [])))


def list_anthropic_models() -> List[str]:
    """Return configured Anthropic models without hardcoding execution state."""
    provider = get_provider_config_manager().get_provider("anthropic")
    if not provider:
        return []
    models = [model.name for model in provider.models if getattr(model, "name", None)]
    return sorted(set(models or ([provider.default_model] if provider.default_model else [])))


def list_groq_models():
    """Return configured Groq models without local filesystem discovery."""
    provider = get_provider_config_manager().get_provider("groq")
    if not provider:
        return []
    models = [model.name for model in provider.models if getattr(model, "name", None)]
    return sorted(set(models or ([provider.default_model] if provider.default_model else [])))


def get_model_providers() -> dict[str, list[str]]:
    """Return a lazily evaluated provider inventory."""
    return {
        "local_gguf": list_local_gguf_models("models/local-gguf"),
        "lmstudio": list_lmstudio_models(),
        "gemini": list_gemini_models(),
        "anthropic": list_anthropic_models(),
        "groq": list_groq_models(),
        "mistral": ["mistral-small", "mistral-medium", "mistral-large"],
        "deepseek": ["deepseek-coder-6.7b", "deepseek-llm-7b"],
        "transformers": list_transformers_models(),
    }


MODEL_PROVIDERS = get_model_providers()
