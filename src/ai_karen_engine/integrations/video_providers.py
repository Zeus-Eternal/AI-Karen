"""Production-ready providers for image and video generation."""

from __future__ import annotations

import base64
import logging
import os
from typing import Any, List

try:  # pragma: no cover - optional dependency typing helpers
    from openai import APIError, APIConnectionError, AuthenticationError, OpenAI, RateLimitError
except ImportError:  # pragma: no cover - fallback for alternate OpenAI versions
    from openai import OpenAI  # type: ignore

    APIError = APIConnectionError = AuthenticationError = RateLimitError = Exception  # type: ignore

logger = logging.getLogger(__name__)


class VideoProviderBase:
    """Base interface for image or video generation providers."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or "default"

    def generate_image(self, prompt: str, **kwargs: Any) -> bytes:  # pragma: no cover - abstract
        """Generate an image from a prompt."""
        raise NotImplementedError

    def generate_video(self, prompt: str, **kwargs: Any) -> bytes:  # pragma: no cover - abstract
        """Generate a video from a prompt."""
        raise NotImplementedError

    def available_models(self) -> List[str]:
        return [self.model]


class DummyVideoProvider(VideoProviderBase):
    """Placeholder provider used for demos and tests."""

    def generate_image(self, prompt: str, **kwargs: Any) -> bytes:
        return f"IMAGE:{prompt}".encode()

    def generate_video(self, prompt: str, **kwargs: Any) -> bytes:
        return f"VIDEO:{prompt}".encode()


class OpenAIImageProvider(VideoProviderBase):
    """Integration with OpenAI's image generation APIs."""

    def __init__(
        self,
        model: str | None = None,
        *,
        api_key: str | None = None,
        organization: str | None = None,
        base_url: str | None = None,
        timeout: float | None = 30.0,
        client: OpenAI | None = None,
        default_size: str = "1024x1024",
        response_format: str = "b64_json",
    ) -> None:
        super().__init__(model or "gpt-image-1")
        self.response_format = response_format
        self.default_size = default_size

        if client is not None:
            self._client = client
        else:
            resolved_key = api_key or os.getenv("OPENAI_API_KEY")
            if not resolved_key:
                raise ValueError(
                    "OpenAI API key must be provided via argument or OPENAI_API_KEY environment variable"
                )

            client_kwargs: dict[str, Any] = {"api_key": resolved_key}
            if organization or os.getenv("OPENAI_ORG_ID"):
                client_kwargs["organization"] = organization or os.getenv("OPENAI_ORG_ID")
            if base_url or os.getenv("OPENAI_BASE_URL"):
                client_kwargs["base_url"] = base_url or os.getenv("OPENAI_BASE_URL")
            if timeout is not None:
                client_kwargs["timeout"] = timeout

            self._client = OpenAI(**client_kwargs)

    def generate_image(
        self,
        prompt: str,
        *,
        size: str | None = None,
        quality: str | None = None,
        n: int = 1,
        **kwargs: Any,
    ) -> bytes:
        if not prompt:
            raise ValueError("Prompt must be provided for image generation")

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "n": n,
            "size": size or self.default_size,
            "response_format": self.response_format,
        }
        if quality is not None:
            payload["quality"] = quality
        payload.update(kwargs)

        try:
            response = self._client.images.generate(**payload)
        except (APIError, APIConnectionError, AuthenticationError, RateLimitError) as exc:  # pragma: no cover - network
            logger.error("OpenAI image generation failed: %s", exc)
            raise RuntimeError("OpenAI image generation request failed") from exc

        data_items = getattr(response, "data", None)
        if not data_items:
            if hasattr(response, "to_dict"):
                data_items = response.to_dict().get("data")
            elif isinstance(response, dict):
                data_items = response.get("data")

        if not data_items:
            raise RuntimeError("OpenAI image response did not include data items")

        first_item = data_items[0]
        encoded = getattr(first_item, "b64_json", None)
        if encoded is None and isinstance(first_item, dict):
            encoded = first_item.get("b64_json")

        if not encoded:
            raise RuntimeError("OpenAI image response missing base64 payload")

        return base64.b64decode(encoded)

    def generate_video(self, prompt: str, **kwargs: Any) -> bytes:
        raise RuntimeError("OpenAI image provider does not currently support video generation")

    def available_models(self) -> List[str]:
        return [self.model]


__all__ = [
    "VideoProviderBase",
    "DummyVideoProvider",
    "OpenAIImageProvider",
]

