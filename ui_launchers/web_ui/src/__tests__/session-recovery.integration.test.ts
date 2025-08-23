/**
 * Integration tests for session recovery functionality
 * 
 * Tests session recovery logic, automatic retry mechanisms,
 * and graceful fallback handling.
 * 
 * Requirements: 1.4, 5.2, 5.3, 5.4, 5.5
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import {
  attemptSessionRecovery,
  recoverFrom401Error,
  silentSessionRecovery,
  shouldAttemptRecovery,
  getRecoveryFailureMessage,
  shouldRetryAfterRecovery,
} from '@/lib/auth/session-recovery';

// Mock the session module
vi.mock('@/lib/auth/session', () => ({
  bootSession: vi.fn(),
  refreshToken: vi.fn(),
  clearSession: vi.fn(),
  isAuthenticated: vi.fn(),
}));

describe('Session Recovery Integration Tests', () => {
  let mockBootSession: any;
  let mockRefreshToken: any;
  let mockClearSession: any;
  let mockIsAuthenticated: any;

  beforeEach(async () => {
    const sessionModule = await import('@/lib/auth/session');
    mockBootSession = sessionModule.bootSession as any;
    mockRefreshToken = sessionModule.refreshToken as any;
    mockClearSession = sessionModule.clearSession as any;
    mockIsAuthenticated = sessionModule.isAuthenticated as any;

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('attemptSessionRecovery', () => {
    it('should successfully recover session when bootSession works', async () => {
      mockBootSession.mockResolvedValue(undefined);
      mockIsAuthenticated.mockReturnValue(true);

      const result = await attemptSessionRecovery();

      expect(result).toEqual({
        success: true,
        shouldShowLogin: false,
      });
      expect(mockBootSession).toHaveBeenCalled();
      expect(mockIsAuthenticated).toHaveBeenCalled();
    });

    it('should fail with no_refresh_token when bootSession succeeds but no session established', async () => {
      mockBootSession.mockResolvedValue(undefined);
      mockIsAuthenticated.mockReturnValue(false);

      const result = await attemptSessionRecovery();

      expect(result).toEqual({
        success: false,
        reason: 'no_refresh_token',
        shouldShowLogin: true,
        message: 'No valid session found. Please log in again.',
      });
    });

    it('should handle network errors gracefully', async () => {
      mockBootSession.mockRejectedValue(new Error('Network error: fetch failed'));

      const result = await attemptSessionRecovery();

      expect(result).toEqual({
        success: false,
        reason: 'network_error',
        shouldShowLogin: false,
        message: 'Network error occurred. Please check your connection and try again.',
      });
    });

    it('should handle 401 unauthorized errors', async () => {
      mockBootSession.mockRejectedValue(new Error('401 Unauthorized'));

      const result = await attemptSessionRecovery();

      expect(result).toEqual({
        success: false,
        reason: 'refresh_failed',
        shouldShowLogin: true,
        message: 'Your session has expired. Please log in again.',
      });
    });

    it('should handle generic errors as invalid session', async () => {
      mockBootSession.mockRejectedValue(new Error('Something went wrong'));

      const result = await attemptSessionRecovery();

      expect(result).toEqual({
        success: false,
        reason: 'invalid_session',
        shouldShowLogin: true,
        message: 'Session could not be restored. Please log in again.',
      });
    });
  });

  describe('recoverFrom401Error', () => {
    it('should successfully recover from 401 error', async () => {
      mockRefreshToken.mockResolvedValue(undefined);
      mockIsAuthenticated.mockReturnValue(true);

      const result = await recoverFrom401Error();

      expect(result).toEqual({
        success: true,
        shouldShowLogin: false,
      });
      expect(mockRefreshToken).toHaveBeenCalled();
      expect(mockIsAuthenticated).toHaveBeenCalled();
    });

    it('should clear session and fail when refresh succeeds but no valid session', async () => {
      mockRefreshToken.mockResolvedValue(undefined);
      mockIsAuthenticated.mockReturnValue(false);

      const result = await recoverFrom401Error();

      expect(result).toEqual({
        success: false,
        reason: 'refresh_failed',
        shouldShowLogin: true,
        message: 'Session expired. Please log in again.',
      });
      expect(mockClearSession).toHaveBeenCalled();
    });

    it('should handle network errors during refresh', async () => {
      mockRefreshToken.mockRejectedValue(new Error('Network timeout'));

      const result = await recoverFrom401Error();

      expect(result).toEqual({
        success: false,
        reason: 'network_error',
        shouldShowLogin: false,
        message: 'Network error during session refresh. Please try again.',
      });
      expect(mockClearSession).toHaveBeenCalled();
    });

    it('should handle refresh token failure', async () => {
      mockRefreshToken.mockRejectedValue(new Error('Refresh token expired'));

      const result = await recoverFrom401Error();

      expect(result).toEqual({
        success: false,
        reason: 'refresh_failed',
        shouldShowLogin: true,
        message: 'Session expired. Please log in again.',
      });
      expect(mockClearSession).toHaveBeenCalled();
    });
  });

  describe('silentSessionRecovery', () => {
    it('should return true for successful recovery', async () => {
      mockBootSession.mockResolvedValue(undefined);
      mockIsAuthenticated.mockReturnValue(true);

      const result = await silentSessionRecovery();

      expect(result).toBe(true);
    });

    it('should return false for failed recovery without throwing', async () => {
      mockBootSession.mockRejectedValue(new Error('Recovery failed'));

      const result = await silentSessionRecovery();

      expect(result).toBe(false);
    });

    it('should never throw errors', async () => {
      mockBootSession.mockRejectedValue(new Error('Catastrophic failure'));

      await expect(silentSessionRecovery()).resolves.toBe(false);
    });
  });

  describe('shouldAttemptRecovery', () => {
    it('should return false when already authenticated', () => {
      mockIsAuthenticated.mockReturnValue(true);

      const result = shouldAttemptRecovery();

      expect(result).toBe(false);
    });

    it('should return true when not authenticated', () => {
      mockIsAuthenticated.mockReturnValue(false);

      const result = shouldAttemptRecovery();

      expect(result).toBe(true);
    });
  });

  describe('getRecoveryFailureMessage', () => {
    it('should return appropriate message for no_refresh_token', () => {
      const message = getRecoveryFailureMessage('no_refresh_token');
      expect(message).toBe('Please log in to continue.');
    });

    it('should return appropriate message for refresh_failed', () => {
      const message = getRecoveryFailureMessage('refresh_failed');
      expect(message).toBe('Your session has expired. Please log in again.');
    });

    it('should return appropriate message for network_error', () => {
      const message = getRecoveryFailureMessage('network_error');
      expect(message).toBe('Network error occurred. Please check your connection and try again.');
    });

    it('should return appropriate message for invalid_session', () => {
      const message = getRecoveryFailureMessage('invalid_session');
      expect(message).toBe('Session could not be restored. Please log in again.');
    });

    it('should return default message for undefined reason', () => {
      const message = getRecoveryFailureMessage(undefined);
      expect(message).toBe('Authentication required. Please log in.');
    });
  });

  describe('shouldRetryAfterRecovery', () => {
    it('should return true for successful recovery (undefined reason)', () => {
      const result = shouldRetryAfterRecovery(undefined);
      expect(result).toBe(true);
    });

    it('should return true for network errors', () => {
      const result = shouldRetryAfterRecovery('network_error');
      expect(result).toBe(true);
    });

    it('should return false for refresh failures', () => {
      const result = shouldRetryAfterRecovery('refresh_failed');
      expect(result).toBe(false);
    });

    it('should return false for no refresh token', () => {
      const result = shouldRetryAfterRecovery('no_refresh_token');
      expect(result).toBe(false);
    });

    it('should return false for invalid session', () => {
      const result = shouldRetryAfterRecovery('invalid_session');
      expect(result).toBe(false);
    });
  });

  describe('Error Classification', () => {
    it('should correctly identify network errors', async () => {
      const networkErrors = [
        'Network error: fetch failed',
        'Failed to fetch',
        'Network timeout',
        'Connection refused',
      ];

      for (const errorMessage of networkErrors) {
        mockBootSession.mockRejectedValue(new Error(errorMessage));
        const result = await attemptSessionRecovery();
        expect(result.reason).toBe('network_error');
      }
    });

    it('should correctly identify authentication errors', async () => {
      const authErrors = [
        '401 Unauthorized',
        'Unauthorized access',
        'Authentication failed',
      ];

      for (const errorMessage of authErrors) {
        mockBootSession.mockRejectedValue(new Error(errorMessage));
        const result = await attemptSessionRecovery();
        expect(result.reason).toBe('refresh_failed');
      }
    });

    it('should treat unknown errors as invalid session', async () => {
      const unknownErrors = [
        'Something went wrong',
        'Internal server error',
        'Unexpected error',
      ];

      for (const errorMessage of unknownErrors) {
        mockBootSession.mockRejectedValue(new Error(errorMessage));
        const result = await attemptSessionRecovery();
        expect(result.reason).toBe('invalid_session');
      }
    });
  });

  describe('Recovery Flow Integration', () => {
    it('should handle complete recovery flow from 401 to success', async () => {
      // Simulate initial 401 error recovery
      mockRefreshToken.mockResolvedValue(undefined);
      mockIsAuthenticated.mockReturnValue(true);

      const result = await recoverFrom401Error();

      expect(result.success).toBe(true);
      expect(result.shouldShowLogin).toBe(false);
      expect(mockRefreshToken).toHaveBeenCalled();
      expect(mockClearSession).not.toHaveBeenCalled();
    });

    it('should handle recovery failure and cleanup', async () => {
      // Simulate refresh failure
      mockRefreshToken.mockRejectedValue(new Error('Token expired'));

      const result = await recoverFrom401Error();

      expect(result.success).toBe(false);
      expect(result.shouldShowLogin).toBe(true);
      expect(mockClearSession).toHaveBeenCalled();
    });

    it('should handle session boot recovery flow', async () => {
      // Simulate successful session boot
      mockBootSession.mockResolvedValue(undefined);
      mockIsAuthenticated.mockReturnValue(true);

      const result = await attemptSessionRecovery();

      expect(result.success).toBe(true);
      expect(result.shouldShowLogin).toBe(false);
      expect(mockBootSession).toHaveBeenCalled();
    });

    it('should handle mixed recovery scenarios', async () => {
      // Test sequence: boot fails, then 401 recovery succeeds
      mockBootSession.mockRejectedValue(new Error('No refresh token'));
      
      const bootResult = await attemptSessionRecovery();
      expect(bootResult.success).toBe(false);
      expect(bootResult.reason).toBe('invalid_session');

      // Now test 401 recovery
      mockRefreshToken.mockResolvedValue(undefined);
      mockIsAuthenticated.mockReturnValue(true);
      
      const recoveryResult = await recoverFrom401Error();
      expect(recoveryResult.success).toBe(true);
    });
  });
});