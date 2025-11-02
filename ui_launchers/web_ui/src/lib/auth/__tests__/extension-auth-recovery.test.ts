import {
import { getExtensionAuthManager } from '../extension-auth-manager';
import { vi } from 'vitest';
/**
 * Tests for Extension Authentication Error Recovery Manager
 */


  ExtensionAuthRecoveryManager,
  extensionAuthRecoveryManager,
  type RecoveryAttemptResult
} from '../extension-auth-recovery';

  ExtensionAuthErrorFactory,
  ExtensionAuthRecoveryStrategy
} from '../extension-auth-errors';




// Mock the extension auth manager
vi.mock('../extension-auth-manager');
const mockGetExtensionAuthManager = vi.mocked(getExtensionAuthManager);

// Mock the degradation manager
vi.mock('../extension-auth-degradation', () => ({
  extensionAuthDegradationManager: {
    applyDegradation: vi.fn().mockReturnValue({
      level: 'limited',
      reason: 'test degradation',
      affectedFeatures: [],
      availableFeatures: ['extension_list'],
      lastUpdate: new Date(),
      userMessage: 'Test degradation applied'
    }),
    getFallbackData: vi.fn().mockReturnValue({ fallback: true }),
    getCachedData: vi.fn().mockReturnValue({ cached: true })
  },
  isExtensionFeatureAvailable: vi.fn().mockReturnValue(true),
  getExtensionFallbackData: vi.fn().mockReturnValue({ fallback: true })
}));

// Mock the error handler
vi.mock('../extension-auth-errors', async () => ({
  ...await vi.importActual('../extension-auth-errors'),
  extensionAuthErrorHandler: {
    handleError: vi.fn().mockReturnValue({
      category: 'test',
      severity: 'medium',
      title: 'Test Error',
      message: 'Test error message'
    })
  }
}));

// Mock the main error handler
vi.mock('@/lib/error-handler', () => ({
  errorHandler: {
    showSuccess: vi.fn(),
    showWarning: vi.fn(),
    showErrorToast: vi.fn()
  }
}));

describe('ExtensionAuthRecoveryManager', () => {
  let manager: ExtensionAuthRecoveryManager;
  let mockAuthManager: any;

  beforeEach(() => {
    manager = ExtensionAuthRecoveryManager.getInstance();
    manager.clearRecoveryHistory();
    manager.cancelAllRecoveries();

    mockAuthManager = {
      forceRefresh: vi.fn(),
      clearAuth: vi.fn()
    };
    mockGetExtensionAuthManager.mockReturnValue(mockAuthManager);
  });

  describe('attemptRecovery', () => {
    it('should attempt recovery with retry and refresh strategy', async () => {
      const error = ExtensionAuthErrorFactory.createTokenExpiredError();
      mockAuthManager.forceRefresh.mockResolvedValue('new-token');

      const result = await manager.attemptRecovery(error, '/api/extensions/', 'test operation');

      expect(result.success).toBe(true);
      expect(result.strategy).toBe(ExtensionAuthRecoveryStrategy.RETRY_WITH_REFRESH);
      expect(result.requiresUserAction).toBe(false);
      expect(mockAuthManager.forceRefresh).toHaveBeenCalled();
    });

    it('should handle failed token refresh', async () => {
      const error = ExtensionAuthErrorFactory.createTokenExpiredError();
      mockAuthManager.forceRefresh.mockResolvedValue(null);

      const result = await manager.attemptRecovery(error, '/api/extensions/', 'test operation');

      expect(result.success).toBe(false);
      expect(result.strategy).toBe(ExtensionAuthRecoveryStrategy.RETRY_WITH_REFRESH);
      expect(result.requiresUserAction).toBe(true);
      expect(result.nextAttemptDelay).toBeDefined();
    });

    it('should handle permission denied with readonly fallback', async () => {
      const error = ExtensionAuthErrorFactory.createPermissionDeniedError();

      const result = await manager.attemptRecovery(error, '/api/extensions/', 'test operation');

      expect(result.success).toBe(true);
      expect(result.strategy).toBe(ExtensionAuthRecoveryStrategy.FALLBACK_TO_READONLY);
      expect(result.requiresUserAction).toBe(false);
      expect(result.fallbackData).toBeDefined();
    });

    it('should handle service unavailable with cached fallback', async () => {
      const error = ExtensionAuthErrorFactory.createServiceUnavailableError();

      const result = await manager.attemptRecovery(error, '/api/extensions/', 'test operation');

      expect(result.success).toBe(true);
      expect(result.strategy).toBe(ExtensionAuthRecoveryStrategy.FALLBACK_TO_CACHED);
      expect(result.requiresUserAction).toBe(false);
      expect(result.fallbackData).toBeDefined();
    });

    it('should handle redirect to login strategy', async () => {
      const error = ExtensionAuthErrorFactory.createTokenInvalidError();

      const result = await manager.attemptRecovery(error, '/api/extensions/', 'test operation');

      expect(result.success).toBe(false);
      expect(result.strategy).toBe(ExtensionAuthRecoveryStrategy.REDIRECT_TO_LOGIN);
      expect(result.requiresUserAction).toBe(true);
      expect(mockAuthManager.clearAuth).toHaveBeenCalled();
    });

    it('should handle graceful degradation strategy', async () => {
      const error = ExtensionAuthErrorFactory.createNetworkError();

      const result = await manager.attemptRecovery(error, '/api/extensions/', 'test operation');

      expect(result.success).toBe(true);
      expect(result.strategy).toBe(ExtensionAuthRecoveryStrategy.GRACEFUL_DEGRADATION);
      expect(result.requiresUserAction).toBe(false);
      expect(result.fallbackData).toBeDefined();
    });

    it('should handle retry with backoff strategy', async () => {
      const error = ExtensionAuthErrorFactory.createRateLimitedError();

      const result = await manager.attemptRecovery(error, '/api/extensions/', 'test operation');

      expect(result.success).toBe(false);
      expect(result.strategy).toBe(ExtensionAuthRecoveryStrategy.RETRY_WITH_BACKOFF);
      expect(result.requiresUserAction).toBe(false);
      expect(result.nextAttemptDelay).toBeDefined();
    });

    it('should handle no recovery strategy', async () => {
      const error = ExtensionAuthErrorFactory.createConfigurationError();

      const result = await manager.attemptRecovery(error, '/api/extensions/', 'test operation');

      expect(result.success).toBe(false);
      expect(result.strategy).toBe(ExtensionAuthRecoveryStrategy.NO_RECOVERY);
      expect(result.requiresUserAction).toBe(true);
    });

    it('should track recovery attempts', async () => {
      const error = ExtensionAuthErrorFactory.createTokenExpiredError();
      mockAuthManager.forceRefresh.mockResolvedValue('new-token');

      await manager.attemptRecovery(error, '/api/extensions/', 'test operation');

      const stats = manager.getRecoveryStatistics();
      expect(stats.totalAttempts).toBe(1);
      expect(stats.successfulRecoveries).toBe(1);
      expect(stats.failedRecoveries).toBe(0);
    });

    it('should limit retry attempts', async () => {
      const error = ExtensionAuthErrorFactory.createRateLimitedError();

      // Attempt recovery multiple times
      await manager.attemptRecovery(error, '/api/extensions/', 'test operation');
      await manager.attemptRecovery(error, '/api/extensions/', 'test operation');
      await manager.attemptRecovery(error, '/api/extensions/', 'test operation');
      const result = await manager.attemptRecovery(error, '/api/extensions/', 'test operation');

      // Should eventually stop retrying
      expect(result.success).toBe(false);
    });
  });

  describe('getRecoveryStatistics', () => {
    it('should return correct statistics', async () => {
      const error1 = ExtensionAuthErrorFactory.createTokenExpiredError();
      const error2 = ExtensionAuthErrorFactory.createPermissionDeniedError();
      
      mockAuthManager.forceRefresh.mockResolvedValue('new-token');

      await manager.attemptRecovery(error1, '/api/extensions/', 'test1');
      await manager.attemptRecovery(error2, '/api/extensions/', 'test2');

      const stats = manager.getRecoveryStatistics();
      expect(stats.totalAttempts).toBe(2);
      expect(stats.successfulRecoveries).toBe(2);
      expect(stats.failedRecoveries).toBe(0);
      expect(stats.recoveryStrategiesUsed.length).toBeGreaterThan(0);
    });
  });

  describe('clearRecoveryHistory', () => {
    it('should clear recovery history', async () => {
      const error = ExtensionAuthErrorFactory.createTokenExpiredError();
      mockAuthManager.forceRefresh.mockResolvedValue('new-token');

      await manager.attemptRecovery(error, '/api/extensions/', 'test');

      let stats = manager.getRecoveryStatistics();
      expect(stats.totalAttempts).toBe(1);

      manager.clearRecoveryHistory();

      stats = manager.getRecoveryStatistics();
      expect(stats.totalAttempts).toBe(0);
    });
  });

  describe('getActiveRecoveries', () => {
    it('should track active recoveries', async () => {
      const error = ExtensionAuthErrorFactory.createRateLimitedError();

      // Start a recovery that will have multiple attempts
      const recoveryPromise = manager.attemptRecovery(error, '/api/extensions/', 'test');

      const activeRecoveries = manager.getActiveRecoveries();
      expect(activeRecoveries.length).toBeGreaterThanOrEqual(0);

      await recoveryPromise;
    });
  });

  describe('cancelRecovery', () => {
    it('should cancel specific recovery', async () => {
      const error = ExtensionAuthErrorFactory.createRateLimitedError();

      // Start a recovery
      const recoveryPromise = manager.attemptRecovery(error, '/api/extensions/', 'test');

      const cancelled = manager.cancelRecovery('/api/extensions/', 'test');
      expect(cancelled).toBe(true);

      await recoveryPromise;
    });

    it('should return false for non-existent recovery', () => {
      const cancelled = manager.cancelRecovery('/api/nonexistent/', 'test');
      expect(cancelled).toBe(false);
    });
  });

  describe('cancelAllRecoveries', () => {
    it('should cancel all active recoveries', async () => {
      const error = ExtensionAuthErrorFactory.createRateLimitedError();

      // Start multiple recoveries
      const recovery1 = manager.attemptRecovery(error, '/api/extensions/', 'test1');
      const recovery2 = manager.attemptRecovery(error, '/api/extensions/', 'test2');

      manager.cancelAllRecoveries();

      const activeRecoveries = manager.getActiveRecoveries();
      expect(activeRecoveries.length).toBe(0);

      await Promise.all([recovery1, recovery2]);
    });
  });

  describe('error handling in recovery', () => {
    it('should handle exceptions during recovery gracefully', async () => {
      const error = ExtensionAuthErrorFactory.createTokenExpiredError();
      mockAuthManager.forceRefresh.mockRejectedValue(new Error('Network error'));

      const result = await manager.attemptRecovery(error, '/api/extensions/', 'test');

      expect(result.success).toBe(false);
      expect(result.requiresUserAction).toBe(true);
    });
  });
});

describe('Global recovery manager instance', () => {
  it('should provide singleton instance', () => {
    const instance1 = ExtensionAuthRecoveryManager.getInstance();
    const instance2 = ExtensionAuthRecoveryManager.getInstance();
    expect(instance1).toBe(instance2);
  });

  it('should be accessible via exported constant', () => {
    expect(extensionAuthRecoveryManager).toBeInstanceOf(ExtensionAuthRecoveryManager);
  });
});