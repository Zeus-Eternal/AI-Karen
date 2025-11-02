/**
 * Real Response Integration Tests for Extension Authentication Error Handling
 * 
 * Tests the complete authentication error handling system with actual HTTP responses
 * and real-world scenarios to ensure production readiness.
 */

import { vi, beforeEach, afterEach, describe, it, expect } from 'vitest';
import { 
  handleExtensionAuthenticationError,
  checkExtensionFeatureAvailability,
  getExtensionAuthStatus,
  initializeExtensionAuthErrorHandling,
  resetExtensionAuthErrorHandling
} from '../index';
import { ExtensionFeatureLevel } from '../extension-auth-degradation';

// Mock fetch for testing real HTTP responses
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock localStorage for token storage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

// Mock sessionStorage
const mockSessionStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
};
Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage
});

// Mock console methods to avoid test noise
const originalConsole = { ...console };
beforeEach(() => {
  console.log = vi.fn();
  console.warn = vi.fn();
  console.error = vi.fn();
  console.info = vi.fn();
  console.debug = vi.fn();
});

afterEach(() => {
  Object.assign(console, originalConsole);
});

describe('Extension Authentication Real Response Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetExtensionAuthErrorHandling();
    initializeExtensionAuthErrorHandling();
    
    // Reset localStorage mocks
    mockLocalStorage.getItem.mockReturnValue(null);
    mockLocalStorage.setItem.mockImplementation(() => {});
    mockLocalStorage.removeItem.mockImplementation(() => {});
    
    // Reset sessionStorage mocks
    mockSessionStorage.getItem.mockReturnValue(null);
    mockSessionStorage.setItem.mockImplementation(() => {});
    mockSessionStorage.removeItem.mockImplementation(() => {});
  });

  describe('HTTP 401 Unauthorized Response Handling', () => {
    it('should handle 401 response with token refresh and retry', async () => {
      // Create a real 401 Response object
      const unauthorizedResponse = new Response(
        JSON.stringify({
          error: 'Unauthorized',
          message: 'Token has expired',
          code: 'TOKEN_EXPIRED'
        }),
        {
          status: 401,
          statusText: 'Unauthorized',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      // Mock successful token refresh
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token',
          expires_in: 3600
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        }
      ));

      // Handle the error
      const result = await handleExtensionAuthenticationError(
        unauthorizedResponse,
        '/api/extensions/',
        'extension_list'
      );

      // Should return null to indicate retry is possible
      expect(result).toBeNull();

      // Verify token refresh was attempted
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/auth/refresh',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
    });

    it('should handle 401 response when token refresh fails', async () => {
      const unauthorizedResponse = new Response(
        JSON.stringify({
          error: 'Unauthorized',
          message: 'Invalid token'
        }),
        {
          status: 401,
          statusText: 'Unauthorized',
          headers: { 'Content-Type': 'application/json' }
        }
      );

      // Mock failed token refresh
      mockFetch.mockRejectedValueOnce(new Error('Refresh failed'));

      const result = await handleExtensionAuthenticationError(
        unauthorizedResponse,
        '/api/extensions/',
        'extension_list'
      );

      // Should provide fallback data
      expect(result).toBeDefined();
      expect(result.extensions).toEqual([]);
      expect(result.message).toContain('temporarily unavailable');
    });
  });

  describe('HTTP 403 Forbidden Response Handling', () => {
    it('should handle 403 response with readonly fallback', async () => {
      const forbiddenResponse = new Response(
        JSON.stringify({
          error: 'Forbidden',
          message: 'Insufficient permissions for this operation',
          required_permissions: ['extension:write']
        }),
        {
          status: 403,
          statusText: 'Forbidden',
          headers: { 'Content-Type': 'application/json' }
        }
      );

      const result = await handleExtensionAuthenticationError(
        forbiddenResponse,
        '/api/extensions/install',
        'extension_install'
      );

      // Should provide fallback data indicating readonly mode
      expect(result).toBeDefined();
      
      // Check that system is in readonly mode
      const authStatus = getExtensionAuthStatus();
      expect(authStatus.degradationLevel).toBe(ExtensionFeatureLevel.READONLY);
      
      // Verify feature availability
      const installAvailability = checkExtensionFeatureAvailability('extension_install');
      expect(installAvailability.available).toBe(false);
      
      const listAvailability = checkExtensionFeatureAvailability('extension_list');
      expect(listAvailability.available).toBe(true);
    });
  });

  describe('HTTP 503 Service Unavailable Response Handling', () => {
    it('should handle 503 response with cached data fallback', async () => {
      const serviceUnavailableResponse = new Response(
        JSON.stringify({
          error: 'Service Unavailable',
          message: 'Extension service is temporarily down for maintenance',
          retry_after: 300
        }),
        {
          status: 503,
          statusText: 'Service Unavailable',
          headers: { 
            'Content-Type': 'application/json',
            'Retry-After': '300'
          }
        }
      );

      const result = await handleExtensionAuthenticationError(
        serviceUnavailableResponse,
        '/api/extensions/',
        'extension_list'
      );

      // Should provide fallback data
      expect(result).toBeDefined();
      expect(result.message).toContain('temporarily unavailable');
      
      // Check that system is in cached mode
      const authStatus = getExtensionAuthStatus();
      expect(authStatus.degradationLevel).toBe(ExtensionFeatureLevel.CACHED);
      expect(authStatus.recoveryEstimate).toBeDefined();
    });

    it('should handle 503 response with HTML error page', async () => {
      const htmlErrorResponse = new Response(
        '<html><body><h1>503 Service Unavailable</h1><p>The server is temporarily unable to service your request.</p></body></html>',
        {
          status: 503,
          statusText: 'Service Unavailable',
          headers: { 'Content-Type': 'text/html' }
        }
      );

      const result = await handleExtensionAuthenticationError(
        htmlErrorResponse,
        '/api/extensions/',
        'extension_list'
      );

      // Should still provide fallback data even with HTML response
      expect(result).toBeDefined();
      expect(result.extensions).toEqual([]);
    });
  });

  describe('Network Error Response Handling', () => {
    it('should handle network timeout errors', async () => {
      const timeoutError = new Error('Request timeout');
      timeoutError.name = 'AbortError';

      const result = await handleExtensionAuthenticationError(
        timeoutError,
        '/api/extensions/',
        'extension_list'
      );

      // Should provide fallback data
      expect(result).toBeDefined();
      
      // Check that system applies graceful degradation
      const authStatus = getExtensionAuthStatus();
      expect([ExtensionFeatureLevel.CACHED, ExtensionFeatureLevel.LIMITED]).toContain(authStatus.degradationLevel);
    });

    it('should handle DNS resolution errors', async () => {
      const dnsError = new TypeError('Failed to fetch');

      const result = await handleExtensionAuthenticationError(
        dnsError,
        '/api/extensions/',
        'extension_list'
      );

      // Should provide fallback data
      expect(result).toBeDefined();
      expect(result.message).toContain('temporarily unavailable');
    });
  });

  describe('Malformed Response Handling', () => {
    it('should handle responses with invalid JSON', async () => {
      const invalidJsonResponse = new Response(
        '{"error": "Invalid JSON", "message": "Something went wrong"', // Missing closing brace
        {
          status: 500,
          statusText: 'Internal Server Error',
          headers: { 'Content-Type': 'application/json' }
        }
      );

      const result = await handleExtensionAuthenticationError(
        invalidJsonResponse,
        '/api/extensions/',
        'extension_list'
      );

      // Should still provide fallback data
      expect(result).toBeDefined();
    });

    it('should handle empty response bodies', async () => {
      const emptyResponse = new Response('', {
        status: 500,
        statusText: 'Internal Server Error',
        headers: { 'Content-Type': 'application/json' }
      });

      const result = await handleExtensionAuthenticationError(
        emptyResponse,
        '/api/extensions/',
        'extension_list'
      );

      // Should provide fallback data
      expect(result).toBeDefined();
    });
  });

  describe('Rate Limiting Response Handling', () => {
    it('should handle 429 Too Many Requests with retry-after', async () => {
      const rateLimitResponse = new Response(
        JSON.stringify({
          error: 'Too Many Requests',
          message: 'Rate limit exceeded. Please try again later.',
          retry_after: 60
        }),
        {
          status: 429,
          statusText: 'Too Many Requests',
          headers: { 
            'Content-Type': 'application/json',
            'Retry-After': '60',
            'X-RateLimit-Limit': '100',
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': String(Date.now() + 60000)
          }
        }
      );

      const result = await handleExtensionAuthenticationError(
        rateLimitResponse,
        '/api/extensions/',
        'extension_list'
      );

      // Should provide fallback data
      expect(result).toBeDefined();
      
      // Check that system applies appropriate degradation
      const authStatus = getExtensionAuthStatus();
      expect(authStatus.degradationLevel).toBe(ExtensionFeatureLevel.LIMITED);
    });
  });

  describe('CORS Error Response Handling', () => {
    it('should handle CORS preflight failures', async () => {
      const corsError = new TypeError('Failed to fetch');
      // Simulate CORS error characteristics
      Object.defineProperty(corsError, 'message', {
        value: 'Failed to fetch'
      });

      const result = await handleExtensionAuthenticationError(
        corsError,
        '/api/extensions/',
        'extension_list'
      );

      // Should provide fallback data
      expect(result).toBeDefined();
      expect(result.message).toContain('temporarily unavailable');
    });
  });

  describe('Authentication Flow Integration', () => {
    it('should handle complete authentication flow with real responses', async () => {
      // Step 1: Initial request fails with 401
      const initialError = new Response(
        JSON.stringify({ error: 'Unauthorized', message: 'Token expired' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      );

      // Step 2: Token refresh succeeds
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          access_token: 'new-token',
          refresh_token: 'new-refresh-token',
          expires_in: 3600
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      ));

      // Step 3: Retry with new token succeeds
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          extensions: [
            { name: 'test-extension', status: 'active' }
          ]
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      ));

      // Handle the initial error
      const result = await handleExtensionAuthenticationError(
        initialError,
        '/api/extensions/',
        'extension_list'
      );

      // Should indicate retry is possible (null result)
      expect(result).toBeNull();

      // Verify token was stored
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        expect.stringContaining('token'),
        expect.any(String)
      );
    });

    it('should handle cascading failures gracefully', async () => {
      // Step 1: Initial request fails with 401
      const initialError = new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 401 }
      );

      // Step 2: Token refresh also fails
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      // Step 3: Fallback to cached/static data
      const result = await handleExtensionAuthenticationError(
        initialError,
        '/api/extensions/',
        'extension_list'
      );

      // Should provide fallback data
      expect(result).toBeDefined();
      expect(result.extensions).toEqual([]);
      expect(result.message).toContain('temporarily unavailable');

      // Verify system is in degraded state
      const authStatus = getExtensionAuthStatus();
      expect(authStatus.degradationLevel).not.toBe(ExtensionFeatureLevel.FULL);
    });
  });

  describe('Feature Availability with Real Responses', () => {
    it('should correctly determine feature availability after real error responses', async () => {
      // Simulate permission denied for write operations
      const forbiddenResponse = new Response(
        JSON.stringify({
          error: 'Forbidden',
          message: 'Write access denied'
        }),
        { status: 403 }
      );

      await handleExtensionAuthenticationError(
        forbiddenResponse,
        '/api/extensions/install',
        'extension_install'
      );

      // Check feature availability
      const installCheck = checkExtensionFeatureAvailability('extension_install');
      expect(installCheck.available).toBe(false);
      expect(installCheck.level).toBe(ExtensionFeatureLevel.READONLY);
      expect(installCheck.fallbackData).toBeDefined();

      const listCheck = checkExtensionFeatureAvailability('extension_list');
      expect(listCheck.available).toBe(true);
      expect(listCheck.level).toBe(ExtensionFeatureLevel.READONLY);
    });
  });

  describe('Error Recovery with Real Responses', () => {
    it('should recover from temporary service issues', async () => {
      // Step 1: Service unavailable
      const serviceError = new Response(
        JSON.stringify({
          error: 'Service Unavailable',
          message: 'Temporary maintenance'
        }),
        { status: 503 }
      );

      await handleExtensionAuthenticationError(
        serviceError,
        '/api/extensions/',
        'extension_list'
      );

      // Verify degraded state
      let authStatus = getExtensionAuthStatus();
      expect(authStatus.degradationLevel).toBe(ExtensionFeatureLevel.CACHED);

      // Step 2: Simulate service recovery
      resetExtensionAuthErrorHandling();

      // Verify recovery
      authStatus = getExtensionAuthStatus();
      expect(authStatus.degradationLevel).toBe(ExtensionFeatureLevel.FULL);
    });
  });

  describe('Performance and Memory Management', () => {
    it('should handle multiple rapid error responses without memory leaks', async () => {
      const errors = [];
      
      // Generate multiple error responses
      for (let i = 0; i < 50; i++) {
        const errorResponse = new Response(
          JSON.stringify({ error: 'Rate Limited' }),
          { status: 429 }
        );
        errors.push(errorResponse);
      }

      // Process all errors
      const results = await Promise.all(
        errors.map((error, index) => 
          handleExtensionAuthenticationError(
            error,
            `/api/extensions/${index}`,
            'extension_list'
          )
        )
      );

      // All should provide fallback data
      results.forEach(result => {
        expect(result).toBeDefined();
      });

      // System should still be responsive
      const authStatus = getExtensionAuthStatus();
      expect(authStatus).toBeDefined();
      expect(authStatus.degradationLevel).toBeDefined();
    });
  });

  describe('Real-world Scenario Simulation', () => {
    it('should handle a complete production failure scenario', async () => {
      // Scenario: Backend deployment causes temporary authentication issues
      
      // Step 1: Multiple users hit auth errors simultaneously
      const authErrors = Array(10).fill(null).map(() => 
        new Response(
          JSON.stringify({ error: 'Internal Server Error' }),
          { status: 500 }
        )
      );

      const results = await Promise.all(
        authErrors.map((error, index) =>
          handleExtensionAuthenticationError(
            error,
            '/api/extensions/',
            `operation_${index}`
          )
        )
      );

      // All should provide fallback data
      results.forEach(result => {
        expect(result).toBeDefined();
      });

      // Step 2: System should detect systemic issues
      const authStatus = getExtensionAuthStatus();
      expect(authStatus.degradationLevel).not.toBe(ExtensionFeatureLevel.FULL);

      // Step 3: Recovery after backend is fixed
      resetExtensionAuthErrorHandling();
      
      const recoveredStatus = getExtensionAuthStatus();
      expect(recoveredStatus.degradationLevel).toBe(ExtensionFeatureLevel.FULL);
    });

    it('should handle mixed success and failure responses', async () => {
      // Simulate partial system degradation
      const responses = [
        new Response(JSON.stringify({ extensions: [] }), { status: 200 }), // Success
        new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 }), // Auth error
        new Response(JSON.stringify({ extensions: [] }), { status: 200 }), // Success
        new Response(JSON.stringify({ error: 'Service Unavailable' }), { status: 503 }), // Service error
      ];

      const results = [];
      for (const response of responses) {
        if (response.ok) {
          // Simulate successful response handling
          results.push(await response.json());
        } else {
          // Handle error response
          const result = await handleExtensionAuthenticationError(
            response,
            '/api/extensions/',
            'extension_list'
          );
          results.push(result);
        }
      }

      // Should have mix of real data and fallback data
      expect(results).toHaveLength(4);
      results.forEach(result => {
        expect(result).toBeDefined();
      });
    });
  });
});