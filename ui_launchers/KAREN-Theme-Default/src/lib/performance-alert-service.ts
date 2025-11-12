'use client';
/**
 * Performance Alert Service for Karen (production-grade)
 * - SSR safe (guards window/document)
 * - Rate limiting per alert type (maxAlertsPerMinute)
 * - Coalescing: suppress duplicate alerts in a short window
 * - Per-type enable switches and thresholds
 * - Toast variants + durations tuned by severity
 * - Lightweight logs (no big payloads)
 */

import type { PerformanceAlert, RequestMetrics } from './performance-monitor';
import { toast } from '../hooks/use-toast';

const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';

export interface PerformanceAlertConfig {
  showSlowRequestAlerts: boolean;
  showErrorRateAlerts: boolean;
  showDegradationAlerts: boolean;
  slowRequestThreshold: number; // ms
  maxAlertsPerMinute: number;   // per type
  dedupeWindowMs: number;       // coalesce same alert type/message
  suppressEndpoints?: string[]; // optional endpoint patterns to ignore
}

export type AlertType = PerformanceAlert['type'];

class PerformanceAlertService {
  private config: PerformanceAlertConfig = {
    showSlowRequestAlerts: true,
    showErrorRateAlerts: true,
    showDegradationAlerts: true,
    slowRequestThreshold: 5000,
    maxAlertsPerMinute: 3,
    dedupeWindowMs: 8000,
    suppressEndpoints: [],
  };

  // For rate-limit windows
  private alertHistory: Array<{ timestamp: number; type: AlertType }> = [];
  // For coalescing duplicates: key = `${type}::${message}`
  private recentAlerts = new Map<string, number>();

  handleAlert(alert: PerformanceAlert): void {
    if (!isBrowser) return; // no-op on server

    if (!this.shouldShowAlert(alert)) return;
    if (!this.isWithinRateLimit(alert)) return;
    if (this.isSuppressedByEndpoint(alert)) return;
    if (this.isDuplicate(alert)) return;

    this.record(alert);
    this.showToast(alert);
    this.logAlert(alert);
  }

  // -------------------- Toasts --------------------

  private showToast(alert: PerformanceAlert): void {
    const { title, description, variant, duration } = this.getToastConfig(alert);
    try {
      toast({ title, description, variant, duration });
    } catch {
      // If the toast system isn't mounted yet, fail silently
    }
  }

  private getToastConfig(alert: PerformanceAlert): {
    title: string;
    description: string;
    variant: 'default' | 'destructive';
    duration: number;
  } {
    switch (alert.type) {
      case 'slow_request': {
        // Severity dial: soft nudge unless extremely slow
        const isHigh = alert.severity === 'high';
        return {
          title: isHigh ? '⏱️ Very Slow Response' : '⏱️ Karen is thinking…',
          description: isHigh
            ? 'That request is taking much longer than expected. We’re on it.'
            : 'This one is a bit slower than usual—hang tight!',
          variant: isHigh ? 'default' : 'default',
          duration: isHigh ? 6000 : 4000,
        };
      }
      case 'high_error_rate': {
        const isHigh = alert.severity === 'high';
        return {
          title: '🔧 Connection Issues',
          description: isHigh
            ? 'High error rate detected. Some features may be degraded.'
            : 'Seeing elevated errors. Retrying in the background.',
          variant: isHigh ? 'destructive' : 'default',
          duration: isHigh ? 7000 : 5000,
        };
      }
      case 'performance_degradation':
        return {
          title: '🐌 Performance Notice',
          description: 'Recent requests are slower than the usual baseline.',
          variant: 'default',
          duration: 5000,
        };
      default:
        return {
          title: '📊 Performance Notice',
          description: alert.message,
          variant: alert.severity === 'high' ? 'destructive' : 'default',
          duration: 4000,
        };
    }
  }

  // -------------------- Gates & Limits --------------------

  private shouldShowAlert(alert: PerformanceAlert): boolean {
    switch (alert.type) {
      case 'slow_request':
        return this.config.showSlowRequestAlerts;
      case 'high_error_rate':
        return this.config.showErrorRateAlerts;
      case 'performance_degradation':
        return this.config.showDegradationAlerts;
      default:
        return true;
    }
  }

  private isWithinRateLimit(alert: PerformanceAlert): boolean {
    const now = Date.now();
    const oneMinuteAgo = now - 60_000;

    // Trim history window
    this.alertHistory = this.alertHistory.filter(a => a.timestamp > oneMinuteAgo);

    const countForType = this.alertHistory.filter(a => a.type === alert.type).length;
    return countForType < this.config.maxAlertsPerMinute;
  }

  private isDuplicate(alert: PerformanceAlert): boolean {
    const key = `${alert.type}::${alert.message}`;
    const last = this.recentAlerts.get(key) ?? 0;
    const now = Date.now();
    if (now - last < this.config.dedupeWindowMs) {
      return true;
    }
    this.recentAlerts.set(key, now);
    // opportunistic cleanup
    this.recentAlerts.forEach((ts, k) => {
      if (now - ts > this.config.dedupeWindowMs * 4) this.recentAlerts.delete(k);
    });
    return false;
  }

  private getAlertMetadata(alert: PerformanceAlert): {
    endpoint?: string;
    duration?: number;
  } {
    const metrics = alert.metrics;

    if (metrics && typeof metrics === 'object' && 'endpoint' in metrics) {
      const requestMetrics = metrics as Partial<RequestMetrics>;

      return {
        endpoint:
          typeof requestMetrics.endpoint === 'string' ? requestMetrics.endpoint : undefined,
        duration:
          typeof requestMetrics.duration === 'number' ? requestMetrics.duration : undefined,
      };
    }

    return {};
  }

  private isSuppressedByEndpoint(alert: PerformanceAlert): boolean {
    const endpoint = this.getAlertMetadata(alert).endpoint;
    if (!endpoint || !this.config.suppressEndpoints?.length) return false;
    return this.config.suppressEndpoints.some(pattern => {
      // simple substring match or wildcard "*"
      if (pattern === '*') return true;
      return endpoint.includes(pattern);
    });
  }

  private record(alert: PerformanceAlert): void {
    this.alertHistory.push({ timestamp: Date.now(), type: alert.type });
  }

  // -------------------- Logs & Stats --------------------

  private logAlert(alert: PerformanceAlert): void {
    const level = alert.severity === 'high' ? 'warn' : 'info';
    const emoji = this.getAlertEmoji(alert.type);
    const { endpoint, duration } = this.getAlertMetadata(alert);

    // Keep logs clean; no large objects
    console[level](`${emoji} Karen Performance: ${alert.message}`, {
      type: alert.type,
      severity: alert.severity,
      endpoint,
      duration,
      timestamp: alert.timestamp,
    });
  }

  private getAlertEmoji(type: AlertType): string {
    switch (type) {
      case 'slow_request':
        return '⏱️';
      case 'high_error_rate':
        return '🔧';
      case 'performance_degradation':
        return '🐌';
      default:
        return '📊';
    }
  }

  // -------------------- Config & Admin --------------------

  updateConfig(newConfig: Partial<PerformanceAlertConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  getConfig(): PerformanceAlertConfig {
    return { ...this.config };
  }

  clearHistory(): void {
    this.alertHistory = [];
    this.recentAlerts.clear();
  }

  getStats(): {
    totalAlerts: number;
    alertsByType: Record<string, number>;
    recentAlerts: number;
  } {
    const now = Date.now();
    const oneMinuteAgo = now - 60_000;
    const recent = this.alertHistory.filter(a => a.timestamp > oneMinuteAgo);
    const byType = this.alertHistory.reduce<Record<string, number>>((acc, a) => {
      acc[a.type] = (acc[a.type] ?? 0) + 1;
      return acc;
    }, {});
    return {
      totalAlerts: this.alertHistory.length,
      alertsByType: byType,
      recentAlerts: recent.length,
    };
  }
}

// Singleton instance
export const performanceAlertService = new PerformanceAlertService();
export { PerformanceAlertService };
