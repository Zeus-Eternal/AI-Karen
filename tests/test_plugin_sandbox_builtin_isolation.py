import builtins
import importlib.util
import threading
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "plugin_execution", Path("src/ai_karen_engine/services/plugin_execution.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

PluginSandbox = module.PluginSandbox
ResourceLimits = module.ResourceLimits
SecurityPolicy = module.SecurityPolicy


def test_sandbox_does_not_modify_global_builtins():
    """Ensure sandboxed execution leaves other threads' builtins untouched."""
    original_open = builtins.open
    policy = SecurityPolicy(allow_file_system=False)
    limits = ResourceLimits()

    start_event = threading.Event()
    finish_event = threading.Event()
    results = {}

    def sandbox_thread():
        with PluginSandbox(limits, policy) as sandbox:
            start_event.set()
            try:
                exec("open('temp.txt', 'w')", {"__builtins__": sandbox.allowed_builtins})
            except PermissionError:
                results["sandbox_restricted"] = True
            finally:
                finish_event.set()

    def other_thread():
        start_event.wait()
        results["other_open_is_original"] = builtins.open is original_open
        finish_event.wait()

    t1 = threading.Thread(target=sandbox_thread)
    t2 = threading.Thread(target=other_thread)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results.get("sandbox_restricted") is True
    assert results.get("other_open_is_original") is True

