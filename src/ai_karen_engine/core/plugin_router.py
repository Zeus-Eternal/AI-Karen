"""Plugin discovery and routing with manifest parsing and RBAC."""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import os
try:
    from jsonschema import ValidationError, validate
except Exception:  # pragma: no cover - optional dependency
    ValidationError = Exception  # type: ignore
    def validate(*args, **kwargs):  # type: ignore
        return None
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional, List


PLUGIN_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "config",
    "plugin_schema.json",
)


@dataclass
class PluginRecord:
    """Metadata for a loaded plugin."""

    name: str
    manifest: Dict[str, object]
    handler: Callable[[Dict[str, object]], object]
    ui: object | None = None


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
        try:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except FileNotFoundError as exc:
            print(f"Plugin schema not found: {exc}")
            schema = None
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
            if schema is not None:
                try:
                    validate(instance=manifest, schema=schema)
                except ValidationError as exc:
                    print(f"Manifest validation failed for {name}: {exc}")
                    continue
            if manifest.get("plugin_api_version") != "1.0":
                continue

            try:
                module = importlib.import_module(f"src.plugins.{name}.handler")
            except ModuleNotFoundError:
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"{name}.handler", os.path.join(path, "handler.py")
                    )
                    module = importlib.util.module_from_spec(spec)
                    assert spec.loader
                    spec.loader.exec_module(module)  # type: ignore
                except Exception:
                    continue
            handler = getattr(module, "run", None)
            if handler is None:
                continue

            ui_module = None
            ui_path = os.path.join(path, "ui.py")
            advanced = os.getenv("ADVANCED_MODE", "false").lower() == "true"
            if os.path.exists(ui_path) and (manifest.get("trusted_ui") or advanced):
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"src.plugins.{name}.ui", ui_path
                    )
                    ui_module = importlib.util.module_from_spec(spec)
                    assert spec.loader
                    spec.loader.exec_module(ui_module)  # type: ignore
                except Exception as exc:
                    print(f"Failed to load UI for {name}: {exc}")
                    ui_module = None

            record = PluginRecord(name, manifest, handler, ui_module)
            intent = manifest.get("intent")
            if not intent:
                continue
            if isinstance(intent, list):
                for single in intent:
                    if isinstance(single, str):
                        self.intent_map[single] = record
            elif isinstance(intent, str):
                self.intent_map[intent] = record

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
