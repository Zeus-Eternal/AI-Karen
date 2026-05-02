from __future__ import annotations

import time
import logging
import asyncio
from typing import Any

from .base import BaseExpressionEngine
from ..contracts import ExpressionResult, ExpressionTask
from ...model_runtime.provider_policy import evaluate_provider_policy

logger = logging.getLogger(__name__)


class BuiltinProviderEngine(BaseExpressionEngine):
    """
    Engine that uses first-party vLLM or Transformers runtimes.
    Strictly limited to 'vllm' and 'transformers' providers.
    """
    engine_id = "builtin"

    async def generate(self, task: ExpressionTask) -> ExpressionResult:
        started = time.perf_counter()
        payload = self._build_payload(task)
        
        # Canonical builtin providers
        providers_to_try = ["vllm", "transformers"]
        if task.preferred_provider == "transformers":
             providers_to_try = ["transformers", "vllm"]

        text = ""
        actual_provider = providers_to_try[0]
        model = None
        attempts = []
        skipped = []

        loop = asyncio.get_event_loop()

        for provider_id in providers_to_try:
            try:
                # Policy check: Must be a builtin engine
                decision = evaluate_provider_policy(provider_id)
                if decision.classification != "builtin_engine":
                    skipped.append({"provider": provider_id, "reason": "not_builtin"})
                    continue

                logger.info(f"BuiltinProviderEngine: Attempting generation with {provider_id}")
                adapter = self._get_adapter(provider_id)
                
                # Run sync generate in thread pool
                response = await loop.run_in_executor(None, lambda: asyncio.run(adapter(payload)))
                
                resp_text = str(response.get("text") or "").strip()
                if resp_text:
                    logger.info(f"BuiltinProviderEngine: Success with {provider_id}")
                    text = resp_text
                    actual_provider = str(response.get("provider") or provider_id)
                    model = response.get("model")
                    break
                else:
                    logger.warning(f"BuiltinProviderEngine: {provider_id} returned empty response")
                    skipped.append({"provider": provider_id, "reason": "empty_response"})
            except Exception as exc:
                logger.error(f"BuiltinProviderEngine: {provider_id} attempt failed: {exc}", exc_info=True)
                attempts.append({"provider": provider_id, "error": str(exc)})
                continue

        return ExpressionResult(
            task_id=task.task_id,
            text=text,
            provider=actual_provider,
            model=str(model) if model else None,
            engine_id=self.engine_id,
            engine_mode="builtin_provider_engine",
            runtime_engine="builtin",
            response_source="builtin_provider_engine",
            attempts=attempts,
            skipped=skipped,
            latency_ms=(time.perf_counter() - started) * 1000,
            degraded=not bool(text.strip()),
            degradation_reason=None if text.strip() else "all_internal_providers_failed",
        )

    def _get_adapter(self, provider_id: str):
        """Resolves the internal runtime adapter for the given provider."""
        import asyncio
        loop = asyncio.get_event_loop()

        if provider_id == "vllm":
            from ai_karen_engine.inference.vllm_runtime import VLLMRuntime
            
            async def vllm_adapter(payload):
                # Ensure runtime is initialized with the requested model
                model_id = payload.get("model") or "auto"
                runtime = VLLMRuntime.get_instance(model=model_id)
                
                prompt = self._extract_prompt(payload["messages"])
                # Run sync generate in thread pool
                text = await loop.run_in_executor(None, lambda: runtime.generate(prompt, **payload))
                return {"text": text, "provider": "vllm", "model": runtime.model}
            
            return vllm_adapter
            
        elif provider_id == "transformers":
            from ai_karen_engine.inference.transformers_runtime import TransformersRuntime
            
            async def transformers_adapter(payload):
                # Ensure runtime is initialized with the requested model
                model_id = payload.get("model")
                if model_id and not model_id.startswith("/") and not model_id.startswith("."):
                    # Try to resolve local path if it's a simple ID
                    from ai_karen_engine.config.config_manager import config_manager
                    tf_dir = config_manager.get_config_value("llm.transformers_dir", default="models/transformers")
                    potential_path = f"{tf_dir}/{model_id}"
                    import os
                    if os.path.exists(potential_path):
                        model_id = potential_path

                runtime = TransformersRuntime.get_instance(model_path=model_id)
                
                # If pipeline isn't warmed yet, try to warm it (sync call in executor)
                if not runtime._pipeline and model_id:
                     await loop.run_in_executor(None, lambda: runtime.warm(model_id))

                prompt = self._extract_prompt(payload["messages"])
                # Run sync generate in thread pool
                text = await loop.run_in_executor(None, lambda: runtime.generate(prompt, **payload))
                return {"text": text, "provider": "transformers", "model": runtime.model_path}
                
            return transformers_adapter
            
        raise ValueError(f"Unknown builtin provider: {provider_id}")

    def _extract_prompt(self, messages: list[dict[str, str]]) -> str:
        """Helper to extract a simple prompt from messages."""
        if not messages:
            return ""
        return messages[-1].get("content", "")

    def _build_payload(self, task: ExpressionTask) -> dict[str, Any]:
        return {
            "messages": task.messages,
            "provider": task.preferred_provider,
            "model": task.preferred_model,
            "max_tokens": task.max_tokens,
            "temperature": task.temperature,
            "timeout_ms": task.timeout_ms,
        }
