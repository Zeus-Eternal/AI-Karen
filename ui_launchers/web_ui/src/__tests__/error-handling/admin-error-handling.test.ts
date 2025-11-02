/**
 * Admin Error Handling Tests
 * 
 * Comprehensive tests for admin error handling system including
 * error classification, retry logic, user messaging, and accessibility.
 * 
 * Requirements: 7.2, 7.4
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import AdminErrorHandler, { type AdminError } from '@/lib/errors/admin-error-handler';
import { useAdminErrorHandler } from '@/hooks/useAdminErrorHandler';

// Mock console methods to avoid noise in tests
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

beforeAll(() => {
  console.error = jest.fn();
  console.warn = jest.fn();

afterAll(() => {
  console.error = originalConsoleError;
  console.warn = originalConsoleWarn;

describe('AdminErrorHandler', () => {
  describe('Error Creation', () => {
    it('should create error with known error code', () => {
      const error = AdminErrorHandler.createError('USER_NOT_FOUND', 'Custom details');
      
      expect(error.code).toBe('USER_NOT_FOUND');
      expect(error.message).toBe('The requested user could not be found.');
      expect(error.details).toBe('Custom details');
      expect(error.severity).toBe('medium');
      expect(error.retryable).toBe(true);
      expect(error.remediation).toHaveLength(3);

    it('should create unknown error for invalid code', () => {
      const error = AdminErrorHandler.createError('INVALID_CODE', 'Test details');
      
      expect(error.code).toBe('UNKNOWN_ERROR');
      expect(error.message).toBe('An unexpected error occurred.');
      expect(error.details).toBe('Test details');
      expect(error.severity).toBe('medium');
      expect(error.retryable).toBe(true);

    it('should create error from HTTP status codes', () => {
      const error401 = AdminErrorHandler.fromHttpError(401);
      expect(error401.code).toBe('AUTH_SESSION_EXPIRED');
      expect(error401.severity).toBe('medium');

      const error403 = AdminErrorHandler.fromHttpError(403);
      expect(error403.code).toBe('AUTH_INSUFFICIENT_PERMISSIONS');
      expect(error403.severity).toBe('medium');

      const error404 = AdminErrorHandler.fromHttpError(404);
      expect(error404.code).toBe('USER_NOT_FOUND');
      expect(error404.severity).toBe('medium');

      const error500 = AdminErrorHandler.fromHttpError(500);
      expect(error500.code).toBe('SYSTEM_SERVER_ERROR');
      expect(error500.severity).toBe('high');

    it('should create error from network errors', () => {
      const networkError = new TypeError('Failed to fetch');
      const error = AdminErrorHandler.fromNetworkError(networkError);
      
      expect(error.code).toBe('SYSTEM_NETWORK_ERROR');
      expect(error.severity).toBe('medium');
      expect(error.retryable).toBe(true);

    it('should handle abort errors', () => {
      const abortError = new Error('The operation was aborted');
      abortError.name = 'AbortError';
      
      const error = AdminErrorHandler.fromNetworkError(abortError);
      
      expect(error.code).toBe('OPERATION_CANCELLED');
      expect(error.severity).toBe('low');
      expect(error.retryable).toBe(true);


  describe('Retry Logic', () => {
    it('should determine if error is retryable', () => {
      const retryableError = AdminErrorHandler.createError('SYSTEM_SERVER_ERROR');
      const nonRetryableError = AdminErrorHandler.createError('AUTH_INSUFFICIENT_PERMISSIONS');
      
      expect(AdminErrorHandler.shouldRetry(retryableError, 1)).toBe(true);
      expect(AdminErrorHandler.shouldRetry(retryableError, 3)).toBe(false); // Max attempts reached
      expect(AdminErrorHandler.shouldRetry(nonRetryableError, 1)).toBe(false);

    it('should calculate retry delay with exponential backoff', () => {
      const error = AdminErrorHandler.createError('SYSTEM_SERVER_ERROR');
      
      const delay1 = AdminErrorHandler.getRetryDelay(error, 1);
      const delay2 = AdminErrorHandler.getRetryDelay(error, 2);
      const delay3 = AdminErrorHandler.getRetryDelay(error, 3);
      
      expect(delay1).toBeGreaterThan(1000);
      expect(delay1).toBeLessThan(3000);
      expect(delay2).toBeGreaterThan(delay1);
      expect(delay3).toBeGreaterThan(delay2);
      expect(delay3).toBeLessThan(31000); // Should cap at 30s + jitter

    it('should not retry validation errors', () => {
      const validationError = AdminErrorHandler.createError('VALIDATION_WEAK_PASSWORD');
      
      expect(AdminErrorHandler.shouldRetry(validationError, 1)).toBe(false);

    it('should not retry auth errors', () => {
      const authError = AdminErrorHandler.createError('AUTH_INSUFFICIENT_PERMISSIONS');
      
      expect(AdminErrorHandler.shouldRetry(authError, 1)).toBe(false);


  describe('Error Logging', () => {
    it('should log high severity errors to console.error', () => {
      const error = AdminErrorHandler.createError('SYSTEM_SERVER_ERROR');
      
      AdminErrorHandler.logError(error, {
        operation: 'test_operation',
        timestamp: new Date()

      expect(console.error).toHaveBeenCalledWith(
        'Admin Error:',
        expect.objectContaining({
          error: 'SYSTEM_SERVER_ERROR',
          severity: 'high'
        })
      );

    it('should log medium severity errors to console.warn', () => {
      const error = AdminErrorHandler.createError('USER_NOT_FOUND');
      
      AdminErrorHandler.logError(error);
      
      expect(console.warn).toHaveBeenCalledWith(
        'Admin Warning:',
        expect.objectContaining({
          error: 'USER_NOT_FOUND',
          severity: 'medium'
        })
      );



describe('useAdminErrorHandler Hook', () => {
  it('should initialize with no error', () => {
    const { result } = renderHook(() => useAdminErrorHandler());
    
    expect(result.current.error).toBeNull();
    expect(result.current.isRetrying).toBe(false);
    expect(result.current.retryCount).toBe(0);
    expect(result.current.canRetry).toBe(false);

  it('should handle errors correctly', () => {
    const { result } = renderHook(() => useAdminErrorHandler());
    
    act(() => {
      result.current.handleError(new Error('Test error'));

    expect(result.current.error).not.toBeNull();
    expect(result.current.error?.code).toBe('UNKNOWN_ERROR');
    expect(result.current.error?.details).toBe('Test error');

  it('should handle HTTP response errors', () => {
    const { result } = renderHook(() => useAdminErrorHandler());
    
    const mockResponse = new Response('Not Found', { status: 404 });
    
    act(() => {
      result.current.handleError(mockResponse);

    expect(result.current.error?.code).toBe('USER_NOT_FOUND');

  it('should handle async operations with success', async () => {
    const { result } = renderHook(() => useAdminErrorHandler());
    
    const mockOperation = jest.fn().mockResolvedValue('success');
    
    let operationResult: any;
    await act(async () => {
      operationResult = await result.current.handleAsyncOperation(mockOperation);

    expect(operationResult).toBe('success');
    expect(result.current.error).toBeNull();
    expect(mockOperation).toHaveBeenCalled();

  it('should handle async operations with failure', async () => {
    const { result } = renderHook(() => useAdminErrorHandler());
    
    const mockOperation = jest.fn().mockRejectedValue(new Error('Operation failed'));
    
    let operationResult: any;
    await act(async () => {
      operationResult = await result.current.handleAsyncOperation(mockOperation);

    expect(operationResult).toBeNull();
    expect(result.current.error).not.toBeNull();
    expect(result.current.error?.details).toBe('Operation failed');

  it('should retry failed operations', async () => {
    const { result } = renderHook(() => useAdminErrorHandler({
      maxRetries: 2
    }));
    
    const mockOperation = jest.fn()
      .mockRejectedValueOnce(new Error('First failure'))
      .mockResolvedValueOnce('success');
    
    // First attempt fails
    await act(async () => {
      await result.current.handleAsyncOperation(mockOperation);

    expect(result.current.error).not.toBeNull();
    expect(result.current.canRetry).toBe(true);
    
    // Retry succeeds
    await act(async () => {
      await result.current.retry();

    await waitFor(() => {
      expect(result.current.error).toBeNull();
      expect(result.current.retryCount).toBe(0);

    expect(mockOperation).toHaveBeenCalledTimes(2);

  it('should not retry non-retryable errors', async () => {
    const { result } = renderHook(() => useAdminErrorHandler());
    
    act(() => {
      result.current.handleError(new Response('Forbidden', { status: 403 }));

    expect(result.current.canRetry).toBe(false);

  it('should clear errors', () => {
    const { result } = renderHook(() => useAdminErrorHandler());
    
    act(() => {
      result.current.handleError(new Error('Test error'));

    expect(result.current.error).not.toBeNull();
    
    act(() => {
      result.current.clearError();

    expect(result.current.error).toBeNull();
    expect(result.current.retryCount).toBe(0);

  it('should set custom error', () => {
    const { result } = renderHook(() => useAdminErrorHandler());
    
    const customError = AdminErrorHandler.createError('USER_NOT_FOUND', 'Custom error');
    
    act(() => {
      result.current.setError(customError);

    expect(result.current.error).toBe(customError);

  it('should handle context in operations', async () => {
    const { result } = renderHook(() => useAdminErrorHandler({
      context: { operation: 'test_operation' }
    }));
    
    const mockOperation = jest.fn().mockRejectedValue(new Error('Test error'));
    
    await act(async () => {
      await result.current.handleAsyncOperation(mockOperation, {
        resource: 'test_resource'


    expect(result.current.error).not.toBeNull();
    // Context should be merged and used for logging

  it('should respect max retry limit', async () => {
    const { result } = renderHook(() => useAdminErrorHandler({
      maxRetries: 1
    }));
    
    const mockOperation = jest.fn().mockRejectedValue(new Error('Always fails'));
    
    // First attempt
    await act(async () => {
      await result.current.handleAsyncOperation(mockOperation);

    expect(result.current.canRetry).toBe(true);
    
    // First retry
    await act(async () => {
      await result.current.retry();

    expect(result.current.canRetry).toBe(false);
    expect(result.current.retryCount).toBe(1);


describe('Error Message Quality', () => {
  it('should provide helpful remediation steps', () => {
    const errors = [
      'AUTH_INSUFFICIENT_PERMISSIONS',
      'USER_NOT_FOUND',
      'VALIDATION_WEAK_PASSWORD',
      'SYSTEM_DATABASE_ERROR',
      'EMAIL_SEND_FAILED'
    ];
    
    errors.forEach(errorCode => {
      const error = AdminErrorHandler.createError(errorCode);
      
      expect(error.remediation).toBeDefined();
      expect(error.remediation!.length).toBeGreaterThan(0);
      
      // Each remediation step should be actionable
      error.remediation!.forEach(step => {
        expect(step.length).toBeGreaterThan(10); // Reasonable length
        expect(step).toMatch(/^[A-Z]/); // Starts with capital letter



  it('should have appropriate severity levels', () => {
    const criticalErrors = ['SYSTEM_DATABASE_ERROR'];
    const highErrors = ['SYSTEM_SERVER_ERROR', 'USER_CANNOT_DEMOTE_LAST_ADMIN'];
    const mediumErrors = ['AUTH_INSUFFICIENT_PERMISSIONS', 'USER_NOT_FOUND'];
    const lowErrors = ['VALIDATION_WEAK_PASSWORD', 'USER_CANNOT_DELETE_SELF'];
    
    criticalErrors.forEach(code => {
      const error = AdminErrorHandler.createError(code);
      expect(error.severity).toBe('critical');

    highErrors.forEach(code => {
      const error = AdminErrorHandler.createError(code);
      expect(error.severity).toBe('high');

    mediumErrors.forEach(code => {
      const error = AdminErrorHandler.createError(code);
      expect(error.severity).toBe('medium');

    lowErrors.forEach(code => {
      const error = AdminErrorHandler.createError(code);
      expect(error.severity).toBe('low');


  it('should have user-friendly messages', () => {
    const error = AdminErrorHandler.createError('USER_NOT_FOUND');
    
    // Should not contain technical jargon
    expect(error.message).not.toMatch(/500|404|HTTP|API|JSON/i);
    
    // Should be clear and actionable
    expect(error.message.length).toBeGreaterThan(10);
    expect(error.message).toMatch(/^[A-Z]/); // Starts with capital
    expect(error.message).toMatch(/\.$/); // Ends with period


describe('Specialized Error Handlers', () => {
  it('should configure user management errors correctly', () => {
    const { useUserManagementErrors } = require('@/hooks/useAdminErrorHandler');
    const { result } = renderHook(() => useUserManagementErrors());
    
    // Should have appropriate configuration for user management
    expect(result.current.error).toBeNull();
    expect(result.current.canRetry).toBe(false);

  it('should configure bulk operation errors correctly', () => {
    const { useBulkOperationErrors } = require('@/hooks/useAdminErrorHandler');
    const { result } = renderHook(() => useBulkOperationErrors());
    
    // Bulk operations should have limited retries
    expect(result.current.error).toBeNull();
    expect(result.current.canRetry).toBe(false);

  it('should configure system config errors correctly', () => {
    const { useSystemConfigErrors } = require('@/hooks/useAdminErrorHandler');
    const { result } = renderHook(() => useSystemConfigErrors());
    
    // System config should allow more retries
    expect(result.current.error).toBeNull();
    expect(result.current.canRetry).toBe(false);

  it('should configure audit log errors correctly', () => {
    const { useAuditLogErrors } = require('@/hooks/useAdminErrorHandler');
    const { result } = renderHook(() => useAuditLogErrors());
    
    // Audit logs should be less intrusive
    expect(result.current.error).toBeNull();
    expect(result.current.canRetry).toBe(false);


describe('Error Recovery Scenarios', () => {
  it('should handle network recovery', async () => {
    const { result } = renderHook(() => useAdminErrorHandler());
    
    const mockOperation = jest.fn()
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce('recovered');
    
    // Network fails
    await act(async () => {
      await result.current.handleAsyncOperation(mockOperation);

    expect(result.current.error?.code).toBe('SYSTEM_NETWORK_ERROR');
    expect(result.current.canRetry).toBe(true);
    
    // Network recovers
    await act(async () => {
      await result.current.retry();

    await waitFor(() => {
      expect(result.current.error).toBeNull();


  it('should handle server recovery', async () => {
    const { result } = renderHook(() => useAdminErrorHandler());
    
    const mockOperation = jest.fn()
      .mockRejectedValueOnce(new Response('Internal Server Error', { status: 500 }))
      .mockResolvedValueOnce('recovered');
    
    // Server error
    await act(async () => {
      await result.current.handleAsyncOperation(mockOperation);

    expect(result.current.error?.code).toBe('SYSTEM_SERVER_ERROR');
    expect(result.current.canRetry).toBe(true);
    
    // Server recovers
    await act(async () => {
      await result.current.retry();

    await waitFor(() => {
      expect(result.current.error).toBeNull();


  it('should handle permanent failures gracefully', async () => {
    const { result } = renderHook(() => useAdminErrorHandler({
      maxRetries: 2
    }));
    
    const mockOperation = jest.fn().mockRejectedValue(new Error('Permanent failure'));
    
    // Initial failure
    await act(async () => {
      await result.current.handleAsyncOperation(mockOperation);

    // Retry 1
    await act(async () => {
      await result.current.retry();

    // Retry 2 (final)
    await act(async () => {
      await result.current.retry();

    expect(result.current.canRetry).toBe(false);
    expect(result.current.retryCount).toBe(2);
    expect(result.current.error).not.toBeNull();

