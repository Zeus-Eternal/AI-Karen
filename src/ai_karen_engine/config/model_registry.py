import logging
import os
from pathlib import Path

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


def list_anthropic_models():
    """Return available Anthropic models (placeholder)."""
    return ["claude-3-opus-20240229", "claude-3-sonnet"]


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
