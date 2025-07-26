"""Registry for video and visual AI providers."""

from __future__ import annotations

from .provider_registry import ModelInfo, ProviderRegistry


class VideoRegistry(ProviderRegistry):
    """Manage image and video generation providers."""

    def register_default_providers(self) -> None:
        """Hook to register built-in visual providers."""
        # Placeholder for future built-in providers
        pass


_video_registry: VideoRegistry | None = None


def get_video_registry() -> VideoRegistry:
    """Get or create the global video registry."""
    global _video_registry
    if _video_registry is None:
        _video_registry = VideoRegistry()
        _video_registry.register_default_providers()
    return _video_registry

__all__ = ["ModelInfo", "VideoRegistry", "get_video_registry"]
