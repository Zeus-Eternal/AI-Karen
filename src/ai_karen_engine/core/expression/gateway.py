from __future__ import annotations
from .contracts import ExpressionResult, ExpressionTask
from .circuit_breakers import ExpressionCircuitBreakers
from .observability import emit_expression_event
from .registry import get_engine
from .settings import ExpressionSettings

class ExpressionGateway:
    def __init__(self, settings: ExpressionSettings | None = None):
        self.settings = settings or ExpressionSettings()
        self.circuits = ExpressionCircuitBreakers()

    def _event_payload(self, task: ExpressionTask, **extra):
        return {
            "correlation_id": task.correlation_id,
            "request_id": task.request_id,
            "response_mode": task.response_mode,
            "capabilities": task.required_capabilities,
            **extra,
        }

    async def generate(self, task: ExpressionTask) -> ExpressionResult:
        emit_expression_event("expression.task.started", self._event_payload(task, engine_id=self.settings.active_engine))
        cfg = self.settings.engines.get(self.settings.active_engine)
        if not cfg or not cfg.enabled:
            emit_expression_event("expression.engine.skipped", self._event_payload(task, engine_id=self.settings.active_engine, degradation_reason="engine_unavailable", degraded=True))
            engine = get_engine("disabled", "disabled_engine")
            return await engine.generate(task)

        if self.circuits.is_open(f"expression.engine.{self.settings.active_engine}"):
            emit_expression_event("expression.engine.skipped", self._event_payload(task, engine_id=self.settings.active_engine, degradation_reason="engine_circuit_open", degraded=True))
            if not cfg.fallback_eligible:
                emit_expression_event("expression.emergency.used", self._event_payload(task, engine_id="disabled", degraded=True, degradation_reason="engine_circuit_open"))
                engine = get_engine("disabled", "disabled_engine")
                return await engine.generate(task)

        emit_expression_event("expression.engine.selected", self._event_payload(task, engine_id=self.settings.active_engine, engine_type=cfg.type))
        engine = get_engine(self.settings.active_engine, cfg.type)
        emit_expression_event("expression.engine.request.started", self._event_payload(task, engine_id=self.settings.active_engine, engine_type=cfg.type, provider=task.preferred_provider, model=task.preferred_model))
        try:
            result = await engine.generate(task)
        except Exception as exc:
            self.circuits.mark_failure(f"expression.engine.{self.settings.active_engine}")
            emit_expression_event("expression.engine.request.failed", self._event_payload(task, engine_id=self.settings.active_engine, engine_type=cfg.type, degraded=True, degradation_reason=str(exc)))
            emit_expression_event("expression.fallback.started", self._event_payload(task, engine_id="disabled", fallback_level=1, degraded=True))
            engine = get_engine("disabled", "disabled_engine")
            result = await engine.generate(task)
            emit_expression_event("expression.fallback.completed", self._event_payload(task, engine_id=result.engine_id, provider=result.provider, model=result.model, fallback_level=1, degraded=True, degradation_reason=result.degradation_reason))
            return result

        if not result.text.strip():
            emit_expression_event("expression.output.invalid", self._event_payload(task, engine_id=result.engine_id, provider=result.provider, model=result.model, degraded=True, degradation_reason="empty_output"))
            self.circuits.mark_failure(f"validation.{result.model or 'unknown'}")
        else:
            self.circuits.mark_success(f"expression.engine.{self.settings.active_engine}")
        emit_expression_event("expression.engine.request.completed", self._event_payload(task, engine_id=result.engine_id, engine_type=cfg.type, provider=result.provider, model=result.model, latency_ms=result.latency_ms, degraded=result.degraded, degradation_reason=result.degradation_reason, fallback_level=result.metadata.get("fallback_level", 0) if isinstance(result.metadata, dict) else 0, policy_rejections=result.metadata.get("policy_rejections", []) if isinstance(result.metadata, dict) else []))
        return result
