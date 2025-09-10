"""
Kari Model Discovery Engine (Enterprise)
- Discovers, validates, and manages local/remote LLM and embedding models.
- Pluggable registry: local disk, llama.cpp (GGUF), transformers, plugin endpoints, remote registry.
- Observability: logs, RBAC, audit, and hot reloads.
"""

import os
import glob
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger("kari.model_discovery")
# Avoid duplicate log messages bubbling up to Uvicorn
logger.propagate = False

# ======== Model Registry/Source Abstractions =========

class ModelSourceBase:
    def list_models(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

# ======== Local Disk Model Discovery ========

class LocalModelSource(ModelSourceBase):
    """
    Scans a directory for model folders/files (for transformers, GGUF, etc.)
    """
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.getenv("KARI_LOCAL_MODEL_DIR", "./models")

    def list_models(self) -> List[Dict[str, Any]]:
        logger.info(f"Scanning for local models in {self.base_dir}")
        pattern = os.path.join(self.base_dir, "**")
        model_files = glob.glob(pattern, recursive=True)
        models = []
        for path in model_files:
            if os.path.isdir(path) or path.endswith(('.bin', '.pt', '.gguf', '.safetensors')):
                models.append({
                    "name": os.path.basename(path),
                    "path": path,
                    "type": self.detect_type(path),
                    "source": "local"
                })
        return models

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        models = self.list_models()
        for m in models:
            if m["name"] == model_name:
                return m
        return None

    def detect_type(self, path: str) -> str:
        # Very basic; you can expand as needed
        if os.path.isdir(path):
            return "transformers"
        elif path.endswith(".gguf"):
            return "llama-gguf"
        elif path.endswith(".pt"):
            return "pytorch"
        elif path.endswith(".bin"):
            return "bin"
        elif path.endswith(".safetensors"):
            return "safetensors"
        else:
            return "unknown"

# ======== Ollama Model Registry (if installed) ========

# Ollama integration removed; prefer llama.cpp GGUF discovery via LocalModelSource.

# ======== Transformers Hub/Plugin Registry (Stub for now) ========

class TransformersHubSource(ModelSourceBase):
    """
    Discovers models from Hugging Face or custom transformers repo.
    """
    def __init__(self, hub_url: Optional[str] = None):
        self.hub_url = hub_url or os.getenv("KARI_HF_HUB_URL", "https://huggingface.co")

    def list_models(self) -> List[Dict[str, Any]]:
        # Evil Twin: Real implementation should query Hugging Face or internal registry
        # Stub: Just returns some common models for now
        return [
            {"name": "bert-base-uncased", "source": "hf_hub", "type": "transformers"},
            {"name": "sentence-transformers/all-MiniLM-L6-v2", "source": "hf_hub", "type": "transformers"},
        ]

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        for m in self.list_models():
            if m["name"] == model_name:
                return m
        return None

# ======== Plugin/Remote Model Sources (Pluggable) ========

class PluginModelSource(ModelSourceBase):
    """
    Discovers models exposed via plugin manifest.
    """
    def __init__(self, plugin_registry: Optional[Callable[[], List[Dict[str, Any]]]] = None):
        self.plugin_registry = plugin_registry

    def list_models(self) -> List[Dict[str, Any]]:
        if self.plugin_registry:
            try:
                return self.plugin_registry()
            except Exception as ex:
                logger.error(f"Plugin model registry error: {ex}")
        return []

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        for m in self.list_models():
            if m["name"] == model_name:
                return m
        return None

# ======== Master Discovery Engine ========

class ModelDiscoveryEngine:
    """
    Aggregates and queries all model sources.
    """
    def __init__(self, sources: Optional[List[ModelSourceBase]] = None):
        self.sources = sources or self.default_sources()

    @staticmethod
    def default_sources() -> List[ModelSourceBase]:
        out = []
    # Ollama provider removed; prefer local llama.cpp (GGUF) discovery.
        out.append(LocalModelSource())
        out.append(TransformersHubSource())
        # Add more as needed (plugins, cloud, enterprise registry...)
        return out

    def list_all_models(self) -> List[Dict[str, Any]]:
        all_models = []
        for source in self.sources:
            try:
                all_models.extend(source.list_models())
            except Exception as ex:
                logger.warning(f"Model source {type(source).__name__} failed: {ex}")
        return all_models

    def find_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        for source in self.sources:
            try:
                info = source.get_model_info(model_name)
                if info:
                    return info
            except Exception:
                continue
        return None

    def reload_sources(self):
        # Hot-reload or refresh logic, if model list can change at runtime
        self.sources = self.default_sources()

# ======== One-liner APIs =========

def list_models() -> List[Dict[str, Any]]:
    """
    Returns all models discoverable by the system.
    """
    engine = ModelDiscoveryEngine()
    return engine.list_all_models()

def get_model_info(model_name: str) -> Optional[Dict[str, Any]]:
    engine = ModelDiscoveryEngine()
    return engine.find_model(model_name)

# === Simplified registry sync used in tests ===
REGISTRY_PATH = Path(os.getenv("KARI_MODEL_REGISTRY", "model_registry.json"))


def sync_registry(path: str | Path = REGISTRY_PATH) -> List[Dict[str, Any]]:
    """Write a trivial registry file and return model list."""
    models = list_models()
    Path(path).write_text(json.dumps(models), encoding="utf-8")
    return models

# ======== Exports =========
__all__ = [
    "ModelSourceBase",
    "LocalModelSource",
    "TransformersHubSource",
    "PluginModelSource",
    "ModelDiscoveryEngine",
    "list_models",
    "get_model_info",
]
