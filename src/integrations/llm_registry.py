from __future__ import annotations

from typing import Dict, Iterable

from pathlib import Path

from .llm_utils import LLMUtils
from services.ollama_inprocess import generate as local_generate


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
        self.backends: Dict[str, object] = {
            "local": LLMUtils(),
            "ollama_cpp": LlamaCppWrapper(),
        }
        self.active = "local"

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
