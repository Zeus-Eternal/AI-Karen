from __future__ import annotations

"""First-party vLLM runtime wrapper.

The API container should not depend on vLLM at import time. This adapter keeps
the runtime boundary stable while allowing a vLLM server to be configured as a
normal OpenAI-compatible endpoint.
"""

import os
from typing import Any, Dict, Iterator, List, Optional

from ai_karen_engine.core.model_runtime.model_manager import ModelManager
from ai_karen_engine.integrations.providers.openai_compatible_provider import (
    OpenAICompatibleProvider,
)


class VLLMRuntime:
    """Neutral wrapper around an OpenAI-compatible vLLM endpoint."""

    _instance: Optional["VLLMRuntime"] = None

    def __init__(
        self,
        model: str = "auto",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_key_env: Optional[str] = None,
        provider_name: str = "builtin_vllm",
    ) -> None:
        self.model = model
        self.base_url = (base_url or os.getenv("VLLM_BASE_URL") or "").strip() or None
        key = api_key
        if key is None and api_key_env:
            key = (os.getenv(api_key_env) or "").strip() or None
        if key is None:
            key = (os.getenv("VLLM_API_KEY") or "").strip() or None
        self.api_key = key
        self.provider_name = provider_name
        self._provider = OpenAICompatibleProvider(
            model=model,
            base_url=self.base_url,
            api_key=self.api_key,
            provider_name=provider_name,
        )
        self._provider.provider_name = provider_name
        self._provider.display_name = "vLLM"

    @classmethod
    def get_instance(cls, **kwargs: Any) -> "VLLMRuntime":
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    def health_check(self) -> Dict[str, Any]:
        status = self._provider.health_check()
        status["provider"] = self.provider_name
        status["runtime"] = "vllm"
        return status

    def load_model(self, model_path: Optional[str] = None) -> bool:
        if model_path:
            self.model = model_path
        return True

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return ModelManager.invoke_provider_sync(self._provider, prompt, **kwargs)

    def generate_response(self, prompt: str, **kwargs: Any) -> str:
        return ModelManager.invoke_provider_sync(self._provider, prompt, **kwargs)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        yield from ModelManager.stream_provider_sync(self._provider, prompt, **kwargs)

    def stream_generate(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        yield from ModelManager.stream_provider_sync(self._provider, prompt, **kwargs)

    def embed(self, text: str, **kwargs: Any) -> List[float]:
        return ModelManager.invoke_embedding_sync(self._provider, text, **kwargs)


__all__ = ["VLLMRuntime"]
