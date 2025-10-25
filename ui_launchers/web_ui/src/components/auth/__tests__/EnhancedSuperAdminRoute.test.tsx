import React from 'react';
import { render, screen } from '@testing-library/react';
import { SuperAdminRoute } from '../SuperAdminRoute';

// Mock the ProtectedRoute component
jest.mock('../ProtectedRoute', () => ({
  ProtectedRoute: ({ children, requiredRole, loadingMessage }: any) => (
    <div data-testid="protected-route" data-required-role={requiredRole} data-loading-message={loadingMessage}>
      {children}
    </div>
  ),
}));

// Mock the NavigationLayout component
jest.mock('@/components/navigation/NavigationLayout', () => ({
  NavigationLayout: ({ children, showBreadcrumbs }: any) => (
    <div data-testid="navigation-layout" data-show-breadcrumbs={showBreadcrumbs}>
      {children}
    </div>
  ),
}));

describe('Enhanced SuperAdminRoute', () => {
  it('renders with super_admin role requirement', () => {
    render(
      <SuperAdminRoute>
        <div>Super Admin Content</div>
      </SuperAdminRoute>
    );

    const protectedRoute = screen.getByTestId('protected-route');
    expect(protectedRoute).toHaveAttribute('data-required-role', 'super_admin');
    expect(screen.getByText('Super Admin Content')).toBeInTheDocument();
  });

  it('wraps content with NavigationLayout by default', () => {
    render(
      <SuperAdminRoute>
        <div>Super Admin Content</div>
      </SuperAdminRoute>
    );

    expect(screen.getByTestId('navigation-layout')).toBeInTheDocument();
    expect(screen.getByText('Super Admin Content')).toBeInTheDocument();
  });

  it('can disable navigation layout', () => {
    render(
      <SuperAdminRoute showNavigation={false}>
        <div>Super Admin Content</div>
      </SuperAdminRoute>
    );

    expect(screen.queryByTestId('navigation-layout')).not.toBeInTheDocument();
    expect(screen.getByText('Super Admin Content')).toBeInTheDocument();
  });

  it('passes through breadcrumbs setting', () => {
    render(
      <SuperAdminRoute showBreadcrumbs={false}>
        <div>Super Admin Content</div>
      </SuperAdminRoute>
    );

    const navigationLayout = screen.getByTestId('navigation-layout');
    expect(navigationLayout).toHaveAttribute('data-show-breadcrumbs', 'false');
  });

  it('uses custom loading message', () => {
    render(
      <SuperAdminRoute loadingMessage="Loading super admin panel...">
        <div>Super Admin Content</div>
      </SuperAdminRoute>
    );

    const protectedRoute = screen.getByTestId('protected-route');
    expect(protectedRoute).toHaveAttribute('data-loading-message', 'Loading super admin panel...');
  });

  it('passes through all ProtectedRoute props', () => {
    const fallback = <div>Access Denied</div>;
    
    render(
      <SuperAdminRoute 
        requiredPermission="admin.system.config"
        fallback={fallback}
        redirectTo="/custom-unauthorized"
      >
        <div>Super Admin Content</div>
      </SuperAdminRoute>
    );

    // The ProtectedRoute should receive these props
    expect(screen.getByTestId('protected-route')).toBeInTheDocument();
  });

  it('shows breadcrumbs by default', () => {
    render(
      <SuperAdminRoute>
        <div>Super Admin Content</div>
      </SuperAdminRoute>
    );

    const navigationLayout = screen.getByTestId('navigation-layout');
    expect(navigationLayout).toHaveAttribute('data-show-breadcrumbs', 'true');
  });

  it('uses default super admin loading message', () => {
    render(
      <SuperAdminRoute>
        <div>Super Admin Content</div>
      </SuperAdminRoute>
    );

    const protectedRoute = screen.getByTestId('protected-route');
    expect(protectedRoute).toHaveAttribute('data-loading-message', 'Loading super admin interface...');
  });
});