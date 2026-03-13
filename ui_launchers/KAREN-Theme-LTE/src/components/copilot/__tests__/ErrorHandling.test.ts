import { describe, test, beforeEach, expect, vi } from 'vitest';
import ErrorHandlingService from '../services/ErrorHandlingService';
import UserErrorMessageService from '../services/UserErrorMessageService';
import RetryService from '../services/RetryService';
import ErrorLoggingService from '../services/ErrorLoggingService';
import ErrorNotificationService from '../services/ErrorNotificationService';
import { ErrorCategory, ErrorSeverity } from '../services/ErrorHandlingService';
import { LogLevel, LogCategory } from '../services/ErrorLoggingService';
import { NotificationType, NotificationPosition, NotificationTheme } from '../services/ErrorNotificationService';

/**
 * Test suite for Error Handling and Recovery components
 */
describe('Error Handling and Recovery', () => {
  let errorHandlingService: ErrorHandlingService;
  let userErrorMessageService: UserErrorMessageService;
  let retryService: RetryService;
  let errorLoggingService: ErrorLoggingService;
  let errorNotificationService: ErrorNotificationService;

  beforeEach(() => {
    // Reset singleton instances by clearing their internal state
    errorHandlingService = ErrorHandlingService.getInstance();
    errorHandlingService.clearAllErrors();
    
    userErrorMessageService = UserErrorMessageService.getInstance();
    (userErrorMessageService as any).clearCustomMessages = () => {};
    
    retryService = RetryService.getInstance();
    
    errorLoggingService = ErrorLoggingService.getInstance();
    errorLoggingService.clearLogs();
    
    errorNotificationService = ErrorNotificationService.getInstance();
    errorNotificationService.removeAllNotifications();
  });

  describe('ErrorHandlingService', () => {
    test('should handle errors with proper categorization', () => {
      const error = new Error('Test error');
      const context = { component: 'TestComponent', function: 'testFunction' };
      
      const errorInfo = errorHandlingService.handleError(
        error,
        ErrorCategory.NETWORK,
        ErrorSeverity.HIGH,
        context
      );
      
      expect(errorInfo).toBeDefined();
      expect((errorInfo as any).category).toBe(ErrorCategory.NETWORK);
      expect((errorInfo as any).severity).toBe(ErrorSeverity.HIGH);
      expect((errorInfo as any).context).toEqual(context);
      expect((errorInfo as any).resolved).toBe(false);
    });

    test('should resolve errors correctly', () => {
      const error = new Error('Test error');
      const errorInfo = errorHandlingService.handleError(
        error,
        ErrorCategory.UNKNOWN,
        ErrorSeverity.MEDIUM
      );
      
      expect((errorInfo as any).resolved).toBe(false);
      
      const resolvedError = errorHandlingService.resolveError((errorInfo as any).id);
      expect(resolvedError).toBeDefined();
      expect((resolvedError as any)?.resolved).toBe(true);
    });

    test('should clear all errors', () => {
      // Add multiple errors
      errorHandlingService.handleError(new Error('Error 1'), ErrorCategory.NETWORK);
      errorHandlingService.handleError(new Error('Error 2'), ErrorCategory.VALIDATION);
      
      let errors = errorHandlingService.getAllErrors();
      expect(errors.length).toBe(2);
      
      errorHandlingService.clearAllErrors();
      
      errors = errorHandlingService.getAllErrors();
      expect(errors.length).toBe(0);
    });

    test('should get error statistics correctly', () => {
      // Add errors with different categories and severities
      errorHandlingService.handleError(new Error('Network error'), ErrorCategory.NETWORK, ErrorSeverity.HIGH);
      errorHandlingService.handleError(new Error('Validation error'), ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM);
      errorHandlingService.handleError(new Error('Another network error'), ErrorCategory.NETWORK, ErrorSeverity.LOW);
      
      const stats = errorHandlingService.getErrorStatistics();
      
      expect(stats.totalErrors).toBe(3);
      expect(stats.resolvedErrors).toBe(0);
      expect(stats.unresolvedErrors).toBe(3);
      expect(stats.errorsByCategory[ErrorCategory.NETWORK]).toBe(2);
      expect(stats.errorsByCategory[ErrorCategory.VALIDATION]).toBe(1);
    });
  });

  describe('UserErrorMessageService', () => {
    test('should get user-friendly error message', () => {
      const errorMessage = (userErrorMessageService as any).getUserErrorMessage(
        'NETWORK_ERROR',
        ErrorSeverity.HIGH
      );
      
      expect(errorMessage).toBeDefined();
      expect(errorMessage.title).toBeDefined();
      expect(errorMessage.message).toBeDefined();
      expect(errorMessage.suggestedActions).toBeDefined();
      expect(Array.isArray(errorMessage.suggestedActions)).toBe(true);
    });

    test('should get contextual error message', () => {
      const context = { component: 'TestComponent', action: 'saveData' };
      const errorMessage = (userErrorMessageService as any).getContextualErrorMessage(
        'VALIDATION_ERROR',
        ErrorSeverity.MEDIUM,
        context
      );
      
      expect(errorMessage).toBeDefined();
      expect(errorMessage.message).toContain('TestComponent');
      expect(errorMessage.message).toContain('saveData');
    });

    test('should register custom error message', () => {
      const customMessage = {
        title: 'Custom Error',
        message: 'This is a custom error message',
        suggestedActions: ['Try again', 'Contact support']
      };
      
      (userErrorMessageService as any).registerCustomErrorMessage('CUSTOM_ERROR', customMessage);
      
      const retrievedMessage = (userErrorMessageService as any).getUserErrorMessage('CUSTOM_ERROR');
      expect(retrievedMessage.title).toBe(customMessage.title);
      expect(retrievedMessage.message).toBe(customMessage.message);
      expect(retrievedMessage.suggestedActions).toEqual(customMessage.suggestedActions);
    });
  });

  describe('RetryService', () => {
    test('should retry function with exponential backoff', async () => {
      let attemptCount = 0;
      const mockFn = vi.fn().mockImplementation(() => {
        attemptCount++;
        if (attemptCount < 3) {
          throw new Error('Network error');
        }
        return 'success';
      });
      
      const result = await (retryService as any).retry(mockFn, {
        maxAttempts: 3,
        baseDelay: 10,
        backoffFactor: 2
      });
      
      expect(result).toBe('success');
      expect(mockFn.mock.calls.length).toBe(3);
    });

    test('should fail after max attempts', async () => {
      const mockFn = vi.fn().mockImplementation(() => {
        throw new Error('Persistent error');
      });
      
      let errorThrown = false;
      try {
        await (retryService as any).retry(mockFn, {
          maxAttempts: 2,
          baseDelay: 10
        });
      } catch (error) {
        errorThrown = true;
      }
      
      expect(errorThrown).toBe(true);
      expect(mockFn.mock.calls.length).toBe(2);
    });

    test('should retry only on network errors', async () => {
      const mockFn = vi.fn().mockImplementation(() => {
        throw new Error('Validation error');
      });
      
      let errorThrown = false;
      try {
        await (retryService as any).retry(mockFn, {
          maxAttempts: 3,
          retryCondition: (error: any) => error.message.includes('Network')
        });
      } catch (error) {
        errorThrown = true;
      }
      
      expect(errorThrown).toBe(true);
      expect(mockFn.mock.calls.length).toBe(1);
    });
  });

  describe('ErrorLoggingService', () => {
    test('should log error messages', () => {
      const error = new Error('Test error');
      const context = { component: 'TestComponent' };
      
      (errorLoggingService as any).logError(error, ErrorCategory.NETWORK, ErrorSeverity.HIGH, context);
      
      const logs = errorLoggingService.getLogs();
      const errorLog = logs.find(log => log.level === LogLevel.ERROR);
      
      expect(errorLog).toBeDefined();
      expect(errorLog?.message).toContain('Test error');
      expect(errorLog?.category).toBe('ERROR');
      expect(errorLog?.component).toBe('TestComponent');
    });

    test('should log performance metrics', () => {
      const metrics = {
        operation: 'testOperation',
        duration: 150,
        success: true
      };
      
      (errorLoggingService as any).logPerformance(metrics);
      
      const logs = errorLoggingService.getLogs();
      const perfLog = logs.find(log => log.level === LogLevel.INFO && log.category === LogCategory.PERFORMANCE);
      
      expect(perfLog).toBeDefined();
      expect(perfLog?.message).toContain('testOperation');
      expect(perfLog?.data).toEqual(metrics);
    });

    test('should track error metrics', () => {
      // Log multiple errors
      (errorLoggingService as any).logError(new Error('Error 1'), ErrorCategory.NETWORK, ErrorSeverity.HIGH);
      (errorLoggingService as any).logError(new Error('Error 2'), ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM);
      
      const metrics = errorLoggingService.getErrorMetrics();
      
      expect(metrics.totalErrors).toBe(2);
      expect(metrics.errorsByCategory[ErrorCategory.NETWORK]).toBe(1);
      expect(metrics.errorsByCategory[ErrorCategory.VALIDATION]).toBe(1);
    });

    test('should track performance metrics', () => {
      // Log multiple performance metrics
      (errorLoggingService as any).logPerformance({ operation: 'op1', duration: 100, success: true });
      (errorLoggingService as any).logPerformance({ operation: 'op2', duration: 200, success: true });
      (errorLoggingService as any).logPerformance({ operation: 'op3', duration: 50, success: false });
      
      const metrics = errorLoggingService.getPerformanceMetrics();
      
      expect(metrics.requestCount).toBe(3);
      expect(metrics.successRate).toBeCloseTo(2/3, 2);
      expect(metrics.averageResponseTime).toBeCloseTo((100 + 200 + 50) / 3, 2);
    });
  });

  describe('ErrorNotificationService', () => {
    test('should show error notification', () => {
      const notification = (errorNotificationService as any).showError(
        'Test Error',
        'This is a test error message',
        ErrorSeverity.HIGH
      );
      
      expect(notification).toBeDefined();
      expect(notification.type).toBe('ERROR');
      expect(notification.title).toBe('Test Error');
      expect(notification.message).toBe('This is a test error message');
      expect(notification.severity).toBe(ErrorSeverity.HIGH);
    });

    test('should show success notification', () => {
      const notification = (errorNotificationService as any).showSuccess(
        'Operation Successful',
        'The operation completed successfully'
      );
      
      expect(notification).toBeDefined();
      expect(notification.type).toBe('SUCCESS');
      expect(notification.title).toBe('Operation Successful');
    });

    test('should close notification', () => {
      const notification = (errorNotificationService as any).showError(
        'Test Error',
        'This is a test error message'
      );
      
      let notifications = errorNotificationService.getAllNotifications();
      expect(notifications.length).toBe(1);
      
      errorNotificationService.closeNotification(notification.id);
      
      notifications = errorNotificationService.getAllNotifications();
      expect(notifications.length).toBe(0);
    });

    test('should configure notification settings', () => {
      const settings = {
        position: NotificationPosition.TOP_RIGHT,
        theme: NotificationTheme.DARK,
        autoClose: true,
        duration: 5000
      };
      
      (errorNotificationService as any).configure(settings);
      
      const notification = (errorNotificationService as any).showError('Test Error', 'Message');
      expect(notification.position).toBe(NotificationPosition.TOP_RIGHT);
      expect(notification.theme).toBe(NotificationTheme.DARK);
      expect(notification.autoClose).toBe(true);
      expect(notification.duration).toBe(5000);
    });
  });

  describe('Integration Tests', () => {
    test('should handle error flow from detection to notification', () => {
      // 1. Error occurs
      const error = new Error('Integration test error');
      
      // 2. Error is handled
      const errorInfo = errorHandlingService.handleError(
        error,
        ErrorCategory.NETWORK,
        ErrorSeverity.HIGH,
        { component: 'TestComponent' }
      );
      
      // 3. Error is logged
      (errorLoggingService as any).logError(error, ErrorCategory.NETWORK, ErrorSeverity.HIGH, { component: 'TestComponent' });
      
      // 4. User-friendly message is retrieved
      const userMessage = (userErrorMessageService as any).getUserErrorMessage(
        'NETWORK_ERROR',
        ErrorSeverity.HIGH
      );
      
      // 5. Notification is shown
      const notification = (errorNotificationService as any).showError(
        userMessage.title,
        userMessage.message,
        ErrorSeverity.HIGH
      );
      
      // Verify the flow
      expect(errorInfo).toBeDefined();
      expect((errorInfo as any).category).toBe(ErrorCategory.NETWORK);
      
      const logs = errorLoggingService.getLogs();
      const errorLog = logs.find(log => log.message.includes('Integration test error'));
      expect(errorLog).toBeDefined();
      
      expect(userMessage).toBeDefined();
      expect(userMessage.title).toBeDefined();
      
      expect(notification).toBeDefined();
      expect(notification.title).toBe(userMessage.title);
      expect(notification.message).toBe(userMessage.message);
    });

    test('should retry failed operations with proper error handling', async () => {
      let attemptCount = 0;
      const mockFn = vi.fn().mockImplementation(() => {
        attemptCount++;
        if (attemptCount < 3) {
          throw new Error('Network error');
        }
        return 'success';
      });
      
      // Retry function
      const result = await (retryService as any).retry(mockFn, {
        maxAttempts: 3,
        baseDelay: 10
      });
      
      expect(result).toBe('success');
      expect(mockFn.mock.calls.length).toBe(3);
      
      // Verify that retry attempts were logged
      const logs = errorLoggingService.getLogs();
      const retryLogs = logs.filter(log => log.message.includes('Retry attempt'));
      expect(retryLogs.length).toBe(2); // 2 retries before success
    });
  });
});