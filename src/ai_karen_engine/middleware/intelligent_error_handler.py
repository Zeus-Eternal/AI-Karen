"""
Intelligent Error Handler Middleware

This middleware provides global error handling with intelligent error responses.
It catches unhandled exceptions and HTTP errors, then uses the error response
service to generate user-friendly, actionable error messages.
"""

import logging
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Callable

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ai_karen_engine.services.error_response_service import ErrorResponseService

logger = logging.getLogger(__name__)


class IntelligentErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for intelligent global error handling.
    
    This middleware:
    1. Catches unhandled exceptions and HTTP errors
    2. Uses the error response service to generate intelligent responses
    3. Provides consistent error response format across the application
    4. Logs errors with appropriate detail levels
    """
    
    def __init__(self, app, enable_intelligent_responses: bool = True, debug_mode: bool = False):
        super().__init__(app)
        self.enable_intelligent_responses = enable_intelligent_responses
        self.debug_mode = debug_mode
        
        # Lazy initialization to avoid circular imports
        self._error_response_service: Optional[ErrorResponseService] = None
        
        # Paths that should use simple error responses (e.g., API endpoints that expect specific formats)
        self.simple_error_paths = {
            "/api/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        }
    
    def _get_error_response_service(self) -> Optional[ErrorResponseService]:
        """Get error response service instance, initializing if necessary."""
        if not self.enable_intelligent_responses:
            return None
            
        if self._error_response_service is None:
            try:
                self._error_response_service = ErrorResponseService()
            except Exception as e:
                logger.warning(f"Failed to initialize error response service: {e}")
                self._error_response_service = None
        return self._error_response_service
    
    def _should_use_simple_error(self, request: Request) -> bool:
        """Check if request should use simple error responses."""
        path = request.url.path
        
        # Use simple errors for specific paths
        if path in self.simple_error_paths:
            return True
            
        # Use simple errors for paths that start with simple error prefixes
        for simple_path in self.simple_error_paths:
            if path.startswith(simple_path):
                return True
                
        return False
    
    async def _extract_request_metadata(self, request: Request) -> Dict[str, str]:
        """Extract request metadata for error analysis."""
        xff = request.headers.get("x-forwarded-for")
        ip = (
            xff.split(",")[0].strip()
            if xff
            else (request.client.host if request.client else "unknown")
        )
        return {
            "ip_address": ip,
            "user_agent": request.headers.get("user-agent", ""),
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def _extract_provider_from_error(self, error_message: str, traceback_str: str) -> Optional[str]:
        """Extract provider name from error message or traceback."""
        # Common provider patterns
        provider_patterns = {
            "openai": ["openai", "gpt", "chatgpt"],
            "anthropic": ["anthropic", "claude"],
            "huggingface": ["huggingface", "transformers"],
            "groq": ["groq"],
            "cohere": ["cohere"],
        }
        
        text_to_check = f"{error_message} {traceback_str}".lower()
        
        for provider, patterns in provider_patterns.items():
            if any(pattern in text_to_check for pattern in patterns):
                return provider
        
        return None
    
    async def _create_intelligent_error_response(
        self,
        error_message: str,
        error_type: str,
        status_code: int,
        request_meta: Dict[str, str],
        traceback_str: Optional[str] = None
    ) -> JSONResponse:
        """Create an intelligent error response using the error response service."""
        error_service = self._get_error_response_service()
        
        if not error_service:
            # Fallback to simple error response
            response_data = {"detail": error_message}
            if self.debug_mode and traceback_str:
                response_data["traceback"] = traceback_str
            return JSONResponse(response_data, status_code=status_code)
        
        try:
            # Extract provider name from error
            provider_name = self._extract_provider_from_error(
                error_message, traceback_str or ""
            )
            
            # Generate intelligent error response
            intelligent_response = error_service.analyze_error(
                error_message=error_message,
                error_type=error_type,
                status_code=status_code,
                provider_name=provider_name,
                additional_context={
                    **request_meta,
                    "traceback": traceback_str if self.debug_mode else None,
                }
            )
            
            # Convert to API response format
            response_data = {
                "detail": intelligent_response.summary,
                "error": {
                    "title": intelligent_response.title,
                    "category": intelligent_response.category,
                    "severity": intelligent_response.severity,
                    "next_steps": intelligent_response.next_steps,
                    "contact_admin": intelligent_response.contact_admin,
                    "retry_after": intelligent_response.retry_after,
                    "help_url": intelligent_response.help_url,
                    "timestamp": request_meta["timestamp"],
                }
            }
            
            # Add provider health if available
            if intelligent_response.provider_health:
                response_data["error"]["provider_health"] = intelligent_response.provider_health
            
            # Add technical details if available and in debug mode
            if self.debug_mode and intelligent_response.technical_details:
                response_data["error"]["technical_details"] = intelligent_response.technical_details
            
            # Add traceback in debug mode
            if self.debug_mode and traceback_str:
                response_data["error"]["traceback"] = traceback_str
            
            headers = {}
            if intelligent_response.retry_after:
                headers["Retry-After"] = str(intelligent_response.retry_after)
            
            return JSONResponse(
                response_data,
                status_code=status_code,
                headers=headers
            )
            
        except Exception as e:
            logger.error(f"Failed to generate intelligent error response: {e}")
            # Fallback to simple error response
            response_data = {"detail": error_message}
            if self.debug_mode and traceback_str:
                response_data["traceback"] = traceback_str
            return JSONResponse(response_data, status_code=status_code)
    
    async def _create_simple_error_response(
        self,
        error_message: str,
        status_code: int,
        traceback_str: Optional[str] = None
    ) -> JSONResponse:
        """Create a simple error response without intelligent analysis."""
        response_data = {"detail": error_message}
        if self.debug_mode and traceback_str:
            response_data["traceback"] = traceback_str
        return JSONResponse(response_data, status_code=status_code)
    
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Main middleware dispatch method."""
        # Extract request metadata
        request_meta = await self._extract_request_metadata(request)
        
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # Handle HTTP exceptions
            logger.info(
                f"HTTP exception: {e.status_code} - {e.detail}",
                extra={
                    "status_code": e.status_code,
                    "path": request_meta["path"],
                    "method": request_meta["method"],
                    "ip_address": request_meta["ip_address"],
                }
            )
            
            # Use simple error response for certain paths
            if self._should_use_simple_error(request):
                return await self._create_simple_error_response(
                    error_message=str(e.detail),
                    status_code=e.status_code
                )
            
            # Use intelligent error response
            return await self._create_intelligent_error_response(
                error_message=str(e.detail),
                error_type="http_exception",
                status_code=e.status_code,
                request_meta=request_meta
            )
            
        except Exception as e:
            # Handle unhandled exceptions
            error_message = str(e)
            error_type = type(e).__name__
            traceback_str = traceback.format_exc()
            
            logger.error(
                f"Unhandled exception: {error_type} - {error_message}",
                extra={
                    "error_type": error_type,
                    "path": request_meta["path"],
                    "method": request_meta["method"],
                    "ip_address": request_meta["ip_address"],
                    "traceback": traceback_str,
                }
            )
            
            # Use simple error response for certain paths
            if self._should_use_simple_error(request):
                return await self._create_simple_error_response(
                    error_message="Internal server error",
                    status_code=500,
                    traceback_str=traceback_str
                )
            
            # Use intelligent error response
            return await self._create_intelligent_error_response(
                error_message=error_message,
                error_type=error_type,
                status_code=500,
                request_meta=request_meta,
                traceback_str=traceback_str
            )


# Convenience function for adding middleware to FastAPI app
def add_intelligent_error_handler(
    app, 
    enable_intelligent_responses: bool = True, 
    debug_mode: bool = False
):
    """Add intelligent error handler middleware to FastAPI app."""
    app.add_middleware(
        IntelligentErrorHandlerMiddleware,
        enable_intelligent_responses=enable_intelligent_responses,
        debug_mode=debug_mode
    )
