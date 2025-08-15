import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import TelemetryService, { getTelemetryService, track, startSpan, setCorrelationId, setUserId, flushTelemetry } from '../telemetry';

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
  now: vi.fn(() => 1000),
  timeOrigin: 1234567890000,
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

describe('TelemetryService', () => {
  let telemetryService: TelemetryService;

  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
    });
    telemetryService = new TelemetryService({
      enabled: true,
      debug: false,
      flushInterval: 100, // Short interval for testing
      batchSize: 2,
    });
  });

  afterEach(() => {
    telemetryService.destroy();
  });

  describe('Basic Functionality', () => {
    it('should create telemetry service with default config', () => {
      const service = new TelemetryService();
      const stats = service.getStats();
      
      expect(stats.config.enabled).toBe(true);
      expect(stats.config.batchSize).toBe(10);
      expect(stats.sessionId).toBeTruthy();
      expect(stats.correlationId).toBeTruthy();
    });

    it('should track events with proper structure', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const debugService = new TelemetryService({ debug: true });
      
      debugService.track('test_event', { key: 'value' });
      
      expect(consoleSpy).toHaveBeenCalledWith(
        '📊 Telemetry Event:',
        expect.objectContaining({
          event: 'test_event',
          payload: expect.objectContaining({
            key: 'value',
            performanceNow: 1000,
            timeOrigin: 1234567890000,
          }),
          timestamp: expect.any(String),
          sessionId: expect.any(String),
          correlationId: expect.any(String),
        })
      );
      
      debugService.destroy();
      consoleSpy.mockRestore();
    });

    it('should not track events when disabled', () => {
      const disabledService = new TelemetryService({ enabled: false });
      disabledService.track('test_event');
      
      const stats = disabledService.getStats();
      expect(stats.queueSize).toBe(0);
      
      disabledService.destroy();
    });

    it('should respect sampling rate', () => {
      const mathSpy = vi.spyOn(Math, 'random').mockReturnValue(0.8);
      const sampledService = new TelemetryService({ sampling: 0.5 });
      
      sampledService.track('test_event');
      
      const stats = sampledService.getStats();
      expect(stats.queueSize).toBe(0); // Should be filtered out
      
      mathSpy.mockRestore();
      sampledService.destroy();
    });
  });

  describe('Correlation ID Management', () => {
    it('should set and use correlation ID', () => {
      const testCorrelationId = 'test-correlation-123';
      telemetryService.setCorrelationId(testCorrelationId);
      
      const stats = telemetryService.getStats();
      expect(stats.correlationId).toBe(testCorrelationId);
    });

    it('should use custom correlation ID for specific events', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const debugService = new TelemetryService({ debug: true });
      
      const customCorrelationId = 'custom-correlation-456';
      debugService.track('test_event', {}, customCorrelationId);
      
      expect(consoleSpy).toHaveBeenCalledWith(
        '📊 Telemetry Event:',
        expect.objectContaining({
          correlationId: customCorrelationId,
        })
      );
      
      debugService.destroy();
      consoleSpy.mockRestore();
    });
  });

  describe('User ID Management', () => {
    it('should set and retrieve user ID', () => {
      const testUserId = 'user-123';
      telemetryService.setUserId(testUserId);
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('telemetry_user_id', testUserId);
    });

    it('should include user ID in events when available', () => {
      localStorageMock.getItem.mockReturnValue('stored-user-456');
      
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const debugService = new TelemetryService({ debug: true });
      
      debugService.track('test_event');
      
      expect(consoleSpy).toHaveBeenCalledWith(
        '📊 Telemetry Event:',
        expect.objectContaining({
          userId: 'stored-user-456',
        })
      );
      
      debugService.destroy();
      consoleSpy.mockRestore();
    });
  });

  describe('Span Tracking', () => {
    it('should create and end spans properly', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const debugService = new TelemetryService({ debug: true });
      
      const span = debugService.startSpan('test_operation');
      
      expect(consoleSpy).toHaveBeenCalledWith(
        '📊 Telemetry Event:',
        expect.objectContaining({
          event: 'span_start',
          payload: expect.objectContaining({
            spanName: 'test_operation',
            startTime: 1000,
          }),
        })
      );
      
      performanceMock.now.mockReturnValue(2000);
      const duration = span.end();
      
      expect(duration).toBe(1000);
      expect(consoleSpy).toHaveBeenCalledWith(
        '📊 Telemetry Event:',
        expect.objectContaining({
          event: 'span_end',
          payload: expect.objectContaining({
            spanName: 'test_operation',
            duration: 1000,
          }),
        })
      );
      
      debugService.destroy();
      consoleSpy.mockRestore();
    });

    it('should add tags to spans', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const debugService = new TelemetryService({ debug: true });
      
      const span = debugService.startSpan('test_operation');
      span.addTag('userId', '123');
      
      expect(consoleSpy).toHaveBeenCalledWith(
        '📊 Telemetry Event:',
        expect.objectContaining({
          event: 'span_tag',
          payload: expect.objectContaining({
            spanName: 'test_operation',
            tagKey: 'userId',
            tagValue: '123',
          }),
        })
      );
      
      debugService.destroy();
      consoleSpy.mockRestore();
    });
  });

  describe('Local Storage', () => {
    it('should store events locally', async () => {
      telemetryService.track('test_event_1');
      telemetryService.track('test_event_2');
      
      await telemetryService.flush();
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'telemetry_events',
        expect.stringContaining('test_event_1')
      );
    });

    it('should retrieve stored events', () => {
      const mockEvents = [
        { event: 'stored_event', timestamp: '2023-01-01T00:00:00.000Z' }
      ];
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockEvents));
      
      const storedEvents = telemetryService.getStoredEvents();
      expect(storedEvents).toEqual(mockEvents);
    });

    it('should clear stored events', () => {
      telemetryService.clearStoredEvents();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('telemetry_events');
    });

    it('should handle localStorage errors gracefully', () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage quota exceeded');
      });
      
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      telemetryService.track('test_event');
      telemetryService.flush();
      
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to store telemetry events locally:',
        expect.any(Error)
      );
      
      consoleSpy.mockRestore();
    });
  });

  describe('Remote Endpoint', () => {
    it('should send events to remote endpoint', async () => {
      // Reset localStorage mock for this test
      localStorageMock.setItem.mockImplementation(() => {});
      
      const endpointService = new TelemetryService({
        endpoint: 'https://api.example.com/telemetry',
        batchSize: 1,
      });
      
      endpointService.track('test_event');
      await endpointService.flush();
      
      expect(fetchMock).toHaveBeenCalledWith(
        'https://api.example.com/telemetry',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('test_event'),
        })
      );
      
      endpointService.destroy();
    });

    it('should handle endpoint errors with retry', async () => {
      // Reset localStorage mock for this test
      localStorageMock.setItem.mockImplementation(() => {});
      fetchMock.mockRejectedValueOnce(new Error('Network error'));
      
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const endpointService = new TelemetryService({
        endpoint: 'https://api.example.com/telemetry',
        batchSize: 1,
        maxRetries: 1,
      });
      
      endpointService.track('test_event');
      await endpointService.flush();
      
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to send telemetry events:',
        expect.any(Error)
      );
      
      // Should retry
      expect(endpointService.getStats().queueSize).toBe(1);
      
      endpointService.destroy();
      consoleSpy.mockRestore();
    });
  });

  describe('Batch Processing', () => {
    it('should flush when batch size is reached', () => {
      const flushSpy = vi.spyOn(telemetryService, 'flush');
      
      telemetryService.track('event_1');
      expect(flushSpy).not.toHaveBeenCalled();
      
      telemetryService.track('event_2');
      expect(flushSpy).toHaveBeenCalled();
      
      flushSpy.mockRestore();
    });

    it('should flush on timer interval', async () => {
      const flushSpy = vi.spyOn(telemetryService, 'flush');
      
      telemetryService.track('test_event');
      
      // Wait for flush interval
      await new Promise(resolve => setTimeout(resolve, 150));
      
      expect(flushSpy).toHaveBeenCalled();
      
      flushSpy.mockRestore();
    });
  });

  describe('Singleton Pattern', () => {
    it('should return same instance from getTelemetryService', () => {
      const instance1 = getTelemetryService();
      const instance2 = getTelemetryService();
      
      expect(instance1).toBe(instance2);
    });

    it('should use convenience functions', () => {
      // Reset localStorage mock for this test
      localStorageMock.setItem.mockImplementation(() => {});
      
      const trackSpy = vi.spyOn(getTelemetryService(), 'track');
      const spanSpy = vi.spyOn(getTelemetryService(), 'startSpan');
      const correlationSpy = vi.spyOn(getTelemetryService(), 'setCorrelationId');
      const userSpy = vi.spyOn(getTelemetryService(), 'setUserId');
      const flushSpy = vi.spyOn(getTelemetryService(), 'flush');
      
      track('test_event', { key: 'value' });
      startSpan('test_span');
      setCorrelationId('test-correlation');
      setUserId('test-user');
      flushTelemetry();
      
      expect(trackSpy).toHaveBeenCalledWith('test_event', { key: 'value' }, undefined);
      expect(spanSpy).toHaveBeenCalledWith('test_span');
      expect(correlationSpy).toHaveBeenCalledWith('test-correlation');
      expect(userSpy).toHaveBeenCalledWith('test-user');
      expect(flushSpy).toHaveBeenCalled();
      
      trackSpy.mockRestore();
      spanSpy.mockRestore();
      correlationSpy.mockRestore();
      userSpy.mockRestore();
      flushSpy.mockRestore();
    });
  });

  describe('Cleanup', () => {
    it('should destroy properly', () => {
      const flushSpy = vi.spyOn(telemetryService, 'flush');
      
      telemetryService.destroy();
      
      expect(flushSpy).toHaveBeenCalled();
      
      flushSpy.mockRestore();
    });
  });
});