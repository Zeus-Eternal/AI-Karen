/**
 * Tests for Extension Authentication Error Handling
 */

import {
  ExtensionAuthErrorFactory,
  ExtensionAuthErrorCategory,
  ExtensionAuthErrorSeverity,
  ExtensionAuthRecoveryStrategy,
  ExtensionAuthErrorHandler,
  extensionAuthErrorHandler
} from '../extension-auth-errors';

describe('ExtensionAuthErrorFactory', () => {
  describe('createTokenExpiredError', () => {
    it('should create a token expired error with correct properties', () => {
      const context = { endpoint: '/api/extensions/', attempt: 1 };
      const error = ExtensionAuthErrorFactory.createTokenExpiredError(context);

      expect(error.category).toBe(ExtensionAuthErrorCategory.TOKEN_EXPIRED);
      expect(error.severity).toBe(ExtensionAuthErrorSeverity.MEDIUM);
      expect(error.code).toBe('EXT_AUTH_TOKEN_EXPIRED');
      expect(error.title).toBe('Authentication Token Expired');
      expect(error.recoveryStrategy).toBe(ExtensionAuthRecoveryStrategy.RETRY_WITH_REFRESH);
      expect(error.retryable).toBe(true);
      expect(error.userActionRequired).toBe(false);
      expect(error.context).toEqual(context);
      expect(error.resolutionSteps).toHaveLength(3);
    });
  });

  describe('createPermissionDeniedError', () => {
    it('should create a permission denied error with correct properties', () => {
      const error = ExtensionAuthErrorFactory.createPermissionDeniedError();

      expect(error.category).toBe(ExtensionAuthErrorCategory.PERMISSION_DENIED);
      expect(error.severity).toBe(ExtensionAuthErrorSeverity.HIGH);
      expect(error.code).toBe('EXT_AUTH_PERMISSION_DENIED');
      expect(error.recoveryStrategy).toBe(ExtensionAuthRecoveryStrategy.FALLBACK_TO_READONLY);
      expect(error.retryable).toBe(false);
      expect(error.userActionRequired).toBe(true);
    });
  });

  describe('createFromHttpStatus', () => {
    it('should create appropriate error for 401 status', () => {
      const error = ExtensionAuthErrorFactory.createFromHttpStatus(401);
      expect(error.category).toBe(ExtensionAuthErrorCategory.TOKEN_EXPIRED);
    });

    it('should create appropriate error for 403 status', () => {
      const error = ExtensionAuthErrorFactory.createFromHttpStatus(403);
      expect(error.category).toBe(ExtensionAuthErrorCategory.PERMISSION_DENIED);
    });

    it('should create appropriate error for 503 status', () => {
      const error = ExtensionAuthErrorFactory.createFromHttpStatus(503);
      expect(error.category).toBe(ExtensionAuthErrorCategory.SERVICE_UNAVAILABLE);
    });

    it('should create network error for unknown status', () => {
      const error = ExtensionAuthErrorFactory.createFromHttpStatus(500);
      expect(error.category).toBe(ExtensionAuthErrorCategory.NETWORK_ERROR);
    });
  });

  describe('createFromException', () => {
    it('should create token expired error for token expired exception', () => {
      const exception = new Error('Token expired');
      const error = ExtensionAuthErrorFactory.createFromException(exception);
      expect(error.category).toBe(ExtensionAuthErrorCategory.TOKEN_EXPIRED);
    });

    it('should create network error for network exception', () => {
      const exception = new Error('Network error occurred');
      const error = ExtensionAuthErrorFactory.createFromException(exception);
      expect(error.category).toBe(ExtensionAuthErrorCategory.NETWORK_ERROR);
    });

    it('should create permission denied error for permission exception', () => {
      const exception = new Error('Permission denied');
      const error = ExtensionAuthErrorFactory.createFromException(exception);
      expect(error.category).toBe(ExtensionAuthErrorCategory.PERMISSION_DENIED);
    });
  });
});

describe('ExtensionAuthErrorHandler', () => {
  let handler: ExtensionAuthErrorHandler;

  beforeEach(() => {
    handler = ExtensionAuthErrorHandler.getInstance();
    handler.clearErrorHistory();
  });

  describe('handleError', () => {
    it('should handle error and return ErrorInfo', () => {
      const authError = ExtensionAuthErrorFactory.createTokenExpiredError();
      const errorInfo = handler.handleError(authError);

      expect(errorInfo.category).toBe(authError.category);
      expect(errorInfo.severity).toBe(authError.severity);
      expect(errorInfo.title).toBe(authError.title);
      expect(errorInfo.message).toBe(authError.message);
      expect(errorInfo.retry_possible).toBe(authError.retryable);
      expect(errorInfo.user_action_required).toBe(authError.userActionRequired);
    });

    it('should add error to history', () => {
      const authError = ExtensionAuthErrorFactory.createTokenExpiredError();
      handler.handleError(authError);

      const history = handler.getErrorHistory();
      expect(history).toHaveLength(1);
      expect(history[0]).toEqual(authError);
    });
  });

  describe('getRecoveryStrategy', () => {
    it('should return correct recovery strategy', () => {
      const authError = ExtensionAuthErrorFactory.createTokenExpiredError();
      const strategy = handler.getRecoveryStrategy(authError);
      expect(strategy).toBe(ExtensionAuthRecoveryStrategy.RETRY_WITH_REFRESH);
    });
  });

  describe('isRetryable', () => {
    it('should return true for retryable errors', () => {
      const authError = ExtensionAuthErrorFactory.createTokenExpiredError();
      expect(handler.isRetryable(authError)).toBe(true);
    });

    it('should return false for non-retryable errors', () => {
      const authError = ExtensionAuthErrorFactory.createPermissionDeniedError();
      expect(handler.isRetryable(authError)).toBe(false);
    });
  });

  describe('requiresUserAction', () => {
    it('should return false for automatic recovery errors', () => {
      const authError = ExtensionAuthErrorFactory.createTokenExpiredError();
      expect(handler.requiresUserAction(authError)).toBe(false);
    });

    it('should return true for errors requiring user action', () => {
      const authError = ExtensionAuthErrorFactory.createPermissionDeniedError();
      expect(handler.requiresUserAction(authError)).toBe(true);
    });
  });

  describe('getErrorStatistics', () => {
    it('should return correct statistics', () => {
      const error1 = ExtensionAuthErrorFactory.createTokenExpiredError();
      const error2 = ExtensionAuthErrorFactory.createTokenExpiredError();
      const error3 = ExtensionAuthErrorFactory.createPermissionDeniedError();

      handler.handleError(error1);
      handler.handleError(error2);
      handler.handleError(error3);

      const stats = handler.getErrorStatistics();
      expect(stats[ExtensionAuthErrorCategory.TOKEN_EXPIRED]).toBe(2);
      expect(stats[ExtensionAuthErrorCategory.PERMISSION_DENIED]).toBe(1);
    });
  });

  describe('detectSystemicIssue', () => {
    it('should detect systemic issues with multiple recent errors', () => {
      // Add 5 errors in quick succession
      for (let i = 0; i < 5; i++) {
        const error = ExtensionAuthErrorFactory.createTokenExpiredError();
        handler.handleError(error);
      }

      expect(handler.detectSystemicIssue()).toBe(true);
    });

    it('should not detect systemic issues with few errors', () => {
      const error = ExtensionAuthErrorFactory.createTokenExpiredError();
      handler.handleError(error);

      expect(handler.detectSystemicIssue()).toBe(false);
    });
  });

  describe('clearErrorHistory', () => {
    it('should clear error history', () => {
      const error = ExtensionAuthErrorFactory.createTokenExpiredError();
      handler.handleError(error);

      expect(handler.getErrorHistory()).toHaveLength(1);
      
      handler.clearErrorHistory();
      expect(handler.getErrorHistory()).toHaveLength(0);
    });
  });
});

describe('Global error handler instance', () => {
  it('should provide singleton instance', () => {
    const instance1 = ExtensionAuthErrorHandler.getInstance();
    const instance2 = ExtensionAuthErrorHandler.getInstance();
    expect(instance1).toBe(instance2);
  });

  it('should be accessible via exported constant', () => {
    expect(extensionAuthErrorHandler).toBeInstanceOf(ExtensionAuthErrorHandler);
  });
});