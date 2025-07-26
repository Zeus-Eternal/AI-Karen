"""Registry for video and visual AI providers."""

from __future__ import annotations

from .provider_registry import ModelInfo, ProviderRegistry
from .video_providers import DummyVideoProvider, VideoProviderBase


class VideoRegistry(ProviderRegistry):
    """Manage image and video generation providers."""

    def register_default_providers(self) -> None:
        """Register built-in visual providers."""
        self.register_provider(
            "dummy",
            DummyVideoProvider,
            description="Example video provider",
            models=[ModelInfo(name="dummy-video")],
            requires_api_key=False,
            default_model="dummy-video",
        )


_video_registry: VideoRegistry | None = None


def get_video_registry() -> VideoRegistry:
    """Get or create the global video registry."""
    global _video_registry
    if _video_registry is None:
        _video_registry = VideoRegistry()
        _video_registry.register_default_providers()
    return _video_registry

__all__ = [
    "ModelInfo",
    "VideoProviderBase",
    "DummyVideoProvider",
    "VideoRegistry",
    "get_video_registry",
]
