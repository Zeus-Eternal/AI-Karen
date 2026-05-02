from __future__ import annotations

import time
from typing import Any

from .base import BaseExpressionEngine
from ..contracts import ExpressionResult, ExpressionTask


class BuiltinProviderEngine(BaseExpressionEngine):
    engine_id = "builtin"

    async def generate(self, task: ExpressionTask) -> ExpressionResult:
        started = time.perf_counter()
        adapter = task.metadata.get("builtin_adapter") if isinstance(task.metadata, dict) else None
        payload = self._build_payload(task)

        if callable(adapter):
            response: dict[str, Any] = adapter(payload) or {}
            text = str(response.get("text") or "")
            provider = str(response.get("provider") or "builtin_transformers")
            model = response.get("model")
            attempts = response.get("attempts") or []
            skipped = response.get("skipped") or []
        else:
            text = ""
            provider = "builtin_transformers"
            model = task.preferred_model
            attempts = []
            skipped = []

        return ExpressionResult(
            task_id=task.task_id,
            text=text,
            provider=provider,
            model=str(model) if model else None,
            engine_id=self.engine_id,
            engine_mode="builtin_provider_engine",
            runtime_engine="builtin",
            response_source="builtin_provider_engine",
            attempts=attempts,
            skipped=skipped,
            latency_ms=(time.perf_counter() - started) * 1000,
            degraded=not bool(text.strip()),
            degradation_reason=None if text.strip() else "empty_response",
        )

    def _build_payload(self, task: ExpressionTask) -> dict[str, Any]:
        return {
            "messages": task.messages,
            "provider": task.preferred_provider,
            "model": task.preferred_model,
            "max_tokens": task.max_tokens,
            "temperature": task.temperature,
            "timeout_ms": task.timeout_ms,
        }
