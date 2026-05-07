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
        providers_to_try = ["builtin_vllm", "builtin_transformers"]
        pref = str(task.preferred_provider or "").lower()
        if "transformers" in pref:
             providers_to_try = ["builtin_transformers", "builtin_vllm"]
        elif "vllm" in pref:
             providers_to_try = ["builtin_vllm", "builtin_transformers"]

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
                
                # Use central registry to get the provider instance
                from ai_karen_engine.integrations.llm_registry import get_provider
                
                # Resolve model from task or payload
                model_id = payload.get("model")
                
                # Get provider instance
                provider = get_provider(provider_id, model=model_id)
                if not provider:
                    skipped.append({"provider": provider_id, "reason": "provider_not_found"})
                    continue
                
                prompt = self._extract_prompt(payload["messages"])
                
                # Check if generate_text_async exists, fallback to generate_text or generate
                if hasattr(provider, "generate_text_async"):
                     text = await provider.generate_text_async(prompt, **payload)
                elif hasattr(provider, "generate_text"):
                     # Offload sync call
                     loop = asyncio.get_running_loop()
                     text = await loop.run_in_executor(None, lambda: provider.generate_text(prompt, **payload))
                else:
                     # Generic generate
                     loop = asyncio.get_running_loop()
                     text = await loop.run_in_executor(None, lambda: provider.generate(prompt, **payload))
                
                resp_text = str(text or "").strip()
                if resp_text:
                    logger.info(f"BuiltinProviderEngine: Success with {provider_id}")
                    text = resp_text
                    actual_provider = provider_id
                    model = getattr(provider, "model", model_id)
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
