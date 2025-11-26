# RBAC System Guide

## Overview

This document provides a comprehensive guide to the new Role-Based Access Control (RBAC) system implemented in the KAREN Theme Default application. The RBAC system is designed to be robust, scalable, and maintainable, with a focus on type safety and ease of use.

## Architecture

The new RBAC system is organized into several key components:

### Core Components

1. **Types and Interfaces** (`src/lib/security/rbac/types.ts`)
   - Defines all TypeScript types and interfaces for the RBAC system
   - Includes core permission and role types, UI component types, and error handling types
   - Aligned with the Karen Python backend RBAC system

2. **Configuration** (`src/lib/security/rbac/config.ts`)
   - Contains configuration constants and mappings between frontend and backend
   - Defines default RBAC configuration, role mappings, and permission categories
   - Includes cache keys, API endpoints, and error messages

3. **Error Handling** (`src/lib/security/rbac/utils/errors.ts`)
   - Defines custom error classes for specific RBAC-related issues
   - Includes base RBACError class and specialized error classes
   - Provides helper functions for error handling

4. **Registries**
   - **RoleRegistry** (`src/lib/security/rbac/registries/RoleRegistry.ts`)
     - Manages role definitions and provides methods to register, validate, and retrieve roles
     - Handles role inheritance and circular dependency detection
   - **PermissionRegistry** (`src/lib/security/rbac/registries/PermissionRegistry.ts`)
     - Manages permission definitions and provides methods to register, validate, and retrieve permissions
     - Handles permission categories and validation

5. **Resolvers**
   - **RoleResolver** (`src/lib/security/rbac/resolvers/RoleResolver.ts`)
     - Handles role resolution and permission checking with comprehensive error handling
     - Provides methods to check user roles and resolve role permissions
   - **PermissionResolver** (`src/lib/security/rbac/resolvers/PermissionResolver.ts`)
     - Handles permission resolution and provides permission-related utilities
     - Provides methods to check permissions and get permission information
   - **HierarchyResolver** (`src/lib/security/rbac/resolvers/HierarchyResolver.ts`)
     - Handles role hierarchy resolution and provides hierarchy-related utilities
     - Provides methods to analyze role relationships and inheritance chains

6. **Managers**
   - **DynamicPermissionManager** (`src/lib/security/rbac/managers/DynamicPermissionManager.ts`)
     - Manages dynamic permissions and roles that can be added or removed at runtime
     - Provides persistence to localStorage and event handling
     - Includes validation for dynamic permissions and roles

7. **Service**
   - **RBACService** (`src/lib/security/rbac/RBACService.ts`)
     - The main entry point for the RBAC system, implemented as a singleton
     - Provides a high-level API for all RBAC operations
     - Coordinates between the different components of the system

### UI Components

1. **PermissionGate** (`src/components/rbac/PermissionGate.tsx`)
   - React component that conditionally renders children based on permissions
   - Can check for single or multiple permissions with requireAll option
   - Includes fallback rendering and error display options

2. **RoleGate** (`src/components/rbac/RoleGate.tsx`)
   - React component that conditionally renders children based on roles
   - Can check for single or multiple roles with requireAll option
   - Includes fallback rendering and error display options

3. **SecureComponent** (`src/components/rbac/SecureComponent.tsx`)
   - React component that combines permission and role checking
   - Can check for permissions, roles, or both
   - Includes fallback rendering and error display options

### React Hooks

1. **usePermissions** (`src/components/hooks/usePermissions.ts`)
   - React hook for checking permissions in components
   - Provides methods to check single permissions, any permissions, or all permissions
   - Handles initialization and error states

2. **useRoles** (`src/components/hooks/useRoles.ts`)
   - React hook for checking roles in components
   - Provides methods to check single roles, any roles, or all roles
   - Handles initialization and error states

3. **useRBAC** (`src/components/hooks/useRBAC.ts`)
   - React hook that combines both usePermissions and useRoles functionality
   - Provides a comprehensive API for permission and role checking
   - Handles user state and initialization

## Usage

### Basic Permission Checking

```typescript
import { usePermissions } from '@/components/hooks/usePermissions';

function MyComponent() {
  const { hasPermission, isLoading } = usePermissions();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (hasPermission('data:read')) {
    return <div>You can read data!</div>;
  }

  return <div>Access denied</div>;
}
```

### Basic Role Checking

```typescript
import { useRoles } from '@/components/hooks/useRoles';

function AdminComponent() {
  const { hasRole, isLoading } = useRoles();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (hasRole('admin')) {
    return <div>Admin content</div>;
  }

  return <div>Access denied</div>;
}
```

### Using PermissionGate Component

```typescript
import { PermissionGate } from '@/components/rbac/PermissionGate';

function SecureDataComponent() {
  return (
    <PermissionGate 
      permissions={["data:read", "data:write"]}
      requireAll={true}
      fallback={<div>You need data read and write permissions</div>}
    >
      <div>Secure data content</div>
    </PermissionGate>
  );
}
```

### Using RoleGate Component

```typescript
import { RoleGate } from '@/components/rbac/RoleGate';

function AdminPanel() {
  return (
    <RoleGate 
      roles={["admin", "super_admin"]}
      fallback={<div>Admin access required</div>}
    >
      <div>Admin panel content</div>
    </RoleGate>
  );
}
```

### Using SecureComponent

```typescript
import { SecureComponent } from '@/components/rbac/SecureComponent';

function HighlySecureComponent() {
  return (
    <SecureComponent 
      permissions={["system:configure"]}
      roles={["admin"]}
      fallback={<div>High-level access required</div>}
    >
      <div>Highly secure content</div>
    </SecureComponent>
  );
}
```

### Using RBACService Directly

```typescript
import { rbacService } from '@/lib/security/rbac/RBACService';

// Check if a user has a permission
const canReadData = rbacService.hasPermission(user, 'data:read');

// Check if a user has a role
const isAdmin = rbacService.hasRole(user, 'admin');

// Get all permissions for a user
const permissions = rbacService.getUserPermissions(user);

// Get all roles for a user
const roles = rbacService.getUserRoles(user);
```

### Dynamic Permissions

```typescript
import { rbacService } from '@/lib/security/rbac/RBACService';

// Add a dynamic permission
rbacService.addDynamicPermission('custom:action', 'Custom action permission');

// Add a dynamic role
rbacService.addDynamicRole('custom_role', {
  description: 'Custom role',
  inherits_from: null,
  permissions: ['custom:action']
});

// Check if a dynamic permission exists
const hasCustomPermission = rbacService.hasDynamicPermission('custom:action');

// Check if a dynamic role exists
const hasCustomRole = rbacService.hasDynamicRole('custom_role');
```

## Configuration

### Default Roles and Permissions

The system comes with a set of default roles and permissions:

#### Roles

1. **super_admin**
   - Description: System super administrator with all permissions
   - Inherits from: admin
   - Permissions: All permissions

2. **admin**
   - Description: System administrator with most permissions
   - Inherits from: user
   - Permissions: user:manage, system:configure, security:admin

3. **user**
   - Description: Standard platform user
   - Inherits from: null
   - Permissions: data:read, data:write, profile:manage

4. **viewer**
   - Description: Read-only user
   - Inherits from: null
   - Permissions: data:read

#### Permissions

Permissions are organized into categories:

1. **Data Permissions**
   - data:read - Read data
   - data:write - Write data
   - data:delete - Delete data

2. **User Permissions**
   - user:read - Read user information
   - user:manage - Manage users
   - user:delete - Delete users

3. **System Permissions**
   - system:configure - Configure system settings
   - system:admin - System administration

4. **Security Permissions**
   - security:admin - Security administration
   - security:audit - Audit security logs

### Custom Configuration

You can customize the RBAC system by modifying the configuration in `src/lib/security/rbac/config.ts`:

```typescript
// Add a custom role
export const CUSTOM_ROLES: Record<RoleName, RoleDefinition> = {
  custom_role: {
    description: "Custom role",
    inherits_from: "user",
    permissions: ["custom:permission"]
  }
};

// Add a custom permission
export const CUSTOM_PERMISSIONS: Permission[] = [
  "custom:permission"
];
```

## Error Handling

The RBAC system provides comprehensive error handling with custom error classes:

```typescript
import { 
  RBACError, 
  RoleNotFoundError, 
  PermissionNotFoundError,
  InvalidRoleDefinitionError,
  InvalidPermissionDefinitionError,
  CircularDependencyError
} from '@/lib/security/rbac/utils/errors';

try {
  // RBAC operation that might throw an error
  rbacService.checkPermission(user, 'nonexistent:permission');
} catch (error) {
  if (error instanceof PermissionNotFoundError) {
    console.error('Permission not found:', error.message);
  } else if (error instanceof RBACError) {
    console.error('RBAC error:', error.message);
  } else {
    console.error('Unexpected error:', error);
  }
}
```

## Testing

The RBAC system includes comprehensive tests:

### Unit Tests

Unit tests are located in the `src/lib/security/rbac/__tests__/` directory:

- `RBACService.test.ts` - Tests for the RBACService class
- `validateRBAC.ts` - Simple validation script for the RBAC system

### Running Tests

To run the tests:

```bash
# Run Jest tests
npm test

# Run validation script
npx ts-node src/lib/security/rbac/__tests__/validateRBAC.ts
```

## Migration from Old RBAC System

### Compatibility Layer

The system includes a compatibility layer in `src/components/security/rbac-shared.ts` to ensure smooth transition from the old RBAC system. This allows existing code to continue working while you migrate to the new system.

### Migration Steps

1. **Update Imports**
   - Replace imports from `@/types/rbac` with `@/lib/security/rbac/types`
   - Replace imports from `@/components/security/rbac` with `@/components/rbac`

2. **Update Components**
   - Replace `RBACGuard` with `PermissionGate` or `RoleGate`
   - Replace `useRBAC` hook with the new `useRBAC` hook

3. **Update Configuration**
   - Move role and permission definitions to the new configuration system

4. **Test**
   - Run the validation script to ensure everything works correctly

## Performance Considerations

The RBAC system is designed with performance in mind:

1. **Caching**
   - Permission and role resolution results are cached
   - Cache entries have TTL-based invalidation
   - Cache can be cleared manually if needed

2. **Lazy Loading**
   - Roles and permissions are loaded on demand
   - Only necessary data is loaded for each operation

3. **Efficient Inheritance Resolution**
   - Role inheritance is resolved efficiently
   - Circular dependencies are detected and prevented

## Security Considerations

1. **Input Validation**
   - All inputs are validated before processing
   - Invalid inputs are rejected with appropriate error messages

2. **Permission Checks**
   - Permission checks are performed at multiple levels
   - No single point of failure

3. **Audit Logging**
   - Important operations are logged for audit purposes
   - Logs include user, action, and timestamp

## Future Enhancements

The RBAC system is designed to be extensible. Potential future enhancements include:

1. **Permission Groups**
   - Group related permissions together
   - Assign groups to roles instead of individual permissions

2. **Time-Based Permissions**
   - Permissions that are only valid during certain time periods
   - Temporary role assignments

3. **Context-Aware Permissions**
   - Permissions that depend on the context of the request
   - Dynamic permission evaluation based on external factors

## Conclusion

The new RBAC system provides a robust, scalable, and maintainable solution for managing access control in the KAREN Theme Default application. With its modular architecture, comprehensive error handling, and easy-to-use API, it simplifies the implementation of complex access control requirements while maintaining type safety and performance.