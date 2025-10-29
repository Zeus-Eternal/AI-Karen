# Extension Authentication Configuration

This document describes the extension authentication configuration system implemented for the Kari platform.

## Overview

The extension authentication system provides secure access control for extension APIs through JWT tokens, API keys, and environment-specific configuration management.

## Configuration Structure

### Environment Variables

The following environment variables control extension authentication behavior:

#### Core Authentication Settings
- `EXTENSION_AUTH_ENABLED` (default: `true`) - Enable/disable extension authentication
- `EXTENSION_SECRET_KEY` (default: `dev-extension-secret-key-change-in-production`) - JWT signing key
- `EXTENSION_JWT_ALGORITHM` (default: `HS256`) - JWT signing algorithm
- `EXTENSION_API_KEY` (default: `dev-extension-api-key-change-in-production`) - API key for admin operations

#### Token Expiration Settings
- `EXTENSION_ACCESS_TOKEN_EXPIRE_MINUTES` (default: `60`) - Access token lifetime in minutes
- `EXTENSION_SERVICE_TOKEN_EXPIRE_MINUTES` (default: `30`) - Service token lifetime in minutes

#### Authentication Mode Settings
- `EXTENSION_AUTH_MODE` (default: `hybrid`) - Authentication mode: `development`, `hybrid`, or `strict`
- `EXTENSION_DEV_BYPASS_ENABLED` (default: `true`) - Allow development mode bypass
- `EXTENSION_REQUIRE_HTTPS` (default: `false`) - Require HTTPS for extension APIs

#### Permission Settings
- `EXTENSION_DEFAULT_PERMISSIONS` (default: `extension:read,extension:write`) - Default user permissions
- `EXTENSION_ADMIN_PERMISSIONS` (default: `extension:*`) - Admin permissions
- `EXTENSION_SERVICE_PERMISSIONS` (default: `extension:background_tasks,extension:health`) - Service permissions

#### Rate Limiting Settings
- `EXTENSION_RATE_LIMIT_PER_MINUTE` (default: `100`) - Requests per minute limit
- `EXTENSION_BURST_LIMIT` (default: `20`) - Burst request limit
- `EXTENSION_ENABLE_RATE_LIMITING` (default: `true`) - Enable rate limiting

#### Security Settings
- `EXTENSION_TOKEN_BLACKLIST_ENABLED` (default: `true`) - Enable token blacklisting
- `EXTENSION_MAX_FAILED_ATTEMPTS` (default: `5`) - Max failed authentication attempts
- `EXTENSION_LOCKOUT_DURATION_MINUTES` (default: `15`) - Account lockout duration
- `EXTENSION_AUDIT_LOGGING_ENABLED` (default: `true`) - Enable audit logging

#### Environment Detection
- `EXTENSION_DEVELOPMENT_MODE` (auto-detected) - Development environment flag
- `EXTENSION_STAGING_MODE` (auto-detected) - Staging environment flag
- `EXTENSION_PRODUCTION_MODE` (auto-detected) - Production environment flag

## Authentication Modes

### Development Mode (`development`)
- All authentication checks are bypassed
- Suitable for local development and testing
- Uses mock user context with admin permissions

### Hybrid Mode (`hybrid`) - Default
- Authentication is enforced for production environments
- Development bypass is available for local development
- Balances security with development convenience

### Strict Mode (`strict`)
- Authentication is always enforced
- No development bypass available
- Maximum security for production environments

## Environment-Specific Configuration

The system automatically adjusts settings based on the detected environment:

### Development Environment
- `dev_bypass_enabled`: `true`
- `require_https`: `false`
- `rate_limit_per_minute`: `1000`
- `burst_limit`: `100`
- `max_failed_attempts`: `10`
- `lockout_duration_minutes`: `1`

### Staging Environment
- `dev_bypass_enabled`: `false`
- `require_https`: `true`
- `rate_limit_per_minute`: `200`
- `burst_limit`: `30`
- `max_failed_attempts`: `5`
- `lockout_duration_minutes`: `10`

### Production Environment
- `dev_bypass_enabled`: `false`
- `require_https`: `true`
- `rate_limit_per_minute`: `100`
- `burst_limit`: `20`
- `max_failed_attempts`: `3`
- `lockout_duration_minutes`: `30`

## Usage Examples

### Basic Configuration Access

```python
from server.config import settings

# Get extension auth configuration
config = settings.get_extension_auth_config()
print(f"Auth enabled: {config['enabled']}")
print(f"Auth mode: {config['auth_mode']}")

# Get environment-specific configuration
env_config = settings.get_environment_specific_extension_config()
print(f"Rate limit: {env_config['rate_limit_per_minute']}/min")
```

### Authentication Manager Usage

```python
from server.security import get_extension_auth_manager

# Get authentication manager
auth_manager = get_extension_auth_manager()

# Create access token
token = auth_manager.create_access_token(
    user_id="user123",
    tenant_id="tenant456",
    roles=["user"],
    permissions=["extension:read", "extension:write"]
)

# Create service token
service_token = auth_manager.create_service_token(
    service_name="background-processor",
    permissions=["extension:background_tasks"]
)
```

### FastAPI Endpoint Protection

```python
from fastapi import APIRouter, Depends
from server.security import require_extension_read, require_extension_write

router = APIRouter()

@router.get("/extensions/")
async def list_extensions(
    user_context = Depends(require_extension_read)
):
    # User has read permission
    return {"extensions": []}

@router.post("/extensions/")
async def create_extension(
    user_context = Depends(require_extension_write)
):
    # User has write permission
    return {"message": "Extension created"}
```

## Configuration Validation

The system includes built-in configuration validation:

```python
from server.config import settings

# Validate configuration
is_valid = settings.validate_extension_auth_config()
if not is_valid:
    print("Configuration validation failed")
```

### Validation Rules

1. **Production Security**: In production mode, default secret keys must be changed
2. **HTTPS Requirement**: HTTPS should be enabled in production
3. **Algorithm Validation**: JWT algorithm must be from approved list
4. **Positive Values**: Token expiration and rate limits must be positive
5. **Auth Mode**: Must be one of `development`, `hybrid`, or `strict`

## Security Considerations

### Secret Key Management
- Change default secret keys in production
- Use strong, randomly generated keys
- Store keys securely (environment variables, secret management systems)
- Rotate keys regularly

### Token Security
- Use appropriate expiration times
- Implement token blacklisting for revoked tokens
- Monitor for suspicious authentication patterns
- Log authentication events for audit trails

### Rate Limiting
- Configure appropriate limits for your use case
- Monitor rate limit violations
- Implement progressive penalties for abuse
- Consider user-specific and IP-based limits

### HTTPS Requirements
- Always use HTTPS in production
- Implement proper certificate management
- Consider certificate pinning for high-security environments

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check secret key configuration
   - Verify token expiration settings
   - Ensure proper permissions are assigned

2. **Development Mode Issues**
   - Verify `EXTENSION_DEV_BYPASS_ENABLED` is `true`
   - Check `EXTENSION_AUTH_MODE` setting
   - Ensure development headers are sent correctly

3. **Rate Limiting Issues**
   - Adjust rate limit settings for your use case
   - Check for burst limit violations
   - Monitor rate limit metrics

### Debugging

Enable debug logging to troubleshoot authentication issues:

```python
import logging
logging.getLogger("server.security").setLevel(logging.DEBUG)
```

### Configuration Testing

Use the provided validation script to test your configuration:

```bash
python3 test_extension_config_simple.py
```

## Migration Guide

### From Previous Authentication System

1. Update environment variables with new `EXTENSION_*` prefixes
2. Update code to use `get_extension_auth_manager()` instead of direct instantiation
3. Replace hardcoded authentication logic with configuration-driven approach
4. Test authentication flows in all environments

### Environment-Specific Deployment

1. **Development**: Use default settings, enable bypass mode
2. **Staging**: Change secret keys, enable HTTPS, disable bypass
3. **Production**: Use strong secrets, enable all security features, strict mode

## API Reference

### Settings Class Methods

- `validate_extension_auth_config()` - Validate configuration
- `get_extension_auth_config()` - Get base configuration
- `get_environment_specific_extension_config()` - Get environment-adjusted configuration

### ExtensionAuthManager Methods

- `create_access_token()` - Create user access token
- `create_service_token()` - Create service-to-service token
- `authenticate_extension_request()` - Authenticate API request
- `has_permission()` - Check user permissions

### FastAPI Dependencies

- `require_extension_read` - Require read permission
- `require_extension_write` - Require write permission
- `require_extension_admin` - Require admin permission
- `require_background_tasks` - Require background tasks permission

## Best Practices

1. **Configuration Management**
   - Use environment-specific configuration files
   - Validate configuration on startup
   - Document all configuration options

2. **Security**
   - Follow principle of least privilege
   - Implement proper audit logging
   - Regular security reviews and updates

3. **Monitoring**
   - Monitor authentication metrics
   - Set up alerts for security events
   - Regular review of access patterns

4. **Development**
   - Use development mode for local testing
   - Test authentication flows thoroughly
   - Document authentication requirements for extensions