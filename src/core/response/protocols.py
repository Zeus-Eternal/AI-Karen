"""Protocol definitions for the response pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Protocol


class Analyzer(Protocol):
    """Analyzes user input to extract conversational signals."""

    def analyze(self, text: str) -> Dict[str, Any]:
        """Return structured analysis data for *text*."""


class Memory(Protocol):
    """Stores and retrieves conversational context."""

    def fetch_context(
        self, conversation_id: str, correlation_id: str | None = None
    ) -> List[str]:
        """Return a list of relevant context strings."""

    def store(
        self,
        conversation_id: str,
        user_input: str,
        response: str,
        correlation_id: str | None = None,
    ) -> None:
        """Persist the exchange for future retrieval."""


class LLMClient(Protocol):
    """Generates model responses from prompts."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Return a model-generated response for *prompt*."""
