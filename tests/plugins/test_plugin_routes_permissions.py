import pytest
from fastapi import HTTPException

from ai_karen_engine.api_routes.plugin_routes import (
    enable_plugin,
    disable_plugin,
    reload_plugins,
)


class DummyPluginService:
    async def enable_plugin(self, plugin_name: str) -> bool:  # pragma: no cover - simple stub
        return True

    async def disable_plugin(self, plugin_name: str) -> bool:  # pragma: no cover - simple stub
        return True

    async def reload_plugins(self) -> int:  # pragma: no cover - simple stub
        return 1


@pytest.mark.asyncio
async def test_non_admin_forbidden():
    service = DummyPluginService()
    for func, args in [
        (enable_plugin, ("test",)),
        (disable_plugin, ("test",)),
        (reload_plugins, ()),
    ]:
        with pytest.raises(HTTPException) as exc:
            await func(*args, {"roles": ["user"]}, service)
        assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_allowed():
    service = DummyPluginService()
    result = await enable_plugin("test", {"roles": ["admin"]}, service)
    assert result == {"success": True, "message": "Plugin test enabled successfully"}

    result = await disable_plugin("test", {"roles": ["admin"]}, service)
    assert result == {"success": True, "message": "Plugin test disabled successfully"}

    result = await reload_plugins({"roles": ["admin"]}, service)
    assert result == {
        "success": True,
        "message": "Reloaded 1 plugins successfully",
        "plugins_loaded": 1,
    }
