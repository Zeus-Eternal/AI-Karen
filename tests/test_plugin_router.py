import asyncio
import json
import sys
from pathlib import Path
from types import ModuleType
import pytest

if "jinja2" not in sys.modules:
    sys.modules["jinja2"] = ModuleType("jinja2")

from ai_karen_engine.plugin_router import AccessDenied, PluginRouter

def ensure_optional_dependency(name: str):
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


def test_load_plugin():
    for dep in ["pyautogui", "urwid", "jinja2", "integrations", "integrations.llm_registry"]:
        ensure_optional_dependency(dep)
    router = PluginRouter()
    plugin = router.get_plugin("greet")
    assert plugin is not None
    assert callable(plugin.handler)
    assert "required_roles" in plugin.manifest


def test_invalid_manifest(monkeypatch, tmp_path):
    bad = tmp_path / "bad_plugin"
    bad.mkdir()
    (bad / "plugin_manifest.json").write_text("{ invalid json }")
    monkeypatch.setattr("ai_karen_engine.plugin_router.PLUGIN_ROOT", Path(tmp_path))
  
    for dep in ["pyautogui", "urwid", "jinja2", "integrations", "integrations.llm_registry"]:
        ensure_optional_dependency(dep)
    router = PluginRouter(plugin_root=Path(tmp_path))
    assert not router.intent_map

    handler = router.get_handler("greet")
    assert handler is None


def test_dispatch_with_rbac():
    for dep in ["pyautogui", "urwid", "jinja2", "integrations", "integrations.llm_registry"]:
        ensure_optional_dependency(dep)
    router = PluginRouter()
    result = asyncio.run(router.dispatch("greet", {}, roles=["user"]))
    assert result == (
        "Hey there! I'm Kari—your AI co-pilot. What can I help with today?"
    )


def test_dispatch_denied():
    for dep in ["pyautogui", "urwid", "jinja2", "integrations", "integrations.llm_registry"]:
        ensure_optional_dependency(dep)
    router = PluginRouter()
    with pytest.raises(AccessDenied):
        asyncio.run(router.dispatch("desktop_action", {}, roles=["user"]))


def test_dispatch_missing_roles_denied():
    for dep in ["pyautogui", "urwid", "jinja2", "integrations", "integrations.llm_registry"]:
        ensure_optional_dependency(dep)
    router = PluginRouter()
    with pytest.raises(AccessDenied):
        asyncio.run(router.dispatch("desktop_action", {}))


def test_list_intents():
    for dep in ["pyautogui", "urwid", "jinja2", "integrations", "integrations.llm_registry"]:
        ensure_optional_dependency(dep)
    router = PluginRouter()
    intents = router.list_intents()
    assert "greet" in intents


def test_plugin_ui_gating(tmp_path, monkeypatch):
    plugin = tmp_path / "ui_plugin"
    plugin.mkdir()
    (plugin / "plugin_manifest.json").write_text(
        json.dumps(
            {
                "plugin_api_version": "1.0",
                "intent": "ui_intent",
                "enable_external_workflow": False,
                "required_roles": ["user"],
                "trusted_ui": False,
            }
        )
    )
    (plugin / "handler.py").write_text("async def run(params):\n    return 'ok'\n")
    (plugin / "ui.py").write_text("def render():\n    return '<div>UI</div>'\n")
    (plugin / "prompt.txt").write_text("Hello")
    monkeypatch.setattr("ai_karen_engine.plugin_router.PLUGIN_ROOT", Path(tmp_path))
    sys.path.insert(0, str(tmp_path))
    router = PluginRouter(plugin_root=Path(tmp_path))
    record = router.get_plugin("ui_intent")
    assert record is not None
    assert record.ui is None
    monkeypatch.setenv("ADVANCED_MODE", "true")
    router.reload()
    record = router.get_plugin("ui_intent")
    assert record.ui is not None


def test_manifest_schema_reject(tmp_path, monkeypatch):
    plugin = tmp_path / "bad_schema"
    plugin.mkdir()
    (plugin / "plugin_manifest.json").write_text(
        json.dumps(
            {
                "plugin_api_version": "1.0",
                "intent": 123,
                "enable_external_workflow": False,
                "required_roles": ["user"],
                "trusted_ui": False,
            }
        )
    )
    (plugin / "handler.py").write_text("async def run(params):\n    return 'ok'\n")
    monkeypatch.setattr("ai_karen_engine.plugin_router.PLUGIN_ROOT", Path(tmp_path))
  
    for dep in ["pyautogui", "urwid", "jinja2", "integrations", "integrations.llm_registry"]:
        ensure_optional_dependency(dep)
    router = PluginRouter(plugin_root=Path(tmp_path))
    assert not router.intent_map

