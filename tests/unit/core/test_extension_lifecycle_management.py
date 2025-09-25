import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.extensions import (
    ExtensionManager,
    HealthStatus,
    ExtensionStatus,
)
from ai_karen_engine.plugins.router import PluginRouter


@pytest.fixture()
def temp_extension(tmp_path):
    ext_dir = tmp_path / "sample-extension"
    ext_dir.mkdir()
    manifest = {
        "name": "sample-extension",
        "version": "1.0.0",
        "display_name": "Sample",
        "description": "Sample",
        "author": "Test",
        "license": "MIT",
        "category": "test",
    }
    (ext_dir / "extension.json").write_text(json.dumps(manifest))
    (ext_dir / "__init__.py").write_text(
        "from ai_karen_engine.extensions.base import BaseExtension\n"
        "class SampleExtension(BaseExtension):\n"
        "    async def _initialize(self):\n        "
        "        pass\n"
        "    async def _shutdown(self):\n        "
        "        pass\n"
    )
    return ext_dir


@pytest.fixture()
def extension_manager(tmp_path):
    router = PluginRouter(plugin_root=Path("plugin_marketplace"))
    return ExtensionManager(extension_root=tmp_path, plugin_router=router)


@pytest.mark.asyncio
async def test_lifecycle_operations(extension_manager, temp_extension):
    assert await extension_manager.install_extension(
        "sample-extension", "1.0.0", path=str(temp_extension)
    )
    record = await extension_manager.enable_extension("sample-extension")
    assert record is not None
    status = extension_manager.get_extension_status("sample-extension")
    assert status["status"] == ExtensionStatus.ACTIVE.value
    health = await extension_manager.check_extension_health("sample-extension")
    assert health in HealthStatus
    await extension_manager.disable_extension("sample-extension")
    await extension_manager.remove_extension("sample-extension")
    assert not (extension_manager.extension_root / "sample-extension").exists()

