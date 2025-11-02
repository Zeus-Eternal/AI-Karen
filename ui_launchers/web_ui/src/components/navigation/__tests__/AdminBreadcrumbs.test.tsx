
import React from 'react';
import { render, screen } from '@testing-library/react';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { AdminBreadcrumbs } from '../AdminBreadcrumbs';

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
}));

// Mock auth context
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

const mockHasRole = jest.fn();

beforeEach(() => {
  (useAuth as jest.Mock).mockReturnValue({
    hasRole: mockHasRole,

  jest.clearAllMocks();

describe('AdminBreadcrumbs', () => {
  it('does not render for non-admin users', () => {
    (usePathname as jest.Mock).mockReturnValue('/admin');
    mockHasRole.mockReturnValue(false);

    const { container } = render(<AdminBreadcrumbs />);
    expect(container.firstChild).toBeNull();

  it('renders breadcrumbs for admin users', () => {
    (usePathname as jest.Mock).mockReturnValue('/admin/super-admin/system');
    mockHasRole.mockImplementation((role: string) => role === 'super_admin');

    render(<AdminBreadcrumbs />);

    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Super Admin Dashboard')).toBeInTheDocument();
    expect(screen.getByText('System Configuration')).toBeInTheDocument();

  it('makes intermediate breadcrumbs clickable', () => {
    (usePathname as jest.Mock).mockReturnValue('/admin/super-admin/system');
    mockHasRole.mockImplementation((role: string) => role === 'super_admin');

    render(<AdminBreadcrumbs />);

    const homeLink = screen.getByText('Home').closest('a');
    const superAdminLink = screen.getByText('Super Admin Dashboard').closest('a');
    const systemConfigSpan = screen.getByText('System Configuration').closest('span');

    expect(homeLink).toHaveAttribute('href', '/');
    expect(superAdminLink).toHaveAttribute('href', '/admin/super-admin');
    expect(systemConfigSpan).not.toHaveAttribute('href'); // Last item should not be a link

  it('shows chevron separators between items', () => {
    (usePathname as jest.Mock).mockReturnValue('/admin/super-admin');
    mockHasRole.mockImplementation((role: string) => role === 'super_admin');

    render(<AdminBreadcrumbs />);

    // Should have chevron icons between breadcrumb items
    const chevrons = screen.getAllByTestId('chevron-right') || 
                    document.querySelectorAll('[data-testid="chevron-right"]') ||
                    document.querySelectorAll('svg');
    
    // At least one separator should be present
    expect(chevrons.length).toBeGreaterThan(0);

  it('handles custom breadcrumb items', () => {
    mockHasRole.mockImplementation((role: string) => role === 'admin');

    const customItems = [
      { label: 'Custom Home', href: '/custom' },
      { label: 'Custom Page', isActive: true },
    ];

    render(<AdminBreadcrumbs customItems={customItems} />);

    expect(screen.getByText('Custom Home')).toBeInTheDocument();
    expect(screen.getByText('Custom Page')).toBeInTheDocument();

  it('handles unmapped routes gracefully', () => {
    (usePathname as jest.Mock).mockReturnValue('/admin/unknown-route');
    mockHasRole.mockImplementation((role: string) => role === 'admin');

    render(<AdminBreadcrumbs />);

    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Unknown Route')).toBeInTheDocument();

  it('does not render for single-level paths', () => {
    (usePathname as jest.Mock).mockReturnValue('/');
    mockHasRole.mockImplementation((role: string) => role === 'admin');

    const { container } = render(<AdminBreadcrumbs />);
    expect(container.firstChild).toBeNull();

  it('sets aria-current for active breadcrumb', () => {
    (usePathname as jest.Mock).mockReturnValue('/admin/super-admin');
    mockHasRole.mockImplementation((role: string) => role === 'super_admin');

    render(<AdminBreadcrumbs />);

    const activeItem = screen.getByText('Super Admin Dashboard').closest('span');
    expect(activeItem).toHaveAttribute('aria-current', 'page');

  it('includes proper ARIA labels for accessibility', () => {
    (usePathname as jest.Mock).mockReturnValue('/admin/super-admin');
    mockHasRole.mockImplementation((role: string) => role === 'super_admin');

    render(<AdminBreadcrumbs />);

    const nav = screen.getByRole('navigation');
    expect(nav).toHaveAttribute('aria-label', 'Breadcrumb');

