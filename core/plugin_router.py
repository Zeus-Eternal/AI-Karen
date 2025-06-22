"""Plugin discovery and routing with manifest parsing and RBAC."""

from __future__ import annotations

import importlib
import json
import os
import asyncio
from dataclasses import dataclass
 


 
from typing import Any, Callable, Dict, Iterable, Optional, List
 

from typing import Any, Callable, Dict, Iterable, Optional, List



PLUGIN_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")


@dataclass
class PluginRecord:
    """Metadata for a loaded plugin."""

    name: str
    manifest: Dict[str, object]
    handler: Callable[[Dict[str, object]], object]


class AccessDenied(Exception):
    """Raised when a caller lacks the required roles for a plugin."""


class PluginRouter:
    """Load plugins and route intents to their handlers."""

    def __init__(self, plugin_dir: str | None = None) -> None:
        self.plugin_dir = plugin_dir or PLUGIN_DIR
        self.intent_map: Dict[str, PluginRecord] = {}
        self.load_plugins()

    def load_plugins(self) -> None:
        """Scan the plugin directory and load manifests and handlers."""
        self.intent_map.clear()
        for name in os.listdir(self.plugin_dir):
            path = os.path.join(self.plugin_dir, name)
            if not os.path.isdir(path) or name.startswith("__"):
                continue
            manifest_path = os.path.join(path, "plugin_manifest.json")
            if not os.path.exists(manifest_path):
                continue
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except json.JSONDecodeError as exc:
                # Skip plugins with malformed manifest files
                print(f"Failed to parse manifest for {name}: {exc}")
                continue
 rpblna-codex/implement-self-refactor-engine-workflow
            if manifest.get("plugin_api_version") != "1.0":
                continue

 
            if manifest.get("plugin_api_version") != "1.0":
                continue

 
 
            try:
                module = importlib.import_module(f"plugins.{name}.handler")
            except ModuleNotFoundError:
                # Optional plugin dependency missing; skip loading
                continue
            handler = getattr(module, "run", None)
            if handler is None:
                continue
            intent = manifest.get("intent")
            if not intent:
                continue
            if isinstance(intent, list):
                for single in intent:
                    if isinstance(single, str):
                        self.intent_map[single] = PluginRecord(name, manifest, handler)
            elif isinstance(intent, str):
                self.intent_map[intent] = PluginRecord(name, manifest, handler)

    def reload(self) -> None:
        """Reload plugin definitions from disk."""
        self.load_plugins()

    def list_intents(self) -> List[str]:
        """Return the loaded intent names."""
        return list(self.intent_map.keys())

    def get_plugin(self, intent: str) -> Optional[PluginRecord]:
        return self.intent_map.get(intent)

    def get_handler(self, intent: str):
        plugin_record = self.intent_map.get(intent)
        if not plugin_record:
            return None
        return plugin_record.handler


    async def dispatch(
        self, intent: str, params: Dict[str, Any], roles: Iterable[str] | None = None
    ) -> Any:
        """Execute the plugin for ``intent`` with RBAC enforcement."""
        record = self.intent_map.get(intent)
        if not record:
            return None
        required = set(record.manifest.get("required_roles", []))
        if roles is not None and required and not required.intersection(roles):
            raise AccessDenied(intent)
        result = record.handler(params)
        if asyncio.iscoroutine(result):
            return await result
        return result

