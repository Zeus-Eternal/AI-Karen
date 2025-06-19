from core.plugin_router import PluginRouter


def test_load_plugin():
    router = PluginRouter()
    handler = router.get_handler("greet")
    assert handler is not None
