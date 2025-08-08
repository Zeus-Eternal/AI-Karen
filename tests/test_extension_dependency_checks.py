import pytest
import sys
from pathlib import Path
import types

# Ensure src is on the path for absolute imports
ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

# Bypass broken extensions package initialization
ext_pkg = types.ModuleType("ai_karen_engine.extensions")
ext_pkg.__path__ = [str(SRC_PATH / "ai_karen_engine" / "extensions")]
sys.modules["ai_karen_engine.extensions"] = ext_pkg

services_pkg = types.ModuleType("ai_karen_engine.services")
services_pkg.__path__ = [str(SRC_PATH / "ai_karen_engine" / "services")]
sys.modules["ai_karen_engine.services"] = services_pkg

import importlib

registry_module = importlib.import_module("ai_karen_engine.extensions.registry")
sys.modules["ai_karen_engine.extensions"].registry = registry_module
models_module = importlib.import_module("ai_karen_engine.extensions.models")
sys.modules["ai_karen_engine.extensions"].models = models_module
plugin_registry_module = importlib.import_module("ai_karen_engine.services.plugin_registry")
sys.modules["ai_karen_engine.services"].plugin_registry = plugin_registry_module

ExtensionRegistry = registry_module.ExtensionRegistry
ExtensionManifest = models_module.ExtensionManifest
ExtensionDependencies = models_module.ExtensionDependencies
ExtensionStatus = models_module.ExtensionStatus
PluginRegistry = plugin_registry_module.PluginRegistry


class DummyExtension:
    async def initialize(self):
        pass


def make_manifest(
    name: str,
    version: str,
    ext_deps=None,
    plugin_deps=None,
    service_deps=None,
):
    return ExtensionManifest(
        name=name,
        version=version,
        display_name=name,
        description="test",
        author="tester",
        license="MIT",
        category="example",
        dependencies=ExtensionDependencies(
            extensions=ext_deps or [],
            plugins=plugin_deps or [],
            system_services=service_deps or [],
        ),
    )


def test_extension_dependency_version_mismatch():
    registry = ExtensionRegistry()
    dep_manifest = make_manifest("dep-ext", "1.0.0")
    registry.register_extension(dep_manifest, DummyExtension(), ".")
    registry.update_status("dep-ext", ExtensionStatus.ACTIVE)

    manifest = make_manifest("main", "1.0.0", ext_deps=["dep-ext@^2.0.0"])
    status = registry.check_dependencies(manifest)

    ok, message = status["dep-ext@^2.0.0"]
    assert not ok
    assert "does not satisfy" in message


def test_extension_missing_plugin_and_service(monkeypatch):
    registry = ExtensionRegistry()
    plugin_registry = PluginRegistry()
    monkeypatch.setattr(
        plugin_registry_module,
        "get_plugin_registry",
        lambda: plugin_registry,
    )

    manifest = make_manifest(
        "main", "1.0.0", plugin_deps=["missing-plugin"], service_deps=["unknown"]
    )
    status = registry.check_dependencies(manifest)

    ok, message = status["plugin:missing-plugin"]
    assert not ok
    assert "not installed" in message

    ok, message = status["service:unknown"]
    assert not ok
    assert "not available" in message
