# mypy: ignore-errors
"""
Token utility functions for extension authentication.
Provides convenient functions for common token operations.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import timedelta

logger = logging.getLogger(__name__)


async def create_user_session_tokens(
    user_id: str,
    tenant_id: str = "default",
    roles: List[str] = None,
    permissions: List[str] = None
) -> Dict[str, Any]:
    """Create complete token set for user session."""
    try:
        from server.security import get_extension_auth_manager
        
        auth_manager = get_extension_auth_manager()
        return await auth_manager.generate_user_token_pair(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles,
            permissions=permissions
        )
    except Exception as e:
        logger.error(f"Failed to create user session tokens: {e}")
        return {}


async def create_service_authentication_token(
    service_name: str,
    permissions: List[str] = None,
    expires_minutes: int = 30
) -> Optional[str]:
    """Create service-to-service authentication token."""
    try:
        from server.security import get_extension_auth_manager
        
        auth_manager = get_extension_auth_manager()
        return auth_manager.create_enhanced_service_token(
            service_name=service_name,
            permissions=permissions,
            expires_delta=timedelta(minutes=expires_minutes)
        )
    except Exception as e:
        logger.error(f"Failed to create service token for {service_name}: {e}")
        return None


async def create_background_task_authentication_token(
    task_name: str,
    user_id: Optional[str] = None,
    service_name: Optional[str] = None,
    permissions: List[str] = None,
    expires_minutes: int = 15
) -> Optional[str]:
    """Create authentication token for background task execution."""
    try:
        from server.security import get_extension_auth_manager
        
        auth_manager = get_extension_auth_manager()
        return auth_manager.create_background_task_token(
            task_name=task_name,
            user_id=user_id,
            service_name=service_name,
            permissions=permissions,
            expires_delta=timedelta(minutes=expires_minutes)
        )
    except Exception as e:
        logger.error(f"Failed to create background task token for {task_name}: {e}")
        return None


async def refresh_user_authentication_token(
    refresh_token: str,
    new_permissions: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """Refresh user authentication token using refresh token."""
    try:
        from server.security import get_extension_auth_manager
        
        auth_manager = get_extension_auth_manager()
        return await auth_manager.refresh_user_token(refresh_token, new_permissions)
    except Exception as e:
        logger.error(f"Failed to refresh user token: {e}")
        return None


async def revoke_authentication_token(token: str) -> bool:
    """Revoke authentication token by adding to blacklist."""
    try:
        from server.security import get_extension_auth_manager
        
        auth_manager = get_extension_auth_manager()
        return await auth_manager.revoke_token(token)
    except Exception as e:
        logger.error(f"Failed to revoke token: {e}")
        return False


async def revoke_all_user_authentication_tokens(user_id: str) -> int:
    """Revoke all authentication tokens for a specific user."""
    try:
        from server.security import get_extension_auth_manager
        
        auth_manager = get_extension_auth_manager()
        return await auth_manager.revoke_all_user_tokens(user_id)
    except Exception as e:
        logger.error(f"Failed to revoke all tokens for user {user_id}: {e}")
        return 0


async def validate_authentication_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate authentication token and return user context."""
    try:
        from server.token_manager import validate_and_extract_user_context
        
        return await validate_and_extract_user_context(token)
    except Exception as e:
        logger.error(f"Failed to validate token: {e}")
        return None


def get_token_information(token: str) -> Optional[Dict[str, Any]]:
    """Get token information for debugging purposes."""
    try:
        from server.token_manager import get_token_manager
        
        token_manager = get_token_manager()
        return token_manager.get_token_info(token)
    except Exception as e:
        logger.error(f"Failed to get token information: {e}")
        return None


async def cleanup_expired_tokens() -> Dict[str, int]:
    """Clean up expired tokens from the system."""
    try:
        from server.token_manager import get_token_manager
        
        token_manager = get_token_manager()
        
        # Clean up expired refresh tokens
        refresh_count = await token_manager.cleanup_expired_refresh_tokens()
        
        # Clean up expired blacklist entries (if using local blacklist)
        blacklist_count = 0
        if token_manager.blacklist:
            blacklist_count = await token_manager.blacklist.cleanup_expired_tokens()
        
        logger.info(f"Cleaned up {refresh_count} refresh tokens and {blacklist_count} blacklist entries")
        
        return {
            "refresh_tokens_cleaned": refresh_count,
            "blacklist_entries_cleaned": blacklist_count,
            "total_cleaned": refresh_count + blacklist_count
        }
    except Exception as e:
        logger.error(f"Failed to cleanup expired tokens: {e}")
        return {"error": str(e)}


# Background task token management utilities
class BackgroundTaskTokenManager:
    """Utility class for managing background task authentication tokens."""
    
    @staticmethod
    async def create_task_token(
        task_name: str,
        task_type: str = "scheduled",
        user_context: Optional[Dict[str, Any]] = None,
        service_context: Optional[str] = None,
        custom_permissions: Optional[List[str]] = None
    ) -> Optional[str]:
        """Create authentication token for background task with context."""
        
        # Determine permissions based on task type
        if custom_permissions:
            permissions = custom_permissions
        elif task_type == "user_initiated":
            permissions = ["extension:background_tasks", "extension:user_data"]
        elif task_type == "system_maintenance":
            permissions = ["extension:background_tasks", "extension:system", "extension:admin"]
        else:  # scheduled or default
            permissions = ["extension:background_tasks", "extension:execute"]
        
        # Extract user ID if available
        user_id = None
        if user_context:
            user_id = user_context.get("user_id")
        
        return await create_background_task_authentication_token(
            task_name=task_name,
            user_id=user_id,
            service_name=service_context,
            permissions=permissions,
            expires_minutes=30  # Longer expiration for background tasks
        )
    
    @staticmethod
    async def validate_task_token(token: str, required_task_name: str) -> bool:
        """Validate that token is valid for specific background task."""
        try:
            user_context = await validate_authentication_token(token)
            
            if not user_context:
                return False
            
            # Check if token has background task permissions
            permissions = user_context.get("permissions", [])
            has_bg_permission = any(
                perm in permissions 
                for perm in ["extension:background_tasks", "extension:*"]
            )
            
            if not has_bg_permission:
                logger.warning(f"Token lacks background task permissions for {required_task_name}")
                return False
            
            # Check token type
            token_type = user_context.get("token_type")
            if token_type not in ["background_task", "service", "access"]:
                logger.warning(f"Invalid token type {token_type} for background task {required_task_name}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate task token for {required_task_name}: {e}")
            return False


# Service-to-service token management utilities
class ServiceTokenManager:
    """Utility class for managing service-to-service authentication tokens."""
    
    @staticmethod
    async def create_inter_service_token(
        source_service: str,
        target_service: str,
        operation: str,
        expires_minutes: int = 15
    ) -> Optional[str]:
        """Create token for service-to-service communication."""
        
        # Define permissions based on operation
        permission_map = {
            "health_check": ["extension:health"],
            "data_sync": ["extension:data", "extension:sync"],
            "background_task": ["extension:background_tasks", "extension:execute"],
            "admin_operation": ["extension:admin", "extension:system"],
            "user_operation": ["extension:user_data", "extension:read", "extension:write"]
        }
        
        permissions = permission_map.get(operation, ["extension:service"])
        
        service_name = f"{source_service}_to_{target_service}"
        
        return await create_service_authentication_token(
            service_name=service_name,
            permissions=permissions,
            expires_minutes=expires_minutes
        )
    
    @staticmethod
    async def validate_service_token(
        token: str,
        expected_source: str,
        expected_target: str,
        required_operation: str
    ) -> bool:
        """Validate service-to-service token for specific operation."""
        try:
            user_context = await validate_authentication_token(token)
            
            if not user_context:
                return False
            
            # Check if it's a service token
            if user_context.get("token_type") != "service":
                logger.warning(f"Non-service token used for service operation {required_operation}")
                return False
            
            # Check service name format
            service_name = user_context.get("service_name", "")
            expected_service_name = f"{expected_source}_to_{expected_target}"
            
            if service_name != expected_service_name:
                logger.warning(f"Service name mismatch: expected {expected_service_name}, got {service_name}")
                return False
            
            # Check permissions for operation
            permissions = user_context.get("permissions", [])
            
            operation_permissions = {
                "health_check": ["extension:health"],
                "data_sync": ["extension:data", "extension:sync"],
                "background_task": ["extension:background_tasks"],
                "admin_operation": ["extension:admin"],
                "user_operation": ["extension:user_data"]
            }
            
            required_perms = operation_permissions.get(required_operation, ["extension:service"])
            
            has_permission = any(
                perm in permissions or "extension:*" in permissions
                for perm in required_perms
            )
            
            if not has_permission:
                logger.warning(f"Service token lacks permissions for {required_operation}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate service token: {e}")
            return False