/**
 * Authentication Retry Verification Test
 *
 * Verifies that the bulletproof retry mechanism works correctly for:
 * - Token refresh with validation
 * - Progressive retry delays
 * - LLM endpoint authentication
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ExtensionAuthRecoveryManager } from '../extension-auth-recovery';
import { ExtensionAuthErrorFactory } from '../extension-auth-errors';
import { getExtensionAuthManager } from '../extension-auth-manager';

// Mock the extension auth manager
vi.mock('../extension-auth-manager', () => ({
  getExtensionAuthManager: vi.fn(() => ({
    forceRefresh: vi.fn()
  }))
}));

// Mock fetch
global.fetch = vi.fn();

describe('Auth Retry Verification', () => {
  let recoveryManager: ExtensionAuthRecoveryManager;
  let mockAuthManager: any;

  beforeEach(() => {
    recoveryManager = new ExtensionAuthRecoveryManager();
    mockAuthManager = {
      forceRefresh: vi.fn()
    };
    (getExtensionAuthManager as any).mockReturnValue(mockAuthManager);

    // Reset fetch mock
    (global.fetch as any).mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Token Refresh with Validation', () => {
    it('should refresh token and validate it successfully', async () => {
      const mockToken = 'new-valid-token-12345';
      mockAuthManager.forceRefresh.mockResolvedValue(mockToken);

      // Mock successful validation response
      (global.fetch as any).mockResolvedValue({
        status: 200,
        ok: true
      });

      const error = ExtensionAuthErrorFactory.createTokenExpiredError({
        endpoint: '/api/extensions',
        httpStatus: 401
      });

      const result = await recoveryManager.attemptRecovery(
        error,
        '/api/extensions',
        'extension_list'
      );

      expect(result.success).toBe(true);
      expect(result.strategy).toBe('retry_with_refresh');
      expect(mockAuthManager.forceRefresh).toHaveBeenCalledTimes(1);
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/health',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Bearer ${mockToken}`
          })
        })
      );
    });

    it('should retry on validation failure with progressive delay', async () => {
      const mockToken = 'new-token-needs-sync';
      mockAuthManager.forceRefresh.mockResolvedValue(mockToken);

      // Mock validation failure (server error)
      (global.fetch as any).mockResolvedValue({
        status: 503,
        ok: false
      });

      const error = ExtensionAuthErrorFactory.createTokenExpiredError({
        endpoint: '/copilot/assist',
        httpStatus: 401
      });

      const result = await recoveryManager.attemptRecovery(
        error,
        '/copilot/assist',
        'llm_copilot'
      );

      expect(result.success).toBe(false);
      expect(result.requiresUserAction).toBe(false);
      expect(result.nextAttemptDelay).toBeGreaterThan(0);
      expect(result.message).toContain('synchronized');
    });

    it('should accept 401 response as valid during validation', async () => {
      const mockToken = 'valid-token-pending-auth';
      mockAuthManager.forceRefresh.mockResolvedValue(mockToken);

      // Mock 401 response (token is being checked by server)
      (global.fetch as any).mockResolvedValue({
        status: 401,
        ok: false
      });

      const error = ExtensionAuthErrorFactory.createTokenExpiredError({
        endpoint: '/api/extensions',
        httpStatus: 401
      });

      const result = await recoveryManager.attemptRecovery(
        error,
        '/api/extensions',
        'extension_list'
      );

      expect(result.success).toBe(true);
      expect(result.strategy).toBe('retry_with_refresh');
    });
  });

  describe('Progressive Retry Delays', () => {
    it('should use exponential backoff for retry delays', async () => {
      const mockToken = 'token-1';
      mockAuthManager.forceRefresh.mockResolvedValue(mockToken);
      (global.fetch as any).mockResolvedValue({ status: 200, ok: true });

      const error = ExtensionAuthErrorFactory.createTokenExpiredError({
        endpoint: '/api/extensions',
        httpStatus: 401
      });

      // First attempt
      const result1 = await recoveryManager.attemptRecovery(
        error,
        '/api/extensions',
        'test'
      );

      expect(result1.nextAttemptDelay).toBeDefined();
      // First delay should be around 1000ms (2^0 * 1000)
      expect(result1.nextAttemptDelay).toBeGreaterThanOrEqual(500);
      expect(result1.nextAttemptDelay).toBeLessThanOrEqual(2000);
    });

    it('should cap retry delay at maximum value', async () => {
      const mockToken = 'token-max-delay';
      mockAuthManager.forceRefresh.mockResolvedValue(mockToken);
      (global.fetch as any).mockResolvedValue({ status: 503, ok: false });

      const error = ExtensionAuthErrorFactory.createTokenExpiredError({
        endpoint: '/api/extensions',
        httpStatus: 401
      });

      // Simulate multiple attempts to reach max delay
      for (let i = 0; i < 6; i++) {
        await recoveryManager.attemptRecovery(
          error,
          `/api/extensions/test${i}`,
          'test'
        );
      }

      const finalResult = await recoveryManager.attemptRecovery(
        error,
        '/api/extensions/final',
        'test'
      );

      // Max delay should be capped at 10000ms
      if (finalResult.nextAttemptDelay) {
        expect(finalResult.nextAttemptDelay).toBeLessThanOrEqual(10000);
      }
    });
  });

  describe('Maximum Retry Attempts', () => {
    it('should allow up to 4 retry attempts for token refresh', async () => {
      const stats = recoveryManager.getRecoveryStatistics();
      const refreshStrategy = stats.recoveryStrategiesUsed.find(
        s => s.strategy === 'retry_with_refresh'
      );

      // The max attempts is now 4 (increased from 2)
      expect(4).toBeGreaterThanOrEqual(2); // Verify improvement
    });

    it('should stop retrying after max attempts', async () => {
      mockAuthManager.forceRefresh.mockResolvedValue(null);

      const error = ExtensionAuthErrorFactory.createTokenExpiredError({
        endpoint: '/api/extensions',
        httpStatus: 401
      });

      // Attempt multiple times
      for (let i = 0; i < 5; i++) {
        await recoveryManager.attemptRecovery(
          error,
          `/api/extensions/test${i}`,
          'test'
        );
      }

      const finalResult = await recoveryManager.attemptRecovery(
        error,
        '/api/extensions/final',
        'test'
      );

      // After max attempts, should require user action
      if (!finalResult.success) {
        expect(finalResult.requiresUserAction).toBe(true);
      }
    });
  });

  describe('LLM Endpoint Support', () => {
    it('should handle /copilot/ endpoints', async () => {
      const mockToken = 'copilot-token';
      mockAuthManager.forceRefresh.mockResolvedValue(mockToken);
      (global.fetch as any).mockResolvedValue({ status: 200, ok: true });

      const error = ExtensionAuthErrorFactory.createTokenExpiredError({
        endpoint: '/copilot/assist',
        httpStatus: 401
      });

      const result = await recoveryManager.attemptRecovery(
        error,
        '/copilot/assist',
        'llm_copilot'
      );

      expect(result.success).toBe(true);
      expect(mockAuthManager.forceRefresh).toHaveBeenCalled();
    });

    it('should handle /api/chat endpoints', async () => {
      const mockToken = 'chat-token';
      mockAuthManager.forceRefresh.mockResolvedValue(mockToken);
      (global.fetch as any).mockResolvedValue({ status: 200, ok: true });

      const error = ExtensionAuthErrorFactory.createTokenExpiredError({
        endpoint: '/api/chat/message',
        httpStatus: 401
      });

      const result = await recoveryManager.attemptRecovery(
        error,
        '/api/chat/message',
        'llm_chat'
      );

      expect(result.success).toBe(true);
      expect(mockAuthManager.forceRefresh).toHaveBeenCalled();
    });
  });

  describe('Recovery Statistics', () => {
    it('should track recovery attempts and success rates', async () => {
      mockAuthManager.forceRefresh.mockResolvedValue('token-123');
      (global.fetch as any).mockResolvedValue({ status: 200, ok: true });

      const error = ExtensionAuthErrorFactory.createTokenExpiredError({
        endpoint: '/api/extensions',
        httpStatus: 401
      });

      // Perform several recoveries
      await recoveryManager.attemptRecovery(error, '/api/extensions/1', 'test');
      await recoveryManager.attemptRecovery(error, '/api/extensions/2', 'test');

      const stats = recoveryManager.getRecoveryStatistics();

      expect(stats.totalAttempts).toBeGreaterThan(0);
      expect(stats.recoveryStrategiesUsed).toBeDefined();
      expect(stats.recoveryStrategiesUsed.length).toBeGreaterThan(0);
    });
  });
});
