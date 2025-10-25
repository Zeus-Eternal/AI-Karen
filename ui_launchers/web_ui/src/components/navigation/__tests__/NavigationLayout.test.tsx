import React from 'react';
import { render, screen } from '@testing-library/react';
import { useAuth } from '@/contexts/AuthContext';
import { NavigationLayout } from '../NavigationLayout';

// Mock auth context
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

// Mock the navigation components
jest.mock('../RoleBasedNavigation', () => ({
  RoleBasedNavigation: ({ variant }: { variant: string }) => (
    <div data-testid={`role-nav-${variant}`}>Role Navigation {variant}</div>
  ),
}));

jest.mock('../AdminBreadcrumbs', () => ({
  AdminBreadcrumbs: () => <div data-testid="admin-breadcrumbs">Admin Breadcrumbs</div>,
}));

jest.mock('@/components/layout/AuthenticatedHeader', () => ({
  AuthenticatedHeader: () => <div data-testid="auth-header">Auth Header</div>,
}));

// Mock sidebar components
jest.mock('@/components/ui/sidebar', () => ({
  SidebarProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="sidebar-provider">{children}</div>
  ),
  Sidebar: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="sidebar">{children}</div>
  ),
  SidebarContent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="sidebar-content">{children}</div>
  ),
  SidebarHeader: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="sidebar-header">{children}</div>
  ),
  SidebarTrigger: () => <div data-testid="sidebar-trigger">Sidebar Trigger</div>,
  SidebarInset: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="sidebar-inset">{children}</div>
  ),
}));

jest.mock('@/components/ui/separator', () => ({
  Separator: () => <div data-testid="separator">Separator</div>,
}));

const mockHasRole = jest.fn();

beforeEach(() => {
  (useAuth as jest.Mock).mockReturnValue({
    isAuthenticated: true,
    hasRole: mockHasRole,
  });
  
  jest.clearAllMocks();
});

describe('NavigationLayout', () => {
  it('renders children without navigation for unauthenticated users', () => {
    (useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      hasRole: mockHasRole,
    });

    render(
      <NavigationLayout>
        <div>Test Content</div>
      </NavigationLayout>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
    expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
    expect(screen.queryByTestId('auth-header')).not.toBeInTheDocument();
  });

  it('renders simple layout for regular users', () => {
    mockHasRole.mockReturnValue(false);

    render(
      <NavigationLayout showSidebar={false}>
        <div>Test Content</div>
      </NavigationLayout>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
    expect(screen.getByText('Karen AI')).toBeInTheDocument();
    expect(screen.getByTestId('role-nav-header')).toBeInTheDocument();
    expect(screen.getByTestId('auth-header')).toBeInTheDocument();
    expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
  });

  it('renders full layout with sidebar for admin users', () => {
    mockHasRole.mockImplementation((role: string) => role === 'admin');

    render(
      <NavigationLayout>
        <div>Test Content</div>
      </NavigationLayout>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar-provider')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar-content')).toBeInTheDocument();
    expect(screen.getByTestId('role-nav-sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar-trigger')).toBeInTheDocument();
  });

  it('shows admin badge for admin users', () => {
    mockHasRole.mockImplementation((role: string) => role === 'admin');

    render(
      <NavigationLayout>
        <div>Test Content</div>
      </NavigationLayout>
    );

    expect(screen.getByText('Admin')).toBeInTheDocument();
    expect(screen.queryByText('Super Admin')).not.toBeInTheDocument();
  });

  it('shows super admin badge for super admin users', () => {
    mockHasRole.mockImplementation((role: string) => role === 'super_admin');

    render(
      <NavigationLayout>
        <div>Test Content</div>
      </NavigationLayout>
    );

    expect(screen.getByText('Super Admin')).toBeInTheDocument();
  });

  it('hides breadcrumbs when showBreadcrumbs is false', () => {
    mockHasRole.mockImplementation((role: string) => role === 'admin');

    render(
      <NavigationLayout showBreadcrumbs={false}>
        <div>Test Content</div>
      </NavigationLayout>
    );

    expect(screen.queryByTestId('admin-breadcrumbs')).not.toBeInTheDocument();
  });

  it('shows breadcrumbs by default for admin users', () => {
    mockHasRole.mockImplementation((role: string) => role === 'admin');

    render(
      <NavigationLayout>
        <div>Test Content</div>
      </NavigationLayout>
    );

    expect(screen.getByTestId('admin-breadcrumbs')).toBeInTheDocument();
  });

  it('hides sidebar when showSidebar is false', () => {
    mockHasRole.mockImplementation((role: string) => role === 'admin');

    render(
      <NavigationLayout showSidebar={false}>
        <div>Test Content</div>
      </NavigationLayout>
    );

    expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
    expect(screen.getByTestId('role-nav-header')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    mockHasRole.mockImplementation((role: string) => role === 'admin');

    const { container } = render(
      <NavigationLayout className="custom-class">
        <div>Test Content</div>
      </NavigationLayout>
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });
});