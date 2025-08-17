"""Registry for voice and audio providers."""

from __future__ import annotations

from ai_karen_engine.integrations.provider_registry import ModelInfo, ProviderRegistry
from ai_karen_engine.integrations.voice_providers import (
    DummyVoiceProvider,
    VoiceProviderBase,
)


class VoiceRegistry(ProviderRegistry):
    """Manage text-to-speech and speech-to-text providers."""

    def register_default_providers(self) -> None:
        """Register built-in voice providers."""
        self.register_provider(
            "dummy",
            DummyVoiceProvider,
            description="Example voice provider",
            models=[ModelInfo(name="dummy-voice")],
            requires_api_key=False,
            default_model="dummy-voice",
        )


# Global registry instance
_voice_registry: VoiceRegistry | None = None


def get_voice_registry() -> VoiceRegistry:
    """Get or create the global voice registry."""
    global _voice_registry
    if _voice_registry is None:
        _voice_registry = VoiceRegistry()
        _voice_registry.register_default_providers()
    return _voice_registry


__all__ = [
    "ModelInfo",
    "VoiceProviderBase",
    "DummyVoiceProvider",
    "VoiceRegistry",
    "get_voice_registry",
]
