"""Integration helpers for Kari AI (compatibility wrappers)."""

from ai_karen_engine.integrations.automation_manager import AutomationManager
from ai_karen_engine.integrations.local_rpa_client import LocalRPAClient
from ai_karen_engine.integrations.llm_router import LLMProfileRouter
from ai_karen_engine.integrations.voice_registry import (
    VoiceRegistry,
    get_voice_registry,
)
from ai_karen_engine.integrations.video_registry import (
    VideoRegistry,
    get_video_registry,
)
from ai_karen_engine.integrations.provider_registry import (
    ProviderRegistry,
    ModelInfo,
)

__all__ = [
    "AutomationManager",
    "LocalRPAClient",
    "LLMProfileRouter",
    "ProviderRegistry",
    "ModelInfo",
    "VoiceRegistry",
    "get_voice_registry",
    "VideoRegistry",
    "get_video_registry",
]
