import sys
from types import ModuleType
import asyncio

dummy = ModuleType("pyautogui")
dummy.click = lambda *args, **kwargs: None
dummy.typewrite = lambda *args, **kwargs: None
dummy.screenshot = lambda path="screenshot.png": path
sys.modules.setdefault("pyautogui", dummy)


from ai_karen_engine.core.workflow_engine_client import WorkflowEngineClient  # noqa: E402
from ai_karen_engine.integrations.automation_manager import AutomationManager  # noqa: E402
from ai_karen_engine.integrations.local_rpa_client import LocalRPAClient  # noqa: E402
from ai_karen_engine.plugins.router import PluginRouter  # noqa: E402

def test_workflow_engine_trigger(capfd):
    wf = WorkflowEngineClient()
    wf.trigger("test_flow", {"ok": True})
    captured = capfd.readouterr()
    assert "test_flow" in captured.out


def test_automation_manager_run_all():
    mgr = AutomationManager()

    async def sample():
        return "done"

    mgr.add_task(sample())
    results = asyncio.run(mgr.run_all())
    assert results == ["done"]


def test_local_rpa_client():
    rpa = LocalRPAClient()
    assert rpa.click(1, 2) is None
    assert rpa.type_text("hi") is None
    assert rpa.screenshot("foo.png") == "foo.png"


def test_manifest_workflow_slug():
    router = PluginRouter()
    plugin = router.get_plugin("autonomous_task_handler")
    assert plugin.manifest.get("workflow_slug") == "autonomous_task_followup"


