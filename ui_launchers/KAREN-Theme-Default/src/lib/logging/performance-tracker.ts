/**
 * Performance metrics collection for response times and system performance
 */
import { PerformanceMetrics } from './types';
interface PerformanceEntry {
  operation: string;
  startTime: number;
  endTime?: number;
  metadata?: Record<string, any>;
}
class PerformanceTracker {
  private static instance: PerformanceTracker;
  private activeOperations = new Map<string, PerformanceEntry>();
  private completedOperations: PerformanceMetrics[] = [];
  private maxHistorySize = 1000;
  static getInstance(): PerformanceTracker {
    if (!PerformanceTracker.instance) {
      PerformanceTracker.instance = new PerformanceTracker();
    }
    return PerformanceTracker.instance;
  }
  /**
   * Start tracking a performance operation
   */
  startOperation(operationId: string, operationName: string, metadata?: Record<string, any>): void {
    const startTime = performance.now();
    this.activeOperations.set(operationId, {
      operation: operationName,
      startTime,
      metadata
    });

  }
  /**
   * End tracking a performance operation
   */
  endOperation(operationId: string): PerformanceMetrics | null {
    const entry = this.activeOperations.get(operationId);
    if (!entry) {
      return null;
    }
    const endTime = performance.now();
    const duration = endTime - entry.startTime;
    const metrics: PerformanceMetrics = {
      startTime: entry.startTime,
      endTime,
      duration,
      responseTime: duration,
      metadata: entry.metadata
    };
    this.activeOperations.delete(operationId);
    this.addToHistory(metrics);
    return metrics;
  }
  /**
   * Track a complete operation with timing
   */
  async trackOperation<T>(
    operationName: string,
    operation: () => Promise<T>,
    metadata?: Record<string, any>
  ): Promise<{ result: T; metrics: PerformanceMetrics }> {
    const operationId = `${operationName}_${Date.now()}_${Math.random()}`;
    this.startOperation(operationId, operationName, metadata);
    try {
      const result = await operation();
      const metrics = this.endOperation(operationId)!;
      return { result, metrics };
    } catch (error) {
      this.endOperation(operationId);
      throw error;
    }
  }
  /**
   * Track synchronous operation
   */
  trackSyncOperation<T>(
    operationName: string,
    operation: () => T,
    metadata?: Record<string, any>
  ): { result: T; metrics: PerformanceMetrics } {
    const operationId = `${operationName}_${Date.now()}_${Math.random()}`;
    this.startOperation(operationId, operationName, metadata);
    try {
      const result = operation();
      const metrics = this.endOperation(operationId)!;
      return { result, metrics };
    } catch (error) {
      this.endOperation(operationId);
      throw error;
    }
  }
  /**
   * Get performance statistics
   */
  getPerformanceStats(operationName?: string): {
    count: number;
    averageTime: number;
    minTime: number;
    maxTime: number;
    p95Time: number;
    p99Time: number;
  } {
    let operations = this.completedOperations;
    if (operationName) {
      // Filter by operation name if provided
      operations = operations.filter(op => 
        op.metadata && op.metadata.operationName === operationName
      );
    }
    if (operations.length === 0) {
      return {
        count: 0,
        averageTime: 0,
        minTime: 0,
        maxTime: 0,
        p95Time: 0,
        p99Time: 0
      };
    }
    const durations = operations
      .map(op => op.duration || 0)
      .sort((a, b) => a - b);
    const sum = durations.reduce((acc, duration) => acc + duration, 0);
    const count = durations.length;
    return {
      count,
      averageTime: sum / count,
      minTime: durations[0],
      maxTime: durations[count - 1],
      p95Time: durations[Math.floor(count * 0.95)],
      p99Time: durations[Math.floor(count * 0.99)]
    };
  }
  /**
   * Get recent performance data
   */
  getRecentMetrics(limit: number = 100): PerformanceMetrics[] {
    return this.completedOperations.slice(-limit);
  }
  /**
   * Clear performance history
   */
  clearHistory(): void {
    this.completedOperations = [];
  }
  /**
   * Get memory usage information
   */
  getMemoryUsage(): {
    usedJSHeapSize?: number;
    totalJSHeapSize?: number;
    jsHeapSizeLimit?: number;
  } {
    if (typeof window !== 'undefined' && 'performance' in window && 'memory' in performance) {
      const memory = (performance as any).memory;
      return {
        usedJSHeapSize: memory.usedJSHeapSize,
        totalJSHeapSize: memory.totalJSHeapSize,
        jsHeapSizeLimit: memory.jsHeapSizeLimit
      };
    }
    return {};
  }
  /**
   * Track network request performance
   */
  trackNetworkRequest(url: string, method: string = 'GET'): {
    start: () => void;
    end: (statusCode?: number, error?: Error) => PerformanceMetrics;
  } {
    const operationId = `network_${method}_${url}_${Date.now()}`;
    return {
      start: () => {
        this.startOperation(operationId, `${method} ${url}`, {
          type: 'network',
          url,
          method
        });

      },
      end: (statusCode?: number, error?: Error) => {
        const metrics = this.endOperation(operationId);
        if (metrics && metrics.metadata) {
          metrics.metadata.statusCode = statusCode;
          metrics.metadata.error = error?.message;
        }
        return metrics || {
          startTime: 0,
          endTime: 0,
          duration: 0,
          responseTime: 0
        };
      }
    };
  }
  private addToHistory(metrics: PerformanceMetrics): void {
    this.completedOperations.push(metrics);
    // Keep history size manageable
    if (this.completedOperations.length > this.maxHistorySize) {
      this.completedOperations = this.completedOperations.slice(-this.maxHistorySize / 2);
    }
  }
}
export const performanceTracker = PerformanceTracker.getInstance();
/**
 * Decorator for tracking method performance
 */
export function trackPerformance(operationName?: string) {
  return function (target: any, propertyName: string, descriptor: PropertyDescriptor) {
    const method = descriptor.value;
    const opName = operationName || `${target.constructor.name}.${propertyName}`;
    descriptor.value = async function (...args: any[]) {
      const { result, metrics } = await performanceTracker.trackOperation(
        opName,
        () => method.apply(this, args)
      );
      return result;
    };
  };
}
