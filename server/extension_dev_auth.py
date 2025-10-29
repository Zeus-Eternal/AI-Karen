"""
Development Mode Authentication for Extensions

Provides development-specific authentication bypass mechanisms, mock authentication,
and hot reload support without authentication issues.

Requirements addressed:
- 6.1: Development mode authentication with local credentials
- 6.2: Hot reload support without authentication issues  
- 6.3: Mock authentication for testing
- 6.4: Detailed logging for debugging
- 6.5: Environment-specific configuration adaptation
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

logger = logging.getLogger(__name__)

class DevelopmentAuthManager:
    """Development-specific authentication manager for extensions."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize development authentication manager."""
        self.config = config or {}
        self.enabled = self._is_development_environment()
        self.mock_users = self._initialize_mock_users()
        self.dev_tokens = {}  # Cache for development tokens
        self.bearer_scheme = HTTPBearer(auto_error=False)
        
        # Development-specific settings
        self.bypass_auth = self.config.get("bypass_auth", True)
        self.mock_auth_enabled = self.config.get("mock_auth_enabled", True)
        self.hot_reload_support = self.config.get("hot_reload_support", True)
        self.debug_logging = self.config.get("debug_logging", True)
        
        if self.enabled:
            logger.info("Development authentication manager initialized")
            if self.debug_logging:
                logger.debug(f"Development auth config: {self.config}")
    
    def _is_development_environment(self) -> bool:
        """Check if running in development environment."""
        env_indicators = [
            os.getenv("ENVIRONMENT", "").lower() in ["development", "dev", "local"],
            os.getenv("NODE_ENV", "").lower() == "development",
            os.getenv("FLASK_ENV", "").lower() == "development",
            os.getenv("FASTAPI_ENV", "").lower() == "development",
            os.getenv("EXTENSION_DEVELOPMENT_MODE", "").lower() == "true",
            # Check for development server indicators
            "runserver" in " ".join(os.sys.argv) if hasattr(os, 'sys') else False,
            "dev" in " ".join(os.sys.argv) if hasattr(os, 'sys') else False,
        ]
        
        return any(env_indicators)
    
    def _initialize_mock_users(self) -> Dict[str, Dict[str, Any]]:
        """Initialize mock users for development testing."""
        return {
            "dev-user": {
                "user_id": "dev-user",
                "tenant_id": "dev-tenant",
                "roles": ["admin", "user", "developer"],
                "permissions": [
                    "extension:*",
                    "extension:read",
                    "extension:write",
                    "extension:admin",
                    "extension:background_tasks",
                    "extension:configure",
                    "extension:install",
                    "extension:health",
                    "extension:metrics"
                ],
                "email": "dev@localhost",
                "name": "Development User"
            },
            "test-user": {
                "user_id": "test-user",
                "tenant_id": "test-tenant",
                "roles": ["user"],
                "permissions": [
                    "extension:read",
                    "extension:write"
                ],
                "email": "test@localhost",
                "name": "Test User"
            },
            "admin-user": {
                "user_id": "admin-user",
                "tenant_id": "admin-tenant",
                "roles": ["admin", "super_admin"],
                "permissions": ["extension:*"],
                "email": "admin@localhost",
                "name": "Admin User"
            },
            "readonly-user": {
                "user_id": "readonly-user",
                "tenant_id": "readonly-tenant",
                "roles": ["user"],
                "permissions": ["extension:read"],
                "email": "readonly@localhost",
                "name": "Read-Only User"
            }
        }
    
    def is_development_request(self, request: Request) -> bool:
        """Check if request should use development authentication."""
        if not self.enabled:
            return False
        
        # Check for development headers
        dev_headers = [
            request.headers.get("X-Development-Mode") == "true",
            request.headers.get("X-Skip-Auth") == "dev",
            request.headers.get("X-Mock-Auth") == "true",
            request.headers.get("X-Hot-Reload") == "true"
        ]
        
        if any(dev_headers):
            return True
        
        # Check for local development
        if request.client and request.client.host in ["127.0.0.1", "localhost", "::1"]:
            # Check for development ports
            dev_ports = [3000, 3001, 8000, 8001, 8010, 8020, 5173, 5174]  # Common dev ports
            if hasattr(request.url, 'port') and request.url.port in dev_ports:
                return True
            
            # Check for development URL patterns
            dev_patterns = ["/dev/", "/development/", "/test/"]
            if any(pattern in str(request.url.path) for pattern in dev_patterns):
                return True
        
        # Check for development environment variables
        if self.bypass_auth:
            return True
        
        return False
    
    def create_development_token(
        self,
        user_id: str = "dev-user",
        tenant_id: Optional[str] = None,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a development authentication token."""
        
        # Get user data from mock users or create default
        user_data = self.mock_users.get(user_id, {
            "user_id": user_id,
            "tenant_id": tenant_id or "dev-tenant",
            "roles": roles or ["user"],
            "permissions": permissions or ["extension:read", "extension:write"]
        })
        
        # Override with provided values
        if tenant_id:
            user_data["tenant_id"] = tenant_id
        if roles:
            user_data["roles"] = roles
        if permissions:
            user_data["permissions"] = permissions
        
        # Set expiration (long-lived for development)
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=24)  # 24 hours for dev
        
        payload = {
            "user_id": user_data["user_id"],
            "tenant_id": user_data["tenant_id"],
            "roles": user_data["roles"],
            "permissions": user_data["permissions"],
            "token_type": "development",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": "kari-extension-dev-system",
            "dev_mode": True,
            "mock_user": True
        }
        
        # Use a simple secret for development
        secret_key = os.getenv("EXTENSION_SECRET_KEY", "dev-extension-secret-key")
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Cache the token
        self.dev_tokens[user_id] = {
            "token": token,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expire,
            "user_data": user_data
        }
        
        if self.debug_logging:
            logger.debug(f"Created development token for user {user_id}")
        
        return token
    
    def get_cached_development_token(self, user_id: str = "dev-user") -> Optional[str]:
        """Get cached development token if still valid."""
        cached = self.dev_tokens.get(user_id)
        if not cached:
            return None
        
        # Check if token is still valid
        if datetime.now(timezone.utc) >= cached["expires_at"]:
            # Token expired, remove from cache
            del self.dev_tokens[user_id]
            return None
        
        return cached["token"]
    
    def authenticate_development_request(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = None
    ) -> Dict[str, Any]:
        """Authenticate development request with bypass or mock authentication."""
        
        if not self.enabled:
            raise HTTPException(
                status_code=500,
                detail="Development authentication not enabled"
            )
        
        # Check for mock user specification in headers
        mock_user_id = request.headers.get("X-Mock-User-ID", "dev-user")
        mock_tenant_id = request.headers.get("X-Mock-Tenant-ID")
        mock_roles = request.headers.get("X-Mock-Roles", "").split(",") if request.headers.get("X-Mock-Roles") else None
        mock_permissions = request.headers.get("X-Mock-Permissions", "").split(",") if request.headers.get("X-Mock-Permissions") else None
        
        # Clean up empty strings from split
        if mock_roles:
            mock_roles = [role.strip() for role in mock_roles if role.strip()]
        if mock_permissions:
            mock_permissions = [perm.strip() for perm in mock_permissions if perm.strip()]
        
        # Check if we should bypass authentication entirely
        if self.bypass_auth and request.headers.get("X-Skip-Auth") == "dev":
            user_context = self._create_bypass_user_context(
                mock_user_id, mock_tenant_id, mock_roles, mock_permissions
            )
            if self.debug_logging:
                logger.debug(f"Development auth bypass for user {user_context['user_id']}")
            return user_context
        
        # Check for existing valid token
        if credentials and credentials.credentials:
            try:
                # Try to validate the provided token
                secret_key = os.getenv("EXTENSION_SECRET_KEY", "dev-extension-secret-key")
                payload = jwt.decode(credentials.credentials, secret_key, algorithms=["HS256"])
                
                # Check if it's a development token
                if payload.get("dev_mode") or payload.get("token_type") == "development":
                    user_context = {
                        "user_id": payload.get("user_id"),
                        "tenant_id": payload.get("tenant_id"),
                        "roles": payload.get("roles", []),
                        "permissions": payload.get("permissions", []),
                        "token_type": "development",
                        "dev_mode": True
                    }
                    
                    if self.debug_logging:
                        logger.debug(f"Validated development token for user {user_context['user_id']}")
                    
                    return user_context
                
            except jwt.ExpiredSignatureError:
                if self.debug_logging:
                    logger.debug("Development token expired, creating new one")
            except jwt.InvalidTokenError:
                if self.debug_logging:
                    logger.debug("Invalid development token, creating new one")
        
        # Create or get cached development token
        token = self.get_cached_development_token(mock_user_id)
        if not token:
            token = self.create_development_token(
                mock_user_id, mock_tenant_id, mock_roles, mock_permissions
            )
        
        # Decode the token to get user context
        try:
            secret_key = os.getenv("EXTENSION_SECRET_KEY", "dev-extension-secret-key")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            
            user_context = {
                "user_id": payload.get("user_id"),
                "tenant_id": payload.get("tenant_id"),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", []),
                "token_type": "development",
                "dev_mode": True,
                "dev_token": token  # Include token for client use
            }
            
            if self.debug_logging:
                logger.debug(f"Created development auth context for user {user_context['user_id']}")
            
            return user_context
            
        except Exception as e:
            logger.error(f"Failed to create development auth context: {e}")
            raise HTTPException(
                status_code=500,
                detail="Development authentication failed"
            )
    
    def _create_bypass_user_context(
        self,
        user_id: str = "dev-user",
        tenant_id: Optional[str] = None,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create user context for authentication bypass."""
        
        # Get base user data
        user_data = self.mock_users.get(user_id, {})
        
        return {
            "user_id": user_id,
            "tenant_id": tenant_id or user_data.get("tenant_id", "dev-tenant"),
            "roles": roles or user_data.get("roles", ["admin", "user"]),
            "permissions": permissions or user_data.get("permissions", ["extension:*"]),
            "token_type": "bypass",
            "dev_mode": True,
            "bypass_auth": True
        }
    
    def create_hot_reload_token(self) -> str:
        """Create a special token for hot reload scenarios."""
        return self.create_development_token(
            user_id="hot-reload-user",
            tenant_id="hot-reload-tenant",
            roles=["developer", "admin"],
            permissions=["extension:*", "hot_reload:*"],
            expires_delta=timedelta(minutes=5)  # Short-lived for security
        )
    
    def validate_hot_reload_request(self, request: Request) -> bool:
        """Validate if request is from hot reload system."""
        hot_reload_indicators = [
            request.headers.get("X-Hot-Reload") == "true",
            request.headers.get("X-Webpack-Dev-Server") is not None,
            request.headers.get("X-Vite-HMR") is not None,
            "webpack-dev-server" in request.headers.get("User-Agent", "").lower(),
            "vite" in request.headers.get("User-Agent", "").lower(),
        ]
        
        return any(hot_reload_indicators)
    
    def get_development_user_list(self) -> List[Dict[str, Any]]:
        """Get list of available development users for testing."""
        return [
            {
                "user_id": user_id,
                "name": user_data.get("name", user_id),
                "email": user_data.get("email", f"{user_id}@localhost"),
                "roles": user_data.get("roles", []),
                "permissions": user_data.get("permissions", []),
                "tenant_id": user_data.get("tenant_id", "dev-tenant")
            }
            for user_id, user_data in self.mock_users.items()
        ]
    
    def create_test_scenario_token(self, scenario: str) -> str:
        """Create tokens for specific test scenarios."""
        scenarios = {
            "expired_token": {
                "user_id": "expired-user",
                "expires_delta": timedelta(seconds=-1)  # Already expired
            },
            "limited_permissions": {
                "user_id": "limited-user",
                "permissions": ["extension:read"]
            },
            "no_permissions": {
                "user_id": "no-perm-user",
                "permissions": []
            },
            "service_token": {
                "user_id": "service:test-service",
                "roles": ["service"],
                "permissions": ["extension:background_tasks"]
            }
        }
        
        scenario_config = scenarios.get(scenario, {})
        return self.create_development_token(**scenario_config)
    
    def clear_development_cache(self):
        """Clear all cached development tokens."""
        self.dev_tokens.clear()
        if self.debug_logging:
            logger.debug("Development token cache cleared")
    
    def get_development_status(self) -> Dict[str, Any]:
        """Get current development authentication status."""
        return {
            "enabled": self.enabled,
            "bypass_auth": self.bypass_auth,
            "mock_auth_enabled": self.mock_auth_enabled,
            "hot_reload_support": self.hot_reload_support,
            "debug_logging": self.debug_logging,
            "cached_tokens": len(self.dev_tokens),
            "mock_users": len(self.mock_users),
            "environment": os.getenv("ENVIRONMENT", "unknown")
        }


# Global development auth manager instance
_dev_auth_manager: Optional[DevelopmentAuthManager] = None

def get_development_auth_manager() -> DevelopmentAuthManager:
    """Get or create the global development authentication manager."""
    global _dev_auth_manager
    if _dev_auth_manager is None:
        # Load configuration from settings
        try:
            from server.config import settings
            config = {
                "bypass_auth": settings.extension_dev_bypass_enabled,
                "mock_auth_enabled": settings.extension_development_mode,
                "hot_reload_support": True,
                "debug_logging": settings.debug,
            }
        except ImportError:
            config = {}
        
        _dev_auth_manager = DevelopmentAuthManager(config)
    
    return _dev_auth_manager

def reset_development_auth_manager():
    """Reset the global development authentication manager (useful for testing)."""
    global _dev_auth_manager
    _dev_auth_manager = None

# FastAPI dependency for development authentication
async def require_development_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Dict[str, Any]:
    """FastAPI dependency for development authentication."""
    dev_auth = get_development_auth_manager()
    
    if not dev_auth.enabled:
        raise HTTPException(
            status_code=403,
            detail="Development authentication not available in this environment"
        )
    
    if not dev_auth.is_development_request(request):
        raise HTTPException(
            status_code=403,
            detail="Request not recognized as development request"
        )
    
    return dev_auth.authenticate_development_request(request, credentials)