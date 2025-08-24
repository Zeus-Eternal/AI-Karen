"""Primary-first LLM client with optional fallback."""
from __future__ import annotations

from typing import Any, Optional

from .protocols import LLMClient


class UnifiedLLMClient:
    """Attempt generation with a primary client before optional fallback."""

    def __init__(
        self,
        primary_client: LLMClient,
        fallback_client: Optional[LLMClient] = None,
    ) -> None:
        self.primary_client = primary_client
        self.fallback_client = fallback_client
        self._warmed = False

    def warmup(self) -> None:
        """Perform a lightweight generation to warm the primary client."""

        if not self._warmed:
            try:  # pragma: no cover - non-critical
                self.primary_client.generate("warmup")
            except Exception:
                pass
            self._warmed = True

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate using the primary client with fallback if it fails."""

        self.warmup()
        fallback_model = kwargs.pop("fallback_model", None)
        try:
            return self.primary_client.generate(prompt, **kwargs)
        except Exception:
            if self.fallback_client is not None:
                if fallback_model is not None:
                    kwargs["model"] = fallback_model
                return self.fallback_client.generate(prompt, **kwargs)
            raise
