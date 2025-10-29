/**
 * Test Providers and Utilities
 * 
 * Provides wrapper components and utilities for testing React components
 * that depend on various context providers.
 */

import React, { ReactNode } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { vi } from 'vitest';
import { AuthContext, AuthContextType, User, LoginCredentials } from '@/contexts/AuthContext';

// Enhanced mock user data for testing with complete and realistic data
export const mockSuperAdminUser: User = {
  userId: 'super-admin-001',
  email: 'superadmin@example.com',
  roles: ['super_admin'],
  tenantId: 'test-tenant-001',
  role: 'super_admin',
  permissions: [
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
  ]
};

export const mockAdminUser: User = {
  userId: 'admin-002',
  email: 'admin@example.com',
  roles: ['admin'],
  tenantId: 'test-tenant-001',
  role: 'admin',
  permissions: [
    'user_management',
    'user_create',
    'user_edit',
    'user_delete'
  ]
};

export const mockRegularUser: User = {
  userId: 'user-003',
  email: 'user@example.com',
  roles: ['user'],
  tenantId: 'test-tenant-001',
  role: 'user',
  permissions: []
};

// Additional mock users for comprehensive testing scenarios
export const mockUnauthenticatedUser: User | null = null;

export const mockUserWithMultipleRoles: User = {
  userId: 'multi-role-004',
  email: 'multirole@example.com',
  roles: ['user', 'admin'],
  tenantId: 'test-tenant-001',
  role: 'admin', // Primary role
  permissions: [
    'user_management',
    'user_create',
    'user_edit',
    'user_delete'
  ]
};

export const mockInactiveUser: User = {
  userId: 'inactive-005',
  email: 'inactive@example.com',
  roles: ['user'],
  tenantId: 'test-tenant-001',
  role: 'user',
  permissions: []
};

export const mockUserWithCustomPermissions: User = {
  userId: 'custom-006',
  email: 'custom@example.com',
  roles: ['user'],
  tenantId: 'test-tenant-001',
  role: 'user',
  permissions: ['custom_permission', 'special_access']
};

// Enhanced Mock AuthContext value factory that matches the actual AuthContextType interface exactly
export const createMockAuthContext = (
  user: User | null = null,
  isAuthenticated: boolean = false,
  overrides: Partial<AuthContextType> = {}
): AuthContextType => {
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

  // Create realistic mock functions that behave like the actual implementation
  const hasRole = vi.fn((role: 'super_admin' | 'admin' | 'user'): boolean => {
    if (!user) return false;
    
    // Check the role field first, then fall back to roles array (matches actual implementation)
    if (user.role) {
      return user.role === role;
    }
    
    // Legacy support: check roles array
    return user.roles.includes(role);
  });

  const hasPermission = vi.fn((permission: string): boolean => {
    if (!user) return false;
    
    // Check permissions array if available
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

  const login = vi.fn(async (credentials: LoginCredentials): Promise<void> => {
    // Mock successful login behavior
    return Promise.resolve();
  });

  const logout = vi.fn((): void => {
    // Mock logout behavior - in real implementation this redirects
    return;
  });

  const checkAuth = vi.fn(async (): Promise<boolean> => {
    return Promise.resolve(isAuthenticated);
  });

  const baseContext: AuthContextType = {
    user,
    isAuthenticated,
    authState: {
      isLoading: false,
      error: null,
      isRefreshing: false,
      lastActivity: new Date(),
    },
    login,
    logout,
    devLogin: vi.fn(async (email?: string): Promise<void> => {
      return Promise.resolve();
    }),
    checkAuth,
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

  // Apply any overrides
  return {
    ...baseContext,
    ...overrides
  };
};

// Enhanced test wrapper component that provides AuthContext
interface TestAuthProviderProps {
  children: ReactNode;
  authValue?: Partial<AuthContextType>;
  user?: User | null;
  isAuthenticated?: boolean;
  // Additional options for test scenarios
  testScenario?: 'authenticated' | 'unauthenticated' | 'super_admin' | 'admin' | 'user' | 'custom';
}

export const TestAuthProvider: React.FC<TestAuthProviderProps> = ({ 
  children, 
  authValue,
  user = null,
  isAuthenticated = false,
  testScenario = 'custom'
}) => {
  // Determine user and authentication state based on test scenario
  let resolvedUser = user;
  let resolvedIsAuthenticated = isAuthenticated;

  switch (testScenario) {
    case 'super_admin':
      resolvedUser = mockSuperAdminUser;
      resolvedIsAuthenticated = true;
      break;
    case 'admin':
      resolvedUser = mockAdminUser;
      resolvedIsAuthenticated = true;
      break;
    case 'user':
      resolvedUser = mockRegularUser;
      resolvedIsAuthenticated = true;
      break;
    case 'authenticated':
      resolvedUser = user || mockRegularUser;
      resolvedIsAuthenticated = true;
      break;
    case 'unauthenticated':
      resolvedUser = null;
      resolvedIsAuthenticated = false;
      break;
    case 'custom':
    default:
      // Use provided values or defaults
      break;
  }

  // Create default auth context with resolved values
  const defaultAuthValue = createMockAuthContext(resolvedUser, resolvedIsAuthenticated);
  
  // Merge provided authValue with defaults, giving priority to provided values
  const mergedAuthValue: AuthContextType = {
    ...defaultAuthValue,
    user: resolvedUser,
    isAuthenticated: resolvedIsAuthenticated,
    ...authValue
  };

  // Use the actual AuthContext from the AuthContext module
  return (
    <AuthContext.Provider value={mergedAuthValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Enhanced custom render function that includes providers with additional options
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  authValue?: Partial<AuthContextType>;
  user?: User | null;
  isAuthenticated?: boolean;
  // Test scenario for quick setup
  testScenario?: 'authenticated' | 'unauthenticated' | 'super_admin' | 'admin' | 'user' | 'custom';
  // Additional provider options for different test scenarios
  providerOptions?: {
    // Mock router context if needed
    mockRouter?: boolean;
    // Mock theme provider if needed
    mockTheme?: boolean;
    // Custom wrapper components
    additionalWrappers?: React.ComponentType<{ children: ReactNode }>[];
  };
}

export const renderWithProviders = (
  ui: React.ReactElement,
  options: CustomRenderOptions = {}
) => {
  const { 
    authValue, 
    user, 
    isAuthenticated, 
    testScenario = 'custom',
    providerOptions = {},
    ...renderOptions 
  } = options;

  const { additionalWrappers = [] } = providerOptions;

  const Wrapper: React.FC<{ children: ReactNode }> = ({ children }) => {
    // Start with the AuthProvider as the base
    let wrappedChildren = (
      <TestAuthProvider 
        authValue={authValue} 
        user={user} 
        isAuthenticated={isAuthenticated}
        testScenario={testScenario}
      >
        {children}
      </TestAuthProvider>
    );

    // Apply additional wrappers if provided
    additionalWrappers.forEach((WrapperComponent) => {
      wrappedChildren = (
        <WrapperComponent>
          {wrappedChildren}
        </WrapperComponent>
      );
    });

    return <>{wrappedChildren}</>;
  };

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Enhanced utilities to mock the useAuth hook directly with better type safety
export const mockUseAuth = (authValue: Partial<AuthContextType> = {}): AuthContextType => {
  const defaultValue = createMockAuthContext();
  return { ...defaultValue, ...authValue };
};

// Utility to mock the useAuth hook for testing with comprehensive options
export const mockUseAuthHook = (
  authValue?: Partial<AuthContextType>, 
  user?: User | null, 
  isAuthenticated?: boolean
): AuthContextType => {
  if (authValue) {
    return { ...createMockAuthContext(), ...authValue };
  }
  return createMockAuthContext(user, isAuthenticated);
};

/**
 * Create a mock useAuth hook return value for super admin
 */
export const mockSuperAdminAuth = (overrides: Partial<AuthContextType> = {}): AuthContextType => {
  return createSuperAdminAuthContext(overrides);
};

/**
 * Create a mock useAuth hook return value for admin
 */
export const mockAdminAuth = (overrides: Partial<AuthContextType> = {}): AuthContextType => {
  return createAdminAuthContext(overrides);
};

/**
 * Create a mock useAuth hook return value for regular user
 */
export const mockUserAuth = (overrides: Partial<AuthContextType> = {}): AuthContextType => {
  return createUserAuthContext(overrides);
};

/**
 * Create a mock useAuth hook return value for unauthenticated state
 */
export const mockUnauthenticatedAuth = (overrides: Partial<AuthContextType> = {}): AuthContextType => {
  return createUnauthenticatedAuthContext(overrides);
};

// Enhanced setup functions to mock authentication hooks and utilities
export const setupAuthMock = () => {
  // Note: vi.mock calls should be done in individual test files, not in utilities
  // This function is kept for compatibility but doesn't perform mocking
  console.warn('setupAuthMock should be replaced with vi.mock calls in individual test files');
};

export const setupAuthMockWithScenario = (scenarioName: keyof typeof authTestScenarios) => {
  setupAuthMock();
  // Return the auth context for manual setup in tests
  return createAuthContextFromScenario(scenarioName);
};

// Mock setup for useRole hook (if it exists)
export const setupRoleMock = (roleData?: any) => {
  // Note: vi.mock calls should be done in individual test files, not in utilities
  console.warn('setupRoleMock should be replaced with vi.mock calls in individual test files');
};

// Comprehensive mock setup for all auth-related modules
export const setupComprehensiveAuthMocks = (authScenario: keyof typeof authTestScenarios = 'user') => {
  const authContext = createAuthContextFromScenario(authScenario);
  
  // Mock session utilities
  mockSessionFunctions(authContext.user, authContext.isAuthenticated);
  
  // Mock UI components
  mockUIComponents();
  
  return authContext;
};

// Utility to create mock implementations for specific test needs
export const createMockImplementations = (scenario: AuthTestScenario) => {
  return {
    login: vi.fn().mockImplementation(async (credentials: LoginCredentials) => {
      if (scenario.authContextOverrides?.login) {
        return scenario.authContextOverrides.login(credentials);
      }
      return Promise.resolve();
    }),
    logout: vi.fn().mockImplementation(() => {
      if (scenario.authContextOverrides?.logout) {
        return scenario.authContextOverrides.logout();
      }
      return;
    }),
    checkAuth: vi.fn().mockImplementation(async () => {
      if (scenario.authContextOverrides?.checkAuth) {
        return scenario.authContextOverrides.checkAuth();
      }
      return Promise.resolve(scenario.isAuthenticated);
    }),
    hasRole: vi.fn().mockImplementation((role: 'super_admin' | 'admin' | 'user') => {
      if (!scenario.user) return false;
      return scenario.user.role === role || scenario.user.roles.includes(role);
    }),
    hasPermission: vi.fn().mockImplementation((permission: string) => {
      if (!scenario.user) return false;
      return scenario.user.permissions?.includes(permission) || false;
    }),
    isAdmin: vi.fn().mockImplementation(() => {
      if (!scenario.user) return false;
      return scenario.user.role === 'admin' || scenario.user.role === 'super_admin';
    }),
    isSuperAdmin: vi.fn().mockImplementation(() => {
      if (!scenario.user) return false;
      return scenario.user.role === 'super_admin';
    })
  };
};

// Enhanced utility functions for creating different authentication scenarios

/**
 * Create mock auth context for super admin scenario
 */
export const createSuperAdminAuthContext = (overrides: Partial<AuthContextType> = {}): AuthContextType => {
  return createMockAuthContext(mockSuperAdminUser, true, overrides);
};

/**
 * Create mock auth context for admin scenario
 */
export const createAdminAuthContext = (overrides: Partial<AuthContextType> = {}): AuthContextType => {
  return createMockAuthContext(mockAdminUser, true, overrides);
};

/**
 * Create mock auth context for regular user scenario
 */
export const createUserAuthContext = (overrides: Partial<AuthContextType> = {}): AuthContextType => {
  return createMockAuthContext(mockRegularUser, true, overrides);
};

/**
 * Create mock auth context for unauthenticated scenario
 */
export const createUnauthenticatedAuthContext = (overrides: Partial<AuthContextType> = {}): AuthContextType => {
  return createMockAuthContext(null, false, overrides);
};

/**
 * Create mock auth context for user with multiple roles
 */
export const createMultiRoleAuthContext = (overrides: Partial<AuthContextType> = {}): AuthContextType => {
  return createMockAuthContext(mockUserWithMultipleRoles, true, overrides);
};

/**
 * Create mock auth context for user with custom permissions
 */
export const createCustomPermissionAuthContext = (overrides: Partial<AuthContextType> = {}): AuthContextType => {
  return createMockAuthContext(mockUserWithCustomPermissions, true, overrides);
};

/**
 * Create mock auth context for specific user and authentication state
 */
export const createCustomAuthContext = (
  user: User | null,
  isAuthenticated: boolean,
  overrides: Partial<AuthContextType> = {}
): AuthContextType => {
  return createMockAuthContext(user, isAuthenticated, overrides);
};

/**
 * Create mock auth context with authentication error scenario
 */
export const createAuthErrorContext = (errorMessage: string = 'Authentication failed'): AuthContextType => {
  return createMockAuthContext(null, false, {
    login: vi.fn().mockRejectedValue(new Error(errorMessage)),
    checkAuth: vi.fn().mockRejectedValue(new Error(errorMessage))
  });
};

/**
 * Create mock auth context with loading state scenario
 */
export const createLoadingAuthContext = (): AuthContextType => {
  return createMockAuthContext(null, false, {
    checkAuth: vi.fn().mockImplementation(() => new Promise(() => {})) // Never resolves
  });
};

// Convenience functions for common test scenarios
export const renderWithSuperAdmin = (ui: React.ReactElement, options: Omit<CustomRenderOptions, 'user' | 'isAuthenticated'> = {}) => {
  return renderWithProviders(ui, {
    ...options,
    testScenario: 'super_admin'
  });
};

export const renderWithAdmin = (ui: React.ReactElement, options: Omit<CustomRenderOptions, 'user' | 'isAuthenticated'> = {}) => {
  return renderWithProviders(ui, {
    ...options,
    testScenario: 'admin'
  });
};

export const renderWithUser = (ui: React.ReactElement, options: Omit<CustomRenderOptions, 'user' | 'isAuthenticated'> = {}) => {
  return renderWithProviders(ui, {
    ...options,
    testScenario: 'user'
  });
};

export const renderWithUnauthenticated = (ui: React.ReactElement, options: Omit<CustomRenderOptions, 'user' | 'isAuthenticated'> = {}) => {
  return renderWithProviders(ui, {
    ...options,
    testScenario: 'unauthenticated'
  });
};

/**
 * Render component with custom auth context
 */
export const renderWithCustomAuth = (
  ui: React.ReactElement, 
  authContext: AuthContextType,
  options: Omit<CustomRenderOptions, 'authValue' | 'user' | 'isAuthenticated'> = {}
) => {
  return renderWithProviders(ui, {
    ...options,
    authValue: authContext
  });
};

/**
 * Render component with authentication error scenario
 */
export const renderWithAuthError = (
  ui: React.ReactElement,
  errorMessage: string = 'Authentication failed',
  options: Omit<CustomRenderOptions, 'authValue'> = {}
) => {
  return renderWithProviders(ui, {
    ...options,
    authValue: createAuthErrorContext(errorMessage)
  });
};

// Mock session functions for testing
export const mockSessionFunctions = (user?: User | null, isAuthenticated: boolean = false) => {
  // Note: vi.mock calls should be done in individual test files, not in utilities
  console.warn('mockSessionFunctions should be replaced with vi.mock calls in individual test files');
};

// Enhanced test isolation and cleanup utilities
export const resetAllMocks = () => {
  vi.clearAllMocks();
  vi.resetAllMocks();
};

export const cleanupTestEnvironment = () => {
  resetAllMocks();
  // Clear any localStorage or sessionStorage if needed
  if (typeof window !== 'undefined') {
    window.localStorage.clear();
    window.sessionStorage.clear();
  }
};

// Advanced scenario builders for complex testing scenarios
export interface AuthTestScenario {
  name: string;
  user: User | null;
  isAuthenticated: boolean;
  authContextOverrides?: Partial<AuthContextType>;
  description: string;
}

export const authTestScenarios: Record<string, AuthTestScenario> = {
  superAdmin: {
    name: 'Super Admin',
    user: mockSuperAdminUser,
    isAuthenticated: true,
    description: 'Authenticated super admin with full permissions'
  },
  admin: {
    name: 'Admin',
    user: mockAdminUser,
    isAuthenticated: true,
    description: 'Authenticated admin with user management permissions'
  },
  user: {
    name: 'Regular User',
    user: mockRegularUser,
    isAuthenticated: true,
    description: 'Authenticated regular user with no special permissions'
  },
  unauthenticated: {
    name: 'Unauthenticated',
    user: null,
    isAuthenticated: false,
    description: 'Not authenticated user'
  },
  multiRole: {
    name: 'Multi-Role User',
    user: mockUserWithMultipleRoles,
    isAuthenticated: true,
    description: 'User with multiple roles'
  },
  customPermissions: {
    name: 'Custom Permissions',
    user: mockUserWithCustomPermissions,
    isAuthenticated: true,
    description: 'User with custom permissions'
  },
  authError: {
    name: 'Authentication Error',
    user: null,
    isAuthenticated: false,
    authContextOverrides: {
      login: vi.fn().mockRejectedValue(new Error('Authentication failed')),
      checkAuth: vi.fn().mockRejectedValue(new Error('Authentication failed'))
    },
    description: 'Authentication error scenario'
  },
  sessionExpired: {
    name: 'Session Expired',
    user: null,
    isAuthenticated: false,
    authContextOverrides: {
      checkAuth: vi.fn().mockResolvedValue(false),
      logout: vi.fn()
    },
    description: 'Expired session scenario'
  }
};

/**
 * Create auth context from predefined scenario
 */
export const createAuthContextFromScenario = (scenarioName: keyof typeof authTestScenarios): AuthContextType => {
  const scenario = authTestScenarios[scenarioName];
  return createMockAuthContext(scenario.user, scenario.isAuthenticated, scenario.authContextOverrides);
};

/**
 * Render component with predefined auth scenario
 */
export const renderWithAuthScenario = (
  ui: React.ReactElement,
  scenarioName: keyof typeof authTestScenarios,
  options: Omit<CustomRenderOptions, 'authValue' | 'user' | 'isAuthenticated'> = {}
) => {
  const authContext = createAuthContextFromScenario(scenarioName);
  return renderWithProviders(ui, {
    ...options,
    authValue: authContext
  });
};

/**
 * Batch test runner for multiple auth scenarios
 */
export const runAuthScenarioTests = (
  testFn: (scenarioName: string, authContext: AuthContextType) => void,
  scenarios: (keyof typeof authTestScenarios)[] = ['superAdmin', 'admin', 'user', 'unauthenticated']
) => {
  scenarios.forEach(scenarioName => {
    const authContext = createAuthContextFromScenario(scenarioName);
    testFn(scenarioName, authContext);
  });
};

// Permission testing utilities
export const createPermissionTestMatrix = (permissions: string[]) => {
  return permissions.map(permission => ({
    permission,
    superAdminShouldHave: true,
    adminShouldHave: ['user_management', 'user_create', 'user_edit', 'user_delete'].includes(permission),
    userShouldHave: false
  }));
};

export const testPermissionMatrix = (
  authContext: AuthContextType,
  permissionMatrix: ReturnType<typeof createPermissionTestMatrix>
) => {
  return permissionMatrix.map(({ permission, superAdminShouldHave, adminShouldHave, userShouldHave }) => {
    const hasPermission = authContext.hasPermission(permission);
    const user = authContext.user;
    
    if (!user) return { permission, result: false, expected: false, passed: true };
    
    let expected = false;
    if (user.role === 'super_admin') expected = superAdminShouldHave;
    else if (user.role === 'admin') expected = adminShouldHave;
    else expected = userShouldHave;
    
    return {
      permission,
      result: hasPermission,
      expected,
      passed: hasPermission === expected
    };
  });
};

// Enhanced mock creation with better type safety
export const createTestAuthContext = (overrides: Partial<AuthContextType> = {}): AuthContextType => {
  const defaultContext = createMockAuthContext();
  return {
    ...defaultContext,
    ...overrides
  };
};

// Test data factories for creating realistic user data
export const createTestUser = (overrides: Partial<User> = {}): User => {
  const baseUser: User = {
    userId: `test-user-${Date.now()}`,
    email: 'test@example.com',
    roles: ['user'],
    tenantId: 'test-tenant',
    role: 'user',
    permissions: []
  };
  
  return { ...baseUser, ...overrides };
};

export const createTestSuperAdmin = (overrides: Partial<User> = {}): User => {
  return createTestUser({
    userId: `test-super-admin-${Date.now()}`,
    email: 'superadmin@example.com',
    roles: ['super_admin'],
    role: 'super_admin',
    permissions: [
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
    ],
    ...overrides
  });
};

export const createTestAdmin = (overrides: Partial<User> = {}): User => {
  return createTestUser({
    userId: `test-admin-${Date.now()}`,
    email: 'admin@example.com',
    roles: ['admin'],
    role: 'admin',
    permissions: [
      'user_management',
      'user_create',
      'user_edit',
      'user_delete'
    ],
    ...overrides
  });
};

// Validation utilities for testing
export const validateAuthContext = (context: AuthContextType): boolean => {
  const requiredMethods = [
    'login', 'logout', 'checkAuth', 'hasRole', 
    'hasPermission', 'isAdmin', 'isSuperAdmin'
  ];
  
  return requiredMethods.every(method => 
    typeof context[method as keyof AuthContextType] === 'function'
  ) && 
  typeof context.isAuthenticated === 'boolean' &&
  (context.user === null || typeof context.user === 'object');
};

export const validateUser = (user: User): boolean => {
  const requiredFields = ['userId', 'email', 'roles', 'tenantId'];
  return requiredFields.every(field => 
    user[field as keyof User] !== undefined && user[field as keyof User] !== null
  );
};

// Mock credential factories for login testing
export const createTestCredentials = (overrides: Partial<LoginCredentials> = {}): LoginCredentials => {
  return {
    email: 'test@example.com',
    password: 'testpassword123',
    ...overrides
  };
};

export const createTestCredentialsWithMFA = (overrides: Partial<LoginCredentials> = {}): LoginCredentials => {
  return {
    email: 'test@example.com',
    password: 'testpassword123',
    totp_code: '123456',
    ...overrides
  };
};

// Simple hook mocking utilities without vi.mock calls
export const createSimpleMockAuth = (user: User | null = null, isAuthenticated: boolean = false) => ({
  user,
  isAuthenticated,
  login: vi.fn(),
  logout: vi.fn(),
  checkAuth: vi.fn(),
  hasRole: vi.fn(() => false),
  hasPermission: vi.fn(() => false),
  isAdmin: vi.fn(() => false),
  isSuperAdmin: vi.fn(() => false),
});

export const createSimpleMockRole = (role: 'super_admin' | 'admin' | 'user' | null = null) => ({
  role,
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

// Mock UI components that might not be available in test environment
export const mockUIComponents = () => {
  // Note: vi.mock calls should be done in individual test files, not in utilities
  console.warn('mockUIComponents should be replaced with vi.mock calls in individual test files');
};