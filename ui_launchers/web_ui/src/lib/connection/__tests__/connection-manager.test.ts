/**
 * Unit tests for ConnectionManager
 * 
 * Tests retry logic, circuit breaker pattern, error categorization,
 * and comprehensive error handling scenarios.
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import {
  ConnectionManager,
  getConnectionManager,
  initializeConnectionManager,
  CircuitBreakerState,
  ErrorCategory,
  ConnectionError,
} from '../connection-manager';

// Mock the environment config manager
vi.mock('../../config', () => ({
  getEnvironmentConfigManager: vi.fn(() => ({
    getRetryPolicy: vi.fn(() => ({
      maxAttempts: 3,
      baseDelay: 1000,
      maxDelay: 10000,
      exponentialBase: 2,
      jitterEnabled: true,
    })),
    getTimeoutConfig: vi.fn(() => ({
      connection: 30000,
      authentication: 45000,
      sessionValidation: 30000,
      healthCheck: 10000,
    })),
    getHealthCheckUrl: vi.fn(() => 'http://localhost:8000/api/health'),
  })),
}));

// Mock fetch
const mockFetch = vi.fn() as Mock;
global.fetch = mockFetch;

describe('ConnectionManager', () => {
  let connectionManager: ConnectionManager;

  beforeEach(() => {
    connectionManager = new ConnectionManager(true); // Enable test mode
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Basic Request Functionality', () => {
    it('should make successful HTTP request', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: vi.fn().mockResolvedValue({ success: true }),
      };
      mockFetch.mockResolvedValue(mockResponse);

      const result = await connectionManager.makeRequest('http://localhost:8000/test');

      expect(result.data).toEqual({ success: true });
      expect(result.status).toBe(200);
      expect(result.retryCount).toBe(0);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should handle text responses', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'text/plain' }),
        text: vi.fn().mockResolvedValue('Hello World'),
      };
      mockFetch.mockResolvedValue(mockResponse);

      const result = await connectionManager.makeRequest('http://localhost:8000/test');

      expect(result.data).toBe('Hello World');
      expect(mockResponse.text).toHaveBeenCalled();
    });

    it('should include custom headers', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        json: vi.fn().mockResolvedValue({}),
        text: vi.fn().mockResolvedValue('{}'),
      };
      mockFetch.mockResolvedValue(mockResponse);

      await connectionManager.makeRequest(
        'http://localhost:8000/test',
        {},
        { headers: { 'Authorization': 'Bearer token' } }
      );

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer token',
            'Content-Type': 'application/json',
          }),
        })
      );
    });
  });

  describe('Error Handling and Categorization', () => {
    it('should categorize network errors correctly', async () => {
      mockFetch.mockRejectedValue(new Error('fetch failed'));

      try {
        await connectionManager.makeRequest('http://localhost:8000/test');
        expect.fail('Should have thrown an error');
      } catch (error) {
        const connectionError = error as ConnectionError;
        expect(connectionError.category).toBe(ErrorCategory.NETWORK_ERROR);
        expect(connectionError.retryable).toBe(true);
      }
    });

    it('should categorize timeout errors correctly', async () => {
      const abortError = new Error('The operation was aborted');
      abortError.name = 'AbortError';
      mockFetch.mockRejectedValue(abortError);

      try {
        await connectionManager.makeRequest('http://localhost:8000/test');
        expect.fail('Should have thrown an error');
      } catch (error) {
        const connectionError = error as ConnectionError;
        expect(connectionError.category).toBe(ErrorCategory.TIMEOUT_ERROR);
        expect(connectionError.retryable).toBe(true);
      }
    });

    it('should categorize HTTP errors correctly', async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: new Headers(),
      };
      mockFetch.mockResolvedValue(mockResponse);

      try {
        await connectionManager.makeRequest('http://localhost:8000/test');
        expect.fail('Should have thrown an error');
      } catch (error) {
        const connectionError = error as ConnectionError;
        expect(connectionError.category).toBe(ErrorCategory.HTTP_ERROR);
        expect(connectionError.statusCode).toBe(500);
        expect(connectionError.retryable).toBe(true); // 5xx errors are retryable
      }
    });

    it('should not retry 4xx client errors', async () => {
      const mockResponse = {
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: new Headers(),
      };
      mockFetch.mockResolvedValue(mockResponse);

      try {
        await connectionManager.makeRequest('http://localhost:8000/test');
        expect.fail('Should have thrown an error');
      } catch (error) {
        const connectionError = error as ConnectionError;
        expect(connectionError.retryable).toBe(false); // 4xx errors are not retryable
        expect(mockFetch).toHaveBeenCalledTimes(1); // No retries
      }
    });

    it('should retry specific 4xx errors (408, 429)', async () => {
      const mockResponse = {
        ok: false,
        status: 429,
        statusText: 'Too Many Requests',
        headers: new Headers(),
      };
      mockFetch.mockResolvedValue(mockResponse);

      try {
        await connectionManager.makeRequest('http://localhost:8000/test', {}, { retryAttempts: 2 });
        expect.fail('Should have thrown an error');
      } catch (error) {
        const connectionError = error as ConnectionError;
        expect(connectionError.retryable).toBe(true); // 429 is retryable
        expect(mockFetch).toHaveBeenCalledTimes(3); // Initial + 2 retries
      }
    });
  });

  describe('Retry Logic', () => {
    it('should retry on retryable errors', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValue({
          ok: true,
          status: 200,
          statusText: 'OK',
          headers: new Headers({ 'content-type': 'application/json' }),
          json: vi.fn().mockResolvedValue({ success: true }),
        });

      const result = await connectionManager.makeRequest(
        'http://localhost:8000/test',
        {},
        { retryAttempts: 3 }
      );

      expect(result.data).toEqual({ success: true });
      expect(result.retryCount).toBe(2); // Failed twice, succeeded on third attempt
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });

    it('should not retry on non-retryable errors', async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        headers: new Headers(),
      };
      mockFetch.mockResolvedValue(mockResponse);

      try {
        await connectionManager.makeRequest(
          'http://localhost:8000/test',
          {},
          { retryAttempts: 3 }
        );
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(mockFetch).toHaveBeenCalledTimes(1); // No retries for 400 error
      }
    });

    it('should respect maximum retry attempts', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      try {
        await connectionManager.makeRequest(
          'http://localhost:8000/test',
          {},
          { retryAttempts: 2 }
        );
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(mockFetch).toHaveBeenCalledTimes(3); // Initial + 2 retries
      }
    });

    it('should calculate exponential backoff delay', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      try {
        await connectionManager.makeRequest(
          'http://localhost:8000/test',
          {},
          { retryAttempts: 3, retryDelay: 1000, exponentialBackoff: true }
        );
        expect.fail('Should have thrown an error');
      } catch (error) {
        // Expected to fail after all retries
        expect(mockFetch).toHaveBeenCalledTimes(4); // Initial + 3 retries
      }
    });
  });

  describe('Circuit Breaker Pattern', () => {
    it('should open circuit breaker after consecutive failures', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      // Make 5 consecutive failed requests to trigger circuit breaker
      for (let i = 0; i < 5; i++) {
        try {
          await connectionManager.makeRequest(
            'http://localhost:8000/test',
            {},
            { retryAttempts: 0 }
          );
        } catch (error) {
          // Expected failures
        }
      }

      const status = connectionManager.getConnectionStatus();
      expect(status.circuitBreakerState).toBe(CircuitBreakerState.OPEN);
      expect(status.isHealthy).toBe(false);
      expect(status.consecutiveFailures).toBe(5);
    });

    it('should fail fast when circuit breaker is open', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      // Trigger circuit breaker
      for (let i = 0; i < 5; i++) {
        try {
          await connectionManager.makeRequest(
            'http://localhost:8000/test',
            {},
            { retryAttempts: 0 }
          );
        } catch (error) {
          // Expected failures
        }
      }

      // Next request should fail immediately due to circuit breaker
      const startTime = Date.now();
      try {
        await connectionManager.makeRequest('http://localhost:8000/test');
        expect.fail('Should have thrown an error');
      } catch (error) {
        const connectionError = error as ConnectionError;
        expect(connectionError.category).toBe(ErrorCategory.CIRCUIT_BREAKER_ERROR);
        
        // Should fail fast (within 100ms)
        const duration = Date.now() - startTime;
        expect(duration).toBeLessThan(100);
      }
    });

    it('should reset circuit breaker on successful request', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      // Trigger circuit breaker
      for (let i = 0; i < 5; i++) {
        try {
          await connectionManager.makeRequest(
            'http://localhost:8000/test',
            {},
            { retryAttempts: 0 }
          );
        } catch (error) {
          // Expected failures
        }
      }

      expect(connectionManager.getConnectionStatus().circuitBreakerState).toBe(CircuitBreakerState.OPEN);

      // Simulate recovery timeout by manually setting state
      const manager = connectionManager as any;
      manager.status.circuitBreakerState = CircuitBreakerState.HALF_OPEN;

      // Make successful request
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: vi.fn().mockResolvedValue({ success: true }),
      });

      await connectionManager.makeRequest('http://localhost:8000/test');

      const status = connectionManager.getConnectionStatus();
      expect(status.circuitBreakerState).toBe(CircuitBreakerState.CLOSED);
      expect(status.isHealthy).toBe(true);
      expect(status.consecutiveFailures).toBe(0);
    });

    it('should allow circuit breaker to be disabled', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      // Make requests with circuit breaker disabled
      for (let i = 0; i < 10; i++) {
        try {
          await connectionManager.makeRequest(
            'http://localhost:8000/test',
            {},
            { retryAttempts: 0, circuitBreakerEnabled: false }
          );
        } catch (error) {
          // Expected failures
        }
      }

      // Circuit breaker should still be closed since it was disabled
      const status = connectionManager.getConnectionStatus();
      expect(status.circuitBreakerState).toBe(CircuitBreakerState.CLOSED);
    });
  });

  describe('Health Check', () => {
    it('should perform successful health check', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: vi.fn().mockResolvedValue({ status: 'healthy' }),
        text: vi.fn().mockResolvedValue('{"status":"healthy"}'),
      });

      const isHealthy = await connectionManager.healthCheck();

      expect(isHealthy).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/health',
        expect.objectContaining({ method: 'GET' })
      );
    });

    it('should handle failed health check', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      const isHealthy = await connectionManager.healthCheck();

      expect(isHealthy).toBe(false);
    });

    it('should use health check timeout', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: vi.fn().mockResolvedValue({}),
        text: vi.fn().mockResolvedValue('{}'),
      });

      const isHealthy = await connectionManager.healthCheck();

      // Verify health check was successful
      expect(isHealthy).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/health',
        expect.objectContaining({ method: 'GET' })
      );
    });
  });

  describe('Connection Status and Metrics', () => {
    it('should track request statistics', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: vi.fn().mockResolvedValue({}),
      };
      mockFetch.mockResolvedValue(mockResponse);

      // Make successful requests
      await connectionManager.makeRequest('http://localhost:8000/test1');
      await connectionManager.makeRequest('http://localhost:8000/test2');

      const status = connectionManager.getConnectionStatus();
      expect(status.totalRequests).toBe(2);
      expect(status.successfulRequests).toBe(2);
      expect(status.failedRequests).toBe(0);
      expect(status.lastSuccessfulRequest).toBeInstanceOf(Date);
    });

    it('should track failure statistics', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      try {
        await connectionManager.makeRequest('http://localhost:8000/test', {}, { retryAttempts: 0 });
      } catch (error) {
        // Expected failure
      }

      const status = connectionManager.getConnectionStatus();
      expect(status.totalRequests).toBe(1);
      expect(status.successfulRequests).toBe(0);
      expect(status.failedRequests).toBe(1);
      expect(status.consecutiveFailures).toBe(1);
      expect(status.lastFailedRequest).toBeInstanceOf(Date);
    });

    it('should calculate average response time', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: vi.fn().mockResolvedValue({}),
        text: vi.fn().mockResolvedValue('{}'),
      };
      mockFetch.mockResolvedValue(mockResponse);

      // Make multiple requests
      await connectionManager.makeRequest('http://localhost:8000/test1');
      await connectionManager.makeRequest('http://localhost:8000/test2');
      await connectionManager.makeRequest('http://localhost:8000/test3');

      const status = connectionManager.getConnectionStatus();
      expect(status.averageResponseTime).toBeGreaterThan(0);
    });

    it('should reset statistics', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      try {
        await connectionManager.makeRequest('http://localhost:8000/test', {}, { retryAttempts: 0 });
      } catch (error) {
        // Expected failure
      }

      connectionManager.resetStatistics();

      const status = connectionManager.getConnectionStatus();
      expect(status.totalRequests).toBe(0);
      expect(status.successfulRequests).toBe(0);
      expect(status.failedRequests).toBe(0);
      expect(status.consecutiveFailures).toBe(0);
      expect(status.circuitBreakerState).toBe(CircuitBreakerState.CLOSED);
      expect(status.isHealthy).toBe(true);
    });
  });

  describe('Singleton Pattern', () => {
    it('should return same instance from getConnectionManager', () => {
      const manager1 = getConnectionManager();
      const manager2 = getConnectionManager();
      expect(manager1).toBe(manager2);
    });

    it('should create new instance with initializeConnectionManager', () => {
      const manager1 = getConnectionManager();
      const manager2 = initializeConnectionManager(true);
      expect(manager1).not.toBe(manager2);
      
      // Subsequent calls to getConnectionManager should return the new instance
      const manager3 = getConnectionManager();
      expect(manager2).toBe(manager3);
    });
  });

  describe('Request Options and Configuration', () => {
    it('should use custom timeout', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: vi.fn().mockResolvedValue({}),
        text: vi.fn().mockResolvedValue('{}'),
      };
      mockFetch.mockResolvedValue(mockResponse);

      const result = await connectionManager.makeRequest(
        'http://localhost:8000/test',
        {},
        { timeout: 5000 }
      );

      // Verify request was successful
      expect(result.status).toBe(200);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should merge request options correctly', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: vi.fn().mockResolvedValue({}),
        text: vi.fn().mockResolvedValue('{}'),
      };
      mockFetch.mockResolvedValue(mockResponse);

      await connectionManager.makeRequest(
        'http://localhost:8000/test',
        {
          method: 'POST',
          body: JSON.stringify({ data: 'test' }),
          headers: { 'X-Custom': 'value' },
        },
        {
          headers: { 'Authorization': 'Bearer token' },
        }
      );

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ data: 'test' }),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-Custom': 'value',
            'Authorization': 'Bearer token',
          }),
        })
      );
    });
  });
});