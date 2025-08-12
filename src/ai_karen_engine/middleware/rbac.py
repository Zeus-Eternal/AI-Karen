"""
RBAC (Role-Based Access Control) Middleware - Phase 4.1.c
Implements scope-based permissions with graceful fallbacks for development environments.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set

try:
    from fastapi import Request, HTTPException
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    # Graceful fallback for environments without FastAPI
    Request = None
    HTTPException = None
    JSONResponse = None
    FASTAPI_AVAILABLE = False

from ai_karen_engine.api_routes.unified_schemas import ErrorHandler, ErrorType

logger = logging.getLogger(__name__)

# Scope definitions according to design spec
VALID_SCOPES = {
    "chat:write",     # Permission to use copilot assistance
    "memory:read",    # Permission to search/query memory
    "memory:write",   # Permission to commit/update/delete memory
    "admin:read",     # Administrative read access
    "admin:write",    # Administrative write access
}

# Role to scope mappings (fallback when database is unavailable)
DEFAULT_ROLE_SCOPES = {
    "admin": {"chat:write", "memory:read", "memory:write", "admin:read", "admin:write"},
    "user": {"chat:write", "memory:read", "memory:write"},
    "readonly": {"memory:read"},
    "guest": set(),
}

class RBACError(Exception):
    """RBAC-specific error"""
    pass

class ScopeValidator:
    """Validates and manages scope-based permissions"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ScopeValidator")
    
    def validate_scope_format(self, scope: str) -> bool:
        """Validate scope format (service:action)"""
        if not scope or not isinstance(scope, str):
            return False
        
        if scope not in VALID_SCOPES:
            self.logger.warning(f"Invalid scope format: {scope}")
            return False
        
        return True
    
    def parse_required_scopes(self, scopes_header: Optional[str]) -> Set[str]:
        """Parse required scopes from header"""
        if not scopes_header:
            return set()
        
        scopes = {s.strip() for s in scopes_header.split(",") if s.strip()}
        
        # Validate each scope
        valid_scopes = set()
        for scope in scopes:
            if self.validate_scope_format(scope):
                valid_scopes.add(scope)
            else:
                self.logger.warning(f"Ignoring invalid scope: {scope}")
        
        return valid_scopes
    
    def get_user_scopes_from_roles(self, roles: List[str]) -> Set[str]:
        """Get user scopes based on roles (fallback method)"""
        user_scopes = set()
        
        for role in roles:
            role_scopes = DEFAULT_ROLE_SCOPES.get(role, set())
            user_scopes.update(role_scopes)
        
        return user_scopes
    
    def check_scope_permission(self, user_scopes: Set[str], required_scopes: Set[str]) -> bool:
        """Check if user has required scopes"""
        if not required_scopes:
            return True  # No scopes required
        
        return required_scopes.issubset(user_scopes)

class RBACMiddleware:
    """RBAC middleware for scope-based access control"""
    
    def __init__(self, development_mode: bool = False):
        self.development_mode = development_mode
        self.scope_validator = ScopeValidator()
        self.logger = logging.getLogger(f"{__name__}.RBACMiddleware")
    
    def get_correlation_id(self, request) -> str:
        """Extract or generate correlation ID"""
        if not request:
            return str(uuid.uuid4())
        
        if hasattr(request, 'headers'):
            return request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
        
        return str(uuid.uuid4())
    
    def create_rbac_error_response(self, request, message: str, status_code: int = 403):
        """Create standardized RBAC error response"""
        correlation_id = self.get_correlation_id(request)
        path = str(request.url.path) if request and hasattr(request, 'url') else "unknown"
        
        if status_code == 401:
            error_response = ErrorHandler.create_authentication_error_response(
                correlation_id=correlation_id,
                path=path,
                message=message
            )
        else:
            error_response = ErrorHandler.create_authorization_error_response(
                correlation_id=correlation_id,
                path=path,
                message=message
            )
        
        return error_response
    
    def log_security_incident(self, request, incident_type: str, details: Dict):
        """Log security incidents for audit purposes"""
        correlation_id = self.get_correlation_id(request)
        
        incident_log = {
            "incident_type": incident_type,
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path) if request and hasattr(request, 'url') else "unknown",
            "method": request.method if request and hasattr(request, 'method') else "unknown",
            "client_ip": request.client.host if request and hasattr(request, 'client') and request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown") if request and hasattr(request, 'headers') else "unknown",
            **details
        }
        
        self.logger.warning(
            f"Security incident: {incident_type}",
            extra=incident_log
        )
    
    async def check_authentication(self, request) -> Dict:
        """Check if request is authenticated"""
        if not request or not hasattr(request, 'state'):
            if self.development_mode:
                self.logger.debug("No request state, allowing in development mode")
                return {"user_id": "dev_user", "roles": ["admin"], "scopes": list(VALID_SCOPES)}
            else:
                raise RBACError("Authentication required")
        
        # Check if user is authenticated (set by auth middleware)
        user_id = getattr(request.state, 'user', None)
        if not user_id:
            if self.development_mode:
                self.logger.debug("No authenticated user, allowing in development mode")
                return {"user_id": "dev_user", "roles": ["admin"], "scopes": list(VALID_SCOPES)}
            else:
                raise RBACError("Authentication required")
        
        # Get user roles and scopes
        roles = getattr(request.state, 'roles', [])
        scopes = getattr(request.state, 'scopes', [])
        
        return {
            "user_id": user_id,
            "roles": roles,
            "scopes": scopes
        }
    
    async def validate_scopes(self, request, required_scopes: Set[str]) -> bool:
        """Validate user has required scopes"""
        try:
            auth_info = await self.check_authentication(request)
            user_scopes = set(auth_info.get("scopes", []))
            
            # If no scopes in auth info, derive from roles
            if not user_scopes:
                roles = auth_info.get("roles", [])
                user_scopes = self.scope_validator.get_user_scopes_from_roles(roles)
            
            # Check scope permissions
            has_permission = self.scope_validator.check_scope_permission(user_scopes, required_scopes)
            
            if not has_permission:
                # Log authorization failure
                self.log_security_incident(
                    request,
                    "authorization_failure",
                    {
                        "user_id": auth_info.get("user_id"),
                        "user_roles": auth_info.get("roles", []),
                        "user_scopes": list(user_scopes),
                        "required_scopes": list(required_scopes),
                        "reason": "insufficient_scopes"
                    }
                )
            
            return has_permission
            
        except RBACError as e:
            # Log authentication failure
            self.log_security_incident(
                request,
                "authentication_failure",
                {
                    "reason": str(e)
                }
            )
            return False
        except Exception as e:
            self.logger.error(f"RBAC validation error: {e}")
            
            if self.development_mode:
                self.logger.debug("RBAC error in development mode, allowing access")
                return True
            
            # Log system error
            self.log_security_incident(
                request,
                "rbac_system_error",
                {
                    "error": str(e)
                }
            )
            return False

# Global RBAC middleware instance
_rbac_middleware = None

def get_rbac_middleware(development_mode: bool = False) -> RBACMiddleware:
    """Get or create RBAC middleware instance"""
    global _rbac_middleware
    
    if _rbac_middleware is None:
        _rbac_middleware = RBACMiddleware(development_mode=development_mode)
    
    return _rbac_middleware

async def rbac_middleware(request, call_next):
    """FastAPI middleware for RBAC enforcement"""
    if not FASTAPI_AVAILABLE:
        logger.warning("FastAPI not available, skipping RBAC middleware")
        return await call_next(request)
    
    # Get RBAC middleware instance
    rbac = get_rbac_middleware(development_mode=True)  # TODO: Set based on environment
    
    # Parse required scopes from header
    scopes_header = request.headers.get("X-Required-Scopes")
    required_scopes = rbac.scope_validator.parse_required_scopes(scopes_header)
    
    # If no scopes required, proceed
    if not required_scopes:
        return await call_next(request)
    
    # Validate scopes
    has_permission = await rbac.validate_scopes(request, required_scopes)
    
    if not has_permission:
        # Determine if it's authentication or authorization error
        try:
            await rbac.check_authentication(request)
            # User is authenticated but lacks permissions
            error_response = rbac.create_rbac_error_response(
                request,
                f"Insufficient permissions. Required scopes: {', '.join(required_scopes)}",
                403
            )
            return JSONResponse(
                status_code=403,
                content=error_response.dict()
            )
        except RBACError:
            # User is not authenticated
            error_response = rbac.create_rbac_error_response(
                request,
                "Authentication required",
                401
            )
            return JSONResponse(
                status_code=401,
                content=error_response.dict()
            )
    
    # Add validated scopes to request state for downstream use
    if hasattr(request, 'state'):
        request.state.validated_scopes = required_scopes
    
    return await call_next(request)

# Decorator for endpoint-level scope checking
def require_scopes(*scopes: str):
    """Decorator to require specific scopes for an endpoint"""
    def decorator(func):
        # Store required scopes in function metadata
        func._required_scopes = set(scopes)
        return func
    return decorator

# Utility functions for manual scope checking
async def check_scope(request, scope: str) -> bool:
    """Check if current request has specific scope"""
    rbac = get_rbac_middleware()
    return await rbac.validate_scopes(request, {scope})

async def check_scopes(request, scopes: Set[str]) -> bool:
    """Check if current request has all specified scopes"""
    rbac = get_rbac_middleware()
    return await rbac.validate_scopes(request, scopes)

def get_user_scopes(request) -> Set[str]:
    """Get current user's scopes"""
    if not request or not hasattr(request, 'state'):
        return set()
    
    scopes = getattr(request.state, 'scopes', [])
    if scopes:
        return set(scopes)
    
    # Fallback to deriving from roles
    roles = getattr(request.state, 'roles', [])
    validator = ScopeValidator()
    return validator.get_user_scopes_from_roles(roles)

# Export public interface
__all__ = [
    "RBACMiddleware",
    "ScopeValidator", 
    "RBACError",
    "VALID_SCOPES",
    "DEFAULT_ROLE_SCOPES",
    "rbac_middleware",
    "require_scopes",
    "check_scope",
    "check_scopes",
    "get_user_scopes",
    "get_rbac_middleware"
]