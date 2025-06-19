"""Plugin discovery and routing with manifest parsing and RBAC."""

from __future__ import annotations

import importlib
import json
import os
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

PLUGIN_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")


@dataclass
class PluginRecord:
    """Metadata for a loaded plugin."""

    name: str
    manifest: Dict[str, object]
    handler: Callable[[Dict[str, object]], object]


class PluginRouter:
    """Load plugins and route intents to their handlers."""

    def __init__(self) -> None:
        self.intent_map: Dict[str, PluginRecord] = {}
        self.load_plugins()

    def load_plugins(self) -> None:
        """Scan the plugin directory and load manifests and handlers."""
        self.intent_map.clear()
        for name in os.listdir(PLUGIN_DIR):
            path = os.path.join(PLUGIN_DIR, name)
            if not os.path.isdir(path) or name.startswith("__"):
                continue
            manifest_path = os.path.join(path, "plugin_manifest.json")
            if not os.path.exists(manifest_path):
                continue
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            intent = manifest.get("intent")
            if not intent:
                continue
            try:
                module = importlib.import_module(f"plugins.{name}.handler")
            except ModuleNotFoundError:
                # Optional plugin dependency missing; skip loading
                continue
            handler = getattr(module, "run", None)
            if handler is None:
                continue
            self.intent_map[intent] = PluginRecord(name, manifest, handler)

    def reload(self) -> None:
        """Reload plugin definitions from disk."""
        self.load_plugins()

    def get_plugin(self, intent: str) -> Optional[PluginRecord]:
        return self.intent_map.get(intent)
