/**
 * Error Metrics Collector (Prod-Ready)
 *
 * Tracks error events across UI/Network/Server/DB/Auth,
 * measures recovery attempts/success, trends, MTTR, and criticals.
 *
 * Highlights:
 * - Trend sampler (1m) with leak-free lifecycle
 * - Safe math & guards (no divide-by-zero)
 * - Recent-window analytics (1h defaults) for dashboards
 * - Stable ID generation (crypto if available, fallback otherwise)
 * - Lightweight hot-path maps + on-demand aggregations
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
  meanTimeToRecovery: number;  // ms
  errorRate: number;           // errors per minute (recent window)
  criticalErrors: number;      // count in recent window
}

export interface ErrorTrend {
  timestamp: number;
  errorCount: number;
  recoveryCount: number;
  errorRate: number;           // errors per second in the sampled minute
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
  recoveryTime?: number;       // ms
  recoveryAttempts: number;
  context?: Record<string, any>;
}

type TrendTimer = ReturnType<typeof setInterval> | null;

function now(): number {
  return Date.now();
}

function safeAvg(nums: number[]): number {
  if (!nums.length) return 0;
  let sum = 0;
  for (let i = 0; i < nums.length; i++) sum += nums[i];
  return sum / nums.length;
}

function median(nums: number[]): number {
  if (!nums.length) return 0;
  const s = [...nums].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 === 0 ? (s[m - 1] + s[m]) / 2 : s[m];
}

function incr(map: Record<string, number>, key: string, by = 1) {
  map[key] = (map[key] || 0) + by;
}

function makeId(): string {
  // Prefer crypto if available
  try {
    const g = (globalThis as any);
    if (g?.crypto?.randomUUID) return 'err-' + g.crypto.randomUUID();
  } catch {}
  // Fallback
  return `err-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export class ErrorMetricsCollector {
  private errorEvents: ErrorEvent[] = [];
  private errorCounts: Record<string, number> = {};
  private errorBoundaries: Record<string, number> = {};
  private recoveryAttempts = 0;
  private recoverySuccesses = 0;

  private errorTrends: ErrorTrend[] = [];
  private trendInterval: TrendTimer = null;

  // Configurable windows
  private readonly trendWindowMs = 60_000;     // 1 minute per sample
  private readonly metricsWindowMs = 60 * 60 * 1000; // 1 hour for recent analytics
  private readonly maxEvents = 5000;           // ring buffer limit

  constructor() {
    this.startTrendTracking();
  }

  // ---------------- Trend tracking ----------------

  private startTrendTracking() {
    this.stopTrendTracking(); // ensure no duplicates
    this.trendInterval = setInterval(() => this.updateErrorTrends(), this.trendWindowMs);
  }

  private stopTrendTracking() {
    if (this.trendInterval) {
      clearInterval(this.trendInterval);
      this.trendInterval = null;
    }
  }

  private updateErrorTrends() {
    const t = now();
    const recent = this.errorEvents.filter(e => e.timestamp >= t - this.trendWindowMs);
    const recovered = recent.filter(e => e.recovered);
    const ratePerSec = recent.length / Math.max(1, this.trendWindowMs / 1000);

    const trend: ErrorTrend = {
      timestamp: t,
      errorCount: recent.length,
      recoveryCount: recovered.length,
      errorRate: ratePerSec,
    };
    this.errorTrends.push(trend);
    if (this.errorTrends.length > 60) {
      this.errorTrends = this.errorTrends.slice(-60); // keep last 60 mins
    }
  }

  // ---------------- Recording APIs ----------------

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
    const id = makeId();
    const evt: ErrorEvent = {
      id,
      timestamp: now(),
      message,
      type,
      category,
      severity,
      section,
      component,
      stack,
      recovered: false,
      recoveryAttempts: 0,
      context,
    };

    this.errorEvents.push(evt);
    incr(this.errorCounts, type, 1);

    // ring buffer bound
    if (this.errorEvents.length > this.maxEvents) {
      this.errorEvents = this.errorEvents.slice(-this.maxEvents);
    }

    return id;
  }

  public recordErrorBoundaryTrigger(component: string) {
    incr(this.errorBoundaries, component, 1);
  }

  public recordRecoveryAttempt(errorId: string) {
    const evt = this.errorEvents.find(e => e.id === errorId);
    if (evt) evt.recoveryAttempts++;
    this.recoveryAttempts++;
  }

  public recordRecoverySuccess(errorId: string, recoveryTimeMs?: number) {
    const evt = this.errorEvents.find(e => e.id === errorId);
    if (evt && !evt.recovered) {
      evt.recovered = true;
      evt.recoveryTime = typeof recoveryTimeMs === 'number' ? recoveryTimeMs : Math.max(0, now() - evt.timestamp);
      this.recoverySuccesses++;
    }
  }

  // ---------------- Aggregations ----------------

  public async getErrorMetrics(): Promise<ErrorMetrics> {
    const t = now();
    const recent = this.errorEvents.filter(e => e.timestamp >= t - this.metricsWindowMs);

    // category
    const byCategory: Record<string, number> = {};
    for (let i = 0; i < recent.length; i++) {
      const c = recent[i].category;
      incr(byCategory, c, 1);
    }

    // severity
    const bySeverity: Record<string, number> = {};
    for (let i = 0; i < recent.length; i++) {
      const s = recent[i].severity;
      incr(bySeverity, s, 1);
    }

    // section
    const bySection: Record<string, number> = {};
    for (let i = 0; i < recent.length; i++) {
      const sec = recent[i].section;
      incr(bySection, sec, 1);
    }

    // MTTR
    const recovered = recent.filter(e => e.recovered && typeof e.recoveryTime === 'number');
    const mttr = safeAvg(recovered.map(e => e.recoveryTime as number)); // ms

    // Error rate: per minute over the 1h window (errors / 60min)
    const minutes = Math.max(1, this.metricsWindowMs / 60_000);
    const errorRatePerMinute = recent.length / minutes;

    // Criticals
    const criticals = recent.reduce((acc, e) => acc + (e.severity === 'critical' ? 1 : 0), 0);

    return {
      errorCounts: { ...this.errorCounts },
      errorBoundaries: { ...this.errorBoundaries },
      recoveryAttempts: this.recoveryAttempts,
      recoverySuccesses: this.recoverySuccesses,
      errorsByCategory: byCategory,
      errorsBySeverity: bySeverity,
      errorsBySection: bySection,
      errorTrends: [...this.errorTrends],
      meanTimeToRecovery: mttr,
      errorRate: errorRatePerMinute,
      criticalErrors: criticals,
    };
  }

  public getErrorEvents(limit = 100): ErrorEvent[] {
    if (limit <= 0) return [];
    const start = Math.max(0, this.errorEvents.length - limit);
    return this.errorEvents.slice(start);
  }

  public getErrorsByTimeRange(startTime: number, endTime: number): ErrorEvent[] {
    return this.errorEvents.filter(e => e.timestamp >= startTime && e.timestamp <= endTime);
  }

  public getErrorsByCategory(category: ErrorEvent['category']): ErrorEvent[] {
    return this.errorEvents.filter(e => e.category === category);
  }

  public getErrorsBySeverity(severity: ErrorEvent['severity']): ErrorEvent[] {
    return this.errorEvents.filter(e => e.severity === severity);
  }

  public getErrorsBySection(section: string): ErrorEvent[] {
    return this.errorEvents.filter(e => e.section === section);
  }

  public getCriticalErrors(): ErrorEvent[] {
    return this.errorEvents.filter(e => e.severity === 'critical');
  }

  public getUnrecoveredErrors(): ErrorEvent[] {
    return this.errorEvents.filter(e => !e.recovered);
  }

  public getRecoveryStats() {
    const total = this.errorEvents.length;
    const recovered = this.errorEvents.filter(e => e.recovered);
    const recoveryRate = total > 0 ? recovered.length / total : 0;

    const times = recovered
      .map(e => e.recoveryTime)
      .filter((v): v is number => typeof v === 'number');

    const averageRecoveryTime = safeAvg(times);
    const medianRecoveryTime = median(times);

    return {
      totalErrors: total,
      recoveredErrors: recovered.length,
      unrecoveredErrors: total - recovered.length,
      recoveryRate,
      averageRecoveryTime,
      medianRecoveryTime,
      totalRecoveryAttempts: this.recoveryAttempts,
      successfulRecoveries: this.recoverySuccesses,
      recoverySuccessRate: this.recoveryAttempts > 0 ? this.recoverySuccesses / this.recoveryAttempts : 0,
    };
  }

  public getErrorFrequency(timeWindowMs = this.metricsWindowMs): Record<string, number> {
    const cutoff = now() - timeWindowMs;
    const recent = this.errorEvents.filter(e => e.timestamp >= cutoff);
    const freq: Record<string, number> = {};
    for (let i = 0; i < recent.length; i++) {
      const e = recent[i];
      const key = `${e.type}:${e.message}`;
      incr(freq, key, 1);
    }
    return freq;
  }

  public getTopErrors(
    limit = 10,
    timeWindowMs = this.metricsWindowMs
  ): Array<{
    type: string;
    message: string;
    count: number;
    lastOccurrence: number;
    severity: string;
    category: string;
  }> {
    const freq = this.getErrorFrequency(timeWindowMs);
    const entries = Object.entries(freq);
    const out: Array<{
      type: string;
      message: string;
      count: number;
      lastOccurrence: number;
      severity: string;
      category: string;
    }> = [];

    for (let i = 0; i < entries.length; i++) {
      const [key, count] = entries[i];
      const [type, message] = key.split(':', 2);
      // find most recent matching event
      let last: ErrorEvent | undefined;
      for (let j = this.errorEvents.length - 1; j >= 0; j--) {
        const e = this.errorEvents[j];
        if (e.type === type && e.message === message) {
          last = e; break;
        }
      }
      out.push({
        type,
        message,
        count,
        lastOccurrence: last?.timestamp ?? 0,
        severity: last?.severity ?? 'unknown',
        category: last?.category ?? 'unknown',
      });
    }

    out.sort((a, b) => b.count - a.count);
    return out.slice(0, Math.max(0, limit));
  }

  public getErrorTrendAnalysis(timeWindowMs = this.metricsWindowMs) {
    const cutoff = now() - timeWindowMs;
    const recentTrends = this.errorTrends.filter(t => t.timestamp >= cutoff);

    if (recentTrends.length === 0) {
      return {
        trend: 'stable' as const,
        changePercent: 0,
        averageErrorRate: 0,
        peakErrorRate: 0,
        totalErrors: 0,
      };
    }

    const totalErrors = recentTrends.reduce((a, t) => a + t.errorCount, 0);
    const avgRate = safeAvg(recentTrends.map(t => t.errorRate));
    const peakRate = Math.max(...recentTrends.map(t => t.errorRate));

    // split halves safely
    const mid = Math.floor(recentTrends.length / 2) || 1;
    const firstHalf = recentTrends.slice(0, mid);
    const secondHalf = recentTrends.slice(mid);

    const firstAvg = safeAvg(firstHalf.map(t => t.errorRate));
    const secondAvg = safeAvg(secondHalf.map(t => t.errorRate));
    const changePercent = firstAvg > 0 ? ((secondAvg - firstAvg) / firstAvg) * 100 : 0;

    let trend: 'increasing' | 'decreasing' | 'stable' = 'stable';
    if (Math.abs(changePercent) > 10) trend = changePercent > 0 ? 'increasing' : 'decreasing';

    return {
      trend,
      changePercent,
      averageErrorRate: avgRate,
      peakErrorRate: peakRate,
      totalErrors,
    };
  }

  public clearOldErrors(maxAgeMs = 24 * 60 * 60 * 1000) {
    const cutoff = now() - maxAgeMs;
    this.errorEvents = this.errorEvents.filter(e => e.timestamp >= cutoff);
  }

  public resetMetrics() {
    this.errorEvents = [];
    this.errorCounts = {};
    this.errorBoundaries = {};
    this.recoveryAttempts = 0;
    this.recoverySuccesses = 0;
    this.errorTrends = [];
    // restart trend timer cleanly
    this.startTrendTracking();
  }

  public destroy() {
    this.stopTrendTracking();
  }

  public exportErrorData() {
    return {
      errorEvents: [...this.errorEvents],
      errorCounts: { ...this.errorCounts },
      errorBoundaries: { ...this.errorBoundaries },
      recoveryAttempts: this.recoveryAttempts,
      recoverySuccesses: this.recoverySuccesses,
      errorTrends: [...this.errorTrends],
      recoveryStats: this.getRecoveryStats(),
      topErrors: this.getTopErrors(),
      trendAnalysis: this.getErrorTrendAnalysis(),
    };
  }
}

export default ErrorMetricsCollector;
