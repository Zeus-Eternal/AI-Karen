import React from 'react';
import { render, screen } from '@testing-library/react';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { RoleBasedNavigation } from '../RoleBasedNavigation';
import { vi, beforeEach, describe, it, expect } from 'vitest';

// Mock Next.js navigation
vi.mock('next/navigation', () => ({
  usePathname: vi.fn(),
}));

// Mock auth context
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

const mockHasRole = vi.fn();
const mockHasPermission = vi.fn();

beforeEach(() => {
  (usePathname as any).mockReturnValue('/chat');
  
  (useAuth as any).mockReturnValue({
    user: { role: 'user' },
    hasRole: mockHasRole,
    hasPermission: mockHasPermission,
  });
  
  vi.clearAllMocks();
});

describe('RoleBasedNavigation', () => {
  it('renders basic navigation for regular users', () => {
    mockHasRole.mockImplementation((role: string) => role === 'user');
    mockHasPermission.mockReturnValue(true);

    render(<RoleBasedNavigation />);

    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.queryByText('User Management')).not.toBeInTheDocument();
    expect(screen.queryByText('Super Admin')).not.toBeInTheDocument();
  });

  it('renders admin navigation for admin users', () => {
    mockHasRole.mockImplementation((role: string) => ['admin', 'user'].includes(role));
    mockHasPermission.mockReturnValue(true);

    render(<RoleBasedNavigation />);

    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('User Management')).toBeInTheDocument();
    expect(screen.getByText('Activity Monitor')).toBeInTheDocument();
    expect(screen.queryByText('Super Admin')).not.toBeInTheDocument();
  });

  it('renders full navigation for super admin users', () => {
    mockHasRole.mockImplementation((role: string) => ['super_admin', 'admin', 'user'].includes(role));
    mockHasPermission.mockReturnValue(true);

    render(<RoleBasedNavigation />);

    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('User Management')).toBeInTheDocument();
    expect(screen.getByText('Super Admin')).toBeInTheDocument();
    expect(screen.getByText('Admin Management')).toBeInTheDocument();
    expect(screen.getByText('System Config')).toBeInTheDocument();
    expect(screen.getByText('Security Settings')).toBeInTheDocument();
    expect(screen.getByText('Audit Logs')).toBeInTheDocument();
  });

  it('renders header variant correctly', () => {
    mockHasRole.mockImplementation((role: string) => role === 'user');
    mockHasPermission.mockReturnValue(true);

    render(<RoleBasedNavigation variant="header" />);

    // Header variant should not show descriptions
    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.queryByText('AI conversation interface')).not.toBeInTheDocument();
  });

  it('highlights active navigation item', () => {
    (usePathname as jest.Mock).mockReturnValue('/admin');
    mockHasRole.mockImplementation((role: string) => ['admin', 'user'].includes(role));
    mockHasPermission.mockReturnValue(true);

    render(<RoleBasedNavigation />);

    const userManagementButton = screen.getByText('User Management').closest('button');
    expect(userManagementButton).toHaveClass('bg-secondary');
  });

  it('shows role badges correctly', () => {
    mockHasRole.mockImplementation((role: string) => ['super_admin', 'admin', 'user'].includes(role));
    mockHasPermission.mockReturnValue(true);

    render(<RoleBasedNavigation />);

    expect(screen.getByText('Admin')).toBeInTheDocument();
    expect(screen.getByText('Super Admin')).toBeInTheDocument();
  });

  it('respects permission requirements', () => {
    mockHasRole.mockImplementation((role: string) => ['admin', 'user'].includes(role));
    mockHasPermission.mockImplementation((permission: string) => permission !== 'restricted_permission');

    render(<RoleBasedNavigation />);

    // Should show admin items since role check passes
    expect(screen.getByText('User Management')).toBeInTheDocument();
  });

  it('returns null when no items are visible', () => {
    mockHasRole.mockReturnValue(false);
    mockHasPermission.mockReturnValue(false);

    const { container } = render(<RoleBasedNavigation />);
    expect(container.firstChild).toBeNull();
  });
});