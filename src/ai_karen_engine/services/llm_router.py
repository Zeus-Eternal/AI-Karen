"""
LLM Router Service
Manages LLM provider selection, routing, and fallback logic with local-first priority
"""

import asyncio
import inspect
import logging
import random
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Union

from ai_karen_engine.integrations.llm_registry import get_registry, LLMRegistry
from ai_karen_engine.integrations.llm_utils import LLMProviderBase

logger = logging.getLogger(__name__)


class ProviderPriority(Enum):
    """Provider priority levels"""
    LOCAL = 1      # Ollama, llama.cpp
    REMOTE = 2     # OpenAI, Anthropic, Gemini
    FALLBACK = 3   # Last resort providers


@dataclass
class ProviderHealth:
    """Provider health status"""
    name: str
    is_healthy: bool
    last_check: float
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    last_failure: Optional[float] = None
    circuit_open_until: float = 0.0
    rate_limited_until: float = 0.0
    requests_in_window: int = 0
    window_start: float = 0.0
    latency_samples: List[float] = field(default_factory=list)
    last_exception_type: Optional[str] = None
    total_requests: int = 0


@dataclass
class ChatRequest:
    """Chat request model for LLM Router"""
    message: str
    context: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None
    memory_context: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None
    preferred_model: Optional[str] = None
    platform: str = "web"
    conversation_id: Optional[str] = None
    stream: bool = True
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class LLMRouter:
    """
    LLM Router with local-first provider selection and health monitoring
    """
    
    def __init__(self, registry: Optional[LLMRegistry] = None):
        """Initialize LLM Router"""
        self.registry = registry or get_registry()
        self.provider_health: Dict[str, ProviderHealth] = {}
        self.health_check_interval = 300  # 5 minutes
        self.max_consecutive_failures = 3
        self.response_timeout = 30  # seconds

        # Retry/circuit breaker configuration
        self.retry_attempts = 3
        self.retry_initial_delay = 1.0
        self.retry_backoff_factor = 2.0
        self.retry_max_delay = 10.0
        self.retry_jitter = 0.5

        self.circuit_breaker_threshold = 3
        self.circuit_breaker_timeout = 60.0

        self.rate_limit_backoff = 15.0
        self.latency_history_size = 20

        self.default_rate_limit = {"max_requests": 30, "window_seconds": 60}
        self.rate_limit_config: Dict[str, Dict[str, float]] = {
            "openai": {"max_requests": 60, "window_seconds": 60},
            "anthropic": {"max_requests": 30, "window_seconds": 60},
            "gemini": {"max_requests": 40, "window_seconds": 60},
            "deepseek": {"max_requests": 40, "window_seconds": 60},
        }
        
        # Provider priority mapping
        self.provider_priorities = {
            "llama_cpp": ProviderPriority.LOCAL,
            "openai": ProviderPriority.REMOTE,
            "anthropic": ProviderPriority.REMOTE,
            "gemini": ProviderPriority.REMOTE,
            "deepseek": ProviderPriority.REMOTE,
            "huggingface": ProviderPriority.FALLBACK,
            # CopilotKit removed - it's a UI framework, not an LLM provider
        }
        
        # Initialize health monitoring
        self._initialize_health_monitoring()
    
    def _initialize_health_monitoring(self):
        """Initialize health monitoring for all providers"""
        for provider_name in self.registry.list_providers():
            self.provider_health[provider_name] = ProviderHealth(
                name=provider_name,
                is_healthy=True,  # Assume healthy initially
                last_check=0,
                consecutive_failures=0,
                window_start=time.time(),
            )
    
    async def select_provider(
        self,
        request: ChatRequest,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[tuple[str, Optional[str]]]:
        """Select the best available provider based on local-first priority."""

        user_preferences = user_preferences or {}
        preferred_provider = user_preferences.get("preferred_llm_provider")
        preferred_model = request.preferred_model or user_preferences.get("preferred_model")

        # If model specified with provider prefix, split it
        if preferred_model and ":" in preferred_model:
            provider_part, model_part = preferred_model.split(":", 1)
            preferred_provider = preferred_provider or provider_part
            preferred_model = model_part

        # Validate preferred provider/model combination
        if preferred_provider and preferred_model:
            info = self.registry.get_provider_info(preferred_provider)
            if info and info.get("default_model") == preferred_model and await self._is_provider_healthy(preferred_provider):
                logger.info(
                    "Using user preferred provider/model: %s/%s",
                    preferred_provider,
                    preferred_model,
                )
                return preferred_provider, preferred_model
            else:
                logger.warning(
                    "Preferred model %s not available for provider %s", preferred_model, preferred_provider
                )
                preferred_provider = None
                preferred_model = None

        # If only preferred model specified, find provider by model
        if preferred_model and not preferred_provider:
            for name in self.registry.list_providers():
                info = self.registry.get_provider_info(name)
                if info and info.get("default_model") == preferred_model:
                    if await self._is_provider_healthy(name):
                        logger.info("Selected provider %s for model %s", name, preferred_model)
                        return name, preferred_model
            logger.warning("Preferred model %s not available; falling back", preferred_model)
            preferred_model = None

        # Preferred provider without model
        if preferred_provider and await self._is_provider_healthy(preferred_provider):
            logger.info(f"Using user preferred provider: {preferred_provider}")
            info = self.registry.get_provider_info(preferred_provider)
            model_name = info.get("default_model") if info else None
            return preferred_provider, model_name

        # Get available providers sorted by priority
        available_providers = await self._get_available_providers_by_priority()

        # Filter by requirements
        suitable_providers: List[str] = []
        for provider_name in available_providers:
            if await self._meets_requirements(provider_name, request):
                suitable_providers.append(provider_name)

        if not suitable_providers:
            logger.warning("No suitable providers found for request")
            return None

        selected_provider = suitable_providers[0]
        info = self.registry.get_provider_info(selected_provider)
        model_name = info.get("default_model") if info else None
        logger.info(f"Selected provider: {selected_provider}")
        return selected_provider, model_name
    
    async def _get_available_providers_by_priority(self) -> List[str]:
        """Get available providers sorted by priority (local first)"""
        providers_by_priority = {
            ProviderPriority.LOCAL: [],
            ProviderPriority.REMOTE: [],
            ProviderPriority.FALLBACK: []
        }
        
        # Categorize providers by priority
        for provider_name in self.registry.list_providers():
            if await self._is_provider_healthy(provider_name):
                priority = self.provider_priorities.get(provider_name, ProviderPriority.FALLBACK)
                providers_by_priority[priority].append(provider_name)
        
        # Return sorted list (local first)
        sorted_providers = []
        for priority in [ProviderPriority.LOCAL, ProviderPriority.REMOTE, ProviderPriority.FALLBACK]:
            sorted_providers.extend(providers_by_priority[priority])
        
        return sorted_providers
    
    async def _meets_requirements(self, provider_name: str, request: ChatRequest) -> bool:
        """Check if provider meets request requirements"""
        provider_info = self.registry.get_provider_info(provider_name)
        if not provider_info:
            return False
        
        # Check streaming requirement
        if request.stream and not provider_info.get("supports_streaming", False):
            return False
        
        # Check if API key is required and available
        if provider_info.get("requires_api_key", False):
            # TODO: Check if API key is configured
            pass
        
        return True
    
    async def _is_provider_healthy(self, provider_name: str) -> bool:
        """Check if provider is healthy"""
        if provider_name not in self.provider_health:
            return False
        
        health = self.provider_health[provider_name]
        
        # Check if health check is recent enough
        if time.time() - health.last_check > self.health_check_interval:
            await self._perform_health_check(provider_name)

        # Circuit breaker handling
        if health.circuit_open_until:
            if time.time() < health.circuit_open_until:
                logger.debug(
                    "Provider %s circuit breaker open for %.2fs",
                    provider_name,
                    health.circuit_open_until - time.time(),
                )
                return False
            health.circuit_open_until = 0.0
            health.consecutive_failures = 0

        # Rate limit cooldowns
        if health.rate_limited_until and time.time() < health.rate_limited_until:
            return False
        if health.rate_limited_until and time.time() >= health.rate_limited_until:
            health.rate_limited_until = 0.0

        return health.is_healthy and health.consecutive_failures < self.max_consecutive_failures
    
    async def _perform_health_check(self, provider_name: str):
        """Perform health check on a provider"""
        try:
            start_time = time.time()
            health_result = self.registry.health_check(provider_name)
            response_time = time.time() - start_time
            
            health = self.provider_health[provider_name]
            health.last_check = time.time()
            health.response_time = response_time
            
            if health_result.get("status") == "healthy":
                health.is_healthy = True
                health.consecutive_failures = 0
                health.error_message = None
                health.last_exception_type = None
            else:
                health.is_healthy = False
                health.consecutive_failures += 1
                health.error_message = health_result.get("error", "Unknown error")
                health.last_exception_type = "HealthCheckError"
            
            logger.debug(f"Health check for {provider_name}: {health_result}")
            
        except Exception as e:
            health = self.provider_health[provider_name]
            health.last_check = time.time()
            health.is_healthy = False
            health.consecutive_failures += 1
            health.error_message = str(e)
            health.last_exception_type = type(e).__name__
            
            logger.error(f"Health check failed for {provider_name}: {e}")
    
    async def process_chat_request(
        self,
        request: ChatRequest,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Process chat request with automatic provider selection and fallback
        """
        request_id = f"llm-router-{uuid.uuid4()}"
        failure_records: List[Dict[str, str]] = []

        selection = await self.select_provider(request, user_preferences)
        if not selection:
            logger.error(
                "[%s] No suitable provider available; invoking degraded mode fallback",
                request_id,
            )
            degraded_message = await self._generate_degraded_fallback(
                request,
                failure_records,
                reason=None,
            )
            if degraded_message:
                yield degraded_message
                return
            raise RuntimeError("No suitable provider available")

        provider_name, model_name = selection

        try:
            async for chunk in self._attempt_provider_with_retries(
                provider_name,
                request,
                request_id=request_id,
                model_name=model_name,
            ):
                yield chunk
            return
        except ProviderProcessingError as error:
            logger.warning(
                "[%s] Provider %s failed after retries: %s",
                request_id,
                provider_name,
                error,
            )
            await self._mark_provider_unhealthy(provider_name, str(error))
            failure_records.append({
                "provider": provider_name,
                "error": str(error.last_error) if error.last_error else str(error),
            })

        fallback_providers = await self._get_fallback_providers(provider_name, request)
        for fallback_provider in fallback_providers:
            try:
                logger.info(
                    "[%s] Trying fallback provider: %s",
                    request_id,
                    fallback_provider,
                )
                async for chunk in self._attempt_provider_with_retries(
                    fallback_provider,
                    request,
                    request_id=request_id,
                    model_name=None,
                ):
                    yield chunk
                return
            except ProviderProcessingError as error:
                logger.warning(
                    "[%s] Fallback provider %s failed: %s",
                    request_id,
                    fallback_provider,
                    error,
                )
                await self._mark_provider_unhealthy(fallback_provider, str(error))
                failure_records.append({
                    "provider": fallback_provider,
                    "error": str(error.last_error) if error.last_error else str(error),
                })

        degraded_reason = self._infer_degraded_reason(failure_records)
        degraded_message = await self._generate_degraded_fallback(
            request,
            failure_records,
            reason=degraded_reason,
        )
        if degraded_message:
            yield degraded_message
            return

        raise RuntimeError("All providers failed to process the request")
    
    async def _process_with_provider(
        self,
        provider_name: str,
        request: ChatRequest,
        model_name: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Process request with a specific provider"""
        if model_name:
            provider = self.registry.get_provider(provider_name, model=model_name)
        else:
            provider = self.registry.get_provider(provider_name)
        if not provider:
            raise RuntimeError(f"Could not get provider instance: {provider_name}")

        provider_params = {
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        provider_params = {k: v for k, v in provider_params.items() if v is not None}

        if request.stream:
            stream_callable = getattr(provider, "stream_response", None)
            if stream_callable:
                stream_result = stream_callable(request.message, **provider_params)
                if inspect.isawaitable(stream_result):
                    stream_result = await stream_result

                if stream_result is not None:
                    if hasattr(stream_result, "__aiter__"):
                        async for chunk in stream_result:
                            yield chunk
                        return
                    if hasattr(stream_result, "__iter__") and not isinstance(stream_result, (str, bytes)):
                        for chunk in stream_result:
                            yield chunk
                        return
                    yield stream_result
                    return

            stream_generate = getattr(provider, "stream_generate", None)
            if stream_generate:
                stream_result = stream_generate(request.message, **provider_params)
                if stream_result is not None:
                    if hasattr(stream_result, "__iter__") and not isinstance(stream_result, (str, bytes)):
                        for chunk in stream_result:
                            yield chunk
                        return
                    yield stream_result
                    return

        generator_callable = getattr(provider, "generate_response", None)
        if generator_callable is None:
            generator_callable = getattr(provider, "generate_text", None)
        if generator_callable is None:
            raise RuntimeError(f"Provider {provider_name} does not support text generation")

        result = generator_callable(request.message, **provider_params)
        if inspect.isawaitable(result):
            result = await result
        yield result
    
    async def _get_fallback_providers(
        self,
        failed_provider: str,
        request: ChatRequest
    ) -> List[str]:
        """Get fallback providers excluding the failed one"""
        all_providers = await self._get_available_providers_by_priority()
        fallback_providers = []
        
        for provider_name in all_providers:
            if (provider_name != failed_provider and 
                await self._is_provider_healthy(provider_name) and
                await self._meets_requirements(provider_name, request)):
                fallback_providers.append(provider_name)
        
        return fallback_providers[:2]  # Limit to 2 fallback attempts
    
    async def _mark_provider_unhealthy(self, provider_name: str, error_message: str):
        """Mark provider as unhealthy"""
        if provider_name in self.provider_health:
            health = self.provider_health[provider_name]
            health.is_healthy = False
            health.consecutive_failures += 1
            health.error_message = error_message
            health.last_check = time.time()
            health.last_failure = time.time()
            health.last_exception_type = "ProviderError"

            if health.consecutive_failures >= self.circuit_breaker_threshold:
                health.circuit_open_until = time.time() + self.circuit_breaker_timeout
                logger.error(
                    "Provider %s circuit breaker opened for %.0f seconds",
                    provider_name,
                    self.circuit_breaker_timeout,
                )
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {
            "providers": {},
            "health_summary": {
                "healthy": 0,
                "unhealthy": 0,
                "total": len(self.provider_health)
            }
        }
        
        for provider_name, health in self.provider_health.items():
            provider_info = self.registry.get_provider_info(provider_name)
            priority = self.provider_priorities.get(provider_name, ProviderPriority.FALLBACK)
            latency_metrics = self._calculate_latency_metrics(health)

            status["providers"][provider_name] = {
                "is_healthy": health.is_healthy,
                "consecutive_failures": health.consecutive_failures,
                "last_check": health.last_check,
                "response_time": health.response_time,
                "error_message": health.error_message,
                "priority": priority.name,
                "supports_streaming": provider_info.get("supports_streaming", False) if provider_info else False,
                "requires_api_key": provider_info.get("requires_api_key", False) if provider_info else False,
                "circuit_open_until": health.circuit_open_until,
                "rate_limited_until": health.rate_limited_until,
                "latency_ms_avg": latency_metrics.get("avg_ms"),
                "latency_ms_p95": latency_metrics.get("p95_ms"),
                "total_requests": health.total_requests,
            }

            if health.is_healthy:
                status["health_summary"]["healthy"] += 1
            else:
                status["health_summary"]["unhealthy"] += 1

        return status

    async def _attempt_provider_with_retries(
        self,
        provider_name: str,
        request: ChatRequest,
        request_id: str,
        model_name: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Attempt provider execution with retries, metrics, and rate limiting."""

        await self._respect_rate_limit(provider_name)
        errors: List[Exception] = []
        delay = self.retry_initial_delay

        for attempt in range(1, self.retry_attempts + 1):
            start_time = time.time()
            try:
                async for chunk in self._instrumented_provider_call(
                    provider_name,
                    request,
                    model_name=model_name,
                    request_id=request_id,
                    attempt=attempt,
                ):
                    yield chunk

                duration = time.time() - start_time
                self._record_provider_success(provider_name, duration)
                self._log_provider_attempt(
                    provider_name,
                    request_id,
                    attempt,
                    duration,
                    success=True,
                )
                return
            except Exception as exc:
                duration = time.time() - start_time
                errors.append(exc)
                self._record_provider_failure(provider_name, duration, exc)
                self._log_provider_attempt(
                    provider_name,
                    request_id,
                    attempt,
                    duration,
                    success=False,
                    error=exc,
                )

                if attempt >= self.retry_attempts:
                    break

                sleep_for = min(delay, self.retry_max_delay)
                jitter = random.uniform(0, self.retry_jitter)
                logger.debug(
                    "[%s] Provider %s retrying in %.2fs (attempt %d/%d)",
                    request_id,
                    provider_name,
                    sleep_for + jitter,
                    attempt,
                    self.retry_attempts,
                )
                await asyncio.sleep(sleep_for + jitter)
                delay *= self.retry_backoff_factor

        raise ProviderProcessingError(provider_name, errors)

    async def _instrumented_provider_call(
        self,
        provider_name: str,
        request: ChatRequest,
        model_name: Optional[str],
        request_id: str,
        attempt: int,
    ) -> AsyncIterator[str]:
        """Execute provider call while logging attempt metadata."""

        logger.debug(
            "[%s] Executing provider %s (attempt %d) streaming=%s",
            request_id,
            provider_name,
            attempt,
            request.stream,
        )

        async for chunk in self._process_with_provider(provider_name, request, model_name):
            yield chunk

    def _log_provider_attempt(
        self,
        provider_name: str,
        request_id: str,
        attempt: int,
        duration: float,
        success: bool,
        error: Optional[BaseException] = None,
    ) -> None:
        """Log structured provider attempt outcomes."""

        if success:
            logger.info(
                "[%s] Provider %s succeeded on attempt %d in %.2fs",
                request_id,
                provider_name,
                attempt,
                duration,
            )
        else:
            logger.warning(
                "[%s] Provider %s failed on attempt %d in %.2fs: %s",
                request_id,
                provider_name,
                attempt,
                duration,
                error,
            )

    async def _respect_rate_limit(self, provider_name: str) -> None:
        """Best-effort rate limiting to avoid exhausting provider quotas."""

        health = self.provider_health.get(provider_name)
        if not health:
            return

        if health.rate_limited_until and time.time() < health.rate_limited_until:
            sleep_for = health.rate_limited_until - time.time()
            if sleep_for > 0:
                logger.warning(
                    "Provider %s temporarily rate limited; sleeping for %.2fs",
                    provider_name,
                    sleep_for,
                )
                await asyncio.sleep(sleep_for)
            health.rate_limited_until = 0.0

        config = self.rate_limit_config.get(provider_name, self.default_rate_limit)
        window_seconds = float(config.get("window_seconds", 60))
        max_requests = int(config.get("max_requests", 30))

        now = time.time()
        if now - health.window_start > window_seconds:
            health.window_start = now
            health.requests_in_window = 0

        if health.requests_in_window >= max_requests:
            sleep_for = window_seconds - (now - health.window_start)
            if sleep_for > 0:
                logger.warning(
                    "Provider %s reached rate limit window; pausing for %.2fs",
                    provider_name,
                    sleep_for,
                )
                await asyncio.sleep(sleep_for)
            health.window_start = time.time()
            health.requests_in_window = 0

        health.requests_in_window += 1

    def _record_provider_success(self, provider_name: str, latency: float) -> None:
        """Record successful provider execution metrics."""

        health = self.provider_health.get(provider_name)
        if not health:
            return

        health.is_healthy = True
        health.consecutive_failures = 0
        health.error_message = None
        health.last_exception_type = None
        health.total_requests += 1
        health.last_failure = None
        health.circuit_open_until = 0.0

        if len(health.latency_samples) >= self.latency_history_size:
            health.latency_samples.pop(0)
        health.latency_samples.append(latency)

    def _record_provider_failure(
        self,
        provider_name: str,
        latency: float,
        error: BaseException,
    ) -> None:
        """Record provider failure and update circuit breaker/rate limits."""

        health = self.provider_health.get(provider_name)
        if not health:
            return

        health.is_healthy = False
        health.consecutive_failures += 1
        health.error_message = str(error)
        health.last_failure = time.time()
        health.last_exception_type = type(error).__name__
        if len(health.latency_samples) >= self.latency_history_size:
            health.latency_samples.pop(0)
        health.latency_samples.append(latency)

        message = str(error).lower()
        if "rate limit" in message or "429" in message:
            health.rate_limited_until = time.time() + self.rate_limit_backoff

        if health.consecutive_failures >= self.circuit_breaker_threshold:
            health.circuit_open_until = time.time() + self.circuit_breaker_timeout

    def _calculate_latency_metrics(self, health: ProviderHealth) -> Dict[str, float]:
        """Compute latency metrics for provider status output."""

        if not health.latency_samples:
            return {}

        samples = sorted(health.latency_samples)
        average = sum(samples) / len(samples)
        p95_index = max(0, min(len(samples) - 1, int(len(samples) * 0.95) - 1))
        p95_value = samples[p95_index]

        return {"avg_ms": average * 1000, "p95_ms": p95_value * 1000}

    def _infer_degraded_reason(self, failure_records: List[Dict[str, str]]):
        """Infer degraded mode reason from accumulated failure information."""

        from ai_karen_engine.core.degraded_mode import DegradedModeReason

        if not failure_records:
            return DegradedModeReason.ALL_PROVIDERS_FAILED

        combined = " ".join(
            record.get("error", "") for record in failure_records if record.get("error")
        ).lower()

        if any(keyword in combined for keyword in ("rate limit", "429")):
            return DegradedModeReason.API_RATE_LIMITS
        if any(keyword in combined for keyword in ("timeout", "timed out", "connection", "network")):
            return DegradedModeReason.NETWORK_ISSUES
        if any(keyword in combined for keyword in ("quota", "exhaust", "memory", "resource")):
            return DegradedModeReason.RESOURCE_EXHAUSTION

        return DegradedModeReason.ALL_PROVIDERS_FAILED

    async def _generate_degraded_fallback(
        self,
        request: ChatRequest,
        failure_records: List[Dict[str, str]],
        reason,
    ) -> Optional[str]:
        """Generate degraded mode fallback response when LLMs are unavailable."""

        try:
            from ai_karen_engine.core.degraded_mode import (
                DegradedModeReason,
                get_degraded_mode_manager,
            )

            manager = get_degraded_mode_manager()
            failed_providers = [record.get("provider", "unknown") for record in failure_records]
            degraded_reason = reason or DegradedModeReason.ALL_PROVIDERS_FAILED

            manager.activate_degraded_mode(degraded_reason, failed_providers)
            envelope = await manager.generate_degraded_response(
                request.message,
                context=request.context or {},
            )

            if isinstance(envelope, dict):
                final_text = envelope.get("final") or envelope.get("response")
                if final_text:
                    logger.error(
                        "Returning degraded mode response due to provider failures: %s",
                        failed_providers,
                    )
                    return final_text
        except Exception as degraded_error:  # pragma: no cover - defensive fallback
            logger.exception("Failed to generate degraded mode response: %s", degraded_error)

        return None

    async def refresh_provider_health(self):
        """Refresh health status for all providers"""
        logger.info("Refreshing provider health status")

        tasks = []
        for provider_name in self.provider_health.keys():
            tasks.append(self._perform_health_check(provider_name))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Provider health refresh completed")
    
    @classmethod
    def default(cls) -> 'LLMRouter':
        """Create default LLM Router instance"""
        return cls()


# Helper exceptions
class ProviderProcessingError(RuntimeError):
    """Raised when a provider fails after exhausting retry attempts."""

    def __init__(self, provider_name: str, errors: Sequence[BaseException]):
        self.provider_name = provider_name
        self.errors = list(errors)
        self.last_error: Optional[BaseException] = self.errors[-1] if self.errors else None

        unique_messages: List[str] = []
        for error in self.errors:
            message = str(error)
            if message and message not in unique_messages:
                unique_messages.append(message)

        attempts = len(self.errors) or 1
        summary = "; ".join(unique_messages) if unique_messages else "unknown error"
        super().__init__(f"{provider_name} failed after {attempts} attempts: {summary}")


# Global router instance
_router_instance: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Get global LLM Router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter.default()
    return _router_instance
