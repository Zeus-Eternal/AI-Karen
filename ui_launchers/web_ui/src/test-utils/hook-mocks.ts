/**
 * Centralized Hook Mocking Utilities
 * 
 * Provides consistent and reusable mocking strategies for authentication hooks
 * and other hooks used throughout the application. This ensures proper test isolation
 * and compatibility with the actual AuthContext implementation.
 */

import { vi, beforeEach, afterEach } from 'vitest';
import type { AuthContextType, User, LoginCredentials } from '@/contexts/AuthContext';
import type { UseRoleReturn } from '@/hooks/useRole';
import { 
  mockSuperAdminUser, 
  mockAdminUser, 
  mockRegularUser,
  createMockAuthContext 
} from './test-providers';

// Global mock registry to track active mocks for cleanup
const activeMocks = new Set<string>();

/**
 * Mock setup for useAuth hook with proper cleanup tracking
 */
export const setupUseAuthMock = (mockImplementation?: () => AuthContextType) => {
  const mockId = 'useAuth';
  activeMocks.add(mockId);

  // Note: vi.mock calls should be done in individual test files, not in utilities
  console.warn('setupUseAuthMock should be replaced with vi.mock calls in individual test files');

  return mockId;
};

/**
 * Mock setup for useRole hook with proper cleanup tracking
 */
export const setupUseRoleMock = (mockImplementation?: () => UseRoleReturn) => {
  const mockId = 'useRole';
  activeMocks.add(mockId);

  // Note: vi.mock calls should be done in individual test files, not in utilities
  console.warn('setupUseRoleMock should be replaced with vi.mock calls in individual test files');

  return mockId;
};

/**
 * Setup both useAuth and useRole mocks with compatible implementations
 */
export const setupAuthAndRoleMocks = (
  authContext?: AuthContextType,
  roleReturn?: UseRoleReturn
) => {
  const resolvedAuthContext = authContext || createMockAuthContext();
  const resolvedRoleReturn = roleReturn || createUseRoleReturnFromAuth(resolvedAuthContext);

  const authMockId = setupUseAuthMock(() => resolvedAuthContext);
  const roleMockId = setupUseRoleMock(() => resolvedRoleReturn);

  return { authMockId, roleMockId, authContext: resolvedAuthContext, roleReturn: resolvedRoleReturn };
};

/**
 * Create UseRoleReturn from AuthContextType to ensure compatibility
 */
export const createUseRoleReturnFromAuth = (authContext: AuthContextType): UseRoleReturn => {
  const role = authContext.user?.role || null;
  
  return {
    role,
    hasRole: authContext.hasRole,
    hasPermission: authContext.hasPermission,
    isAdmin: authContext.isAdmin(),
    isSuperAdmin: authContext.isSuperAdmin(),
    isUser: authContext.hasRole('user'),
    canManageUsers: authContext.hasPermission('user_management'),
    canManageAdmins: authContext.hasPermission('admin_management'),
    canManageSystem: authContext.hasPermission('system_config'),
    canViewAuditLogs: authContext.hasPermission('audit_logs'),
  };
};

/**
 * Predefined mock scenarios for common test cases
 */
export const mockScenarios = {
  superAdmin: () => {
    const authContext = createMockAuthContext(mockSuperAdminUser, true);
    const roleReturn = createUseRoleReturnFromAuth(authContext);
    return setupAuthAndRoleMocks(authContext, roleReturn);
  },

  admin: () => {
    const authContext = createMockAuthContext(mockAdminUser, true);
    const roleReturn = createUseRoleReturnFromAuth(authContext);
    return setupAuthAndRoleMocks(authContext, roleReturn);
  },

  user: () => {
    const authContext = createMockAuthContext(mockRegularUser, true);
    const roleReturn = createUseRoleReturnFromAuth(authContext);
    return setupAuthAndRoleMocks(authContext, roleReturn);
  },

  unauthenticated: () => {
    const authContext = createMockAuthContext(null, false);
    const roleReturn = createUseRoleReturnFromAuth(authContext);
    return setupAuthAndRoleMocks(authContext, roleReturn);
  },

  authError: () => {
    const authContext = createMockAuthContext(null, false, {
      login: vi.fn().mockRejectedValue(new Error('Authentication failed')),
      checkAuth: vi.fn().mockRejectedValue(new Error('Authentication failed'))
    });
    const roleReturn = createUseRoleReturnFromAuth(authContext);
    return setupAuthAndRoleMocks(authContext, roleReturn);
  },

  sessionExpired: () => {
    const authContext = createMockAuthContext(null, false, {
      checkAuth: vi.fn().mockResolvedValue(false),
      logout: vi.fn()
    });
    const roleReturn = createUseRoleReturnFromAuth(authContext);
    return setupAuthAndRoleMocks(authContext, roleReturn);
  }
};

/**
 * Mock implementations for specific hook methods
 */
export const createMockUseAuth = (
  user: User | null = null,
  isAuthenticated: boolean = false,
  overrides: Partial<AuthContextType> = {}
): AuthContextType => {
  return createMockAuthContext(user, isAuthenticated, overrides);
};

export const createMockUseRole = (
  user: User | null = null,
  overrides: Partial<UseRoleReturn> = {}
): UseRoleReturn => {
  const role = user?.role || null;
  const baseReturn: UseRoleReturn = {
    role,
    hasRole: vi.fn((requiredRole) => user?.role === requiredRole || user?.roles.includes(requiredRole) || false),
    hasPermission: vi.fn((permission) => user?.permissions?.includes(permission) || false),
    isAdmin: user?.role === 'admin' || user?.role === 'super_admin' || false,
    isSuperAdmin: user?.role === 'super_admin' || false,
    isUser: user?.role === 'user' || false,
    canManageUsers: user?.permissions?.includes('user_management') || false,
    canManageAdmins: user?.permissions?.includes('admin_management') || false,
    canManageSystem: user?.permissions?.includes('system_config') || false,
    canViewAuditLogs: user?.permissions?.includes('audit_logs') || false,
  };

  return { ...baseReturn, ...overrides };
};

/**
 * Advanced mock setup with custom implementations
 */
export const setupCustomAuthMock = (customImplementation: Partial<AuthContextType>) => {
  const defaultAuth = createMockAuthContext();
  const mergedAuth = { ...defaultAuth, ...customImplementation };
  
  return setupUseAuthMock(() => mergedAuth);
};

export const setupCustomRoleMock = (customImplementation: Partial<UseRoleReturn>) => {
  const defaultRole = createMockUseRole();
  const mergedRole = { ...defaultRole, ...customImplementation };
  
  return setupUseRoleMock(() => mergedRole);
};

/**
 * Mock cleanup utilities
 */
export const resetHookMocks = () => {
  vi.clearAllMocks();
  vi.resetAllMocks();
};

export const cleanupHookMocks = () => {
  activeMocks.clear();
  resetHookMocks();
};

/**
 * Test isolation utilities - use in beforeEach/afterEach
 */
export const setupTestIsolation = () => {
  beforeEach(() => {
    resetHookMocks();
  });

  afterEach(() => {
    cleanupHookMocks();
  });
};

/**
 * Batch mock setup for multiple hooks with consistent state
 */
export const setupConsistentMocks = (scenario: keyof typeof mockScenarios) => {
  return mockScenarios[scenario]();
};

/**
 * Mock validation utilities to ensure mocks are working correctly
 */
export const validateMockSetup = (authContext: AuthContextType, roleReturn: UseRoleReturn): boolean => {
  // Validate that auth context and role return are consistent
  const authUser = authContext.user;
  const roleUser = roleReturn.role;
  
  if (authUser && roleUser) {
    return authUser.role === roleUser;
  }
  
  if (!authUser && !roleUser) {
    return true;
  }
  
  return false;
};

/**
 * Debug utilities for troubleshooting mock issues
 */
export const debugMockState = (authContext: AuthContextType, roleReturn: UseRoleReturn) => {
  console.log('Mock Debug Info:', {
    authUser: authContext.user,
    authIsAuthenticated: authContext.isAuthenticated,
    roleRole: roleReturn.role,
    roleIsAdmin: roleReturn.isAdmin,
    roleIsSuperAdmin: roleReturn.isSuperAdmin,
    mockValidation: validateMockSetup(authContext, roleReturn)
  });
};

/**
 * Helper to create mock implementations that match actual hook behavior
 */
export const createRealisticMockAuth = (user: User | null, isAuthenticated: boolean): AuthContextType => {
  const hasRole = vi.fn((role: 'super_admin' | 'admin' | 'user'): boolean => {
    if (!user) return false;
    
    // Match actual implementation logic
    if (user.role) {
      return user.role === role;
    }
    
    return user.roles.includes(role);
  });

  const hasPermission = vi.fn((permission: string): boolean => {
    if (!user) return false;
    
    // Match actual implementation logic
    if (user.permissions) {
      return user.permissions.includes(permission);
    }
    
    // Default permissions based on role (matches actual implementation)
    const rolePermissions = getRolePermissions(user.role || (user.roles[0] as 'super_admin' | 'admin' | 'user'));
    return rolePermissions.includes(permission);
  });

  const isAdmin = vi.fn((): boolean => {
    return hasRole('admin') || hasRole('super_admin');
  });

  const isSuperAdmin = vi.fn((): boolean => {
    return hasRole('super_admin');
  });

  return {
    user,
    isAuthenticated,
    authState: {
      isLoading: false,
      error: null,
      isRefreshing: false,
      lastActivity: new Date(),
    },
    login: vi.fn(async (credentials: LoginCredentials): Promise<void> => {
      return Promise.resolve();
    }),
    logout: vi.fn((): void => {
      return;
    }),
    devLogin: vi.fn(async (email?: string): Promise<void> => {
      return Promise.resolve();
    }),
    checkAuth: vi.fn(async (): Promise<boolean> => {
      return Promise.resolve(isAuthenticated);
    }),
    refreshSession: vi.fn(async (): Promise<boolean> => {
      return Promise.resolve(isAuthenticated);
    }),
    clearError: vi.fn((): void => {
      return;
    }),
    hasRole,
    hasPermission,
    isAdmin,
    isSuperAdmin,
  };
};

// Helper function to get default permissions for a role (matches actual implementation)
const getRolePermissions = (role: 'super_admin' | 'admin' | 'user'): string[] => {
  switch (role) {
    case 'super_admin':
      return [
        'user_management',
        'admin_management', 
        'system_config',
        'audit_logs',
        'security_settings',
        'user_create',
        'user_edit',
        'user_delete',
        'admin_create',
        'admin_edit',
        'admin_delete'
      ];
    case 'admin':
      return [
        'user_management',
        'user_create',
        'user_edit',
        'user_delete'
      ];
    case 'user':
    default:
      return [];
  }
};

/**
 * Convenience functions for common test patterns
 */
export const mockAuthForTest = (scenario: keyof typeof mockScenarios) => {
  const { authContext, roleReturn } = mockScenarios[scenario]();
  return { authContext, roleReturn };
};

export const mockAuthWithUser = (user: User | null, isAuthenticated: boolean = !!user) => {
  const authContext = createRealisticMockAuth(user, isAuthenticated);
  const roleReturn = createUseRoleReturnFromAuth(authContext);
  return setupAuthAndRoleMocks(authContext, roleReturn);
};

/**
 * Mock factory for creating test-specific implementations
 */
export const createTestMocks = (options: {
  user?: User | null;
  isAuthenticated?: boolean;
  authOverrides?: Partial<AuthContextType>;
  roleOverrides?: Partial<UseRoleReturn>;
}) => {
  const { user = null, isAuthenticated = false, authOverrides = {}, roleOverrides = {} } = options;
  
  const baseAuth = createRealisticMockAuth(user, isAuthenticated);
  const authContext = { ...baseAuth, ...authOverrides };
  
  const baseRole = createUseRoleReturnFromAuth(authContext);
  const roleReturn = { ...baseRole, ...roleOverrides };
  
  return setupAuthAndRoleMocks(authContext, roleReturn);
};

/**
 * Export commonly used mock implementations for direct use
 */
export const commonMocks = {
  superAdminAuth: () => createRealisticMockAuth(mockSuperAdminUser, true),
  adminAuth: () => createRealisticMockAuth(mockAdminUser, true),
  userAuth: () => createRealisticMockAuth(mockRegularUser, true),
  unauthenticatedAuth: () => createRealisticMockAuth(null, false),
};

/**
 * Global test setup utilities for consistent mock behavior across tests
 */
export const setupGlobalMocks = () => {
  // Note: vi.mock calls should be done in individual test files, not in utilities
  console.warn('setupGlobalMocks should be replaced with vi.mock calls in individual test files');
};

/**
 * Reset all mocks to default state
 */
export const resetToDefaultMocks = () => {
  try {
    const { useAuth } = require('@/contexts/AuthContext');
    const { useRole } = require('@/hooks/useRole');
    
    if (vi.isMockFunction(useAuth)) {
      useAuth.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn(),
        hasRole: vi.fn(() => false),
        hasPermission: vi.fn(() => false),
        isAdmin: vi.fn(() => false),
        isSuperAdmin: vi.fn(() => false),
      });
    }
    
    if (vi.isMockFunction(useRole)) {
      useRole.mockReturnValue({
        role: null,
        hasRole: vi.fn(() => false),
        hasPermission: vi.fn(() => false),
        isAdmin: false,
        isSuperAdmin: false,
        isUser: false,
        canManageUsers: false,
        canManageAdmins: false,
        canManageSystem: false,
        canViewAuditLogs: false,
      });
    }
  } catch (error) {
    // Ignore errors if modules are not available
  }
};