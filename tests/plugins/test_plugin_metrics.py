import importlib
import sys
from ai_karen_engine.core import plugin_registry as pr


def test_plugin_metrics():
    # reload to reset metrics
    importlib.reload(pr)
    handler = pr.plugin_registry.get('hello_world')
    assert handler is not None
    handler['handler'].run = lambda *_a, **_k: 'ok'
    result = pr.execute_plugin(handler, {}, 'hi')
    assert result == 'ok'
    assert pr._METRICS['plugin_exec_total'] > 0
    assert pr._METRICS['plugins_loaded'] > 0


def test_plugin_metrics_without_prometheus(monkeypatch):
    for mod in list(sys.modules):
        if mod.startswith("prometheus_client"):
            monkeypatch.delitem(sys.modules, mod, raising=False)
    monkeypatch.setitem(sys.modules, "prometheus_client", None)

    importlib.reload(pr)
    handler = pr.plugin_registry.get('hello_world')
    assert handler is not None
    handler['handler'].run = lambda *_a, **_k: 'ok'
    result = pr.execute_plugin(handler, {}, 'hi')
    assert result == 'ok'
    assert pr._METRICS['plugin_exec_total'] > 0
    importlib.reload(pr)

