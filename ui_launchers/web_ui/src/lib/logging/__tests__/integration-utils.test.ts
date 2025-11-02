/**
 * Tests for logging integration utilities
 */

import { loggedFetch, loggedFetchWithRetry, logAuthenticationAttempt, withPerformanceLogging, withAsyncPerformanceLogging, logComponentError, logSessionEvent } from '../integration-utils';
import { connectivityLogger } from '../connectivity-logger';
import { correlationTracker } from '../correlation-tracker';
import { performanceTracker } from '../performance-tracker';

// Mock the logger
jest.mock('../connectivity-logger');
jest.mock('../correlation-tracker');
jest.mock('../performance-tracker');

// Mock fetch
global.fetch = jest.fn();

describe('Integration Utils', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (correlationTracker.getCurrentCorrelationId as jest.Mock).mockReturnValue('test-correlation-id');
    (performanceTracker.trackNetworkRequest as jest.Mock).mockReturnValue({
      start: jest.fn(),
      end: jest.fn(() => ({ duration: 100, responseTime: 100 }))


  describe('loggedFetch', () => {
    it('should add correlation ID to headers and log request', async () => {
      const mockResponse = new Response('{"data": "test"}', { status: 200 });
      (fetch as jest.Mock).mockResolvedValueOnce(mockResponse);

      const response = await loggedFetch('https://api.example.com/test', {
        method: 'POST'

      expect(fetch).toHaveBeenCalledWith(
        'https://api.example.com/test',
        expect.objectContaining({
          method: 'POST',
          headers: expect.any(Headers)
        })
      );

      // Check that correlation ID was added to headers
      const callArgs = (fetch as jest.Mock).mock.calls[0];
      const headers = callArgs[1].headers;
      expect(headers.get('X-Correlation-ID')).toBe('test-correlation-id');

      expect(connectivityLogger.logConnectivity).toHaveBeenCalledWith(
        'debug',
        'Starting POST request to https://api.example.com/test',
        expect.objectContaining({
          url: 'https://api.example.com/test',
          method: 'POST'
        }),
        undefined,
        undefined,
        expect.objectContaining({
          correlationId: 'test-correlation-id'
        })
      );

      expect(connectivityLogger.logConnectivity).toHaveBeenCalledWith(
        'info',
        'POST request to https://api.example.com/test completed with status 200',
        expect.objectContaining({
          statusCode: 200
        }),
        undefined,
        expect.objectContaining({
          duration: 100
        }),
        expect.objectContaining({
          correlationId: 'test-correlation-id'
        })
      );

    it('should log errors and performance warnings', async () => {
      const error = new Error('Network error');
      (fetch as jest.Mock).mockRejectedValueOnce(error);

      const networkTracker = {
        start: jest.fn(),
        end: jest.fn(() => ({ duration: 6000, responseTime: 6000 }))
      };
      (performanceTracker.trackNetworkRequest as jest.Mock).mockReturnValue(networkTracker);

      await expect(
        loggedFetch('https://api.example.com/test')
      ).rejects.toThrow('Network error');

      expect(connectivityLogger.logConnectivity).toHaveBeenCalledWith(
        'error',
        'GET request to https://api.example.com/test failed',
        expect.objectContaining({
          url: 'https://api.example.com/test',
          method: 'GET'
        }),
        error,
        expect.objectContaining({
          duration: 6000
        }),
        expect.objectContaining({
          correlationId: 'test-correlation-id'
        })
      );

    it('should log performance warnings for slow requests', async () => {
      const mockResponse = new Response('{"data": "test"}', { status: 200 });
      (fetch as jest.Mock).mockResolvedValueOnce(mockResponse);

      const networkTracker = {
        start: jest.fn(),
        end: jest.fn(() => ({ duration: 6000, responseTime: 6000 }))
      };
      (performanceTracker.trackNetworkRequest as jest.Mock).mockReturnValue(networkTracker);

      await loggedFetch('https://api.example.com/test');

      expect(connectivityLogger.logPerformance).toHaveBeenCalledWith(
        'warn',
        'Slow network request detected: GET https://api.example.com/test',
        expect.objectContaining({
          operation: 'GET https://api.example.com/test',
          duration: 6000,
          threshold: 5000,
          exceeded: true
        })
      );


  describe('loggedFetchWithRetry', () => {
    it('should retry failed requests and log retry attempts', async () => {
      const error = new Error('Network error');
      const mockResponse = new Response('{"data": "test"}', { status: 200 });
      
      (fetch as jest.Mock)
        .mockRejectedValueOnce(error)
        .mockRejectedValueOnce(error)
        .mockResolvedValueOnce(mockResponse);

      const response = await loggedFetchWithRetry(
        'https://api.example.com/test',
        { method: 'GET' },
        2
      );

      expect(fetch).toHaveBeenCalledTimes(3);
      expect(connectivityLogger.logConnectivity).toHaveBeenCalledWith(
        'info',
        'Retrying request to https://api.example.com/test (attempt 2/3)',
        expect.objectContaining({
          retryAttempt: 1
        })
      );

    it('should log when all retries are exhausted', async () => {
      const error = new Error('Network error');
      (fetch as jest.Mock).mockRejectedValue(error);

      await expect(
        loggedFetchWithRetry('https://api.example.com/test', {}, 1)
      ).rejects.toThrow('Network error');

      expect(connectivityLogger.logConnectivity).toHaveBeenCalledWith(
        'error',
        'All retry attempts failed for https://api.example.com/test',
        expect.objectContaining({
          retryAttempt: 1
        }),
        error
      );


  describe('logAuthenticationAttempt', () => {
    it('should log successful authentication attempts', async () => {
      const mockOperation = jest.fn(async () => 'auth-result');
      (correlationTracker.withCorrelationAsync as jest.Mock).mockImplementation(
        (id, fn) => fn()
      );

      const result = await logAuthenticationAttempt(
        mockOperation,
        'user@example.com',
        'login'
      );

      expect(result).toBe('auth-result');
      expect(connectivityLogger.logAuthentication).toHaveBeenCalledWith(
        'info',
        'Starting login attempt',
        expect.objectContaining({
          email: 'user@example.com',
          success: false
        }),
        'login'
      );

      expect(connectivityLogger.logAuthentication).toHaveBeenCalledWith(
        'info',
        'login attempt succeeded',
        expect.objectContaining({
          email: 'user@example.com',
          success: true
        }),
        'login',
        undefined,
        expect.objectContaining({
          duration: expect.any(Number)
        })
      );

    it('should log failed authentication attempts', async () => {
      const error = new Error('Invalid credentials');
      const mockOperation = jest.fn(async () => {
        throw error;

      (correlationTracker.withCorrelationAsync as jest.Mock).mockImplementation(
        (id, fn) => fn()
      );

      await expect(
        logAuthenticationAttempt(mockOperation, 'user@example.com', 'login')
      ).rejects.toThrow('Invalid credentials');

      expect(connectivityLogger.logAuthentication).toHaveBeenCalledWith(
        'error',
        'login attempt failed',
        expect.objectContaining({
          email: 'user@example.com',
          success: false,
          failureReason: 'Invalid credentials'
        }),
        'login',
        error,
        expect.objectContaining({
          duration: expect.any(Number)
        })
      );


  describe('withPerformanceLogging', () => {
    it('should wrap function with performance logging', () => {
      const mockFn = jest.fn(() => 'result');
      (performanceTracker.trackSyncOperation as jest.Mock).mockReturnValue({
        result: 'result',
        metrics: { duration: 150 }

      const wrappedFn = withPerformanceLogging(mockFn, 'test-operation');
      const result = wrappedFn('arg1', 'arg2');

      expect(result).toBe('result');
      expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2');
      expect(performanceTracker.trackSyncOperation).toHaveBeenCalledWith(
        'test-operation',
        expect.any(Function)
      );

      expect(connectivityLogger.logPerformance).toHaveBeenCalledWith(
        'info',
        'Component operation: test-operation',
        expect.objectContaining({
          operation: 'test-operation',
          duration: 150,
          threshold: 100,
          exceeded: true
        })
      );


  describe('withAsyncPerformanceLogging', () => {
    it('should wrap async function with performance logging', async () => {
      const mockFn = jest.fn(async () => 'async-result');
      (performanceTracker.trackOperation as jest.Mock).mockResolvedValue({
        result: 'async-result',
        metrics: { duration: 2000 }

      const wrappedFn = withAsyncPerformanceLogging(mockFn, 'async-operation');
      const result = await wrappedFn('arg1');

      expect(result).toBe('async-result');
      expect(mockFn).toHaveBeenCalledWith('arg1');
      expect(performanceTracker.trackOperation).toHaveBeenCalledWith(
        'async-operation',
        expect.any(Function)
      );

      expect(connectivityLogger.logPerformance).toHaveBeenCalledWith(
        'info',
        'Async operation: async-operation',
        expect.objectContaining({
          operation: 'async-operation',
          duration: 2000,
          threshold: 1000,
          exceeded: true
        })
      );


  describe('logComponentError', () => {
    it('should log React component errors', () => {
      const error = new Error('Component error');
      const errorInfo = { componentStack: 'Component stack trace' };

      logComponentError(error, errorInfo, 'TestComponent');

      expect(connectivityLogger.logError).toHaveBeenCalledWith(
        'React component error in TestComponent',
        error,
        'error',
        expect.objectContaining({
          correlationId: 'test-correlation-id'
        })
      );


  describe('logSessionEvent', () => {
    it('should log session events', () => {
      logSessionEvent('created', 'session-123', 'user-456');

      expect(connectivityLogger.logAuthentication).toHaveBeenCalledWith(
        'info',
        'Session created',
        expect.objectContaining({
          success: true
        }),
        'session_validation',
        undefined,
        undefined,
        expect.objectContaining({
          sessionId: 'session-123',
          userId: 'user-456'
        })
      );

    it('should log session expiration as failure', () => {
      logSessionEvent('expired', 'session-123');

      expect(connectivityLogger.logAuthentication).toHaveBeenCalledWith(
        'info',
        'Session expired',
        expect.objectContaining({
          success: false,
          failureReason: 'Session expired'
        }),
        'session_validation',
        undefined,
        undefined,
        expect.objectContaining({
          sessionId: 'session-123'
        })
      );


