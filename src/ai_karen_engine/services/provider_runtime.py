"""Unified provider runtime service for LLM execution and fallbacks."""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, AsyncIterator

from ai_karen_engine.core.model_runtime.runtime_contracts import (
    ProviderRouteDecision,
    ProviderExecutionResult,
)
from ai_karen_engine.services.models.routing.llm_router_service import ChatRequest, LLMRouter
from ai_karen_engine.services.response import ResponseSanitizer

logger = logging.getLogger(__name__)

class ProviderRuntime:
    """
    Unified runtime for executing LLM requests based on routing decisions.
    Handles execution, retries, and fallback chains.
    """

    def __init__(self, router: Optional[LLMRouter] = None):
        self.router = router or LLMRouter()
        self._response_sanitizer = ResponseSanitizer()

    async def execute(
        self,
        decision: ProviderRouteDecision,
        request: ChatRequest,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> ProviderExecutionResult:
        """
        Execute an LLM request based on a route decision.
        If the primary provider fails, it attempts fallbacks.
        """
        correlation_id = f"exec-{uuid.uuid4()}"
        start_time = time.time()
        
        current_provider = decision.selected_provider
        current_model = decision.selected_model
        
        # Primary execution attempt
        try:
            text = ""
            async for chunk in self.router._attempt_provider_with_retries(
                current_provider,
                request,
                request_id=correlation_id,
                model_name=current_model,
            ):
                if isinstance(chunk, str):
                    text += chunk
            
            latency_ms = (time.time() - start_time) * 1000
            
            return ProviderExecutionResult(
                text=text,
                requested_provider=decision.requested_provider,
                requested_model=decision.requested_model,
                selected_provider=decision.selected_provider,
                selected_model=decision.selected_model,
                actual_provider=current_provider,
                actual_model=current_model,
                runtime_engine=decision.runtime_engine,
                response_source="provider_runtime",
                fallback_level=decision.fallback_level,
                degraded_mode=decision.degraded_mode,
                degradation_reason=decision.degradation_reason,
                latency_ms=latency_ms,
                correlation_id=correlation_id,
                metadata={"source": "primary_execution"}
            )
            
        except Exception as exc:
            logger.warning(f"Primary provider {current_provider} failed: {exc}. Attempting fallbacks.")
            return await self._execute_fallback_chain(decision, request, exc, start_time, correlation_id)

    async def stream_execute(
        self,
        decision: ProviderRouteDecision,
        request: ChatRequest,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Any]:
        """
        Stream an LLM request based on a route decision.
        Handles fallbacks and yields both content chunks and final execution result.
        """
        correlation_id = f"exec-stream-{uuid.uuid4()}"
        start_time = time.time()
        
        current_provider = decision.selected_provider
        current_model = decision.selected_model
        
        try:
            async for chunk in self.router._attempt_provider_with_retries(
                current_provider,
                request,
                request_id=correlation_id,
                model_name=current_model,
            ):
                yield chunk
            
            latency_ms = (time.time() - start_time) * 1000
            yield ProviderExecutionResult(
                text="", # Content already yielded
                requested_provider=decision.requested_provider,
                requested_model=decision.requested_model,
                selected_provider=decision.selected_provider,
                selected_model=decision.selected_model,
                actual_provider=current_provider,
                actual_model=current_model,
                runtime_engine=decision.runtime_engine,
                response_source="provider_runtime",
                fallback_level=decision.fallback_level,
                degraded_mode=decision.degraded_mode,
                degradation_reason=decision.degradation_reason,
                latency_ms=latency_ms,
                correlation_id=correlation_id,
                metadata={"source": "primary_execution"}
            )
            
        except Exception as exc:
            logger.warning(f"Primary provider {current_provider} failed during stream: {exc}. Attempting fallbacks.")
            # In streaming mode, if we already yielded content, fallback is harder but we try
            fallback_providers = await self.router._get_fallback_providers(current_provider, request)
            
            for i, fallback_provider in enumerate(fallback_providers, 1):
                try:
                    fallback_info = self.router.registry.get_provider_info(fallback_provider)
                    fallback_model = self.router._effective_provider_model(fallback_info)
                    
                    async for chunk in self.router._attempt_provider_with_retries(
                        fallback_provider,
                        request,
                        request_id=correlation_id,
                        model_name=fallback_model,
                    ):
                        yield chunk
                    
                    latency_ms = (time.time() - start_time) * 1000
                    yield ProviderExecutionResult(
                        text="",
                        requested_provider=decision.requested_provider,
                        requested_model=decision.requested_model,
                        selected_provider=decision.selected_provider,
                        selected_model=decision.selected_model,
                        actual_provider=fallback_provider,
                        actual_model=fallback_model or "auto",
                        runtime_engine=fallback_provider.replace("builtin_", ""),
                        response_source="fallback_provider_runtime",
                        fallback_level=decision.fallback_level + i,
                        degraded_mode=True,
                        degradation_reason=f"primary_failed: {str(exc)}",
                        latency_ms=latency_ms,
                        correlation_id=correlation_id,
                        metadata={"source": "fallback_execution"}
                    )
                    return
                except Exception:
                    continue
            
            # Static fallback if all else fails
            degraded_message = await self.router._generate_degraded_fallback(request, [], reason="all_failed")
            yield degraded_message
            yield ProviderExecutionResult(
                text=degraded_message,
                requested_provider=decision.requested_provider,
                requested_model=decision.requested_model,
                selected_provider=decision.selected_provider,
                selected_model=decision.selected_model,
                actual_provider="emergency_static",
                actual_model="none",
                runtime_engine="none",
                response_source="static_fallback",
                fallback_level=99,
                degraded_mode=True,
                degradation_reason="all_providers_failed",
                latency_ms=(time.time() - start_time) * 1000,
                correlation_id=correlation_id,
            )

    async def _execute_fallback_chain(self, decision, request, primary_exc, start_time, correlation_id):
        fallback_providers = await self.router._get_fallback_providers(decision.selected_provider, request)
        
        for i, fallback_provider in enumerate(fallback_providers, 1):
            try:
                fallback_info = self.router.registry.get_provider_info(fallback_provider)
                fallback_model = self.router._effective_provider_model(fallback_info)
                
                text = ""
                async for chunk in self.router._attempt_provider_with_retries(
                    fallback_provider,
                    request,
                    request_id=correlation_id,
                    model_name=fallback_model,
                ):
                    if isinstance(chunk, str):
                        text += chunk
                
                latency_ms = (time.time() - start_time) * 1000
                return ProviderExecutionResult(
                    text=text,
                    requested_provider=decision.requested_provider,
                    requested_model=decision.requested_model,
                    selected_provider=decision.selected_provider,
                    selected_model=decision.selected_model,
                    actual_provider=fallback_provider,
                    actual_model=fallback_model or "auto",
                    runtime_engine=fallback_provider.replace("builtin_", ""),
                    response_source="fallback_provider_runtime",
                    fallback_level=decision.fallback_level + i,
                    degraded_mode=True,
                    degradation_reason=f"primary_failed: {str(primary_exc)}",
                    latency_ms=latency_ms,
                    correlation_id=correlation_id,
                )
            except Exception:
                continue

        # Static fallback
        degraded_message = await self.router._generate_degraded_fallback(request, [], reason="all_failed")
        return ProviderExecutionResult(
            text=degraded_message or "I'm sorry, I'm having trouble connecting to my brain right now.",
            requested_provider=decision.requested_provider,
            requested_model=decision.requested_model,
            selected_provider=decision.selected_provider,
            selected_model=decision.selected_model,
            actual_provider="emergency_static",
            actual_model="none",
            runtime_engine="none",
            response_source="static_fallback",
            fallback_level=99,
            degraded_mode=True,
            degradation_reason="all_providers_failed",
            latency_ms=(time.time() - start_time) * 1000,
            correlation_id=correlation_id,
        )
