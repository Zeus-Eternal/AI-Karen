"""Utilities for building hierarchical provider information."""

from __future__ import annotations

from typing import Any, Dict, List

from ai_karen_engine.integrations.llm_registry import get_registry as get_llm_registry
from ai_karen_engine.integrations.voice_registry import get_voice_registry
from ai_karen_engine.integrations.video_registry import get_video_registry


def get_provider_hierarchy() -> Dict[str, List[Dict[str, Any]]]:
    """Return hierarchical provider->model information for UI consumption."""
    hierarchy: Dict[str, List[Dict[str, Any]]] = {"llm": [], "voice": [], "video": []}

    llm_reg = get_llm_registry()
    for name in llm_reg.list_providers():
        hierarchy["llm"].append({"name": name, "models": llm_reg.list_models(name)})

    voice_reg = get_voice_registry()
    for name in voice_reg.list_providers():
        hierarchy["voice"].append({"name": name, "models": voice_reg.list_models(name)})

    video_reg = get_video_registry()
    for name in video_reg.list_providers():
        hierarchy["video"].append({"name": name, "models": video_reg.list_models(name)})

    return hierarchy

__all__ = ["get_provider_hierarchy"]
