/**
 * Hook Mocking Strategy Examples
 * 
 * This file demonstrates the proper way to use the new hook mocking utilities
 * for testing authentication-dependent components. It serves as both documentation
 * and validation of the mocking strategy.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { 
  setupAuthAndRoleMocks,
  mockScenarios,
  createTestMocks,
  resetHookMocks,
  cleanupHookMocks,
  validateMockSetup,
  debugMockState,
  renderWithProviders,
  mockSuperAdminUser,
  mockAdminUser,
  mockRegularUser
} from '../test-providers';
import { useAuth } from '@/contexts/AuthContext';
import { useRole } from '@/hooks/useRole';

// Test component that uses both useAuth and useRole hooks
const TestComponent: React.FC = () => {
  const { user, isAuthenticated, hasRole, hasPermission } = useAuth();
  const { role, isAdmin, isSuperAdmin, canManageUsers } = useRole();

  if (!isAuthenticated) {
    return <div data-testid="unauthenticated">Not authenticated</div>;
  }

  return (
    <div data-testid="authenticated">
      <div data-testid="user-email">{user?.email}</div>
      <div data-testid="user-role">{role}</div>
      <div data-testid="is-admin">{isAdmin.toString()}</div>
      <div data-testid="is-super-admin">{isSuperAdmin.toString()}</div>
      <div data-testid="can-manage-users">{canManageUsers.toString()}</div>
      <div data-testid="has-super-admin-role">{hasRole('super_admin').toString()}</div>
      <div data-testid="has-user-management-permission">{hasPermission('user_management').toString()}</div>
    </div>
  );
};

describe('Hook Mocking Strategy Examples', () => {
  beforeEach(() => {
    resetHookMocks();
  });

  afterEach(() => {
    cleanupHookMocks();
  });

  describe('Basic Mock Scenarios', () => {
    it('should work with super admin scenario', () => {
      const { authContext, roleReturn } = mockScenarios.superAdmin();
      
      // Validate that mocks are consistent
      expect(validateMockSetup(authContext, roleReturn)).toBe(true);

      render(<TestComponent />);

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('superadmin@example.com');
      expect(screen.getByTestId('user-role')).toHaveTextContent('super_admin');
      expect(screen.getByTestId('is-admin')).toHaveTextContent('true');
      expect(screen.getByTestId('is-super-admin')).toHaveTextContent('true');
      expect(screen.getByTestId('can-manage-users')).toHaveTextContent('true');
      expect(screen.getByTestId('has-super-admin-role')).toHaveTextContent('true');
      expect(screen.getByTestId('has-user-management-permission')).toHaveTextContent('true');
    });

    it('should work with admin scenario', () => {
      const { authContext, roleReturn } = mockScenarios.admin();
      
      // Validate that mocks are consistent
      expect(validateMockSetup(authContext, roleReturn)).toBe(true);

      render(<TestComponent />);

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('admin@example.com');
      expect(screen.getByTestId('user-role')).toHaveTextContent('admin');
      expect(screen.getByTestId('is-admin')).toHaveTextContent('true');
      expect(screen.getByTestId('is-super-admin')).toHaveTextContent('false');
      expect(screen.getByTestId('can-manage-users')).toHaveTextContent('true');
      expect(screen.getByTestId('has-super-admin-role')).toHaveTextContent('false');
      expect(screen.getByTestId('has-user-management-permission')).toHaveTextContent('true');
    });

    it('should work with regular user scenario', () => {
      const { authContext, roleReturn } = mockScenarios.user();
      
      // Validate that mocks are consistent
      expect(validateMockSetup(authContext, roleReturn)).toBe(true);

      render(<TestComponent />);

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('user@example.com');
      expect(screen.getByTestId('user-role')).toHaveTextContent('user');
      expect(screen.getByTestId('is-admin')).toHaveTextContent('false');
      expect(screen.getByTestId('is-super-admin')).toHaveTextContent('false');
      expect(screen.getByTestId('can-manage-users')).toHaveTextContent('false');
      expect(screen.getByTestId('has-super-admin-role')).toHaveTextContent('false');
      expect(screen.getByTestId('has-user-management-permission')).toHaveTextContent('false');
    });

    it('should work with unauthenticated scenario', () => {
      const { authContext, roleReturn } = mockScenarios.unauthenticated();
      
      // Validate that mocks are consistent
      expect(validateMockSetup(authContext, roleReturn)).toBe(true);

      render(<TestComponent />);

      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
      expect(screen.queryByTestId('authenticated')).not.toBeInTheDocument();
    });
  });

  describe('Custom Mock Creation', () => {
    it('should work with custom test mocks', () => {
      const { authContext, roleReturn } = createTestMocks({
        user: mockSuperAdminUser,
        isAuthenticated: true,
        authOverrides: {
          hasPermission: vi.fn((permission) => permission === 'custom_permission')
        },
        roleOverrides: {
          canManageUsers: false // Override specific role behavior
        }
      });

      // Validate that mocks are consistent
      expect(validateMockSetup(authContext, roleReturn)).toBe(true);

      render(<TestComponent />);

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('superadmin@example.com');
      expect(screen.getByTestId('can-manage-users')).toHaveTextContent('false'); // Overridden
      expect(screen.getByTestId('has-user-management-permission')).toHaveTextContent('false'); // Custom permission logic
    });

    it('should work with renderWithProviders integration', () => {
      renderWithProviders(<TestComponent />, {
        testScenario: 'super_admin'
      });

      expect(screen.getByTestId('authenticated')).toBeInTheDocument();
      expect(screen.getByTestId('user-email')).toHaveTextContent('superadmin@example.com');
      expect(screen.getByTestId('user-role')).toHaveTextContent('super_admin');
    });
  });

  describe('Error Scenarios', () => {
    it('should handle authentication errors', () => {
      const { authContext, roleReturn } = mockScenarios.authError();
      
      // Validate that mocks are consistent
      expect(validateMockSetup(authContext, roleReturn)).toBe(true);

      render(<TestComponent />);

      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });

    it('should handle session expired scenario', () => {
      const { authContext, roleReturn } = mockScenarios.sessionExpired();
      
      // Validate that mocks are consistent
      expect(validateMockSetup(authContext, roleReturn)).toBe(true);

      render(<TestComponent />);

      expect(screen.getByTestId('unauthenticated')).toBeInTheDocument();
    });
  });

  describe('Mock Validation and Debugging', () => {
    it('should validate mock consistency', () => {
      const { authContext, roleReturn } = mockScenarios.superAdmin();
      
      expect(validateMockSetup(authContext, roleReturn)).toBe(true);
      
      // Debug information should be available
      debugMockState(authContext, roleReturn);
      
      // Mock functions should be properly created
      expect(vi.isMockFunction(authContext.login)).toBe(true);
      expect(vi.isMockFunction(authContext.logout)).toBe(true);
      expect(vi.isMockFunction(authContext.hasRole)).toBe(true);
      expect(vi.isMockFunction(authContext.hasPermission)).toBe(true);
      expect(vi.isMockFunction(roleReturn.hasRole)).toBe(true);
      expect(vi.isMockFunction(roleReturn.hasPermission)).toBe(true);
    });

    it('should detect inconsistent mocks', () => {
      const { authContext } = mockScenarios.superAdmin();
      const { roleReturn } = mockScenarios.user(); // Inconsistent role return
      
      expect(validateMockSetup(authContext, roleReturn)).toBe(false);
    });
  });

  describe('Hook Isolation', () => {
    it('should properly isolate tests', () => {
      // First test with super admin
      const { authContext: superAdminAuth } = mockScenarios.superAdmin();
      render(<TestComponent />);
      expect(screen.getByTestId('user-role')).toHaveTextContent('super_admin');
      
      // Clean up and reset
      cleanupHookMocks();
      resetHookMocks();
      
      // Second test with regular user should not be affected by first test
      const { authContext: userAuth } = mockScenarios.user();
      render(<TestComponent />);
      expect(screen.getByTestId('user-role')).toHaveTextContent('user');
    });
  });

  describe('Advanced Mock Patterns', () => {
    it('should support dynamic mock behavior', () => {
      let currentUser = mockRegularUser;
      
      const { authContext, roleReturn } = createTestMocks({
        user: currentUser,
        isAuthenticated: true,
        authOverrides: {
          hasRole: vi.fn((role) => {
            // Dynamic behavior based on current user
            return currentUser.role === role || currentUser.roles.includes(role);
          })
        }
      });

      render(<TestComponent />);
      expect(screen.getByTestId('user-role')).toHaveTextContent('user');
      
      // Change user and verify behavior changes
      currentUser = mockSuperAdminUser;
      expect(authContext.hasRole('super_admin')).toBe(true);
    });

    it('should support async mock behavior', async () => {
      const { authContext } = createTestMocks({
        user: mockSuperAdminUser,
        isAuthenticated: true,
        authOverrides: {
          checkAuth: vi.fn().mockResolvedValue(true),
          login: vi.fn().mockImplementation(async (credentials) => {
            // Simulate async login
            await new Promise(resolve => setTimeout(resolve, 10));
            return Promise.resolve();
          })
        }
      });

      // Test async behavior
      await expect(authContext.checkAuth()).resolves.toBe(true);
      await expect(authContext.login({ email: 'test@example.com', password: 'password' })).resolves.toBeUndefined();
    });
  });
});

// Example of a more complex component test using the new mocking strategy
describe('Complex Component Example', () => {
  const ComplexComponent: React.FC = () => {
    const { user, isAuthenticated, login, logout } = useAuth();
    const { isAdmin, isSuperAdmin, canManageUsers, canManageAdmins } = useRole();

    if (!isAuthenticated) {
      return (
        <div data-testid="login-form">
          <button onClick={() => login({ email: 'test@example.com', password: 'password' })}>
            Login
          </button>
        </div>
      );
    }

    return (
      <div data-testid="dashboard">
        <h1>Welcome, {user?.email}</h1>
        <button onClick={logout} data-testid="logout-button">Logout</button>
        
        {canManageUsers && (
          <div data-testid="user-management">User Management</div>
        )}
        
        {canManageAdmins && (
          <div data-testid="admin-management">Admin Management</div>
        )}
        
        {isAdmin && (
          <div data-testid="admin-panel">Admin Panel</div>
        )}
        
        {isSuperAdmin && (
          <div data-testid="super-admin-panel">Super Admin Panel</div>
        )}
      </div>
    );
  };

  beforeEach(() => {
    resetHookMocks();
  });

  afterEach(() => {
    cleanupHookMocks();
  });

  it('should handle complete authentication flow', async () => {
    // Start with unauthenticated state
    const { authContext: unauthContext } = mockScenarios.unauthenticated();
    
    const { rerender } = render(<ComplexComponent />);
    expect(screen.getByTestId('login-form')).toBeInTheDocument();
    
    // Simulate login
    const loginButton = screen.getByText('Login');
    loginButton.click();
    
    // Verify login was called
    expect(unauthContext.login).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password'
    });
    
    // Switch to authenticated state
    const { authContext: authContext } = mockScenarios.superAdmin();
    
    rerender(<ComplexComponent />);
    
    expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    expect(screen.getByText('Welcome, superadmin@example.com')).toBeInTheDocument();
    expect(screen.getByTestId('user-management')).toBeInTheDocument();
    expect(screen.getByTestId('admin-management')).toBeInTheDocument();
    expect(screen.getByTestId('admin-panel')).toBeInTheDocument();
    expect(screen.getByTestId('super-admin-panel')).toBeInTheDocument();
    
    // Test logout
    const logoutButton = screen.getByTestId('logout-button');
    logoutButton.click();
    
    expect(authContext.logout).toHaveBeenCalled();
  });

  it('should show appropriate UI for different user roles', () => {
    // Test admin user
    mockScenarios.admin();
    render(<ComplexComponent />);
    
    expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    expect(screen.getByTestId('user-management')).toBeInTheDocument();
    expect(screen.queryByTestId('admin-management')).not.toBeInTheDocument();
    expect(screen.getByTestId('admin-panel')).toBeInTheDocument();
    expect(screen.queryByTestId('super-admin-panel')).not.toBeInTheDocument();
  });

  it('should show minimal UI for regular users', () => {
    // Test regular user
    mockScenarios.user();
    render(<ComplexComponent />);
    
    expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    expect(screen.queryByTestId('user-management')).not.toBeInTheDocument();
    expect(screen.queryByTestId('admin-management')).not.toBeInTheDocument();
    expect(screen.queryByTestId('admin-panel')).not.toBeInTheDocument();
    expect(screen.queryByTestId('super-admin-panel')).not.toBeInTheDocument();
  });
});