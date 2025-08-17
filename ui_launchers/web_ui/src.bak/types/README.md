# Enhanced Authentication Types and Interfaces

This directory contains comprehensive TypeScript types and interfaces for the enhanced authentication system with detailed user feedback, error handling, and form validation.

## Overview

The enhanced authentication system provides:

- **Comprehensive Error Classification**: Detailed error types with user-friendly messages
- **Real-time Form Validation**: Field-level validation with immediate feedback
- **Feedback Message System**: Success, error, warning, and info messages
- **State Management**: Complete authentication flow state tracking
- **Accessibility Support**: ARIA labels and screen reader compatibility
- **Security Features**: Rate limiting, security blocks, and 2FA support

## File Structure

### Core Types (`auth.ts`)

Contains the base authentication types and interfaces:

- `User` - User profile and preferences
- `LoginCredentials` - Login form data
- `AuthenticationError` - Detailed error information
- `ValidationErrors` - Form validation errors
- `FeedbackMessage` - User feedback messages
- `AuthenticationState` - Authentication flow state
- `SecurityFlags` - Security-related flags

### Utility Functions (`auth-utils.ts`)

Provides utility functions and constants:

- `createAuthError()` - Creates standardized authentication errors
- `validateCredentials()` - Validates login credentials
- `parseBackendError()` - Parses backend errors into standard format
- `classifyError()` - Classifies errors for appropriate handling
- `ERROR_MESSAGES` - User-friendly error messages
- `ERROR_CLASSIFICATIONS` - Error classification mappings

### Feedback Types (`auth-feedback.ts`)

Types for user feedback components:

- `SuccessMessageProps` - Success message component props
- `ErrorMessageProps` - Error message component props
- `LoadingIndicatorProps` - Loading indicator props
- `FeedbackMessageFactory` - Factory for creating feedback messages
- `FeedbackState` - Feedback state management

### Form Types (`auth-form.ts`)

Types for form management and validation:

- `FormFieldType` - Form field identifiers
- `FormFieldState` - Individual field state
- `AuthFormState` - Complete form state
- `FormValidator` - Form validation class
- `ValidationConfig` - Validation rules configuration

### Enhanced Types (`auth-enhanced.ts`)

Comprehensive exports and additional types:

- Re-exports all base types
- `AuthSystemConfig` - System configuration
- `EnhancedAuthService` - Enhanced service interface
- `UseAuthenticationHook` - React hook interface
- `AUTH_CONSTANTS` - System constants

## Usage Examples

### Basic Error Handling

```typescript
import { createAuthError, classifyError, ERROR_MESSAGES } from '@/types/auth-enhanced';

// Create a standardized error
const error = createAuthError('invalid_credentials', 'Custom message');

// Classify the error
const classification = classifyError(error.type);

// Get user-friendly message
const userMessage = ERROR_MESSAGES[error.type];
```

### Form Validation

```typescript
import { FormValidator, validateCredentials } from '@/types/auth-enhanced';

const validator = new FormValidator();
const credentials = { email: 'user@example.com', password: 'password123' };

// Validate individual field
const emailError = validator.validateField('email', credentials.email);

// Validate complete form
const result = validator.validateForm(credentials);
if (!result.isValid) {
  console.log('Validation errors:', result.errors);
}
```

### Feedback Messages

```typescript
import { FeedbackMessageFactory } from '@/types/auth-enhanced';

// Create success message
const successMessage = FeedbackMessageFactory.createSuccessMessage(
  'Login Successful',
  'Welcome back!'
);

// Create error message with retry action
const errorMessage = FeedbackMessageFactory.createErrorMessage(
  'Login Failed',
  'Invalid credentials',
  () => retryLogin()
);
```

### Backend Error Parsing

```typescript
import { parseBackendError } from '@/types/auth-enhanced';

try {
  await authService.login(credentials);
} catch (error) {
  const authError = parseBackendError(error);
  
  switch (authError.type) {
    case 'network_error':
      showNetworkErrorMessage();
      break;
    case 'rate_limit':
      showRateLimitMessage(authError.retryAfter);
      break;
    default:
      showGenericErrorMessage(authError.message);
  }
}
```

## Error Types

### Authentication Error Types

- `invalid_credentials` - Wrong email/password
- `network_error` - Connection issues
- `rate_limit` - Too many attempts
- `security_block` - Security system block
- `verification_required` - Email verification needed
- `account_locked` - Account temporarily locked
- `account_suspended` - Account suspended
- `two_factor_required` - 2FA code needed
- `two_factor_invalid` - Invalid 2FA code
- `server_error` - Backend server error
- `validation_error` - Form validation error
- `timeout_error` - Request timeout
- `unknown_error` - Unexpected error

### Error Classifications

Each error type has a classification with:

- `category` - Error category (authentication, network, security, etc.)
- `severity` - Error severity (low, medium, high, critical)
- `userAction` - Recommended user action
- `retryable` - Whether the error can be retried
- `supportContact` - Whether user should contact support

## Form Field Types

- `email` - Email address field
- `password` - Password field
- `totp_code` - Two-factor authentication code

## Validation Rules

### Email Validation

- Required field
- Valid email format
- Maximum length (254 characters)

### Password Validation

- Required field
- Minimum length (8 characters)
- Maximum length (128 characters)

### TOTP Code Validation

- Required when 2FA is enabled
- Must be 6 digits
- Numeric only

## State Management

### Authentication States

- `initial` - Initial state
- `validating` - Validating form input
- `authenticating` - Authenticating with server
- `two_factor` - Waiting for 2FA code
- `success` - Authentication successful
- `error` - Authentication failed

### Form States

Each form field tracks:

- `value` - Current field value
- `error` - Validation error message
- `touched` - Whether field has been interacted with
- `focused` - Whether field is currently focused
- `validating` - Whether field is being validated

## Configuration

### System Configuration

```typescript
interface AuthSystemConfig {
  enableRealTimeValidation: boolean;
  enableRetryLogic: boolean;
  enableFeedbackMessages: boolean;
  enableSecurityFeatures: boolean;
  enableAccessibility: boolean;
  enableLogging: boolean;
  maxRetryAttempts: number;
  retryBaseDelay: number;
  feedbackAutoHideDuration: number;
  validationDebounceDelay: number;
}
```

### Default Configuration

The system comes with sensible defaults:

- Real-time validation enabled
- 3 retry attempts maximum
- 1 second base retry delay
- 5 second feedback auto-hide
- 300ms validation debounce

## Testing

The types include comprehensive test coverage in `__tests__/auth-types.test.ts`:

- Type creation and validation
- Error classification and parsing
- Form validation logic
- Feedback message generation
- Configuration validation

Run tests with:

```bash
npm test src/types/__tests__/auth-types.test.ts
```

## Integration

### React Components

The types are designed to work seamlessly with React components:

```typescript
import { EnhancedLoginFormProps, UseAuthenticationHook } from '@/types/auth-enhanced';

const LoginForm: React.FC<EnhancedLoginFormProps> = ({ onSuccess, onError }) => {
  // Component implementation
};
```

### Service Integration

Enhanced service interface for better error handling:

```typescript
import { EnhancedAuthService } from '@/types/auth-enhanced';

class AuthService implements EnhancedAuthService {
  async login(credentials: LoginCredentials): Promise<AuthServiceResponse<LoginResponse>> {
    // Implementation with enhanced error handling
  }
}
```

## Best Practices

1. **Always use type-safe error handling**:
   ```typescript
   const error = parseBackendError(backendError);
   const classification = classifyError(error.type);
   ```

2. **Validate user input with proper feedback**:
   ```typescript
   const errors = validateCredentials(credentials);
   if (hasValidationErrors(errors)) {
     showValidationErrors(errors);
   }
   ```

3. **Provide appropriate user feedback**:
   ```typescript
   const message = FeedbackMessageFactory.fromAuthError(error, retryCallback);
   showFeedbackMessage(message);
   ```

4. **Handle security scenarios appropriately**:
   ```typescript
   if (requiresSupportContact(error)) {
     showSupportContactMessage();
   }
   ```

## Migration Guide

When migrating from the basic authentication types:

1. Update imports to use enhanced types
2. Replace basic error handling with classified errors
3. Add form validation using the new validation system
4. Implement feedback messages for better UX
5. Update components to use enhanced prop types

## Contributing

When adding new authentication features:

1. Add appropriate types to the relevant files
2. Update error classifications if needed
3. Add validation rules for new fields
4. Include comprehensive tests
5. Update this documentation

## Support

For questions about the authentication types:

1. Check the test files for usage examples
2. Review the type definitions for available options
3. Consult the error classification mappings
4. Refer to the validation rule configurations