/**
 * Error Metrics Collector
 * 
 * Specialized metrics collection for error tracking, recovery monitoring,
 * and error analytics for comprehensive error observability.
 */

export interface ErrorMetrics {
  errorCounts: Record<string, number>;
  errorBoundaries: Record<string, number>;
  recoveryAttempts: number;
  recoverySuccesses: number;
  errorsByCategory: Record<string, number>;
  errorsBySeverity: Record<string, number>;
  errorsBySection: Record<string, number>;
  errorTrends: ErrorTrend[];
  meanTimeToRecovery: number;
  errorRate: number;
  criticalErrors: number;
}

export interface ErrorTrend {
  timestamp: number;
  errorCount: number;
  recoveryCount: number;
  errorRate: number;
}

export interface ErrorEvent {
  id: string;
  timestamp: number;
  message: string;
  type: string;
  category: 'ui' | 'network' | 'server' | 'database' | 'auth' | 'unknown';
  severity: 'low' | 'medium' | 'high' | 'critical';
  section: string;
  component?: string;
  stack?: string;
  recovered: boolean;
  recoveryTime?: number;
  recoveryAttempts: number;
  context?: Record<string, any>;
}

export class ErrorMetricsCollector {
  private errorEvents: ErrorEvent[] = [];
  private errorCounts: Record<string, number> = {};
  private errorBoundaries: Record<string, number> = {};
  private recoveryAttempts: number = 0;
  private recoverySuccesses: number = 0;
  private errorTrends: ErrorTrend[] = [];
  private trendInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.startTrendTracking();
  }

  private startTrendTracking() {
    // Update error trends every minute
    this.trendInterval = setInterval(() => {
      this.updateErrorTrends();
    }, 60000);
  }

  private updateErrorTrends() {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;
    
    // Get errors from the last minute
    const recentErrors = this.errorEvents.filter(event => event.timestamp >= oneMinuteAgo);
    const recentRecoveries = recentErrors.filter(event => event.recovered);
    
    // Calculate error rate (errors per second)
    const errorRate = recentErrors.length / 60;
    
    const trend: ErrorTrend = {
      timestamp: now,
      errorCount: recentErrors.length,
      recoveryCount: recentRecoveries.length,
      errorRate
    };
    
    this.errorTrends.push(trend);
    
    // Keep only last 60 trends (1 hour of data)
    if (this.errorTrends.length > 60) {
      this.errorTrends = this.errorTrends.slice(-60);
    }
  }

  public recordError(
    message: string,
    type: string,
    category: ErrorEvent['category'],
    severity: ErrorEvent['severity'],
    section: string,
    component?: string,
    stack?: string,
    context?: Record<string, any>
  ): string {
    const errorId = `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const errorEvent: ErrorEvent = {
      id: errorId,
      timestamp: Date.now(),
      message,
      type,
      category,
      severity,
      section,
      component,
      stack,
      recovered: false,
      recoveryAttempts: 0,
      context
    };
    
    this.errorEvents.push(errorEvent);
    
    // Update error counts
    this.errorCounts[type] = (this.errorCounts[type] || 0) + 1;
    
    // Keep only last 1000 error events
    if (this.errorEvents.length > 1000) {
      this.errorEvents = this.errorEvents.slice(-1000);
    }
    
    return errorId;
  }

  public recordErrorBoundaryTrigger(component: string) {
    this.errorBoundaries[component] = (this.errorBoundaries[component] || 0) + 1;
  }

  public recordRecoveryAttempt(errorId: string) {
    const errorEvent = this.errorEvents.find(event => event.id === errorId);
    if (errorEvent) {
      errorEvent.recoveryAttempts++;
    }
    
    this.recoveryAttempts++;
  }

  public recordRecoverySuccess(errorId: string, recoveryTime?: number) {
    const errorEvent = this.errorEvents.find(event => event.id === errorId);
    if (errorEvent) {
      errorEvent.recovered = true;
      errorEvent.recoveryTime = recoveryTime || (Date.now() - errorEvent.timestamp);
    }
    
    this.recoverySuccesses++;
  }

  public async getErrorMetrics(): Promise<ErrorMetrics> {
    const now = Date.now();
    const oneHourAgo = now - 3600000;
    
    // Get recent errors for calculations
    const recentErrors = this.errorEvents.filter(event => event.timestamp >= oneHourAgo);
    
    // Calculate error counts by category
    const errorsByCategory: Record<string, number> = {};
    recentErrors.forEach(event => {
      errorsByCategory[event.category] = (errorsByCategory[event.category] || 0) + 1;

    // Calculate error counts by severity
    const errorsBySeverity: Record<string, number> = {};
    recentErrors.forEach(event => {
      errorsBySeverity[event.severity] = (errorsBySeverity[event.severity] || 0) + 1;

    // Calculate error counts by section
    const errorsBySection: Record<string, number> = {};
    recentErrors.forEach(event => {
      errorsBySection[event.section] = (errorsBySection[event.section] || 0) + 1;

    // Calculate mean time to recovery
    const recoveredErrors = recentErrors.filter(event => event.recovered && event.recoveryTime);
    const meanTimeToRecovery = recoveredErrors.length > 0
      ? recoveredErrors.reduce((sum, event) => sum + (event.recoveryTime || 0), 0) / recoveredErrors.length
      : 0;
    
    // Calculate error rate (errors per minute)
    const errorRate = recentErrors.length / 60;
    
    // Count critical errors
    const criticalErrors = recentErrors.filter(event => event.severity === 'critical').length;
    
    return {
      errorCounts: { ...this.errorCounts },
      errorBoundaries: { ...this.errorBoundaries },
      recoveryAttempts: this.recoveryAttempts,
      recoverySuccesses: this.recoverySuccesses,
      errorsByCategory,
      errorsBySeverity,
      errorsBySection,
      errorTrends: [...this.errorTrends],
      meanTimeToRecovery,
      errorRate,
      criticalErrors
    };
  }

  public getErrorEvents(limit: number = 100): ErrorEvent[] {
    return this.errorEvents.slice(-limit);
  }

  public getErrorsByTimeRange(startTime: number, endTime: number): ErrorEvent[] {
    return this.errorEvents.filter(event => 
      event.timestamp >= startTime && event.timestamp <= endTime
    );
  }

  public getErrorsByCategory(category: ErrorEvent['category']): ErrorEvent[] {
    return this.errorEvents.filter(event => event.category === category);
  }

  public getErrorsBySeverity(severity: ErrorEvent['severity']): ErrorEvent[] {
    return this.errorEvents.filter(event => event.severity === severity);
  }

  public getErrorsBySection(section: string): ErrorEvent[] {
    return this.errorEvents.filter(event => event.section === section);
  }

  public getCriticalErrors(): ErrorEvent[] {
    return this.errorEvents.filter(event => event.severity === 'critical');
  }

  public getUnrecoveredErrors(): ErrorEvent[] {
    return this.errorEvents.filter(event => !event.recovered);
  }

  public getRecoveryStats() {
    const totalErrors = this.errorEvents.length;
    const recoveredErrors = this.errorEvents.filter(event => event.recovered).length;
    const recoveryRate = totalErrors > 0 ? recoveredErrors / totalErrors : 0;
    
    const recoveryTimes = this.errorEvents
      .filter(event => event.recovered && event.recoveryTime)
      .map(event => event.recoveryTime!);
    
    const averageRecoveryTime = recoveryTimes.length > 0
      ? recoveryTimes.reduce((sum, time) => sum + time, 0) / recoveryTimes.length
      : 0;
    
    const medianRecoveryTime = recoveryTimes.length > 0
      ? this.calculateMedian(recoveryTimes)
      : 0;
    
    return {
      totalErrors,
      recoveredErrors,
      unrecoveredErrors: totalErrors - recoveredErrors,
      recoveryRate,
      averageRecoveryTime,
      medianRecoveryTime,
      totalRecoveryAttempts: this.recoveryAttempts,
      successfulRecoveries: this.recoverySuccesses,
      recoverySuccessRate: this.recoveryAttempts > 0 ? this.recoverySuccesses / this.recoveryAttempts : 0
    };
  }

  private calculateMedian(numbers: number[]): number {
    const sorted = [...numbers].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);
    
    if (sorted.length % 2 === 0) {
      return (sorted[middle - 1] + sorted[middle]) / 2;
    } else {
      return sorted[middle];
    }
  }

  public getErrorFrequency(timeWindowMs: number = 3600000): Record<string, number> {
    const now = Date.now();
    const cutoff = now - timeWindowMs;
    
    const recentErrors = this.errorEvents.filter(event => event.timestamp >= cutoff);
    const frequency: Record<string, number> = {};
    
    recentErrors.forEach(event => {
      const key = `${event.type}:${event.message}`;
      frequency[key] = (frequency[key] || 0) + 1;

    return frequency;
  }

  public getTopErrors(limit: number = 10, timeWindowMs: number = 3600000): Array<{
    type: string;
    message: string;
    count: number;
    lastOccurrence: number;
    severity: string;
    category: string;
  }> {
    const frequency = this.getErrorFrequency(timeWindowMs);
    
    return Object.entries(frequency)
      .map(([key, count]) => {
        const [type, message] = key.split(':', 2);
        const lastError = this.errorEvents
          .filter(event => event.type === type && event.message === message)
          .sort((a, b) => b.timestamp - a.timestamp)[0];
        
        return {
          type,
          message,
          count,
          lastOccurrence: lastError?.timestamp || 0,
          severity: lastError?.severity || 'unknown',
          category: lastError?.category || 'unknown'
        };
      })
      .sort((a, b) => b.count - a.count)
      .slice(0, limit);
  }

  public getErrorTrendAnalysis(timeWindowMs: number = 3600000) {
    const now = Date.now();
    const cutoff = now - timeWindowMs;
    
    const recentTrends = this.errorTrends.filter(trend => trend.timestamp >= cutoff);
    
    if (recentTrends.length === 0) {
      return {
        trend: 'stable',
        changePercent: 0,
        averageErrorRate: 0,
        peakErrorRate: 0,
        totalErrors: 0
      };
    }
    
    const totalErrors = recentTrends.reduce((sum, trend) => sum + trend.errorCount, 0);
    const averageErrorRate = recentTrends.reduce((sum, trend) => sum + trend.errorRate, 0) / recentTrends.length;
    const peakErrorRate = Math.max(...recentTrends.map(trend => trend.errorRate));
    
    // Calculate trend direction
    const firstHalf = recentTrends.slice(0, Math.floor(recentTrends.length / 2));
    const secondHalf = recentTrends.slice(Math.floor(recentTrends.length / 2));
    
    const firstHalfAvg = firstHalf.reduce((sum, trend) => sum + trend.errorRate, 0) / firstHalf.length;
    const secondHalfAvg = secondHalf.reduce((sum, trend) => sum + trend.errorRate, 0) / secondHalf.length;
    
    const changePercent = firstHalfAvg > 0 ? ((secondHalfAvg - firstHalfAvg) / firstHalfAvg) * 100 : 0;
    
    let trend: 'increasing' | 'decreasing' | 'stable' = 'stable';
    if (Math.abs(changePercent) > 10) {
      trend = changePercent > 0 ? 'increasing' : 'decreasing';
    }
    
    return {
      trend,
      changePercent,
      averageErrorRate,
      peakErrorRate,
      totalErrors
    };
  }

  public clearOldErrors(maxAge: number = 86400000) { // Default: 24 hours
    const cutoff = Date.now() - maxAge;
    this.errorEvents = this.errorEvents.filter(event => event.timestamp >= cutoff);
  }

  public resetMetrics() {
    this.errorEvents = [];
    this.errorCounts = {};
    this.errorBoundaries = {};
    this.recoveryAttempts = 0;
    this.recoverySuccesses = 0;
    this.errorTrends = [];
  }

  public destroy() {
    if (this.trendInterval) {
      clearInterval(this.trendInterval);
      this.trendInterval = null;
    }
  }

  public exportErrorData() {
    return {
      errorEvents: this.errorEvents,
      errorCounts: this.errorCounts,
      errorBoundaries: this.errorBoundaries,
      recoveryAttempts: this.recoveryAttempts,
      recoverySuccesses: this.recoverySuccesses,
      errorTrends: this.errorTrends,
      recoveryStats: this.getRecoveryStats(),
      topErrors: this.getTopErrors(),
      trendAnalysis: this.getErrorTrendAnalysis()
    };
  }
}

export default ErrorMetricsCollector;