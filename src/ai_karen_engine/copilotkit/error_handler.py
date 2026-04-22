"""
CopilotKit Error Handler with LLM Provider Fallback Integration

This module provides specialized error handling for CopilotKit integration,
including fallback to existing LLM providers and graceful degradation.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CopilotKitErrorType(Enum):
    """Specific CopilotKit error types."""

    API_UNAVAILABLE = "api_unavailable"
    AUTHENTICATION_FAILED = "authentication_failed"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CONTEXT_TOO_LARGE = "context_too_large"
    MODEL_UNAVAILABLE = "model_unavailable"
    TIMEOUT = "timeout"
    INVALID_REQUEST = "invalid_request"
    QUOTA_EXCEEDED = "quota_exceeded"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


class CopilotKitFallbackHandler:
    """Handles CopilotKit errors with intelligent fallback strategies."""

    CACHE_TTL_SECONDS = 900
    MAX_CACHE_ENTRIES = 256

    def __init__(self) -> None:
        try:
            from ai_karen_engine.llm_orchestrator import get_orchestrator

            self.llm_orchestrator = get_orchestrator()
        except Exception:
            self.llm_orchestrator = None
        self.fallback_cache: Dict[str, Dict[str, Any]] = {}
        self.error_counts: Dict[str, int] = {}
        self.last_error_time: Dict[str, float] = {}

    async def handle_code_suggestions_error(
        self,
        error: Exception,
        code: str,
        language: str = "python",
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Handle code suggestions error with fallback to LLM providers."""
        error_type = self._classify_error(error)
        self._record_error(error_type)

        logger.warning(
            "CopilotKit code suggestions failed (%s): %s",
            error_type.value,
            error,
        )

        cache_key = self._make_cache_key(
            "code_suggestions",
            {"code": code, "language": language},
        )

        try:
            fallback_suggestions = await self._get_code_suggestions_fallback(
                code=code,
                language=language,
                error_type=error_type,
                cache_key=cache_key,
                **kwargs,
            )
            if fallback_suggestions:
                return fallback_suggestions

            cached = self._get_cached_payload(cache_key, "suggestions")
            if cached is not None:
                logger.info("Using cached code suggestions")
                return cached

            return self._create_generic_code_suggestions(code, language)

        except Exception as fallback_error:
            logger.error(
                "Code suggestions fallback failed: %s",
                fallback_error,
                exc_info=True,
            )
            return self._create_generic_code_suggestions(code, language)

    async def handle_debugging_assistance_error(
        self,
        error: Exception,
        code: str,
        error_message: str = "",
        language: str = "python",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Handle debugging assistance error with fallback."""
        error_type = self._classify_error(error)
        self._record_error(error_type)

        logger.warning(
            "CopilotKit debugging assistance failed (%s): %s",
            error_type.value,
            error,
        )

        cache_key = self._make_cache_key(
            "debug_assistance",
            {
                "code": code,
                "error_message": error_message,
                "language": language,
            },
        )

        try:
            fallback_assistance = await self._get_debugging_assistance_fallback(
                code=code,
                error_message=error_message,
                language=language,
                error_type=error_type,
                cache_key=cache_key,
                **kwargs,
            )
            if fallback_assistance:
                return fallback_assistance

            cached = self._get_cached_payload(cache_key, "assistance")
            if cached is not None:
                logger.info("Using cached debugging assistance")
                return cached

            return self._create_generic_debugging_assistance(
                code,
                error_message,
                language,
            )

        except Exception as fallback_error:
            logger.error(
                "Debugging assistance fallback failed: %s",
                fallback_error,
                exc_info=True,
            )
            return self._create_generic_debugging_assistance(
                code,
                error_message,
                language,
            )

    async def handle_contextual_suggestions_error(
        self,
        error: Exception,
        message: str,
        context: Dict[str, Any],
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Handle contextual suggestions error with fallback."""
        error_type = self._classify_error(error)
        self._record_error(error_type)

        logger.warning(
            "CopilotKit contextual suggestions failed (%s): %s",
            error_type.value,
            error,
        )

        cache_key = self._make_cache_key(
            "contextual_suggestions",
            {"message": message, "context": context},
        )

        try:
            fallback_suggestions = await self._get_contextual_suggestions_fallback(
                message=message,
                context=context,
                error_type=error_type,
                cache_key=cache_key,
                **kwargs,
            )
            if fallback_suggestions:
                return fallback_suggestions

            cached = self._get_cached_payload(cache_key, "suggestions")
            if cached is not None:
                logger.info("Using cached contextual suggestions")
                return cached

            return self._create_generic_contextual_suggestions(message, context)

        except Exception as fallback_error:
            logger.error(
                "Contextual suggestions fallback failed: %s",
                fallback_error,
                exc_info=True,
            )
            return self._create_generic_contextual_suggestions(message, context)

    async def handle_documentation_generation_error(
        self,
        error: Exception,
        code: str,
        language: str = "python",
        style: str = "comprehensive",
        **kwargs: Any,
    ) -> str:
        """Handle documentation generation error with fallback."""
        error_type = self._classify_error(error)
        self._record_error(error_type)

        logger.warning(
            "CopilotKit documentation generation failed (%s): %s",
            error_type.value,
            error,
        )

        cache_key = self._make_cache_key(
            "documentation",
            {"code": code, "language": language, "style": style},
        )

        try:
            fallback_docs = await self._get_documentation_generation_fallback(
                code=code,
                language=language,
                style=style,
                error_type=error_type,
                cache_key=cache_key,
                **kwargs,
            )
            if fallback_docs:
                return fallback_docs

            cached = self._get_cached_payload(cache_key, "documentation")
            if cached is not None:
                logger.info("Using cached documentation")
                return cached

            return self._create_generic_documentation(code, language, style)

        except Exception as fallback_error:
            logger.error(
                "Documentation generation fallback failed: %s",
                fallback_error,
                exc_info=True,
            )
            return self._create_generic_documentation(code, language, style)

    def _classify_error(self, error: Exception) -> CopilotKitErrorType:
        """Classify CopilotKit error by type."""
        error_msg = str(error).lower()

        if (
            "authentication" in error_msg
            or "unauthorized" in error_msg
            or "forbidden" in error_msg
        ):
            return CopilotKitErrorType.AUTHENTICATION_FAILED
        if "rate limit" in error_msg or "429" in error_msg:
            return CopilotKitErrorType.RATE_LIMIT_EXCEEDED
        if "quota" in error_msg:
            return CopilotKitErrorType.QUOTA_EXCEEDED
        if "timeout" in error_msg or "timed out" in error_msg:
            return CopilotKitErrorType.TIMEOUT
        if "context" in error_msg and ("large" in error_msg or "size" in error_msg):
            return CopilotKitErrorType.CONTEXT_TOO_LARGE
        if "model" in error_msg and (
            "unavailable" in error_msg or "not found" in error_msg
        ):
            return CopilotKitErrorType.MODEL_UNAVAILABLE
        if "network" in error_msg or "dns" in error_msg or "socket" in error_msg:
            return CopilotKitErrorType.NETWORK_ERROR
        if "unavailable" in error_msg or "service down" in error_msg:
            return CopilotKitErrorType.API_UNAVAILABLE
        if "invalid" in error_msg or "bad request" in error_msg or "400" in error_msg:
            return CopilotKitErrorType.INVALID_REQUEST

        return CopilotKitErrorType.UNKNOWN

    def _record_error(self, error_type: CopilotKitErrorType) -> None:
        """Track error counts and timestamps for diagnostics."""
        key = error_type.value
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        self.last_error_time[key] = time.time()

    async def _get_code_suggestions_fallback(
        self,
        code: str,
        language: str,
        error_type: CopilotKitErrorType,
        cache_key: str,
        **kwargs: Any,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get code suggestions using LLM orchestrator fallback."""
        prompt = self._create_code_suggestions_prompt(code, language, error_type)
        response = await self._call_llm_fallback(
            prompt=prompt,
            skill="code_assistance",
            timeout_seconds=30.0,
            **kwargs,
        )
        if not response:
            return None

        suggestions = self._parse_code_suggestions_response(response, language)
        self._store_cache_entry(
            cache_key,
            {"suggestions": suggestions, "source": "llm_fallback"},
        )
        return suggestions

    async def _get_debugging_assistance_fallback(
        self,
        code: str,
        error_message: str,
        language: str,
        error_type: CopilotKitErrorType,
        cache_key: str,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Get debugging assistance using LLM orchestrator fallback."""
        prompt = self._create_debugging_prompt(
            code,
            error_message,
            language,
            error_type,
        )
        response = await self._call_llm_fallback(
            prompt=prompt,
            skill="debugging",
            timeout_seconds=45.0,
            **kwargs,
        )
        if not response:
            return None

        assistance = self._parse_debugging_response(response, language)
        self._store_cache_entry(
            cache_key,
            {"assistance": assistance, "source": "llm_fallback"},
        )
        return assistance

    async def _get_contextual_suggestions_fallback(
        self,
        message: str,
        context: Dict[str, Any],
        error_type: CopilotKitErrorType,
        cache_key: str,
        **kwargs: Any,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get contextual suggestions using LLM orchestrator fallback."""
        prompt = self._create_contextual_suggestions_prompt(
            message,
            context,
        )
        response = await self._call_llm_fallback(
            prompt=prompt,
            skill="conversation",
            timeout_seconds=30.0,
            **kwargs,
        )
        if not response:
            return None

        suggestions = self._parse_contextual_suggestions_response(response)
        self._store_cache_entry(
            cache_key,
            {"suggestions": suggestions, "source": "llm_fallback"},
        )
        return suggestions

    async def _get_documentation_generation_fallback(
        self,
        code: str,
        language: str,
        style: str,
        error_type: CopilotKitErrorType,
        cache_key: str,
        **kwargs: Any,
    ) -> Optional[str]:
        """Get documentation generation using LLM orchestrator fallback."""
        prompt = self._create_documentation_prompt(code, language, style, error_type)
        response = await self._call_llm_fallback(
            prompt=prompt,
            skill="documentation",
            timeout_seconds=60.0,
            **kwargs,
        )
        if not response:
            return None

        self._store_cache_entry(
            cache_key,
            {"documentation": response, "source": "llm_fallback"},
        )
        return response

    async def _call_llm_fallback(
        self,
        prompt: str,
        skill: str,
        timeout_seconds: float,
        **kwargs: Any,
    ) -> Optional[str]:
        """Call the LLM orchestrator safely with timeout and availability checks."""
        if self.llm_orchestrator is None:
            logger.warning("LLM orchestrator unavailable for CopilotKit fallback")
            return None

        if not hasattr(self.llm_orchestrator, "enhanced_route"):
            logger.warning("LLM orchestrator missing enhanced_route for fallback")
            return None

        try:
            response = await asyncio.wait_for(
                self.llm_orchestrator.enhanced_route(prompt, skill=skill, **kwargs),
                timeout=timeout_seconds,
            )
            if response is None:
                return None
            return str(response)
        except Exception as exc:
            logger.error("LLM fallback call failed for skill %s: %s", skill, exc)
            return None

    def _make_cache_key(self, prefix: str, payload: Dict[str, Any]) -> str:
        """Create stable cache keys from structured payloads."""
        try:
            normalized = json.dumps(payload, sort_keys=True, default=str)
        except Exception:
            normalized = str(payload)
        return f"{prefix}:{normalized}"

    def _store_cache_entry(self, cache_key: str, payload: Dict[str, Any]) -> None:
        """Store cache entry with timestamp and bounded size."""
        self._prune_cache()

        cache_payload = dict(payload)
        cache_payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        cache_payload["created_at_epoch"] = time.time()

        self.fallback_cache[cache_key] = cache_payload

        if len(self.fallback_cache) > self.MAX_CACHE_ENTRIES:
            oldest_key = min(
                self.fallback_cache,
                key=lambda key: self.fallback_cache[key].get("created_at_epoch", 0.0),
            )
            self.fallback_cache.pop(oldest_key, None)

    def _get_cached_payload(self, cache_key: str, field: str) -> Optional[Any]:
        """Get a cached payload if not expired."""
        self._prune_cache()
        cached = self.fallback_cache.get(cache_key)
        if not cached:
            return None
        return cached.get(field)

    def _prune_cache(self) -> None:
        """Remove expired cache entries."""
        now_epoch = time.time()
        expired_keys = [
            key
            for key, value in self.fallback_cache.items()
            if now_epoch - float(value.get("created_at_epoch", 0.0))
            > self.CACHE_TTL_SECONDS
        ]
        for key in expired_keys:
            self.fallback_cache.pop(key, None)

    def _create_code_suggestions_prompt(
        self,
        code: str,
        language: str,
        error_type: CopilotKitErrorType,
    ) -> str:
        """Create prompt for code suggestions."""
        return f"""
Please analyze the following {language} code and provide helpful suggestions for improvement, completion, or fixes.

Fallback reason: {error_type.value}

```{language}
{code}
```

Provide your suggestions as a JSON array of objects with 'type', 'title', 'description', and optionally 'code' fields.
"""

    def _create_generic_code_suggestions(
        self, code: str, language: str
    ) -> List[Dict[str, Any]]:
        """Create generic code suggestions when all fallbacks fail."""
        return [
            {
                "type": "info",
                "title": "Code Analysis Available",
                "description": f"Basic syntax checking for {language} code. Consider reviewing variable names and code structure.",
            }
        ]

    def _parse_code_suggestions_response(
        self, response: str, language: str
    ) -> List[Dict[str, Any]]:
        """Parse LLM response for code suggestions."""
        try:
            import json

            suggestions = json.loads(response)
            if isinstance(suggestions, list):
                return suggestions
        except (json.JSONDecodeError, TypeError):
            pass

        # Fallback parsing
        return [
            {
                "type": "info",
                "title": "LLM Response",
                "description": response[:200] + "..."
                if len(response) > 200
                else response,
            }
        ]

    def _create_debugging_prompt(
        self,
        code: str,
        error_message: str,
        language: str,
        error_type: CopilotKitErrorType,
    ) -> str:
        """Create prompt for debugging assistance."""
        return f"""
Please help debug the following {language} code that is experiencing an error.

Error: {error_message}
Fallback reason: {error_type.value}

```{language}
{code}
```

Provide debugging assistance as JSON with 'analysis', 'suggestions', and 'fixed_code' fields.
"""

    def _parse_debugging_response(self, response: str, language: str) -> Dict[str, Any]:
        """Parse LLM response for debugging assistance."""
        try:
            import json

            result = json.loads(response)
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, TypeError):
            pass

        return {
            "analysis": "Unable to parse LLM response",
            "suggestions": ["Check syntax and variable references"],
            "fixed_code": None,
        }

    def _create_contextual_suggestions_prompt(
        self, message: str, context: Dict[str, Any]
    ) -> str:
        """Create prompt for contextual suggestions."""
        context_part = f"\n\nContext:\n{context}" if context else ""
        return f"""
Based on the following message and context, provide helpful suggestions or completions.

Message: {message}{context_part}

Provide suggestions as a JSON array of strings.
"""

    def _parse_contextual_suggestions_response(
        self, response: str
    ) -> List[Dict[str, Any]]:
        """Parse LLM response for contextual suggestions."""
        try:
            import json

            suggestions = json.loads(response)
            if isinstance(suggestions, list):
                return suggestions
        except (json.JSONDecodeError, TypeError):
            pass

        # Fallback: split by lines and convert to dict format
        return [
            {"type": "suggestion", "content": line.strip(), "confidence": 0.5}
            for line in response.split("\n")
            if line.strip()
        ][:5]

    def _create_documentation_prompt(
        self, code: str, language: str, style: str, error_type: CopilotKitErrorType
    ) -> str:
        """Create prompt for documentation generation."""
        return f"""
Generate documentation for the following {language} code in {style} style.

Fallback reason: {error_type.value}

```{language}
{code}
```

Provide documentation as a JSON object with 'summary', 'description', 'parameters', and 'examples' fields.
"""

    def _create_generic_debugging_assistance(
        self, code: str, error_message: str, language: str
    ) -> Dict[str, Any]:
        """Create generic debugging assistance when all fallbacks fail."""
        return {
            "analysis": f"Error in {language} code: {error_message}",
            "suggestions": [
                "Check for syntax errors",
                "Verify variable declarations",
                "Review function calls and parameters",
            ],
            "fixed_code": None,
        }

    def _create_generic_contextual_suggestions(
        self, message: str, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create generic contextual suggestions when all fallbacks fail."""
        suggestions = [
            {
                "type": "suggestion",
                "content": f"Consider the context: {message}",
                "confidence": 0.5,
            }
        ]
        if context:
            context_str = str(context)
            suggestions.append(
                {
                    "type": "context",
                    "content": f"Additional context: {context_str[:100]}...",
                    "confidence": 0.3,
                }
            )
        return suggestions

    def _create_generic_documentation(
        self, code: str, language: str, style: str
    ) -> str:
        """Create generic documentation when all fallbacks fail."""
        return f"""# {language.title()} Code Documentation

## Summary
Documentation for {language} code that provides specific functionality.

## Description
This {language} code implements certain features that require proper documentation for maintainability and understanding.

## Usage
``` {language}
{code[:200]}...
```

## Notes
This is generic documentation generated as a fallback when detailed analysis is unavailable.
"""
