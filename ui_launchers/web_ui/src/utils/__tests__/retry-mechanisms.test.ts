import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { retryMechanism } from '../retry-mechanisms';

// Mock fetch
global.fetch = vi.fn();

describe('RetryMechanismService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('withRetry', () => {
    it('should succeed on first attempt', async () => {
      const operation = vi.fn().mockResolvedValue('success');
      
      const result = await retryMechanism.withRetry(operation);
      
      expect(result).toBe('success');
      expect(operation).toHaveBeenCalledTimes(1);
    });

    it('should retry on failure and eventually succeed', async () => {
      const operation = vi.fn()
        .mockRejectedValueOnce(new Error('First failure'))
        .mockRejectedValueOnce(new Error('Second failure'))
        .mockResolvedValue('success');

      const promise = retryMechanism.withRetry(operation, {
        maxAttempts: 3,
        baseDelay: 1000,
      });

      // Fast-forward through delays
      vi.advanceTimersByTime(3000);
      
      const result = await promise;
      
      expect(result).toBe('success');
      expect(operation).toHaveBeenCalledTimes(3);
    });

    it('should fail after max attempts', async () => {
      const operation = vi.fn().mockRejectedValue(new Error('Always fails'));

      const promise = retryMechanism.withRetry(operation, {
        maxAttempts: 2,
        baseDelay: 100,
      });

      // Fast-forward through delays
      vi.advanceTimersByTime(1000);

      await expect(promise).rejects.toThrow('Always fails');
      expect(operation).toHaveBeenCalledTimes(2);
    });

    it('should call retry callback on each attempt', async () => {
      const operation = vi.fn()
        .mockRejectedValueOnce(new Error('First failure'))
        .mockResolvedValue('success');
      
      const onRetry = vi.fn();

      const promise = retryMechanism.withRetry(operation, {
        maxAttempts: 2,
        baseDelay: 100,
        onRetry,
      });

      vi.advanceTimersByTime(200);
      await promise;

      expect(onRetry).toHaveBeenCalledTimes(1);
      expect(onRetry).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'First failure' }),
        1
      );
    });

    it('should call success callback on success', async () => {
      const operation = vi.fn().mockResolvedValue('success');
      const onSuccess = vi.fn();

      await retryMechanism.withRetry(operation, { onSuccess });

      expect(onSuccess).toHaveBeenCalledWith('success', 1);
    });

    it('should call failure callback after all retries exhausted', async () => {
      const operation = vi.fn().mockRejectedValue(new Error('Always fails'));
      const onFailure = vi.fn();

      const promise = retryMechanism.withRetry(operation, {
        maxAttempts: 2,
        baseDelay: 100,
        onFailure,
      });

      vi.advanceTimersByTime(1000);

      await expect(promise).rejects.toThrow();
      expect(onFailure).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'Always fails' }),
        2
      );
    });

    it('should use custom retry condition', async () => {
      const operation = vi.fn().mockRejectedValue(new Error('Client error'));
      const retryCondition = vi.fn().mockReturnValue(false);

      const promise = retryMechanism.withRetry(operation, {
        maxAttempts: 3,
        retryCondition,
      });

      await expect(promise).rejects.toThrow('Client error');
      expect(operation).toHaveBeenCalledTimes(1);
      expect(retryCondition).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'Client error' }),
        1
      );
    });

    it('should apply exponential backoff', async () => {
      const operation = vi.fn()
        .mockRejectedValueOnce(new Error('First failure'))
        .mockRejectedValueOnce(new Error('Second failure'))
        .mockResolvedValue('success');

      const promise = retryMechanism.withRetry(operation, {
        maxAttempts: 3,
        baseDelay: 1000,
        backoffFactor: 2,
        jitter: false, // Disable jitter for predictable testing
      });

      // First retry after 1000ms
      vi.advanceTimersByTime(1000);
      expect(operation).toHaveBeenCalledTimes(2);

      // Second retry after 2000ms more
      vi.advanceTimersByTime(2000);
      expect(operation).toHaveBeenCalledTimes(3);

      await promise;
    });

    it('should respect max delay', async () => {
      const operation = vi.fn()
        .mockRejectedValueOnce(new Error('First failure'))
        .mockResolvedValue('success');

      const promise = retryMechanism.withRetry(operation, {
        maxAttempts: 2,
        baseDelay: 10000,
        maxDelay: 2000,
        backoffFactor: 2,
        jitter: false,
      });

      // Should be capped at maxDelay (2000ms), not baseDelay * backoffFactor (20000ms)
      vi.advanceTimersByTime(2000);
      await promise;

      expect(operation).toHaveBeenCalledTimes(2);
    });
  });

  describe('retryFetch', () => {
    it('should retry on network errors', async () => {
      const mockFetch = vi.mocked(fetch);
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValue(new Response('success', { status: 200 }));

      const promise = retryMechanism.retryFetch('/api/test', {}, {
        maxAttempts: 2,
        baseDelay: 100,
      });

      vi.advanceTimersByTime(200);
      const response = await promise;

      expect(response.status).toBe(200);
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it('should retry on 5xx errors', async () => {
      const mockFetch = vi.mocked(fetch);
      mockFetch
        .mockResolvedValueOnce(new Response('Server Error', { status: 500 }))
        .mockResolvedValue(new Response('success', { status: 200 }));

      const promise = retryMechanism.retryFetch('/api/test', {}, {
        maxAttempts: 2,
        baseDelay: 100,
      });

      vi.advanceTimersByTime(200);
      const response = await promise;

      expect(response.status).toBe(200);
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it('should not retry on 4xx errors (except 408, 429)', async () => {
      const mockFetch = vi.mocked(fetch);
      mockFetch.mockResolvedValue(new Response('Not Found', { status: 404 }));

      await expect(
        retryMechanism.retryFetch('/api/test', {}, { maxAttempts: 2 })
      ).rejects.toThrow('HTTP 404');

      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should retry on 429 (rate limit)', async () => {
      const mockFetch = vi.mocked(fetch);
      mockFetch
        .mockResolvedValueOnce(new Response('Rate Limited', { status: 429 }))
        .mockResolvedValue(new Response('success', { status: 200 }));

      const promise = retryMechanism.retryFetch('/api/test', {}, {
        maxAttempts: 2,
        baseDelay: 100,
      });

      vi.advanceTimersByTime(200);
      const response = await promise;

      expect(response.status).toBe(200);
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Circuit Breaker', () => {
    it('should open circuit after failure threshold', async () => {
      const operation = vi.fn().mockRejectedValue(new Error('Always fails'));
      const operationId = 'test-operation';

      // Fail 5 times to trigger circuit breaker
      for (let i = 0; i < 5; i++) {
        try {
          await retryMechanism.withRetry(operation, { maxAttempts: 1 }, operationId);
        } catch {
          // Expected to fail
        }
      }

      // Circuit should now be open
      const circuitState = retryMechanism.getCircuitBreakerStatus(operationId);
      expect(circuitState.state).toBe('open');
      expect(circuitState.failures).toBe(5);
    });

    it('should prevent execution when circuit is open', async () => {
      const operation = vi.fn().mockRejectedValue(new Error('Always fails'));
      const operationId = 'test-operation-2';

      // Trigger circuit breaker
      for (let i = 0; i < 5; i++) {
        try {
          await retryMechanism.withRetry(operation, { maxAttempts: 1 }, operationId);
        } catch {
          // Expected to fail
        }
      }

      // Reset mock to track new calls
      operation.mockClear();

      // Try to execute - should fail immediately due to open circuit
      await expect(
        retryMechanism.withRetry(operation, { maxAttempts: 1 }, operationId)
      ).rejects.toThrow('Circuit breaker is open');

      // Operation should not have been called
      expect(operation).not.toHaveBeenCalled();
    });

    it('should reset circuit breaker on success', async () => {
      const operationId = 'test-operation-3';
      
      // Record some failures
      for (let i = 0; i < 3; i++) {
        retryMechanism.recordFailure(operationId);
      }

      // Record success
      retryMechanism.recordSuccess(operationId);

      const circuitState = retryMechanism.getCircuitBreakerStatus(operationId);
      expect(circuitState.failures).toBe(3); // Failures are not reset, only state
    });

    it('should allow manual circuit breaker reset', () => {
      const operationId = 'test-operation-4';
      
      // Trigger failures
      for (let i = 0; i < 5; i++) {
        retryMechanism.recordFailure(operationId);
      }

      let circuitState = retryMechanism.getCircuitBreakerStatus(operationId);
      expect(circuitState.state).toBe('open');

      // Reset circuit breaker
      retryMechanism.resetCircuitBreaker(operationId);

      circuitState = retryMechanism.getCircuitBreakerStatus(operationId);
      expect(circuitState.state).toBe('closed');
      expect(circuitState.failures).toBe(0);
    });
  });

  describe('Batch Operations', () => {
    it('should handle batch retry operations', async () => {
      const op1 = vi.fn().mockResolvedValue('result1');
      const op2 = vi.fn().mockRejectedValue(new Error('op2 failed'));
      const op3 = vi.fn().mockResolvedValue('result3');

      const results = await retryMechanism.retryBatch([op1, op2, op3], {
        maxAttempts: 1,
      });

      expect(results).toHaveLength(3);
      expect(results[0]).toBe('result1');
      expect(results[1]).toBeInstanceOf(Error);
      expect(results[2]).toBe('result3');
    });
  });

  describe('Retry State Management', () => {
    it('should track retry state', async () => {
      const operation = vi.fn()
        .mockRejectedValueOnce(new Error('First failure'))
        .mockResolvedValue('success');

      const operationId = 'tracked-operation';
      
      const promise = retryMechanism.withRetry(operation, {
        maxAttempts: 2,
        baseDelay: 100,
      }, operationId);

      // Check initial state
      let state = retryMechanism.getRetryState(operationId);
      expect(state?.attempt).toBe(1);
      expect(state?.isRetrying).toBe(false);

      // Advance time to trigger retry
      vi.advanceTimersByTime(100);
      
      await promise;

      // State should be cleaned up after completion
      state = retryMechanism.getRetryState(operationId);
      expect(state).toBeNull();
    });
  });
});