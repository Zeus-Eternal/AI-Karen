from __future__ import annotations

"""LLM registry and router honoring user preferences."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ai_karen_engine.integrations.providers.deepseek_provider import (  # type: ignore[import-not-found]
    DeepseekProvider,
)
from ai_karen_engine.integrations.providers.gemini_provider import (  # type: ignore[import-not-found]
    GeminiProvider,
)
from ai_karen_engine.integrations.providers.huggingface_provider import (  # type: ignore[import-not-found]
    HuggingFaceProvider,
)
from ai_karen_engine.integrations.providers.ollama_provider import (  # type: ignore[import-not-found]
    OllamaProvider,
)
from ai_karen_engine.integrations.providers.openai_provider import (  # type: ignore[import-not-found]
    OpenAIProvider,
)

logger = logging.getLogger(__name__)


@dataclass
class InvocationResult:
    text: str
    meta: Dict[str, Any]


class LLMRegistry:
    """Simple registry coordinating multiple LLM providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, Any] = {
            "ollama": OllamaProvider(),
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
            "deepseek": DeepseekProvider(),
            "huggingface": HuggingFaceProvider(),
        }
        self._order = ["ollama", "openai", "gemini", "deepseek", "huggingface"]

    async def invoke(
        self,
        prompt: str,
        task_intent: str,
        preferred_provider: str | None = None,
        preferred_model: str | None = None,
        **kwargs: Any,
    ) -> InvocationResult:
        """Invoke an LLM with fallback hierarchy."""
        order: List[str] = []
        if preferred_provider:
            order.append(preferred_provider.lower())
        order.extend([p for p in self._order if p not in order])

        last_error: Optional[Exception] = None
        for name in order:
            provider = self._providers.get(name)
            if not provider:
                continue
            model = (
                preferred_model
                if preferred_provider
                and name == preferred_provider.lower()
                and preferred_model
                else getattr(provider, "model", "")
            )
            start = time.perf_counter()
            try:
                text = await asyncio.to_thread(
                    provider.generate_text, prompt, model=model, **kwargs
                )
                latency = int((time.perf_counter() - start) * 1000)
                meta = {"provider": name.title(), "model": model, "latency_ms": latency}
                return InvocationResult(text=text, meta=meta)
            except Exception as exc:  # pragma: no cover - provider failure
                last_error = exc
                logger.warning("Provider %s failed: %s", name, exc)
                continue
        raise RuntimeError("All providers failed") from last_error

    def select_provider(self, task_intent: str) -> str:
        """Return default provider based on intent (currently static)."""
        return self._order[0]
