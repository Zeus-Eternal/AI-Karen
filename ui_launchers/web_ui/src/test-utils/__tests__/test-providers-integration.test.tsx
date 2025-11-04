import React from 'react';
import { render, screen, cleanup, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useAuth } from '@/contexts/AuthContext';
import { useRole } from '@/hooks/useRole';
/**
 * Integration Tests for Test Providers
 * 
 * This file tests the integration between all test provider utilities
 * to ensure they work together correctly and provide proper isolation.
 */





// Mock the hooks at the top level
vi.mock('@/contexts/AuthContext', async () => {
  const actual = await vi.importActual('@/contexts/AuthContext');
  return {
    ...actual,
    useAuth: vi.fn(),
  };

vi.mock('@/hooks/useRole', () => ({
  useRole: vi.fn(),
  useHasRole: vi.fn(),
  useHasPermission: vi.fn(),
  useIsAdmin: vi.fn(),
  useIsSuperAdmin: vi.fn(),
}));

  renderWithProviders,
  renderWithSuperAdmin,
  renderWithAdmin,
  renderWithUser,
  renderWithUnauthenticated,
  renderWithAuthScenario,
  runAuthScenarioTests,
  authTestScenarios,
  mockSuperAdminUser,
  mockAdminUser,
  mockRegularUser,
  createMockAuthContext,
  resetAllMocks,
  cleanupTestEnvironment
import { } from '../test-providers';

  setupAuthAndRoleMocks,
  mockScenarios,
  createTestMocks,
  resetHookMocks,
  cleanupHookMocks
import { } from '../hook-mocks';

  setupAuthTestEnvironment,
  setupTimerMocks,
  waitForAsync,
  flushPromises
import { } from '../test-setup';



// Complex test component that uses multiple authentication features
const ComplexAuthComponent: React.FC = () => {
  const { user, isAuthenticated, login, logout, hasRole, hasPermission } = useAuth();
  const { role, isAdmin, isSuperAdmin, canManageUsers, canManageAdmins } = useRole();
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      await login({ email: 'test@example.com', password: 'password' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  if (!isAuthenticated) {
    return (
      <div data-testid="login-form">
        <h1>Login Required</h1>
        <Button 
          onClick={handleLogin} 
          disabled={loading}
          data-testid="login-button"
        >
          {loading ? 'Logging in...' : 'Login'}
        </Button>
        {error && <div data-testid="error-message">{error}</div>}
      </div>
    );
  }

  return (
    <div data-testid="dashboard">
      <header data-testid="dashboard-header">
        <h1>Welcome, {user?.email}</h1>
        <div data-testid="user-info">
          <span data-testid="user-role">Role: {role}</span>
          <span data-testid="user-id">ID: {user?.userId}</span>
        </div>
        <Button onClick={handleLogout} data-testid="logout-button">
        </Button>
      </header>

      <main data-testid="dashboard-content">
        {/* Role-based content */}
        {isSuperAdmin && (
          <section data-testid="super-admin-section">
            <h2>Super Admin Panel</h2>
            <div data-testid="super-admin-actions">
              <Button data-testid="manage-system">Manage System</Button>
              <Button data-testid="view-audit-logs">View Audit Logs</Button>
              <Button data-testid="security-settings">Security Settings</Button>
            </div>
          </section>
        )}

        {isAdmin && (
          <section data-testid="admin-section">
            <h2>Admin Panel</h2>
            <div data-testid="admin-actions">
              <Button data-testid="manage-users">Manage Users</Button>
              {canManageAdmins && (
                <Button data-testid="manage-admins">Manage Admins</Button>
              )}
            </div>
          </section>
        )}

        {/* Permission-based content */}
        {hasPermission('user_management') && (
          <section data-testid="user-management-section">
            <h2>User Management</h2>
            <div data-testid="user-management-actions">
              <Button data-testid="create-user">Create User</Button>
              <Button data-testid="edit-user">Edit User</Button>
              <Button data-testid="delete-user">Delete User</Button>
            </div>
          </section>
        )}

        {/* Role checking */}
        <section data-testid="role-checks">
          <div data-testid="has-super-admin-role">{hasRole('super_admin').toString()}</div>
          <div data-testid="has-admin-role">{hasRole('admin').toString()}</div>
          <div data-testid="has-user-role">{hasRole('user').toString()}</div>
        </section>

        {/* Permission checking */}
        <section data-testid="permission-checks">
          <div data-testid="has-user-management">{hasPermission('user_management').toString()}</div>
          <div data-testid="has-admin-management">{hasPermission('admin_management').toString()}</div>
          <div data-testid="has-system-config">{hasPermission('system_config').toString()}</div>
        </section>

        {/* User capabilities */}
        <section data-testid="capabilities">
          <div data-testid="can-manage-users">{canManageUsers.toString()}</div>
          <div data-testid="can-manage-admins">{canManageAdmins.toString()}</div>
        </section>
      </main>
    </div>
  );
};

// Component that tests async behavior
const AsyncAuthComponent: React.FC = () => {
  const { checkAuth, isAuthenticated } = useAuth();
  const [checking, setChecking] = React.useState(false);
  const [authStatus, setAuthStatus] = React.useState<boolean | null>(null);

  const handleCheckAuth = async () => {
    setChecking(true);
    try {
      const result = await checkAuth();
      setAuthStatus(result);
    } catch (error) {
      setAuthStatus(false);
    } finally {
      setChecking(false);
    }
  };

  return (
    <div data-testid="async-auth-component">
      <div data-testid="current-auth-status">{isAuthenticated.toString()}</div>
      <Button 
        onClick={handleCheckAuth} 
        disabled={checking}
        data-testid="check-auth-button"
      >
        {checking ? 'Checking...' : 'Check Auth'}
      </Button>
      {authStatus !== null && (
        <div data-testid="auth-check-result">{authStatus.toString()}</div>
      )}
    </div>
  );
};

describe('Test Providers Integration', () => {
  beforeEach(() => {
    resetAllMocks();
    resetHookMocks();

  afterEach(() => {
    cleanup();
    cleanupTestEnvironment();
    cleanupHookMocks();

  describe('Provider and Hook Mock Integration', () => {
    it('should work with TestAuthProvider and hook mocks together', () => {
      // Setup hook mocks
      const { authContext, roleReturn } = mockScenarios.superAdmin();

      // Render with TestAuthProvider
      render(
        <TestAuthProvider testScenario="super_admin">
          <ComplexAuthComponent />
        </TestAuthProvider>
      );

      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('user-role')).toHaveTextContent('Role: super_admin');
      expect(screen.getByTestId('super-admin-section')).toBeInTheDocument();
      expect(screen.getByTestId('admin-section')).toBeInTheDocument();
      expect(screen.getByTestId('user-management-section')).toBeInTheDocument();

    it('should handle provider override with hook mocks', () => {
      // Setup hook mocks for admin
      mockScenarios.admin();

      // But use super admin provider (provider should take precedence)
      render(
        <TestAuthProvider testScenario="super_admin">
          <ComplexAuthComponent />
        </TestAuthProvider>
      );

      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('super-admin-section')).toBeInTheDocument();

    it('should work with renderWithProviders and hook mocks', () => {
      // Setup hook mocks
      mockScenarios.admin();

      renderWithProviders(<ComplexAuthComponent />, {
        testScenario: 'admin'

      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('admin-section')).toBeInTheDocument();
      expect(screen.queryByTestId('super-admin-section')).not.toBeInTheDocument();


  describe('Comprehensive Role and Permission Testing', () => {
    it('should test super admin with all permissions', () => {
      renderWithSuperAdmin(<ComplexAuthComponent />);

      // Should have access to everything
      expect(screen.getByTestId('super-admin-section')).toBeInTheDocument();
      expect(screen.getByTestId('admin-section')).toBeInTheDocument();
      expect(screen.getByTestId('user-management-section')).toBeInTheDocument();

      // Role checks
      expect(screen.getByTestId('has-super-admin-role')).toHaveTextContent('true');
      expect(screen.getByTestId('has-admin-role')).toHaveTextContent('false');
      expect(screen.getByTestId('has-user-role')).toHaveTextContent('false');

      // Permission checks
      expect(screen.getByTestId('has-user-management')).toHaveTextContent('true');
      expect(screen.getByTestId('has-admin-management')).toHaveTextContent('true');
      expect(screen.getByTestId('has-system-config')).toHaveTextContent('true');

      // Capabilities
      expect(screen.getByTestId('can-manage-users')).toHaveTextContent('true');
      expect(screen.getByTestId('can-manage-admins')).toHaveTextContent('true');

    it('should test admin with limited permissions', () => {
      renderWithAdmin(<ComplexAuthComponent />);

      // Should have admin access but not super admin
      expect(screen.queryByTestId('super-admin-section')).not.toBeInTheDocument();
      expect(screen.getByTestId('admin-section')).toBeInTheDocument();
      expect(screen.getByTestId('user-management-section')).toBeInTheDocument();

      // Role checks
      expect(screen.getByTestId('has-super-admin-role')).toHaveTextContent('false');
      expect(screen.getByTestId('has-admin-role')).toHaveTextContent('true');
      expect(screen.getByTestId('has-user-role')).toHaveTextContent('false');

      // Permission checks
      expect(screen.getByTestId('has-user-management')).toHaveTextContent('true');
      expect(screen.getByTestId('has-admin-management')).toHaveTextContent('false');
      expect(screen.getByTestId('has-system-config')).toHaveTextContent('false');

      // Capabilities
      expect(screen.getByTestId('can-manage-users')).toHaveTextContent('true');
      expect(screen.getByTestId('can-manage-admins')).toHaveTextContent('false');

    it('should test regular user with no special permissions', () => {
      renderWithUser(<ComplexAuthComponent />);

      // Should have minimal access
      expect(screen.queryByTestId('super-admin-section')).not.toBeInTheDocument();
      expect(screen.queryByTestId('admin-section')).not.toBeInTheDocument();
      expect(screen.queryByTestId('user-management-section')).not.toBeInTheDocument();

      // Role checks
      expect(screen.getByTestId('has-super-admin-role')).toHaveTextContent('false');
      expect(screen.getByTestId('has-admin-role')).toHaveTextContent('false');
      expect(screen.getByTestId('has-user-role')).toHaveTextContent('true');

      // Permission checks
      expect(screen.getByTestId('has-user-management')).toHaveTextContent('false');
      expect(screen.getByTestId('has-admin-management')).toHaveTextContent('false');
      expect(screen.getByTestId('has-system-config')).toHaveTextContent('false');

      // Capabilities
      expect(screen.getByTestId('can-manage-users')).toHaveTextContent('false');
      expect(screen.getByTestId('can-manage-admins')).toHaveTextContent('false');

    it('should test unauthenticated user', () => {
      renderWithUnauthenticated(<ComplexAuthComponent />);

      // Should show login form
      expect(screen.getByTestId('login-form')).toBeInTheDocument();
      expect(screen.queryByTestId('dashboard')).not.toBeInTheDocument();


  describe('Authentication Flow Testing', () => {
    it('should handle login flow', async () => {
      // Start with unauthenticated
      const { rerender } = renderWithUnauthenticated(<ComplexAuthComponent />);

      expect(screen.getByTestId('login-form')).toBeInTheDocument();

      // Click login button
      const loginButton = screen.getByTestId('login-button');
      fireEvent.click(loginButton);

      // Should show loading state
      expect(screen.getByText('Logging in...')).toBeInTheDocument();

      // Wait for async operation
      await waitForAsync(10);

      // Switch to authenticated state
      rerender(
        <TestAuthProvider testScenario="super_admin">
          <ComplexAuthComponent />
        </TestAuthProvider>
      );

      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
      expect(screen.getByText('Welcome, superadmin@example.com')).toBeInTheDocument();

    it('should handle login error', async () => {
      // Setup error scenario
      const errorAuth = createMockAuthContext(null, false, {
        login: vi.fn().mockRejectedValue(new Error('Invalid credentials'))

      renderWithProviders(<ComplexAuthComponent />, {
        authValue: errorAuth

      expect(screen.getByTestId('login-form')).toBeInTheDocument();

      // Click login button
      const loginButton = screen.getByTestId('login-button');
      fireEvent.click(loginButton);

      // Wait for error
      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent('Invalid credentials');


    it('should handle logout flow', () => {
      const mockLogout = vi.fn();
      const authContext = createMockAuthContext(mockSuperAdminUser, true, {
        logout: mockLogout

      renderWithProviders(<ComplexAuthComponent />, {
        authValue: authContext

      expect(screen.getByTestId('dashboard')).toBeInTheDocument();

      // Click logout button
      const logoutButton = screen.getByTestId('logout-button');
      fireEvent.click(logoutButton);

      expect(mockLogout).toHaveBeenCalled();


  describe('Async Authentication Testing', () => {
    it('should handle async auth check', async () => {
      const mockCheckAuth = vi.fn().mockResolvedValue(true);
      const authContext = createMockAuthContext(mockSuperAdminUser, true, {
        checkAuth: mockCheckAuth

      renderWithProviders(<AsyncAuthComponent />, {
        authValue: authContext

      expect(screen.getByTestId('current-auth-status')).toHaveTextContent('true');

      // Click check auth button
      const checkButton = screen.getByTestId('check-auth-button');
      fireEvent.click(checkButton);

      // Should show checking state
      expect(screen.getByText('Checking...')).toBeInTheDocument();

      // Wait for result
      await waitFor(() => {
        expect(screen.getByTestId('auth-check-result')).toHaveTextContent('true');

      expect(mockCheckAuth).toHaveBeenCalled();

    it('should handle async auth check error', async () => {
      const mockCheckAuth = vi.fn().mockRejectedValue(new Error('Auth check failed'));
      const authContext = createMockAuthContext(mockSuperAdminUser, true, {
        checkAuth: mockCheckAuth

      renderWithProviders(<AsyncAuthComponent />, {
        authValue: authContext

      // Click check auth button
      const checkButton = screen.getByTestId('check-auth-button');
      fireEvent.click(checkButton);

      // Wait for error result
      await waitFor(() => {
        expect(screen.getByTestId('auth-check-result')).toHaveTextContent('false');

      expect(mockCheckAuth).toHaveBeenCalled();


  describe('Batch Scenario Testing', () => {
    it('should run all scenarios with batch testing', () => {
      const testResults: Array<{ scenario: string; success: boolean }> = [];

      runAuthScenarioTests((scenarioName, authContext) => {
        try {
          renderWithProviders(<ComplexAuthComponent />, {
            authValue: authContext

          // Basic validation that component renders
          const isAuthenticated = authContext.isAuthenticated;
          if (isAuthenticated) {
            expect(screen.getByTestId('dashboard')).toBeInTheDocument();
          } else {
            expect(screen.getByTestId('login-form')).toBeInTheDocument();
          }

          testResults.push({ scenario: scenarioName, success: true });
        } catch (error) {
          testResults.push({ scenario: scenarioName, success: false });
        } finally {
          cleanup();
        }

      // All scenarios should pass
      expect(testResults.every(result => result.success)).toBe(true);
      expect(testResults).toHaveLength(4); // Default scenarios

    it('should test all predefined scenarios individually', () => {
      Object.keys(authTestScenarios).forEach(scenarioName => {
        renderWithAuthScenario(<ComplexAuthComponent />, scenarioName as any);

        const scenario = authTestScenarios[scenarioName];
        if (scenario.isAuthenticated) {
          expect(screen.getByTestId('dashboard')).toBeInTheDocument();
        } else {
          expect(screen.getByTestId('login-form')).toBeInTheDocument();
        }

        cleanup();



  describe('Test Isolation Verification', () => {
    it('should isolate tests properly - test 1', () => {
      renderWithSuperAdmin(<ComplexAuthComponent />);
      expect(screen.getByTestId('super-admin-section')).toBeInTheDocument();

    it('should isolate tests properly - test 2', () => {
      // Should not be affected by previous test
      renderWithUser(<ComplexAuthComponent />);
      expect(screen.queryByTestId('super-admin-section')).not.toBeInTheDocument();

    it('should isolate tests properly - test 3', () => {
      // Should not be affected by previous tests
      renderWithUnauthenticated(<ComplexAuthComponent />);
      expect(screen.getByTestId('login-form')).toBeInTheDocument();


  describe('Complex Integration Scenarios', () => {
    it('should handle multiple provider instances', () => {
      const MultiProviderComponent = () => (
        <div>
          <TestAuthProvider testScenario="super_admin">
            <div data-testid="provider-1">
              <ComplexAuthComponent />
            </div>
          </TestAuthProvider>
          <TestAuthProvider testScenario="user">
            <div data-testid="provider-2">
              <ComplexAuthComponent />
            </div>
          </TestAuthProvider>
        </div>
      );

      render(<MultiProviderComponent />);

      // Both providers should work independently
      const provider1 = screen.getByTestId('provider-1');
      const provider2 = screen.getByTestId('provider-2');

      expect(provider1.querySelector('[data-testid="super-admin-section"]')).toBeInTheDocument();
      expect(provider2.querySelector('[data-testid="super-admin-section"]')).not.toBeInTheDocument();

    it('should handle provider with custom auth context', () => {
      const customAuth = createMockAuthContext(mockAdminUser, true, {
        hasPermission: vi.fn((permission) => {
          // Custom permission logic
          if (permission === 'special_permission') return true;
          return mockAdminUser.permissions?.includes(permission) || false;
        })

      renderWithProviders(<ComplexAuthComponent />, {
        authValue: customAuth

      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('admin-section')).toBeInTheDocument();
      expect(screen.queryByTestId('super-admin-section')).not.toBeInTheDocument();

    it('should handle mixed provider and hook mock setup', () => {
      // Setup hook mocks
      const { authContext } = createTestMocks({
        user: mockSuperAdminUser,
        isAuthenticated: true,
        authOverrides: {
          hasRole: vi.fn((role) => role === 'super_admin')
        }

      // Use provider with different scenario
      renderWithProviders(<ComplexAuthComponent />, {
        testScenario: 'admin' // This should take precedence

      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
      // Provider scenario should win
      expect(screen.getByTestId('user-role')).toHaveTextContent('Role: admin');


  describe('Performance and Memory Testing', () => {
    it('should not leak memory with multiple renders', () => {
      // Render and unmount multiple times
      for (let i = 0; i < 10; i++) {
        const { unmount } = renderWithSuperAdmin(<ComplexAuthComponent />);
        expect(screen.getByTestId('dashboard')).toBeInTheDocument();
        unmount();
      }

      // Should not throw or cause issues
      expect(() => {
        renderWithUser(<ComplexAuthComponent />);
      }).not.toThrow();

    it('should handle rapid scenario switching', () => {
      const scenarios = ['super_admin', 'admin', 'user', 'unauthenticated'] as const;

      scenarios.forEach(scenario => {
        const { unmount } = renderWithProviders(<ComplexAuthComponent />, {
          testScenario: scenario

        if (scenario === 'unauthenticated') {
          expect(screen.getByTestId('login-form')).toBeInTheDocument();
        } else {
          expect(screen.getByTestId('dashboard')).toBeInTheDocument();
        }

        unmount();



  describe('Error Handling Integration', () => {
    it('should handle provider errors gracefully', () => {
      // Invalid scenario should not crash
      expect(() => {
        render(
          <TestAuthProvider testScenario={'invalid' as any}>
            <ComplexAuthComponent />
          </TestAuthProvider>
        );
      }).not.toThrow();

    it('should handle missing context gracefully', () => {
      // Component without provider should handle missing context
      expect(() => {
        render(<ComplexAuthComponent />);
      }).not.toThrow();

    it('should handle malformed auth context', () => {
      const malformedAuth = {
        user: mockSuperAdminUser,
        isAuthenticated: true,
        // Missing required methods - should be handled gracefully
      } as any;

      expect(() => {
        renderWithProviders(<ComplexAuthComponent />, {
          authValue: malformedAuth

      }).not.toThrow();


