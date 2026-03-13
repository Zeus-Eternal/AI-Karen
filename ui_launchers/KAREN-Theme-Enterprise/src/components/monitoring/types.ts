/**
 * Types for monitoring dashboard components
 */

export interface ConnectionStatus {
  isConnected: boolean;
  lastCheck: Date;
  responseTime: number;
  endpoint: string;
  status: 'healthy' | 'degraded' | 'failed';
  errorCount: number;
  successCount: number;
}

export interface PerformanceMetrics {
  averageResponseTime: number;
  p95ResponseTime: number;
  p99ResponseTime: number;
  requestCount: number;
  errorRate: number;
  throughput: number;
  timeRange: string;
}

export interface ErrorMetrics {
  totalErrors: number;
  errorRate: number;
  errorsByType: Record<string, number>;
  recentErrors: Array<{
    timestamp: Date;
    type: string;
    message: string;
    correlationId: string;
  }>;
}

export interface AuthenticationMetrics {
  totalAttempts: number;
  successfulAttempts: number;
  failedAttempts: number;
  successRate: number;
  averageAuthTime: number;
  recentFailures: Array<{
    timestamp: Date;
    reason: string;
    email?: string;
  }>;
}

export interface SystemHealth {
  overall: 'healthy' | 'degraded' | 'critical';
  components: {
    backend: ConnectionStatus;
    database: ConnectionStatus;
    authentication: ConnectionStatus;
  };
  performance: PerformanceMetrics;
  errors: ErrorMetrics;
  authentication: AuthenticationMetrics;
  lastUpdated: Date;
}

export interface MonitoringConfig {
  refreshInterval: number;
  enableRealTimeUpdates: boolean;
  showDetailedMetrics: boolean;
  alertThresholds: {
    responseTime: number;
    errorRate: number;
    authFailureRate: number;
  };
}