/**
 * Unit tests for Enhanced API Client
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { EnhancedApiClient, getEnhancedApiClient } from '@/lib/auth/api-client-enhanced';

// Mock dependencies
vi.mock('@/lib/api-client', () => ({
  getApiClient: vi.fn(() => ({
    request: vi.fn(),
  })),
}));

vi.mock('@/lib/auth/session', () => ({
  ensureToken: vi.fn(),
  getAuthHeader: vi.fn(),
  clearSession: vi.fn(),
}));

describe('EnhancedApiClient', () => {
  let client: EnhancedApiClient;
  let mockRequest: any;
  let mockEnsureToken: any;
  let mockGetAuthHeader: any;
  let mockClearSession: any;

  beforeEach(async () => {
    // Get the mocked functions
    const { getApiClient } = await import('@/lib/api-client');
    const { ensureToken, getAuthHeader, clearSession } = await import('@/lib/auth/session');
    
    mockRequest = vi.fn();
    mockEnsureToken = ensureToken as any;
    mockGetAuthHeader = getAuthHeader as any;
    mockClearSession = clearSession as any;
    
    (getApiClient as any).mockReturnValue({
      request: mockRequest,
    });
    
    client = new EnhancedApiClient();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Request with Auth', () => {
    it('should add auth headers to requests', async () => {
      mockRequest.mockResolvedValue({ data: 'success' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });

      const result = await client.get('/api/test');

      expect(result.data).toBe('success');
      expect(mockEnsureToken).toHaveBeenCalled();
      expect(mockGetAuthHeader).toHaveBeenCalled();
      expect(mockRequest).toHaveBeenCalledWith({
        endpoint: '/api/test',
        method: 'GET',
        headers: {
          'Authorization': 'Bearer token',
        },
      });
    });

    it('should handle 401 errors with token refresh', async () => {
      mockRequest
        .mockRejectedValueOnce({ status: 401, message: 'Unauthorized' })
        .mockResolvedValueOnce({ data: 'success after refresh' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader
        .mockReturnValueOnce({ 'Authorization': 'Bearer old-token' })
        .mockReturnValueOnce({ 'Authorization': 'Bearer new-token' });

      const result = await client.get('/api/test');

      expect(result.data).toBe('success after refresh');
      expect(mockEnsureToken).toHaveBeenCalledTimes(2); // Once initially, once for refresh
      expect(mockRequest).toHaveBeenCalledTimes(2);
    });

    it('should clear session if token refresh fails', async () => {
      mockRequest.mockRejectedValue({ status: 401, message: 'Unauthorized' });
      mockEnsureToken
        .mockResolvedValueOnce(undefined)
        .mockRejectedValueOnce(new Error('Refresh failed'));
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });

      await expect(client.get('/api/test')).rejects.toEqual({
        status: 401,
        message: 'Unauthorized',
      });

      expect(mockClearSession).toHaveBeenCalled();
    });

    it('should not retry for non-401 errors', async () => {
      mockRequest.mockRejectedValue({ status: 500, message: 'Server Error' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });

      await expect(client.get('/api/test')).rejects.toEqual({
        status: 500,
        message: 'Server Error',
      });

      expect(mockRequest).toHaveBeenCalledTimes(1);
    });

    it('should prevent multiple simultaneous refresh attempts', async () => {
      mockRequest.mockRejectedValue({ status: 401, message: 'Unauthorized' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });

      // Make multiple simultaneous requests that will fail with 401
      const promises = [
        client.get('/api/test1').catch(() => {}),
        client.get('/api/test2').catch(() => {}),
        client.get('/api/test3').catch(() => {}),
      ];

      await Promise.all(promises);

      // Only the first request should trigger a refresh attempt
      // The others should fail immediately since isRefreshing flag is set
      expect(mockRequest).toHaveBeenCalledTimes(4); // 3 initial + 1 retry
    });
  });

  describe('HTTP Methods', () => {
    it('should support GET requests', async () => {
      mockRequest.mockResolvedValue({ data: 'get success' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({});

      await client.get('/api/test');

      expect(mockRequest).toHaveBeenCalledWith({
        endpoint: '/api/test',
        method: 'GET',
        headers: {},
      });
    });

    it('should support POST requests', async () => {
      mockRequest.mockResolvedValue({ data: 'post success' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({});

      await client.post('/api/test', { data: 'test' });

      expect(mockRequest).toHaveBeenCalledWith({
        endpoint: '/api/test',
        method: 'POST',
        body: { data: 'test' },
        headers: {},
      });
    });

    it('should support PUT requests', async () => {
      mockRequest.mockResolvedValue({ data: 'put success' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({});

      await client.put('/api/test', { data: 'test' });

      expect(mockRequest).toHaveBeenCalledWith({
        endpoint: '/api/test',
        method: 'PUT',
        body: { data: 'test' },
        headers: {},
      });
    });

    it('should support DELETE requests', async () => {
      mockRequest.mockResolvedValue({ data: 'delete success' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({});

      await client.delete('/api/test');

      expect(mockRequest).toHaveBeenCalledWith({
        endpoint: '/api/test',
        method: 'DELETE',
        headers: {},
      });
    });

    it('should support PATCH requests', async () => {
      mockRequest.mockResolvedValue({ data: 'patch success' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({});

      await client.patch('/api/test', { data: 'test' });

      expect(mockRequest).toHaveBeenCalledWith({
        endpoint: '/api/test',
        method: 'PATCH',
        body: { data: 'test' },
        headers: {},
      });
    });
  });

  describe('File Upload', () => {
    it('should handle file uploads with auth', async () => {
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });
      mockRequest.mockResolvedValue({ data: 'upload success' });

      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' });

      await client.uploadFile('/api/upload', mockFile);

      expect(mockEnsureToken).toHaveBeenCalled();
      expect(mockRequest).toHaveBeenCalledWith({
        endpoint: '/api/upload',
        method: 'POST',
        body: expect.any(FormData),
        headers: { 'Authorization': 'Bearer token' },
      });
    });
  });

  describe('Public Requests', () => {
    it('should make public requests without auth', async () => {
      mockRequest.mockResolvedValue({ data: 'public success' });

      await client.requestPublic({ endpoint: '/api/public', method: 'GET' });

      expect(mockRequest).toHaveBeenCalledWith({
        endpoint: '/api/public',
        method: 'GET',
      });
    });
  });

  describe('Singleton', () => {
    it('should return the same instance', () => {
      const client1 = getEnhancedApiClient();
      const client2 = getEnhancedApiClient();
      
      expect(client1).toBe(client2);
    });
  });
});