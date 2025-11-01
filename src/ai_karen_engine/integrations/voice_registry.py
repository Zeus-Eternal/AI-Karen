"""Registry for voice and audio providers."""

from __future__ import annotations

from ai_karen_engine.integrations.provider_registry import ModelInfo, ProviderRegistry
from ai_karen_engine.integrations.voice_providers import (
    DummyVoiceProvider,
    OpenAIVoiceProvider,
    VoiceProviderBase,
)


class VoiceRegistry(ProviderRegistry):
    """Manage text-to-speech and speech-to-text providers."""

    def register_default_providers(self) -> None:
        """Register built-in voice providers."""
        self.register_provider(
            "dummy",
            DummyVoiceProvider,
            description="Deterministic offline synthesiser for smoke tests and QA",
            models=[
                ModelInfo(
                    name="sine-demo",
                    description="Lightweight sine-wave generator",
                    capabilities=["text-to-speech", "waveform-analysis"],
                    default_settings={"sample_rate": 16_000},
                )
            ],
            requires_api_key=False,
            default_model="sine-demo",
            category="VOICE",
        )

        self.register_provider(
            "openai",
            OpenAIVoiceProvider,
            description="OpenAI neural text-to-speech and speech-to-text",
            models=[
                ModelInfo(
                    name="gpt-4o-mini-tts",
                    description="Low-latency neural text-to-speech",
                    capabilities=["text-to-speech"],
                    default_settings={"voice": "alloy"},
                ),
                ModelInfo(
                    name="gpt-4o-mini-transcribe",
                    description="Streaming transcription model",
                    capabilities=["speech-to-text"],
                    default_settings={"response_format": "text"},
                ),
            ],
            requires_api_key=True,
            default_model="gpt-4o-mini-tts",
            category="VOICE",
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
    "OpenAIVoiceProvider",
    "VoiceRegistry",
    "get_voice_registry",
]
