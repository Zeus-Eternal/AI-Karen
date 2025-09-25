import importlib

from ai_karen_engine.utils import metrics


def test_metrics_initialized_once(caplog):
    module = importlib.reload(metrics)
    caplog.set_level("DEBUG")
    first = module.init_metrics()[0]
    second = module.init_metrics()[0]
    assert first is second
    assert "Metrics already initialized" in caplog.text
