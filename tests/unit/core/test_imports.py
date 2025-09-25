import sys
import types


def test_import_automation_manager(monkeypatch):
    stub = types.ModuleType("ai_karen_engine.automation_manager")
    class DummyAM:
        pass
    stub.AutomationManager = DummyAM
    monkeypatch.setitem(sys.modules, "ai_karen_engine.automation_manager", stub)

    from ai_karen_engine import AutomationManager

    assert AutomationManager is DummyAM


def test_core_prompt_router_reexport():
    from ai_karen_engine.core.prompt_router import PluginRouter as PR1
    from ai_karen_engine.plugins.router import PluginRouter as PR2
    assert PR1 is PR2
