from __future__ import annotations

from typing import Dict, Iterable, Optional

from ai_karen_engine.integrations.llm_utils import LLMUtils


class SLMPool:
    """Manage a set of small language models keyed by skill."""

    def __init__(self) -> None:
        self._models: Dict[str, LLMUtils] = {}

    def register(self, skill: str, model: LLMUtils) -> None:
        """Register a model for a given skill."""
        self._models[skill] = model

    def get(self, skill: str) -> Optional[LLMUtils]:
        """Return the model registered for ``skill`` if present."""
        return self._models.get(skill)

    def skills(self) -> Iterable[str]:
        """Return all known skills."""
        return self._models.keys()
