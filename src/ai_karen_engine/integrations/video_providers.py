"""Base classes and example providers for video and visual integrations."""

from __future__ import annotations

from typing import Any, Dict, List


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


__all__ = [
    "VideoProviderBase",
    "DummyVideoProvider",
]

