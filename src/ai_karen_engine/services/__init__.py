"""Service utilities for Kari AI (compatibility wrappers, lazy-load, zero circular imports)."""

__all__ = [
    "get_ollama_engine",
    "get_deepseek_client",
    "get_openai_service",
    "get_gemini_service",
]

def get_ollama_engine():
    from ai_karen_engine.services import ollama_engine
    return ollama_engine

def get_deepseek_client():
    from ai_karen_engine.services import deepseek_client
    return deepseek_client

def get_openai_service():
    from ai_karen_engine.services import openai
    return openai

def get_gemini_service():
    from ai_karen_engine.services import gemini
    return gemini

# Optional: registry pattern for dynamic dispatch
SERVICES_REGISTRY = {
    "ollama": get_ollama_engine,
    "deepseek": get_deepseek_client,
    "openai": get_openai_service,
    "gemini": get_gemini_service,
}
