/**
 * Tests for performance tracking functionality
 */

import { performanceTracker } from '../performance-tracker';

// Mock performance API
const mockPerformance = {
  now: jest.fn(() => Date.now()),
  memory: {
    usedJSHeapSize: 1000000,
    totalJSHeapSize: 2000000,
    jsHeapSizeLimit: 4000000
  }
};

Object.defineProperty(global, 'performance', {
  value: mockPerformance
});

describe('PerformanceTracker', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    performanceTracker.clearHistory();
    mockPerformance.now.mockImplementation(() => Date.now());
  });

  describe('startOperation and endOperation', () => {
    it('should track operation timing', () => {
      const operationId = 'test-operation';
      const operationName = 'Test Operation';
      
      let startTime = 1000;
      let endTime = 1500;
      
      mockPerformance.now
        .mockReturnValueOnce(startTime)
        .mockReturnValueOnce(endTime);
      
      performanceTracker.startOperation(operationId, operationName);
      const metrics = performanceTracker.endOperation(operationId);
      
      expect(metrics).toEqual({
        startTime,
        endTime,
        duration: 500,
        responseTime: 500
      });
    });

    it('should return null for non-existent operation', () => {
      const metrics = performanceTracker.endOperation('non-existent');
      expect(metrics).toBeNull();
    });

    it('should handle metadata', () => {
      const operationId = 'test-operation';
      const metadata = { userId: '123', action: 'login' };
      
      performanceTracker.startOperation(operationId, 'Test', metadata);
      const metrics = performanceTracker.endOperation(operationId);
      
      expect(metrics).toBeDefined();
    });
  });

  describe('trackOperation', () => {
    it('should track async operation', async () => {
      const operation = jest.fn(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
        return 'result';
      });
      
      mockPerformance.now
        .mockReturnValueOnce(1000)
        .mockReturnValueOnce(1100);
      
      const { result, metrics } = await performanceTracker.trackOperation(
        'async-test',
        operation
      );
      
      expect(result).toBe('result');
      expect(metrics.duration).toBe(100);
      expect(operation).toHaveBeenCalled();
    });

    it('should handle operation errors', async () => {
      const operation = jest.fn(async () => {
        throw new Error('Test error');
      });
      
      await expect(
        performanceTracker.trackOperation('error-test', operation)
      ).rejects.toThrow('Test error');
      
      expect(operation).toHaveBeenCalled();
    });
  });

  describe('trackSyncOperation', () => {
    it('should track synchronous operation', () => {
      const operation = jest.fn(() => 'sync-result');
      
      mockPerformance.now
        .mockReturnValueOnce(1000)
        .mockReturnValueOnce(1050);
      
      const { result, metrics } = performanceTracker.trackSyncOperation(
        'sync-test',
        operation
      );
      
      expect(result).toBe('sync-result');
      expect(metrics.duration).toBe(50);
      expect(operation).toHaveBeenCalled();
    });

    it('should handle sync operation errors', () => {
      const operation = jest.fn(() => {
        throw new Error('Sync error');
      });
      
      expect(() =>
        performanceTracker.trackSyncOperation('sync-error-test', operation)
      ).toThrow('Sync error');
      
      expect(operation).toHaveBeenCalled();
    });
  });

  describe('getPerformanceStats', () => {
    it('should calculate performance statistics', async () => {
      // Add some test operations
      const operations = [
        () => Promise.resolve('op1'),
        () => Promise.resolve('op2'),
        () => Promise.resolve('op3')
      ];
      
      const durations = [100, 200, 300];
      let callIndex = 0;
      
      mockPerformance.now.mockImplementation(() => {
        const duration = durations[Math.floor(callIndex / 2)];
        const time = callIndex % 2 === 0 ? 1000 : 1000 + duration;
        callIndex++;
        return time;
      });
      
      for (const op of operations) {
        await performanceTracker.trackOperation('test-op', op);
      }
      
      const stats = performanceTracker.getPerformanceStats();
      
      expect(stats.count).toBe(3);
      expect(stats.averageTime).toBe(200);
      expect(stats.minTime).toBe(100);
      expect(stats.maxTime).toBe(300);
    });

    it('should return zero stats for no operations', () => {
      const stats = performanceTracker.getPerformanceStats();
      
      expect(stats).toEqual({
        count: 0,
        averageTime: 0,
        minTime: 0,
        maxTime: 0,
        p95Time: 0,
        p99Time: 0
      });
    });
  });

  describe('getMemoryUsage', () => {
    it('should return memory usage when available', () => {
      const usage = performanceTracker.getMemoryUsage();
      
      expect(usage).toEqual({
        usedJSHeapSize: 1000000,
        totalJSHeapSize: 2000000,
        jsHeapSizeLimit: 4000000
      });
    });

    it('should return empty object when memory API not available', () => {
      const originalPerformance = global.performance;
      delete (global as any).performance;
      
      const usage = performanceTracker.getMemoryUsage();
      
      expect(usage).toEqual({});
      
      // Restore
      (global as any).performance = originalPerformance;
    });
  });

  describe('trackNetworkRequest', () => {
    it('should track network request performance', () => {
      const url = 'https://api.example.com/test';
      const method = 'POST';
      
      mockPerformance.now
        .mockReturnValueOnce(1000)
        .mockReturnValueOnce(1200);
      
      const tracker = performanceTracker.trackNetworkRequest(url, method);
      tracker.start();
      const metrics = tracker.end(200);
      
      expect(metrics.duration).toBe(200);
      expect(metrics.metadata?.statusCode).toBe(200);
      expect(metrics.metadata?.url).toBe(url);
      expect(metrics.metadata?.method).toBe(method);
    });

    it('should track network request errors', () => {
      const url = 'https://api.example.com/test';
      const error = new Error('Network error');
      
      const tracker = performanceTracker.trackNetworkRequest(url);
      tracker.start();
      const metrics = tracker.end(undefined, error);
      
      expect(metrics.metadata?.error).toBe('Network error');
    });
  });

  describe('getRecentMetrics', () => {
    it('should return recent metrics with limit', async () => {
      // Add multiple operations
      for (let i = 0; i < 10; i++) {
        await performanceTracker.trackOperation(`op-${i}`, async () => `result-${i}`);
      }
      
      const recent = performanceTracker.getRecentMetrics(5);
      
      expect(recent).toHaveLength(5);
    });
  });

  describe('clearHistory', () => {
    it('should clear performance history', async () => {
      await performanceTracker.trackOperation('test', async () => 'result');
      
      let stats = performanceTracker.getPerformanceStats();
      expect(stats.count).toBe(1);
      
      performanceTracker.clearHistory();
      
      stats = performanceTracker.getPerformanceStats();
      expect(stats.count).toBe(0);
    });
  });
});