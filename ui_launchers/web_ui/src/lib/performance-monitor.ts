/**
 * Performance Monitoring for API Requests
 * Tracks request/response times and provides performance insights
 */

import { webUIConfig } from './config';
import { safeError, safeWarn } from './safe-console';

export interface RequestMetrics {
  endpoint: string;
  method: string;
  startTime: number;
  endTime: number;
  duration: number;
  status: number;
  success: boolean;
  size?: number;
  error?: string;
  timestamp: string;
}

export interface PerformanceStats {
  totalRequests: number;
  averageResponseTime: number;
  medianResponseTime: number;
  p95ResponseTime: number;
  p99ResponseTime: number;
  slowestRequest: RequestMetrics | null;
  fastestRequest: RequestMetrics | null;
  errorRate: number;
  requestsPerMinute: number;
  endpointStats: Record<string, {
    count: number;
    averageTime: number;
    errorRate: number;
    lastRequest: string;
  }>;
}

export interface PerformanceAlert {
  id: string;
  type: 'slow_request' | 'high_error_rate' | 'performance_degradation';
  message: string;
  severity: 'low' | 'medium' | 'high';
  timestamp: string;
  metrics: RequestMetrics | PerformanceStats;
}

class PerformanceMonitor {
  private metrics: RequestMetrics[] = [];
  private maxMetrics: number = 1000; // Keep last 1000 requests
  private listeners: Array<(metrics: RequestMetrics) => void> = [];
  private alertListeners: Array<(alert: PerformanceAlert) => void> = [];
  private slowRequestThreshold: number = 5000; // 5 seconds
  private verySlowRequestThreshold: number = 10000; // 10 seconds

  constructor() {
    // Clean up old metrics periodically
    setInterval(() => {
      this.cleanupOldMetrics();
    }, 60000); // Every minute
  }

  /**
   * Record a request metric
   */
  public recordRequest(
    endpoint: string,
    method: string,
    startTime: number,
    endTime: number,
    status: number,
    size?: number,
    error?: string
  ): void {
    const duration = endTime - startTime;
    const success = status >= 200 && status < 400;

    const metric: RequestMetrics = {
      endpoint,
      method,
      startTime,
      endTime,
      duration,
      status,
      success,
      size,
      error,
      timestamp: new Date().toISOString(),
    };

    // Add to metrics array
    this.metrics.unshift(metric);

    // Keep only the most recent metrics
    if (this.metrics.length > this.maxMetrics) {
      this.metrics = this.metrics.slice(0, this.maxMetrics);
    }

    // Check for performance alerts
    this.checkPerformanceAlerts(metric);

    // Notify listeners
    this.notifyListeners(metric);

    // Log slow requests
    if (webUIConfig.performanceMonitoring && duration > this.slowRequestThreshold) {
      const logLevel = duration > this.verySlowRequestThreshold ? 'error' : 'warn';
      console[logLevel](`🐌 Slow request detected: ${method} ${endpoint} took ${duration}ms`, {
        duration,
        status,
        success,
        size,
        error,

    }
  }

  /**
   * Check for performance alerts
   */
  private checkPerformanceAlerts(metric: RequestMetrics): void {
    // Slow request alert
    if (metric.duration > this.slowRequestThreshold) {
      const severity = metric.duration > this.verySlowRequestThreshold ? 'high' : 'medium';
      this.triggerAlert({
        id: `slow_request_${Date.now()}`,
        type: 'slow_request',
        message: `Slow request: ${metric.method} ${metric.endpoint} took ${metric.duration}ms`,
        severity,
        timestamp: new Date().toISOString(),
        metrics: metric,

    }

    // Check for performance degradation (if we have enough data)
    if (this.metrics.length >= 10) {
      const recentMetrics = this.metrics.slice(0, 10);
      const averageRecent = recentMetrics.reduce((sum, m) => sum + m.duration, 0) / recentMetrics.length;
      
      const olderMetrics = this.metrics.slice(10, 20);
      if (olderMetrics.length >= 10) {
        const averageOlder = olderMetrics.reduce((sum, m) => sum + m.duration, 0) / olderMetrics.length;
        
        // If recent requests are 50% slower than older ones
        if (averageRecent > averageOlder * 1.5 && averageRecent > 2000) {
          this.triggerAlert({
            id: `performance_degradation_${Date.now()}`,
            type: 'performance_degradation',
            message: `Performance degradation detected: recent requests are ${((averageRecent / averageOlder - 1) * 100).toFixed(0)}% slower`,
            severity: 'medium',
            timestamp: new Date().toISOString(),
            metrics: this.getStats(),

        }
      }
    }

    // High error rate alert (check last 20 requests)
    if (this.metrics.length >= 20) {
      const recentMetrics = this.metrics.slice(0, 20);
      const errorCount = recentMetrics.filter(m => !m.success).length;
      const errorRate = errorCount / recentMetrics.length;

      if (errorRate > 0.3) { // 30% error rate
        this.triggerAlert({
          id: `high_error_rate_${Date.now()}`,
          type: 'high_error_rate',
          message: `High error rate detected: ${(errorRate * 100).toFixed(0)}% of recent requests failed`,
          severity: 'high',
          timestamp: new Date().toISOString(),
          metrics: this.getStats(),

      }
    }
  }

  /**
   * Trigger a performance alert
   */
  private triggerAlert(alert: PerformanceAlert): void {
    // Use the performance alert service for graceful handling
    if (typeof window !== 'undefined') {
      // Only import and use the alert service in browser environment
      import('./performance-alert-service').then(({ performanceAlertService }) => { performanceAlertService.handleAlert(alert); }).catch(error => { from "@/lib/placeholder";
        // Fallback to console logging if alert service fails
        safeWarn('Performance alert service unavailable, falling back to console:', error);
        const logLevel = alert.severity === 'high' ? 'warn' : 'info';
        console[logLevel](`Karen Performance: ${alert.message}`, {
          type: alert.type,
          severity: alert.severity,
          endpoint: (alert.metrics as any)?.endpoint || 'unknown'


    } else {
      // Server-side: just log without the alert service
      const logLevel = alert.severity === 'high' ? 'warn' : 'info';
      console[logLevel](`Karen Performance: ${alert.message}`, {
        type: alert.type,
        severity: alert.severity,
        endpoint: (alert.metrics as any)?.endpoint || 'unknown'

    }

    // Notify alert listeners
    this.alertListeners.forEach(listener => {
      try {
        listener(alert);
      } catch (error) {
        safeError('Error in performance alert listener:', error);
      }

  }

  /**
   * Notify metrics listeners
   */
  private notifyListeners(metric: RequestMetrics): void {
    this.listeners.forEach(listener => {
      try {
        listener(metric);
      } catch (error) {
        safeError('Error in performance metrics listener:', error);
      }

  }

  /**
   * Clean up old metrics
   */
  private cleanupOldMetrics(): void {
    const oneHourAgo = Date.now() - (60 * 60 * 1000);
    this.metrics = this.metrics.filter(metric => metric.startTime > oneHourAgo);
  }

  /**
   * Get performance statistics
   */
  public getStats(): PerformanceStats {
    if (this.metrics.length === 0) {
      return {
        totalRequests: 0,
        averageResponseTime: 0,
        medianResponseTime: 0,
        p95ResponseTime: 0,
        p99ResponseTime: 0,
        slowestRequest: null,
        fastestRequest: null,
        errorRate: 0,
        requestsPerMinute: 0,
        endpointStats: {},
      };
    }

    const durations = this.metrics.map(m => m.duration).sort((a, b) => a - b);
    const successfulRequests = this.metrics.filter(m => m.success);
    const failedRequests = this.metrics.filter(m => !m.success);

    // Calculate percentiles
    const p95Index = Math.floor(durations.length * 0.95);
    const p99Index = Math.floor(durations.length * 0.99);
    const medianIndex = Math.floor(durations.length * 0.5);

    // Calculate requests per minute
    const oldestTimestamp = Math.min(...this.metrics.map(m => m.startTime));
    const timeSpanMinutes = (Date.now() - oldestTimestamp) / (1000 * 60);
    const requestsPerMinute = timeSpanMinutes > 0 ? this.metrics.length / timeSpanMinutes : 0;

    // Calculate endpoint statistics
    const endpointStats: Record<string, any> = {};
    this.metrics.forEach(metric => {
      const key = `${metric.method} ${metric.endpoint}`;
      if (!endpointStats[key]) {
        endpointStats[key] = {
          count: 0,
          totalTime: 0,
          errors: 0,
          lastRequest: metric.timestamp,
        };
      }
      
      endpointStats[key].count++;
      endpointStats[key].totalTime += metric.duration;
      if (!metric.success) {
        endpointStats[key].errors++;
      }
      
      if (metric.timestamp > endpointStats[key].lastRequest) {
        endpointStats[key].lastRequest = metric.timestamp;
      }

    // Transform endpoint stats
    const transformedEndpointStats: Record<string, any> = {};
    Object.entries(endpointStats).forEach(([key, stats]: [string, any]) => {
      transformedEndpointStats[key] = {
        count: stats.count,
        averageTime: stats.totalTime / stats.count,
        errorRate: stats.errors / stats.count,
        lastRequest: stats.lastRequest,
      };

    return {
      totalRequests: this.metrics.length,
      averageResponseTime: this.metrics.reduce((sum, m) => sum + m.duration, 0) / this.metrics.length,
      medianResponseTime: durations[medianIndex] || 0,
      p95ResponseTime: durations[p95Index] || 0,
      p99ResponseTime: durations[p99Index] || 0,
      slowestRequest: this.metrics.reduce((slowest, current) => 
        !slowest || current.duration > slowest.duration ? current : slowest, null as RequestMetrics | null),
      fastestRequest: this.metrics.reduce((fastest, current) => 
        !fastest || current.duration < fastest.duration ? current : fastest, null as RequestMetrics | null),
      errorRate: failedRequests.length / this.metrics.length,
      requestsPerMinute,
      endpointStats: transformedEndpointStats,
    };
  }

  /**
   * Get recent metrics
   */
  public getRecentMetrics(limit: number = 50): RequestMetrics[] {
    return this.metrics.slice(0, limit);
  }

  /**
   * Get metrics for a specific endpoint
   */
  public getEndpointMetrics(endpoint: string, method?: string): RequestMetrics[] {
    return this.metrics.filter(metric => {
      const endpointMatch = metric.endpoint === endpoint;
      const methodMatch = !method || metric.method === method;
      return endpointMatch && methodMatch;

  }

  /**
   * Get slow requests
   */
  public getSlowRequests(threshold: number = this.slowRequestThreshold): RequestMetrics[] {
    return this.metrics.filter(metric => metric.duration > threshold);
  }

  /**
   * Get failed requests
   */
  public getFailedRequests(): RequestMetrics[] {
    return this.metrics.filter(metric => !metric.success);
  }

  /**
   * Add a metrics listener
   */
  public onMetrics(listener: (metrics: RequestMetrics) => void): () => void {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  /**
   * Add an alert listener
   */
  public onAlert(listener: (alert: PerformanceAlert) => void): () => void {
    this.alertListeners.push(listener);
    return () => {
      const index = this.alertListeners.indexOf(listener);
      if (index > -1) {
        this.alertListeners.splice(index, 1);
      }
    };
  }

  /**
   * Clear all metrics
   */
  public clearMetrics(): void {
    this.metrics = [];
  }

  /**
   * Set slow request threshold
   */
  public setSlowRequestThreshold(threshold: number): void {
    this.slowRequestThreshold = threshold;
  }

  /**
   * Set very slow request threshold
   */
  public setVerySlowRequestThreshold(threshold: number): void {
    this.verySlowRequestThreshold = threshold;
  }

  /**
   * Export metrics as JSON
   */
  public exportMetrics(): string {
    return JSON.stringify({
      metrics: this.metrics,
      stats: this.getStats(),
      exportedAt: new Date().toISOString(),
    }, null, 2);
  }
}

// Global performance monitor instance
let performanceMonitor: PerformanceMonitor | null = null;

export function getPerformanceMonitor(): PerformanceMonitor {
  if (!performanceMonitor) {
    performanceMonitor = new PerformanceMonitor();
  }
  return performanceMonitor;
}

export function initializePerformanceMonitor(): PerformanceMonitor {
  performanceMonitor = new PerformanceMonitor();
  return performanceMonitor;
}

// Types are already exported via export interface declarations above

export { PerformanceMonitor };