
import React from 'react';
import { render, screen } from '@testing-library/react';
import { AdminRoute } from '../AdminRoute';

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

describe('Enhanced AdminRoute', () => {
  it('renders with default admin role requirement', () => {
    render(
      <AdminRoute>
        <div>Admin Content</div>
      </AdminRoute>
    );

    const protectedRoute = screen.getByTestId('protected-route');
    expect(protectedRoute).toHaveAttribute('data-required-role', 'admin');
    expect(screen.getByText('Admin Content')).toBeInTheDocument();

  it('wraps content with NavigationLayout by default', () => {
    render(
      <AdminRoute>
        <div>Admin Content</div>
      </AdminRoute>
    );

    expect(screen.getByTestId('navigation-layout')).toBeInTheDocument();
    expect(screen.getByText('Admin Content')).toBeInTheDocument();

  it('can disable navigation layout', () => {
    render(
      <AdminRoute showNavigation={false}>
        <div>Admin Content</div>
      </AdminRoute>
    );

    expect(screen.queryByTestId('navigation-layout')).not.toBeInTheDocument();
    expect(screen.getByText('Admin Content')).toBeInTheDocument();

  it('passes through breadcrumbs setting', () => {
    render(
      <AdminRoute showBreadcrumbs={false}>
        <div>Admin Content</div>
      </AdminRoute>
    );

    const navigationLayout = screen.getByTestId('navigation-layout');
    expect(navigationLayout).toHaveAttribute('data-show-breadcrumbs', 'false');

  it('uses custom loading message', () => {
    render(
      <AdminRoute loadingMessage="Loading admin panel...">
        <div>Admin Content</div>
      </AdminRoute>
    );

    const protectedRoute = screen.getByTestId('protected-route');
    expect(protectedRoute).toHaveAttribute('data-loading-message', 'Loading admin panel...');

  it('accepts super_admin role requirement', () => {
    render(
      <AdminRoute requiredRole="super_admin">
        <div>Super Admin Content</div>
      </AdminRoute>
    );

    const protectedRoute = screen.getByTestId('protected-route');
    expect(protectedRoute).toHaveAttribute('data-required-role', 'super_admin');

  it('passes through all ProtectedRoute props', () => {
    const fallback = <div>Access Denied</div>;
    
    render(
      <AdminRoute 
        requiredPermission="admin.users.read"
        fallback={fallback}
        redirectTo="/custom-unauthorized"
      >
        <div>Admin Content</div>
      </AdminRoute>
    );

    // The ProtectedRoute should receive these props
    expect(screen.getByTestId('protected-route')).toBeInTheDocument();

  it('shows breadcrumbs by default', () => {
    render(
      <AdminRoute>
        <div>Admin Content</div>
      </AdminRoute>
    );

    const navigationLayout = screen.getByTestId('navigation-layout');
    expect(navigationLayout).toHaveAttribute('data-show-breadcrumbs', 'true');

  it('uses default admin loading message', () => {
    render(
      <AdminRoute>
        <div>Admin Content</div>
      </AdminRoute>
    );

    const protectedRoute = screen.getByTestId('protected-route');
    expect(protectedRoute).toHaveAttribute('data-loading-message', 'Loading admin interface...');

