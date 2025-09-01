"""
Enhanced Error Handling Middleware with AG-UI and CopilotKit Fallbacks

This middleware extends existing error handling to include:
- AG-UI component failure recovery
- CopilotKit error handling with LLM provider fallback mechanisms
- Hook system error recovery with retry logic and circuit breaker patterns
- Graceful degradation for AI features
"""

import asyncio
import logging
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ai_karen_engine.llm_orchestrator import get_orchestrator
from ai_karen_engine.hooks import get_hook_manager
from ai_karen_engine.server.http_validator import HTTPRequestValidator

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Enhanced error types for AG-UI and CopilotKit integration."""
    
    # AG-UI specific errors
    AG_UI_COMPONENT_FAILURE = "ag_ui_component_failure"
    AG_UI_DATA_LOAD_ERROR = "ag_ui_data_load_error"
    AG_UI_GRID_RENDER_ERROR = "ag_ui_grid_render_error"
    AG_UI_CHART_RENDER_ERROR = "ag_ui_chart_render_error"
    
    # CopilotKit specific errors
    COPILOTKIT_API_UNAVAILABLE = "copilotkit_api_unavailable"
    COPILOTKIT_CONTEXT_TOO_LARGE = "copilotkit_context_too_large"
    COPILOTKIT_MODEL_UNAVAILABLE = "copilotkit_model_unavailable"
    COPILOTKIT_RATE_LIMIT = "copilotkit_rate_limit"
    
    # Hook system errors
    HOOK_EXECUTION_TIMEOUT = "hook_execution_timeout"
    HOOK_CIRCUIT_BREAKER_OPEN = "hook_circuit_breaker_open"
    HOOK_SYSTEM_OVERLOAD = "hook_system_overload"
    
    # LLM provider fallback errors
    LLM_PROVIDER_UNAVAILABLE = "llm_provider_unavailable"
    LLM_FALLBACK_EXHAUSTED = "llm_fallback_exhausted"
    
    # General system errors
    SYSTEM_OVERLOAD = "system_overload"
    GRACEFUL_DEGRADATION = "graceful_degradation"


class FallbackStrategy(Enum):
    """Fallback strategies for different error types."""
    
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    FALLBACK_PROVIDER = "fallback_provider"
    CACHED_RESPONSE = "cached_response"
    SIMPLIFIED_UI = "simplified_ui"


class ErrorRecoveryConfig:
    """Configuration for error recovery strategies."""
    
    def __init__(self):
        # Retry configuration
        self.max_retries = 3
        self.retry_backoff_base = 1.0
        self.retry_backoff_multiplier = 2.0
        
        # Circuit breaker configuration
        self.circuit_breaker_failure_threshold = 5
        self.circuit_breaker_timeout = 60.0
        self.circuit_breaker_half_open_max_calls = 3
        
        # Timeout configuration
        self.hook_execution_timeout = 10.0
        self.copilotkit_request_timeout = 30.0
        self.ag_ui_render_timeout = 5.0
        
        # Fallback configuration
        self.enable_graceful_degradation = True
        self.enable_cached_responses = True
        self.enable_simplified_ui = True


class CircuitBreakerState:
    """Circuit breaker state management."""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"  # closed, open, half_open
        self.half_open_calls = 0
        self.max_half_open_calls = 3
    
    def record_success(self):
        """Record a successful operation."""
        self.failure_count = 0
        self.state = "closed"
        self.half_open_calls = 0
    
    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    def can_execute(self) -> bool:
        """Check if operation can be executed."""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half_open"
                self.half_open_calls = 0
                return True
            return False
        
        if self.state == "half_open":
            if self.half_open_calls < self.max_half_open_calls:
                self.half_open_calls += 1
                return True
            return False
        
        return False


class EnhancedErrorHandler:
    """Enhanced error handler with AG-UI and CopilotKit fallbacks."""
    
    def __init__(self, config: Optional[ErrorRecoveryConfig] = None):
        self.config = config or ErrorRecoveryConfig()
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.error_cache: Dict[str, Dict[str, Any]] = {}
        self.llm_orchestrator = get_orchestrator()
        self.hook_manager = get_hook_manager()
        
        # Initialize circuit breakers for different components
        self._init_circuit_breakers()
    
    def _init_circuit_breakers(self):
        """Initialize circuit breakers for different components."""
        components = [
            "ag_ui_grid",
            "ag_ui_charts",
            "copilotkit_api",
            "hook_system",
            "llm_providers"
        ]
        
        for component in components:
            self.circuit_breakers[component] = CircuitBreakerState(
                failure_threshold=self.config.circuit_breaker_failure_threshold,
                timeout=self.config.circuit_breaker_timeout
            )
    
    async def handle_ag_ui_error(self, error: Exception, component: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AG-UI component errors with fallback strategies."""
        error_type = self._classify_ag_ui_error(error, component)
        
        logger.warning(f"AG-UI error in {component}: {error}")
        
        # Check circuit breaker
        circuit_breaker = self.circuit_breakers.get(f"ag_ui_{component}")
        if circuit_breaker and not circuit_breaker.can_execute():
            return self._create_simplified_ui_fallback(component, context)
        
        # Try recovery strategies
        if error_type == ErrorType.AG_UI_DATA_LOAD_ERROR:
            return await self._handle_ag_ui_data_error(error, component, context)
        elif error_type == ErrorType.AG_UI_GRID_RENDER_ERROR:
            return await self._handle_ag_ui_grid_error(error, component, context)
        elif error_type == ErrorType.AG_UI_CHART_RENDER_ERROR:
            return await self._handle_ag_ui_chart_error(error, component, context)
        else:
            return self._create_simplified_ui_fallback(component, context)
    
    async def handle_copilotkit_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle CopilotKit errors with LLM provider fallback."""
        error_type = self._classify_copilotkit_error(error)
        
        logger.warning(f"CopilotKit error: {error}")
        
        # Check circuit breaker
        circuit_breaker = self.circuit_breakers.get("copilotkit_api")
        if circuit_breaker:
            if not circuit_breaker.can_execute():
                return await self._fallback_to_llm_providers(context)
            circuit_breaker.record_failure()
        
        # Try specific recovery strategies
        if error_type == ErrorType.COPILOTKIT_API_UNAVAILABLE:
            return await self._fallback_to_llm_providers(context)
        elif error_type == ErrorType.COPILOTKIT_CONTEXT_TOO_LARGE:
            return await self._handle_context_too_large(context)
        elif error_type == ErrorType.COPILOTKIT_MODEL_UNAVAILABLE:
            return await self._fallback_to_alternative_models(context)
        elif error_type == ErrorType.COPILOTKIT_RATE_LIMIT:
            return await self._handle_rate_limit_with_backoff(context)
        else:
            return await self._fallback_to_llm_providers(context)
    
    async def handle_hook_system_error(self, error: Exception, hook_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle hook system errors with retry logic and circuit breaker."""
        error_type = self._classify_hook_error(error)
        
        logger.warning(f"Hook system error for {hook_type}: {error}")
        
        # Check circuit breaker
        circuit_breaker = self.circuit_breakers.get("hook_system")
        if circuit_breaker:
            if not circuit_breaker.can_execute():
                return self._create_hook_bypass_response(hook_type, context)
            circuit_breaker.record_failure()
        
        # Try recovery strategies
        if error_type == ErrorType.HOOK_EXECUTION_TIMEOUT:
            return await self._handle_hook_timeout(hook_type, context)
        elif error_type == ErrorType.HOOK_SYSTEM_OVERLOAD:
            return await self._handle_hook_overload(hook_type, context)
        else:
            return self._create_hook_bypass_response(hook_type, context)
    
    async def handle_llm_provider_error(self, error: Exception, provider: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle LLM provider errors with fallback mechanisms."""
        logger.warning(f"LLM provider error for {provider}: {error}")
        
        # Check circuit breaker
        circuit_breaker = self.circuit_breakers.get("llm_providers")
        if circuit_breaker:
            if not circuit_breaker.can_execute():
                return self._create_cached_response(context)
            circuit_breaker.record_failure()
        
        # Try fallback providers
        try:
            fallback_response = await self._try_fallback_providers(provider, context)
            if circuit_breaker:
                circuit_breaker.record_success()
            return fallback_response
        except Exception as fallback_error:
            logger.error(f"All LLM providers failed: {fallback_error}")
            return self._create_cached_response(context)
    
    def _classify_ag_ui_error(self, error: Exception, component: str) -> ErrorType:
        """Classify AG-UI errors by type."""
        error_msg = str(error).lower()
        
        if "data" in error_msg and ("load" in error_msg or "fetch" in error_msg):
            return ErrorType.AG_UI_DATA_LOAD_ERROR
        elif "grid" in error_msg or component == "grid":
            return ErrorType.AG_UI_GRID_RENDER_ERROR
        elif "chart" in error_msg or component == "chart":
            return ErrorType.AG_UI_CHART_RENDER_ERROR
        else:
            return ErrorType.AG_UI_COMPONENT_FAILURE
    
    def _classify_copilotkit_error(self, error: Exception) -> ErrorType:
        """Classify CopilotKit errors by type."""
        error_msg = str(error).lower()
        
        if "unavailable" in error_msg or "connection" in error_msg:
            return ErrorType.COPILOTKIT_API_UNAVAILABLE
        elif "context" in error_msg and "large" in error_msg:
            return ErrorType.COPILOTKIT_CONTEXT_TOO_LARGE
        elif "model" in error_msg and "unavailable" in error_msg:
            return ErrorType.COPILOTKIT_MODEL_UNAVAILABLE
        elif "rate limit" in error_msg or "429" in error_msg:
            return ErrorType.COPILOTKIT_RATE_LIMIT
        else:
            return ErrorType.COPILOTKIT_API_UNAVAILABLE
    
    def _classify_hook_error(self, error: Exception) -> ErrorType:
        """Classify hook system errors by type."""
        error_msg = str(error).lower()
        
        if "timeout" in error_msg:
            return ErrorType.HOOK_EXECUTION_TIMEOUT
        elif "overload" in error_msg or "too many" in error_msg:
            return ErrorType.HOOK_SYSTEM_OVERLOAD
        else:
            return ErrorType.HOOK_EXECUTION_TIMEOUT
    
    async def _handle_ag_ui_data_error(self, error: Exception, component: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AG-UI data loading errors."""
        # Try to use cached data if available
        cache_key = f"ag_ui_data_{component}_{hash(str(context))}"
        if cache_key in self.error_cache:
            cached_data = self.error_cache[cache_key]
            logger.info(f"Using cached data for AG-UI {component}")
            return {
                "fallback_type": "cached_data",
                "data": cached_data["data"],
                "warning": "Using cached data due to loading error",
                "timestamp": cached_data["timestamp"]
            }
        
        # Return simplified data structure
        return {
            "fallback_type": "simplified_data",
            "data": self._create_simplified_data(component),
            "error": "Data loading failed, showing simplified view",
            "retry_available": True
        }
    
    async def _handle_ag_ui_grid_error(self, error: Exception, component: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AG-UI grid rendering errors."""
        return {
            "fallback_type": "simple_table",
            "component": "SimpleTable",
            "data": context.get("data", []),
            "columns": self._extract_simple_columns(context.get("data", [])),
            "error": "Grid rendering failed, using simple table",
            "retry_available": True
        }
    
    async def _handle_ag_ui_chart_error(self, error: Exception, component: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AG-UI chart rendering errors."""
        return {
            "fallback_type": "simple_chart",
            "component": "SimpleChart",
            "data": context.get("data", []),
            "chart_type": "bar",  # Default to simple bar chart
            "error": "Chart rendering failed, using simple visualization",
            "retry_available": True
        }
    
    def _create_simplified_ui_fallback(self, component: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create simplified UI fallback."""
        return {
            "fallback_type": "simplified_ui",
            "component": f"Simple{component.title()}",
            "data": context.get("data", {}),
            "error": f"{component} component failed, using simplified interface",
            "features_disabled": ["sorting", "filtering", "advanced_interactions"],
            "retry_available": True
        }
    
    async def _fallback_to_llm_providers(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to regular LLM providers when CopilotKit fails."""
        try:
            prompt = context.get("prompt", "")
            if not prompt:
                return self._create_cached_response(context)
            
            # Use LLM orchestrator for fallback
            response = await asyncio.wait_for(
                self.llm_orchestrator.enhanced_route(prompt, **context),
                timeout=self.config.copilotkit_request_timeout
            )
            
            return {
                "fallback_type": "llm_provider",
                "response": response,
                "provider": "fallback_llm",
                "warning": "CopilotKit unavailable, using fallback LLM provider"
            }
        except Exception as e:
            logger.error(f"LLM fallback failed: {e}")
            return self._create_cached_response(context)
    
    async def _handle_context_too_large(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle context too large error by truncating context."""
        try:
            # Truncate context to manageable size
            truncated_context = self._truncate_context(context)
            
            # Retry with truncated context
            prompt = truncated_context.get("prompt", "")
            response = await self.llm_orchestrator.route_with_copilotkit(prompt, truncated_context)
            
            return {
                "fallback_type": "truncated_context",
                "response": response,
                "warning": "Context was truncated due to size limits"
            }
        except Exception as e:
            logger.error(f"Context truncation fallback failed: {e}")
            return await self._fallback_to_llm_providers(context)
    
    async def _fallback_to_alternative_models(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to alternative models when primary model unavailable."""
        try:
            # Try different model configurations
            alternative_models = ["gpt-3.5-turbo", "claude-3-haiku", "llama-3.1-8b"]
            
            for model in alternative_models:
                try:
                    context_with_model = {**context, "model": model}
                    response = await self.llm_orchestrator.enhanced_route(
                        context.get("prompt", ""), 
                        **context_with_model
                    )
                    return {
                        "fallback_type": "alternative_model",
                        "response": response,
                        "model": model,
                        "warning": f"Using alternative model: {model}"
                    }
                except Exception:
                    continue
            
            # If all models fail, use cached response
            return self._create_cached_response(context)
        except Exception as e:
            logger.error(f"Alternative model fallback failed: {e}")
            return self._create_cached_response(context)
    
    async def _handle_rate_limit_with_backoff(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle rate limit with exponential backoff."""
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
            
            try:
                response = await self.llm_orchestrator.route_with_copilotkit(
                    context.get("prompt", ""), 
                    context
                )
                return {
                    "fallback_type": "retry_after_backoff",
                    "response": response,
                    "attempts": attempt + 1,
                    "warning": f"Request succeeded after {attempt + 1} attempts"
                }
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Rate limit backoff failed after {max_retries} attempts: {e}")
                    return await self._fallback_to_llm_providers(context)
        
        return self._create_cached_response(context)
    
    async def _handle_hook_timeout(self, hook_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle hook execution timeout."""
        return {
            "fallback_type": "hook_bypass",
            "hook_type": hook_type,
            "status": "bypassed",
            "warning": f"Hook {hook_type} timed out, continuing without hook execution",
            "retry_available": True
        }
    
    async def _handle_hook_overload(self, hook_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle hook system overload."""
        return {
            "fallback_type": "hook_bypass",
            "hook_type": hook_type,
            "status": "bypassed",
            "warning": f"Hook system overloaded, bypassing {hook_type} hooks",
            "retry_available": False
        }
    
    def _create_hook_bypass_response(self, hook_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create response when hooks are bypassed."""
        return {
            "fallback_type": "hook_bypass",
            "hook_type": hook_type,
            "status": "bypassed",
            "warning": f"Hook {hook_type} bypassed due to system issues",
            "context": context
        }
    
    async def _try_fallback_providers(self, failed_provider: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Try fallback LLM providers."""
        # Get list of available providers excluding the failed one
        available_providers = ["openai", "anthropic", "llama-cpp", "huggingface"]
        if failed_provider in available_providers:
            available_providers.remove(failed_provider)
        
        for provider in available_providers:
            try:
                # Try each provider with timeout
                response = await asyncio.wait_for(
                    self.llm_orchestrator.enhanced_route(
                        context.get("prompt", ""),
                        provider=provider,
                        **context
                    ),
                    timeout=30.0
                )
                
                return {
                    "fallback_type": "provider_fallback",
                    "response": response,
                    "provider": provider,
                    "warning": f"Fallback to {provider} due to {failed_provider} failure"
                }
            except Exception as e:
                logger.debug(f"Provider {provider} also failed: {e}")
                continue
        
        raise Exception("All LLM providers failed")
    
    def _create_cached_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create cached response when all else fails."""
        cache_key = f"response_{hash(str(context.get('prompt', '')))}"
        
        if cache_key in self.error_cache:
            cached_response = self.error_cache[cache_key]
            return {
                "fallback_type": "cached_response",
                "response": cached_response["response"],
                "warning": "Using cached response due to system unavailability",
                "timestamp": cached_response["timestamp"]
            }
        
        # Generic fallback response
        return {
            "fallback_type": "generic_fallback",
            "response": "I'm experiencing technical difficulties. Please try again later.",
            "error": "All systems unavailable",
            "retry_available": True
        }
    
    def _create_simplified_data(self, component: str) -> List[Dict[str, Any]]:
        """Create simplified data structure for fallback."""
        if component == "grid":
            return [
                {"id": 1, "status": "Data loading failed", "message": "Please refresh to retry"}
            ]
        elif component == "chart":
            return [
                {"label": "Error", "value": 0, "message": "Chart data unavailable"}
            ]
        else:
            return [{"error": "Component data unavailable"}]
    
    def _extract_simple_columns(self, data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract simple column definitions from data."""
        if not data:
            return [{"field": "message", "headerName": "Status"}]
        
        first_row = data[0]
        return [
            {"field": key, "headerName": key.replace("_", " ").title()}
            for key in first_row.keys()
        ]
    
    def _truncate_context(self, context: Dict[str, Any], max_tokens: int = 4000) -> Dict[str, Any]:
        """Truncate context to fit within token limits."""
        truncated = context.copy()
        
        # Truncate conversation history
        if "conversation_history" in truncated:
            history = truncated["conversation_history"]
            if len(history) > 10:  # Keep only last 10 messages
                truncated["conversation_history"] = history[-10:]
        
        # Truncate prompt if too long
        if "prompt" in truncated:
            prompt = truncated["prompt"]
            if len(prompt) > max_tokens * 4:  # Rough token estimation
                truncated["prompt"] = prompt[:max_tokens * 4] + "... [truncated]"
        
        return truncated


class EnhancedErrorMiddleware(BaseHTTPMiddleware):
    """Enhanced error handling middleware with AG-UI and CopilotKit fallbacks."""
    
    def __init__(self, app, config: Optional[ErrorRecoveryConfig] = None):
        super().__init__(app)
        self.error_handler = EnhancedErrorHandler(config)
        self.config = config or ErrorRecoveryConfig()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with enhanced error handling."""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            return await self._handle_error(request, e)
    
    async def _handle_error(self, request: Request, error: Exception) -> JSONResponse:
        """Handle errors with appropriate fallback strategies."""
        error_context = {
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown")
        }
        
        # Classify error and apply appropriate handling
        if self._is_ag_ui_error(error, request):
            component = self._extract_ag_ui_component(request)
            fallback_response = await self.error_handler.handle_ag_ui_error(
                error, component, error_context
            )
            return self._create_error_response(fallback_response, 200)  # Graceful degradation
        
        elif self._is_copilotkit_error(error, request):
            fallback_response = await self.error_handler.handle_copilotkit_error(
                error, error_context
            )
            return self._create_error_response(fallback_response, 200)  # Graceful degradation
        
        elif self._is_hook_error(error, request):
            hook_type = self._extract_hook_type(request)
            fallback_response = await self.error_handler.handle_hook_system_error(
                error, hook_type, error_context
            )
            return self._create_error_response(fallback_response, 200)  # Continue processing
        
        elif self._is_llm_provider_error(error, request):
            provider = self._extract_provider(request)
            fallback_response = await self.error_handler.handle_llm_provider_error(
                error, provider, error_context
            )
            return self._create_error_response(fallback_response, 200)  # Graceful degradation
        
        else:
            # Handle as general error
            logger.error(f"Unhandled error: {error}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "fallback_type": "generic_error",
                    "message": "An unexpected error occurred. Please try again.",
                    "request_id": error_context["request_id"],
                    "timestamp": error_context["timestamp"]
                }
            )
    
    def _is_ag_ui_error(self, error: Exception, request: Request) -> bool:
        """Check if error is AG-UI related."""
        error_msg = str(error).lower()
        path = request.url.path.lower()
        
        return (
            "ag-grid" in error_msg or
            "ag-charts" in error_msg or
            "/api/analytics" in path or
            "/api/grid" in path or
            "/api/charts" in path
        )
    
    def _is_copilotkit_error(self, error: Exception, request: Request) -> bool:
        """Check if error is CopilotKit related."""
        error_msg = str(error).lower()
        path = request.url.path.lower()
        
        return (
            "copilotkit" in error_msg or
            "/api/copilot" in path or
            "/api/ai/suggestions" in path or
            "/api/ai/code" in path
        )
    
    def _is_hook_error(self, error: Exception, request: Request) -> bool:
        """Check if error is hook system related."""
        error_msg = str(error).lower()
        path = request.url.path.lower()
        
        return (
            "hook" in error_msg or
            "/api/hooks" in path or
            "hook_execution" in error_msg
        )
    
    def _is_llm_provider_error(self, error: Exception, request: Request) -> bool:
        """Check if error is LLM provider related."""
        error_msg = str(error).lower()
        path = request.url.path.lower()
        
        return (
            "llm" in error_msg or
            "provider" in error_msg or
            "/api/llm" in path or
            "/api/chat" in path
        )
    
    def _extract_ag_ui_component(self, request: Request) -> str:
        """Extract AG-UI component from request."""
        path = request.url.path.lower()
        
        if "grid" in path:
            return "grid"
        elif "chart" in path:
            return "chart"
        elif "analytics" in path:
            return "analytics"
        else:
            return "unknown"
    
    def _extract_hook_type(self, request: Request) -> str:
        """Extract hook type from request."""
        path = request.url.path.lower()
        
        if "chat" in path:
            return "chat_hooks"
        elif "plugin" in path:
            return "plugin_hooks"
        elif "extension" in path:
            return "extension_hooks"
        else:
            return "unknown_hooks"
    
    def _extract_provider(self, request: Request) -> str:
        """Extract LLM provider from request."""
        # Try to get provider from query params or headers
        provider = request.query_params.get("provider", "unknown")
        if provider == "unknown":
            provider = request.headers.get("x-llm-provider", "unknown")
        return provider
    
    def _create_error_response(self, fallback_response: Dict[str, Any], status_code: int) -> JSONResponse:
        """Create standardized error response."""
        return JSONResponse(
            status_code=status_code,
            content={
                **fallback_response,
                "success": status_code == 200,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


def create_enhanced_error_middleware(app, config: Optional[ErrorRecoveryConfig] = None):
    """Create and configure enhanced error middleware."""
    return EnhancedErrorMiddleware(app, config)


__all__ = [
    "EnhancedErrorMiddleware",
    "EnhancedErrorHandler", 
    "ErrorRecoveryConfig",
    "ErrorType",
    "FallbackStrategy",
    "create_enhanced_error_middleware"
]