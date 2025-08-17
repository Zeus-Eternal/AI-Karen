import json
import os
import pathlib
from typing import List, Dict, Any

from ai_karen_engine.self_refactor.engine import PatchReport

LOG_PATH = pathlib.Path(os.getenv("SRE_LOG_PATH", "logs/self_refactor.log"))


def _advanced() -> bool:
    return os.getenv("ADVANCED_MODE", "false").lower() == "true"


def record_report(report: PatchReport) -> None:
    """Append a sanitized report entry to the log file."""
    entry: Dict[str, Any] = {
        "reward": report.reward,
        "duration": report.get("duration"),
        "signatures": report.get("signatures", {}),
    }
    if _advanced():
        entry.update(
            {
                "patches": report.get("patches", {}),
                "stdout": report.get("stdout", ""),
                "stderr": report.get("stderr", ""),
            }
        )
    LOG_PATH.parent.mkdir(exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def load_logs(full: bool = False) -> List[Dict[str, Any]]:
    """Return log entries. Sanitized unless full and ADVANCED_MODE is true."""
    if not LOG_PATH.exists():
        return []
    entries = [json.loads(line) for line in LOG_PATH.read_text().splitlines() if line]
    if full and _advanced():
        return entries
    for e in entries:
        e.pop("patches", None)
        e.pop("stdout", None)
        e.pop("stderr", None)
    return entries
