"""Base classes and example providers for voice integrations."""

from __future__ import annotations

from typing import Any, Dict, List


class VoiceProviderBase:
    """Base interface for text-to-speech and speech-to-text providers."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or "default"

    def synthesize_speech(self, text: str, **kwargs: Any) -> bytes:  # pragma: no cover - abstract
        """Generate speech audio for the given text."""
        raise NotImplementedError

    def recognize_speech(self, audio: bytes, **kwargs: Any) -> str:  # pragma: no cover - abstract
        """Transcribe speech audio into text."""
        raise NotImplementedError

    def available_models(self) -> List[str]:
        """Return list of supported models for this provider."""
        return [self.model]


class DummyVoiceProvider(VoiceProviderBase):
    """Simple placeholder provider used for testing and demos."""

    def synthesize_speech(self, text: str, **kwargs: Any) -> bytes:
        return f"VOICE:{text}".encode()

    def recognize_speech(self, audio: bytes, **kwargs: Any) -> str:
        return audio.decode().replace("VOICE:", "")


__all__ = [
    "VoiceProviderBase",
    "DummyVoiceProvider",
]

