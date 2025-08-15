import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import PerformanceMonitor, { 
  getPerformanceMonitor, 
  markTTI, 
  markFirstToken, 
  markStreamComplete, 
  measureLatency, 
  getPerformanceMetrics 
} from '../performanceMonitoring';
import { getTelemetryService } from '../telemetry';

// Mock telemetry service
vi.mock('../telemetry', () => ({
  getTelemetryService: vi.fn(() => ({
    track: vi.fn(),
  })),
}));

// Mock PerformanceObserver
const mockPerformanceObserver = vi.fn();
const mockObserve = vi.fn();
const mockDisconnect = vi.fn();

mockPerformanceObserver.mockImplementation((callback) => ({
  observe: mockObserve,
  disconnect: mockDisconnect,
}));

Object.defineProperty(global, 'PerformanceObserver', {
  value: mockPerformanceObserver,
  writable: true,
});

// Mock performance API
const mockPerformance = {
  now: vi.fn(() => 1000),
  mark: vi.fn(),
  measure: vi.fn(),
  clearMarks: vi.fn(),
  clearMeasures: vi.fn(),
  getEntriesByType: vi.fn(() => []),
  memory: {
    usedJSHeapSize: 1000000,
    totalJSHeapSize: 2000000,
    jsHeapSizeLimit: 4000000,
  },
};

Object.defineProperty(global, 'performance', {
  value: mockPerformance,
  writable: true,
});

// Mock document
Object.defineProperty(global, 'document', {
  value: {
    addEventListener: vi.fn(),
    visibilityState: 'visible',
  },
  writable: true,
});

describe('PerformanceMonitor', () => {
  let performanceMonitor: PerformanceMonitor;
  let mockTelemetryTrack: any;

  beforeEach(() => {
    vi.clearAllMocks();
    mockTelemetryTrack = vi.fn();
    (getTelemetryService as any).mockReturnValue({
      track: mockTelemetryTrack,
    });
    
    performanceMonitor = new PerformanceMonitor();
  });

  afterEach(() => {
    performanceMonitor.destroy();
  });

  describe('Initialization', () => {
    it('should initialize performance observer', () => {
      expect(mockPerformanceObserver).toHaveBeenCalled();
      expect(mockObserve).toHaveBeenCalledWith({
        entryTypes: ['navigation', 'paint', 'largest-contentful-paint', 'first-input', 'layout-shift', 'measure', 'mark']
      });
    });

    it('should handle missing PerformanceObserver gracefully', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      // Temporarily remove PerformanceObserver
      const originalPO = global.PerformanceObserver;
      delete (global as any).PerformanceObserver;
      
      const monitor = new PerformanceMonitor();
      
      expect(consoleSpy).toHaveBeenCalledWith('PerformanceObserver not supported');
      
      // Restore
      global.PerformanceObserver = originalPO;
      monitor.destroy();
      consoleSpy.mockRestore();
    });
  });

  describe('Performance Entry Handling', () => {
    it('should handle navigation entries', () => {
      const callback = mockPerformanceObserver.mock.calls[0][0];
      const mockNavigationEntry = {
        entryType: 'navigation',
        domContentLoadedEventEnd: 2000,
        domContentLoadedEventStart: 1500,
        loadEventEnd: 3000,
        loadEventStart: 2500,
        domInteractive: 1800,
        navigationStart: 1000,
        redirectEnd: 1100,
        redirectStart: 1050,
        domainLookupEnd: 1200,
        domainLookupStart: 1150,
        connectEnd: 1300,
        connectStart: 1250,
        responseEnd: 1600,
        requestStart: 1400,
        responseStart: 1550,
        domComplete: 2200,
        domLoading: 1700,
      };

      callback({
        getEntries: () => [mockNavigationEntry]
      });

      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_navigation', {
        domContentLoaded: 500,
        loadComplete: 500,
        domInteractive: 800,
        redirectTime: 50,
        dnsTime: 50,
        connectTime: 50,
        requestTime: 200,
        responseTime: 50,
        renderTime: 500,
      });
    });

    it('should handle paint entries', () => {
      const callback = mockPerformanceObserver.mock.calls[0][0];
      const mockPaintEntry = {
        entryType: 'paint',
        name: 'first-contentful-paint',
        startTime: 1500,
        duration: 0,
      };

      callback({
        getEntries: () => [mockPaintEntry]
      });

      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_paint', {
        name: 'first-contentful-paint',
        startTime: 1500,
        duration: 0,
      });
    });

    it('should handle LCP entries', () => {
      const callback = mockPerformanceObserver.mock.calls[0][0];
      const mockLCPEntry = {
        entryType: 'largest-contentful-paint',
        startTime: 2000,
        size: 1000,
        element: { tagName: 'IMG' },
      };

      callback({
        getEntries: () => [mockLCPEntry]
      });

      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_lcp', {
        startTime: 2000,
        renderTime: 2000,
        size: 1000,
        element: 'IMG',
      });
    });

    it('should handle FID entries', () => {
      const callback = mockPerformanceObserver.mock.calls[0][0];
      const mockFIDEntry = {
        entryType: 'first-input',
        startTime: 1500,
        duration: 100,
        processingStart: 1520,
        processingEnd: 1580,
      };

      callback({
        getEntries: () => [mockFIDEntry]
      });

      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_fid', {
        startTime: 1500,
        processingStart: 1520,
        processingEnd: 1580,
        duration: 100,
        delay: 20,
      });
    });

    it('should handle CLS entries', () => {
      const callback = mockPerformanceObserver.mock.calls[0][0];
      const mockCLSEntry = {
        entryType: 'layout-shift',
        startTime: 1500,
        value: 0.1,
        hadRecentInput: false,
        sources: [
          {
            node: { tagName: 'DIV' },
            currentRect: { x: 0, y: 0, width: 100, height: 100 },
            previousRect: { x: 0, y: 50, width: 100, height: 100 },
          }
        ],
      };

      callback({
        getEntries: () => [mockCLSEntry]
      });

      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_cls', {
        startTime: 1500,
        value: 0.1,
        sources: [
          {
            node: 'DIV',
            currentRect: { x: 0, y: 0, width: 100, height: 100 },
            previousRect: { x: 0, y: 50, width: 100, height: 100 },
          }
        ],
      });
    });

    it('should ignore CLS entries with recent input', () => {
      const callback = mockPerformanceObserver.mock.calls[0][0];
      const mockCLSEntry = {
        entryType: 'layout-shift',
        startTime: 1500,
        value: 0.1,
        hadRecentInput: true,
      };

      callback({
        getEntries: () => [mockCLSEntry]
      });

      expect(mockTelemetryTrack).not.toHaveBeenCalledWith('performance_cls', expect.any(Object));
    });
  });

  describe('Custom Marks', () => {
    it('should create TTI mark', () => {
      performanceMonitor.markTTI();

      expect(mockPerformance.mark).toHaveBeenCalledWith('tti');
      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_mark', {
        name: 'tti',
        startTime: 1000,
        metadata: { type: 'time_to_interactive' },
      });
    });

    it('should create first token mark', () => {
      performanceMonitor.markFirstToken();

      expect(mockPerformance.mark).toHaveBeenCalledWith('first_token');
      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_mark', {
        name: 'first_token',
        startTime: 1000,
        metadata: { type: 'ai_response_start' },
      });
    });

    it('should create stream complete mark', () => {
      performanceMonitor.markStreamComplete();

      expect(mockPerformance.mark).toHaveBeenCalledWith('stream_complete');
      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_mark', {
        name: 'stream_complete',
        startTime: 1000,
        metadata: { type: 'ai_response_complete' },
      });
    });

    it('should create custom marks', () => {
      performanceMonitor.mark('custom_mark', { custom: 'data' });

      expect(mockPerformance.mark).toHaveBeenCalledWith('custom_mark');
      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_mark', {
        name: 'custom_mark',
        startTime: 1000,
        metadata: { custom: 'data' },
      });
    });
  });

  describe('Measurements', () => {
    it('should measure between marks', () => {
      performanceMonitor.mark('start_mark');
      mockPerformance.now.mockReturnValue(2000);
      performanceMonitor.mark('end_mark');

      const duration = performanceMonitor.measure('test_measure', 'start_mark', 'end_mark');

      expect(duration).toBe(1000);
      expect(mockPerformance.measure).toHaveBeenCalledWith('test_measure', 'start_mark', 'end_mark');
      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_measure', {
        name: 'test_measure',
        startMark: 'start_mark',
        endMark: 'end_mark',
        duration: 1000,
        startTime: 1000,
        endTime: 2000,
      });
    });

    it('should measure from mark to now', () => {
      performanceMonitor.mark('start_mark');
      mockPerformance.now.mockReturnValue(2000);

      const duration = performanceMonitor.measure('test_measure', 'start_mark');

      expect(duration).toBe(1000);
      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_measure', {
        name: 'test_measure',
        startMark: 'start_mark',
        endMark: undefined,
        duration: 1000,
        startTime: 1000,
        endTime: 2000,
      });
    });

    it('should handle missing start mark', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const duration = performanceMonitor.measure('test_measure', 'missing_mark');

      expect(duration).toBe(0);
      expect(consoleSpy).toHaveBeenCalledWith('Start mark "missing_mark" not found');

      consoleSpy.mockRestore();
    });

    it('should handle missing end mark', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      performanceMonitor.mark('start_mark');
      const duration = performanceMonitor.measure('test_measure', 'start_mark', 'missing_end');

      expect(duration).toBe(0);
      expect(consoleSpy).toHaveBeenCalledWith('End mark "missing_end" not found');

      consoleSpy.mockRestore();
    });

    it('should measure latency', () => {
      performanceMonitor.mark('request_start');
      mockPerformance.now.mockReturnValue(2000);

      const latency = performanceMonitor.measureLatency('request_start');

      expect(latency).toBe(1000);
      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_measure', 
        expect.objectContaining({
          name: 'request_start_latency',
          startMark: 'request_start',
        })
      );
    });
  });

  describe('Metrics Collection', () => {
    it('should collect performance metrics', () => {
      // Mock paint entries
      mockPerformance.getEntriesByType.mockImplementation((type) => {
        if (type === 'paint') {
          return [{ name: 'first-contentful-paint', startTime: 1500 }];
        }
        if (type === 'largest-contentful-paint') {
          return [{ startTime: 2000 }, { startTime: 2500 }];
        }
        return [];
      });

      // Create some marks
      performanceMonitor.markTTI();
      performanceMonitor.markFirstToken();
      performanceMonitor.markStreamComplete();

      const metrics = performanceMonitor.getMetrics();

      expect(metrics).toEqual({
        fcp: 1500,
        lcp: 2500,
        tti: 1000,
        firstToken: 1000,
        streamComplete: 1000,
        memoryUsage: 1000000,
      });
    });

    it('should handle missing performance entries', () => {
      mockPerformance.getEntriesByType.mockReturnValue([]);

      const metrics = performanceMonitor.getMetrics();

      expect(metrics).toEqual({
        memoryUsage: 1000000,
      });
    });
  });

  describe('Memory Monitoring', () => {
    it('should track memory usage periodically', () => {
      vi.useFakeTimers();
      
      // Create new monitor to trigger memory monitoring setup
      const monitor = new PerformanceMonitor();
      
      // Fast forward 30 seconds
      vi.advanceTimersByTime(30000);
      
      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_memory', {
        usedJSHeapSize: 1000000,
        totalJSHeapSize: 2000000,
        jsHeapSizeLimit: 4000000,
        memoryUsagePercent: 25,
      });
      
      monitor.destroy();
      vi.useRealTimers();
    });
  });

  describe('Bundle Size Tracking', () => {
    it('should track bundle size from resources', () => {
      const mockResources = [
        { name: 'app.js', transferSize: 100000 },
        { name: 'vendor.js', transferSize: 200000 },
        { name: 'styles.css', transferSize: 50000 },
        { name: 'image.png', transferSize: 75000 },
      ];

      mockPerformance.getEntriesByType.mockImplementation((type) => {
        if (type === 'resource') {
          return mockResources;
        }
        return [];
      });

      // Create new monitor to trigger bundle size tracking
      const monitor = new PerformanceMonitor();

      expect(mockTelemetryTrack).toHaveBeenCalledWith('performance_bundle_size', {
        totalSize: 425000,
        jsSize: 300000,
        cssSize: 50000,
        resourceCount: 4,
      });

      monitor.destroy();
    });
  });

  describe('Cleanup', () => {
    it('should clear marks and measures', () => {
      performanceMonitor.clearMarks();

      expect(mockPerformance.clearMarks).toHaveBeenCalled();
      expect(mockPerformance.clearMeasures).toHaveBeenCalled();
    });

    it('should destroy properly', () => {
      performanceMonitor.destroy();

      expect(mockDisconnect).toHaveBeenCalled();
      expect(mockPerformance.clearMarks).toHaveBeenCalled();
      expect(mockPerformance.clearMeasures).toHaveBeenCalled();
    });
  });

  describe('Singleton Pattern', () => {
    it('should return same instance from getPerformanceMonitor', () => {
      const instance1 = getPerformanceMonitor();
      const instance2 = getPerformanceMonitor();

      expect(instance1).toBe(instance2);
    });

    it('should use convenience functions', () => {
      const monitor = getPerformanceMonitor();
      const markTTISpy = vi.spyOn(monitor, 'markTTI');
      const markFirstTokenSpy = vi.spyOn(monitor, 'markFirstToken');
      const markStreamCompleteSpy = vi.spyOn(monitor, 'markStreamComplete');
      const measureLatencySpy = vi.spyOn(monitor, 'measureLatency');
      const getMetricsSpy = vi.spyOn(monitor, 'getMetrics');

      markTTI();
      markFirstToken();
      markStreamComplete();
      measureLatency('start', 'end');
      getPerformanceMetrics();

      expect(markTTISpy).toHaveBeenCalled();
      expect(markFirstTokenSpy).toHaveBeenCalled();
      expect(markStreamCompleteSpy).toHaveBeenCalled();
      expect(measureLatencySpy).toHaveBeenCalledWith('start', 'end');
      expect(getMetricsSpy).toHaveBeenCalled();

      markTTISpy.mockRestore();
      markFirstTokenSpy.mockRestore();
      markStreamCompleteSpy.mockRestore();
      measureLatencySpy.mockRestore();
      getMetricsSpy.mockRestore();
    });
  });
});