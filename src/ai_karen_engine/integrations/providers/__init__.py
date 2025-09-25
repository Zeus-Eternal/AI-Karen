"""LLM Provider implementations for Kari AI (lazy import facade)."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "HuggingFaceProvider",
    "LlamaCppProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "DeepseekProvider",
    "CopilotKitProvider",
    "FallbackProvider",
]


def __getattr__(name: str):
    module_map = {
        "HuggingFaceProvider": "ai_karen_engine.integrations.providers.huggingface_provider",
        "LlamaCppProvider": "ai_karen_engine.integrations.providers.llamacpp_provider",
        "OpenAIProvider": "ai_karen_engine.integrations.providers.openai_provider",
        "GeminiProvider": "ai_karen_engine.integrations.providers.gemini_provider",
        "DeepseekProvider": "ai_karen_engine.integrations.providers.deepseek_provider",
        "CopilotKitProvider": "ai_karen_engine.integrations.providers.copilotkit_provider",
        "FallbackProvider": "ai_karen_engine.integrations.providers.fallback_provider",
    }

    if name not in module_map:
        raise AttributeError(name)

    module = import_module(module_map[name])
    return getattr(module, name)
