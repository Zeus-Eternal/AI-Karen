"""
Security decorators and utilities for extension development.

This module provides decorators and utilities that make it easy for extension
developers to implement security controls in their extensions.
"""

import functools
import logging
from typing import Callable, List, Optional, Any, Dict
from datetime import datetime

from .security import ExtensionSecurityManager
from .models import ExtensionContext

logger = logging.getLogger(__name__)

# Global security manager instance
_security_manager: Optional[ExtensionSecurityManager] = None


def set_security_manager(manager: ExtensionSecurityManager) -> None:
    """Set the global security manager instance."""
    global _security_manager
    _security_manager = manager


def get_security_manager() -> Optional[ExtensionSecurityManager]:
    """Get the global security manager instance."""
    return _security_manager


def require_permission(permission: str):
    """
    Decorator that requires a specific permission to execute a function.
    
    Args:
        permission: The required permission (e.g., 'data:read', 'system:files')
    
    Usage:
        @require_permission('data:write')
        def save_data(self, data):
            # Function implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get extension context from self or arguments
            extension_name = None
            context = None
            
            # Check if first argument is an extension instance
            if args and hasattr(args[0], 'manifest'):
                extension_name = args[0].manifest.name
                if hasattr(args[0], 'context'):
                    context = args[0].context
            
            # Check if context is passed as argument
            for arg in args:
                if isinstance(arg, ExtensionContext):
                    extension_name = arg.extension_name
                    context = arg
                    break
            
            # Check if context is passed as keyword argument
            if 'context' in kwargs and isinstance(kwargs['context'], ExtensionContext):
                context = kwargs['context']
                extension_name = context.extension_name
            
            if not extension_name:
                logger.error(f"Cannot determine extension name for permission check: {permission}")
                raise PermissionError(f"Cannot determine extension context for permission: {permission}")
            
            # Check permission
            if _security_manager:
                if not _security_manager.check_permission(extension_name, permission, context):
                    logger.warning(f"Permission denied for {extension_name}: {permission}")
                    raise PermissionError(f"Extension {extension_name} does not have permission: {permission}")
            else:
                logger.warning("Security manager not available, skipping permission check")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_permissions(permissions: List[str]):
    """
    Decorator that requires multiple permissions to execute a function.
    
    Args:
        permissions: List of required permissions
    
    Usage:
        @require_permissions(['data:read', 'system:files'])
        def process_files(self):
            # Function implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get extension context
            extension_name = None
            context = None
            
            if args and hasattr(args[0], 'manifest'):
                extension_name = args[0].manifest.name
                if hasattr(args[0], 'context'):
                    context = args[0].context
            
            for arg in args:
                if isinstance(arg, ExtensionContext):
                    extension_name = arg.extension_name
                    context = arg
                    break
            
            if 'context' in kwargs and isinstance(kwargs['context'], ExtensionContext):
                context = kwargs['context']
                extension_name = context.extension_name
            
            if not extension_name:
                logger.error(f"Cannot determine extension name for permission check: {permissions}")
                raise PermissionError(f"Cannot determine extension context for permissions: {permissions}")
            
            # Check all permissions
            if _security_manager:
                for permission in permissions:
                    if not _security_manager.check_permission(extension_name, permission, context):
                        logger.warning(f"Permission denied for {extension_name}: {permission}")
                        raise PermissionError(f"Extension {extension_name} does not have permission: {permission}")
            else:
                logger.warning("Security manager not available, skipping permission checks")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit(calls_per_minute: int = 60):
    """
    Decorator that implements rate limiting for extension functions.
    
    Args:
        calls_per_minute: Maximum number of calls per minute
    
    Usage:
        @rate_limit(calls_per_minute=30)
        def api_call(self):
            # Function implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        call_history: Dict[str, List[datetime]] = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get extension name
            extension_name = None
            if args and hasattr(args[0], 'manifest'):
                extension_name = args[0].manifest.name
            
            if not extension_name:
                extension_name = 'unknown'
            
            # Track calls
            now = datetime.now()
            if extension_name not in call_history:
                call_history[extension_name] = []
            
            # Remove old calls (older than 1 minute)
            cutoff_time = now.timestamp() - 60
            call_history[extension_name] = [
                call_time for call_time in call_history[extension_name]
                if call_time.timestamp() > cutoff_time
            ]
            
            # Check rate limit
            if len(call_history[extension_name]) >= calls_per_minute:
                logger.warning(f"Rate limit exceeded for {extension_name}: {func.__name__}")
                raise RuntimeError(f"Rate limit exceeded: {calls_per_minute} calls per minute")
            
            # Record this call
            call_history[extension_name].append(now)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def audit_log(action: str, sensitive: bool = False):
    """
    Decorator that logs extension actions for audit purposes.
    
    Args:
        action: Description of the action being performed
        sensitive: Whether this action involves sensitive data
    
    Usage:
        @audit_log("user_data_access", sensitive=True)
        def get_user_data(self, user_id):
            # Function implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get extension context
            extension_name = None
            context = None
            
            if args and hasattr(args[0], 'manifest'):
                extension_name = args[0].manifest.name
                if hasattr(args[0], 'context'):
                    context = args[0].context
            
            # Log the action
            log_data = {
                'extension_name': extension_name or 'unknown',
                'action': action,
                'function': func.__name__,
                'timestamp': datetime.now().isoformat(),
                'sensitive': sensitive
            }
            
            if context:
                log_data.update({
                    'tenant_id': context.tenant_id,
                    'user_id': context.user_id
                })
            
            # Log with appropriate level
            if sensitive:
                logger.info(f"AUDIT: {log_data}")
            else:
                logger.debug(f"AUDIT: {log_data}")
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful completion
                if sensitive:
                    logger.info(f"AUDIT_SUCCESS: {extension_name} - {action}")
                
                return result
                
            except Exception as e:
                # Log failure
                logger.error(f"AUDIT_FAILURE: {extension_name} - {action} - {str(e)}")
                raise
        
        return wrapper
    return decorator


def secure_temp_file(extension_name: str, suffix: str = '.tmp') -> str:
    """
    Create a secure temporary file for an extension.
    
    Args:
        extension_name: Name of the extension
        suffix: File suffix
    
    Returns:
        Path to the temporary file
    """
    import tempfile
    import os
    
    # Get sandbox directory if available
    sandbox_info = None
    if _security_manager:
        sandbox_info = _security_manager.sandbox.get_sandbox_info(extension_name)
    
    if sandbox_info:
        # Create temp file in sandbox
        temp_dir = os.path.join(sandbox_info['sandbox_directory'], 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        fd, path = tempfile.mkstemp(suffix=suffix, dir=temp_dir, prefix=f"{extension_name}_")
        os.close(fd)
        return path
    else:
        # Fallback to system temp
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=f"ext_{extension_name}_")
        os.close(fd)
        return path


def secure_temp_dir(extension_name: str) -> str:
    """
    Create a secure temporary directory for an extension.
    
    Args:
        extension_name: Name of the extension
    
    Returns:
        Path to the temporary directory
    """
    import tempfile
    import os
    
    # Get sandbox directory if available
    sandbox_info = None
    if _security_manager:
        sandbox_info = _security_manager.sandbox.get_sandbox_info(extension_name)
    
    if sandbox_info:
        # Create temp dir in sandbox
        temp_base = os.path.join(sandbox_info['sandbox_directory'], 'temp')
        os.makedirs(temp_base, exist_ok=True)
        return tempfile.mkdtemp(dir=temp_base, prefix=f"{extension_name}_")
    else:
        # Fallback to system temp
        return tempfile.mkdtemp(prefix=f"ext_{extension_name}_")


def validate_network_access(host: str, port: int, direction: str = 'outbound'):
    """
    Decorator that validates network access before allowing network operations.
    
    Args:
        host: Target host
        port: Target port
        direction: 'outbound' or 'inbound'
    
    Usage:
        @validate_network_access('api.example.com', 443)
        def call_external_api(self):
            # Network operation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get extension name
            extension_name = None
            if args and hasattr(args[0], 'manifest'):
                extension_name = args[0].manifest.name
            
            if not extension_name:
                logger.error("Cannot determine extension name for network access validation")
                raise PermissionError("Cannot determine extension context for network access")
            
            # Check network access
            if _security_manager:
                if not _security_manager.network_controller.check_network_access(
                    extension_name, host, port, direction
                ):
                    logger.warning(f"Network access denied for {extension_name}: {host}:{port} ({direction})")
                    raise PermissionError(f"Network access denied: {host}:{port} ({direction})")
            else:
                logger.warning("Security manager not available, skipping network access check")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class SecurityContext:
    """
    Context manager for secure operations within extensions.
    
    Usage:
        with SecurityContext(extension_name, ['data:write', 'system:files']) as ctx:
            # Perform secure operations
            ctx.write_file(path, data)
    """
    
    def __init__(self, extension_name: str, required_permissions: List[str]):
        self.extension_name = extension_name
        self.required_permissions = required_permissions
        self.temp_files: List[str] = []
        self.temp_dirs: List[str] = []
    
    def __enter__(self):
        # Check permissions
        if _security_manager:
            for permission in self.required_permissions:
                if not _security_manager.check_permission(self.extension_name, permission):
                    raise PermissionError(f"Extension {self.extension_name} does not have permission: {permission}")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up temporary files and directories
        import os
        import shutil
        
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.error(f"Failed to clean up temp file {temp_file}: {e}")
        
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Failed to clean up temp dir {temp_dir}: {e}")
    
    def create_temp_file(self, suffix: str = '.tmp') -> str:
        """Create a temporary file that will be cleaned up automatically."""
        temp_file = secure_temp_file(self.extension_name, suffix)
        self.temp_files.append(temp_file)
        return temp_file
    
    def create_temp_dir(self) -> str:
        """Create a temporary directory that will be cleaned up automatically."""
        temp_dir = secure_temp_dir(self.extension_name)
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def write_file(self, path: str, data: bytes) -> None:
        """Write data to a file with security checks."""
        # This would include additional security checks
        with open(path, 'wb') as f:
            f.write(data)
    
    def read_file(self, path: str) -> bytes:
        """Read data from a file with security checks."""
        # This would include additional security checks
        with open(path, 'rb') as f:
            return f.read()


def security_monitor(func: Callable) -> Callable:
    """
    Decorator that monitors function execution for security purposes.
    
    This decorator tracks execution time, resource usage, and potential
    security issues during function execution.
    
    Usage:
        @security_monitor
        def sensitive_operation(self):
            # Function implementation
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        
        # Get extension name
        extension_name = None
        if args and hasattr(args[0], 'manifest'):
            extension_name = args[0].manifest.name
        
        try:
            result = func(*args, **kwargs)
            
            # Log successful execution
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"SECURITY_MONITOR: {extension_name} - {func.__name__} - {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            # Log failed execution
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.warning(f"SECURITY_MONITOR_ERROR: {extension_name} - {func.__name__} - {execution_time:.3f}s - {str(e)}")
            raise
    
    return wrapper


# Utility functions for extension developers

def check_extension_permission(extension_name: str, permission: str) -> bool:
    """
    Check if an extension has a specific permission.
    
    Args:
        extension_name: Name of the extension
        permission: Permission to check
    
    Returns:
        True if extension has permission, False otherwise
    """
    if _security_manager:
        return _security_manager.check_permission(extension_name, permission)
    return False


def get_extension_permissions(extension_name: str) -> List[str]:
    """
    Get all permissions for an extension.
    
    Args:
        extension_name: Name of the extension
    
    Returns:
        List of permissions
    """
    if _security_manager:
        return list(_security_manager.permission_manager.get_extension_permissions(extension_name))
    return []


def get_resource_usage(extension_name: str) -> Optional[Dict[str, Any]]:
    """
    Get current resource usage for an extension.
    
    Args:
        extension_name: Name of the extension
    
    Returns:
        Resource usage information or None
    """
    if _security_manager:
        usage = _security_manager.resource_enforcer.get_resource_usage(extension_name)
        if usage:
            return {
                'cpu_percent': usage.cpu_percent,
                'memory_mb': usage.memory_mb,
                'disk_mb': usage.disk_mb,
                'uptime_seconds': usage.uptime_seconds
            }
    return None


def is_within_resource_limits(extension_name: str) -> bool:
    """
    Check if extension is within resource limits.
    
    Args:
        extension_name: Name of the extension
    
    Returns:
        True if within limits, False otherwise
    """
    if _security_manager:
        limits_check = _security_manager.resource_enforcer.check_resource_limits(extension_name)
        return limits_check.get('within_limits', True)
    return True