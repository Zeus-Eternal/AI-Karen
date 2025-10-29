# Token Management Implementation

## Overview

This document describes the comprehensive token management utilities implemented for the extension runtime authentication system. The implementation provides JWT token generation, validation, refresh logic, blacklisting, and service-to-service authentication tokens for background tasks.

## Components

### 1. TokenManager (`server/token_manager.py`)

The core token management class that handles all token operations.

#### Features

- **JWT Token Generation**: Creates access, refresh, service, and background task tokens
- **Token Validation**: Validates tokens with signature verification and blacklist checking
- **Token Refresh**: Implements secure token refresh with blacklist support
- **Token Blacklisting**: Redis-based or in-memory token blacklisting for security
- **Service-to-Service Authentication**: Specialized tokens for background tasks and inter-service communication

#### Configuration

```python
config = {
    "secret_key": "your-secret-key",
    "algorithm": "HS256",
    "access_token_expire_minutes": 60,
    "service_token_expire_minutes": 30,
    "refresh_token_expire_days": 7,
    "token_blacklist_enabled": True,
    "redis_url": "redis://localhost:6379/0"  # Optional
}
```

### 2. Token Types

#### TokenType Enum

- `ACCESS`: Standard user access tokens
- `REFRESH`: Long-lived tokens for refreshing access tokens
- `SERVICE`: Service-to-service authentication tokens
- `BACKGROUND_TASK`: Specialized tokens for background task execution
- `API_KEY`: API key-based authentication tokens

#### TokenStatus Enum

- `VALID`: Token is valid and can be used
- `EXPIRED`: Token has expired
- `BLACKLISTED`: Token has been revoked/blacklisted
- `INVALID`: Token is malformed or has invalid signature
- `REVOKED`: Token has been explicitly revoked

### 3. TokenPayload Class

Structured token payload for consistent token generation:

```python
@dataclass
class TokenPayload:
    user_id: Optional[str] = None
    service_name: Optional[str] = None
    tenant_id: str = "default"
    roles: List[str] = None
    permissions: List[str] = None
    token_type: TokenType = TokenType.ACCESS
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    issuer: str = "kari-extension-system"
    audience: str = "kari-extensions"
    jti: Optional[str] = None  # JWT ID for blacklisting
```

### 4. TokenBlacklist Class

Redis-based or in-memory token blacklisting system:

- **Redis Support**: Uses Redis for distributed blacklisting
- **Local Fallback**: Falls back to in-memory blacklisting if Redis unavailable
- **TTL Support**: Automatically expires blacklisted tokens
- **Cleanup**: Provides cleanup methods for expired entries

## Usage Examples

### Basic Token Operations

```python
from server.token_manager import get_token_manager

# Get token manager instance
token_manager = get_token_manager()

# Generate access token
access_token, payload = token_manager.generate_access_token(
    user_id="user123",
    tenant_id="tenant1",
    roles=["user", "extension_user"],
    permissions=["extension:read", "extension:write"]
)

# Validate token
status, validated_payload = await token_manager.validate_token(access_token)

if status == TokenStatus.VALID:
    print(f"Token valid for user: {validated_payload['user_id']}")
```

### Service-to-Service Authentication

```python
# Generate service token
service_token, payload = token_manager.generate_service_token(
    service_name="extension_manager",
    permissions=["extension:background_tasks", "extension:health"]
)

# Generate background task token
bg_token, payload = token_manager.generate_background_task_token(
    task_name="data_sync_task",
    user_id="user123",
    permissions=["extension:background_tasks", "extension:data"]
)
```

### Token Refresh

```python
# Generate refresh token
refresh_token, payload = token_manager.generate_refresh_token(
    user_id="user123",
    tenant_id="tenant1"
)

# Refresh access token
new_access, new_refresh, payload = await token_manager.refresh_access_token(
    refresh_token,
    new_permissions=["extension:read", "extension:write", "extension:admin"]
)
```

### Token Revocation

```python
# Revoke single token
success = await token_manager.revoke_token(access_token)

# Revoke all user tokens
revoked_count = await token_manager.revoke_all_user_tokens("user123")
```

## Utility Functions (`server/token_utils.py`)

### User Session Management

```python
from server.token_utils import create_user_session_tokens

# Create complete token set for user session
tokens = await create_user_session_tokens(
    user_id="user123",
    tenant_id="tenant1",
    roles=["user", "admin"],
    permissions=["extension:read", "extension:write"]
)
```

### Background Task Authentication

```python
from server.token_utils import BackgroundTaskTokenManager

# Create task token
task_token = await BackgroundTaskTokenManager.create_task_token(
    task_name="scheduled_maintenance",
    task_type="system_maintenance",
    service_context="maintenance_service"
)

# Validate task token
is_valid = await BackgroundTaskTokenManager.validate_task_token(
    task_token, "scheduled_maintenance"
)
```

### Service-to-Service Communication

```python
from server.token_utils import ServiceTokenManager

# Create inter-service token
inter_service_token = await ServiceTokenManager.create_inter_service_token(
    source_service="extension_manager",
    target_service="background_processor",
    operation="background_task"
)

# Validate service token
is_valid = await ServiceTokenManager.validate_service_token(
    inter_service_token,
    expected_source="extension_manager",
    expected_target="background_processor",
    required_operation="background_task"
)
```

## Integration with ExtensionAuthManager

The token management utilities are integrated with the existing `ExtensionAuthManager`:

```python
from server.security import get_extension_auth_manager

auth_manager = get_extension_auth_manager()

# Enhanced token creation
access_token = auth_manager.create_enhanced_access_token(
    user_id="user123",
    permissions=["extension:read", "extension:write"]
)

# Token refresh
tokens = await auth_manager.refresh_user_token(refresh_token)

# Token revocation
success = await auth_manager.revoke_token(access_token)
```

## Security Features

### 1. JWT ID (JTI) for Blacklisting

Every token includes a unique JWT ID that enables:
- Token blacklisting for security
- Tracking token usage
- Preventing token reuse after refresh

### 2. Token Blacklisting

- **Redis-based**: Distributed blacklisting across multiple instances
- **TTL Support**: Automatic cleanup of expired blacklist entries
- **Fallback**: Local in-memory blacklisting when Redis unavailable

### 3. Signature Verification

- **Algorithm Validation**: Ensures tokens use expected signing algorithm
- **Secret Key Protection**: Validates tokens with configured secret key
- **Tampering Detection**: Detects any modifications to token content

### 4. Expiration Handling

- **Configurable Expiration**: Different expiration times for different token types
- **Automatic Validation**: Rejects expired tokens during validation
- **Proactive Refresh**: Supports proactive token refresh before expiration

## Error Handling

The token management system provides comprehensive error handling:

```python
try:
    status, payload = await token_manager.validate_token(token)
    
    if status == TokenStatus.VALID:
        # Token is valid, use payload
        pass
    elif status == TokenStatus.EXPIRED:
        # Token expired, refresh needed
        pass
    elif status == TokenStatus.BLACKLISTED:
        # Token revoked, authentication required
        pass
    else:
        # Invalid token, authentication required
        pass
        
except Exception as e:
    # Handle validation errors
    logger.error(f"Token validation error: {e}")
```

## Performance Considerations

### 1. Redis Connection Pooling

The token blacklist uses Redis connection pooling for optimal performance:

```python
# Redis client is initialized with connection pooling
redis_client = redis.from_url(redis_url, decode_responses=True)
```

### 2. Local Fallback

When Redis is unavailable, the system falls back to in-memory blacklisting:

```python
if not REDIS_AVAILABLE:
    logger.info("Redis not available, using local token blacklist")
    self.blacklist = TokenBlacklist()  # Use local fallback
```

### 3. Efficient Cleanup

The system provides efficient cleanup of expired tokens:

```python
# Clean up expired refresh tokens
refresh_count = await token_manager.cleanup_expired_refresh_tokens()

# Clean up expired blacklist entries
blacklist_count = await token_manager.blacklist.cleanup_expired_tokens()
```

## Testing

The implementation includes comprehensive tests:

- **Core Functionality**: Token generation, validation, and refresh
- **Security Features**: Blacklisting, tampering detection, algorithm validation
- **Error Handling**: Invalid tokens, expired tokens, network failures
- **Performance**: Token cleanup, Redis fallback, concurrent operations

Run tests with:

```bash
python3 test_token_core.py
python3 test_token_simple.py
```

## Configuration Requirements

### Environment Variables

```bash
# Required
EXTENSION_SECRET_KEY=your-super-secret-jwt-key-change-in-production
EXTENSION_JWT_ALGORITHM=HS256

# Token Expiration (minutes)
EXTENSION_ACCESS_TOKEN_EXPIRE_MINUTES=60
EXTENSION_SERVICE_TOKEN_EXPIRE_MINUTES=30

# Security Settings
EXTENSION_TOKEN_BLACKLIST_ENABLED=true
EXTENSION_REQUIRE_HTTPS=true  # Production only

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
```

### Production Security

For production deployments:

1. **Change Default Secret Keys**: Never use default development keys
2. **Enable HTTPS**: Set `EXTENSION_REQUIRE_HTTPS=true`
3. **Configure Redis**: Use Redis for distributed blacklisting
4. **Monitor Token Usage**: Implement logging and monitoring
5. **Regular Key Rotation**: Implement secret key rotation strategy

## Requirements Satisfied

This implementation satisfies the following requirements from the specification:

- **4.1**: JWT token generation and validation functions ✓
- **4.2**: Token refresh logic with proper expiration handling ✓
- **4.3**: Token blacklisting for security ✓
- **4.4**: Service-to-service authentication tokens for background tasks ✓
- **4.5**: Comprehensive error handling and security features ✓

The token management utilities provide a robust, secure, and scalable foundation for extension runtime authentication.