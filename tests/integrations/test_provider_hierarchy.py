import pytest
from ai_karen_engine.integrations.provider_hierarchy import get_provider_hierarchy


def test_provider_hierarchy_structure():
    hierarchy = get_provider_hierarchy()
    assert "llm" in hierarchy
    assert "voice" in hierarchy
    assert "video" in hierarchy
    # ensure dummy providers are included
    voice_names = [p["name"] for p in hierarchy["voice"]]
    video_names = [p["name"] for p in hierarchy["video"]]
    assert "dummy" in voice_names
    assert "dummy" in video_names
