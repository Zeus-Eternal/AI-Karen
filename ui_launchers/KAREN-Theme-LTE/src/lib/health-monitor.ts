/**
 * Health Monitor
 * Provides health monitoring functionality
 */

export interface MemoryPerformance {
  memory: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
  };
}

export interface HealthMetrics {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  uptime: number;
  errorRate: number;
  averageResponseTime: number;
  lastCheck: Date;
  checks: HealthCheck[];
}

export interface HealthCheck {
  name: string;
  status: 'pass' | 'fail' | 'warning';
  message?: string;
  timestamp: Date;
  responseTime?: number;
}

export interface Alert {
  id: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  timestamp: Date;
  acknowledged: boolean;
  source: string;
  details?: Record<string, unknown>;
}

export interface HealthMonitorStatus {
  isMonitoring: boolean;
  lastUpdate: Date;
  uptime: number;
}

class HealthMonitor {
  private metrics: HealthMetrics;
  private alerts: Alert[] = [];
  private isMonitoring = false;
  private status: HealthMonitorStatus;
  private updateInterval: NodeJS.Timeout | null = null;
  private listeners: Record<string, ((data: unknown) => void)[]> = {};

  constructor() {
    this.metrics = this.getDefaultMetrics();
    this.status = this.getDefaultStatus();
  }

  private getDefaultMetrics(): HealthMetrics {
    return {
      status: 'unknown',
      uptime: 0,
      errorRate: 0,
      averageResponseTime: 0,
      lastCheck: new Date(),
      checks: [],
    };
  }

  private getDefaultStatus(): HealthMonitorStatus {
    return {
      isMonitoring: false,
      lastUpdate: new Date(),
      uptime: 0,
    };
  }

  getMetrics(): HealthMetrics {
    return { ...this.metrics };
  }

  getAlerts(limit?: number): Alert[] {
    if (limit && limit > 0) {
      return this.alerts.slice(0, limit);
    }
    return [...this.alerts];
  }

  getStatus(): HealthMonitorStatus {
    return { ...this.status };
  }

  acknowledgeAlert(alertId: string): boolean {
    const alertIndex = this.alerts.findIndex(alert => alert.id === alertId);
    if (alertIndex === -1) {
      return false;
    }

    if (this.alerts[alertIndex]) {
      this.alerts[alertIndex].acknowledged = true;
    }
    this.emit('alert-acknowledged', { alertId });
    return true;
  }

  clearAlerts(): void {
    this.alerts = [];
    this.emit('alerts-cleared');
  }

  start(): void {
    if (this.isMonitoring) return;

    this.isMonitoring = true;
    this.status.isMonitoring = true;
    this.status.lastUpdate = new Date();

    // Start monitoring interval
    this.updateInterval = setInterval(() => {
      this.performHealthCheck();
    }, 30000); // Check every 30 seconds

    this.emit('monitoring-started');
  }

  stop(): void {
    if (!this.isMonitoring) return;

    this.isMonitoring = false;
    this.status.isMonitoring = false;
    this.status.lastUpdate = new Date();

    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }

    this.emit('monitoring-stopped');
  }

  onMetricsUpdate(callback: (metrics: HealthMetrics) => void): () => void {
    return this.addEventListener('metrics-update', callback as (data: unknown) => void);
  }

  onAlert(callback: (alert: Alert) => void): () => void {
    return this.addEventListener('alert', callback as (data: unknown) => void);
  }

  private addEventListener(event: string, callback: (data: unknown) => void): () => void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }

    this.listeners[event].push(callback);

    return () => {
      const listeners = this.listeners[event];
      if (listeners) {
        const index = listeners.indexOf(callback);
        if (index > -1) {
          listeners.splice(index, 1);
        }
      }
    };
  }

  private emit(event: string, data?: unknown): void {
    const listeners = this.listeners[event];
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(data);
        } catch (error) {
          console.error(`Error in health monitor event listener for ${event}:`, error);
        }
      });
    }
  }

  private async performHealthCheck(): Promise<void> {
    try {
      const startTime = performance.now();

      // Perform basic health checks
      const checks: HealthCheck[] = [
        await this.checkApiHealth(),
        await this.checkDatabaseHealth(),
        await this.checkMemoryHealth(),
        await this.checkCpuHealth(),
      ];

      const endTime = performance.now();
      const responseTime = endTime - startTime;

      // Calculate overall health status
      const failedChecks = checks.filter(check => check.status === 'fail');
      const warningChecks = checks.filter(check => check.status === 'warning');

      let status: HealthMetrics['status'] = 'healthy';
      if (failedChecks.length > 0) {
        status = 'unhealthy';
      } else if (warningChecks.length > 0) {
        status = 'degraded';
      }

      // Update metrics
      this.metrics = {
        ...this.metrics,
        status,
        lastCheck: new Date(),
        averageResponseTime: (this.metrics.averageResponseTime + responseTime) / 2,
        checks,
      };

      // Check for new alerts
      this.checkForAlerts(checks);

      this.status.lastUpdate = new Date();
      this.emit('metrics-update', this.metrics);
    } catch (error) {
      console.error('Health check failed:', error);

      this.metrics.status = 'unhealthy';
      this.metrics.lastCheck = new Date();
      this.emit('metrics-update', this.metrics);
    }
  }

  private async checkApiHealth(): Promise<HealthCheck> {
    try {
      const response = await fetch('/api/health', {
        method: 'GET',
        signal: AbortSignal.timeout(5000) // 5 second timeout
      });

      if (response.ok) {
        return {
          name: 'API',
          status: 'pass',
          message: 'API is responding correctly',
          timestamp: new Date(),
        };
      } else {
        return {
          name: 'API',
          status: 'fail',
          message: `API returned status ${response.status}`,
          timestamp: new Date(),
        };
      }
    } catch (error) {
      return {
        name: 'API',
        status: 'fail',
        message: error instanceof Error ? error.message : 'Unknown API error',
        timestamp: new Date(),
      };
    }
  }

  private async checkDatabaseHealth(): Promise<HealthCheck> {
    try {
      const response = await fetch('/api/health/database', {
        method: 'GET',
        signal: AbortSignal.timeout(3000) // 3 second timeout
      });

      if (response.ok) {
        const data = await response.json();
        return {
          name: 'Database',
          status: data.connected ? 'pass' : 'fail',
          message: data.connected ? 'Database connection is healthy' : 'Database connection failed',
          timestamp: new Date(),
        };
      } else {
        return {
          name: 'Database',
          status: 'fail',
          message: `Database health check failed: ${response.status}`,
          timestamp: new Date(),
        };
      }
    } catch (error) {
      return {
        name: 'Database',
        status: 'fail',
        message: error instanceof Error ? error.message : 'Database health check error',
        timestamp: new Date(),
      };
    }
  }
  private async checkMemoryHealth(): Promise<HealthCheck> {
    try {
      // Check memory usage
      if (typeof performance !== 'undefined' && 'memory' in performance) {
        const perfMemory = performance as typeof performance & { memory?: { usedJSHeapSize: number; totalJSHeapSize: number } };
        const memory = perfMemory.memory;
        if (memory) {
          const usageRatio = memory.usedJSHeapSize! / memory.totalJSHeapSize!;

          if (usageRatio > 0.9) {
            return {
              name: 'Memory',
              status: 'fail',
              message: `Memory usage is critical: ${(usageRatio * 100).toFixed(1)}%`,
              timestamp: new Date(),
            };
          } else if (usageRatio > 0.7) {
            return {
              name: 'Memory',
              status: 'warning',
              message: `Memory usage is high: ${(usageRatio * 100).toFixed(1)}%`,
              timestamp: new Date(),
            };
          }
        }
      }

      return {
        name: 'Memory',
        status: 'pass',
        message: 'Memory usage is normal',
        timestamp: new Date(),
      };
    } catch (error) {
      return {
        name: 'Memory',
        status: 'fail',
        message: 'Memory health check failed',
        timestamp: new Date(),
      };
    }
  }

  private async checkCpuHealth(): Promise<HealthCheck> {
    try {
      // Simulate CPU check (in a real implementation, this would be more sophisticated)
      const start = performance.now();
      await new Promise(resolve => setTimeout(resolve, 100)); // Simulate work
      const end = performance.now();

      const responseTime = end - start;
      if (responseTime > 50) {
        return {
          name: 'CPU',
          status: 'warning',
          message: `CPU response time is elevated: ${responseTime.toFixed(2)}ms`,
          timestamp: new Date(),
          responseTime,
        };
      }

      return {
        name: 'CPU',
        status: 'pass',
        message: 'CPU performance is normal',
        timestamp: new Date(),
        responseTime,
      };
    } catch (error) {
      return {
        name: 'CPU',
        status: 'fail',
        message: 'CPU health check failed',
        timestamp: new Date(),
      };
    }
  }

  private checkForAlerts(checks: HealthCheck[]): void {
    const failedChecks = checks.filter(check => check.status === 'fail');
    const criticalChecks = failedChecks.filter(check =>
      check.name === 'API' || check.name === 'Database'
    );

    // Create alerts for critical failures
    criticalChecks.forEach(check => {
      const existingAlert = this.alerts.find(alert =>
        alert.source === check.name &&
        alert.severity === 'critical' &&
        !alert.acknowledged
      );

      if (!existingAlert) {
        const alert: Alert = {
          id: this.generateAlertId(),
          severity: 'critical',
          message: `${check.name} failure: ${check.message}`,
          timestamp: new Date(),
          acknowledged: false,
          source: check.name,
          details: { check },
        };

        this.alerts.unshift(alert);
        this.emit('alert', alert);
      }
    });

    // Keep only last 50 alerts
    if (this.alerts.length > 50) {
      this.alerts = this.alerts.slice(0, 50);
    }
  }

  private generateAlertId(): string {
    return `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Singleton instance
let healthMonitor: HealthMonitor | null = null;

export const getHealthMonitor = (): HealthMonitor => {
  if (!healthMonitor) {
    healthMonitor = new HealthMonitor();
  }
  return healthMonitor;
};

export default HealthMonitor;
