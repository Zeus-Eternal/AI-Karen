from ai_karen_engine.self_refactor.log_utils import record_report, load_logs, LOG_PATH
from ai_karen_engine.self_refactor.engine import PatchReport
import os
import json


def test_log_sanitization(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_karen_engine.self_refactor.log_utils.LOG_PATH", tmp_path / "log.jsonl")
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
    log_utils.record_report(report)
    logs = log_utils.load_logs()
    assert logs and "patches" not in logs[0]
    monkeypatch.setenv("ADVANCED_MODE", "true")
    log_utils.record_report(report)
    logs_full = log_utils.load_logs(full=True)
    assert "patches" in logs_full[-1]
