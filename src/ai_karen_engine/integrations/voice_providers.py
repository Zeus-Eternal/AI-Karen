"""Base classes and concrete providers for voice integrations."""

from __future__ import annotations

import io
import math
import wave
from typing import Any, List

import numpy as np


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
    """Deterministic sine-wave synthesiser used for local validation flows."""

    def __init__(self, model: str | None = None) -> None:
        super().__init__(model)
        self._default_sample_rate = 16_000

    def synthesize_speech(
        self,
        text: str,
        *,
        sample_rate: int | None = None,
        amplitude: float = 0.35,
        base_frequency: float | None = None,
        **_: Any,
    ) -> bytes:
        """Generate a short sine-wave clip that encodes the requested text length."""

        if not text:
            raise ValueError("Text must be provided for synthesis")

        sample_rate = sample_rate or self._default_sample_rate
        amplitude = max(0.05, min(amplitude, 0.95))

        # Scale clip duration with the amount of text so that long prompts
        # produce longer audio.  Cap to keep the demo snappy.
        token_count = max(1, len(text.split()))
        duration = min(8.0, 0.45 * token_count)

        # Modulate the carrier frequency using a deterministic hash of the text
        # so that different prompts sound distinct without needing any external
        # TTS dependencies.
        base_frequency = base_frequency or 180 + (hash(text) % 220)

        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        waveform = np.sin(2 * math.pi * base_frequency * t)

        # Apply a simple raised-cosine envelope to avoid pops at the edges and
        # multiply by amplitude for volume control.
        envelope = np.sin(math.pi * np.linspace(0, 1, waveform.size)) ** 2
        audio = (waveform * envelope * amplitude * 32767).astype(np.int16)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio.tobytes())

        return buffer.getvalue()

    def recognize_speech(self, audio: bytes, **_: Any) -> str:
        """Return a diagnostic summary of the supplied audio payload."""

        if not audio:
            raise ValueError("Audio payload is empty")

        with wave.open(io.BytesIO(audio), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            frames = wav_file.readframes(wav_file.getnframes())

        samples = np.frombuffer(frames, dtype=np.int16)
        if samples.size == 0 or sample_rate <= 0:
            return "Empty audio stream"

        duration = samples.size / sample_rate
        mean_amplitude = float(np.abs(samples).mean()) / 32767

        zero_crossings = np.where(np.diff(np.signbit(samples)))[0]
        if zero_crossings.size > 1:
            periods = np.diff(zero_crossings) / sample_rate
            dominant_frequency = 1.0 / (2 * periods.mean()) if periods.size else 0.0
        else:
            dominant_frequency = 0.0

        return (
            "Synthetic sine-wave audio detected "
            f"(duration={duration:.2f}s, mean_amplitude={mean_amplitude:.2f}, "
            f"dominant_frequency={dominant_frequency:.0f}Hz)."
        )


__all__ = [
    "VoiceProviderBase",
    "DummyVoiceProvider",
]

