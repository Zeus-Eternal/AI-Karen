"""Local-first LLM client with optional remote fallback."""
from __future__ import annotations

from typing import Any, Optional

from .protocols import LLMClient


class UnifiedLLMClient:
    """Route requests to local models with optional remote fallback."""

    def __init__(
        self,
        local_client: LLMClient,
        remote_client: Optional[LLMClient] = None,
    ) -> None:
        self.local_client = local_client
        self.remote_client = remote_client
        self._warmed = False

    def warmup(self) -> None:
        """Perform a lightweight generation to warm local models."""

        if not self._warmed:
            try:  # pragma: no cover - non-critical
                self.local_client.generate("warmup")
            except Exception:
                pass
            self._warmed = True

    def generate(self, prompt: str, **kwargs: Any) -> str:
        self.warmup()
        try:
            return self.local_client.generate(prompt, **kwargs)
        except Exception:
            if self.remote_client is not None:
                return self.remote_client.generate(prompt, **kwargs)
            raise
