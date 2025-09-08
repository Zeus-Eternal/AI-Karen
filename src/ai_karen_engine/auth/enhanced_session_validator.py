"""
Enhanced Session Validation Service

This module provides improved session validation logic that prevents false
"invalid authorization header" errors and implements proper session state
management to avoid duplicate validation attempts.
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field

from fastapi import Request, HTTPException, status

from ai_karen_engine.auth.tokens import EnhancedTokenManager
from ai_karen_engine.auth.cookie_manager import SessionCookieManager
from ai_karen_engine.auth.service import AuthService
from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    SessionExpiredError,
    SessionNotFoundError,
)
from ai_karen_engine.core.cache import get_request_deduplicator
from ai_karen_engine.services.audit_logging import get_audit_logger

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of session validation attempt."""
    success: bool
    user_data: Optional[Dict[str, Any]] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    should_retry_with_refresh: bool = False
    validation_source: Optional[str] = None  # 'access_token', 'session', 'refresh'


@dataclass
class ValidationState:
    """Tracks validation state to prevent duplicate attempts."""
    request_id: str
    validation_attempts: Set[str] = field(default_factory=set)
    last_validation_time: Optional[datetime] = None
    cached_result: Optional[ValidationResult] = None
    cache_expires_at: Optional[datetime] = None


class EnhancedSessionValidator:
    """
    Enhanced session validator that prevents false errors and manages validation state.
    
    Key improvements:
    1. Prevents false "invalid authorization header" errors for valid sessions
    2. Implements proper token validation without generating unnecessary warnings
    3. Adds session state management to prevent duplicate validation attempts
    4. Creates clear error messages for different authentication failure scenarios
    """
    
    def __init__(self):
        self._token_manager: Optional[EnhancedTokenManager] = None
        self._cookie_manager: Optional[SessionCookieManager] = None
        self._auth_service: Optional[AuthService] = None
        self._audit_logger = get_audit_logger()
        self._deduplicator = get_request_deduplicator()
        
        # State management for validation attempts
        self._validation_states: Dict[str, ValidationState] = {}
        self._state_cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()
        
        # Cache for validation results (short-lived to prevent stale data)
        self._validation_cache_ttl = 30  # 30 seconds
        
    async def _get_token_manager(self) -> EnhancedTokenManager:
        """Get token manager instance, initializing if necessary."""
        if self._token_manager is None:
            auth_config = AuthConfig.from_env()
            self._token_manager = EnhancedTokenManager(auth_config.jwt)
        return self._token_manager
    
    def _get_cookie_manager(self) -> SessionCookieManager:
        """Get cookie manager instance, initializing if necessary."""
        if self._cookie_manager is None:
            from ai_karen_engine.auth.cookie_manager import get_cookie_manager
            self._cookie_manager = get_cookie_manager()
        return self._cookie_manager
    
    async def _get_auth_service(self) -> AuthService:
        """Get auth service instance, initializing if necessary."""
        if self._auth_service is None:
            from ai_karen_engine.auth.service import get_auth_service
            self._auth_service = await get_auth_service()
        return self._auth_service
    
    def _generate_request_id(self, request: Request) -> str:
        """Generate a unique request ID for state tracking."""
        # Use a combination of IP, user agent, and auth header for uniqueness
        # Don't use timestamp to allow caching of same request
        ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")[:50]  # Truncate for memory
        auth_header = request.headers.get("Authorization", "")[:20]  # First 20 chars
        
        import hashlib
        request_data = f"{ip}:{user_agent}:{auth_header}"
        return hashlib.md5(request_data.encode()).hexdigest()[:16]
    
    def _cleanup_old_states(self) -> None:
        """Clean up old validation states to prevent memory leaks."""
        current_time = time.time()
        if current_time - self._last_cleanup < self._state_cleanup_interval:
            return
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        expired_keys = []
        
        for request_id, state in self._validation_states.items():
            if (state.last_validation_time and 
                state.last_validation_time < cutoff_time):
                expired_keys.append(request_id)
        
        for key in expired_keys:
            del self._validation_states[key]
        
        self._last_cleanup = current_time
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired validation states")
    
    def _get_validation_state(self, request: Request) -> ValidationState:
        """Get or create validation state for a request."""
        self._cleanup_old_states()
        
        request_id = self._generate_request_id(request)
        
        if request_id not in self._validation_states:
            self._validation_states[request_id] = ValidationState(request_id=request_id)
        
        return self._validation_states[request_id]
    
    def _is_cached_result_valid(self, state: ValidationState) -> bool:
        """Check if cached validation result is still valid."""
        if not state.cached_result or not state.cache_expires_at:
            return False
        
        return datetime.now(timezone.utc) < state.cache_expires_at
    
    def _cache_validation_result(
        self, 
        state: ValidationState, 
        result: ValidationResult
    ) -> None:
        """Cache validation result for short-term reuse."""
        state.cached_result = result
        state.cache_expires_at = (
            datetime.now(timezone.utc) + 
            timedelta(seconds=self._validation_cache_ttl)
        )
        state.last_validation_time = datetime.now(timezone.utc)
    
    def _extract_request_metadata(self, request: Request) -> Dict[str, str]:
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
    
    async def _validate_access_token_safely(
        self, 
        access_token: str,
        request_meta: Dict[str, str]
    ) -> ValidationResult:
        """Validate access token without generating unnecessary warnings."""
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
            
            return ValidationResult(
                success=True,
                user_data=user_dict,
                validation_source="access_token"
            )
            
        except TokenExpiredError:
            # Token is expired but structurally valid - suggest refresh
            return ValidationResult(
                success=False,
                error_type="token_expired",
                error_message="Access token has expired",
                should_retry_with_refresh=True
            )
        except InvalidTokenError as e:
            # Token is invalid - don't suggest refresh
            return ValidationResult(
                success=False,
                error_type="invalid_token",
                error_message=f"Invalid access token: {str(e)}"
            )
        except Exception as e:
            logger.error(
                "Unexpected error during token validation",
                extra={
                    "error": str(e),
                    "ip_address": request_meta.get("ip_address"),
                    "path": request_meta.get("path")
                }
            )
            return ValidationResult(
                success=False,
                error_type="validation_error",
                error_message="Token validation failed due to internal error"
            )
    
    async def _validate_session_token_safely(
        self,
        session_token: str,
        request_meta: Dict[str, str]
    ) -> ValidationResult:
        """Validate session token without generating unnecessary warnings."""
        try:
            auth_service = await self._get_auth_service()
            user_data = await auth_service.validate_session(
                session_token=session_token,
                ip_address=request_meta["ip_address"],
                user_agent=request_meta["user_agent"],
            )
            
            if not user_data:
                return ValidationResult(
                    success=False,
                    error_type="session_not_found",
                    error_message="Session not found or expired"
                )
            
            # Convert UserData to dict format
            user_dict = {
                "user_id": user_data.user_id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "roles": user_data.roles,
                "tenant_id": user_data.tenant_id,
                "preferences": user_data.preferences,
                "two_factor_enabled": False,
                "is_verified": user_data.is_verified,
            }
            
            return ValidationResult(
                success=True,
                user_data=user_dict,
                validation_source="session"
            )
            
        except (SessionExpiredError, SessionNotFoundError) as e:
            return ValidationResult(
                success=False,
                error_type="session_expired",
                error_message=str(e)
            )
        except Exception as e:
            logger.error(
                "Unexpected error during session validation",
                extra={
                    "error": str(e),
                    "ip_address": request_meta.get("ip_address"),
                    "path": request_meta.get("path")
                }
            )
            return ValidationResult(
                success=False,
                error_type="validation_error",
                error_message="Session validation failed due to internal error"
            )
    
    async def _attempt_token_refresh(
        self,
        request: Request,
        request_meta: Dict[str, str]
    ) -> ValidationResult:
        """Attempt to refresh access token using refresh token from cookie."""
        try:
            cookie_manager = self._get_cookie_manager()
            refresh_token = cookie_manager.get_refresh_token(request)
            
            if not refresh_token:
                return ValidationResult(
                    success=False,
                    error_type="no_refresh_token",
                    error_message="No refresh token available for token refresh"
                )
            
            token_manager = await self._get_token_manager()
            
            # Validate refresh token
            try:
                payload = await token_manager.validate_refresh_token(refresh_token)
            except TokenExpiredError:
                return ValidationResult(
                    success=False,
                    error_type="refresh_token_expired",
                    error_message="Refresh token has expired"
                )
            except InvalidTokenError:
                return ValidationResult(
                    success=False,
                    error_type="invalid_refresh_token",
                    error_message="Invalid refresh token"
                )
            
            # Get user data from payload
            user_id = payload.get("sub")
            if not user_id:
                return ValidationResult(
                    success=False,
                    error_type="invalid_refresh_payload",
                    error_message="Invalid refresh token payload"
                )
            
            # Return user data (actual token refresh would be handled by middleware)
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
            
            return ValidationResult(
                success=True,
                user_data=user_dict,
                validation_source="refresh"
            )
            
        except Exception as e:
            logger.error(
                "Unexpected error during token refresh",
                extra={
                    "error": str(e),
                    "ip_address": request_meta.get("ip_address"),
                    "path": request_meta.get("path")
                }
            )
            return ValidationResult(
                success=False,
                error_type="refresh_error",
                error_message="Token refresh failed due to internal error"
            )
    
    def _create_clear_error_message(self, result: ValidationResult) -> Tuple[str, int]:
        """Create clear, actionable error messages for different failure scenarios."""
        error_messages = {
            "missing_auth_header": (
                "Authentication required. Please provide a valid access token in the Authorization header.",
                401
            ),
            "malformed_auth_header": (
                "Invalid authorization header format. Expected 'Bearer <token>'.",
                401
            ),
            "token_expired": (
                "Access token has expired. Please refresh your token or log in again.",
                401
            ),
            "invalid_token": (
                "Invalid access token. Please log in again to obtain a new token.",
                401
            ),
            "session_expired": (
                "Your session has expired. Please log in again.",
                401
            ),
            "session_not_found": (
                "Session not found. Please log in to create a new session.",
                401
            ),
            "no_refresh_token": (
                "Authentication session expired and no refresh token available. Please log in again.",
                401
            ),
            "refresh_token_expired": (
                "Refresh token has expired. Please log in again.",
                401
            ),
            "invalid_refresh_token": (
                "Invalid refresh token. Please log in again.",
                401
            ),
            "validation_error": (
                "Authentication validation failed. Please try again or contact support.",
                500
            ),
            "refresh_error": (
                "Token refresh failed. Please log in again.",
                401
            ),
        }
        
        error_type = result.error_type or "validation_error"
        message, status_code = error_messages.get(
            error_type, 
            (result.error_message or "Authentication failed", 401)
        )
        
        return message, status_code
    
    async def validate_request_authentication(
        self, 
        request: Request,
        allow_session_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Validate request authentication with enhanced error handling and state management.
        
        Args:
            request: FastAPI request object
            allow_session_fallback: Whether to fall back to session validation
            
        Returns:
            User data dictionary if authentication succeeds
            
        Raises:
            HTTPException: If authentication fails with clear error message
        """
        # Get validation state to prevent duplicate attempts
        state = self._get_validation_state(request)
        
        # Check if we have a cached result
        if self._is_cached_result_valid(state):
            cached_result = state.cached_result
            if cached_result.success:
                return cached_result.user_data
            else:
                message, status_code = self._create_clear_error_message(cached_result)
                raise HTTPException(
                    status_code=status_code,
                    detail=message
                )
        
        # Extract request metadata
        request_meta = self._extract_request_metadata(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        
        # Handle missing or malformed Authorization header
        if not auth_header:
            if allow_session_fallback:
                # Try session validation as fallback
                cookie_manager = self._get_cookie_manager()
                session_token = cookie_manager.get_session_token(request)
                
                if session_token:
                    result = await self._validate_session_token_safely(session_token, request_meta)
                    self._cache_validation_result(state, result)
                    
                    if result.success:
                        return result.user_data
            
            # No valid authentication found
            result = ValidationResult(
                success=False,
                error_type="missing_auth_header",
                error_message="Missing authorization header"
            )
            self._cache_validation_result(state, result)
            message, status_code = self._create_clear_error_message(result)
            raise HTTPException(
                status_code=status_code,
                detail=message
            )
        
        if not auth_header.startswith("Bearer "):
            result = ValidationResult(
                success=False,
                error_type="malformed_auth_header",
                error_message="Malformed authorization header"
            )
            self._cache_validation_result(state, result)
            message, status_code = self._create_clear_error_message(result)
            raise HTTPException(
                status_code=status_code,
                detail=message
            )
        
        # Extract access token
        access_token = auth_header.split(" ")[1]
        
        # Validate access token
        result = await self._validate_access_token_safely(access_token, request_meta)
        
        # If token is expired, try refresh if available
        if not result.success and result.should_retry_with_refresh:
            refresh_result = await self._attempt_token_refresh(request, request_meta)
            if refresh_result.success:
                result = refresh_result
        
        # Cache the result
        self._cache_validation_result(state, result)
        
        # Return user data or raise exception
        if result.success:
            # Log successful session validation (separate from login events)
            try:
                # Guard optional fields to avoid attribute errors in logging
                validation_method = getattr(result, "validation_method", None) or getattr(result, "validation_source", None) or "token"
                self._audit_logger.log_session_validation(
                    user_id=result.user_data["user_id"],
                    ip_address=request_meta["ip_address"],
                    user_agent=request_meta["user_agent"],
                    tenant_id=result.user_data.get("tenant_id", "default"),
                    session_id=result.user_data.get("session_id"),
                    validation_method=validation_method,
                    logged_by="session_validator"
                )
            except Exception as e:
                logger.warning(f"Failed to log session validation: {e}")
            return result.user_data
        else:
            # Don't log failed session validations as login failures
            # These are just invalid/expired tokens, not actual login attempts
            message, status_code = self._create_clear_error_message(result)
            raise HTTPException(
                status_code=status_code,
                detail=message
            )
    
    async def validate_optional_authentication(
        self, 
        request: Request
    ) -> Optional[Dict[str, Any]]:
        """
        Validate optional authentication (returns None if no auth provided).
        
        Args:
            request: FastAPI request object
            
        Returns:
            User data dictionary if authentication succeeds, None if no auth provided
        """
        try:
            return await self.validate_request_authentication(request)
        except HTTPException as e:
            # If it's a missing auth header, return None for optional auth
            if e.status_code == 401 and ("missing" in e.detail.lower() or "authentication required" in e.detail.lower()):
                return None
            # Re-raise other authentication errors
            raise
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics for monitoring."""
        active_states = len(self._validation_states)
        cached_results = sum(
            1 for state in self._validation_states.values() 
            if self._is_cached_result_valid(state)
        )
        
        return {
            "active_validation_states": active_states,
            "cached_validation_results": cached_results,
            "cache_ttl_seconds": self._validation_cache_ttl,
            "cleanup_interval_seconds": self._state_cleanup_interval,
        }


# Global instance for reuse
_session_validator: Optional[EnhancedSessionValidator] = None


def get_session_validator() -> EnhancedSessionValidator:
    """Get the global session validator instance."""
    global _session_validator
    if _session_validator is None:
        _session_validator = EnhancedSessionValidator()
    return _session_validator
