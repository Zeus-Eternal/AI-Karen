"""Simple RBAC and audit logging utilities."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict


class RBAC:
    """Role-based access control helper."""

    def require(self, user: Dict[str, Any], role: str) -> None:
        if role not in user.get("roles", []):
            raise PermissionError(f"{role} role required")


class AuditLogger:
    """Audit trail logger with basic data retention."""

    def __init__(self, path: str | Path = "cloud_audit.log", retention_days: int = 30) -> None:
        self.path = Path(path)
        self.retention_seconds = retention_days * 86400

    def log_cloud_usage(self, user_id: str, provider: str, model: str) -> None:
        entry = {
            "timestamp": time.time(),
            "user_id": user_id,
            "provider": provider,
            "model": model,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        self.purge()

    def purge(self) -> None:
        if not self.path.exists():
            return
        now = time.time()
        lines = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if now - entry.get("timestamp", 0) <= self.retention_seconds:
                    lines.append(line)
        with self.path.open("w", encoding="utf-8") as f:
            f.writelines(lines)


rbac = RBAC()
audit_logger = AuditLogger()
