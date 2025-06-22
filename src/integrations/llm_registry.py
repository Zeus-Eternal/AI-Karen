from __future__ import annotations

from typing import Dict, Iterable

from .llm_utils import LLMUtils


class LLMRegistry:
    """Manage available LLM backends with a local-first default."""

    def __init__(self) -> None:
        self.backends: Dict[str, object] = {"local": LLMUtils()}
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
