/**
 * Performance Monitor Service Tests
 * Tests for comprehensive performance monitoring functionality
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { PerformanceMonitor } from '../performance-monitor';

// Mock web-vitals
vi.mock('web-vitals', () => ({
  getCLS: vi.fn(),
  getFCP: vi.fn(),
  getFID: vi.fn(),
  getLCP: vi.fn(),
  getTTFB: vi.fn(),
}));

// Mock performance API
const mockPerformance = {
  now: vi.fn(() => Date.now()),
  memory: {
    usedJSHeapSize: 50000000,
    totalJSHeapSize: 100000000,
  },
};

const mockNavigator = {
  connection: {
    downlink: 10,
    effectiveType: '4g',
    rtt: 50,
  },
};

// Mock PerformanceObserver
class MockPerformanceObserver {
  private callback: (list: any) => void;
  
  constructor(callback: (list: any) => void) {
    this.callback = callback;
  }
  
  observe() {}
  disconnect() {}
}

describe('PerformanceMonitor', () => {
  let monitor: PerformanceMonitor;
  let alertCallback: Mock;

  beforeEach(() => {
    // Setup global mocks
    global.performance = mockPerformance as any;
    global.navigator = mockNavigator as any;
    global.PerformanceObserver = MockPerformanceObserver as any;
    global.Date.now = vi.fn(() => 1000000);

    alertCallback = vi.fn();
    monitor = new PerformanceMonitor({
      lcp: { warning: 2000, critical: 3000 },
      fid: { warning: 80, critical: 200 },
      memoryUsage: { warning: 70, critical: 90 },
      pageLoad: { warning: 2000, critical: 3000 },


  afterEach(() => {
    monitor.destroy();
    vi.clearAllMocks();

  describe('Initialization', () => {
    it('should initialize with default thresholds', () => {
      const defaultMonitor = new PerformanceMonitor();
      expect(defaultMonitor).toBeDefined();
      defaultMonitor.destroy();

    it('should initialize with custom thresholds', () => {
      const customThresholds = {
        lcp: { warning: 1500, critical: 2500 },
        fid: { warning: 50, critical: 150 },
      };
      
      const customMonitor = new PerformanceMonitor(customThresholds);
      expect(customMonitor).toBeDefined();
      customMonitor.destroy();


  describe('Metric Recording', () => {
    it('should record page load metrics', () => {
      monitor.trackPageLoad('/dashboard', 1500);
      
      const metrics = monitor.getMetrics('route-load');
      expect(metrics).toHaveLength(1);
      expect(metrics[0].name).toBe('route-load');
      expect(metrics[0].metadata?.route).toBe('/dashboard');

    it('should record user interaction metrics', () => {
      monitor.trackUserInteraction('button-click', 50, { component: 'submit-btn' });
      
      const metrics = monitor.getMetrics('user-interaction');
      expect(metrics).toHaveLength(1);
      expect(metrics[0].value).toBe(50);
      expect(metrics[0].metadata?.action).toBe('button-click');
      expect(metrics[0].metadata?.component).toBe('submit-btn');

    it('should record API call metrics', () => {
      monitor.trackAPICall('/api/users', 250, 200, { method: 'GET' });
      
      const metrics = monitor.getMetrics('api-call');
      expect(metrics).toHaveLength(1);
      expect(metrics[0].value).toBe(250);
      expect(metrics[0].metadata?.endpoint).toBe('/api/users');
      expect(metrics[0].metadata?.status).toBe(200);
      expect(metrics[0].metadata?.success).toBe(true);


  describe('Alert System', () => {
    it('should create alerts when thresholds are exceeded', () => {
      monitor.onAlert(alertCallback);
      
      // Trigger a warning alert
      monitor.trackPageLoad('/slow-page', 2500);
      
      expect(alertCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'warning',
          metric: 'pageLoad',
          value: 2500,
        })
      );

    it('should create critical alerts for severe threshold violations', () => {
      monitor.onAlert(alertCallback);
      
      // Trigger a critical alert
      monitor.trackPageLoad('/very-slow-page', 3500);
      
      expect(alertCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'critical',
          metric: 'pageLoad',
          value: 3500,
        })
      );

    it('should not create alerts for values within thresholds', () => {
      monitor.onAlert(alertCallback);
      
      // Track a fast page load
      monitor.trackPageLoad('/fast-page', 1000);
      
      expect(alertCallback).not.toHaveBeenCalled();

    it('should allow unsubscribing from alerts', () => {
      const unsubscribe = monitor.onAlert(alertCallback);
      
      unsubscribe();
      monitor.trackPageLoad('/slow-page', 2500);
      
      expect(alertCallback).not.toHaveBeenCalled();


  describe('Resource Usage Monitoring', () => {
    it('should get current resource usage', () => {
      const usage = monitor.getCurrentResourceUsage();
      
      expect(usage.memory.used).toBe(50000000);
      expect(usage.memory.total).toBe(100000000);
      expect(usage.memory.percentage).toBe(50);
      expect(usage.network.downlink).toBe(10);
      expect(usage.network.effectiveType).toBe('4g');
      expect(usage.network.rtt).toBe(50);

    it('should handle missing performance.memory', () => {
      const originalMemory = global.performance.memory;
      delete (global.performance as any).memory;
      
      const usage = monitor.getCurrentResourceUsage();
      
      expect(usage.memory.used).toBe(0);
      expect(usage.memory.total).toBe(0);
      expect(usage.memory.percentage).toBe(0);
      
      (global.performance as any).memory = originalMemory;

    it('should handle missing navigator.connection', () => {
      const originalConnection = global.navigator.connection;
      delete (global.navigator as any).connection;
      
      const usage = monitor.getCurrentResourceUsage();
      
      expect(usage.network.downlink).toBe(0);
      expect(usage.network.effectiveType).toBe('unknown');
      expect(usage.network.rtt).toBe(0);
      
      (global.navigator as any).connection = originalConnection;


  describe('Web Vitals Integration', () => {
    it('should get Web Vitals metrics', () => {
      // Simulate recording some Web Vitals
      monitor['recordMetric']('lcp', 2000);
      monitor['recordMetric']('fid', 100);
      monitor['recordMetric']('cls', 0.1);
      
      const vitals = monitor.getWebVitalsMetrics();
      
      expect(vitals.lcp).toBe(2000);
      expect(vitals.fid).toBe(100);
      expect(vitals.cls).toBe(0.1);

    it('should return partial metrics when some are missing', () => {
      monitor['recordMetric']('lcp', 1500);
      
      const vitals = monitor.getWebVitalsMetrics();
      
      expect(vitals.lcp).toBe(1500);
      expect(vitals.fid).toBeUndefined();
      expect(vitals.cls).toBeUndefined();


  describe('Metric Retrieval', () => {
    beforeEach(() => {
      // Add some test metrics
      monitor.trackPageLoad('/page1', 1000);
      monitor.trackPageLoad('/page2', 1500);
      monitor.trackUserInteraction('click', 50);
      monitor.trackAPICall('/api/test', 200, 200);

    it('should get all metrics when no type specified', () => {
      const metrics = monitor.getMetrics();
      expect(metrics.length).toBeGreaterThanOrEqual(4);

    it('should filter metrics by type', () => {
      const pageLoadMetrics = monitor.getMetrics('route-load');
      expect(pageLoadMetrics).toHaveLength(2);
      expect(pageLoadMetrics.every(m => m.name === 'route-load')).toBe(true);

    it('should limit metrics when limit specified', () => {
      const limitedMetrics = monitor.getMetrics('route-load', 1);
      expect(limitedMetrics).toHaveLength(1);

    it('should return metrics sorted by timestamp (newest first)', () => {
      const metrics = monitor.getMetrics('route-load');
      expect(metrics[0].timestamp).toBeGreaterThanOrEqual(metrics[1].timestamp);

    it('should get latest metrics for specified types', () => {
      const latestMetrics = monitor.getLatestMetrics(['route-load', 'user-interaction']);
      expect(latestMetrics).toHaveLength(2);
      expect(latestMetrics.some(m => m.name === 'route-load')).toBe(true);
      expect(latestMetrics.some(m => m.name === 'user-interaction')).toBe(true);


  describe('Alert Management', () => {
    beforeEach(() => {
      // Trigger some alerts
      monitor.trackPageLoad('/slow1', 2500); // warning
      monitor.trackPageLoad('/slow2', 3500); // critical
      monitor.trackUserInteraction('slow-click', 250); // critical

    it('should get all alerts', () => {
      const alerts = monitor.getAlerts();
      expect(alerts.length).toBeGreaterThanOrEqual(2);

    it('should limit alerts when limit specified', () => {
      const limitedAlerts = monitor.getAlerts(2);
      expect(limitedAlerts).toHaveLength(2);

    it('should return alerts sorted by timestamp (newest first)', () => {
      const alerts = monitor.getAlerts();
      for (let i = 0; i < alerts.length - 1; i++) {
        expect(alerts[i].timestamp).toBeGreaterThanOrEqual(alerts[i + 1].timestamp);
      }


  describe('Optimization Recommendations', () => {
    it('should provide recommendations for poor LCP', () => {
      monitor['recordMetric']('lcp', 3000);
      
      const recommendations = monitor.getOptimizationRecommendations();
      expect(recommendations.some(r => r.includes('LCP'))).toBe(true);

    it('should provide recommendations for poor FID', () => {
      monitor['recordMetric']('fid', 150);
      
      const recommendations = monitor.getOptimizationRecommendations();
      expect(recommendations.some(r => r.includes('FID'))).toBe(true);

    it('should provide recommendations for poor CLS', () => {
      monitor['recordMetric']('cls', 0.3);
      
      const recommendations = monitor.getOptimizationRecommendations();
      expect(recommendations.some(r => r.includes('CLS'))).toBe(true);

    it('should provide recommendations for high memory usage', () => {
      // Simulate high memory usage
      for (let i = 0; i < 10; i++) {
        monitor['recordMetric']('memory-usage', 85);
      }
      
      const recommendations = monitor.getOptimizationRecommendations();
      expect(recommendations.some(r => r.includes('memory'))).toBe(true);

    it('should return empty recommendations for good performance', () => {
      monitor['recordMetric']('lcp', 1000);
      monitor['recordMetric']('fid', 50);
      monitor['recordMetric']('cls', 0.05);
      monitor['recordMetric']('memory-usage', 30);
      
      const recommendations = monitor.getOptimizationRecommendations();
      expect(recommendations).toHaveLength(0);


  describe('Memory Management', () => {
    it('should clear old metrics', () => {
      // Add metrics with old timestamps
      const oldTimestamp = Date.now() - (25 * 60 * 60 * 1000); // 25 hours ago
      monitor['recordMetric']('old-metric', 100);
      monitor['metrics'][monitor['metrics'].length - 1].timestamp = oldTimestamp;
      
      // Add recent metric
      monitor['recordMetric']('recent-metric', 200);
      
      monitor.clearOldMetrics(24 * 60 * 60 * 1000); // 24 hours
      
      const metrics = monitor.getMetrics();
      expect(metrics.every(m => m.name !== 'old-metric')).toBe(true);
      expect(metrics.some(m => m.name === 'recent-metric')).toBe(true);

    it('should prevent memory leaks by limiting metrics', () => {
      // Add many metrics to trigger cleanup
      for (let i = 0; i < 6000; i++) {
        monitor['recordMetric']('test-metric', i);
      }
      
      const metrics = monitor.getMetrics();
      // Should be significantly less than the total added
      expect(metrics.length).toBeLessThan(6000);
      expect(metrics.length).toBeGreaterThan(2000); // But still have a reasonable amount

    it('should prevent memory leaks by limiting alerts', () => {
      // Trigger many alerts
      for (let i = 0; i < 1200; i++) {
        monitor.trackPageLoad(`/page-${i}`, 3500); // Above critical threshold
      }
      
      const alerts = monitor.getAlerts();
      // Should be significantly less than the total triggered
      expect(alerts.length).toBeLessThan(1200);
      expect(alerts.length).toBeGreaterThan(400); // But still have a reasonable amount


  describe('Cleanup', () => {
    it('should cleanup observers and callbacks on destroy', () => {
      const callback = vi.fn();
      monitor.onAlert(callback);
      
      monitor.destroy();
      
      // Should not receive alerts after destroy
      monitor.trackPageLoad('/test', 3000);
      expect(callback).not.toHaveBeenCalled();


  describe('Error Handling', () => {
    it('should handle PerformanceObserver not being supported', () => {
      const originalPO = global.PerformanceObserver;
      delete (global as any).PerformanceObserver;
      
      expect(() => {
        const testMonitor = new PerformanceMonitor();
        testMonitor.destroy();
      }).not.toThrow();
      
      global.PerformanceObserver = originalPO;

    it('should handle performance.now not being available', () => {
      const originalNow = global.performance.now;
      delete (global.performance as any).now;
      
      expect(() => {
        monitor.trackPageLoad('/test', 1000); // Provide explicit time
      }).not.toThrow();
      
      global.performance.now = originalNow;


