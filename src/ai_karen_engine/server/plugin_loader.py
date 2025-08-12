"""Utility for loading plugin manifests for legacy systems."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from ai_karen_engine.plugins.validator import validate_plugin_manifest

logger = logging.getLogger(__name__)

PLUGIN_MAP: Dict[str, Dict[str, Any]] = {}
ENABLED_PLUGINS: set[str] = set()


def load_plugins(plugin_dir: str) -> None:
    """Load and validate all plugins from a directory."""
    PLUGIN_MAP.clear()
    ENABLED_PLUGINS.clear()

    path = Path(plugin_dir)
    if not path.exists():
        logger.warning("Plugin directory not found: %s", path)
        return

    for plugin_path in path.iterdir():
        if not plugin_path.is_dir():
            continue

        manifest_file = plugin_path / "plugin_manifest.json"
        if not manifest_file.exists():
            continue

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            valid, errors, _ = validate_plugin_manifest(manifest)
            if not valid:
                logger.warning(
                    "Invalid plugin manifest %s: %s", manifest_file, "; ".join(errors)
                )
                continue

            intents = manifest.get("intent", [])
            if isinstance(intents, str):
                intents = [intents]

            for intent in intents:
                PLUGIN_MAP[intent] = manifest
                ENABLED_PLUGINS.add(intent)

            logger.info("Loaded plugin: %s", plugin_path.name)
        except Exception as e:  # pragma: no cover - defensive
            logger.error("Failed loading plugin %s: %s", plugin_path.name, str(e))
