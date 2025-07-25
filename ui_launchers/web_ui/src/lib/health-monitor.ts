/**
 * Health Check Monitoring for AI Karen Web UI API Integration
 * Monitors backend API endpoints and provides alerting for issues
 */

import { webUIConfig } from './config';
import { getKarenBackend } from './karen-backend';

export interface HealthCheckResult {
  endpoint: string;
  status: 'healthy' | 'degraded' | 'error';
  responseTime: number;
  timestamp: string;
  error?: string;
  details?: Record<string, any>;
}

export interface HealthMetrics {
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  averageResponseTime: number;
  errorRate: number;
  lastHealthCheck: string;
  uptime: number;
  endpoints: Record<string, HealthCheckResult>;
}

export interface AlertRule {
  id: string;
  name: string;
  condition: (metrics: HealthMetrics) => boolean;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  cooldown: number; // milliseconds
  lastTriggered?: number;
}

export interface Alert {
  id: string;
  ruleId: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  acknowledged: boolean;
  metrics?: Partial<HealthMetrics>;
}

class HealthMonitor {
  private metrics: HealthMetrics;
  private alerts: Alert[] = [];
  private alertRules: AlertRule[] = [];
  private isMonitoring: boolean = false;
  private monitoringInterval?: NodeJS.Timeout;
  private startTime: number = Date.now();
  private listeners: Array<(metrics: HealthMetrics) => void> = [];
  private alertListeners: Array<(alert: Alert) => void> = [];

  constructor() {
    this.metrics = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      averageResponseTime: 0,
      errorRate: 0,
      lastHealthCheck: new Date().toISOString(),
      uptime: 0,
      endpoints: {},
    };

    this.initializeDefaultAlertRules();
  }

  private initializeDefaultAlertRules(): void {
    this.alertRules = [
      {
        id: 'high-error-rate',
        name: 'High Error Rate',
        condition: (metrics) => metrics.errorRate > 0.1, // 10% error rate
        message: 'API error rate is above 10%',
        severity: 'high',
        cooldown: 300000, // 5 minutes
      },
      {
        id: 'critical-error-rate',
        name: 'Critical Error Rate',
        condition: (metrics) => metrics.errorRate > 0.25, // 25% error rate
        message: 'API error rate is critically high (>25%)',
        severity: 'critical',
        cooldown: 60000, // 1 minute
      },
      {
        id: 'slow-response-time',
        name: 'Slow Response Time',
        condition: (metrics) => metrics.averageResponseTime > 5000, // 5 seconds
        message: 'Average API response time is above 5 seconds',
        severity: 'medium',
        cooldown: 600000, // 10 minutes
      },
      {
        id: 'very-slow-response-time',
        name: 'Very Slow Response Time',
        condition: (metrics) => metrics.averageResponseTime > 10000, // 10 seconds
        message: 'Average API response time is critically slow (>10s)',
        severity: 'high',
        cooldown: 300000, // 5 minutes
      },
      {
        id: 'backend-unavailable',
        name: 'Backend Unavailable',
        condition: (metrics) => {
          const healthEndpoint = metrics.endpoints['/api/health'];
          return healthEndpoint && healthEndpoint.status === 'error';
        },
        message: 'Backend health check is failing',
        severity: 'critical',
        cooldown: 60000, // 1 minute
      },
      {
        id: 'chat-endpoint-down',
        name: 'Chat Endpoint Down',
        condition: (metrics) => {
          const chatEndpoint = metrics.endpoints['/api/chat/process'];
          return chatEndpoint && chatEndpoint.status === 'error';
        },
        message: 'Chat processing endpoint is not responding',
        severity: 'high',
        cooldown: 120000, // 2 minutes
      },
      {
        id: 'memory-endpoint-down',
        name: 'Memory Endpoint Down',
        condition: (metrics) => {
          const memoryEndpoint = metrics.endpoints['/api/memory/query'];
          return memoryEndpoint && memoryEndpoint.status === 'error';
        },
        message: 'Memory query endpoint is not responding',
        severity: 'medium',
        cooldown: 300000, // 5 minutes
      },
    ];
  }

  /**
   * Start health monitoring
   */
  public start(): void {
    if (this.isMonitoring) {
      console.warn('Health monitoring is already running');
      return;
    }

    if (!webUIConfig.enableHealthChecks) {
      console.log('Health checks are disabled in configuration');
      return;
    }

    this.isMonitoring = true;
    this.startTime = Date.now();

    console.log(`🏥 Starting health monitoring (interval: ${webUIConfig.healthCheckInterval}ms)`);

    // Run initial health check
    this.performHealthCheck();

    // Set up periodic health checks
    this.monitoringInterval = setInterval(() => {
      this.performHealthCheck();
    }, webUIConfig.healthCheckInterval);
  }

  /**
   * Stop health monitoring
   */
  public stop(): void {
    if (!this.isMonitoring) {
      return;
    }

    this.isMonitoring = false;

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = undefined;
    }

    console.log('🏥 Health monitoring stopped');
  }

  /**
   * Perform a comprehensive health check
   */
  private async performHealthCheck(): Promise<void> {
    const backend = getKarenBackend();
    const startTime = Date.now();

    try {
      // Check main health endpoint
      await this.checkEndpoint('/api/health', async () => {
        return await backend.healthCheck();
      });

      // Check chat processing endpoint (lightweight test)
      await this.checkEndpoint('/api/chat/process', async () => {
        // We don't want to actually process a message, so we'll just check if the endpoint responds to OPTIONS
        const response = await fetch(`${webUIConfig.backendUrl}/api/chat/process`, {
          method: 'OPTIONS',
          headers: { 'Content-Type': 'application/json' },
        });
        return { status: response.ok ? 'healthy' : 'error' };
      });

      // Check memory query endpoint (lightweight test)
      await this.checkEndpoint('/api/memory/query', async () => {
        const response = await fetch(`${webUIConfig.backendUrl}/api/memory/query`, {
          method: 'OPTIONS',
          headers: { 'Content-Type': 'application/json' },
        });
        return { status: response.ok ? 'healthy' : 'error' };
      });

      // Check plugin endpoints
      await this.checkEndpoint('/api/plugins/list', async () => {
        return await backend.getAvailablePlugins();
      });

      // Check analytics endpoints
      await this.checkEndpoint('/api/analytics/system-metrics', async () => {
        return await backend.getSystemMetrics();
      });

    } catch (error) {
      console.error('Health check failed:', error);
    }

    // Update metrics
    this.updateMetrics();

    // Check alert rules
    this.checkAlertRules();

    // Notify listeners
    this.notifyListeners();

    if (webUIConfig.debugLogging) {
      const duration = Date.now() - startTime;
      console.log(`🏥 Health check completed in ${duration}ms`);
    }
  }

  /**
   * Check a specific endpoint
   */
  private async checkEndpoint(
    endpoint: string,
    checkFunction: () => Promise<any>
  ): Promise<void> {
    const startTime = Date.now();

    try {
      const result = await Promise.race([
        checkFunction(),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Health check timeout')), webUIConfig.healthCheckTimeout)
        ),
      ]);

      const responseTime = Date.now() - startTime;

      this.metrics.endpoints[endpoint] = {
        endpoint,
        status: result?.status === 'error' ? 'error' : 'healthy',
        responseTime,
        timestamp: new Date().toISOString(),
        details: result,
      };

      this.metrics.totalRequests++;
      this.metrics.successfulRequests++;

    } catch (error) {
      const responseTime = Date.now() - startTime;

      this.metrics.endpoints[endpoint] = {
        endpoint,
        status: 'error',
        responseTime,
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : String(error),
      };

      this.metrics.totalRequests++;
      this.metrics.failedRequests++;
    }
  }

  /**
   * Update overall metrics
   */
  private updateMetrics(): void {
    // Calculate error rate
    this.metrics.errorRate = this.metrics.totalRequests > 0
      ? this.metrics.failedRequests / this.metrics.totalRequests
      : 0;

    // Calculate average response time
    const responseTimes = Object.values(this.metrics.endpoints).map(e => e.responseTime);
    this.metrics.averageResponseTime = responseTimes.length > 0
      ? responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length
      : 0;

    // Update uptime
    this.metrics.uptime = Date.now() - this.startTime;

    // Update last health check timestamp
    this.metrics.lastHealthCheck = new Date().toISOString();
  }

  /**
   * Check alert rules and trigger alerts if necessary
   */
  private checkAlertRules(): void {
    const now = Date.now();

    for (const rule of this.alertRules) {
      // Check cooldown
      if (rule.lastTriggered && (now - rule.lastTriggered) < rule.cooldown) {
        continue;
      }

      // Check condition
      if (rule.condition(this.metrics)) {
        this.triggerAlert(rule);
        rule.lastTriggered = now;
      }
    }
  }

  /**
   * Trigger an alert
   */
  private triggerAlert(rule: AlertRule): void {
    const alert: Alert = {
      id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      ruleId: rule.id,
      message: rule.message,
      severity: rule.severity,
      timestamp: new Date().toISOString(),
      acknowledged: false,
      metrics: { ...this.metrics },
    };

    this.alerts.unshift(alert); // Add to beginning of array

    // Keep only last 100 alerts
    if (this.alerts.length > 100) {
      this.alerts = this.alerts.slice(0, 100);
    }

    // Log alert
    const logLevel = alert.severity === 'critical' ? 'error' : 
                    alert.severity === 'high' ? 'error' :
                    alert.severity === 'medium' ? 'warn' : 'info';

    console[logLevel](`🚨 [${alert.severity.toUpperCase()}] ${alert.message}`, {
      alertId: alert.id,
      ruleId: alert.ruleId,
      timestamp: alert.timestamp,
      metrics: {
        errorRate: `${(this.metrics.errorRate * 100).toFixed(1)}%`,
        avgResponseTime: `${this.metrics.averageResponseTime.toFixed(0)}ms`,
        totalRequests: this.metrics.totalRequests,
        failedRequests: this.metrics.failedRequests,
      },
    });

    // Notify alert listeners
    this.alertListeners.forEach(listener => {
      try {
        listener(alert);
      } catch (error) {
        console.error('Error in alert listener:', error);
      }
    });
  }

  /**
   * Notify metrics listeners
   */
  private notifyListeners(): void {
    this.listeners.forEach(listener => {
      try {
        listener(this.metrics);
      } catch (error) {
        console.error('Error in metrics listener:', error);
      }
    });
  }

  /**
   * Get current metrics
   */
  public getMetrics(): HealthMetrics {
    return { ...this.metrics };
  }

  /**
   * Get recent alerts
   */
  public getAlerts(limit: number = 50): Alert[] {
    return this.alerts.slice(0, limit);
  }

  /**
   * Get unacknowledged alerts
   */
  public getUnacknowledgedAlerts(): Alert[] {
    return this.alerts.filter(alert => !alert.acknowledged);
  }

  /**
   * Acknowledge an alert
   */
  public acknowledgeAlert(alertId: string): boolean {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.acknowledged = true;
      return true;
    }
    return false;
  }

  /**
   * Add a metrics listener
   */
  public onMetricsUpdate(listener: (metrics: HealthMetrics) => void): () => void {
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
  public onAlert(listener: (alert: Alert) => void): () => void {
    this.alertListeners.push(listener);
    return () => {
      const index = this.alertListeners.indexOf(listener);
      if (index > -1) {
        this.alertListeners.splice(index, 1);
      }
    };
  }

  /**
   * Add a custom alert rule
   */
  public addAlertRule(rule: AlertRule): void {
    this.alertRules.push(rule);
  }

  /**
   * Remove an alert rule
   */
  public removeAlertRule(ruleId: string): boolean {
    const index = this.alertRules.findIndex(rule => rule.id === ruleId);
    if (index > -1) {
      this.alertRules.splice(index, 1);
      return true;
    }
    return false;
  }

  /**
   * Get monitoring status
   */
  public getStatus(): {
    isMonitoring: boolean;
    uptime: number;
    startTime: number;
    totalRequests: number;
    errorRate: number;
    averageResponseTime: number;
  } {
    return {
      isMonitoring: this.isMonitoring,
      uptime: this.metrics.uptime,
      startTime: this.startTime,
      totalRequests: this.metrics.totalRequests,
      errorRate: this.metrics.errorRate,
      averageResponseTime: this.metrics.averageResponseTime,
    };
  }

  /**
   * Reset metrics
   */
  public resetMetrics(): void {
    this.metrics = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      averageResponseTime: 0,
      errorRate: 0,
      lastHealthCheck: new Date().toISOString(),
      uptime: 0,
      endpoints: {},
    };
    this.startTime = Date.now();
  }

  /**
   * Clear alerts
   */
  public clearAlerts(): void {
    this.alerts = [];
  }
}

// Global health monitor instance
let healthMonitor: HealthMonitor | null = null;

export function getHealthMonitor(): HealthMonitor {
  if (!healthMonitor) {
    healthMonitor = new HealthMonitor();
  }
  return healthMonitor;
}

export function initializeHealthMonitor(): HealthMonitor {
  healthMonitor = new HealthMonitor();
  return healthMonitor;
}

// Export types
export type {
  HealthCheckResult,
  HealthMetrics,
  AlertRule,
  Alert,
};

export { HealthMonitor };