"""Tests for ExtensionRegistry dependency validation."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_karen_engine.extension_host.models2 import (
    ExtensionDependencies,
    ExtensionManifest,
    ExtensionStatus,
)
from ai_karen_engine.extensions.registry import ExtensionRegistry
from ai_karen_engine.services.plugin_registry import (
    PluginManifest,
    PluginMetadata,
    PluginStatus,
)
from ai_karen_engine.core.service_registry import ServiceStatus


class DummyPluginRegistry:
    """Minimal plugin registry stand-in for dependency tests."""

    def __init__(self, plugins):
        self._plugins = plugins

    def get_plugin(self, name: str):  # pragma: no cover - simple passthrough
        return self._plugins.get(name)


class DummyServiceRegistry:
    """Minimal service registry stand-in for dependency tests."""

    def __init__(self, services):
        self._services = services

    def get_service_info(self, name: str):  # pragma: no cover - simple passthrough
        return self._services.get(name)


def _create_extension_manifest(name: str, version: str, dependencies: ExtensionDependencies | None = None) -> ExtensionManifest:
    """Helper to create extension manifests with sensible defaults."""

    return ExtensionManifest(
        name=name,
        version=version,
        display_name=f"{name.title()} Extension",
        description=f"Extension {name}",
        author="Test",
        license="MPL-2.0",
        category="core",
        dependencies=dependencies or ExtensionDependencies(),
        tags=[],
    )


def test_check_dependencies_reports_success_for_available_resources(tmp_path: Path):
    """All dependency types resolve successfully when resources are available."""

    base_manifest = _create_extension_manifest("base", "1.2.3")
    dependent_manifest = _create_extension_manifest(
        "dependent",
        "1.0.0",
        ExtensionDependencies(
            extensions=["base@^1.2.0"],
            plugins=["hello_world@^1.0.0"],
            system_services=["memory_service"],
        ),
    )

    plugin_manifest = PluginManifest(
        name="hello_world",
        version="1.1.0",
        description="Test plugin",
        author="Tester",
        module="plugins.hello_world",
    )
    plugin_metadata = PluginMetadata(
        manifest=plugin_manifest,
        path=tmp_path,
        status=PluginStatus.ACTIVE,
    )

    plugin_registry = DummyPluginRegistry({"hello_world": plugin_metadata})
    service_registry = DummyServiceRegistry(
        {"memory_service": SimpleNamespace(status=ServiceStatus.READY)}
    )

    registry = ExtensionRegistry(
        plugin_registry=plugin_registry,
        service_registry=service_registry,
    )

    registry.register_extension(base_manifest, object(), str(tmp_path))
    registry.update_status("base", ExtensionStatus.ACTIVE)

    status_map = registry.check_dependencies(dependent_manifest)

    assert status_map["extension:base@^1.2.0"] is True
    assert status_map["plugin:hello_world@^1.0.0"] is True
    assert status_map["service:memory_service"] is True


def test_check_dependencies_flags_missing_and_incompatible_resources(tmp_path: Path):
    """Missing or incompatible dependencies are reported as False."""

    base_manifest = _create_extension_manifest("core", "1.0.0")
    dependent_manifest = _create_extension_manifest(
        "needs-core",
        "1.0.0",
        ExtensionDependencies(
            extensions=["core@^2.0.0"],
            plugins=["absent_plugin@^1.0.0"],
            system_services=["analytics_service"],
        ),
    )

    plugin_registry = DummyPluginRegistry({})
    service_registry = DummyServiceRegistry({})

    registry = ExtensionRegistry(
        plugin_registry=plugin_registry,
        service_registry=service_registry,
    )

    registry.register_extension(base_manifest, object(), str(tmp_path))
    registry.update_status("core", ExtensionStatus.ACTIVE)

    status_map = registry.check_dependencies(dependent_manifest)

    assert status_map["extension:core@^2.0.0"] is False
    assert status_map["plugin:absent_plugin@^1.0.0"] is False
    assert status_map["service:analytics_service"] is False
