from __future__ import annotations

import time
from typing import Any

from .base import BaseExpressionEngine
from ..contracts import ExpressionResult, ExpressionTask


class OpenAICompatibleEngine(BaseExpressionEngine):
    engine_id = "openai_compatible"

    async def generate(self, task: ExpressionTask) -> ExpressionResult:
        started = time.perf_counter()
        adapter = task.metadata.get("openai_compatible_adapter") if isinstance(task.metadata, dict) else None
        request = {
            "messages": task.messages,
            "model": task.preferred_model,
            "temperature": task.temperature,
            "max_tokens": task.max_tokens,
        }

        response: dict[str, Any] = adapter(request) if callable(adapter) else {}
        text = str(response.get("text") or "")
        provider = str(response.get("provider") or "openai_compatible")
        model = response.get("model") or task.preferred_model

        return ExpressionResult(
            task_id=task.task_id,
            text=text,
            provider=provider,
            model=str(model) if model else None,
            engine_id=self.engine_id,
            engine_mode="openai_compatible",
            runtime_engine="openai_compatible",
            response_source="openai_compatible_engine",
            attempts=response.get("attempts") or [],
            skipped=response.get("skipped") or [],
            latency_ms=(time.perf_counter() - started) * 1000,
            degraded=not bool(text.strip()),
            degradation_reason=None if text.strip() else "empty_response",
        )
