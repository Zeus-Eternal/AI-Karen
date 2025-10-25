"""Simple deterministic fallback provider for offline environments.

This provider acts as a safety net when no networked or heavy-weight LLM
backends are available.  It produces lightweight, helpful responses without
external dependencies so that the rest of the Kari stack can continue to
operate (for smoke tests, demos, or degraded modes).
"""

from __future__ import annotations

import hashlib
import logging
import textwrap
from datetime import datetime
from typing import Any, Dict, Iterable, Iterator, List

from ai_karen_engine.integrations.llm_utils import (
    EmbeddingFailed,
    GenerationFailed,
    LLMProviderBase,
    record_llm_metric,
)

logger = logging.getLogger("kari.fallback_provider")


class FallbackProvider(LLMProviderBase):
    """Deterministic provider that keeps Kari responsive without real LLMs.

    The goal is graceful degradation: when "real" providers are unavailable the
    fallback still returns a contextual acknowledgement so that the UI and
    downstream services can verify the full request/response loop.
    """

    def __init__(
        self,
        model: str = "kari-fallback-v1",
        max_history: int = 5,
        **_: Any,
    ) -> None:
        self.model = model
        self.max_history = max_history
        self._history: List[str] = []
        self.last_usage: Dict[str, Any] = {}
        self.provider_name = "fallback"

    # ------------------------------------------------------------------
    # Core helpers
    def _summarize_prompt(self, prompt: str) -> str:
        """Create a compact summary snippet for the prompt."""

        cleaned = " ".join(prompt.strip().split())
        if not cleaned:
            return "an empty prompt"

        words = cleaned.split(" ")
        if len(words) <= 16:
            return cleaned

        # Generate a deterministic checksum fragment so responses are stable
        digest = hashlib.sha1(cleaned.encode("utf-8")).hexdigest()[:6]
        preview = " ".join(words[:16])
        return f"{preview}… (ref:{digest})"

    def _build_suggestions(self, prompt: str) -> List[str]:
        """Generate a couple of lightweight follow-up suggestions."""

        topics = [
            "analysis",
            "planning",
            "next steps",
            "limitations",
            "validation",
        ]
        # Deterministic shuffle based on prompt hash for variety without RNG drift
        digest = hashlib.md5(prompt.encode("utf-8")).hexdigest()
        start = int(digest[:8], 16)
        ordered = topics[start % len(topics) :] + topics[: start % len(topics)]
        return [f"Explore {topic}." for topic in ordered[:2]]

    # ------------------------------------------------------------------
    # LLMProviderBase interface
    def generate_text(self, prompt: str, **kwargs: Any) -> str:  # type: ignore[override]
        """Try to use real LLM first, fall back to deterministic response if needed."""

        start = datetime.utcnow()
        
        # Try to use the real llamacpp provider first
        try:
            from ai_karen_engine.integrations.llm_registry import get_registry
            registry = get_registry()
            llamacpp_provider = registry.get_provider("llamacpp")
            
            if llamacpp_provider:
                # Try to generate with the real llamacpp provider
                real_response = llamacpp_provider.generate_text(prompt, **kwargs)
                if real_response and len(real_response.strip()) > 0:
                    logger.info("FallbackProvider successfully used real llamacpp provider")
                    
                    # Calculate usage for the real response
                    duration = (datetime.utcnow() - start).total_seconds()
                    token_estimate = max(1, len(prompt.split()))
                    completion_tokens = max(1, len(real_response.split()))
                    self.last_usage = {
                        "prompt_tokens": token_estimate,
                        "completion_tokens": completion_tokens,
                        "total_tokens": token_estimate + completion_tokens,
                        "cost": 0.0,
                    }
                    
                    record_llm_metric("generate_text", duration, True, "fallback_with_real_llm")
                    return real_response
        except Exception as e:
            logger.debug(f"FallbackProvider could not use real LLM: {e}")
        
        # Fall back to deterministic response
        prompt_summary = self._summarize_prompt(prompt)

        self._history.append(prompt_summary)
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history :]

        suggestions = self._build_suggestions(prompt)
        response = textwrap.dedent(
            f"""
            Hello! I'm Kari's fallback assistant ({self.model}).
            I received your message about: {prompt_summary}.

            Here's a concise next step you can take right now:
            - {suggestions[0]}

            Another idea to continue the work:
            - {suggestions[1]}

            Let me know if you'd like me to expand on any part of this topic.
            """
        ).strip()

        duration = (datetime.utcnow() - start).total_seconds()
        token_estimate = max(1, len(prompt.split()))
        self.last_usage = {
            "prompt_tokens": token_estimate,
            "completion_tokens": max(1, len(response.split()) // 2),
            "total_tokens": token_estimate + max(1, len(response.split()) // 2),
            "cost": 0.0,
        }

        record_llm_metric("generate_text", duration, True, "fallback")
        logger.debug("FallbackProvider returning deterministic response")
        return response

    # The orchestrator prefers providers exposing ``generate_response`` (and
    # sometimes ``enhanced_generate_response``) so mirror ``generate_text`` to
    # keep compatibility with richer providers without duplicating logic.
    def generate_response(self, prompt: str, **kwargs: Any) -> str:  # type: ignore[override]
        return self.generate_text(prompt, **kwargs)

    def enhanced_generate_response(self, prompt: str, **kwargs: Any) -> str:  # type: ignore[override]
        return self.generate_text(prompt, **kwargs)

    def stream_generate(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Provide a very small streaming-compatible generator."""

        try:
            result = self.generate_text(prompt, **kwargs)
        except GenerationFailed as exc:  # pragma: no cover - defensive
            raise exc

        for chunk in textwrap.wrap(result, 80):
            yield chunk

    def embed(self, text: Any, **kwargs: Any) -> List[float]:  # type: ignore[override]
        """Produce a deterministic pseudo-embedding vector."""

        if isinstance(text, str):
            values = text
        elif isinstance(text, Iterable):
            values = " ".join(str(item) for item in text)
        else:
            raise EmbeddingFailed("Unsupported input type for fallback embeddings")

        digest = hashlib.sha1(values.encode("utf-8")).digest()
        # Create a small deterministic vector in range [-1, 1]
        vector = [((b / 255.0) * 2) - 1 for b in digest[:32]]
        if not vector:
            raise EmbeddingFailed("Unable to generate embedding")
        return vector

    def warm_cache(self) -> None:  # type: ignore[override]
        """Nothing to warm, but keep interface parity."""

        logger.debug("FallbackProvider warm_cache invoked - no action needed")

    # ------------------------------------------------------------------
    # Metadata helpers
    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "name": "fallback",
            "model": self.model,
            "supports_streaming": False,
            "supports_embeddings": True,
            "description": "Deterministic offline fallback provider",
        }

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "message": "Fallback provider operational",
            "checked_at": datetime.utcnow().isoformat(),
        }


__all__ = ["FallbackProvider"]

