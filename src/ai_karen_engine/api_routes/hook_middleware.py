"""
Hook Middleware for FastAPI Request/Response Pipeline

This middleware integrates the hook system with the FastAPI request/response
pipeline, allowing hooks to be triggered on various API events without
breaking existing functionality.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from ai_karen_engine.hooks import HookContext, HookTypes, get_hook_manager
from ai_karen_engine.utils.dependency_checks import import_fastapi

Request = import_fastapi("Request")

logger = logging.getLogger(__name__)


class HookMiddleware(BaseHTTPMiddleware):
    """
    Middleware that integrates hooks with the FastAPI request/response pipeline.

    This middleware triggers hooks at various points in the request lifecycle:
    - Before request processing (pre-request hooks)
    - After successful response (post-response hooks)
    - On request errors (error hooks)
    """

    def __init__(
        self,
        app,
        enabled: bool = True,
        hook_timeout: float = 5.0,
        excluded_paths: Optional[list] = None,
    ):
        """
        Initialize hook middleware.

        Args:
            app: FastAPI application instance
            enabled: Whether middleware is enabled
            hook_timeout: Timeout for hook execution
            excluded_paths: Paths to exclude from hook processing
        """
        super().__init__(app)
        self.enabled = enabled
        self.hook_timeout = hook_timeout
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
        ]
        self.hook_manager = get_hook_manager()

        logger.info(f"Hook middleware initialized (enabled: {enabled})")

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> StarletteResponse:
        """
        Process request through hook middleware.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response object
        """
        if not self.enabled:
            return await call_next(request)

        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        start_time = time.time()
        request_id = f"req_{int(time.time() * 1000000)}"

        # Extract request information
        request_info = await self._extract_request_info(request, request_id)

        # Trigger pre-request hooks
        pre_hook_results = await self._trigger_pre_request_hooks(request_info)

        try:
            # Process request
            response = await call_next(request)
            processing_time = time.time() - start_time

            # Extract response information
            response_info = self._extract_response_info(response, processing_time)

            # Trigger post-response hooks
            await self._trigger_post_response_hooks(
                request_info, response_info, pre_hook_results
            )

            return response

        except Exception as e:
            processing_time = time.time() - start_time

            # Trigger error hooks
            await self._trigger_error_hooks(
                request_info, str(e), processing_time, pre_hook_results
            )

            # Re-raise the exception to maintain normal error handling
            raise

    async def _extract_request_info(
        self, request: Request, request_id: str
    ) -> Dict[str, Any]:
        """Extract relevant information from the request."""
        try:
            # Try to read body (for POST/PUT requests)
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        body = body.decode("utf-8")
                except Exception:
                    body = None

            return {
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "path_params": dict(request.path_params),
                "body": body,
                "timestamp": datetime.utcnow().isoformat(),
                "client_host": getattr(request.client, "host", None)
                if request.client
                else None,
                "user_agent": request.headers.get("user-agent"),
                "content_type": request.headers.get("content-type"),
                "content_length": request.headers.get("content-length"),
            }
        except Exception as e:
            logger.warning(f"Failed to extract request info: {e}")
            return {
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "timestamp": datetime.utcnow().isoformat(),
                "extraction_error": str(e),
            }

    def _extract_response_info(
        self, response: StarletteResponse, processing_time: float
    ) -> Dict[str, Any]:
        """Extract relevant information from the response."""
        try:
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "processing_time": processing_time,
                "content_type": response.headers.get("content-type"),
                "content_length": response.headers.get("content-length"),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.warning(f"Failed to extract response info: {e}")
            return {
                "status_code": getattr(response, "status_code", 500),
                "processing_time": processing_time,
                "timestamp": datetime.utcnow().isoformat(),
                "extraction_error": str(e),
            }

    async def _trigger_pre_request_hooks(
        self, request_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger pre-request hooks."""
        try:
            # Determine hook type based on request path
            hook_type = self._determine_hook_type(request_info["path"], "pre")

            if not hook_type:
                return {"skipped": True, "reason": "no_matching_hook_type"}

            # Create hook context
            context = HookContext(
                hook_type=hook_type,
                data={
                    "request": request_info,
                    "event_type": "pre_request",
                    "api_endpoint": request_info["path"],
                    "http_method": request_info["method"],
                },
                user_context=self._extract_user_context(request_info),
            )

            # Trigger hooks with timeout
            summary = await asyncio.wait_for(
                self.hook_manager.trigger_hooks(context), timeout=self.hook_timeout
            )

            logger.debug(
                f"Pre-request hooks executed: {summary.successful_hooks}/{summary.total_hooks} for {request_info['path']}"
            )

            return {
                "hook_type": hook_type,
                "summary": summary.__dict__,
                "executed_at": datetime.utcnow().isoformat(),
            }

        except asyncio.TimeoutError:
            logger.warning(f"Pre-request hooks timed out for {request_info['path']}")
            return {
                "error": "timeout",
                "hook_type": hook_type if "hook_type" in locals() else None,
            }
        except Exception as e:
            logger.error(f"Failed to trigger pre-request hooks: {e}")
            return {"error": str(e)}

    async def _trigger_post_response_hooks(
        self,
        request_info: Dict[str, Any],
        response_info: Dict[str, Any],
        pre_hook_results: Dict[str, Any],
    ) -> None:
        """Trigger post-response hooks."""
        try:
            # Determine hook type based on request path
            hook_type = self._determine_hook_type(request_info["path"], "post")

            if not hook_type:
                return

            # Create hook context
            context = HookContext(
                hook_type=hook_type,
                data={
                    "request": request_info,
                    "response": response_info,
                    "event_type": "post_response",
                    "api_endpoint": request_info["path"],
                    "http_method": request_info["method"],
                    "pre_hook_results": pre_hook_results,
                },
                user_context=self._extract_user_context(request_info),
            )

            # Trigger hooks with timeout
            summary = await asyncio.wait_for(
                self.hook_manager.trigger_hooks(context), timeout=self.hook_timeout
            )

            logger.debug(
                f"Post-response hooks executed: {summary.successful_hooks}/{summary.total_hooks} for {request_info['path']}"
            )

        except asyncio.TimeoutError:
            logger.warning(f"Post-response hooks timed out for {request_info['path']}")
        except Exception as e:
            logger.error(f"Failed to trigger post-response hooks: {e}")

    async def _trigger_error_hooks(
        self,
        request_info: Dict[str, Any],
        error: str,
        processing_time: float,
        pre_hook_results: Dict[str, Any],
    ) -> None:
        """Trigger error hooks."""
        try:
            # Create hook context
            context = HookContext(
                hook_type=HookTypes.SYSTEM_ERROR,
                data={
                    "request": request_info,
                    "error": error,
                    "processing_time": processing_time,
                    "event_type": "request_error",
                    "api_endpoint": request_info["path"],
                    "http_method": request_info["method"],
                    "pre_hook_results": pre_hook_results,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                user_context=self._extract_user_context(request_info),
            )

            # Trigger hooks with timeout
            summary = await asyncio.wait_for(
                self.hook_manager.trigger_hooks(context), timeout=self.hook_timeout
            )

            logger.debug(
                f"Error hooks executed: {summary.successful_hooks}/{summary.total_hooks} for {request_info['path']}"
            )

        except asyncio.TimeoutError:
            logger.warning(f"Error hooks timed out for {request_info['path']}")
        except Exception as e:
            logger.error(f"Failed to trigger error hooks: {e}")

    def _determine_hook_type(self, path: str, phase: str) -> Optional[str]:
        """
        Determine the appropriate hook type based on the request path and phase.

        Args:
            path: Request path
            phase: Hook phase ('pre' or 'post')

        Returns:
            Hook type string or None if no matching type
        """
        # Map API paths to hook types
        path_mappings = {
            "/api/chat": HookTypes.PRE_MESSAGE
            if phase == "pre"
            else HookTypes.POST_MESSAGE,
            "/api/ws/chat": HookTypes.PRE_MESSAGE
            if phase == "pre"
            else HookTypes.POST_MESSAGE,
            "/api/ws/stream": HookTypes.PRE_MESSAGE
            if phase == "pre"
            else HookTypes.POST_MESSAGE,
            "/api/plugins": HookTypes.PLUGIN_EXECUTION_START
            if phase == "pre"
            else HookTypes.PLUGIN_EXECUTION_END,
            "/api/extensions": HookTypes.EXTENSION_ACTIVATED
            if phase == "pre"
            else HookTypes.EXTENSION_DEACTIVATED,
            "/api/memory": HookTypes.MEMORY_RETRIEVE
            if phase == "pre"
            else HookTypes.MEMORY_STORE,
            "/api/llm": HookTypes.LLM_REQUEST
            if phase == "pre"
            else HookTypes.LLM_RESPONSE,
            "/api/auth": HookTypes.USER_LOGIN
            if phase == "pre"
            else HookTypes.USER_LOGIN,
            "/api/files": HookTypes.FILE_UPLOADED
            if phase == "pre"
            else HookTypes.FILE_PROCESSED,
        }

        # Check for exact matches first
        if path in path_mappings:
            return path_mappings[path]

        # Check for path prefixes
        for path_prefix, hook_type in path_mappings.items():
            if path.startswith(path_prefix):
                return hook_type

        # Default hook types for unknown paths
        if phase == "pre":
            return "api_request_start"
        else:
            return "api_request_end"

    def _extract_user_context(self, request_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user context from request information."""
        try:
            user_context = {}

            # Extract user ID from various sources
            headers = request_info.get("headers", {})
            query_params = request_info.get("query_params", {})
            path_params = request_info.get("path_params", {})

            # Check for user ID in headers
            if "x-user-id" in headers:
                user_context["user_id"] = headers["x-user-id"]
            elif "user-id" in headers:
                user_context["user_id"] = headers["user-id"]

            # Check for user ID in query parameters
            if "user_id" in query_params:
                user_context["user_id"] = query_params["user_id"]

            # Check for user ID in path parameters
            if "user_id" in path_params:
                user_context["user_id"] = path_params["user_id"]

            # Extract session information
            if "x-session-id" in headers:
                user_context["session_id"] = headers["x-session-id"]
            elif "session_id" in query_params:
                user_context["session_id"] = query_params["session_id"]

            # Extract conversation ID
            if "x-conversation-id" in headers:
                user_context["conversation_id"] = headers["x-conversation-id"]
            elif "conversation_id" in query_params:
                user_context["conversation_id"] = query_params["conversation_id"]
            elif "conversation_id" in path_params:
                user_context["conversation_id"] = path_params["conversation_id"]

            # Add request metadata
            user_context.update(
                {
                    "client_host": request_info.get("client_host"),
                    "user_agent": request_info.get("user_agent"),
                    "request_id": request_info.get("request_id"),
                }
            )

            return user_context

        except Exception as e:
            logger.warning(f"Failed to extract user context: {e}")
            return {"extraction_error": str(e)}

    def enable(self) -> None:
        """Enable the hook middleware."""
        self.enabled = True
        logger.info("Hook middleware enabled")

    def disable(self) -> None:
        """Disable the hook middleware."""
        self.enabled = False
        logger.info("Hook middleware disabled")

    def is_enabled(self) -> bool:
        """Check if the hook middleware is enabled."""
        return self.enabled

    def add_excluded_path(self, path: str) -> None:
        """Add a path to the exclusion list."""
        if path not in self.excluded_paths:
            self.excluded_paths.append(path)
            logger.info(f"Added excluded path: {path}")

    def remove_excluded_path(self, path: str) -> None:
        """Remove a path from the exclusion list."""
        if path in self.excluded_paths:
            self.excluded_paths.remove(path)
            logger.info(f"Removed excluded path: {path}")

    def get_stats(self) -> Dict[str, Any]:
        """Get middleware statistics."""
        return {
            "enabled": self.enabled,
            "hook_timeout": self.hook_timeout,
            "excluded_paths": self.excluded_paths,
            "hook_manager_stats": self.hook_manager.get_summary(),
        }


def create_hook_middleware(
    app,
    enabled: bool = True,
    hook_timeout: float = 5.0,
    excluded_paths: Optional[list] = None,
) -> HookMiddleware:
    """
    Create and configure hook middleware.

    Args:
        app: FastAPI application instance
        enabled: Whether middleware is enabled
        hook_timeout: Timeout for hook execution
        excluded_paths: Paths to exclude from hook processing

    Returns:
        Configured HookMiddleware instance
    """
    return HookMiddleware(
        app=app,
        enabled=enabled,
        hook_timeout=hook_timeout,
        excluded_paths=excluded_paths,
    )


__all__ = ["HookMiddleware", "create_hook_middleware"]
