from __future__ import annotations

from typing import Dict, Iterable, Optional
from pathlib import Path
import os
import logging

# Configure logger
logger = logging.getLogger(__name__)

try:
    # Use the shared LLM helper from the same package
    from .llm_utils import LLMUtils
    from ..services.ollama_inprocess import generate as local_generate
    from ..services.deepseek_client import DeepSeekClient
except ImportError as e:
    logger.warning(f"Import error: {e}")
    
class LlamaCppWrapper:
    """Adapter exposing a generate_text method for llama-cpp."""

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = model_path or str(
            (Path.home() / ".ollama" / "models" / "llama3.gguf").expanduser()
        )

    def generate_text(self, prompt: str, max_tokens: int = 128) -> str:
        return local_generate(prompt, self.model_path, max_tokens=max_tokens)


class LLMRegistry:
    """Manage available LLM backends with a local-first default."""

    def __init__(self) -> None:
        self.backends: Dict[str, object] = {}

        # local HF/transformers backend is always available
        self.backends["local"] = LLMUtils()
        self.active = "local"

        # optional llama.cpp / ollama wrapper
        try:
            wrapper = LlamaCppWrapper()
        except Exception:
            pass
        else:
            self.backends["ollama_cpp"] = wrapper

        # optional OpenAI backend
        try:  # pragma: no cover - optional dep
            import openai  # type: ignore
        except Exception:
            pass
        else:
            class OpenAIWrapper:
                def generate_text(self, prompt: str, max_tokens: int = 128) -> str:
                    resp = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                    )
                    return resp.choices[0].message.content

            self.backends["openai"] = OpenAIWrapper()

        # optional DeepSeek backend
        if os.getenv("DEEPSEEK_API_KEY"):
            self.backends["deepseek"] = DeepSeekClient()

    def register(self, name: str, llm: object) -> None:
        self.backends[name] = llm

    def list_models(self) -> Iterable[str]:
        return self.backends.keys()

    def set_active(self, name: str) -> None:
        if name not in self.backends:
            raise KeyError(name)
        self.active = name

    def get_active(self) -> object:
        return self.backends[self.active]


registry = LLMRegistry()
