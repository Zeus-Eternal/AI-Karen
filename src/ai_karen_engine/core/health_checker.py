from __future__ import annotations

"""LLM provider health checking utilities."""

import logging
from dataclasses import dataclass
from datetime import datetime
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


class HealthChecker:
    """Check health and readiness of configured LLM providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, Callable[[], Awaitable[ProviderStatus]]] = {
            "llama-cpp": self._check_llamacpp,
            "openai": self._check_openai,
            "gemini": self._check_gemini,
            "deepseek": self._check_deepseek,
            "huggingface": self._check_huggingface,
        }

    async def check_health_and_readiness(self) -> List[ProviderStatus]:
        """Run health checks for all providers."""
        results: List[ProviderStatus] = []
        for name, checker in self._providers.items():
            try:
                status = await checker()
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Health check failed for %s", name)
                status = ProviderStatus(
                    provider=name,
                    model="unknown",
                    available=False,
                    authenticated=False,
                    tool_support=False,
                    policy_gates_passed=False,
                    last_check=datetime.utcnow(),
                    error_message=str(exc),
                )
            results.append(status)
        return results

    async def _check_llamacpp(self) -> ProviderStatus:
        provider = LlamaCppProvider()
        try:
            info = provider.health_check()
            available = info.get("status") == "ok" or info.get("healthy", False)
        except Exception as exc:
            return ProviderStatus(
                provider="llama-cpp",
                model=provider.model,
                available=False,
                authenticated=True,
                tool_support=True,
                policy_gates_passed=True,
                last_check=datetime.utcnow(),
                error_message=str(exc),
            )
        return ProviderStatus(
            provider="llama-cpp",
            model=provider.model,
            available=available,
            authenticated=True,
            tool_support=True,
            policy_gates_passed=True,
            last_check=datetime.utcnow(),
        )

    async def _check_openai(self) -> ProviderStatus:
        provider = OpenAIProvider()
        try:
            info = provider.health_check()
            available = info.get("status") == "ok" or info.get("healthy", False)
            authenticated = not info.get("auth_error", False)
        except Exception as exc:
            return ProviderStatus(
                provider="openai",
                model=provider.model,
                available=False,
                authenticated=False,
                tool_support=True,
                policy_gates_passed=True,
                last_check=datetime.utcnow(),
                error_message=str(exc),
            )
        return ProviderStatus(
            provider="openai",
            model=provider.model,
            available=available,
            authenticated=authenticated,
            tool_support=True,
            policy_gates_passed=True,
            last_check=datetime.utcnow(),
        )

    async def _check_gemini(self) -> ProviderStatus:
        provider = GeminiProvider()
        try:
            info = provider.health_check()
            available = info.get("status") == "ok" or info.get("healthy", False)
            authenticated = not info.get("auth_error", False)
        except Exception as exc:
            return ProviderStatus(
                provider="gemini",
                model=provider.model,
                available=False,
                authenticated=False,
                tool_support=True,
                policy_gates_passed=True,
                last_check=datetime.utcnow(),
                error_message=str(exc),
            )
        return ProviderStatus(
            provider="gemini",
            model=provider.model,
            available=available,
            authenticated=authenticated,
            tool_support=True,
            policy_gates_passed=True,
            last_check=datetime.utcnow(),
        )

    async def _check_deepseek(self) -> ProviderStatus:
        provider = DeepseekProvider()
        try:
            info = provider.health_check()
            available = info.get("status") == "ok" or info.get("healthy", False)
            authenticated = not info.get("auth_error", False)
        except Exception as exc:
            return ProviderStatus(
                provider="deepseek",
                model=provider.model,
                available=False,
                authenticated=False,
                tool_support=True,
                policy_gates_passed=True,
                last_check=datetime.utcnow(),
                error_message=str(exc),
            )
        return ProviderStatus(
            provider="deepseek",
            model=provider.model,
            available=available,
            authenticated=authenticated,
            tool_support=True,
            policy_gates_passed=True,
            last_check=datetime.utcnow(),
        )

    async def _check_huggingface(self) -> ProviderStatus:
        provider = HuggingFaceProvider()
        try:
            info = provider.health_check()
            available = info.get("status") == "ok" or info.get("healthy", False)
            authenticated = not info.get("auth_error", False)
        except Exception as exc:
            return ProviderStatus(
                provider="huggingface",
                model=provider.model,
                available=False,
                authenticated=False,
                tool_support=True,
                policy_gates_passed=True,
                last_check=datetime.utcnow(),
                error_message=str(exc),
            )
        return ProviderStatus(
            provider="huggingface",
            model=provider.model,
            available=available,
            authenticated=authenticated,
            tool_support=True,
            policy_gates_passed=True,
            last_check=datetime.utcnow(),
        )
