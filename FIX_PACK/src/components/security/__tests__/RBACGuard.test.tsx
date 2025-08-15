import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RBACGuard, usePermissions, UserRole, Permission } from '../RBACGuard';

// Mock the required hooks and contexts
const mockTrack = vi.fn();
const mockUseAuth = vi.fn();
const mockUseFeature = vi.fn();

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth()
}));

vi.mock('@/hooks/use-feature', () => ({
  useFeature: (flag?: string) => mockUseFeature(flag)
}));

vi.mock('@/hooks/use-telemetry', () => ({
  useTelemetry: () => ({
    track: mockTrack
  })
}));

// Test component for rendering children
const TestComponent = () => <div data-testid="protected-content">Protected Content</div>;

describe('RBACGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseFeature.mockReturnValue(true); // Default: feature enabled
  });

  describe('Authentication Checks', () => {
    it('denies access when user is not authenticated', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: false
      });

      render(
        <RBACGuard fallback={<div data-testid="fallback">Access Denied</div>}>
          <TestComponent />
        </RBACGuard>
      );

      expect(screen.getByTestId('fallback')).toBeInTheDocument();
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(mockTrack).toHaveBeenCalledWith('rbac_access_denied', {
        reason: 'not_authenticated',
        requiredRole: undefined,
        requiredPermission: undefined,
        userId: null
      });
    });

    it('grants access when user is authenticated with no specific requirements', () => {
      mockUseAuth.mockReturnValue({
        user: { user_id: 'user123', roles: ['user'] },
        isAuthenticated: true
      });

      render(
        <RBACGuard>
          <TestComponent />
        </RBACGuard>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
      expect(mockTrack).toHaveBeenCalledWith('rbac_access_granted', {
        userRole: 'user',
        requiredRole: undefined,
        requiredPermission: undefined,
        featureFlag: undefined,
        userId: 'user123'
      });
    });
  });

  describe('Role-Based Access Control', () => {
    const mockUser = { user_id: 'user123', roles: ['user'] };

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isAuthenticated: true
      });
    });

    it('grants access when user has required role', () => {
      render(
        <RBACGuard requiredRole="user">
          <TestComponent />
        </RBACGuard>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('grants access when user has higher role than required', () => {
      mockUseAuth.mockReturnValue({
        user: { user_id: 'admin123', roles: ['admin'] },
        isAuthenticated: true
      });

      render(
        <RBACGuard requiredRole="user">
          <TestComponent />
        </RBACGuard>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('denies access when user has insufficient role', () => {
      render(
        <RBACGuard 
          requiredRole="admin" 
          fallback={<div data-testid="insufficient-role">Need Admin Role</div>}
        >
          <TestComponent />
        </RBACGuard>
      );

      expect(screen.getByTestId('insufficient-role')).toBeInTheDocument();
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(mockTrack).toHaveBeenCalledWith('rbac_access_denied', {
        reason: 'insufficient_role',
        userRole: 'user',
        requiredRole: 'admin',
        userId: 'user123'
      });
    });

    it('handles guest role correctly', () => {
      mockUseAuth.mockReturnValue({
        user: { user_id: 'guest123', roles: [] }, // No roles = guest
        isAuthenticated: true
      });

      render(
        <RBACGuard requiredRole="user" fallback={<div data-testid="guest-denied">Guest Denied</div>}>
          <TestComponent />
        </RBACGuard>
      );

      expect(screen.getByTestId('guest-denied')).toBeInTheDocument();
    });
  });

  describe('Permission-Based Access Control', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: { user_id: 'user123', roles: ['user'] },
        isAuthenticated: true
      });
    });

    it('grants access when user has required permission', () => {
      render(
        <RBACGuard requiredPermission="chat.send">
          <TestComponent />
        </RBACGuard>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('denies access when user lacks required permission', () => {
      render(
        <RBACGuard 
          requiredPermission="admin.settings" 
          fallback={<div data-testid="no-permission">No Permission</div>}
        >
          <TestComponent />
        </RBACGuard>
      );

      expect(screen.getByTestId('no-permission')).toBeInTheDocument();
      expect(mockTrack).toHaveBeenCalledWith('rbac_access_denied', {
        reason: 'insufficient_permission',
        userRole: 'user',
        requiredPermission: 'admin.settings',
        userPermissions: expect.arrayContaining(['chat.send', 'chat.code_assistance']),
        userId: 'user123'
      });
    });

    it('works with admin permissions', () => {
      mockUseAuth.mockReturnValue({
        user: { user_id: 'admin123', roles: ['admin'] },
        isAuthenticated: true
      });

      render(
        <RBACGuard requiredPermission="admin.settings">
          <TestComponent />
        </RBACGuard>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Feature Flag Integration', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: { user_id: 'user123', roles: ['user'] },
        isAuthenticated: true
      });
    });

    it('denies access when feature flag is disabled', () => {
      mockUseFeature.mockReturnValue(false);

      render(
        <RBACGuard 
          featureFlag="chat.streaming" 
          fallback={<div data-testid="feature-disabled">Feature Disabled</div>}
        >
          <TestComponent />
        </RBACGuard>
      );

      expect(screen.getByTestId('feature-disabled')).toBeInTheDocument();
      expect(mockTrack).toHaveBeenCalledWith('rbac_access_denied', {
        reason: 'feature_disabled',
        featureFlag: 'chat.streaming',
        userId: 'user123'
      });
    });

    it('grants access when feature flag is enabled', () => {
      mockUseFeature.mockReturnValue(true);

      render(
        <RBACGuard featureFlag="chat.streaming">
          <TestComponent />
        </RBACGuard>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Combined Requirements', () => {
    it('requires all conditions to be met', () => {
      mockUseAuth.mockReturnValue({
        user: { user_id: 'admin123', roles: ['admin'] },
        isAuthenticated: true
      });
      mockUseFeature.mockReturnValue(true);

      render(
        <RBACGuard 
          requiredRole="admin" 
          requiredPermission="admin.settings" 
          featureFlag="admin.panel"
        >
          <TestComponent />
        </RBACGuard>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('denies access if any condition fails', () => {
      mockUseAuth.mockReturnValue({
        user: { user_id: 'user123', roles: ['user'] }, // Insufficient role
        isAuthenticated: true
      });
      mockUseFeature.mockReturnValue(true);

      render(
        <RBACGuard 
          requiredRole="admin" 
          requiredPermission="admin.settings" 
          featureFlag="admin.panel"
          fallback={<div data-testid="combined-denied">Access Denied</div>}
        >
          <TestComponent />
        </RBACGuard>
      );

      expect(screen.getByTestId('combined-denied')).toBeInTheDocument();
    });
  });

  describe('Callback and Styling', () => {
    const mockOnAccessDenied = vi.fn();

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: false
      });
    });

    it('calls onAccessDenied callback when access is denied', () => {
      render(
        <RBACGuard onAccessDenied={mockOnAccessDenied}>
          <TestComponent />
        </RBACGuard>
      );

      expect(mockOnAccessDenied).toHaveBeenCalledWith('Authentication required');
    });

    it('applies custom className when access is granted', () => {
      mockUseAuth.mockReturnValue({
        user: { user_id: 'user123', roles: ['user'] },
        isAuthenticated: true
      });

      const { container } = render(
        <RBACGuard className="custom-rbac-class">
          <TestComponent />
        </RBACGuard>
      );

      expect(container.firstChild).toHaveClass('custom-rbac-class');
      expect(container.firstChild).toHaveAttribute('data-rbac-protected', 'true');
    });
  });
});

describe('usePermissions hook', () => {
  // Note: This would need to be tested with renderHook from @testing-library/react
  // For now, we'll test the logic through the component tests above
  
  it('should be tested with renderHook in a real implementation', () => {
    // This is a placeholder - in a real implementation, you would use:
    // const { result } = renderHook(() => usePermissions(), {
    //   wrapper: ({ children }) => (
    //     <AuthProvider>
    //       <FeatureFlagsProvider>
    //         {children}
    //       </FeatureFlagsProvider>
    //     </AuthProvider>
    //   )
    // });
    expect(true).toBe(true);
  });
});

describe('Role Hierarchy', () => {
  const testCases: Array<{
    userRole: UserRole;
    requiredRole: UserRole;
    shouldHaveAccess: boolean;
  }> = [
    { userRole: 'guest', requiredRole: 'guest', shouldHaveAccess: true },
    { userRole: 'user', requiredRole: 'guest', shouldHaveAccess: true },
    { userRole: 'guest', requiredRole: 'user', shouldHaveAccess: false },
    { userRole: 'admin', requiredRole: 'user', shouldHaveAccess: true },
    { userRole: 'moderator', requiredRole: 'admin', shouldHaveAccess: false },
    { userRole: 'developer', requiredRole: 'moderator', shouldHaveAccess: true },
  ];

  testCases.forEach(({ userRole, requiredRole, shouldHaveAccess }) => {
    it(`${userRole} ${shouldHaveAccess ? 'should' : 'should not'} have access to ${requiredRole} content`, () => {
      mockUseAuth.mockReturnValue({
        user: { user_id: 'test123', roles: [userRole] },
        isAuthenticated: true
      });

      render(
        <RBACGuard 
          requiredRole={requiredRole}
          fallback={<div data-testid="access-denied">Access Denied</div>}
        >
          <TestComponent />
        </RBACGuard>
      );

      if (shouldHaveAccess) {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();
        expect(screen.queryByTestId('access-denied')).not.toBeInTheDocument();
      } else {
        expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
        expect(screen.getByTestId('access-denied')).toBeInTheDocument();
      }
    });
  });
});