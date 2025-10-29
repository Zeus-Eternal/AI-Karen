"""
Secure Extension Example.

This extension demonstrates the security features and sandboxing capabilities
of the Kari Extensions System.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.extensions.base import BaseExtension
from src.extensions.security_decorators import (
    require_permission,
    require_permissions,
    rate_limit,
    audit_log,
    security_monitor,
    SecurityContext,
    secure_temp_file,
    secure_temp_dir
)

logger = logging.getLogger(__name__)


class SecurityTestRequest(BaseModel):
    """Request model for security tests."""
    test_type: str
    parameters: Dict[str, Any] = {}


class SecurityTestResponse(BaseModel):
    """Response model for security tests."""
    success: bool
    message: str
    details: Dict[str, Any] = {}


class SecureExtension(BaseExtension):
    """
    Example extension demonstrating security features.
    
    This extension shows how to:
    - Use permission decorators
    - Implement secure file operations
    - Handle network access with security checks
    - Monitor resource usage
    - Use the security context manager
    """
    
    async def _initialize(self) -> None:
        """Initialize the secure extension."""
        self.logger.info("Initializing Secure Extension")
        
        # Check our permissions
        permissions = self.get_permissions()
        self.logger.info(f"Extension permissions: {permissions}")
        
        # Check resource limits
        if self.is_within_limits():
            self.logger.info("Extension is within resource limits")
        else:
            self.logger.warning("Extension may be exceeding resource limits")
        
        self.logger.info("Secure Extension initialized successfully")
    
    async def _shutdown(self) -> None:
        """Shutdown the secure extension."""
        self.logger.info("Shutting down Secure Extension")
    
    def create_api_router(self) -> Optional[APIRouter]:
        """Create API router with security demonstrations."""
        router = APIRouter(prefix="/security", tags=["security"])
        
        @router.get("/status")
        @require_permission('data:read')
        @audit_log('security_status_check')
        async def get_security_status():
            """Get security status for this extension."""
            try:
                status = self.get_security_status()
                resource_usage = self.get_resource_usage()
                
                return {
                    "extension": self.manifest.name,
                    "version": self.manifest.version,
                    "security_status": status,
                    "resource_usage": resource_usage,
                    "within_limits": self.is_within_limits(),
                    "permissions": self.get_permissions()
                }
            except Exception as e:
                self.logger.error(f"Error getting security status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.post("/test", response_model=SecurityTestResponse)
        @require_permission('data:write')
        @rate_limit(calls_per_minute=10)
        @audit_log('security_test', sensitive=True)
        @security_monitor
        async def test_security_feature(request: SecurityTestRequest):
            """Test various security features."""
            try:
                if request.test_type == "file_operations":
                    return await self._test_file_operations(request.parameters)
                elif request.test_type == "network_access":
                    return await self._test_network_access(request.parameters)
                elif request.test_type == "permission_check":
                    return await self._test_permission_check(request.parameters)
                elif request.test_type == "resource_usage":
                    return await self._test_resource_usage(request.parameters)
                elif request.test_type == "security_context":
                    return await self._test_security_context(request.parameters)
                else:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Unknown test type: {request.test_type}"
                    )
            except Exception as e:
                self.logger.error(f"Security test failed: {e}")
                return SecurityTestResponse(
                    success=False,
                    message=f"Test failed: {str(e)}",
                    details={"error": str(e)}
                )
        
        @router.get("/violations")
        @require_permission('system:logs')
        @audit_log('security_violations_access', sensitive=True)
        async def get_security_violations():
            """Get recent security violations."""
            try:
                if self.security_manager:
                    violations = self.security_manager.get_all_security_violations(
                        extension_name=self.manifest.name,
                        hours=24
                    )
                    return {
                        "extension": self.manifest.name,
                        "violations": violations,
                        "count": len(violations)
                    }
                else:
                    return {"error": "Security manager not available"}
            except Exception as e:
                self.logger.error(f"Error getting violations: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        return router
    
    @require_permission('system:files')
    @audit_log('file_operations_test')
    async def _test_file_operations(self, parameters: Dict[str, Any]) -> SecurityTestResponse:
        """Test secure file operations."""
        try:
            with SecurityContext(self.manifest.name, ['system:files']) as ctx:
                # Create a temporary file
                temp_file = ctx.create_temp_file('.txt')
                
                # Write some test data
                test_data = parameters.get('data', 'Hello, secure world!')
                ctx.write_file(temp_file, test_data.encode())
                
                # Read it back
                read_data = ctx.read_file(temp_file)
                
                return SecurityTestResponse(
                    success=True,
                    message="File operations test completed successfully",
                    details={
                        "temp_file": temp_file,
                        "data_written": len(test_data),
                        "data_read": len(read_data),
                        "data_matches": test_data.encode() == read_data
                    }
                )
        except Exception as e:
            return SecurityTestResponse(
                success=False,
                message=f"File operations test failed: {str(e)}",
                details={"error": str(e)}
            )
    
    @require_permission('network:external')
    @audit_log('network_access_test')
    async def _test_network_access(self, parameters: Dict[str, Any]) -> SecurityTestResponse:
        """Test secure network access."""
        try:
            url = parameters.get('url', 'https://httpbin.org/json')
            
            # Use the secure HTTP request method
            response_data = await self.secure_http_request(url)
            
            return SecurityTestResponse(
                success=True,
                message="Network access test completed successfully",
                details={
                    "url": url,
                    "response_received": response_data is not None,
                    "response_type": type(response_data).__name__
                }
            )
        except Exception as e:
            return SecurityTestResponse(
                success=False,
                message=f"Network access test failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _test_permission_check(self, parameters: Dict[str, Any]) -> SecurityTestResponse:
        """Test permission checking."""
        try:
            permission = parameters.get('permission', 'data:read')
            has_permission = self.check_permission(permission)
            
            all_permissions = self.get_permissions()
            
            return SecurityTestResponse(
                success=True,
                message="Permission check test completed successfully",
                details={
                    "tested_permission": permission,
                    "has_permission": has_permission,
                    "all_permissions": list(all_permissions)
                }
            )
        except Exception as e:
            return SecurityTestResponse(
                success=False,
                message=f"Permission check test failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _test_resource_usage(self, parameters: Dict[str, Any]) -> SecurityTestResponse:
        """Test resource usage monitoring."""
        try:
            resource_usage = self.get_resource_usage()
            within_limits = self.is_within_limits()
            security_status = self.get_security_status()
            
            return SecurityTestResponse(
                success=True,
                message="Resource usage test completed successfully",
                details={
                    "resource_usage": resource_usage,
                    "within_limits": within_limits,
                    "resource_limits_check": security_status.get('resource_limits_check', {}),
                    "uptime_seconds": resource_usage.get('uptime_seconds', 0) if resource_usage else 0
                }
            )
        except Exception as e:
            return SecurityTestResponse(
                success=False,
                message=f"Resource usage test failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _test_security_context(self, parameters: Dict[str, Any]) -> SecurityTestResponse:
        """Test security context manager."""
        try:
            required_permissions = parameters.get('permissions', ['data:read', 'system:files'])
            
            with SecurityContext(self.manifest.name, required_permissions) as ctx:
                # Create temporary files and directories
                temp_file = ctx.create_temp_file('.test')
                temp_dir = ctx.create_temp_dir()
                
                # Write some data
                test_data = b"Security context test data"
                ctx.write_file(temp_file, test_data)
                
                # Read it back
                read_data = ctx.read_file(temp_file)
                
                return SecurityTestResponse(
                    success=True,
                    message="Security context test completed successfully",
                    details={
                        "required_permissions": required_permissions,
                        "temp_file_created": temp_file,
                        "temp_dir_created": temp_dir,
                        "data_written": len(test_data),
                        "data_read": len(read_data),
                        "data_matches": test_data == read_data
                    }
                )
        except Exception as e:
            return SecurityTestResponse(
                success=False,
                message=f"Security context test failed: {str(e)}",
                details={"error": str(e)}
            )
    
    @require_permissions(['data:read', 'system:logs'])
    @rate_limit(calls_per_minute=5)
    @audit_log('security_monitoring', sensitive=False)
    async def monitor_security_status(self) -> Dict[str, Any]:
        """Monitor security status (called by background task)."""
        try:
            self.logger.info("Running security monitoring")
            
            # Get current security status
            security_status = self.get_security_status()
            resource_usage = self.get_resource_usage()
            within_limits = self.is_within_limits()
            
            # Log any issues
            if not within_limits:
                self.logger.warning("Extension is exceeding resource limits")
            
            if security_status.get('recent_violations'):
                violation_count = len(security_status['recent_violations'])
                self.logger.warning(f"Extension has {violation_count} recent security violations")
            
            monitoring_result = {
                "timestamp": asyncio.get_event_loop().time(),
                "security_healthy": len(security_status.get('recent_violations', [])) == 0,
                "resource_healthy": within_limits,
                "resource_usage": resource_usage,
                "violation_count": len(security_status.get('recent_violations', []))
            }
            
            self.logger.info(f"Security monitoring completed: {monitoring_result}")
            return monitoring_result
            
        except Exception as e:
            self.logger.error(f"Security monitoring failed: {e}")
            return {
                "timestamp": asyncio.get_event_loop().time(),
                "error": str(e),
                "security_healthy": False,
                "resource_healthy": False
            }
    
    def create_background_tasks(self) -> List[Dict[str, Any]]:
        """Create background tasks for security monitoring."""
        tasks = super().create_background_tasks()
        
        # Add custom security monitoring task
        tasks.append({
            'name': 'security_status_check',
            'schedule': '*/10 * * * *',  # Every 10 minutes
            'function': 'monitor_security_status',
            'description': 'Check security status and resource usage',
            'extension': self.manifest.name
        })
        
        return tasks
    
    def create_ui_components(self) -> Dict[str, Any]:
        """Create UI components for security dashboard."""
        components = super().create_ui_components()
        
        # Add security-specific UI components
        components['security_widgets'] = [
            {
                'name': 'Permission Status',
                'type': 'status_card',
                'data_source': '/api/security/status',
                'refresh_interval': 30
            },
            {
                'name': 'Resource Usage',
                'type': 'chart',
                'data_source': '/api/security/status',
                'chart_type': 'gauge'
            },
            {
                'name': 'Security Violations',
                'type': 'table',
                'data_source': '/api/security/violations',
                'refresh_interval': 60
            }
        ]
        
        return components


# Background task functions (called by the background task manager)
async def monitor_security():
    """Background task function for security monitoring."""
    # This would be called by the background task manager
    # For now, it's a placeholder that logs the monitoring attempt
    logger.info("Security monitoring background task executed")
    return {"status": "completed", "timestamp": asyncio.get_event_loop().time()}


# Export the extension class
Extension = SecureExtension