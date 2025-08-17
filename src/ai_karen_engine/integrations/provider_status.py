"""Utilities for collecting runtime provider status information."""

from __future__ import annotations

import time
from typing import Any, Dict

from .llm_registry import get_registry


def collect_provider_statuses() -> Dict[str, Any]:
    """Ping each registered provider and gather basic statistics."""

    registry = get_registry()
    statuses: Dict[str, Any] = {}

    for name in registry.list_providers():
        provider = registry.get_provider(name)
        if not provider:
            continue
        start = time.perf_counter()
        healthy = False
        try:
            healthy = bool(getattr(provider, "ping", lambda: False)())
        except Exception:
            healthy = False
        latency = int((time.perf_counter() - start) * 1000)
        models: list[str] = []
        try:
            models = list(getattr(provider, "available_models", lambda: [])())
        except Exception:
            pass
        statuses[name] = {
            "healthy": healthy,
            "latency_ms": latency,
            "models": models,
            "model_count": len(models),
        }

    return statuses


__all__ = ["collect_provider_statuses"]

