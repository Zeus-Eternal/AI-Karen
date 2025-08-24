"""Local-first LLM client with optional remote/cloud routing.

This module provides a small utility for favouring local LLM providers
(e.g. TinyLLaMA via llama.cpp or an in-process Ollama model) while still
allowing callers to explicitly opt in to cloud based models.  When both
local and remote providers fail, a trivial fallback client is used to
guarantee a response.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from .protocols import LLMClient

log = logging.getLogger(__name__)


class FallbackLLM:
    """Trivial LLM used when all providers fail."""

    def __init__(self, message: str = "No providers available") -> None:
        self.message = message

    def generate(self, prompt: str, **_: Any) -> str:  # pragma: no cover - trivial
        return self.message


class ModelSelector:
    """Select which clients should be tried for a request.

    Parameters
    ----------
    local_client:
        Client that serves local models such as TinyLLaMA or Ollama.
    remote_client:
        Optional cloud based client.
    """

    def __init__(self, local_client: LLMClient, remote_client: Optional[LLMClient]) -> None:
        self.local_client = local_client
        self.remote_client = remote_client

    def ordered(self, cloud_enabled: bool) -> List[LLMClient]:
        """Return clients in the order they should be attempted."""

        order = [self.local_client]
        if cloud_enabled and self.remote_client is not None:
            order.append(self.remote_client)
        return order


class UnifiedLLMClient:
    """Route requests to local models with optional remote fallback."""

    def __init__(
        self,
        local_client: LLMClient,
        remote_client: Optional[LLMClient] = None,
        *,
        default_model: str = "default-local",
        fallback_client: Optional[LLMClient] = None,
        cloud_enabled: bool = False,
    ) -> None:
        self.selector = ModelSelector(local_client, remote_client)
        self.fallback_client = fallback_client or FallbackLLM()
        self.default_model = default_model
        self.cloud_enabled = cloud_enabled
        self._warmed = False

    def warmup(self) -> None:
        """Perform a lightweight generation to warm local models."""

        if not self._warmed:
            try:  # pragma: no cover - non-critical
                self.selector.local_client.generate("warmup")
            except Exception:
                pass
            self._warmed = True

    def generate(self, prompt: str, *, cloud: Optional[bool] = None, **kwargs: Any) -> str:
        """Generate a response from the selected model.

        Parameters
        ----------
        prompt:
            Prompt to send to the LLM.
        cloud:
            If ``True`` the remote/cloud model will be attempted after the
            local model fails.  By default cloud usage follows the setting
            provided at construction time.
        fallback_model:
            Optional name of the model to use when the remote provider is
            invoked.  This allows callers to specify different local and
            remote model identifiers.
        """

        self.warmup()
        kwargs.setdefault("model", self.default_model)
        fallback_model = kwargs.pop("fallback_model", None)
        cloud_enabled = self.cloud_enabled if cloud is None else cloud

        clients = self.selector.ordered(cloud_enabled)
        models = [kwargs["model"]]
        if len(clients) > 1:
            models.append(fallback_model or kwargs["model"])

        for client, model_name in zip(clients, models):
            call_kwargs = dict(kwargs)
            call_kwargs["model"] = model_name
            try:
                return client.generate(prompt, **call_kwargs)
            except Exception:  # pragma: no cover - simple retry logic
                continue

        log.warning("All LLM providers failed; using fallback client")
        final_kwargs = dict(kwargs)
        final_kwargs["model"] = fallback_model or kwargs["model"]
        return self.fallback_client.generate(prompt, **final_kwargs)
