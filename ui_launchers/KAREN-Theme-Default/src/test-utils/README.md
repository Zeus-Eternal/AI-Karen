# Test Infrastructure - Hook Mocking Strategy

This document explains the improved hook mocking strategy for testing authentication-dependent components. The new approach provides consistent, reliable, and isolated mocking of authentication hooks.

## Overview

The test infrastructure now provides:

1. **Centralized Hook Mocking**: Consistent mocking utilities for `useAuth` and `useRole` hooks
2. **Proper Test Isolation**: Automatic cleanup and reset between tests
3. **Realistic Mock Implementations**: Mocks that behave like the actual hooks
4. **Predefined Scenarios**: Common authentication scenarios ready to use
5. **Validation Utilities**: Tools to ensure mocks are working correctly

## Key Files

- `hook-mocks.ts` - Core hook mocking utilities
- `test-setup.ts` - Test environment setup and isolation
- `test-providers.tsx` - Enhanced test providers and rendering utilities
- `__tests__/hook-mocking-examples.test.tsx` - Examples and documentation

## Quick Start

### Basic Usage

```typescript
import { mockScenarios, resetHookMocks, cleanupHookMocks } from '@/test-utils/test-providers';

describe('MyComponent', () => {
  beforeEach(() => {
    resetHookMocks();
  });

  afterEach(() => {
    cleanupHookMocks();
  });

  it('should work for super admin users', () => {
    // Setup consistent mocks for super admin scenario
    const { authContext, roleReturn } = mockScenarios.superAdmin();
    
    render(<MyComponent />);
    
    // Test super admin specific behavior
    expect(screen.getByText('Admin Panel')).toBeInTheDocument();
  });
});
```

### Using with renderWithProviders

```typescript
import { renderWithProviders } from '@/test-utils/test-providers';

it('should render correctly for authenticated users', () => {
  renderWithProviders(<MyComponent />, {
    testScenario: 'super_admin'
  });
  
  expect(screen.getByText('Welcome')).toBeInTheDocument();
});
```

## Available Mock Scenarios

### Predefined Scenarios

```typescript
// Available scenarios
mockScenarios.superAdmin()    // Super admin with full permissions
mockScenarios.admin()         // Admin with user management permissions
mockScenarios.user()          // Regular user with no special permissions
mockScenarios.unauthenticated() // Not authenticated
mockScenarios.authError()     // Authentication error state
mockScenarios.sessionExpired() // Session expired state
```

### Custom Scenarios

```typescript
import { createTestMocks } from '@/test-utils/test-providers';

const { authContext, roleReturn } = createTestMocks({
  user: customUser,
  isAuthenticated: true,
  authOverrides: {
    hasPermission: vi.fn((permission) => permission === 'custom_permission')
  },
  roleOverrides: {
    canManageUsers: false
  }
});
```

## Hook Mocking Patterns

### 1. Scenario-Based Testing

Use predefined scenarios for common test cases:

```typescript
it('should show admin features for admin users', () => {
  mockScenarios.admin();
  render(<AdminComponent />);
  expect(screen.getByText('User Management')).toBeInTheDocument();
});
```

### 2. Custom Mock Behavior

Create custom mock implementations for specific test needs:

```typescript
it('should handle permission checking', () => {
  const { authContext } = createTestMocks({
    user: mockSuperAdminUser,
    isAuthenticated: true,
    authOverrides: {
      hasPermission: vi.fn((permission) => {
        return ['user_management', 'custom_permission'].includes(permission);
      })
    }
  });
  
  render(<PermissionComponent />);
  // Test custom permission logic
});
```

### 3. Dynamic Mock Behavior

Create mocks that change behavior during the test:

```typescript
it('should handle role changes', () => {
  let currentRole = 'user';
  
  const { authContext } = createTestMocks({
    user: mockRegularUser,
    isAuthenticated: true,
    authOverrides: {
      hasRole: vi.fn((role) => role === currentRole)
    }
  });
  
  render(<RoleComponent />);
  expect(screen.queryByText('Admin Panel')).not.toBeInTheDocument();
  
  // Change role
  currentRole = 'admin';
  // Trigger re-render or component update
  // Test new behavior
});
```

## Test Isolation

### Automatic Cleanup

The test setup automatically handles cleanup between tests:

```typescript
import { setupTestIsolation } from '@/test-utils/test-providers';

// This is automatically called in vitest.setup.ts
setupTestIsolation();
```

### Manual Cleanup

For custom test setups:

```typescript
beforeEach(() => {
  resetHookMocks();
});

afterEach(() => {
  cleanupHookMocks();
});
```

## Validation and Debugging

### Mock Validation

Ensure mocks are consistent:

```typescript
import { validateMockSetup } from '@/test-utils/test-providers';

const { authContext, roleReturn } = mockScenarios.superAdmin();
expect(validateMockSetup(authContext, roleReturn)).toBe(true);
```

### Debug Information

Get debug information about mock state:

```typescript
import { debugMockState } from '@/test-utils/test-providers';

const { authContext, roleReturn } = mockScenarios.superAdmin();
debugMockState(authContext, roleReturn);
```

## Common Patterns

### Testing Access Control

```typescript
describe('Access Control', () => {
  it('should deny access to non-admin users', () => {
    mockScenarios.user();
    render(<AdminOnlyComponent />);
    expect(screen.getByText('Access Denied')).toBeInTheDocument();
  });

  it('should allow access to admin users', () => {
    mockScenarios.admin();
    render(<AdminOnlyComponent />);
    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
  });
});
```

### Testing Authentication Flows

```typescript
describe('Authentication Flow', () => {
  it('should handle login process', async () => {
    const { authContext } = mockScenarios.unauthenticated();
    
    render(<LoginComponent />);
    
    // Simulate login
    fireEvent.click(screen.getByText('Login'));
    
    expect(authContext.login).toHaveBeenCalled();
  });
});
```

### Testing Permission-Based Features

```typescript
describe('Permission-Based Features', () => {
  it('should show features based on permissions', () => {
    const { authContext } = createTestMocks({
      user: mockAdminUser,
      isAuthenticated: true,
      authOverrides: {
        hasPermission: vi.fn((permission) => {
          return ['user_management', 'user_create'].includes(permission);
        })
      }
    });
    
    render(<FeatureComponent />);
    
    expect(screen.getByText('Create User')).toBeInTheDocument();
    expect(screen.queryByText('Delete User')).not.toBeInTheDocument();
  });
});
```

## Migration Guide

### From Old Mocking Pattern

**Old Pattern:**
```typescript
vi.mock('@/hooks/useRole');
const mockUseRole = vi.mocked(useRole);

mockUseRole.mockReturnValue({
  user: { id: '1', role: 'admin' },
  hasRole: vi.fn().mockReturnValue(true),
  // ... incomplete mock
});
```

**New Pattern:**
```typescript
import { mockScenarios } from '@/test-utils/test-providers';

const { authContext, roleReturn } = mockScenarios.admin();
// Consistent, complete mocks automatically set up
```

### Benefits of New Pattern

1. **Consistency**: All mocks follow the same pattern and interface
2. **Completeness**: All required methods and properties are mocked
3. **Isolation**: Automatic cleanup prevents test interference
4. **Validation**: Built-in validation ensures mocks work correctly
5. **Maintainability**: Centralized mocking logic is easier to maintain

## Troubleshooting

### Common Issues

1. **"useAuth must be used within an AuthProvider" Error**
   - Ensure you're using the new mocking utilities
   - Check that `setupCompleteTestEnvironment()` is called in vitest.setup.ts

2. **Inconsistent Mock Behavior**
   - Use `validateMockSetup()` to check mock consistency
   - Ensure proper cleanup between tests

3. **Mock Not Working**
   - Verify the mock is set up before rendering the component
   - Check that the component is actually using the mocked hooks

### Debug Steps

1. Use `debugMockState()` to inspect mock configuration
2. Use `validateTestEnvironment()` to check test setup
3. Check console for mock-related warnings
4. Verify mock functions are being called with expected arguments

## Best Practices

1. **Use Predefined Scenarios**: Start with predefined scenarios when possible
2. **Validate Mocks**: Use validation utilities to ensure mocks are working
3. **Clean Up**: Always clean up mocks between tests
4. **Test Isolation**: Each test should be independent
5. **Realistic Mocks**: Use mocks that behave like the actual implementation
6. **Document Custom Mocks**: Comment complex custom mock logic
7. **Test Edge Cases**: Include error scenarios and edge cases

## Examples

See `__tests__/hook-mocking-examples.test.tsx` for comprehensive examples of all patterns and utilities.