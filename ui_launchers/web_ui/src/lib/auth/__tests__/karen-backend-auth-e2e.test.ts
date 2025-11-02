/**
 * End-to-End Integration Tests for KarenBackendService with Extension Authentication
 * 
 * Tests the complete integration between KarenBackendService and the extension
 * authentication error handling system with real HTTP responses.
 */

import { vi, beforeEach, afterEach, describe, it, expect } from 'vitest';

// Mock the auth modules before importing KarenBackendService
vi.mock('../extension-auth-manager', () => ({
  getExtensionAuthManager: vi.fn(() => ({
    getAuthHeaders: vi.fn().mockResolvedValue({
      'Authorization': 'Bearer test-token',
      'Content-Type': 'application/json',
      'X-Client-Type': 'extension-integration'
    }),
    forceRefresh: vi.fn().mockResolvedValue('new-test-token'),
    clearAuth: vi.fn(),
    isAuthenticated: vi.fn().mockReturnValue(true)
  }))
}));

vi.mock('../extension-auth-errors', () => ({
  ExtensionAuthErrorFactory: {
    createTokenExpiredError: vi.fn().mockReturnValue({
      category: 'token_expired',
      severity: 'medium',
      code: 'EXT_AUTH_TOKEN_EXPIRED',
      title: 'Authentication Token Expired',
      message: 'Your authentication token has expired.',
      recoveryStrategy: 'retry_with_refresh',
      retryable: true,
      userActionRequired: false,
      resolutionSteps: ['Token will be refreshed automatically'],
      timestamp: new Date()
    }),
    createPermissionDeniedError: vi.fn().mockReturnValue({
      category: 'permission_denied',
      severity: 'high',
      code: 'EXT_AUTH_PERMISSION_DENIED',
      title: 'Permission Denied',
      message: 'You do not have permission to access this extension feature.',
      recoveryStrategy: 'fallback_to_readonly',
      retryable: false,
      userActionRequired: true,
      resolutionSteps: ['Contact your administrator'],
      timestamp: new Date()
    }),
    createServiceUnavailableError: vi.fn().mockReturnValue({
      category: 'service_unavailable',
      severity: 'medium',
      code: 'EXT_AUTH_SERVICE_UNAVAILABLE',
      title: 'Extension Service Unavailable',
      message: 'The extension service is temporarily unavailable.',
      recoveryStrategy: 'graceful_degradation',
      retryable: true,
      userActionRequired: false,
      resolutionSteps: ['System will retry automatically'],
      timestamp: new Date()
    })
  },
  extensionAuthErrorHandler: {
    handleError: vi.fn().mockReturnValue({
      category: 'test',
      severity: 'medium',
      title: 'Test Error',
      message: 'Test error message'
    })
  }
}));

vi.mock('../extension-auth-recovery', () => ({
  extensionAuthRecoveryManager: {
    attemptRecovery: vi.fn().mockResolvedValue({
      success: true,
      strategy: 'retry_with_refresh',
      message: 'Recovery successful',
      requiresUserAction: false,
      fallbackData: null
    })
  }
}));

vi.mock('../extension-auth-degradation', () => ({
  isExtensionFeatureAvailable: vi.fn().mockReturnValue(true),
  getExtensionFallbackData: vi.fn().mockReturnValue({
    extensions: [],
    total: 0,
    message: 'Extension list temporarily unavailable'
  })
}));

// Now import the service after mocks are set up
import { KarenBackendService } from '../../karen-backend';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock localStorage and sessionStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
};

const mockSessionStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
};

Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });
Object.defineProperty(window, 'sessionStorage', { value: mockSessionStorage });

// Mock console to reduce test noise
const originalConsole = { ...console };
beforeEach(() => {
  console.log = vi.fn();
  console.warn = vi.fn();
  console.error = vi.fn();
  console.info = vi.fn();
  console.debug = vi.fn();

afterEach(() => {
  Object.assign(console, originalConsole);

describe('KarenBackendService Extension Authentication E2E Tests', () => {
  let backendService: KarenBackendService;

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Reset storage mocks
    mockLocalStorage.getItem.mockReturnValue(null);
    mockSessionStorage.getItem.mockReturnValue(null);
    
    // Create service instance
    backendService = new KarenBackendService({
      baseUrl: '',
      timeout: 5000


  describe('Extension List API Integration', () => {
    it('should successfully fetch extension list with authentication', async () => {
      // Mock successful response
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          extensions: {
            'test-extension': {
              name: 'test-extension',
              version: '1.0.0',
              display_name: 'Test Extension',
              description: 'A test extension',
              status: 'active',
              capabilities: {},
              loaded_at: '2023-01-01T00:00:00Z'
            }
          },
          total: 1,
          user_context: {
            user_id: 'test-user',
            tenant_id: 'test-tenant'
          }
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        }
      ));

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(result.extensions).toBeDefined();
      expect(result.total).toBe(1);
      expect(result.user_context).toBeDefined();

      // Verify authentication headers were included
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/extensions/',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'X-Client-Type': 'extension-integration',
            'X-Extension-Request': 'true'
          })
        })
      );

    it('should handle 401 unauthorized response with token refresh', async () => {
      // Mock initial 401 response
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          error: 'Unauthorized',
          message: 'Token has expired',
          code: 'TOKEN_EXPIRED'
        }),
        {
          status: 401,
          statusText: 'Unauthorized',
          headers: { 'Content-Type': 'application/json' }
        }
      ));

      // Mock successful retry after token refresh
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          extensions: {},
          total: 0,
          message: 'No extensions available'
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        }
      ));

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(result.extensions).toBeDefined();

      // Verify that fetch was called twice (initial + retry)
      expect(mockFetch).toHaveBeenCalledTimes(2);

    it('should provide fallback data when authentication fails completely', async () => {
      // Mock persistent 401 response
      mockFetch.mockResolvedValue(new Response(
        JSON.stringify({
          error: 'Unauthorized',
          message: 'Authentication failed'
        }),
        {
          status: 401,
          headers: { 'Content-Type': 'application/json' }
        }
      ));

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(result.extensions).toEqual([]);
      expect(result.message).toContain('temporarily unavailable');

    it('should handle 403 forbidden response with readonly fallback', async () => {
      // Mock 403 response
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          error: 'Forbidden',
          message: 'Insufficient permissions',
          required_permissions: ['extension:read']
        }),
        {
          status: 403,
          statusText: 'Forbidden',
          headers: { 'Content-Type': 'application/json' }
        }
      ));

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(result.extensions).toEqual([]);
      expect(result.message).toContain('temporarily unavailable');


  describe('Background Tasks API Integration', () => {
    it('should successfully fetch background tasks with authentication', async () => {
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          tasks: [
            {
              task_id: 'task-1',
              name: 'Test Task',
              extension_name: 'test-extension',
              status: 'running',
              created_at: '2023-01-01T00:00:00Z',
              last_run: '2023-01-01T01:00:00Z',
              next_run: '2023-01-01T02:00:00Z'
            }
          ],
          total: 1,
          extension_name: 'test-extension'
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        }
      ));

      const result = await backendService.listBackgroundTasks('test-extension');

      expect(result).toBeDefined();
      expect(result.tasks).toHaveLength(1);
      expect(result.total).toBe(1);
      expect(result.extension_name).toBe('test-extension');

      // Verify correct endpoint was called
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/extensions/background-tasks/?extension_name=test-extension',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'X-Extension-Request': 'true'
          })
        })
      );

    it('should successfully register background task with authentication', async () => {
      const taskData = {
        name: 'New Task',
        extension_name: 'test-extension',
        schedule: '0 */1 * * *',
        enabled: true
      };

      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          task_id: 'task-123',
          message: 'Background task registered successfully',
          status: 'registered'
        }),
        {
          status: 201,
          headers: { 'Content-Type': 'application/json' }
        }
      ));

      const result = await backendService.registerBackgroundTask(taskData);

      expect(result).toBeDefined();
      expect(result.task_id).toBe('task-123');
      expect(result.status).toBe('registered');

      // Verify POST request with correct data
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/extensions/background-tasks/',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify(taskData)
        })
      );

    it('should handle background task registration with insufficient permissions', async () => {
      const taskData = {
        name: 'Admin Task',
        extension_name: 'admin-extension',
        schedule: '0 0 * * *'
      };

      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          error: 'Forbidden',
          message: 'Insufficient permissions to register background tasks',
          required_permissions: ['extension:background_tasks_write']
        }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' }
        }
      ));

      const result = await backendService.registerBackgroundTask(taskData);

      expect(result).toBeDefined();
      expect(result.message).toContain('temporarily unavailable');


  describe('Service Unavailable Scenarios', () => {
    it('should handle 503 service unavailable with retry logic', async () => {
      // Mock initial 503 response
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          error: 'Service Unavailable',
          message: 'Extension service is temporarily down for maintenance',
          retry_after: 60
        }),
        {
          status: 503,
          statusText: 'Service Unavailable',
          headers: { 
            'Content-Type': 'application/json',
            'Retry-After': '60'
          }
        }
      ));

      // Mock successful retry
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          extensions: {},
          total: 0
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        }
      ));

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(mockFetch).toHaveBeenCalledTimes(2);

    it('should provide cached data when service remains unavailable', async () => {
      // Mock persistent 503 responses
      mockFetch.mockResolvedValue(new Response(
        JSON.stringify({
          error: 'Service Unavailable',
          message: 'Service is down'
        }),
        {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        }
      ));

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(result.extensions).toEqual([]);
      expect(result.message).toContain('temporarily unavailable');


  describe('Network Error Scenarios', () => {
    it('should handle network timeout errors', async () => {
      const timeoutError = new Error('Request timeout');
      timeoutError.name = 'AbortError';
      
      mockFetch.mockRejectedValueOnce(timeoutError);

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(result.extensions).toEqual([]);
      expect(result.message).toContain('temporarily unavailable');

    it('should handle DNS resolution failures', async () => {
      const networkError = new TypeError('Failed to fetch');
      
      mockFetch.mockRejectedValueOnce(networkError);

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(result.extensions).toEqual([]);

    it('should handle CORS errors gracefully', async () => {
      const corsError = new TypeError('Failed to fetch');
      // Simulate CORS error characteristics
      Object.defineProperty(corsError, 'message', {
        value: 'Failed to fetch'

      mockFetch.mockRejectedValueOnce(corsError);

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(result.message).toContain('temporarily unavailable');


  describe('Rate Limiting Scenarios', () => {
    it('should handle 429 rate limiting with exponential backoff', async () => {
      // Mock initial rate limit response
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          error: 'Too Many Requests',
          message: 'Rate limit exceeded',
          retry_after: 30
        }),
        {
          status: 429,
          statusText: 'Too Many Requests',
          headers: { 
            'Content-Type': 'application/json',
            'Retry-After': '30',
            'X-RateLimit-Limit': '100',
            'X-RateLimit-Remaining': '0'
          }
        }
      ));

      // Mock successful retry after backoff
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          extensions: {},
          total: 0
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        }
      ));

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(mockFetch).toHaveBeenCalledTimes(2);


  describe('Malformed Response Handling', () => {
    it('should handle responses with invalid JSON', async () => {
      mockFetch.mockResolvedValueOnce(new Response(
        '{"error": "Invalid JSON", "message": "Something went wrong"', // Missing closing brace
        {
          status: 500,
          headers: { 'Content-Type': 'application/json' }
        }
      ));

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(result.extensions).toEqual([]);

    it('should handle empty response bodies', async () => {
      mockFetch.mockResolvedValueOnce(new Response('', {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }));

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();

    it('should handle non-JSON response content', async () => {
      mockFetch.mockResolvedValueOnce(new Response(
        '<html><body>Server Error</body></html>',
        {
          status: 500,
          headers: { 'Content-Type': 'text/html' }
        }
      ));

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(result.extensions).toEqual([]);


  describe('Authentication Header Management', () => {
    it('should include proper authentication headers for extension endpoints', async () => {
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({ extensions: {}, total: 0 }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      ));

      await backendService.listExtensions();

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/extensions/',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json',
            'X-Client-Type': 'extension-integration',
            'X-Extension-Request': 'true',
            'X-Correlation-ID': expect.any(String)
          })
        })
      );

    it('should handle missing authentication gracefully', async () => {
      // Mock auth manager returning no headers
      const { getExtensionAuthManager } = await import('../extension-auth-manager');
      const mockAuthManager = getExtensionAuthManager();
      vi.mocked(mockAuthManager.getAuthHeaders).mockResolvedValueOnce({
        'Content-Type': 'application/json'

      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({ extensions: {}, total: 0 }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      ));

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/extensions/',
        expect.objectContaining({
          headers: expect.not.objectContaining({
            'Authorization': expect.any(String)
          })
        })
      );


  describe('Performance and Reliability', () => {
    it('should handle multiple concurrent requests without interference', async () => {
      // Mock successful responses for all requests
      mockFetch.mockResolvedValue(new Response(
        JSON.stringify({ extensions: {}, total: 0 }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      ));

      // Make multiple concurrent requests
      const requests = Array(10).fill(null).map((_, index) => 
        backendService.listExtensions()
      );

      const results = await Promise.all(requests);

      // All requests should succeed
      results.forEach(result => {
        expect(result).toBeDefined();
        expect(result.extensions).toBeDefined();

      expect(mockFetch).toHaveBeenCalledTimes(10);

    it('should handle request cancellation gracefully', async () => {
      const abortController = new AbortController();
      
      // Mock a slow response
      mockFetch.mockImplementationOnce(() => 
        new Promise((resolve) => {
          setTimeout(() => {
            resolve(new Response(
              JSON.stringify({ extensions: {}, total: 0 }),
              { status: 200, headers: { 'Content-Type': 'application/json' } }
            ));
          }, 1000);
        })
      );

      // Start request and immediately cancel
      const requestPromise = backendService.listExtensions();
      abortController.abort();

      // Should still handle gracefully
      const result = await requestPromise;
      expect(result).toBeDefined();


  describe('Real-world Integration Scenarios', () => {
    it('should handle complete authentication flow in production-like scenario', async () => {
      // Scenario: User session expires during extension usage
      
      // Step 1: Initial request fails with expired token
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          error: 'Unauthorized',
          message: 'JWT token has expired',
          code: 'TOKEN_EXPIRED'
        }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      ));

      // Step 2: Token refresh succeeds
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          access_token: 'refreshed-token',
          refresh_token: 'new-refresh-token',
          expires_in: 3600
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      ));

      // Step 3: Retry with new token succeeds
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          extensions: {
            'production-extension': {
              name: 'production-extension',
              status: 'active'
            }
          },
          total: 1
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      ));

      const result = await backendService.listExtensions();

      expect(result).toBeDefined();
      expect(result.extensions['production-extension']).toBeDefined();
      expect(result.total).toBe(1);

      // Verify the complete flow: initial request + token refresh + retry
      expect(mockFetch).toHaveBeenCalledTimes(3);

    it('should handle partial system failure with mixed responses', async () => {
      // Scenario: Some extension services are down, others working
      
      // Extension list works
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          extensions: { 'working-extension': { status: 'active' } },
          total: 1
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      ));

      const listResult = await backendService.listExtensions();
      expect(listResult.total).toBe(1);

      // Background tasks service is down
      mockFetch.mockResolvedValueOnce(new Response(
        JSON.stringify({
          error: 'Service Unavailable',
          message: 'Background task service is down'
        }),
        { status: 503, headers: { 'Content-Type': 'application/json' } }
      ));

      const tasksResult = await backendService.listBackgroundTasks();
      expect(tasksResult.tasks).toEqual([]);
      expect(tasksResult.message).toContain('temporarily unavailable');


