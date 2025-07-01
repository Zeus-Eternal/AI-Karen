# mobile_ui/logic/model_registry.py

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Union, Callable, Dict

logger = logging.getLogger(__name__)

# ─── Dynamic Loaders ────────────────────────────────────────────────────────────

def list_llama_cpp_models(models_dir: str = "/models") -> List[str]:
    exts = {".gguf", ".bin"}
    out = []
    try:
        for f in Path(models_dir).iterdir():
            if f.is_file() and f.suffix in exts:
                out.append(f.stem)
    except Exception as e:
        logger.warning(f"[llama-cpp] scan failed: {e}")
    return out

def list_lmstudio_models() -> List[str]:
    # placeholder for real LM Studio REST lookup
    return ["lmstudio-api-models"]

def list_gemini_models() -> List[str]:
    # placeholder for real Google Gemini API
    return ["gemini-pro", "gemini-1.5-pro"]

def list_anthropic_models() -> List[str]:
    # placeholder for Anthropic API
    return ["claude-3-opus-20240229", "claude-3-sonnet"]

def list_groq_models() -> List[str]:
    # if you have a local Groq runner, scan its model folder
    groq_dir = Path("/models/groq")
    return [p.stem for p in groq_dir.glob("*.gguf")] if groq_dir.exists() else ["<no-groq-models>"]

# ─── Static Lists ───────────────────────────────────────────────────────────────

STATIC_MODELS = {
    "deepseek":    ["deepseek-coder-6.7b", "deepseek-llm-7b"],
    "mistral":     ["mistral-small", "mistral-medium", "mistral-large"],
}

# ─── Provider Map ───────────────────────────────────────────────────────────────

# Value is either a callable loader (for dynamic) or a static list
MODEL_PROVIDERS: Dict[str, Union[Callable[[], List[str]], List[str]]] = {
    "llama-cpp": list_llama_cpp_models,
    "lmstudio":  list_lmstudio_models,
    "gemini":    list_gemini_models,
    "anthropic": list_anthropic_models,
    "groq":      list_groq_models,
    "claude":    ["claude-3-opus-20240229"],
    "deepseek":  STATIC_MODELS["deepseek"],
    "mistral":   STATIC_MODELS["mistral"],
    "transformers": ["gpt2", "bert-base", "custom-finetune"],
}

# ─── Public Interface ──────────────────────────────────────────────────────────

def list_providers() -> List[str]:
    """Return all registered provider names."""
    return list(MODEL_PROVIDERS.keys())

def get_models(provider: str) -> List[Dict[str, str]]:
    """
    Return a list of {'name': <model>, 'provider': <provider>} for the given provider.
    """
    loader = MODEL_PROVIDERS.get(provider)
    if not loader:
        return []
    # if loader is a function, call it; otherwise treat as static list
    raw: List[str] = loader() if callable(loader) else loader
    return [{"name": m, "provider": provider} for m in raw]

def ensure_model_downloaded(provider: str, model: str) -> bool:
    """
    Stub for pre-fetching or verifying a model. Customize per provider if needed.
    """
    logger.info(f"[model_registry] assume '{model}' for '{provider}' is ready.")
    return True
