/**
 * Audit Logger
 * Enterprise security logging for compliance and monitoring
 */

interface AuditLogEntry {
  timestamp: Date;
  level: 'INFO' | 'WARN' | 'ERROR' | 'SECURITY';
  event: string;
  userId?: string;
  ip?: string;
  userAgent?: string;
  details: Record<string, unknown>;
  provider?: string;
  responseTime?: number;
  tokensUsed?: number;
  error?: string;
}

class AuditLogger {
  private logs: AuditLogEntry[] = [];
  private maxLogs = 1000; // Keep last 1000 logs in memory
  
  // Log levels with different retention policies
  private retentionMs = {
    'INFO': 7 * 24 * 60 * 60 * 1000, // 7 days
    'WARN': 30 * 24 * 60 * 60 * 1000, // 30 days
    'ERROR': 90 * 24 * 60 * 60 * 1000, // 90 days
    'SECURITY': 365 * 24 * 60 * 60 * 1000, // 1 year
  };
  
  async log(
    level: AuditLogEntry['level'],
    event: string,
    details: Record<string, unknown> = {},
    additional?: {
      userId?: string;
      ip?: string;
      userAgent?: string;
      provider?: string;
      responseTime?: number;
      tokensUsed?: number;
      error?: string;
    }
  ): Promise<void> {
    const entry: AuditLogEntry = {
      timestamp: new Date(),
      level,
      event,
      ...additional,
      details,
    };
    
    // Add to in-memory logs
    this.logs.push(entry);
    
    // Trim if exceeds max
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }
    
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      const logMethod = level === 'ERROR' ? 'error' : level === 'WARN' ? 'warn' : 'log';
      console[logMethod](`[AUDIT-${level}] ${event}`, {
        timestamp: entry.timestamp,
        details: entry.details,
        ...additional,
      });
    }
    
    // In production, would send to logging service
    // For now, also log to console
    if (process.env.NODE_ENV === 'production') {
      console.log(`[AUDIT-${level}] ${event}`, {
        timestamp: entry.timestamp,
        details: entry.details,
        ...additional,
      });
    }
    
    // TODO: Send to external logging service (Splunk, ELK, etc.)
    await this.persistLog(entry);
  }
  
  private async persistLog(entry: AuditLogEntry): Promise<void> {
    // In production, this would send to external logging service
    // For now, just log to console
    if (process.env.NODE_ENV === 'production') {
      // Could integrate with services like:
      // - AWS CloudWatch Logs
      // - Azure Monitor Logs
      // - Google Cloud Logging
      // - Splunk HTTP Collector
      // - Loggly
      // - Papertrail
      console.log('[AUDIT-PERSIST]', entry);
    }
  }
  
  // Get recent logs for monitoring
  getRecentLogs(count: number = 100, level?: AuditLogEntry['level']): AuditLogEntry[] {
    let filtered = this.logs;
    
    if (level) {
      filtered = this.logs.filter(log => log.level === level);
    }
    
    return filtered.slice(-count);
  }
  
  // Get logs by time range
  getLogsByTimeRange(startTime: Date, endTime: Date): AuditLogEntry[] {
    return this.logs.filter(log => 
      log.timestamp >= startTime && log.timestamp <= endTime
    );
  }
  
  // Get security events
  getSecurityEvents(): AuditLogEntry[] {
    return this.logs.filter(log => log.level === 'SECURITY');
  }
  
  // Get error events
  getErrorEvents(): AuditLogEntry[] {
    return this.logs.filter(log => log.level === 'ERROR');
  }
  
  // Clear old logs
  clearOldLogs(): void {
    const now = Date.now();
    const cutoffTime = now - (90 * 24 * 60 * 60 * 1000); // 90 days ago
    
    this.logs = this.logs.filter(log => 
      log.timestamp.getTime() > cutoffTime
    );
  }
  
  // Export logs for analysis
  exportLogs(): AuditLogEntry[] {
    return [...this.logs];
  }
  
  // Get statistics
  getStatistics(): {
    totalLogs: number;
    logsByLevel: Record<string, number>;
    recentSecurityEvents: AuditLogEntry[];
    recentErrors: AuditLogEntry[];
    averageResponseTime?: number;
  totalTokensUsed: number;
  providersUsed: Record<string, number>;
  errorRate: number;
  topEvents: Array<{ event: string; count: number }>;
  topErrors: Array<{ error: string; count: number }>;
  timeRange: { start: Date; end: Date };
  } {
    const now = new Date();
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    const logsByLevel = this.logs.reduce((acc, log) => {
      acc[log.level] = (acc[log.level] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const recentSecurityEvents = this.logs
      .filter(log => log.level === 'SECURITY')
      .filter(log => log.timestamp >= oneDayAgo)
      .slice(0, 10);
    
    const recentErrors = this.logs
      .filter(log => log.level === 'ERROR')
      .filter(log => log.timestamp >= oneDayAgo)
      .slice(0, 10);
    
    const responseTimes = this.logs
      .filter(log => log.responseTime && log.responseTime > 0)
      .map(log => log.responseTime!);
    
    const averageResponseTime = responseTimes.length > 0 
      ? responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length
      : undefined;
    
    const tokensUsed = this.logs
      .filter(log => log.tokensUsed && log.tokensUsed > 0)
      .reduce((sum, log) => sum + log.tokensUsed!, 0);
    
    const providersUsed = this.logs
      .filter(log => log.provider)
      .reduce((acc, log) => {
        acc[log.provider!] = (acc[log.provider!] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
    
    const eventCounts = this.logs.reduce((acc, log) => {
      acc[log.event] = (acc[log.event] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const topEvents = Object.entries(eventCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([event, count]) => ({ event, count }));
    
    const errorCounts = this.logs
      .filter(log => log.level === 'ERROR' && log.error)
      .reduce((acc, log) => {
        acc[log.error!] = (acc[log.error!] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
    
    const topErrors = Object.entries(errorCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([error, count]) => ({ error, count }));
    
    return {
      totalLogs: this.logs.length,
      logsByLevel,
      recentSecurityEvents,
      recentErrors,
      averageResponseTime,
      totalTokensUsed: tokensUsed,
      providersUsed,
      errorRate: logsByLevel['ERROR'] || 0 / (this.logs.length / (24 * 60 * 60)), // errors per hour
      topEvents,
      topErrors,
      timeRange: {
        start: this.logs.length > 0 ? this.logs[0]?.timestamp || now : now,
        end: now,
      },
    };
  }
}

// Global audit logger instance
const auditLoggerInstance = new AuditLogger();

// Export functions instead of the instance for Next.js compatibility
export const auditLogger = {
  log: (level: AuditLogEntry['level'], event: string, details?: Record<string, unknown>, additional?: {
    userId?: string;
    ip?: string;
    userAgent?: string;
    provider?: string;
    responseTime?: number;
    tokensUsed?: number;
    error?: string;
  }) => auditLoggerInstance.log(level, event, details, additional),
  getRecentLogs: (count?: number, level?: AuditLogEntry['level']) => auditLoggerInstance.getRecentLogs(count, level),
  getLogsByTimeRange: (startTime: Date, endTime: Date) => auditLoggerInstance.getLogsByTimeRange(startTime, endTime),
  getSecurityEvents: () => auditLoggerInstance.getSecurityEvents(),
  getErrorEvents: () => auditLoggerInstance.getErrorEvents(),
  clearOldLogs: () => auditLoggerInstance.clearOldLogs(),
  exportLogs: () => auditLoggerInstance.exportLogs(),
  getStatistics: () => auditLoggerInstance.getStatistics(),
};