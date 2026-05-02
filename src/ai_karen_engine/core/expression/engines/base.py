from __future__ import annotations
from ..contracts import EngineHealth, ExpressionResult, ExpressionTask

class BaseExpressionEngine:
    engine_id = 'base'
    async def generate(self, task: ExpressionTask) -> ExpressionResult:
        raise NotImplementedError
    async def health(self) -> EngineHealth:
        return EngineHealth(engine_id=self.engine_id, status='healthy', capabilities=[], models=[])
