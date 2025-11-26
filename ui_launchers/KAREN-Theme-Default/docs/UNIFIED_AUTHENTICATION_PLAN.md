# Unified Authentication System Plan

## Current Problems

The current authentication system has several issues:

1. **Scattered Components**: Authentication logic is spread across multiple files with overlapping responsibilities
2. **Complex Dependencies**: There are circular dependencies and complex interconnections between modules
3. **Inconsistent Patterns**: Different files handle authentication in different ways
4. **Redundant Code**: Similar functionality is implemented in multiple places
5. **Over-Engineering**: The system is more complex than necessary for the requirements

## Proposed Solution

We will create a clean, modular authentication system with the following structure:

### 1. Core Authentication Service (`AuthService.ts`)
- Single source of truth for authentication
- Handles login, logout, and session validation
- Simple, straightforward implementation
- Integrates with the existing RBAC system

### 2. Token Management (`TokenService.ts`)
- Simple, secure token handling
- Storage and retrieval of authentication tokens
- Token refresh logic
- No complex encryption or obfuscation

### 3. Session Management (`SessionService.ts`)
- Lightweight session handling
- User session state management
- Session validation and refresh
- Integration with cookies

### 4. Authentication Context (`AuthContext.tsx`)
- React context for authentication state
- Provides authentication methods to components
- Integrates with the core authentication service
- Simple, clean interface

### 5. Authentication Utilities (`AuthUtils.ts`)
- Helper functions for authentication
- Type definitions
- Error handling utilities
- Common authentication patterns

## File Structure

```
src/lib/auth/
├── core/
│   ├── AuthService.ts          # Core authentication service
│   ├── TokenService.ts        # Token management
│   └── SessionService.ts      # Session management
├── AuthContext.tsx            # React context (updated)
├── AuthUtils.ts               # Authentication utilities
└── index.ts                   # Exports
```

## Implementation Plan

1. **Create Core Authentication Service**
   - Implement basic authentication methods
   - Integrate with existing RBAC system
   - Handle login, logout, and session validation

2. **Implement Token Management**
   - Simple token storage and retrieval
   - Token refresh logic
   - Integration with authentication service

3. **Create Session Management**
   - Lightweight session handling
   - Integration with cookies
   - Session validation and refresh

4. **Update AuthContext**
   - Simplify the existing AuthContext
   - Remove redundant code
   - Integrate with new authentication service

5. **Create Authentication Utilities**
   - Helper functions for authentication
   - Type definitions
   - Error handling utilities

6. **Remove Redundant Files**
   - Identify and remove redundant authentication files
   - Update imports throughout the application
   - Ensure no circular dependencies

## Benefits

1. **Simplicity**: Clean, straightforward implementation
2. **Modularity**: Each component has a single responsibility
3. **Maintainability**: Easier to understand and modify
4. **Testability**: Each component can be tested independently
5. **Performance**: Reduced overhead and complexity

## Integration with Existing Systems

The new authentication system will integrate with:
- The existing RBAC system for role and permission checking
- The existing session cookie system
- The existing API endpoints for authentication
- The existing React components and contexts

## Migration Plan

1. Create the new authentication system alongside the existing one
2. Gradually update components to use the new system
3. Remove the old system once all components are updated
4. Test thoroughly to ensure no regressions