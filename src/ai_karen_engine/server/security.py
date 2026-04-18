# mypy: ignore-errors
"""
Security configuration for Kari FastAPI Server.
Handles password context, API key headers, OAuth2 schemes, SSL context, and extension authentication.
"""

import ssl
import jwt
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Request, Depends
from fastapi.security import (
    APIKeyHeader,
    OAuth2PasswordBearer,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Security Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Extension-specific authentication
extension_bearer = HTTPBearer(auto_error=False)
extension_api_key = APIKeyHeader(name="X-EXTENSION-API-KEY", auto_error=False)


def get_ssl_context():
    """Create and configure SSL context for secure connections"""
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.set_ciphers("ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384")
    ssl_context.load_cert_chain("cert.pem", "key.pem")
    return ssl_context


class ExtensionAuthManager:
    """Authentication manager for extension API endpoints."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize extension authentication manager with configuration."""
        if config is None:
            # Import here to avoid circular imports
            from ai_karen_engine.server.config import Settings

            settings = Settings()
            config = settings.get_extension_auth_config()

        self.config = config
        self.secret_key = config.get(
            "secret_key", os.getenv("EXTENSION_SECRET_KEY", "dev-secret-key")
        )
        self.algorithm = config.get("algorithm", "HS256")
        self.bearer_scheme = HTTPBearer(auto_error=False)
        self.enabled = config.get("enabled", True)
        self.auth_mode = config.get("auth_mode", "hybrid")
        self.dev_bypass_enabled = config.get("dev_bypass_enabled", True)
        self.require_https = config.get("require_https", False)

        # Initialize token manager for advanced token operations
        self.token_manager = None
        self._init_token_manager()

    def _init_token_manager(self):
        """Initialize token manager if available."""
        try:
            from ai_karen_engine.server.token_manager import TokenManager

            self.token_manager = TokenManager(self.config)
        except ImportError:
            # Token manager not available, use basic token handling
            logger.info(
                "Using basic token handling (advanced token manager not available)"
            )

    def create_access_token(
        self,
        user_id: str,
        tenant_id: str = "default",
        roles: List[str] = None,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create JWT access token for extension API access."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            # Use configured expiration time
            expire_minutes = self.config.get("access_token_expire_minutes", 60)
            expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)

        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "roles": roles or ["user"],
            "permissions": permissions or ["extension:read"],
            "token_type": "access",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": "kari-extension-system",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_service_token(
        self,
        service_name: str,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create service-to-service authentication token."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            # Use configured service token expiration time
            expire_minutes = self.config.get("service_token_expire_minutes", 30)
            expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)

        payload = {
            "service_name": service_name,
            "permissions": permissions or ["extension:background_tasks"],
            "token_type": "service",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": "kari-extension-system",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_background_task_token(
        self, task_id: str, task_type: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create specialized token for background task execution."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            # Short-lived token for background tasks
            expire = datetime.now(timezone.utc) + timedelta(minutes=5)

        payload = {
            "task_id": task_id,
            "task_type": task_type,
            "token_type": "background_task",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": "kari-extension-system",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_token_pair(
        self,
        user_id: str,
        tenant_id: str = "default",
        roles: List[str] = None,
        permissions: List[str] = None,
    ) -> Dict[str, str]:
        """Create access token and refresh token pair."""
        access_token = self.create_access_token(
            user_id=user_id, tenant_id=tenant_id, roles=roles, permissions=permissions
        )

        # Create refresh token with longer expiration
        refresh_expire = datetime.now(timezone.utc) + timedelta(days=7)
        refresh_payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "token_type": "refresh",
            "exp": refresh_expire,
            "iat": datetime.now(timezone.utc),
            "iss": "kari-extension-system",
        }
        refresh_token = jwt.encode(
            refresh_payload, self.secret_key, algorithm=self.algorithm
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create new access token using refresh token."""
        try:
            payload = jwt.decode(
                refresh_token, self.secret_key, algorithms=[self.algorithm]
            )

            # Validate token type
            if payload.get("token_type") != "refresh":
                return None

            # Create new access token
            return self.create_access_token(
                user_id=payload.get("user_id"),
                tenant_id=payload.get("tenant_id"),
                roles=payload.get("roles"),
                permissions=payload.get("permissions"),
            )
        except jwt.PyJWTError:
            return None

    def revoke_token(self, token: str) -> bool:
        """Revoke a specific token (requires token manager)."""
        if self.token_manager:
            return self.token_manager.revoke_token(token)
        return False

    def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a specific user (requires token manager)."""
        if self.token_manager:
            return self.token_manager.revoke_user_tokens(user_id)
        return 0

    async def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload."""
        try:
            # First try enhanced validation if token manager is available
            if self.token_manager:
                result = await self.token_manager.validate_token(token)
                if result["valid"]:
                    return result["payload"]

            # Fallback to basic JWT validation
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None

    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return user information."""
        # This would typically check against a database of API keys
        # For now, we'll use a simple validation
        if api_key == self.config.get("api_key"):
            return {
                "user_id": "api_key_user",
                "tenant_id": "default",
                "roles": ["admin"],
                "permissions": ["extension:*"],
            }
        return None

    def is_development_mode(self, request: Request) -> bool:
        """Check if request is in development mode."""
        if not self.dev_bypass_enabled:
            return False

        # Check multiple indicators of development mode
        user_agent = request.headers.get("user-agent", "").lower()
        forwarded_for = request.headers.get("x-forwarded-for")
        real_ip = request.headers.get("x-real-ip")

        # Check for development indicators in headers
        if forwarded_for and forwarded_for in ["127.0.0.1", "localhost"]:
            return True

        if real_ip and real_ip in ["127.0.0.1", "localhost"]:
            return True

        # Check for development user agents
        dev_indicators = ["python", "curl", "postman", "insomnia", "localhost"]
        if any(indicator in user_agent for indicator in dev_indicators):
            return True

        # Check for localhost in host header
        host = request.headers.get("host", "")
        if "localhost" in host or "127.0.0.1" in host:
            return True

        return False

    async def authenticate_extension_request(
        self, request: Request
    ) -> Optional[Dict[str, Any]]:
        """Authenticate extension request using multiple methods."""
        if not self.enabled:
            # Extension authentication disabled, allow all requests
            return {
                "user_id": "anonymous",
                "tenant_id": "default",
                "roles": ["public"],
                "permissions": ["extension:read"],
            }

        # Check development mode bypass
        if self.is_development_mode(request):
            logger.info("Development mode bypass for extension request")
            return {
                "user_id": "dev_user",
                "tenant_id": "default",
                "roles": ["developer"],
                "permissions": ["extension:*"],
            }

        # Try JWT token authentication
        credentials = await self.bearer_scheme(request)
        if credentials:
            token_data = await self.validate_jwt_token(credentials.credentials)
            if token_data:
                return token_data

        # Try API key authentication
        api_key = await extension_api_key(request)
        if api_key:
            key_data = await self.validate_api_key(api_key)
            if key_data:
                return key_data

        # No valid authentication found
        return None

    def require_extension_read(
        self, token: str = Depends(extension_bearer)
    ) -> Dict[str, Any]:
        """FastAPI dependency for extension read access."""
        if not self.enabled:
            return {
                "user_id": "anonymous",
                "tenant_id": "default",
                "roles": ["public"],
                "permissions": ["extension:read"],
            }

        # Check development mode bypass
        if self.dev_bypass_enabled:
            # For development mode, allow read access
            return {
                "user_id": "dev_user",
                "tenant_id": "default",
                "roles": ["developer"],
                "permissions": ["extension:read"],
            }

        # Validate token
        token_data = self.validate_jwt_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid extension token")

        # Check read permission
        permissions = token_data.get("permissions", [])
        if "extension:read" not in permissions and "extension:*" not in permissions:
            raise HTTPException(
                status_code=403, detail="Extension read access required"
            )

        return token_data

    def require_extension_write(
        self, token: str = Depends(extension_bearer)
    ) -> Dict[str, Any]:
        """FastAPI dependency for extension write access."""
        if not self.enabled:
            raise HTTPException(
                status_code=401, detail="Extension authentication required"
            )

        # Check development mode bypass
        if self.dev_bypass_enabled:
            # For development mode, allow write access
            return {
                "user_id": "dev_user",
                "tenant_id": "default",
                "roles": ["developer"],
                "permissions": ["extension:*"],
            }

        # Validate token
        token_data = self.validate_jwt_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid extension token")

        # Check write permission
        permissions = token_data.get("permissions", [])
        if "extension:write" not in permissions and "extension:*" not in permissions:
            raise HTTPException(
                status_code=403, detail="Extension write access required"
            )

        return token_data

    def require_extension_admin(
        self, token: str = Depends(extension_bearer)
    ) -> Dict[str, Any]:
        """FastAPI dependency for extension admin access."""
        if not self.enabled:
            raise HTTPException(
                status_code=401, detail="Extension authentication required"
            )

        # Check development mode bypass
        if self.dev_bypass_enabled:
            # For development mode, allow admin access
            return {
                "user_id": "dev_user",
                "tenant_id": "default",
                "roles": ["developer"],
                "permissions": ["extension:*"],
            }

        # Validate token
        token_data = self.validate_jwt_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid extension token")

        # Check admin permission
        permissions = token_data.get("permissions", [])
        if "extension:*" not in permissions:
            raise HTTPException(
                status_code=403, detail="Extension admin access required"
            )

        return token_data

    def require_background_tasks(
        self, token: str = Depends(extension_bearer)
    ) -> Dict[str, Any]:
        """FastAPI dependency for background task access."""
        if not self.enabled:
            raise HTTPException(
                status_code=401, detail="Extension authentication required"
            )

        # Check development mode bypass
        if self.dev_bypass_enabled:
            # For development mode, allow background task access
            return {
                "user_id": "dev_user",
                "tenant_id": "default",
                "roles": ["developer"],
                "permissions": ["extension:*"],
            }

        # Validate token
        token_data = self.validate_jwt_token(token.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid extension token")

        # Check background task permission
        permissions = token_data.get("permissions", [])
        if not any(
            perm in permissions
            for perm in ["extension:background_tasks", "extension:*"]
        ):
            raise HTTPException(
                status_code=403, detail="Background task access required"
            )

        return token_data


# Global extension authentication manager instance
_extension_auth_manager = None


def get_extension_auth_manager() -> ExtensionAuthManager:
    """Get the global extension authentication manager instance."""
    global _extension_auth_manager
    if _extension_auth_manager is None:
        _extension_auth_manager = ExtensionAuthManager()
    return _extension_auth_manager


def require_extension_read_dep(
    token: str = Depends(extension_bearer),
) -> Dict[str, Any]:
    """Global dependency for extension read access."""
    auth_manager = get_extension_auth_manager()
    return auth_manager.require_extension_read(token)


def require_extension_write_dep(
    token: str = Depends(extension_bearer),
) -> Dict[str, Any]:
    """Global dependency for extension write access."""
    auth_manager = get_extension_auth_manager()
    return auth_manager.require_extension_write(token)


def require_extension_admin_dep(
    token: str = Depends(extension_bearer),
) -> Dict[str, Any]:
    """Global dependency for extension admin access."""
    auth_manager = get_extension_auth_manager()
    return auth_manager.require_extension_admin(token)


def require_background_tasks_dep(
    token: str = Depends(extension_bearer),
) -> Dict[str, Any]:
    """Global dependency for background task access."""
    auth_manager = get_extension_auth_manager()
    return auth_manager.require_background_tasks(token)


def validate_environment_security() -> Dict[str, Any]:
    """Validate environment security configuration."""
    issues = []

    try:
        from ai_karen_engine.server.config import Settings

        settings = Settings()

        # Check for default secrets in production
        if settings.environment.lower() == "production":
            if settings.secret_key == "super-secret-key-change-me":
                issues.append("Default SECRET_KEY detected in production")

            if (
                settings.extension_secret_key
                == "dev-extension-secret-key-change-in-production"
            ):
                issues.append("Default extension secret key detected in production")

            if (
                settings.extension_api_key
                == "dev-extension-api-key-change-in-production"
            ):
                issues.append("Default extension API key detected in production")

        # Check SSL configuration
        try:
            ssl_context = get_ssl_context()
            if ssl_context:
                logger.info("SSL context configured successfully")
            else:
                issues.append("SSL context configuration failed")
        except Exception as e:
            issues.append(f"SSL configuration error: {e}")

        # Check debug mode in production
        if settings.debug and settings.environment.lower() == "production":
            issues.append("Debug mode enabled in production")

        # Check HTTPS requirement for extensions in production
        if (
            settings.extension_require_https
            and settings.environment.lower() == "production"
        ):
            # This would check if HTTPS is actually being used
            pass

        # Validate extension configuration
        if not settings.validate_extension_auth_config():
            issues.append("Extension authentication configuration validation failed")

        # Overall status
        overall_status = "secure" if not issues else "issues_found"

        return {
            "overall_status": overall_status,
            "secrets_validation": {
                "secret_key_secure": settings.secret_key
                != "super-secret-key-change-me",
                "extension_secret_key_secure": settings.extension_secret_key
                != "dev-extension-secret-key-change-in-production",
                "extension_api_key_secure": settings.extension_api_key
                != "dev-extension-api-key-change-in-production",
            },
            "issues": issues,
            "environment": settings.environment,
            "debug_mode": settings.debug,
        }

    except Exception as e:
        logger.error(f"Environment security validation failed: {e}")
        return {
            "overall_status": "error",
            "error": str(e),
            "issues": ["Environment security validation failed"],
        }
