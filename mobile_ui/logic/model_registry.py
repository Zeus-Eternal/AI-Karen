from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from src.integrations.llm_registry import registry as llm_registry


def list_providers() -> List[str]:
    """Return available provider names."""
    return list(llm_registry.list_models())


def get_models(provider: str) -> List[Dict[str, str]]:
    """Return model details for ``provider`` from the active registry."""
    llm = llm_registry.backends.get(provider)
    if not llm:
        return []
    name = getattr(llm, "model_name", None) or getattr(llm, "model", None)
    if not name and hasattr(llm, "model_path"):
        name = Path(getattr(llm, "model_path")).stem
    return [{"name": name or provider}]
