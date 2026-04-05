"""Compatibility registry wrapper for host-facing extension execution."""

from __future__ import annotations

from typing import List

from extensions.core.registry.plugin_registry import PluginRegistry, get_registry
from extensions.core.manifest import HookPoint


class ExtensionRegistry(PluginRegistry):
    """Host-facing registry contract."""

    def get_extensions_for_hook(self, hook_point: HookPoint) -> List[object]:
        return super().get_extensions_for_hook(hook_point)


__all__ = ["ExtensionRegistry", "get_registry"]
