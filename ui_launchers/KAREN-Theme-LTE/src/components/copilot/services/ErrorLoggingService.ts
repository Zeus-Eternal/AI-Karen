import { ErrorInfo, ErrorCategory, ErrorSeverity } from './ErrorHandlingService';

/**
 * Log entry structure
 */
export interface LogEntry {
  /** Unique log ID */
  id: string;
  
  /** Log timestamp */
  timestamp: Date;
  
  /** Log level */
  level: LogLevel;
  
  /** Log message */
  message: string;
  
  /** Log category */
  category: LogCategory;
  
  /** Additional data */
  data?: any;
  
  /** Error information if this is an error log */
  error?: ErrorInfo;
  
  /** User ID if available */
  userId?: string;
  
  /** Session ID if available */
  sessionId?: string;
  
  /** Component where the log originated */
  component?: string;
  
  /** Function where the log originated */
  function?: string;
}

/**
 * Log levels
 */
export enum LogLevel {
  /** Debug information */
  DEBUG = 'debug',
  
  /** General information */
  INFO = 'info',
  
  /** Warning information */
  WARN = 'warn',
  
  /** Error information */
  ERROR = 'error'
}

/**
 * Log categories
 */
export enum LogCategory {
  /** Application logs */
  APPLICATION = 'application',
  
  /** Network logs */
  NETWORK = 'network',
  
  /** API logs */
  API = 'api',
  
  /** Authentication logs */
  AUTH = 'auth',
  
  /** Database logs */
  DATABASE = 'database',
  
  /** Performance logs */
  PERFORMANCE = 'performance',
  
  /** Security logs */
  SECURITY = 'security',
  
  /** UI logs */
  UI = 'ui',
  
  /** Extension logs */
  EXTENSION = 'extension',
  
  /** System logs */
  SYSTEM = 'system'
}

/**
 * Analytics event structure
 */
export interface AnalyticsEvent {
  /** Event name */
  name: string;
  
  /** Event timestamp */
  timestamp: Date;
  
  /** Event properties */
  properties?: Record<string, any>;
  
  /** User ID if available */
  userId?: string;
  
  /** Session ID if available */
  sessionId?: string;
  
  /** Event value (numeric) */
  value?: number;
  
  /** Event duration in milliseconds */
  duration?: number;
}

/**
 * Error metrics
 */
export interface ErrorMetrics {
  /** Total number of errors */
  totalErrors: number;
  
  /** Number of errors by category */
  errorsByCategory: Record<ErrorCategory, number>;
  
  /** Number of errors by severity */
  errorsBySeverity: Record<ErrorSeverity, number>;
  
  /** Number of errors by component */
  errorsByComponent: Record<string, number>;
  
  /** Number of errors over time */
  errorsOverTime: Array<{
    timestamp: Date;
    count: number;
  }>;
  
  /** Average time to resolve errors in milliseconds */
  averageResolutionTime: number;
  
  /** Number of resolved errors */
  resolvedErrors: number;
  
  /** Error rate (errors per hour) */
  errorRate: number;
}

/**
 * Performance metrics
 */
export interface PerformanceMetrics {
  /** Average response time in milliseconds */
  averageResponseTime: number;
  
  /** 90th percentile response time in milliseconds */
  p90ResponseTime: number;
  
  /** 95th percentile response time in milliseconds */
  p95ResponseTime: number;
  
  /** 99th percentile response time in milliseconds */
  p99ResponseTime: number;
  
  /** Request count */
  requestCount: number;
  
  /** Error count */
  errorCount: number;
  
  /** Success rate (0-1) */
  successRate: number;
  
  /** Throughput (requests per minute) */
  throughput: number;
}

/**
 * Service for comprehensive error logging and analytics
 */
class ErrorLoggingService {
  private static instance: ErrorLoggingService;
  private logs: LogEntry[] = [];
  private analyticsEvents: AnalyticsEvent[] = [];
  private errorMetrics!: ErrorMetrics;
  private performanceMetrics!: PerformanceMetrics;
  private logListeners: Map<string, Function[]> = new Map();
  private analyticsListeners: Map<string, Function[]> = new Map();
  private maxLogEntries: number = 1000;
  private maxAnalyticsEvents: number = 1000;
  
  private constructor() {
    this.initializeMetrics();
  }
  
  public static getInstance(): ErrorLoggingService {
    if (!ErrorLoggingService.instance) {
      ErrorLoggingService.instance = new ErrorLoggingService();
    }
    return ErrorLoggingService.instance;
  }
  
  /**
   * Initialize metrics
   */
  private initializeMetrics(): void {
    this.errorMetrics = {
      totalErrors: 0,
      errorsByCategory: {} as Record<ErrorCategory, number>,
      errorsBySeverity: {} as Record<ErrorSeverity, number>,
      errorsByComponent: {},
      errorsOverTime: [],
      averageResolutionTime: 0,
      resolvedErrors: 0,
      errorRate: 0
    };
    
    // Initialize error category and severity counts
    Object.values(ErrorCategory).forEach(category => {
      this.errorMetrics.errorsByCategory[category] = 0;
    });
    
    Object.values(ErrorSeverity).forEach(severity => {
      this.errorMetrics.errorsBySeverity[severity] = 0;
    });
    
    this.performanceMetrics = {
      averageResponseTime: 0,
      p90ResponseTime: 0,
      p95ResponseTime: 0,
      p99ResponseTime: 0,
      requestCount: 0,
      errorCount: 0,
      successRate: 1,
      throughput: 0
    };
  }
  
  /**
   * Log a message
   */
  public log(
    level: LogLevel,
    message: string,
    category: LogCategory = LogCategory.APPLICATION,
    data?: any,
    context?: {
      userId?: string;
      sessionId?: string;
      component?: string;
      function?: string;
    }
  ): void {
    const logEntry: LogEntry = {
      id: this.generateLogId(),
      timestamp: new Date(),
      level,
      message,
      category,
      data,
      userId: context?.userId,
      sessionId: context?.sessionId,
      component: context?.component,
      function: context?.function
    };
    
    // Add to logs
    this.logs.push(logEntry);
    
    // Trim logs if necessary
    if (this.logs.length > this.maxLogEntries) {
      this.logs = this.logs.slice(-this.maxLogEntries);
    }
    
    // Emit log event
    this.emitLogEvent('log_added', { logEntry });
    
    // Also log to console
    this.logToConsole(logEntry);
  }
  
  /**
   * Log an error
   */
  public logError(
    errorInfo: ErrorInfo,
    context?: {
      userId?: string;
      sessionId?: string;
      component?: string;
      function?: string;
    }
  ): void {
    const logEntry: LogEntry = {
      id: this.generateLogId(),
      timestamp: new Date(),
      level: LogLevel.ERROR,
      message: errorInfo.message,
      category: this.mapErrorCategoryToLogCategory(errorInfo.category),
      error: errorInfo,
      userId: context?.userId,
      sessionId: context?.sessionId,
      component: context?.component || errorInfo.context?.component,
      function: context?.function || errorInfo.context?.function
    };
    
    // Add to logs
    this.logs.push(logEntry);
    
    // Trim logs if necessary
    if (this.logs.length > this.maxLogEntries) {
      this.logs = this.logs.slice(-this.maxLogEntries);
    }
    
    // Update error metrics
    this.updateErrorMetrics(errorInfo);
    
    // Emit log event
    this.emitLogEvent('error_logged', { logEntry });
    
    // Also log to console
    this.logToConsole(logEntry);
  }
  
  /**
   * Track an analytics event
   */
  public trackEvent(
    name: string,
    properties?: Record<string, any>,
    context?: {
      userId?: string;
      sessionId?: string;
      value?: number;
      duration?: number;
    }
  ): void {
    const event: AnalyticsEvent = {
      name,
      timestamp: new Date(),
      properties,
      userId: context?.userId,
      sessionId: context?.sessionId,
      value: context?.value,
      duration: context?.duration
    };
    
    // Add to analytics events
    this.analyticsEvents.push(event);
    
    // Trim analytics events if necessary
    if (this.analyticsEvents.length > this.maxAnalyticsEvents) {
      this.analyticsEvents = this.analyticsEvents.slice(-this.maxAnalyticsEvents);
    }
    
    // Emit analytics event
    this.emitAnalyticsEvent('event_tracked', { event });
  }
  
  /**
   * Track performance metrics
   */
  public trackPerformance(
    responseTime: number,
    success: boolean = true,
    context?: {
      userId?: string;
      sessionId?: string;
      endpoint?: string;
      method?: string;
    }
  ): void {
    // Update performance metrics
    this.updatePerformanceMetrics(responseTime, success);
    
    // Track as analytics event
    this.trackEvent('performance', {
      responseTime,
      success,
      endpoint: context?.endpoint,
      method: context?.method
    }, {
      userId: context?.userId,
      sessionId: context?.sessionId,
      value: responseTime
    });
  }
  
  /**
   * Get logs
   */
  public getLogs(
    level?: LogLevel,
    category?: LogCategory,
    component?: string,
    limit?: number,
    offset?: number
  ): LogEntry[] {
    let filteredLogs = [...this.logs];
    
    // Filter by level
    if (level) {
      filteredLogs = filteredLogs.filter(log => log.level === level);
    }
    
    // Filter by category
    if (category) {
      filteredLogs = filteredLogs.filter(log => log.category === category);
    }
    
    // Filter by component
    if (component) {
      filteredLogs = filteredLogs.filter(log => log.component === component);
    }
    
    // Sort by timestamp (newest first)
    filteredLogs.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
    
    // Apply offset and limit
    if (offset) {
      filteredLogs = filteredLogs.slice(offset);
    }
    
    if (limit) {
      filteredLogs = filteredLogs.slice(0, limit);
    }
    
    return filteredLogs;
  }
  
  /**
   * Get analytics events
   */
  public getAnalyticsEvents(
    name?: string,
    limit?: number,
    offset?: number
  ): AnalyticsEvent[] {
    let filteredEvents = [...this.analyticsEvents];
    
    // Filter by name
    if (name) {
      filteredEvents = filteredEvents.filter(event => event.name === name);
    }
    
    // Sort by timestamp (newest first)
    filteredEvents.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
    
    // Apply offset and limit
    if (offset) {
      filteredEvents = filteredEvents.slice(offset);
    }
    
    if (limit) {
      filteredEvents = filteredEvents.slice(0, limit);
    }
    
    return filteredEvents;
  }
  
  /**
   * Get error metrics
   */
  public getErrorMetrics(): ErrorMetrics {
    return { ...this.errorMetrics };
  }
  
  /**
   * Get performance metrics
   */
  public getPerformanceMetrics(): PerformanceMetrics {
    return { ...this.performanceMetrics };
  }
  
  /**
   * Add log event listener
   */
  public addLogEventListener(eventType: string, listener: (event: any) => void): void {
    if (!this.logListeners.has(eventType)) {
      this.logListeners.set(eventType, []);
    }
    this.logListeners.get(eventType)?.push(listener);
  }
  
  /**
   * Remove log event listener
   */
  public removeLogEventListener(eventType: string, listener: (event: any) => void): void {
    const listeners = this.logListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
    }
  }
  
  /**
   * Add analytics event listener
   */
  public addAnalyticsEventListener(eventType: string, listener: (event: any) => void): void {
    if (!this.analyticsListeners.has(eventType)) {
      this.analyticsListeners.set(eventType, []);
    }
    this.analyticsListeners.get(eventType)?.push(listener);
  }
  
  /**
   * Remove analytics event listener
   */
  public removeAnalyticsEventListener(eventType: string, listener: (event: any) => void): void {
    const listeners = this.analyticsListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
    }
  }
  
  /**
   * Clear all logs
   */
  public clearLogs(): void {
    this.logs = [];
    this.emitLogEvent('logs_cleared', {});
  }
  
  /**
   * Clear all analytics events
   */
  public clearAnalyticsEvents(): void {
    this.analyticsEvents = [];
    this.emitAnalyticsEvent('analytics_cleared', {});
  }
  
  /**
   * Export logs to JSON
   */
  public exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }
  
  /**
   * Export analytics events to JSON
   */
  public exportAnalyticsEvents(): string {
    return JSON.stringify(this.analyticsEvents, null, 2);
  }
  
  /**
   * Set maximum log entries
   */
  public setMaxLogEntries(max: number): void {
    this.maxLogEntries = max;
    
    // Trim logs if necessary
    if (this.logs.length > this.maxLogEntries) {
      this.logs = this.logs.slice(-this.maxLogEntries);
    }
  }
  
  /**
   * Set maximum analytics events
   */
  public setMaxAnalyticsEvents(max: number): void {
    this.maxAnalyticsEvents = max;
    
    // Trim analytics events if necessary
    if (this.analyticsEvents.length > this.maxAnalyticsEvents) {
      this.analyticsEvents = this.analyticsEvents.slice(-this.maxAnalyticsEvents);
    }
  }
  
  /**
   * Generate a unique log ID
   */
  private generateLogId(): string {
    return `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  /**
   * Map error category to log category
   */
  private mapErrorCategoryToLogCategory(errorCategory: ErrorCategory): LogCategory {
    switch (errorCategory) {
      case ErrorCategory.NETWORK:
        return LogCategory.NETWORK;
      case ErrorCategory.API:
        return LogCategory.API;
      case ErrorCategory.AUTH:
        return LogCategory.AUTH;
      case ErrorCategory.UI:
        return LogCategory.UI;
      case ErrorCategory.EXTENSION:
        return LogCategory.EXTENSION;
      default:
        return LogCategory.APPLICATION;
    }
  }
  
  /**
   * Update error metrics
   */
  private updateErrorMetrics(errorInfo: ErrorInfo): void {
    // Increment total errors
    this.errorMetrics.totalErrors++;
    
    // Increment errors by category
    this.errorMetrics.errorsByCategory[errorInfo.category]++;
    
    // Increment errors by severity
    this.errorMetrics.errorsBySeverity[errorInfo.severity]++;
    
    // Increment errors by component
    const component = errorInfo.context?.component || 'unknown';
    this.errorMetrics.errorsByComponent[component] = (this.errorMetrics.errorsByComponent[component] || 0) + 1;
    
    // Add to errors over time
    const now = new Date();
    const timeSlot = new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours(), 0, 0, 0);
    
    const existingTimeSlot = this.errorMetrics.errorsOverTime.find(slot => 
      slot.timestamp.getTime() === timeSlot.getTime()
    );
    
    if (existingTimeSlot) {
      existingTimeSlot.count++;
    } else {
      this.errorMetrics.errorsOverTime.push({
        timestamp: timeSlot,
        count: 1
      });
    }
    
    // Keep only last 24 hours of error data
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    this.errorMetrics.errorsOverTime = this.errorMetrics.errorsOverTime.filter(slot => 
      slot.timestamp >= oneDayAgo
    );
    
    // Calculate error rate (errors per hour)
    const totalErrorsInLast24Hours = this.errorMetrics.errorsOverTime.reduce((sum, slot) => sum + slot.count, 0);
    this.errorMetrics.errorRate = totalErrorsInLast24Hours / 24;
    
    // Update resolved errors count
    if (errorInfo.resolved) {
      this.errorMetrics.resolvedErrors++;
      
      // Update average resolution time
      const resolutionTime = now.getTime() - errorInfo.firstOccurrence.getTime();
      const currentTotal = this.errorMetrics.averageResolutionTime * (this.errorMetrics.resolvedErrors - 1);
      this.errorMetrics.averageResolutionTime = (currentTotal + resolutionTime) / this.errorMetrics.resolvedErrors;
    }
  }
  
  /**
   * Update performance metrics
   */
  private updatePerformanceMetrics(responseTime: number, success: boolean): void {
    // Update request count
    this.performanceMetrics.requestCount++;
    
    // Update error count
    if (!success) {
      this.performanceMetrics.errorCount++;
    }
    
    // Update success rate
    this.performanceMetrics.successRate = 
      (this.performanceMetrics.requestCount - this.performanceMetrics.errorCount) / 
      this.performanceMetrics.requestCount;
    
    // Update average response time
    const currentTotal = this.performanceMetrics.averageResponseTime * (this.performanceMetrics.requestCount - 1);
    this.performanceMetrics.averageResponseTime = (currentTotal + responseTime) / this.performanceMetrics.requestCount;
    
    // For percentile calculations, we would need to store all response times
    // For simplicity, we'll just use approximations
    this.performanceMetrics.p90ResponseTime = this.performanceMetrics.averageResponseTime * 1.5;
    this.performanceMetrics.p95ResponseTime = this.performanceMetrics.averageResponseTime * 2;
    this.performanceMetrics.p99ResponseTime = this.performanceMetrics.averageResponseTime * 3;
    
    // Calculate throughput (requests per minute)
    // This would typically be calculated over a sliding window
    // For simplicity, we'll use a simple approximation
    this.performanceMetrics.throughput = this.performanceMetrics.requestCount / 
      (Date.now() / 60000);
  }
  
  /**
   * Log to console
   */
  private logToConsole(logEntry: LogEntry): void {
    const { level, message, data, error } = logEntry;
    const logData = {
      id: logEntry.id,
      timestamp: logEntry.timestamp,
      category: logEntry.category,
      component: logEntry.component,
      function: logEntry.function,
      userId: logEntry.userId,
      sessionId: logEntry.sessionId,
      data,
      error
    };
    
    switch (level) {
      case LogLevel.DEBUG:
        console.debug(`[DEBUG] ${message}`, logData);
        break;
      case LogLevel.INFO:
        console.info(`[INFO] ${message}`, logData);
        break;
      case LogLevel.WARN:
        console.warn(`[WARN] ${message}`, logData);
        break;
      case LogLevel.ERROR:
        console.error(`[ERROR] ${message}`, logData);
        break;
    }
  }
  
  /**
   * Emit log event
   */
  private emitLogEvent(eventType: string, data: any): void {
    const listeners = this.logListeners.get(eventType);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener({
            type: eventType,
            timestamp: new Date(),
            ...data
          });
        } catch (error) {
          console.error(`Error in log event listener for ${eventType}:`, error);
        }
      });
    }
  }
  
  /**
   * Emit analytics event
   */
  private emitAnalyticsEvent(eventType: string, data: any): void {
    const listeners = this.analyticsListeners.get(eventType);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener({
            type: eventType,
            timestamp: new Date(),
            ...data
          });
        } catch (error) {
          console.error(`Error in analytics event listener for ${eventType}:`, error);
        }
      });
    }
  }
}

export default ErrorLoggingService;