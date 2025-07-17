"""
LLM Registry for Kari AI: Secure, dynamic, zero-circular-import LLM provider registry.
- All providers loaded via factory/lazy-load pattern.
- No direct imports at module level.
- Supports hot-swapping and test stubbing.
"""

import os

# --- Factory Loader Functions (lazy) ---

def load_ollama_engine():
    from ai_karen_engine.services import get_ollama_engine
    return get_ollama_engine()

def load_deepseek_client():
    from ai_karen_engine.services import get_deepseek_client
    return get_deepseek_client()

def load_openai_service():
    from ai_karen_engine.services import get_openai_service
    return get_openai_service()

def load_gemini_service():
    from ai_karen_engine.services import get_gemini_service
    return get_gemini_service()

# --- Main Registry (priority order; can override with ENV) ---

REGISTRY = {
    "ollama": load_ollama_engine,
    "deepseek": load_deepseek_client,
    "openai": load_openai_service,
    "gemini": load_gemini_service,
}

_ACTIVE_PROVIDER = os.getenv("KARI_DEFAULT_PROVIDER", "ollama")

def set_active(provider: str) -> None:
    if provider not in REGISTRY:
        raise KeyError(provider)
    global _ACTIVE_PROVIDER
    _ACTIVE_PROVIDER = provider

def get_active():
    """Get the current active LLM provider."""
    if _ACTIVE_PROVIDER not in REGISTRY:
        raise RuntimeError(f"Provider '{_ACTIVE_PROVIDER}' not available.")
    return REGISTRY[_ACTIVE_PROVIDER]()

def get_llm(provider: str):
    """Explicitly get a named provider (raises if not found)."""
    if provider not in REGISTRY:
        raise RuntimeError(f"LLM provider '{provider}' not registered.")
    return REGISTRY[provider]()

def list_llms():
    """List available LLM provider names."""
    return list(REGISTRY.keys())

def active() -> str:
    return _ACTIVE_PROVIDER

registry = type(
    "KariLLMRegistry",
    (),
    {
        "get_active": staticmethod(get_active),
        "get_llm": staticmethod(get_llm),
        "list_llms": staticmethod(list_llms),
        "set_active": staticmethod(set_active),
        "active": property(lambda self: _ACTIVE_PROVIDER),
    },
)()

__all__ = ["registry", "get_llm", "get_active", "list_llms", "set_active", "active"]
