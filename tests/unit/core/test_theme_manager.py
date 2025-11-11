from datetime import datetime, timedelta
import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "extensions"
    / "automation"
    / "prompt-driven"
    / "ui"
    / "workflow_analytics.py"
)

spec = importlib.util.spec_from_file_location("workflow_analytics", MODULE_PATH)
workflow_analytics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow_analytics)
WorkflowAnalytics = workflow_analytics.WorkflowAnalytics


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_workflow_analytics_summarize_filters_and_counts(monkeypatch):
    now = datetime.utcnow()
    payloads = {
        "http://test/api/extensions/prompt-driven-automation/workflows": {
            "workflows": [
                {"name": "alpha", "tags": ["ops", "ops"]},
                {"name": "beta", "tags": ["ml"]},
            ]
        },
        "http://test/api/extensions/prompt-driven-automation/execution-history?limit=1000": {
            "executions": [
                {
                    "id": "1",
                    "status": "Success",
                    "duration_seconds": 2,
                    "start_time": (now - timedelta(hours=1)).isoformat(),
                },
                {
                    "id": "2",
                    "status": "Failed",
                    "duration_seconds": 4,
                    "start_time": (now - timedelta(days=2)).isoformat(),
                },
            ]
        },
        "http://test/api/extensions/prompt-driven-automation/metrics": {"throughput": 10},
    }

    def fake_get(url, timeout):  # noqa: D401
        return _Response(payloads[url])

    monkeypatch.setattr(
        workflow_analytics.requests,
        "get",
        fake_get,
    )

    analytics = WorkflowAnalytics(api_base_url="http://test")
    summary = analytics.summarize(time_range="24h")

    assert summary["workflow_totals"]["count"] == 2
    assert summary["workflow_totals"]["top_tags"][0][0] == "ops"
    stats = summary["execution_stats"]
    assert stats["total"] == 1
    assert stats["success"] == 1
    assert stats["failed"] == 0
    assert stats["average_duration"] == 2
    assert summary["raw_metrics"] == {"throughput": 10}
