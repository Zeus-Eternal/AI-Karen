"""Integration helpers for Kari AI (compatibility wrappers)."""

__all__ = [
    "AutomationManager",
    "LocalRPAClient",
    "LLMProfileRouter",
    "ProviderRegistry",
    "ModelInfo",
    "get_provider_registry",
    "VoiceRegistry",
    "VoiceProviderBase",
    "DummyVoiceProvider",
    "OpenAIVoiceProvider",
    "get_voice_registry",
    "VideoRegistry",
    "VideoProviderBase",
    "DummyVideoProvider",
    "OpenAIImageProvider",
    "get_video_registry",
]


def __getattr__(name):
    if name == "AutomationManager":
        from ai_karen_engine.integrations.automation_manager import AutomationManager as _AutomationManager

        return _AutomationManager
    if name == "LocalRPAClient":
        from ai_karen_engine.integrations.local_rpa_client import LocalRPAClient as _LocalRPAClient

        return _LocalRPAClient
    if name == "LLMProfileRouter":
        from ai_karen_engine.integrations.llm_router import LLMProfileRouter as _LLMProfileRouter

        return _LLMProfileRouter
    if name in {"ProviderRegistry", "ModelInfo", "get_provider_registry"}:
        from ai_karen_engine.integrations.provider_registry import (
            ProviderRegistry as _ProviderRegistry,
            ModelInfo as _ModelInfo,
            get_provider_registry as _get_provider_registry,
        )

        return {
            "ProviderRegistry": _ProviderRegistry,
            "ModelInfo": _ModelInfo,
            "get_provider_registry": _get_provider_registry,
        }[name]
    if name in {
        "VoiceRegistry",
        "VoiceProviderBase",
        "DummyVoiceProvider",
        "OpenAIVoiceProvider",
        "get_voice_registry",
    }:
        from ai_karen_engine.integrations.voice_registry import (
            VoiceRegistry as _VoiceRegistry,
            VoiceProviderBase as _VoiceProviderBase,
            DummyVoiceProvider as _DummyVoiceProvider,
            OpenAIVoiceProvider as _OpenAIVoiceProvider,
            get_voice_registry as _get_voice_registry,
        )

        return {
            "VoiceRegistry": _VoiceRegistry,
            "VoiceProviderBase": _VoiceProviderBase,
            "DummyVoiceProvider": _DummyVoiceProvider,
            "OpenAIVoiceProvider": _OpenAIVoiceProvider,
            "get_voice_registry": _get_voice_registry,
        }[name]
    if name in {
        "VideoRegistry",
        "VideoProviderBase",
        "DummyVideoProvider",
        "OpenAIImageProvider",
        "get_video_registry",
    }:
        from ai_karen_engine.integrations.video_registry import (
            VideoRegistry as _VideoRegistry,
            VideoProviderBase as _VideoProviderBase,
            DummyVideoProvider as _DummyVideoProvider,
            OpenAIImageProvider as _OpenAIImageProvider,
            get_video_registry as _get_video_registry,
        )

        return {
            "VideoRegistry": _VideoRegistry,
            "VideoProviderBase": _VideoProviderBase,
            "DummyVideoProvider": _DummyVideoProvider,
            "OpenAIImageProvider": _OpenAIImageProvider,
            "get_video_registry": _get_video_registry,
        }[name]
    raise AttributeError(name)
