from src.self_refactor.log_utils import record_report, load_logs, LOG_PATH
from src.self_refactor.engine import PatchReport
import os
import json


def test_log_sanitization(tmp_path, monkeypatch):
    monkeypatch.setattr("src.self_refactor.log_utils.LOG_PATH", tmp_path / "log.jsonl")
    report = PatchReport()
    report.update(
        {
            "reward": 1,
            "duration": 0.1,
            "patches": {"a.py": "code"},
            "stdout": "ok",
            "stderr": "",
            "signatures": {"a.py": "123"},
        }
    )
    record_report(report)
    logs = load_logs()
    assert logs and "patches" not in logs[0]
    monkeypatch.setenv("ADVANCED_MODE", "true")
    record_report(report)
    logs_full = load_logs(full=True)
    assert "patches" in logs_full[-1]
