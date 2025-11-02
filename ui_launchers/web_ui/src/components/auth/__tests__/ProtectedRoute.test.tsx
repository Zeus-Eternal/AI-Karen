
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';

const mockReplace = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: mockReplace }),
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockReplace.mockClear();
    
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


  it('renders children when authenticated', async () => {
    const mockCheckAuth = vi.fn().mockResolvedValue(true);
    (useAuth as any).mockReturnValue({ 
      isAuthenticated: true, 
      checkAuth: mockCheckAuth,
      hasRole: vi.fn(() => true),
      hasPermission: vi.fn(() => true),
      user: { role: 'user' }

    render(
      <ProtectedRoute>
        <div data-testid="child">Child</div>
      </ProtectedRoute>
    );
    
    // Wait for the auth check to complete
    await waitFor(() => {
      expect(mockCheckAuth).toHaveBeenCalled();

    await waitFor(() => {
      expect(screen.getByTestId('child')).toBeInTheDocument();
    }, { timeout: 3000 });

  it('redirects to login when not authenticated', async () => {
    const mockCheckAuth = vi.fn().mockResolvedValue(false);
    (useAuth as any).mockReturnValue({ 
      isAuthenticated: false, 
      checkAuth: mockCheckAuth,
      hasRole: vi.fn(() => false),
      hasPermission: vi.fn(() => false),
      user: null

    await act(async () => {
      render(
        <ProtectedRoute>
          <div data-testid="child">Child</div>
        </ProtectedRoute>
      );

    // Wait for auth check to complete
    await waitFor(() => {
      expect(mockCheckAuth).toHaveBeenCalled();

    // Should redirect to login
    expect(mockReplace).toHaveBeenCalledWith('/login');

  it('renders children when user has required role', async () => {
    const mockCheckAuth = vi.fn().mockResolvedValue(true);
    (useAuth as any).mockReturnValue({ 
      isAuthenticated: true, 
      checkAuth: mockCheckAuth,
      hasRole: vi.fn((role) => role === 'admin'),
      hasPermission: vi.fn(() => true),
      user: { role: 'admin' }

    render(
      <ProtectedRoute requiredRole="admin">
        <div data-testid="child">Admin Content</div>
      </ProtectedRoute>
    );
    
    await waitFor(() => {
      expect(mockCheckAuth).toHaveBeenCalled();

    await waitFor(() => {
      expect(screen.getByTestId('child')).toBeInTheDocument();


  it('redirects to unauthorized when user lacks required role', async () => {
    const mockCheckAuth = vi.fn().mockResolvedValue(true);
    (useAuth as any).mockReturnValue({ 
      isAuthenticated: true, 
      checkAuth: mockCheckAuth,
      hasRole: vi.fn((role) => role !== 'admin'), // User doesn't have admin role
      hasPermission: vi.fn(() => true),
      user: { role: 'user' }

    render(
      <ProtectedRoute requiredRole="admin">
        <div data-testid="child">Admin Content</div>
      </ProtectedRoute>
    );
    
    await waitFor(() => {
      expect(mockCheckAuth).toHaveBeenCalled();

    expect(mockReplace).toHaveBeenCalledWith('/unauthorized');

  it('renders children when user has required permission', async () => {
    const mockCheckAuth = vi.fn().mockResolvedValue(true);
    (useAuth as any).mockReturnValue({ 
      isAuthenticated: true, 
      checkAuth: mockCheckAuth,
      hasRole: vi.fn(() => true),
      hasPermission: vi.fn((permission) => permission === 'special_access'),
      user: { role: 'user' }

    render(
      <ProtectedRoute requiredPermission="special_access">
        <div data-testid="child">Special Content</div>
      </ProtectedRoute>
    );
    
    await waitFor(() => {
      expect(mockCheckAuth).toHaveBeenCalled();

    await waitFor(() => {
      expect(screen.getByTestId('child')).toBeInTheDocument();


  it('redirects to unauthorized when user lacks required permission', async () => {
    const mockCheckAuth = vi.fn().mockResolvedValue(true);
    (useAuth as any).mockReturnValue({ 
      isAuthenticated: true, 
      checkAuth: mockCheckAuth,
      hasRole: vi.fn(() => true),
      hasPermission: vi.fn((permission) => permission !== 'special_access'), // User doesn't have permission
      user: { role: 'user' }

    render(
      <ProtectedRoute requiredPermission="special_access">
        <div data-testid="child">Special Content</div>
      </ProtectedRoute>
    );
    
    await waitFor(() => {
      expect(mockCheckAuth).toHaveBeenCalled();

    expect(mockReplace).toHaveBeenCalledWith('/unauthorized');

  it('renders fallback when provided and access denied', async () => {
    const mockCheckAuth = vi.fn().mockResolvedValue(true);
    (useAuth as any).mockReturnValue({ 
      isAuthenticated: true, 
      checkAuth: mockCheckAuth,
      hasRole: vi.fn(() => false), // User doesn't have required role
      hasPermission: vi.fn(() => true),
      user: { role: 'user' }

    render(
      <ProtectedRoute 
        requiredRole="admin" 
        fallback={<div data-testid="fallback">Access Denied</div>}
      >
        <div data-testid="child">Admin Content</div>
      </ProtectedRoute>
    );
    
    await waitFor(() => {
      expect(mockCheckAuth).toHaveBeenCalled();

    expect(screen.getByTestId('fallback')).toBeInTheDocument();
    expect(screen.queryByTestId('child')).not.toBeInTheDocument();
    expect(mockReplace).not.toHaveBeenCalled();

  it('uses custom redirect path', async () => {
    const mockCheckAuth = vi.fn().mockResolvedValue(true);
    (useAuth as any).mockReturnValue({ 
      isAuthenticated: true, 
      checkAuth: mockCheckAuth,
      hasRole: vi.fn(() => false), // User doesn't have required role
      hasPermission: vi.fn(() => true),
      user: { role: 'user' }

    render(
      <ProtectedRoute requiredRole="admin" redirectTo="/custom-forbidden">
        <div data-testid="child">Admin Content</div>
      </ProtectedRoute>
    );
    
    await waitFor(() => {
      expect(mockCheckAuth).toHaveBeenCalled();

    expect(mockReplace).toHaveBeenCalledWith('/custom-forbidden');

