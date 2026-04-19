"""
Chat authentication middleware for AI-Karen chat system.
Integrates production middleware with canonical authentication architecture.
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

from .security import (
    generate_session_token,
    hash_password,
    verify_password,
    get_security_monitor,
    SecurityLevel,
    ThreatLevel,
)
from .dependencies import get_chat_orchestrator_dependency
from .services import ChatService

logger = logging.getLogger(__name__)

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "requests_per_minute": 100,
    "requests_per_hour": 1000,
    "message_per_minute": 30,
    "failed_auth_per_hour": 5,
    "burst_limit": 20,
}


class ChatAuthenticationMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for chat authentication and security."""

    def __init__(self, app, redis_url: Optional[str] = None):
        super().__init__(app)
        self.redis_client = None
        self.security_monitor = get_security_monitor()
        self.rate_limits = RATE_LIMIT_CONFIG
        self.bearer_scheme = HTTPBearer()

        # Initialize in-process cache for frequent requests (1 second window)
        self._rate_limit_cache: Dict[str, Dict[str, Any]] = {}

        # Initialize Redis for rate limiting
        if redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    max_connections=50,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                )
                logger.info("Redis client initialized for rate limiting")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis client: {e}")
                self.redis_client = None

    async def dispatch(self, request: Request, call_next):
        """Process request with authentication and rate limiting."""
        start_time = time.time()

        try:
            # Extract path for special handling
            path = request.url.path

            # Skip authentication for health checks and static files
            if self._should_skip_auth(path):
                response = await call_next(request)
                self._add_security_headers(response, start_time)
                return response

            # Check rate limiting
            if not await self._check_rate_limit(request):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"},
                )

            # Authenticate request
            user_info = await self._authenticate_request(request)
            if not user_info:
                # Log authentication failure
                await self.security_monitor.log_event(
                    event_type="authentication_failed",
                    threat_level=ThreatLevel.MEDIUM,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get("user-agent"),
                    details={"path": path},
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication credentials"},
                )

            # Add user info to request state
            request.state.user_id = user_info.get("user_id")
            request.state.user_roles = user_info.get("roles", [])
            request.state.security_context = user_info.get("security_context", {})

            # Process request
            response = await call_next(request)

            # Add security headers
            self._add_security_headers(response, start_time)

            # Log successful request (non-blocking)
            asyncio.create_task(
                self.security_monitor.log_event(
                    event_type="request_completed",
                    threat_level=ThreatLevel.LOW,
                    user_id=user_info.get("user_id"),
                    ip_address=self._get_client_ip(request),
                    details={
                        "path": path,
                        "method": request.method,
                        "status_code": response.status_code,
                        "duration": time.time() - start_time,
                    },
                )
            )

            return response

        except Exception as e:
            logger.error(f"Middleware error: {e}")

            # Log security event
            await self.security_monitor.log_event(
                event_type="middleware_error",
                threat_level=ThreatLevel.HIGH,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                details={"error": str(e), "path": path},
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )

    def _should_skip_auth(self, path: str) -> bool:
        """Check if authentication should be skipped for this path."""
        skip_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
            "/favicon.ico",
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    async def _check_rate_limit(self, request: Request) -> bool:
        """Rate limiting with in-process caching for hot paths."""
        if not self.redis_client:
            return True  # Skip rate limiting if Redis not available

        client_ip = self._get_client_ip(request)
        path = request.url.path

        # In-process cache for frequent requests (1 second window)
        cache_key = f"{client_ip}:{path}"
        now = time.time()

        if hasattr(self, "_rate_limit_cache"):
            cached = self._rate_limit_cache.get(cache_key)
            if cached and (now - cached["timestamp"]) < 1.0:
                # Use cached result
                return cached["allowed"]

        # Check Redis
        minute_key = f"rate_limit:{client_ip}:{path}:minute"
        hour_key = f"rate_limit:{client_ip}:{path}:hour"

        try:
            # Get current counts
            pipe = self.redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.incr(hour_key)
            pipe.expire(minute_key, 60)
            pipe.expire(hour_key, 3600)

            results = await pipe.execute()
            minute_count, hour_count = results[0], results[1]

            # Check limits
            allowed = (
                minute_count <= self.rate_limits["requests_per_minute"]
                and hour_count <= self.rate_limits["requests_per_hour"]
            )

            # Cache result
            if not hasattr(self, "_rate_limit_cache"):
                self._rate_limit_cache = {}

            self._rate_limit_cache[cache_key] = {
                "allowed": allowed,
                "timestamp": now,
            }

            # Clean old cache entries
            if len(self._rate_limit_cache) > 1000:
                cutoff = now - 1.0
                self._rate_limit_cache = {
                    k: v
                    for k, v in self._rate_limit_cache.items()
                    if v["timestamp"] > cutoff
                }

            return allowed

        except Exception as e:
            logger.warning(f"Rate limiting error: {e}")
            return True  # Allow request if rate limiting fails

    async def _authenticate_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """Authenticate the request and return user info."""
        try:
            # Get authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header:
                return None

            # Extract token
            try:
                scheme, token = auth_header.split(" ", 1)
                if scheme.lower() != "bearer":
                    return None
            except ValueError:
                return None

            # Validate token
            user_info = await self._validate_token(token)
            if not user_info:
                return None

            # Check user permissions for the specific path
            if not await self._check_user_permissions(request, user_info):
                return None

            return user_info

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    async def _validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return user info."""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                "your-secret-key",  # Should be from config
                algorithms=["HS256"],
            )

            # Check token expiration
            if payload.get("exp") < time.time():
                return None

            # Get user info from payload
            user_id = payload.get("user_id")
            if not user_id:
                return None

            return {
                "user_id": user_id,
                "roles": payload.get("roles", []),
                "security_context": payload.get("security_context", {}),
                "token_type": payload.get("token_type", "access"),
            }

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None

    async def _check_user_permissions(
        self, request: Request, user_info: Dict[str, Any]
    ) -> bool:
        """Check if user has permissions for the requested path."""
        path = request.url.path
        method = request.method
        user_roles = user_info.get("roles", [])

        # Define role-based permissions
        role_permissions = {
            "admin": ["*"],  # Admin can access everything
            "user": ["/chat/*", "/conversations/*"],
            "guest": ["/chat/public/*", "/conversations/public/*"],
        }

        user_role = user_roles[0] if user_roles else "guest"

        if user_role == "admin":
            return True

        # Check if path is allowed for this role
        allowed_paths = role_permissions.get(user_role, [])
        for allowed_path in allowed_paths:
            if allowed_path.endswith("*"):
                if path.startswith(allowed_path[:-1]):
                    return True
            elif path == allowed_path:
                return True

        return False

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers first
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        x_real_ip = request.headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip

        # Fall back to remote address
        return request.client.host if request.client else "unknown"

    def _add_security_headers(self, response: Response, start_time: float):
        """Add security headers to response."""
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # Add performance headers
        response.headers["X-Response-Time"] = f"{time.time() - start_time:.3f}s"
        response.headers["X-Content-Security-Policy"] = "default-src 'self'"

        # Remove potentially dangerous headers
        response.headers.pop("Server", None)


class ChatRateLimiter:
    """Rate limiter for chat operations."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        self.config = RATE_LIMIT_CONFIG

        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            except Exception as e:
                logger.warning(f"Failed to initialize Redis for rate limiting: {e}")

    async def check_message_rate(self, user_id: str) -> bool:
        """Check if user is within message rate limits."""
        if not self.redis_client:
            return True

        key = f"message_rate:{user_id}"
        current_time = time.time()

        try:
            # Remove old entries (older than 1 minute)
            await self.redis_client.zremrangebyscore(key, 0, current_time - 60)

            # Add current message
            await self.redis_client.zadd(key, {str(current_time): current_time})
            await self.redis_client.expire(key, 60)

            # Check if limit exceeded
            count = await self.redis_client.zcard(key)
            return count <= self.config["message_per_minute"]

        except Exception as e:
            logger.warning(f"Rate limiting error: {e}")
            return True

    async def check_authentication_rate(self, user_id: str) -> bool:
        """Check if user is within authentication rate limits."""
        if not self.redis_client:
            return True

        key = f"auth_rate:{user_id}"
        current_time = time.time()

        try:
            # Remove old entries (older than 1 hour)
            await self.redis_client.zremrangebyscore(key, 0, current_time - 3600)

            # Add failed authentication attempt
            await self.redis_client.zadd(key, {str(current_time): current_time})
            await self.redis_client.expire(key, 3600)

            # Check if limit exceeded
            count = await self.redis_client.zcard(key)
            return count <= self.config["failed_auth_per_hour"]

        except Exception as e:
            logger.warning(f"Authentication rate limiting error: {e}")
            return True


# Dependency functions for FastAPI
async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user from request state."""
    return getattr(request.state, "user_id", None)


async def require_chat_permission(permission: str):
    """Decorator to require specific chat permission."""

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user_info = getattr(request.state, "user_roles", [])
            if permission not in user_info and "admin" not in user_info:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


async def get_current_chat_user(request: Request) -> Dict[str, Any]:
    """Get current chat user with validation."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    return {
        "user_id": user_id,
        "roles": getattr(request.state, "user_roles", []),
        "security_context": getattr(request.state, "security_context", {}),
    }


# Factory functions
def create_chat_middleware(
    app, redis_url: Optional[str] = None
) -> ChatAuthenticationMiddleware:
    """Create chat authentication middleware instance."""
    return ChatAuthenticationMiddleware(app, redis_url)


def create_rate_limiter(redis_url: Optional[str] = None) -> ChatRateLimiter:
    """Create rate limiter instance."""
    return ChatRateLimiter(redis_url)
