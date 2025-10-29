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
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
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
            from server.config import settings
            config = settings.get_extension_auth_config()
        
        self.config = config
        self.secret_key = config.get("secret_key", os.getenv("EXTENSION_SECRET_KEY", "dev-secret-key"))
        self.algorithm = config.get("algorithm", "HS256")
        self.bearer_scheme = HTTPBearer(auto_error=False)
        self.enabled = config.get("enabled", True)
        self.auth_mode = config.get("auth_mode", "hybrid")
        self.dev_bypass_enabled = config.get("dev_bypass_enabled", True)
        self.require_https = config.get("require_https", False)
        
        # Initialize token manager for advanced token operations
        self.token_manager = None
        self._init_token_manager()
        
    def create_access_token(
        self, 
        user_id: str, 
        tenant_id: str = "default",
        roles: List[str] = None,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None
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
            "iss": "kari-extension-system"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_service_token(
        self,
        service_name: str,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None
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
            "token_type": "service",
            "permissions": permissions or ["extension:background_tasks"],
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": "kari-extension-system"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def _init_token_manager(self):
        """Initialize token manager for advanced token operations."""
        try:
            from server.token_manager import create_token_manager
            self.token_manager = create_token_manager(self.config)
            logger.debug("Token manager initialized for extension authentication")
        except Exception as e:
            logger.warning(f"Failed to initialize token manager: {e}")
            self.token_manager = None
    
    def create_enhanced_access_token(
        self, 
        user_id: str, 
        tenant_id: str = "default",
        roles: List[str] = None,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create enhanced JWT access token with blacklist support."""
        if self.token_manager:
            token, _ = self.token_manager.generate_access_token(
                user_id=user_id,
                tenant_id=tenant_id,
                roles=roles,
                permissions=permissions,
                expires_delta=expires_delta
            )
            return token
        else:
            # Fallback to basic token creation
            return self.create_access_token(user_id, tenant_id, roles, permissions, expires_delta)
    
    def create_enhanced_service_token(
        self,
        service_name: str,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create enhanced service token with blacklist support."""
        if self.token_manager:
            token, _ = self.token_manager.generate_service_token(
                service_name=service_name,
                permissions=permissions,
                expires_delta=expires_delta
            )
            return token
        else:
            # Fallback to basic service token creation
            return self.create_service_token(service_name, permissions, expires_delta)
    
    def create_background_task_token(
        self,
        task_name: str,
        user_id: Optional[str] = None,
        service_name: Optional[str] = None,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create token specifically for background task execution."""
        if self.token_manager:
            token, _ = self.token_manager.generate_background_task_token(
                task_name=task_name,
                user_id=user_id,
                service_name=service_name,
                permissions=permissions,
                expires_delta=expires_delta
            )
            return token
        else:
            # Fallback: create service token for background tasks
            effective_service_name = service_name or f"background_task_{task_name}"
            return self.create_service_token(
                effective_service_name,
                permissions or ["extension:background_tasks", "extension:execute"],
                expires_delta or timedelta(minutes=15)
            )
    
    async def generate_user_token_pair(
        self,
        user_id: str,
        tenant_id: str = "default",
        roles: List[str] = None,
        permissions: List[str] = None
    ) -> Dict[str, Any]:
        """Generate both access and refresh tokens for a user."""
        if self.token_manager:
            from server.token_manager import generate_user_tokens
            return await generate_user_tokens(user_id, tenant_id, roles, permissions)
        else:
            # Fallback: generate only access token
            access_token = self.create_access_token(user_id, tenant_id, roles, permissions)
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": self.config.get("access_token_expire_minutes", 60) * 60
            }
    
    async def refresh_user_token(
        self,
        refresh_token: str,
        new_permissions: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token."""
        if self.token_manager:
            access_token, new_refresh_token, payload = await self.token_manager.refresh_access_token(
                refresh_token, new_permissions
            )
            
            if access_token and new_refresh_token:
                return {
                    "access_token": access_token,
                    "refresh_token": new_refresh_token,
                    "token_type": "bearer",
                    "expires_in": self.config.get("access_token_expire_minutes", 60) * 60
                }
        
        return None
    
    async def revoke_token(self, token: str) -> bool:
        """Revoke token by adding to blacklist."""
        if self.token_manager:
            return await self.token_manager.revoke_token(token)
        else:
            logger.warning("Token revocation not available without token manager")
            return False
    
    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a specific user."""
        if self.token_manager:
            return await self.token_manager.revoke_all_user_tokens(user_id)
        else:
            logger.warning("Bulk token revocation not available without token manager")
            return 0

    async def authenticate_extension_request(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(extension_bearer)
    ) -> Dict[str, Any]:
        """Authenticate extension API request and return user context."""
        
        # Check if authentication is disabled
        if not self.enabled:
            logger.debug("Extension authentication is disabled")
            return self._create_dev_user_context()
        
        # Check for development mode authentication
        if self.dev_bypass_enabled and self._is_development_mode(request):
            try:
                from .extension_dev_auth import get_development_auth_manager
                dev_auth = get_development_auth_manager()
                
                if dev_auth.enabled and dev_auth.is_development_request(request):
                    logger.debug("Using development mode authentication")
                    return dev_auth.authenticate_development_request(request, credentials)
            except Exception as e:
                logger.warning(f"Development authentication failed, falling back to standard: {e}")
            
            # Fallback to standard development context
            logger.debug("Using development mode authentication bypass")
            return self._create_dev_user_context()
        
        # Check for API key authentication first
        api_key = request.headers.get("X-EXTENSION-API-KEY")
        if api_key:
            return await self._authenticate_with_api_key(api_key)
        
        # Check for JWT token authentication
        if not credentials:
            logger.warning(f"No authentication credentials provided for {request.url.path}")
            raise HTTPException(
                status_code=403,
                detail="Authentication required for extension API"
            )
        
        try:
            # Use enhanced token validation if available
            if self.token_manager:
                from server.token_manager import TokenStatus, validate_and_extract_user_context
                
                user_context = await validate_and_extract_user_context(credentials.credentials)
                
                if not user_context:
                    logger.warning("Token validation failed with enhanced token manager")
                    raise HTTPException(status_code=403, detail="Invalid or expired token")
                
                logger.debug(f"Authenticated {user_context['user_id']} for extension API (enhanced)")
                return user_context
            else:
                # Fallback to basic JWT validation
                payload = jwt.decode(
                    credentials.credentials,
                    self.secret_key,
                    algorithms=[self.algorithm]
                )
                
                # Extract user context based on token type
                if payload.get("token_type") == "service":
                    user_context = {
                        'service_name': payload.get('service_name'),
                        'token_type': 'service',
                        'permissions': payload.get('permissions', []),
                        'user_id': f"service:{payload.get('service_name')}",
                        'tenant_id': 'system',
                        'roles': ['service']
                    }
                else:
                    user_context = {
                        'user_id': payload.get('user_id'),
                        'tenant_id': payload.get('tenant_id', 'default'),
                        'roles': payload.get('roles', []),
                        'permissions': payload.get('permissions', []),
                        'token_type': payload.get('token_type', 'access')
                    }
                
                # Validate required fields
                if not user_context.get('user_id'):
                    raise HTTPException(status_code=403, detail="Invalid token: missing user identification")
                
                logger.debug(f"Authenticated {user_context['user_id']} for extension API (basic)")
                return user_context
            
        except jwt.ExpiredSignatureError:
            logger.warning("Expired token provided for extension API")
            raise HTTPException(status_code=403, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token provided for extension API: {e}")
            raise HTTPException(status_code=403, detail="Invalid token")
        except Exception as e:
            logger.error(f"Authentication error for extension API: {e}")
            raise HTTPException(status_code=500, detail="Authentication service error")
    
    async def _authenticate_with_api_key(self, api_key: str) -> Dict[str, Any]:
        """Authenticate using API key (for admin operations)."""
        # Use configured API key
        expected_key = self.config.get("api_key", os.getenv("EXTENSION_API_KEY", "dev-extension-key"))
        
        if api_key != expected_key:
            raise HTTPException(status_code=403, detail="Invalid API key")
        
        return {
            'user_id': 'api-key-user',
            'tenant_id': 'system',
            'roles': ['admin'],
            'permissions': ['extension:*'],
            'token_type': 'api_key'
        }
    
    def _is_development_mode(self, request: Request) -> bool:
        """Check if running in development mode with auth bypass."""
        # Check configured auth mode
        if self.auth_mode == "development":
            return True
        
        # Check for development headers
        if request.headers.get('X-Development-Mode') == 'true':
            return True
        
        # Check for local development with skip auth header
        if (request.client and 
            request.client.host in ['127.0.0.1', 'localhost'] and
            request.headers.get('X-Skip-Auth') == 'dev'):
            return True
        
        # Check if running in development environment
        if self.config.get("development_mode", False):
            return True
        
        return False
    
    def _create_dev_user_context(self) -> Dict[str, Any]:
        """Create development user context for testing."""
        # Use configured default permissions for development
        default_permissions = self.config.get("default_permissions", ["extension:read", "extension:write"])
        
        return {
            'user_id': 'dev-user',
            'tenant_id': 'dev-tenant',
            'roles': ['admin', 'user'],
            'permissions': default_permissions,
            'token_type': 'development'
        }
    
    def has_permission(self, user_context: Dict[str, Any], permission: str, extension_name: Optional[str] = None) -> bool:
        """Check if user has required permission using the enhanced permission system."""
        try:
            # Import here to avoid circular imports
            from .extension_permissions import has_extension_permission, ExtensionPermission
            from .extension_rbac import check_extension_role_permission
            from .extension_tenant_access import check_tenant_extension_access
            
            # Try to convert string permission to ExtensionPermission enum
            try:
                ext_permission = ExtensionPermission(permission)
            except ValueError:
                # Fallback to legacy permission checking for non-extension permissions
                return self._has_legacy_permission(user_context, permission)
            
            # Check using the enhanced permission system
            # 1. Check role-based permissions
            if check_extension_role_permission(user_context, ext_permission, extension_name):
                return True
            
            # 2. Check tenant-specific access
            if extension_name and check_tenant_extension_access(user_context, extension_name, ext_permission):
                return True
            
            # 3. Check direct permission grants
            if has_extension_permission(user_context, ext_permission, extension_name):
                return True
            
            # 4. Fallback to legacy permission checking
            return self._has_legacy_permission(user_context, permission, extension_name)
            
        except Exception as e:
            logger.error(f"Error checking permission {permission}: {e}")
            # Fallback to legacy permission checking on error
            return self._has_legacy_permission(user_context, permission, extension_name)
    
    def _has_legacy_permission(self, user_context: Dict[str, Any], permission: str, extension_name: Optional[str] = None) -> bool:
        """Legacy permission checking for backward compatibility."""
        user_permissions = user_context.get('permissions', [])
        user_roles = user_context.get('roles', [])
        
        # Admin users and services have all permissions
        if 'admin' in user_roles or 'extension:*' in user_permissions:
            return True
        
        # Check specific permission formats
        extension_permissions = [
            f'extension:{permission}',
            f'extensions:{permission}',
            permission
        ]
        
        # Add extension-specific permission if extension name provided
        if extension_name:
            extension_permissions.extend([
                f'extension:{extension_name}:{permission}',
                f'extensions:{extension_name}:{permission}'
            ])
        
        return any(perm in user_permissions for perm in extension_permissions)
    
    def require_permission(self, permission: str):
        """Dependency to require specific permission."""
        async def permission_checker(
            user_context: Dict[str, Any] = Depends(self.authenticate_extension_request)
        ) -> Dict[str, Any]:
            if not self.has_permission(user_context, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required: {permission}"
                )
            return user_context
        
        return permission_checker


# Global extension authentication manager (will be initialized with config)
extension_auth_manager = None

def get_extension_auth_manager() -> ExtensionAuthManager:
    """Get or create the global extension authentication manager."""
    global extension_auth_manager
    if extension_auth_manager is None:
        from server.config import settings
        extension_auth_manager = ExtensionAuthManager(settings.get_extension_auth_config())
    return extension_auth_manager

# Enhanced convenience dependencies using the new permission system
async def require_extension_read(
    extension_name: Optional[str] = None,
    user_context: Dict[str, Any] = Depends(lambda: get_extension_auth_manager().authenticate_extension_request)
) -> Dict[str, Any]:
    """Require read permission for extension APIs with enhanced checking."""
    from .extension_permissions import require_extension_permission, ExtensionPermission
    
    # Use the enhanced permission system
    permission_checker = require_extension_permission(ExtensionPermission.READ, extension_name)
    return await permission_checker(user_context)

async def require_extension_write(
    extension_name: Optional[str] = None,
    user_context: Dict[str, Any] = Depends(lambda: get_extension_auth_manager().authenticate_extension_request)
) -> Dict[str, Any]:
    """Require write permission for extension APIs with enhanced checking."""
    from .extension_permissions import require_extension_permission, ExtensionPermission
    
    # Use the enhanced permission system
    permission_checker = require_extension_permission(ExtensionPermission.WRITE, extension_name)
    return await permission_checker(user_context)

async def require_extension_admin(
    extension_name: Optional[str] = None,
    user_context: Dict[str, Any] = Depends(lambda: get_extension_auth_manager().authenticate_extension_request)
) -> Dict[str, Any]:
    """Require admin permission for extension APIs with enhanced checking."""
    from .extension_permissions import require_extension_permission, ExtensionPermission
    
    # Use the enhanced permission system
    permission_checker = require_extension_permission(ExtensionPermission.ADMIN, extension_name)
    return await permission_checker(user_context)

async def require_background_tasks(
    extension_name: Optional[str] = None,
    user_context: Dict[str, Any] = Depends(lambda: get_extension_auth_manager().authenticate_extension_request)
) -> Dict[str, Any]:
    """Require background tasks permission with enhanced checking."""
    from .extension_permissions import require_extension_permission, ExtensionPermission
    
    # Use the enhanced permission system
    permission_checker = require_extension_permission(ExtensionPermission.BACKGROUND_TASKS, extension_name)
    return await permission_checker(user_context)

# Additional enhanced permission dependencies
async def require_extension_configure(
    extension_name: Optional[str] = None,
    user_context: Dict[str, Any] = Depends(lambda: get_extension_auth_manager().authenticate_extension_request)
) -> Dict[str, Any]:
    """Require configure permission for extension APIs."""
    from .extension_permissions import require_extension_permission, ExtensionPermission
    
    permission_checker = require_extension_permission(ExtensionPermission.CONFIGURE, extension_name)
    return await permission_checker(user_context)

async def require_extension_install(
    user_context: Dict[str, Any] = Depends(lambda: get_extension_auth_manager().authenticate_extension_request)
) -> Dict[str, Any]:
    """Require install permission for extension management."""
    from .extension_permissions import require_extension_permission, ExtensionPermission
    
    permission_checker = require_extension_permission(ExtensionPermission.INSTALL)
    return await permission_checker(user_context)

async def require_extension_health(
    extension_name: Optional[str] = None,
    user_context: Dict[str, Any] = Depends(lambda: get_extension_auth_manager().authenticate_extension_request)
) -> Dict[str, Any]:
    """Require health monitoring permission for extensions."""
    from .extension_permissions import require_extension_permission, ExtensionPermission
    
    permission_checker = require_extension_permission(ExtensionPermission.HEALTH, extension_name)
    return await permission_checker(user_context)

async def require_extension_metrics(
    extension_name: Optional[str] = None,
    user_context: Dict[str, Any] = Depends(lambda: get_extension_auth_manager().authenticate_extension_request)
) -> Dict[str, Any]:
    """Require metrics access permission for extensions."""
    from .extension_permissions import require_extension_permission, ExtensionPermission
    
    permission_checker = require_extension_permission(ExtensionPermission.METRICS, extension_name)
    return await permission_checker(user_context)

# Tenant-aware permission dependencies
def require_tenant_extension_access(extension_name: str, required_permission: Optional[str] = None):
    """Require tenant-specific access to an extension."""
    async def dependency(
        user_context: Dict[str, Any] = Depends(lambda: get_extension_auth_manager().authenticate_extension_request)
    ) -> Dict[str, Any]:
        from .extension_tenant_access import check_tenant_extension_access
        from .extension_permissions import ExtensionPermission
        
        # Convert permission string to enum if provided
        permission_enum = None
        if required_permission:
            try:
                permission_enum = ExtensionPermission(required_permission)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid permission: {required_permission}")
        
        # Check tenant access
        if not check_tenant_extension_access(user_context, extension_name, permission_enum):
            raise HTTPException(
                status_code=403,
                detail=f"Tenant access denied to extension {extension_name}"
            )
        
        return user_context
    
    return dependency