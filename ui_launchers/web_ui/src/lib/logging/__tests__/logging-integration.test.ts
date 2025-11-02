/**
 * Integration tests for the complete logging system
 */

import { connectivityLogger, ConnectivityLogger } from '../connectivity-logger';
import { correlationTracker } from '../correlation-tracker';
import { performanceTracker } from '../performance-tracker';
import { loggedFetch, logAuthenticationAttempt } from '../integration-utils';

// Mock fetch
global.fetch = jest.fn();

// Mock console
const mockConsole = {
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};
Object.assign(console, mockConsole);

// Mock sessionStorage
const mockSessionStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn()
};
Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage

describe('Logging System Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    performanceTracker.clearHistory();
    correlationTracker.clearCorrelationId();

  describe('End-to-End Authentication Flow Logging', () => {
    it('should track complete authentication flow with correlation', async () => {
      // Mock successful authentication
      const mockAuthOperation = jest.fn(async () => ({
        success: true,
        token: 'auth-token-123',
        user: { id: 'user-123', email: 'user@example.com' }
      }));

      const mockResponse = new Response(JSON.stringify({ success: true }), { status: 200 });
      (fetch as jest.Mock).mockResolvedValueOnce(mockResponse);

      // Execute authentication with logging
      const result = await logAuthenticationAttempt(
        async () => {
          // Simulate API call within auth operation
          const response = await loggedFetch('https://api.example.com/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email: 'user@example.com', password: 'password' })

          return mockAuthOperation();
        },
        'user@example.com',
        'login'
      );

      // Verify correlation ID consistency
      const correlationId = correlationTracker.getCurrentCorrelationId();
      expect(correlationId).toMatch(/^corr_[a-f0-9-]+$/);

      // Verify authentication logging
      expect(mockConsole.info).toHaveBeenCalledWith(
        expect.stringContaining('[INFO] [authentication:login]'),
        'Starting login attempt',
        expect.objectContaining({
          context: expect.objectContaining({
            correlationId: expect.stringMatching(/^corr_[a-f0-9-]+$/)
          }),
          authData: expect.objectContaining({
            email: 'us***@example.com',
            success: false
          })
        })
      );

      expect(mockConsole.info).toHaveBeenCalledWith(
        expect.stringContaining('[INFO] [authentication:login]'),
        'login attempt succeeded',
        expect.objectContaining({
          authData: expect.objectContaining({
            success: true
          }),
          metrics: expect.objectContaining({
            duration: expect.any(Number)
          })
        })
      );

      // Verify connectivity logging for API call
      expect(mockConsole.debug).toHaveBeenCalledWith(
        expect.stringContaining('[DEBUG] [connectivity:request]'),
        'Starting POST request to https://api.example.com/auth/login',
        expect.objectContaining({
          connectionData: expect.objectContaining({
            url: 'https://api.example.com/auth/login',
            method: 'POST'
          })
        })
      );

      expect(mockConsole.info).toHaveBeenCalledWith(
        expect.stringContaining('[INFO] [connectivity:request]'),
        'POST request to https://api.example.com/auth/login completed with status 200',
        expect.objectContaining({
          connectionData: expect.objectContaining({
            statusCode: 200
          })
        })
      );

    it('should track authentication failure with retry attempts', async () => {
      const authError = new Error('Invalid credentials');
      const networkError = new Error('Network timeout');
      
      (fetch as jest.Mock)
        .mockRejectedValueOnce(networkError)
        .mockRejectedValueOnce(networkError)
        .mockRejectedValueOnce(authError);

      try {
        await logAuthenticationAttempt(
          async () => {
            const response = await loggedFetch('https://api.example.com/auth/login', {
              method: 'POST'

            throw authError;
          },
          'user@example.com',
          'login'
        );
      } catch (error) {
        expect(error).toBe(authError);
      }

      // Verify network error logging
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('[ERROR] [connectivity:request]'),
        'POST request to https://api.example.com/auth/login failed',
        expect.objectContaining({
          error: expect.objectContaining({
            message: 'Network timeout'
          })
        })
      );

      // Verify authentication failure logging
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('[ERROR] [authentication:login]'),
        'login attempt failed',
        expect.objectContaining({
          authData: expect.objectContaining({
            success: false,
            failureReason: 'Invalid credentials'
          })
        })
      );


  describe('Performance Monitoring Integration', () => {
    it('should track and log performance metrics across operations', async () => {
      // Mock slow operations
      const slowResponse = new Response('{"data": "test"}', { status: 200 });
      (fetch as jest.Mock).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve(slowResponse), 100))
      );

      // Execute multiple operations
      const operations = [
        () => loggedFetch('https://api.example.com/endpoint1'),
        () => loggedFetch('https://api.example.com/endpoint2'),
        () => loggedFetch('https://api.example.com/endpoint3')
      ];

      await Promise.all(operations.map(op => op()));

      // Get performance statistics
      const stats = performanceTracker.getPerformanceStats();
      expect(stats.count).toBeGreaterThan(0);
      expect(stats.averageTime).toBeGreaterThan(0);

      // Verify performance logging occurred
      const performanceLogs = mockConsole.info.mock.calls.filter(call =>
        call[0].includes('[INFO] [connectivity:request]')
      );
      expect(performanceLogs.length).toBeGreaterThan(0);

    it('should detect and log slow operations', async () => {
      // Mock very slow response
      const slowResponse = new Response('{"data": "test"}', { status: 200 });
      (fetch as jest.Mock).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve(slowResponse), 6000))
      );

      await loggedFetch('https://api.example.com/slow-endpoint');

      // Should log performance warning for slow request
      expect(mockConsole.warn).toHaveBeenCalledWith(
        expect.stringContaining('[WARN] [performance:response_time]'),
        'Slow network request detected: GET https://api.example.com/slow-endpoint',
        expect.objectContaining({
          performanceData: expect.objectContaining({
            exceeded: true,
            threshold: 5000
          })
        })
      );


  describe('Error Correlation and Tracking', () => {
    it('should maintain correlation across nested operations', async () => {
      const correlationId = correlationTracker.generateCorrelationId();
      
      await correlationTracker.withCorrelationAsync(correlationId, async () => {
        // Nested operation 1
        connectivityLogger.logConnectivity(
          'info',
          'Operation 1',
          { url: 'test1', method: 'GET' }
        );

        // Nested operation 2
        await correlationTracker.withCorrelationAsync(
          correlationTracker.generateCorrelationId(),
          async () => {
            connectivityLogger.logConnectivity(
              'info',
              'Nested operation',
              { url: 'test2', method: 'POST' }
            );
          }
        );

        // Back to original context
        connectivityLogger.logConnectivity(
          'info',
          'Operation 3',
          { url: 'test3', method: 'PUT' }
        );

      // Verify correlation IDs in logs
      const logCalls = mockConsole.info.mock.calls;
      
      // First and third operations should have same correlation ID
      const firstLog = logCalls.find(call => call[1] === 'Operation 1');
      const thirdLog = logCalls.find(call => call[1] === 'Operation 3');
      
      expect(firstLog[0]).toContain(correlationId);
      expect(thirdLog[0]).toContain(correlationId);

      // Nested operation should have different correlation ID
      const nestedLog = logCalls.find(call => call[1] === 'Nested operation');
      expect(nestedLog[0]).not.toContain(correlationId);


  describe('Remote Logging Integration', () => {
    it('should batch and send logs to remote endpoint', async () => {
      const remoteLogger = new ConnectivityLogger({
        enableRemoteLogging: true,
        remoteEndpoint: 'https://logs.example.com/api/logs',
        batchSize: 2,
        enableConsoleLogging: false

      (fetch as jest.Mock).mockResolvedValueOnce(new Response('OK', { status: 200 }));

      // Generate logs to trigger batch send
      remoteLogger.logConnectivity('info', 'Log 1', { url: 'test1', method: 'GET' });
      remoteLogger.logConnectivity('info', 'Log 2', { url: 'test2', method: 'POST' });

      // Wait for async flush
      await new Promise(resolve => setTimeout(resolve, 0));

      expect(fetch).toHaveBeenCalledWith(
        'https://logs.example.com/api/logs',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('"logs"')
        })
      );

      const requestBody = JSON.parse((fetch as jest.Mock).mock.calls[0][1].body);
      expect(requestBody.logs).toHaveLength(2);
      expect(requestBody.logs[0].message).toBe('Log 1');
      expect(requestBody.logs[1].message).toBe('Log 2');

    it('should handle remote logging failures and retry', async () => {
      const remoteLogger = new ConnectivityLogger({
        enableRemoteLogging: true,
        remoteEndpoint: 'https://logs.example.com/api/logs',
        batchSize: 1,
        enableConsoleLogging: true

      // First call fails, second succeeds
      (fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(new Response('OK', { status: 200 }));

      remoteLogger.logConnectivity('info', 'Test log', { url: 'test', method: 'GET' });

      // Wait for first flush attempt
      await new Promise(resolve => setTimeout(resolve, 0));

      // Should log error about failed remote logging
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to send logs to remote endpoint:',
        expect.any(Error)
      );

      // Trigger another log to retry
      remoteLogger.logConnectivity('info', 'Retry log', { url: 'test2', method: 'GET' });

      // Wait for retry
      await new Promise(resolve => setTimeout(resolve, 0));

      // Should eventually succeed
      expect(fetch).toHaveBeenCalledTimes(2);


  describe('Memory and Resource Management', () => {
    it('should manage memory usage and clean up old data', () => {
      // Generate many correlation associations
      for (let i = 0; i < 1500; i++) {
        correlationTracker.associateRequest(`request-${i}`, `correlation-${i}`);
      }

      correlationTracker.cleanup();

      // Old associations should be cleaned up
      expect(correlationTracker.getCorrelationForRequest('request-0')).toBeUndefined();
      expect(correlationTracker.getCorrelationForRequest('request-1400')).toBeDefined();

    it('should limit performance history size', async () => {
      // Generate many performance entries
      for (let i = 0; i < 1200; i++) {
        await performanceTracker.trackOperation(`operation-${i}`, async () => `result-${i}`);
      }

      const recentMetrics = performanceTracker.getRecentMetrics(100);
      expect(recentMetrics.length).toBeLessThanOrEqual(100);

      const stats = performanceTracker.getPerformanceStats();
      expect(stats.count).toBeLessThan(1200); // Should have been trimmed


  describe('Configuration and Environment Handling', () => {
    it('should adapt to different environments', () => {
      // Test with different configurations
      const debugLogger = new ConnectivityLogger({
        logLevel: 'debug',
        enablePerformanceMetrics: true,
        enableCorrelationTracking: true

      const productionLogger = new ConnectivityLogger({
        logLevel: 'warn',
        enablePerformanceMetrics: false,
        enableCorrelationTracking: false,
        enableRemoteLogging: true

      // Debug logger should log debug messages
      debugLogger.logConnectivity('debug', 'Debug message', { url: 'test', method: 'GET' });
      expect(mockConsole.debug).toHaveBeenCalled();

      jest.clearAllMocks();

      // Production logger should not log debug messages
      productionLogger.logConnectivity('debug', 'Debug message', { url: 'test', method: 'GET' });
      expect(mockConsole.debug).not.toHaveBeenCalled();

      // But should log warnings
      productionLogger.logConnectivity('warn', 'Warning message', { url: 'test', method: 'GET' });
      expect(mockConsole.warn).toHaveBeenCalled();


