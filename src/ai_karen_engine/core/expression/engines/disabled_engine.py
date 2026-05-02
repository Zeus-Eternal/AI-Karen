from __future__ import annotations
from .base import BaseExpressionEngine
from ..contracts import ExpressionResult, ExpressionTask

class DisabledEngine(BaseExpressionEngine):
    engine_id = 'disabled'
    async def generate(self, task: ExpressionTask) -> ExpressionResult:
        return ExpressionResult(task_id=task.task_id, text='Expression engine is disabled.', provider='disabled', model=None, engine_id=self.engine_id, engine_mode='disabled', runtime_engine=None, response_source='engine_disabled', attempts=[], skipped=[], latency_ms=0.0, degraded=True, degradation_reason='engine_disabled')
