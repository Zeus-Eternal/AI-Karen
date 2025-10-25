/**
 * Tests for connectivity logging functionality
 */

import { ConnectivityLogger } from '../connectivity-logger';
import { correlationTracker } from '../correlation-tracker';

// Mock fetch for remote logging tests
global.fetch = jest.fn();

// Mock console methods
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
});

describe('ConnectivityLogger', () => {
  let logger: ConnectivityLogger;

  beforeEach(() => {
    jest.clearAllMocks();
    logger = new ConnectivityLogger({
      enableConsoleLogging: true,
      enableRemoteLogging: false,
      logLevel: 'debug'
    });
  });

  afterEach(() => {
    logger.stopAutoFlush();
  });

  describe('logConnectivity', () => {
    it('should log connectivity issues with proper structure', () => {
      const connectionData = {
        url: 'https://api.example.com/test',
        method: 'GET',
        statusCode: 500,
        retryAttempt: 1
      };
      
      const error = new Error('Connection failed');
      
      logger.logConnectivity(
        'error',
        'Connection failed',
        connectionData,
        error
      );
      
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('[ERROR] [connectivity:retry]'),
        'Connection failed',
        expect.objectContaining({
          category: 'connectivity',
          subcategory: 'retry',
          connectionData,
          error: expect.objectContaining({
            name: 'Error',
            message: 'Connection failed'
          })
        })
      );
    });

    it('should determine correct subcategory based on error type', () => {
      const timeoutError = new Error('Request timeout');
      timeoutError.name = 'TimeoutError';
      
      logger.logConnectivity(
        'error',
        'Request timed out',
        { url: 'test', method: 'GET' },
        timeoutError
      );
      
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('[ERROR] [connectivity:timeout]'),
        expect.any(String),
        expect.objectContaining({
          subcategory: 'timeout'
        })
      );
    });
  });

  describe('logAuthentication', () => {
    it('should log authentication attempts with sanitized email', () => {
      const authData = {
        email: 'user@example.com',
        success: true,
        attemptNumber: 1
      };
      
      logger.logAuthentication(
        'info',
        'Login successful',
        authData,
        'login'
      );
      
      expect(mockConsole.info).toHaveBeenCalledWith(
        expect.stringContaining('[INFO] [authentication:login]'),
        'Login successful',
        expect.objectContaining({
          category: 'authentication',
          subcategory: 'login',
          authData: expect.objectContaining({
            email: 'us***@example.com', // Sanitized
            success: true
          })
        })
      );
    });

    it('should handle authentication failures', () => {
      const authData = {
        email: 'user@example.com',
        success: false,
        failureReason: 'Invalid credentials'
      };
      
      const error = new Error('Authentication failed');
      
      logger.logAuthentication(
        'error',
        'Login failed',
        authData,
        'login',
        error
      );
      
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('[ERROR] [authentication:login]'),
        'Login failed',
        expect.objectContaining({
          authData: expect.objectContaining({
            success: false,
            failureReason: 'Invalid credentials'
          }),
          error: expect.objectContaining({
            message: 'Authentication failed'
          })
        })
      );
    });
  });

  describe('logPerformance', () => {
    it('should log performance metrics', () => {
      const performanceData = {
        operation: 'API Call',
        duration: 1500,
        threshold: 1000,
        exceeded: true
      };
      
      logger.logPerformance(
        'warn',
        'Slow API call detected',
        performanceData,
        'api_call'
      );
      
      expect(mockConsole.warn).toHaveBeenCalledWith(
        expect.stringContaining('[WARN] [performance:api_call]'),
        'Slow API call detected',
        expect.objectContaining({
          category: 'performance',
          subcategory: 'api_call',
          performanceData
        })
      );
    });

    it('should skip performance logging when disabled', () => {
      const disabledLogger = new ConnectivityLogger({
        enablePerformanceMetrics: false
      });
      
      disabledLogger.logPerformance(
        'info',
        'Performance test',
        { operation: 'test', duration: 100 }
      );
      
      expect(mockConsole.info).not.toHaveBeenCalled();
    });
  });

  describe('logError', () => {
    it('should log general errors with context', () => {
      const error = new Error('General error');
      error.stack = 'Error stack trace';
      
      logger.logError(
        'Something went wrong',
        error,
        'error',
        { userId: 'user123' }
      );
      
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('[ERROR] [error]'),
        'Something went wrong',
        expect.objectContaining({
          category: 'error',
          error: expect.objectContaining({
            name: 'Error',
            message: 'General error',
            stack: 'Error stack trace'
          }),
          context: expect.objectContaining({
            userId: 'user123'
          })
        })
      );
    });
  });

  describe('log level filtering', () => {
    it('should respect log level configuration', () => {
      const warnLogger = new ConnectivityLogger({
        logLevel: 'warn',
        enableConsoleLogging: true
      });
      
      // Debug and info should be filtered out
      warnLogger.logConnectivity('debug', 'Debug message', { url: 'test', method: 'GET' });
      warnLogger.logConnectivity('info', 'Info message', { url: 'test', method: 'GET' });
      
      expect(mockConsole.debug).not.toHaveBeenCalled();
      expect(mockConsole.info).not.toHaveBeenCalled();
      
      // Warn and error should be logged
      warnLogger.logConnectivity('warn', 'Warn message', { url: 'test', method: 'GET' });
      warnLogger.logConnectivity('error', 'Error message', { url: 'test', method: 'GET' });
      
      expect(mockConsole.warn).toHaveBeenCalled();
      expect(mockConsole.error).toHaveBeenCalled();
    });
  });

  describe('remote logging', () => {
    it('should buffer logs for remote sending', () => {
      const remoteLogger = new ConnectivityLogger({
        enableRemoteLogging: true,
        remoteEndpoint: 'https://logs.example.com/api/logs',
        batchSize: 2
      });
      
      remoteLogger.logConnectivity('info', 'Test 1', { url: 'test1', method: 'GET' });
      remoteLogger.logConnectivity('info', 'Test 2', { url: 'test2', method: 'GET' });
      
      // Should trigger flush when batch size is reached
      expect(fetch).toHaveBeenCalledWith(
        'https://logs.example.com/api/logs',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('"logs"')
        })
      );
    });

    it('should handle remote logging failures gracefully', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));
      
      const remoteLogger = new ConnectivityLogger({
        enableRemoteLogging: true,
        remoteEndpoint: 'https://logs.example.com/api/logs',
        batchSize: 1
      });
      
      // Should not throw error
      remoteLogger.logConnectivity('info', 'Test', { url: 'test', method: 'GET' });
      
      // Wait for async flush
      await new Promise(resolve => setTimeout(resolve, 0));
      
      expect(mockConsole.error).toHaveBeenCalledWith(
        'Failed to send logs to remote endpoint:',
        expect.any(Error)
      );
    });
  });

  describe('configuration management', () => {
    it('should update configuration', () => {
      const initialConfig = logger.getConfig();
      expect(initialConfig.logLevel).toBe('debug');
      
      logger.updateConfig({ logLevel: 'error' });
      
      const updatedConfig = logger.getConfig();
      expect(updatedConfig.logLevel).toBe('error');
    });

    it('should start auto flush when remote logging is enabled', () => {
      const spy = jest.spyOn(logger as any, 'startAutoFlush');
      
      logger.updateConfig({
        enableRemoteLogging: true,
        flushInterval: 1000
      });
      
      expect(spy).toHaveBeenCalled();
    });
  });

  describe('correlation tracking integration', () => {
    it('should include correlation ID in log context', () => {
      const testCorrelationId = 'test-correlation-123';
      correlationTracker.setCorrelationId(testCorrelationId);
      
      logger.logConnectivity('info', 'Test message', { url: 'test', method: 'GET' });
      
      expect(mockConsole.info).toHaveBeenCalledWith(
        expect.stringContaining(testCorrelationId),
        'Test message',
        expect.objectContaining({
          context: expect.objectContaining({
            correlationId: testCorrelationId
          })
        })
      );
    });
  });

  describe('email sanitization', () => {
    it('should sanitize short emails', () => {
      const logger = new ConnectivityLogger();
      const sanitized = (logger as any).sanitizeEmail('ab@example.com');
      expect(sanitized).toBe('ab***@example.com');
    });

    it('should sanitize longer emails', () => {
      const logger = new ConnectivityLogger();
      const sanitized = (logger as any).sanitizeEmail('longuser@example.com');
      expect(sanitized).toBe('lo***@example.com');
    });
  });
});