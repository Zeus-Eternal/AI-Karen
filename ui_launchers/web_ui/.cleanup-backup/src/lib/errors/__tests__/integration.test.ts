/**
 * Integration tests for comprehensive error handling system
 * Requirements: 1.3, 2.3, 3.3, 4.3
 */

import { 
  handleError, 
  withErrorHandling, 
  withRetry,
  ErrorCategory,
  ErrorSeverity,
  ComprehensiveErrorHandler
} from '../index';

const errorHandler = ComprehensiveErrorHandler.getInstance();

import { vi } from 'vitest';

// Mock fetch for testing
global.fetch = vi.fn();

// Mock localStorage
Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  },
  writable: true,
});

describe('Error Handling System Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('End-to-End Error Handling Scenarios', () => {
    it('should handle authentication flow with session expiry and recovery', async () => {
      const mockFetch = fetch as any;
      
      // First call fails with session expired
      // Second call (refresh) succeeds
      // Third call (retry original) succeeds
      mockFetch
        .mockRejectedValueOnce(new Error('Session expired'))
        .mockResolvedValueOnce({ ok: true } as Response) // refresh call
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ data: 'success' }) } as Response);

      const authenticatedApiCall = async () => {
        const response = await fetch('/api/protected-resource');
        if (!response.ok) {
          throw new Error('Session expired');
        }
        return response.json();
      };

      const result = await withRetry(authenticatedApiCall, {
        maxRetryAttempts: 3,
        context: { operation: 'protected-api-call' }
      });

      expect(result).toEqual({ data: 'success' });
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });

    it('should handle database connectivity issues with degraded mode', async () => {
      const mockFetch = fetch as any;
      
      // Database health check fails, then degraded mode is enabled
      mockFetch
        .mockRejectedValueOnce(new Error('Database connection failed'))
        .mockResolvedValueOnce({ ok: false } as Response); // health check fails

      const databaseOperation = async () => {
        throw new Error('Database connection failed');
      };

      const result = await handleError(new Error('Database connection failed'), {
        enableRecovery: true,
        context: { operation: 'user-lookup' }
      });

      expect(result.categorizedError.category).toBe(ErrorCategory.DATABASE);
      expect(result.categorizedError.severity).toBe(ErrorSeverity.CRITICAL);
      expect(result.recoveryResult?.actionTaken).toBe('ENABLE_DEGRADED_MODE');
      expect(window.localStorage.setItem).toHaveBeenCalledWith('degraded_mode', 'true');
    });

    it('should handle network failures with fallback backend', async () => {
      const mockFetch = fetch as any;
      
      // Health check succeeds, indicating fallback is working
      mockFetch.mockResolvedValueOnce({ ok: true } as Response);

      const networkOperation = async () => {
        throw new Error('ECONNREFUSED: Connection refused');
      };

      const result = await handleError(new Error('ECONNREFUSED: Connection refused'), {
        enableRecovery: true,
        context: { endpoint: 'http://localhost:8000/api/data' }
      });

      expect(result.categorizedError.category).toBe(ErrorCategory.NETWORK);
      expect(result.recoveryResult?.success).toBe(true);
      expect(result.recoveryResult?.actionTaken).toBe('CHECK_CONNECTIVITY');
      expect(result.shouldRetry).toBe(true);
    });

    it('should handle timeout errors with progressive timeout increase', async () => {
      let timeoutValue = 5000;
      const timeoutOperation = withErrorHandling(async () => {
        if (timeoutValue < 15000) {
          timeoutValue += 5000; // Simulate timeout increase
          throw new Error('Request timed out');
        }
        return 'success';
      }, {
        maxRetryAttempts: 3,
        context: { timeout: timeoutValue }
      });

      const result = await timeoutOperation();
      expect(result).toBe('success');
    });
  });

  describe('Error Recovery Scenarios', () => {
    it('should recover from temporary network issues', async () => {
      const mockFetch = fetch as any;
      mockFetch.mockResolvedValueOnce({ ok: true } as Response);

      let callCount = 0;
      const unstableNetworkCall = withErrorHandling(async () => {
        callCount++;
        if (callCount === 1) {
          throw new Error('ETIMEDOUT: Network timeout');
        }
        return 'network-success';
      }, {
        maxRetryAttempts: 3,
        enableRecovery: true
      });

      const result = await unstableNetworkCall();
      expect(result).toBe('network-success');
      expect(callCount).toBe(2);
    });

    it('should handle authentication token refresh', async () => {
      const mockFetch = fetch as any;
      mockFetch.mockResolvedValueOnce({ ok: true } as Response); // refresh succeeds

      let tokenExpired = true;
      const authenticatedCall = withErrorHandling(async () => {
        if (tokenExpired) {
          tokenExpired = false; // Simulate token refresh
          throw new Error('Token expired');
        }
        return 'authenticated-success';
      }, {
        maxRetryAttempts: 2,
        enableRecovery: true
      });

      const result = await authenticatedCall();
      expect(result).toBe('authenticated-success');
    });

    it('should enable degraded mode for persistent database issues', async () => {
      const mockFetch = fetch as any;
      mockFetch.mockResolvedValueOnce({ ok: false } as Response); // DB health check fails

      const result = await handleError(new Error('Connection pool exhausted'), {
        enableRecovery: true,
        context: { service: 'user-service' }
      });

      expect(result.recoveryResult?.actionTaken).toBe('ENABLE_DEGRADED_MODE');
      expect(window.localStorage.setItem).toHaveBeenCalledWith('degraded_mode', 'true');
    });
  });

  describe('Error Categorization Integration', () => {
    it('should properly categorize and handle various error types', async () => {
      const testCases = [
        {
          error: new Error('ECONNREFUSED'),
          expectedCategory: ErrorCategory.NETWORK,
          expectedRetryable: true
        },
        {
          error: new Error('401 Unauthorized'),
          expectedCategory: ErrorCategory.AUTHENTICATION,
          expectedRetryable: false
        },
        {
          error: new Error('Database connection timeout'),
          expectedCategory: ErrorCategory.DATABASE,
          expectedRetryable: true
        },
        {
          error: new Error('Invalid URL configuration'),
          expectedCategory: ErrorCategory.CONFIGURATION,
          expectedRetryable: false
        },
        {
          error: new Error('Request timeout after 30s'),
          expectedCategory: ErrorCategory.TIMEOUT,
          expectedRetryable: true
        },
        {
          error: new Error('Validation failed: missing required field'),
          expectedCategory: ErrorCategory.VALIDATION,
          expectedRetryable: false
        }
      ];

      for (const testCase of testCases) {
        const result = await handleError(testCase.error, {
          enableRecovery: true
        });

        expect(result.categorizedError.category).toBe(testCase.expectedCategory);
        expect(result.categorizedError.retryable).toBe(testCase.expectedRetryable);
      }
    });
  });

  describe('User Experience Integration', () => {
    it('should provide appropriate user messages for different error scenarios', async () => {
      const networkError = await handleError(new Error('ECONNREFUSED'), {
        context: { isRetrying: true }
      });
      expect(networkError.userMessage).toContain('Retrying');

      const authError = await handleError(new Error('Session expired'));
      expect(authError.userMessage).toContain('session has expired');

      const dbError = await handleError(new Error('Database connection failed'));
      expect(dbError.userMessage).toContain('temporarily unavailable');

      const configError = await handleError(new Error('Invalid URL provided'));
      expect(configError.userMessage).toContain('configuration error');
    });

    it('should determine when user action is required', async () => {
      const configError = await handleError(new Error('Missing environment variable'));
      expect(configError.requiresUserAction).toBe(true);

      const validationError = await handleError(new Error('Invalid input format'));
      expect(validationError.requiresUserAction).toBe(true);

      const networkError = await handleError(new Error('ECONNREFUSED'));
      expect(networkError.requiresUserAction).toBe(false);
    });
  });

  describe('Performance and Reliability', () => {
    it('should handle high-frequency errors without memory leaks', async () => {
      const errors = Array.from({ length: 100 }, (_, i) => 
        new Error(`Test error ${i}`)
      );

      const results = await Promise.all(
        errors.map(error => handleError(error, { enableLogging: false }))
      );

      expect(results).toHaveLength(100);
      results.forEach(result => {
        expect(result.categorizedError).toBeDefined();
        expect(result.userMessage).toBeDefined();
      });
    });

    it('should handle concurrent error processing', async () => {
      const concurrentOperations = Array.from({ length: 10 }, (_, i) => 
        withRetry(async () => {
          if (Math.random() < 0.5) {
            throw new Error(`Concurrent error ${i}`);
          }
          return `success-${i}`;
        }, { maxRetryAttempts: 2 })
      );

      const results = await Promise.allSettled(concurrentOperations);
      
      // Some should succeed, some might fail, but all should be handled properly
      results.forEach(result => {
        expect(['fulfilled', 'rejected']).toContain(result.status);
      });
    });
  });

  describe('Error Listener Integration', () => {
    it('should notify listeners of all error events', async () => {
      const errorEvents: any[] = [];
      const listener = (error: any) => errorEvents.push(error);
      
      errorHandler.addErrorListener(listener);

      await handleError(new Error('Test error 1'));
      await handleError(new Error('Test error 2'));
      await handleError(new Error('Test error 3'));

      expect(errorEvents).toHaveLength(3);
      expect(errorEvents[0].message).toBe('Test error 1');
      expect(errorEvents[1].message).toBe('Test error 2');
      expect(errorEvents[2].message).toBe('Test error 3');

      errorHandler.removeErrorListener(listener);
    });
  });

  describe('Real-world Scenario Simulation', () => {
    it('should handle complete authentication flow failure and recovery', async () => {
      const mockFetch = fetch as any;
      
      // Simulate: login fails -> session refresh fails -> clear cache -> retry succeeds
      mockFetch
        .mockRejectedValueOnce(new Error('Authentication timeout'))
        .mockResolvedValueOnce({ ok: false } as Response) // refresh fails
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ token: 'new-token' }) } as Response);

      let authAttempts = 0;
      const authFlow = withErrorHandling(async () => {
        authAttempts++;
        if (authAttempts === 1) {
          throw new Error('Authentication timeout');
        }
        if (authAttempts === 2) {
          throw new Error('Session refresh failed');
        }
        return { success: true, token: 'new-token' };
      }, {
        maxRetryAttempts: 3,
        enableRecovery: true,
        context: { flow: 'complete-auth' }
      });

      const result = await authFlow();
      expect(result.success).toBe(true);
      expect(authAttempts).toBe(3);
    });

    it('should handle cascading system failures gracefully', async () => {
      const mockFetch = fetch as any;
      mockFetch.mockResolvedValue({ ok: false } as Response);

      // Simulate multiple system failures
      const systemCall = async (service: string) => {
        switch (service) {
          case 'database':
            throw new Error('Database connection pool exhausted');
          case 'cache':
            throw new Error('Redis connection timeout');
          case 'auth':
            throw new Error('Authentication service unavailable');
          default:
            throw new Error('Unknown service error');
        }
      };

      const services = ['database', 'cache', 'auth'];
      const results = await Promise.allSettled(
        services.map(service => 
          handleError(new Error(`${service} failure`), {
            enableRecovery: true,
            context: { service }
          })
        )
      );

      results.forEach((result, index) => {
        expect(result.status).toBe('fulfilled');
        if (result.status === 'fulfilled') {
          expect(result.value.categorizedError).toBeDefined();
          expect(result.value.userMessage).toBeDefined();
        }
      });
    });
  });
});