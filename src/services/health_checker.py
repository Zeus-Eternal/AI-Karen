"""Utilities for reporting system health."""

from __future__ import annotations

import os
import platform
import time

try:  # pragma: no cover - optional dependency
    import psutil
except Exception:  # pragma: no cover - optional dependency
    psutil = None

_START_TIME = time.time()


def get_system_health() -> dict:
    """Return runtime and memory statistics."""
    runtime = {
        "pid": os.getpid(),
        "python_version": platform.python_version(),
        "uptime": time.time() - _START_TIME,
    }

    memory = {}
    if psutil:
        vm = psutil.virtual_memory()
        memory = {
            "total": vm.total,
            "available": vm.available,
            "percent": vm.percent,
            "used": vm.used,
            "free": vm.free,
        }

    return {"runtime": runtime, "memory": memory}
