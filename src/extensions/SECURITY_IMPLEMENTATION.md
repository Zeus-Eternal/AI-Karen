# Extension Security and Sandboxing Implementation

## Overview

This document describes the implementation of the extension security and sandboxing system for the Kari Extensions platform. The security system provides comprehensive protection through permission management, resource limits, process isolation, and network access controls.

## Components Implemented

### 1. Extension Security Manager (`security.py`)

The main security coordinator that manages all security components:

- **ExtensionSecurityManager**: Main class that coordinates all security components
- **ExtensionPermissionManager**: Manages extension permissions and access control
- **ResourceLimitEnforcer**: Enforces CPU, memory, and disk usage limits
- **ExtensionSandbox**: Provides process isolation and sandboxing
- **NetworkAccessController**: Controls network access for extensions
- **ProcessMonitor**: Monitors resource usage of extension processes
- **NetworkMonitor**: Monitors network connections for extensions

### 2. Security Decorators (`security_decorators.py`)

Provides easy-to-use decorators and utilities for extension developers:

- **@require_permission**: Requires specific permission to execute function
- **@require_permissions**: Requires multiple permissions
- **@rate_limit**: Implements rate limiting
- **@audit_log**: Logs actions for audit purposes
- **@security_monitor**: Monitors function execution
- **@validate_network_access**: Validates network access before operations
- **SecurityContext**: Context manager for secure operations

### 3. Security Integration

Updated existing components to integrate with security:

- **BaseExtension**: Added security methods and integration
- **ExtensionManager**: Integrated security initialization and cleanup
- **Models**: Extended with security-related data structures

### 4. Example Extension (`extensions/examples/secure-extension/`)

A complete example extension demonstrating security features:

- Permission-based API endpoints
- Secure file operations
- Network access with validation
- Resource monitoring
- Security status reporting

## Security Features

### Permission Management

The system implements a hierarchical permission model:

```python
permission_hierarchy = {
    'data_access': {
        'read': ['read'],
        'write': ['read', 'write'],
        'admin': ['read', 'write', 'admin']
    },
    'plugin_access': {
        'execute': ['execute'],
        'manage': ['execute', 'manage']
    },
    'system_access': {
        'files': ['files'],
        'network': ['network'],
        'scheduler': ['scheduler'],
        'logs': ['logs'],
        'metrics': ['metrics'],
        'admin': ['files', 'network', 'scheduler', 'logs', 'metrics', 'admin']
    },
    'network_access': {
        'internal': ['internal'],
        'external': ['internal', 'external']
    }
}
```

### Resource Limits

Extensions can be limited in their resource usage:

- **CPU Usage**: Maximum CPU percentage
- **Memory Usage**: Maximum memory in MB
- **Disk Usage**: Maximum disk space in MB
- **Network Usage**: Monitored and can be restricted
- **File Descriptors**: Tracked and can be limited
- **Thread Count**: Monitored

### Process Isolation

Extensions run in isolated environments:

- **Sandbox Directories**: Each extension gets its own isolated directory
- **Environment Variables**: Controlled environment setup
- **File System Access**: Limited to sandbox directory
- **Process Monitoring**: Real-time monitoring of extension processes

### Network Access Control

Network access is controlled through rules:

- **Outbound/Inbound Control**: Separate controls for each direction
- **Host Allowlists/Blocklists**: Control which hosts can be accessed
- **Port Restrictions**: Control which ports can be used
- **Connection Monitoring**: Track all network connections

## Usage Examples

### Using Security Decorators

```python
from src.extensions.security_decorators import require_permission, audit_log

class MyExtension(BaseExtension):
    @require_permission('data:write')
    @audit_log('user_data_update', sensitive=True)
    async def update_user_data(self, user_id: str, data: dict):
        # This method requires data:write permission
        # and logs the action for audit purposes
        pass
```

### Using Security Context

```python
from src.extensions.security_decorators import SecurityContext

async def secure_operation(self):
    with SecurityContext(self.manifest.name, ['system:files', 'data:write']) as ctx:
        # Create temporary files that are automatically cleaned up
        temp_file = ctx.create_temp_file('.json')
        
        # Perform secure file operations
        ctx.write_file(temp_file, data)
        result = ctx.read_file(temp_file)
        
        return result
    # Files are automatically cleaned up here
```

### Checking Permissions

```python
# In extension code
if self.check_permission('network:external'):
    # Make external network request
    response = await self.secure_http_request('https://api.example.com/data')
else:
    # Handle lack of permission
    raise PermissionError("External network access not permitted")
```

## Security Violations

The system tracks and responds to security violations:

- **Resource Limit Violations**: When extensions exceed CPU, memory, or disk limits
- **Permission Violations**: When extensions attempt unauthorized operations
- **Network Violations**: When extensions attempt blocked network access
- **File System Violations**: When extensions attempt to access restricted files

Violations are logged and can trigger automatic responses like:
- Warnings and alerts
- Resource throttling
- Extension suspension
- Automatic restart with stricter limits

## Configuration

Extensions declare their security requirements in their manifest:

```json
{
  "permissions": {
    "data_access": ["read", "write"],
    "plugin_access": ["execute"],
    "system_access": ["files", "logs"],
    "network_access": ["external"]
  },
  "resources": {
    "max_memory_mb": 256,
    "max_cpu_percent": 15,
    "max_disk_mb": 512
  }
}
```

## Testing

The implementation includes comprehensive tests:

- **Unit Tests**: Test individual security components
- **Integration Tests**: Test security system integration
- **Example Extension**: Demonstrates all security features
- **Verification Scripts**: Validate security system functionality

## Files Created

1. **Core Security System**:
   - `src/extensions/security.py` - Main security implementation
   - `src/extensions/security_decorators.py` - Developer-friendly decorators

2. **Integration**:
   - Updated `src/extensions/base.py` - Added security methods to BaseExtension
   - Updated `src/extensions/manager.py` - Integrated security into ExtensionManager

3. **Example and Tests**:
   - `extensions/examples/secure-extension/` - Complete example extension
   - `src/extensions/tests/test_security.py` - Comprehensive test suite
   - `src/extensions/tests/verify_security.py` - Verification script
   - `src/extensions/tests/simple_security_test.py` - Basic structure tests

## Security Best Practices

The implementation follows security best practices:

1. **Principle of Least Privilege**: Extensions only get permissions they explicitly request
2. **Defense in Depth**: Multiple layers of security controls
3. **Fail Secure**: Default to denying access when in doubt
4. **Audit Trail**: All security-relevant actions are logged
5. **Resource Isolation**: Extensions cannot interfere with each other
6. **Graceful Degradation**: System continues to function even if extensions fail

## Next Steps

The security system is now ready for:

1. **Integration Testing**: Test with real extensions in development environment
2. **Performance Tuning**: Optimize monitoring and enforcement overhead
3. **Policy Refinement**: Adjust default security policies based on usage
4. **Documentation**: Create developer guides for using security features
5. **Monitoring Dashboard**: Build UI for security status and violations

## Compliance and Standards

The implementation supports:

- **RBAC (Role-Based Access Control)**: Through permission system
- **Audit Logging**: For compliance requirements
- **Resource Quotas**: For fair resource sharing
- **Network Segmentation**: Through network access controls
- **Data Isolation**: Through tenant-aware data management

This security system provides a robust foundation for running untrusted extensions safely while maintaining system performance and reliability.