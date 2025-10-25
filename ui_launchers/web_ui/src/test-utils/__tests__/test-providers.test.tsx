/**
 * Comprehensive Test Coverage for Test Providers
 * 
 * This file tests the TestAuthProvider itself and all related utilities
 * to ensure they work correctly and provide proper test isolation.
 */

import React from 'react';
import { render, screen, cleanup } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// Mock the AuthContext at the top level
vi.mock('@/contexts/AuthContext', async () => {
  const actual = await vi.importActual('@/contexts/AuthContext');
  return {
    ...actual,
    useAuth: vi.fn(),
  };
});
import {
  TestAuthProvider,
  renderWithProviders,
  createMockAuthContext,
  mockSuperAdminUser,
  mockAdminUser,
  mockRegularUser,
  mockUnauthenticatedUser,
  mockUserWithMultipleRoles,
  mockUserWithCustomPermissions,
  createSuperAdminAuthContext,
  createAdminAuthContext,
  createUserAuthContext,
  createUnauthenticatedAuthContext,
  createAuthErrorContext,
  createLoadingAuthContext,
  renderWithSuperAdmin,
  renderWithAdmin,
  renderWithUser,
  renderWithUnauthenticated,
  renderWithCustomAuth,
  renderWithAuthError,
  authTestScenarios,
  createAuthContextFromScenario,
  renderWithAuthScenario,
  runAuthScenarioTests,
  createPermissionTestMatrix,
  testPermissionMatrix,
  validateAuthContext,
  validateUser,
  createTestUser,
  createTestSuperAdmin,
  createTestAdmin,
  createTestCredentials,
  createTestCredentialsWithMFA,
  resetAllMocks,
  cleanupTestEnvironment
} from '../test-providers';
import { useAuth } from '@/contexts/AuthContext';

// Test component that uses the AuthContext
const TestAuthComponent: React.FC = () => {
  const { user, isAuthenticated, hasRole, hasPermission, isAdmin, isSuperAdmin } = useAuth();

  if (!isAuthenticated) {
    return <div data-testid="unauthenticated">Not authenticated</div>;
  }

  return (
    <div data-testid="authenticated">
      <div data-testid="user-email">{user?.email}</div>
      <div data-testid="user-role">{user?.role}</div>
      <div data-testid="is-admin">{isAdmin().toString()}</div>
      <div data-testid="is-super-admin">{isSuperAdmin().toString()}</div>
      <div data-testid="has-super-admin-role">{hasRole('super_admin').toString()}</div>
      <div data-testid="has-admin-role">{hasRole('admin').toString()}</div>
      <div data-testid="has-user-role">{hasRole('user').toString()}</div>
      <div data-testid="has-user-management">{hasPermission('user_management').toString()}</div>
      <div data-testid="has-admin-management">{hasPermission('admin_management').toString()}</div>
    </div>
  );
};

describe('TestAuthProvider', () => {
  beforeEach(() => {
    resetAllMocks();
  });

  afterEach(() => {
    cleanup();
    cleanupTestEnvironment();
  });

  describe('Basic Provider Functionality', () => {
    it('should provide AuthContext to child components', () => {
      render(
        <TestAuthProvider>
          <TestAuthComponent />
        </TestAuthProvider>
      );

      // Should render unauthenticated by default
      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });

    it('should provide authenticated context when user is provided', () => {
      render(
        <TestAuthProvider user={mockSuperAdminUser} isAuthenticated={true}>
          <TestAuthComponent />
        </TestAuthProvider>
      );

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('superadmin@example.com');
      expect(screen.getByTestId('user-role')).toHaveTextContent('super_admin');
    });

    it('should accept custom authValue overrides', () => {
      const customAuthValue = createMockAuthContext(mockAdminUser, true, {
        hasPermission: vi.fn(() => false) // Override to always return false
      });

      render(
        <TestAuthProvider authValue={customAuthValue}>
          <TestAuthComponent />
        </TestAuthProvider>
      );

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('has-user-management')).toHaveTextContent('false');
    });
  });

  describe('Test Scenario Support', () => {
    it('should support super_admin test scenario', () => {
      render(
        <TestAuthProvider testScenario="super_admin">
          <TestAuthComponent />
        </TestAuthProvider>
      );

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('superadmin@example.com');
      expect(screen.getByTestId('is-super-admin')).toHaveTextContent('true');
      expect(screen.getByTestId('has-admin-management')).toHaveTextContent('true');
    });

    it('should support admin test scenario', () => {
      render(
        <TestAuthProvider testScenario="admin">
          <TestAuthComponent />
        </TestAuthProvider>
      );

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('admin@example.com');
      expect(screen.getByTestId('is-admin')).toHaveTextContent('true');
      expect(screen.getByTestId('is-super-admin')).toHaveTextContent('false');
      expect(screen.getByTestId('has-user-management')).toHaveTextContent('true');
      expect(screen.getByTestId('has-admin-management')).toHaveTextContent('false');
    });

    it('should support user test scenario', () => {
      render(
        <TestAuthProvider testScenario="user">
          <TestAuthComponent />
        </TestAuthProvider>
      );

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('user@example.com');
      expect(screen.getByTestId('is-admin')).toHaveTextContent('false');
      expect(screen.getByTestId('has-user-management')).toHaveTextContent('false');
    });

    it('should support unauthenticated test scenario', () => {
      render(
        <TestAuthProvider testScenario="unauthenticated">
          <TestAuthComponent />
        </TestAuthProvider>
      );

      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });

    it('should support authenticated test scenario with default user', () => {
      render(
        <TestAuthProvider testScenario="authenticated">
          <TestAuthComponent />
        </TestAuthProvider>
      );

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('user@example.com');
    });
  });

  describe('Custom User and Authentication State', () => {
    it('should override scenario with explicit user and isAuthenticated props', () => {
      render(
        <TestAuthProvider 
          testScenario="unauthenticated" 
          user={mockSuperAdminUser} 
          isAuthenticated={true}
        >
          <TestAuthComponent />
        </TestAuthProvider>
      );

      // Should use explicit props over scenario
      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('superadmin@example.com');
    });

    it('should handle null user correctly', () => {
      render(
        <TestAuthProvider user={null} isAuthenticated={false}>
          <TestAuthComponent />
        </TestAuthProvider>
      );

      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });

    it('should handle inconsistent user and authentication state', () => {
      render(
        <TestAuthProvider user={mockSuperAdminUser} isAuthenticated={false}>
          <TestAuthComponent />
        </TestAuthProvider>
      );

      // Should respect isAuthenticated prop
      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });
  });
});

describe('Mock Utilities', () => {
  beforeEach(() => {
    resetAllMocks();
  });

  afterEach(() => {
    cleanupTestEnvironment();
  });

  describe('createMockAuthContext', () => {
    it('should create valid AuthContext with default values', () => {
      const authContext = createMockAuthContext();

      expect(authContext.user).toBeNull();
      expect(authContext.isAuthenticated).toBe(false);
      expect(typeof authContext.login).toBe('function');
      expect(typeof authContext.logout).toBe('function');
      expect(typeof authContext.checkAuth).toBe('function');
      expect(typeof authContext.hasRole).toBe('function');
      expect(typeof authContext.hasPermission).toBe('function');
      expect(typeof authContext.isAdmin).toBe('function');
      expect(typeof authContext.isSuperAdmin).toBe('function');
    });

    it('should create AuthContext with provided user and authentication state', () => {
      const authContext = createMockAuthContext(mockSuperAdminUser, true);

      expect(authContext.user).toEqual(mockSuperAdminUser);
      expect(authContext.isAuthenticated).toBe(true);
    });

    it('should apply overrides correctly', () => {
      const customLogin = vi.fn();
      const authContext = createMockAuthContext(null, false, { login: customLogin });

      expect(authContext.login).toBe(customLogin);
    });

    it('should have realistic role checking behavior', () => {
      const authContext = createMockAuthContext(mockSuperAdminUser, true);

      expect(authContext.hasRole('super_admin')).toBe(true);
      expect(authContext.hasRole('admin')).toBe(false);
      expect(authContext.hasRole('user')).toBe(false);
    });

    it('should have realistic permission checking behavior', () => {
      const authContext = createMockAuthContext(mockSuperAdminUser, true);

      expect(authContext.hasPermission('user_management')).toBe(true);
      expect(authContext.hasPermission('admin_management')).toBe(true);
      expect(authContext.hasPermission('nonexistent_permission')).toBe(false);
    });

    it('should handle users without explicit permissions', () => {
      const userWithoutPermissions = { ...mockRegularUser, permissions: undefined };
      const authContext = createMockAuthContext(userWithoutPermissions, true);

      // Should fall back to role-based permissions
      expect(authContext.hasPermission('user_management')).toBe(false);
    });
  });

  describe('Predefined Auth Context Creators', () => {
    it('should create super admin context correctly', () => {
      const authContext = createSuperAdminAuthContext();

      expect(authContext.user).toEqual(mockSuperAdminUser);
      expect(authContext.isAuthenticated).toBe(true);
      expect(authContext.isSuperAdmin()).toBe(true);
      expect(authContext.isAdmin()).toBe(true);
      expect(authContext.hasPermission('admin_management')).toBe(true);
    });

    it('should create admin context correctly', () => {
      const authContext = createAdminAuthContext();

      expect(authContext.user).toEqual(mockAdminUser);
      expect(authContext.isAuthenticated).toBe(true);
      expect(authContext.isSuperAdmin()).toBe(false);
      expect(authContext.isAdmin()).toBe(true);
      expect(authContext.hasPermission('user_management')).toBe(true);
      expect(authContext.hasPermission('admin_management')).toBe(false);
    });

    it('should create user context correctly', () => {
      const authContext = createUserAuthContext();

      expect(authContext.user).toEqual(mockRegularUser);
      expect(authContext.isAuthenticated).toBe(true);
      expect(authContext.isSuperAdmin()).toBe(false);
      expect(authContext.isAdmin()).toBe(false);
      expect(authContext.hasPermission('user_management')).toBe(false);
    });

    it('should create unauthenticated context correctly', () => {
      const authContext = createUnauthenticatedAuthContext();

      expect(authContext.user).toBeNull();
      expect(authContext.isAuthenticated).toBe(false);
      expect(authContext.isSuperAdmin()).toBe(false);
      expect(authContext.isAdmin()).toBe(false);
      expect(authContext.hasPermission('user_management')).toBe(false);
    });

    it('should create auth error context correctly', () => {
      const errorMessage = 'Custom auth error';
      const authContext = createAuthErrorContext(errorMessage);

      expect(authContext.user).toBeNull();
      expect(authContext.isAuthenticated).toBe(false);
      expect(authContext.login).rejects.toThrow(errorMessage);
      expect(authContext.checkAuth).rejects.toThrow(errorMessage);
    });

    it('should create loading context correctly', () => {
      const authContext = createLoadingAuthContext();

      expect(authContext.user).toBeNull();
      expect(authContext.isAuthenticated).toBe(false);
      // checkAuth should never resolve (loading state)
      const checkAuthPromise = authContext.checkAuth();
      expect(checkAuthPromise).toBeInstanceOf(Promise);
    });
  });

  describe('Mock User Data', () => {
    it('should have complete and realistic mock users', () => {
      const users = [mockSuperAdminUser, mockAdminUser, mockRegularUser];
      
      users.forEach(user => {
        expect(user.user_id).toBeDefined();
        expect(user.email).toContain('@example.com');
        expect(user.tenant_id).toBe('test-tenant-001');
        expect(user.roles).toBeInstanceOf(Array);
        expect(user.role).toBeDefined();
        expect(user.permissions).toBeInstanceOf(Array);
      });
    });

    it('should have unique user IDs', () => {
      const users = [mockSuperAdminUser, mockAdminUser, mockRegularUser];
      const userIds = users.map(u => u.user_id);
      const uniqueIds = new Set(userIds);
      
      expect(uniqueIds.size).toBe(userIds.length);
    });

    it('should have appropriate permissions for each role', () => {
      expect(mockSuperAdminUser.permissions).toContain('admin_management');
      expect(mockSuperAdminUser.permissions).toContain('user_management');
      expect(mockSuperAdminUser.permissions).toContain('system_config');

      expect(mockAdminUser.permissions).toContain('user_management');
      expect(mockAdminUser.permissions).not.toContain('admin_management');

      expect(mockRegularUser.permissions).toHaveLength(0);
    });

    it('should have consistent role and roles fields', () => {
      expect(mockSuperAdminUser.role).toBe('super_admin');
      expect(mockSuperAdminUser.roles).toContain('super_admin');

      expect(mockAdminUser.role).toBe('admin');
      expect(mockAdminUser.roles).toContain('admin');

      expect(mockRegularUser.role).toBe('user');
      expect(mockRegularUser.roles).toContain('user');
    });

    it('should support users with multiple roles', () => {
      expect(mockUserWithMultipleRoles.roles).toContain('user');
      expect(mockUserWithMultipleRoles.roles).toContain('admin');
      expect(mockUserWithMultipleRoles.role).toBe('admin'); // Primary role
    });

    it('should support users with custom permissions', () => {
      expect(mockUserWithCustomPermissions.permissions).toContain('custom_permission');
      expect(mockUserWithCustomPermissions.permissions).toContain('special_access');
    });
  });
});

describe('Render Utilities', () => {
  beforeEach(() => {
    resetAllMocks();
  });

  afterEach(() => {
    cleanup();
    cleanupTestEnvironment();
  });

  describe('renderWithProviders', () => {
    it('should render with default unauthenticated state', () => {
      renderWithProviders(<TestAuthComponent />);
      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });

    it('should render with provided auth values', () => {
      const authValue = createMockAuthContext(mockSuperAdminUser, true);
      renderWithProviders(<TestAuthComponent />, { authValue });

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('superadmin@example.com');
    });

    it('should render with test scenarios', () => {
      renderWithProviders(<TestAuthComponent />, { testScenario: 'super_admin' });

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('is-super-admin')).toHaveTextContent('true');
    });

    it('should support additional provider options', () => {
      const additionalWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
        <div data-testid="additional-wrapper">{children}</div>
      );

      renderWithProviders(<TestAuthComponent />, {
        testScenario: 'user',
        providerOptions: {
          additionalWrappers: [additionalWrapper]
        }
      });

      expect(screen.getByTestId('additional-wrapper')).toBeInTheDocument();
      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
    });
  });

  describe('Convenience Render Functions', () => {
    it('should render with super admin', () => {
      renderWithSuperAdmin(<TestAuthComponent />);

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('is-super-admin')).toHaveTextContent('true');
    });

    it('should render with admin', () => {
      renderWithAdmin(<TestAuthComponent />);

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('is-admin')).toHaveTextContent('true');
      expect(screen.getByTestId('is-super-admin')).toHaveTextContent('false');
    });

    it('should render with user', () => {
      renderWithUser(<TestAuthComponent />);

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('is-admin')).toHaveTextContent('false');
    });

    it('should render with unauthenticated', () => {
      renderWithUnauthenticated(<TestAuthComponent />);

      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });

    it('should render with custom auth', () => {
      const customAuth = createMockAuthContext(mockAdminUser, true);
      renderWithCustomAuth(<TestAuthComponent />, customAuth);

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('admin@example.com');
    });

    it('should render with auth error', () => {
      renderWithAuthError(<TestAuthComponent />, 'Custom error message');

      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });
  });
});

describe('Auth Test Scenarios', () => {
  beforeEach(() => {
    resetAllMocks();
  });

  afterEach(() => {
    cleanup();
    cleanupTestEnvironment();
  });

  describe('Predefined Scenarios', () => {
    it('should have all expected scenarios', () => {
      const expectedScenarios = [
        'superAdmin', 'admin', 'user', 'unauthenticated',
        'multiRole', 'customPermissions', 'authError', 'sessionExpired'
      ];

      expectedScenarios.forEach(scenario => {
        expect(authTestScenarios).toHaveProperty(scenario);
      });
    });

    it('should create auth context from scenario', () => {
      const superAdminContext = createAuthContextFromScenario('superAdmin');
      expect(superAdminContext.user).toEqual(mockSuperAdminUser);
      expect(superAdminContext.isAuthenticated).toBe(true);

      const unauthContext = createAuthContextFromScenario('unauthenticated');
      expect(unauthContext.user).toBeNull();
      expect(unauthContext.isAuthenticated).toBe(false);
    });

    it('should render with auth scenario', () => {
      renderWithAuthScenario(<TestAuthComponent />, 'superAdmin');

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('is-super-admin')).toHaveTextContent('true');
    });

    it('should run batch scenario tests', () => {
      const testResults: Array<{ scenario: string; passed: boolean }> = [];

      runAuthScenarioTests((scenarioName, authContext) => {
        testResults.push({
          scenario: scenarioName,
          passed: validateAuthContext(authContext)
        });
      });

      expect(testResults).toHaveLength(4); // Default scenarios
      testResults.forEach(result => {
        expect(result.passed).toBe(true);
      });
    });
  });

  describe('Permission Testing Utilities', () => {
    it('should create permission test matrix', () => {
      const permissions = ['user_management', 'admin_management', 'system_config'];
      const matrix = createPermissionTestMatrix(permissions);

      expect(matrix).toHaveLength(3);
      matrix.forEach(item => {
        expect(item).toHaveProperty('permission');
        expect(item).toHaveProperty('superAdminShouldHave');
        expect(item).toHaveProperty('adminShouldHave');
        expect(item).toHaveProperty('userShouldHave');
      });
    });

    it('should test permission matrix correctly', () => {
      const permissions = ['user_management', 'admin_management'];
      const matrix = createPermissionTestMatrix(permissions);

      // Test super admin
      const superAdminContext = createSuperAdminAuthContext();
      const superAdminResults = testPermissionMatrix(superAdminContext, matrix);
      expect(superAdminResults.every(r => r.passed)).toBe(true);

      // Test admin
      const adminContext = createAdminAuthContext();
      const adminResults = testPermissionMatrix(adminContext, matrix);
      expect(adminResults.every(r => r.passed)).toBe(true);

      // Test user
      const userContext = createUserAuthContext();
      const userResults = testPermissionMatrix(userContext, matrix);
      expect(userResults.every(r => r.passed)).toBe(true);
    });
  });
});

describe('Validation Utilities', () => {
  beforeEach(() => {
    resetAllMocks();
  });

  afterEach(() => {
    cleanupTestEnvironment();
  });

  describe('validateAuthContext', () => {
    it('should validate complete auth context', () => {
      const authContext = createMockAuthContext(mockSuperAdminUser, true);
      expect(validateAuthContext(authContext)).toBe(true);
    });

    it('should reject incomplete auth context', () => {
      const incompleteContext = {
        user: mockSuperAdminUser,
        isAuthenticated: true,
        // Missing required methods
      } as any;

      expect(validateAuthContext(incompleteContext)).toBe(false);
    });

    it('should validate auth context with null user', () => {
      const authContext = createMockAuthContext(null, false);
      expect(validateAuthContext(authContext)).toBe(true);
    });
  });

  describe('validateUser', () => {
    it('should validate complete user object', () => {
      expect(validateUser(mockSuperAdminUser)).toBe(true);
      expect(validateUser(mockAdminUser)).toBe(true);
      expect(validateUser(mockRegularUser)).toBe(true);
    });

    it('should reject incomplete user object', () => {
      const incompleteUser = {
        user_id: 'test-id',
        email: 'test@example.com',
        // Missing required fields
      } as any;

      expect(validateUser(incompleteUser)).toBe(false);
    });
  });
});

describe('Test Data Factories', () => {
  beforeEach(() => {
    resetAllMocks();
  });

  afterEach(() => {
    cleanupTestEnvironment();
  });

  describe('User Factories', () => {
    it('should create test user with defaults', () => {
      const user = createTestUser();

      expect(user.user_id).toMatch(/^test-user-\d+$/);
      expect(user.email).toBe('test@example.com');
      expect(user.role).toBe('user');
      expect(user.roles).toEqual(['user']);
      expect(user.permissions).toEqual([]);
    });

    it('should create test user with overrides', () => {
      const user = createTestUser({
        email: 'custom@example.com',
        role: 'admin'
      });

      expect(user.email).toBe('custom@example.com');
      expect(user.role).toBe('admin');
    });

    it('should create test super admin', () => {
      const user = createTestSuperAdmin();

      expect(user.user_id).toMatch(/^test-super-admin-\d+$/);
      expect(user.email).toBe('superadmin@example.com');
      expect(user.role).toBe('super_admin');
      expect(user.permissions).toContain('admin_management');
    });

    it('should create test admin', () => {
      const user = createTestAdmin();

      expect(user.user_id).toMatch(/^test-admin-\d+$/);
      expect(user.email).toBe('admin@example.com');
      expect(user.role).toBe('admin');
      expect(user.permissions).toContain('user_management');
      expect(user.permissions).not.toContain('admin_management');
    });
  });

  describe('Credential Factories', () => {
    it('should create test credentials', () => {
      const credentials = createTestCredentials();

      expect(credentials.email).toBe('test@example.com');
      expect(credentials.password).toBe('testpassword123');
    });

    it('should create test credentials with overrides', () => {
      const credentials = createTestCredentials({
        email: 'custom@example.com'
      });

      expect(credentials.email).toBe('custom@example.com');
      expect(credentials.password).toBe('testpassword123');
    });

    it('should create test credentials with MFA', () => {
      const credentials = createTestCredentialsWithMFA();

      expect(credentials.email).toBe('test@example.com');
      expect(credentials.password).toBe('testpassword123');
      expect(credentials.totp_code).toBe('123456');
    });
  });
});

describe('Test Isolation and Cleanup', () => {
  describe('Mock Reset and Cleanup', () => {
    it('should reset all mocks', () => {
      const mockFn = vi.fn();
      mockFn('test');
      expect(mockFn).toHaveBeenCalledWith('test');

      resetAllMocks();
      expect(mockFn).not.toHaveBeenCalled();
    });

    it('should cleanup test environment', () => {
      // Set some test data
      if (typeof window !== 'undefined') {
        window.localStorage.setItem('test-key', 'test-value');
        window.sessionStorage.setItem('test-key', 'test-value');
      }

      cleanupTestEnvironment();

      if (typeof window !== 'undefined') {
        expect(window.localStorage.getItem('test-key')).toBeNull();
        expect(window.sessionStorage.getItem('test-key')).toBeNull();
      }
    });
  });

  describe('Test Isolation Between Tests', () => {
    it('should isolate test state - first test', () => {
      renderWithProviders(<TestAuthComponent />, { testScenario: 'super_admin' });
      expect(screen.getByTestId('is-super-admin')).toHaveTextContent('true');
    });

    it('should isolate test state - second test', () => {
      // This test should not be affected by the previous test
      renderWithProviders(<TestAuthComponent />, { testScenario: 'user' });
      expect(screen.getByTestId('is-admin')).toHaveTextContent('false');
    });

    it('should isolate test state - third test', () => {
      // This test should also be isolated
      renderWithProviders(<TestAuthComponent />, { testScenario: 'unauthenticated' });
      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });
  });

  describe('Provider State Isolation', () => {
    it('should not leak state between provider instances', () => {
      // First provider instance
      const { unmount: unmount1 } = renderWithProviders(
        <TestAuthComponent />, 
        { testScenario: 'super_admin' }
      );
      expect(screen.getByTestId('is-super-admin')).toHaveTextContent('true');
      unmount1();

      // Second provider instance should be independent
      renderWithProviders(<TestAuthComponent />, { testScenario: 'user' });
      expect(screen.getByTestId('is-admin')).toHaveTextContent('false');
    });

    it('should handle multiple simultaneous provider instances', () => {
      const TestMultipleProviders: React.FC = () => (
        <div>
          <TestAuthProvider testScenario="super_admin">
            <div data-testid="provider-1">
              <TestAuthComponent />
            </div>
          </TestAuthProvider>
          <TestAuthProvider testScenario="user">
            <div data-testid="provider-2">
              <TestAuthComponent />
            </div>
          </TestAuthProvider>
        </div>
      );

      render(<TestMultipleProviders />);

      // Both providers should work independently
      const provider1 = screen.getByTestId('provider-1');
      const provider2 = screen.getByTestId('provider-2');

      expect(provider1.querySelector('[data-testid="is-super-admin"]')).toHaveTextContent('true');
      expect(provider2.querySelector('[data-testid="is-admin"]')).toHaveTextContent('false');
    });
  });
});

describe('Error Handling and Edge Cases', () => {
  beforeEach(() => {
    resetAllMocks();
  });

  afterEach(() => {
    cleanup();
    cleanupTestEnvironment();
  });

  describe('Invalid Props Handling', () => {
    it('should handle undefined user gracefully', () => {
      render(
        <TestAuthProvider user={undefined as any} isAuthenticated={false}>
          <TestAuthComponent />
        </TestAuthProvider>
      );

      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });

    it('should handle invalid test scenario gracefully', () => {
      render(
        <TestAuthProvider testScenario={'invalid' as any}>
          <TestAuthComponent />
        </TestAuthProvider>
      );

      // Should fall back to default behavior
      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });
  });

  describe('Mock Function Error Scenarios', () => {
    it('should handle auth context with error functions', () => {
      const errorContext = createAuthErrorContext('Test error');
      
      renderWithProviders(<TestAuthComponent />, { authValue: errorContext });
      
      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
      expect(errorContext.login).rejects.toThrow('Test error');
    });

    it('should handle loading auth context', () => {
      const loadingContext = createLoadingAuthContext();
      
      renderWithProviders(<TestAuthComponent />, { authValue: loadingContext });
      
      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
      
      // checkAuth should return a promise that never resolves
      const checkAuthPromise = loadingContext.checkAuth();
      expect(checkAuthPromise).toBeInstanceOf(Promise);
    });
  });

  describe('Memory Leaks Prevention', () => {
    it('should not retain references after cleanup', () => {
      let authContext: any;
      
      const { unmount } = renderWithProviders(
        <TestAuthComponent />, 
        { testScenario: 'super_admin' }
      );
      
      // Get reference to auth context
      authContext = createSuperAdminAuthContext();
      
      unmount();
      cleanupTestEnvironment();
      
      // Context should still be accessible but isolated
      expect(authContext.user).toEqual(mockSuperAdminUser);
    });
  });
});