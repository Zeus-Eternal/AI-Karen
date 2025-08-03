"""Tests for ResourceMonitor enforcement actions."""

import asyncio
import sys
import types
from pathlib import Path

import pytest

# Stub out heavy database client to avoid optional dependencies during import
milvus_stub = types.ModuleType("ai_karen_engine.clients.database.milvus_client")
milvus_stub.recall_vectors = lambda *_, **__: []
milvus_stub.store_vector = lambda *_, **__: None
sys.modules.setdefault("ai_karen_engine.clients.database.milvus_client", milvus_stub)

from ai_karen_engine.extensions.models import (  # noqa: E402
    ExtensionManifest,
    ExtensionRecord,
    ExtensionResources,
    ExtensionStatus,
)
from ai_karen_engine.extensions.resource_monitor import (  # noqa: E402
    ResourceMonitor,
    ResourceUsage,
)


class DummyExtension:
    """Minimal extension placeholder for tests."""


def build_record(name: str, enforcement_action: str | None = None) -> ExtensionRecord:
    resources = ExtensionResources(
        max_memory_mb=10,
        max_cpu_percent=10,
        max_disk_mb=10,
    )
    if enforcement_action is not None:
        resources.enforcement_action = enforcement_action
    manifest = ExtensionManifest(
        name=name,
        version="1.0",
        display_name=name,
        description="test",
        author="author",
        license="MIT",
        category="test",
        resources=resources,
    )
    return ExtensionRecord(
        manifest=manifest,
        instance=DummyExtension(),
        status=ExtensionStatus.ACTIVE,
        directory=Path("."),
    )


@pytest.mark.asyncio
async def test_resource_monitor_env_action_shutdown(monkeypatch):
    """Environment variable should trigger shutdown enforcement."""
    monkeypatch.setenv("RESOURCE_MONITOR_ACTION", "shutdown")
    monitor = ResourceMonitor()
    record = build_record("ext_env")
    monitor.register_extension(record)
    monitor.extension_usage["ext_env"] = ResourceUsage(
        memory_mb=20, cpu_percent=0, disk_mb=0
    )
    await monitor._check_resource_limits("ext_env")
    assert "ext_env" not in monitor.extension_usage


@pytest.mark.asyncio
async def test_resource_monitor_extension_setting_throttle(monkeypatch):
    """Extension-level configuration should override env defaults."""
    monkeypatch.setenv("RESOURCE_MONITOR_ACTION", "warn")
    monitor = ResourceMonitor()
    record = build_record("ext_throttle", enforcement_action="throttle")
    monitor.register_extension(record)
    monitor.extension_usage["ext_throttle"] = ResourceUsage(
        memory_mb=20, cpu_percent=0, disk_mb=0
    )

    called = False

    async def fake_sleep(duration):
        nonlocal called
        called = True
        assert duration == monitor.throttle_seconds

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    await monitor._check_resource_limits("ext_throttle")
    assert called
    assert "ext_throttle" in monitor.extension_usage
