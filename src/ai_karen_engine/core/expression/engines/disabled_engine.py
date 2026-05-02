from __future__ import annotations
from .base import BaseExpressionEngine
from ..contracts import ExpressionResult, ExpressionTask

class DisabledEngine(BaseExpressionEngine):
    engine_id = 'disabled'
    async def generate(self, task: ExpressionTask) -> ExpressionResult:
        return ExpressionResult(
            task_id=task.task_id, 
            text='Expression engine is currently inactive or all functional engines failed. Enable a valid expression engine (Built-in, OpenAI Compatible, or Remote) in Model Settings to restore natural language generation.', 
            provider='disabled', 
            model=None, 
            engine_id=self.engine_id, 
            engine_mode='disabled', 
            runtime_engine=None, 
            response_source='engine_disabled', 
            attempts=[], 
            skipped=[], 
            latency_ms=0.0, 
            degraded=True, 
            degradation_reason='engine_disabled'
        )
