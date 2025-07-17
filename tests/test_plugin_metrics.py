import importlib
from ai_karen_engine.core import plugin_registry as pr


def test_plugin_metrics():
    # reload to reset metrics
    importlib.reload(pr)
    handler = pr.plugin_registry.get('hello_world')
    assert handler is not None
    result = pr.execute_plugin(handler, {}, 'hi')
    assert result
    assert pr._METRICS['plugin_exec_total'] > 0
    assert pr._METRICS['plugins_loaded'] > 0

