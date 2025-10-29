# Extension Authentication System

This directory contains the authentication system for extension API calls, implementing secure token management, automatic refresh, and comprehensive error handling.

## Components

### ExtensionAuthManager (`extension-auth-manager.ts`)

The core authentication manager that handles:

- **Token Management**: Secure storage and retrieval of JWT tokens
- **Automatic Refresh**: Proactive token renewal before expiration
- **Secure Storage**: Encrypted token storage using XOR encryption
- **Authentication State**: Comprehensive state management with retry logic
- **Development Mode**: Special handling for development environments

#### Key Features

1. **Secure Token Storage**
   - XOR encryption for token obfuscation
   - Automatic encryption key generation
   - Fallback to plain text if encryption fails

2. **Automatic Token Refresh**
   - Proactive renewal 5 minutes before expiration
   - Prevents concurrent refresh attempts
   - Exponential backoff on failures
   - Fallback to main auth context

3. **Authentication State Management**
   - Tracks authentication status
   - Monitors refresh operations
   - Handles failure counts and retry delays
   - Provides comprehensive state information

4. **Development Mode Support**
   - Automatic detection of development environment
   - Special headers for development bypass
   - Hot reload compatibility

#### Usage

```typescript
import { getExtensionAuthManager } from '@/lib/auth/extension-auth-manager';

const authManager = getExtensionAuthManager();

// Get authentication headers for API calls
const headers = await authManager.getAuthHeaders();

// Check authentication status
const isAuthenticated = authManager.isAuthenticated();

// Get current auth state
const authState = authManager.getAuthState();

// Force token refresh
await authManager.forceRefresh();

// Clear authentication
authManager.clearAuth();
```

### EnhancedKarenBackendService (`enhanced-karen-backend-service.ts`)

Enhanced backend service that integrates with the ExtensionAuthManager to provide:

- **Authenticated Requests**: Automatic authentication header injection
- **Retry Logic**: Intelligent retry with exponential backoff
- **Error Handling**: Comprehensive error classification and recovery
- **Service Integration**: Seamless integration with existing backend services

#### Key Features

1. **Automatic Authentication**
   - Injects authentication headers automatically
   - Handles token refresh on 403 errors
   - Supports development mode bypass

2. **Intelligent Retry Logic**
   - Exponential backoff for retryable errors
   - Different strategies for different error types
   - Configurable retry attempts and timeouts

3. **Comprehensive Error Handling**
   - Detailed error classification
   - Graceful degradation on failures
   - Structured error logging

#### Usage

```typescript
import { getEnhancedKarenBackendService } from '@/lib/auth/enhanced-karen-backend-service';

const backendService = getEnhancedKarenBackendService();

// Make authenticated API calls
const extensions = await backendService.getExtensions();
const tasks = await backendService.getBackgroundTasks();

// Register background tasks
await backendService.registerBackgroundTask(taskData);

// Check extension health
const health = await backendService.getExtensionHealth();
```

## Dependencies

### Connection Manager (`../connection/connection-manager.ts`)

Handles HTTP connections with:
- Timeout management
- Retry logic
- Error classification
- Health monitoring

### Timeout Manager (`../connection/timeout-manager.ts`)

Manages operation-specific timeouts:
- Different timeouts for different operations
- Adaptive timeout based on network conditions
- Development mode adjustments

## Testing

Comprehensive test suite covering:
- Token storage and encryption
- Authentication header generation
- Token expiration detection
- Authentication state management
- Development mode detection
- Global instance management

Run tests with:
```bash
npm test -- --run src/lib/auth/__tests__/extension-auth-manager.test.ts
```

## Requirements Addressed

This implementation addresses the following requirements from the specification:

- **3.1**: Extension integration service error handling
- **3.2**: Extension API calls with proper authentication
- **3.3**: Authentication failures and retry logic
- **6.1**: Development mode authentication support
- **6.2**: Hot reload support without authentication issues

## Security Considerations

1. **Token Encryption**: Tokens are encrypted using XOR encryption for basic obfuscation
2. **Secure Storage**: Uses localStorage with encryption for token persistence
3. **Development Mode**: Special handling for development environments
4. **Error Handling**: Comprehensive error handling without exposing sensitive information
5. **Token Refresh**: Automatic refresh prevents token expiration issues

## Future Enhancements

1. **Advanced Encryption**: Implement stronger encryption algorithms
2. **Token Rotation**: Implement automatic token rotation
3. **Biometric Authentication**: Add support for biometric authentication
4. **Multi-Factor Authentication**: Support for MFA flows
5. **Session Management**: Enhanced session management capabilities