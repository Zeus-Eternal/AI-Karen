"""
Adapter that exposes a small in-process llama.cpp client matching the legacy
``llamacpp_inprocess_client`` surface expected by the lightweight LM services.

This module wraps ``ai_karen_engine.inference.llamacpp_runtime.LlamaCppRuntime``
to provide ``load_model``, ``chat``, and ``health_check`` helpers with a very
simple prompt formatter so the services code can remain unchanged.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional

from ai_karen_engine.inference.llamacpp_runtime import LlamaCppRuntime

logger = logging.getLogger(__name__)


class _LlamaCppInProcessClient:
    """Minimal wrapper around ``LlamaCppRuntime`` that exposes the expected API."""

    def __init__(self) -> None:
        self._runtime: Optional[LlamaCppRuntime] = None
        self._model_path: Optional[str] = None

    def _ensure_runtime(self) -> LlamaCppRuntime:
        if self._runtime is None:
            if not LlamaCppRuntime.is_available():
                raise RuntimeError("llama-cpp-python is not available")
            self._runtime = LlamaCppRuntime()
        return self._runtime

    @staticmethod
    def _render_conversation(messages: Iterable[Dict[str, Any]]) -> str:
        lines: List[str] = []
        for message in messages:
            role = str(message.get("role", "user")).strip()
            content = str(message.get("content", "")).strip()
            if not content:
                continue
            if role.lower() == "system":
                lines.append(f"System: {content}")
            else:
                lines.append(f"{role.capitalize()}: {content}")
        lines.append("Assistant:")
        return "\n".join(lines).strip()

    def load_model(self, model_path: str) -> Dict[str, Any]:
        """Load a GGUF model through the underlying runtime."""
        runtime = self._ensure_runtime()
        logger.debug("Loading llama.cpp model at %s", model_path)
        try:
            loaded = runtime.load_model(model_path)
        except Exception as error:
            logger.error("Failed to load model %s: %s", model_path, error)
            return {"status": "error", "error": str(error)}

        if loaded:
            self._model_path = model_path
            return {"status": "success"}

        return {"status": "error", "error": f"Failed to load model: {model_path}"}

    def chat(
        self,
        messages: Iterable[Dict[str, Any]],
        *,
        max_tokens: int = 256,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs: Any,
    ) -> str:
        """Generate a single response from the in-process runtime."""
        runtime = self._ensure_runtime()
        prompt = self._render_conversation(messages)
        if not prompt:
            prompt = "Assistant:"

        response = runtime.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream,
            **kwargs,
        )

        if stream and isinstance(response, Iterable) and not isinstance(response, str):
            return "".join(str(chunk) for chunk in response)

        return response if isinstance(response, str) else str(response)

    def health_check(self) -> Dict[str, Any]:
        """Proxy the runtime health check and annotate the result."""
        runtime = self._ensure_runtime()
        status = runtime.health_check()
        status.setdefault("client", "llamacpp_inprocess")
        status.setdefault("model_path", self._model_path)
        return status


llamacpp_inprocess_client = _LlamaCppInProcessClient()

__all__ = ["llamacpp_inprocess_client"]
