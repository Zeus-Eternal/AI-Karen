"""Plugin discovery and routing."""

import importlib
import json
import os
from typing import Dict

PLUGIN_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")


class PluginRouter:
    """Load plugins and route intents to their handlers."""

    def __init__(self) -> None:
        self.intent_map: Dict[str, str] = {}
        self.load_plugins()

    def load_plugins(self) -> None:
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
            if intent:
                self.intent_map[intent] = name

    def get_handler(self, intent: str):
        module_name = self.intent_map.get(intent)
        if not module_name:
            return None
        module = importlib.import_module(f"plugins.{module_name}.handler")
        return module.run
