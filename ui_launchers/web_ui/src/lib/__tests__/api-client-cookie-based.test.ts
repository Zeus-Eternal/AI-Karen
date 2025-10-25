/**
 * Tests for cookie-based API client implementation
 * Verifies automatic cookie handling and simple 401 error handling
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { getApiClient } from '../api-client';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock window.location
const mockLocation = {
  href: '',
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

describe('Cookie-based API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    mockLocation.href = '';
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should include credentials in all requests', async () => {
    const apiClient = getApiClient();
    
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    await apiClient.get('/api/test');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/test'),
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('should redirect to login on 401 error', async () => {
    const apiClient = getApiClient();
    
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    try {
      await apiClient.get('/api/protected');
    } catch (error) {
      // Error is expected
    }

    expect(mockLocation.href).toBe('/login');
  });

  it('should handle FormData uploads without JSON stringification', async () => {
    const apiClient = getApiClient();
    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    await apiClient.uploadFile('/api/upload', file);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/upload'),
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        body: expect.any(FormData),
      })
    );

    // Verify body is FormData, not stringified
    const callArgs = mockFetch.mock.calls[0][1];
    expect(callArgs.body).toBeInstanceOf(FormData);
  });

  it('should handle JSON requests with proper stringification', async () => {
    const apiClient = getApiClient();
    const testData = { name: 'test', value: 123 };
    
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    await apiClient.post('/api/data', testData);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/data'),
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        body: JSON.stringify(testData),
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    );
  });

  it('should not include manual token headers', async () => {
    const apiClient = getApiClient();
    
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    await apiClient.get('/api/test');

    const callArgs = mockFetch.mock.calls[0][1];
    expect(callArgs.headers).not.toHaveProperty('Authorization');
    expect(callArgs.headers).not.toHaveProperty('X-Auth-Token');
  });

  it('should handle network errors without complex retry logic', async () => {
    const apiClient = getApiClient();
    
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    await expect(apiClient.get('/api/test', { skipFallback: true })).rejects.toThrow('Network error');
    
    // Should only make one attempt, no retries
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });
});