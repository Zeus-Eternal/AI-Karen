import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.extensions.models import ExtensionManifest, ExtensionContext


class DummyExtension(BaseExtension):
    async def _initialize(self) -> None:
        pass


def _build_manifest(name: str) -> ExtensionManifest:
    return ExtensionManifest(
        name=name,
        version="0.1.0",
        display_name=name.title(),
        description="test",
        author="tester",
        license="MIT",
        category="example",
    )


def test_base_extension_router_prefix() -> None:
    with patch("ai_karen_engine.extensions.base.ExtensionDataManager") as dm, \
            patch("ai_karen_engine.extensions.base.PluginOrchestrator") as po:
        dm.return_value = MagicMock()
        po.return_value = MagicMock()
        manifest = _build_manifest("dummy")
        context = ExtensionContext(plugin_router=MagicMock(), db_session=None, app_instance=None)
        ext = DummyExtension(manifest, context)
        router = ext.create_api_router()
        assert router and router.prefix == "/api/extensions/dummy"


def test_hello_extension_router_prefix() -> None:
    with patch("ai_karen_engine.extensions.base.ExtensionDataManager") as dm, \
            patch("ai_karen_engine.extensions.base.PluginOrchestrator") as po:
        dm.return_value = MagicMock()
        po.return_value = MagicMock()

        import importlib.util

        ext_path = Path("extensions/examples/hello-extension/__init__.py")
        spec = importlib.util.spec_from_file_location("hello_extension", ext_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)  # type: ignore
        HelloExtension = module.HelloExtension

        manifest_path = Path("extensions/examples/hello-extension/extension.json")
        manifest = ExtensionManifest.from_file(manifest_path)
        context = ExtensionContext(plugin_router=MagicMock(), db_session=None, app_instance=None)
        extension = HelloExtension(manifest, context)
        router = extension.create_api_router()
        assert router and router.prefix == "/api/extensions/hello-extension"
