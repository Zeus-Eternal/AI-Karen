"""
CSRF Protection for Authentication Operations

This module provides Cross-Site Request Forgery (CSRF) protection for
state-changing authentication operations like login, logout, password reset, etc.
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Set

from fastapi import HTTPException, Request, Response, status

from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.core.logging import get_logger


class CSRFError(Exception):
    """CSRF protection error"""
    pass


class CSRFTokenManager:
    """
    Manages CSRF tokens for authentication operations
    
    Uses double-submit cookie pattern with HMAC validation for security.
    """
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.logger = get_logger(__name__)
        
        # CSRF configuration
        self.secret_key = getattr(config.jwt, 'secret_key', 'default-csrf-secret')
        self.token_lifetime_minutes = 60  # CSRF tokens valid for 1 hour
        self.cookie_name = "csrf_token"
        self.header_name = "X-CSRF-Token"
        
        # Exempt paths that don't need CSRF protection (read-only operations)
        self.exempt_paths: Set[str] = {
            "/api/auth/me",
            "/api/auth/health",
            "/api/auth/refresh",  # Uses HttpOnly cookies, not form data
        }
        
        # Methods that require CSRF protection
        self.protected_methods: Set[str] = {"POST", "PUT", "PATCH", "DELETE"}
    
    def _generate_token_data(self, user_id: Optional[str] = None) -> Dict[str, str]:
        """Generate CSRF token data with timestamp and optional user binding"""
        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(16)
        
        # Create payload
        payload_parts = [timestamp, nonce]
        if user_id:
            payload_parts.append(user_id)
        
        payload = ":".join(payload_parts)
        
        # Create HMAC signature
        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        token = f"{payload}:{signature}"
        
        return {
            "token": token,
            "timestamp": timestamp,
            "nonce": nonce,
            "user_id": user_id or "",
        }
    
    def _validate_token_format(self, token: str) -> Optional[Dict[str, str]]:
        """Validate token format and extract components"""
        try:
            parts = token.split(":")
            if len(parts) < 3:
                return None
            
            signature = parts[-1]
            payload_parts = parts[:-1]
            
            # Reconstruct payload
            payload = ":".join(payload_parts)
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            # Extract components
            timestamp = payload_parts[0]
            nonce = payload_parts[1]
            user_id = payload_parts[2] if len(payload_parts) > 2 else ""
            
            return {
                "timestamp": timestamp,
                "nonce": nonce,
                "user_id": user_id,
                "token": token,
            }
        
        except Exception:
            return None
    
    def generate_csrf_token(self, user_id: Optional[str] = None) -> str:
        """
        Generate a new CSRF token
        
        Args:
            user_id: Optional user ID to bind token to specific user
            
        Returns:
            CSRF token string
        """
        token_data = self._generate_token_data(user_id)
        return token_data["token"]
    
    def validate_csrf_token(
        self, 
        token: str, 
        user_id: Optional[str] = None
    ) -> bool:
        """
        Validate a CSRF token
        
        Args:
            token: CSRF token to validate
            user_id: Optional user ID to check token binding
            
        Returns:
            True if token is valid, False otherwise
        """
        # Parse token
        token_data = self._validate_token_format(token)
        if not token_data:
            return False
        
        # Check timestamp (token expiry)
        try:
            token_timestamp = int(token_data["timestamp"])
            current_timestamp = int(time.time())
            max_age_seconds = self.token_lifetime_minutes * 60
            
            if current_timestamp - token_timestamp > max_age_seconds:
                return False
        except (ValueError, KeyError):
            return False
        
        # Check user binding if provided
        if user_id and token_data["user_id"] != user_id:
            return False
        
        return True
    
    def set_csrf_cookie(
        self, 
        response: Response, 
        token: str,
        secure: bool = True
    ) -> None:
        """
        Set CSRF token as HttpOnly cookie
        
        Args:
            response: FastAPI response object
            token: CSRF token to set
            secure: Whether to set Secure flag (HTTPS only)
        """
        expires = datetime.now(timezone.utc) + timedelta(minutes=self.token_lifetime_minutes)
        
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            expires=expires,
            httponly=True,  # Prevent XSS access
            secure=secure,  # HTTPS only in production
            samesite="strict",  # CSRF protection
            path="/api/auth",  # Scope to auth endpoints only
        )
    
    def get_csrf_token_from_cookie(self, request: Request) -> Optional[str]:
        """Extract CSRF token from cookie"""
        return request.cookies.get(self.cookie_name)
    
    def get_csrf_token_from_header(self, request: Request) -> Optional[str]:
        """Extract CSRF token from header"""
        return request.headers.get(self.header_name)
    
    def clear_csrf_cookie(self, response: Response) -> None:
        """Clear CSRF token cookie"""
        response.delete_cookie(
            key=self.cookie_name,
            path="/api/auth",
        )


class CSRFProtectionMiddleware:
    """
    CSRF Protection Middleware for authentication endpoints
    
    Implements double-submit cookie pattern:
    1. Server sets CSRF token in HttpOnly cookie
    2. Client must include same token in request header
    3. Server validates both tokens match
    """
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.token_manager = CSRFTokenManager(config)
        
        # Enable/disable CSRF protection
        self.enabled = getattr(config.security, 'enable_csrf_protection', True)
        
    def is_protected_request(self, request: Request) -> bool:
        """
        Check if request requires CSRF protection
        
        Args:
            request: FastAPI request object
            
        Returns:
            True if request needs CSRF protection
        """
        if not self.enabled:
            return False
        
        # Only protect state-changing methods
        if request.method not in self.token_manager.protected_methods:
            return False
        
        # Check if path is exempt
        path = request.url.path
        if path in self.token_manager.exempt_paths:
            return False
        
        # Protect all auth endpoints by default
        if path.startswith("/api/auth/"):
            return True
        
        return False
    
    async def validate_csrf_protection(
        self, 
        request: Request,
        user_id: Optional[str] = None
    ) -> None:
        """
        Validate CSRF protection for a request
        
        Args:
            request: FastAPI request object
            user_id: Optional user ID for token binding validation
            
        Raises:
            HTTPException: If CSRF validation fails
        """
        if not self.is_protected_request(request):
            return
        
        # Get tokens from cookie and header
        cookie_token = self.token_manager.get_csrf_token_from_cookie(request)
        header_token = self.token_manager.get_csrf_token_from_header(request)
        
        # Both tokens must be present
        if not cookie_token or not header_token:
            self.logger.warning(
                "CSRF validation failed: missing tokens",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "has_cookie_token": bool(cookie_token),
                    "has_header_token": bool(header_token),
                    "user_id": user_id,
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing",
                headers={"X-CSRF-Error": "missing_token"}
            )
        
        # Tokens must match (double-submit pattern)
        if cookie_token != header_token:
            self.logger.warning(
                "CSRF validation failed: token mismatch",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "user_id": user_id,
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token mismatch",
                headers={"X-CSRF-Error": "token_mismatch"}
            )
        
        # Validate token format and expiry
        if not self.token_manager.validate_csrf_token(cookie_token, user_id):
            self.logger.warning(
                "CSRF validation failed: invalid token",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "user_id": user_id,
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token invalid or expired",
                headers={"X-CSRF-Error": "invalid_token"}
            )
        
        self.logger.debug(
            "CSRF validation successful",
            extra={
                "path": request.url.path,
                "method": request.method,
                "user_id": user_id,
            }
        )
    
    def generate_csrf_response(
        self, 
        response: Response,
        user_id: Optional[str] = None,
        secure: bool = True
    ) -> str:
        """
        Generate CSRF token and set cookie
        
        Args:
            response: FastAPI response object
            user_id: Optional user ID to bind token to
            secure: Whether to set Secure flag on cookie
            
        Returns:
            Generated CSRF token (for client to use in headers)
        """
        if not self.enabled:
            return ""
        
        token = self.token_manager.generate_csrf_token(user_id)
        self.token_manager.set_csrf_cookie(response, token, secure)
        
        return token
    
    def clear_csrf_protection(self, response: Response) -> None:
        """Clear CSRF protection cookies"""
        if self.enabled:
            self.token_manager.clear_csrf_cookie(response)


# Dependency for FastAPI routes
async def validate_csrf_token(request: Request) -> None:
    """
    FastAPI dependency to validate CSRF tokens
    
    Usage:
        @router.post("/login", dependencies=[Depends(validate_csrf_token)])
        async def login(...):
            ...
    """
    from ai_karen_engine.auth.config import AuthConfig
    
    config = AuthConfig.from_env()
    csrf_middleware = CSRFProtectionMiddleware(config)
    
    await csrf_middleware.validate_csrf_protection(request)


# Utility functions for manual CSRF handling

def get_csrf_token_manager() -> CSRFTokenManager:
    """Get CSRF token manager instance"""
    from ai_karen_engine.auth.config import AuthConfig
    
    config = AuthConfig.from_env()
    return CSRFTokenManager(config)


def get_csrf_protection_middleware() -> CSRFProtectionMiddleware:
    """Get CSRF protection middleware instance"""
    from ai_karen_engine.auth.config import AuthConfig
    
    config = AuthConfig.from_env()
    return CSRFProtectionMiddleware(config)