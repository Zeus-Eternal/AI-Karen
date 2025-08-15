import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import ErrorTracker, { 
  getErrorTracker, 
  captureError, 
  addBreadcrumb, 
  setUser, 
  setTag, 
  setContext 
} from '../errorTracking';
import { getTelemetryService } from '../telemetry';

// Mock telemetry service
vi.mock('../telemetry', () => ({
  getTelemetryService: vi.fn(() => ({
    track: vi.fn(),
    setUserId: vi.fn(),
  })),
}));

// Mock React
vi.mock('react', () => ({
  version: '18.2.0',
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

// Mock fetch
const fetchMock = vi.fn();

// Mock performance
const performanceMock = {
  memory: {
    usedJSHeapSize: 1000000,
    totalJSHeapSize: 2000000,
    jsHeapSizeLimit: 4000000,
  },
};

// Mock navigator
const navigatorMock = {
  userAgent: 'Mozilla/5.0 (Test Browser)',
  onLine: true,
  connection: {
    effectiveType: '4g',
  },
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

Object.defineProperty(global, 'fetch', {
  value: fetchMock,
});

Object.defineProperty(global, 'performance', {
  value: performanceMock,
});

Object.defineProperty(global, 'navigator', {
  value: navigatorMock,
});

// Mock window location
Object.defineProperty(window, 'location', {
  value: {
    href: 'https://example.com/test',
    pathname: '/test',
    search: '?param=value',
  },
  writable: true,
});

// Mock process.env
Object.defineProperty(process, 'env', {
  value: {
    NODE_ENV: 'test',
    REACT_APP_VERSION: '1.0.0',
  },
});

describe('ErrorTracker', () => {
  let errorTracker: ErrorTracker;
  let mockTelemetryTrack: any;
  let mockTelemetrySetUserId: any;

  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
    });

    mockTelemetryTrack = vi.fn();
    mockTelemetrySetUserId = vi.fn();
    (getTelemetryService as any).mockReturnValue({
      track: mockTelemetryTrack,
      setUserId: mockTelemetrySetUserId,
    });

    errorTracker = new ErrorTracker({
      enabled: true,
      captureUnhandledRejections: false, // Disable for testing
      captureConsoleErrors: false, // Disable for testing
    });
  });

  afterEach(() => {
    errorTracker.destroy();
  });

  describe('Initialization', () => {
    it('should initialize with default config', () => {
      const tracker = new ErrorTracker();
      const stats = tracker.getStats();
      
      expect(stats.isInitialized).toBe(true);
      expect(stats.sessionId).toBeTruthy();
      
      tracker.destroy();
    });

    it('should not initialize when disabled', () => {
      const tracker = new ErrorTracker({ enabled: false });
      const stats = tracker.getStats();
      
      expect(stats.isInitialized).toBe(false);
      
      tracker.destroy();
    });
  });

  describe('Error Capture', () => {
    it('should capture basic error', () => {
      const testError = new Error('Test error message');
      const errorId = errorTracker.captureError(testError);
      
      expect(errorId).toBeTruthy();
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'error_captured',
        expect.objectContaining({
          errorId,
          errorName: 'Error',
          errorMessage: 'Test error message',
          severity: 'low',
          url: 'https://example.com/test',
          userAgent: 'Mozilla/5.0 (Test Browser)',
        }),
        undefined
      );
    });

    it('should capture error with context', () => {
      const testError = new Error('Component error');
      const context = {
        componentName: 'TestComponent',
        componentProps: { prop1: 'value1' },
        correlationId: 'test-correlation-123',
      };
      
      const errorId = errorTracker.captureError(testError, context);
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'error_captured',
        expect.objectContaining({
          errorId,
          componentName: 'TestComponent',
        }),
        'test-correlation-123'
      );
    });

    it('should determine severity correctly', () => {
      // Critical error
      const chunkError = new Error('Loading chunk 1 failed');
      chunkError.name = 'ChunkLoadError';
      errorTracker.captureError(chunkError);
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'error_captured',
        expect.objectContaining({ severity: 'critical' }),
        undefined
      );

      // High severity error
      const chatError = new Error('Chat component error');
      errorTracker.captureError(chatError, { componentName: 'ChatInterface' });
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'error_captured',
        expect.objectContaining({ severity: 'high' }),
        undefined
      );

      // Medium severity error
      const networkError = new Error('Network request failed');
      networkError.name = 'NetworkError';
      errorTracker.captureError(networkError);
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'error_captured',
        expect.objectContaining({ severity: 'medium' }),
        undefined
      );
    });

    it('should generate consistent fingerprints', () => {
      const error1 = new Error('Same error message');
      const error2 = new Error('Same error message');
      
      const id1 = errorTracker.captureError(error1);
      const id2 = errorTracker.captureError(error2);
      
      const calls = mockTelemetryTrack.mock.calls;
      const fingerprint1 = calls.find(call => call[1].errorId === id1)?.[1].fingerprint;
      const fingerprint2 = calls.find(call => call[1].errorId === id2)?.[1].fingerprint;
      
      expect(fingerprint1).toBe(fingerprint2);
    });

    it('should respect sample rate', () => {
      const mathSpy = vi.spyOn(Math, 'random').mockReturnValue(0.8);
      const sampledTracker = new ErrorTracker({ sampleRate: 0.5 });
      
      const testError = new Error('Sampled error');
      const errorId = sampledTracker.captureError(testError);
      
      expect(errorId).toBe(''); // Should be filtered out
      expect(mockTelemetryTrack).not.toHaveBeenCalled();
      
      mathSpy.mockRestore();
      sampledTracker.destroy();
    });

    it('should apply beforeSend hook', () => {
      const beforeSendSpy = vi.fn((report) => {
        report.severity = 'critical';
        return report;
      });
      
      const hookedTracker = new ErrorTracker({ beforeSend: beforeSendSpy });
      
      const testError = new Error('Hooked error');
      hookedTracker.captureError(testError);
      
      expect(beforeSendSpy).toHaveBeenCalled();
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'error_captured',
        expect.objectContaining({ severity: 'critical' }),
        undefined
      );
      
      hookedTracker.destroy();
    });

    it('should filter out errors when beforeSend returns null', () => {
      const beforeSendSpy = vi.fn(() => null);
      const hookedTracker = new ErrorTracker({ beforeSend: beforeSendSpy });
      
      const testError = new Error('Filtered error');
      const errorId = hookedTracker.captureError(testError);
      
      expect(errorId).toBeTruthy(); // ID is still generated
      expect(mockTelemetryTrack).not.toHaveBeenCalled();
      
      hookedTracker.destroy();
    });
  });

  describe('Breadcrumbs', () => {
    it('should add breadcrumbs', () => {
      errorTracker.addBreadcrumb({
        category: 'user',
        message: 'User clicked button',
        level: 'info',
        data: { buttonId: 'submit' }
      });
      
      const stats = errorTracker.getStats();
      expect(stats.breadcrumbCount).toBe(1);
    });

    it('should limit breadcrumb count', () => {
      const limitedTracker = new ErrorTracker({ maxBreadcrumbs: 3 });
      
      for (let i = 0; i < 5; i++) {
        limitedTracker.addBreadcrumb({
          category: 'custom',
          message: `Breadcrumb ${i}`,
          level: 'info'
        });
      }
      
      const stats = limitedTracker.getStats();
      expect(stats.breadcrumbCount).toBe(3);
      
      limitedTracker.destroy();
    });

    it('should include breadcrumbs in error context', () => {
      errorTracker.addBreadcrumb({
        category: 'user',
        message: 'User action before error',
        level: 'info'
      });
      
      const testError = new Error('Error with breadcrumbs');
      errorTracker.captureError(testError);
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith(
        'error_captured',
        expect.objectContaining({
          breadcrumbCount: 1,
        }),
        undefined
      );
    });
  });

  describe('User Context', () => {
    it('should set user context', () => {
      errorTracker.setUser('user-123', { name: 'Test User' });
      
      expect(mockTelemetrySetUserId).toHaveBeenCalledWith('user-123');
      
      const stats = errorTracker.getStats();
      expect(stats.breadcrumbCount).toBe(1); // User identification breadcrumb
    });

    it('should set tags', () => {
      errorTracker.setTag('environment', 'production');
      
      const stats = errorTracker.getStats();
      expect(stats.breadcrumbCount).toBe(1); // Tag breadcrumb
    });

    it('should set context', () => {
      errorTracker.setContext('user', { id: '123', role: 'admin' });
      
      const stats = errorTracker.getStats();
      expect(stats.breadcrumbCount).toBe(1); // Context breadcrumb
    });
  });

  describe('Local Storage', () => {
    it('should store error reports locally', () => {
      const testError = new Error('Stored error');
      errorTracker.captureError(testError);
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'error_reports',
        expect.stringContaining('Stored error')
      );
    });

    it('should retrieve stored reports', () => {
      const mockReports = [
        { id: '1', error: { name: 'Error', message: 'Test' } }
      ];
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockReports));
      
      const storedReports = errorTracker.getStoredReports();
      expect(storedReports).toEqual(mockReports);
    });

    it('should clear stored reports', () => {
      errorTracker.clearStoredReports();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('error_reports');
    });

    it('should handle localStorage errors gracefully', () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage quota exceeded');
      });
      
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      const testError = new Error('Storage error test');
      errorTracker.captureError(testError);
      
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to store error report locally:',
        expect.any(Error)
      );
      
      consoleSpy.mockRestore();
    });
  });

  describe('Remote Endpoint', () => {
    it('should send error reports to endpoint', async () => {
      const endpointTracker = new ErrorTracker({
        endpoint: 'https://api.example.com/errors',
        apiKey: 'test-api-key',
        environment: 'test',
        release: '1.0.0',
      });
      
      const testError = new Error('Remote error');
      endpointTracker.captureError(testError);
      
      // Wait for async operation
      await new Promise(resolve => setTimeout(resolve, 0));
      
      expect(fetchMock).toHaveBeenCalledWith(
        'https://api.example.com/errors',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-api-key',
          }),
          body: expect.stringContaining('Remote error'),
        })
      );
      
      endpointTracker.destroy();
    });

    it('should handle endpoint errors gracefully', async () => {
      fetchMock.mockRejectedValueOnce(new Error('Network error'));
      
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const endpointTracker = new ErrorTracker({
        endpoint: 'https://api.example.com/errors',
      });
      
      const testError = new Error('Endpoint error test');
      endpointTracker.captureError(testError);
      
      // Wait for async operation
      await new Promise(resolve => setTimeout(resolve, 0));
      
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to send error report to endpoint:',
        expect.any(Error)
      );
      
      endpointTracker.destroy();
      consoleSpy.mockRestore();
    });
  });

  describe('Global Error Handlers', () => {
    it('should setup global error handlers', () => {
      const addEventListenerSpy = vi.spyOn(window, 'addEventListener');
      
      const tracker = new ErrorTracker();
      
      expect(addEventListenerSpy).toHaveBeenCalledWith('error', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('error', expect.any(Function), true);
      expect(addEventListenerSpy).toHaveBeenCalledWith('unhandledrejection', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));
      
      tracker.destroy();
      addEventListenerSpy.mockRestore();
    });
  });

  describe('Stack Trace Sanitization', () => {
    it('should sanitize long stack traces', () => {
      const longStackTrace = 'a'.repeat(15000);
      const testError = new Error('Long stack error');
      testError.stack = longStackTrace;
      
      const limitedTracker = new ErrorTracker({ maxStackTraceLength: 1000 });
      limitedTracker.captureError(testError);
      
      // Check that the stored report has truncated stack
      const storedReports = limitedTracker.getStoredReports();
      expect(storedReports[0].error.stack).toContain('... (truncated)');
      expect(storedReports[0].error.stack!.length).toBeLessThan(1100);
      
      limitedTracker.destroy();
    });
  });

  describe('Cleanup', () => {
    it('should clear breadcrumbs', () => {
      errorTracker.addBreadcrumb({
        category: 'custom',
        message: 'Test breadcrumb',
        level: 'info'
      });
      
      expect(errorTracker.getStats().breadcrumbCount).toBe(1);
      
      errorTracker.clearBreadcrumbs();
      
      expect(errorTracker.getStats().breadcrumbCount).toBe(0);
    });

    it('should destroy properly', () => {
      errorTracker.addBreadcrumb({
        category: 'custom',
        message: 'Test breadcrumb',
        level: 'info'
      });
      
      errorTracker.destroy();
      
      const stats = errorTracker.getStats();
      expect(stats.breadcrumbCount).toBe(0);
      expect(stats.isInitialized).toBe(false);
    });
  });

  describe('Singleton Pattern', () => {
    it('should return same instance from getErrorTracker', () => {
      const instance1 = getErrorTracker();
      const instance2 = getErrorTracker();
      
      expect(instance1).toBe(instance2);
    });

    it('should use convenience functions', () => {
      const tracker = getErrorTracker();
      const captureErrorSpy = vi.spyOn(tracker, 'captureError');
      const addBreadcrumbSpy = vi.spyOn(tracker, 'addBreadcrumb');
      const setUserSpy = vi.spyOn(tracker, 'setUser');
      const setTagSpy = vi.spyOn(tracker, 'setTag');
      const setContextSpy = vi.spyOn(tracker, 'setContext');
      
      const testError = new Error('Convenience test');
      captureError(testError, { componentName: 'Test' });
      addBreadcrumb({ category: 'custom', message: 'Test', level: 'info' });
      setUser('user-123');
      setTag('env', 'test');
      setContext('test', { key: 'value' });
      
      expect(captureErrorSpy).toHaveBeenCalledWith(testError, { componentName: 'Test' });
      expect(addBreadcrumbSpy).toHaveBeenCalledWith({ category: 'custom', message: 'Test', level: 'info' });
      expect(setUserSpy).toHaveBeenCalledWith('user-123');
      expect(setTagSpy).toHaveBeenCalledWith('env', 'test');
      expect(setContextSpy).toHaveBeenCalledWith('test', { key: 'value' });
      
      captureErrorSpy.mockRestore();
      addBreadcrumbSpy.mockRestore();
      setUserSpy.mockRestore();
      setTagSpy.mockRestore();
      setContextSpy.mockRestore();
    });
  });
});