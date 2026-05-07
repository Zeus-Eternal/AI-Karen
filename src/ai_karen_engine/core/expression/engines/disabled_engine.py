from __future__ import annotations
from .base import BaseExpressionEngine
from ..contracts import ExpressionResult, ExpressionTask

class DisabledEngine(BaseExpressionEngine):
    engine_id = 'disabled'
    async def generate(self, task: ExpressionTask) -> ExpressionResult:
        return ExpressionResult(
            task_id=task.task_id, 
            text='Expression engine is currently inactive or all functional engines failed. Enable a valid expression engine (Built-in, OpenAI Compatible, or Remote) in Model Settings to restore natural language generation.', 
            provider=None, 
            model=None, 
            engine_id=self.engine_id, 
            engine_mode='emergency_static', 
            runtime_engine=None, 
            response_source='emergency_static', 
            attempts=[], 
            skipped=[], 
            latency_ms=0.0, 
            degraded=True, 
            degradation_reason='fallback_exhausted',
            metadata={
                'actual_provider': None,
                'actual_model': None,
                'response_source': 'emergency_static',
                'fallback_level': 99,
                'degraded_mode': True,
                'degradation_type': 'fallback_exhausted',
                'degradation_reason': 'No configured provider could generate a response.',
            }
        )
