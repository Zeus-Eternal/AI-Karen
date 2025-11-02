import React from 'react';
import { render, screen, cleanup } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
import { useAuth } from '@/contexts/AuthContext';
import { useRole } from '@/hooks/useRole';
/**
 * Comprehensive Test Coverage for Hook Mocking Utilities
 * 
 * This file tests the hook mocking utilities to ensure they provide
 * proper mock setup, cleanup, and isolation for authentication hooks.
 */





// Mock the hooks at the top level
vi.mock('@/contexts/AuthContext', async () => {
  const actual = await vi.importActual('@/contexts/AuthContext');
  return {
    ...actual,
    useAuth: vi.fn(),
  };
});

vi.mock('@/hooks/useRole', () => ({
  useRole: vi.fn(),
  useHasRole: vi.fn(),
  useHasPermission: vi.fn(),
  useIsAdmin: vi.fn(),
  useIsSuperAdmin: vi.fn(),
}));

  setupUseAuthMock,
  setupUseRoleMock,
  setupAuthAndRoleMocks,
  createUseRoleReturnFromAuth,
  mockScenarios,
  createMockUseAuth,
  createMockUseRole,
  setupCustomAuthMock,
  setupCustomRoleMock,
  resetHookMocks,
  cleanupHookMocks,
  setupConsistentMocks,
  validateMockSetup,
  debugMockState,
  createRealisticMockAuth,
  mockAuthForTest,
  mockAuthWithUser,
  createTestMocks,
  commonMocks,
  setupGlobalMocks,
  resetToDefaultMocks
} from '../hook-mocks';

  mockSuperAdminUser,
  mockAdminUser,
  mockRegularUser,
  createMockAuthContext
} from '../test-providers';



// Test component that uses both hooks
const TestHookComponent: React.FC = () => {
  const { user, isAuthenticated, hasRole, hasPermission, isAdmin, isSuperAdmin } = useAuth();
  const roleData = useRole();

  if (!isAuthenticated) {
    return <div data-testid="unauthenticated">Not authenticated</div>;
  }

  return (
    <div data-testid="authenticated">
      <div data-testid="user-email">{user?.email}</div>
      <div data-testid="auth-role">{user?.role}</div>
      <div data-testid="role-data-role">{roleData.role}</div>
      <div data-testid="auth-is-admin">{isAdmin().toString()}</div>
      <div data-testid="role-is-admin">{roleData.isAdmin.toString()}</div>
      <div data-testid="auth-is-super-admin">{isSuperAdmin().toString()}</div>
      <div data-testid="role-is-super-admin">{roleData.isSuperAdmin.toString()}</div>
      <div data-testid="auth-has-user-management">{hasPermission('user_management').toString()}</div>
      <div data-testid="role-can-manage-users">{roleData.canManageUsers.toString()}</div>
    </div>
  );
};

describe('Hook Mocking Utilities', () => {
  beforeEach(() => {
    resetHookMocks();
  });

  afterEach(() => {
    cleanup();
    cleanupHookMocks();
  });

  describe('Individual Hook Setup', () => {
    it('should setup useAuth mock', () => {
      const mockAuth = createMockAuthContext(mockSuperAdminUser, true);
      const mockId = setupUseAuthMock(() => mockAuth);

      expect(mockId).toBe('useAuth');
      
      // Test that the mock is working
      render(<TestHookComponent />);
      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('superadmin@example.com');
    });

    it('should setup useRole mock', () => {
      const mockRole = createMockUseRole(mockAdminUser);
      const mockId = setupUseRoleMock(() => mockRole);

      expect(mockId).toBe('useRole');
      
      // Need to also setup useAuth for the component to work
      setupUseAuthMock(() => createMockAuthContext(mockAdminUser, true));
      
      render(<TestHookComponent />);
      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('role-data-role')).toHaveTextContent('admin');
    });

    it('should setup both hooks with compatible implementations', () => {
      const authContext = createMockAuthContext(mockSuperAdminUser, true);
      const roleReturn = createUseRoleReturnFromAuth(authContext);
      
      const { authMockId, roleMockId } = setupAuthAndRoleMocks(authContext, roleReturn);

      expect(authMockId).toBe('useAuth');
      expect(roleMockId).toBe('useRole');
      expect(validateMockSetup(authContext, roleReturn)).toBe(true);

      render(<TestHookComponent />);
      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('auth-role')).toHaveTextContent('super_admin');
      expect(screen.getByTestId('role-data-role')).toHaveTextContent('super_admin');
    });
  });

  describe('createUseRoleReturnFromAuth', () => {
    it('should create compatible UseRoleReturn from AuthContext', () => {
      const authContext = createMockAuthContext(mockSuperAdminUser, true);
      const roleReturn = createUseRoleReturnFromAuth(authContext);

      expect(roleReturn.role).toBe('super_admin');
      expect(roleReturn.isAdmin).toBe(true);
      expect(roleReturn.isSuperAdmin).toBe(true);
      expect(roleReturn.canManageUsers).toBe(true);
      expect(roleReturn.canManageAdmins).toBe(true);
      expect(roleReturn.canManageSystem).toBe(true);
      expect(roleReturn.canViewAuditLogs).toBe(true);
    });

    it('should handle admin user correctly', () => {
      const authContext = createMockAuthContext(mockAdminUser, true);
      const roleReturn = createUseRoleReturnFromAuth(authContext);

      expect(roleReturn.role).toBe('admin');
      expect(roleReturn.isAdmin).toBe(true);
      expect(roleReturn.isSuperAdmin).toBe(false);
      expect(roleReturn.canManageUsers).toBe(true);
      expect(roleReturn.canManageAdmins).toBe(false);
      expect(roleReturn.canManageSystem).toBe(false);
      expect(roleReturn.canViewAuditLogs).toBe(false);
    });

    it('should handle regular user correctly', () => {
      const authContext = createMockAuthContext(mockRegularUser, true);
      const roleReturn = createUseRoleReturnFromAuth(authContext);

      expect(roleReturn.role).toBe('user');
      expect(roleReturn.isAdmin).toBe(false);
      expect(roleReturn.isSuperAdmin).toBe(false);
      expect(roleReturn.canManageUsers).toBe(false);
      expect(roleReturn.canManageAdmins).toBe(false);
      expect(roleReturn.canManageSystem).toBe(false);
      expect(roleReturn.canViewAuditLogs).toBe(false);
    });

    it('should handle unauthenticated user correctly', () => {
      const authContext = createMockAuthContext(null, false);
      const roleReturn = createUseRoleReturnFromAuth(authContext);

      expect(roleReturn.role).toBeNull();
      expect(roleReturn.isAdmin).toBe(false);
      expect(roleReturn.isSuperAdmin).toBe(false);
      expect(roleReturn.canManageUsers).toBe(false);
      expect(roleReturn.canManageAdmins).toBe(false);
      expect(roleReturn.canManageSystem).toBe(false);
      expect(roleReturn.canViewAuditLogs).toBe(false);
    });
  });

  describe('Predefined Mock Scenarios', () => {
    it('should setup super admin scenario correctly', () => {
      const { authContext, roleReturn } = mockScenarios.superAdmin();

      expect(validateMockSetup(authContext, roleReturn)).toBe(true);
      expect(authContext.user).toEqual(mockSuperAdminUser);
      expect(authContext.isAuthenticated).toBe(true);
      expect(roleReturn.isSuperAdmin).toBe(true);

      render(<TestHookComponent />);
      expect(screen.getByTestId('auth-is-super-admin')).toHaveTextContent('true');
      expect(screen.getByTestId('role-is-super-admin')).toHaveTextContent('true');
    });

    it('should setup admin scenario correctly', () => {
      const { authContext, roleReturn } = mockScenarios.admin();

      expect(validateMockSetup(authContext, roleReturn)).toBe(true);
      expect(authContext.user).toEqual(mockAdminUser);
      expect(authContext.isAuthenticated).toBe(true);
      expect(roleReturn.isAdmin).toBe(true);
      expect(roleReturn.isSuperAdmin).toBe(false);

      render(<TestHookComponent />);
      expect(screen.getByTestId('auth-is-admin')).toHaveTextContent('true');
      expect(screen.getByTestId('role-is-admin')).toHaveTextContent('true');
      expect(screen.getByTestId('auth-is-super-admin')).toHaveTextContent('false');
      expect(screen.getByTestId('role-is-super-admin')).toHaveTextContent('false');
    });

    it('should setup user scenario correctly', () => {
      const { authContext, roleReturn } = mockScenarios.user();

      expect(validateMockSetup(authContext, roleReturn)).toBe(true);
      expect(authContext.user).toEqual(mockRegularUser);
      expect(authContext.isAuthenticated).toBe(true);
      expect(roleReturn.isAdmin).toBe(false);
      expect(roleReturn.isSuperAdmin).toBe(false);

      render(<TestHookComponent />);
      expect(screen.getByTestId('auth-is-admin')).toHaveTextContent('false');
      expect(screen.getByTestId('role-is-admin')).toHaveTextContent('false');
    });

    it('should setup unauthenticated scenario correctly', () => {
      const { authContext, roleReturn } = mockScenarios.unauthenticated();

      expect(validateMockSetup(authContext, roleReturn)).toBe(true);
      expect(authContext.user).toBeNull();
      expect(authContext.isAuthenticated).toBe(false);
      expect(roleReturn.role).toBeNull();

      render(<TestHookComponent />);
      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });

    it('should setup auth error scenario correctly', () => {
      const { authContext, roleReturn } = mockScenarios.authError();

      expect(validateMockSetup(authContext, roleReturn)).toBe(true);
      expect(authContext.user).toBeNull();
      expect(authContext.isAuthenticated).toBe(false);
      expect(authContext.login).rejects.toThrow('Authentication failed');
      expect(authContext.checkAuth).rejects.toThrow('Authentication failed');

      render(<TestHookComponent />);
      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });

    it('should setup session expired scenario correctly', () => {
      const { authContext, roleReturn } = mockScenarios.sessionExpired();

      expect(validateMockSetup(authContext, roleReturn)).toBe(true);
      expect(authContext.user).toBeNull();
      expect(authContext.isAuthenticated).toBe(false);
      expect(authContext.checkAuth()).resolves.toBe(false);

      render(<TestHookComponent />);
      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });
  });

  describe('Mock Creation Utilities', () => {
    it('should create mock useAuth with defaults', () => {
      const mockAuth = createMockUseAuth();

      expect(mockAuth.user).toBeNull();
      expect(mockAuth.isAuthenticated).toBe(false);
      expect(typeof mockAuth.login).toBe('function');
      expect(typeof mockAuth.hasRole).toBe('function');
      expect(typeof mockAuth.hasPermission).toBe('function');
    });

    it('should create mock useAuth with user and authentication state', () => {
      const mockAuth = createMockUseAuth(mockSuperAdminUser, true);

      expect(mockAuth.user).toEqual(mockSuperAdminUser);
      expect(mockAuth.isAuthenticated).toBe(true);
    });

    it('should create mock useAuth with overrides', () => {
      const customLogin = vi.fn();
      const mockAuth = createMockUseAuth(null, false, { login: customLogin });

      expect(mockAuth.login).toBe(customLogin);
    });

    it('should create mock useRole with defaults', () => {
      const mockRole = createMockUseRole();

      expect(mockRole.role).toBeNull();
      expect(mockRole.isAdmin).toBe(false);
      expect(mockRole.isSuperAdmin).toBe(false);
      expect(typeof mockRole.hasRole).toBe('function');
      expect(typeof mockRole.hasPermission).toBe('function');
    });

    it('should create mock useRole with user', () => {
      const mockRole = createMockUseRole(mockAdminUser);

      expect(mockRole.role).toBe('admin');
      expect(mockRole.isAdmin).toBe(true);
      expect(mockRole.isSuperAdmin).toBe(false);
      expect(mockRole.canManageUsers).toBe(true);
    });

    it('should create mock useRole with overrides', () => {
      const customHasRole = vi.fn();
      const mockRole = createMockUseRole(mockRegularUser, { hasRole: customHasRole });

      expect(mockRole.hasRole).toBe(customHasRole);
    });
  });

  describe('Custom Mock Setup', () => {
    it('should setup custom auth mock', () => {
      const customImplementation = {
        user: mockSuperAdminUser,
        isAuthenticated: true,
        hasPermission: vi.fn(() => false) // Custom behavior
      };

      const mockId = setupCustomAuthMock(customImplementation);
      expect(mockId).toBe('useAuth');

      // Also setup role mock for component to work
      setupUseRoleMock(() => createMockUseRole(mockSuperAdminUser));

      render(<TestHookComponent />);
      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('auth-has-user-management')).toHaveTextContent('false');
    });

    it('should setup custom role mock', () => {
      const customImplementation = {
        role: 'admin' as const,
        isAdmin: false, // Custom behavior
        canManageUsers: false
      };

      const mockId = setupCustomRoleMock(customImplementation);
      expect(mockId).toBe('useRole');

      // Also setup auth mock for component to work
      setupUseAuthMock(() => createMockAuthContext(mockAdminUser, true));

      render(<TestHookComponent />);
      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('role-is-admin')).toHaveTextContent('false');
      expect(screen.getByTestId('role-can-manage-users')).toHaveTextContent('false');
    });
  });

  describe('Mock Cleanup and Reset', () => {
    it('should reset hook mocks', () => {
      const mockFn = vi.fn();
      mockFn('test');
      expect(mockFn).toHaveBeenCalledWith('test');

      resetHookMocks();
      expect(mockFn).not.toHaveBeenCalled();
    });

    it('should cleanup hook mocks', () => {
      setupUseAuthMock(() => createMockAuthContext(mockSuperAdminUser, true));
      setupUseRoleMock(() => createMockUseRole(mockSuperAdminUser));

      cleanupHookMocks();

      // After cleanup, mocks should be reset
      // This is tested by ensuring no errors occur during cleanup
      expect(() => cleanupHookMocks()).not.toThrow();
    });
  });

  describe('Consistent Mock Setup', () => {
    it('should setup consistent mocks for super admin', () => {
      const { authContext, roleReturn } = setupConsistentMocks('superAdmin');

      expect(validateMockSetup(authContext, roleReturn)).toBe(true);
      expect(authContext.user?.role).toBe(roleReturn.role);

      render(<TestHookComponent />);
      expect(screen.getByTestId('auth-role')).toHaveTextContent('super_admin');
      expect(screen.getByTestId('role-data-role')).toHaveTextContent('super_admin');
    });

    it('should setup consistent mocks for admin', () => {
      const { authContext, roleReturn } = setupConsistentMocks('admin');

      expect(validateMockSetup(authContext, roleReturn)).toBe(true);
      expect(authContext.user?.role).toBe(roleReturn.role);

      render(<TestHookComponent />);
      expect(screen.getByTestId('auth-role')).toHaveTextContent('admin');
      expect(screen.getByTestId('role-data-role')).toHaveTextContent('admin');
    });

    it('should setup consistent mocks for user', () => {
      const { authContext, roleReturn } = setupConsistentMocks('user');

      expect(validateMockSetup(authContext, roleReturn)).toBe(true);
      expect(authContext.user?.role).toBe(roleReturn.role);

      render(<TestHookComponent />);
      expect(screen.getByTestId('auth-role')).toHaveTextContent('user');
      expect(screen.getByTestId('role-data-role')).toHaveTextContent('user');
    });

    it('should setup consistent mocks for unauthenticated', () => {
      const { authContext, roleReturn } = setupConsistentMocks('unauthenticated');

      expect(validateMockSetup(authContext, roleReturn)).toBe(true);
      expect(authContext.user).toBeNull();
      expect(roleReturn.role).toBeNull();

      render(<TestHookComponent />);
      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });
  });

  describe('Mock Validation and Debugging', () => {
    it('should validate consistent mock setup', () => {
      const authContext = createMockAuthContext(mockSuperAdminUser, true);
      const roleReturn = createUseRoleReturnFromAuth(authContext);

      expect(validateMockSetup(authContext, roleReturn)).toBe(true);
    });

    it('should detect inconsistent mock setup', () => {
      const authContext = createMockAuthContext(mockSuperAdminUser, true);
      const roleReturn = createMockUseRole(mockRegularUser); // Inconsistent

      expect(validateMockSetup(authContext, roleReturn)).toBe(false);
    });

    it('should provide debug information', () => {
      const authContext = createMockAuthContext(mockSuperAdminUser, true);
      const roleReturn = createUseRoleReturnFromAuth(authContext);

      // Should not throw when debugging
      expect(() => debugMockState(authContext, roleReturn)).not.toThrow();
    });
  });

  describe('Realistic Mock Creation', () => {
    it('should create realistic mock auth', () => {
      const mockAuth = createRealisticMockAuth(mockSuperAdminUser, true);

      expect(mockAuth.user).toEqual(mockSuperAdminUser);
      expect(mockAuth.isAuthenticated).toBe(true);
      expect(mockAuth.hasRole('super_admin')).toBe(true);
      expect(mockAuth.hasRole('admin')).toBe(false);
      expect(mockAuth.hasPermission('admin_management')).toBe(true);
      expect(mockAuth.isAdmin()).toBe(true);
      expect(mockAuth.isSuperAdmin()).toBe(true);
    });

    it('should handle role-based permissions correctly', () => {
      const mockAuth = createRealisticMockAuth(mockAdminUser, true);

      expect(mockAuth.hasPermission('user_management')).toBe(true);
      expect(mockAuth.hasPermission('admin_management')).toBe(false);
      expect(mockAuth.isAdmin()).toBe(true);
      expect(mockAuth.isSuperAdmin()).toBe(false);
    });

    it('should handle users without explicit permissions', () => {
      const userWithoutPermissions = { ...mockRegularUser, permissions: undefined };
      const mockAuth = createRealisticMockAuth(userWithoutPermissions, true);

      expect(mockAuth.hasPermission('user_management')).toBe(false);
      expect(mockAuth.isAdmin()).toBe(false);
      expect(mockAuth.isSuperAdmin()).toBe(false);
    });
  });

  describe('Convenience Functions', () => {
    it('should provide mock auth for test scenarios', () => {
      const { authContext, roleReturn } = mockAuthForTest('superAdmin');

      expect(authContext.user).toEqual(mockSuperAdminUser);
      expect(roleReturn.isSuperAdmin).toBe(true);
    });

    it('should mock auth with specific user', () => {
      const { authContext, roleReturn } = mockAuthWithUser(mockAdminUser, true);

      expect(authContext.user).toEqual(mockAdminUser);
      expect(authContext.isAuthenticated).toBe(true);
      expect(roleReturn.role).toBe('admin');
    });

    it('should create test mocks with options', () => {
      const { authContext, roleReturn } = createTestMocks({
        user: mockSuperAdminUser,
        isAuthenticated: true,
        authOverrides: {
          hasPermission: vi.fn(() => false)
        },
        roleOverrides: {
          canManageUsers: false
        }
      });

      expect(authContext.user).toEqual(mockSuperAdminUser);
      expect(authContext.hasPermission('user_management')).toBe(false);
      expect(roleReturn.canManageUsers).toBe(false);
    });
  });

  describe('Common Mock Implementations', () => {
    it('should provide super admin auth', () => {
      const mockAuth = commonMocks.superAdminAuth();

      expect(mockAuth.user).toEqual(mockSuperAdminUser);
      expect(mockAuth.isAuthenticated).toBe(true);
      expect(mockAuth.isSuperAdmin()).toBe(true);
    });

    it('should provide admin auth', () => {
      const mockAuth = commonMocks.adminAuth();

      expect(mockAuth.user).toEqual(mockAdminUser);
      expect(mockAuth.isAuthenticated).toBe(true);
      expect(mockAuth.isAdmin()).toBe(true);
      expect(mockAuth.isSuperAdmin()).toBe(false);
    });

    it('should provide user auth', () => {
      const mockAuth = commonMocks.userAuth();

      expect(mockAuth.user).toEqual(mockRegularUser);
      expect(mockAuth.isAuthenticated).toBe(true);
      expect(mockAuth.isAdmin()).toBe(false);
    });

    it('should provide unauthenticated auth', () => {
      const mockAuth = commonMocks.unauthenticatedAuth();

      expect(mockAuth.user).toBeNull();
      expect(mockAuth.isAuthenticated).toBe(false);
      expect(mockAuth.isAdmin()).toBe(false);
    });
  });

  describe('Global Mock Setup', () => {
    it('should setup global mocks without errors', () => {
      expect(() => setupGlobalMocks()).not.toThrow();
    });

    it('should reset to default mocks without errors', () => {
      setupGlobalMocks();
      expect(() => resetToDefaultMocks()).not.toThrow();
    });
  });

  describe('Hook Isolation Between Tests', () => {
    it('should isolate hook mocks - first test', () => {
      mockScenarios.superAdmin();
      render(<TestHookComponent />);
      expect(screen.getByTestId('auth-is-super-admin')).toHaveTextContent('true');
    });

    it('should isolate hook mocks - second test', () => {
      // This test should not be affected by the previous test
      mockScenarios.user();
      render(<TestHookComponent />);
      expect(screen.getByTestId('auth-is-admin')).toHaveTextContent('false');
    });

    it('should isolate hook mocks - third test', () => {
      // This test should also be isolated
      mockScenarios.unauthenticated();
      render(<TestHookComponent />);
      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });
  });

  describe('Advanced Mock Patterns', () => {
    it('should support dynamic mock behavior', () => {
      let currentRole = 'user';
      
      const { authContext } = createTestMocks({
        user: mockRegularUser,
        isAuthenticated: true,
        authOverrides: {
          hasRole: vi.fn((role) => role === currentRole)
        }
      });

      expect(authContext.hasRole('user')).toBe(true);
      expect(authContext.hasRole('admin')).toBe(false);

      // Change behavior
      currentRole = 'admin';
      expect(authContext.hasRole('admin')).toBe(true);
      expect(authContext.hasRole('user')).toBe(false);
    });

    it('should support async mock behavior', async () => {
      const { authContext } = createTestMocks({
        user: mockSuperAdminUser,
        isAuthenticated: true,
        authOverrides: {
          checkAuth: vi.fn().mockResolvedValue(true),
          login: vi.fn().mockImplementation(async () => {
            await new Promise(resolve => setTimeout(resolve, 10));
            return Promise.resolve();
          })
        }
      });

      await expect(authContext.checkAuth()).resolves.toBe(true);
      await expect(authContext.login({ email: 'test@example.com', password: 'password' })).resolves.toBeUndefined();
    });

    it('should support conditional mock behavior', () => {
      const { authContext } = createTestMocks({
        user: mockAdminUser,
        isAuthenticated: true,
        authOverrides: {
          hasPermission: vi.fn((permission) => {
            // Custom logic for specific permissions
            if (permission === 'special_permission') return true;
            return mockAdminUser.permissions?.includes(permission) || false;
          })
        }
      });

      expect(authContext.hasPermission('user_management')).toBe(true);
      expect(authContext.hasPermission('admin_management')).toBe(false);
      expect(authContext.hasPermission('special_permission')).toBe(true);
    });
  });
});