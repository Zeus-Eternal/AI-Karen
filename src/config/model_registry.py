import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# === Dynamic Model Providers ===

def list_llama_cpp_models(models_dir="/models"):
    """
    Scan for GGUF/llama.cpp compatible models
    """
    supported_ext = {".gguf", ".bin"}
    models = []

    try:
        for file in Path(models_dir).iterdir():
            if file.is_file() and file.suffix in supported_ext:
                models.append(file.stem)
    except Exception as e:
        logger.warning(f"[llama-cpp] Failed to list models: {e}")

    return models or ["<no-models-found>"]


def list_transformers_models():
    """
    Return known local transformers models or fine-tuned ones
    """
    return ["gpt2", "bert-base", "custom-finetune"]


def list_ollama_models():
    """
    Attempt to list Ollama models locally — no `ollama serve` required.
    Parses from ~/.ollama/models or equivalent.
    """
    ollama_path = Path.home() / ".ollama" / "models"
    models = []

    try:
        if ollama_path.exists():
            for file in ollama_path.rglob("*.bin"):
                models.append(file.stem)
    except Exception as e:
        logger.warning(f"[ollama] Failed to fetch models: {e}")

    return models or ["<no-ollama-models>"]


def list_gemini_models():
    # Placeholder for Gemini dynamic API fetch (if available)
    return ["gemini-pro", "gemini-1.5-pro"]


def list_lmstudio_models():
    # TODO: Ping local REST on `http://localhost:1234/v1/models`
    return ["lmstudio-api-models"]


# === Final Aggregation ===

MODEL_PROVIDERS = {
    "llama-cpp": list_llama_cpp_models("/models"),
    "ollama": list_ollama_models(),
    "transformers": list_transformers_models(),
    "lmstudio": list_lmstudio_models(),
    "gemini": list_gemini_models(),
    "claude": ["claude-3-opus-20240229"],
    "deepseek": ["deepseek-coder-6.7b", "deepseek-llm-7b"],
    "mistral": ["mistral-small", "mistral-medium", "mistral-large"],
}
