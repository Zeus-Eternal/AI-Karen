/**
 * Tests for error recovery system
 * Requirements: 1.3, 2.3, 3.3, 4.3
 */

import { vi } from 'vitest';
import { ErrorRecoveryManager } from '../error-recovery';
import { ErrorCategorizer } from '../error-categorizer';
import { ErrorCategory, ErrorSeverity } from '../error-categories';

// Mock fetch for testing
global.fetch = vi.fn();

describe('ErrorRecoveryManager', () => {
  let recoveryManager: ErrorRecoveryManager;
  let categorizer: ErrorCategorizer;

  beforeEach(() => {
    recoveryManager = ErrorRecoveryManager.getInstance();
    categorizer = ErrorCategorizer.getInstance();
    vi.clearAllMocks();
    
    // Clear localStorage for each test
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    });
  });

  describe('Network Error Recovery', () => {
    it('should attempt network connectivity check', async () => {
      const mockFetch = fetch as any;
      mockFetch.mockResolvedValueOnce({
        ok: true,
      } as Response);

      const error = categorizer.categorizeError(new Error('ECONNREFUSED'));
      const result = await recoveryManager.attemptRecovery(error);

      expect(result.success).toBe(true);
      expect(result.actionTaken).toBe('CHECK_CONNECTIVITY');
      expect(result.shouldRetry).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith('/api/health', {
        method: 'HEAD',
        signal: expect.any(AbortSignal)
      });
    });

    it('should try fallback backend when connectivity check fails', async () => {
      const mockFetch = fetch as any;
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const error = categorizer.categorizeError(new Error('ECONNREFUSED'));
      const result = await recoveryManager.attemptRecovery(error);

      expect(result.success).toBe(true);
      expect(result.actionTaken).toBe('USE_FALLBACK_BACKEND');
    });

    it('should try fallback backend when connectivity check fails', async () => {
      const mockFetch = fetch as any;
      mockFetch.mockRejectedValue(new Error('Network error'));

      const error = categorizer.categorizeError(new Error('ECONNREFUSED'));
      const result = await recoveryManager.attemptRecovery(error);

      expect(result.success).toBe(true);
      expect(result.actionTaken).toBe('USE_FALLBACK_BACKEND');
    });
  });

  describe('Authentication Error Recovery', () => {
    it('should attempt session refresh for expired sessions', async () => {
      const mockFetch = fetch as any;
      mockFetch.mockResolvedValueOnce({
        ok: true,
      } as Response);

      const error = categorizer.categorizeError(new Error('Session expired'));
      const result = await recoveryManager.attemptRecovery(error);

      expect(result.success).toBe(true);
      expect(result.actionTaken).toBe('REFRESH_SESSION');
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include'
      });
    });

    it('should clear auth cache when session refresh fails', async () => {
      const mockFetch = fetch as any;
      mockFetch.mockResolvedValueOnce({
        ok: false,
      } as Response);

      const error = categorizer.categorizeError(new Error('Session expired'));
      const result = await recoveryManager.attemptRecovery(error);

      expect(result.success).toBe(true);
      expect(result.actionTaken).toBe('CLEAR_AUTH_CACHE');
      expect(window.localStorage.removeItem).toHaveBeenCalledWith('auth_token');
    });
  });

  describe('Database Error Recovery', () => {
    it('should retry database connection', async () => {
      const mockFetch = fetch as any;
      mockFetch.mockResolvedValueOnce({
        ok: true,
      } as Response);

      const error = categorizer.categorizeError(new Error('Database connection failed'));
      const result = await recoveryManager.attemptRecovery(error);

      expect(result.success).toBe(true);
      expect(result.actionTaken).toBe('RETRY_CONNECTION');
      expect(mockFetch).toHaveBeenCalledWith('/api/health/database', {
        method: 'GET',
        signal: expect.any(AbortSignal)
      });
    });

    it('should enable degraded mode when database retry fails', async () => {
      const mockFetch = fetch as any;
      mockFetch.mockResolvedValueOnce({
        ok: false,
      } as Response);

      const error = categorizer.categorizeError(new Error('Database connection failed'));
      const result = await recoveryManager.attemptRecovery(error);

      expect(result.success).toBe(true);
      expect(result.actionTaken).toBe('ENABLE_DEGRADED_MODE');
      expect(window.localStorage.setItem).toHaveBeenCalledWith('degraded_mode', 'true');
    });
  });

  describe('Timeout Error Recovery', () => {
    it('should increase timeout for next attempt', async () => {
      const error = categorizer.categorizeError(new Error('Request timed out'));
      const result = await recoveryManager.attemptRecovery(error);

      expect(result.success).toBe(true);
      expect(result.actionTaken).toBe('INCREASE_TIMEOUT');
    });

    it('should attempt to split request when timeout increase fails', async () => {
      // Mock the increase timeout to fail
      const originalConsoleLog = console.log;
      console.log = vi.fn();

      const error = categorizer.categorizeError(new Error('Request timed out'));
      
      // Force the first action to fail by mocking it
      vi.spyOn(recoveryManager as any, 'increaseTimeout').mockResolvedValueOnce(false);
      
      const result = await recoveryManager.attemptRecovery(error);

      expect(result.success).toBe(true);
      expect(result.actionTaken).toBe('SPLIT_REQUEST');
      
      console.log = originalConsoleLog;
    });
  });

  describe('Recovery Attempt Tracking', () => {
    it('should track recovery attempts', async () => {
      const error = categorizer.categorizeError(new Error('ECONNREFUSED'));
      
      expect(recoveryManager.getRecoveryAttemptCount(error)).toBe(0);
      
      await recoveryManager.attemptRecovery(error);
      expect(recoveryManager.getRecoveryAttemptCount(error)).toBe(0); // Reset on success
    });

    it('should respect cooldown period', async () => {
      const error = categorizer.categorizeError(new Error('ECONNREFUSED'));
      
      // First attempt should succeed
      const result1 = await recoveryManager.attemptRecovery(error);
      expect(result1.success).toBe(true);
      
      // Immediate second attempt should be in cooldown (but first was successful, so attempts were reset)
      // Let's force a failure to test cooldown
      const mockFetch = fetch as any;
      mockFetch.mockRejectedValue(new Error('All actions failed'));
      
      const failedError = categorizer.categorizeError(new Error('ECONNREFUSED'));
      await recoveryManager.attemptRecovery(failedError);
      
      // Immediate retry should be in cooldown
      const result2 = await recoveryManager.attemptRecovery(failedError);
      expect(result2.actionTaken).toBe('COOLDOWN_WAIT');
      expect(result2.shouldRetry).toBe(true);
      expect(result2.nextRetryDelay).toBeGreaterThan(0);
    });

    it('should respect maximum attempts', async () => {
      const mockFetch = fetch as any;
      mockFetch.mockRejectedValue(new Error('All actions failed'));
      
      const error = categorizer.categorizeError(new Error('ECONNREFUSED'));
      
      // Exhaust all attempts
      for (let i = 0; i < 3; i++) {
        await recoveryManager.attemptRecovery(error);
        // Wait for cooldown
        await new Promise(resolve => setTimeout(resolve, 5100));
      }
      
      // Next attempt should be rejected
      const result = await recoveryManager.attemptRecovery(error);
      expect(result.actionTaken).toBe('MAX_ATTEMPTS_REACHED');
      expect(result.shouldRetry).toBe(false);
    });

    it('should reset recovery attempts on successful recovery', async () => {
      const error = categorizer.categorizeError(new Error('ECONNREFUSED'));
      
      const result = await recoveryManager.attemptRecovery(error);
      expect(result.success).toBe(true);
      
      // Attempts should be reset
      expect(recoveryManager.getRecoveryAttemptCount(error)).toBe(0);
    });
  });

  describe('Recovery Strategy Selection', () => {
    it('should use appropriate strategy for each error category', async () => {
      const networkError = categorizer.categorizeError(new Error('ECONNREFUSED'));
      const authError = categorizer.categorizeError(new Error('Session expired'));
      const dbError = categorizer.categorizeError(new Error('Database connection failed'));
      const timeoutError = categorizer.categorizeError(new Error('Request timed out'));
      const unknownError = categorizer.categorizeError(new Error('Unknown error'));

      // Each should use different recovery strategies
      const networkResult = await recoveryManager.attemptRecovery(networkError);
      const authResult = await recoveryManager.attemptRecovery(authError);
      const dbResult = await recoveryManager.attemptRecovery(dbError);
      const timeoutResult = await recoveryManager.attemptRecovery(timeoutError);
      const unknownResult = await recoveryManager.attemptRecovery(unknownError);

      expect(networkResult.actionTaken).toBe('CHECK_CONNECTIVITY');
      expect(authResult.actionTaken).toBe('REFRESH_SESSION');
      expect(dbResult.actionTaken).toBe('RETRY_CONNECTION');
      expect(timeoutResult.actionTaken).toBe('INCREASE_TIMEOUT');
      expect(unknownResult.actionTaken).toBe('GENERIC_RETRY');
    });
  });

  describe('Manual Recovery Control', () => {
    it('should allow manual reset of recovery attempts', () => {
      const error = categorizer.categorizeError(new Error('ECONNREFUSED'));
      
      // Simulate some attempts
      recoveryManager['recoveryAttempts'].set('NETWORK_UNKNOWN_ERROR_CODE', 2);
      
      recoveryManager.resetRecoveryAttempts(error);
      expect(recoveryManager.getRecoveryAttemptCount(error)).toBe(0);
    });
  });
});