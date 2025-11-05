/**
 * Admin Performance Monitor
 * 
 * Monitors and tracks performance metrics for admin operations including
 * database queries, API response times, and component render times.
 * 
 * Requirements: 7.3, 7.5
 */
import React from 'react';
import type {  PerformanceMetric, DatabaseQueryMetric, ApiResponseMetric, ComponentRenderMetric, PerformanceReport } from '@/types/admin';
// Performance metrics storage
class PerformanceMetricsStore {
  private metrics: Map<string, PerformanceMetric[]> = new Map();
  private maxMetricsPerType = 1000;
  addMetric(type: string, metric: PerformanceMetric): void {
    if (!this.metrics.has(type)) {
      this.metrics.set(type, []);
    }
    const typeMetrics = this.metrics.get(type)!;
    typeMetrics.push(metric);
    // Keep only the most recent metrics
    if (typeMetrics.length > this.maxMetricsPerType) {
      typeMetrics.shift();
    }
  }
  getMetrics(type: string): PerformanceMetric[] {
    return this.metrics.get(type) || [];
  }
  getAllMetrics(): Map<string, PerformanceMetric[]> {
    return new Map(this.metrics);
  }
  clearMetrics(type?: string): void {
    if (type) {
      this.metrics.delete(type);
    } else {
      this.metrics.clear();
    }
  }
  getMetricsSummary(type: string): {
    count: number;
    avgDuration: number;
    minDuration: number;
    maxDuration: number;
    p95Duration: number;
  } {
    const typeMetrics = this.getMetrics(type);
    if (typeMetrics.length === 0) {
      return { count: 0, avgDuration: 0, minDuration: 0, maxDuration: 0, p95Duration: 0 };
    }
    const durations = typeMetrics.map(m => m.duration).sort((a, b) => a - b);
    const sum = durations.reduce((acc, d) => acc + d, 0);
    const p95Index = Math.floor(durations.length * 0.95);
    return {
      count: typeMetrics.length,
      avgDuration: sum / durations.length,
      minDuration: durations[0],
      maxDuration: durations[durations.length - 1],
      p95Duration: durations[p95Index] || 0
    };
  }
}
const metricsStore = new PerformanceMetricsStore();
// Database query performance monitoring
export class DatabasePerformanceMonitor {
  static startQuery(queryName: string, query: string): () => DatabaseQueryMetric {
    const startTime = performance.now();
    const startMemory = (performance as any).memory?.usedJSHeapSize || 0;
    return () => {
      const endTime = performance.now();
      const endMemory = (performance as any).memory?.usedJSHeapSize || 0;
      const duration = endTime - startTime;
      const memoryUsed = endMemory - startMemory;
      const metric: DatabaseQueryMetric = {
        id: `db_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'database_query',
        name: queryName,
        startTime,
        endTime,
        duration,
        metadata: {
          query: query.substring(0, 200), // Truncate long queries
          memoryUsed,
          timestamp: new Date().toISOString()
        }
      };
      metricsStore.addMetric('database_query', metric);
      // Log slow queries
      if (duration > 1000) { // > 1 second
        console.warn(`Slow database query detected: ${queryName} took ${duration.toFixed(2)}ms`);
      }
      return metric;
    };
  }
  static getQueryMetrics(): DatabaseQueryMetric[] {
    return metricsStore.getMetrics('database_query') as DatabaseQueryMetric[];
  }
  static getSlowQueries(threshold = 1000): DatabaseQueryMetric[] {
    return this.getQueryMetrics().filter(metric => metric.duration > threshold);
  }
}
// API response performance monitoring
export class ApiPerformanceMonitor {
  static startRequest(endpoint: string, method: string): (statusCode: number, responseSize?: number) => ApiResponseMetric {
    const startTime = performance.now();
    return (statusCode: number, responseSize?: number) => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      const metric: ApiResponseMetric = {
        id: `api_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'api_response',
        name: `${method} ${endpoint}`,
        startTime,
        endTime,
        duration,
        metadata: {
          endpoint,
          method,
          statusCode,
          responseSize: responseSize || 0,
          timestamp: new Date().toISOString()
        }
      };
      metricsStore.addMetric('api_response', metric);
      // Log slow API calls
      if (duration > 2000) { // > 2 seconds
        console.warn(`Slow API call detected: ${method} ${endpoint} took ${duration.toFixed(2)}ms`);
      }
      return metric;
    };
  }
  static getApiMetrics(): ApiResponseMetric[] {
    return metricsStore.getMetrics('api_response') as ApiResponseMetric[];
  }
  static getSlowRequests(threshold = 2000): ApiResponseMetric[] {
    return this.getApiMetrics().filter(metric => metric.duration > threshold);
  }
}
// Component render performance monitoring
export class ComponentPerformanceMonitor {
  static startRender(componentName: string): () => ComponentRenderMetric {
    const startTime = performance.now();
    const startMemory = (performance as any).memory?.usedJSHeapSize || 0;
    return () => {
      const endTime = performance.now();
      const endMemory = (performance as any).memory?.usedJSHeapSize || 0;
      const duration = endTime - startTime;
      const memoryUsed = endMemory - startMemory;
      const metric: ComponentRenderMetric = {
        id: `comp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'component_render',
        name: componentName,
        startTime,
        endTime,
        duration,
        metadata: {
          componentName,
          memoryUsed,
          timestamp: new Date().toISOString()
        }
      };
      metricsStore.addMetric('component_render', metric);
      // Log slow renders
      if (duration > 100) { // > 100ms
        console.warn(`Slow component render detected: ${componentName} took ${duration.toFixed(2)}ms`);
      }
      return metric;
    };
  }
  static getRenderMetrics(): ComponentRenderMetric[] {
    return metricsStore.getMetrics('component_render') as ComponentRenderMetric[];
  }
  static getSlowRenders(threshold = 100): ComponentRenderMetric[] {
    return this.getRenderMetrics().filter(metric => metric.duration > threshold);
  }
}
// Performance reporting and analysis
export class PerformanceReporter {
  static generateReport(): PerformanceReport {
    const dbMetrics = metricsStore.getMetricsSummary('database_query');
    const apiMetrics = metricsStore.getMetricsSummary('api_response');
    const componentMetrics = metricsStore.getMetricsSummary('component_render');
    const report: PerformanceReport = {
      timestamp: new Date().toISOString(),
      summary: {
        totalMetrics: dbMetrics.count + apiMetrics.count + componentMetrics.count,
        timeRange: this.getTimeRange(),
        avgResponseTime: (dbMetrics.avgDuration + apiMetrics.avgDuration) / 2
      },
      database: {
        queryCount: dbMetrics.count,
        avgQueryTime: dbMetrics.avgDuration,
        slowQueries: DatabasePerformanceMonitor.getSlowQueries().length,
        p95QueryTime: dbMetrics.p95Duration
      },
      api: {
        requestCount: apiMetrics.count,
        avgResponseTime: apiMetrics.avgDuration,
        slowRequests: ApiPerformanceMonitor.getSlowRequests().length,
        p95ResponseTime: apiMetrics.p95Duration
      },
      components: {
        renderCount: componentMetrics.count,
        avgRenderTime: componentMetrics.avgDuration,
        slowRenders: ComponentPerformanceMonitor.getSlowRenders().length,
        p95RenderTime: componentMetrics.p95Duration
      },
      recommendations: this.generateRecommendations()
    };
    return report;
  }
  private static getTimeRange(): { start: string; end: string } {
    const allMetrics = Array.from(metricsStore.getAllMetrics().values()).flat();
    if (allMetrics.length === 0) {
      const now = new Date().toISOString();
      return { start: now, end: now };
    }
    const startTimes = allMetrics.map(m => m.startTime);
    const endTimes = allMetrics.map(m => m.endTime);
    return {
      start: new Date(Math.min(...startTimes)).toISOString(),
      end: new Date(Math.max(...endTimes)).toISOString()
    };
  }
  private static generateRecommendations(): string[] {
    const recommendations: string[] = [];
    const slowQueries = DatabasePerformanceMonitor.getSlowQueries();
    if (slowQueries.length > 0) {
      recommendations.push(`Consider optimizing ${slowQueries.length} slow database queries`);
    }
    const slowRequests = ApiPerformanceMonitor.getSlowRequests();
    if (slowRequests.length > 0) {
      recommendations.push(`${slowRequests.length} API endpoints are responding slowly`);
    }
    const slowRenders = ComponentPerformanceMonitor.getSlowRenders();
    if (slowRenders.length > 0) {
      recommendations.push(`${slowRenders.length} components are rendering slowly`);
    }
    const dbSummary = metricsStore.getMetricsSummary('database_query');
    if (dbSummary.avgDuration > 500) {
      recommendations.push('Average database query time is high - consider adding indexes');
    }
    const apiSummary = metricsStore.getMetricsSummary('api_response');
    if (apiSummary.avgDuration > 1000) {
      recommendations.push('Average API response time is high - consider caching');
    }
    if (recommendations.length === 0) {
      recommendations.push('Performance looks good! No immediate optimizations needed.');
    }
    return recommendations;
  }
  static exportMetrics(format: 'json' | 'csv' = 'json'): string {
    const allMetrics = Array.from(metricsStore.getAllMetrics().entries());
    if (format === 'csv') {
      const csvRows = ['Type,Name,Duration,StartTime,EndTime,Metadata'];
      allMetrics.forEach(([type, metrics]) => {
        metrics.forEach(metric => {
          const row = [
            type,
            metric.name,
            metric.duration.toString(),
            new Date(metric.startTime).toISOString(),
            new Date(metric.endTime).toISOString(),
            JSON.stringify(metric.metadata)
          ].map(field => `"${field.replace(/"/g, '""')}"`).join(',');
          csvRows.push(row);
        });
      });

      return csvRows.join('\n');
    }
    return JSON.stringify(Object.fromEntries(allMetrics), null, 2);
  }
}
// Performance hooks for React components
export function usePerformanceMonitoring(componentName: string) {
  const [renderMetric, setRenderMetric] = React.useState<ComponentRenderMetric | null>(null);
  React.useEffect(() => {
    const endRender = ComponentPerformanceMonitor.startRender(componentName);
    return () => {
      const metric = endRender();
      setRenderMetric(metric);
    };
  }, [componentName]);
  return renderMetric;
}
// Performance middleware for API routes
export function withPerformanceMonitoring(
  handler: (req: any, res: any) => Promise<any>
) {
  return async (req: any, res: any) => {
    const endpoint = req.url || 'unknown';
    const method = req.method || 'GET';
    const endRequest = ApiPerformanceMonitor.startRequest(endpoint, method);
    try {
      const result = await handler(req, res);
      endRequest(res.statusCode || 200);
      return result;
    } catch (error) {
      endRequest(500);
      throw error;
    }
  };
}
// Global performance monitoring setup
export class AdminPerformanceMonitor {
  private static instance: AdminPerformanceMonitor;
  private isMonitoring = false;
  private reportInterval: NodeJS.Timeout | null = null;
  static getInstance(): AdminPerformanceMonitor {
    if (!AdminPerformanceMonitor.instance) {
      AdminPerformanceMonitor.instance = new AdminPerformanceMonitor();
    }
    return AdminPerformanceMonitor.instance;
  }
  startMonitoring(options: {
    reportInterval?: number;
    enableConsoleReports?: boolean;
    enableRemoteReporting?: boolean;
  } = {}): void {
    if (this.isMonitoring) return;
    this.isMonitoring = true;
    const { reportInterval = 60000, enableConsoleReports = true } = options;
    // Set up periodic reporting
    this.reportInterval = setInterval(() => {
      const report = PerformanceReporter.generateReport();
      if (enableConsoleReports) {
        console.group('🚀 Admin Performance Report');
        console.groupEnd();
      }
      // Send to remote monitoring service if configured
      if (options.enableRemoteReporting) {
        this.sendReportToRemote(report);
      }
    }, reportInterval);
  }
  stopMonitoring(): void {
    if (!this.isMonitoring) return;
    this.isMonitoring = false;
    if (this.reportInterval) {
      clearInterval(this.reportInterval);
      this.reportInterval = null;
    }
  }
  private async sendReportToRemote(report: PerformanceReport): Promise<void> {
    try {
      await fetch('/api/admin/performance/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(report)
      });
    } catch (error) {
      // Silently fail - don't block on reporting errors
    }
  }
  getMetricsStore(): PerformanceMetricsStore {
    return metricsStore;
  }
  clearAllMetrics(): void {
    metricsStore.clearMetrics();
  }
  generateReport(): PerformanceReport {
    return PerformanceReporter.generateReport();
  }
}
// Export the singleton instance
export const adminPerformanceMonitor = AdminPerformanceMonitor.getInstance();
// Auto-start monitoring in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  adminPerformanceMonitor.startMonitoring({
    reportInterval: 30000, // 30 seconds in dev
    enableConsoleReports: true,
    enableRemoteReporting: false

}
