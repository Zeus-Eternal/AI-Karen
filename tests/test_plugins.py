import importlib
import json
import os
import inspect
from pathlib import Path
from types import ModuleType
import sys

PLUGIN_DIR = Path(__file__).resolve().parents[1] / "src" / "ai_karen_engine" / "plugins"


def ensure_optional_dependency(name: str):
    """Create a dummy module if the real one is missing."""
    if name not in sys.modules:
        sys.modules[name] = ModuleType(name)


def get_plugins():
    for name in os.listdir(PLUGIN_DIR):
        path = os.path.join(PLUGIN_DIR, name)
        if os.path.isdir(path) and not name.startswith('__'):
            yield name


def test_manifest_and_handler():
    for plugin in get_plugins():
        manifest_path = os.path.join(PLUGIN_DIR, plugin, 'plugin_manifest.json')
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        assert 'plugin_api_version' in manifest
        assert 'enable_external_workflow' in manifest
        assert 'required_roles' in manifest
        assert 'intent' in manifest
        assert 'trusted_ui' in manifest

        # provide dummy optional deps such as pyautogui and urwid
        for dep in ['pyautogui', 'urwid']:
            ensure_optional_dependency(dep)
        handler_module = importlib.import_module(f'ai_karen_engine.plugins.{plugin}.handler')
        assert hasattr(handler_module, 'run')
        assert inspect.iscoroutinefunction(handler_module.run)
