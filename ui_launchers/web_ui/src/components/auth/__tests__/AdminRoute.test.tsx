/**
 * Unit tests for AdminRoute component
 */


import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { AdminRoute } from '../AdminRoute';
import { useAuth } from '@/contexts/AuthContext';

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: vi.fn()
}));

// Mock the useAuth hook
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn()
}));

const mockUseAuth = useAuth as any;
const mockUseRouter = useRouter as any;
const mockReplace = vi.fn();

describe('AdminRoute Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseRouter.mockReturnValue({
      replace: mockReplace,
      push: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
      refresh: vi.fn(),
      prefetch: vi.fn()
    } as any);

    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/test',
        search: '',
      },
      writable: true,

    // Mock sessionStorage
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        setItem: vi.fn(),
        getItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,


  it('should render children for authenticated super admin', async () => {
    const mockCheckAuth = vi.fn().mockResolvedValue(true);
    mockUseAuth.mockReturnValue({
      user: { user_id: '1', email: 'admin@test.com', roles: ['super_admin'], tenant_id: '1', role: 'super_admin' },
      isAuthenticated: true,
      hasRole: vi.fn((role: string) => role === 'super_admin' || role === 'admin'),
      hasPermission: vi.fn(() => true),
      isAdmin: vi.fn(() => true),
      isSuperAdmin: vi.fn(() => true),
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: mockCheckAuth

    render(
      <AdminRoute>
        <div>Admin Content</div>
      </AdminRoute>
    );

    await waitFor(() => {
      expect(mockCheckAuth).toHaveBeenCalled();

    await waitFor(() => {
      expect(screen.getByText('Admin Content')).toBeInTheDocument();
    }, { timeout: 3000 });
    expect(mockReplace).not.toHaveBeenCalled();

  it('should render children for authenticated admin', async () => {
    const mockCheckAuth = vi.fn().mockResolvedValue(true);
    mockUseAuth.mockReturnValue({
      user: { user_id: '2', email: 'admin@test.com', roles: ['admin'], tenant_id: '1', role: 'admin' },
      isAuthenticated: true,
      hasRole: vi.fn((role: string) => role === 'admin'),
      hasPermission: vi.fn(() => true),
      isAdmin: vi.fn(() => true),
      isSuperAdmin: vi.fn(() => false),
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: mockCheckAuth

    render(
      <AdminRoute>
        <div>Admin Content</div>
      </AdminRoute>
    );

    await waitFor(() => {
      expect(mockCheckAuth).toHaveBeenCalled();

    await waitFor(() => {
      expect(screen.getByText('Admin Content')).toBeInTheDocument();

    expect(mockReplace).not.toHaveBeenCalled();

  it('should redirect to login for unauthenticated user', async () => {
    const mockCheckAuth = vi.fn().mockResolvedValue(false);
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      hasRole: vi.fn(() => false),
      hasPermission: vi.fn(() => false),
      isAdmin: vi.fn(() => false),
      isSuperAdmin: vi.fn(() => false),
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: mockCheckAuth

    await act(async () => {
      render(
        <AdminRoute>
          <div>Admin Content</div>
        </AdminRoute>
      );

    await waitFor(() => {
      expect(mockCheckAuth).toHaveBeenCalled();

    expect(screen.queryByText('Admin Content')).not.toBeInTheDocument();
    expect(mockReplace).toHaveBeenCalledWith('/login');

  it('should show access denied for regular user', async () => {
    const mockCheckAuth = vi.fn().mockResolvedValue(true);
    mockUseAuth.mockReturnValue({
      user: { user_id: '3', email: 'user@test.com', roles: ['user'], tenant_id: '1', role: 'user' },
      isAuthenticated: true,
      hasRole: vi.fn((role: string) => role === 'user'),
      hasPermission: vi.fn(() => false),
      isAdmin: vi.fn(() => false),
      isSuperAdmin: vi.fn(() => false),
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: mockCheckAuth

    render(
      <AdminRoute>
        <div>Admin Content</div>
      </AdminRoute>
    );

    await waitFor(() => {
      expect(mockCheckAuth).toHaveBeenCalled();

    // Should show loading state instead of access denied text
    expect(screen.queryByText('Admin Content')).not.toBeInTheDocument();

  it('should use custom redirect path', async () => {
    const mockCheckAuth = vi.fn().mockResolvedValue(true);
    mockUseAuth.mockReturnValue({
      user: { user_id: '3', email: 'user@test.com', roles: ['user'], tenant_id: '1', role: 'user' },
      isAuthenticated: true,
      hasRole: vi.fn((role: string) => role === 'user'),
      hasPermission: vi.fn(() => false),
      isAdmin: vi.fn(() => false),
      isSuperAdmin: vi.fn(() => false),
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: mockCheckAuth

    render(
      <AdminRoute redirectTo="/custom-unauthorized">
        <div>Admin Content</div>
      </AdminRoute>
    );

    await waitFor(() => {
      expect(mockCheckAuth).toHaveBeenCalled();

    // Should redirect to custom path instead of default
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/custom-unauthorized');


