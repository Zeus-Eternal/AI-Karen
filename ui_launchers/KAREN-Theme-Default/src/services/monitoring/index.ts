import { enhancedApiClient } from '@/lib/enhanced-api-client';
import { getPerformanceOptimizer } from '@/lib/performance/performance-optimizer';
import { adminPerformanceMonitor } from '@/lib/performance/admin-performance-monitor';

// Types
export interface MetricsData {
  timestamp: number;
  metrics: {
    cpu: number;
    memory: number;
    disk: number;
    network: number;
    responseTime: number;
    throughput: number;
  };
}

export interface PerformanceReport {
  id?: string;
  timestamp: string;
  duration?: number;
  metrics?: MetricsData;
  summary: {
    totalMetrics: number;
    timeRange: { start: string; end: string };
    avgResponseTime: number;
  };
  database: {
    queryCount: number;
    avgQueryTime: number;
    slowQueries: number;
    p95QueryTime: number;
  };
  api: {
    requestCount: number;
    avgResponseTime: number;
    slowRequests: number;
    p95ResponseTime: number;
  };
  components: {
    renderCount: number;
    avgRenderTime: number;
    slowRenders: number;
    p95RenderTime: number;
  };
  recommendations: string[];
}

export interface ResourceUsage {
  cpu: {
    usage: number;
    cores: number;
    frequency: number;
  };
  memory: {
    total: number;
    used: number;
    free: number;
    percentage: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
    percentage: number;
  };
  network: {
    incoming: number;
    outgoing: number;
    total: number;
  };
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical';
  score: number;
  checks: {
    name: string;
    status: 'pass' | 'fail' | 'warning';
    message: string;
  }[];
}

/**
 * Monitoring Service - Centralized monitoring and metrics collection
 */
export class MonitoringService {
  private static instance: MonitoringService | null = null;
  private isInitialized = false;
  private initializationPromise: Promise<void> | null = null;
  private metricsInterval: NodeJS.Timeout | null = null;
  private resourceUsageInterval: NodeJS.Timeout | null = null;

  /**
   * Private constructor to enforce singleton pattern
   */
  private constructor() {
    // Initialize performance monitors
    adminPerformanceMonitor.startMonitoring();
  }

  /**
   * Get the singleton instance of MonitoringService
   */
  public static getInstance(): MonitoringService {
    if (!MonitoringService.instance) {
      MonitoringService.instance = new MonitoringService();
    }
    return MonitoringService.instance;
  }

  /**
   * Initialize the monitoring service
   */
  public async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    if (this.initializationPromise) {
      return this.initializationPromise;
    }

    this.initializationPromise = this.performInitialization();
    return this.initializationPromise;
  }

  /**
   * Perform the actual initialization
   */
  private async performInitialization(): Promise<void> {
    try {
      // Initialize performance monitors
      adminPerformanceMonitor.startMonitoring();
      
      // Start collecting metrics
      this.startMetricsCollection();
      
      this.isInitialized = true;
    } catch (error) {
      console.error('Failed to initialize MonitoringService:', error);
      throw error;
    }
  }

  /**
   * Start collecting metrics periodically
   */
  private startMetricsCollection(): void {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
    }

    // Collect metrics every 30 seconds
    this.metricsInterval = setInterval(async () => {
      try {
        await this.collectMetrics();
      } catch (error) {
        console.error('Error collecting metrics:', error);
      }
    }, 30000);
  }


  /**
   * Collect current metrics
   */
  private async collectMetrics(): Promise<void> {
    try {
      const report = adminPerformanceMonitor.generateReport();
      
      // Send metrics to backend
      await enhancedApiClient.post('/api/admin/performance/report', report);
    } catch (error) {
      console.error('Error collecting metrics:', error);
    }
  }

  /**
   * Get current metrics
   */
  public async getCurrentMetrics(): Promise<MetricsData> {
    await this.initialize();
    const report = adminPerformanceMonitor.generateReport();
    return {
      timestamp: Date.now(),
      metrics: {
        cpu: 0, // These would be populated by actual monitoring
        memory: 0,
        disk: 0,
        network: 0,
        responseTime: report.summary.avgResponseTime,
        throughput: 0
      }
    };
  }

  /**
   * Get system health status
   */
  public async getSystemHealth(): Promise<SystemHealth> {
    await this.initialize();
    
    try {
      const response = await enhancedApiClient.get('/api/health');
      return response.data as SystemHealth;
    } catch (error) {
      console.error('Error fetching system health:', error);
      throw error;
    }
  }

  /**
   * Generate performance report
   */
  public async generatePerformanceReport(): Promise<PerformanceReport> {
    await this.initialize();
    
    try {
      const report = adminPerformanceMonitor.generateReport();
      // Convert the admin report to our interface format
      return {
        id: `report_${Date.now()}`,
        timestamp: report.timestamp,
        duration: 0, // Not available in admin report
        metrics: undefined, // Not directly available
        summary: report.summary,
        database: report.database,
        api: report.api,
        components: report.components,
        recommendations: report.recommendations
      };
    } catch (error) {
      console.error('Error generating performance report:', error);
      throw error;
    }
  }

  /**
   * Optimize system performance
   */
  public async optimizePerformance(): Promise<void> {
    await this.initialize();
    
    try {
      const optimizer = getPerformanceOptimizer();
      optimizer.autoOptimize();
    } catch (error) {
      console.error('Error optimizing performance:', error);
      throw error;
    }
  }

  /**
   * Get performance metrics for a specific time range
   */
  public async getPerformanceMetrics(startTime: number, endTime: number): Promise<MetricsData[]> {
    await this.initialize();
    
    try {
      const response = await enhancedApiClient.get(`/api/metrics/range?startTime=${startTime}&endTime=${endTime}`);
      return response.data as MetricsData[];
    } catch (error) {
      console.error('Error fetching performance metrics:', error);
      throw error;
    }
  }

  /**
   * Clean up resources
   */
  public cleanup(): void {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
      this.metricsInterval = null;
    }
    
    adminPerformanceMonitor.stopMonitoring();
    this.isInitialized = false;
  }
}

// Export singleton instance
export const monitoringService = MonitoringService.getInstance();