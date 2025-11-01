"""Production-grade voice provider implementations."""

from __future__ import annotations

import io
import logging
import math
import os
import wave
from typing import Any, List

import numpy as np

try:  # pragma: no cover - optional dependency typing helpers
    from openai import APIError, APIConnectionError, AuthenticationError, OpenAI, RateLimitError
except ImportError:  # pragma: no cover - fallback for alternate OpenAI versions
    from openai import OpenAI  # type: ignore

    APIError = APIConnectionError = AuthenticationError = RateLimitError = Exception  # type: ignore

logger = logging.getLogger(__name__)


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


class OpenAIVoiceProvider(VoiceProviderBase):
    """Production integration for OpenAI text-to-speech and transcription APIs."""

    def __init__(
        self,
        model: str | None = None,
        *,
        transcription_model: str | None = None,
        voice: str = "alloy",
        api_key: str | None = None,
        organization: str | None = None,
        base_url: str | None = None,
        timeout: float | None = 30.0,
        client: OpenAI | None = None,
    ) -> None:
        super().__init__(model or "gpt-4o-mini-tts")
        self.transcription_model = transcription_model or "gpt-4o-mini-transcribe"
        self.voice = voice

        if client is not None:
            self._client = client
        else:
            resolved_api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not resolved_api_key:
                raise ValueError(
                    "OpenAI API key must be provided via argument or OPENAI_API_KEY environment variable"
                )

            client_kwargs: dict[str, Any] = {"api_key": resolved_api_key}
            if organization or os.getenv("OPENAI_ORG_ID"):
                client_kwargs["organization"] = organization or os.getenv("OPENAI_ORG_ID")
            if base_url or os.getenv("OPENAI_BASE_URL"):
                client_kwargs["base_url"] = base_url or os.getenv("OPENAI_BASE_URL")
            if timeout is not None:
                client_kwargs["timeout"] = timeout

            self._client = OpenAI(**client_kwargs)

        self._last_tts_request: dict[str, Any] = {}
        self._last_stt_request: dict[str, Any] = {}

    def synthesize_speech(
        self,
        text: str,
        *,
        voice: str | None = None,
        format: str = "wav",
        sample_rate: int | None = None,
        speed: float | None = None,
        **kwargs: Any,
    ) -> bytes:
        if not text:
            raise ValueError("Text must be provided for synthesis")

        payload: dict[str, Any] = {
            "model": self.model,
            "voice": voice or self.voice,
            "input": text,
            "format": format,
        }
        if sample_rate is not None:
            payload["sample_rate"] = sample_rate
        if speed is not None:
            payload["speed"] = speed
        payload.update(kwargs)

        try:
            response = self._client.audio.speech.create(**payload)
            self._last_tts_request = payload
        except (APIError, APIConnectionError, AuthenticationError, RateLimitError) as exc:  # pragma: no cover - network
            logger.error("OpenAI speech synthesis failed: %s", exc)
            raise RuntimeError("OpenAI speech synthesis request failed") from exc

        if hasattr(response, "read"):
            return response.read()
        if hasattr(response, "content") and isinstance(response.content, (bytes, bytearray)):
            return bytes(response.content)

        # Fall back to dict representation for older SDKs
        if hasattr(response, "to_dict"):
            data = response.to_dict()
        elif isinstance(response, dict):
            data = response
        else:  # pragma: no cover - defensive
            raise RuntimeError("Unexpected OpenAI speech response format")

        audio_data = data.get("data") or data.get("audio") or data.get("content")
        if isinstance(audio_data, (bytes, bytearray)):
            return bytes(audio_data)
        if isinstance(audio_data, str):
            return audio_data.encode()

        raise RuntimeError("OpenAI speech response did not include audio payload")

    def recognize_speech(
        self,
        audio: bytes,
        *,
        language: str | None = None,
        response_format: str = "text",
        **kwargs: Any,
    ) -> str:
        if not audio:
            raise ValueError("Audio payload is empty")

        audio_buffer = io.BytesIO(audio)
        audio_buffer.name = kwargs.pop("filename", "speech.wav")

        payload: dict[str, Any] = {
            "model": self.transcription_model,
            "file": audio_buffer,
            "response_format": response_format,
        }
        if language:
            payload["language"] = language
        payload.update(kwargs)

        try:
            result = self._client.audio.transcriptions.create(**payload)
            self._last_stt_request = payload
        except (APIError, APIConnectionError, AuthenticationError, RateLimitError) as exc:  # pragma: no cover - network
            logger.error("OpenAI transcription failed: %s", exc)
            raise RuntimeError("OpenAI transcription request failed") from exc

        if isinstance(result, str):
            return result
        if hasattr(result, "text"):
            return result.text
        if hasattr(result, "to_dict"):
            data = result.to_dict()
        elif isinstance(result, dict):
            data = result
        else:  # pragma: no cover - defensive
            raise RuntimeError("Unexpected OpenAI transcription response format")

        if "text" in data and isinstance(data["text"], str):
            return data["text"]

        raise RuntimeError("OpenAI transcription response did not include text output")

    def available_models(self) -> List[str]:
        return [self.model, self.transcription_model]


__all__ = [
    "VoiceProviderBase",
    "DummyVoiceProvider",
    "OpenAIVoiceProvider",
]

