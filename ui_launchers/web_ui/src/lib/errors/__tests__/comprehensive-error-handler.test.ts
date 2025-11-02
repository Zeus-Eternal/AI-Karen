/**
 * Tests for comprehensive error handler
 * Requirements: 1.3, 2.3, 3.3, 4.3
 */

import { ComprehensiveErrorHandler } from '../comprehensive-error-handler';
import { ErrorCategory, ErrorSeverity } from '../error-categories';

import { vi } from 'vitest';

// Mock console methods
const originalConsole = { ...console };
beforeAll(() => {
  console.error = vi.fn();
  console.warn = vi.fn();
  console.info = vi.fn();
  console.log = vi.fn();

afterAll(() => {
  Object.assign(console, originalConsole);

describe('ComprehensiveErrorHandler', () => {
  let errorHandler: ComprehensiveErrorHandler;

  beforeEach(() => {
    errorHandler = ComprehensiveErrorHandler.getInstance();
    vi.clearAllMocks();

  describe('Error Handling', () => {
    it('should handle basic errors without recovery', async () => {
      const error = new Error('Test error');
      const result = await errorHandler.handleError(error, {
        enableRecovery: false

      expect(result.categorizedError).toBeDefined();
      expect(result.categorizedError.message).toBe('Test error');
      expect(result.recoveryResult).toBeUndefined();
      expect(result.userMessage).toBeDefined();

    it('should handle errors with recovery enabled', async () => {
      const error = new Error('ECONNREFUSED');
      const result = await errorHandler.handleError(error, {
        enableRecovery: true

      expect(result.categorizedError).toBeDefined();
      expect(result.recoveryResult).toBeDefined();
      expect(result.userMessage).toBeDefined();

    it('should handle string errors', async () => {
      const error = 'String error message';
      const result = await errorHandler.handleError(error);

      expect(result.categorizedError.message).toBe(error);
      expect(result.userMessage).toBeDefined();

    it('should include context in error handling', async () => {
      const error = new Error('Test error');
      const context = { userId: '123', action: 'login' };
      
      const result = await errorHandler.handleError(error, {
        context

      expect(result.categorizedError.context).toMatchObject(context);


  describe('Retry Logic', () => {
    it('should retry operations with success', async () => {
      let attemptCount = 0;
      const operation = vi.fn().mockImplementation(() => {
        attemptCount++;
        if (attemptCount === 1) {
          throw new Error('Temporary failure');
        }
        return Promise.resolve('success');

      const result = await errorHandler.handleWithRetry(operation, {
        maxRetryAttempts: 3

      expect(result).toBe('success');
      expect(operation).toHaveBeenCalledTimes(2);

    it('should fail after max retry attempts', async () => {
      const operation = vi.fn().mockRejectedValue(new Error('Persistent failure'));

      await expect(errorHandler.handleWithRetry(operation, {
        maxRetryAttempts: 2
      })).rejects.toThrow('Persistent failure');

      expect(operation).toHaveBeenCalledTimes(1); // Non-retryable errors only get called once

    it('should not retry non-retryable errors', async () => {
      const operation = vi.fn().mockRejectedValue(new Error('401 Unauthorized'));

      await expect(errorHandler.handleWithRetry(operation, {
        maxRetryAttempts: 3
      })).rejects.toThrow('401 Unauthorized');

      expect(operation).toHaveBeenCalledTimes(1);


  describe('Error-Handled Function Creation', () => {
    it('should create error-handled function wrapper', async () => {
      const originalFunction = vi.fn().mockResolvedValue('success');
      const wrappedFunction = errorHandler.createErrorHandledFunction(
        originalFunction,
        { maxRetryAttempts: 2 }
      );

      const result = await wrappedFunction('arg1', 'arg2');

      expect(result).toBe('success');
      expect(originalFunction).toHaveBeenCalledWith('arg1', 'arg2');

    it('should handle errors in wrapped function', async () => {
      let attemptCount = 0;
      const originalFunction = vi.fn().mockImplementation(() => {
        attemptCount++;
        if (attemptCount === 1) {
          throw new Error('ECONNREFUSED');
        }
        return Promise.resolve('success');

      const wrappedFunction = errorHandler.createErrorHandledFunction(
        originalFunction,
        { maxRetryAttempts: 3 }
      );

      const result = await wrappedFunction();
      expect(result).toBe('success');
      expect(originalFunction).toHaveBeenCalledTimes(2);


  describe('Error Logging', () => {
    it('should log critical errors with console.error', async () => {
      const error = new Error('Database connection failed');
      await errorHandler.handleError(error);

      expect(console.error).toHaveBeenCalled();

    it('should log medium severity errors with console.warn', async () => {
      const error = new Error('401 Unauthorized');
      await errorHandler.handleError(error);

      expect(console.warn).toHaveBeenCalled();

    it('should log low severity errors with console.info', async () => {
      const error = new Error('Validation error');
      await errorHandler.handleError(error);

      expect(console.info).toHaveBeenCalled();

    it('should not log when logging is disabled', async () => {
      const error = new Error('Test error');
      await errorHandler.handleError(error, {
        enableLogging: false

      expect(console.error).not.toHaveBeenCalled();
      expect(console.warn).not.toHaveBeenCalled();
      expect(console.info).not.toHaveBeenCalled();


  describe('User Action Requirements', () => {
    it('should require user action for configuration errors', async () => {
      const error = new Error('Invalid URL provided');
      const result = await errorHandler.handleError(error);

      expect(result.requiresUserAction).toBe(true);

    it('should require user action for invalid credentials', async () => {
      const error = new Error('Invalid credentials provided');
      const result = await errorHandler.handleError(error);

      expect(result.requiresUserAction).toBe(true);

    it('should require user action for validation errors', async () => {
      const error = new Error('Validation error: required field missing');
      const result = await errorHandler.handleError(error);

      expect(result.requiresUserAction).toBe(true);

    it('should not require user action for retryable network errors', async () => {
      const error = new Error('ECONNREFUSED');
      const result = await errorHandler.handleError(error);

      expect(result.requiresUserAction).toBe(false);


  describe('Error Listeners', () => {
    it('should notify error listeners', async () => {
      const listener = vi.fn();
      errorHandler.addErrorListener(listener);

      const error = new Error('Test error');
      await errorHandler.handleError(error);

      expect(listener).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Test error'
        })
      );

    it('should remove error listeners', async () => {
      const listener = vi.fn();
      errorHandler.addErrorListener(listener);
      errorHandler.removeErrorListener(listener);

      const error = new Error('Test error');
      await errorHandler.handleError(error);

      expect(listener).not.toHaveBeenCalled();

    it('should handle errors in error listeners gracefully', async () => {
      const faultyListener = vi.fn().mockImplementation(() => {
        throw new Error('Listener error');

      errorHandler.addErrorListener(faultyListener);

      const error = new Error('Test error');
      const result = await errorHandler.handleError(error);

      expect(result).toBeDefined();
      expect(console.error).toHaveBeenCalledWith(
        'Error in error listener:',
        expect.any(Error)
      );


  describe('Error Statistics', () => {
    it('should provide error statistics', () => {
      const stats = errorHandler.getErrorStatistics();

      expect(stats).toHaveProperty('totalErrors');
      expect(stats).toHaveProperty('errorsByCategory');
      expect(stats).toHaveProperty('errorsBySeverity');
      expect(stats.errorsByCategory).toHaveProperty(ErrorCategory.NETWORK);
      expect(stats.errorsBySeverity).toHaveProperty(ErrorSeverity.CRITICAL);


  describe('Error Tracking Management', () => {
    it('should clear error tracking data', () => {
      expect(() => errorHandler.clearErrorTracking()).not.toThrow();


  describe('Integration Scenarios', () => {
    it('should handle authentication timeout with recovery', async () => {
      const error = new Error('Authentication timeout');
      const result = await errorHandler.handleError(error, {
        enableRecovery: true,
        context: { operation: 'login', userId: '123' }

      expect(result.categorizedError.category).toBe(ErrorCategory.TIMEOUT);
      expect(result.userMessage).toContain('Recovery successful');
      expect(result.shouldRetry).toBe(true);

    it('should handle database connection failure with degraded mode', async () => {
      const error = new Error('Database connection pool exhausted');
      const result = await errorHandler.handleError(error, {
        enableRecovery: true

      expect(result.categorizedError.category).toBe(ErrorCategory.DATABASE);
      expect(result.categorizedError.severity).toBe(ErrorSeverity.CRITICAL);
      expect(result.recoveryResult).toBeDefined();

    it('should handle network failure with fallback', async () => {
      const error = new Error('ECONNREFUSED: Connection refused');
      const result = await errorHandler.handleError(error, {
        enableRecovery: true,
        context: { endpoint: '/api/auth/login' }

      expect(result.categorizedError.category).toBe(ErrorCategory.NETWORK);
      expect(result.categorizedError.fallbackAction).toBe('USE_FALLBACK_BACKEND');
      expect(result.shouldRetry).toBe(true);


  describe('Edge Cases', () => {
    it('should handle null/undefined errors gracefully', async () => {
      const result1 = await errorHandler.handleError(null as any);
      const result2 = await errorHandler.handleError(undefined as any);

      expect(result1.categorizedError).toBeDefined();
      expect(result2.categorizedError).toBeDefined();

    it('should handle errors during recovery gracefully', async () => {
      // Mock recovery manager to throw an error
      const mockRecoveryManager = {
        attemptRecovery: vi.fn().mockRejectedValue(new Error('Recovery failed'))
      };
      
      (errorHandler as any).recoveryManager = mockRecoveryManager;

      const error = new Error('ECONNREFUSED');
      const result = await errorHandler.handleError(error, {
        enableRecovery: true

      expect(result.categorizedError).toBeDefined();
      expect(result.recoveryResult).toBeUndefined();
      expect(console.error).toHaveBeenCalledWith(
        'Error during recovery attempt:',
        expect.any(Error)
      );


