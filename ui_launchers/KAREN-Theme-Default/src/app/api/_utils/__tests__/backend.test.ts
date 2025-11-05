/**
 * Tests for backend utility functions
 * 
 * Requirements: 1.1, 3.1, 3.2
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { getBackendBaseUrl, getBackendCandidates, withBackendPath, getTimeoutConfig, getRetryPolicy, getEnvironmentInfo, validateBackendConfiguration, makeBackendRequest, apiRequest, apiGet, apiPost, apiPut, apiDelete, checkBackendHealth, getConnectionStatus } from '../backend';

// Mock dependencies
vi.mock('../../../../lib/config', () => ({
  getEnvironmentConfigManager: vi.fn(),
}));

vi.mock('../../../../lib/connection/connection-manager', () => ({
  getConnectionManager: vi.fn(),
  ConnectionError: class ConnectionError extends Error {
    constructor(
      message: string,
      public category: string,
      public retryable: boolean,
      public retryCount: number,
      public url?: string,
      public statusCode?: number,
      public duration?: number,
      public originalError?: Error
    ) {
      super(message);
      this.name = 'ConnectionError';
    }
  },
}));

import { getEnvironmentConfigManager } from '../../../../lib/config/index';
import { getConnectionManager, ConnectionError } from '../../../../lib/connection/connection-manager';

describe('Backend Utilities', () => {
  let mockConfigManager: any;
  let mockConnectionManager: any;

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();

    // Mock environment config manager
    mockConfigManager = {
      getBackendConfig: vi.fn().mockReturnValue({
        primaryUrl: 'http://localhost:8000',
        fallbackUrls: ['http://127.0.0.1:8000'],
        timeout: 30000,
        retryAttempts: 3,
        healthCheckInterval: 30000,
      }),
      getAllCandidateUrls: vi.fn().mockReturnValue([
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://0.0.0.0:8000',
      ]),
      getTimeoutConfig: vi.fn().mockReturnValue({
        connection: 30000,
        authentication: 45000,
        sessionValidation: 30000,
        healthCheck: 10000,
      }),
      getRetryPolicy: vi.fn().mockReturnValue({
        maxAttempts: 3,
        baseDelay: 1000,
        maxDelay: 10000,
        exponentialBase: 2,
        jitterEnabled: true,
      }),
      getEnvironmentInfo: vi.fn().mockReturnValue({
        type: 'local',
        networkMode: 'localhost',
        isDocker: false,
        isProduction: false,
      }),
      validateConfiguration: vi.fn().mockReturnValue({
        isValid: true,
        warnings: [],
        errors: [],
        environment: {
          type: 'local',
          networkMode: 'localhost',
          isDocker: false,
          isProduction: false,
        },
        config: {
          primaryUrl: 'http://localhost:8000',
          fallbackUrls: ['http://127.0.0.1:8000'],
          timeout: 30000,
          retryAttempts: 3,
          healthCheckInterval: 30000,
        },
      }),
      getHealthCheckUrl: vi.fn().mockReturnValue('http://localhost:8000/health'),
    };

    // Mock connection manager
    mockConnectionManager = {
      makeRequest: vi.fn(),
      healthCheck: vi.fn(),
      getConnectionStatus: vi.fn().mockReturnValue({
        isHealthy: true,
        lastSuccessfulRequest: new Date(),
        lastFailedRequest: null,
        consecutiveFailures: 0,
        totalRequests: 10,
        successfulRequests: 10,
        failedRequests: 0,
        averageResponseTime: 150,
        circuitBreakerState: 'closed',
      }),
    };

    (getEnvironmentConfigManager as Mock).mockReturnValue(mockConfigManager);
    (getConnectionManager as Mock).mockReturnValue(mockConnectionManager);

  afterEach(() => {
    vi.restoreAllMocks();

  describe('getBackendBaseUrl', () => {
    it('should return primary URL from config manager', () => {
      const url = getBackendBaseUrl();
      expect(url).toBe('http://localhost:8000');
      expect(mockConfigManager.getBackendConfig).toHaveBeenCalled();
    });

    it('should fallback to legacy implementation when config manager fails', () => {
      (getEnvironmentConfigManager as Mock).mockImplementation(() => {
        throw new Error('Config manager not available');
      });
      const url = getBackendBaseUrl();
      expect(url).toMatch(/^http:\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0):8000$/);
    });
  });

  describe('getBackendCandidates', () => {
    it('should return all candidate URLs from config manager', () => {
      const candidates = getBackendCandidates();
      expect(candidates).toEqual([
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://0.0.0.0:8000',
      ]);
      expect(mockConfigManager.getAllCandidateUrls).toHaveBeenCalled();
    });

    it('should include additional URLs', () => {
      const additional = ['http://custom:8000'];
      const candidates = getBackendCandidates(additional);
      expect(candidates).toContain('http://custom:8000');
    });

    it('should fallback to legacy implementation when config manager fails', () => {
      (getEnvironmentConfigManager as Mock).mockImplementation(() => {
        throw new Error('Config manager not available');
      });
      const candidates = getBackendCandidates();
      expect(Array.isArray(candidates)).toBe(true);
      expect(candidates.length).toBeGreaterThan(0);
    });
  });

  describe('withBackendPath', () => {
    it('should join path with base URL', () => {
      const result = withBackendPath('/api/test');
      expect(result).toBe('http://localhost:8000/api/test');
    });

    it('should handle path without leading slash', () => {
      const result = withBackendPath('api/test');
      expect(result).toBe('http://localhost:8000/api/test');
    });

    it('should use custom base URL', () => {
      const result = withBackendPath('/api/test', 'http://custom:9000');
      expect(result).toBe('http://custom:9000/api/test');
    });
  });

  describe('Configuration functions', () => {
    it('should return timeout config from config manager', () => {
      const config = getTimeoutConfig();
      expect(config).toEqual({
        connection: 30000,
        authentication: 45000,
        sessionValidation: 30000,
        healthCheck: 10000,
      });
    });

    it('should return retry policy from config manager', () => {
      const policy = getRetryPolicy();
      expect(policy).toEqual({
        maxAttempts: 3,
        baseDelay: 1000,
        maxDelay: 10000,
        exponentialBase: 2,
        jitterEnabled: true,
      });
    });

    it('should return environment info from config manager', () => {
      const info = getEnvironmentInfo();
      expect(info).toEqual({
        type: 'local',
        networkMode: 'localhost',
        isDocker: false,
        isProduction: false,
      });
    });

    it('should validate backend configuration', () => {
      const validation = validateBackendConfiguration();
      expect(validation.isValid).toBe(true);
      expect(validation.errors).toEqual([]);
    });
  });

  describe('makeBackendRequest', () => {
    it('should make successful request using connection manager', async () => {
      const mockResponse = {
        data: { success: true },
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        url: 'http://localhost:8000/api/test',
        duration: 100,
        retryCount: 0,
      };

      mockConnectionManager.makeRequest.mockResolvedValue(mockResponse);

      const result = await makeBackendRequest('/api/test');
      expect(result).toEqual(mockResponse);
      expect(mockConnectionManager.makeRequest).toHaveBeenCalledWith(
        'http://localhost:8000/api/test',
        {},
        {}
      );
    });

    it('should try fallback URLs on retryable errors', async () => {
      const error = new ConnectionError(
        'Network error',
        'network_error',
        true,
        1,
        'http://localhost:8000/api/test'
      );

      const mockResponse = {
        data: { success: true },
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        url: 'http://127.0.0.1:8000/api/test',
        duration: 150,
        retryCount: 0,
      };

      mockConnectionManager.makeRequest
        .mockRejectedValueOnce(error)
        .mockResolvedValueOnce(mockResponse);

      const result = await makeBackendRequest('/api/test');
      expect(result).toEqual(mockResponse);
      expect(mockConnectionManager.makeRequest).toHaveBeenCalledTimes(2);
    });

    it('should throw error if all fallbacks fail', async () => {
      const error = new ConnectionError(
        'Network error',
        'network_error',
        true,
        1,
        'http://localhost:8000/api/test'
      );

      mockConnectionManager.makeRequest.mockRejectedValue(error);

      await expect(makeBackendRequest('/api/test')).rejects.toThrow('Network error');
    });
  });

  describe('API convenience functions', () => {
    beforeEach(() => {
      mockConnectionManager.makeRequest.mockResolvedValue({
        data: { success: true },
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        url: 'http://localhost:8000/api/test',
        duration: 100,
        retryCount: 0,
      });
    });

    it('should make GET request', async () => {
      const result = await apiGet('/api/test');
      expect(result).toEqual({ success: true });
      expect(mockConnectionManager.makeRequest).toHaveBeenCalledWith(
        'http://localhost:8000/api/test',
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        },
        {}
      );
    });

    it('should make POST request with body', async () => {
      const body = { name: 'test' };
      const result = await apiPost('/api/test', body);
      expect(result).toEqual({ success: true });
      expect(mockConnectionManager.makeRequest).toHaveBeenCalledWith(
        'http://localhost:8000/api/test',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        },
        {}
      );
    });

    it('should make PUT request with body', async () => {
      const body = { name: 'updated' };
      const result = await apiPut('/api/test', body);
      expect(result).toEqual({ success: true });
      expect(mockConnectionManager.makeRequest).toHaveBeenCalledWith(
        'http://localhost:8000/api/test',
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        },
        {}
      );
    });

    it('should make DELETE request', async () => {
      const result = await apiDelete('/api/test');
      expect(result).toEqual({ success: true });
      expect(mockConnectionManager.makeRequest).toHaveBeenCalledWith(
        'http://localhost:8000/api/test',
        {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' },
        },
        {}
      );
    });

    it('should handle custom headers', async () => {
      const headers = { Authorization: 'Bearer token' };
      await apiGet('/api/test', headers);
      expect(mockConnectionManager.makeRequest).toHaveBeenCalledWith(
        'http://localhost:8000/api/test',
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json', ...headers },
        },
        {}
      );
    });
  });

  describe('Health and status functions', () => {
    it('should check backend health', async () => {
      mockConnectionManager.healthCheck.mockResolvedValue(true);

      const result = await checkBackendHealth();
      expect(result).toBe(true);
      expect(mockConnectionManager.healthCheck).toHaveBeenCalled();
    });

    it('should get connection status', () => {
      const status = getConnectionStatus();
      expect(status.isHealthy).toBe(true);
      expect(status.totalRequests).toBe(10);
      expect(mockConnectionManager.getConnectionStatus).toHaveBeenCalled();
    });
  });

  describe('Error handling', () => {
    it('should handle config manager errors gracefully', () => {
      (getEnvironmentConfigManager as Mock).mockImplementation(() => {
        throw new Error('Config manager failed');
      });

      const config = getTimeoutConfig();
      expect(config).toEqual({
        connection: 30000,
        authentication: 45000,
        sessionValidation: 30000,
        healthCheck: 10000,
      });
    });

    it('should handle validation errors gracefully', () => {
      (getEnvironmentConfigManager as Mock).mockImplementation(() => {
        throw new Error('Config manager failed');
      });

      const validation = validateBackendConfiguration();
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('Error: Config manager failed');
    });
  });
});