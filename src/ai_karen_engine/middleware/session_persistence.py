"""
Session Persistence Middleware

This middleware integrates the enhanced session management system with automatic
token refresh and intelligent error responses. It handles session validation,
automatic token refresh for expired tokens, and provides intelligent error
responses when authentication fails.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Callable

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ai_karen_engine.auth.tokens import EnhancedTokenManager
from ai_karen_engine.auth.cookie_manager import SessionCookieManager, get_cookie_manager
from ai_karen_engine.auth.service import AuthService, get_auth_service
from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.exceptions import (
    AuthError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    AccountLockedError,
    SessionExpiredError,
    SessionNotFoundError,
    RateLimitExceededError,
    SecurityError,
    AnomalyDetectedError,
)
from ai_karen_engine.services.error_response_service import ErrorResponseService

logger = logging.getLogger(__name__)


class SessionPersistenceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for session persistence with automatic token refresh and intelligent error responses.
    
    This middleware:
    1. Validates access tokens from Authorization headers
    2. Automatically attempts token refresh for expired tokens using HttpOnly cookies
    3. Provides intelligent error responses for authentication failures
    4. Maintains backward compatibility with existing session validation
    """
    
    def __init__(self, app, enable_intelligent_errors: bool = True):
        super().__init__(app)
        self.enable_intelligent_errors = enable_intelligent_errors
        
        # Lazy initialization to avoid circular imports
        self._token_manager: Optional[EnhancedTokenManager] = None
        self._cookie_manager: Optional[SessionCookieManager] = None
        self._auth_service: Optional[AuthService] = None
        self._error_response_service: Optional[ErrorResponseService] = None
        
        # Paths that don't require authentication
        self.public_paths = {
            "/api/auth/login",
            "/api/auth/register", 
            "/api/auth/refresh",
            "/api/auth/health",
            "/api/health",
            "/api/health/degraded-mode",
            "/api/reasoning/analyze",
            "/api/analytics",  # All analytics endpoints
            "/system/status",  # System status endpoint
            "/copilot",  # All CopilotKit endpoints
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico",
        }
        
        # Paths that should skip session persistence (use existing auth middleware)
        self.skip_session_persistence_paths = {
            "/api/auth/",  # Auth routes handle their own session management
        }
    
    async def _get_token_manager(self) -> EnhancedTokenManager:
        """Get token manager instance, initializing if necessary."""
        if self._token_manager is None:
            auth_config = AuthConfig.from_env()
            self._token_manager = EnhancedTokenManager(auth_config.jwt)
        return self._token_manager
    
    def _get_cookie_manager(self) -> SessionCookieManager:
        """Get cookie manager instance, initializing if necessary."""
        if self._cookie_manager is None:
            self._cookie_manager = get_cookie_manager()
        return self._cookie_manager
    
    async def _get_auth_service(self) -> AuthService:
        """Get auth service instance, initializing if necessary."""
        if self._auth_service is None:
            self._auth_service = await get_auth_service()
        return self._auth_service
    
    def _get_error_response_service(self) -> Optional[ErrorResponseService]:
        """Get error response service instance, initializing if necessary."""
        if not self.enable_intelligent_errors:
            return None
            
        if self._error_response_service is None:
            try:
                self._error_response_service = ErrorResponseService()
            except Exception as e:
                logger.warning(f"Failed to initialize error response service: {e}")
                self._error_response_service = None
        return self._error_response_service
    
    def _should_skip_auth(self, request: Request) -> bool:
        """Check if request should skip authentication."""
        path = request.url.path
        
        # Skip public paths
        if path in self.public_paths:
            return True
            
        # Skip paths that start with public prefixes
        for public_path in self.public_paths:
            if path.startswith(public_path):
                return True
                
        return False
    
    def _should_skip_session_persistence(self, request: Request) -> bool:
        """Check if request should skip session persistence middleware."""
        path = request.url.path
        
        # Skip auth routes that handle their own session management
        for skip_path in self.skip_session_persistence_paths:
            if path.startswith(skip_path):
                return True
                
        return False
    
    async def _extract_request_metadata(self, request: Request) -> Dict[str, str]:
        """Extract request metadata for logging and validation."""
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
        }
    
    async def _validate_access_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Validate access token and return user data."""
        try:
            token_manager = await self._get_token_manager()
            payload = await token_manager.validate_access_token(access_token)
            
            # Convert payload to user dict format
            user_dict = {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "full_name": payload.get("full_name"),
                "roles": payload.get("roles", []),
                "tenant_id": payload.get("tenant_id", "default"),
                "preferences": {},  # Not stored in access token
                "two_factor_enabled": False,
                "is_verified": payload.get("is_verified", True),
            }
            
            return user_dict
            
        except TokenExpiredError:
            logger.debug("Access token expired")
            return None
        except InvalidTokenError:
            logger.debug("Invalid access token")
            # Don't raise exception here - let the enhanced validator handle it
            return None
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            # Don't raise exception here - let the enhanced validator handle it
            return None
    
    async def _attempt_token_refresh(
        self, 
        request: Request, 
        response: Response,
        request_meta: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Attempt to refresh expired access token using refresh token from cookie."""
        try:
            cookie_manager = self._get_cookie_manager()
            refresh_token = cookie_manager.get_refresh_token(request)
            
            if not refresh_token:
                logger.debug("No refresh token found in cookies")
                return None
            
            token_manager = await self._get_token_manager()
            
            # Validate refresh token
            try:
                payload = await token_manager.validate_refresh_token(refresh_token)
            except TokenExpiredError:
                logger.debug("Refresh token expired")
                # Clear expired refresh token cookie
                cookie_manager.clear_refresh_token_cookie(response)
                return None
            except InvalidTokenError:
                logger.debug("Invalid refresh token")
                # Clear invalid refresh token cookie
                cookie_manager.clear_refresh_token_cookie(response)
                return None
            
            # Get user data from payload
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("Invalid refresh token payload - missing user ID")
                cookie_manager.clear_refresh_token_cookie(response)
                return None
            
            # Reconstruct user data from token payload
            from ai_karen_engine.auth.models import UserData
            user_data = UserData(
                user_id=user_id,
                email=payload.get("email", ""),
                full_name=None,  # Not in refresh token
                tenant_id=payload.get("tenant_id", "default"),
                roles=[],  # Not in refresh token
                is_verified=True,  # Assume verified if they have a refresh token
                is_active=True,
                preferences={}
            )
            
            # Rotate tokens for enhanced security
            new_access_token, new_refresh_token, refresh_expires_at = await token_manager.rotate_tokens(
                refresh_token, user_data
            )
            
            # Update refresh token cookie with new token
            cookie_manager.set_refresh_token_cookie(
                response, 
                new_refresh_token,
                expires_at=refresh_expires_at
            )
            
            # Add new access token to response headers for frontend to use
            response.headers["X-New-Access-Token"] = new_access_token
            
            logger.info(
                "Token refresh successful",
                extra={
                    "user_id": user_id,
                    "ip_address": request_meta["ip_address"]
                },
            )
            
            # Return user data
            user_dict = {
                "user_id": user_id,
                "email": payload.get("email", ""),
                "full_name": None,
                "roles": [],  # Not in refresh token
                "tenant_id": payload.get("tenant_id", "default"),
                "preferences": {},
                "two_factor_enabled": False,
                "is_verified": True,
            }
            
            return user_dict
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return None
    
    async def _create_intelligent_error_response(
        self,
        error_message: str,
        error_type: str,
        status_code: int,
        request_meta: Dict[str, str],
        provider_name: Optional[str] = None
    ) -> JSONResponse:
        """Create an intelligent error response using the error response service."""
        error_service = self._get_error_response_service()
        
        if not error_service:
            # Fallback to simple error response
            return JSONResponse(
                {"detail": error_message},
                status_code=status_code
            )
        
        try:
            # Generate intelligent error response
            intelligent_response = error_service.analyze_error(
                error_message=error_message,
                error_type=error_type,
                status_code=status_code,
                provider_name=provider_name,
                additional_context={
                    "path": request_meta["path"],
                    "method": request_meta["method"],
                    "ip_address": request_meta["ip_address"],
                    "user_agent": request_meta["user_agent"],
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
                }
            }
            
            # Add provider health if available
            if intelligent_response.provider_health:
                response_data["error"]["provider_health"] = intelligent_response.provider_health
            
            # Add technical details if available
            if intelligent_response.technical_details:
                response_data["error"]["technical_details"] = intelligent_response.technical_details
            
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
            return JSONResponse(
                {"detail": error_message},
                status_code=status_code
            )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch method."""
        # Skip authentication for public paths
        if self._should_skip_auth(request):
            return await call_next(request)
        
        # Skip session persistence for auth routes that handle their own session management
        if self._should_skip_session_persistence(request):
            return await call_next(request)
        
        # Extract request metadata
        request_meta = await self._extract_request_metadata(request)
        
        # Create response object for potential cookie updates
        response = Response()
        
        # Use enhanced session validator for better error handling
        try:
            from ai_karen_engine.auth.enhanced_session_validator import get_session_validator
            
            session_validator = get_session_validator()
            user_data = await session_validator.validate_request_authentication(
                request, 
                allow_session_fallback=True
            )
            
        except HTTPException as e:
            # Convert HTTPException to intelligent error response
            error_type_mapping = {
                "Authentication required": "missing_auth_header",
                "Access token has expired": "token_expired",
                "Invalid access token": "invalid_token",
                "Your session has expired": "session_expired",
            }
            
            error_type = "authentication_error"
            for key, value in error_type_mapping.items():
                if key.lower() in e.detail.lower():
                    error_type = value
                    break
            
            return await self._create_intelligent_error_response(
                error_message=e.detail,
                error_type=error_type,
                status_code=e.status_code,
                request_meta=request_meta
            )
        
        # Set user data in request state for downstream handlers
        request.state.user = user_data["user_id"]
        request.state.user_data = user_data
        request.state.roles = user_data.get("roles", [])
        request.state.tenant_id = user_data.get("tenant_id", "default")
        
        # Process the request
        try:
            actual_response = await call_next(request)
            
            # If we have cookie updates from token refresh, merge them
            if response.headers:
                for key, value in response.headers.items():
                    actual_response.headers[key] = value
            
            return actual_response
            
        except HTTPException as e:
            # Handle HTTP exceptions with intelligent error responses
            return await self._create_intelligent_error_response(
                error_message=str(e.detail),
                error_type="http_exception",
                status_code=e.status_code,
                request_meta=request_meta
            )
        except Exception as e:
            logger.error(f"Unhandled exception in session persistence middleware: {e}")
            return await self._create_intelligent_error_response(
                error_message="Internal server error",
                error_type="internal_error",
                status_code=500,
                request_meta=request_meta
            )


# Convenience function for adding middleware to FastAPI app
def add_session_persistence_middleware(app, enable_intelligent_errors: bool = True):
    """Add session persistence middleware to FastAPI app."""
    app.add_middleware(
        SessionPersistenceMiddleware,
        enable_intelligent_errors=enable_intelligent_errors
    )