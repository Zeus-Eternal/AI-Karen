/**
 * Integrated API Client Tests
 * 
 * Tests the integrated API client that combines existing API client
 * with enhanced session management and authentication.
 * 
 * Requirements: 5.2, 5.3, 1.1, 1.2
 */

import { vi } from 'vitest';
import { IntegratedApiClient, getIntegratedApiClient, initializeIntegratedApiClient } from '@/lib/api-client-integrated';
import * as apiClientModule from '@/lib/api-client';
import * as sessionModule from '@/lib/auth/session';

// Mock dependencies
vi.mock('@/lib/api-client');
vi.mock('@/lib/auth/session');

const mockApiClient = apiClientModule as any;
const mockSession = sessionModule as any;

describe('IntegratedApiClient', () => {
  let mockRegularClient: any;
  let mockEnhancedClientInstance: any;

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock regular API client
    mockRegularClient = {
      request: vi.fn(),
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
      uploadFile: vi.fn(),
      healthCheck: vi.fn(),
      getBackendUrl: vi.fn().mockReturnValue('http://localhost:8000'),
      getEndpoints: vi.fn().mockReturnValue({}),
      getEndpointStats: vi.fn().mockReturnValue([]),
      resetEndpointStats: vi.fn(),
      clearCaches: vi.fn(),
    };

    mockApiClient.getApiClient.mockReturnValue(mockRegularClient);

    // Mock enhanced API client
    mockEnhancedClientInstance = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
      uploadFile: vi.fn(),
      requestPublic: vi.fn(),
      request: vi.fn(),
      getApiClient: vi.fn().mockReturnValue(mockRegularClient),
    };

    // Mock session functions
    mockSession.isAuthenticated.mockReturnValue(false);
    mockSession.clearSession.mockImplementation(() => {});
  });

  describe('Constructor and Initialization', () => {
    it('should create instance with default options', () => {
      const client = new IntegratedApiClient();
      expect(client).toBeInstanceOf(IntegratedApiClient);
      expect(mockApiClient.getApiClient).toHaveBeenCalled();
    });

    it('should create instance with custom options', () => {
      const options = {
        useEnhancedAuth: false,
        autoRetryOn401: false,
        includeCredentials: false,
      };

      const client = new IntegratedApiClient(options);
      expect(client.getOptions()).toEqual(expect.objectContaining(options));
    });

    it('should get singleton instance', () => {
      const client1 = getIntegratedApiClient();
      const client2 = getIntegratedApiClient();
      expect(client1).toBe(client2);
    });

    it('should initialize new instance', () => {
      const client1 = getIntegratedApiClient();
      const client2 = initializeIntegratedApiClient();
      expect(client1).not.toBe(client2);
    });
  });

  describe('Protected Endpoint Detection', () => {
    let client: IntegratedApiClient;

    beforeEach(() => {
      client = new IntegratedApiClient();
    });

    it('should identify public endpoints correctly', async () => {
      const publicEndpoints = [
        '/api/auth/login',
        '/api/auth/register',
        '/api/auth/forgot-password',
        '/api/auth/reset-password',
        '/health',
        '/api/health',
        '/api/public/data',
      ];

      for (const endpoint of publicEndpoints) {
        await client.get(endpoint);
        // Should use regular client for public endpoints
        expect(mockRegularClient.request).toHaveBeenCalled();
        mockRegularClient.request.mockClear();
      }
    });

    it('should identify protected endpoints correctly', async () => {
      const protectedEndpoints = [
        '/api/user/profile',
        '/api/chat/messages',
        '/api/protected/data',
        '/api/admin/users',
      ];

      for (const endpoint of protectedEndpoints) {
        await client.get(endpoint);
        // Should use enhanced client for protected endpoints
        expect(mockEnhancedClientInstance.request).toHaveBeenCalled();
        mockEnhancedClientInstance.request.mockClear();
      }
    });
  });

  describe('HTTP Methods', () => {
    let client: IntegratedApiClient;

    beforeEach(() => {
      client = new IntegratedApiClient();
      mockEnhancedClientInstance.get.mockResolvedValue({ data: 'success' });
      mockEnhancedClientInstance.post.mockResolvedValue({ data: 'success' });
      mockEnhancedClientInstance.put.mockResolvedValue({ data: 'success' });
      mockEnhancedClientInstance.delete.mockResolvedValue({ data: 'success' });
      mockEnhancedClientInstance.patch.mockResolvedValue({ data: 'success' });
    });

    it('should handle GET requests', async () => {
      await client.get('/api/protected/data');
      expect(mockEnhancedClientInstance.request).toHaveBeenCalledWith({
        endpoint: '/api/protected/data',
        method: 'GET',
      });
    });

    it('should handle POST requests', async () => {
      const body = { test: 'data' };
      await client.post('/api/protected/data', body);
      expect(mockEnhancedClientInstance.request).toHaveBeenCalledWith({
        endpoint: '/api/protected/data',
        method: 'POST',
        body,
      });
    });

    it('should handle PUT requests', async () => {
      const body = { test: 'data' };
      await client.put('/api/protected/data', body);
      expect(mockEnhancedClientInstance.request).toHaveBeenCalledWith({
        endpoint: '/api/protected/data',
        method: 'PUT',
        body,
      });
    });

    it('should handle DELETE requests', async () => {
      await client.delete('/api/protected/data');
      expect(mockEnhancedClientInstance.request).toHaveBeenCalledWith({
        endpoint: '/api/protected/data',
        method: 'DELETE',
      });
    });

    it('should handle PATCH requests', async () => {
      const body = { test: 'data' };
      await client.patch('/api/protected/data', body);
      expect(mockEnhancedClientInstance.request).toHaveBeenCalledWith({
        endpoint: '/api/protected/data',
        method: 'PATCH',
        body,
      });
    });
  });

  describe('File Upload', () => {
    let client: IntegratedApiClient;

    beforeEach(() => {
      client = new IntegratedApiClient();
      mockEnhancedClientInstance.uploadFile.mockResolvedValue({ data: 'success' });
      mockRegularClient.uploadFile.mockResolvedValue({ data: 'success' });
    });

    it('should use enhanced client for protected upload endpoints', async () => {
      const file = new File(['test'], 'test.txt', { type: 'text/plain' });
      await client.uploadFile('/api/protected/upload', file);
      
      expect(mockEnhancedClientInstance.uploadFile).toHaveBeenCalledWith(
        '/api/protected/upload',
        file,
        'file',
        undefined,
        undefined
      );
    });

    it('should use regular client for public upload endpoints', async () => {
      const file = new File(['test'], 'test.txt', { type: 'text/plain' });
      await client.uploadFile('/api/public/upload', file);
      
      expect(mockRegularClient.uploadFile).toHaveBeenCalledWith(
        '/api/public/upload',
        file,
        'file',
        undefined,
        undefined
      );
    });

    it('should pass additional fields and options', async () => {
      const file = new File(['test'], 'test.txt', { type: 'text/plain' });
      const additionalFields = { category: 'document' };
      const options = { timeout: 30000 };

      await client.uploadFile('/api/protected/upload', file, 'document', additionalFields, options);
      
      expect(mockEnhancedClientInstance.uploadFile).toHaveBeenCalledWith(
        '/api/protected/upload',
        file,
        'document',
        additionalFields,
        options
      );
    });
  });

  describe('Authentication Integration', () => {
    let client: IntegratedApiClient;

    beforeEach(() => {
      client = new IntegratedApiClient();
    });

    it('should add auth headers for authenticated users with regular client', async () => {
      // Use a public endpoint that still gets auth headers when user is authenticated
      const client = new IntegratedApiClient({ useEnhancedAuth: false });
      
      mockSession.isAuthenticated.mockReturnValue(true);
      mockSession.getAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token123' });
      mockRegularClient.request.mockResolvedValue({ data: 'success' });

      await client.get('/api/public/data');

      expect(mockSession.ensureToken).toHaveBeenCalled();
      expect(mockRegularClient.request).toHaveBeenCalledWith({
        endpoint: '/api/public/data',
        method: 'GET',
        headers: {
          'Authorization': 'Bearer token123',
        },
      });
    });

    it('should handle token refresh failures gracefully', async () => {
      mockSession.isAuthenticated.mockReturnValue(true);
      mockSession.ensureToken.mockRejectedValue(new Error('Token refresh failed'));
      mockRegularClient.request.mockResolvedValue({ data: 'success' });

      await client.requestPublic({ endpoint: '/api/public/data', method: 'GET' });

      // Should still make the request without auth headers
      expect(mockRegularClient.request).toHaveBeenCalledWith({
        endpoint: '/api/public/data',
        method: 'GET',
      });
    });
  });

  describe('Enhanced Auth Configuration', () => {
    it('should use enhanced client when useEnhancedAuth is true', async () => {
      const client = new IntegratedApiClient({ useEnhancedAuth: true });
      mockEnhancedClientInstance.request.mockResolvedValue({ data: 'success' });

      await client.get('/api/protected/data');
      expect(mockEnhancedClientInstance.request).toHaveBeenCalled();
    });

    it('should use regular client when useEnhancedAuth is false', async () => {
      const client = new IntegratedApiClient({ useEnhancedAuth: false });
      mockRegularClient.request.mockResolvedValue({ data: 'success' });

      await client.get('/api/protected/data');
      expect(mockRegularClient.request).toHaveBeenCalled();
    });
  });

  describe('Utility Methods', () => {
    let client: IntegratedApiClient;

    beforeEach(() => {
      client = new IntegratedApiClient();
    });

    it('should delegate health check to regular client', async () => {
      mockRegularClient.healthCheck.mockResolvedValue({ data: 'healthy' });
      
      const result = await client.healthCheck();
      expect(mockRegularClient.healthCheck).toHaveBeenCalled();
      expect(result).toEqual({ data: 'healthy' });
    });

    it('should delegate getBackendUrl to regular client', () => {
      const result = client.getBackendUrl();
      expect(mockRegularClient.getBackendUrl).toHaveBeenCalled();
      expect(result).toBe('http://localhost:8000');
    });

    it('should delegate getEndpoints to regular client', () => {
      const result = client.getEndpoints();
      expect(mockRegularClient.getEndpoints).toHaveBeenCalled();
      expect(result).toEqual({});
    });

    it('should delegate getEndpointStats to regular client', () => {
      const result = client.getEndpointStats();
      expect(mockRegularClient.getEndpointStats).toHaveBeenCalled();
      expect(result).toEqual([]);
    });

    it('should delegate resetEndpointStats to regular client', () => {
      client.resetEndpointStats('/api/test');
      expect(mockRegularClient.resetEndpointStats).toHaveBeenCalledWith('/api/test');
    });

    it('should delegate clearCaches to regular client', () => {
      client.clearCaches();
      expect(mockRegularClient.clearCaches).toHaveBeenCalled();
    });

    it('should return underlying clients', () => {
      const clients = client.getClients();
      expect(clients.regular).toBe(mockRegularClient);
      expect(clients.enhanced).toBe(mockEnhancedClientInstance);
    });
  });

  describe('Options Management', () => {
    let client: IntegratedApiClient;

    beforeEach(() => {
      client = new IntegratedApiClient();
    });

    it('should update options', () => {
      const newOptions = { useEnhancedAuth: false };
      client.updateOptions(newOptions);
      
      const options = client.getOptions();
      expect(options.useEnhancedAuth).toBe(false);
    });

    it('should get current options', () => {
      const options = client.getOptions();
      expect(options).toEqual({
        useEnhancedAuth: true,
        autoRetryOn401: true,
        includeCredentials: true,
      });
    });
  });

  describe('Error Handling', () => {
    let client: IntegratedApiClient;

    beforeEach(() => {
      client = new IntegratedApiClient();
    });

    it('should propagate errors from enhanced client', async () => {
      const error = new Error('Enhanced client error');
      mockEnhancedClientInstance.request.mockRejectedValue(error);

      await expect(client.get('/api/protected/data')).rejects.toThrow('Enhanced client error');
    });

    it('should propagate errors from regular client', async () => {
      const error = new Error('Regular client error');
      mockRegularClient.request.mockRejectedValue(error);

      await expect(client.requestPublic({ endpoint: '/api/public/data', method: 'GET' })).rejects.toThrow('Regular client error');
    });
  });
});