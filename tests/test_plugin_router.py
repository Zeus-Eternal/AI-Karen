import asyncio
import sys
from types import ModuleType
import pytest

from core.plugin_router import AccessDenied, PluginRouter


def ensure_optional_dependency(name: str):
    if name not in sys.modules:
        sys.modules[name] = ModuleType(name)


def test_load_plugin():
    for dep in ["pyautogui", "urwid"]:
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
    monkeypatch.setattr("core.plugin_router.PLUGIN_DIR", str(tmp_path))
    for dep in ["pyautogui", "urwid"]:
        ensure_optional_dependency(dep)
    router = PluginRouter()
    assert not router.intent_map

    handler = router.get_handler("greet")
    assert handler is None


def test_dispatch_with_rbac():
    for dep in ["pyautogui", "urwid"]:
        ensure_optional_dependency(dep)
    router = PluginRouter()
    result = asyncio.run(router.dispatch("greet", {}, roles=["user"]))
    assert result == "Hello World from plugin!"


def test_dispatch_denied():
    for dep in ["pyautogui", "urwid"]:
        ensure_optional_dependency(dep)
    router = PluginRouter()
    with pytest.raises(AccessDenied):
        asyncio.run(router.dispatch("desktop_action", {}, roles=["user"]))


def test_list_intents():
    for dep in ["pyautogui", "urwid"]:
        ensure_optional_dependency(dep)
    router = PluginRouter()
    intents = router.list_intents()
    assert "greet" in intents
