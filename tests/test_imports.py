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
