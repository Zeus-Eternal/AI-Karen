"""Local-first LLM client with optional remote fallback."""
from __future__ import annotations

from typing import Any, Optional

from .protocols import LLMClient


class FallbackLLM:
    """Trivial LLM used when all providers fail."""

    def __init__(self, message: str = "No providers available") -> None:
        self.message = message

    def generate(self, prompt: str, **_: Any) -> str:  # pragma: no cover - trivial
        return self.message


class UnifiedLLMClient:
    """Route requests to local models with optional remote fallback."""

    def __init__(
        self,
        local_client: LLMClient,
        remote_client: Optional[LLMClient] = None,
        *,
        default_model: str = "default-local",
        fallback_client: Optional[LLMClient] = None,
    ) -> None:
        self.local_client = local_client
        self.remote_client = remote_client
        self.fallback_client = fallback_client or FallbackLLM()
        self.default_model = default_model
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
        kwargs.setdefault("model", self.default_model)
        try:
            return self.local_client.generate(prompt, **kwargs)
        except Exception:
            if self.remote_client is not None:
                try:
                    return self.remote_client.generate(prompt, **kwargs)
                except Exception:
                    pass
            return self.fallback_client.generate(prompt, **kwargs)
