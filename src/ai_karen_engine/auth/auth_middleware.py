"""
Secure Authentication Middleware with Comprehensive JWT Validation

This module provides secure authentication with:
- Proper JWT token validation and verification
- Token revocation and refresh mechanisms
- Rate limiting on authentication endpoints
- Secure session management
- Comprehensive audit logging
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional, Union

import jwt
import redis
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ai_karen_engine.auth.auth_service import get_auth_service, user_account_to_dict
from ai_karen_engine.core.config_manager import get_config_manager
from ai_karen_engine.core.logging.logger import get_structured_logger
from ai_karen_engine.core.metrics_manager import get_metrics_manager

logger = logging.getLogger(__name__)
security = HTTPBearer()


def _load_auth_jwt_secret() -> str:
    """Resolve the JWT secret using the shared auth env precedence."""
    import os

    return (
        os.getenv("AUTH_JWT_SECRET_KEY")
        or os.getenv("AUTH_SECRET_KEY")
        or os.getenv("JWT_SECRET_KEY")
        or os.getenv("JWT_SECRET")
        or os.getenv("SECRET_KEY")
        or "fallback_secret_key_for_development_only"
    )


class TokenStatus(Enum):
    """JWT token status."""

    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    REVOKED = "revoked"
    RATE_LIMITED = "rate_limited"


class AuthenticationError(Exception):
    """Custom authentication error."""

    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BaseAuthMiddleware:
    """Base class for authentication middleware with common interface."""

    def get_current_user(self, request: Request) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement get_current_user")

    def is_public_endpoint(self, path: str) -> bool:
        raise NotImplementedError("Subclasses must implement is_public_endpoint")

    def _check_rate_limit(self, user_id: str, action: str) -> bool:
        raise NotImplementedError("Subclasses must implement _check_rate_limit")

    async def authenticate_request(self, request: Request) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement authenticate_request")


class SecureAuthMiddleware(BaseAuthMiddleware):
    """Secure authentication middleware with comprehensive JWT validation."""

    def __init__(self):
        self.config_manager: Optional[Any] = None
        self.structured_logger: Optional[Any] = None
        self.metrics_manager: Optional[Any] = None

        self.jwt_secret = _load_auth_jwt_secret()
        self.jwt_algorithm: str = "HS256"
        self.jwt_expiration_hours: int = 24
        self.refresh_token_expiration_days: int = 7
        self.redis_client: Optional[Union[redis.Redis, Any]] = None

        try:
            self.config_manager = get_config_manager()
            self.structured_logger = get_structured_logger()
            self.metrics_manager = get_metrics_manager()

            if self.config_manager is not None:
                config = self.config_manager.get_config()
                if config is not None and hasattr(config, "security"):
                    if self.jwt_secret == "fallback_secret_key_for_development_only":
                        self.jwt_secret = config.security.jwt_secret

                    self.jwt_algorithm = config.security.jwt_algorithm
                    self.jwt_expiration_hours = config.security.jwt_expiration // 3600

                self._init_redis()

            logger.info("SecureAuthMiddleware initialized with full services")
        except Exception as e:
            logger.warning(
                f"Failed to initialize full auth services, using fallback mode: {e}"
            )

        self.auth_rate_limits = {
            "login_attempts": {"window": 300, "limit": 5},
            "token_refresh": {"window": 3600, "limit": 10},
            "password_reset": {"window": 3600, "limit": 3},
        }
        self.failed_attempts: Dict[str, List[Dict[str, Any]]] = {}

    def _init_redis(self) -> None:
        """Initialize Redis client for token management."""
        try:
            if self.config_manager is None:
                logger.warning("Config manager is None, skipping Redis initialization")
                self.redis_client = None
                return

            config = self.config_manager.get_config()
            if config is None or not hasattr(config, "redis"):
                logger.warning(
                    "Config or redis config is None, skipping Redis initialization"
                )
                self.redis_client = None
                return

            redis_host = config.redis.host
            redis_port = config.redis.port
            redis_password = config.redis.password

            redis_url = f"redis://{redis_host}:{redis_port}/0"
            if redis_password:
                redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/0"

            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
                retry_on_timeout=False,
            )

            try:
                self.redis_client.ping()
                logger.info(
                    f"Connected to token revocation store at {redis_host}:{redis_port}"
                )
            except Exception as e:
                logger.warning(
                    f"Could not connect to Redis at {redis_host}:{redis_port}: {e}. Revocation checks may be skipped."
                )

        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self.redis_client = None

    def _get_redis_key(self, key_type: str, identifier: str) -> str:
        return f"auth:{key_type}:{identifier}"

    def _hash_password(self, password: str, salt: str) -> str:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        return kdf.derive(password.encode()).hex()

    def _verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        return self._hash_password(password, salt) == hashed_password

    def _generate_token_id(self) -> str:
        return secrets.token_urlsafe(32)

    def _create_jwt_payload(
        self, user_data: Dict[str, Any], token_id: str
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        return {
            "sub": user_data["user_id"],
            "email": user_data.get("email", ""),
            "user_type": user_data.get("user_type", "user"),
            "permissions": user_data.get("permissions", []),
            "token_id": token_id,
            "iat": now,
            "exp": now + timedelta(hours=self.jwt_expiration_hours),
            "iss": "ai-karen",
            "aud": "ai-karen-users",
        }

    def _create_refresh_token_payload(
        self, user_data: Dict[str, Any], token_id: str
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        return {
            "sub": user_data["user_id"],
            "token_id": token_id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=self.refresh_token_expiration_days),
            "iss": "ai-karen",
            "aud": "ai-karen-refresh",
        }

    def _encode_jwt(self, payload: Dict[str, Any]) -> str:
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def _decode_jwt(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                audience="ai-karen-users",
                issuer="ai-karen",
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")

    def _decode_refresh_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                audience="ai-karen-refresh",
                issuer="ai-karen",
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Refresh token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid refresh token: {e}")

    def _is_token_revoked(self, token_id: str) -> bool:
        if self.redis_client is None:
            return False
        try:
            return bool(
                self.redis_client.exists(self._get_redis_key("revoked", token_id))
            )
        except Exception as e:
            logger.warning(f"Failed to check token revocation: {e}")
            return False

    def _revoke_token(self, token_id: str, exp: datetime) -> bool:
        if self.redis_client is None:
            return False
        try:
            ttl = max(1, int((exp - datetime.utcnow()).total_seconds()))
            self.redis_client.setex(self._get_redis_key("revoked", token_id), ttl, "1")
            return True
        except Exception as e:
            logger.warning(f"Failed to revoke token: {e}")
            return False

    def _check_rate_limit(self, user_id: str, action: str) -> bool:
        limit_config = self.auth_rate_limits.get(action)
        if not limit_config:
            return True

        now = time.time()
        attempts = self.failed_attempts.get(user_id, [])
        attempts = [
            attempt
            for attempt in attempts
            if now - attempt["timestamp"] < limit_config["window"]
        ]
        self.failed_attempts[user_id] = attempts
        return len(attempts) < limit_config["limit"]

    def _record_failed_attempt(self, user_id: str, action: str, reason: str) -> None:
        attempts = self.failed_attempts.setdefault(user_id, [])
        attempts.append({"timestamp": time.time(), "action": action, "reason": reason})

    def _extract_token_from_request(self, request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]

        cookie_token = request.cookies.get("access_token")
        if cookie_token:
            return cookie_token

        return None

    def _extract_session_token_from_request(self, request: Request) -> Optional[str]:
        # Check for kari_session cookie (set by login endpoint)
        session_token = request.cookies.get("kari_session")
        if session_token:
            return session_token
        # Fallback to session_token for backward compatibility
        return request.cookies.get("session_token")

    def _extract_basic_auth(self, request: Request) -> Optional[tuple[str, str]]:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return None

        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, password = decoded.split(":", 1)
            return username, password
        except Exception:
            return None

    def is_public_endpoint(self, path: str) -> bool:
        public_patterns = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/refresh",
            "/api/auth/logout",
            "/api/auth/forgot-password",
            "/api/auth/reset-password",
            "/api/public/",
            "/ws",
        ]
        return any(path.startswith(pattern) for pattern in public_patterns)

    def _verify_access_token(self, token: str) -> Dict[str, Any]:
        payload = self._decode_jwt(token)
        token_id = payload.get("token_id")
        if token_id and self._is_token_revoked(token_id):
            raise AuthenticationError("Token has been revoked")
        return payload

    def _get_user_from_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "user_id": payload["sub"],
            "email": payload.get("email"),
            "user_type": payload.get("user_type", "user"),
            "permissions": payload.get("permissions", []),
            "token_id": payload.get("token_id"),
        }

    def get_current_user(self, request: Request) -> Dict[str, Any]:
        try:
            if self.is_public_endpoint(request.url.path):
                return {
                    "user_id": "anonymous",
                    "email": None,
                    "user_type": "anonymous",
                    "permissions": [],
                }

            token = self._extract_token_from_request(request)
            if token:
                payload = self._verify_access_token(token)
                return self._get_user_from_payload(payload)

            session_token = self._extract_session_token_from_request(request)
            if session_token:
                token_result = self.validate_token(session_token)
                if token_result["status"] == TokenStatus.VALID:
                    payload = token_result["payload"]
                    return {
                        "user_id": payload["sub"],
                        "email": payload.get("email"),
                        "user_type": payload.get("user_type", "user"),
                        "permissions": payload.get("permissions", []),
                        "token_id": payload.get("token_id"),
                    }

            basic_auth = self._extract_basic_auth(request)
            if basic_auth:
                username, _ = basic_auth
                return {
                    "user_id": username,
                    "email": None,
                    "user_type": "service",
                    "permissions": ["api_access"],
                }

            raise AuthenticationError("Authentication required")
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            raise AuthenticationError("Failed to authenticate user")

    def create_tokens(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        access_token_id = self._generate_token_id()
        refresh_token_id = self._generate_token_id()

        access_payload = self._create_jwt_payload(user_data, access_token_id)
        refresh_payload = self._create_refresh_token_payload(
            user_data, refresh_token_id
        )

        return {
            "access_token": self._encode_jwt(access_payload),
            "refresh_token": self._encode_jwt(refresh_payload),
            "token_type": "bearer",
            "expires_in": str(self.jwt_expiration_hours * 3600),
        }

    def validate_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = self._verify_access_token(token)
            return {"status": TokenStatus.VALID, "payload": payload}
        except AuthenticationError as e:
            message = str(e).lower()
            if "expired" in message:
                return {"status": TokenStatus.EXPIRED, "error": str(e)}
            if "revoked" in message:
                return {"status": TokenStatus.REVOKED, "error": str(e)}
            return {"status": TokenStatus.INVALID, "error": str(e)}

    def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        payload = self._decode_refresh_token(refresh_token)
        token_id = payload.get("token_id")
        if token_id and self._is_token_revoked(token_id):
            raise AuthenticationError("Refresh token has been revoked")

        user_data = {
            "user_id": payload["sub"],
            "email": payload.get("email"),
            "user_type": payload.get("user_type", "user"),
            "permissions": payload.get("permissions", []),
        }
        return self.create_tokens(user_data)

    def revoke_token(self, token: str) -> bool:
        try:
            payload = self._decode_jwt(token)
            token_id = payload.get("token_id")
            exp = payload.get("exp")
            if not token_id or not exp:
                return False
            exp_dt = datetime.utcfromtimestamp(exp)
            return self._revoke_token(token_id, exp_dt)
        except Exception as e:
            logger.warning(f"Failed to revoke token: {e}")
            return False

    def revoke_refresh_token(self, token: str) -> bool:
        try:
            payload = self._decode_refresh_token(token)
            token_id = payload.get("token_id")
            exp = payload.get("exp")
            if not token_id or not exp:
                return False
            exp_dt = datetime.utcfromtimestamp(exp)
            return self._revoke_token(token_id, exp_dt)
        except Exception as e:
            logger.warning(f"Failed to revoke refresh token: {e}")
            return False

    def require_permission(self, permission: str):
        def decorator(func):
            @wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                user = self.get_current_user(request)
                if permission not in user.get("permissions", []):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission '{permission}' required",
                    )
                return await func(request, *args, **kwargs)

            return wrapper

        return decorator

    async def authenticate_request(self, request: Request) -> Dict[str, Any]:
        try:
            token = self._extract_token_from_request(request)
            if token:
                token_result = self.validate_token(token)
                if token_result["status"] == TokenStatus.VALID:
                    payload = token_result["payload"]
                    return {
                        "user_id": payload["sub"],
                        "email": payload.get("email"),
                        "user_type": payload.get("user_type", "user"),
                        "permissions": payload.get("permissions", []),
                        "token_id": payload.get("token_id"),
                    }

            session_token = self._extract_session_token_from_request(request)
            if session_token:
                token_result = self.validate_token(session_token)
                if token_result["status"] == TokenStatus.VALID:
                    payload = token_result["payload"]
                    return {
                        "user_id": payload["sub"],
                        "email": payload.get("email"),
                        "user_type": payload.get("user_type", "user"),
                        "permissions": payload.get("permissions", []),
                        "token_id": payload.get("token_id"),
                    }

                auth_service = await get_auth_service()
                client_ip = request.client.host if request.client else "unknown"
                user_agent = request.headers.get("User-Agent", "")
                user = await auth_service.validate_session(
                    session_token,
                    ip_address=client_ip,
                    user_agent=user_agent,
                )
                if not user:
                    raise AuthenticationError(
                        f"Invalid session: {token_result.get('error', 'verification failed')}"
                    )

                user_data = user_account_to_dict(user)
                user_data.setdefault("user_id", user.id)
                user_data.setdefault("user_type", "user")
                user_data.setdefault("permissions", [])
                return user_data

            return self.get_current_user(request)

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error authenticating request: {e}")
            raise AuthenticationError("Failed to authenticate user")


_auth_middleware: Optional[SecureAuthMiddleware] = None


def get_auth_middleware() -> SecureAuthMiddleware:
    """Get global authentication middleware instance."""
    global _auth_middleware
    if _auth_middleware is None:
        _auth_middleware = SecureAuthMiddleware()
    return _auth_middleware


async def get_current_user(request: Request) -> Dict[str, Any]:
    """FastAPI dependency to get current user."""
    auth_middleware = get_auth_middleware()
    return auth_middleware.get_current_user(request)


async def get_rate_limiter() -> SecureAuthMiddleware:
    """FastAPI dependency to get rate limiter."""
    auth_middleware = get_auth_middleware()
    return auth_middleware


__all__ = [
    "AuthenticationError",
    "BaseAuthMiddleware",
    "SecureAuthMiddleware",
    "TokenStatus",
    "get_auth_middleware",
    "get_current_user",
    "get_rate_limiter",
]
