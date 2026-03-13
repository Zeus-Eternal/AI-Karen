# Form Validation System

This directory contains a comprehensive form validation system with real-time feedback for authentication forms.

## Overview

The form validation system provides:

- **Real-time validation** with debounced input handling
- **Field-specific error display** and clearing logic
- **Comprehensive validation rules** for email, password, and 2FA codes
- **Enhanced security validation** with common password detection
- **TypeScript support** with full type safety
- **Accessibility features** with proper ARIA labels and screen reader support

## Components

### FormValidator Class (`form-validator.ts`)

The core validation engine that handles:

- Email format validation with enhanced rules
- Password strength validation with security checks
- 2FA code format validation
- Debounced validation for real-time feedback
- Configurable validation rules

#### Basic Usage

```typescript
import { FormValidator, createFormValidator } from '@/lib/form-validator';

// Create validator with default rules
const validator = createFormValidator();

// Validate a field
const result = validator.validateField('email', 'user@example.com');
if (!result.isValid) {
  console.log(result.error); // "Invalid email format"
}

// Validate entire form
const formResult = validator.validateForm({
  email: 'user@example.com',
  password: 'securePassword123'
});
```

#### Enhanced Validation

```typescript
// Create validator with enhanced security rules
const enhancedValidator = createFormValidator(true);

// This will catch common weak passwords
const result = enhancedValidator.validateField('password', 'password');
// result.error: "Password is too common. Please choose a stronger password"
```

### useFormValidation Hook (`../hooks/use-form-validation.ts`)

React hook that provides form state management with validation:

```typescript
import { useFormValidation } from '@/hooks/use-form-validation';

function LoginForm() {
  const validation = useFormValidation({
    validateOnChange: true,
    validateOnBlur: true,
    enhanced: true
  });

  const handleSubmit = (credentials) => {
    const result = validation.validateForm(credentials);
    if (!result.isValid) {
      // Handle validation errors
      return;
    }
    // Proceed with form submission
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => {
          setEmail(e.target.value);
          validation.handleFieldChange('email', e.target.value);
        }}
        onBlur={() => validation.handleFieldBlur('email', email)}
      />
      {validation.shouldShowError('email') && (
        <span className="error">{validation.getFieldError('email')}</span>
      )}
    </form>
  );
}
```

### FormField Component (`../components/ui/form-field.tsx`)

Pre-built form field component with integrated validation:

```typescript
import { ValidatedFormField } from '@/components/ui/form-field';

<ValidatedFormField
  name="email"
  label="Email Address"
  value={email}
  onValueChange={setEmail}
  onValidationChange={validation.handleFieldChange}
  onBlurValidation={validation.handleFieldBlur}
  error={validation.getFieldError('email')}
  touched={validation.isFieldTouched('email')}
  isValidating={validation.validationState.fields.email.isValidating}
  required
/>
```

## Validation Rules

### Email Validation

- **Required**: Email cannot be empty
- **Format**: Must match standard email regex pattern
- **Length**: Maximum 254 characters
- **Enhanced**: No consecutive dots, leading/trailing dots in local part

### Password Validation

- **Required**: Password cannot be empty
- **Length**: Minimum 8 characters, maximum 128 characters
- **Enhanced**: Must contain at least one letter and one number
- **Enhanced**: Rejects common weak passwords (password, 12345678, etc.)

### 2FA Code Validation

- **Format**: Exactly 6 digits
- **Optional**: Can be empty when not required

## Configuration

### Validation Timing

```typescript
const validation = useFormValidation({
  validateOnChange: true,    // Validate as user types
  validateOnBlur: true,      // Validate when field loses focus
  debounceDelay: 300,        // Delay before validation (ms)
  enhanced: false            // Use enhanced security rules
});
```

### Custom Validation Rules

```typescript
const validator = createFormValidator();

// Add custom rule
validator.addValidationRule('password', {
  validate: (value) => value.includes('@'),
  message: 'Password must contain @ symbol'
});

// Remove existing rule
validator.removeValidationRule('password', 'Password must be at least 8 characters long');
```

## Accessibility

The form validation system includes comprehensive accessibility features:

- **ARIA labels** for all form elements
- **Screen reader announcements** for validation state changes
- **Focus management** during error states
- **Keyboard navigation** support
- **High contrast** error styling

## Testing

The system includes comprehensive unit tests:

```bash
# Run validation tests
npm test -- src/lib/__tests__/form-validator.test.ts

# Run hook tests
npm test -- src/hooks/__tests__/use-form-validation.test.ts
```

## Examples

See `../components/auth/LoginForm.tsx` for a complete implementation example that demonstrates:

- Real-time validation feedback
- Error message display
- Password strength indicator
- 2FA field handling
- Accessibility features

## Performance

The validation system is optimized for performance:

- **Debounced validation** prevents excessive API calls
- **Memoized components** prevent unnecessary re-renders
- **Efficient state updates** minimize React re-renders
- **Lazy validation** only validates when needed

## Browser Support

The system supports all modern browsers and includes:

- **Progressive enhancement** for JavaScript-disabled scenarios
- **Polyfills** for older browser compatibility
- **Graceful degradation** for unsupported features