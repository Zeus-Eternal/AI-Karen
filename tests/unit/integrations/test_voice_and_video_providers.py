"""Unit tests for production voice and video providers."""

from __future__ import annotations

import base64
import types

import pytest

from ai_karen_engine.integrations.video_providers import OpenAIImageProvider
from ai_karen_engine.integrations.voice_providers import OpenAIVoiceProvider
from ai_karen_engine.integrations.video_registry import get_video_registry
from ai_karen_engine.integrations.voice_registry import get_voice_registry


class _FakeSpeechResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload


class _FakeOpenAIAudioClient:
    def __init__(self, speech_payload: bytes, transcription_text: str) -> None:
        self._speech_payload = speech_payload
        self._transcription_text = transcription_text
        self.audio = types.SimpleNamespace(
            speech=types.SimpleNamespace(create=self._create_speech),
            transcriptions=types.SimpleNamespace(create=self._create_transcription),
        )
        self.last_speech_kwargs: dict[str, object] | None = None
        self.last_transcription_kwargs: dict[str, object] | None = None

    def _create_speech(self, **kwargs):  # type: ignore[override]
        self.last_speech_kwargs = kwargs
        return _FakeSpeechResponse(self._speech_payload)

    def _create_transcription(self, **kwargs):  # type: ignore[override]
        self.last_transcription_kwargs = kwargs
        return types.SimpleNamespace(text=self._transcription_text)


class _FakeImagesResponse:
    def __init__(self, encoded_payload: str) -> None:
        self.data = [types.SimpleNamespace(b64_json=encoded_payload)]


class _FakeOpenAIImageClient:
    def __init__(self, encoded_payload: str) -> None:
        self._encoded_payload = encoded_payload
        self.images = types.SimpleNamespace(generate=self._generate)
        self.last_kwargs: dict[str, object] | None = None

    def _generate(self, **kwargs):  # type: ignore[override]
        self.last_kwargs = kwargs
        return _FakeImagesResponse(self._encoded_payload)


def test_openai_voice_provider_uses_dependency_injection() -> None:
    client = _FakeOpenAIAudioClient(b"audio-bytes", "transcribed text")
    provider = OpenAIVoiceProvider(client=client)

    audio = provider.synthesize_speech("hello world", sample_rate=22_050)
    assert audio == b"audio-bytes"
    assert client.last_speech_kwargs is not None
    assert client.last_speech_kwargs["sample_rate"] == 22_050

    transcript = provider.recognize_speech(b"fake-bytes", language="en")
    assert transcript == "transcribed text"
    assert client.last_transcription_kwargs is not None
    assert client.last_transcription_kwargs["language"] == "en"
    assert provider.available_models() == ["gpt-4o-mini-tts", "gpt-4o-mini-transcribe"]


def test_openai_voice_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        OpenAIVoiceProvider()


def test_openai_image_provider_generates_bytes() -> None:
    payload = base64.b64encode(b"image-bytes").decode()
    client = _FakeOpenAIImageClient(payload)
    provider = OpenAIImageProvider(client=client)

    image = provider.generate_image("a futuristic control room", size="512x512")
    assert image == b"image-bytes"
    assert client.last_kwargs is not None
    assert client.last_kwargs["size"] == "512x512"
    assert provider.available_models() == ["gpt-image-1"]


def test_openai_image_provider_rejects_video_requests() -> None:
    payload = base64.b64encode(b"image-bytes").decode()
    provider = OpenAIImageProvider(client=_FakeOpenAIImageClient(payload))

    with pytest.raises(RuntimeError):
        provider.generate_video("render a cinematic sequence")


def test_registries_include_openai_providers() -> None:
    voice_registry = get_voice_registry()
    assert "openai" in voice_registry.list_providers("VOICE")

    video_registry = get_video_registry()
    assert "openai" in video_registry.list_providers("VISUAL")
