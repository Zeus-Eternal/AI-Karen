from core.plugin_router import PluginRouter


def test_load_plugin():
    router = PluginRouter()
    plugin = router.get_plugin("greet")
    assert plugin is not None
    assert callable(plugin.handler)
    assert "required_roles" in plugin.manifest
