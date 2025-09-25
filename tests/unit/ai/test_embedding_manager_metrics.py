from ai_karen_engine.core.embedding_manager import (
    _METRIC_HISTORY,
    get_metrics,
    record_metric,
)


def test_metric_retention_and_reset():
    for i in range(_METRIC_HISTORY * 2):
        record_metric("test_metric", float(i))

    metrics = get_metrics()
    values = metrics.get("test_metric", [])
    assert len(values) == _METRIC_HISTORY
    assert values[0] == float(_METRIC_HISTORY)

    get_metrics(reset=True)
    assert "test_metric" not in get_metrics()
