from __future__ import annotations
from .contracts import ExpressionResult, ExpressionTask
from .circuit_breakers import ExpressionCircuitBreakers
from .observability import emit_expression_event
from .registry import get_engine
from .settings import ExpressionSettings
from ..response.response_validator import validate_response_text

class ExpressionGateway:
    def __init__(self, settings: ExpressionSettings | None = None):
        self.settings = settings or ExpressionSettings.load_from_config()
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
        
        # Build the actual execution sequence (max 5 steps)
        # Sequence starts with the active engine, then follows the fallback order.
        # Fixed 5th step is always 'disabled' (Emergency Static).
        fallback_order = self.settings.engine_fallback_order
        sequence = []
        if self.settings.active_engine not in sequence:
             sequence.append(self.settings.active_engine)
             
        for engine_id in fallback_order:
            if engine_id not in sequence and len(sequence) < 4:
                sequence.append(engine_id)
        
        # Step 5: Always Emergency Static
        sequence.append("disabled")

        last_error = None
        skipped_engines = []
        
        for level, engine_id in enumerate(sequence):
            # Resolve config
            cfg = self.settings.engines.get(engine_id)
            if engine_id == "disabled":
                # Emergency static is always enabled and fallback-eligible
                cfg = EngineConfig(enabled=True, type="disabled_engine", fallback_eligible=True)
            
            if not cfg or not cfg.enabled:
                skipped_engines.append({"engine_id": engine_id, "reason": "disabled"})
                continue

            if engine_id != "disabled" and self.circuits.is_open(f"expression.engine.{engine_id}"):
                skipped_engines.append({"engine_id": engine_id, "reason": "circuit_open"})
                continue

            emit_expression_event("expression.engine.selected", self._event_payload(task, engine_id=engine_id, engine_type=cfg.type, fallback_level=level))
            engine = get_engine(engine_id, cfg.type)
            
            # If engine_id is a specific provider, override preference for this attempt
            original_provider = task.preferred_provider
            original_model = task.preferred_model
            
            from ..model_runtime.provider_policy import evaluate_provider_policy
            decision = evaluate_provider_policy(engine_id)
            if decision.classification != "unknown":
                 task.preferred_provider = engine_id
            
            # Inject engine-specific overrides from config metadata
            if cfg and cfg.metadata:
                 if "preferred_provider" in cfg.metadata:
                      task.preferred_provider = cfg.metadata["preferred_provider"]
                 if "preferred_model" in cfg.metadata:
                      task.preferred_model = cfg.metadata["preferred_model"]

            emit_expression_event("expression.engine.request.started", self._event_payload(task, engine_id=engine_id, engine_type=cfg.type, provider=task.preferred_provider, model=task.preferred_model))
            
            try:
                result = await engine.generate(task)
                
                # Validate the generated output
                is_valid = validate_response_text(result.text)
                
                if result.text.strip() and is_valid:
                    if engine_id != "disabled":
                        self.circuits.mark_success(f"expression.engine.{engine_id}")
                    
                    # Update metadata with execution details
                    if level > 0:
                        result.metadata = {**(result.metadata or {}), "fallback_level": level, "skipped_engines": skipped_engines}
                    
                    emit_expression_event("expression.engine.request.completed", self._event_payload(task, engine_id=result.engine_id, engine_type=cfg.type, provider=result.provider, model=result.model, latency_ms=result.latency_ms, degraded=result.degraded, fallback_level=level))
                    return result
                else:
                    reason = "invalid_output" if not is_valid else "empty_output"
                    emit_expression_event("expression.output.invalid", self._event_payload(task, engine_id=result.engine_id, provider=result.provider, model=result.model, degraded=True, degradation_reason=reason))
                    if engine_id != "disabled":
                        self.circuits.mark_failure(f"validation.{result.model or 'unknown'}")
                    skipped_engines.append({"engine_id": engine_id, "reason": reason})

            except Exception as exc:
                if engine_id != "disabled":
                    self.circuits.mark_failure(f"expression.engine.{engine_id}")
                last_error = str(exc)
                emit_expression_event("expression.engine.request.failed", self._event_payload(task, engine_id=engine_id, engine_type=cfg.type, degraded=True, degradation_reason=last_error))
                skipped_engines.append({"engine_id": engine_id, "reason": "exception", "error": last_error})
            finally:
                # Restore original preference
                task.preferred_provider = original_provider
                task.preferred_model = original_model
                
            if engine_id != "disabled" and not cfg.fallback_eligible and level == 0:
                # If active engine is not fallback eligible and it was the first attempt, we stop early
                # unless it's the fixed emergency step.
                break

        # If we reached here, even Emergency Static failed (extremely unlikely)
        return ExpressionResult(
            task_id=task.task_id,
            text="System is operating in restricted mode. Expression engine unavailable.",
            provider="system",
            model="static",
            engine_id="disabled",
            engine_mode="emergency",
            runtime_engine=None,
            response_source="system_failure",
            latency_ms=0,
            degraded=True,
            degradation_reason="all_engines_failed"
        )
