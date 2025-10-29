"""
Development Authentication API Endpoints

Provides API endpoints for development authentication, mock user management,
and development configuration.

Requirements addressed:
- 6.3: Mock authentication for testing
- 6.4: Detailed logging for debugging extension issues
- 6.5: Environment-specific configuration adaptation
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field

from .extension_dev_auth import get_development_auth_manager, require_development_auth
from .extension_dev_config import get_development_config_manager

logger = logging.getLogger(__name__)

# Request/Response models
class MockAuthRequest(BaseModel):
    user_id: str = Field(..., description="Mock user ID to authenticate as")
    tenant_id: Optional[str] = Field(None, description="Optional tenant ID override")
    roles: Optional[List[str]] = Field(None, description="Optional roles override")
    permissions: Optional[List[str]] = Field(None, description="Optional permissions override")

class MockAuthResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: Dict[str, Any]
    dev_mode: bool = True

class DevelopmentStatusResponse(BaseModel):
    enabled: bool
    environment: str
    mock_users: int
    cached_tokens: int
    hot_reload_supported: bool
    config: Dict[str, Any]

class MockUserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    roles: List[str]
    permissions: List[str]
    tenant_id: str

class ConfigUpdateRequest(BaseModel):
    config_name: str = Field(..., description="Configuration section to update")
    updates: Dict[str, Any] = Field(..., description="Configuration updates")
    persist: bool = Field(True, description="Whether to persist changes to file")

def create_development_auth_router() -> APIRouter:
    """Create development authentication API router."""
    
    router = APIRouter(prefix="/api/dev/auth", tags=["development-auth"])
    
    @router.get("/status", response_model=DevelopmentStatusResponse)
    async def get_development_status(
        request: Request,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """Get development authentication status."""
        try:
            dev_auth = get_development_auth_manager()
            status = dev_auth.get_development_status()
            
            return DevelopmentStatusResponse(
                enabled=status["enabled"],
                environment=status["environment"],
                mock_users=status["mock_users"],
                cached_tokens=status["cached_tokens"],
                hot_reload_supported=status.get("hot_reload_support", False),
                config=status
            )
        
        except Exception as e:
            logger.error(f"Failed to get development status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get development status")
    
    @router.get("/users", response_model=List[MockUserResponse])
    async def list_mock_users(
        request: Request,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """List available mock users for development."""
        try:
            dev_auth = get_development_auth_manager()
            users = dev_auth.get_development_user_list()
            
            return [
                MockUserResponse(
                    user_id=user["user_id"],
                    name=user["name"],
                    email=user["email"],
                    roles=user["roles"],
                    permissions=user["permissions"],
                    tenant_id=user["tenant_id"]
                )
                for user in users
            ]
        
        except Exception as e:
            logger.error(f"Failed to list mock users: {e}")
            raise HTTPException(status_code=500, detail="Failed to list mock users")
    
    @router.post("/mock-login", response_model=MockAuthResponse)
    async def mock_login(
        request: MockAuthRequest,
        req: Request,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """Authenticate as a mock user for development."""
        try:
            dev_auth = get_development_auth_manager()
            
            # Create development token
            token = dev_auth.create_development_token(
                user_id=request.user_id,
                tenant_id=request.tenant_id,
                roles=request.roles,
                permissions=request.permissions
            )
            
            # Get user data
            users = dev_auth.get_development_user_list()
            user_data = next((u for u in users if u["user_id"] == request.user_id), None)
            
            if not user_data:
                raise HTTPException(status_code=404, detail=f"Mock user not found: {request.user_id}")
            
            return MockAuthResponse(
                access_token=token,
                token_type="Bearer",
                expires_in=24 * 3600,  # 24 hours
                user=user_data
            )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to perform mock login: {e}")
            raise HTTPException(status_code=500, detail="Mock login failed")
    
    @router.post("/create-token")
    async def create_development_token(
        user_id: str = Query(..., description="User ID for token"),
        scenario: Optional[str] = Query(None, description="Test scenario (expired_token, limited_permissions, etc.)"),
        req: Request = None,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """Create development token for specific user or test scenario."""
        try:
            dev_auth = get_development_auth_manager()
            
            if scenario:
                # Create token for specific test scenario
                token = dev_auth.create_test_scenario_token(scenario)
            else:
                # Create regular development token
                token = dev_auth.create_development_token(user_id)
            
            return {
                "access_token": token,
                "token_type": "Bearer",
                "user_id": user_id,
                "scenario": scenario,
                "dev_mode": True
            }
        
        except Exception as e:
            logger.error(f"Failed to create development token: {e}")
            raise HTTPException(status_code=500, detail="Failed to create development token")
    
    @router.post("/hot-reload-token")
    async def create_hot_reload_token(
        req: Request,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """Create special token for hot reload scenarios."""
        try:
            dev_auth = get_development_auth_manager()
            token = dev_auth.create_hot_reload_token()
            
            return {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": 300,  # 5 minutes
                "purpose": "hot_reload",
                "dev_mode": True
            }
        
        except Exception as e:
            logger.error(f"Failed to create hot reload token: {e}")
            raise HTTPException(status_code=500, detail="Failed to create hot reload token")
    
    @router.delete("/clear-cache")
    async def clear_development_cache(
        req: Request,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """Clear development authentication cache."""
        try:
            dev_auth = get_development_auth_manager()
            dev_auth.clear_development_cache()
            
            return {
                "message": "Development authentication cache cleared",
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Failed to clear development cache: {e}")
            raise HTTPException(status_code=500, detail="Failed to clear development cache")
    
    return router

def create_development_config_router() -> APIRouter:
    """Create development configuration API router."""
    
    router = APIRouter(prefix="/api/dev/config", tags=["development-config"])
    
    @router.get("/status")
    async def get_config_status(
        req: Request,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """Get development configuration status."""
        try:
            config_manager = get_development_config_manager()
            
            return {
                "environment_info": config_manager.get_environment_info(),
                "validation_errors": config_manager.validate_configuration(),
                "auth_config": config_manager.get_auth_config().__dict__,
                "server_config": config_manager.get_server_config().__dict__,
                "extension_config": config_manager.get_extension_config().__dict__
            }
        
        except Exception as e:
            logger.error(f"Failed to get config status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get config status")
    
    @router.get("/export")
    async def export_configuration(
        config_name: Optional[str] = Query(None, description="Specific config to export"),
        req: Request = None,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """Export development configuration."""
        try:
            config_manager = get_development_config_manager()
            config_data = config_manager.export_config(config_name)
            
            return {
                "config": config_data,
                "exported_at": req.headers.get("date") if req else None,
                "config_name": config_name
            }
        
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            raise HTTPException(status_code=500, detail="Failed to export configuration")
    
    @router.post("/update")
    async def update_configuration(
        request: ConfigUpdateRequest,
        req: Request,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """Update development configuration."""
        try:
            config_manager = get_development_config_manager()
            
            config_manager.update_config(
                request.config_name,
                request.updates,
                request.persist
            )
            
            return {
                "message": f"Configuration {request.config_name} updated successfully",
                "config_name": request.config_name,
                "persisted": request.persist,
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            raise HTTPException(status_code=500, detail="Failed to update configuration")
    
    @router.post("/reload")
    async def reload_configuration(
        config_name: Optional[str] = Query(None, description="Specific config to reload"),
        req: Request = None,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """Reload development configuration from files."""
        try:
            config_manager = get_development_config_manager()
            config_manager.reload_config(config_name)
            
            return {
                "message": f"Configuration {'all' if not config_name else config_name} reloaded successfully",
                "config_name": config_name,
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            raise HTTPException(status_code=500, detail="Failed to reload configuration")
    
    @router.post("/create-env-file")
    async def create_environment_file(
        req: Request,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """Create development environment file."""
        try:
            config_manager = get_development_config_manager()
            env_file_path = config_manager.create_development_environment_file()
            
            return {
                "message": "Development environment file created successfully",
                "file_path": env_file_path,
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Failed to create environment file: {e}")
            raise HTTPException(status_code=500, detail="Failed to create environment file")
    
    @router.get("/check-changes")
    async def check_configuration_changes(
        req: Request,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """Check for configuration file changes and reload if necessary."""
        try:
            config_manager = get_development_config_manager()
            changed_configs = config_manager.check_for_config_changes()
            
            return {
                "changed_configs": changed_configs,
                "changes_detected": len(changed_configs) > 0,
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Failed to check configuration changes: {e}")
            raise HTTPException(status_code=500, detail="Failed to check configuration changes")
    
    return router

def create_development_debug_router() -> APIRouter:
    """Create development debugging API router."""
    
    router = APIRouter(prefix="/api/dev/debug", tags=["development-debug"])
    
    @router.get("/environment")
    async def get_environment_info(
        req: Request,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """Get detailed environment information for debugging."""
        try:
            import os
            import sys
            from datetime import datetime
            
            config_manager = get_development_config_manager()
            dev_auth = get_development_auth_manager()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "environment": {
                    "python_version": sys.version,
                    "working_directory": os.getcwd(),
                    "environment_variables": {
                        key: value for key, value in os.environ.items()
                        if key.startswith(('EXTENSION_', 'KARI_', 'NODE_', 'DEBUG'))
                    }
                },
                "development_auth": dev_auth.get_development_status(),
                "configuration": config_manager.get_environment_info(),
                "request_info": {
                    "method": req.method,
                    "url": str(req.url),
                    "headers": dict(req.headers),
                    "client": req.client.host if req.client else None
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to get environment info: {e}")
            raise HTTPException(status_code=500, detail="Failed to get environment info")
    
    @router.post("/test-auth-flow")
    async def test_authentication_flow(
        user_id: str = Query("dev-user", description="User ID to test"),
        req: Request = None,
        user_context: Dict[str, Any] = Depends(require_development_auth)
    ):
        """Test complete authentication flow for debugging."""
        try:
            dev_auth = get_development_auth_manager()
            
            # Test token creation
            token = dev_auth.create_development_token(user_id)
            
            # Test token validation
            import jwt
            import os
            secret_key = os.getenv("EXTENSION_SECRET_KEY", "dev-extension-secret-key")
            
            try:
                payload = jwt.decode(token, secret_key, algorithms=["HS256"])
                token_valid = True
                token_payload = payload
            except Exception as e:
                token_valid = False
                token_payload = {"error": str(e)}
            
            # Test user context creation
            user_context_test = dev_auth.authenticate_development_request(req)
            
            return {
                "user_id": user_id,
                "token_created": bool(token),
                "token_length": len(token) if token else 0,
                "token_valid": token_valid,
                "token_payload": token_payload,
                "user_context": user_context_test,
                "test_passed": token_valid and bool(user_context_test),
                "timestamp": req.headers.get("date") if req else None
            }
        
        except Exception as e:
            logger.error(f"Failed to test authentication flow: {e}")
            return {
                "user_id": user_id,
                "test_passed": False,
                "error": str(e),
                "timestamp": req.headers.get("date") if req else None
            }
    
    return router

# Combined router factory
def create_development_api_router() -> APIRouter:
    """Create combined development API router."""
    
    main_router = APIRouter()
    
    # Add sub-routers
    main_router.include_router(create_development_auth_router())
    main_router.include_router(create_development_config_router())
    main_router.include_router(create_development_debug_router())
    
    return main_router