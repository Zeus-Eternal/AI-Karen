"""Local-first LLM routing service with health, policy, and metrics support."""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import logging
import os
from pathlib import Path
import random
import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, Iterable, List, Optional, Sequence, Set, Union

from ai_karen_engine.config.llm_provider_config import (
    get_openai_compatible_provider_defaults,
)

from ai_karen_engine.integrations.llm_registry import get_registry, LLMRegistry
from ai_karen_engine.integrations.llm_utils import LLMProviderBase

try:  # pragma: no cover - SecretManager may require optional deps
    from src.services.secret_manager import SecretManager
except Exception:  # pragma: no cover - gracefully handle missing optional dependency
    SecretManager = None  # type: ignore[assignment]


class _DummyMetric:  # type: ignore[too-few-public-methods]
    """Fallback metric collector when prometheus-client is unavailable."""

    def labels(self, **_kwargs: Any) -> "_DummyMetric":
        return self

    def inc(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def observe(self, *_args: Any, **_kwargs: Any) -> None:
        return None


try:  # pragma: no cover - prometheus is optional
    from prometheus_client import Counter, Histogram, REGISTRY

    METRICS_ENABLED = True
except Exception:  # pragma: no cover - optional dependency missing
    METRICS_ENABLED = False
    Counter = Histogram = _DummyMetric  # type: ignore[assignment]


def _get_or_create_metric(name: str, factory) -> Any:
    """Return a metric collector, reusing existing instances when possible."""

    if not METRICS_ENABLED:
        return _DummyMetric()

    if name in REGISTRY._names_to_collectors:  # type: ignore[attr-defined]
        return REGISTRY._names_to_collectors[name]  # type: ignore[index]

    return factory()


PROVIDER_SELECTION_COUNTER = _get_or_create_metric(
    "kari_llm_provider_selections_total",
    lambda: Counter(
        "kari_llm_provider_selections_total",
        "LLM provider selections recorded by the router",
        ["provider", "policy", "result"],
    ),
)

PROVIDER_FALLBACK_COUNTER = _get_or_create_metric(
    "kari_llm_provider_fallbacks_total",
    lambda: Counter(
        "kari_llm_provider_fallbacks_total",
        "Fallback transitions between LLM providers",
        ["from_provider", "to_provider", "reason"],
    ),
)

PROVIDER_LATENCY_HISTOGRAM = _get_or_create_metric(
    "kari_llm_provider_latency_seconds",
    lambda: Histogram(
        "kari_llm_provider_latency_seconds",
        "Observed provider latency from the router",
        ["provider", "policy"],
        buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
    ),
)

PROVIDER_FAILURE_COUNTER = _get_or_create_metric(
    "kari_llm_provider_failures_total",
    lambda: Counter(
        "kari_llm_provider_failures_total",
        "Failures encountered when invoking an LLM provider",
        ["provider", "error_type"],
    ),
)

logger = logging.getLogger(__name__)


class ProviderPriority(Enum):
    """Provider priority levels honoring Kari's local-first doctrine."""

    LOCAL = 1  # llama.cpp, GGUF runtimes
    TRANSFORMER = 2  # Transformers running locally (HF pipelines, GGML wrappers)
    NLP = 3  # spaCy-powered deterministic responders
    LIGHTWEIGHT = 4  # Small distilled models (e.g., DistilBERT, classifiers)
    REMOTE = 5  # Managed APIs (OpenAI, Anthropic, Gemini, etc.)
    FALLBACK = 6  # Deterministic and offline fallbacks


class RoutingPolicy(Enum):
    """Routing policies supported by the router."""

    PRIORITY = "priority"  # Strict local-first priority order
    ROUND_ROBIN = "round_robin"  # Rotate through healthy providers
    HYBRID = "hybrid"  # Local-first buckets with in-bucket rotation


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


PROVIDER_API_KEY_ENV_MAPPING: Dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "zai": "ZAI_API_KEY",
    "huggingface": "HUGGINGFACE_API_KEY",
    "cohere": "COHERE_API_KEY",
    "copilotkit": "COPILOT_API_KEY",
}

NON_CHAT_PROVIDERS: Set[str] = {
    "copilotkit",
    "custom_copilotkit",
}


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

        # Routing policy configuration
        self.routing_policy: RoutingPolicy = RoutingPolicy.PRIORITY
        self.priority_order: List[ProviderPriority] = [
            ProviderPriority.LOCAL,
            ProviderPriority.TRANSFORMER,
            ProviderPriority.NLP,
            ProviderPriority.LIGHTWEIGHT,
            ProviderPriority.REMOTE,
            ProviderPriority.FALLBACK,
        ]
        self._round_robin_offset: int = 0
        self._hybrid_state: Dict[ProviderPriority, int] = {}
        self._secret_manager: Optional[SecretManager] = None
        self._secret_manager_unavailable: bool = False

        # Background health monitoring
        self._health_monitor_task: Optional[asyncio.Task[None]] = None
        self._health_monitor_lock: Optional[asyncio.Lock] = None
        self.background_health_interval = 180  # seconds

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
            "llamacpp": ProviderPriority.LOCAL,
            "llama_cpp": ProviderPriority.LOCAL,
            "transformers": ProviderPriority.TRANSFORMER,
            "huggingface": ProviderPriority.TRANSFORMER,
            "spacy": ProviderPriority.NLP,
            "distilbert": ProviderPriority.LIGHTWEIGHT,
            "openai": ProviderPriority.REMOTE,
            "zai": ProviderPriority.REMOTE,
            "anthropic": ProviderPriority.REMOTE,
            "gemini": ProviderPriority.REMOTE,
            "deepseek": ProviderPriority.REMOTE,
            "fallback": ProviderPriority.FALLBACK,
        }

        # Initialize health monitoring
        self._initialize_health_monitoring()

    def configure_routing(
        self,
        policy: RoutingPolicy = RoutingPolicy.PRIORITY,
        priority_order: Optional[Iterable[ProviderPriority]] = None,
    ) -> None:
        """Configure routing policy and priority ordering at runtime."""

        self.routing_policy = policy
        if priority_order:
            ordered = list(dict.fromkeys(priority_order))
            if not ordered:
                raise ValueError("priority_order must contain at least one priority")
            self.priority_order = ordered

        # Reset rotation state when configuration changes
        self._round_robin_offset = 0
        self._hybrid_state.clear()

    def set_provider_priority(self, provider_name: str, priority: ProviderPriority) -> None:
        """Override the priority bucket for a specific provider."""

        self.provider_priorities[provider_name] = priority
    
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

        await self._ensure_background_health_task()
        user_preferences = user_preferences or {}
        preferred_provider = self._normalize_provider_name(user_preferences.get("preferred_llm_provider"))
        preferred_model = self._normalize_model_name(
            request.preferred_model or user_preferences.get("preferred_model")
        )

        # If model specified with provider prefix, split it
        if preferred_model and ":" in preferred_model:
            provider_part, model_part = preferred_model.split(":", 1)
            preferred_provider = preferred_provider or self._normalize_provider_name(provider_part)
            preferred_model = self._normalize_model_name(model_part)

        # Validate preferred provider/model combination
        if preferred_provider and preferred_model:
            if preferred_provider in NON_CHAT_PROVIDERS:
                preferred_provider = None
                preferred_model = None
            else:
                info = self.registry.get_provider_info(preferred_provider)
                if (
                    info
                    and (
                        await self._is_provider_healthy(preferred_provider)
                        or (
                            self._health_allows_attempt(preferred_provider)
                            and self._provider_has_runtime_readiness(preferred_provider, info)
                        )
                    )
                    and await self._meets_requirements(preferred_provider, request)
                    and self._provider_supports_model(preferred_provider, preferred_model, info)
                ):
                    self._structured_log(
                        logging.INFO,
                        "Using preferred provider/model",
                        provider=preferred_provider,
                        model=preferred_model,
                        policy=self.routing_policy.value,
                        conversation_id=request.conversation_id,
                        platform=request.platform,
                    )
                    self._record_selection_metric(preferred_provider, "selected")
                    return preferred_provider, preferred_model
                else:
                    self._structured_log(
                        logging.WARNING,
                        "Preferred provider/model unavailable",
                        provider=preferred_provider,
                        model=preferred_model,
                        policy=self.routing_policy.value,
                        conversation_id=request.conversation_id,
                        platform=request.platform,
                    )
                    preferred_provider = None
                    preferred_model = None

        # If only preferred model specified, find provider by model
        if preferred_model and not preferred_provider:
            for name in self.registry.list_providers():
                if name in NON_CHAT_PROVIDERS:
                    continue
                info = self.registry.get_provider_info(name)
                if (
                    info
                    and (
                        await self._is_provider_healthy(name)
                        or (
                            self._health_allows_attempt(name)
                            and self._provider_has_runtime_readiness(name, info)
                        )
                    )
                    and await self._meets_requirements(name, request)
                    and self._provider_supports_model(name, preferred_model, info)
                ):
                    self._structured_log(
                        logging.INFO,
                        "Resolved provider for preferred model",
                        provider=name,
                        model=preferred_model,
                        policy=self.routing_policy.value,
                        conversation_id=request.conversation_id,
                        platform=request.platform,
                    )
                    self._record_selection_metric(name, "selected")
                    return name, preferred_model
            self._structured_log(
                logging.WARNING,
                "Preferred model unavailable across providers",
                model=preferred_model,
                policy=self.routing_policy.value,
                conversation_id=request.conversation_id,
                platform=request.platform,
            )
            preferred_model = None

        # Preferred provider without model
        if preferred_provider and await self._is_provider_healthy(preferred_provider):
            if preferred_provider in NON_CHAT_PROVIDERS:
                preferred_provider = None
            else:
                self._structured_log(
                    logging.INFO,
                    "Using preferred provider",
                    provider=preferred_provider,
                    policy=self.routing_policy.value,
                    conversation_id=request.conversation_id,
                    platform=request.platform,
                )
                info = self.registry.get_provider_info(preferred_provider)
                model_name = info.get("default_model") if info else None
                self._record_selection_metric(preferred_provider, "selected")
                return preferred_provider, model_name

        # Get available providers sorted by priority
        available_providers = await self._get_available_providers_by_priority()

        # Filter by requirements
        suitable_providers: List[str] = []
        for provider_name in available_providers:
            if await self._meets_requirements(provider_name, request):
                suitable_providers.append(provider_name)

        if not suitable_providers:
            self._structured_log(
                logging.WARNING,
                "No suitable providers found for request",
                policy=self.routing_policy.value,
                conversation_id=request.conversation_id,
                platform=request.platform,
            )
            self._record_selection_metric("none", "unavailable")
            return None

        selected_provider = suitable_providers[0]
        info = self.registry.get_provider_info(selected_provider)
        model_name = info.get("default_model") if info else None
        self._structured_log(
            logging.INFO,
            "Selected provider via routing policy",
            provider=selected_provider,
            policy=self.routing_policy.value,
            conversation_id=request.conversation_id,
            platform=request.platform,
        )
        self._record_selection_metric(selected_provider, "selected")
        return selected_provider, model_name
    
    async def _get_available_providers_by_priority(self) -> List[str]:
        """Return healthy providers ordered according to the active policy."""

        providers_by_priority = await self._collect_available_providers()
        ordered: List[str] = []
        for priority in self.priority_order:
            bucket = providers_by_priority.get(priority, [])
            if bucket:
                ordered.extend(sorted(bucket))

        if not ordered:
            return ordered

        if self.routing_policy == RoutingPolicy.PRIORITY:
            return ordered

        if self.routing_policy == RoutingPolicy.ROUND_ROBIN:
            offset = self._round_robin_offset % len(ordered)
            self._round_robin_offset = (self._round_robin_offset + 1) % len(ordered)
            return ordered[offset:] + ordered[:offset]

        if self.routing_policy == RoutingPolicy.HYBRID:
            return self._apply_hybrid_policy(providers_by_priority)

        return ordered

    @staticmethod
    def _normalize_provider_name(provider_name: Optional[Any]) -> Optional[str]:
        if provider_name is None:
            return None

        normalized = str(provider_name).strip().lower()
        if not normalized:
            return None

        aliases = {
            "local": "llamacpp",
            "llama-cpp": "llamacpp",
            "llama_cpp": "llamacpp",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _normalize_model_name(model_name: Optional[Any]) -> Optional[str]:
        if model_name is None:
            return None

        normalized = str(model_name).strip()
        if not normalized:
            return None

        if ":" in normalized:
            _, normalized = normalized.split(":", 1)

        # Only strip filesystem-style extensions for local file-backed model ids.
        # Dotted remote model ids such as "glm-4.5" are semantic identifiers, not
        # filenames, and Path(...).stem would incorrectly collapse them to "glm-4".
        lowered = normalized.lower()
        known_local_suffixes = (
            ".gguf",
            ".bin",
            ".safetensors",
            ".onnx",
            ".pt",
            ".pth",
        )
        if "/" in normalized or "\\" in normalized or lowered.endswith(known_local_suffixes):
            stem = Path(normalized).stem
            return stem or normalized

        return normalized

    def _provider_supports_model(
        self,
        provider_name: str,
        preferred_model: str,
        provider_info: Optional[Dict[str, Any]],
    ) -> bool:
        """Treat explicit provider/model pairs like OpenAI-compatible routing."""

        normalized_model = self._normalize_model_name(preferred_model)
        if not normalized_model:
            return False

        default_model = self._normalize_model_name(
            provider_info.get("default_model") if provider_info else None
        )
        if default_model == normalized_model:
            return True

        candidate_models: List[str] = []
        if isinstance(provider_info, dict):
            for key in ("available_models", "models", "common_models"):
                values = provider_info.get(key)
                if isinstance(values, list):
                    candidate_models.extend(str(value) for value in values if value)

        if provider_name in {"openai", "zai"}:
            candidate_models.extend(
                get_openai_compatible_provider_defaults(provider_name).get("common_models", [])
            )

        normalized_candidates = {
            self._normalize_model_name(candidate)
            for candidate in candidate_models
            if self._normalize_model_name(candidate)
        }
        if normalized_model in normalized_candidates:
            return True

        family_hints = {
            "openai": ("gpt", "o1", "o3", "o4", "text-embedding", "omni"),
            "zai": ("glm",),
            "gemini": ("gemini",),
            "anthropic": ("claude",),
            "deepseek": ("deepseek",),
            "mistral": ("mistral", "codestral"),
            "groq": ("llama", "mixtral", "gemma", "qwen"),
            "xai": ("grok",),
            "qwen": ("qwen",),
        }

        hints = family_hints.get(provider_name, ())
        return bool(hints) and normalized_model.lower().startswith(hints)

    def _provider_has_runtime_readiness(
        self, provider_name: str, provider_info: Optional[Dict[str, Any]]
    ) -> bool:
        """Use current runtime/provider metadata to decide if a provider is worth attempting."""

        if not isinstance(provider_info, dict):
            return False

        if provider_info.get("requires_api_key", False) and not self._is_api_key_configured(provider_name, provider_info):
            return False

        has_api_key = provider_info.get("has_api_key") is True
        api_key_valid = provider_info.get("api_key_valid") is not False
        available_models = provider_info.get("available_models")
        has_available_models = isinstance(available_models, list) and len(available_models) > 0
        return has_api_key and api_key_valid and has_available_models

    def _health_allows_attempt(self, provider_name: str) -> bool:
        """Respect active cooldowns while allowing recovery from stale unhealthy snapshots."""

        health = self.provider_health.get(provider_name)
        if not health:
            return True

        if health.circuit_open_until and time.time() < health.circuit_open_until:
            return False
        if health.rate_limited_until and time.time() < health.rate_limited_until:
            return False
        return True
    
    async def _meets_requirements(self, provider_name: str, request: ChatRequest) -> bool:
        """Check if provider meets request requirements"""
        if provider_name in NON_CHAT_PROVIDERS:
            return False

        provider_info = self.registry.get_provider_info(provider_name)
        if not provider_info:
            return False

        # Check streaming requirement
        if request.stream and not provider_info.get("supports_streaming", False):
            return False

        # Check if API key is required and available
        if provider_info.get("requires_api_key", False):
            if not self._is_api_key_configured(provider_name, provider_info):
                self._structured_log(
                    logging.WARNING,
                    "Provider missing required API key",
                    provider=provider_name,
                    requires_api_key=True,
                    conversation_id=request.conversation_id,
                    platform=request.platform,
                )
                return False

        return True

    def _get_secret_manager(self) -> Optional[SecretManager]:
        """Return a cached SecretManager instance when available."""

        if self._secret_manager_unavailable or SecretManager is None:
            return None

        if self._secret_manager is not None:
            return self._secret_manager

        try:
            self._secret_manager = SecretManager()
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            self._secret_manager_unavailable = True
            logger.debug("SecretManager unavailable: %s", exc)
            return None

        return self._secret_manager

    def _is_api_key_configured(
        self, provider_name: str, provider_info: Optional[Dict[str, Any]]
    ) -> bool:
        """Determine whether a provider has the required API credentials."""

        normalized_name = provider_name.lower()

        if provider_info:
            has_key = provider_info.get("has_api_key")
            if isinstance(has_key, bool):
                if not has_key:
                    return False
                if provider_info.get("api_key_valid") is False:
                    return False
                return True

        env_var_candidates: List[str] = []
        if provider_info:
            for key in ("api_key_env_var", "api_key_env"):
                env_var = provider_info.get(key)
                if isinstance(env_var, str) and env_var:
                    env_var_candidates.append(env_var)

        mapped_env = PROVIDER_API_KEY_ENV_MAPPING.get(normalized_name)
        if mapped_env:
            env_var_candidates.append(mapped_env)

        # Remove duplicates while preserving order
        seen: Set[str] = set()
        unique_env_vars: List[str] = []
        for candidate in env_var_candidates:
            if candidate not in seen:
                seen.add(candidate)
                unique_env_vars.append(candidate)

        secret_manager = self._get_secret_manager()

        for env_var in unique_env_vars:
            env_value = os.getenv(env_var)
            if env_value and env_value.strip():
                return True
            if secret_manager and secret_manager.has_secret(env_var):
                return True

        # As a final fallback honour provider_info flags if present without explicit env var
        return False

    async def _collect_available_providers(self) -> Dict[ProviderPriority, List[str]]:
        """Group healthy providers by priority bucket."""

        providers_by_priority: Dict[ProviderPriority, List[str]] = {
            priority: [] for priority in self.priority_order
        }

        for provider_name in self.registry.list_providers():
            if provider_name in NON_CHAT_PROVIDERS:
                continue
            if not await self._is_provider_healthy(provider_name):
                continue
            priority = self.provider_priorities.get(provider_name, ProviderPriority.FALLBACK)
            if priority not in providers_by_priority:
                providers_by_priority[priority] = []
            providers_by_priority[priority].append(provider_name)

        return providers_by_priority

    def _apply_hybrid_policy(
        self,
        providers_by_priority: Dict[ProviderPriority, List[str]],
    ) -> List[str]:
        """Rotate providers within each priority bucket for hybrid routing."""

        ordered: List[str] = []
        for priority in self.priority_order:
            bucket = providers_by_priority.get(priority, [])
            if not bucket:
                continue

            bucket = sorted(bucket)
            current_index = self._hybrid_state.get(priority, 0) % len(bucket)
            self._hybrid_state[priority] = (current_index + 1) % len(bucket)
            rotated = bucket[current_index:] + bucket[:current_index]
            ordered.extend(rotated)

        return ordered

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

        if health.is_healthy and health.consecutive_failures < self.max_consecutive_failures:
            return True

        provider_info = self.registry.get_provider_info(provider_name)
        if isinstance(provider_info, dict):
            has_api_key = provider_info.get("has_api_key") is True
            api_key_valid = provider_info.get("api_key_valid") is not False
            available_models = provider_info.get("available_models")
            has_available_models = isinstance(available_models, list) and len(available_models) > 0

            # Some providers fail an eager startup health probe before their persisted
            # secret/config state is fully loaded. If the provider now has a valid key
            # and successful model discovery, treat it as eligible for routing unless
            # a circuit breaker or active rate-limit cooldown says otherwise.
            if has_api_key and api_key_valid and has_available_models and health.consecutive_failures == 0:
                return True

        return False
    
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
        previous_provider: Optional[str] = None
        previous_error: Optional[BaseException] = None

        selection = await self.select_provider(request, user_preferences)
        if not selection:
            self._structured_log(
                logging.ERROR,
                "No suitable provider available",
                request_id=request_id,
                policy=self.routing_policy.value,
                conversation_id=request.conversation_id,
                platform=request.platform,
            )
            degraded_message = await self._generate_degraded_fallback(
                request,
                failure_records,
                reason=None,
            )
            if degraded_message:
                self._record_selection_metric("degraded_mode", "degraded")
                yield degraded_message
                return
            raise RuntimeError("No suitable provider available")

        provider_name, model_name = selection
        previous_provider = provider_name

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
            self._structured_log(
                logging.WARNING,
                "Provider failed after retries",
                request_id=request_id,
                provider=provider_name,
                policy=self.routing_policy.value,
                error=str(error),
                conversation_id=request.conversation_id,
                platform=request.platform,
            )
            self._record_selection_metric(provider_name, "failure")
            await self._mark_provider_unhealthy(provider_name, str(error))
            failure_records.append({
                "provider": provider_name,
                "error": str(error.last_error) if error.last_error else str(error),
            })
            previous_error = error.last_error or error

        fallback_providers = await self._get_fallback_providers(provider_name, request)
        for fallback_provider in fallback_providers:
            try:
                reason = self._derive_error_reason(previous_error) if previous_error else "fallback"
                self._record_fallback_metric(
                    previous_provider or "none",
                    fallback_provider,
                    reason,
                )
                self._structured_log(
                    logging.INFO,
                    "Attempting fallback provider",
                    request_id=request_id,
                    provider=fallback_provider,
                    from_provider=previous_provider,
                    reason=reason,
                    policy=self.routing_policy.value,
                    conversation_id=request.conversation_id,
                    platform=request.platform,
                )
                self._record_selection_metric(fallback_provider, "fallback_selected")
                async for chunk in self._attempt_provider_with_retries(
                    fallback_provider,
                    request,
                    request_id=request_id,
                    model_name=None,
                ):
                    yield chunk
                return
            except ProviderProcessingError as error:
                self._structured_log(
                    logging.WARNING,
                    "Fallback provider failed",
                    request_id=request_id,
                    provider=fallback_provider,
                    policy=self.routing_policy.value,
                    error=str(error),
                    conversation_id=request.conversation_id,
                    platform=request.platform,
                )
                self._record_selection_metric(fallback_provider, "failure")
                await self._mark_provider_unhealthy(fallback_provider, str(error))
                failure_records.append({
                    "provider": fallback_provider,
                    "error": str(error.last_error) if error.last_error else str(error),
                })
                previous_provider = fallback_provider
                previous_error = error.last_error or error

        degraded_reason = self._infer_degraded_reason(failure_records)
        degraded_message = await self._generate_degraded_fallback(
            request,
            failure_records,
            reason=degraded_reason,
        )
        if degraded_message:
            if previous_provider and previous_error:
                self._record_fallback_metric(
                    previous_provider,
                    "degraded_mode",
                    self._derive_error_reason(previous_error),
                )
            self._record_selection_metric("degraded_mode", "degraded")
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
        provider_prompt = self._build_provider_prompt(request)

        if request.stream:
            stream_callable = getattr(provider, "stream_response", None)
            if stream_callable:
                stream_result = stream_callable(provider_prompt, **provider_params)
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
                stream_result = stream_generate(provider_prompt, **provider_params)
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

        result = generator_callable(provider_prompt, **provider_params)
        if inspect.isawaitable(result):
            result = await result
        if result is None:
            raise RuntimeError(f"Provider {provider_name} returned no response")
        if isinstance(result, bytes):
            result = result.decode("utf-8", errors="ignore")
        result_text = self._sanitize_provider_completion(str(result))
        if not result_text:
            raise RuntimeError(f"Provider {provider_name} returned an empty response")
        if self._looks_like_bad_completion(request, result_text):
            raise RuntimeError(f"Provider {provider_name} returned a malformed response")
        yield result_text

    def _build_provider_prompt(self, request: ChatRequest) -> str:
        """Build a grounded prompt from request context for plain-text providers."""

        context = request.context if isinstance(request.context, dict) else {}
        recent_messages = context.get("recent_messages")
        has_recent_history = False
        if isinstance(recent_messages, list):
            for item in recent_messages:
                if not isinstance(item, dict):
                    continue
                role = str(item.get("role", "")).strip()
                content = str(item.get("content", "")).strip()
                if role in {"user", "assistant"} and content:
                    has_recent_history = True
                    break

        first_turn_value = "yes" if not has_recent_history else "no"
        lines: List[str] = [
            "You are Karen, an intelligent assistant.",
            "Answer only the user's latest message.",
            "Be brief, direct, and relevant.",
            "Do not continue unrelated text.",
            "Do not repeat instructions or metadata.",
            f"First turn: {first_turn_value}.",
            "Greet only if the latest user message is a greeting and this is the first turn.",
            "Do not prepend a greeting to non-greeting questions.",
        ]

        profile = context.get("conversation_profile") if isinstance(context.get("conversation_profile"), dict) else {}
        display_name = str(profile.get("preferred_address_name") or profile.get("display_name") or "").strip()
        if display_name:
            lines.append(f"Known user name: {display_name}.")

        if isinstance(recent_messages, list):
            rendered_messages: List[str] = []
            for item in recent_messages[-6:]:
                if not isinstance(item, dict):
                    continue
                role = str(item.get("role", "")).strip()
                content = str(item.get("content", "")).strip()
                if role in {"user", "assistant"} and content:
                    speaker = "User" if role == "user" else "Assistant"
                    rendered_messages.append(f"{speaker}: {content}")
            if rendered_messages:
                lines.append("Recent conversation:")
                lines.extend(rendered_messages)

        if request.memory_context:
            lines.append("Memory context:")
            lines.append(str(request.memory_context))
        lines.append("Latest user message:")
        lines.append(request.message)
        lines.append("Assistant:")
        return "\n".join(lines)

    def _looks_like_bad_completion(self, request: ChatRequest, result_text: str) -> bool:
        """Reject obvious continuation artifacts from low-quality local completions."""

        normalized_request = request.message.strip().lower()
        normalized_result = result_text.strip().lower()

        if not normalized_result:
            return True

        leaked_prompt_markers = (
            "first turn:",
            "latest user message:",
            "known user name:",
            "recent conversation:",
            "<assistant_context>",
            "</assistant_context>",
            "<recent_conversation>",
            "</recent_conversation>",
            "<memory_context>",
            "</memory_context>",
            "<user_message>",
            "</user_message>",
            "<assistant_reply>",
            "first_turn=",
            "user_name=",
        )
        if any(marker in normalized_result for marker in leaked_prompt_markers):
            return True

        malformed_starts = (
            ",",
            ".",
            ";",
            ":",
            "and ",
            "but ",
            "or ",
        )
        if normalized_result.startswith(malformed_starts):
            return True

        if normalized_request in {"hi", "hello", "hey", "yo"}:
            greeting_markers = ("hi", "hello", "hey", "yo")
            return not normalized_result.startswith(greeting_markers)

        generic_greeting_answers = (
            "hello! how can i assist you today?",
            "hello! how can i help you today?",
            "hi! how can i assist you today?",
            "hi! how can i help you today?",
        )
        if normalized_result in generic_greeting_answers and normalized_request not in {"hi", "hello", "hey", "yo"}:
            return True

        if normalized_result.startswith(("hello!", "hi!", "hello ", "hi ")) and "?" in normalized_request:
            return True

        if "what's my name" in normalized_request or "whats my name" in normalized_request or "what is my name" in normalized_request:
            context = request.context if isinstance(request.context, dict) else {}
            profile = context.get("conversation_profile") if isinstance(context.get("conversation_profile"), dict) else {}
            known_name = str(profile.get("preferred_address_name") or profile.get("display_name") or "").strip()
            if known_name and ("do not have the ability to know personal information" in normalized_result or "i do not know" in normalized_result):
                return True

        return False

    @staticmethod
    def _sanitize_provider_completion(result_text: str) -> str:
        """Normalize low-quality local completions before malformed-response checks."""

        cleaned = str(result_text or "").strip()
        if not cleaned:
            return ""

        marker_extractors = (
            "<assistant_reply>",
            "assistant:",
            "answer:",
        )
        lowered = cleaned.lower()
        for marker in marker_extractors:
            marker_index = lowered.rfind(marker)
            if marker_index != -1:
                candidate = cleaned[marker_index + len(marker):].strip()
                if candidate:
                    cleaned = candidate
                    lowered = cleaned.lower()

        for prefix in (",", ".", ";", ":", "-", "and ", "but ", "or "):
            while lowered.startswith(prefix):
                cleaned = cleaned[len(prefix):].lstrip()
                lowered = cleaned.lower()

        speaker_assignment = inspect.cleandoc(
            r"""
            ^
            [a-z][a-z0-9_-]{1,30}
            \s*=
            \s*
            """
        )
        cleaned = re.sub(speaker_assignment, "", cleaned, count=1, flags=re.IGNORECASE | re.VERBOSE).strip()

        leaked_line_markers = (
            "first turn:",
            "latest user message:",
            "known user name:",
            "recent conversation:",
            "<assistant_context>",
            "</assistant_context>",
            "<recent_conversation>",
            "</recent_conversation>",
            "<memory_context>",
            "</memory_context>",
            "<user_message>",
            "</user_message>",
            "<assistant_reply>",
            "first_turn=",
            "user_name=",
            "response>",
            "response:",
            "response =",
            "response=",
            "output:",
            "user:",
            "in this scenario,",
            "the assistant responds",
            "the user's message",
        )
        filtered_lines = []
        for raw_line in cleaned.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            lowered_line = line.lower()
            if any(marker in lowered_line for marker in leaked_line_markers):
                continue
            filtered_lines.append(line)

        if filtered_lines:
            cleaned = "\n".join(filtered_lines).strip()

        return cleaned
    
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

        PROVIDER_LATENCY_HISTOGRAM.labels(
            provider=provider_name,
            policy=self.routing_policy.value,
        ).observe(latency)

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

        PROVIDER_FAILURE_COUNTER.labels(
            provider=provider_name,
            error_type=self._normalize_metric_label(type(error).__name__),
        ).inc()

    def _calculate_latency_metrics(self, health: ProviderHealth) -> Dict[str, float]:
        """Compute latency metrics for provider status output."""

        if not health.latency_samples:
            return {}

        samples = sorted(health.latency_samples)
        average = sum(samples) / len(samples)
        p95_index = max(0, min(len(samples) - 1, int(len(samples) * 0.95) - 1))
        p95_value = samples[p95_index]

        return {"avg_ms": average * 1000, "p95_ms": p95_value * 1000}

    def _structured_log(self, level: int, message: str, **payload: Any) -> None:
        """Emit structured logs with router metadata."""

        logger.log(level, message, extra={"llm_router": payload})

    def _record_selection_metric(self, provider: str, result: str) -> None:
        """Record provider selection outcomes."""

        PROVIDER_SELECTION_COUNTER.labels(
            provider=provider,
            policy=self.routing_policy.value,
            result=self._normalize_metric_label(result),
        ).inc()

    def _record_fallback_metric(self, from_provider: str, to_provider: str, reason: str) -> None:
        """Record fallback transitions between providers."""

        PROVIDER_FALLBACK_COUNTER.labels(
            from_provider=from_provider,
            to_provider=to_provider,
            reason=self._normalize_metric_label(reason),
        ).inc()

    @staticmethod
    def _normalize_metric_label(value: Optional[str]) -> str:
        """Normalize free-form text for metric label usage."""

        if not value:
            return "unknown"
        sanitized = value.strip().lower().replace(" ", "_")
        return sanitized[:64]

    def _derive_error_reason(self, error: Optional[BaseException]) -> str:
        """Derive a stable reason label from an exception."""

        if error is None:
            return "unknown"
        if isinstance(error, ProviderProcessingError) and error.last_error:
            return self._normalize_metric_label(type(error.last_error).__name__)
        return self._normalize_metric_label(type(error).__name__)

    @staticmethod
    def _classify_failure_detail(error_message: str) -> str:
        """Convert raw provider/runtime errors into a short user-facing cause."""

        lowered = str(error_message or "").strip().lower()
        if not lowered:
            return "Unknown provider failure."
        if any(term in lowered for term in ("api key", "unauthorized", "401", "forbidden", "403", "authentication")):
            return "The provider rejected the credentials or API key."
        if any(term in lowered for term in ("rate limit", "429", "quota")):
            return "The provider rejected the request because of rate limits or quota."
        if any(term in lowered for term in ("bad gateway", "502", "gateway")):
            return "The provider or upstream gateway returned a bad gateway error."
        if any(term in lowered for term in ("timeout", "timed out")):
            return "The provider timed out while generating a response."
        if any(term in lowered for term in ("rejected", "safety", "moderat", "policy")):
            return "The provider rejected the request under its policy or safety checks."
        if any(term in lowered for term in ("connection", "network", "connect", "dns")):
            return "The system could not connect to the provider."
        if "empty response" in lowered:
            return "The provider returned an empty response."
        if "malformed response" in lowered:
            return "The provider returned a malformed response."
        if "could not get provider instance" in lowered:
            return "The configured provider could not be initialized."
        return "The provider failed while handling the request."

    async def _ensure_background_health_task(self) -> None:
        """Ensure a background health monitor loop is running."""

        if self._health_monitor_task and not self._health_monitor_task.done():
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # pragma: no cover - called outside event loop
            return

        if self._health_monitor_lock is None:
            self._health_monitor_lock = asyncio.Lock()

        async with self._health_monitor_lock:
            task = self._health_monitor_task
            if task and not task.done():
                return

            self._health_monitor_task = loop.create_task(self._health_monitor_loop())

    async def _health_monitor_loop(self) -> None:
        """Background loop that periodically refreshes provider health."""

        try:
            while True:
                try:
                    await self.refresh_provider_health()
                except asyncio.CancelledError:
                    raise
                except Exception as exc:  # pragma: no cover - defensive logging
                    self._structured_log(
                        logging.ERROR,
                        "Background health refresh failed",
                        error=str(exc),
                        policy=self.routing_policy.value,
                    )

                await asyncio.sleep(self.background_health_interval)
        except asyncio.CancelledError:
            self._structured_log(
                logging.DEBUG,
                "Background health monitor cancelled",
                policy=self.routing_policy.value,
            )
            raise

    async def _cancel_health_monitor_task(self) -> None:
        """Cancel the background health monitor task if active."""

        task = self._health_monitor_task
        if not task:
            return

        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        self._health_monitor_task = None

    async def shutdown(self) -> None:
        """Shutdown router background tasks."""

        await self._cancel_health_monitor_task()

    def __del__(self):  # pragma: no cover - defensive cleanup
        """Best-effort cancellation of background tasks on destruction."""

        task = getattr(self, "_health_monitor_task", None)
        if task and not task.done():
            task.cancel()

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

            provider_name = "provider"
            provider_cause = "The provider failed while handling the request."
            suggestion = "Try again shortly or switch to a different model in Settings."

            if failure_records:
                primary_failure = failure_records[0]
                provider_name = primary_failure.get("provider", "provider")
                provider_cause = self._classify_failure_detail(primary_failure.get("error", ""))
                lowered_error = str(primary_failure.get("error", "")).lower()
                if "api key" in lowered_error or "401" in lowered_error or "403" in lowered_error:
                    suggestion = "Check the provider credentials in Settings."
                elif "timeout" in lowered_error or "timed out" in lowered_error:
                    suggestion = "Try a shorter prompt or switch to a faster model."
                elif "malformed response" in lowered_error or "empty response" in lowered_error:
                    suggestion = "Try again or switch to a different model in Settings."
                elif "rate limit" in lowered_error or "429" in lowered_error:
                    suggestion = "Wait a moment before trying again, or switch providers."
                elif "connect" in lowered_error or "network" in lowered_error:
                    suggestion = "Check the provider connection and base URL in Settings."

            provider_block = (
                f"Primary provider: {provider_name}\n"
                if provider_name and provider_name != "provider"
                else ""
            )
            final_text = (
                "Karen is operating in degraded mode.\n\n"
                f"{provider_block}"
                f"Cause: {provider_cause}\n\n"
                "I couldn't produce a reliable full answer from the selected model.\n"
                f"{suggestion}"
            )
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
