/**
 * Tests for simplified session functions
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock the API client
vi.mock('@/lib/api-client', () => ({
  getApiClient: vi.fn(() => ({
    get: vi.fn(),
    post: vi.fn(),
  })),
}));

// Mock document.cookie for browser environment
Object.defineProperty(document, 'cookie', {
  writable: true,
  value: '',
});

import { 
  setSession, 
  getSession, 
  clearSession, 
  isSessionValid, 
  hasSessionCookie,
  getCurrentUser,
  hasRole,
  isAuthenticated,
  validateSession,
  login,
  logout,
  type SessionData 
} from '../session';

describe('Session Functions', () => {
  const mockSessionData: SessionData = {
    userId: 'user123',
    email: 'test@example.com',
    roles: ['user', 'admin'],
    tenantId: 'tenant123',
  };

  beforeEach(() => {
    clearSession();
    document.cookie = '';
    vi.clearAllMocks();
  });

  describe('setSession and getSession', () => {
    it('should store and retrieve session data', () => {
      setSession(mockSessionData);
      const retrieved = getSession();
      
      expect(retrieved).toEqual(mockSessionData);
    });

    it('should return null when no session is set', () => {
      expect(getSession()).toBeNull();
    });
  });

  describe('clearSession', () => {
    it('should clear stored session data', () => {
      setSession(mockSessionData);
      expect(getSession()).toEqual(mockSessionData);
      
      clearSession();
      expect(getSession()).toBeNull();
    });
  });

  describe('isSessionValid', () => {
    it('should return true when session exists', () => {
      setSession(mockSessionData);
      expect(isSessionValid()).toBe(true);
    });

    it('should return false when no session exists', () => {
      expect(isSessionValid()).toBe(false);
    });
  });

  describe('hasSessionCookie', () => {
    it('should return true when session cookie exists', () => {
      document.cookie = 'session_id=abc123; path=/';
      expect(hasSessionCookie()).toBe(true);
    });

    it('should return false when session cookie does not exist', () => {
      document.cookie = 'other_cookie=value; path=/';
      expect(hasSessionCookie()).toBe(false);
    });

    it('should return false when no cookies exist', () => {
      document.cookie = '';
      expect(hasSessionCookie()).toBe(false);
    });
  });

  describe('getCurrentUser', () => {
    it('should return current user data when session exists', () => {
      setSession(mockSessionData);
      expect(getCurrentUser()).toEqual(mockSessionData);
    });

    it('should return null when no session exists', () => {
      expect(getCurrentUser()).toBeNull();
    });
  });

  describe('hasRole', () => {
    it('should return true when user has the role', () => {
      setSession(mockSessionData);
      expect(hasRole('admin')).toBe(true);
      expect(hasRole('user')).toBe(true);
    });

    it('should return false when user does not have the role', () => {
      setSession(mockSessionData);
      expect(hasRole('superadmin')).toBe(false);
    });

    it('should return false when no session exists', () => {
      expect(hasRole('admin')).toBe(false);
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when session exists', () => {
      setSession(mockSessionData);
      expect(isAuthenticated()).toBe(true);
    });

    it('should return false when no session exists', () => {
      expect(isAuthenticated()).toBe(false);
    });
  });
});