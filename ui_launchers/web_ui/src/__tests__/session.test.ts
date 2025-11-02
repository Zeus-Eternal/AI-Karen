/**
 * Unit tests for session management functions
 * 
 * Tests in-memory token storage, expiry tracking, token refresh,
 * and auth header injection utilities.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { setSession, getSession, clearSession, isSessionValid, getAuthHeader, bootSession, refreshToken, ensureToken, getCurrentUser, hasRole, isAuthenticated, login, logout, type SessionData } from '@/lib/auth/session';

// Mock the API client
vi.mock('@/lib/api-client', () => ({
  getApiClient: vi.fn(() => ({
    post: vi.fn(),
  })),
}));

describe('Session Management', () => {
  const mockSessionData: SessionData = {
    accessToken: 'mock-access-token',
    expiresAt: Date.now() + 15 * 60 * 1000, // 15 minutes from now
    userId: 'user-123',
    email: 'test@example.com',
    roles: ['user', 'admin'],
    tenantId: 'tenant-123',
  };

  beforeEach(() => {
    // Clear session before each test
    clearSession();
    vi.clearAllMocks();

  afterEach(() => {
    vi.restoreAllMocks();

  describe('Session Storage', () => {
    it('should store and retrieve session data', () => {
      setSession(mockSessionData);
      const retrieved = getSession();
      
      expect(retrieved).toEqual(mockSessionData);

    it('should return null when no session is stored', () => {
      const retrieved = getSession();
      expect(retrieved).toBeNull();

    it('should clear session data', () => {
      setSession(mockSessionData);
      clearSession();
      
      const retrieved = getSession();
      expect(retrieved).toBeNull();


  describe('Session Validation', () => {
    it('should return true for valid session', () => {
      setSession(mockSessionData);
      expect(isSessionValid()).toBe(true);

    it('should return false for expired session', () => {
      const expiredSession: SessionData = {
        ...mockSessionData,
        expiresAt: Date.now() - 1000, // 1 second ago
      };
      
      setSession(expiredSession);
      expect(isSessionValid()).toBe(false);

    it('should return false when no session exists', () => {
      expect(isSessionValid()).toBe(false);

    it('should return false for session expiring within buffer time', () => {
      const soonToExpireSession: SessionData = {
        ...mockSessionData,
        expiresAt: Date.now() + 15 * 1000, // 15 seconds from now (within 30s buffer)
      };
      
      setSession(soonToExpireSession);
      expect(isSessionValid()).toBe(false);


  describe('Auth Header Generation', () => {
    it('should return auth header for valid session', () => {
      setSession(mockSessionData);
      const header = getAuthHeader();
      
      expect(header).toEqual({
        'Authorization': `Bearer ${mockSessionData.accessToken}`,


    it('should return empty object for invalid session', () => {
      const expiredSession: SessionData = {
        ...mockSessionData,
        expiresAt: Date.now() - 1000,
      };
      
      setSession(expiredSession);
      const header = getAuthHeader();
      
      expect(header).toEqual({});

    it('should return empty object when no session exists', () => {
      const header = getAuthHeader();
      expect(header).toEqual({});


  describe('User Data Access', () => {
    it('should return current user data', () => {
      setSession(mockSessionData);
      const user = getCurrentUser();
      
      expect(user).toEqual({
        userId: mockSessionData.userId,
        email: mockSessionData.email,
        roles: mockSessionData.roles,
        tenantId: mockSessionData.tenantId,


    it('should return null when no session exists', () => {
      const user = getCurrentUser();
      expect(user).toBeNull();

    it('should check user roles correctly', () => {
      setSession(mockSessionData);
      
      expect(hasRole('admin')).toBe(true);
      expect(hasRole('user')).toBe(true);
      expect(hasRole('superuser')).toBe(false);

    it('should return false for role check when no session', () => {
      expect(hasRole('admin')).toBe(false);

    it('should check authentication status', () => {
      setSession(mockSessionData);
      expect(isAuthenticated()).toBe(true);
      
      clearSession();
      expect(isAuthenticated()).toBe(false);


  describe('Session Boot and Refresh', () => {
    it('should boot session successfully', async () => {
      const { getApiClient } = await import('@/lib/api-client');
      const mockApiClient = {
        post: vi.fn().mockResolvedValue({
          data: {
            access_token: 'new-access-token',
            expires_in: 900, // 15 minutes
            user_data: {
              user_id: 'user-123',
              email: 'test@example.com',
              roles: ['user'],
              tenant_id: 'tenant-123',
            },
          },
        }),
      };
      
      (getApiClient as any).mockReturnValue(mockApiClient);
      
      await bootSession();
      
      const session = getSession();
      expect(session).not.toBeNull();
      expect(session?.accessToken).toBe('new-access-token');
      expect(session?.userId).toBe('user-123');
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/auth/refresh');

    it('should handle boot session failure silently', async () => {
      const { getApiClient } = await import('@/lib/api-client');
      const mockApiClient = {
        post: vi.fn().mockRejectedValue(new Error('No refresh token')),
      };
      
      (getApiClient as any).mockReturnValue(mockApiClient);
      
      await bootSession();
      
      const session = getSession();
      expect(session).toBeNull();

    it('should refresh token successfully', async () => {
      const { getApiClient } = await import('@/lib/api-client');
      const mockApiClient = {
        post: vi.fn().mockResolvedValue({
          data: {
            access_token: 'refreshed-access-token',
            expires_in: 900,
            user_data: {
              user_id: 'user-123',
              email: 'test@example.com',
              roles: ['user'],
              tenant_id: 'tenant-123',
            },
          },
        }),
      };
      
      (getApiClient as any).mockReturnValue(mockApiClient);
      
      await refreshToken();
      
      const session = getSession();
      expect(session?.accessToken).toBe('refreshed-access-token');
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/auth/refresh');

    it('should handle refresh token failure', async () => {
      const { getApiClient } = await import('@/lib/api-client');
      const mockApiClient = {
        post: vi.fn().mockRejectedValue(new Error('Refresh failed')),
      };
      
      (getApiClient as any).mockReturnValue(mockApiClient);
      
      await expect(refreshToken()).rejects.toThrow('Refresh failed');
      
      const session = getSession();
      expect(session).toBeNull();

    it('should prevent multiple simultaneous refresh attempts', async () => {
      const { getApiClient } = await import('@/lib/api-client');
      const mockApiClient = {
        post: vi.fn().mockImplementation(() => 
          new Promise(resolve => setTimeout(() => resolve({
            data: {
              access_token: 'refreshed-token',
              expires_in: 900,
              user_data: {
                user_id: 'user-123',
                email: 'test@example.com',
                roles: ['user'],
                tenant_id: 'tenant-123',
              },
            },
          }), 100))
        ),
      };
      
      (getApiClient as any).mockReturnValue(mockApiClient);
      
      // Start multiple refresh attempts simultaneously
      const promises = [refreshToken(), refreshToken(), refreshToken()];
      
      await Promise.all(promises);
      
      // Should only make one API call
      expect(mockApiClient.post).toHaveBeenCalledTimes(1);


  describe('Ensure Token', () => {
    it('should boot session when no current session', async () => {
      const { getApiClient } = await import('@/lib/api-client');
      const mockApiClient = {
        post: vi.fn().mockResolvedValue({
          data: {
            access_token: 'new-token',
            expires_in: 900,
            user_data: {
              user_id: 'user-123',
              email: 'test@example.com',
              roles: ['user'],
              tenant_id: 'tenant-123',
            },
          },
        }),
      };
      
      (getApiClient as any).mockReturnValue(mockApiClient);
      
      await ensureToken();
      
      const session = getSession();
      expect(session?.accessToken).toBe('new-token');

    it('should do nothing when session is valid', async () => {
      const { getApiClient } = await import('@/lib/api-client');
      const mockApiClient = {
        post: vi.fn(),
      };
      
      (getApiClient as any).mockReturnValue(mockApiClient);
      
      setSession(mockSessionData);
      
      await ensureToken();
      
      // Should not make any API calls
      expect(mockApiClient.post).not.toHaveBeenCalled();

    it('should refresh token when session is expired', async () => {
      const { getApiClient } = await import('@/lib/api-client');
      const mockApiClient = {
        post: vi.fn().mockResolvedValue({
          data: {
            access_token: 'refreshed-token',
            expires_in: 900,
            user_data: {
              user_id: 'user-123',
              email: 'test@example.com',
              roles: ['user'],
              tenant_id: 'tenant-123',
            },
          },
        }),
      };
      
      (getApiClient as any).mockReturnValue(mockApiClient);
      
      const expiredSession: SessionData = {
        ...mockSessionData,
        expiresAt: Date.now() - 1000,
      };
      
      setSession(expiredSession);
      
      await ensureToken();
      
      const session = getSession();
      expect(session?.accessToken).toBe('refreshed-token');
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/auth/refresh');


  describe('Login and Logout', () => {
    it('should login successfully', async () => {
      const { getApiClient } = await import('@/lib/api-client');
      const mockApiClient = {
        post: vi.fn().mockResolvedValue({
          data: {
            access_token: 'login-token',
            expires_in: 900,
            user_data: {
              user_id: 'user-123',
              email: 'test@example.com',
              roles: ['user'],
              tenant_id: 'tenant-123',
            },
          },
        }),
      };
      
      (getApiClient as any).mockReturnValue(mockApiClient);
      
      await login('test@example.com', 'password');
      
      const session = getSession();
      expect(session?.accessToken).toBe('login-token');
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/auth/login', {
        email: 'test@example.com',
        password: 'password',


    it('should login with TOTP code', async () => {
      const { getApiClient } = await import('@/lib/api-client');
      const mockApiClient = {
        post: vi.fn().mockResolvedValue({
          data: {
            access_token: 'login-token',
            expires_in: 900,
            user_data: {
              user_id: 'user-123',
              email: 'test@example.com',
              roles: ['user'],
              tenant_id: 'tenant-123',
            },
          },
        }),
      };
      
      (getApiClient as any).mockReturnValue(mockApiClient);
      
      await login('test@example.com', 'password', '123456');
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/auth/login', {
        email: 'test@example.com',
        password: 'password',
        totp_code: '123456',


    it('should handle login failure', async () => {
      const { getApiClient } = await import('@/lib/api-client');
      const mockApiClient = {
        post: vi.fn().mockRejectedValue(new Error('Invalid credentials')),
      };
      
      (getApiClient as any).mockReturnValue(mockApiClient);
      
      await expect(login('test@example.com', 'wrong-password')).rejects.toThrow('Invalid credentials');
      
      const session = getSession();
      expect(session).toBeNull();

    it('should logout successfully', async () => {
      const { getApiClient } = await import('@/lib/api-client');
      const mockApiClient = {
        post: vi.fn().mockResolvedValue({}),
      };
      
      (getApiClient as any).mockReturnValue(mockApiClient);
      
      setSession(mockSessionData);
      
      await logout();
      
      const session = getSession();
      expect(session).toBeNull();
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/auth/logout');

    it('should clear session even if logout request fails', async () => {
      const { getApiClient } = await import('@/lib/api-client');
      const mockApiClient = {
        post: vi.fn().mockRejectedValue(new Error('Network error')),
      };
      
      (getApiClient as any).mockReturnValue(mockApiClient);
      
      setSession(mockSessionData);
      
      await logout();
      
      const session = getSession();
      expect(session).toBeNull();


