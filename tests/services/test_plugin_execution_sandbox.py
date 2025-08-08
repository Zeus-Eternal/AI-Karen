"""Tests for PluginSandbox builtin isolation across threads."""

import builtins
import threading
import time

from src.ai_karen_engine.services.plugin_execution import (
    PluginSandbox,
    ResourceLimits,
    SecurityPolicy,
)


def _attempt_file_write(_: dict):
    try:
        open("somefile", "w")
    except PermissionError:
        pass
    else:
        raise AssertionError("open should be restricted")
    time.sleep(0.2)


def test_builtin_isolation_between_threads():
    """Ensure sandboxing does not alter builtins in other threads."""
    open_before = builtins.open

    def run_sandbox():
        with PluginSandbox(ResourceLimits(), SecurityPolicy()) as sandbox:
            sandbox.run(_attempt_file_write, {})

    t = threading.Thread(target=run_sandbox)
    t.start()
    time.sleep(0.1)

    with open(__file__, "r") as f:
        f.read(1)

    t.join()
    assert builtins.open is open_before
