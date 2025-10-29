"""
API endpoints for extension environment configuration management.
Provides REST API for configuration CRUD operations, validation, and hot-reload.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
from enum import Enum

from .extension_environment_config import (
    Environment,
    ExtensionEnvironmentConfig,
    get_config_manager,
    get_current_extension_config
)
from .extension_config_validator import (
    validate_extension_config,
    run_extension_health_checks
)
from .extension_config_hot_reload import (
    get_hot_reloader,
    reload_extension_config,
    ReloadTrigger
)

logger = logging.getLogger(__name__)


class ConfigUpdateRequest(BaseModel):
    """Request model for configuration updates."""
    auth_enabled: Optional[bool] = None
    jwt_algorithm: Optional[str] = None
    access_token_expire_minutes: Optional[int] = None
    service_token_expire_minutes: Optional[int] = None
    auth_mode: Optional[str] = None
    dev_bypass_enabled: Optional[bool] = None
    require_https: Optional[bool] = None
    token_blacklist_enabled: Optional[bool] = None
    max_failed_attempts: Optional[int] = None
    lockout_duration_minutes: Optional[int] = None
    audit_logging_enabled: Optional[bool] = None
    rate_limit_per_minute: Optional[int] = None
    burst_limit: Optional[int] = None
    enable_rate_limiting: Optional[bool] = None
    default_permissions: Optional[List[str]] = None
    admin_permissions: Optional[List[str]] = None
    service_permissions: Optional[List[str]] = None
    health_check_enabled: Optional[bool] = None
    health_check_interval_seconds: Optional[int] = None
    health_check_timeout_seconds: Optional[int] = None
    log_level: Optional[str] = None
    enable_debug_logging: Optional[bool] = None
    log_sensitive_data: Optional[bool] = None


class CredentialRequest(BaseModel):
    """Request model for credential operations."""
    name: str = Field(..., description="Credential name")
    value: Optional[str] = Field(None, description="Credential value (for store operations)")
    environment: Optional[str] = Field(None, description="Environment scope")
    rotation_interval_days: Optional[int] = Field(None, description="Auto-rotation interval in days")
    description: Optional[str] = Field(None, description="Credential description")


class ReloadRequest(BaseModel):
    """Request model for configuration reload."""
    environment: Optional[str] = Field(None, description="Environment to reload (current if not specified)")
    force: bool = Field(False, description="Force reload even if no changes detected")


def create_extension_config_router() -> APIRouter:
    """Create the extension configuration API router."""
    
    router = APIRouter(prefix="/api/extension-config", tags=["extension-config"])
    
    @router.get("/")
    async def get_current_config() -> Dict[str, Any]:
        """Get current extension configuration."""
        try:
            config = get_current_extension_config()
            config_dict = {
                'environment': config.environment.value,
                'auth_enabled': config.auth_enabled,
                'jwt_algorithm': config.jwt_algorithm,
                'access_token_expire_minutes': config.access_token_expire_minutes,
                'service_token_expire_minutes': config.service_token_expire_minutes,
                'auth_mode': config.auth_mode,
                'dev_bypass_enabled': config.dev_bypass_enabled,
                'require_https': config.require_https,
                'token_blacklist_enabled': config.token_blacklist_enabled,
                'max_failed_attempts': config.max_failed_attempts,
                'lockout_duration_minutes': config.lockout_duration_minutes,
                'audit_logging_enabled': config.audit_logging_enabled,
                'rate_limit_per_minute': config.rate_limit_per_minute,
                'burst_limit': config.burst_limit,
                'enable_rate_limiting': config.enable_rate_limiting,
                'default_permissions': config.default_permissions,
                'admin_permissions': config.admin_permissions,
                'service_permissions': config.service_permissions,
                'health_check_enabled': config.health_check_enabled,
                'health_check_interval_seconds': config.health_check_interval_seconds,
                'health_check_timeout_seconds': config.health_check_timeout_seconds,
                'log_level': config.log_level,
                'enable_debug_logging': config.enable_debug_logging,
                'log_sensitive_data': config.log_sensitive_data,
                # Exclude sensitive data
                'secret_key': '***REDACTED***',
                'api_key': '***REDACTED***'
            }
            
            return {
                'success': True,
                'config': config_dict,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get current config: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get configuration: {e}")
    
    @router.get("/{environment}")
    async def get_environment_config(environment: str) -> Dict[str, Any]:
        """Get configuration for a specific environment."""
        try:
            try:
                env = Environment(environment.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid environment: {environment}")
            
            config_manager = get_config_manager()
            config = config_manager.get_config(env)
            
            config_dict = {
                'environment': config.environment.value,
                'auth_enabled': config.auth_enabled,
                'jwt_algorithm': config.jwt_algorithm,
                'access_token_expire_minutes': config.access_token_expire_minutes,
                'service_token_expire_minutes': config.service_token_expire_minutes,
                'auth_mode': config.auth_mode,
                'dev_bypass_enabled': config.dev_bypass_enabled,
                'require_https': config.require_https,
                'token_blacklist_enabled': config.token_blacklist_enabled,
                'max_failed_attempts': config.max_failed_attempts,
                'lockout_duration_minutes': config.lockout_duration_minutes,
                'audit_logging_enabled': config.audit_logging_enabled,
                'rate_limit_per_minute': config.rate_limit_per_minute,
                'burst_limit': config.burst_limit,
                'enable_rate_limiting': config.enable_rate_limiting,
                'default_permissions': config.default_permissions,
                'admin_permissions': config.admin_permissions,
                'service_permissions': config.service_permissions,
                'health_check_enabled': config.health_check_enabled,
                'health_check_interval_seconds': config.health_check_interval_seconds,
                'health_check_timeout_seconds': config.health_check_timeout_seconds,
                'log_level': config.log_level,
                'enable_debug_logging': config.enable_debug_logging,
                'log_sensitive_data': config.log_sensitive_data,
                # Exclude sensitive data
                'secret_key': '***REDACTED***',
                'api_key': '***REDACTED***'
            }
            
            return {
                'success': True,
                'config': config_dict,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get config for {environment}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get configuration: {e}")
    
    @router.put("/{environment}")
    async def update_environment_config(
        environment: str,
        updates: ConfigUpdateRequest
    ) -> Dict[str, Any]:
        """Update configuration for a specific environment."""
        try:
            try:
                env = Environment(environment.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid environment: {environment}")
            
            config_manager = get_config_manager()
            
            # Convert updates to dict, excluding None values
            update_dict = {}
            for field, value in updates.dict().items():
                if value is not None:
                    update_dict[field] = value
            
            if not update_dict:
                raise HTTPException(status_code=400, detail="No updates provided")
            
            # Update configuration
            success = config_manager.update_config(env, update_dict, save_to_file=True)
            
            if not success:
                raise HTTPException(status_code=400, detail="Configuration update failed validation")
            
            # Get updated configuration
            updated_config = config_manager.get_config(env)
            
            return {
                'success': True,
                'message': f'Configuration updated for {environment}',
                'updated_fields': list(update_dict.keys()),
                'environment': env.value,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update config for {environment}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update configuration: {e}")
    
    @router.post("/validate")
    async def validate_config(environment: Optional[str] = None) -> Dict[str, Any]:
        """Validate extension configuration."""
        try:
            if environment:
                try:
                    env = Environment(environment.lower())
                    config_manager = get_config_manager()
                    config = config_manager.get_config(env)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid environment: {environment}")
            else:
                config = get_current_extension_config()
            
            validation_result = await validate_extension_config()
            return validation_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Validation failed: {e}")
    
    @router.get("/health/status")
    async def get_health_status() -> Dict[str, Any]:
        """Get comprehensive health status of configuration system."""
        try:
            health_result = await run_extension_health_checks()
            return health_result
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=500, detail=f"Health check failed: {e}")
    
    @router.post("/reload")
    async def reload_config(request: ReloadRequest) -> Dict[str, Any]:
        """Reload configuration from files."""
        try:
            environment = None
            if request.environment:
                try:
                    environment = Environment(request.environment.lower())
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid environment: {request.environment}")
            
            reload_result = await reload_extension_config(
                environment=environment,
                force=request.force
            )
            
            return {
                'success': reload_result.get('status') in ['success', 'rolled_back'],
                'reload_event': reload_result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Configuration reload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Reload failed: {e}")
    
    @router.get("/reload/history")
    async def get_reload_history(limit: int = Query(50, ge=1, le=200)) -> Dict[str, Any]:
        """Get configuration reload history."""
        try:
            hot_reloader = get_hot_reloader()
            history = hot_reloader.get_reload_history(limit)
            
            return {
                'success': True,
                'history': history,
                'count': len(history),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get reload history: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get reload history: {e}")
    
    @router.get("/snapshots/{environment}")
    async def get_config_snapshots(
        environment: str,
        limit: int = Query(10, ge=1, le=50)
    ) -> Dict[str, Any]:
        """Get configuration snapshots for an environment."""
        try:
            try:
                env = Environment(environment.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid environment: {environment}")
            
            hot_reloader = get_hot_reloader()
            snapshots = hot_reloader.get_snapshots(env, limit)
            
            return {
                'success': True,
                'environment': env.value,
                'snapshots': snapshots,
                'count': len(snapshots),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get snapshots for {environment}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get snapshots: {e}")
    
    @router.get("/credentials")
    async def list_credentials(environment: Optional[str] = None) -> Dict[str, Any]:
        """List stored credentials (without values)."""
        try:
            config_manager = get_config_manager()
            credentials = config_manager.credentials_manager.list_credentials(environment)
            
            return {
                'success': True,
                'credentials': credentials,
                'count': len(credentials),
                'environment_filter': environment,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to list credentials: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list credentials: {e}")
    
    @router.post("/credentials")
    async def store_credential(request: CredentialRequest) -> Dict[str, Any]:
        """Store a credential securely."""
        try:
            if not request.value:
                raise HTTPException(status_code=400, detail="Credential value is required")
            
            config_manager = get_config_manager()
            success = config_manager.credentials_manager.store_credential(
                name=request.name,
                value=request.value,
                environment=request.environment,
                rotation_interval_days=request.rotation_interval_days,
                description=request.description
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to store credential")
            
            return {
                'success': True,
                'message': f'Credential "{request.name}" stored successfully',
                'name': request.name,
                'environment': request.environment,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to store credential: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store credential: {e}")
    
    @router.post("/credentials/{name}/rotate")
    async def rotate_credential(name: str, new_value: Optional[str] = Body(None)) -> Dict[str, Any]:
        """Rotate a credential to a new value."""
        try:
            config_manager = get_config_manager()
            success = config_manager.credentials_manager.rotate_credential(name, new_value)
            
            if not success:
                raise HTTPException(status_code=404, detail=f"Credential '{name}' not found or rotation failed")
            
            return {
                'success': True,
                'message': f'Credential "{name}" rotated successfully',
                'name': name,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to rotate credential {name}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to rotate credential: {e}")
    
    @router.get("/status")
    async def get_system_status() -> Dict[str, Any]:
        """Get overall configuration system status."""
        try:
            config_manager = get_config_manager()
            hot_reloader = get_hot_reloader()
            
            # Get basic status
            config_health = config_manager.get_health_status()
            reload_status = hot_reloader.get_status()
            
            # Get validation status
            validation_result = await validate_extension_config()
            
            return {
                'success': True,
                'overall_status': config_health.get('status', 'unknown'),
                'current_environment': config_manager.current_environment.value,
                'config_health': config_health,
                'hot_reload_status': reload_status,
                'validation_status': {
                    'valid': validation_result.get('valid', False),
                    'total_issues': validation_result.get('total_issues', 0),
                    'critical_issues': validation_result.get('critical_issues', 0),
                    'error_issues': validation_result.get('error_issues', 0)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get system status: {e}")
    
    @router.get("/environments")
    async def list_environments() -> Dict[str, Any]:
        """List all supported environments."""
        try:
            config_manager = get_config_manager()
            
            environments = []
            for env in Environment:
                config = config_manager.get_config(env)
                validation_result = await validate_extension_config()
                
                environments.append({
                    'name': env.value,
                    'current': env == config_manager.current_environment,
                    'auth_mode': config.auth_mode,
                    'auth_enabled': config.auth_enabled,
                    'require_https': config.require_https,
                    'health_check_enabled': config.health_check_enabled,
                    'valid': validation_result.get('valid', False) if env == config_manager.current_environment else None
                })
            
            return {
                'success': True,
                'environments': environments,
                'current_environment': config_manager.current_environment.value,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to list environments: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list environments: {e}")
    
    return router


# Create the router instance
extension_config_router = create_extension_config_router()