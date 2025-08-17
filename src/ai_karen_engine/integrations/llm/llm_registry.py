from __future__ import annotations

"""LLM registry and router honoring user preferences."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ai_karen_engine.integrations.llm_registry import (
    LLMRegistry as GlobalRegistry,
    get_registry,
)

logger = logging.getLogger(__name__)


@dataclass
class InvocationResult:
    text: str
    meta: Dict[str, Any]


class LLMRegistry:
    """Simple registry coordinating multiple LLM providers."""

    def __init__(self, registry: Optional[GlobalRegistry] = None) -> None:
        self.registry = registry or get_registry()

    def default_chain(self, healthy_only: bool = True) -> List[str]:
        return self.registry.default_chain(healthy_only=healthy_only)

    async def invoke(
        self,
        prompt: str,
        task_intent: str,
        preferred_provider: str | None = None,
        preferred_model: str | None = None,
        **kwargs: Any,
    ) -> InvocationResult:
        """Invoke an LLM with fallback hierarchy."""
        order: List[str] = self.default_chain(healthy_only=True)
        if preferred_provider:
            order = [preferred_provider.lower()] + [p for p in order if p != preferred_provider.lower()]

        last_error: Optional[Exception] = None
        for name in order:
            provider = self.registry.get_provider(name)
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
        chain = self.default_chain(healthy_only=False)
        return chain[0] if chain else ""
