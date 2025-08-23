# Frontend Session Recovery and Error Handling

This directory contains the implementation of Task 5: "Implement frontend session recovery and error handling" from the session persistence premium response specification.

## Overview

The implementation provides intelligent session recovery that attempts token refresh before showing login screens, with graceful fallback handling and comprehensive error recovery mechanisms.

## Components

### 1. Session Recovery System (`session-recovery.ts`)

Core session recovery logic that handles different failure scenarios:

- **`attemptSessionRecovery()`**: Main entry point for session recovery
- **`recoverFrom401Error()`**: Handles 401 authentication errors with token refresh
- **`silentSessionRecovery()`**: Background session recovery without user interruption
- **Error Classification**: Intelligent error analysis (network, auth, invalid session)

```typescript
import { attemptSessionRecovery } from '@/lib/auth/session-recovery';

const result = await attemptSessionRecovery();
if (result.success) {
  // Session recovered successfully
} else {
  // Handle failure based on result.reason and result.shouldShowLogin
}
```

### 2. Enhanced API Client (`api-client-enhanced.ts`)

Extended API client with automatic retry mechanism for 401 errors:

- **Automatic Token Refresh**: Detects 401 errors and attempts session recovery
- **Request Queuing**: Queues multiple requests during recovery to prevent race conditions
- **Intelligent Retry**: Only retries requests after successful session recovery

```typescript
import { getEnhancedApiClient } from '@/lib/auth/api-client-enhanced';

const client = getEnhancedApiClient();
// Automatically handles 401 errors with session recovery
const response = await client.get('/api/protected-endpoint');
```

### 3. Enhanced Protected Route (`ProtectedRouteEnhanced.tsx`)

React component that ensures valid sessions with intelligent recovery:

- **Session Recovery**: Attempts recovery before showing login
- **Network Error Handling**: Retry mechanism for network issues
- **User Experience**: Loading states, error messages, and graceful fallbacks

```tsx
import { ProtectedRouteEnhanced } from '@/components/auth/ProtectedRouteEnhanced';

<ProtectedRouteEnhanced
  showRecoveryStatus={true}
  onRecoveryFailure={(result) => console.log('Recovery failed:', result)}
>
  <YourProtectedContent />
</ProtectedRouteEnhanced>
```

### 4. Session Error Boundary (`SessionErrorBoundary.tsx`)

React error boundary that catches authentication-related errors:

- **Error Classification**: Distinguishes auth errors from other errors
- **Automatic Recovery**: Attempts session recovery for auth errors
- **User Interface**: Provides recovery options and clear error messages

```tsx
import { SessionErrorBoundary } from '@/components/auth/SessionErrorBoundary';

<SessionErrorBoundary
  onAuthError={(error) => console.log('Auth error:', error)}
  onRecoveryAttempt={(result) => console.log('Recovery attempt:', result)}
>
  <YourApplication />
</SessionErrorBoundary>
```

## Key Features

### Intelligent Error Classification

The system classifies errors into categories for appropriate handling:

- **Network Errors**: Connection issues, timeouts → Retry without login
- **Authentication Errors**: 401, unauthorized, token issues → Attempt recovery then login
- **Invalid Session**: Generic errors → Clear session and require login

### Graceful Fallback Handling

- **Silent Recovery**: Attempts recovery without user interruption
- **Progressive Degradation**: Shows appropriate UI states during recovery
- **User Control**: Provides retry options and clear next steps

### Session Recovery Flow

1. **Detection**: Error or session check triggers recovery
2. **Classification**: Determine error type and recovery strategy
3. **Recovery Attempt**: Try token refresh or session boot
4. **Result Handling**: Success → continue, Failure → show appropriate UI
5. **User Feedback**: Clear messaging about what happened and next steps

## Requirements Fulfilled

### Requirement 1.4: Graceful Fallback
- ✅ Graceful redirect to login when session recovery fails
- ✅ Context preservation for post-login redirect

### Requirement 5.2: Automatic Retry Mechanism
- ✅ Automatic retry for 401 errors with token refresh
- ✅ Request queuing during recovery to prevent race conditions

### Requirement 5.3: Silent Session Recovery
- ✅ Background session recovery without user interruption
- ✅ Transparent retry of failed requests after recovery

### Requirement 5.4: Protected Route Wrapper
- ✅ Enhanced protected route with session validation
- ✅ Automatic recovery attempts before showing login

### Requirement 5.5: Session Recovery Scenarios
- ✅ Comprehensive test coverage for recovery scenarios
- ✅ Error boundary integration for application-wide error handling

## Usage Examples

### Basic Protected Route

```tsx
function App() {
  return (
    <SessionErrorBoundary>
      <ProtectedRouteEnhanced>
        <Dashboard />
      </ProtectedRouteEnhanced>
    </SessionErrorBoundary>
  );
}
```

### API Client with Recovery

```typescript
async function fetchUserData() {
  const client = getEnhancedApiClient();
  try {
    // Automatically handles 401 errors and session recovery
    const response = await client.get('/api/user');
    return response.data;
  } catch (error) {
    // Only non-recoverable errors reach here
    console.error('Failed to fetch user data:', error);
    throw error;
  }
}
```

### Manual Session Recovery

```typescript
import { useProtectedRoute } from '@/components/auth/ProtectedRouteEnhanced';

function MyComponent() {
  const { ensureAuthenticated } = useProtectedRoute();
  
  const handleSecureAction = async () => {
    const isAuthenticated = await ensureAuthenticated();
    if (isAuthenticated) {
      // Proceed with secure action
    } else {
      // User needs to log in
    }
  };
}
```

## Testing

The implementation includes comprehensive test coverage:

- **Unit Tests**: Core session recovery logic
- **Integration Tests**: API client retry mechanisms
- **Component Tests**: React component behavior
- **Error Boundary Tests**: Error handling and recovery

Run tests with:
```bash
npm test -- --run src/__tests__/session-recovery*.test.ts
npm test -- --run src/__tests__/api-client-enhanced-recovery.test.ts
```

## Error Handling Patterns

### Network Errors
- Show retry button with attempt counter
- Limit retry attempts (max 3)
- Provide "skip to login" option after max retries

### Authentication Errors
- Attempt automatic session recovery
- Show recovery progress to user
- Fallback to login with clear messaging

### Generic Errors
- Provide retry option
- Show technical details in expandable section
- Clear session if recovery attempts fail

## Integration with Existing System

The enhanced components are designed to work alongside the existing authentication system:

- **Backward Compatible**: Existing `ProtectedRoute` continues to work
- **Progressive Enhancement**: New components provide additional features
- **Modular Design**: Components can be used independently or together

## Performance Considerations

- **Request Deduplication**: Prevents multiple simultaneous recovery attempts
- **Silent Recovery**: Minimizes user interruption
- **Efficient Queuing**: Batches requests during recovery
- **Error Caching**: Avoids repeated recovery attempts for same error

## Security Considerations

- **Token Validation**: Ensures tokens are valid before use
- **Session Cleanup**: Clears invalid sessions properly
- **Error Information**: Limits sensitive information in error messages
- **Recovery Limits**: Prevents infinite recovery loops