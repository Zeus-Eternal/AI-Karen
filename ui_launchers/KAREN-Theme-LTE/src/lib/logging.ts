/**
 * Logging Utilities
 * Centralized logging functionality for the application
 */

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  FATAL = 4
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: string;
  data?: unknown;
  userId?: string;
  sessionId?: string;
  component?: string;
  stack?: string;
}

export interface LogContext {
  userId?: string;
  sessionId?: string;
  component?: string;
  operation?: string;
  requestId?: string;
  metadata?: Record<string, unknown>;
}

export interface Logger {
  debug: (message: string, context?: LogContext) => void;
  info: (message: string, context?: LogContext) => void;
  warn: (message: string, context?: LogContext) => void;
  error: (message: string, context?: LogContext) => void;
  fatal: (message: string, context?: LogContext) => void;
  setContext: (context: LogContext) => void;
  clearContext: () => void;
  getLogs: (level?: LogLevel, limit?: number) => LogEntry[];
  export: (level?: LogLevel) => LogEntry[];
}

export class LoggerImpl implements Logger {
  private context: LogContext = {};
  private logs: LogEntry[] = [];
  private maxLogs = 10000;
  private currentLogLevel: LogLevel = LogLevel.INFO;

  constructor(initialLevel: LogLevel = LogLevel.INFO) {
    this.currentLogLevel = initialLevel;
  }

  debug(message: string, context?: LogContext): void {
    this.log(LogLevel.DEBUG, message, context);
  }

  info(message: string, context?: LogContext): void {
    this.log(LogLevel.INFO, message, context);
  }

  warn(message: string, context?: LogContext): void {
    this.log(LogLevel.WARN, message, context);
  }

  error(message: string, context?: LogContext): void {
    this.log(LogLevel.ERROR, message, context);
  }

  fatal(message: string, context?: LogContext): void {
    this.log(LogLevel.FATAL, message, context);
  }

  setContext(context: LogContext): void {
    this.context = { ...this.context, ...context };
  }

  clearContext(): void {
    this.context = {};
  }

  private log(level: LogLevel, message: string, context?: LogContext): void {
    if (level < this.currentLogLevel) {
      return;
    }

    const logEntry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context: context ? JSON.stringify(context) : this.context.component,
      data: context?.metadata,
      userId: context?.userId || this.context.userId,
      sessionId: context?.sessionId || this.context.sessionId,
      component: context?.component || this.context.component,
      stack: level >= LogLevel.ERROR ? new Error().stack : undefined
    };

    this.logs.push(logEntry);

    // Keep only the last maxLogs entries
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // Console output
    const consoleMethod = this.getConsoleMethod(level);
    const contextStr = context ? ` [${context.component || 'Unknown'}]` : '';
    consoleMethod(`${message}${contextStr}`, logEntry);
  }

  private getConsoleMethod(level: LogLevel): (...args: unknown[]) => void {
    switch (level) {
      case LogLevel.DEBUG:
        return console.debug || console.log;
      case LogLevel.INFO:
        return console.info || console.log;
      case LogLevel.WARN:
        return console.warn;
      case LogLevel.ERROR:
        return console.error;
      case LogLevel.FATAL:
        return console.error;
      default:
        return console.log;
    }
  }

  getLogs(level?: LogLevel, limit?: number): LogEntry[] {
    let filteredLogs = this.logs;
    
    if (level !== undefined) {
      filteredLogs = this.logs.filter(log => log.level >= level);
    }

    if (limit && limit > 0) {
      filteredLogs = filteredLogs.slice(-limit);
    }

    return filteredLogs;
  }

  getAllLogs(): LogEntry[] {
    return [...this.logs];
  }

  clearLogs(): void {
    this.logs = [];
  }

  export(): LogEntry[] {
    return [...this.logs];
  }

  setLogLevel(level: LogLevel): void {
    this.currentLogLevel = level;
  }
}

// Create default logger instance
export const logger = new LoggerImpl();

// Create specialized loggers
export const createLogger = (component?: string, initialLevel?: LogLevel): Logger => {
  const specializedLogger = new LoggerImpl(initialLevel);
  if (component) {
    specializedLogger.setContext({ component });
  }
  return specializedLogger;
};

// Export convenience functions
export const logDebug = (message: string, context?: LogContext) => logger.debug(message, context);
export const logInfo = (message: string, context?: LogContext) => logger.info(message, context);
export const logWarn = (message: string, context?: LogContext) => logger.warn(message, context);
export const logError = (message: string, context?: LogContext) => logger.error(message, context);
export const logFatal = (message: string, context?: LogContext) => logger.fatal(message, context);

// LogLevel is already exported above, no need to re-export