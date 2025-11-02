/**
 * Resource Monitor Tests
 * Tests for resource utilization monitoring and scaling functionality
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { ResourceMonitor } from '../resource-monitor';

// Mock performance API
const mockPerformance = {
  now: vi.fn(() => Date.now()),
  memory: {
    usedJSHeapSize: 50000000,
    totalJSHeapSize: 100000000,
    jsHeapSizeLimit: 200000000,
  },
  getEntriesByType: vi.fn((type) => {
    if (type === 'navigation') {
      return [{
        transferSize: 100000,
        responseStart: 100,
        requestStart: 50,
      }];
    }
    if (type === 'resource') {
      return [
        {
          transferSize: 50000,
          encodedBodySize: 45000,
          responseStart: 150,
          requestStart: 100,
        },
        {
          transferSize: 30000,
          encodedBodySize: 28000,
          responseStart: 200,
          requestStart: 180,
        },
      ];
    }
    if (type === 'longtask') {
      return [
        { startTime: Date.now() - 5000, duration: 100 },
        { startTime: Date.now() - 3000, duration: 150 },
      ];
    }
    return [];
  }),
};

// Mock navigator
const mockNavigator = {
  hardwareConcurrency: 8,
  connection: {
    downlink: 10,
    effectiveType: '4g',
  },
  storage: {
    estimate: vi.fn(() => Promise.resolve({
      usage: 50000000,
      quota: 100000000,
    })),
  },
};

global.performance = mockPerformance as any;
global.navigator = mockNavigator as any;

describe('ResourceMonitor', () => {
  let monitor: ResourceMonitor;
  let alertCallback: Mock;

  beforeEach(() => {
    vi.clearAllMocks();
    alertCallback = vi.fn();
    monitor = new ResourceMonitor({
      cpu: { warning: 70, critical: 90, scaleUp: 80, scaleDown: 30 },
      memory: { warning: 75, critical: 90, scaleUp: 85, scaleDown: 40 },
    });
  });

  afterEach(() => {
    monitor.destroy();
  });

  describe('Initialization', () => {
    it('should initialize with default thresholds', () => {
      const defaultMonitor = new ResourceMonitor();
      expect(defaultMonitor).toBeDefined();
      defaultMonitor.destroy();
    });

    it('should initialize with custom thresholds', () => {
      const customThresholds = {
        cpu: { warning: 60, critical: 80, scaleUp: 70, scaleDown: 20 },
      };
      
      const customMonitor = new ResourceMonitor(customThresholds);
      expect(customMonitor).toBeDefined();
      customMonitor.destroy();
    });

    it('should start monitoring automatically', () => {
      expect(monitor['isMonitoring']).toBe(true);
    });
  });

  describe('Metric Collection', () => {
    it('should collect CPU metrics', async () => {
      const cpuMetrics = await monitor['getCPUMetrics']();
      
      expect(cpuMetrics).toHaveProperty('usage');
      expect(cpuMetrics).toHaveProperty('cores');
      expect(cpuMetrics).toHaveProperty('loadAverage');
      expect(cpuMetrics).toHaveProperty('processes');
      expect(cpuMetrics.cores).toBe(8);
    });

    it('should collect memory metrics', async () => {
      const memoryMetrics = await monitor['getMemoryMetrics']();
      
      expect(memoryMetrics).toHaveProperty('used');
      expect(memoryMetrics).toHaveProperty('total');
      expect(memoryMetrics).toHaveProperty('available');
      expect(memoryMetrics).toHaveProperty('percentage');
      expect(memoryMetrics.used).toBe(50000000);
      expect(memoryMetrics.total).toBe(100000000);
      expect(memoryMetrics.percentage).toBe(50);
    });

    it('should collect network metrics', async () => {
      const networkMetrics = await monitor['getNetworkMetrics']();
      
      expect(networkMetrics).toHaveProperty('bytesReceived');
      expect(networkMetrics).toHaveProperty('bytesSent');
      expect(networkMetrics).toHaveProperty('bandwidth');
      expect(networkMetrics).toHaveProperty('latency');
      expect(networkMetrics).toHaveProperty('connectionType');
      expect(networkMetrics.bandwidth).toBe(10);
      expect(networkMetrics.connectionType).toBe('4g');
    });

    it('should collect storage metrics', async () => {
      const storageMetrics = await monitor['getStorageMetrics']();
      
      expect(storageMetrics).toHaveProperty('used');
      expect(storageMetrics).toHaveProperty('total');
      expect(storageMetrics).toHaveProperty('available');
      expect(storageMetrics).toHaveProperty('percentage');
    });

    it('should handle missing performance.memory gracefully', async () => {
      const originalMemory = global.performance.memory;
      delete (global.performance as any).memory;
      
      const memoryMetrics = await monitor['getMemoryMetrics']();
      
      expect(memoryMetrics.used).toBe(0);
      expect(memoryMetrics.total).toBe(0);
      expect(memoryMetrics.percentage).toBe(0);
      
      global.performance.memory = originalMemory;
    });

    it('should handle missing navigator.storage gracefully', async () => {
      const originalStorage = global.navigator.storage;
      delete (global.navigator as any).storage;
      
      const storageMetrics = await monitor['getStorageMetrics']();
      
      expect(storageMetrics.used).toBe(0);
      expect(storageMetrics.total).toBe(0);
      
      global.navigator.storage = originalStorage;
    });
  });

  describe('CPU Usage Estimation', () => {
    it('should estimate CPU usage from long tasks', () => {
      const usage = monitor['estimateCPUUsage']();
      expect(usage).toBeGreaterThanOrEqual(0);
      expect(usage).toBeLessThanOrEqual(100);
    });

    it('should return low usage when no long tasks', () => {
      mockPerformance.getEntriesByType.mockImplementation((type) => {
        if (type === 'longtask') return [];
        return [];
      });
      
      const usage = monitor['estimateCPUUsage']();
      expect(usage).toBeLessThan(30);
    });
  });

  describe('Network Latency Calculation', () => {
    it('should calculate average latency from resource timings', () => {
      const timings = [
        { responseStart: 150, requestStart: 100 } as PerformanceResourceTiming,
        { responseStart: 200, requestStart: 180 } as PerformanceResourceTiming,
      ];
      
      const latency = monitor['calculateAverageLatency'](timings);
      expect(latency).toBe(35); // (50 + 20) / 2
    });

    it('should return 0 for empty timings', () => {
      const latency = monitor['calculateAverageLatency']([]);
      expect(latency).toBe(0);
    });

    it('should filter out invalid latencies', () => {
      const timings = [
        { responseStart: 100, requestStart: 150 } as PerformanceResourceTiming, // Invalid
        { responseStart: 200, requestStart: 180 } as PerformanceResourceTiming, // Valid
      ];
      
      const latency = monitor['calculateAverageLatency'](timings);
      expect(latency).toBe(20);
    });
  });

  describe('Alert System', () => {
    it('should create alerts when thresholds are exceeded', () => {
      monitor.onAlert(alertCallback);
      
      const metrics = {
        cpu: { usage: 95, cores: 8, loadAverage: [0.95, 0.95, 0.95], processes: 1 },
        memory: { used: 90000000, total: 100000000, available: 10000000, percentage: 90, swapUsed: 0, swapTotal: 0 },
        network: { bytesReceived: 1000, bytesSent: 500, packetsReceived: 10, packetsSent: 5, bandwidth: 10, latency: 50, connectionType: '4g' },
        storage: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, readSpeed: 0, writeSpeed: 0 },
        timestamp: Date.now(),
      };
      
      monitor['checkThresholds'](metrics);
      
      expect(alertCallback).toHaveBeenCalled();
      const alerts = monitor.getAlerts();
      expect(alerts.length).toBeGreaterThan(0);
    });

    it('should not create duplicate alerts', () => {
      monitor.onAlert(alertCallback);
      
      const metrics = {
        cpu: { usage: 95, cores: 8, loadAverage: [0.95, 0.95, 0.95], processes: 1 },
        memory: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, swapUsed: 0, swapTotal: 0 },
        network: { bytesReceived: 1000, bytesSent: 500, packetsReceived: 10, packetsSent: 5, bandwidth: 10, latency: 50, connectionType: '4g' },
        storage: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, readSpeed: 0, writeSpeed: 0 },
        timestamp: Date.now(),
      };
      
      // Create alert twice
      monitor['checkThresholds'](metrics);
      monitor['checkThresholds'](metrics);
      
      const alerts = monitor.getAlerts();
      expect(alerts.length).toBe(1); // Should only have one alert
    });

    it('should allow unsubscribing from alerts', () => {
      const unsubscribe = monitor.onAlert(alertCallback);
      
      unsubscribe();
      
      const metrics = {
        cpu: { usage: 95, cores: 8, loadAverage: [0.95, 0.95, 0.95], processes: 1 },
        memory: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, swapUsed: 0, swapTotal: 0 },
        network: { bytesReceived: 1000, bytesSent: 500, packetsReceived: 10, packetsSent: 5, bandwidth: 10, latency: 50, connectionType: '4g' },
        storage: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, readSpeed: 0, writeSpeed: 0 },
        timestamp: Date.now(),
      };
      
      monitor['checkThresholds'](metrics);
      
      expect(alertCallback).not.toHaveBeenCalled();
    });

    it('should resolve alerts', () => {
      const metrics = {
        cpu: { usage: 95, cores: 8, loadAverage: [0.95, 0.95, 0.95], processes: 1 },
        memory: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, swapUsed: 0, swapTotal: 0 },
        network: { bytesReceived: 1000, bytesSent: 500, packetsReceived: 10, packetsSent: 5, bandwidth: 10, latency: 50, connectionType: '4g' },
        storage: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, readSpeed: 0, writeSpeed: 0 },
        timestamp: Date.now(),
      };
      
      monitor['checkThresholds'](metrics);
      
      const alerts = monitor.getAlerts();
      expect(alerts.length).toBeGreaterThan(0);
      
      const alertId = alerts[0].id;
      monitor.resolveAlert(alertId);
      
      const resolvedAlert = monitor.getAlerts(true).find(a => a.id === alertId);
      expect(resolvedAlert?.resolved).toBe(true);
    });
  });

  describe('Scaling Recommendations', () => {
    beforeEach(() => {
      // Add some historical data
      for (let i = 0; i < 15; i++) {
        monitor['metrics'].push({
          cpu: { usage: 60 + i * 2, cores: 8, loadAverage: [0.6, 0.6, 0.6], processes: 1 },
          memory: { used: 60000000 + i * 2000000, total: 100000000, available: 40000000 - i * 2000000, percentage: 60 + i * 2, swapUsed: 0, swapTotal: 0 },
          network: { bytesReceived: 1000, bytesSent: 500, packetsReceived: 10, packetsSent: 5, bandwidth: 10, latency: 50, connectionType: '4g' },
          storage: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, readSpeed: 0, writeSpeed: 0 },
          timestamp: Date.now() - (15 - i) * 60000,
        });
      }
    });

    it('should generate scale-up recommendations for high usage', () => {
      monitor['generateScalingRecommendations']();
      
      const recommendations = monitor.getScalingRecommendations();
      const scaleUpRecs = recommendations.filter(r => r.type === 'scale-up');
      
      expect(scaleUpRecs.length).toBeGreaterThan(0);
    });

    it('should generate scale-down recommendations for low usage', () => {
      // Add low usage metrics
      for (let i = 0; i < 15; i++) {
        monitor['metrics'].push({
          cpu: { usage: 20 - i, cores: 8, loadAverage: [0.2, 0.2, 0.2], processes: 1 },
          memory: { used: 30000000 - i * 1000000, total: 100000000, available: 70000000 + i * 1000000, percentage: 30 - i, swapUsed: 0, swapTotal: 0 },
          network: { bytesReceived: 1000, bytesSent: 500, packetsReceived: 10, packetsSent: 5, bandwidth: 10, latency: 50, connectionType: '4g' },
          storage: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, readSpeed: 0, writeSpeed: 0 },
          timestamp: Date.now() - (15 - i) * 60000,
        });
      }
      
      monitor['generateScalingRecommendations']();
      
      const recommendations = monitor.getScalingRecommendations();
      const scaleDownRecs = recommendations.filter(r => r.type === 'scale-down');
      
      expect(scaleDownRecs.length).toBeGreaterThan(0);
    });

    it('should generate network optimization recommendations', () => {
      // Add high latency metrics
      monitor['metrics'][monitor['metrics'].length - 1].network.latency = 600;
      
      monitor['generateScalingRecommendations']();
      
      const recommendations = monitor.getScalingRecommendations();
      const networkRecs = recommendations.filter(r => r.resource === 'network');
      
      expect(networkRecs.length).toBeGreaterThan(0);
    });

    it('should sort recommendations by priority and confidence', () => {
      monitor['generateScalingRecommendations']();
      
      const recommendations = monitor.getScalingRecommendations();
      
      if (recommendations.length > 1) {
        const priorities = { critical: 4, high: 3, medium: 2, low: 1 };
        
        for (let i = 0; i < recommendations.length - 1; i++) {
          const currentPriority = priorities[recommendations[i].priority];
          const nextPriority = priorities[recommendations[i + 1].priority];
          
          if (currentPriority === nextPriority) {
            expect(recommendations[i].confidence).toBeGreaterThanOrEqual(recommendations[i + 1].confidence);
          } else {
            expect(currentPriority).toBeGreaterThanOrEqual(nextPriority);
          }
        }
      }
    });
  });

  describe('Resource Trends', () => {
    beforeEach(() => {
      // Add trend data
      for (let i = 0; i < 20; i++) {
        monitor['metrics'].push({
          cpu: { usage: 50 + i, cores: 8, loadAverage: [0.5, 0.5, 0.5], processes: 1 },
          memory: { used: 50000000 + i * 1000000, total: 100000000, available: 50000000 - i * 1000000, percentage: 50 + i, swapUsed: 0, swapTotal: 0 },
          network: { bytesReceived: 1000, bytesSent: 500, packetsReceived: 10, packetsSent: 5, bandwidth: 10, latency: 50 + i, connectionType: '4g' },
          storage: { used: 50000000 + i * 1000000, total: 100000000, available: 50000000 - i * 1000000, percentage: 50 + i, readSpeed: 0, writeSpeed: 0 },
          timestamp: Date.now() - (20 - i) * 60000,
        });
      }
    });

    it('should calculate resource trends', () => {
      const trends = monitor['calculateResourceTrends']();
      
      expect(trends).toHaveProperty('cpu');
      expect(trends).toHaveProperty('memory');
      expect(trends).toHaveProperty('network');
      expect(trends).toHaveProperty('storage');
      
      // All should be positive trends based on our test data
      expect(trends.cpu).toBeGreaterThan(0);
      expect(trends.memory).toBeGreaterThan(0);
      expect(trends.network).toBeGreaterThan(0);
      expect(trends.storage).toBeGreaterThan(0);
    });

    it('should return zero trends with insufficient data', () => {
      monitor['metrics'] = monitor['metrics'].slice(0, 5); // Keep only 5 metrics
      
      const trends = monitor['calculateResourceTrends']();
      
      expect(trends.cpu).toBe(0);
      expect(trends.memory).toBe(0);
      expect(trends.network).toBe(0);
      expect(trends.storage).toBe(0);
    });
  });

  describe('Confidence Calculation', () => {
    it('should calculate confidence based on trend and value', () => {
      const confidence1 = monitor['calculateConfidence'](10, 90);
      const confidence2 = monitor['calculateConfidence'](1, 50);
      
      expect(confidence1).toBeGreaterThan(confidence2);
      expect(confidence1).toBeLessThanOrEqual(100);
      expect(confidence2).toBeGreaterThanOrEqual(0);
    });

    it('should cap confidence at 100', () => {
      const confidence = monitor['calculateConfidence'](50, 95);
      expect(confidence).toBeLessThanOrEqual(100);
    });
  });

  describe('Capacity Planning', () => {
    beforeEach(() => {
      // Add historical data for capacity planning
      for (let i = 0; i < 30; i++) {
        monitor['metrics'].push({
          cpu: { usage: 40 + i * 0.5, cores: 8, loadAverage: [0.4, 0.4, 0.4], processes: 1 },
          memory: { used: 40000000 + i * 500000, total: 100000000, available: 60000000 - i * 500000, percentage: 40 + i * 0.5, swapUsed: 0, swapTotal: 0 },
          network: { bytesReceived: 1000, bytesSent: 500, packetsReceived: 10, packetsSent: 5, bandwidth: 10, latency: 50, connectionType: '4g' },
          storage: { used: 40000000 + i * 1000000, total: 100000000, available: 60000000 - i * 1000000, percentage: 40 + i, readSpeed: 0, writeSpeed: 0 },
          timestamp: Date.now() - (30 - i) * 60000,
        });
      }
    });

    it('should generate capacity plans', () => {
      const plans = monitor.generateCapacityPlan('3months');
      
      expect(plans.length).toBeGreaterThan(0);
      expect(plans).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            resource: 'cpu',
            timeframe: '3months',
          }),
          expect.objectContaining({
            resource: 'memory',
            timeframe: '3months',
          }),
          expect.objectContaining({
            resource: 'storage',
            timeframe: '3months',
          }),
        ])
      );
    });

    it('should project resource usage based on trends', () => {
      const plans = monitor.generateCapacityPlan('6months');
      
      plans.forEach(plan => {
        expect(plan.projectedUsage).toBeGreaterThanOrEqual(plan.currentUsage);
        expect(plan.growthRate).toBeGreaterThanOrEqual(0);
      });
    });

    it('should recommend capacity increases for high projected usage', () => {
      const plans = monitor.generateCapacityPlan('1year');
      
      const highUsagePlans = plans.filter(p => p.projectedUsage > 80);
      highUsagePlans.forEach(plan => {
        expect(plan.recommendedCapacity).toBeGreaterThan(plan.resource === 'cpu' ? 8 : 100000000);
        expect(plan.costImpact).toBeGreaterThan(0);
      });
    });

    it('should return empty plans with insufficient data', () => {
      monitor['metrics'] = monitor['metrics'].slice(0, 10); // Keep only 10 metrics
      
      const plans = monitor.generateCapacityPlan();
      expect(plans).toEqual([]);
    });
  });

  describe('Data Management', () => {
    it('should get current metrics', () => {
      // Add a metric
      monitor['metrics'].push({
        cpu: { usage: 50, cores: 8, loadAverage: [0.5, 0.5, 0.5], processes: 1 },
        memory: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, swapUsed: 0, swapTotal: 0 },
        network: { bytesReceived: 1000, bytesSent: 500, packetsReceived: 10, packetsSent: 5, bandwidth: 10, latency: 50, connectionType: '4g' },
        storage: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, readSpeed: 0, writeSpeed: 0 },
        timestamp: Date.now(),
      });
      
      const current = monitor.getCurrentMetrics();
      expect(current).toBeDefined();
      expect(current?.cpu.usage).toBe(50);
    });

    it('should get historical metrics', () => {
      // Add multiple metrics
      for (let i = 0; i < 5; i++) {
        monitor['metrics'].push({
          cpu: { usage: 50 + i, cores: 8, loadAverage: [0.5, 0.5, 0.5], processes: 1 },
          memory: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, swapUsed: 0, swapTotal: 0 },
          network: { bytesReceived: 1000, bytesSent: 500, packetsReceived: 10, packetsSent: 5, bandwidth: 10, latency: 50, connectionType: '4g' },
          storage: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, readSpeed: 0, writeSpeed: 0 },
          timestamp: Date.now() - i * 60000,
        });
      }
      
      const historical = monitor.getHistoricalMetrics();
      expect(historical.length).toBe(5);
      
      const limited = monitor.getHistoricalMetrics(3);
      expect(limited.length).toBe(3);
    });

    it('should update thresholds', () => {
      const newThresholds = {
        cpu: { warning: 60, critical: 80, scaleUp: 70, scaleDown: 20 },
      };
      
      monitor.updateThresholds(newThresholds);
      
      expect(monitor['thresholds'].cpu.warning).toBe(60);
      expect(monitor['thresholds'].cpu.critical).toBe(80);
    });

    it('should cleanup old data', () => {
      // Add old metrics
      const oldTimestamp = Date.now() - (25 * 60 * 60 * 1000); // 25 hours ago
      monitor['metrics'].push({
        cpu: { usage: 50, cores: 8, loadAverage: [0.5, 0.5, 0.5], processes: 1 },
        memory: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, swapUsed: 0, swapTotal: 0 },
        network: { bytesReceived: 1000, bytesSent: 500, packetsReceived: 10, packetsSent: 5, bandwidth: 10, latency: 50, connectionType: '4g' },
        storage: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, readSpeed: 0, writeSpeed: 0 },
        timestamp: oldTimestamp,
      });
      
      // Add recent metric
      monitor['metrics'].push({
        cpu: { usage: 60, cores: 8, loadAverage: [0.6, 0.6, 0.6], processes: 1 },
        memory: { used: 60000000, total: 100000000, available: 40000000, percentage: 60, swapUsed: 0, swapTotal: 0 },
        network: { bytesReceived: 1000, bytesSent: 500, packetsReceived: 10, packetsSent: 5, bandwidth: 10, latency: 50, connectionType: '4g' },
        storage: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, readSpeed: 0, writeSpeed: 0 },
        timestamp: Date.now(),
      });
      
      monitor.cleanup(24 * 60 * 60 * 1000); // 24 hours
      
      const metrics = monitor.getHistoricalMetrics();
      expect(metrics.every(m => m.timestamp > Date.now() - (24 * 60 * 60 * 1000))).toBe(true);
    });
  });

  describe('Monitoring Control', () => {
    it('should start and stop monitoring', () => {
      monitor.stopMonitoring();
      expect(monitor['isMonitoring']).toBe(false);
      
      monitor.startMonitoring();
      expect(monitor['isMonitoring']).toBe(true);
    });

    it('should not start monitoring if already monitoring', () => {
      const originalInterval = monitor['monitoringInterval'];
      
      monitor.startMonitoring(); // Should not create new interval
      
      expect(monitor['monitoringInterval']).toBe(originalInterval);
    });
  });

  describe('Memory Management', () => {
    it('should limit metrics to prevent memory leaks', async () => {
      // Add many metrics
      for (let i = 0; i < 1200; i++) {
        monitor['metrics'].push({
          cpu: { usage: 50, cores: 8, loadAverage: [0.5, 0.5, 0.5], processes: 1 },
          memory: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, swapUsed: 0, swapTotal: 0 },
          network: { bytesReceived: 1000, bytesSent: 500, packetsReceived: 10, packetsSent: 5, bandwidth: 10, latency: 50, connectionType: '4g' },
          storage: { used: 50000000, total: 100000000, available: 50000000, percentage: 50, readSpeed: 0, writeSpeed: 0 },
          timestamp: Date.now() - i * 1000,
        });
      }
      
      // Trigger collection which should clean up
      await monitor['collectMetrics']();
      
      expect(monitor['metrics'].length).toBeLessThanOrEqual(500);
    });

    it('should limit alerts to prevent memory leaks', () => {
      // Add many alerts
      for (let i = 0; i < 120; i++) {
        monitor['alerts'].push({
          id: `alert-${i}`,
          type: 'cpu',
          severity: 'high',
          threshold: 70,
          currentValue: 80,
          message: `Test alert ${i}`,
          timestamp: Date.now() - i * 1000,
          resolved: false,
        });
      }
      
      // Trigger alert creation which should clean up
      monitor['createAlert']('memory', 'critical', 90, 95, 'Test cleanup');
      
      expect(monitor['alerts'].length).toBeLessThanOrEqual(50);
    });
  });

  describe('Cleanup', () => {
    it('should cleanup all resources on destroy', () => {
      monitor.onAlert(alertCallback);
      
      monitor.destroy();
      
      expect(monitor['isMonitoring']).toBe(false);
      expect(monitor['alertCallbacks']).toEqual([]);
      expect(monitor['metrics']).toEqual([]);
      expect(monitor['alerts']).toEqual([]);
      expect(monitor['recommendations']).toEqual([]);
    });
  });
});