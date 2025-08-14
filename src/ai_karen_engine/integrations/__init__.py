"""Integration helpers for Kari AI (compatibility wrappers)."""

from ai_karen_engine.integrations.automation_manager import (  # type: ignore[import-not-found]
    AutomationManager,
)
from ai_karen_engine.integrations.llm_router import (  # type: ignore[import-not-found]
    LLMProfileRouter,
)
from ai_karen_engine.integrations.local_rpa_client import (  # type: ignore[import-not-found]
    LocalRPAClient,
)
from ai_karen_engine.integrations.provider_registry import (  # type: ignore[import-not-found]
    ModelInfo,
    ProviderRegistry,
    get_provider_registry,
)
from ai_karen_engine.integrations.video_registry import (  # type: ignore[import-not-found]
    DummyVideoProvider,
    VideoProviderBase,
    VideoRegistry,
    get_video_registry,
)
from ai_karen_engine.integrations.voice_registry import (  # type: ignore[import-not-found]
    DummyVoiceProvider,
    VoiceProviderBase,
    VoiceRegistry,
    get_voice_registry,
)

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
    "get_voice_registry",
    "VideoRegistry",
    "VideoProviderBase",
    "DummyVideoProvider",
    "get_video_registry",
]
