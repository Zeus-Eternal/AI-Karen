"""Response orchestration for the chat pipeline."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List

try:  # pragma: no cover - optional dependency
    from ai_karen_engine.services.correlation_service import get_request_id
except Exception:  # pragma: no cover - fallback when service unavailable
    import uuid

    def get_request_id() -> str:  # type: ignore[override]
        return str(uuid.uuid4())

from .circuit_breaker import CircuitBreaker
from .config import PipelineConfig
from .formatter import DRYFormatter
from .prompt_builder import PromptBuilder
from .protocols import Analyzer, LLMClient, Memory

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Histogram

    _RESP_COUNTER = Counter(
        "response_requests_total", "Total response orchestrations", ["status"]
    )
    _LATENCY_HIST = Histogram(
        "response_latency_seconds", "Latency of response orchestration"
    )
except Exception:  # pragma: no cover
    class _DummyMetric:
        def labels(self, **_kwargs):  # type: ignore[override]
            return self

        def inc(self, *_args, **_kwargs):  # type: ignore[override]
            pass

        def observe(self, *_args, **_kwargs):  # type: ignore[override]
            pass

    _RESP_COUNTER = _DummyMetric()
    _LATENCY_HIST = _DummyMetric()

logger = logging.getLogger(__name__)


class ResponseOrchestrator:
    """Coordinates analysis, memory, and model generation."""

    def __init__(
        self,
        config: PipelineConfig,
        analyzer: Analyzer,
        memory: Memory,
        llm_client: LLMClient,
        prompt_builder: PromptBuilder | None = None,
        formatter: DRYFormatter | None = None,
        breaker: CircuitBreaker | None = None,
    ) -> None:
        self.config = config
        self.analyzer = analyzer
        self.memory = memory
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder or PromptBuilder(config.template_dir)
        self.formatter = formatter or DRYFormatter()
        self.breaker = breaker or CircuitBreaker()

    def build_prompt(
        self, user_input: str, context: List[str], analysis: Dict[str, Any]
    ) -> str:
        """Create a prompt from context, input, and analysis."""

        persona = analysis.get("persona", "assistant")
        gaps = analysis.get("profile_gaps")
        return self.prompt_builder.build(
            persona=persona,
            user_input=user_input,
            context=context,
            profile_gaps=gaps,
            system_prompts=self.config.system_prompts,
            max_history=self.config.max_history,
        )

    def respond(
        self,
        conversation_id: str,
        user_input: str,
        correlation_id: str | None = None,
        **llm_kwargs: Any,
    ) -> str:
        """Generate a model response for *user_input* in *conversation_id*."""

        start = time.time()
        correlation_id = correlation_id or get_request_id()
        if not self.breaker.allow():
            logger.warning(
                "Circuit breaker open", extra={"correlation_id": correlation_id}
            )
            _RESP_COUNTER.labels(status="open").inc()
            _LATENCY_HIST.observe(time.time() - start)
            return self.config.safe_default

        try:
            analysis = self.analyzer.analyze(user_input)
            context = self.memory.fetch_context(conversation_id, correlation_id)
            prompt = self.build_prompt(user_input, context, analysis)
            llm_kwargs.setdefault("model", self.config.model)
            if self.config.fallback_model is not None:
                llm_kwargs.setdefault("fallback_model", self.config.fallback_model)
            response = self.llm_client.generate(prompt, **llm_kwargs)
            formatted = self.formatter.format("Response", response)
            self.memory.store(
                conversation_id, user_input, formatted, correlation_id=correlation_id
            )
            self.breaker.record_success()
            duration = time.time() - start
            _RESP_COUNTER.labels(status="success").inc()
            _LATENCY_HIST.observe(duration)
            logger.info(
                "Generated response",
                extra={"correlation_id": correlation_id, "duration_ms": duration * 1000},
            )
            return formatted
        except Exception as exc:
            self.breaker.record_failure()
            duration = time.time() - start
            _RESP_COUNTER.labels(status="error").inc()
            _LATENCY_HIST.observe(duration)
            logger.exception(
                "Response generation failed",
                extra={"correlation_id": correlation_id},
            )
            return self.config.safe_default

    def diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information for health checks."""
        info: Dict[str, Any] = {"circuit_breaker": self.breaker.state}
        if hasattr(self.memory, "diagnostics"):
            info["memory"] = self.memory.diagnostics()
        return info
