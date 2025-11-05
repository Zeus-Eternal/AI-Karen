/**
 * Diagnostic and Logging Utilities for AI Karen Web UI
 * Provides detailed logging for endpoint connectivity and network diagnostics
 */

import { webUIConfig } from './config';

export interface DiagnosticInfo {
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  category: 'network' | 'cors' | 'auth' | 'api' | 'health' | 'config';
  message: string;
  details?: Record<string, any>;
  endpoint?: string;
  duration?: number;
  error?: Error | string;
  troubleshooting?: TroubleshootingInfo;
}

export interface TroubleshootingInfo {
  possibleCauses: string[];
  suggestedFixes: string[];
  documentationLinks: string[];
  relatedErrors?: string[];
}

export interface NetworkDiagnostic {
  endpoint: string;
  method: string;
  status: 'success' | 'error' | 'timeout' | 'cors' | 'network';
  statusCode?: number;
  responseTime: number;
  timestamp: string;
  headers?: Record<string, string>;
  error?: string;
  corsInfo?: CORSInfo;
  networkInfo?: NetworkInfo;
}

export interface CORSInfo {
  origin: string;
  allowedOrigins?: string[];
  allowedMethods?: string[];
  allowedHeaders?: string[];
  preflightRequired: boolean;
  preflightStatus?: number;
  corsError?: string;
}

export interface NetworkInfo {
  userAgent: string;
  connectionType?: string;
  isOnline: boolean;
  protocol: string;
  host: string;
  port: string;
  dnsResolution?: boolean;
  tcpConnection?: boolean;
}

type LogLevel = DiagnosticInfo['level'];
type LogCategory = DiagnosticInfo['category'];

const LEVEL_PRIORITY: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

function safeNowISO(): string {
  try {
    return new Date().toISOString();
  } catch {
    return '' + Date.now();
  }
}

function pickLogLevelFromConfig(): LogLevel {
  const lvl = (webUIConfig as any)?.logLevel;
  if (lvl === 'debug' || lvl === 'info' || lvl === 'warn' || lvl === 'error') return lvl;
  return 'info';
}

function sanitizeForConsole(obj: Record<string, any>): Record<string, any> {
  const copy: Record<string, any> = {};
  for (const [k, v] of Object.entries(obj)) {
    if (v === undefined) continue;
    if (v instanceof Error) {
      copy[k] = { name: v.name, message: v.message, stack: v.stack };
    } else {
      copy[k] = v;
    }
  }
  return copy;
}

export class DiagnosticLogger {
  private logs: DiagnosticInfo[] = [];
  private maxLogs = 1000;
  private listeners: Array<(log: DiagnosticInfo) => void> = [];

  constructor() {
    this.logSystemInfo();
  }

  /**
   * Log system information on startup
   */
  private logSystemInfo(): void {
    const runtime = {
      userAgent:
        typeof navigator !== 'undefined' && navigator?.userAgent
          ? navigator.userAgent
          : 'server',
      url: typeof window !== 'undefined' && (window as any)?.location?.href
        ? (window as any).location.href
        : 'server',
      online: typeof navigator !== 'undefined' && 'onLine' in navigator ? !!navigator.onLine : true,
      timestamp: safeNowISO(),
    };

    this.log(
      'info',
      'config',
      'Diagnostic logger initialized',
      {
        config: {
          backendUrl: webUIConfig.backendUrl,
          environment: webUIConfig.environment,
          networkMode: webUIConfig.networkMode,
          debugLogging: webUIConfig.debugLogging,
          healthChecksEnabled: webUIConfig.enableHealthChecks,
          logLevel: pickLogLevelFromConfig(),
        },
        runtime,
      }
    );
  }

  /**
   * Log a diagnostic message
   */
  public log(
    level: LogLevel,
    category: LogCategory,
    message: string,
    details?: Record<string, any>,
    endpoint?: string,
    duration?: number,
    error?: Error | string,
    troubleshooting?: TroubleshootingInfo
  ): void {
    const logEntry: DiagnosticInfo = {
      timestamp: safeNowISO(),
      level,
      category,
      message,
      details,
      endpoint,
      duration,
      error: error instanceof Error ? error.message : error,
      troubleshooting,
    };

    // Add newest first
    this.logs.unshift(logEntry);

    // Trim to maxLogs
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(0, this.maxLogs);
    }

    // Console emission
    if (this.shouldLog(level)) {
      this.consoleLog(logEntry);
    }

    // Notify listeners (fault-isolated)
    this.notifyListeners(logEntry);
  }

  /**
   * Dynamic logging threshold and debug toggle
   */
  private shouldLog(level: LogLevel): boolean {
    if (!webUIConfig.debugLogging && level === 'debug') return false;

    const configLevelPriority = LEVEL_PRIORITY[pickLogLevelFromConfig()];
    const logLevelPriority = LEVEL_PRIORITY[level];
    return logLevelPriority >= configLevelPriority;
  }

  /**
   * Output to console with appropriate formatting
   */
  private consoleLog(log: DiagnosticInfo): void {
    const prefix = `🔍 [${log.category.toUpperCase()}]`;
    const t = new Date(log.timestamp);
    const timestamp = isNaN(t.getTime()) ? log.timestamp : t.toLocaleTimeString();
    const msg = `${timestamp} ${prefix} ${log.message}`;

    const payload = sanitizeForConsole({
      endpoint: log.endpoint,
      duration: typeof log.duration === 'number' ? `${log.duration}ms` : undefined,
      details: log.details,
      error: log.error,
      troubleshooting: log.troubleshooting,
    });

    // Route based on level (network "error" -> warn to reduce dev noise)
    switch (log.level) {
      case 'debug':
        console.debug(msg, payload);
        break;
      case 'info':
        console.info(msg, payload);
        break;
      case 'warn':
        console.warn(msg, payload);
        break;
      case 'error':
        if (log.category === 'network') {
          console.warn(msg, payload);
        } else {
          console.error(msg, payload);
        }
        break;
    }
  }

  /**
   * Notify listeners of new log entries
   */
  private notifyListeners(log: DiagnosticInfo): void {
    for (const listener of this.listeners) {
      try {
        listener(log);
      } catch (err) {
        // Listener failures shouldn't cascade
        console.error('Error in diagnostic log listener:', err);
      }
    }
  }

  /**
   * Log endpoint connectivity attempt
   */
  public logEndpointAttempt(
    endpoint: string,
    method: string,
    startTime: number,
    success: boolean,
    statusCode?: number,
    error?: Error | string,
    headers?: Record<string, string>
  ): void {
    const duration = Date.now() - startTime;
    const isNetworkIssue = !success && (!statusCode || statusCode === 0);
    const isClientError = !success && statusCode ? Math.floor(statusCode / 100) === 4 : false;

    const level: LogLevel = success ? 'info' : (isNetworkIssue || isClientError ? 'warn' : 'error');
    const message = success
      ? `Endpoint connectivity successful: ${method} ${endpoint}`
      : isNetworkIssue
        ? `Network connectivity failed: ${method} ${endpoint}`
        : `Endpoint connectivity failed: ${method} ${endpoint}`;

    const troubleshooting = success
      ? undefined
      : this.generateEndpointTroubleshooting(endpoint, statusCode, error);

    this.log(
      level,
      'network',
      message,
      { method, statusCode, headers, responseTime: duration },
      endpoint,
      duration,
      error,
      troubleshooting
    );
  }

  /**
   * Log CORS-related issues
   */
  public logCORSIssue(
    endpoint: string,
    origin: string,
    error: Error | string,
    corsInfo?: Partial<CORSInfo>
  ): void {
    const message = `CORS error detected for ${endpoint}`;
    const troubleshooting = this.generateCORSTroubleshooting(origin, corsInfo);

    this.log('error', 'cors', message, { origin, corsInfo }, endpoint, undefined, error, troubleshooting);
  }

  /**
   * Log network diagnostic information
   */
  public logNetworkDiagnostic(diagnostic: NetworkDiagnostic): void {
    const level: LogLevel = diagnostic.status === 'success' ? 'info' : 'error';
    const message = `Network diagnostic: ${diagnostic.method} ${diagnostic.endpoint} - ${diagnostic.status}`;

    const troubleshooting =
      diagnostic.status !== 'success' ? this.generateNetworkTroubleshooting(diagnostic) : undefined;

    this.log(
      level,
      'network',
      message,
      {
        method: diagnostic.method,
        status: diagnostic.status,
        statusCode: diagnostic.statusCode,
        responseTime: diagnostic.responseTime,
        headers: diagnostic.headers,
        corsInfo: diagnostic.corsInfo,
        networkInfo: diagnostic.networkInfo,
      },
      diagnostic.endpoint,
      diagnostic.responseTime,
      diagnostic.error,
      troubleshooting
    );
  }

  /**
   * Generate troubleshooting information for endpoint issues
   */
  private generateEndpointTroubleshooting(
    endpoint: string,
    statusCode?: number,
    error?: Error | string
  ): TroubleshootingInfo {
    const possibleCauses: string[] = [];
    const suggestedFixes: string[] = [];
    const documentationLinks: string[] = [];

    if (!statusCode || statusCode === 0) {
      possibleCauses.push('Backend server is not running');
      possibleCauses.push('Incorrect backend URL or port');
      possibleCauses.push('CORS policy or network restrictions are blocking the request');
      possibleCauses.push('API route is missing or mismatched');

      suggestedFixes.push('Start the backend server and ensure it listens on the expected port');
      suggestedFixes.push('Verify the webUI backendUrl points to the correct host and port');
      suggestedFixes.push('Allow requests from the web UI origin in CORS settings and check network/firewall rules');
      suggestedFixes.push('Confirm the backend exposes the requested API route');
    }

    if (statusCode) {
      switch (Math.floor(statusCode / 100)) {
        case 4:
          possibleCauses.push('Client-side error (4xx status code)');
          if (statusCode === 404) {
            possibleCauses.push('Endpoint not found or incorrect URL');
            suggestedFixes.push('Verify the endpoint URL is correct');
            suggestedFixes.push('Check if the backend service is running');
          } else if (statusCode === 401) {
            possibleCauses.push('Authentication required or invalid credentials');
            suggestedFixes.push('Check API key or authentication token');
            suggestedFixes.push('Verify authentication headers are included');
          } else if (statusCode === 403) {
            possibleCauses.push('Access forbidden - insufficient permissions');
            suggestedFixes.push('Check user permissions and roles');
          }
          break;
        case 5:
          possibleCauses.push('Server-side error (5xx status code)');
          possibleCauses.push('Backend service may be experiencing issues');
          suggestedFixes.push('Check backend service logs');
          suggestedFixes.push('Verify backend service is healthy');
          suggestedFixes.push('Try again after a short delay');
          break;
      }
    }

    const errorMessage = error instanceof Error ? error.message : String(error || '');
    if (errorMessage.toLowerCase().includes('cors')) {
      possibleCauses.push('Cross-Origin Resource Sharing (CORS) policy violation');
      suggestedFixes.push('Check CORS configuration on the backend');
      suggestedFixes.push('Verify the origin is allowed in CORS settings');
    }

    if (errorMessage.toLowerCase().includes('timeout')) {
      possibleCauses.push('Request timeout - server took too long to respond');
      suggestedFixes.push('Increase timeout configuration');
      suggestedFixes.push('Check network connectivity');
      suggestedFixes.push('Verify backend service performance');
    }

    if (errorMessage.toLowerCase().includes('network')) {
      possibleCauses.push('Network connectivity issue');
      suggestedFixes.push('Check internet connection');
      suggestedFixes.push('Verify backend service is accessible');
      suggestedFixes.push('Check firewall and proxy settings');
    }

    if (possibleCauses.length === 0) {
      possibleCauses.push('Unknown connectivity issue');
      suggestedFixes.push('Check network connectivity');
      suggestedFixes.push('Verify backend service is running');
      suggestedFixes.push('Check browser console for additional errors');
    }

    documentationLinks.push('https://developer.mozilla.org/en-US/docs/Web/HTTP/Status');
    documentationLinks.push('https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS');

    return {
      possibleCauses,
      suggestedFixes,
      documentationLinks,
    };
  }

  /**
   * Generate troubleshooting information for CORS issues
   */
  private generateCORSTroubleshooting(
    origin: string,
    corsInfo?: Partial<CORSInfo>
  ): TroubleshootingInfo {
    const possibleCauses = [
      'Backend CORS configuration does not allow the current origin',
      'Preflight request failed or not properly handled',
      'Required CORS headers are missing from the response',
      'CORS policy is too restrictive for the requested operation',
    ];

    const suggestedFixes = [
      `Add "${origin}" to the allowed origins in backend CORS configuration`,
      'Check if preflight OPTIONS requests are properly handled',
      'Verify CORS headers are included in all responses',
      'Review and update CORS middleware configuration',
      'Check for wildcard (*) origin restrictions in production',
    ];

    const documentationLinks = [
      'https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS',
      'https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS/Errors',
      'https://web.dev/cross-origin-resource-sharing/',
    ];

    if (corsInfo?.preflightRequired) {
      possibleCauses.push('Preflight request is required but failing');
      suggestedFixes.push('Ensure OPTIONS method is allowed for the endpoint');
      suggestedFixes.push('Check preflight response headers');
    }

    return {
      possibleCauses,
      suggestedFixes,
      documentationLinks,
    };
  }

  /**
   * Generate troubleshooting information for network issues
   */
  private generateNetworkTroubleshooting(diagnostic: NetworkDiagnostic): TroubleshootingInfo {
    const possibleCauses: string[] = [];
    const suggestedFixes: string[] = [];
    const documentationLinks: string[] = [];

    switch (diagnostic.status) {
      case 'timeout':
        possibleCauses.push('Request timeout - server response too slow');
        possibleCauses.push('Network latency or connectivity issues');
        suggestedFixes.push('Increase timeout configuration');
        suggestedFixes.push('Check network connection quality');
        suggestedFixes.push('Verify backend service performance');
        break;
      case 'cors':
        possibleCauses.push('CORS policy violation');
        suggestedFixes.push('Update backend CORS configuration');
        suggestedFixes.push('Check allowed origins and methods');
        break;
      case 'network':
        possibleCauses.push('Network connectivity failure');
        possibleCauses.push('DNS resolution issues');
        possibleCauses.push('Firewall or proxy blocking requests');
        suggestedFixes.push('Check internet connection');
        suggestedFixes.push('Verify DNS settings');
        suggestedFixes.push('Check firewall and proxy configuration');
        break;
      case 'error':
        possibleCauses.push('General request error');
        suggestedFixes.push('Check backend service status');
        suggestedFixes.push('Review error details for specific issues');
        break;
    }

    documentationLinks.push('https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API');
    documentationLinks.push('https://developer.mozilla.org/en-US/docs/Web/HTTP/Status');

    return {
      possibleCauses,
      suggestedFixes,
      documentationLinks,
    };
  }

  /**
   * Get recent logs
   */
  public getLogs(limit: number = 100, category?: LogCategory): DiagnosticInfo[] {
    let logs = this.logs;
    if (category) logs = logs.filter((l) => l.category === category);
    return logs.slice(0, Math.max(0, limit));
  }

  /**
   * Get logs by level
   */
  public getLogsByLevel(level: LogLevel, limit: number = 50): DiagnosticInfo[] {
    return this.logs.filter((l) => l.level === level).slice(0, Math.max(0, limit));
  }

  /**
   * Get error logs with troubleshooting info
   */
  public getErrorLogs(limit: number = 50): DiagnosticInfo[] {
    return this.logs.filter((l) => l.level === 'error').slice(0, Math.max(0, limit));
  }

  /**
   * Clear logs
   */
  public clearLogs(): void {
    this.logs = [];
    this.log('info', 'config', 'Diagnostic logs cleared');
  }

  /**
   * Add a log listener
   */
  public onLog(listener: (log: DiagnosticInfo) => void): () => void {
    this.listeners.push(listener);
    return () => {
      const idx = this.listeners.indexOf(listener);
      if (idx > -1) this.listeners.splice(idx, 1);
    };
  }

  /**
   * Export logs for debugging
   */
  public exportLogs(): string {
    return JSON.stringify(
      {
        exportTime: safeNowISO(),
        config: {
          backendUrl: webUIConfig.backendUrl,
          environment: webUIConfig.environment,
          networkMode: webUIConfig.networkMode,
          logLevel: pickLogLevelFromConfig(),
        },
        logs: this.logs,
      },
      null,
      2
    );
  }

  /**
   * Get diagnostic summary
   */
  public getSummary(): {
    totalLogs: number;
    errorCount: number;
    warningCount: number;
    categories: Record<string, number>;
    recentErrors: DiagnosticInfo[];
  } {
    const categories: Record<string, number> = {};
    let errorCount = 0;
    let warningCount = 0;

    for (const log of this.logs) {
      categories[log.category] = (categories[log.category] || 0) + 1;
      if (log.level === 'error') errorCount++;
      if (log.level === 'warn') warningCount++;
    }

    return {
      totalLogs: this.logs.length,
      errorCount,
      warningCount,
      categories,
      recentErrors: this.getErrorLogs(5),
    };
  }
}

// Global diagnostic logger instance (singleton)
let diagnosticLogger: DiagnosticLogger | null = null;

export function getDiagnosticLogger(): DiagnosticLogger {
  if (!diagnosticLogger) {
    diagnosticLogger = new DiagnosticLogger();
  }
  return diagnosticLogger;
}

export function initializeDiagnosticLogger(): DiagnosticLogger {
  diagnosticLogger = new DiagnosticLogger();
  return diagnosticLogger;
}

// Convenience functions
export function logEndpointAttempt(
  endpoint: string,
  method: string,
  startTime: number,
  success: boolean,
  statusCode?: number,
  error?: Error | string,
  headers?: Record<string, string>
): void {
  getDiagnosticLogger().logEndpointAttempt(endpoint, method, startTime, success, statusCode, error, headers);
}

export function logCORSIssue(
  endpoint: string,
  origin: string,
  error: Error | string,
  corsInfo?: Partial<CORSInfo>
): void {
  getDiagnosticLogger().logCORSIssue(endpoint, origin, error, corsInfo);
}

export function logNetworkDiagnostic(diagnostic: NetworkDiagnostic): void {
  getDiagnosticLogger().logNetworkDiagnostic(diagnostic);
}
