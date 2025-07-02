# mobile_ui/logic/model_registry.py

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

try:
    from huggingface_hub import snapshot_download
except Exception:  # pragma: no cover - optional dep
    snapshot_download = None

logger = logging.getLogger(__name__)

# Paths & constants
ROOT_DIR = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT_DIR / "models" / "llm_registry.json"
LOCAL_MODEL_DIR = Path.home() / ".cache" / "kari_models"
SUPPORTED_EXTENSIONS = {".bin", ".gguf", ".safetensors", ".pt"}

# Static fallback entries
STATIC_MODELS: Dict[str, List[Dict[str, Any]]] = {
    "huggingface": [
        {"id": "meta_llama_2_7b", "name": "meta-llama/Llama-2-7b-chat-hf", "runtime": "transformers", "prompt_size": 4096},
        {"id": "mistral_7b",     "name": "mistralai/Mistral-7B-Instruct-v0.1",   "runtime": "transformers", "prompt_size": 32768},
    ],
    "mistral": [
        {"id": "mixtral_8x7b",   "name": "mistralai/Mixtral-8x7B-Instruct-v0.1", "runtime": "transformers", "prompt_size": 32768},
    ],
    "deepseek": [
        {"id": "deepseek_coder","name": "deepseek-ai/deepseek-coder-6.7b-instruct","runtime": "transformers","prompt_size": 32768},
    ],
}


def normalize_model_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure every model dict has the same shape."""
    _id = entry.get("id") or entry.get("name", "").lower().replace(" ", "_")
    return {
        "id": _id,
        "name": entry.get("name", ""),
        "provider": entry.get("provider", ""),
        "runtime": entry.get("runtime", ""),
        "path": entry.get("path"),
        "prompt_size": entry.get("prompt_size", 0),
        "metadata": entry.get("metadata", {}),
    }


def list_llama_cpp_models() -> List[Dict[str, Any]]:
    root = Path(os.getenv("MODEL_DIR", "/models/llama-cpp"))
    try:
        return [
            normalize_model_entry({
                "id": p.stem,
                "name": p.stem,
                "provider": "llama-cpp",
                "runtime": "llama_cpp",
                "path": str(p),
                "prompt_size": 32768,
            })
            for p in root.iterdir() if p.suffix in SUPPORTED_EXTENSIONS
        ]
    except Exception as e:
        logger.debug("llama-cpp scan failed: %s", e)
        return []


def list_lmstudio_models() -> List[Dict[str, Any]]:
    # reuse llama-cpp logic for now
    return list_llama_cpp_models()


def list_gemini_models() -> List[Dict[str, Any]]:
    specs = [
        {"name": "gemini-pro",    "runtime": "api", "prompt_size": 32768},
        {"name": "gemini-1.5-pro","runtime": "api", "prompt_size": 1048576},
    ]
    return [
        normalize_model_entry({**s, "provider": "gemini"})
        for s in specs
    ]


def list_anthropic_models() -> List[Dict[str, Any]]:
    specs = [
        {"name": "claude-3-opus-20240229",   "runtime": "api", "prompt_size": 1048576},
        {"name": "claude-3-sonnet-20240229", "runtime": "api", "prompt_size": 1048576},
    ]
    return [
        normalize_model_entry({**s, "provider": "anthropic"})
        for s in specs
    ]


def list_groq_models() -> List[Dict[str, Any]]:
    specs = [
        {"name": "mixtral-8x7b-32768", "runtime": "api", "prompt_size": 32768},
        {"name": "llama3-70b-8192",   "runtime": "api", "prompt_size": 8192},
    ]
    return [
        normalize_model_entry({**s, "provider": "groq"})
        for s in specs
    ]


def list_custom_models() -> List[Dict[str, Any]]:
    """Read user-defined entries from llm_registry.json under key 'custom'."""
    if not REGISTRY_PATH.exists():
        return []
    try:
        raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        return [
            normalize_model_entry({**m, "provider": "custom"})
            for m in raw.get("custom", [])
        ]
    except Exception as e:
        logger.error("Failed to load custom registry: %s", e)
        return []


# Top-level provider→loader map
MODEL_PROVIDERS: Dict[str, Union[List[Dict[str, Any]], Callable[[], List[Dict[str, Any]]]]] = {
    "llama-cpp":   list_llama_cpp_models,
    "lmstudio":    list_lmstudio_models,
    "gemini":      list_gemini_models,
    "anthropic":   list_anthropic_models,
    "groq":        list_groq_models,
    "huggingface": STATIC_MODELS["huggingface"],
    "mistral":     STATIC_MODELS["mistral"],
    "deepseek":    STATIC_MODELS["deepseek"],
    "custom":      list_custom_models,
}


def list_providers(only_ready: bool = True) -> List[str]:
    """
    Return all provider keys. If only_ready, omit providers without models.
    """
    keys = list(MODEL_PROVIDERS.keys())
    if only_ready:
        keys = [k for k in keys if get_models(k)]
    return sorted(keys)


def get_models(provider: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch normalized model entries for a given provider.
    If provider is None, returns all models across all providers.
    """
    out: List[Dict[str, Any]] = []
    for prov, loader in MODEL_PROVIDERS.items():
        if provider and prov != provider:
            continue
        entries = loader() if callable(loader) else loader
        for e in entries:
            item = normalize_model_entry({**e, "provider": prov})
            item["model_name"] = item.get("name", "")
            out.append(item)

    # Append registry-defined models
    out.extend(get_registry_models(provider))

    return out


def load_registry() -> Dict[str, Dict[str, Any]]:
    """Load raw registry JSON from ``REGISTRY_PATH`` if present."""
    if not REGISTRY_PATH.exists():
        return {}
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception as e:  # pragma: no cover - invalid json
        logger.error("Failed to load registry: %s", e)
        return {}


def get_registry_models(provider: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return models declared in ``llm_registry.json`` filtered by provider."""
    data = load_registry()
    models = []
    for entry in data.values():
        prov = entry.get("provider", "")
        if provider:
            alias = provider.lower()
            if alias == "local":
                alias = "llama-cpp"
            if prov != alias:
                continue
        models.append(entry)
    return models


def get_ready_models() -> List[Dict[str, Any]]:
    """Return union of static models and registry models with fallback."""
    ready = get_models(None) + get_registry_models(None)
    if not any(m.get("model_name") == "distilbert-base-uncased" for m in ready):
        ready.append(
            {
                "model_name": "distilbert-base-uncased",
                "provider": "local",
                "runtime": "transformers",
            }
        )
    return ready


def get_providers() -> List[str]:
    """Return all provider keys including registry providers."""
    providers = set(MODEL_PROVIDERS.keys())
    providers.update(m.get("provider", "") for m in load_registry().values())
    return sorted(p for p in providers if p)


def ensure_model_downloaded(model: Dict[str, Any]) -> str:
    """
    Ensure the given model entry is available locally.
    Returns the local filesystem path.
    """
    name = model["name"]
    runtime = model["runtime"]
    path = model.get("path")

    # Already local
    if runtime in ("llama_cpp",) and path:
        if Path(path).exists():
            return path
        raise FileNotFoundError(f"Local model not found: {path}")

    # HuggingFace snapshot
    if runtime == "transformers" and "/" in name:
        if snapshot_download is None:
            raise RuntimeError("huggingface_hub is required to download models")
        dest = LOCAL_MODEL_DIR / name.replace("/", "_")
        if dest.exists():
            return str(dest)
        dest.mkdir(parents=True, exist_ok=True)
        try:
            snapshot_download(repo_id=name, local_dir=str(dest), resume_download=True)
            return str(dest)
        except Exception as e:
            raise RuntimeError(f"HF download failed for {name}: {e}")

    # Custom via URL (not yet implemented)
    if runtime == "custom":
        raise NotImplementedError("Custom URL download not implemented")

    raise RuntimeError(f"Cannot download model: {model}")
