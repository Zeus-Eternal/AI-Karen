import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { 
  PerformanceMonitor, 
  checkPerformanceBudget,
  PERFORMANCE_THRESHOLDS 
} from '../performance-monitor';

// Mock performance API
const mockPerformance = {
  now: vi.fn(() => 1000),
  mark: vi.fn(),
  measure: vi.fn(),
  getEntriesByName: vi.fn(() => [{ duration: 100 }]),
  getEntriesByType: vi.fn(() => []),
  clearMarks: vi.fn(),
  clearMeasures: vi.fn(),
};

const mockPerformanceObserver = vi.fn();
mockPerformanceObserver.prototype.observe = vi.fn();
mockPerformanceObserver.prototype.disconnect = vi.fn();

// Mock window and performance APIs
Object.defineProperty(global, 'performance', {
  writable: true,
  value: mockPerformance,
});

Object.defineProperty(global, 'PerformanceObserver', {
  writable: true,
  value: mockPerformanceObserver,
});

Object.defineProperty(global, 'requestAnimationFrame', {
  writable: true,
  value: vi.fn((callback) => setTimeout(callback, 16)),
});

describe('PerformanceMonitor', () => {
  let monitor: PerformanceMonitor;
  let reportCallback: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    reportCallback = vi.fn();
    monitor = new PerformanceMonitor(reportCallback);
  });

  afterEach(() => {
    monitor.stopMonitoring();
  });

  describe('basic functionality', () => {
    it('should create a performance monitor instance', () => {
      expect(monitor).toBeInstanceOf(PerformanceMonitor);
    });

    it('should start and stop monitoring', () => {
      monitor.startMonitoring();
      expect(mockPerformanceObserver).toHaveBeenCalled();

      monitor.stopMonitoring();
      expect(mockPerformanceObserver.prototype.disconnect).toHaveBeenCalled();
    });

    it('should not start monitoring multiple times', () => {
      monitor.startMonitoring();
      monitor.startMonitoring();
      
      // Should only create observers once
      expect(mockPerformanceObserver).toHaveBeenCalledTimes(4); // 4 different entry types
    });
  });

  describe('metric recording', () => {
    it('should record custom metrics', () => {
      monitor.recordMetric('test-metric', 100, { type: 'test' });
      
      const metrics = monitor.getMetricsByName('test-metric');
      expect(metrics).toHaveLength(1);
      expect(metrics[0].name).toBe('test-metric');
      expect(metrics[0].value).toBe(100);
      expect(metrics[0].metadata).toEqual({ type: 'test' });
    });

    it('should call report callback when recording metrics', () => {
      monitor.recordMetric('callback-test', 50);
      
      expect(reportCallback).toHaveBeenCalledWith({
        name: 'callback-test',
        value: 50,
        timestamp: expect.any(Number),
      });
    });

    it('should store multiple metrics with the same name', () => {
      monitor.recordMetric('multi-metric', 100);
      monitor.recordMetric('multi-metric', 200);
      monitor.recordMetric('multi-metric', 300);
      
      const metrics = monitor.getMetricsByName('multi-metric');
      expect(metrics).toHaveLength(3);
      expect(metrics.map(m => m.value)).toEqual([100, 200, 300]);
    });
  });

  describe('function measurement', () => {
    it('should measure synchronous function execution', () => {
      mockPerformance.now
        .mockReturnValueOnce(1000) // start
        .mockReturnValueOnce(1100); // end

      const testFn = vi.fn(() => 'result');
      const result = monitor.measureFunction('sync-test', testFn);
      
      expect(result).toBe('result');
      expect(testFn).toHaveBeenCalled();
      
      const metrics = monitor.getMetricsByName('sync-test');
      expect(metrics).toHaveLength(1);
      expect(metrics[0].value).toBe(100);
    });

    it('should measure asynchronous function execution', async () => {
      mockPerformance.now
        .mockReturnValueOnce(1000) // start
        .mockReturnValueOnce(1150); // end

      const asyncFn = vi.fn(async () => {
        await new Promise(resolve => setTimeout(resolve, 10));
        return 'async-result';
      });

      const result = await monitor.measureAsyncFunction('async-test', asyncFn);
      
      expect(result).toBe('async-result');
      expect(asyncFn).toHaveBeenCalled();
      
      const metrics = monitor.getMetricsByName('async-test');
      expect(metrics).toHaveLength(1);
      expect(metrics[0].value).toBe(150);
    });
  });

  describe('performance marks and measures', () => {
    it('should create performance marks and measures', () => {
      monitor.startMeasure('mark-test');
      monitor.endMeasure('mark-test', { type: 'mark' });
      
      expect(mockPerformance.mark).toHaveBeenCalledWith('mark-test-start');
      expect(mockPerformance.mark).toHaveBeenCalledWith('mark-test-end');
      expect(mockPerformance.measure).toHaveBeenCalledWith(
        'mark-test-measure',
        'mark-test-start',
        'mark-test-end'
      );
      
      const metrics = monitor.getMetricsByName('mark-test');
      expect(metrics).toHaveLength(1);
      expect(metrics[0].value).toBe(100); // from mock getEntriesByName
    });

    it('should clean up marks and measures', () => {
      monitor.startMeasure('cleanup-test');
      monitor.endMeasure('cleanup-test');
      
      expect(mockPerformance.clearMarks).toHaveBeenCalledWith('cleanup-test-start');
      expect(mockPerformance.clearMarks).toHaveBeenCalledWith('cleanup-test-end');
      expect(mockPerformance.clearMeasures).toHaveBeenCalledWith('cleanup-test-measure');
    });
  });

  describe('performance summary', () => {
    beforeEach(() => {
      // Mock performance entries
      mockPerformance.getEntriesByType.mockImplementation((type) => {
        if (type === 'resource') {
          return [
            {
              name: 'script.js',
              initiatorType: 'script',
              startTime: 100,
              responseEnd: 300,
              transferSize: 1024,
            },
            {
              name: 'style.css',
              initiatorType: 'css',
              startTime: 150,
              responseEnd: 250,
              transferSize: 512,
            },
          ];
        }
        if (type === 'navigation') {
          return [
            {
              startTime: 0,
              loadEventEnd: 2000,
              domainLookupStart: 10,
              domainLookupEnd: 50,
              connectStart: 60,
              connectEnd: 100,
              requestStart: 110,
              responseStart: 200,
              domContentLoadedEventEnd: 1500,
            },
          ];
        }
        return [];
      });
    });

    it('should generate performance summary', () => {
      monitor.recordMetric('test-metric-1', 100);
      monitor.recordMetric('test-metric-1', 200);
      monitor.recordMetric('test-metric-2', 50);
      
      const summary = monitor.getPerformanceSummary();
      
      expect(summary).toHaveProperty('webVitals');
      expect(summary).toHaveProperty('customMetrics');
      expect(summary).toHaveProperty('resourceTiming');
      expect(summary).toHaveProperty('navigationTiming');
      
      // Check custom metrics summary
      expect(summary.customMetrics['test-metric-1']).toEqual({
        count: 2,
        min: 100,
        max: 200,
        avg: 150,
        p95: 200,
        latest: expect.objectContaining({ value: 200 }),
      });
    });

    it('should summarize resource timing', () => {
      const summary = monitor.getPerformanceSummary();
      
      expect(summary.resourceTiming.totalResources).toBe(2);
      expect(summary.resourceTiming.totalSize).toBe(1536); // 1024 + 512
      expect(summary.resourceTiming.byType.script).toEqual({
        count: 1,
        totalSize: 1024,
        totalLoadTime: 200,
        avgLoadTime: 200,
      });
    });

    it('should summarize navigation timing', () => {
      const summary = monitor.getPerformanceSummary();
      
      expect(summary.navigationTiming).toEqual({
        totalTime: 2000,
        dnsTime: 40, // 50 - 10
        connectTime: 40, // 100 - 60
        ttfb: 90, // 200 - 110
        domContentLoaded: 1500,
        loadComplete: 2000,
      });
    });
  });

  describe('percentile calculation', () => {
    it('should calculate percentiles correctly', () => {
      const values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
      
      // Add metrics to test percentile calculation
      values.forEach(value => {
        monitor.recordMetric('percentile-test', value);
      });
      
      const summary = monitor.getPerformanceSummary();
      const metricSummary = summary.customMetrics['percentile-test'];
      
      expect(metricSummary.p95).toBe(100); // 95th percentile should be 100
      expect(metricSummary.min).toBe(10);
      expect(metricSummary.max).toBe(100);
      expect(metricSummary.avg).toBe(55);
    });
  });
});

describe('checkPerformanceBudget', () => {
  it('should check Web Vitals budget correctly', () => {
    const goodLCP = { name: 'LCP' as const, value: 2000 };
    const poorLCP = { name: 'LCP' as const, value: 5000 };
    const warningLCP = { name: 'LCP' as const, value: 3000 };
    
    expect(checkPerformanceBudget(goodLCP)).toEqual({
      withinBudget: true,
      rating: 'good',
      threshold: PERFORMANCE_THRESHOLDS.LCP,
    });
    
    expect(checkPerformanceBudget(poorLCP)).toEqual({
      withinBudget: false,
      rating: 'poor',
      threshold: PERFORMANCE_THRESHOLDS.LCP,
    });
    
    expect(checkPerformanceBudget(warningLCP)).toEqual({
      withinBudget: false,
      rating: 'needs-improvement',
      threshold: PERFORMANCE_THRESHOLDS.LCP,
    });
  });

  it('should handle unknown metrics', () => {
    const unknownMetric = { name: 'unknown-metric', value: 100 };
    
    expect(checkPerformanceBudget(unknownMetric)).toEqual({
      withinBudget: true,
      rating: 'good',
      threshold: null,
    });
  });

  it('should check custom metric budgets', () => {
    const goodAnimation = { name: 'ANIMATION_FRAME_TIME', value: 10 };
    const poorAnimation = { name: 'ANIMATION_FRAME_TIME', value: 40 };
    
    expect(checkPerformanceBudget(goodAnimation)).toEqual({
      withinBudget: true,
      rating: 'good',
      threshold: PERFORMANCE_THRESHOLDS.ANIMATION_FRAME_TIME,
    });
    
    expect(checkPerformanceBudget(poorAnimation)).toEqual({
      withinBudget: false,
      rating: 'poor',
      threshold: PERFORMANCE_THRESHOLDS.ANIMATION_FRAME_TIME,
    });
  });
});

describe('PERFORMANCE_THRESHOLDS', () => {
  it('should have correct threshold values', () => {
    expect(PERFORMANCE_THRESHOLDS.LCP).toEqual({ good: 2500, poor: 4000 });
    expect(PERFORMANCE_THRESHOLDS.FID).toEqual({ good: 100, poor: 300 });
    expect(PERFORMANCE_THRESHOLDS.CLS).toEqual({ good: 0.1, poor: 0.25 });
    expect(PERFORMANCE_THRESHOLDS.FCP).toEqual({ good: 1800, poor: 3000 });
    expect(PERFORMANCE_THRESHOLDS.TTFB).toEqual({ good: 800, poor: 1800 });
  });

  it('should have custom thresholds', () => {
    expect(PERFORMANCE_THRESHOLDS.ANIMATION_FRAME_TIME).toEqual({ good: 16, poor: 32 });
    expect(PERFORMANCE_THRESHOLDS.BUNDLE_LOAD_TIME).toEqual({ good: 1000, poor: 3000 });
    expect(PERFORMANCE_THRESHOLDS.ROUTE_CHANGE_TIME).toEqual({ good: 200, poor: 500 });
  });
});