/**
 * Structured logging system for connectivity and authentication issues
 */

import {  LogContext, BaseLogEntry, ConnectivityLogEntry, AuthenticationLogEntry, PerformanceLogEntry, LoggerConfig, PerformanceMetrics } from './types';
import { correlationTracker } from './correlation-tracker';
import { performanceTracker } from './performance-tracker';

class ConnectivityLogger {
  private static instance: ConnectivityLogger;
  private config: LoggerConfig;
  private logBuffer: BaseLogEntry[] = [];
  private flushTimer?: NodeJS.Timeout;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = {
      enableConsoleLogging: true,
      enableRemoteLogging: false,
      logLevel: 'info',
      batchSize: 50,
      flushInterval: 5000,
      enablePerformanceMetrics: true,
      enableCorrelationTracking: true,
      ...config
    };

    if (this.config.enableRemoteLogging && this.config.flushInterval) {
      this.startAutoFlush();
    }
  }

  static getInstance(config?: Partial<LoggerConfig>): ConnectivityLogger {
    if (!ConnectivityLogger.instance) {
      ConnectivityLogger.instance = new ConnectivityLogger(config);
    }
    return ConnectivityLogger.instance;
  }

  /**
   * Create base log context
   */
  private createLogContext(additionalContext?: Partial<LogContext>): LogContext {
    const correlationId = this.config.enableCorrelationTracking 
      ? correlationTracker.getCurrentCorrelationId()
      : `log_${Date.now()}`;

    return {
      correlationId,
      timestamp: new Date().toISOString(),
      userId: this.getCurrentUserId(),
      sessionId: this.getSessionId(),
      requestId: `req_${Date.now()}_${Math.random()}`,
      userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : undefined,
      ...additionalContext
    };
  }

  private extractErrorCode(error?: Error): string | undefined {
    if (!error) return undefined;
    const candidate = error as Error & { code?: string | number };
    return candidate.code ? String(candidate.code) : undefined;
  }

  /**
   * Log connectivity issues
   */
  logConnectivity(
    level: 'debug' | 'info' | 'warn' | 'error',
    message: string,
    connectionData: {
      url: string;
      method: string;
      statusCode?: number;
      backendUrl?: string;
      retryAttempt?: number;
      timeoutMs?: number;
    },
    error?: Error,
    metrics?: PerformanceMetrics,
    additionalContext?: Partial<LogContext>
  ): void {
    const logEntry: ConnectivityLogEntry = {
      level,
      message,
      context: this.createLogContext(additionalContext),
      category: 'connectivity',
      subcategory: this.determineConnectivitySubcategory(connectionData, error),
      connectionData,
      metrics,
      error: error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
        code: this.extractErrorCode(error)
      } : undefined,
      metadata: {
        timestamp: Date.now(),
        userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : undefined
      }
    };

    this.processLogEntry(logEntry);
  }

  /**
   * Log authentication attempts and results
   */
  logAuthentication(
    level: 'debug' | 'info' | 'warn' | 'error',
    message: string,
    authData: {
      email?: string;
      success: boolean;
      failureReason?: string;
      attemptNumber?: number;
      maxAttempts?: number;
    },
    subcategory: 'login' | 'logout' | 'session_validation' | 'token_refresh' = 'login',
    error?: Error,
    metrics?: PerformanceMetrics,
    additionalContext?: Partial<LogContext>
  ): void {
    const logEntry: AuthenticationLogEntry = {
      level,
      message,
      context: this.createLogContext(additionalContext),
      category: 'authentication',
      subcategory,
      connectionData: {
        url: '/auth',
        method: 'POST'
      },
      authData: {
        ...authData,
        // Never log actual email in production, use hash or identifier
        email: authData.email ? this.sanitizeEmail(authData.email) : undefined
      },
      metrics,
      error: error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
        code: this.extractErrorCode(error)
      } : undefined,
      metadata: {
        timestamp: Date.now(),
        attemptTimestamp: Date.now()
      }
    };

    this.processLogEntry(logEntry);
  }

  /**
   * Log performance metrics
   */
  logPerformance(
    level: 'debug' | 'info' | 'warn' | 'error',
    message: string,
    performanceData: {
      operation: string;
      duration: number;
      threshold?: number;
      exceeded?: boolean;
      resourceUsage?: {
        memory?: number;
        cpu?: number;
      };
    },
    subcategory: 'response_time' | 'database_query' | 'api_call' | 'render_time' = 'response_time',
    additionalContext?: Partial<LogContext>
  ): void {
    if (!this.config.enablePerformanceMetrics) return;

    const logEntry: PerformanceLogEntry = {
      level,
      message,
      context: this.createLogContext(additionalContext),
      category: 'performance',
      subcategory,
      connectionData: {
        url: performanceData.operation,
        method: 'GET'
      },
      performanceData,
      metadata: {
        timestamp: Date.now(),
        memoryUsage: performanceTracker.getMemoryUsage()
      }
    };

    this.processLogEntry(logEntry);
  }

  /**
   * Log general errors with context
   */
  logError(
    message: string,
    error: Error,
    category: 'connectivity' | 'authentication' | 'performance' | 'error' = 'error',
    additionalContext?: Partial<LogContext>
  ): void {
    const logEntry: BaseLogEntry = {
      level: 'error',
      message,
      context: this.createLogContext(additionalContext),
      category,
      connectionData: {
        url: 'unknown',
        method: 'unknown'
      },
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
        code: this.extractErrorCode(error)
      },
      metadata: {
        timestamp: Date.now(),
        errorTimestamp: Date.now()
      }
    };

    this.processLogEntry(logEntry);
  }

  /**
   * Process and route log entries
   */
  private processLogEntry(logEntry: BaseLogEntry): void {
    // Check log level
    if (!this.shouldLog(logEntry.level)) {
      return;
    }

    // Console logging
    if (this.config.enableConsoleLogging) {
      this.logToConsole(logEntry);
    }

    // Remote logging
    if (this.config.enableRemoteLogging) {
      this.addToBuffer(logEntry);
    }
  }

  /**
   * Check if log level should be processed
   */
  private shouldLog(level: string): boolean {
    const levels = ['debug', 'info', 'warn', 'error'];
    const configLevelIndex = levels.indexOf(this.config.logLevel);
    const logLevelIndex = levels.indexOf(level);
    return logLevelIndex >= configLevelIndex;
  }

  /**
   * Log to console with structured format
   */
  private logToConsole(logEntry: BaseLogEntry): void {
    const { level, message, context, category, subcategory } = logEntry;
    const prefix = `[${level.toUpperCase()}] [${category}${subcategory ? `:${subcategory}` : ''}] [${context.correlationId}]`;
    
    const logData = {
      ...logEntry,
      context
    };

    switch (level) {
      case 'debug':
        console.debug(prefix, message, logData);
        break;
      case 'info':
        console.info(prefix, message, logData);
        break;
      case 'warn':
        console.warn(prefix, message, logData);
        break;
      case 'error':
        console.error(prefix, message, logData);
        break;
    }
  }

  /**
   * Add log entry to buffer for remote logging
   */
  private addToBuffer(logEntry: BaseLogEntry): void {
    this.logBuffer.push(logEntry);
    
    if (this.logBuffer.length >= (this.config.batchSize || 50)) {
      this.flushLogs();
    }
  }

  /**
   * Flush logs to remote endpoint
   */
  private async flushLogs(): Promise<void> {
    if (this.logBuffer.length === 0 || !this.config.remoteEndpoint) {
      return;
    }

    const logsToSend = [...this.logBuffer];
    this.logBuffer = [];

    try {
      await fetch(this.config.remoteEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          logs: logsToSend,
          timestamp: new Date().toISOString(),
          source: 'frontend'
        })
      });

    } catch (error) {
      console.error('Failed to send logs to remote endpoint:', error);
      // Re-add logs to buffer for retry
      this.logBuffer.unshift(...logsToSend);
    }
  }

  /**
   * Start automatic log flushing
   */
  private startAutoFlush(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushTimer = setInterval(() => {
      this.flushLogs();
    }, this.config.flushInterval);
  }

  /**
   * Stop automatic log flushing
   */
  stopAutoFlush(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = undefined;
    }
  }

  /**
   * Manually flush all pending logs
   */
  async flush(): Promise<void> {
    await this.flushLogs();
  }

  /**
   * Update logger configuration
   */
  updateConfig(newConfig: Partial<LoggerConfig>): void {
    this.config = { ...this.config, ...newConfig };
    
    if (this.config.enableRemoteLogging && this.config.flushInterval) {
      this.startAutoFlush();
    } else {
      this.stopAutoFlush();
    }
  }

  /**
   * Get current configuration
   */
  getConfig(): LoggerConfig {
    return { ...this.config };
  }

  /**
   * Determine connectivity subcategory based on data and error
   */
  private determineConnectivitySubcategory(
    connectionData: unknown,
    error?: Error
  ): 'request' | 'retry' | 'timeout' | 'circuit_breaker' {
    const data = connectionData as { retryAttempt?: number };
    if (data.retryAttempt && data.retryAttempt > 0) {
      return 'retry';
    }
    if (error?.message.includes('timeout') || error?.name === 'TimeoutError') {
      return 'timeout';
    }
    if (error?.message.includes('circuit') || error?.message.includes('breaker')) {
      return 'circuit_breaker';
    }
    return 'request';
  }

  /**
   * Sanitize email for logging (hash or mask)
   */
  private sanitizeEmail(email: string): string {
    // In production, consider hashing the email
    const [local, domain] = email.split('@');
    if (local.length <= 2) {
      return `${local}***@${domain}`;
    }
    return `${local.substring(0, 2)}***@${domain}`;
  }

  /**
   * Get current user ID from session/context
   */
  private getCurrentUserId(): string | undefined {
    if (typeof window !== 'undefined') {
      // Try to get from session storage or auth context
      return sessionStorage.getItem('userId') || undefined;
    }
    return undefined;
  }

  /**
   * Get current session ID
   */
  private getSessionId(): string | undefined {
    if (typeof window !== 'undefined') {
      return sessionStorage.getItem('sessionId') || undefined;
    }
    return undefined;
  }
}

// Export singleton instance
export const connectivityLogger = ConnectivityLogger.getInstance();

// Export class for testing
export { ConnectivityLogger };
