"""Registry for video and visual AI providers."""

from __future__ import annotations

from ai_karen_engine.integrations.provider_registry import ModelInfo, ProviderRegistry
from ai_karen_engine.integrations.video_providers import (
    DummyVideoProvider,
    OpenAIImageProvider,
    VideoProviderBase,
)


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

        self.register_provider(
            "openai",
            OpenAIImageProvider,
            description="OpenAI image generation models",
            models=[
                ModelInfo(
                    name="gpt-image-1",
                    description="Multi-modal image generation",
                    capabilities=["image-generation"],
                    default_settings={"size": "1024x1024"},
                )
            ],
            requires_api_key=True,
            default_model="gpt-image-1",
            category="VISUAL",
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
    "OpenAIImageProvider",
    "VideoRegistry",
    "get_video_registry",
]
