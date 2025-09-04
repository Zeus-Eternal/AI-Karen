from __future__ import annotations

"""LLM provider health checking utilities."""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Awaitable, Callable, Dict, List, Optional

from ai_karen_engine.integrations.providers.deepseek_provider import (  # type: ignore[import-not-found]
    DeepseekProvider,
)
from ai_karen_engine.integrations.providers.gemini_provider import (  # type: ignore[import-not-found]
    GeminiProvider,
)
from ai_karen_engine.integrations.providers.huggingface_provider import (  # type: ignore[import-not-found]
    HuggingFaceProvider,
)
from ai_karen_engine.integrations.providers.llamacpp_provider import (  # type: ignore[import-not-found]
    LlamaCppProvider,
)
from ai_karen_engine.integrations.providers.openai_provider import (  # type: ignore[import-not-found]
    OpenAIProvider,
)

logger = logging.getLogger(__name__)


@dataclass
class ProviderStatus:
    provider: str
    model: str
    available: bool
    authenticated: bool
    tool_support: bool
    policy_gates_passed: bool
    last_check: datetime
    error_message: Optional[str] = None
    quota_remaining: Optional[int] = None
    rate_limit_remaining: Optional[int] = None
    response_time_ms: Optional[float] = None


class HealthChecker:
    """
    Enhanced health checker for provider availability verification.
    Requirements: 5.1, 5.2, 5.3, 5.4
    """

    def __init__(self, cache_ttl: int = 300) -> None:
        self._providers: Dict[str, Callable[[], Awaitable[ProviderStatus]]] = {
            "llama-cpp": self._check_llamacpp,
            "llamacpp": self._check_llamacpp,  # Support both naming conventions
            "transformers": self._check_transformers,
            "openai": self._check_openai,
            "gemini": self._check_gemini,
            "deepseek": self._check_deepseek,
            "huggingface": self._check_huggingface,
        }
        
        # Health check caching and periodic refresh (Requirement 5.4)
        self._cache_ttl = cache_ttl  # Cache TTL in seconds
        self._status_cache: Dict[str, ProviderStatus] = {}
        self._last_refresh = 0.0
        self._refresh_lock = asyncio.Lock()

    async def check_health_and_readiness(self, force_refresh: bool = False) -> List[ProviderStatus]:
        """
        Run health checks for all providers with caching and periodic refresh.
        Requirements: 5.1, 5.2, 5.3, 5.4
        """
        current_time = time.time()
        
        # Check if cache refresh is needed
        if force_refresh or (current_time - self._last_refresh) > self._cache_ttl:
            async with self._refresh_lock:
                # Double-check after acquiring lock
                if force_refresh or (current_time - self._last_refresh) > self._cache_ttl:
                    await self._refresh_all_providers()
                    self._last_refresh = current_time
        
        return list(self._status_cache.values())
    
    async def check_single_provider(self, provider_name: str, force_refresh: bool = False) -> Optional[ProviderStatus]:
        """
        Check health of a single provider with caching.
        Requirements: 5.1, 5.2, 5.3
        """
        if provider_name not in self._providers:
            logger.warning(f"Unknown provider: {provider_name}")
            return None
        
        # Check cache first
        cached_status = self._status_cache.get(provider_name)
        if not force_refresh and cached_status:
            cache_age = time.time() - cached_status.last_check.timestamp()
            if cache_age < self._cache_ttl:
                return cached_status
        
        # Refresh this provider
        try:
            checker = self._providers[provider_name]
            status = await checker()
            self._status_cache[provider_name] = status
            return status
        except Exception as exc:
            logger.exception("Health check failed for %s", provider_name)
            status = ProviderStatus(
                provider=provider_name,
                model="unknown",
                available=False,
                authenticated=False,
                tool_support=False,
                policy_gates_passed=False,
                last_check=datetime.utcnow(),
                error_message=str(exc),
            )
            self._status_cache[provider_name] = status
            return status
    
    async def _refresh_all_providers(self) -> None:
        """Refresh health status for all providers."""
        tasks = []
        for name, checker in self._providers.items():
            tasks.append(self._check_provider_with_error_handling(name, checker))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, ProviderStatus):
                self._status_cache[result.provider] = result
            elif isinstance(result, Exception):
                logger.error(f"Provider health check failed: {result}")
    
    async def _check_provider_with_error_handling(
        self, 
        name: str, 
        checker: Callable[[], Awaitable[ProviderStatus]]
    ) -> ProviderStatus:
        """Check a single provider with comprehensive error handling."""
        try:
            return await checker()
        except Exception as exc:
            logger.exception("Health check failed for %s", name)
            return ProviderStatus(
                provider=name,
                model="unknown",
                available=False,
                authenticated=False,
                tool_support=False,
                policy_gates_passed=False,
                last_check=datetime.utcnow(),
                error_message=str(exc),
            )

    async def _check_llamacpp(self) -> ProviderStatus:
        """Enhanced LlamaCpp provider health check with comprehensive validation."""
        provider = LlamaCppProvider()
        start_time = time.time()
        
        try:
            # Check basic health
            info = provider.health_check()
            available = info.get("status") == "ok" or info.get("healthy", False)
            
            # Measure response time
            response_time = (time.time() - start_time) * 1000
            
            # Enhanced authentication/quota checking (Requirement 5.2)
            authenticated = True  # Local provider doesn't need API key
            quota_remaining = None  # Local provider has no quota limits
            
            # Tool support validation (Requirement 5.3)
            tool_support = self._validate_tool_support(provider)
            
            # Policy gate validation (Requirement 5.3)
            policy_gates_passed = self._validate_policy_gates(provider, "llamacpp")
            
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            return ProviderStatus(
                provider="llamacpp",
                model=getattr(provider, 'model', 'unknown'),
                available=False,
                authenticated=True,
                tool_support=False,
                policy_gates_passed=False,
                last_check=datetime.utcnow(),
                error_message=str(exc),
                response_time_ms=response_time,
            )
            
        return ProviderStatus(
            provider="llamacpp",
            model=getattr(provider, 'model', 'default'),
            available=available,
            authenticated=authenticated,
            tool_support=tool_support,
            policy_gates_passed=policy_gates_passed,
            last_check=datetime.utcnow(),
            quota_remaining=quota_remaining,
            response_time_ms=response_time,
        )

    async def _check_transformers(self) -> ProviderStatus:
        """Check Transformers provider health (local transformers models)."""
        start_time = time.time()
        
        try:
            # For transformers, we check if the library is available and models can be loaded
            import transformers
            
            # Basic availability check - assume available if transformers library is installed
            available = True
            authenticated = True  # No API key needed for local transformers
            response_time = (time.time() - start_time) * 1000
            
            # Tool support and policy validation
            tool_support = True  # Transformers supports text generation
            policy_gates_passed = True  # Local models pass policy gates
            
        except ImportError:
            response_time = (time.time() - start_time) * 1000
            return ProviderStatus(
                provider="transformers",
                model="unknown",
                available=False,
                authenticated=True,
                tool_support=False,
                policy_gates_passed=False,
                last_check=datetime.utcnow(),
                error_message="Transformers library not installed",
                response_time_ms=response_time,
            )
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            return ProviderStatus(
                provider="transformers",
                model="unknown",
                available=False,
                authenticated=True,
                tool_support=False,
                policy_gates_passed=False,
                last_check=datetime.utcnow(),
                error_message=str(exc),
                response_time_ms=response_time,
            )
            
        return ProviderStatus(
            provider="transformers",
            model="default",
            available=available,
            authenticated=authenticated,
            tool_support=tool_support,
            policy_gates_passed=policy_gates_passed,
            last_check=datetime.utcnow(),
            response_time_ms=response_time,
        )

    async def _check_openai(self) -> ProviderStatus:
        """Enhanced OpenAI provider health check with quota and rate limit validation."""
        provider = OpenAIProvider()
        start_time = time.time()
        
        try:
            # Check basic health and authentication
            info = provider.health_check()
            available = info.get("status") == "ok" or info.get("healthy", False)
            authenticated = not info.get("auth_error", False)
            
            # Measure response time
            response_time = (time.time() - start_time) * 1000
            
            # Enhanced quota/rate limit checking (Requirement 5.2)
            quota_remaining = info.get("quota_remaining")
            rate_limit_remaining = info.get("rate_limit_remaining")
            
            # Tool support validation (Requirement 5.3)
            tool_support = self._validate_tool_support(provider)
            
            # Policy gate validation (Requirement 5.3)
            policy_gates_passed = self._validate_policy_gates(provider, "openai")
            
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            return ProviderStatus(
                provider="openai",
                model=getattr(provider, 'model', 'unknown'),
                available=False,
                authenticated=False,
                tool_support=False,
                policy_gates_passed=False,
                last_check=datetime.utcnow(),
                error_message=str(exc),
                response_time_ms=response_time,
            )
            
        return ProviderStatus(
            provider="openai",
            model=getattr(provider, 'model', 'gpt-3.5-turbo'),
            available=available,
            authenticated=authenticated,
            tool_support=tool_support,
            policy_gates_passed=policy_gates_passed,
            last_check=datetime.utcnow(),
            quota_remaining=quota_remaining,
            rate_limit_remaining=rate_limit_remaining,
            response_time_ms=response_time,
        )

    async def _check_gemini(self) -> ProviderStatus:
        """Enhanced Gemini provider health check with comprehensive validation."""
        provider = GeminiProvider()
        start_time = time.time()
        
        try:
            info = provider.health_check()
            available = info.get("status") == "ok" or info.get("healthy", False)
            authenticated = not info.get("auth_error", False)
            
            response_time = (time.time() - start_time) * 1000
            quota_remaining = info.get("quota_remaining")
            rate_limit_remaining = info.get("rate_limit_remaining")
            
            tool_support = self._validate_tool_support(provider)
            policy_gates_passed = self._validate_policy_gates(provider, "gemini")
            
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            return ProviderStatus(
                provider="gemini",
                model=getattr(provider, 'model', 'unknown'),
                available=False,
                authenticated=False,
                tool_support=False,
                policy_gates_passed=False,
                last_check=datetime.utcnow(),
                error_message=str(exc),
                response_time_ms=response_time,
            )
            
        return ProviderStatus(
            provider="gemini",
            model=getattr(provider, 'model', 'gemini-1.5-pro'),
            available=available,
            authenticated=authenticated,
            tool_support=tool_support,
            policy_gates_passed=policy_gates_passed,
            last_check=datetime.utcnow(),
            quota_remaining=quota_remaining,
            rate_limit_remaining=rate_limit_remaining,
            response_time_ms=response_time,
        )

    async def _check_deepseek(self) -> ProviderStatus:
        """Enhanced DeepSeek provider health check with comprehensive validation."""
        provider = DeepseekProvider()
        start_time = time.time()
        
        try:
            info = provider.health_check()
            available = info.get("status") == "ok" or info.get("healthy", False)
            authenticated = not info.get("auth_error", False)
            
            response_time = (time.time() - start_time) * 1000
            quota_remaining = info.get("quota_remaining")
            rate_limit_remaining = info.get("rate_limit_remaining")
            
            tool_support = self._validate_tool_support(provider)
            policy_gates_passed = self._validate_policy_gates(provider, "deepseek")
            
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            return ProviderStatus(
                provider="deepseek",
                model=getattr(provider, 'model', 'unknown'),
                available=False,
                authenticated=False,
                tool_support=False,
                policy_gates_passed=False,
                last_check=datetime.utcnow(),
                error_message=str(exc),
                response_time_ms=response_time,
            )
            
        return ProviderStatus(
            provider="deepseek",
            model=getattr(provider, 'model', 'deepseek-chat'),
            available=available,
            authenticated=authenticated,
            tool_support=tool_support,
            policy_gates_passed=policy_gates_passed,
            last_check=datetime.utcnow(),
            quota_remaining=quota_remaining,
            rate_limit_remaining=rate_limit_remaining,
            response_time_ms=response_time,
        )

    async def _check_huggingface(self) -> ProviderStatus:
        """Enhanced HuggingFace provider health check with comprehensive validation."""
        provider = HuggingFaceProvider()
        start_time = time.time()
        
        try:
            info = provider.health_check()
            available = info.get("status") == "ok" or info.get("healthy", False)
            authenticated = not info.get("auth_error", False)
            
            response_time = (time.time() - start_time) * 1000
            quota_remaining = info.get("quota_remaining")
            rate_limit_remaining = info.get("rate_limit_remaining")
            
            tool_support = self._validate_tool_support(provider)
            policy_gates_passed = self._validate_policy_gates(provider, "huggingface")
            
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            return ProviderStatus(
                provider="huggingface",
                model=getattr(provider, 'model', 'unknown'),
                available=False,
                authenticated=False,
                tool_support=False,
                policy_gates_passed=False,
                last_check=datetime.utcnow(),
                error_message=str(exc),
                response_time_ms=response_time,
            )
            
        return ProviderStatus(
            provider="huggingface",
            model=getattr(provider, 'model', 'distilbert-base-uncased'),
            available=available,
            authenticated=authenticated,
            tool_support=tool_support,
            policy_gates_passed=policy_gates_passed,
            last_check=datetime.utcnow(),
            quota_remaining=quota_remaining,
            rate_limit_remaining=rate_limit_remaining,
            response_time_ms=response_time,
        )
    
    def _validate_tool_support(self, provider) -> bool:
        """
        Validate tool support for the provider.
        Requirements: 5.3
        """
        try:
            # Check if provider has required methods for tool support
            required_methods = ['generate_text', 'generate_response']
            return any(hasattr(provider, method) for method in required_methods)
        except Exception as e:
            logger.debug(f"Tool support validation failed: {e}")
            return False
    
    def _validate_policy_gates(self, provider, provider_name: str) -> bool:
        """
        Validate policy gates for the provider.
        Requirements: 5.3
        """
        try:
            # Basic policy validation - can be enhanced with actual policy checks
            # For now, assume all providers pass policy gates unless explicitly configured otherwise
            
            # Could check for:
            # - Content filtering capabilities
            # - Safety model availability
            # - Compliance with usage policies
            
            return True  # Default to passing policy gates
        except Exception as e:
            logger.debug(f"Policy gate validation failed for {provider_name}: {e}")
            return False
