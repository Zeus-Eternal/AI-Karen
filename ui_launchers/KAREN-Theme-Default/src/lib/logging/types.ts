/**
 * Types for structured logging system
 */
export interface LogContext {
  correlationId: string;
  userId?: string;
  sessionId?: string;
  requestId?: string;
  timestamp: string;
  userAgent?: string;
  ipAddress?: string;
}
export interface PerformanceMetrics {
  startTime: number;
  endTime?: number;
  duration?: number;
  responseTime?: number;
  retryCount?: number;
  errorCount?: number;
  metadata?: Record<string, any>;
}
export interface BaseLogEntry {
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  context: LogContext;
  category: 'connectivity' | 'authentication' | 'performance' | 'error';
  subcategory?: string;
  connectionData?: {
    url: string;
    method: string;
    statusCode?: number;
    backendUrl?: string;
    retryAttempt?: number;
    timeoutMs?: number;
  };
  metrics?: PerformanceMetrics;
  error?: {
    name: string;
    message: string;
    stack?: string;
    code?: string;
  };
  metadata?: Record<string, any>;
}
export interface ConnectivityLogEntry extends BaseLogEntry {
  category: 'connectivity';
  subcategory: 'request' | 'retry' | 'timeout' | 'circuit_breaker';
  connectionData: {
    url: string;
    method: string;
    statusCode?: number;
    backendUrl?: string;
    retryAttempt?: number;
    timeoutMs?: number;
  };
}
export interface AuthenticationLogEntry extends BaseLogEntry {
  category: 'authentication';
  subcategory: 'login' | 'logout' | 'session_validation' | 'token_refresh';
  connectionData: {
    url: string;
    method: string;
    statusCode?: number;
    backendUrl?: string;
    retryAttempt?: number;
    timeoutMs?: number;
  };
  authData: {
    email?: string;
    success: boolean;
    failureReason?: string;
    attemptNumber?: number;
    maxAttempts?: number;
  };
}
export interface PerformanceLogEntry extends BaseLogEntry {
  category: 'performance';
  subcategory: 'response_time' | 'database_query' | 'api_call' | 'render_time';
  connectionData: {
    url: string;
    method: string;
    statusCode?: number;
    backendUrl?: string;
    retryAttempt?: number;
    timeoutMs?: number;
  };
  performanceData: {
    operation: string;
    duration: number;
    threshold?: number;
    exceeded?: boolean;
    resourceUsage?: {
      memory?: number;
      cpu?: number;
    };
  };
}
export interface LoggerConfig {
  enableConsoleLogging: boolean;
  enableRemoteLogging: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  remoteEndpoint?: string;
  batchSize?: number;
  flushInterval?: number;
  enablePerformanceMetrics: boolean;
  enableCorrelationTracking: boolean;
}
