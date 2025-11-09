'use client';

import { safeWarn, safeInfo } from './safe-console';

const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';

export interface TelemetryEvent {
  event: string;
  payload: Record<string, any>;
  correlationId?: string;
  timestamp: string;
  sessionId: string;
  userId?: string;
  userAgent: string;
  url: string;
}

export interface TelemetryConfig {
  enabled: boolean;
  endpoint?: string;
  batchSize: number;
  flushInterval: number; // ms
  maxRetries: number;
  debug: boolean;
  sampling: number; // 0..1
  maxQueueSize: number;
  requestTimeout: number; // ms
  beaconOnUnload: boolean;
}

export interface Span {
  id: string;
  name: string;
  startTime: number;
  end: () => number;
  addTag: (key: string, value: any) => void;
}

export type Timer = ReturnType<typeof setInterval>;

class TelemetryService {
  private config: TelemetryConfig;
  private eventQueue: TelemetryEvent[] = [];
  private correlationId = '';
  private sessionId = '';
  private flushTimer: Timer | null = null;
  private retryCount = 0;
  private isFlushing = false;

  constructor(config: Partial<TelemetryConfig> = {}) {
    this.config = {
      enabled: true,
      batchSize: 20,
      flushInterval: 5000,
      maxRetries: 3,
      debug: process.env.NODE_ENV === 'development',
      sampling: 1.0,
      maxQueueSize: 2000,
      requestTimeout: 8000,
      beaconOnUnload: true,
      ...config,
    };

    // Stable IDs
    this.sessionId = this.getOrCreateSessionId();
    this.correlationId = this.generateId();

    // Timers & lifecycle (browser only)
    if (isBrowser) {
      this.startFlushTimer();

      // Flush when page is being hidden/backgrounded
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
          this.flush({ useBeacon: this.config.beaconOnUnload }).catch(() => void 0);
        }
      });

      // Heavier guarantee when page really unloads
      window.addEventListener('pagehide', () => {
        this.flush({ useBeacon: this.config.beaconOnUnload }).catch(() => void 0);
      });
    }
  }

  // ---------------- Public API ----------------

  public track(event: string, payload: Record<string, any> = {}, correlationId?: string): void {
    if (!this.config.enabled || !isBrowser) return;
    if (!this.shouldSample()) return;

    const perfNow =
      typeof performance !== 'undefined' && typeof performance.now === 'function'
        ? performance.now()
        : undefined;

    const telemetryEvent: TelemetryEvent = {
      event,
      payload: {
        ...payload,
        ...(perfNow !== undefined
          ? {
              performanceNow: perfNow,
              timeOrigin: (performance as any)?.timeOrigin,
            }
          : {}),
      },
      correlationId: correlationId || this.correlationId,
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId,
      userId: this.getUserId(),
      userAgent: isBrowser ? navigator.userAgent : 'unknown',
      url: isBrowser ? window.location.href : 'unknown',
    };

    // Enforce queue cap (drop oldest)
    if (this.eventQueue.length >= this.config.maxQueueSize) {
      this.eventQueue.splice(0, this.eventQueue.length - this.config.maxQueueSize + 1);
    }
    this.eventQueue.push(telemetryEvent);

    if (this.config.debug) {
      safeInfo('📊 Telemetry Event:', telemetryEvent);
    }

    if (this.eventQueue.length >= this.config.batchSize) {
      void this.flush();
    }
  }

  public startSpan(name: string): Span {
    const spanId = this.generateId();
    const startTime = isBrowser && typeof performance !== 'undefined' ? performance.now() : Date.now();

    this.track('span_start', { spanId, spanName: name, startTime });

    return {
      id: spanId,
      name,
      startTime,
      end: () => {
        const endTime = isBrowser && typeof performance !== 'undefined' ? performance.now() : Date.now();
        const duration = endTime - startTime;
        this.track('span_end', { spanId, spanName: name, startTime, endTime, duration });
        return duration;
      },
      addTag: (key: string, value: any) => {
        this.track('span_tag', { spanId, spanName: name, tagKey: key, tagValue: value });
      },
    };
  }

  public setCorrelationId(id: string): void {
    this.correlationId = id;
    this.track('correlation_id_set', { correlationId: id });
  }

  public setUserId(userId: string): void {
    if (!isBrowser) return;
    try {
      localStorage.setItem('telemetry_user_id', userId);
      this.track('user_id_set', { userId });
    } catch {
      // ignore
    }
  }

  public async flush(opts?: { useBeacon?: boolean }): Promise<void> {
    if (!isBrowser || this.eventQueue.length === 0) return;
    if (this.isFlushing) return; // de-dupe concurrent flushes

    const useBeacon = Boolean(opts?.useBeacon);
    const events = this.drainQueue();

    if (this.config.debug) {
      safeInfo(`📊 Flushing ${events.length} telemetry events`);
    }

    // Always store locally as fallback
    this.storeLocally(events);

    if (!this.config.endpoint) return;

    try {
      if (useBeacon && 'sendBeacon' in navigator) {
        const ok = this.sendWithBeacon(events);
        if (!ok) throw new Error('sendBeacon returned false');
        this.retryCount = 0;
        return;
      }

      await this.sendWithFetch(events);
      this.retryCount = 0;
    } catch (error) {
      safeWarn('Failed to send telemetry events:', error);

      // Re-queue for retry (prepend to preserve order)
      this.eventQueue = [...events, ...this.eventQueue];

      if (this.retryCount < this.config.maxRetries) {
        this.retryCount++;
        const delay = Math.min(1000 * 2 ** this.retryCount, 15000); // capped backoff
        setTimeout(() => void this.flush(), delay);
      }
    }
  }

  public getStoredEvents(): TelemetryEvent[] {
    if (!isBrowser) return [];
    try {
      return JSON.parse(localStorage.getItem('telemetry_events') || '[]');
    } catch {
      return [];
    }
  }

  public clearStoredEvents(): void {
    if (!isBrowser) return;
    try {
      localStorage.removeItem('telemetry_events');
    } catch {
      // ignore
    }
  }

  public getStats(): {
    queueSize: number;
    sessionId: string;
    correlationId: string;
    storedEvents: number;
    config: TelemetryConfig;
  } {
    return {
      queueSize: this.eventQueue.length,
      sessionId: this.sessionId,
      correlationId: this.correlationId,
      storedEvents: this.getStoredEvents().length,
      config: this.config,
    };
  }

  public updateConfig(next: Partial<TelemetryConfig>): void {
    this.config = { ...this.config, ...next };
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    if (isBrowser) {
      this.startFlushTimer();
    }
  }

  public destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    // fire and forget
    void this.flush({ useBeacon: this.config.beaconOnUnload });
  }

  // ---------------- Internals ----------------

  private startFlushTimer(): void {
    if (this.flushTimer) clearInterval(this.flushTimer);
    this.flushTimer = setInterval(() => void this.flush(), this.config.flushInterval);
  }

  private shouldSample(): boolean {
    return Math.random() <= this.config.sampling;
  }

  private generateId(): string {
    // time-ordered + random suffix
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  }

  private getOrCreateSessionId(): string {
    if (!isBrowser) return this.generateId();
    try {
      const key = 'telemetry_session_id';
      const existing = sessionStorage.getItem(key);
      if (existing) return existing;
      const sid = this.generateId();
      sessionStorage.setItem(key, sid);
      return sid;
    } catch {
      return this.generateId();
    }
  }

  private getUserId(): string | undefined {
    if (!isBrowser) return undefined;
    try {
      return localStorage.getItem('telemetry_user_id') || undefined;
    } catch {
      return undefined;
    }
  }

  private drainQueue(): TelemetryEvent[] {
    const events = this.eventQueue;
    this.eventQueue = [];
    return events;
  }

  private storeLocally(events: TelemetryEvent[]): void {
    if (!isBrowser) return;
    try {
      const existing: TelemetryEvent[] = JSON.parse(localStorage.getItem('telemetry_events') || '[]');
      const combined = [...existing, ...events];
      const trimmed = combined.slice(-1000);
      localStorage.setItem('telemetry_events', JSON.stringify(trimmed));
    } catch (error) {
      safeWarn('Failed to store telemetry events locally:', error);
    }
  }

  private sendWithBeacon(events: TelemetryEvent[]): boolean {
    try {
      const blob = new Blob(
        [
          JSON.stringify({
            events,
            metadata: { version: '1.0', source: 'web-ui', timestamp: new Date().toISOString() },
          }),
        ],
        { type: 'application/json' }
      );
      // @ts-expect-error TS lib doesn’t know sendBeacon returns boolean
      return navigator.sendBeacon(this.config.endpoint!, blob);
    } catch (e) {
      return false;
    }
  }

  private async sendWithFetch(events: TelemetryEvent[]): Promise<void> {
    this.isFlushing = true;
    try {
      const controller = new AbortController();
      const t = setTimeout(() => controller.abort(), this.config.requestTimeout);

      const res = await fetch(this.config.endpoint!, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          events,
          metadata: { version: '1.0', source: 'web-ui', timestamp: new Date().toISOString() },
        }),
        signal: controller.signal,
        keepalive: true, // improves delivery during unload on some browsers
      });

      clearTimeout(t);

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
    } finally {
      this.isFlushing = false;
    }
  }
}

// ---------------- Singleton + Convenience ----------------

let telemetryInstance: TelemetryService | null = null;

export const getTelemetryService = (config?: Partial<TelemetryConfig>): TelemetryService => {
  if (!telemetryInstance) {
    telemetryInstance = new TelemetryService(config);
  } else if (config) {
    telemetryInstance.updateConfig(config);
  }
  return telemetryInstance;
};

export const track = (event: string, payload?: Record<string, any>, correlationId?: string): void => {
  getTelemetryService().track(event, payload, correlationId);
};

export const startSpan = (name: string): Span => {
  return getTelemetryService().startSpan(name);
};

export const setCorrelationId = (id: string): void => {
  getTelemetryService().setCorrelationId(id);
};

export const setUserId = (userId: string): void => {
  getTelemetryService().setUserId(userId);
};

export const flushTelemetry = (): Promise<void> => {
  return getTelemetryService().flush();
};

export default TelemetryService;
