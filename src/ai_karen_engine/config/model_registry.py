import json
import logging
import os
from json import JSONDecodeError
from pathlib import Path
from typing import Iterable, List

logger = logging.getLogger(__name__)

# === Dynamic Model Providers ===

def list_llama_cpp_models(models_dir=None):
    """
    Scan for GGUF/llama.cpp compatible models
    """
    models_dir = models_dir or os.getenv("KARI_MODEL_DIR", "models")
    supported_ext = {".gguf", ".bin"}
    models = []

    try:
        models_path = Path(models_dir)
        if not models_path.exists():
            # Trigger system initialization if models directory doesn't exist
            logger.info(f"[llama-cpp] Models directory not found, initializing system...")
            try:
                from ai_karen_engine.core.initialization import initialize_system
                import asyncio
                
                # Try to initialize in background
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If event loop is running, schedule initialization
                        asyncio.create_task(initialize_system())
                    else:
                        # If no event loop, run initialization
                        asyncio.run(initialize_system())
                except RuntimeError:
                    # Fallback: just create the directory
                    models_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"[llama-cpp] Created models directory: {models_dir}")
                    
            except ImportError:
                # Fallback if initialization module not available
                models_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"[llama-cpp] Created models directory: {models_dir}")
            
            return ["<initializing-models>"]
        
        # Search recursively for model files
        for file in models_path.rglob("*"):
            if file.is_file() and file.suffix in supported_ext:
                models.append(file.stem)
                
        # If no models found, suggest initialization
        if not models:
            logger.info(f"[llama-cpp] No models found in {models_dir}. Run system initialization to download default models.")
            
    except Exception as e:
        logger.warning(f"[llama-cpp] Error accessing models directory: {e}")

    return models or ["<no-models-found>"]


def _load_model_registry_entries(model_type: str, registry_path: Path | None = None) -> List[dict]:
    """Load model entries of a specific type from the registry."""
    path = registry_path or Path(os.getenv("KARI_MODEL_REGISTRY", "model_registry.json"))
    path = path.expanduser().resolve()

    if not path.exists():
        logger.debug("Model registry not found at %s", path)
        return []

    try:
        with path.open("r", encoding="utf-8") as registry_file:
            data = json.load(registry_file)
    except (OSError, JSONDecodeError) as exc:
        logger.warning("Failed to read model registry %s: %s", path, exc)
        return []

    if not isinstance(data, list):
        logger.warning("Model registry at %s is not a list. Received type: %s", path, type(data).__name__)
        return []

    return [entry for entry in data if isinstance(entry, dict) and entry.get("type") == model_type]


def _discover_transformer_models_from_paths(paths: Iterable[str]) -> List[str]:
    discovered: List[str] = []

    for raw_path in paths:
        if not raw_path:
            continue

        path = Path(raw_path).expanduser()
        if not path.exists():
            logger.debug("Transformers model path does not exist: %s", path)
            continue

        if path.is_file():
            discovered.append(path.stem)
            continue

        for candidate in path.iterdir():
            if not candidate.is_dir():
                continue

            if (candidate / "config.json").exists() or (candidate / "tokenizer.json").exists():
                discovered.append(candidate.name)

    return discovered


def list_transformers_models(registry_path: Path | None = None) -> List[str]:
    """Return locally available transformers models discovered from the registry and filesystem."""
    entries = _load_model_registry_entries("transformers", registry_path)

    declared_names = [entry.get("name", "").strip() for entry in entries if entry.get("name")]
    declared_paths = [entry.get("path") for entry in entries if entry.get("path")]

    fallback_dir = os.getenv("KARI_TRANSFORMERS_DIR", "models/transformers")
    paths_to_scan = declared_paths + [fallback_dir]

    discovered = set(name for name in declared_names if name)
    discovered.update(_discover_transformer_models_from_paths(paths_to_scan))

    models = sorted(discovered)
    if not models:
        logger.debug("No transformers models detected. Ensure the model registry or models directory is populated.")

    return models


def list_ollama_models():
    """Deprecated: use list_llama_cpp_models instead."""
    return list_llama_cpp_models()


def list_gemini_models() -> List[str]:
    """Fetch available Gemini models using the production provider."""
    try:
        from ai_karen_engine.integrations.providers.gemini_provider import GeminiProvider

        provider = GeminiProvider()
        models = provider.get_models()
        if not models:
            logger.warning("Gemini provider returned no models. Verify GEMINI_API_KEY configuration.")
        return models
    except Exception as exc:
        logger.error("Failed to enumerate Gemini models: %s", exc)
        return []


def list_lmstudio_models(endpoint: str | None = None, registry_path: Path | None = None) -> List[str]:
    """Discover models exposed by an LM Studio server and the local registry."""
    endpoint = endpoint or os.getenv("LMSTUDIO_ENDPOINT", "http://localhost:1234/v1/models")
    timeout = float(os.getenv("LMSTUDIO_DISCOVERY_TIMEOUT", "3.0"))
    models: List[str] = []

    try:
        import requests
    except ImportError as exc:  # pragma: no cover - production dependency
        logger.error("requests library is required for LM Studio discovery: %s", exc)
        requests = None

    if requests:
        try:
            response = requests.get(endpoint, timeout=timeout)
            response.raise_for_status()
            payload = response.json()

            if isinstance(payload, dict):
                raw_models = payload.get("data") or payload.get("models") or []
            else:
                raw_models = payload

            for item in raw_models:
                if isinstance(item, dict):
                    model_id = item.get("id") or item.get("name")
                    if model_id:
                        models.append(str(model_id))
                elif isinstance(item, str):
                    models.append(item)

            logger.info("Discovered %d LM Studio models from %s", len(models), endpoint)
        except Exception as exc:  # Broad catch to include JSON decode and request errors
            logger.warning("Failed to query LM Studio endpoint %s: %s", endpoint, exc)

    if not models:
        registry_entries = _load_model_registry_entries("lmstudio", registry_path)
        models.extend(entry["name"] for entry in registry_entries if entry.get("name"))

    unique_models = sorted({model for model in models if model})
    if not unique_models:
        logger.info("No LM Studio models detected from endpoint %s or registry", endpoint)

    return unique_models


def list_anthropic_models() -> List[str]:
    """Return the Anthropic models supported by Kari's production configuration."""
    return [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-2.1",
        "claude-instant-1.2",
    ]


def list_groq_models():
    """Return local Groq models under ``models/groq`` if present."""
    groq_dir = Path("models/groq")
    return [p.stem for p in groq_dir.glob("*.gguf")] if groq_dir.exists() else []


# === Final Aggregation ===

MODEL_PROVIDERS = {
    "llama-cpp": list_llama_cpp_models("models"),
    "lmstudio": list_lmstudio_models(),
    "gemini": list_gemini_models(),
    "anthropic": list_anthropic_models(),
    "groq": list_groq_models(),
    "mistral": ["mistral-small", "mistral-medium", "mistral-large"],
    "deepseek": ["deepseek-coder-6.7b", "deepseek-llm-7b"],
    "transformers": list_transformers_models(),
}
