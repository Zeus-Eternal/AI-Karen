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

def get_active():
    """Get the current default LLM provider (env or hardcoded fallback)."""
    provider = os.getenv("KARI_DEFAULT_PROVIDER", "ollama")
    if provider not in REGISTRY:
        raise RuntimeError(f"Provider '{provider}' not available.")
    return REGISTRY[provider]()

def get_llm(provider: str):
    """Explicitly get a named provider (raises if not found)."""
    if provider not in REGISTRY:
        raise RuntimeError(f"LLM provider '{provider}' not registered.")
    return REGISTRY[provider]()

def list_llms():
    """List available LLM provider names."""
    return list(REGISTRY.keys())

# Optionally, if you want to expose a single global:
registry = type("KariLLMRegistry", (), {
    "get_active": staticmethod(get_active),
    "get_llm": staticmethod(get_llm),
    "list_llms": staticmethod(list_llms),
})()
