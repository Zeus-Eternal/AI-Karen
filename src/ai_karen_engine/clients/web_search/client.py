"""
Compatibility web search client.

This module exposes the same `WebSearchClient` API used by the intelligent
search plugin, but under a conventional import path that application services
can import directly.
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
import sys


def _load_plugin_search_client_module() -> ModuleType:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "extensions"
        / "plugins"
        / "intelligent-search"
        / "search_client.py"
    )

    spec = spec_from_file_location(
        "ai_karen_engine._intelligent_search_search_client",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load search client module from {module_path}")

    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_plugin_module = _load_plugin_search_client_module()

SearchResult = _plugin_module.SearchResult
SearchResponse = _plugin_module.SearchResponse
WebSearchClient = _plugin_module.WebSearchClient

__all__ = ["SearchResult", "SearchResponse", "WebSearchClient"]
