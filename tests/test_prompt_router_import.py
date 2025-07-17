from ai_karen_engine.core.prompt_router import PluginRouter
from ai_karen_engine.plugin_router import PluginRouter as RealRouter


def test_prompt_router_reexport():
    assert PluginRouter is RealRouter
