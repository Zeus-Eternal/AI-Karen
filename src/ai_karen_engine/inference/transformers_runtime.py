from __future__ import annotations

"""Neutral local runtime backed by optional Transformers support."""

import logging
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

logger = logging.getLogger(__name__)


def _lazy_import_transformers() -> bool:
    try:
        import transformers  # noqa: F401
        return True
    except Exception:
        return False


class TransformersRuntime:
    """Best-effort local text runtime with a deterministic fallback path."""

    _instance: Optional["TransformersRuntime"] = None

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "auto",
        torch_dtype: str = "auto",
        quantization: Optional[str] = None,
        use_flash_attention: bool = False,
        **kwargs: Any,
    ) -> None:
        self.model_path = model_path
        self.device = device
        self.torch_dtype = torch_dtype
        self.quantization = quantization
        self.use_flash_attention = use_flash_attention
        self.options = dict(kwargs)
        self._transformers_available = _lazy_import_transformers()
        self._model_name = self._resolve_model_name(model_path)

        if not self._transformers_available:
            logger.info("Transformers not installed; using deterministic fallback runtime")

    @staticmethod
    def _resolve_model_name(model_path: Optional[str]) -> str:
        if not model_path:
            return "auto"
        return Path(model_path).name or "auto"

    @classmethod
    def get_instance(cls, **kwargs: Any) -> "TransformersRuntime":
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "available",
            "model_path": self.model_path,
            "model": self._model_name,
            "transformers_available": self._transformers_available,
        }

    def load_model(self, model_path: Optional[str] = None) -> bool:
        if model_path:
            self.model_path = model_path
            self._model_name = self._resolve_model_name(model_path)
        return True

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return self._fallback_generate(prompt, **kwargs)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        for token in self._fallback_generate(prompt, **kwargs).split():
            yield token

    def generate_response(self, prompt: str, **kwargs: Any) -> str:
        return self._fallback_generate(prompt, **kwargs)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model": self._model_name,
            "device": self.device,
            "quantization": self.quantization,
            "transformers_available": self._transformers_available,
        }

    def shutdown(self) -> None:
        logger.info("Shutting down Transformers runtime")

    def _fallback_generate(self, prompt: str, **kwargs: Any) -> str:
        prompt = (prompt or "").strip()
        if not prompt:
            return "No prompt provided."

        if self._transformers_available:
            return f"[transformers:{self._model_name}] {prompt}"

        return f"[local-fallback:{self._model_name}] {prompt}"


__all__ = ["TransformersRuntime"]
