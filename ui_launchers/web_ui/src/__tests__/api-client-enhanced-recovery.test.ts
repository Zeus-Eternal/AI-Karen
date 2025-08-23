/**
 * Integration tests for Enhanced API Client with Session Recovery
 * 
 * Tests automatic retry mechanism for 401 errors with token refresh
 * and intelligent session recovery.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { EnhancedApiClient } from '@/lib/auth/api-client-enhanced';

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

vi.mock('@/lib/auth/session-recovery', () => ({
  recoverFrom401Error: vi.fn(),
}));

describe('Enhanced API Client with Session Recovery', () => {
  let client: EnhancedApiClient;
  let mockRequest: any;
  let mockEnsureToken: any;
  let mockGetAuthHeader: any;
  let mockClearSession: any;
  let mockRecoverFrom401Error: any;

  beforeEach(async () => {
    // Get the mocked functions
    const { getApiClient } = await import('@/lib/api-client');
    const { ensureToken, getAuthHeader, clearSession } = await import('@/lib/auth/session');
    const { recoverFrom401Error } = await import('@/lib/auth/session-recovery');
    
    mockRequest = vi.fn();
    mockEnsureToken = ensureToken as any;
    mockGetAuthHeader = getAuthHeader as any;
    mockClearSession = clearSession as any;
    mockRecoverFrom401Error = recoverFrom401Error as any;
    
    (getApiClient as any).mockReturnValue({
      request: mockRequest,
    });
    
    client = new EnhancedApiClient();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Session Recovery on 401 Errors', () => {
    it('should recover from 401 error and retry request successfully', async () => {
      // Setup: First request fails with 401, recovery succeeds, retry succeeds
      mockRequest
        .mockRejectedValueOnce({ status: 401, message: 'Unauthorized' })
        .mockResolvedValueOnce({ data: 'success after recovery' });
      
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader
        .mockReturnValueOnce({ 'Authorization': 'Bearer old-token' })
        .mockReturnValueOnce({ 'Authorization': 'Bearer new-token' });
      
      mockRecoverFrom401Error.mockResolvedValue({
        success: true,
        shouldShowLogin: false,
      });

      const result = await client.get('/api/test');

      expect(result.data).toBe('success after recovery');
      expect(mockRecoverFrom401Error).toHaveBeenCalled();
      expect(mockRequest).toHaveBeenCalledTimes(2);
      expect(mockClearSession).not.toHaveBeenCalled();
    });

    it('should handle recovery failure and throw original error', async () => {
      mockRequest.mockRejectedValue({ status: 401, message: 'Unauthorized' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });
      
      mockRecoverFrom401Error.mockResolvedValue({
        success: false,
        reason: 'refresh_failed',
        shouldShowLogin: true,
        message: 'Session expired',
      });

      await expect(client.get('/api/test')).rejects.toEqual({
        status: 401,
        message: 'Unauthorized',
      });

      expect(mockRecoverFrom401Error).toHaveBeenCalled();
      expect(mockRequest).toHaveBeenCalledTimes(1);
    });

    it('should handle recovery exception and clear session', async () => {
      mockRequest.mockRejectedValue({ status: 401, message: 'Unauthorized' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });
      
      mockRecoverFrom401Error.mockRejectedValue(new Error('Recovery failed'));

      await expect(client.get('/api/test')).rejects.toEqual({
        status: 401,
        message: 'Unauthorized',
      });

      expect(mockClearSession).toHaveBeenCalled();
    });

    it('should not attempt recovery for non-401 errors', async () => {
      mockRequest.mockRejectedValue({ status: 500, message: 'Server Error' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });

      await expect(client.get('/api/test')).rejects.toEqual({
        status: 500,
        message: 'Server Error',
      });

      expect(mockRecoverFrom401Error).not.toHaveBeenCalled();
      expect(mockRequest).toHaveBeenCalledTimes(1);
    });
  });

  describe('Request Queuing During Recovery', () => {
    it('should queue multiple requests during recovery', async () => {
      // Setup: All requests fail with 401, recovery takes time, then all succeed
      mockRequest
        .mockRejectedValueOnce({ status: 401, message: 'Unauthorized' })
        .mockRejectedValueOnce({ status: 401, message: 'Unauthorized' })
        .mockRejectedValueOnce({ status: 401, message: 'Unauthorized' })
        .mockResolvedValue({ data: 'success' });
      
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });
      
      // Simulate slow recovery
      let recoveryResolve: (value: any) => void;
      const recoveryPromise = new Promise(resolve => {
        recoveryResolve = resolve;
      });
      
      mockRecoverFrom401Error.mockReturnValue(recoveryPromise);

      // Start multiple requests simultaneously
      const promises = [
        client.get('/api/test1'),
        client.get('/api/test2'),
        client.get('/api/test3'),
      ];

      // Let recovery complete
      setTimeout(() => {
        recoveryResolve!({
          success: true,
          shouldShowLogin: false,
        });
      }, 50);

      const results = await Promise.all(promises);

      // All requests should succeed
      results.forEach(result => {
        expect(result.data).toBe('success');
      });

      // Recovery should only be called once
      expect(mockRecoverFrom401Error).toHaveBeenCalledTimes(1);
      
      // Should have 3 initial requests + 3 retries after recovery
      expect(mockRequest).toHaveBeenCalledTimes(6);
    });

    it('should handle queued requests when recovery fails', async () => {
      mockRequest.mockRejectedValue({ status: 401, message: 'Unauthorized' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });
      
      mockRecoverFrom401Error.mockResolvedValue({
        success: false,
        reason: 'refresh_failed',
        shouldShowLogin: true,
      });

      // Start multiple requests simultaneously
      const promises = [
        client.get('/api/test1').catch(e => e),
        client.get('/api/test2').catch(e => e),
        client.get('/api/test3').catch(e => e),
      ];

      const results = await Promise.all(promises);

      // All requests should fail with the original error
      results.forEach(result => {
        expect(result).toEqual({ status: 401, message: 'Unauthorized' });
      });

      expect(mockRecoverFrom401Error).toHaveBeenCalledTimes(1);
    });
  });

  describe('Different HTTP Methods with Recovery', () => {
    it('should handle POST request recovery', async () => {
      mockRequest
        .mockRejectedValueOnce({ status: 401, message: 'Unauthorized' })
        .mockResolvedValueOnce({ data: 'post success' });
      
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });
      
      mockRecoverFrom401Error.mockResolvedValue({
        success: true,
        shouldShowLogin: false,
      });

      const result = await client.post('/api/test', { data: 'test' });

      expect(result.data).toBe('post success');
      expect(mockRequest).toHaveBeenCalledTimes(2);
      
      // Verify the request was made with correct parameters
      expect(mockRequest).toHaveBeenCalledWith({
        endpoint: '/api/test',
        method: 'POST',
        body: { data: 'test' },
        headers: { 'Authorization': 'Bearer token' },
      });
    });

    it('should handle PUT request recovery', async () => {
      mockRequest
        .mockRejectedValueOnce({ status: 401, message: 'Unauthorized' })
        .mockResolvedValueOnce({ data: 'put success' });
      
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });
      
      mockRecoverFrom401Error.mockResolvedValue({
        success: true,
        shouldShowLogin: false,
      });

      const result = await client.put('/api/test', { data: 'test' });

      expect(result.data).toBe('put success');
      expect(mockRecoverFrom401Error).toHaveBeenCalled();
    });

    it('should handle DELETE request recovery', async () => {
      mockRequest
        .mockRejectedValueOnce({ status: 401, message: 'Unauthorized' })
        .mockResolvedValueOnce({ data: 'delete success' });
      
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });
      
      mockRecoverFrom401Error.mockResolvedValue({
        success: true,
        shouldShowLogin: false,
      });

      const result = await client.delete('/api/test');

      expect(result.data).toBe('delete success');
      expect(mockRecoverFrom401Error).toHaveBeenCalled();
    });
  });

  describe('File Upload with Recovery', () => {
    it('should handle file upload recovery', async () => {
      mockRequest
        .mockRejectedValueOnce({ status: 401, message: 'Unauthorized' })
        .mockResolvedValueOnce({ data: 'upload success' });
      
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });
      
      mockRecoverFrom401Error.mockResolvedValue({
        success: true,
        shouldShowLogin: false,
      });

      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' });
      const result = await client.uploadFile('/api/upload', mockFile);

      expect(result.data).toBe('upload success');
      expect(mockRecoverFrom401Error).toHaveBeenCalled();
      expect(mockRequest).toHaveBeenCalledTimes(2);
    });
  });

  describe('Edge Cases', () => {
    it('should handle ensureToken failure before request', async () => {
      mockEnsureToken.mockRejectedValue(new Error('Token ensure failed'));
      mockGetAuthHeader.mockReturnValue({});
      mockRequest.mockResolvedValue({ data: 'success' });

      // Should still make the request even if ensureToken fails
      const result = await client.get('/api/test');

      expect(result.data).toBe('success');
      expect(mockClearSession).toHaveBeenCalled();
    });

    it('should handle concurrent recovery attempts correctly', async () => {
      mockRequest.mockRejectedValue({ status: 401, message: 'Unauthorized' });
      mockEnsureToken.mockResolvedValue(undefined);
      mockGetAuthHeader.mockReturnValue({ 'Authorization': 'Bearer token' });
      
      // First recovery attempt succeeds
      mockRecoverFrom401Error
        .mockResolvedValueOnce({
          success: true,
          shouldShowLogin: false,
        })
        .mockResolvedValue({
          success: false,
          shouldShowLogin: true,
        });

      // Start multiple requests, but only first should trigger recovery
      const promises = [
        client.get('/api/test1').catch(e => e),
        client.get('/api/test2').catch(e => e),
      ];

      await Promise.all(promises);

      // Recovery should only be called once
      expect(mockRecoverFrom401Error).toHaveBeenCalledTimes(1);
    });
  });
});