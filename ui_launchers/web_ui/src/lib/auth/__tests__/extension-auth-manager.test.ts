/**
 * Extension Authentication Manager Tests
 * 
 * Tests for the ExtensionAuthManager class to ensure proper
 * token management, refresh logic, and authentication state handling.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ExtensionAuthManager, getExtensionAuthManager } from '../extension-auth-manager';

// Mock dependencies
vi.mock('@/lib/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('@/lib/connection/connection-manager', () => ({
  getConnectionManager: vi.fn(() => ({
    makeRequest: vi.fn(),
  })),
  ConnectionError: class ConnectionError extends Error {
    constructor(message: string, public category: string, public retryable: boolean) {
      super(message);
    }
  },
  ErrorCategory: {
    CONFIGURATION_ERROR: 'configuration_error',
  },
}));

vi.mock('@/lib/connection/timeout-manager', () => ({
  getTimeoutManager: vi.fn(() => ({
    getTimeout: vi.fn(() => 30000),
  })),
  OperationType: {
    AUTHENTICATION: 'authentication',
    SESSION_VALIDATION: 'session_validation',
  },
}));

describe('ExtensionAuthManager', () => {
  let authManager: ExtensionAuthManager;
  let mockLocalStorage: { [key: string]: string };

  beforeEach(() => {
    // Mock localStorage
    mockLocalStorage = {};
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn((key: string) => mockLocalStorage[key] || null),
        setItem: vi.fn((key: string, value: string) => {
          mockLocalStorage[key] = value;
        }),
        removeItem: vi.fn((key: string) => {
          delete mockLocalStorage[key];
        }),
      },
      writable: true,
    });

    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: {
        hostname: 'localhost',
        origin: 'http://localhost:3000',
        search: '',
      },
      writable: true,
    });

    // Mock process.env
    process.env.NODE_ENV = 'test';

    authManager = new ExtensionAuthManager();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Token Storage', () => {
    it('should store and retrieve access tokens securely', () => {
      const testToken = 'test-access-token';
      
      authManager['tokenStorage'].setTokens(testToken);
      const retrievedToken = authManager['tokenStorage'].getAccessToken();
      
      expect(retrievedToken).toBe(testToken);
    });

    it('should store and retrieve refresh tokens securely', () => {
      const accessToken = 'test-access-token';
      const refreshToken = 'test-refresh-token';
      
      authManager['tokenStorage'].setTokens(accessToken, refreshToken);
      const retrievedRefreshToken = authManager['tokenStorage'].getRefreshToken();
      
      expect(retrievedRefreshToken).toBe(refreshToken);
    });

    it('should clear tokens when requested', () => {
      authManager['tokenStorage'].setTokens('access-token', 'refresh-token');
      authManager['tokenStorage'].clearTokens();
      
      expect(authManager['tokenStorage'].getAccessToken()).toBeNull();
      expect(authManager['tokenStorage'].getRefreshToken()).toBeNull();
    });
  });

  describe('Authentication Headers', () => {
    it('should return headers with Bearer token when authenticated', async () => {
      const testToken = 'test-token';
      authManager['tokenStorage'].setTokens(testToken);
      
      const headers = await authManager.getAuthHeaders();
      
      expect(headers['Authorization']).toBe(`Bearer ${testToken}`);
      expect(headers['Content-Type']).toBe('application/json');
      expect(headers['Accept']).toBe('application/json');
      expect(headers['X-Client-Type']).toBe('extension-integration');
    });

    it('should include development mode headers in development', async () => {
      process.env.NODE_ENV = 'development';
      
      const headers = await authManager.getAuthHeaders();
      
      expect(headers['X-Development-Mode']).toBe('true');
      expect(headers['X-Skip-Auth']).toBe('dev');
    });

    it('should return headers without token when not authenticated', async () => {
      const headers = await authManager.getAuthHeaders();
      
      expect(headers['Authorization']).toBeUndefined();
      expect(headers['Content-Type']).toBe('application/json');
    });
  });

  describe('Token Expiration', () => {
    it('should detect tokens expiring soon', () => {
      // Create a token that expires in 2 minutes
      const payload = {
        exp: Math.floor(Date.now() / 1000) + 120, // 2 minutes from now
      };
      const token = `header.${btoa(JSON.stringify(payload))}.signature`;
      
      const isExpiring = authManager['tokenStorage'].isTokenExpiringSoon(token);
      
      expect(isExpiring).toBe(true);
    });

    it('should not detect fresh tokens as expiring', () => {
      // Create a token that expires in 10 minutes
      const payload = {
        exp: Math.floor(Date.now() / 1000) + 600, // 10 minutes from now
      };
      const token = `header.${btoa(JSON.stringify(payload))}.signature`;
      
      const isExpiring = authManager['tokenStorage'].isTokenExpiringSoon(token);
      
      expect(isExpiring).toBe(false);
    });

    it('should handle malformed tokens gracefully', () => {
      const malformedToken = 'not-a-valid-jwt-token';
      
      const isExpiring = authManager['tokenStorage'].isTokenExpiringSoon(malformedToken);
      
      expect(isExpiring).toBe(true); // Should assume expired if can't parse
    });
  });

  describe('Authentication State', () => {
    it('should initialize with unauthenticated state', () => {
      const authState = authManager.getAuthState();
      
      expect(authState.isAuthenticated).toBe(false);
      expect(authState.isRefreshing).toBe(false);
      expect(authState.failureCount).toBe(0);
    });

    it('should update authentication state when tokens are set', () => {
      // Create a fresh token
      const payload = {
        exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
      };
      const token = `header.${btoa(JSON.stringify(payload))}.signature`;
      
      authManager['tokenStorage'].setTokens(token);
      authManager['initializeAuthState']();
      
      const authState = authManager.getAuthState();
      expect(authState.isAuthenticated).toBe(true);
    });

    it('should clear authentication state', () => {
      authManager['tokenStorage'].setTokens('test-token');
      authManager.clearAuth();
      
      const authState = authManager.getAuthState();
      expect(authState.isAuthenticated).toBe(false);
      expect(authManager['tokenStorage'].getAccessToken()).toBeNull();
    });
  });

  describe('Development Mode Detection', () => {
    it('should detect development mode from NODE_ENV', () => {
      process.env.NODE_ENV = 'development';
      
      const isDev = authManager['isDevelopmentMode']();
      
      expect(isDev).toBe(true);
    });

    it('should detect development mode from localhost hostname', () => {
      process.env.NODE_ENV = 'production';
      window.location.hostname = 'localhost';
      
      const isDev = authManager['isDevelopmentMode']();
      
      expect(isDev).toBe(true);
    });

    it('should detect development mode from query parameter', () => {
      process.env.NODE_ENV = 'production';
      window.location.hostname = 'example.com';
      window.location.search = '?dev=true';
      
      const isDev = authManager['isDevelopmentMode']();
      
      expect(isDev).toBe(true);
    });

    it('should not detect development mode in production', () => {
      process.env.NODE_ENV = 'production';
      window.location.hostname = 'example.com';
      window.location.search = '';
      
      const isDev = authManager['isDevelopmentMode']();
      
      expect(isDev).toBe(false);
    });
  });

  describe('Global Instance', () => {
    it('should return the same instance when called multiple times', () => {
      const instance1 = getExtensionAuthManager();
      const instance2 = getExtensionAuthManager();
      
      expect(instance1).toBe(instance2);
    });

    it('should be an instance of ExtensionAuthManager', () => {
      const instance = getExtensionAuthManager();
      
      expect(instance).toBeInstanceOf(ExtensionAuthManager);
    });
  });
});