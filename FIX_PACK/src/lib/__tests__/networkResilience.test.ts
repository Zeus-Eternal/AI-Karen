import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { CircuitBreaker, NetworkResilience, CircuitBreakerState, resilientFetch } from '../networkResilience';
import { telemetryService } from '../telemetry';

// Mock telemetry service
vi.mock('../telemetry', () => ({
  telemetryService: {
    track: vi.fn(),
  },
}));

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true,
});

describe('CircuitBreaker', () => {
  let circuitBreaker: CircuitBreaker;

  beforeEach(() => {
    vi.clearAllMocks();
    circuitBreaker = new CircuitBreaker({
      failureThreshold: 3,
      recoveryTimeout: 5000,
      correlationId: 'test-correlation',
    });
  });

  it('starts in CLOSED state', () => {
    expect(circuitBreaker.getState()).toBe(CircuitBreakerState.CLOSED);
  });

  it('opens after failure threshold is reached', async () => {
    const failingFunction = vi.fn().mockRejectedValue(new Error('Test error'));

    // Trigger failures up to threshold
    for (let i = 0; i < 3; i++) {
      try {
        await circuitBreaker.execute(failingFunction);
      } catch (error) {
        // Expected to fail
      }
    }

    expect(circuitBreaker.getState()).toBe(CircuitBreakerState.OPEN);
    expect(telemetryService.track).toHaveBeenCalledWith(
      'circuit_breaker.state_changed',
      expect.objectContaining({
        from: CircuitBreakerState.CLOSED,
        to: CircuitBreakerState.OPEN,
      }),
      'test-correlation'
    );
  });

  it('blocks requests when OPEN', async () => {
    const failingFunction = vi.fn().mockRejectedValue(new Error('Test error'));

    // Open the circuit breaker
    for (let i = 0; i < 3; i++) {
      try {
        await circuitBreaker.execute(failingFunction);
      } catch (error) {
        // Expected to fail
      }
    }

    // Now it should block requests
    await expect(circuitBreaker.execute(vi.fn())).rejects.toThrow('Circuit breaker is OPEN');
    expect(telemetryService.track).toHaveBeenCalledWith(
      'circuit_breaker.request_blocked',
      expect.objectContaining({
        state: CircuitBreakerState.OPEN,
      }),
      'test-correlation'
    );
  });

  it('transitions to HALF_OPEN after recovery timeout', async () => {
    vi.useFakeTimers();
    
    const failingFunction = vi.fn().mockRejectedValue(new Error('Test error'));

    // Open the circuit breaker
    for (let i = 0; i < 3; i++) {
      try {
        await circuitBreaker.execute(failingFunction);
      } catch (error) {
        // Expected to fail
      }
    }

    expect(circuitBreaker.getState()).toBe(CircuitBreakerState.OPEN);

    // Fast-forward past recovery timeout
    vi.advanceTimersByTime(6000);

    const successFunction = vi.fn().mockResolvedValue('success');
    await circuitBreaker.execute(successFunction);

    expect(circuitBreaker.getState()).toBe(CircuitBreakerState.HALF_OPEN);
    
    vi.useRealTimers();
  });

  it('closes after successful requests in HALF_OPEN state', async () => {
    vi.useFakeTimers();
    
    const failingFunction = vi.fn().mockRejectedValue(new Error('Test error'));
    const successFunction = vi.fn().mockResolvedValue('success');

    // Open the circuit breaker
    for (let i = 0; i < 3; i++) {
      try {
        await circuitBreaker.execute(failingFunction);
      } catch (error) {
        // Expected to fail
      }
    }

    // Wait for recovery timeout
    vi.advanceTimersByTime(6000);

    // Execute successful requests to close the circuit
    await circuitBreaker.execute(successFunction);
    expect(circuitBreaker.getState()).toBe(CircuitBreakerState.HALF_OPEN);

    await circuitBreaker.execute(successFunction);
    await circuitBreaker.execute(successFunction);

    expect(circuitBreaker.getState()).toBe(CircuitBreakerState.CLOSED);
    
    vi.useRealTimers();
  });

  it('resets state correctly', () => {
    const failingFunction = vi.fn().mockRejectedValue(new Error('Test error'));

    // Cause some failures
    circuitBreaker.execute(failingFunction).catch(() => {});
    circuitBreaker.execute(failingFunction).catch(() => {});

    const metrics = circuitBreaker.getMetrics();
    expect(metrics.failureCount).toBe(2);

    circuitBreaker.reset();

    const resetMetrics = circuitBreaker.getMetrics();
    expect(resetMetrics.state).toBe(CircuitBreakerState.CLOSED);
    expect(resetMetrics.failureCount).toBe(0);
    expect(resetMetrics.successCount).toBe(0);
  });
});

describe('NetworkResilience', () => {
  let networkResilience: NetworkResilience;

  beforeEach(() => {
    vi.clearAllMocks();
    networkResilience = new NetworkResilience({
      failureThreshold: 2,
      correlationId: 'test-correlation',
    });
  });

  afterEach(() => {
    networkResilience.destroy();
  });

  it('makes successful requests', async () => {
    const mockResponse = new Response('success', { status: 200 });
    mockFetch.mockResolvedValue(mockResponse);

    const response = await networkResilience.fetchWithResilience({
      url: 'http://test.com/api',
    });

    expect(response).toBe(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith('http://test.com/api', {
      signal: expect.any(AbortSignal),
    });
  });

  it('retries failed requests with exponential backoff', async () => {
    vi.useFakeTimers();
    
    mockFetch
      .mockRejectedValueOnce(new TypeError('Network error'))
      .mockRejectedValueOnce(new TypeError('Network error'))
      .mockResolvedValueOnce(new Response('success', { status: 200 }));

    const promise = networkResilience.fetchWithResilience(
      { url: 'http://test.com/api' },
      { maxRetries: 3, baseDelay: 1000 }
    );

    // Fast-forward through retry delays
    vi.advanceTimersByTime(5000);

    const response = await promise;
    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(3);

    expect(telemetryService.track).toHaveBeenCalledWith(
      'network.retry_scheduled',
      expect.objectContaining({
        attempt: 1,
        delay: expect.any(Number),
      }),
      undefined
    );

    vi.useRealTimers();
  });

  it('blocks requests when offline', async () => {
    // Simulate offline
    Object.defineProperty(navigator, 'onLine', { value: false });
    networkResilience = new NetworkResilience();

    await expect(
      networkResilience.fetchWithResilience({ url: 'http://test.com/api' })
    ).rejects.toThrow('Network is offline');

    expect(telemetryService.track).toHaveBeenCalledWith(
      'network.request_blocked_offline',
      expect.objectContaining({
        url: 'http://test.com/api',
      }),
      undefined
    );
  });

  it('handles timeout correctly', async () => {
    vi.useFakeTimers();
    
    // Mock fetch to never resolve
    mockFetch.mockImplementation(() => new Promise(() => {}));

    const promise = networkResilience.fetchWithResilience(
      { url: 'http://test.com/api', timeout: 1000 }
    );

    // Fast-forward past timeout
    vi.advanceTimersByTime(1500);

    await expect(promise).rejects.toThrow();
    
    vi.useRealTimers();
  });

  it('performs health checks', async () => {
    const mockResponse = new Response('', { status: 200 });
    mockFetch.mockResolvedValue(mockResponse);

    const isHealthy = await networkResilience.healthCheck('http://test.com/health');

    expect(isHealthy).toBe(true);
    expect(mockFetch).toHaveBeenCalledWith('http://test.com/health', {
      method: 'HEAD',
      signal: expect.any(AbortSignal),
    });

    expect(telemetryService.track).toHaveBeenCalledWith(
      'network.health_check',
      expect.objectContaining({
        url: 'http://test.com/health',
        healthy: true,
        status: 200,
      })
    );
  });

  it('reports unhealthy status on failed health check', async () => {
    mockFetch.mockRejectedValue(new Error('Connection failed'));

    const isHealthy = await networkResilience.healthCheck('http://test.com/health');

    expect(isHealthy).toBe(false);
    expect(telemetryService.track).toHaveBeenCalledWith(
      'network.health_check',
      expect.objectContaining({
        url: 'http://test.com/health',
        healthy: false,
        error: 'Connection failed',
      })
    );
  });

  it('provides network status', () => {
    const status = networkResilience.getNetworkStatus();

    expect(status).toEqual({
      isOnline: expect.any(Boolean),
      circuitBreaker: expect.objectContaining({
        state: CircuitBreakerState.CLOSED,
        failureCount: 0,
        successCount: 0,
        lastFailureTime: 0,
      }),
      connection: expect.any(Object),
    });
  });

  it('handles online/offline events', () => {
    const listener = vi.fn();
    const unsubscribe = networkResilience.onOnlineStatusChange(listener);

    // Simulate going offline
    window.dispatchEvent(new Event('offline'));
    expect(listener).toHaveBeenCalledWith(false);

    // Simulate going online
    window.dispatchEvent(new Event('online'));
    expect(listener).toHaveBeenCalledWith(true);

    unsubscribe();
  });

  it('uses custom retry condition', async () => {
    const customRetryCondition = vi.fn().mockReturnValue(false);
    mockFetch.mockRejectedValue(new Error('Custom error'));

    await expect(
      networkResilience.fetchWithResilience(
        { url: 'http://test.com/api' },
        { retryCondition: customRetryCondition }
      )
    ).rejects.toThrow('Custom error');

    expect(customRetryCondition).toHaveBeenCalledWith(expect.any(Error));
    expect(mockFetch).toHaveBeenCalledTimes(1); // No retries due to custom condition
  });

  it('calls onRetry callback', async () => {
    vi.useFakeTimers();
    
    const onRetry = vi.fn();
    mockFetch
      .mockRejectedValueOnce(new TypeError('Network error'))
      .mockResolvedValueOnce(new Response('success', { status: 200 }));

    const promise = networkResilience.fetchWithResilience(
      { url: 'http://test.com/api' },
      { onRetry, baseDelay: 1000 }
    );

    vi.advanceTimersByTime(2000);
    await promise;

    expect(onRetry).toHaveBeenCalledWith(1, expect.any(Error));
    
    vi.useRealTimers();
  });
});

describe('resilientFetch utility', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('works as a convenience function', async () => {
    const mockResponse = new Response('success', { status: 200 });
    mockFetch.mockResolvedValue(mockResponse);

    const response = await resilientFetch('http://test.com/api');

    expect(response).toBe(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith('http://test.com/api', {
      signal: expect.any(AbortSignal),
    });
  });

  it('passes through options correctly', async () => {
    const mockResponse = new Response('success', { status: 200 });
    mockFetch.mockResolvedValue(mockResponse);

    await resilientFetch(
      'http://test.com/api',
      { method: 'POST', body: 'test' },
      { maxRetries: 5, correlationId: 'test-id' }
    );

    expect(mockFetch).toHaveBeenCalledWith('http://test.com/api', {
      method: 'POST',
      body: 'test',
      signal: expect.any(AbortSignal),
    });
  });
});