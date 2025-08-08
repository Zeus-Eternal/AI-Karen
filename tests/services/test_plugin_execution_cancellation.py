import asyncio
import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from ai_karen_engine.services.plugin_execution import (
    ExecutionMode,
    ExecutionRequest,
    ExecutionStatus,
    PluginExecutionEngine,
)
from ai_karen_engine.services.plugin_registry import (
    PluginManifest,
    PluginMetadata,
    PluginStatus,
)


@pytest.mark.asyncio
async def test_cancel_thread_execution_success(tmp_path: Path):
    plugin_dir = tmp_path / "cancellable"
    plugin_dir.mkdir()
    handler_code = (
        "import time\n"
        "def run(params, cancel_event=None):\n"
        "    while not cancel_event.is_set():\n"
        "        time.sleep(0.1)\n"
        "    return {'stopped': True}\n"
    )
    (plugin_dir / "handler.py").write_text(handler_code)

    manifest = PluginManifest(
        name="cancellable",
        version="1.0.0",
        description="test",
        author="test",
        module="handler",
    )
    metadata = PluginMetadata(manifest=manifest, path=plugin_dir, status=PluginStatus.REGISTERED)
    registry = Mock()
    registry.get_plugin.return_value = metadata

    engine = PluginExecutionEngine(registry=registry)
    request = ExecutionRequest(
        plugin_name="cancellable",
        parameters={},
        execution_mode=ExecutionMode.THREAD,
        timeout_seconds=5,
        security_policy={
            "allowed_builtins": list(__builtins__.keys()),
            "allow_imports": None,
            "blocked_imports": [],
        },
    )

    exec_task = asyncio.create_task(engine.execute_plugin(request))
    await asyncio.sleep(0.2)
    cancel_success = await engine.cancel_execution(request.request_id)
    result = await exec_task

    assert cancel_success is True
    assert result.status == ExecutionStatus.CANCELLED
    assert result.terminated is True


@pytest.mark.asyncio
async def test_cancel_thread_execution_failure(tmp_path: Path):
    plugin_dir = tmp_path / "noncancellable"
    plugin_dir.mkdir()
    handler_code = (
        "import time\n"
        "def run(params):\n"
        "    time.sleep(5)\n"
        "    return {'done': True}\n"
    )
    (plugin_dir / "handler.py").write_text(handler_code)

    manifest = PluginManifest(
        name="noncancellable",
        version="1.0.0",
        description="test",
        author="test",
        module="handler",
    )
    metadata = PluginMetadata(manifest=manifest, path=plugin_dir, status=PluginStatus.REGISTERED)
    registry = Mock()
    registry.get_plugin.return_value = metadata

    engine = PluginExecutionEngine(registry=registry)
    request = ExecutionRequest(
        plugin_name="noncancellable",
        parameters={},
        execution_mode=ExecutionMode.THREAD,
        timeout_seconds=5,
        security_policy={
            "allowed_builtins": list(__builtins__.keys()),
            "allow_imports": None,
            "blocked_imports": [],
        },
    )

    exec_task = asyncio.create_task(engine.execute_plugin(request))
    await asyncio.sleep(0.2)
    cancel_success = await engine.cancel_execution(request.request_id)
    result = await exec_task
    await asyncio.sleep(5.2)

    assert cancel_success is False
    assert result.status == ExecutionStatus.CANCELLED
    assert result.terminated is False
