"""Dynamic LLM provider registry used by the mobile UI."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------

def list_llama_cpp_models(models_dir: str = "/models") -> List[str]:
    """Return local GGUF/bin models if present."""
    exts = {".gguf", ".bin"}
    out: List[str] = []
    try:
        for f in Path(models_dir).iterdir():
            if f.is_file() and f.suffix in exts:
                out.append(f.stem)
    except Exception as exc:  # pragma: no cover - optional
        logger.warning("[llama-cpp] scan failed: %s", exc)
    return out


def list_lmstudio_models() -> List[str]:
    """Placeholder for LM Studio REST lookup."""
    return ["lmstudio-api-models"]


def list_gemini_models() -> List[str]:
    """Placeholder for Gemini API."""
    return ["gemini-pro", "gemini-1.5-pro"]


def list_anthropic_models() -> List[str]:
    """Placeholder for Anthropic API."""
    return ["claude-3-opus-20240229", "claude-3-sonnet"]


def list_groq_models() -> List[str]:
    """Return GGUF models under /models/groq if present."""
    groq_dir = Path("/models/groq")
    return [p.stem for p in groq_dir.glob("*.gguf")] if groq_dir.exists() else []


# ---------------------------------------------------------------------------
# Static lists
# ---------------------------------------------------------------------------

STATIC_MODELS: Dict[str, List[str]] = {
    "deepseek": ["deepseek-coder-6.7b", "deepseek-llm-7b"],
    "mistral": ["mistral-small", "mistral-medium", "mistral-large"],
    "huggingface": ["gpt2", "bert-base", "custom-finetune"],
}

# ---------------------------------------------------------------------------
# Provider mapping and canonicalization
# ---------------------------------------------------------------------------

MODEL_PROVIDERS: Dict[str, Union[List[str], Callable[[], List[str]]]] = {
    "llama-cpp": list_llama_cpp_models,
    "lmstudio": list_lmstudio_models,
    "gemini": list_gemini_models,
    "anthropic": list_anthropic_models,
    "groq": list_groq_models,
    "mistral": STATIC_MODELS["mistral"],
    "deepseek": STATIC_MODELS["deepseek"],
    "huggingface": STATIC_MODELS["huggingface"],
}

ALIAS_MAP = {
    "local": "llama-cpp",
    "ollama": "llama-cpp",
    "claude": "anthropic",
}

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "models" / "llm_registry.json"

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def canonical_provider(name: str) -> str:
    """Return canonical provider key for name."""
    return ALIAS_MAP.get(name, name)


def get_providers() -> List[str]:
    """Return list of all known provider keys."""
    return list(MODEL_PROVIDERS.keys())


def get_models() -> List[dict]:
    """Return list of model metadata blocks from the registry."""
    if not REGISTRY_PATH.exists():
        return []
    try:
        data = json.loads(REGISTRY_PATH.read_text())
    except Exception as exc:  # pragma: no cover - optional
        logger.warning("failed to load registry: %s", exc)
        return []

    entries = []
    for _, meta in (data.items() if isinstance(data, dict) else []):
        if isinstance(meta, dict):
            entries.append(meta)
    return entries


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------

def load_registry() -> Dict[str, dict]:
    """Loads llm_registry.json or returns empty dict."""
    if not REGISTRY_PATH.exists():
        return {}
    try:
        raw = json.loads(REGISTRY_PATH.read_text())
    except Exception as exc:  # pragma: no cover - load error
        logger.warning("failed to load registry: %s", exc)
        return {}

    if isinstance(raw, dict):
        return raw
    result: Dict[str, dict] = {}
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                name = item.get("model_name") or item.get("name")
                if name:
                    result[name] = item
    return result


def get_registry_models(provider_filter: Optional[str] = None) -> List[dict]:
    """Return models from registry.json, optionally filtered by provider."""
    data = load_registry()
    models = list(data.values())
    if provider_filter:
        p = canonical_provider(provider_filter)
        models = [m for m in models if canonical_provider(str(m.get("provider", ""))) == p]
    return models


# Backwards compatibility -----------------------------------------------------

# Legacy API used by some UI components
list_providers = get_providers


def ensure_model_downloaded(provider: str, model: str) -> bool:
    """Stub for verifying or pre-fetching a model."""
    logger.info("[model_registry] assume '%s' for '%s' is ready.", model, provider)
    return True
