import importlib
import json
import os
import inspect
from pathlib import Path
from types import ModuleType
import sys

if "jinja2" not in sys.modules:
    sys.modules["jinja2"] = ModuleType("jinja2")

PLUGIN_DIR = Path(__file__).resolve().parents[2] / "src" / "ai_karen_engine" / "plugins"


def ensure_optional_dependency(name: str):
    """Create a dummy module if the real one is missing."""
    if name not in sys.modules:
        sys.modules[name] = ModuleType(name)
    if "." in name:
        pkg, _, sub = name.partition(".")
        if pkg not in sys.modules:
            sys.modules[pkg] = ModuleType(pkg)
        if name not in sys.modules:
            sys.modules[name] = ModuleType(name)
        setattr(sys.modules[pkg], sub, sys.modules[name])
    if name.endswith("llm_registry"):
        sys.modules[name].registry = None
    if name.endswith("model_discovery"):
        sys.modules[name].model_discovery = None
    if name.endswith("llm_utils"):
        sys.modules[name].LLMUtils = object


def get_plugins():
    for root, dirs, _ in os.walk(PLUGIN_DIR):
        for d in dirs:
            plugin_path = Path(root) / d
            if (plugin_path / 'plugin_manifest.json').exists():
                yield plugin_path.relative_to(PLUGIN_DIR).as_posix().replace('/', '.')


def test_manifest_and_handler():
    for plugin in get_plugins():
        manifest_path = os.path.join(PLUGIN_DIR, plugin.replace('.', os.sep), 'plugin_manifest.json')
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        assert 'plugin_api_version' in manifest
        assert 'enable_external_workflow' in manifest
        assert 'required_roles' in manifest
        assert 'intent' in manifest
        assert 'trusted_ui' in manifest

        # provide dummy optional deps such as pyautogui and urwid
        for dep in ['pyautogui', 'urwid', 'jinja2', 'integrations', 'integrations.llm_registry', 'integrations.model_discovery', 'integrations.llm_utils']:
            ensure_optional_dependency(dep)
        handler_module = importlib.import_module(f'ai_karen_engine.plugins.{plugin}.handler')
        assert hasattr(handler_module, 'run')
        assert inspect.iscoroutinefunction(handler_module.run)
