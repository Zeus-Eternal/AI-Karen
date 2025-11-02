/**
 * Unit tests for useSession React hook
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useSession } from '@/hooks/use-session';

// Mock the session module
vi.mock('@/lib/auth/session', () => ({
  bootSession: vi.fn(),
  ensureToken: vi.fn(),
  isAuthenticated: vi.fn(),
  getCurrentUser: vi.fn(),
  hasRole: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  getSession: vi.fn(),
}));

describe('useSession Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with loading state', () => {
    const { result } = renderHook(() => useSession());
    
    expect(result.current.isLoading).toBe(true);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('should boot session on mount', async () => {
    const { bootSession, isAuthenticated, getCurrentUser } = await import('@/lib/auth/session');
    
    (bootSession as any).mockResolvedValue(undefined);
    (isAuthenticated as any).mockReturnValue(true);
    (getCurrentUser as any).mockReturnValue({
      userId: 'user-123',
      email: 'test@example.com',
      roles: ['user'],
      tenantId: 'tenant-123',
    });

    const { result } = renderHook(() => useSession());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(bootSession).toHaveBeenCalled();
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual({
      userId: 'user-123',
      email: 'test@example.com',
      roles: ['user'],
      tenantId: 'tenant-123',
    });
  });

  it('should handle login', async () => {
    const { login: sessionLogin, isAuthenticated, getCurrentUser } = await import('@/lib/auth/session');
    
    (sessionLogin as any).mockResolvedValue(undefined);
    (isAuthenticated as any).mockReturnValue(true);
    (getCurrentUser as any).mockReturnValue({
      userId: 'user-123',
      email: 'test@example.com',
      roles: ['user'],
      tenantId: 'tenant-123',
    });

    const { result } = renderHook(() => useSession());

    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });

    expect(sessionLogin).toHaveBeenCalledWith('test@example.com', 'password', undefined);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('should handle logout', async () => {
    const { logout: sessionLogout, isAuthenticated, getCurrentUser } = await import('@/lib/auth/session');
    
    (sessionLogout as any).mockResolvedValue(undefined);
    (isAuthenticated as any).mockReturnValue(false);
    (getCurrentUser as any).mockReturnValue(null);

    const { result } = renderHook(() => useSession());

    await act(async () => {
      await result.current.logout();
    });

    expect(sessionLogout).toHaveBeenCalled();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('should handle role checking', async () => {
    const { hasRole } = await import('@/lib/auth/session');
    
    (hasRole as any).mockImplementation((role: string) => role === 'admin');

    const { result } = renderHook(() => useSession());

    expect(result.current.hasRole('admin')).toBe(true);
    expect(result.current.hasRole('user')).toBe(false);
  });

  it('should handle token refresh', async () => {
    const { ensureToken, isAuthenticated, getCurrentUser } = await import('@/lib/auth/session');
    
    (ensureToken as any).mockResolvedValue(undefined);
    (isAuthenticated as any).mockReturnValue(true);
    (getCurrentUser as any).mockReturnValue({
      userId: 'user-123',
      email: 'test@example.com',
      roles: ['user'],
      tenantId: 'tenant-123',
    });

    const { result } = renderHook(() => useSession());

    await act(async () => {
      await result.current.ensureToken();
    });

    expect(ensureToken).toHaveBeenCalled();
  });

  it('should refresh session state', async () => {
    const { isAuthenticated, getCurrentUser } = await import('@/lib/auth/session');
    
    (isAuthenticated as any).mockReturnValue(true);
    (getCurrentUser as any).mockReturnValue({
      userId: 'user-123',
      email: 'test@example.com',
      roles: ['user'],
      tenantId: 'tenant-123',
    });

    const { result } = renderHook(() => useSession());

    act(() => {
      result.current.refreshSession();
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual({
      userId: 'user-123',
      email: 'test@example.com',
      roles: ['user'],
      tenantId: 'tenant-123',
    });
  });
});