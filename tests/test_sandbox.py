import asyncio
from types import ModuleType
import sys

if "jinja2" not in sys.modules:
    sys.modules["jinja2"] = ModuleType("jinja2")

from ai_karen_engine.plugin_router import PluginRouter


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


def test_sandbox_crash_plugin():
    for dep in ["pyautogui", "urwid", "jinja2", "integrations", "integrations.llm_registry"]:
        ensure_optional_dependency(dep)
    router = PluginRouter()
    try:
        asyncio.run(router.dispatch("sandbox_fail", {}, roles=["user"]))
    except RuntimeError as exc:
        assert "exit code" in str(exc) or "result" in str(exc)
    else:
        assert False, "sandbox did not raise"
