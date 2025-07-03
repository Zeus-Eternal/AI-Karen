from __future__ import annotations

from typing import Optional

from src.integrations.llm_registry import registry
from ai_karen_engine.clients.slm_pool import SLMPool


class LLMOrchestrator:
    """Route text generation to the smallest capable model."""

    def __init__(self, pool: SLMPool | None = None) -> None:
        self.pool = pool or SLMPool()
        self.default_llm = registry.get_active()

    def generate_text(self, prompt: str, *, skill: Optional[str] = None, max_tokens: int = 128) -> str:
        # first attempt: use a skill-specific SLM if available
        if skill:
            slm = self.pool.get(skill)
            if slm:
                return slm.generate_text(prompt, max_tokens=max_tokens)

        # otherwise pick any SLM that seems capable (naive length check)
        for slm in self.pool._models.values():
            if len(prompt.split()) <= max_tokens * 2:
                return slm.generate_text(prompt, max_tokens=max_tokens)

        if hasattr(self.default_llm, "generate_text"):
            return self.default_llm.generate_text(prompt, max_tokens=max_tokens)
        raise RuntimeError("No language model available")
