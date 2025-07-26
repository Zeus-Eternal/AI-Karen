"""Registry for voice and audio providers."""

from __future__ import annotations

from .provider_registry import ModelInfo, ProviderRegistry


class VoiceRegistry(ProviderRegistry):
    """Manage text-to-speech and speech-to-text providers."""

    def register_default_providers(self) -> None:
        """Hook to register built-in voice providers."""
        # Placeholder for future built-in providers
        pass


# Global registry instance
_voice_registry: VoiceRegistry | None = None


def get_voice_registry() -> VoiceRegistry:
    """Get or create the global voice registry."""
    global _voice_registry
    if _voice_registry is None:
        _voice_registry = VoiceRegistry()
        _voice_registry.register_default_providers()
    return _voice_registry

__all__ = ["ModelInfo", "VoiceRegistry", "get_voice_registry"]
