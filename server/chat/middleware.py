"""
Chat authentication middleware for the AI-Karen production chat system.
Provides JWT token validation, rate limiting, and security headers for chat endpoints.
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..security import ExtensionAuthManager, get_extension_auth_manager
from ..config import settings

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
rate_limit_store = {}
security_events = []

class ChatAuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for chat authentication and security."""
    
    def __init__(self, app, redis_url: Optional[str] = None):
        super().__init__(app)
        self.redis_client = None
        self.auth_manager = get_extension_auth_manager()
        self.rate_limits = {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "message_per_minute": 30,
            "failed_auth_per_hour": 10
        }
        
        # Initialize Redis if available
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                logger.info("Redis client initialized for rate limiting")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis client: {e}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through authentication and security checks."""
        
        # Skip authentication for health checks and options
        if self._is_public_endpoint(request):
            return await call_next(request)
        
        # Add security headers
        response = await self._process_request(request, call_next)
        self._add_security_headers(response)
        
        return response
    
    def _is_public_endpoint(self, request: Request) -> bool:
        """Check if endpoint is public (no auth required)."""
        public_paths = [
            "/api/chat/health",
            "/api/docs",
            "/api/openapi.json",
            "/api/redoc"
        ]
        
        return any(request.url.path.startswith(path) for path in public_paths)
    
    def _is_development_mode(self) -> bool:
        """Check if system is in development mode."""
        import os
        return os.getenv("ENVIRONMENT", "development").lower() in ["development", "dev"]
    
    def _create_dev_user_context(self) -> Dict[str, Any]:
        """Create development user context for testing."""
        return {
            'user_id': 'dev-user',
            'tenant_id': 'dev-tenant',
            'roles': ['admin', 'user'],
            'permissions': ['chat:read', 'chat:write', 'chat:admin', 'conversation:create', 'message:send'],
            'token_type': 'development'
        }
    
    async def _process_request(self, request: Request, call_next: Callable) -> Response:
        """Process request with authentication and rate limiting."""
        
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        try:
            # Rate limiting check
            await self._check_rate_limit(request, client_ip)
            
            # Authentication check
            user_context = await self._authenticate_request(request)
            
            # Add user context to request state
            request.state.user_context = user_context
            request.state.client_ip = client_ip
            
            # Log security event
            await self._log_security_event(
                "request_authenticated",
                {
                    "user_id": user_context.get("user_id"),
                    "ip": client_ip,
                    "user_agent": user_agent,
                    "endpoint": request.url.path,
                    "method": request.method
                }
            )
            
            return await call_next(request)
            
        except HTTPException as e:
            # Log failed authentication
            await self._log_security_event(
                "authentication_failed",
                {
                    "ip": client_ip,
                    "user_agent": user_agent,
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status_code": e.status_code,
                    "detail": e.detail
                }
            )
            
            # Check for brute force
            await self._check_brute_force(client_ip)
            
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail, "timestamp": datetime.utcnow().isoformat()}
            )
        except Exception as e:
            logger.error(f"Unexpected error in middleware: {e}")
            
            await self._log_security_event(
                "middleware_error",
                {
                    "ip": client_ip,
                    "endpoint": request.url.path,
                    "error": str(e)
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error", "timestamp": datetime.utcnow().isoformat()}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _check_rate_limit(self, request: Request, client_ip: str) -> None:
        """Check rate limiting for client."""
        current_time = time.time()
        endpoint = request.url.path
        
        # Different rate limits for different endpoints
        if endpoint.startswith("/api/chat/conversations") and request.method == "POST":
            # Message sending rate limit
            limit_key = f"message_rate:{client_ip}"
            limit = self.rate_limits["message_per_minute"]
            window = 60  # 1 minute
        else:
            # General API rate limit
            limit_key = f"api_rate:{client_ip}"
            limit = self.rate_limits["requests_per_minute"]
            window = 60  # 1 minute
        
        # Check rate limit using Redis or in-memory store
        if self.redis_client:
            await self._check_redis_rate_limit(limit_key, limit, window)
        else:
            self._check_memory_rate_limit(limit_key, limit, window, current_time)
    
    async def _check_redis_rate_limit(self, key: str, limit: int, window: int) -> None:
        """Check rate limit using Redis."""
        try:
            if self.redis_client is None:
                raise Exception("Redis client not initialized")
                
            current = await self.redis_client.incr(key)
            
            if current == 1:
                # Set expiration on first request
                await self.redis_client.expire(key, window)
            
            if current > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {limit} requests per {window} seconds."
                )
        except Exception as e:
            logger.warning(f"Redis rate limit check failed: {e}")
            # Fallback to memory-based rate limiting
    
    def _check_memory_rate_limit(self, key: str, limit: int, window: int, current_time: float) -> None:
        """Check rate limit using in-memory store."""
        if key not in rate_limit_store:
            rate_limit_store[key] = []
        
        # Remove old requests outside the window
        rate_limit_store[key] = [
            req_time for req_time in rate_limit_store[key]
            if current_time - req_time < window
        ]
        
        # Check if limit exceeded
        if len(rate_limit_store[key]) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {limit} requests per {window} seconds."
            )
        
        # Add current request
        rate_limit_store[key].append(current_time)
    
    async def _authenticate_request(self, request: Request) -> Dict[str, Any]:
        """Authenticate request using JWT token or API key."""
        
        # DEVELOPMENT MODE: Check if in development and provide dev user context
        if self._is_development_mode():
            logger.debug("Development mode detected: Using development user context")
            return self._create_dev_user_context()
        
        # Try JWT token authentication first
        authorization = request.headers.get("authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            return await self._validate_jwt_token(token)
        
        # Try API key authentication
        api_key = request.headers.get("x-api-key")
        if api_key:
            return await self._authenticate_api_key(api_key)
        
        # Try cookie-based authentication
        token = request.cookies.get("access_token")
        if token:
            return await self._validate_jwt_token(token)
        
        # No authentication provided
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    async def _validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return user context."""
        try:
            # Use existing auth manager to validate token
            from fastapi import HTTPException
            from fastapi.security import HTTPAuthorizationCredentials
            from fastapi import Request as FastAPIRequest
            
            # Create mock request for the auth manager
            mock_request = FastAPIRequest(
                scope={
                    "type": "http",
                    "method": "GET",
                    "path": "/api/chat",
                    "headers": {}
                }
            )
            
            # Create mock credentials for the auth manager
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
            
            # Authenticate using existing extension auth manager
            user_context = await self.auth_manager.authenticate_extension_request(
                request=mock_request,
                credentials=credentials
            )
            
            # Add chat-specific permissions
            await self._add_chat_permissions(user_context)
            
            return user_context
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    async def _authenticate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Authenticate using API key."""
        try:
            # Use existing auth manager for API key authentication
            user_context = await self.auth_manager._authenticate_with_api_key(api_key)
            
            # Add chat-specific permissions
            await self._add_chat_permissions(user_context)
            
            return user_context
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
    
    async def _add_chat_permissions(self, user_context: Dict[str, Any]) -> None:
        """Add chat-specific permissions to user context."""
        existing_permissions = user_context.get("permissions", [])
        
        # Add base chat permissions
        chat_permissions = [
            "chat:read",
            "chat:write",
            "chat:conversations:read",
            "chat:conversations:write",
            "chat:messages:read",
            "chat:messages:write"
        ]
        
        # Add admin permissions if user is admin
        if "admin" in user_context.get("roles", []):
            chat_permissions.extend([
                "chat:admin",
                "chat:providers:read",
                "chat:providers:write",
                "chat:users:read",
                "chat:audit:read"
            ])
        
        # Merge permissions without duplicates
        all_permissions = list(set(existing_permissions + chat_permissions))
        user_context["permissions"] = all_permissions
    
    async def _check_brute_force(self, client_ip: str) -> None:
        """Check for brute force attacks and block if necessary."""
        current_time = time.time()
        window = 3600  # 1 hour
        max_failed = self.rate_limits["failed_auth_per_hour"]
        
        # Track failed attempts
        key = f"failed_auth:{client_ip}"
        
        if self.redis_client:
            failed_count = await self.redis_client.incr(key)
            
            if failed_count == 1:
                await self.redis_client.expire(key, window)
            
            if failed_count > max_failed:
                await self._log_security_event(
                    "brute_force_detected",
                    {
                        "ip": client_ip,
                        "failed_count": failed_count,
                        "action": "temporary_block"
                    }
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed authentication attempts. Please try again later."
                )
        else:
            # In-memory fallback
            if key not in rate_limit_store:
                rate_limit_store[key] = []
            
            # Clean old attempts
            rate_limit_store[key] = [
                req_time for req_time in rate_limit_store[key]
                if current_time - req_time < window
            ]
            
            if len(rate_limit_store[key]) >= max_failed:
                await self._log_security_event(
                    "brute_force_detected",
                    {
                        "ip": client_ip,
                        "failed_count": len(rate_limit_store[key]),
                        "action": "temporary_block"
                    }
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed authentication attempts. Please try again later."
                )
            
            rate_limit_store[key].append(current_time)
    
    async def _log_security_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log security events for monitoring."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        # Add to in-memory store (in production, use proper logging)
        security_events.append(event)
        
        # Keep only last 1000 events in memory
        if len(security_events) > 1000:
            security_events.pop(0)
        
        # Log to standard logger
        logger.info(f"Security event: {event_type} - {data}")
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' wss:; "
            "frame-ancestors 'none';"
        )


# Dependency functions for route protection
async def get_current_chat_user(request: Request) -> Dict[str, Any]:
    """Get current authenticated user from request state."""
    if not hasattr(request.state, "user_context"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return request.state.user_context


async def require_chat_permission(permission: str):
    """Dependency to require specific chat permission."""
    async def permission_checker(
        request: Request,
        user_context: Dict[str, Any] = Depends(get_current_chat_user)
    ) -> Dict[str, Any]:
        user_permissions = user_context.get("permissions", [])
        
        if permission not in user_permissions and "chat:admin" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        
        return user_context
    
    return permission_checker


async def require_chat_admin(
    user_context: Dict[str, Any] = Depends(get_current_chat_user)
) -> Dict[str, Any]:
    """Require chat admin permissions."""
    user_permissions = user_context.get("permissions", [])
    
    if "chat:admin" not in user_permissions and "admin" not in user_context.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chat admin permissions required"
        )
    
    return user_context


# Rate limiting utilities
async def check_message_rate_limit(user_id: str, redis_client=None) -> bool:
    """Check if user has exceeded message rate limit."""
    limit = 30  # messages per minute
    
    if redis_client:
        key = f"message_rate:{user_id}"
        current = await redis_client.incr(key)
        
        if current == 1:
            await redis_client.expire(key, 60)
        
        return current <= limit
    else:
        # In-memory fallback
        current_time = time.time()
        key = f"message_rate:{user_id}"
        
        if key not in rate_limit_store:
            rate_limit_store[key] = []
        
        # Clean old messages
        rate_limit_store[key] = [
            msg_time for msg_time in rate_limit_store[key]
            if current_time - msg_time < 60
        ]
        
        if len(rate_limit_store[key]) >= limit:
            return False
        
        rate_limit_store[key].append(current_time)
        return True


# Security event retrieval
async def get_security_events(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent security events."""
    return security_events[-limit:]


# CORS configuration
def get_chat_cors_config() -> Dict[str, Any]:
    """Get CORS configuration for chat endpoints."""
    return {
        "allow_origins": settings.get("chat.cors_origins", ["http://localhost:3000"]),
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Authorization",
            "Content-Type",
            "X-API-Key",
            "X-Requested-With"
        ]
    }
