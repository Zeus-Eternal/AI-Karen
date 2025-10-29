"""
Extension debugging endpoints for authentication and health monitoring.
Provides detailed debugging information for troubleshooting extension issues.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

from server.extension_dev_auth import ExtensionDevAuth
from server.extension_health_monitor import ExtensionHealthMonitor

logger = logging.getLogger(__name__)

class AuthDebugInfo(BaseModel):
    """Authentication debug information model."""
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    token_type: Optional[str] = None
    roles: List[str] = []
    permissions: List[str] = []
    token_valid: bool = False
    token_expired: bool = False
    token_expires_at: Optional[datetime] = None
    authentication_method: Optional[str] = None
    request_headers: Dict[str, str] = {}
    debug_mode: bool = False

class ExtensionDebugInfo(BaseModel):
    """Extension debug information model."""
    name: str
    status: str
    health_status: str
    last_health_check: Optional[datetime] = None
    failure_count: int = 0
    capabilities: Dict[str, Any] = {}
    endpoints: List[str] = []
    background_tasks: List[Dict[str, Any]] = []
    error_history: List[Dict[str, Any]] = []

def create_extension_debug_router(
    dev_auth: ExtensionDevAuth,
    health_monitor: Optional[ExtensionHealthMonitor] = None
) -> APIRouter:
    """Create extension debugging router."""
    
    router = APIRouter(prefix="/api/debug/extensions", tags=["extension-debug"])

    @router.get("/auth/status")
    async def get_auth_debug_status(
        request: Request,
        include_headers: bool = Query(False, description="Include request headers in response")
    ) -> AuthDebugInfo:
        """Get detailed authentication status for debugging."""
        try:
            # Extract authentication information
            auth_info = AuthDebugInfo()
            
            # Check for authorization header
            auth_header = request.headers.get("authorization")
            if auth_header:
                auth_info.authentication_method = "bearer_token"
                
                # Try to validate token
                try:
                    user_context = await dev_auth.authenticate_request(request)
                    auth_info.user_id = user_context.get("user_id")
                    auth_info.tenant_id = user_context.get("tenant_id")
                    auth_info.token_type = user_context.get("token_type")
                    auth_info.roles = user_context.get("roles", [])
                    auth_info.permissions = user_context.get("permissions", [])
                    auth_info.token_valid = True
                    
                    # Check token expiration
                    if auth_info.token_type != "development":
                        token_payload = dev_auth._decode_token_payload(auth_header.replace("Bearer ", ""))
                        if token_payload and "exp" in token_payload:
                            auth_info.token_expires_at = datetime.fromtimestamp(token_payload["exp"])
                            auth_info.token_expired = datetime.utcnow() > auth_info.token_expires_at
                    
                except Exception as e:
                    logger.debug(f"Token validation failed: {e}")
                    auth_info.token_valid = False
                    auth_info.token_expired = True
            
            # Check for development mode
            auth_info.debug_mode = dev_auth._is_development_mode(request)
            if auth_info.debug_mode and not auth_header:
                auth_info.authentication_method = "development_bypass"
                auth_info.token_valid = True
            
            # Include headers if requested
            if include_headers:
                auth_info.request_headers = dict(request.headers)
            
            return auth_info
            
        except Exception as e:
            logger.error(f"Error getting auth debug status: {e}")
            raise HTTPException(status_code=500, detail=f"Debug status error: {str(e)}")

    @router.get("/auth/validate")
    async def validate_auth_token(
        request: Request,
        token: Optional[str] = Query(None, description="Token to validate (optional)")
    ) -> Dict[str, Any]:
        """Validate authentication token and return detailed information."""
        try:
            # Use provided token or extract from headers
            auth_token = token
            if not auth_token:
                auth_header = request.headers.get("authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    auth_token = auth_header.replace("Bearer ", "")
            
            if not auth_token:
                return {
                    "valid": False,
                    "error": "No token provided",
                    "debug_info": {
                        "development_mode": dev_auth._is_development_mode(request),
                        "request_ip": request.client.host if request.client else "unknown"
                    }
                }
            
            # Validate token
            try:
                payload = dev_auth._decode_token_payload(auth_token)
                
                validation_result = {
                    "valid": True,
                    "payload": payload,
                    "token_type": payload.get("token_type", "access"),
                    "user_id": payload.get("user_id"),
                    "tenant_id": payload.get("tenant_id"),
                    "roles": payload.get("roles", []),
                    "permissions": payload.get("permissions", []),
                    "issued_at": datetime.fromtimestamp(payload["iat"]) if "iat" in payload else None,
                    "expires_at": datetime.fromtimestamp(payload["exp"]) if "exp" in payload else None,
                    "is_expired": False
                }
                
                # Check expiration
                if "exp" in payload:
                    validation_result["is_expired"] = datetime.utcnow() > datetime.fromtimestamp(payload["exp"])
                
                return validation_result
                
            except Exception as e:
                return {
                    "valid": False,
                    "error": str(e),
                    "token_preview": auth_token[:20] + "..." if len(auth_token) > 20 else auth_token,
                    "debug_info": {
                        "development_mode": dev_auth._is_development_mode(request),
                        "error_type": type(e).__name__
                    }
                }
                
        except Exception as e:
            logger.error(f"Error validating auth token: {e}")
            raise HTTPException(status_code=500, detail=f"Token validation error: {str(e)}")

    @router.get("/health/detailed")
    async def get_detailed_health_status(
        request: Request,
        extension_name: Optional[str] = Query(None, description="Specific extension to check")
    ) -> Dict[str, Any]:
        """Get detailed health status for extensions."""
        try:
            if not health_monitor:
                return {
                    "error": "Health monitor not available",
                    "extensions": {},
                    "overall_health": "unknown"
                }
            
            # Get overall health status
            health_status = health_monitor.get_service_status()
            
            # Add detailed information for each extension
            detailed_extensions = {}
            for service_name, service_info in health_status.get("services", {}).items():
                if extension_name and service_name != extension_name:
                    continue
                
                detailed_info = {
                    **service_info,
                    "debug_info": {
                        "last_error": None,
                        "recovery_attempts": 0,
                        "uptime": None
                    }
                }
                
                # Add extension-specific debug information
                if hasattr(health_monitor, 'get_extension_debug_info'):
                    debug_info = health_monitor.get_extension_debug_info(service_name)
                    detailed_info["debug_info"].update(debug_info)
                
                detailed_extensions[service_name] = detailed_info
            
            return {
                "overall_health": health_status.get("overall_health", "unknown"),
                "monitoring_active": health_status.get("monitoring_active", False),
                "extensions": detailed_extensions,
                "timestamp": datetime.utcnow().isoformat(),
                "request_info": {
                    "client_ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown")
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed health status: {e}")
            raise HTTPException(status_code=500, detail=f"Health status error: {str(e)}")

    @router.get("/extensions/{extension_name}/debug")
    async def get_extension_debug_info(
        extension_name: str,
        request: Request
    ) -> ExtensionDebugInfo:
        """Get detailed debug information for specific extension."""
        try:
            # This would integrate with the extension manager
            # For now, return mock debug information
            debug_info = ExtensionDebugInfo(
                name=extension_name,
                status="active",
                health_status="healthy",
                last_health_check=datetime.utcnow(),
                failure_count=0,
                capabilities={
                    "api_endpoints": True,
                    "background_tasks": True,
                    "webhooks": False
                },
                endpoints=[
                    f"/api/extensions/{extension_name}/status",
                    f"/api/extensions/{extension_name}/config"
                ],
                background_tasks=[],
                error_history=[]
            )
            
            return debug_info
            
        except Exception as e:
            logger.error(f"Error getting extension debug info for {extension_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Extension debug error: {str(e)}")

    @router.get("/requests/trace")
    async def get_request_trace(
        request: Request,
        limit: int = Query(50, description="Number of recent requests to return")
    ) -> Dict[str, Any]:
        """Get trace information for recent extension API requests."""
        try:
            # This would integrate with request logging middleware
            # For now, return mock trace information
            traces = []
            
            for i in range(min(limit, 10)):  # Mock data
                trace = {
                    "request_id": f"req_{i}_{datetime.utcnow().timestamp()}",
                    "timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                    "method": "GET",
                    "path": f"/api/extensions/example/status",
                    "status_code": 200 if i % 5 != 0 else 403,
                    "response_time_ms": 150 + (i * 10),
                    "user_id": "debug-user",
                    "auth_method": "bearer_token",
                    "error": "Authentication failed" if i % 5 == 0 else None
                }
                traces.append(trace)
            
            return {
                "traces": traces,
                "total_count": len(traces),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting request trace: {e}")
            raise HTTPException(status_code=500, detail=f"Request trace error: {str(e)}")

    return router

# Utility functions for debugging
def format_debug_response(data: Dict[str, Any], pretty: bool = True) -> str:
    """Format debug response for display."""
    if pretty:
        return json.dumps(data, indent=2, default=str)
    return json.dumps(data, default=str)

def create_debug_summary(auth_info: AuthDebugInfo, health_info: Dict[str, Any]) -> Dict[str, Any]:
    """Create summary of debug information."""
    return {
        "authentication": {
            "status": "valid" if auth_info.token_valid else "invalid",
            "method": auth_info.authentication_method,
            "user": auth_info.user_id,
            "debug_mode": auth_info.debug_mode
        },
        "health": {
            "overall": health_info.get("overall_health", "unknown"),
            "services_count": len(health_info.get("extensions", {})),
            "monitoring_active": health_info.get("monitoring_active", False)
        },
        "timestamp": datetime.utcnow().isoformat()
    }